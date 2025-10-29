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

    # ▼ Excelシリアル日付を自動変換＋曜日追加
    for col in df.columns:
        # 数値で日付範囲の可能性あり（例：40000〜60000）
        if pd.api.types.is_numeric_dtype(df[col]):
            if df[col].between(40000, 60000).any():
                try:
                    dt_series = pd.to_datetime("1899-12-30") + pd.to_timedelta(df[col], unit="D")
                    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
                    df[col] = dt_series.dt.strftime("%Y-%m-%d") + "（" + dt_series.dt.dayofweek.map(lambda i: weekdays[i]) + "）"
                except Exception:
                    pass
        # 文字列でも日付形式っぽければ変換＋曜日追加
        elif df[col].dtype == object:
            df[col] = df[col].astype(str).str.replace(".", "-").str.replace("/", "-")
            try:
                dt_series = pd.to_datetime(df[col], errors="coerce")
                mask = dt_series.notna()
                weekdays = ["月", "火", "水", "木", "金", "土", "日"]
                df.loc[mask, col] = dt_series[mask].dt.strftime("%Y-%m-%d") + "（" + dt_series[mask].dt.dayofweek.map(lambda i: weekdays[i]) + "）"
            except Exception:
                pass

    return df

def filter_dataframe(df):
    """各列で絞り込みフィルター"""
    for col in df.columns:
        col_type = df[col].dtype
        if pd.api.types.is_numeric_dtype(col_type):
            min_val, max_val = float(df[col].min()), float(df[col].max())
            f_min, f_max = st.slider(f"{col} の範囲", min_val, max_val, (min_val, max_val))
            df = df[df[col].between(f_min, f_max)]
        else:
            unique_vals = df[col].dropna().unique().tolist()
            if len(unique_vals) <= 30:  # 候補が少ない場合は選択ボックス
                selected = st.multiselect(f"{col} を選択", unique_vals, default=unique_vals)
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

        st.markdown("### ✅ 表示する項目を選択（チェックした列のみ表示）")
        selected_fields = []
        cols = st.columns(min(5, len(df.columns)))
        for i, col in enumerate(df.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=(col == "施設名")):
                    selected_fields.append(col)

        if st.button("データを表示"):
            if not selected_fields:
                st.warning("少なくとも1つ項目を選択してください。")
            else:
                if "施設名" not in df.columns:
                    st.error("Excelに『施設名』という列が必要です。")
                else:
                    if query.strip():
                        names = [n.strip() for n in query.splitlines() if n.strip()]
                        filtered = df[df["施設名"].isin(names)]
                    else:
                        filtered = df.copy()

                    results = filtered[selected_fields]
                    st.subheader("📋 絞り込み前データ")
                    st.dataframe(results, use_container_width=True)

                    # ▼「さらに絞り込み」セクションを必要時のみ表示
                    with st.expander("🔎 さらに絞り込み（必要な時だけ開く）", expanded=False):
                        refined = filter_dataframe(results)
                        st.subheader("🔎 絞り込み後データ")
                        st.dataframe(refined, use_container_width=True)

                        # エクスポート
                        output = BytesIO()
                        refined.to_csv(output, index=False, encoding="utf-8-sig")
                        st.download_button("CSVで保存", data=output.getvalue(),
                                           file_name="filtered_data.csv", mime="text/csv")
    else:
        st.info("まずExcelファイルをアップロードしてください。")

# 生体タブ（後で同様に追加）
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
