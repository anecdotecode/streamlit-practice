"""漢字リバーシ(Streamlit ページ)。

ロジックは reversi/ にあり、このファイルは表示と session_state の受け渡しだけを行う。
画面の並び: 盤面 → 状態 → 漢字予想欄(自分の手番のみ) → 最初から遊ぶ → (敵の手番の処理)。
「最初から遊ぶ」を敵の待機(sleep)より前に描くことで、待機中でも押せる。
"""

import time

import streamlit as st

from reversi.ai import LEVELS
from reversi.board import BLACK, WHITE
from reversi.component import reversi_board
from reversi.game import ENEMY, HUMAN, enemy_delay, new_game, outcome_text
from reversi.kanji import hint_cells, load_kanji

st.set_page_config(page_title="漢字リバーシ", page_icon="⚫")

STATE_KEY = "kanji_reversi_game"
COLORS = {"黒（先手）": BLACK, "白（後手）": WHITE}


def show_setup():
    st.title("漢字リバーシ")
    st.write(
        "リバーシで盤面を奪い合いながら、盤面に隠れた漢字を推理して当てるゲームです。"
        "リバーシに勝てば勝ち。負けても、漢字を当てれば勝ちです。"
        "漢字は、あなたの石の上にだけ一部が見えます。"
    )
    with st.form("kanji_reversi_setup"):
        color = st.radio("自分の色", list(COLORS), horizontal=True)
        level = st.radio("敵の強さ", list(LEVELS), index=2, horizontal=True)
        started = st.form_submit_button("対戦開始")
    if started:
        st.session_state[STATE_KEY] = new_game(COLORS[color], level, load_kanji())
        st.rerun()


def show_status(game):
    if game.is_over:
        text = outcome_text(game)
        winner = game.outcome.winner
        if winner == HUMAN:
            st.success(text)
        elif winner == ENEMY:
            st.error(text)
        else:
            st.info(text)
        st.write(f"答えは「{game.answer}」でした。")
    elif game.is_enemy_turn:
        st.info("相手が考えています…")
    else:
        st.write("あなたの番です。")
    if game.notice:
        st.caption(game.notice)


def show_guess_form(game):
    with st.form(f"kanji_reversi_guess_{game.game_id}", clear_on_submit=True):
        text = st.text_input("漢字を予想（外れても続けられます）", key=f"kanji_reversi_text_{game.game_id}")
        submitted = st.form_submit_button("予想する")
    if submitted:
        game.guess(text)
        st.rerun()


def run_enemy_turn(game):
    """敵の手番なら、一定時間を置いて1手打ち、再描画する。"""
    if game.is_over or not game.is_enemy_turn:
        return
    t0 = time.perf_counter()
    move = game.choose_enemy_move()
    wait = enemy_delay(game.level_name, len(game.legal()), game.ply)
    rest = wait - (time.perf_counter() - t0)
    if rest > 0:
        time.sleep(rest)
    game.play_enemy_move(move)
    st.rerun()


def show_game(game):
    human_turn = game.is_human_turn
    click = reversi_board(
        board=game.board,
        human=game.human,
        turn=game.turn or 0,
        enabled=human_turn,
        legal=game.legal() if human_turn else [],
        hint=hint_cells(game.board, game.human),
        glyph=game.answer,
        game_id=game.game_id,
        ply=game.ply,
        key=f"kanji_reversi_board_{game.game_id}",
    )
    if human_turn and click is not None and game.human_move(click):
        st.rerun()

    show_status(game)
    if game.is_human_turn:
        show_guess_form(game)
    if st.button("最初から遊ぶ"):
        st.session_state.pop(STATE_KEY, None)
        st.rerun()
    run_enemy_turn(game)


_game = st.session_state.get(STATE_KEY)
if _game is None:
    show_setup()
else:
    show_game(_game)
