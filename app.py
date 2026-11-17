import streamlit as st
import math as mt
from pathlib import Path

# 他のページ(high and low の正解数など)と session_state は共有されるため、
# このページ専用のキーを使う。
if "app_stage" not in st.session_state:
    st.session_state.app_stage = 0
a = 0
b = 0

# pages/ にあるゲームページ。ファイル名に含まれる語で、アイコンと説明を割り当てる。
GAME_INFO = {
    "hangman": ("🔤", "伏せられた英単語を1文字ずつ当てる。ミスは8回まで。"),
    "high": ("🃏", "場のカードと次のカードの大小を予想する。"),
}


def show_game_links():
    st.subheader("Two games are here")
    pages = sorted(
        p for p in (Path(__file__).parent / "pages").glob("*.py")
        if not p.name.startswith("_")
    )
    if not pages:
        return
    for col, page in zip(st.columns(len(pages)), pages):
        icon, text = next(
            (v for k, v in GAME_INFO.items() if k in page.stem.lower()),
            (None, ""),
        )
        with col.container(border=True):
            st.page_link(
                f"pages/{page.name}",
                label=page.stem.lstrip("0123456789_").replace("_", " "),
                icon=icon,
            )
            if text:
                st.caption(text)


if st.session_state.app_stage == 0:
    st.title("Hello, Streamlit!")
    st.write("Welcome")
    st.image("wel.png", width=200)

    show_game_links()
    st.divider()

    a = int(st.number_input(label = "ところで、好きな数字を一つ書いて下さい",
                            value = 0,
                            step = 1,
                            format="%d",
                            key="a"))
    b = int(st.number_input(label = "もう一つ",
                            value = 0,
                            step = 1,
                            format="%d",
                            key="b"))

    st.metric(label="これらの積", value=f"{a * b}")
    st.metric(label="これらの和", value=f"{a + b}")

    if a == 5 and b == 7:
        st.session_state.app_stage = 1
        st.rerun()

elif st.session_state.app_stage == 1:
    st.image("from-PixAI-2064196393477388158.png", width=500)

if st.button("reset"):
    st.session_state.app_stage = 0