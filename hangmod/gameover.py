import streamlit as st

def gameover():
    if st.session_state.show_gameover:
        st.title("GAME OVER")
        st.text(f"The answer is {st.session_state.quiz['word']}\nAnd meanings in japanese is {st.session_state.quiz['mean']}")
        if st.button("CONTINUE?"):
            st.session_state.imgnum = 0
            st.session_state.length = 0
            st.session_state.DoesQuizExist = False
            st.session_state.quiz = None
            st.session_state.used = set()
            st.session_state.show_gameover = False
        st.stop()