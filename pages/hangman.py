import streamlit as st
from pathlib import Path
import string
import streamlit as st

stri = ""
img_path = Path(__file__).parent.parent / "imges" / "0.svg"
left,right = st.columns(2, vertical_alignment="center")
with left:
    st.image(img_path)
for i in range(2,9):
    stri += "_ "
with right:
    st.header(stri)

if "used" not in st.session_state:
    st.session_state.used = set()

cols = st.columns(9)
for i, ch in enumerate(string.ascii_uppercase):
    with cols[i % 9]:
        used = ch in st.session_state.used
        if st.button("❌" if used else ch, key=ch, disabled=used):
            st.session_state.used.add(ch)
            st.rerun()