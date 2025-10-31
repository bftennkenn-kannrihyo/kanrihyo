import streamlit as st
from utils.gsheet_utils import connect_gspread, load_sheet
from pages.medical_page import medical_tab
from pages.bio_page import bio_tab
from pages.calendar_page import calendar_tab
from pages.user_page import user_tab

# ===== Streamlit 設定 =====
st.set_page_config(page_title="医療・生体システム管理表", layout="wide")
st.title("🏥 医療・生体システム管理表")

# ===== スプレッドシート設定 =====
SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

# ===== ユーザー選択 =====
try:
    client = connect_gspread()

    # ✅ ここでは「列名＋ユーザー一覧」だけ取得する（データ全件ではない）
    ws_user, df_users = load_sheet(SPREADSHEET_ID, "ユーザー情報")

    if "名前" not in df_users.columns:
        st.sidebar.error("❌ 『名前』列が見つかりません。")
        st.stop()

    # ✅ サイドバーにユーザー選択を表示
    user_names = df_users["名前"].dropna().unique().tolist()
    current_user = st.sidebar.selectbox("👤 編集ユーザーを選択", user_names)
    st.session_state["current_user"] = current_user

except Exception as e:
    st.sidebar.error(f"ユーザー情報の取得に失敗しました: {e}")
    st.stop()

# ===== タブ構成 =====
tabs = st.tabs(["医療", "生体", "カレンダー", "ユーザー情報"])

# --- 医療 ---
with tabs[0]:
    medical_tab(SPREADSHEET_ID, current_user)

# --- 生体 ---
with tabs[1]:
    bio_tab(SPREADSHEET_ID, current_user)

# --- カレンダー ---
with tabs[2]:
    calendar_tab(SPREADSHEET_ID, current_user)

# --- ユーザー情報 ---
with tabs[3]:
    user_tab(SPREADSHEET_ID, current_user)
