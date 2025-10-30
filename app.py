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

# ✅ 履歴に残すユーザー名
user_name = st.text_input("編集者名（履歴に残します）", value=st.session_state.get("user_name", ""))
st.session_state["user_name"] = user_name.strip() or "不明なユーザー"

tabs = st.tabs(["医療", "生体", "カレンダー"])

# ======================================
# Googleスプレッドシート接続
# ======================================
SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

def connect_to_gsheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    return gspread.authorize(creds)

# ======================================
# 差分抽出関数
# ======================================
def compare_dataframes(old_df, new_df):
    diffs = []
    max_len = max(len(old_df), len(new_df))
    old = old_df.reindex(range(max_len)).fillna("")
    new = new_df.reindex(range(max_len)).fillna("")
    common_cols = [c for c in new.columns if c in old.columns]
    for i in range(max_len):
        for col in common_cols:
            old_val = str(old.iloc[i][col])
            new_val = str(new.iloc[i][col])
            if old_val != new_val:
                diffs.append({
                    "row": i + 1,
                    "col": col,
                    "before": old_val,
                    "after": new_val
                })
    return diffs

# ======================================
# 履歴シートに追記
# ======================================
def append_history(sheet_name, user, diffs):
    client = connect_to_gsheet()
    sh = client.open_by_key(SPREADSHEET_ID)
    log_title = f"{sheet_name}_履歴"
    try:
        log_ws = sh.worksheet(log_title)
    except gspread.exceptions.WorksheetNotFound:
        log_ws = sh.add_worksheet(title=log_title, rows="1000", cols="7")
        log_ws.append_row(["日時", "ユーザー", "対象シート", "行", "列", "変更前", "変更後"])

    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    rows = [[now, user, sheet_name, d["row"], d["col"], d["before"], d["after"]] for d in diffs]
    if rows:
        for i in range(0, len(rows), 100):
            log_ws.append_rows(rows[i:i+100], value_input_option="USER_ENTERED")

# ======================================
# 保存処理（絞り込み後編集対応：キー一致で部分更新）
# ======================================
def save_to_gsheet(sheet_name, session_key, user):
    try:
        client = connect_to_gsheet()
        sh = client.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet(sheet_name)

        displayed = st.session_state.get(session_key)
        full_original = st.session_state.get(f"{session_key}_full")

        if displayed is None or full_original is None:
            st.error("元データが見つかりません。『データを取得』を押してください。")
            return

        # ✅ 施設名（またはユニークなID列）をキーにマージ更新
        key_col = "施設名"  # 一意のキーが別にあるならここを変更
        if key_col not in full_original.columns or key_col not in displayed.columns:
            st.error("『施設名』列が見つかりません。キー列を確認してください。")
            return

        # 元データのコピー
        merged = full_original.copy()

        # 同じ施設名の行を上書き
        for _, row in displayed.iterrows():
            key_val = row[key_col]
            mask = merged[key_col] == key_val
            if mask.any():
                for col in displayed.columns:
                    merged.loc[mask, col] = row[col]

        # 差分抽出
        current_full = pd.DataFrame(ws.get_all_records())
        diffs = compare_dataframes(current_full, merged)

        # 保存
        header = merged.columns.tolist()
        values = merged.fillna("").astype(str).values.tolist()
        ws.clear()
        ws.update([header] + values, value_input_option="USER_ENTERED")

        st.success("✅ 編集した行だけスプレッドシートに反映しました！")

        # 履歴追記
        if diffs:
            append_history(sheet_name, user, diffs)
            st.info(f"📝 {len(diffs)}件の変更を履歴シートに保存しました。")
        else:
            st.info("変更はありませんでした。")

    except Exception as e:
        st.error(f"❌ 保存中にエラー: {e}")

# ======================================
# 保存処理（履歴シートのみ追記・非表示列保持）
# ======================================
def save_to_gsheet(sheet_name, session_key, user):
    try:
        client = connect_to_gsheet()
        sh = client.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet(sheet_name)

        displayed = st.session_state.get(session_key)
        full_original = st.session_state.get(f"{session_key}_full")

        if displayed is None or full_original is None:
            st.error("元データが見つかりません。『データを取得』を押してください。")
            return

        current_full = pd.DataFrame(ws.get_all_records())

        # 表示している列だけ更新（非表示列は保持）
        merged = current_full.copy()
        for col in displayed.columns:
            if col in merged.columns:
                merged.loc[:len(displayed)-1, col] = displayed[col].values
            else:
                merged[col] = ""
                merged.loc[:len(displayed)-1, col] = displayed[col].values

        # 差分抽出
        diffs = compare_dataframes(current_full, merged)

        # 保存
        header = merged.columns.tolist()
        values = merged.fillna("").astype(str).values.tolist()
        ws.clear()
        ws.update([header] + values, value_input_option="USER_ENTERED")
        st.success("✅ スプレッドシートに上書き保存しました（非表示列も保持）")

        # 履歴のみ追記
        if diffs:
            append_history(sheet_name, user, diffs)
            st.info(f"📝 {len(diffs)}件の変更を履歴シートに保存しました。")
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
        with st.form("iryo_form"):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.subheader("📋 医療データ（直接編集可）")
            with col2:
                save_iryo = st.form_submit_button("☁️ 上書き保存")

            edited = st.data_editor(
                st.session_state["iryo_df"],
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
            )
            st.session_state["iryo_df"] = edited

            if save_iryo:
                save_to_gsheet("医療", "iryo_df", st.session_state["user_name"])

# ======================================
# 生体タブ
# ======================================
with tabs[1]:
    st.header("🧬 生体システム管理表")
    fetch_sheet_data("生体", "seitai_df")

    if "seitai_df" in st.session_state:
        with st.form("seitai_form"):
            col1, col2 = st.columns([5, 1])
            with col1:
                st.subheader("📋 生体データ（直接編集可）")
            with col2:
                save_seitai = st.form_submit_button("☁️ 上書き保存")

            edited = st.data_editor(
                st.session_state["seitai_df"],
                use_container_width=True,
                hide_index=True,
                num_rows="dynamic",
            )
            st.session_state["seitai_df"] = edited

            if save_seitai:
                save_to_gsheet("生体", "seitai_df", st.session_state["user_name"])

# ======================================
# カレンダー
# ======================================
with tabs[2]:
    st.header("📅 点検スケジュール生成")
    facilities_text = st.text_area("施設名（スプレッドシートからコピペ可）", height=200)
    if st.button("スケジュールを生成"):
        facilities = [h.strip() for h in facilities_text.splitlines() if h.strip()]
        today = datetime.today().replace(day=1)
        schedule, day = [], today
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
