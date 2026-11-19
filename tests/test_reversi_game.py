import random
import unittest

from reversi.ai import LEVELS
from reversi.board import (
    BLACK, EMPTY, WHITE, apply_move, count, initial_board, is_game_over,
    legal_moves, opponent, winner,
)
from reversi.game import (
    DRAW, ENEMY, GUESS_CORRECT, GUESS_INVALID, GUESS_NOT_ALLOWED, GUESS_WRONG, HUMAN,
    Game, Outcome, enemy_delay, new_game, outcome_text,
)

KANJI = ["挨", "曖", "宛", "嵐", "畏"]


def click(game, move, **kw):
    v = {"game_id": game.game_id, "ply": game.ply, "turn": game.turn,
         "r": move[0], "c": move[1], "nonce": 1}
    v.update(kw)
    return v


class TestStart(unittest.TestCase):
    def test_black_human_starts(self):
        g = new_game(BLACK, "よわ", KANJI, random.Random(0))
        self.assertTrue(g.is_human_turn)
        self.assertFalse(g.is_enemy_turn)
        self.assertEqual(g.turn, BLACK)
        self.assertEqual(g.ply, 0)
        self.assertIn(g.answer, KANJI)
        self.assertEqual(g.board, initial_board())
        self.assertEqual(g.enemy_history, [])
        self.assertEqual(g.guesses, [])
        self.assertIsNone(g.outcome)

    def test_white_human_enemy_starts(self):
        g = new_game(WHITE, "よわ", KANJI, random.Random(0))
        self.assertTrue(g.is_enemy_turn)
        self.assertFalse(g.is_human_turn)
        self.assertEqual(g.turn, BLACK)
        self.assertEqual(g.enemy, BLACK)
        # 人間は敵の手番に着手できない
        self.assertFalse(g.human_move(click(g, (2, 3))))
        self.assertEqual(g.board, initial_board())

    def test_new_game_is_independent(self):
        a = new_game(BLACK, "よわ", KANJI)
        a.human_move(click(a, a.legal()[0]))
        a.guess("嵐")
        b = new_game(BLACK, "よわ", KANJI)
        self.assertNotEqual(a.game_id, b.game_id)
        self.assertEqual(b.board, initial_board())
        self.assertEqual((b.ply, b.guesses, b.enemy_history, b.notice), (0, [], [], ""))

    def test_invalid_args(self):
        with self.assertRaises(ValueError):
            new_game(BLACK, "つよつよ", KANJI)
        with self.assertRaises(ValueError):
            new_game(0, "よわ", KANJI)
        with self.assertRaises(ValueError):
            new_game(BLACK, "よわ", [])


class TestTurns(unittest.TestCase):
    def test_human_then_enemy_then_human(self):
        g = new_game(BLACK, "よわ", KANJI, random.Random(1))
        self.assertTrue(g.human_move(click(g, g.legal()[0])))
        self.assertTrue(g.is_enemy_turn)
        self.assertEqual(g.ply, 1)
        # 敵の手番では、人間のクリックは無効
        self.assertFalse(g.human_move(click(g, (0, 0))))
        g.enemy_move(random.Random(2))
        self.assertTrue(g.is_human_turn)
        self.assertEqual(g.ply, 2)
        self.assertEqual(len(g.enemy_history), 1)

    def test_invalid_clicks_do_not_change_state(self):
        g = new_game(BLACK, "よわ", KANJI)
        before = (g.board, g.ply, g.turn)
        legal = g.legal()[0]
        for v in (None, {}, click(g, (0, 0)), click(g, legal, ply=5),
                  click(g, legal, game_id="x"), click(g, legal, turn=WHITE)):
            self.assertFalse(g.human_move(v))
            self.assertEqual((g.board, g.ply, g.turn), before)

    def test_double_submit_rejected(self):
        g = new_game(BLACK, "よわ", KANJI)
        v = click(g, g.legal()[0])
        self.assertTrue(g.human_move(v))
        self.assertFalse(g.human_move(v))   # 同じ値の再送
        g.enemy_move(random.Random(0))
        self.assertFalse(g.human_move(v))   # 敵の着手後にも届く古い値

    def test_enemy_methods_require_enemy_turn(self):
        g = new_game(BLACK, "よわ", KANJI)
        with self.assertRaises(ValueError):
            g.choose_enemy_move()
        with self.assertRaises(ValueError):
            g.play_enemy_move((2, 3))
        g.human_move(click(g, g.legal()[0]))
        with self.assertRaises(ValueError):
            g.play_enemy_move((0, 0))       # 合法手でない

    def test_choose_does_not_change_state(self):
        g = new_game(WHITE, "ふつー", KANJI)
        before = (g.board, g.ply, g.turn, list(g.enemy_history))
        g.choose_enemy_move(random.Random(0))
        self.assertEqual((g.board, g.ply, g.turn, g.enemy_history), before)


class TestGuess(unittest.TestCase):
    def make(self):
        g = new_game(BLACK, "よわ", KANJI, random.Random(0))
        return g

    def test_correct_wins_regardless_of_discs(self):
        g = self.make()
        g.board = tuple(tuple(WHITE for _ in range(8)) for _ in range(8))  # 人間(黒)は0個
        self.assertEqual(g.guess(g.answer), GUESS_CORRECT)
        self.assertTrue(g.is_over)
        self.assertEqual(g.outcome.winner, HUMAN)
        self.assertEqual(g.outcome.reason, "kanji")
        self.assertEqual(g.legal(), [])
        self.assertFalse(g.is_human_turn or g.is_enemy_turn)

    def test_wrong_continues_and_keeps_turn(self):
        g = self.make()
        wrong = next(k for k in KANJI if k != g.answer)
        before = (g.board, g.ply, g.turn)
        self.assertEqual(g.guess(wrong), GUESS_WRONG)
        self.assertEqual((g.board, g.ply, g.turn), before)
        self.assertEqual(g.guesses, [wrong])
        self.assertIn(wrong, g.notice)
        self.assertFalse(g.is_over)
        # 外れた後も着手できる
        self.assertTrue(g.human_move(click(g, g.legal()[0])))

    def test_invalid_inputs_not_counted(self):
        g = self.make()
        for t in ("", "   ", "挨曖", "ab"):
            self.assertEqual(g.guess(t), GUESS_INVALID)
        self.assertEqual(g.guesses, [])
        self.assertFalse(g.is_over)

    def test_whitespace_tolerated(self):
        g = self.make()
        self.assertEqual(g.guess(f" {g.answer}　"), GUESS_CORRECT)

    def test_not_allowed_on_enemy_turn_or_after_end(self):
        g = new_game(WHITE, "よわ", KANJI, random.Random(0))
        self.assertEqual(g.guess(g.answer), GUESS_NOT_ALLOWED)
        self.assertFalse(g.is_over)
        g2 = self.make()
        g2.guess(g2.answer)
        self.assertEqual(g2.guess(g2.answer), GUESS_NOT_ALLOWED)
        self.assertFalse(g2.human_move(click(g2, (2, 3))))


def make_board(rows):
    table = {".": EMPTY, "B": BLACK, "W": WHITE}
    return tuple(tuple(table[ch] for ch in r) for r in rows)


# 黒が (0,2) に打つと、白は置ける場所がなくなる(白の石は端に挟まれず、黒の石は挟めない)。
# 黒には (7,3) など打てる場所が残るので、白はパスして黒が続ける。
PASS_BOARD = [
    "BW......",
    "........",
    "........",
    "........",
    "........",
    "........",
    "........",
    "BWW.....",
]


class TestPassAndEnd(unittest.TestCase):
    def test_enemy_passes_human_continues(self):
        g = new_game(BLACK, "よわ", KANJI)
        g.board = make_board(PASS_BOARD)
        g.ply = 10
        self.assertIn((0, 2), g.legal())
        self.assertTrue(g.human_move(click(g, (0, 2))))
        self.assertTrue(g.is_human_turn)      # 敵がパス → 人間の連続手番
        self.assertEqual(g.notice, "相手はパスしました")
        self.assertEqual(g.enemy_history, [])
        self.assertFalse(g.is_over)

    def test_human_passes_enemy_continues(self):
        g = new_game(WHITE, "よわ", KANJI)    # 敵=黒
        g.board = make_board(PASS_BOARD)
        g.ply = 10
        self.assertTrue(g.is_enemy_turn)
        g.play_enemy_move((0, 2))
        self.assertTrue(g.is_enemy_turn)      # 人間(白)はパス → 敵の連続手番
        self.assertEqual(g.notice, "あなたはパスしました")
        self.assertEqual(g.enemy_history, [(0, 2)])
        self.assertFalse(g.is_over)

    def test_pass_notice_cleared_on_next_move(self):
        g = new_game(BLACK, "よわ", KANJI)
        g.board = make_board(PASS_BOARD)
        g.ply = 10
        g.human_move(click(g, (0, 2)))
        self.assertTrue(g.notice)
        g.human_move(click(g, (7, 3)))
        self.assertEqual(g.notice, "")

    def test_finish_by_discs(self):
        for rows, who in ((["B" * 8] * 8, HUMAN), (["W" * 8] * 8, ENEMY),
                          (["B" * 8] * 4 + ["W" * 8] * 4, DRAW)):
            g = new_game(BLACK, "よわ", KANJI)
            g.board = tuple(tuple(BLACK if ch == "B" else WHITE for ch in r) for r in rows)
            g._finish_by_discs()
            self.assertEqual(g.outcome.winner, who)
            self.assertEqual(g.outcome.reason, "discs")
            self.assertTrue(g.is_over)
            self.assertIsNone(g.turn)

    def test_outcome_text(self):
        g = new_game(BLACK, "よわ", KANJI)
        self.assertEqual(outcome_text(g), "")
        g.outcome = Outcome("discs", HUMAN, 40, 24)
        self.assertIn("勝ち", outcome_text(g))
        self.assertIn("40", outcome_text(g))
        g.outcome = Outcome("discs", ENEMY, 20, 44)
        self.assertIn("負け", outcome_text(g))
        g.outcome = Outcome("discs", DRAW, 32, 32)
        self.assertIn("引き分け", outcome_text(g))
        g.outcome = Outcome("kanji", HUMAN, 10, 50)
        self.assertIn("漢字", outcome_text(g))


class TestFullGames(unittest.TestCase):
    def play(self, human, level, seed):
        rng = random.Random(seed)
        g = new_game(human, level, KANJI, rng)
        movers = []   # (誰が打ったか)
        steps = 0
        while not g.is_over:
            steps += 1
            self.assertLess(steps, 200)
            self.assertEqual(g.ply, count(g.board, BLACK) + count(g.board, WHITE) - 4)
            legal = g.legal()
            self.assertTrue(legal)                       # 手番側には必ず合法手がある
            if g.is_human_turn:
                move = rng.choice(legal)
                self.assertTrue(g.human_move(click(g, move)))
                movers.append(HUMAN)
            else:
                g.enemy_move(rng)
                movers.append(ENEMY)
        # 終局の整合
        self.assertTrue(is_game_over(g.board))
        h, e = g.discs()
        w = winner(g.board)
        expect = DRAW if w is None else (HUMAN if w == g.human else ENEMY)
        self.assertEqual(g.outcome.winner, expect)
        self.assertEqual((g.outcome.human_discs, g.outcome.enemy_discs), (h, e))
        return g, movers

    def test_random_games_both_colors(self):
        for human in (BLACK, WHITE):
            for seed in range(25):
                g, movers = self.play(human, "よわ", seed)
                # 先手は黒
                self.assertEqual(movers[0], HUMAN if human == BLACK else ENEMY)
                self.assertGreater(g.ply, 4)             # 4手目以降も着手できている

    def test_alternation_except_pass(self):
        """同じ側が連続で打つのは、相手に合法手がなかったときだけ。"""
        passes = 0
        for seed in range(20):
            rng = random.Random(seed)
            g = new_game(BLACK, "ふつー", KANJI, rng)
            prev = None
            board_after_prev = None
            while not g.is_over:
                mover = g.turn
                if prev == mover:
                    passes += 1
                    self.assertEqual(legal_moves(board_after_prev, opponent(mover)), [])
                if g.is_human_turn:
                    g.human_move(click(g, rng.choice(g.legal())))
                else:
                    g.enemy_move(rng)
                prev, board_after_prev = mover, g.board
        self.assertGreater(passes, 0)   # パスが実際に起きた対局が含まれている

    def test_enemy_never_moves_twice_unless_human_passes(self):
        for seed in range(15):
            rng = random.Random(100 + seed)
            g = new_game(WHITE, "よわ", KANJI, rng)
            last = None
            while not g.is_over:
                if g.is_human_turn:
                    g.human_move(click(g, rng.choice(g.legal())))
                    last = HUMAN
                else:
                    board = g.board
                    g.enemy_move(rng)
                    if last == ENEMY:
                        # 連続して打てたのは、人間に合法手がなかったから
                        self.assertEqual(legal_moves(board, g.human), [])
                    last = ENEMY

    def test_strong_levels_complete_a_game(self):
        g, _ = self.play(BLACK, "つよ", 0)
        self.assertTrue(g.is_over)

    def test_enemy_history_matches_enemy_moves(self):
        g, movers = self.play(WHITE, "よわ", 3)
        self.assertEqual(len(g.enemy_history), movers.count(ENEMY))


class TestDelay(unittest.TestCase):
    def test_properties(self):
        for name in LEVELS:
            self.assertGreater(enemy_delay(name, 5, 20), 0)
        self.assertGreater(enemy_delay("げきつよ", 5, 20), enemy_delay("よわ", 5, 20))
        self.assertLess(enemy_delay("つよ", 1, 20), enemy_delay("つよ", 5, 20))     # 候補1手は短い
        self.assertLess(enemy_delay("つよ", 5, 0), enemy_delay("つよ", 5, 20))      # 序盤は短い
        self.assertGreater(enemy_delay("つよ", 12, 20), enemy_delay("つよ", 5, 20))  # 候補が多いと長い
        self.assertLess(enemy_delay("げきつよ", 12, 20), 3.0)


if __name__ == "__main__":
    unittest.main()
