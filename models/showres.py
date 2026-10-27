import streamlit as st

def show():
    if st.session_state.message:
        st.write(st.session_state.message)