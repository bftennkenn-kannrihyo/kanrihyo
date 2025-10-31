import streamlit as st
from utils.gsheet_utils import read_sheet, write_with_history
import pandas as pd

def run(current_user):
    st.header("🧬 生体システム管理表")

    try:
        df = read_sheet("生体")

        st.markdown("### ✅ 表示する項目を選択")
        selected_fields = []
        cols = st.columns(min(5, len(df.columns)))
        for i, col in enumerate(df.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=True, key=f"bio_{col}"):
                    selected_fields.append(col)

        col1, col2 = st.columns([4, 1])
        with col1:
            st.subheader("📋 生体データ（直接編集可）")
        with col2:
            if st.button("💾 上書き保存", key="save_bio"):
                edited_df = st.session_state.get("edit_bio", df)
                write_with_history("生体", edited_df, current_user)
                st.success(f"✅ 保存しました（編集者: {current_user}）")

        edited_df = st.data_editor(df[selected_fields], use_container_width=True, key="edit_bio")
        st.session_state["edit_bio"] = edited_df

    except Exception as e:
        st.error(f"❌ 生体データ取得エラー: {e}")
