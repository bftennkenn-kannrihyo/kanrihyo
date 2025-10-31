import streamlit as st
from utils.gsheet_utils import read_sheet, write_with_history
import pandas as pd

def run(current_user):
    st.header("💊 医療システム管理表")

    try:
        df = read_sheet("医療")

        st.markdown("### ✅ 表示する項目を選択")
        selected_fields = []
        cols = st.columns(min(5, len(df.columns)))
        for i, col in enumerate(df.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=True, key=f"med_{col}"):
                    selected_fields.append(col)

        filter_active = st.checkbox("🔎 絞り込み", value=False, key="filter_medical")
        if filter_active:
            if "点検予定月" in df.columns:
                months = [f"{i}月" for i in range(1, 13)]
                selected_months = st.multiselect("点検予定月", months)
                if selected_months:
                    df = df[df["点検予定月"].isin(selected_months)]

        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader("📋 医療データ（直接編集可）")
        with col2:
            if st.button("💾 上書き保存", key="save_med"):
                edited_df = st.session_state.get("edit_med", df)
                write_with_history("医療", edited_df, current_user)
                st.success(f"✅ 保存しました（編集者: {current_user}）")

        edited_df = st.data_editor(df[selected_fields], use_container_width=True, key="edit_med")
        st.session_state["edit_med"] = edited_df

    except Exception as e:
        st.error(f"❌ 医療データ取得エラー: {e}")
