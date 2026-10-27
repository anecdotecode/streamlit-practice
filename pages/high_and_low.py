import streamlit as st
import json
from pathlib import Path
import random
from models.launch import launch
from models.judge import judge
# 初期化
launch()
def conv_shape_num(a)->int:
    if(a == "spades"):
        return 0
    if(a == "hearts"):
        return 1
    if(a == "diamonds"):
        return 2
    else:
        return 3

# JSONファイルを読み込む
json_path = Path(__file__).parent.parent / "sample_data" / "highAndLow.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# カードの情報
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
    
if st.session_state.get("finished"):
    st.write(st.session_state.message)
    st.title(f"全部やった。もうカードはないよ。総得点は{st.session_state.point}点で正答率は{float(int(st.session_state.score/st.session_state.all * 1000))/10}％だよ")
    if st.button("もう一回やるならここをクリック"):
        st.session_state.finished = False
        st.session_state.already = [0] * 52
    st.stop()

#main
st.title(f"場のカード: {st.session_state.enemy["suit"]} の {st.session_state.enemy["rank"]}")


if(st.session_state.result["rank"] > st.session_state.enemy["rank"]):
    st.session_state.answer = "high"
elif(st.session_state.result["rank"] < st.session_state.enemy["rank"]):
    st.session_state.answer = "low"
else:
    st.session_state.answer = "draw"

judge()

if st.session_state.message:
    st.write(st.session_state.message)



