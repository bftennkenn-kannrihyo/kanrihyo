# utils/gsheet_utils.py
import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials


# =====================================
# 🔗 Googleスプレッドシート接続
# =====================================
def connect_gspread():
    """Googleスプレッドシートに接続してクライアントを返す"""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    return gspread.authorize(creds)


# =====================================
# 📄 シートの読み込み（ヘッダーのみ or 全件）
# =====================================
def load_sheet(spreadsheet_id, sheet_name, header_only=False):
    """
    Googleスプレッドシートを読み込む
    header_only=True の場合は1行目（列名）だけ読み込む
    """
    client = connect_gspread()
    ws = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

    if header_only:
        # 1行目（ヘッダー）だけ取得
        headers = ws.row_values(1)
        df = pd.DataFrame(columns=headers)
    else:
        # 全データ取得
        df = pd.DataFrame(ws.get_all_records())

    return ws, df


# =====================================
# 💾 データ保存（部分更新）＆履歴追加
# =====================================
def save_with_history(
    spreadsheet_id: str,
    sheet_name: str,
    df_before: pd.DataFrame,
    df_after: pd.DataFrame,
    user: str,
    key_col: str | None = None,
):
    """
    絞り込み・列選択後の DataFrame（df_after）を
    スプレッドシートの元データに“部分的にマージして保存”する。

    - 既存行は key_col（既定は「施設名」→無ければ先頭列）で突き合わせて更新
    - df_after に無い行は変更しない（消さない）
    - df_after に存在しない列は触らない（消さない）
    - df_after に新しい列がある場合は列を追加して反映
    - 見出し（1行目）の順序はシートの現在の順序を尊重
    - 履歴は {シート名}_履歴 に [日時, ユーザー, 対象シート, 行番号(1始), 列名, 変更前, 変更後]
    """

    client = connect_gspread()
    ws = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

    # ---- 最新シートを丸ごと取得（ベースとして保持）----
    headers = ws.row_values(1)
    current_df = pd.DataFrame(ws.get_all_records())

    # 空シートなどで get_all_records() が空のときに備える
    if current_df.empty and headers:
        current_df = pd.DataFrame(columns=headers)

    # ---- 突き合わせキーを決定 ----
    if key_col is None:
        key_col = "施設名" if "施設名" in (current_df.columns.tolist() or headers) else (
            df_after.columns[0] if len(df_after.columns) > 0 else None
        )
    if key_col is None or key_col not in (current_df.columns.tolist() + df_after.columns.tolist()):
        st.error("キー列（例: 施設名）が見つかりません。保存を中止します。")
        return

    # ---- 列のユニオンを取り、足りない列は追加（保持）----
    union_cols = list(dict.fromkeys(  # 順序を保ったユニーク
        (headers or []) + current_df.columns.tolist() + df_after.columns.tolist()
    ))
    for c in union_cols:
        if c not in current_df.columns:
            current_df[c] = ""
        if c not in df_after.columns:
            # df_afterに無い列は更新対象外。比較時はスキップするのでOK
            pass

    # ---- マッチングのためにキー列は文字列化 ----
    cur_key = current_df.get(key_col, pd.Series(dtype=str)).astype(str)
    aft_key = df_after.get(key_col, pd.Series(dtype=str)).astype(str)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    diffs: list[list[str]] = []

    # ---- df_after の各レコードを current_df に反映（部分更新）----
    for _, aft_row in df_after.iterrows():
        k = str(aft_row.get(key_col, ""))
        if k == "":
            # キーが空の行はスキップ
            continue

        # 既存行を検索
        hit_idx = current_df.index[cur_key == k].tolist()
        if hit_idx:
            idx = hit_idx[0]
        else:
            # 見つからなければ末尾に新規行を追加
            idx = len(current_df)
            current_df.loc[idx, union_cols] = ""
            current_df.at[idx, key_col] = k

        # df_after に含まれる列だけを更新対象にする
        for col in df_after.columns:
            # シートにまだ無い列は追加されているはず（上で union 済み）
            old_val = "" if pd.isna(current_df.at[idx, col]) else str(current_df.at[idx, col])
            new_val = "" if pd.isna(aft_row[col]) else str(aft_row[col])
            if old_val != new_val:
                current_df.at[idx, col] = new_val
                # 行番号は見出しを除いた +2（A1がヘッダー、データ開始が2行目）
                diffs.append([now, user, sheet_name, idx + 2, col, old_val, new_val])

    # ---- 見出しの順序は元シートを尊重（無ければユニオン順）----
    out_cols = headers if headers else union_cols
    # もしユニオンで増えた列があり、ヘッダーに無いなら末尾に追加
    out_cols = list(dict.fromkeys(out_cols + union_cols))

    # ---- シートへ反映 ----
    # 既存の余り行/列が残らないようにクリア → 全件更新
    ws.clear()
    ws.update([out_cols] + current_df[out_cols].astype(str).fillna("").values.tolist())

    # ---- 履歴を追記 ----
    if diffs:
        ws_hist = client.open_by_key(spreadsheet_id).worksheet(f"{sheet_name}_履歴")
        ws_hist.append_rows(diffs)
        st.success("✅ 変更を部分更新し、履歴を追加しました。")
    else:
        st.info("変更はありません。")

