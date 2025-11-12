# app.py
import streamlit as st
import pandas as pd

st.set_page_config(page_title="Excel参照", layout="wide")
st.title("📄 SharePointのExcelを参照（方式A）")

# ここだけSharePoint読み込み
from utils.sharepoint_fetch import load_excel_from_share_link

try:
    data_map = load_excel_from_share_link()
except Exception as e:
    st.error(f"読み込みエラー: {e}")
    st.stop()

if not data_map:
    st.warning("Excelにシートがありません")
    st.stop()

tabs = st.tabs(list(data_map.keys()))
for tab, name in zip(tabs, data_map.keys()):
    with tab:
        df = data_map[name].copy()
        st.caption(f"シート: {name} / 行数: {len(df):,}")

        # 列選択
        cols = st.multiselect("表示列", list(df.columns), default=list(df.columns), key=f"cols_{name}")
        view = df[cols] if cols else df

        # 全列キーワード検索
        q = st.text_input("キーワード検索（全列）", key=f"q_{name}")
        if q:
            mask = view.astype(str).apply(lambda r: q.lower() in " ".join(r).lower(), axis=1)
            view = view[mask]

        st.dataframe(view, use_container_width=True, height=520)
        st.download_button(
            "CSVダウンロード",
            data=view.to_csv(index=False).encode("utf-8-sig"),
            file_name=f"{name}.csv",
            mime="text/csv",
            key=f"dl_{name}",
        )
