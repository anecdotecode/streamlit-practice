"""リバーシの盤面ロジック。画面・Streamlitには依存しない。

盤面は 8x8 の tuple of tuple (不変)。値は EMPTY / BLACK / WHITE。
座標は (row, col)、0〜7。
"""

from __future__ import annotations

SIZE = 8
EMPTY = 0
BLACK = 1
WHITE = 2

Board = tuple[tuple[int, ...], ...]
Move = tuple[int, int]

_DIRECTIONS = (
    (-1, -1), (-1, 0), (-1, 1),
    (0, -1),           (0, 1),
    (1, -1),  (1, 0),  (1, 1),
)


def opponent(player: int) -> int:
    if player == BLACK:
        return WHITE
    if player == WHITE:
        return BLACK
    raise ValueError(f"invalid player: {player}")


def initial_board() -> Board:
    rows = [[EMPTY] * SIZE for _ in range(SIZE)]
    rows[3][3] = WHITE
    rows[3][4] = BLACK
    rows[4][3] = BLACK
    rows[4][4] = WHITE
    return tuple(tuple(r) for r in rows)


def _in_range(r: int, c: int) -> bool:
    return 0 <= r < SIZE and 0 <= c < SIZE


def flips(board: Board, r: int, c: int, player: int) -> list[Move]:
    """(r, c) に player が置いたとき反転する石の座標。置けなければ空リスト。"""
    if not _in_range(r, c) or board[r][c] != EMPTY:
        return []
    enemy = opponent(player)
    result: list[Move] = []
    for dr, dc in _DIRECTIONS:
        line: list[Move] = []
        rr, cc = r + dr, c + dc
        while _in_range(rr, cc) and board[rr][cc] == enemy:
            line.append((rr, cc))
            rr += dr
            cc += dc
        if line and _in_range(rr, cc) and board[rr][cc] == player:
            result.extend(line)
    return result


def legal_moves(board: Board, player: int) -> list[Move]:
    return [
        (r, c)
        for r in range(SIZE)
        for c in range(SIZE)
        if flips(board, r, c, player)
    ]


def is_legal(board: Board, r: int, c: int, player: int) -> bool:
    return bool(flips(board, r, c, player))


def apply_move(board: Board, r: int, c: int, player: int) -> Board:
    """着手後の新しい盤面を返す。不正な手は ValueError。元の盤面は変更しない。"""
    flipped = flips(board, r, c, player)
    if not flipped:
        raise ValueError(f"illegal move: ({r}, {c}) by {player}")
    rows = [list(row) for row in board]
    rows[r][c] = player
    for fr, fc in flipped:
        rows[fr][fc] = player
    return tuple(tuple(row) for row in rows)


def count(board: Board, player: int) -> int:
    return sum(row.count(player) for row in board)


def next_player(board: Board, current: int) -> int | None:
    """current が着手した直後に、次に打つ側を返す。

    相手に合法手があれば相手。なければ current(相手をパス)。
    どちらも打てなければ None(ゲーム終了)。
    """
    enemy = opponent(current)
    if legal_moves(board, enemy):
        return enemy
    if legal_moves(board, current):
        return current
    return None


def is_game_over(board: Board) -> bool:
    return not legal_moves(board, BLACK) and not legal_moves(board, WHITE)


def winner(board: Board) -> int | None:
    """石数の多い側。同数なら None(引き分け)。終了判定はしない。"""
    b, w = count(board, BLACK), count(board, WHITE)
    if b > w:
        return BLACK
    if w > b:
        return WHITE
    return None
