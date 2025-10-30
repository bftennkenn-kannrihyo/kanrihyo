import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ======================================
# 基本設定
# ======================================
st.set_page_config(page_title="管理表", layout="wide")
st.title("🏥 管理表")

tabs = st.tabs(["医療", "生体", "カレンダー"])

# ======================================
# Googleスプレッドシート接続
# ======================================
def connect_to_gsheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    return gspread.authorize(creds)

SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

# ======================================
# 差分抽出関数（どこを変更したか）
# ======================================
def compare_dataframes(old_df, new_df):
    diffs = []
    for col in new_df.columns:
        if col not in old_df.columns:
            continue
        for i in range(len(new_df)):
            old_val = str(old_df.iloc[i][col]) if i < len(old_df) else ""
            new_val = str(new_df.iloc[i][col])
            if old_val != new_val:
                diffs.append({"行": i + 1, "列": col, "変更前": old_val, "変更後": new_val})
    return diffs

# ======================================
# 履歴保存（差分含む）
# ======================================
def save_edit_history(sheet_name, user, diffs):
    client = connect_to_gsheet()
    log_sheet_name = f"{sheet_name}_履歴"
    try:
        log_sheet = client.open_by_key(SPREADSHEET_ID).worksheet(log_sheet_name)
    except gspread.exceptions.WorksheetNotFound:
        log_sheet = client.open_by_key(SPREADSHEET_ID).add_worksheet(title=log_sheet_name, rows="1000", cols="6")
        log_sheet.append_row(["日時", "ユーザー", "対象シート", "行", "列", "変更前", "変更後"])

    for diff in diffs:
        log_sheet.append_row([
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            user,
            sheet_name,
            diff["行"],
            diff["列"],
            diff["変更前"],
            diff["変更後"]
        ])

# ======================================
# 共通：列選択＋データ取得
# ======================================
def fetch_sheet_data(sheet_name, session_key):
    st.markdown("### ✅ 表示する項目を選択")

    try:
        client = connect_to_gsheet()
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
        columns = sheet.row_values(1)
        all_data = sheet.get_all_records()
        full_df = pd.DataFrame(all_data)
    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")
        st.stop()

    cols = st.columns(min(5, len(columns)))
    selected_cols = []
    for i, col in enumerate(columns):
        with cols[i % len(cols)]:
            if st.checkbox(col, value=True, key=f"{sheet_name}_col_{col}"):
                selected_cols.append(col)

    if st.button(f"🔄 スプレッドシートから最新データを取得（{sheet_name}）"):
        st.session_state[f"{session_key}_full"] = full_df  # 全データ保持
        if selected_cols:
            df = full_df[selected_cols].copy()
        else:
            df = full_df.copy()
        st.session_state[session_key] = df
        st.success(f"✅ {len(df)}件のデータを取得しました。")

# ======================================
# 共通：保存処理（非表示列も保持）
# ======================================
def save_to_gsheet(sheet_name, displayed_df, session_key, user="不明なユーザー"):
    try:
        client = connect_to_gsheet()
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)

        # 元データ取得
        full_df = st.session_state.get(f"{session_key}_full")
        if full_df is None or full_df.empty:
            st.error("元データが見つかりません。再取得してください。")
            return

        # 非表示列を維持（表示している列だけ更新）
        for col in displayed_df.columns:
            full_df[col] = displayed_df[col]

        # 差分を抽出
        old_df = pd.DataFrame(sheet.get_all_records())
        diffs = compare_dataframes(old_df, full_df)

        # 更新実行
        data = [full_df.columns.tolist()] + full_df.fillna("").values.tolist()
        sheet.clear()
        sheet.update(data)
        st.success("✅ スプレッドシートに上書き保存しました（非表示列も保持）")

        # 履歴記録
        if diffs:
            save_edit_history(sheet_name, user, diffs)
            st.info(f"📝 {len(diffs)}件の変更を履歴に保存しました。")
        else:
            st.info("変更はありませんでした。")

    except Exception as e:
        st.error(f"❌ 保存中にエラー: {e}")

# ======================================
# 医療タブ
# ======================================
with tabs[0]:
    st.header("🩺 医療システム管理表")

    fetch_sheet_data("医療", "iryo_df")

    if "iryo_df" in st.session_state:
        # タイトル＋ボタンを横並びに
        col1, col2 = st.columns([5, 1])
        with col1:
            st.subheader("📋 医療データ（直接編集可）")
        with col2:
            if st.button("☁️ 上書き保存", key="save_iryo"):
                save_to_gsheet("医療", st.session_state["iryo_df"], "iryo_df")

        edited_df = st.data_editor(
            st.session_state["iryo_df"],
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
        )
        st.session_state["iryo_df"] = edited_df

# ======================================
# 生体タブ
# ======================================
with tabs[1]:
    st.header("🧬 生体システム管理表")

    fetch_sheet_data("生体", "seitai_df")

    if "seitai_df" in st.session_state:
        col1, col2 = st.columns([5, 1])
        with col1:
            st.subheader("📋 生体データ（直接編集可）")
        with col2:
            if st.button("☁️ 上書き保存", key="save_seitai"):
                save_to_gsheet("生体", st.session_state["seitai_df"], "seitai_df")

        edited_df = st.data_editor(
            st.session_state["seitai_df"],
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
        )
        st.session_state["seitai_df"] = edited_df

# ======================================
# カレンダータブ
# ======================================
with tabs[2]:
    st.header("📅 点検スケジュール生成")
    facilities_text = st.text_area("施設名（スプレッドシートからコピペ可）", height=200)
    if st.button("スケジュールを生成"):
        facilities = [h.strip() for h in facilities_text.splitlines() if h.strip()]
        today = datetime.today().replace(day=1)
        schedule = []
        day = today
        for h in facilities:
            while day.weekday() >= 5:
                day += timedelta(days=1)
            schedule.append({"日付": day.strftime("%Y-%m-%d（%a）"), "施設名": h})
            day += timedelta(days=1)
        df_sch = pd.DataFrame(schedule)
        st.dataframe(df_sch, use_container_width=True)
        st.download_button(
            "スケジュールをCSVで保存",
            data=df_sch.to_csv(index=False, encoding="utf-8-sig"),
            file_name="schedule.csv",
            mime="text/csv"
        )
