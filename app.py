import streamlit as st
from medical_tab import render as render_medical
from bio_tab import render as render_bio
from calendar_tab import render as render_calendar

st.set_page_config(page_title="管理表", layout="wide")
st.title("🏥 管理表")

_tab_med, _tab_bio, _tab_cal = st.tabs(["医療", "生体", "カレンダー"])

with _tab_med:
    render_medical()

with _tab_bio:
    render_bio()

with _tab_cal:
    render_calendar()
