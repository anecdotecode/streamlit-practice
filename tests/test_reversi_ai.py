import math
import random
import unittest

from reversi.ai import (
    CORNER_WEIGHT, DISC_WEIGHT, LEVELS, MOBILITY_WEIGHT, WIN_BONUS,
    Level, choose_move, flip_bits, legal_bits, score_moves, to_bitboards,
)
from reversi.board import (
    BLACK, EMPTY, SIZE, WHITE,
    apply_move, count, flips, initial_board, legal_moves, next_player, opponent,
)


# ---------------------------------------------------------------- 補助

def random_positions(seed, games, min_moves=0, max_moves=60, max_empties=None):
    """ランダム対局の途中局面 (board, 手番) を集める。手番側には合法手がある。"""
    rng = random.Random(seed)
    out = []
    for _ in range(games):
        board, player = initial_board(), BLACK
        history = [(board, player)]
        while True:
            lm = legal_moves(board, player)
            r, c = rng.choice(lm)
            board = apply_move(board, r, c, player)
            player = next_player(board, player)
            if player is None:
                break
            history.append((board, player))
        for i, (b, p) in enumerate(history):
            if not (min_moves <= i <= max_moves):
                continue
            if max_empties is not None and count(b, EMPTY) > max_empties:
                continue
            out.append((b, p))
    return out


def corner_count(board, player):
    cs = [board[0][0], board[0][7], board[7][0], board[7][7]]
    return cs.count(player) - cs.count(opponent(player))


def ref_terminal(board, player):
    diff = count(board, player) - count(board, opponent(player))
    if diff > 0:
        return WIN_BONUS + diff
    if diff < 0:
        return -WIN_BONUS + diff
    return 0.0


def ref_eval(board, player, my_moves):
    enemy = opponent(player)
    mobility = my_moves - len(legal_moves(board, enemy))
    corners = corner_count(board, player)
    empties = count(board, EMPTY)
    disc_diff = count(board, player) - count(board, enemy)
    disc_w = DISC_WEIGHT * (60 - empties) / 60
    return MOBILITY_WEIGHT * mobility + CORNER_WEIGHT * corners + disc_w * disc_diff


def ref_search(board, player, depth):
    """枝刈りなしの素朴な negamax(board.py のみ使用)。"""
    moves = legal_moves(board, player)
    if not moves:
        if not legal_moves(board, opponent(player)):
            return ref_terminal(board, player)
        return -ref_search(board, opponent(player), depth)
    if depth == 0:
        return ref_eval(board, player, len(moves))
    return max(
        -ref_search(apply_move(board, r, c, player), opponent(player), depth - 1)
        for r, c in moves
    )


def ref_scores(board, player, depth):
    return {
        (r, c): -ref_search(apply_move(board, r, c, player), opponent(player), depth - 1)
        for r, c in legal_moves(board, player)
    }


def ref_final_diff(board, player):
    """双方最善で終局まで進めたときの石数差(player 視点)。"""
    moves = legal_moves(board, player)
    if not moves:
        if not legal_moves(board, opponent(player)):
            return count(board, player) - count(board, opponent(player))
        return -ref_final_diff(board, opponent(player))
    return max(
        -ref_final_diff(apply_move(board, r, c, player), opponent(player))
        for r, c in moves
    )


# ---------------------------------------------------------------- ビットボード

class TestBitboard(unittest.TestCase):
    def test_legal_and_flips_match_board(self):
        for board, player in random_positions(1, 40):
            for p in (BLACK, WHITE):
                mine, theirs = to_bitboards(board, p)
                bits = legal_bits(mine, theirs)
                got = {(i // SIZE, i % SIZE) for i in range(64) if bits >> i & 1}
                self.assertEqual(got, set(legal_moves(board, p)))
                for r, c in got:
                    m = 1 << (r * SIZE + c)
                    fb = flip_bits(mine, theirs, m)
                    fl = {(i // SIZE, i % SIZE) for i in range(64) if fb >> i & 1}
                    self.assertEqual(fl, set(flips(board, r, c, p)))

    def test_initial_bitboards(self):
        mine, theirs = to_bitboards(initial_board(), BLACK)
        self.assertEqual(bin(mine).count("1"), 2)
        self.assertEqual(bin(theirs).count("1"), 2)
        self.assertEqual(mine & theirs, 0)


# ---------------------------------------------------------------- 探索の正しさ

class TestSearch(unittest.TestCase):
    def test_scores_match_reference(self):
        positions = random_positions(2, 6, min_moves=0, max_moves=50)
        rng = random.Random(0)
        rng.shuffle(positions)
        for depth in (1, 2, 3):
            lv = Level("t", depth=depth, k=0.0)
            for board, player in positions[:25]:
                got = score_moves(board, player, lv)
                want = ref_scores(board, player, depth)
                self.assertEqual(set(got), set(want))
                for m in want:
                    self.assertAlmostEqual(got[m], want[m], places=9)

    def test_endgame_scores_match_reference(self):
        lv = Level("t", depth=1, k=0.0, endgame_empties=6)
        for board, player in random_positions(3, 30, max_empties=6)[:40]:
            got = score_moves(board, player, lv)
            want = ref_scores(board, player, 99)
            for m in want:
                self.assertAlmostEqual(got[m], want[m], places=9)

    def test_inexact_keeps_best(self):
        for name in ("つよ", "げきつよ"):
            lv = LEVELS[name]
            for board, player in random_positions(4, 4, min_moves=20, max_moves=45)[:10]:
                full = score_moves(board, player, lv, exact=True)
                part = score_moves(board, player, lv, exact=False)
                top = max(full.values())
                self.assertEqual(max(part.values()), top)
                self.assertEqual(
                    {m for m, v in full.items() if v == top},
                    {m for m, v in part.items() if v == top},
                )


# ---------------------------------------------------------------- 着手選択

class TestChoose(unittest.TestCase):
    def test_always_legal_all_levels(self):
        positions = random_positions(5, 3, min_moves=0, max_moves=60)
        rng = random.Random(7)
        rng.shuffle(positions)
        for name in LEVELS:
            for board, player in positions[:12]:
                m = choose_move(board, player, name, random.Random(1))
                self.assertIn(m, legal_moves(board, player))

    def test_none_when_no_moves(self):
        board = tuple(tuple(BLACK for _ in range(8)) for _ in range(8))
        for name in LEVELS:
            self.assertIsNone(choose_move(board, WHITE, name))

    def test_accepts_level_object_and_name(self):
        b = initial_board()
        self.assertIn(choose_move(b, BLACK, LEVELS["よわ"], random.Random(0)), legal_moves(b, BLACK))
        self.assertIn(choose_move(b, BLACK, "よわ", random.Random(0)), legal_moves(b, BLACK))

    def test_strongest_picks_argmax(self):
        lv = LEVELS["げきつよ"]
        for board, player in random_positions(6, 3, min_moves=10, max_moves=40)[:6]:
            scores = score_moves(board, player, lv, exact=True)
            top = max(scores.values())
            best = {m for m, v in scores.items() if v == top}
            for seed in range(5):
                self.assertIn(choose_move(board, player, lv, random.Random(seed)), best)

    def test_endgame_is_optimal(self):
        lv = LEVELS["げきつよ"]
        checked = 0
        for board, player in random_positions(8, 40, max_empties=8):
            m = choose_move(board, player, lv, random.Random(0))
            child = apply_move(board, *m, player)
            got = -ref_final_diff(child, opponent(player))
            want = max(
                -ref_final_diff(apply_move(board, r, c, player), opponent(player))
                for r, c in legal_moves(board, player)
            )
            self.assertEqual(got, want)
            checked += 1
            if checked >= 25:
                break
        self.assertGreater(checked, 5)

    def test_k_controls_preference(self):
        board, player = initial_board(), BLACK
        # 初手は4手とも対称で同点になるので、2手目の局面を使う
        board = apply_move(board, 2, 3, BLACK)
        player = WHITE
        scores = score_moves(board, player, Level("t", depth=2, k=0.0))
        self.assertGreater(len(set(scores.values())), 1)
        best = max(scores, key=scores.get)
        worst = min(scores, key=scores.get)

        def freq(k, target):
            rng = random.Random(0)
            lv = Level("t", depth=2, k=k)
            n = 1500
            return sum(choose_move(board, player, lv, rng) == target for _ in range(n)) / n

        self.assertGreater(freq(1.0, best), freq(0.0, best))
        self.assertGreater(freq(0.0, best), freq(-1.0, best))
        self.assertGreater(freq(-1.0, worst), freq(0.0, worst))
        uniform = 1 / len(scores)
        self.assertAlmostEqual(freq(0.0, best), uniform, delta=0.05)

    def test_all_levels_defined(self):
        self.assertEqual(list(LEVELS), ["激よわ", "よわ", "ふつー", "つよ", "げきつよ"])


if __name__ == "__main__":
    unittest.main()
