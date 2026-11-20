import streamlit as st
from pathlib import Path
def clear():
    more = Path(__file__).parent.parent / "imges" / "more.png"
    if st.session_state.show_clear:
        st.title("CLEAR")
        left, right = st.columns(2, vertical_alignment='center')

        with left:
            st.markdown(f"<h4>The answer is <span style='color:{"#282bd6"}'>{st.session_state.quiz['word']}</span></h4>", unsafe_allow_html=True)
            st.markdown(f"<h4>And meanings in japanese is</h4>", unsafe_allow_html=True)
            st.markdown(f"<h4><span style='color:{"#39d628"}'>{st.session_state.quiz['mean']}</span></h4>", unsafe_allow_html=True)
        with right:
            st.image(more, width=230)
        if st.button("CONTINUE?"):
            st.session_state.imgnum = 0
            st.session_state.length = 0
            st.session_state.DoesQuizExist = False
            st.session_state.quiz = None
            st.session_state.used = set()
            st.session_state.show_clear = False
            st.rerun()