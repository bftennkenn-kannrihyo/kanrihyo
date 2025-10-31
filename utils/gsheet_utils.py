import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import streamlit as st

SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

def connect_gspread():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    return gspread.authorize(creds)

def get_worksheet(sheet_name):
    client = connect_gspread()
    return client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)

def load_sheet(sheet_name):
    ws = get_worksheet(sheet_name)
    df = pd.DataFrame(ws.get_all_records())
    return ws, df

def save_with_history(sheet_name, df_before, df_after, user):
    ws = get_worksheet(sheet_name)
    ws.update([df_after.columns.values.tolist()] + df_after.values.tolist())

    # 履歴シートに記録
    ws_history_name = f"{sheet_name}_履歴"
    ws_history = get_worksheet(ws_history_name)
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
