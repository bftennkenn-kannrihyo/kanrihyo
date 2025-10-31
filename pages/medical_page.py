import streamlit as st
from utils.gsheet_utils import load_sheet, save_with_history

def medical_tab(spreadsheet_id, current_user):
    st.header("🏥 医療")

    try:
        ws_med, df_med = load_sheet(spreadsheet_id, "医療")

        # --- 表示列チェック ---
        st.markdown("### ✅ 表示する項目を選択")
        selected_fields = []
        cols = st.columns(min(5, len(df_med.columns)))
        for i, col in enumerate(df_med.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=(col in ["施設名", "点検予定月", "エリア"]), key=f"med_{col}"):
                    selected_fields.append(col)

        # --- さらに絞り込み（チェックで出現） ---
        st.markdown("### 🔎 さらに絞り込みを使用する？")
        use_filter = st.checkbox("さらに絞り込みをする", key="med_filter_toggle")

        filter_options = {}
        if use_filter:
            st.markdown("#### 🧭 絞り込み条件を選択")

            # 点検予定月
            if "点検予定月" in df_med.columns:
                use_month_filter = st.checkbox("点検予定月で絞り込み", value=False, key="med_month_toggle")
                if use_month_filter:
                    months = [str(i) for i in range(1, 13)]
                    selected_months = []
                    cols = st.columns(6)
                    for i, m in enumerate(months):
                        with cols[i % 6]:
                            if st.checkbox(f"{m}月", key=f"med_month_{m}"):
                                selected_months.append(m)
                    filter_options["months"] = selected_months

            # エリア
            if "エリア" in df_med.columns:
                use_area_filter = st.checkbox("エリアで絞り込み", value=False, key="med_area_toggle")
                if use_area_filter:
                    areas = ["北海道", "東北", "北関東", "東関東", "東京", "南関東",
                             "中部", "関西", "中国", "四国", "九州"]
                    selected_areas = []
                    cols = st.columns(5)
                    for i, a in enumerate(areas):
                        with cols[i % 5]:
                            if st.checkbox(a, key=f"med_area_{a}"):
                                selected_areas.append(a)
                    filter_options["areas"] = selected_areas

        # --- データ取得 ---
        if st.button("📄 データを取得", key="get_med"):
            filtered_df = df_med.copy()

            if selected_fields:
                filtered_df = filtered_df[selected_fields]

            if use_filter:
                if "months" in filter_options and filter_options["months"]:
                    filtered_df = filtered_df[filtered_df["点検予定月"].astype(str).isin(filter_options["months"])]
                if "areas" in filter_options and filter_options["areas"]:
                    filtered_df = filtered_df[filtered_df["エリア"].isin(filter_options["areas"])]

            st.session_state["filtered_med"] = filtered_df

        # --- 一覧表示 ---
        if "filtered_med" in st.session_state:
            st.subheader("📋 医療一覧")
            edited_df = st.data_editor(st.session_state["filtered_med"], use_container_width=True, key="edit_医療")

            if st.button("💾 上書き保存", key="save_医療"):
                save_with_history(ws_med, df_med, edited_df, current_user, "医療", spreadsheet_id)

    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")
