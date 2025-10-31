import gspread
import pandas as pd
from google.oauth2.service_account import Credentials
import streamlit as st
from datetime import datetime

def connect_gspread():
    """Googleスプレッドシートに接続"""
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=300)  # 5分間キャッシュ
def load_sheet(spreadsheet_id, sheet_name):
    """スプレッドシートのデータを取得（キャッシュ対応）"""
    client = connect_gspread()
    ws = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    df = pd.DataFrame(ws.get_all_records())
    return ws, df

def save_with_history(sheet_name, df_before, df_after, user):
    """変更を保存して履歴に追記"""
    from datetime import datetime
    client = connect_gspread()
    ss = client.open(sheet_name)
    ws = ss.worksheet(sheet_name)
    ws.update([df_after.columns.values.tolist()] + df_after.values.tolist())

    # 履歴シートに追記
    history_sheet = f"{sheet_name}_履歴"
    try:
        ws_history = ss.worksheet(history_sheet)
    except:
        ws_history = ss.add_worksheet(title=history_sheet, rows="1000", cols="10")

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    diffs = []
    for i in range(len(df_before)):
        for col in df_before.columns:
            before = str(df_before.at[i, col])
            after = str(df_after.at[i, col])
            if before != after:
                diffs.append([now, user, sheet_name, i + 2, col, before, after])

    if diffs:
        ws_history.append_rows(diffs)
