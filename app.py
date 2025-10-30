import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime, timedelta

# ============== 基本設定 ==============
st.set_page_config(page_title="管理表", layout="wide")
st.title("🏥 管理表")

# ✅ ユーザー名（履歴用）：未入力なら「不明なユーザー」
user_name = st.text_input("編集者名（履歴に残します）", value=st.session_state.get("user_name", ""))
st.session_state["user_name"] = user_name.strip() or "不明なユーザー"

tabs = st.tabs(["医療", "生体", "カレンダー"])

# ============== Google接続 ==============
SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

def connect_to_gsheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive",
    ]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    return gspread.authorize(creds)

# ============== 差分抽出（行番号は表示順の1-based） ==============
def compare_dataframes(old_df: pd.DataFrame, new_df: pd.DataFrame):
    diffs = []
    # 長さ合わせ（不足は空文字で埋める）
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
                    "row": i + 1,  # 1-based
                    "col": col,
                    "before": old_val,
                    "after": new_val,
                })
    return diffs

# ============== 履歴追記 ==============
def append_history(sheet_name: str, user: str, diffs: list):
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
        # 100行ずつ
        for i in range(0, len(rows), 100):
            log_ws.append_rows(rows[i:i+100], value_input_option="USER_ENTERED")

# ============== 取得（列選択あり） ==============
def fetch_sheet_data(sheet_name: str, session_key: str):
    st.markdown("### ✅ 表示する項目を選択")
    try:
        client = connect_to_gsheet()
        ws = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
        header = ws.row_values(1)
        full_df = pd.DataFrame(ws.get_all_records())
    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")
        st.stop()

    # 列チェック
    cols = st.columns(min(5, len(header)) or 1)
    selected_cols = []
    for i, col in enumerate(header):
        with cols[i % len(cols)]:
            if st.checkbox(col, value=True, key=f"{sheet_name}_col_{col}"):
                selected_cols.append(col)

    if st.button(f"🔄 スプレッドシートから最新データを取得（{sheet_name}）"):
        st.session_state[f"{session_key}_full"] = full_df.copy()   # 全列保持
        if selected_cols:
            st.session_state[session_key] = full_df[selected_cols].copy()
        else:
            st.session_state[session_key] = full_df.copy()
        st.success(f"✅ {len(st.session_state[session_key])}件のデータを取得しました。")

# ============== 保存（非表示列保持＋差分履歴＋更新者/日時） ==============
def save_to_gsheet(sheet_name: str, session_key: str, user: str):
    try:
        client = connect_to_gsheet()
        sh = client.open_by_key(SPREADSHEET_ID)
        ws = sh.worksheet(sheet_name)

        displayed = st.session_state.get(session_key)               # 表示中（編集後）
        original_full = st.session_state.get(f"{session_key}_full") # 取得時の全列

        if displayed is None or original_full is None or original_full.empty:
            st.error("元データが見つかりません。まずは『データを取得』を実行してください。")
            return

        # 現在のシート（真の最新）を取得して、そこから差分＆保存
        current_full = pd.DataFrame(ws.get_all_records())

        # 1) 非表示列保持：現在のfullに対して「表示列のみ」置き換え
        #   行対応は“行順で”行う前提（IDキーを使う場合はここでjoinしてください）
        merged = current_full.copy()
        for c in displayed.columns:
            if c in merged.columns:
                # 行数がズレる可能性もあるため、長さを合わせてから代入
                # 足りない行は空で拡張
                if len(merged) < len(displayed):
                    add_rows = pd.DataFrame([[""]*len(merged.columns)], columns=merged.columns)
                    merged = pd.concat([merged, add_rows.iloc[0:1].repeat(len(displayed)-len(merged))], ignore_index=True)
                merged.loc[:len(displayed)-1, c] = displayed[c].values
            else:
                # 新規列は追加
                merged[c] = ""
                merged.loc[:len(displayed)-1, c] = displayed[c].values

        # 2) 差分抽出（更新者/日時のため）
        diffs = compare_dataframes(current_full, merged)

        # 3) 変更があった行に「前回更新者/前回更新日時」付与
        if diffs:
            if "前回更新者" not in merged.columns:
                merged["前回更新者"] = ""
            if "前回更新日時" not in merged.columns:
                merged["前回更新日時"] = ""
            changed_rows = sorted(set(d["row"] for d in diffs))
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            for r in changed_rows:
                if 1 <= r <= len(merged):
                    merged.at[r-1, "前回更新者"] = user
                    merged.at[r-1, "前回更新日時"] = now_str

        # 4) 書き込み（100行ずつ分割・USER_ENTERED）
        header = merged.columns.tolist()
        values = merged.fillna("").astype(str).values.tolist()
        ws.clear()
        ws.update([header], value_input_option="USER_ENTERED")
        for i in range(0, len(values), 100):
            ws.append_rows(values[i:i+100], value_input_option="USER_ENTERED")

        st.success("✅ スプレッドシートに上書き保存しました（非表示列も保持）")

        # 5) 履歴追記（差分のみ）
        if diffs:
            append_history(sheet_name, user, diffs)
            st.info(f"📝 {len(diffs)}件の変更を履歴に保存しました。")
        else:
            st.info("変更はありませんでした。")

    except Exception as e:
        st.error(f"❌ 保存中にエラー: {e}")

# ============== 医療タブ ==============
with tabs[0]:
    st.header("🩺 医療システム管理表")
    fetch_sheet_data("医療", "iryo_df")

    if "iryo_df" in st.session_state:
        # 📌 フォーム化：編集と保存を同時に送信（最新の編集を確実に拾う）
        with st.form("iryo_form", clear_on_submit=False):
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
            # フォーム送信ごとに最新編集を反映
            st.session_state["iryo_df"] = edited

            if save_iryo:
                save_to_gsheet("医療", "iryo_df", st.session_state["user_name"])

# ============== 生体タブ ==============
with tabs[1]:
    st.header("🧬 生体システム管理表")
    fetch_sheet_data("生体", "seitai_df")

    if "seitai_df" in st.session_state:
        with st.form("seitai_form", clear_on_submit=False):
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

# ============== カレンダー ==============
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
