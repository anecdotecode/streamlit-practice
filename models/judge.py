import streamlit as st

def judge():
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
        st.session_state.message += f"\n答え: {st.session_state.result["suit"]} の {st.session_state.result["rank"]}\nつまり{st.session_state.answer}が答え"
        st.session_state.check = True
        st.rerun()