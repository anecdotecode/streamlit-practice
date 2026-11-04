import streamlit as st

def launch():
    if 'imgnum' not in st.session_state:
        st.session_state.imgnum = 0

    if 'length' not in st.session_state:
        st.session_state.length = 0

    if 'DoesQuizExist' not in st.session_state:
        st.session_state.DoesQuizExist = False

    if 'tempans' not in st.session_state:
        st.session_state.tempans = []

    if 'quiz' not in st.session_state:
        st.session_state.quiz = None

    if 'used' not in st.session_state:
        st.session_state.used = set()

    if 'show_gameover' not in st.session_state:
        st.session_state.show_gameover = False

    if 'show_clear' not in st.session_state:
            st.session_state.show_clear = False