import streamlit as st
from io import BytesIO
from io_utils import read_excel


def render():
    st.header("医療システム管理表")

    file = st.file_uploader("Excelファイルを選択", type=["xlsx"], key="med_file")
    if file:
        df = read_excel(file)
        st.session_state["med_df"] = df
        st.success(f"{len(df)}件のデータを読み込みました。")
        st.dataframe(df.head(10), use_container_width=True)

    st.markdown("### 🔍 病院名検索")
    query = st.text_area("病院名をコピペ（1行1件）", height=150, key="med_query")

    if st.button("検索", key="med_search"):
        df = st.session_state.get("med_df")
        if df is None:
            st.warning("先にExcelを読み込んでください。")
            return

        names = [n.strip() for n in query.splitlines() if n.strip()]
        if "病院名" in df.columns:
            results = df[df["病院名"].isin(names)]
        else:
            st.error("Excelに『病院名』列が見つかりません。")
            return

        st.dataframe(results, use_container_width=True)

        output = BytesIO()
        results.to_csv(output, index=False, encoding="utf-8-sig")
        st.download_button(
            "検索結果をCSVで保存",
            data=output.getvalue(),
            file_name="search_result.csv",
            mime="text/csv",
        )
