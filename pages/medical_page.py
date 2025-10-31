# =====================
# 🏥 医療データ
# =====================
with tabs[0]:
    st.header("🏥 医療")
    try:
        # --- 1️⃣ ヘッダーだけを先に読み込む（列名取得用） ---
        ws_temp, df_temp = load_sheet(SPREADSHEET_ID, "医療")
        col_names = df_temp.columns.tolist()

        # --- 2️⃣ 表示列チェック ---
        st.markdown("### ✅ 表示する項目を選択（チェックした列のみ表示）")
        selected_fields = []
        cols = st.columns(min(5, len(col_names)))
        for i, col in enumerate(col_names):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=(col in ["施設名", "点検予定月", "エリア"]), key=f"med_{col}"):
                    selected_fields.append(col)

        # --- 3️⃣ 絞り込みチェックボックス ---
        enable_filter = st.checkbox("🔎 さらに絞り込みを有効にする", key="enable_med_filter")
        filter_options = {}

        if enable_filter:
            st.markdown("### さらに絞り込み条件（有効時のみ）")
            if "点検予定月" in col_names:
                filter_options["months"] = st.multiselect("点検予定月を選択", [str(i) for i in range(1, 13)], key="med_months")
            if "エリア" in col_names:
                filter_options["areas"] = st.multiselect(
                    "エリアを選択",
                    ["北海道", "東北", "北関東", "東関東", "東京", "南関東", "中部", "関西", "中国", "四国", "九州"],
                    key="med_areas"
                )

        # --- 4️⃣ 📄 データを取得ボタン ---
        if st.button("📄 データを取得", key="get_med"):
            ws_med, df_med = load_sheet(SPREADSHEET_ID, "医療")
            st.session_state["ws_med"] = ws_med
            st.session_state["df_med"] = df_med

            filtered_df = df_med.copy()

            # 表示列限定
            if selected_fields:
                filtered_df = filtered_df[selected_fields]

            # 絞り込み反映
            if enable_filter:
                if "months" in filter_options and filter_options["months"]:
                    filtered_df = filtered_df[filtered_df["点検予定月"].astype(str).isin(filter_options["months"])]
                if "areas" in filter_options and filter_options["areas"]:
                    filtered_df = filtered_df[filtered_df["エリア"].isin(filter_options["areas"])]

            st.session_state["filtered_med"] = filtered_df

        # --- 5️⃣ 一覧表示 ---
        if "filtered_med" in st.session_state:
            st.subheader("📋 医療一覧")
            edited_df = st.data_editor(st.session_state["filtered_med"], use_container_width=True, key="edit_医療")

            if st.button("💾 上書き保存", key="save_医療"):
                save_with_history(
                    SPREADSHEET_ID,
                    "医療",
                    st.session_state["df_med"],
                    edited_df,
                    st.session_state["current_user"]
                )

    except Exception as e:
        st.error(f"❌ データ取得エラー: {e}")
