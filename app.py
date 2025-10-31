import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ===============================
# Google スプレッドシート接続
# ===============================
SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

def connect_to_gsheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    client = gspread.authorize(creds)
    return client

def read_sheet(sheet_name):
    """スプレッドシートから読み込み"""
    client = connect_to_gsheet()
    ws = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
    data = ws.get_all_records()
    return pd.DataFrame(data)

# ===============================
# 変更検出＋履歴書き込み
# ===============================
def write_with_history(sheet_name, new_df, user):
    client = connect_to_gsheet()
    ss = client.open_by_key(SPREADSHEET_ID)
    ws = ss.worksheet(sheet_name)
    old_df = pd.DataFrame(ws.get_all_records())

    changes = []
    for i in range(min(len(new_df), len(old_df))):
        for col in new_df.columns:
            old_val = str(old_df.at[i, col]) if col in old_df.columns else ""
            new_val = str(new_df.at[i, col])
            if old_val != new_val:
                changes.append([
                    datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    user,
                    sheet_name,
                    i + 2,
                    col,
                    old_val,
                    new_val
                ])

    ws.clear()
    ws.update([new_df.columns.values.tolist()] + new_df.fillna("").values.tolist())

    if changes:
        log_name = f"{sheet_name}_履歴"
        try:
            ws_log = ss.worksheet(log_name)
        except gspread.WorksheetNotFound:
            ws_log = ss.add_worksheet(title=log_name, rows=1000, cols=10)
            ws_log.append_row(["日時", "ユーザー", "対象シート", "行", "列", "変更前", "変更後"])
        ws_log.append_rows(changes)

# ===============================
# Streamlit 設定
# ===============================
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
        st.sidebar.warning("登録済みユーザーがいません。『ユーザー情報』タブで登録してください。")
        current_user = "未登録ユーザー"
    else:
        current_user = st.sidebar.selectbox("編集者を選択", user_list)
        st.session_state["current_user"] = current_user
except Exception:
    st.sidebar.error("ユーザー情報の読み込みに失敗しました。")
    current_user = "未登録ユーザー"

# ===============================
# タブ設定
# ===============================
tabs = st.tabs(["💊 医療", "🧬 生体", "📅 カレンダー", "👤 ユーザー情報"])

# ===============================
# 共通：データ表示＋編集機能
# ===============================
def display_sheet(sheet_name):
    try:
        df = read_sheet(sheet_name)

        st.markdown("### ✅ 表示する項目を選択")
        selected_fields = []
        cols = st.columns(min(5, len(df.columns)))
        for i, col in enumerate(df.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=True, key=f"{sheet_name}_{col}"):
                    selected_fields.append(col)

        # 絞り込み
        filter_active = st.checkbox("🔎 さらに絞り込みをする", value=False, key=f"filter_{sheet_name}")
        if filter_active:
            if "点検予定月" in df.columns:
                months = [f"{i}月" for i in range(1, 13)]
                selected_months = st.multiselect("点検予定月を選択", months, key=f"{sheet_name}_month")
                if selected_months:
                    df = df[df["点検予定月"].isin(selected_months)]
            if "エリア" in df.columns:
                areas = ["北海道","東北","北関東","東関東","東京","南関東",
                         "中部","関西","中国","四国","九州"]
                selected_areas = st.multiselect("エリアを選択", areas, key=f"{sheet_name}_area")
                if selected_areas:
                    df = df[df["エリア"].isin(selected_areas)]

        # 上書きボタン
        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader(f"📋 {sheet_name}データ（直接編集可）")
        with col2:
            if st.button("💾 上書き保存", key=f"save_{sheet_name}"):
                edited_df = st.session_state.get(f"edit_{sheet_name}", df)
                write_with_history(sheet_name, edited_df, current_user)
                st.success(f"✅ {sheet_name}の変更を保存しました（編集者: {current_user}）")

        edited_df = st.data_editor(df[selected_fields], use_container_width=True, key=f"edit_{sheet_name}")
        st.session_state[f"edit_{sheet_name}"] = edited_df

    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")

# ===============================
# 医療タブ
# ===============================
with tabs[0]:
    st.header("💊 医療システム管理表")
    display_sheet("医療")

# ===============================
# 生体タブ
# ===============================
with tabs[1]:
    st.header("🧬 生体システム管理表")
    display_sheet("生体")

# ===============================
# カレンダータブ
# ===============================
with tabs[2]:
    st.header("📅 点検スケジュール生成")

    try:
        sheet_choice = st.radio("対象シートを選択", ["医療", "生体"], horizontal=True)
        df = read_sheet(sheet_choice)

        if "施設名" not in df.columns:
            st.warning("施設名の列が見つかりません。")
        else:
            if "点検予定月" in df.columns:
                months = sorted(df["点検予定月"].dropna().unique().tolist())
                selected_month = st.selectbox("📆 点検予定月を選択", months)
                df = df[df["点検予定月"] == selected_month]

            if not df.empty:
                start_date = datetime(datetime.today().year, int(selected_month.replace("月", "")), 1)
                schedule = []
                day = start_date
                for _, row in df.iterrows():
                    while day.weekday() >= 5:
                        day += timedelta(days=1)
                    schedule.append({"日付": day.strftime("%Y-%m-%d（%a）"), "施設名": row["施設名"]})
                    day += timedelta(days=1)

                df_schedule = pd.DataFrame(schedule)
                st.dataframe(df_schedule, use_container_width=True)
                st.download_button(
                    "📤 CSVで保存",
                    df_schedule.to_csv(index=False, encoding="utf-8-sig"),
                    file_name=f"schedule_{sheet_choice}.csv",
                    mime="text/csv"
                )
            else:
                st.info("選択した月に該当するデータがありません。")
    except Exception as e:
        st.error(f"❌ カレンダー生成エラー: {e}")

# ===============================
# ユーザー情報タブ（以前の仕様）
# ===============================
with tabs[3]:
    st.header("👤 ユーザー情報")
    try:
        df_user = read_sheet("ユーザー情報")
        st.dataframe(df_user, use_container_width=True)

        with st.expander("➕ 新しいユーザーを登録"):
            with st.form("user_form"):
                name = st.text_input("氏名")
                dept = st.text_input("部署")
                email = st.text_input("メールアドレス")
                submitted = st.form_submit_button("登録")

                if submitted and name:
                    new_user = pd.DataFrame([[name, dept, email]], columns=df_user.columns)
                    client = connect_to_gsheet()
                    ws = client.open_by_key(SPREADSHEET_ID).worksheet("ユーザー情報")
                    ws.append_rows(new_user.values.tolist())
                    st.session_state["current_user"] = name
                    st.success(f"✅ ユーザー「{name}」を登録しました。")
    except Exception as e:
        st.error(f"❌ ユーザー情報取得エラー: {e}")
