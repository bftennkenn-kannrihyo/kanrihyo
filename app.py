import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Excel管理アプリ", layout="wide")
st.title("📊 Excelインポート・エクスポート管理")

uploaded_file = st.file_uploader("Excelファイルをアップロード", type=["xlsx", "xls"])

if uploaded_file is not None:
    df = pd.read_excel(uploaded_file)
    st.success("✅ ファイルを読み込みました")

    # データ編集画面
    edited_df = st.data_editor(df, num_rows="dynamic", use_container_width=True)

    # Excelエクスポート関数
    def to_excel(df):
        output = BytesIO()
        with pd.ExcelWriter(output, engine="openpyxl") as writer:
            df.to_excel(writer, index=False)
        return output.getvalue()

    # ダウンロードボタン
    excel_data = to_excel(edited_df)
    st.download_button(
        label="📥 編集後データをダウンロード",
        data=excel_data,
        file_name="updated_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
else:
    st.info("👆 Excelファイルをアップロードしてください。")
