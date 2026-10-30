import streamlit as st
import json
from pathlib import Path
import string
import streamlit as st
import random

stri = ""
if "imgnum" not in st.session_state:
    st.session_state.imgnum = 0

if "DoesQuizExist" not in st.session_state:
    st.session_state.DoseQuizExist = False
imgnum = 0

imgname = str(imgnum) + ".svg"
img_path = Path(__file__).parent.parent / "imges" / imgname
wordlist_path = Path(__file__).parent.parent/ "sample_data"/ "hangman.json"

with open(wordlist_path, "r", encoding="utf-8") as f:
    data = json.load(f)

if not st.session_state.DoseQuizExist:
    st.session_state.quiz = random.choice(data)
print(st.session_state.quiz)
leng = len(st.session_state.quiz["word"])
left,right = st.columns(2, vertical_alignment="center")
with left:
    st.image(img_path)
for i in range(0,leng):
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