import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="管理表", layout="wide")
st.title("🏥 管理表")

tabs = st.tabs(["医療", "生体", "カレンダー"])

# 共通関数
def read_excel(upload):
    if upload is None:
        return None
    df = pd.read_excel(upload)
    df.columns = [c.strip() for c in df.columns]
    return df

# 医療タブ
with tabs[0]:
    st.header("医療システム管理表")
    file = st.file_uploader("Excelファイルを選択", type=["xlsx"])
    if file:
        df = read_excel(file)
        st.success(f"{len(df)}件のデータを読み込みました。")
        st.dataframe(df.head(10), use_container_width=True)

    st.markdown("### 🔍 病院名検索")
    query = st.text_area("病院名をコピペ（1行1件）", height=150)
    if st.button("検索"):
        if file is None:
            st.warning("先にExcelを読み込んでください。")
        else:
            names = [n.strip() for n in query.splitlines() if n.strip()]
            results = df[df["病院名"].isin(names)]
            st.dataframe(results, use_container_width=True)
            # エクスポート
            output = BytesIO()
            results.to_csv(output, index=False, encoding="utf-8-sig")
            st.download_button("検索結果をCSVで保存", data=output.getvalue(), file_name="search_result.csv", mime="text/csv")

# 生体タブ（同じ構成）
with tabs[1]:
    st.header("生体システム管理表")
    file2 = st.file_uploader("Excelファイルを選択", type=["xlsx"], key="bio")
    if file2:
        df2 = read_excel(file2)
        st.success(f"{len(df2)}件のデータを読み込みました。")
        st.dataframe(df2.head(10), use_container_width=True)

# カレンダータブ
with tabs[2]:
    st.header("📅 点検スケジュール生成")
    hospitals_text = st.text_area("病院名（Excelからコピペ）", height=200)
    if st.button("スケジュールを生成"):
        hospitals = [h.strip() for h in hospitals_text.splitlines() if h.strip()]
        today = datetime.today().replace(day=1)
        schedule = []
        day = today
        for h in hospitals:
            while day.weekday() >= 5:
                day += timedelta(days=1)
            schedule.append({"日付": day.strftime("%Y-%m-%d"), "病院名": h})
            day += timedelta(days=1)
        df_sch = pd.DataFrame(schedule)
        st.dataframe(df_sch, use_container_width=True)
        st.download_button("スケジュールをCSVで保存", data=df_sch.to_csv(index=False, encoding="utf-8-sig"),
                           file_name="schedule.csv", mime="text/csv")
