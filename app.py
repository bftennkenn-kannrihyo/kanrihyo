import streamlit as st
from pages.medical_page import medical_tab
from pages.bio_page import bio_tab
from pages.user_page import user_tab
from pages.calendar_page import calendar_tab
from utils.gsheet_utils import connect_gspread, load_sheet

# --- Google スプレッドシート設定 ---
SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

# --- ユーザー情報 ---
client = connect_gspread()
ws_user, df_users = load_sheet(SPREADSHEET_ID, "ユーザー情報")
user_names = df_users["名前"].dropna().unique().tolist()
current_user = st.sidebar.selectbox("👤 編集ユーザーを選択", user_names)

# --- タブ構成 ---
tabs = st.tabs(["医療", "生体", "カレンダー", "ユーザー情報"])

with tabs[0]:
    medical_tab(SPREADSHEET_ID, current_user)

with tabs[1]:
    bio_tab(SPREADSHEET_ID, current_user)

with tabs[2]:
    calendar_tab(SPREADSHEET_ID, current_user)

with tabs[3]:
    user_tab(SPREADSHEET_ID, current_user)
