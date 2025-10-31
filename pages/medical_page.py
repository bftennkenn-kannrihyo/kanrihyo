import streamlit as st
from utils.gsheet_utils import load_sheet, save_with_history

def medical_tab(spreadsheet_id, current_user):
    st.header("🏥 医療データ管理")

    try:
        # 1️⃣ まずヘッダーだけ読み込み（軽い）
        _, df_header = load_sheet(spreadsheet_id, "医療", header_only=True)

        # --- 表示項目チェック ---
        st.markdown("### ✅ 表示する項目を選択")
        selected_cols = []
        cols = st.columns(min(5, len(df_header.columns)))
        for i, c in enumerate(df_header.columns):
            with cols[i % len(cols)]:
                if st.checkbox(c, value=(c in ["施設名", "点検予定月", "エリア"]), key=f"med_{c}"):
                    selected_cols.append(c)

        # --- さらに絞り込み設定 ---
        st.markdown("### 🔎 さらに絞り込み（必要な場合）")
        enable_filter = st.checkbox("さらに絞り込みを有効にする", key="enable_med_filter")
        filter_opt = {}

        if enable_filter:
            if "点検予定月" in df_header.columns:
                filter_opt["months"] = st.multiselect("点検予定月", [str(i) for i in range(1, 13)], key="med_months")
            if "エリア" in df_header.columns:
                filter_opt["areas"] = st.multiselect(
                    "エリア",
                    ["北海道","東北","北関東","東関東","東京","南関東","中部","関西","中国","四国","九州"],
                    key="med_areas"
                )

        # --- データ取得ボタン ---
        if st.button("📄 データを取得", key="get_med"):
            ws, df = load_sheet(spreadsheet_id, "医療")
            filtered = df.copy()
            if selected_cols:
                filtered = filtered[selected_cols]
            if enable_filter:
                if "months" in filter_opt and filter_opt["months"]:
                    filtered = filtered[filtered["点検予定月"].astype(str).isin(filter_opt["months"])]
                if "areas" in filter_opt and filter_opt["areas"]:
                    filtered = filtered[filtered["エリア"].isin(filter_opt["areas"])]

            st.session_state["filtered_med"] = filtered

        # --- 表示＆保存 ---
        if "filtered_med" in st.session_state:
            st.subheader("📋 医療一覧")
            edited_df = st.data_editor(st.session_state["filtered_med"], use_container_width=True, key="edit_med")

            if st.button("💾 上書き保存", key="save_med"):
                save_with_history(spreadsheet_id, "医療", df, edited_df, current_user)

    except Exception as e:
        st.error(f"❌ エラー: {e}")
