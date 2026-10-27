import streamlit as st

# 初期化
def launch():
    st.title("High & Low Game")
    if "check" not in st.session_state:
        st.session_state.check = True
    if "guess" not in st.session_state:
        st.session_state.guess = ""
    if "answer" not in st.session_state:
        st.session_state.answer = ""
    if "message" not in st.session_state:         
        st.session_state.message = ""
    if "all" not in st.session_state:
        st.session_state.all = 0
    if "point" not in st.session_state:
        st.session_state.point = 0
    if "score" not in st.session_state:
        st.session_state.score = 0
    if "already" not in st.session_state:
        st.session_state.already = [0] * 52
    st.title(f"得点:{st.session_state.point}\n問題数:{st.session_state.all}\n正解数:{st.session_state.score}\n誤答数:{st.session_state.all - st.session_state.score}")
    if "finished" not in st.session_state:
        st.session_state.finished = False