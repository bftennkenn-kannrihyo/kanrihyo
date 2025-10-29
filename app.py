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
    df = read_excel(file) if file else None

    if df is not None:
        st.success(f"{len(df)}件のデータを読み込みました。")
        st.dataframe(df.head(10), use_container_width=True)

        st.markdown("### 🔍 病院名検索")
        query = st.text_area("病院名をコピペ（1行1件）", height=150)

        st.markdown("**表示する項目を選択**")
        selected_fields = []
        # Excel列名をチェックボックスに自動展開
        for col in df.columns:
            if st.checkbox(col, value=(col == "病院名")):
                selected_fields.append(col)

        if st.button("検索"):
            if "病院名" not in df.columns:
                st.error("Excelに『病院名』という列が必要です。")
            elif not query.strip():
                st.warning("検索したい病院名を入力してください。")
            elif not selected_fields:
                st.warning("少なくとも1つ項目を選択してください。")
            else:
                names = [n.strip() for n in query.splitlines() if n.strip()]
                results = df[df["病院名"].isin(names)][selected_fields]
                st.dataframe(results, use_container_width=True)
                # エクスポート
                output = BytesIO()
                results.to_csv(output, index=False, encoding="utf-8-sig")
                st.download_button("検索結果をCSVで保存", data=output.getvalue(),
                                   file_name="search_result.csv", mime="text/csv")
    else:
        st.info("Excelファイルをアップロードしてください。")

# 生体タブ（同じ構成で後から追加可）
with tabs[1]:
    st.header("生体システム管理表")
    st.info("ここも後で医療タブと同じ構成にできます。")

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
