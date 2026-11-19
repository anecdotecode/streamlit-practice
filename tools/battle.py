"""AI同士の対戦で強さの順序を確認する。 python -m tools.battle"""

import random
import sys
import time

from reversi.ai import LEVELS, choose_move
from reversi.board import BLACK, WHITE, apply_move, count, initial_board, next_player


def play(black_level, white_level, rng):
    board, player = initial_board(), BLACK
    levels = {BLACK: black_level, WHITE: white_level}
    while player is not None:
        r, c = choose_move(board, player, levels[player], rng)
        board = apply_move(board, r, c, player)
        player = next_player(board, player)
    b, w = count(board, BLACK), count(board, WHITE)
    return BLACK if b > w else WHITE if w > b else None


def match(strong, weak, games, seed=0):
    """strong 側の(勝, 分, 負)。先後を半分ずつ入れ替える。"""
    rng = random.Random(seed)
    win = draw = lose = 0
    for i in range(games):
        if i % 2 == 0:
            res = play(strong, weak, rng)
            strong_color = BLACK
        else:
            res = play(weak, strong, rng)
            strong_color = WHITE
        if res is None:
            draw += 1
        elif res == strong_color:
            win += 1
        else:
            lose += 1
    return win, draw, lose


if __name__ == "__main__":
    games = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    names = list(LEVELS)
    for weak, strong in zip(names, names[1:]):
        n = max(6, games // 2) if strong == "げきつよ" else games
        t0 = time.time()
        w, d, l = match(strong, weak, n)
        print(f"{strong} vs {weak}: {w}勝 {d}分 {l}敗 ({n}戦, {time.time() - t0:.0f}秒)", flush=True)
