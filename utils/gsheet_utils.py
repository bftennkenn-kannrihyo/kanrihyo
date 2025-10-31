import streamlit as st
import gspread
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials


# =====================================
# 🔗 Googleスプレッドシート接続
# =====================================
@st.cache_resource
def connect_gspread():
    """Googleスプレッドシートに接続してクライアントを返す"""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    return gspread.authorize(creds)


# =====================================
# 📄 シートの読み込み（キャッシュ付き）
# =====================================
@st.cache_data(ttl=180)  # 3分間キャッシュ保持
def load_sheet(spreadsheet_id, sheet_name, header_only=False):
    """
    Googleスプレッドシートを読み込む
    header_only=True の場合は1行目（列名）だけ読み込む
    """
    client = connect_gspread()
    ws = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

    if header_only:
        headers = ws.row_values(1)
        df = pd.DataFrame(columns=headers)
    else:
        records = ws.get_all_records()
        if not records:
            headers = ws.row_values(1)
            df = pd.DataFrame(columns=headers)
        else:
            df = pd.DataFrame(records)

    return ws, df


# =====================================
# 💾 データ保存＆履歴追加（安定版）
# =====================================
def save_with_history(spreadsheet_id, sheet_name, df_before, df_after, user):
    """
    フィルタ表示で編集された行のみを更新。
    表示されていないデータは保持したまま。
    履歴シート（{シート名}_履歴）には変更内容を追記。
    """
    try:
        client = connect_gspread()
        ws = client.open_by_key(spreadsheet_id).worksheet(sheet_name)

        # Googleシート全体のデータを取得（削除しないため）
        all_data = pd.DataFrame(ws.get_all_records())
        headers = ws.row_values(1)

        if all_data.empty:
            raise ValueError("シートにデータが存在しません。")

        # NaN対策
        df_before = df_before.fillna("").astype(str)
        df_after = df_after.fillna("").astype(str)
        all_data = all_data.fillna("").astype(str)

        # 履歴記録用
        ws_history = client.open_by_key(spreadsheet_id).worksheet(f"{sheet_name}_履歴")
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        diffs = []

        # 編集対象の施設名などを基準に行を特定（「施設名」が主キー想定）
        key_col = "施設名"
        if key_col not in df_after.columns:
            raise ValueError("『施設名』列が存在しません。主キーに必要です。")

        # 各行ごとに差分検出して反映
        for _, row_after in df_after.iterrows():
            key_val = row_after[key_col]

            if key_val in all_data[key_col].values:
                row_idx = all_data[all_data[key_col] == key_val].index[0]
                for col in df_after.columns:
                    before_val = all_data.at[row_idx, col] if col in all_data.columns else ""
                    after_val = row_after[col]
                    if before_val != after_val:
                        all_data.at[row_idx, col] = after_val
                        diffs.append([now, user, sheet_name, row_idx + 2, col, before_val, after_val])
            else:
                # 新しい施設名の追加（新規行）
                new_row = {c: row_after.get(c, "") for c in headers}
                all_data = pd.concat([all_data, pd.DataFrame([new_row])], ignore_index=True)
                diffs.append([now, user, sheet_name, len(all_data) + 1, "新規行", "", str(row_after.to_dict())])

        # シート更新（全体再書き込みではなく安全に）
        ws.update([headers] + all_data.values.tolist())

        # 履歴追記
        if diffs:
            ws_history.append_rows(diffs)
            st.success("✅ 変更を部分的に反映し、履歴を追加しました。")
        else:
            st.info("変更はありません。")

    except Exception as e:
        st.error(f"❌ 保存時エラー: {type(e).__name__} - {e}")


