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
# Googleスプレッドシート接続関数
# ======================================
def connect_to_gsheet():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    client = gspread.authorize(creds)
    return client

SPREADSHEET_ID = "15bsvTOQOJrHjgsVh2IJFzKkaig2Rk2YLA130y8_k4Vs"

# ======================================
# 共通：列選択UI + データ取得関数
# ======================================
def fetch_sheet_data(sheet_name, session_key):
    st.markdown("### ✅ 表示する項目を選択")
    try:
        client = connect_to_gsheet()
        sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
        columns = sheet.row_values(1)  # 1行目の列名を取得
    except Exception as e:
        st.error(f"❌ 列名を取得できませんでした: {e}")
        st.stop()

    # --- チェックボックス群 ---
    cols = st.columns(min(5, len(columns)))
    selected_cols = []
    for i, col in enumerate(columns):
        with cols[i % len(cols)]:
            if st.checkbox(col, value=True, key=f"{sheet_name}_col_{col}"):
                selected_cols.append(col)

    # --- データ取得ボタン ---
    if st.button(f"🔄 スプレッドシートから最新データを取得（{sheet_name}）"):
        try:
            client = connect_to_gsheet()
            sheet = client.open_by_key(SPREADSHEET_ID).worksheet(sheet_name)
            data = sheet.get_all_records()
            df = pd.DataFrame(data)

            if df.empty:
                st.warning("⚠️ スプレッドシートにデータがありません。")
            else:
                # ✅ 選択した列だけを反映
                if selected_cols:
                    df = df[selected_cols]
                st.session_state[session_key] = df
                st.success(f"✅ {len(df)}件のデータを取得しました。")
        except Exception as e:
            st.error(f"❌ データ取得中にエラーが発生しました: {e}")

# ======================================
# 医療タブ
# ======================================
with tabs[0]:
    st.header("🩺 医療システム管理表（Googleスプレッドシート連携）")

    fetch_sheet_data("医療", "iryo_df")

    if "iryo_df" in st.session_state:
        st.subheader("📋 医療データ（直接編集可）")

        edited_df = st.data_editor(
            st.session_state["iryo_df"],
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
        )
        st.session_state["iryo_edited_df"] = edited_df

        if st.button("☁️ スプレッドシートに上書き保存（医療）"):
            try:
                client = connect_to_gsheet()
                sheet = client.open_by_key(SPREADSHEET_ID).worksheet("医療")
                data = [edited_df.columns.tolist()] + edited_df.fillna("").values.tolist()
                sheet.clear()
                sheet.update(data)
                st.success("✅ 医療データをスプレッドシートに上書き保存しました！")
            except Exception as e:
                st.error(f"❌ 医療データの書き込み中にエラーが発生しました: {e}")

# ======================================
# 生体タブ
# ======================================
with tabs[1]:
    st.header("🧬 生体システム管理表（Googleスプレッドシート連携）")

    fetch_sheet_data("生体", "seitai_df")

    if "seitai_df" in st.session_state:
        st.subheader("📋 生体データ（直接編集可）")

        edited_df = st.data_editor(
            st.session_state["seitai_df"],
            use_container_width=True,
            hide_index=True,
            num_rows="dynamic",
        )
        st.session_state["seitai_edited_df"] = edited_df

        if st.button("☁️ スプレッドシートに上書き保存（生体）"):
            try:
                client = connect_to_gsheet()
                sheet = client.open_by_key(SPREADSHEET_ID).worksheet("生体")
                data = [edited_df.columns.tolist()] + edited_df.fillna("").values.tolist()
                sheet.clear()
                sheet.update(data)
                st.success("✅ 生体データをスプレッドシートに上書き保存しました！")
            except Exception as e:
                st.error(f"❌ 生体データの書き込み中にエラーが発生しました: {e}")

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
