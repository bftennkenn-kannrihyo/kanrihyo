import streamlit as st
import pandas as pd
from utils.gsheet_utils import read_sheet, connect_to_gsheet, SPREADSHEET_ID

def run():
    st.header("👤 ユーザー情報")

    try:
        df_user = read_sheet("ユーザー情報")
        st.dataframe(df_user, use_container_width=True)

        with st.expander("➕ 新しいユーザーを登録"):
            with st.form("user_form"):
                name = st.text_input("氏名")
                email = st.text_input("メールアドレス")
                date = st.text_input("登録日時")
                submitted = st.form_submit_button("登録")

                if submitted and name:
                    new_user = pd.DataFrame([[name, date, email, date]], columns=df_user.columns)
                    client = connect_to_gsheet()
                    ws = client.open_by_key(SPREADSHEET_ID).worksheet("ユーザー情報")
                    ws.append_rows(new_user.values.tolist())
                    st.success(f"✅ ユーザー「{name}」を登録しました。")

    except Exception as e:
        st.error(f"❌ ユーザー情報取得エラー: {e}")
