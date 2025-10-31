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

def save_with_history(sheet_name, df_before, df_after, user, spreadsheet_id):
    import gspread
    from datetime import datetime
    from google.oauth2.service_account import Credentials
    import streamlit as st

    # --- Google認証 ---
    scope = ["https://www.googleapis.com/auth/spreadsheets",
             "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    client = gspread.authorize(creds)

    ws = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    ws.update([df_after.columns.values.tolist()] + df_after.values.tolist())

    # --- 履歴用ワークシート ---
    history_name = f"{sheet_name}_履歴"
    ws_history = client.open_by_key(spreadsheet_id).worksheet(history_name)

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
