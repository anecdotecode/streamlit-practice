import streamlit as st
import json
from pathlib import Path
import random

# 初期化
st.title("High & Low Game")
if "check" not in st.session_state:
    st.session_state.check = True
if "guess" not in st.session_state:
    st.session_state.guess = ""
if "answer" not in st.session_state:
    st.session_state.answer = ""
if "message" not in st.session_state:         
    st.session_state.message = ""
if "all" not in st.session_state:
    st.session_state.all = 0
if "point" not in st.session_state:
    st.session_state.point = 0
if "score" not in st.session_state:
    st.session_state.score = 0

st.title(f"得点:{st.session_state.point}\n問題数:{st.session_state.all}\n正解数:{st.session_state.score}\n誤答数:{st.session_state.all - st.session_state.score}")

# JSONファイルを読み込む
json_path = Path(__file__).parent.parent / "sample_data" / "highAndLow.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# カードの情報
if st.session_state.check:
    st.session_state.pair = random.choice(data)
    st.session_state.check = False

    if "result" in st.session_state:
        st.session_state.base = st.session_state.result
    else:
        st.session_state.base = st.session_state.pair["base_card"]
    st.session_state.result = st.session_state.pair["result_card"]
    roop = st.session_state.base['rank'] == st.session_state.result['rank'] and st.session_state.base['suit'] == st.session_state.result['suit']
    if roop:
        while roop:
            st.session_state.pair = random.choice(data)
            st.session_state.result = st.session_state.pair["result_card"]
            roop = st.session_state.base['rank'] == st.session_state.result['rank'] and st.session_state.base['suit'] == st.session_state.result['suit']


        

st.title(f"場のカード: {st.session_state.base['suit']} の {st.session_state.base['rank']}")


if(st.session_state.result["rank"] > st.session_state.base["rank"]):
    st.session_state.answer = "high"
elif(st.session_state.result["rank"] < st.session_state.base["rank"]):
    st.session_state.answer = "low"
else:
    st.session_state.answer = "draw"

with st.form("f", clear_on_submit=True):
    st.session_state.guess = st.text_input("high, low or draw:")
    submitted = st.form_submit_button("送信")

if(submitted and st.session_state.guess in ("high","low","draw")):
    if(st.session_state.answer == st.session_state.guess):
        st.session_state.message = "正解"
        if(st.session_state.guess == "draw"):
            st.session_state.point += 1
            st.session_state.point *= 2
        else:
            st.session_state.point += 1
            st.session_state.score += 1
        st.session_state.all += 1
        
    else:
       st.session_state.message = "不正解"
       st.session_state.all += 1
    st.session_state.message += f"\n答え: {st.session_state.result['suit']} の {st.session_state.result['rank']}\nつまり{st.session_state.answer}が答え"
    st.session_state.check = True
    st.rerun() 

if st.session_state.message:
    st.write(st.session_state.message)



