import streamlit as st
import gspread
import pandas as pd
from google.oauth2.service_account import Credentials

@st.cache_data(ttl=60)
def connect_gspread():
    """Googleスプレッドシートへ接続（キャッシュ付き）"""
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    return gspread.authorize(creds)

@st.cache_data(ttl=60)
def load_sheet(spreadsheet_id, sheet_name):
    """シートをDataFrameで読み込み（キャッシュ付き）"""
    client = connect_gspread()
    ws = client.open_by_key(spreadsheet_id).worksheet(sheet_name)
    df = pd.DataFrame(ws.get_all_records())
    return ws, df
