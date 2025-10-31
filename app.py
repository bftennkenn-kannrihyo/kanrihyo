import streamlit as st
from utils.gsheet_utils import read_sheet
from pages import medical_page, bio_page, calendar_page, user_page

st.set_page_config(page_title="医療・生体システム管理表", layout="wide")
st.title("🏥 医療・生体システム管理表")

# ===============================
# 👤 サイドバー：編集者選択
# ===============================
st.sidebar.header("👤 編集者")
try:
    df_user = read_sheet("ユーザー情報")
    user_list = df_user["名前"].dropna().unique().tolist()
    if not user_list:
        st.sidebar.warning("登録済みユーザーがいません。")
        current_user = "未登録ユーザー"
    else:
        current_user = st.sidebar.selectbox("編集者を選択", user_list)
        st.session_state["current_user"] = current_user
except Exception:
    st.sidebar.error("ユーザー情報の読み込みに失敗しました。")
    current_user = "未登録ユーザー"

# ===============================
# タブ構成
# ===============================
tabs = st.tabs(["💊 医療", "🧬 生体", "📅 カレンダー", "👤 ユーザー情報"])

with tabs[0]:
    medical_page.run(current_user)

with tabs[1]:
    bio_page.run(current_user)

with tabs[2]:
    calendar_page.run()

with tabs[3]:
    user_page.run()
