import streamlit as st
import json
from pathlib import Path

# タイトル
st.title("High & Low Game")

# JSONファイルを読み込む
json_path = Path(__file__).parent.parent / "sample_data" / "highAndLow.json"

with open(json_path, "r", encoding="utf-8") as f:
    data = json.load(f)

# カードの情報
base_card = data["base_card"]
result_card = data["result_card"]

st.write("次のカードは大きい？ 小さい？")

# 最初のカードを表示
st.write("最初のカード")
st.header(
    f"{base_card['suit']} {base_card['rank']}"
)

# 次のカードを表示
st.write("次のカード")
st.header(
    f"{result_card['suit']} {result_card['rank']}"
)

st.button("High") 
