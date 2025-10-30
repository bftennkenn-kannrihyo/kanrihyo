import streamlit as st
import pandas as pd
from datetime import datetime, timedelta
import gspread
from google.oauth2.service_account import Credentials

# ===============================
# 🔧 Google設定
# ===============================
SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

def connect_to_gsheet():
    scope = ["https://www.googleapis.com/auth/spreadsheets", "https://www.googleapis.com/auth/drive"]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    client = gspread.authorize(creds)
    return client

# ===============================
# 📦 データ取得
# ===============================
@st.cache_data(ttl=300)
def get_sheet_data(sheet_name):
    client = connect_to_gsheet()
    ws = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
    data = ws.get_all_records()
    df = pd.DataFrame(data)
    return df

# ===============================
# 💾 シート更新 & 履歴追加
# ===============================
def save_changes(sheet_name, edited_df, original_df, editor_name):
    try:
        client = connect_to_gsheet()
        ws = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
        ws_history = client.open_by_key(SPREADSHEET_ID).worksheet("履歴")

        updated = []
        for idx, row in edited_df.iterrows():
            if not row.equals(original_df.loc[idx]):
                for col in row.index:
                    if row[col] != original_df.loc[idx, col]:
                        ws.update_cell(idx + 2, list(edited_df.columns).index(col) + 1, str(row[col]))
                        updated.append([
                            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            sheet_name,
                            col,
                            str(original_df.loc[idx, col]),
                            str(row[col]),
                            editor_name
                        ])

        if updated:
            ws_history.append_rows(updated)
            st.success(f"✅ {len(updated)}件の変更を保存しました（編集者: {editor_name}）")
        else:
            st.info("変更はありません。")

    except Exception as e:
        st.error(f"❌ 保存エラー: {e}")

# ===============================
# 🧭 データ表示
# ===============================
def fetch_and_display(sheet_name, editor_name):
    st.markdown(f"### 📋 {sheet_name}データ（直接編集可）")

    if st.button(f"🔄 {sheet_name}データを取得", key=f"load_{sheet_name}"):
        df = get_sheet_data(sheet_name)
        st.session_state[f"{sheet_name}_data"] = df

    df = st.session_state.get(f"{sheet_name}_data", pd.DataFrame())

    if not df.empty:
        st.success(f"{len(df)}件のデータを取得しました。")

        # ✅ 表示項目の選択
        st.markdown("### ✅ 表示する項目を選択")
        selected_fields = []
        cols = st.columns(5)
        for i, col_name in enumerate(df.columns):
            with cols[i % 5]:
                if st.checkbox(col_name, value=(col_name in ["施設名", "点検予定月", "エリア"]), key=f"{sheet_name}_{col_name}"):
                    selected_fields.append(col_name)

        filtered_df = df[selected_fields] if selected_fields else df

        # ✅ 絞り込み（点検予定月・エリア）
        with st.expander("🔎 さらに絞り込み（必要な時だけ開く）"):
            month_filter = None
            area_filter = None

            if "点検予定月" in df.columns:
                months = sorted(df["点検予定月"].dropna().unique().tolist())
                month_filter = st.multiselect("点検予定月", months, default=months)

            if "エリア" in df.columns:
                areas = ["北海道","東北","北関東","東関東","東京","南関東","中部","関西","中国","四国","九州"]
                area_filter = st.multiselect("エリア", areas, default=areas)

            if month_filter:
                filtered_df = filtered_df[filtered_df["点検予定月"].isin(month_filter)]
            if area_filter:
                filtered_df = filtered_df[filtered_df["エリア"].isin(area_filter)]

        # ✅ データ編集（Excelのように）
        edited_df = st.data_editor(filtered_df, use_container_width=True, key=f"edit_{sheet_name}")

        # ✅ 保存ボタン（タイトル横）
        save_col, _ = st.columns([1, 6])
        with save_col:
            if st.button("💾 上書き保存", key=f"save_{sheet_name}"):
                save_changes(sheet_name, edited_df, filtered_df, editor_name)
    else:
        st.info("『🔄 データを取得』ボタンを押してください。")

# ===============================
# 👤 ユーザー管理（登録のみ）
# ===============================
def user_registration():
    st.header("👤 ユーザー情報登録")

    client = connect_to_gsheet()
    ws_user = client.open_by_key(SPREADSHEET_ID).worksheet("ユーザー情報")
    df_users = pd.DataFrame(ws_user.get_all_records())

    st.subheader("登録済みユーザー")
    if not df_users.empty:
        st.dataframe(df_users, use_container_width=True)
    else:
        st.info("まだ登録者がいません。")

    st.divider()
    st.subheader("新規登録")

    name = st.text_input("名前")
    email = st.text_input("メールアドレス")

    if st.button("登録"):
        if not name or not email:
            st.warning("名前とメールを入力してください。")
        else:
            ws_user.append_row([name, email, datetime.now().strftime("%Y-%m-%d %H:%M:%S")])
            st.success(f"✅ {name} さんを登録しました！")

# ===============================
# 📅 カレンダー
# ===============================
def calendar_tab():
    st.header("📅 点検スケジュール生成")

    sheet_choice = st.radio("対象シートを選択", ["医療", "生体"], horizontal=True)
    df = get_sheet_data(sheet_choice)

    if df.empty or "施設名" not in df.columns:
        st.warning("施設名が含まれたデータが見つかりません。")
        return

    if "点検予定月" in df.columns:
        months = sorted(df["点検予定月"].dropna().unique().tolist())
        selected_month = st.selectbox("📆 点検予定月を選択", months)
        df = df[df["点検予定月"] == selected_month]

    if df.empty:
        st.warning("該当するデータがありません。")
        return

    start_date = datetime(datetime.today().year, int(selected_month), 1)
    schedule = []
    day = start_date

    for _, row in df.iterrows():
        while day.weekday() >= 5:
            day += timedelta(days=1)
        schedule.append({"日付": day.strftime("%Y-%m-%d（%a）"), "施設名": row["施設名"]})
        day += timedelta(days=1)

    df_schedule = pd.DataFrame(schedule)
    st.dataframe(df_schedule, use_container_width=True)
    st.download_button("📤 CSVで保存", df_schedule.to_csv(index=False, encoding="utf-8-sig"), file_name=f"schedule_{sheet_choice}.csv")

# ===============================
# 🚀 メイン画面
# ===============================
st.set_page_config(page_title="管理表", layout="wide")
st.title("🏥 医療・生体システム管理表")

# 👤 編集者選択
st.sidebar.header("👤 編集者")
client = connect_to_gsheet()
ws_user = client.open_by_key(SPREADSHEET_ID).worksheet("ユーザー情報")
df_users = pd.DataFrame(ws_user.get_all_records())
user_list = df_users["名前"].tolist() if not df_users.empty else []
editor_name = st.sidebar.selectbox("編集者を選択", user_list)

if not editor_name:
    st.warning("左のサイドバーから編集者を選択してください。")
else:
    tabs = st.tabs(["医療", "生体", "カレンダー", "ユーザー情報"])

    with tabs[0]:
        fetch_and_display("医療", editor_name)
    with tabs[1]:
        fetch_and_display("生体", editor_name)
    with tabs[2]:
        calendar_tab()
    with tabs[3]:
        user_registration()
