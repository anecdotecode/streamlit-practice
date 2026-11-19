"""リバーシのAI。画面・Streamlitには依存しない。

内部はビットボード(64bit整数)で探索する。盤面(board.py)との変換は入口と出口だけ。
ビット位置は row*8 + col。

評価値は「自分の手数 − 相手の手数」「角の差」「石数差(終盤ほど重視)」の合成。
先読みの深さと、手の選び方(ソフトマックス温度 k)で5段階の強さを作る。
  k < 0 : 評価の低い手を選びやすい
  k = 0 : 完全ランダム
  k > 0 : 評価の高い手を選びやすい
  k = None : 評価最大の手(同点はランダム)
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass

from reversi.board import BLACK, SIZE, WHITE, Board, Move, opponent

FULL = (1 << 64) - 1
_NOT_C0 = 0xFEFEFEFEFEFEFEFE  # 列0を除く
_NOT_C7 = 0x7F7F7F7F7F7F7F7F  # 列7を除く

# (シフト量, 折り返し除去マスク)。左シフトは64bitに収める。
_LEFT = (
    (1, _NOT_C0),            # 東   (r,   c+1)
    (8, FULL),               # 南   (r+1, c)
    (9, _NOT_C0 & FULL),     # 南東 (r+1, c+1)
    (7, _NOT_C7 & FULL),     # 南西 (r+1, c-1)
)
_RIGHT = (
    (1, _NOT_C7),            # 西   (r,   c-1)
    (8, FULL),               # 北   (r-1, c)
    (7, _NOT_C0),            # 北東 (r-1, c+1)
    (9, _NOT_C7),            # 北西 (r-1, c-1)
)

_CORNER_MASK = (1 << 0) | (1 << 7) | (1 << 56) | (1 << 63)


def _build_groups() -> tuple[int, int, int, int]:
    """探索順(α-β枝刈りの効率用)のマス群: 角 → 辺 → 内側・C → X。"""
    groups = [0, 0, 0, 0]
    for r in range(SIZE):
        for c in range(SIZE):
            edge_r = r in (0, SIZE - 1)
            edge_c = c in (0, SIZE - 1)
            near_r = r in (1, SIZE - 2)
            near_c = c in (1, SIZE - 2)
            if edge_r and edge_c:
                p = 0
            elif near_r and near_c:
                p = 3
            elif (edge_r and near_c) or (edge_c and near_r):
                p = 2
            elif edge_r or edge_c:
                p = 1
            else:
                p = 2
            groups[p] |= 1 << (r * SIZE + c)
    return tuple(groups)  # type: ignore[return-value]


_GROUPS = _build_groups()

try:
    _popcount = int.bit_count  # Python 3.10+
except AttributeError:  # pragma: no cover
    def _popcount(x: int) -> int:
        return bin(x).count("1")

MOBILITY_WEIGHT = 1.0
CORNER_WEIGHT = 10.0
DISC_WEIGHT = 1.0  # 終盤に向けて 0 → この値へ増える
WIN_BONUS = 1000.0  # 終局時の勝敗ボーナス
SCORE_CLIP = 60.0  # 確率抽選のときだけ評価値をこの範囲に丸める


@dataclass(frozen=True)
class Level:
    name: str
    depth: int
    k: float | None
    endgame_empties: int = 0  # 空きマスがこれ以下なら終局まで全探索


LEVELS: dict[str, Level] = {
    "激よわ": Level("激よわ", depth=1, k=-0.3),
    "よわ": Level("よわ", depth=1, k=0.0),
    "ふつー": Level("ふつー", depth=2, k=0.3),
    "つよ": Level("つよ", depth=4, k=1.0),
    "げきつよ": Level("げきつよ", depth=6, k=None, endgame_empties=10),
}


# ---------------------------------------------------------------- ビットボード

def to_bitboards(board: Board, player: int) -> tuple[int, int]:
    """(player の石, 相手の石) のビットボード。"""
    enemy = opponent(player)
    mine = theirs = 0
    for r in range(SIZE):
        for c in range(SIZE):
            v = board[r][c]
            if v == player:
                mine |= 1 << (r * SIZE + c)
            elif v == enemy:
                theirs |= 1 << (r * SIZE + c)
    return mine, theirs


def legal_bits(p: int, o: int) -> int:
    """p が置けるマスのビット集合。"""
    empty = ~(p | o) & FULL
    res = 0
    for n, mask in _LEFT:
        t = ((p << n) & mask) & o
        t |= ((t << n) & mask) & o
        t |= ((t << n) & mask) & o
        t |= ((t << n) & mask) & o
        t |= ((t << n) & mask) & o
        t |= ((t << n) & mask) & o
        res |= ((t << n) & mask) & empty
    for n, mask in _RIGHT:
        t = ((p >> n) & mask) & o
        t |= ((t >> n) & mask) & o
        t |= ((t >> n) & mask) & o
        t |= ((t >> n) & mask) & o
        t |= ((t >> n) & mask) & o
        t |= ((t >> n) & mask) & o
        res |= ((t >> n) & mask) & empty
    return res


def flip_bits(p: int, o: int, move: int) -> int:
    """p が move(1ビット)に置いたとき反転する石のビット集合。"""
    flipped = 0
    for n, mask in _LEFT:
        line = 0
        x = (move << n) & mask
        while x & o:
            line |= x
            x = (x << n) & mask
        if x & p:
            flipped |= line
    for n, mask in _RIGHT:
        line = 0
        x = (move >> n) & mask
        while x & o:
            line |= x
            x = (x >> n) & mask
        if x & p:
            flipped |= line
    return flipped


# ---------------------------------------------------------------- 評価と探索

def _terminal_value(p: int, o: int) -> float:
    diff = _popcount(p) - _popcount(o)
    if diff > 0:
        return WIN_BONUS + diff
    if diff < 0:
        return -WIN_BONUS + diff
    return 0.0


def _evaluate(p: int, o: int, my_moves: int) -> float:
    """p 視点の評価値。my_moves は p の合法手数。"""
    mobility = my_moves - _popcount(legal_bits(o, p))
    corners = _popcount(p & _CORNER_MASK) - _popcount(o & _CORNER_MASK)
    empties = 64 - _popcount(p | o)
    disc_diff = _popcount(p) - _popcount(o)
    disc_w = DISC_WEIGHT * (60 - empties) / 60
    return MOBILITY_WEIGHT * mobility + CORNER_WEIGHT * corners + disc_w * disc_diff


def _search(p: int, o: int, depth: int, alpha: float, beta: float) -> float:
    """negamax + α-β。p が手番の盤面の、p 視点の値を返す。"""
    moves = legal_bits(p, o)
    if not moves:
        if not legal_bits(o, p):
            return _terminal_value(p, o)
        # パス: 深さは消費しない
        return -_search(o, p, depth, -beta, -alpha)
    if depth == 0:
        return _evaluate(p, o, _popcount(moves))
    best = -math.inf
    for group in _GROUPS:
        sub = moves & group
        while sub:
            m = sub & -sub
            sub ^= m
            f = flip_bits(p, o, m)
            value = -_search(o & ~f, p | m | f, depth - 1, -beta, -alpha)
            if value > best:
                best = value
                if best > alpha:
                    alpha = best
                    if alpha >= beta:
                        return best
    return best


def score_moves(
    board: Board,
    player: int,
    level: Level,
    exact: bool = True,
) -> dict[Move, float]:
    """各合法手の評価値(player 視点)。

    exact=True : 全手を正確に評価する。
    exact=False: 最大値(同点含む)だけが正確。それ未満の手は上限値で、最善手の選択には影響しない。
    """
    p, o = to_bitboards(board, player)
    empties = 64 - _popcount(p | o)
    depth = 99 if empties <= level.endgame_empties else level.depth
    moves = legal_bits(p, o)
    scores: dict[Move, float] = {}
    best = -math.inf
    sub = moves
    while sub:
        m = sub & -sub
        sub ^= m
        f = flip_bits(p, o, m)
        if exact:
            value = -_search(o & ~f, p | m | f, depth - 1, -math.inf, math.inf)
        else:
            # best より真に悪い手は打ち切る。同点は正確に求める。
            floor = best - 1e-9
            value = -_search(o & ~f, p | m | f, depth - 1, -math.inf, -floor)
            if value > best:
                best = value
        idx = m.bit_length() - 1
        scores[(idx // SIZE, idx % SIZE)] = value
    return scores


def choose_move(
    board: Board,
    player: int,
    level: Level | str,
    rng: random.Random | None = None,
) -> Move | None:
    """player の着手を選ぶ。合法手がなければ None。"""
    if isinstance(level, str):
        level = LEVELS[level]
    rng = rng or random.Random()
    scores = score_moves(board, player, level, exact=level.k is not None)
    if not scores:
        return None
    moves = list(scores)
    if level.k is None:
        top = max(scores.values())
        return rng.choice([m for m in moves if scores[m] == top])
    clipped = [max(-SCORE_CLIP, min(SCORE_CLIP, scores[m])) for m in moves]
    # k>0 は高評価、k<0 は低評価を選びやすい。k=0 は一様。
    ref = max(level.k * s for s in clipped)
    weights = [math.exp(level.k * s - ref) for s in clipped]
    return rng.choices(moves, weights=weights, k=1)[0]
