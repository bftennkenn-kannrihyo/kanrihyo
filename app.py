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

# ===== フィルタ関数（点検予定月・エリア） =====
def apply_extra_filters(df):
    with st.expander("🔎 さらに絞り込み（必要なときだけ開く）", expanded=False):
        filtered_df = df.copy()

        if "点検予定月" in df.columns:
            months = [str(i) for i in range(1, 13)]
            selected_months = st.multiselect("点検予定月を選択", months)
            if selected_months:
                filtered_df = filtered_df[filtered_df["点検予定月"].astype(str).isin(selected_months)]

        if "エリア" in df.columns:
            areas = ["北海道", "東北", "北関東", "東関東", "東京", "南関東",
                     "中部", "関西", "中国", "四国", "九州"]
            selected_areas = st.multiselect("エリアを選択", areas)
            if selected_areas:
                filtered_df = filtered_df[filtered_df["エリア"].isin(selected_areas)]

        return filtered_df


# ===== メインタブ =====
tabs = st.tabs(["医療", "生体", "カレンダー"])


# =====================
# 🏥 医療データ
# =====================
with tabs[0]:
    st.header("🏥 医療 データ管理")
    try:
        ws_med, df_med = load_sheet("医療")

        st.markdown("### ✅ 表示する項目を選択（チェックした列のみ表示）")
        selected_fields = []
        cols = st.columns(min(5, len(df_med.columns)))
        for i, col in enumerate(df_med.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=(col in ["施設名", "点検予定月", "エリア"])):
                    selected_fields.append(col)

        if st.button("📄 データを取得", key="get_med"):
            st.session_state["filtered_med"] = df_med[selected_fields]

        if "filtered_med" in st.session_state:
            filtered_df = st.session_state["filtered_med"]
            filtered_df = apply_extra_filters(filtered_df)  # 絞り込み

            st.subheader("📋 医療データ（直接編集可）")
            st.markdown("💾 下のボタンで上書き保存（履歴に残ります）")

            edited_df = st.data_editor(filtered_df, use_container_width=True, key="edit_医療")

            if st.button("💾 上書き保存（履歴に記録）", key="save_医療"):
                save_changes_with_history("医療", ws_med, df_med, edited_df, st.session_state["current_user"])

    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")


# =====================
# 🧬 生体データ
# =====================
with tabs[1]:
    st.header("🧬 生体 データ管理")
    try:
        ws_bio, df_bio = load_sheet("生体")

        st.markdown("### ✅ 表示する項目を選択（チェックした列のみ表示）")
        selected_fields = []
        cols = st.columns(min(5, len(df_bio.columns)))
        for i, col in enumerate(df_bio.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=(col in ["施設名", "点検予定月", "エリア"]), key=f"bio_{col}"):
                    selected_fields.append(col)

        if st.button("📄 データを取得", key="get_bio"):
            st.session_state["filtered_bio"] = df_bio[selected_fields]

        if "filtered_bio" in st.session_state:
            filtered_df = st.session_state["filtered_bio"]
            filtered_df = apply_extra_filters(filtered_df)  # 絞り込み

            st.subheader("📋 生体データ（直接編集可）")
            st.markdown("💾 下のボタンで上書き保存（履歴に残ります）")

            edited_df = st.data_editor(filtered_df, use_container_width=True, key="edit_生体")

            if st.button("💾 上書き保存（履歴に記録）", key="save_生体"):
                save_changes_with_history("生体", ws_bio, df_bio, edited_df, st.session_state["current_user"])

    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")


# =====================
# 📅 カレンダー（仮）
# =====================
with tabs[2]:
    st.header("📅 カレンダー（準備中）")
    st.info("後でスケジュール生成機能を追加します。")
