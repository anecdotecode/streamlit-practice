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
st.markdown("""
<style>
[data-testid="stMetricValue"] { font-size: 28px; }
[data-testid="stMetricLabel"] p { font-size: 16px; }
[data-testid="stColumn"]:nth-child(1) [data-testid="stMetricValue"] { color: #f4af5f; }
[data-testid="stColumn"]:nth-child(4) [data-testid="stMetricValue"] { color: #00aaff; }
</style>
""", unsafe_allow_html=True)

p, a, s = st.session_state.point, st.session_state.all, st.session_state.score
c1, c2, c3, c4 = st.columns(4)
c1.metric("得点", p)
c2.metric("問題数", a)
c3.metric("正解数", s)
c4.metric("誤答数", a - s)
if st.session_state.get("finished"):
    st.markdown(st.session_state.message,
                unsafe_allow_html=True,
                )
    st.title(f"全部やった。もうカードはないよ。総得点は{st.session_state.point}点で正答率は{float(int(st.session_state.score/st.session_state.all * 1000))/10}％だよ")
    if st.button("もう一回やるならここをクリック"):
        st.session_state.clear()
    st.stop()

judge()
show()



