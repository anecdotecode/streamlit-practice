import random
import unittest

from reversi.board import (
    BLACK, EMPTY, SIZE, WHITE,
    apply_move, count, flips, initial_board, is_game_over, is_legal,
    legal_moves, next_player, opponent, winner,
)


def make(rows):
    """文字列8行 ('.', 'B', 'W') から盤面を作る。"""
    table = {".": EMPTY, "B": BLACK, "W": WHITE}
    assert len(rows) == SIZE and all(len(r) == SIZE for r in rows)
    return tuple(tuple(table[ch] for ch in r) for r in rows)


class TestInitial(unittest.TestCase):
    def test_initial_position(self):
        b = initial_board()
        self.assertEqual(b[3][3], WHITE)
        self.assertEqual(b[3][4], BLACK)
        self.assertEqual(b[4][3], BLACK)
        self.assertEqual(b[4][4], WHITE)
        self.assertEqual(count(b, BLACK), 2)
        self.assertEqual(count(b, WHITE), 2)
        self.assertEqual(count(b, EMPTY), 60)

    def test_initial_legal_moves(self):
        b = initial_board()
        self.assertEqual(set(legal_moves(b, BLACK)), {(2, 3), (3, 2), (4, 5), (5, 4)})
        self.assertEqual(set(legal_moves(b, WHITE)), {(2, 4), (3, 5), (4, 2), (5, 3)})

    def test_opponent(self):
        self.assertEqual(opponent(BLACK), WHITE)
        self.assertEqual(opponent(WHITE), BLACK)
        with self.assertRaises(ValueError):
            opponent(EMPTY)


class TestMove(unittest.TestCase):
    def test_first_move_flips(self):
        b = apply_move(initial_board(), 2, 3, BLACK)
        self.assertEqual(b[2][3], BLACK)
        self.assertEqual(b[3][3], BLACK)
        self.assertEqual(count(b, BLACK), 4)
        self.assertEqual(count(b, WHITE), 1)

    def test_original_board_unchanged(self):
        b0 = initial_board()
        apply_move(b0, 2, 3, BLACK)
        self.assertEqual(b0, initial_board())

    def test_illegal_move_raises(self):
        b = initial_board()
        for r, c in [(0, 0), (3, 3), (3, 4), (2, 2)]:
            with self.assertRaises(ValueError):
                apply_move(b, r, c, BLACK)

    def test_out_of_range(self):
        b = initial_board()
        self.assertEqual(flips(b, -1, 0, BLACK), [])
        self.assertEqual(flips(b, 0, 8, BLACK), [])
        self.assertFalse(is_legal(b, 8, 8, BLACK))

    def test_multi_direction_flip(self):
        b = make([
            "........",
            "........",
            "..B.B.B.",
            "...WWW..",
            "..BW.WB.",
            "...WWW..",
            "..B.B.B.",
            "........",
        ])
        got = set(flips(b, 4, 4, BLACK))
        self.assertEqual(got, {(3, 4), (4, 3), (4, 5), (5, 4), (3, 3), (3, 5), (5, 3), (5, 5)})

    def test_no_flip_without_anchor(self):
        b = make([
            "........",
            "........",
            "........",
            "..WW....",
            "........",
            "........",
            "........",
            "........",
        ])
        self.assertEqual(flips(b, 3, 1, BLACK), [])

    def test_no_wraparound(self):
        # 右端の白は、左端の黒と挟めない(行をまたがない)
        b = make([
            "........",
            "........",
            "B.......",
            ".......W",
            "........",
            "........",
            "........",
            "........",
        ])
        self.assertEqual(flips(b, 2, 6, BLACK), [])
        self.assertEqual(flips(b, 3, 6, BLACK), [])

    def test_corner_move(self):
        b = make([
            "........",
            ".W......",
            "..B.....",
            "........",
            "........",
            "........",
            "........",
            "........",
        ])
        self.assertEqual(flips(b, 0, 0, BLACK), [(1, 1)])


class TestTurnAndEnd(unittest.TestCase):
    def test_normal_alternation(self):
        b = apply_move(initial_board(), 2, 3, BLACK)
        self.assertEqual(next_player(b, BLACK), WHITE)

    def test_pass_opponent_when_only_current_can_move(self):
        # 白は置けず、黒は(0,2)に置ける -> 黒が続ける(白をパス)
        b = make([
            "BW......",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
        ])
        self.assertEqual(legal_moves(b, WHITE), [])
        self.assertEqual(legal_moves(b, BLACK), [(0, 2)])
        self.assertEqual(next_player(b, BLACK), BLACK)

    def test_pass_opponent_when_only_white_can_move(self):
        # 黒は置けず、白は(0,3)に置ける -> 白が続ける(黒をパス)
        b = make([
            "BWB.....",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
        ])
        self.assertEqual(legal_moves(b, BLACK), [])
        self.assertEqual(legal_moves(b, WHITE), [(0, 3)])
        self.assertEqual(next_player(b, WHITE), WHITE)

    def test_opponent_can_move(self):
        b = make([
            "WB.....W",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
        ])
        self.assertEqual(legal_moves(b, WHITE), [(0, 2)])
        self.assertEqual(next_player(b, BLACK), WHITE)

    def test_end_when_nobody_can_move(self):
        b = make([
            "BW......",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
            "W.......",
        ])
        # 黒(0,2)は置ける -> 終了ではない
        self.assertIsNotNone(next_player(b, WHITE))
        b2 = make([
            "B.......",
            "........",
            "........",
            "........",
            "........",
            "........",
            "........",
            ".......W",
        ])
        self.assertIsNone(next_player(b2, BLACK))
        self.assertIsNone(next_player(b2, WHITE))
        self.assertTrue(is_game_over(b2))

    def test_game_over_and_winner(self):
        full_black = make(["BBBBBBBB"] * 8)
        self.assertTrue(is_game_over(full_black))
        self.assertEqual(winner(full_black), BLACK)
        tie = make(["BBBBBBBB"] * 4 + ["WWWWWWWW"] * 4)
        self.assertTrue(is_game_over(tie))
        self.assertIsNone(winner(tie))
        self.assertFalse(is_game_over(initial_board()))


class TestRandomPlayouts(unittest.TestCase):
    def test_random_games(self):
        rng = random.Random(12345)
        passes_seen = 0
        for _ in range(300):
            board = initial_board()
            player = BLACK
            moves = 0
            while True:
                legal = legal_moves(board, player)
                self.assertTrue(legal)
                r, c = rng.choice(legal)
                before = count(board, EMPTY)
                board = apply_move(board, r, c, player)
                moves += 1
                self.assertEqual(count(board, EMPTY), before - 1)
                self.assertEqual(count(board, BLACK) + count(board, WHITE) + count(board, EMPTY), 64)
                nxt = next_player(board, player)
                if nxt is None:
                    break
                if nxt == player:
                    passes_seen += 1
                player = nxt
            self.assertTrue(is_game_over(board))
            self.assertEqual(count(board, BLACK) + count(board, WHITE), 4 + moves)
        self.assertGreater(passes_seen, 0)


if __name__ == "__main__":
    unittest.main()
