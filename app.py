import streamlit as st
import pandas as pd
from io import BytesIO

st.set_page_config(page_title="Excelインポート・エクスポート管理", layout="wide")
st.title("📊 Excelインポート・エクスポート管理")

st.caption("画面で編集 → ボタンでExcelに書き出しできます（複数シート対応）")

# ========== ヘルパー ==========
@st.cache_data(show_spinner=False)
def read_excel_all_sheets(file) -> dict[str, pd.DataFrame]:
    """Excelを全シート読み込みして {sheet_name: DataFrame} を返す"""
    xls = pd.ExcelFile(file)
    sheets: dict[str, pd.DataFrame] = {}
    for name in xls.sheet_names:
        sheets[name] = pd.read_excel(xls, sheet_name=name)
    return sheets

def to_excel_bytes(sheet_map: dict[str, pd.DataFrame]) -> bytes:
    """{sheet: df} を1つのExcelバイナリにして返す"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        for sheet, df in sheet_map.items():
            # 空DFは最低1列ないと保存時にエラーになるため調整
            safe_df = df.copy()
            if safe_df.shape[1] == 0:
                safe_df[" "] = []
            safe_df.to_excel(writer, index=False, sheet_name=sheet[:31] or "Sheet1")
    return output.getvalue()

def empty_template() -> bytes:
    """空のテンプレートExcel（Sheet1だけ）"""
    return to_excel_bytes({"Sheet1": pd.DataFrame()})

# ========== UI ==========
col_l, col_r = st.columns([2, 1])
with col_l:
    uploaded = st.file_uploader("Excelファイルをアップロード", type=["xlsx", "xls"], accept_multiple_files=False)
with col_r:
    st.download_button(
        "🧾 空のテンプレートをダウンロード",
        data=empty_template(),
        file_name="template.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        use_container_width=True,
    )

if uploaded is None:
    st.info("👆 Excelファイルをアップロードしてください。")
    st.stop()

# アップロード → 全シート読み込み
sheets = read_excel_all_sheets(uploaded)
if not sheets:
    st.warning("シートが見つかりませんでした。")
    st.stop()

st.success(f"✅ 読み込み完了：{uploaded.name}（{len(sheets)}シート）")

# セッションに初期化
if "edited_sheets" not in st.session_state:
    st.session_state.edited_sheets = sheets
else:
    # 新しいファイルを読み込んだら上書き
    # 同名アップロード時はここをコメントアウトしてもOK
    st.session_state.edited_sheets = sheets

# タブで各シートを編集
tab_names = list(st.session_state.edited_sheets.keys())
tabs = st.tabs(tab_names)

for i, t in enumerate(tabs):
    sheet_name = tab_names[i]
    with t:
        st.markdown(f"**シート名：** `{sheet_name}`")
        df = st.session_state.edited_sheets[sheet_name]
        edited = st.data_editor(
            df,
            num_rows="dynamic",
            use_container_width=True,
            key=f"editor_{i}",
            height=420,
        )
        st.session_state.edited_sheets[sheet_name] = edited

        # 選択シートだけCSVで落とす
        csv = edited.to_csv(index=False).encode("utf-8-sig")
        st.download_button(
            "🔻 このシートだけCSVでダウンロード",
            data=csv,
            file_name=f"{sheet_name}.csv",
            mime="text/csv",
            key=f"csv_{i}",
        )

st.divider()

# すべてのシートを1つのExcelにまとめて書き出し
excel_bytes = to_excel_bytes(st.session_state.edited_sheets)
st.download_button(
    "📥 編集結果をExcelでダウンロード（全シート）",
    data=excel_bytes,
    file_name="updated_data.xlsx",
    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    use_container_width=True,
)
