import streamlit as st
from PIL import Image

@st.cache_data
def make_card(art_path, suit):
    art = Image.open(art_path).convert("RGBA")
    suit_img = Image.open(suit).convert("RGBA")
    card = Image.alpha_composite(art, suit_img)
    return card.resize((400,661),Image.LANCZOS).convert("RGB") 