import streamlit as st

# 初期化
def launch():
    st.markdown(f"<h1><span style='color:{"#d67f28"}'>High</span> <span style='color:{"inherit"}'>&</span> <span style='color:{"#28bcd6"}'>Low</span> <span style='color:{"inherit"}'>Game<span></h1>",
                unsafe_allow_html=True,
                )
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
    if "finished" not in st.session_state:
        st.session_state.finished = False
    if "history" not in st.session_state:
        st.session_state.history = []