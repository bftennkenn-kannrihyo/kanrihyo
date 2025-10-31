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
# 💾 データ保存＆履歴追加
# =====================================
def save_with_history(spreadsheet_id, sheet_name, df_before, df_after, user):
    """
    データを上書き保存し、変更履歴をシートに追加する。
    履歴シート名は「{シート名}_履歴」
    """
    client = connect_gspread()

    # --- メインシート更新 ---
    ws = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    ws.update([df_after.columns.values.tolist()] + df_after.values.tolist())

    # --- 履歴シート処理 ---
    ws_history_name = f"{sheet_name}_履歴"
    ws_history = client.open_by_key(spreadsheet_id).worksheet(ws_history_name)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    diffs = []
    for r in range(len(df_before)):
        for c in df_before.columns:
            before = str(df_before.loc[r, c])
            after = str(df_after.loc[r, c])
            if before != after:
                diffs.append([now, user, sheet_name, r + 2, c, before, after])

    if diffs:
        ws_history.append_rows(diffs)
        st.success("✅ 変更を保存し、履歴を追加しました。")
    else:
        st.info("変更はありません。")
