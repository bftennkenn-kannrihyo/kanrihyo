import io
import requests
import pandas as pd
import streamlit as st

@st.cache_data(ttl=600)
def load_excel_from_share_link() -> dict[str, pd.DataFrame]:
    """
    Secrets の SHAREPOINT_FILE_URL（download.aspx?share=...）から
    Excelを読み込み、{シート名: DataFrame} を返す。
    """
    url = st.secrets["general"]["SHAREPOINT_FILE_URL"]
    r = requests.get(url, timeout=30)
    r.raise_for_status()
    xls = pd.ExcelFile(io.BytesIO(r.content))
    return {name: pd.read_excel(xls, sheet_name=name) for name in xls.sheet_names}
