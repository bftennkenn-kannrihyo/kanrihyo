import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
from datetime import datetime
import streamlit as st

def connect_gspread():
    """Googleスプレッドシートへ接続"""
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    return gspread.authorize(creds)


def load_sheet(spreadsheet_id, sheet_name):
    """スプレッドシートとデータフレームを返す"""
    client = connect_gspread()
    ws = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    df = pd.DataFrame(ws.get_all_records())
    return ws, df


def save_with_history(spreadsheet_id, sheet_name, ws, df_before, df_after, user):
    """変更をシートに反映し、履歴を保存"""
    ws.update([df_after.columns.values.tolist()] + df_after.values.tolist())

    ws_history_name = f"{sheet_name}_履歴"
    ws_history = connect_gspread().open_by_key(spreadsheet_id).worksheet(ws_history_name)

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    diffs = []
    for r in range(len(df_before)):
        for c in df_before.columns:
            before = str(df_before.loc[r, c])
            after = str(df_after.loc[r, c])
            if before != after:
                diffs.append([now, user, sheet_name, r+2, c, before, after])

    if diffs:
        ws_history.append_rows(diffs)
        st.success("✅ 変更を保存し、履歴を追加しました。")
    else:
        st.info("変更はありません。")
