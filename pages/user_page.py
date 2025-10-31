import streamlit as st
from utils.gsheet_utils import load_sheet

def user_tab(spreadsheet_id, current_user):
    st.header("👤 ユーザー情報")

    try:
        ws_user, df_users = load_sheet(spreadsheet_id, "ユーザー情報")
        st.subheader("📋 登録ユーザー一覧")

        edited_users = st.data_editor(df_users, use_container_width=True, key="edit_users")

        if st.button("💾 上書き保存（ユーザー情報）"):
            ws_user.update([edited_users.columns.values.tolist()] + edited_users.values.tolist())
            st.success("✅ ユーザー情報を更新しました！")

        with st.expander("➕ 新規ユーザー登録"):
            with st.form("add_user_form", clear_on_submit=True):
                name = st.text_input("名前")
                mail = st.text_input("メールアドレス（任意）")
                date = st.text_input("登録日時")
                submitted = st.form_submit_button("登録")
                if submitted and name.strip():
                    ws_user.append_row([name, mail, date])
                    st.success(f"✅ 新規ユーザー「{name}」を登録しました！")
                    st.rerun()

    except Exception as e:
        st.error(f"❌ ユーザー情報取得エラー: {e}")
