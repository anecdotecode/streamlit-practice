import streamlit as st

def judge():
    SUIT_COLOR = {"spades": "inherit", "clubs": "inherit", "hearts": "#d62828", "diamonds": "#d62828"}
    SUIT_MARK  = {"spades": "♠", "hearts": "♥", "diamonds": "♦", "clubs": "♣"}
    SIZE = {"high":"#d67f28","draw":"inherient","low":"#28bcd6"}
    st.session_state.guess = ""
    if(st.session_state.result["rank"] > st.session_state.enemy["rank"]):
        st.session_state.answer = "high"
    elif(st.session_state.result["rank"] < st.session_state.enemy["rank"]):
        st.session_state.answer = "low"
    else:
        st.session_state.answer = "draw"

    a,b,c = st.columns(3, vertical_alignment='center')
    st.markdown("""
                <style>
                .st-key-high button p { color: #d67f28; font-size: 24px !important;  }
                .st-key-high button { width: 200px; height: 80px; }
                .st-key-draw button p { color: inherient;font-size: 24px !important; }
                .st-key-draw button { width: 200px; height: 80px; }
                .st-key-low button p { color: #28bcd6; font-size: 24px !important;}
                .st-key-low button { width: 200px; height: 80px; }
                </style>
                """,
                unsafe_allow_html=True)
    with a:
        if(st.button("high",key= "high",disabled= st.session_state.check)):
            st.session_state.guess = "high"
    with b:
        if(st.button("draw",key= "draw",disabled= st.session_state.check)):
            st.session_state.guess = "draw"
    with c:
        if(st.button("low",key="low",disabled= st.session_state.check)):
            st.session_state.guess = "low"
    if(st.session_state.guess in ("high","low","draw")):
        if(st.session_state.answer == st.session_state.guess):
            st.session_state.message = f"<h3 style='color:{"#d62879"}'>正解</h3>"
            if(st.session_state.guess == "draw"):
                st.session_state.point += 1
                st.session_state.point *= 2
            else:
                st.session_state.point += 1
            st.session_state.score += 1
            st.session_state.all += 1
            
        else:
            st.session_state.message = f"<h3 style='color:{"#2828d6"}'>不正解</h3>"
            st.session_state.all += 1
        e = st.session_state.result
        f = st.session_state.answer
        st.session_state.message += f"<h2>\n答え: <span style='color:{SUIT_COLOR[e['suit']]}'>{SUIT_MARK[e['suit']]} {e['rank']}</span>つまり<span style='color:{SIZE[f]}'>{f}</span>が答え</h2>"
        st.session_state.check = True
        st.rerun()        