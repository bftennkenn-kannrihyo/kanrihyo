import streamlit as st
from utils.gsheet_utils import load_sheet, save_with_history

def medical_tab(spreadsheet_id, current_user):
    st.header("🏥 医療")

    ws_med, df_med = load_sheet(spreadsheet_id, "医療")

    st.markdown("### ✅ 表示する項目を選択")
    selected_fields = [col for col in df_med.columns if st.checkbox(col, value=(col in ["施設名", "点検予定月", "エリア"]), key=f"med_{col}")]

    use_filter = st.checkbox("さらに絞り込みをする", key="med_filter")
    filter_options = {}

    if use_filter:
        if "点検予定月" in df_med.columns:
            st.markdown("#### 🗓 点検予定月")
            months = [str(i) for i in range(1, 13)]
            selected_months = [m for m in months if st.checkbox(f"{m}月", key=f"med_month_{m}")]
            filter_options["months"] = selected_months

        if "エリア" in df_med.columns:
            st.markdown("#### 🗾 エリア")
            areas = ["北海道", "東北", "北関東", "東関東", "東京", "南関東", "中部", "関西", "中国", "四国", "九州"]
            selected_areas = [a for a in areas if st.checkbox(a, key=f"med_area_{a}")]
            filter_options["areas"] = selected_areas

    if st.button("📄 データを取得", key="get_med"):
        filtered_df = df_med.copy()
        if selected_fields:
            filtered_df = filtered_df[selected_fields]

        if use_filter:
            if filter_options.get("months"):
                filtered_df = filtered_df[filtered_df["点検予定月"].astype(str).isin(filter_options["months"])]
            if filter_options.get("areas"):
                filtered_df = filtered_df[filtered_df["エリア"].isin(filter_options["areas"])]

        st.session_state["filtered_med"] = filtered_df

    if "filtered_med" in st.session_state:
        st.subheader("📋 医療一覧")
        edited_df = st.data_editor(st.session_state["filtered_med"], use_container_width=True, key="edit_医療")

        if st.button("💾 上書き保存", key="save_医療"):
            save_with_history(ws_med, df_med, edited_df, current_user, "医療", spreadsheet_id)
