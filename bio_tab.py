import streamlit as st
from io_utils import read_excel




def render():
st.header("生体システム管理表")


file2 = st.file_uploader("Excelファイルを選択", type=["xlsx"], key="bio_file")
if file2:
df2 = read_excel(file2)
st.session_state["bio_df"] = df2
st.success(f"{len(df2)}件のデータを読み込みました。")
st.dataframe(df2.head(10), use_container_width=True)
