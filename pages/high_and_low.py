import streamlit as st
import json
from pathlib import Path
import random

# タイトル
st.title("High & Low Game")
if "check" not in st.session_state:
    st.session_state.check = True
if "guess" not in st.session_state:
    st.session_state.guess = ""
if "answer" not in st.session_state:
    st.session_state.answer = ""

# JSONファイルを読み 込む
json_path = Path(__file__).parent.parent / "sample_data" / "highAndLow.json"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# カードの情報
if st.session_state.check:
    st.session_state.pair = random.choice(data)
    st.session_state.check = False

st.session_state.base = st.session_state.pair["base_card"]
st.session_state.result = st.session_state.pair["result_card"]

st.title(f"場のカード: {st.session_state.base['suit']} の {st.session_state.base['rank']}")

st.session_state.guess = st.text_input("high, low or draw:")

if(st.session_state.result["rank"] > st.session_state.base["rank"]):
    st.session_state.answer = "high"
elif(st.session_state.result["rank"] < st.session_state.base["rank"]):
    st.session_state.answer = "low"
else:
    st.session_state.answer = "draw"

if(st.session_state.guess != ""):
    if(st.session_state.answer == st.session_state.guess):
        st.title("正解")
        st.title(f"答え: {st.session_state.result['suit']} の {st.session_state.result['rank']}")
        st.session_state.check = True
        st.session_state.guess != "empty"
    else:
        st.title("不正解")
        st.title(f"答え: {st.session_state.result['suit']} の {st.session_state.result['rank']}")
        st.session_state.check = True
        st.session_state.guess != "empty"




