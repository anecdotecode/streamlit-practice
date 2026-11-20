import streamlit as st
from pathlib import Path

SITE_URL = "https://anecdotecode.github.io/streamlit-practice/"

# 他のページ(high and low の正解数など)と session_state は共有されるため、
# このページ専用のキーを使う。
if "app_stage" not in st.session_state:
    st.session_state.app_stage = 0

# pages/ にあるゲームページ。ファイル名に含まれる語で、アイコン・表示名・説明を割り当てる。
GAME_INFO = {
    "hangman": ("🔤", "hangman", "伏せられた英単語を1文字ずつ当てる。ミスは8回まで。"),
    "high": ("🃏", "high and low", "場のカードと次のカードの大小を予想する。"),
    "kanji": ("⚫", "kanji reversi", "リバーシをしながら、盤面に隠れた漢字を当てる。"),
}

CSS = """
<style>
.block-container { max-width: 860px; padding-top: 3rem; }
.game-icon { font-size: 2.2rem; line-height: 1; margin-bottom: .4rem; }
.game-title { font-size: 1.15rem; font-weight: 600; margin-bottom: .2rem; }
.game-text { font-size: .9rem; opacity: .7; margin-bottom: .6rem; min-height: 4.8em; }
.hero-sub { opacity: .65; margin-top: -.6rem; }
</style>
"""


def show_hero():
    left, right = st.columns([1, 5], vertical_alignment="center")
    with left:
        st.image("wel.png", width=88)
    with right:
        st.title("Games")
    st.markdown(
        '<p class="hero-sub">Streamlit で作った小さなゲーム集。遊びたいものを選んでください。</p>',
        unsafe_allow_html=True,
    )


def show_game_links():
    pages = sorted(
        p for p in (Path(__file__).parent / "pages").glob("*.py")
        if not p.name.startswith("_")
    )
    if not pages:
        return
    for col, page in zip(st.columns(len(pages)), pages):
        stem = page.stem.lower()
        icon, title, text = next(
            (v for k, v in GAME_INFO.items() if k in stem),
            ("🎮", page.stem.lstrip("0123456789_").replace("_", " "), ""),
        )
        with col.container(border=True):
            st.markdown(
                f'<div class="game-icon">{icon}</div>'
                f'<div class="game-title">{title}</div>'
                f'<div class="game-text">{text}</div>',
                unsafe_allow_html=True,
            )
            st.page_link(f"pages/{page.name}", label="プレイする", icon="➡️")


def show_extras():
    st.link_button("遊び方を見る", SITE_URL)
    with st.expander("おまけ: 数字あそび"):
        a = int(st.number_input("好きな数字を一つ", value=0, step=1, format="%d", key="a"))
        b = int(st.number_input("もう一つ", value=0, step=1, format="%d", key="b"))
        left, right = st.columns(2)
        left.metric("これらの積", f"{a * b}")
        right.metric("これらの和", f"{a + b}")
    if a == 5 and b == 7:
        st.session_state.app_stage = 1
        st.rerun()


st.markdown(CSS, unsafe_allow_html=True)

if st.session_state.app_stage == 0:
    show_hero()
    show_game_links()
    st.write("")
    show_extras()

elif st.session_state.app_stage == 1:
    st.image("find.png", width=500)
    if st.button("reset"):
        st.session_state.app_stage = 0
        st.rerun()