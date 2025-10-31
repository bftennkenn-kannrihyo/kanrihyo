import streamlit as st
import pandas as pd
from utils.gsheet_utils import load_sheet, save_with_history

def medical_tab(SPREADSHEET_ID, current_user):
    st.header("🏥 医療データ管理")

    try:
        # --- スプレッドシートから取得 ---
        ws, df = load_sheet(SPREADSHEET_ID, "医療")

        st.markdown("### ✅ 表示する項目を選択")
        selected_cols = []
        cols = st.columns(min(5, len(df.columns)))
        for i, c in enumerate(df.columns):
            with cols[i % len(cols)]:
                if st.checkbox(c, value=(c in ["施設名", "点検予定月", "エリア"]), key=f"med_{c}"):
                    selected_cols.append(c)

        # --- 絞り込みチェック ---
        st.markdown("### 🔎 さらに絞り込みを使う")
        enable_filter = st.checkbox("さらに絞り込みを有効にする", key="enable_med_filter")
        filter_opt = {}

        if enable_filter:
            if "点検予定月" in df.columns:
                filter_opt["months"] = st.multiselect("点検予定月", [str(i) for i in range(1, 13)], key="med_months")
            if "エリア" in df.columns:
                filter_opt["areas"] = st.multiselect(
                    "エリア",
                    ["北海道", "東北", "北関東", "東関東", "東京", "南関東", "中部", "関西", "中国", "四国", "九州"],
                    key="med_areas"
                )

        # --- データ取得ボタン ---
        if st.button("📄 データを取得", key="get_med"):
            filtered = df.copy()

            # 表示列を限定
            if selected_cols:
                filtered = filtered[selected_cols]

            # 絞り込み適用
            if enable_filter:
                if "months" in filter_opt and filter_opt["months"]:
                    filtered = filtered[filtered["点検予定月"].astype(str).isin(filter_opt["months"])]
                if "areas" in filter_opt and filter_opt["areas"]:
                    filtered = filtered[filtered["エリア"].isin(filter_opt["areas"])]

            st.session_state["filtered_med"] = filtered

        # --- 一覧表示と編集 ---
        if "filtered_med" in st.session_state:
            st.subheader("📋 医療一覧")
            edited_df = st.data_editor(
                st.session_state["filtered_med"], use_container_width=True, key="edit_med"
            )

            # --- 保存ボタン ---
            if st.button("💾 上書き保存", key="save_med"):
                user = current_user or "不明ユーザー"
                save_with_history(SPREADSHEET_ID, "医療", df, edited_df, user)

    except Exception as e:
        st.error(f"❌ エラー: {e}")
