import streamlit as st
import json
from pathlib import Path
import string
import random
from hangmod.launch import launch
from hangmod.gameover import gameover
from hangmod.clear import clear

launch()
gameover()       
clear()

imgname = str(st.session_state.imgnum) + '.svg'
img_path = Path(__file__).parent.parent / 'imges' / imgname
wordlist_path = Path(__file__).parent.parent/ 'sample_data'/ 'hangman.json'

with open(wordlist_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

if not st.session_state.DoesQuizExist:
    st.session_state.quiz = random.choice(data)

leng = len(st.session_state.quiz['word'])

if not st.session_state.DoesQuizExist:
    st.session_state.tempans.clear()
    for i in range(0,leng):
        st.session_state.tempans.append('_ ')
    st.session_state.DoesQuizExist = True
left,right = st.columns(2, vertical_alignment='center')
with left:
    st.image(img_path)
with right:
    s_new = ''.join(st.session_state.tempans)
    st.header(s_new)


cols = st.columns(9)
for i, ch in enumerate(string.ascii_uppercase):
    with cols[i % 9]:
        used = ch in st.session_state.used
        st.markdown("""
                    <style>
                    [data-testid="stBaseButton-secondary"] p { color: inherit !important; font-size: 24px !important; }
                    [data-testid="stBaseButton-secondary"] { width: 50px; height: 50px; }
                    </style>
                    """, unsafe_allow_html=True)

        if st.button('❌' if used else ch, key=ch, disabled=used):
            st.session_state.used.add(ch)
            num = st.session_state.quiz['word'].count(ch.lower())
            if not 0 == num:
                countwords = 0
                countall = 0
                st.session_state.length += num
                while countwords != st.session_state.quiz['word'].count(ch.lower()):
                    if  st.session_state.quiz['word'][countall] == ch.lower():
                        st.session_state.tempans[countall] = ch.lower() + ' '
                        countwords += 1
                    countall += 1
            else:
                st.session_state.imgnum += 1
            if st.session_state.imgnum == 8:
                st.session_state.length = 0
                st.session_state.show_gameover = True

            if st.session_state.length == leng:
                st.session_state.length = 0
                st.session_state.show_clear = True
            st.rerun()
