import streamlit as st
import math as mt

if "score" not in st.session_state:
    st.session_state.score = 0
a = 0
b = 0

if st.session_state.score == 0:
    st.title("Hello, Streamlit!")
    st.write("これは最小構成の Streamlit アプリです。")
    st.image("from-PixAI-2064196393477388158.png", width=200)

    a = int(st.number_input(label = "ところで、好きな数字を一つ書いて下さい",
                            value = 0,
                            step = 1,
                            format="%d",))
    b = int(st.number_input(label = "もう一つ",
                            value = 0,
                            step = 1,
                            format="%d",))

    st.metric(label="これらの積", value=f"{a * b}")
    st.metric(label="これらの和", value=f"{a + b}")

    if a == 5 and b == 7:
        st.session_state.score = 1
        st.rerun()

elif st.session_state.score == 1:
    st.image("from-PixAI-2064196393477388158.png", width=500)