import streamlit as st
import random
from PIL import Image
from models.image import make_card

def conv_shape_num(a)->int:
    if(a == "spades"):
        return 0
    if(a == "hearts"):
        return 1
    if(a == "diamonds"):
        return 2
    else:
        return 3

from pathlib import Path

def card_img(card):
    base = Path(__file__).parent.parent / 'hal_img'
    return make_card(base / f"{card['rank']}.png", base / f"{card['suit']}.png")

def draw(data):
    SUIT_COLOR = {"spades": "inherit", "clubs": "inherit", "hearts": "#d62828", "diamonds": "#d62828"}
    SUIT_MARK  = {"spades": "♠", "hearts": "♥", "diamonds": "♦", "clubs": "♣"}

    left,right = st.columns(2, vertical_alignment='center')


    if st.session_state.check:
        st.session_state.check = False

        if "result" in st.session_state:
            st.session_state.prev = st.session_state.enemy  
            st.session_state.enemy = st.session_state.result
        else:
            st.session_state.enemy = random.choice(data)
            st.session_state.history.append((st.session_state.enemy["suit"], st.session_state.enemy["rank"]))
            st.session_state.already[conv_shape_num(st.session_state.enemy["suit"])*13 + st.session_state.enemy["rank"] -1] = 1
        if sum(st.session_state.already) != 52:
            st.session_state.result = random.choice(data)
            while st.session_state.already[conv_shape_num(st.session_state.result["suit"])*13 + st.session_state.result["rank"] - 1] == 1:
                st.session_state.result = random.choice(data)
            st.session_state.already[conv_shape_num(st.session_state.result["suit"])*13 + st.session_state.result["rank"] - 1] = 1
            st.session_state.history.append((st.session_state.result["suit"], st.session_state.result["rank"]))
        else:
            st.session_state.all = 52
            st.session_state.finished = True
            
    e = st.session_state.enemy
    st.markdown(
        f"<h1>場のカード: <span style='color:{SUIT_COLOR[e['suit']]}'>{SUIT_MARK[e['suit']]} {e['rank']}</span></h1>",
        unsafe_allow_html=True,
    )
    h = st.session_state.history
    if len(h) != len(set(h)):
        st.error("重複を検出")
        st.write(h, st.session_state.already)
    if "prev" in st.session_state: 
        with left:
            st.image(card_img(st.session_state.prev),width=200)
    with right:
        st.image(card_img(st.session_state.enemy),width= 200)  