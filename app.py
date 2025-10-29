import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

st.set_page_config(page_title="管理表", layout="wide")
st.title("🏥 管理表")

tabs = st.tabs(["医療", "生体", "カレンダー"])

# 共通関数
def read_excel(upload):
    if upload is None:
        return None
    df = pd.read_excel(upload)
    df.columns = [c.strip() for c in df.columns]
    return df

def filter_dataframe(df):
    """列ごとに絞り込みを追加"""
    st.markdown("### 🔎 さらに絞り込み条件を設定")
    for col in df.columns:
        col_type = df[col].dtype
        if pd.api.types.is_numeric_dtype(col_type):
            min_val, max_val = float(df[col].min()), float(df[col].max())
            f_min, f_max = st.slider(f"{col} の範囲", min_val, max_val, (min_val, max_val))
            df = df[df[col].between(f_min, f_max)]
        else:
            unique_vals = df[col].dropna().unique().tolist()
            if len(unique_vals) <= 30:
                selected = st.multiselect(f"{col} の値を選択", unique_vals, default=unique_vals)
                df = df[df[col].isin(selected)]
            else:
                keyword = st.text_input(f"{col} に含まれる文字を検索")
                if keyword:
                    df = df[df[col].astype(str).str.contains(keyword, case=False, na=False)]
    return df


# 医療タブ
with tabs[0]:
    st.header("医療システム管理表")
    file = st.file_uploader("Excelファイルを選択", type=["xlsx"])
    df = read_excel(file) if file else None

    if df is not None:
        st.success(f"{len(df)}件のデータを読み込みました。")

        st.markdown("### 🔍 任意で施設名検索（空欄でもOK）")
        query = st.text_area("施設名をコピペ（1行1件）", height=150, placeholder="入力しなくても全件表示できます")

        st.markdown("### ✅ 表示する項目を選択")
        selected_fields = []
        cols = st.columns(min(5, len(df.columns)))
        for i, col in enumerate(df.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=(col == "施設名")):
                    selected_fields.append(col)

        use_filter = st.checkbox("🔎 絞り込み機能を使う")

        if st.button("データを表示"):
            if not selected_fields:
                st.warning("少なくとも1つ項目を選択してください。")
            else:
                if "施設名" not in df.columns:
                    st.error("Excelに『施設名』という列が必要です。")
                else:
                    # 検索条件
                    if query.strip():
                        names = [n.strip() for n in query.splitlines() if n.strip()]
                        filtered = df[df["施設名"].isin(names)]
                    else:
                        filtered = df.copy()

                    results = filtered[selected_fields]
                    st.subheader("📋 データ表示")
                    st.dataframe(results, use_container_width=True)

                    # ✅ 絞り込み機能がONの時だけフィルターUIを出す
                    if use_filter:
                        refined = filter_dataframe(results)
                        st.subheader("🔎 絞り込み後データ")
                        st.dataframe(refined, use_container_width=True)

                        # CSVエクスポート
                        output = BytesIO()
                        refined.to_csv(output, index=False, encoding="utf-8-sig")
                        st.download_button("絞り込み後データをCSVで保存", data=output.getvalue(),
                                           file_name="filtered_data.csv", mime="text/csv")
                    else:
                        # 通常出力
                        output = BytesIO()
                        results.to_csv(output, index=False, encoding="utf-8-sig")
                        st.download_button("表示データをCSVで保存", data=output.getvalue(),
                                           file_name="display_data.csv", mime="text/csv")
    else:
        st.info("まずExcelファイルをアップロードしてください。")

# 生体タブ（後で同じ構成にできます）
with tabs[1]:
    st.header("生体システム管理表")
    st.info("ここも後で医療タブと同じ構成にします。")

# カレンダータブ
with tabs[2]:
    st.header("📅 点検スケジュール生成")
    facilities_text = st.text_area("施設名（Excelからコピペ）", height=200)
    if st.button("スケジュールを生成"):
        facilities = [h.strip() for h in facilities_text.splitlines() if h.strip()]
        today = datetime.today().replace(day=1)
        schedule = []
        day = today
        for h in facilities:
            while day.weekday() >= 5:
                day += timedelta(days=1)
            schedule.append({"日付": day.strftime("%Y-%m-%d"), "施設名": h})
            day += timedelta(days=1)
        df_sch = pd.DataFrame(schedule)
        st.dataframe(df_sch, use_container_width=True)
        st.download_button("スケジュールをCSVで保存", data=df_sch.to_csv(index=False, encoding="utf-8-sig"),
                           file_name="schedule.csv", mime="text/csv")
