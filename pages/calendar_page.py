import streamlit as st
from utils.gsheet_utils import read_sheet
from datetime import datetime, timedelta
import pandas as pd

def run():
    st.header("📅 点検スケジュール生成")

    try:
        sheet_choice = st.radio("対象シートを選択", ["医療", "生体"], horizontal=True)
        df = read_sheet(sheet_choice)

        if "施設名" not in df.columns:
            st.warning("施設名の列が見つかりません。")
            return

        if "点検予定月" in df.columns:
            months = sorted(df["点検予定月"].dropna().unique().tolist())
            selected_month = st.selectbox("📆 点検予定月を選択", months)
            df = df[df["点検予定月"] == selected_month]

        if not df.empty:
            start_date = datetime(datetime.today().year, int(selected_month.replace("月", "")), 1)
            schedule = []
            day = start_date
            for _, row in df.iterrows():
                while day.weekday() >= 5:  # 土日スキップ
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
            st.info("選択した月に該当データがありません。")

    except Exception as e:
        st.error(f"❌ カレンダー生成エラー: {e}")
