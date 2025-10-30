import streamlit as st
import pandas as pd
from datetime import datetime
from google.oauth2.service_account import Credentials
import gspread

# ===== Google スプレッドシート接続 =====
SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

def connect_gspread():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    return gspread.authorize(creds)

# ===== シート操作 =====
def read_sheet(sheet_name):
    client = connect_gspread()
    ws = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
    df = pd.DataFrame(ws.get_all_records())
    return df

def write_with_history(sheet_name, edited_df, user_name):
    client = connect_gspread()
    ss = client.open_by_key(SPREADSHEET_ID)
    ws_main = ss.worksheet(sheet_name)
    ws_history = ss.worksheet(f"{sheet_name}_履歴")

    df_before = pd.DataFrame(ws_main.get_all_records())
    ws_main.clear()
    ws_main.update([edited_df.columns.values.tolist()] + edited_df.values.tolist())

    # 差分を履歴に記録
    for i in range(len(df_before)):
        for col in df_before.columns:
            before = df_before.at[i, col] if col in df_before.columns else ""
            after = edited_df.at[i, col] if col in edited_df.columns else ""
            if before != after:
                ws_history.append_row([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    user_name,
                    sheet_name,
                    i + 2,
                    col,
                    before,
                    after
                ])

# ===== 共通UI：表示・編集 =====
def display_sheet(sheet_name):
    try:
        st.markdown(f"## 📄 {sheet_name} データ管理")

        # --- ユーザー選択 ---
        client = connect_gspread()
        ws_user = client.open_by_key(SPREADSHEET_ID).worksheet("ユーザー情報")
        df_users = pd.DataFrame(ws_user.get_all_records())
        if not df_users.empty:
            user_names = df_users["氏名"].dropna().unique().tolist()
            current_user = st.sidebar.selectbox("👤 編集ユーザーを選択", user_names)
            st.session_state["current_user"] = current_user

        # --- データ取得ボタン ---
        if st.button(f"🔄 {sheet_name} データを取得", key=f"load_{sheet_name}"):
            df = read_sheet(sheet_name)
            st.session_state[f"df_{sheet_name}"] = df
            st.success(f"{sheet_name} のデータを取得しました！（{len(df)}行）")

        if f"df_{sheet_name}" not in st.session_state:
            st.info("📥 『データを取得』ボタンを押してスプレッドシートを読み込んでください。")
            return

        df = st.session_state[f"df_{sheet_name}"]

        # --- 表示項目チェック ---
        st.markdown("### ✅ 表示する項目を選択（スプレッドシートの1行目）")
        selected_fields = []
        cols = st.columns(min(5, len(df.columns)))
        for i, col in enumerate(df.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=(col == "施設名"), key=f"{sheet_name}_show_{col}"):
                    selected_fields.append(col)

        if st.button(f"📋 選択した項目で一覧表示", key=f"show_{sheet_name}"):
            if not selected_fields:
                st.warning("少なくとも1つ項目を選択してください。")
            else:
                st.session_state[f"selected_fields_{sheet_name}"] = selected_fields
                st.session_state[f"show_{sheet_name}"] = True

        if not st.session_state.get(f"show_{sheet_name}", False):
            return

        selected_fields = st.session_state.get(f"selected_fields_{sheet_name}", df.columns.tolist())
        filtered_df = df.copy()

        # --- さらに絞り込み（点検予定月・エリア）---
        with st.expander("🔍 さらに絞り込み（必要な場合のみ）", expanded=False):
            if "点検予定月" in df.columns:
                months = [f"{i}月" for i in range(1, 13)]
                selected_months = st.multiselect("点検予定月を選択", months, key=f"{sheet_name}_month")
                if selected_months:
                    filtered_df = filtered_df[filtered_df["点検予定月"].isin(selected_months)]

            if "エリア" in df.columns:
                areas = ["北海道", "東北", "北関東", "東関東", "東京", "南関東",
                         "中部", "関西", "中国", "四国", "九州"]
                selected_areas = st.multiselect("エリアを選択", areas, key=f"{sheet_name}_area")
                if selected_areas:
                    filtered_df = filtered_df[filtered_df["エリア"].isin(selected_areas)]

        # --- 一覧表示 & 保存ボタン ---
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader(f"📋 {sheet_name} データ（直接編集可）")
        with col2:
            save_clicked = st.button("💾 上書き保存", key=f"save_{sheet_name}")

        edited_df = st.data_editor(
            filtered_df[selected_fields],
            use_container_width=True,
            key=f"edit_{sheet_name}"
        )

        if save_clicked:
            write_with_history(sheet_name, edited_df, st.session_state.get("current_user", "未登録ユーザー"))
            st.success(f"✅ {sheet_name} の変更を保存しました！")

    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")

# ===== Streamlit UI =====
st.set_page_config(page_title="医療・生体システム管理表", layout="wide")
st.title("🏥 医療・生体システム管理表")

tabs = st.tabs(["医療", "生体", "カレンダー", "ユーザー情報"])

# --- 医療タブ ---
with tabs[0]:
    display_sheet("医療")

# --- 生体タブ ---
with tabs[1]:
    display_sheet("生体")

# --- カレンダー（空）---
with tabs[2]:
    st.info("📅 カレンダー機能は今後追加予定です。")

# --- ユーザー情報 ---
with tabs[3]:
    try:
        st.header("👥 ユーザー情報管理")
        client = connect_gspread()
        ws_user = client.open_by_key(SPREADSHEET_ID).worksheet("ユーザー情報")
        df_user = pd.DataFrame(ws_user.get_all_records())

        st.subheader("📋 登録ユーザー一覧")
        st.dataframe(df_user, use_container_width=True)

        with st.expander("➕ 新規ユーザー登録"):
            new_name = st.text_input("氏名")
            new_mail = st.text_input("メールアドレス")
            new_date = st.text_input("登録日時")
            if st.button("登録"):
                if new_name:
                    ws_user.append_row([new_name, new_mail, new_date])
                    st.success(f"✅ {new_name} さんを登録しました。")
                else:
                    st.warning("氏名は必須です。")

    except Exception as e:
        st.error(f"❌ ユーザー情報の読み込みエラー: {e}")
