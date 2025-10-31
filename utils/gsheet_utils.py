import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import streamlit as st

SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

# =====================================
# 🔗 Googleスプレッドシート接続
# =====================================
def connect_to_gsheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    client = gspread.authorize(creds)
    return client


def read_sheet(sheet_name):
    """スプレッドシートからDataFrameとして読み込み"""
    client = connect_to_gsheet()
    ws = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
    data = ws.get_all_records()
    return pd.DataFrame(data)


def write_with_history(sheet_name, new_df, user):
    """変更検出＋履歴書き込み"""
    client = connect_to_gsheet()
    ss = client.open_by_key(SPREADSHEET_ID)
    ws = ss.worksheet(sheet_name)
    old_df = pd.DataFrame(ws.get_all_records())

    changes = []
    for i in range(min(len(new_df), len(old_df))):
        for col in new_df.columns:
            old_val = str(old_df.at[i, col]) if col in old_df.columns else ""
            new_val = str(new_df.at[i, col])
            if old_val != new_val:
                changes.append([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    user,
                    sheet_name,
                    i + 2,
                    col,
                    old_val,
                    new_val
                ])

    # データ更新
    ws.clear()
    ws.update([new_df.columns.values.tolist()] + new_df.fillna("").values.tolist())

    # 履歴保存
    if changes:
        log_name = f"{sheet_name}_履歴"
        try:
            ws_log = ss.worksheet(log_name)
        except gspread.WorksheetNotFound:
            ws_log = ss.add_worksheet(title=log_name, rows=1000, cols=10)
            ws_log.append_row(["日時", "ユーザー", "対象シート", "行", "列", "変更前", "変更後"])
        ws_log.append_rows(changes)
