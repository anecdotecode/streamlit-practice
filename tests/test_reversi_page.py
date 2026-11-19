"""pages/kanji_reversi.py の流れを、偽の streamlit で通して確認する(煙テスト)。

本物の Streamlit は使っていない。ここで確かめるのは、このページが
「設定 → 対局 → 敵の手番 → 予想 → 終局 → リセット」の各状態で、
正しい順序・引数でゲームを操作し、例外を出さないこと。
Streamlit 本体の挙動(再実行・ウィジェットの状態・画面のちらつき等)は検証できない。
"""

import contextlib
import runpy
import sys
import types
import unittest
from pathlib import Path

import reversi.component as component
from reversi.board import BLACK, WHITE

PAGE = Path(__file__).resolve().parent.parent / "pages" / "kanji_reversi.py"


class Rerun(Exception):
    pass


class FakeSt(types.ModuleType):
    def __init__(self, events, state):
        super().__init__("streamlit")
        self.events = events                 # (名前, 内容) の呼び出し順
        self.session_state = state
        self.radio_values = {}
        self.pressed = set()                 # このランで押されるボタン/送信ボタンのラベル
        self.text = ""

    def _rec(self, name, *a):
        self.events.append((name, a[0] if a else None))

    def set_page_config(self, **kw): self._rec("set_page_config")
    def title(self, t): self._rec("title", t)
    def write(self, t): self._rec("write", t)
    def success(self, t): self._rec("success", t)
    def error(self, t): self._rec("error", t)
    def info(self, t): self._rec("info", t)
    def caption(self, t): self._rec("caption", t)

    def form(self, key, clear_on_submit=False):
        self._rec("form", key)
        return contextlib.nullcontext()

    def radio(self, label, options, index=0, horizontal=False):
        return self.radio_values.get(label, list(options)[index])

    def text_input(self, label, key=None):
        self._rec("text_input", label)
        return self.text

    def form_submit_button(self, label):
        self._rec("form_submit_button", label)
        return label in self.pressed

    def button(self, label):
        self._rec("button", label)
        return label in self.pressed

    def rerun(self):
        self._rec("rerun")
        raise Rerun()


class PageHarness:
    def __init__(self):
        self.events = []
        self.state = {}
        self.board_calls = []
        self.board_return = None
        self.sleeps = []
        self.st = FakeSt(self.events, self.state)

    def run(self):
        """ページを1回実行する。'rerun' か 'done' を返す。"""
        self.events.clear()
        self.board_calls.clear()
        self.sleeps.clear()

        def fake_board(**kw):
            self.events.append(("board", None))
            self.board_calls.append(kw)
            return self.board_return

        saved = (sys.modules.get("streamlit"), component.reversi_board)
        import time
        saved_sleep = time.sleep
        sys.modules["streamlit"] = self.st
        component.reversi_board = fake_board
        time.sleep = lambda s: (self.sleeps.append(s), self.events.append(("sleep", s)))
        try:
            runpy.run_path(str(PAGE))
            return "done"
        except Rerun:
            return "rerun"
        finally:
            time.sleep = saved_sleep
            component.reversi_board = saved[1]
            if saved[0] is None:
                sys.modules.pop("streamlit", None)
            else:
                sys.modules["streamlit"] = saved[0]

    def names(self):
        return [e[0] for e in self.events]

    def start(self, color_label, level):
        self.st.radio_values = {"自分の色": color_label, "敵の強さ": level}
        self.st.pressed = {"対戦開始"}
        self.assert_rerun()
        self.st.pressed = set()

    def assert_rerun(self):
        assert self.run() == "rerun"

    @property
    def game(self):
        return self.state.get("kanji_reversi_game")


class TestPage(unittest.TestCase):
    def test_setup_screen(self):
        h = PageHarness()
        self.assertEqual(h.run(), "done")
        self.assertEqual(h.names().count("title"), 1)
        self.assertIn(("form", "kanji_reversi_setup"), h.events)
        self.assertIn(("form_submit_button", "対戦開始"), h.events)
        self.assertEqual(h.board_calls, [])
        self.assertIsNone(h.game)

    def test_start_white_then_enemy_moves_first(self):
        h = PageHarness()
        h.start("白（後手）", "よわ")
        g = h.game
        self.assertEqual((g.human, g.level_name, g.ply), (WHITE, "よわ", 0))
        # 敵(黒)の手番: 盤面は操作不可、待機してから1手打って再描画
        self.assertEqual(h.run(), "rerun")
        call = h.board_calls[0]
        self.assertFalse(call["enabled"])
        self.assertEqual(call["legal"], [])
        self.assertEqual(call["turn"], BLACK)
        self.assertIn(("info", "相手が考えています…"), h.events)
        self.assertEqual(g.ply, 1)
        self.assertEqual(len(g.enemy_history), 1)
        self.assertEqual(len(h.sleeps), 1)
        # 設定画面は出ない(タイトルなし)
        self.assertNotIn("title", h.names())
        # 「最初から遊ぶ」と予想欄は、待機(sleep)より前に描かれる。予想欄は敵の手番では出ない
        self.assertLess(h.names().index("button"), h.names().index("sleep"))
        self.assertNotIn("form", h.names())

    def test_human_turn_click_guess_and_reset(self):
        h = PageHarness()
        h.start("黒（先手）", "よわ")
        g = h.game
        # 人間の手番: 盤面は操作可、予想欄が出る、敵は動かない
        self.assertEqual(h.run(), "done")
        call = h.board_calls[0]
        self.assertTrue(call["enabled"])
        self.assertEqual(sorted(call["legal"]), sorted(g.legal()))
        self.assertEqual(call["hint"], [(3, 4), (4, 3)])   # 黒の初期石
        self.assertEqual(call["glyph"], g.answer)
        self.assertEqual(h.sleeps, [])
        self.assertIn("form", h.names())
        self.assertEqual(h.names()[:2], ["set_page_config", "board"])   # 盤面が最初(予想欄・結果は盤面の下)
        self.assertLess(h.names().index("board"), h.names().index("form"))

        # 古い値は無視される
        h.board_return = {"game_id": g.game_id, "ply": 99, "turn": BLACK, "r": 2, "c": 3, "nonce": 1}
        self.assertEqual(h.run(), "done")
        self.assertEqual(g.ply, 0)

        # 有効なクリックで着手 → 再描画
        r, c = call["legal"][0]
        h.board_return = {"game_id": g.game_id, "ply": g.ply, "turn": BLACK, "r": r, "c": c, "nonce": 2}
        self.assertEqual(h.run(), "rerun")
        self.assertEqual(g.ply, 1)
        self.assertTrue(g.is_enemy_turn)
        h.board_return = None

        # 敵の手番を進めて、人間の手番に戻す
        self.assertEqual(h.run(), "rerun")
        self.assertTrue(g.is_human_turn)

        # 外れの予想 → 続行
        wrong = next(k for k in "挨曖宛嵐畏" if k != g.answer)
        h.st.text = wrong
        h.st.pressed = {"予想する"}
        self.assertEqual(h.run(), "rerun")
        self.assertEqual(g.guesses, [wrong])
        h.st.pressed = set()
        self.assertEqual(h.run(), "done")
        self.assertIn(("caption", f"「{wrong}」ではありません"), h.events)

        # 正解 → 勝利。盤面は操作不可、予想欄なし、敵は動かない
        h.st.text = g.answer
        h.st.pressed = {"予想する"}
        self.assertEqual(h.run(), "rerun")
        h.st.pressed = set()
        self.assertTrue(g.is_over)
        self.assertEqual(h.run(), "done")
        self.assertFalse(h.board_calls[0]["enabled"])
        self.assertNotIn("form", h.names())
        self.assertEqual(h.sleeps, [])
        self.assertEqual([e[0] for e in h.events if e[0] == "success"], ["success"])
        self.assertIn(("write", f"答えは「{g.answer}」でした。"), h.events)

        # リセット → 設定画面へ
        h.st.pressed = {"最初から遊ぶ"}
        self.assertEqual(h.run(), "rerun")
        h.st.pressed = set()
        self.assertIsNone(h.game)
        self.assertEqual(h.run(), "done")
        self.assertEqual(h.names().count("title"), 1)

    def test_reset_during_enemy_wait_is_available_and_works(self):
        h = PageHarness()
        h.start("白（後手）", "よわ")
        h.st.pressed = {"最初から遊ぶ"}
        self.assertEqual(h.run(), "rerun")
        self.assertIsNone(h.game)
        self.assertEqual(h.sleeps, [])    # 待機に入る前にリセットされた

    def test_play_to_the_end_through_page(self):
        """人間はランダム、敵は「よわ」。ページ経由で終局まで進める。"""
        import random
        rng = random.Random(0)
        h = PageHarness()
        h.start("黒（先手）", "よわ")
        g = h.game
        for _ in range(400):
            if g.is_over:
                break
            if g.is_human_turn:
                r, c = rng.choice(g.legal())
                h.board_return = {"game_id": g.game_id, "ply": g.ply, "turn": g.turn,
                                  "r": r, "c": c, "nonce": 1}
            else:
                h.board_return = None
            h.run()
        else:
            self.fail("終局しない")
        h.board_return = None
        self.assertEqual(h.run(), "done")
        self.assertTrue(any(n in h.names() for n in ("success", "error", "info")))


if __name__ == "__main__":
    unittest.main()
