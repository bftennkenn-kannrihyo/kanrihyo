# app.py — 見た目だけのUIスケルトン（データ処理は未接続）
# ----------------------------------------------------
# ・サイドバー：ユーザー選択のみ
# ・タブ：📅カレンダー（デフォルトで開く）/ 🏥医療 / 🧬生体
# ・データ読込の土台だけ用意（ttl=300）
# ----------------------------------------------------

from datetime import date, timedelta
import streamlit as st

# ==============================
# ページ設定
# ==============================
st.set_page_config(
    page_title="点検ダッシュボード",
    page_icon="🗂️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ==============================
# 軽いスタイル調整（上部余白やフッターなどを非表示）
# ==============================
HIDE_DEFAULT_CSS = """
<style>
/* Streamlitの上マージンを少し詰める */
section.main > div {padding-top: 0.5rem;}
/* 右上メニューとフッター非表示 */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
/* タブの文字をやや太く */
.stTabs [data-baseweb="tab"] {font-weight: 600;}
/* 見出し余白の微調整 */
h1, h2, h3 {margin-top: 0.2rem;}
</style>
"""
st.markdown(HIDE_DEFAULT_CSS, unsafe_allow_html=True)

# ==============================
# サイドバー：ユーザー選択のみ
# ==============================
with st.sidebar:
    st.markdown("## 👤 ユーザー")
    # TODO: 後でスプシやDBからユーザー一覧を取得する
    user_list = ["未選択", "担当A", "担当B", "担当C"]
    user = st.selectbox("ユーザーを選択", user_list, index=0, key="ui_user")

    # 将来のためのヘルプテキスト（不要になったら削除OK）
    st.caption("※ この画面では見た目のみ。データ接続は後で差し込みます。")

# ==============================
# データ読込の土台（ダミー）。ttl=300。
# ==============================
@st.cache_data(ttl=300)
def load_medical_data(user: str):
    # TODO: ここにスプシ/DB読込を実装
    # 例: return pd.DataFrame(...)
    return {"rows": 0, "user": user}

@st.cache_data(ttl=300)
def load_bio_data(user: str):
    # TODO: ここにスプシ/DB読込を実装
    return {"rows": 0, "user": user}

@st.cache_data(ttl=300)
def load_calendar_data(user: str, base_date: date):
    # TODO: ここに予定データの読込を実装（ユーザー×日付）
    # ここではダミーで当日+1〜+3日を返す
    return [
        {"日付": base_date, "件名": "日次点検", "場所": "A病院"},
        {"日付": base_date + timedelta(days=1), "件名": "システム更新", "場所": "Bクリニック"},
        {"日付": base_date + timedelta(days=3), "件名": "端末交換", "場所": "C病院"},
    ]

# ==============================
# メイン：タブ（カレンダーを先頭にしてデフォルト表示）
# ==============================
# ※ Streamlitはプログラムからの"タブ選択"ができないため、
#   デフォルトで開かせたいタブ（カレンダー）を先頭に配置しています。

TAB_CAL, TAB_MED, TAB_BIO = st.tabs(["📅 カレンダー", "🏥 医療", "🧬 生体"])

# ------------------------------
# 📅 カレンダー（デフォルトで開く）
# ------------------------------
with TAB_CAL:
    st.subheader("カレンダー")

    c1, c2, c3 = st.columns([1, 1, 2])
    with c1:
        base_day = st.date_input("基準日", value=date.today(), format="YYYY-MM-DD", key="cal_base")
    with c2:
        span = st.select_slider("表示期間", options=["1日","3日","1週間","2週間","1ヶ月"], value="1週間")
    with c3:
        st.write("")
        st.caption("ユーザー：**%s**" % user)

    # ダミーデータ（接続前）
    cal_items = load_calendar_data(user, base_day)

    # リスト表示（見た目を先に固める）
    st.markdown("#### 予定一覧（ダミー）")
    for item in cal_items:
        with st.container(border=True):
            st.markdown(
                f"**{item['件名']}**  ")
            st.write(f"日付：{item['日付']} / 場所：{item['場所']}")
    st.caption("※ 後でスプシの実データに差し替えます（ttl=300キャッシュ）。")

# ------------------------------
# 🏥 医療
# ------------------------------
with TAB_MED:
    st.subheader("医療")

    fc1, fc2, fc3, fc4 = st.columns([1,1,1,2])
    with fc1:
        st.text_input("病院名フィルタ", key="med_filter_name")
    with fc2:
        st.selectbox("都道府県", ["すべて","東京","神奈川","千葉","埼玉"], key="med_filter_pref")
    with fc3:
        st.selectbox("状態", ["すべて","未着手","進行中","完了"], key="med_filter_status")
    with fc4:
        med_reload = st.button("読み込み", use_container_width=True, key="med_reload")

    # ダミー読込
    if med_reload:
        med_data = load_medical_data(user)
        st.success(f"読込完了（件数: {med_data['rows']}）")
    else:
        st.info("上の『読み込み』ボタンでデータを取得します。")

    st.divider()
    st.caption("※ ここに表やカードを並べます。スプシ実装時に差し替え。")

# ------------------------------
# 🧬 生体
# ------------------------------
with TAB_BIO:
    st.subheader("生体")

    bc1, bc2, bc3 = st.columns([1,1,2])
    with bc1:
        st.text_input("項目名フィルタ", key="bio_filter_name")
    with bc2:
        st.selectbox("優先度", ["すべて","高","中","低"], key="bio_filter_priority")
    with bc3:
        bio_reload = st.button("読み込み", use_container_width=True, key="bio_reload")

    if bio_reload:
        bio_data = load_bio_data(user)
        st.success(f"読込完了（件数: {bio_data['rows']}）")
    else:
        st.info("上の『読み込み』ボタンでデータを取得します。")

    st.divider()
    st.caption("※ ここに表やカードを並べます。スプシ実装時に差し替え。")

# ==============================
# 画面下：軽いヘルプ
# ==============================
st.markdown(
    """
    <div style='opacity:0.7; font-size:0.9rem;'>
    見た目だけのスケルトンです。後で
    <ul>
      <li>Googleスプレッドシート接続（読み込みは各タブのボタン押下時）</li>
      <li>キャッシュ ttl=300 の適用</li>
      <li>フィルタ条件の反映・表描画</li>
    </ul>
    を差し込みます。
    </div>
    """,
    unsafe_allow_html=True
)
