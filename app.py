import streamlit as st
st.title("Hello, Streamlit!")
st.write("これは最小構成の Streamlit アプリです。")
st.image("from-PixAI-2064196393477388158.png", width=200)

a = st.number_input("ところで、好きな数字を一つ書いて下さい")
b = st.number_input("もう一つ")

st.title("これらの積は%.2fです" % (float(a)*float(b)))