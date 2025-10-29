import streamlit as st
import pandas as pd
from io import BytesIO
from datetime import datetime, timedelta

# ▼ Googleスプレッドシート接続関数
import gspread
from google.oauth2.service_account import Credentials

def connect_to_gsheet():
    """Googleスプレッドシートに接続"""
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds = Credentials.from_service_account_info(st.secrets["default"], scopes=scope)
    client = gspread.authorize(creds)
    return client

st.set_page_config(page_title="管理表", layout="wide")
st.title("🏥 管理表")

tabs = st.tabs(["医療", "生体", "カレンダー"])

# ▼ Excel読み込み関数（シリアル日付変換＋曜日付き）
def read_excel(upload):
    if upload is None:
        return None
    df = pd.read_excel(upload, dtype=str)
    df.columns = [c.strip() for c in df.columns]

    target_cols = ["点検確定日", "前回点検日"]  # 対象の列だけ変換

    for col in df.columns:
        if col not in target_cols:
            continue  # 他の列はスキップ

        converted = []
        for val in df[col]:
            if pd.isna(val) or str(val).strip() == "":
                converted.append("")
                continue

            val_str = str(val).strip()

            # Excelシリアル値（例：45749）
            if val_str.replace(".", "", 1).isdigit():
                num = float(val_str)
                if 30000 < num < 80000:
                    try:
                        dt = pd.to_datetime("1899-12-30") + pd.to_timedelta(num, unit="D")
                        weekdays = ["月", "火", "水", "木", "金", "土", "日"]
                        converted.append(dt.strftime("%Y-%m-%d") + f"（{weekdays[dt.weekday()]}）")
                        continue
                    except Exception:
                        pass

            # 通常の日付文字列（例：2025/4/2, 4月2日など）
            try:
                dt = pd.to_datetime(val_str, errors="coerce")
                if pd.notna(dt):
                    weekdays = ["月", "火", "水", "木", "金", "土", "日"]
                    converted.append(dt.strftime("%Y-%m-%d") + f"（{weekdays[dt.weekday()]}）")
                    continue
            except Exception:
                pass

            # 変換できなければ元のまま
            converted.append(val_str)

        df[col] = converted

    return df

# ▼ データフィルタリング関数
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
            if len(unique_vals) <= 30:
                selected = st.multiselect(f"{col} を選択", unique_vals, default=unique_vals)
                df = df[df[col].isin(selected)]
            else:
                keyword = st.text_input(f"{col} に含まれる文字を検索")
                if keyword:
                    df = df[df[col].astype(str).str.contains(keyword, case=False, na=False)]
    return df

# ▼ 医療タブ
with tabs[0]:
    st.header("医療システム管理表")

    # --- ファイルアップロード（保持付き）---
    uploaded_file = st.file_uploader("Excelファイルを選択", type=["xlsx"])
    if uploaded_file is not None:
        st.session_state["uploaded_file"] = uploaded_file

    # --- セッションから再利用 ---
    file = st.session_state.get("uploaded_file", None)
    df = read_excel(file) if file else None

    if df is not None:
        st.success(f"{len(df)}件のデータを読み込みました。")

        # --- 検索 ---
        st.markdown("### 🔍 任意で施設名検索（空欄でもOK）")
        query = st.text_area("施設名をコピペ（1行1件）", height=150, placeholder="入力しなくても全件表示できます")

        # --- 項目選択 ---
        st.markdown("### ✅ 表示する項目を選択（チェックした列のみ表示）")
        selected_fields = []
        cols = st.columns(min(5, len(df.columns)))
        for i, col in enumerate(df.columns):
            with cols[i % len(cols)]:
                if st.checkbox(col, value=(col == "施設名"), key=f"col_{col}"):
                    selected_fields.append(col)

        # --- データ表示 ---
        if st.button("データを表示"):
            if not selected_fields:
                st.warning("少なくとも1つ項目を選択してください。")
            elif "施設名" not in df.columns:
                st.error("Excelに『施設名』という列が必要です。")
            else:
                # 絞り込み
                if query.strip():
                    names = [n.strip() for n in query.splitlines() if n.strip()]
                    filtered = df[df["施設名"].isin(names)]
                else:
                    filtered = df.copy()

                results = filtered[selected_fields]
                st.session_state["results"] = results  # ← ✅ 結果を保存

    # --- データ表示（ボタン後も保持）---
    if "results" in st.session_state:
        results = st.session_state["results"]
        st.subheader("📋 絞り込み前データ")
        st.dataframe(results, use_container_width=True)

        # ▼ さらに絞り込み
        with st.expander("🔎 さらに絞り込み（必要な時だけ開く）", expanded=False):
            refined = filter_dataframe(results)
            st.subheader("🔎 絞り込み後データ")
            st.dataframe(refined, use_container_width=True)

            # CSV出力
            output = BytesIO()
            refined.to_csv(output, index=False, encoding="utf-8-sig")
            st.download_button("CSVで保存", data=output.getvalue(),
                               file_name="filtered_data.csv", mime="text/csv")

        # ☁️ Googleスプレッドシート保存
        st.markdown("### ☁️ Googleスプレッドシート連携")
        st.write("書き込み予定データ数:", len(results))

        if st.button("Googleスプレッドシートに上書き保存"):
            try:
                st.info("🔄 スプレッドシートに接続中…")
                client = connect_to_gsheet()
                sheet = client.open("医療システム管理表").worksheet("シート1")
                st.success("✅ 接続成功！")
        
                data_to_write = st.session_state["results_data"]
                clean_df = data_to_write.fillna("").astype(str)
        
                st.info(f"📄 書き込みデータ数: {len(clean_df)} 件")
        
                # 全消去
                sheet.clear()
                st.info("🧹 既存データをクリアしました。")
        
                # 列名＋データ
                all_data = [clean_df.columns.values.tolist()] + clean_df.values.tolist()
        
                import time
                import requests
        
                try:
                    st.info("🔄 スプレッドシートに接続中…")
                    client = connect_to_gsheet()
                    ss = client.open("医療システム管理表")
                    sheet = ss.sheet1
                    st.success("✅ 接続成功！")
                
                    st.write("📄 シート名:", sheet.title)  # ← デバッグ
                    st.write("📘 スプレッドシートタイトル:", ss.title)  # ← デバッグ
                
                    data_to_write = st.session_state["results_data"]
                    clean_df = data_to_write.fillna("").astype(str)
                
                    st.info(f"📄 書き込みデータ数: {len(clean_df)} 件")
                
                    sheet.clear()
                    sheet.update([clean_df.columns.values.tolist()] + clean_df.values.tolist())
                    st.success("✅ Googleスプレッドシートに上書き保存しました！")
                
                except Exception as e:
                    st.error(f"❌ エラーが発生しました: {e}")

    else:
        st.info("まずExcelファイルをアップロードして『データを表示』を押してください。")

# ▼ 生体タブ（同じ構成にあとで拡張可能）
with tabs[1]:
    st.header("生体システム管理表")
    st.info("ここも後で医療タブと同じ構成にできます。")

# ▼ カレンダータブ
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
            schedule.append({"日付": day.strftime("%Y-%m-%d（%a）"), "施設名": h})
            day += timedelta(days=1)
        df_sch = pd.DataFrame(schedule)
        st.dataframe(df_sch, use_container_width=True)
        st.download_button("スケジュールをCSVで保存", data=df_sch.to_csv(index=False, encoding="utf-8-sig"),
                           file_name="schedule.csv", mime="text/csv")
