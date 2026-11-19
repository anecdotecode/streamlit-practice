"""盤面クリックの検証。画面・Streamlitには依存しない。

コンポーネントから返る値は、古い盤面・古いマス・二重送信・敵の手番のものが混じりうる。
「対局・手数・手番・合法手」がすべて一致するときだけ着手として受け付ける。
"""

from __future__ import annotations

from typing import Any, Iterable

from reversi.board import Move


def _is_int(x: Any) -> bool:
    return isinstance(x, int) and not isinstance(x, bool)


def accept_click(
    value: Any,
    *,
    game_id: str,
    ply: int,
    turn: int,
    legal: Iterable[Move],
) -> Move | None:
    """有効なクリックなら (row, col)、そうでなければ None。

    ply は「これまでに打たれた手数」で、着手のたびに必ず増える。
    したがって同じ (game_id, ply) のクリックは高々1回しか受理されず、
    二重送信や古い値の再送は ply の不一致で弾かれる。
    """
    if not isinstance(value, dict):
        return None
    if value.get("game_id") != game_id:
        return None
    if not _is_int(value.get("ply")) or value["ply"] != ply:
        return None
    if not _is_int(value.get("turn")) or value["turn"] != turn:
        return None
    r, c = value.get("r"), value.get("c")
    if not _is_int(r) or not _is_int(c):
        return None
    if (r, c) not in set(legal):
        return None
    return (r, c)
