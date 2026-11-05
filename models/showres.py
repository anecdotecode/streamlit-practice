import streamlit as st

def show():
    if st.session_state.message:
        st.markdown(st.session_state.message,
                    unsafe_allow_html=True,)