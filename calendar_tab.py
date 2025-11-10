import streamlit as st
import pandas as pd
from datetime import datetime, timedelta




def render():
st.header("📅 点検スケジュール生成")


hospitals_text = st.text_area("病院名（Excelからコピペ）", height=200, key="cal_hospitals")


if st.button("スケジュールを生成", key="cal_generate"):
hospitals = [h.strip() for h in hospitals_text.splitlines() if h.strip()]
today = datetime.today().replace(day=1)
schedule = []
day = today
for h in hospitals:
while day.weekday() >= 5: # 土日スキップ
day += timedelta(days=1)
schedule.append({"日付": day.strftime("%Y-%m-%d"), "病院名": h})
day += timedelta(days=1)


df_sch = pd.DataFrame(schedule)
st.dataframe(df_sch, use_container_width=True)
st.download_button(
"スケジュールをCSVで保存",
data=df_sch.to_csv(index=False, encoding="utf-8-sig"),
file_name="schedule.csv",
mime="text/csv",
)
