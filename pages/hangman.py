import streamlit as st
import json
from pathlib import Path
import string
import streamlit as st
import random

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

if st.session_state.show_clear:
    st.title("CLEAR")
    if st.button("CONTINUE?"):
        st.session_state.imgnum = 0
        st.session_state.length = 0
        st.session_state.DoesQuizExist = False
        st.session_state.quiz = None
        st.session_state.used = set()
        st.session_state.show_clear = False
    st.stop()
imgname = str(st.session_state.imgnum) + '.svg'
img_path = Path(__file__).parent.parent / 'imges' / imgname
wordlist_path = Path(__file__).parent.parent/ 'sample_data'/ 'hangman.json'

with open(wordlist_path, 'r', encoding='utf-8') as f:
    data = json.load(f)

if not st.session_state.DoesQuizExist:
    st.session_state.quiz = random.choice(data)

print(st.session_state.quiz)
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
        if st.button('❌' if used else ch, key=ch, disabled=used):
            print(ch)
            st.session_state.used.add(ch)
            num = st.session_state.quiz['word'].count(ch.lower())
            if not 0 == num:
                countwords = 0
                print('a')
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
