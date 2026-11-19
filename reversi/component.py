"""盤面コンポーネントの Python 側ラッパー。

streamlit は呼び出し時に初めて読み込む(テストや段階1〜3のコードが streamlit なしで動くように)。
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from reversi.board import Board, Move

_FRONTEND = Path(__file__).resolve().parent / "frontend"
_component = None


def _get_component():
    global _component
    if _component is None:
        import streamlit.components.v1 as components

        _component = components.declare_component("reversi_board", path=str(_FRONTEND))
    return _component


def reversi_board(
    *,
    board: Board,
    human: int,
    turn: int,
    enabled: bool,
    legal: list[Move],
    hint: list[Move],
    glyph: str,
    game_id: str,
    ply: int,
    key: str | None = None,
) -> Any:
    """盤面を表示し、クリックがあれば {game_id, ply, turn, r, c, nonce}、なければ None を返す。

    戻り値は検証前の生の値。必ず reversi.click.accept_click を通すこと。
    enabled=False の間は、legal を渡しても黄色い点は出ず、クリックも送られない。
    """
    return _get_component()(
        board=[list(row) for row in board],
        human=human,
        turn=turn,
        enabled=enabled,
        legal=[list(m) for m in legal],
        hint=[list(m) for m in hint],
        glyph=glyph,
        game_id=game_id,
        ply=ply,
        key=key,
        default=None,
    )
