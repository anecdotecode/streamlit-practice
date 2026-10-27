import streamlit as st
import random


def conv_shape_num(a)->int:
    if(a == "spades"):
        return 0
    if(a == "hearts"):
        return 1
    if(a == "diamonds"):
        return 2
    else:
        return 3


def draw(data):
    if st.session_state.check:
        st.session_state.check = False

    if "result" in st.session_state:
        st.session_state.enemy = st.session_state.result
    else:
        st.session_state.enemy = random.choice(data)
        st.session_state.already[conv_shape_num(st.session_state.enemy["suit"])*13 + st.session_state.enemy["rank"] -1] = 1

    if sum(st.session_state.already) != 52:
        st.session_state.result = random.choice(data)
        while st.session_state.already[conv_shape_num(st.session_state.result["suit"])*13 + st.session_state.result["rank"] - 1] == 1:   # 1) -1 を追加
            st.session_state.result = random.choice(data)
        st.session_state.already[conv_shape_num(st.session_state.result["suit"])*13 + st.session_state.result["rank"] - 1] = 1
    else:
        st.session_state.all = 52
        st.session_state.finished = True
    st.title(f"場のカード: {st.session_state.enemy["suit"]} の {st.session_state.enemy["rank"]}")
