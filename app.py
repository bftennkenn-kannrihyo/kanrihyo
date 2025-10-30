import streamlit as st
import pandas as pd
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# ===== Streamlit 設定 =====
st.set_page_config(page_title="医療・生体システム管理表", layout="wide")
st.title("🏥 医療・生体システム管理表")

# ===== Google スプレッドシート設定 =====
SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

def connect_gspread():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    return gspread.authorize(creds)

# ===== ユーザー選択（サイドバー） =====
try:
    client = connect_gspread()
    ws_user = client.open_by_key(SPREADSHEET_ID).worksheet("ユーザー情報")
    df_users = pd.DataFrame(ws_user.get_all_records())

    if "名前" not in df_users.columns:
        st.sidebar.error("❌ ユーザー情報シートに『名前』列が見つかりません。")
        st.stop()

    user_names = df_users["名前"].dropna().unique().tolist()
    current_user = st.sidebar.selectbox("👤 編集ユーザーを選択", user_names)
    st.session_state["current_user"] = current_user

except Exception as e:
    st.sidebar.error(f"ユーザー情報の取得に失敗しました: {e}")
    st.stop()


# ===== 共通関数 =====
def get_worksheet(sheet_name):
    client = connect_gspread()
    return client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)

def load_sheet(sheet_name):
    ws = get_worksheet(sheet_name)
    df = pd.DataFrame(ws.get_all_records())
    return ws, df

def save_changes_with_history(sheet_name, ws, df_before, df_after, user):
    ws.update([df_after.columns.values.tolist()] + df_after.values.tolist())

    ws_history_name = f"{sheet_name}_履歴"
    ws_history = get_worksheet(ws_history_name)

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


# ===== メインタブ =====
tabs = st.tabs(["医療", "生体", "カレンダー"])


# =====================
# 🏥 医療データ
# =====================
with tabs[0]:
    st.header("🏥 医療")
    try:
        ws_med, df_med = load_sheet("医療")

        # --- 表示列チェック ---
        st.markdown("### ✅ 表示する項目を選択（チェックした列のみ表示）")
        selected_fields = []
        cols = st.columns(min(5, len(df_med.columns)))
        for i, col in enumerate(df_med.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=(col in ["施設名", "点検予定月", "エリア"]), key=f"med_{col}"):
                    selected_fields.append(col)

        # --- 絞り込み設定（まだ反映しない）---
        st.markdown("### 🔎 さらに絞り込み（必要な場合）")
        filter_options = {}
        if "点検予定月" in df_med.columns:
            months = [str(i) for i in range(1, 13)]
            filter_options["months"] = st.multiselect("点検予定月を選択", months, key="med_months")

        if "エリア" in df_med.columns:
            areas = ["北海道", "東北", "北関東", "東関東", "東京", "南関東",
                     "中部", "関西", "中国", "四国", "九州"]
            filter_options["areas"] = st.multiselect("エリアを選択", areas, key="med_areas")

        # --- データを取得ボタン ---
        if st.button("📄 データを取得", key="get_med"):
            filtered_df = df_med.copy()

            # 1️⃣ 表示列を限定
            if selected_fields:
                filtered_df = filtered_df[selected_fields]

            # 2️⃣ ボタンを押したタイミングで絞り込みを適用
            if "months" in filter_options and filter_options["months"]:
                filtered_df = filtered_df[filtered_df["点検予定月"].astype(str).isin(filter_options["months"])]
            if "areas" in filter_options and filter_options["areas"]:
                filtered_df = filtered_df[filtered_df["エリア"].isin(filter_options["areas"])]

            st.session_state["filtered_med"] = filtered_df

        # --- 一覧表示 ---
        if "filtered_med" in st.session_state:
            st.subheader("📋 医療一覧")
            edited_df = st.data_editor(st.session_state["filtered_med"], use_container_width=True, key="edit_医療")

            if st.button("💾 上書き保存", key="save_医療"):
                save_changes_with_history("医療", ws_med, df_med, edited_df, st.session_state["current_user"])

    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")


# =====================
# 🧬 生体データ
# =====================
with tabs[1]:
    st.header("🧬 生体")
    try:
        ws_bio, df_bio = load_sheet("生体")

        # --- 表示列チェック ---
        st.markdown("### ✅ 表示する項目を選択（チェックした列のみ表示）")
        selected_fields = []
        cols = st.columns(min(5, len(df_bio.columns)))
        for i, col in enumerate(df_bio.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=(col in ["施設名", "点検予定月", "エリア"]), key=f"bio_{col}"):
                    selected_fields.append(col)

        # --- 絞り込み設定（まだ反映しない）---
        st.markdown("### 🔎 さらに絞り込み（必要な場合）")
        filter_options = {}
        if "点検予定月" in df_bio.columns:
            months = [str(i) for i in range(1, 13)]
            filter_options["months"] = st.multiselect("点検予定月を選択", months, key="bio_months")

        if "エリア" in df_bio.columns:
            areas = ["北海道", "東北", "北関東", "東関東", "東京", "南関東",
                     "中部", "関西", "中国", "四国", "九州"]
            filter_options["areas"] = st.multiselect("エリアを選択", areas, key="bio_areas")

        # --- データを取得ボタン ---
        if st.button("📄 データを取得", key="get_bio"):
            filtered_df = df_bio.copy()

            # 1️⃣ 表示列を限定
            if selected_fields:
                filtered_df = filtered_df[selected_fields]

            # 2️⃣ 絞り込み反映
            if "months" in filter_options and filter_options["months"]:
                filtered_df = filtered_df[filtered_df["点検予定月"].astype(str).isin(filter_options["months"])]
            if "areas" in filter_options and filter_options["areas"]:
                filtered_df = filtered_df[filtered_df["エリア"].isin(filter_options["areas"])]

            st.session_state["filtered_bio"] = filtered_df

        # --- 一覧表示 ---
        if "filtered_bio" in st.session_state:
            st.subheader("📋 生体一覧")
            edited_df = st.data_editor(st.session_state["filtered_bio"], use_container_width=True, key="edit_生体")

            if st.button("💾 上書き保存", key="save_生体"):
                save_changes_with_history("生体", ws_bio, df_bio, edited_df, st.session_state["current_user"])

    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")

# =====================
# 👤 ユーザー情報
# =====================
tabs = st.tabs(["医療", "生体", "カレンダー", "ユーザー情報"])

with tabs[3]:
    st.header("👤 ユーザー情報")

    try:
        ws_user = get_worksheet("ユーザー情報")
        df_users = pd.DataFrame(ws_user.get_all_records())

        st.subheader("📋 登録ユーザー一覧")
        edited_users = st.data_editor(
            df_users,
            use_container_width=True,
            key="edit_users"
        )

        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("💾 上書き保存（ユーザー情報）", key="save_users"):
                ws_user.update([edited_users.columns.values.tolist()] + edited_users.values.tolist())
                st.success("✅ ユーザー情報を更新しました！")

        with col2:
            with st.expander("➕ 新規ユーザーを登録"):
                with st.form("add_user_form", clear_on_submit=True):
                    new_name = st.text_input("名前")
                    new_dept = st.text_input("所属（任意）")
                    new_mail = st.text_input("メールアドレス（任意）")
                    submitted = st.form_submit_button("登録")

                    if submitted and new_name.strip():
                        new_row = {"名前": new_name, "所属": new_dept, "メールアドレス": new_mail}
                        ws_user.append_row(list(new_row.values()))
                        st.success(f"✅ 新規ユーザー『{new_name}』を登録しました！")
                        st.rerun()

    except Exception as e:
        st.error(f"❌ ユーザー情報の取得に失敗しました: {e}")

# =====================
# 📅 カレンダー（仮）
# =====================
with tabs[2]:
    st.header("📅 カレンダー（準備中）")
    st.info("後でスケジュール生成機能を追加します。")
