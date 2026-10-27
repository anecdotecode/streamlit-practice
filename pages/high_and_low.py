import streamlit as st
import json
from pathlib import Path

from models.launch import launch
from models.judge import judge
from models.draw import draw
from models.showres import show

launch()

json_path = Path(__file__).parent.parent / "sample_data" / "highAndLow.json"
with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

draw(data)

if st.session_state.get("finished"):
    st.write(st.session_state.message)
    st.title(f"全部やった。もうカードはないよ。総得点は{st.session_state.point}点で正答率は{float(int(st.session_state.score/st.session_state.all * 1000))/10}％だよ")
    if st.button("もう一回やるならここをクリック"):
        st.session_state.finished = False
        st.session_state.already = [0] * 52
    st.stop()

judge()
show()



