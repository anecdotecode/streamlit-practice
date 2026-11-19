import unittest

from reversi.board import BLACK, WHITE
from reversi.click import accept_click

LEGAL = [(2, 3), (3, 2), (4, 5), (5, 4)]


def ev(**kw):
    base = {"game_id": "g1", "ply": 0, "turn": BLACK, "r": 2, "c": 3, "nonce": 1}
    base.update(kw)
    return base


def acc(value, **kw):
    params = dict(game_id="g1", ply=0, turn=BLACK, legal=LEGAL)
    params.update(kw)
    return accept_click(value, **params)


class TestAcceptClick(unittest.TestCase):
    def test_valid(self):
        self.assertEqual(acc(ev()), (2, 3))
        self.assertEqual(acc(ev(r=5, c=4)), (5, 4))

    def test_none_and_garbage(self):
        for v in (None, 1, "x", [], [2, 3], {}):
            self.assertIsNone(acc(v))

    def test_stale_ply(self):
        self.assertIsNone(acc(ev(ply=0), ply=1))      # 古い盤面
        self.assertIsNone(acc(ev(ply=2), ply=1))      # 未来の盤面

    def test_other_game(self):
        self.assertIsNone(acc(ev(game_id="g0")))

    def test_wrong_turn(self):
        self.assertIsNone(acc(ev(turn=WHITE)))                     # 手番が違う
        self.assertIsNone(acc(ev(turn=BLACK), turn=WHITE))         # 敵の手番に届いた

    def test_not_legal(self):
        self.assertIsNone(acc(ev(r=0, c=0)))
        self.assertIsNone(acc(ev(r=3, c=3)))                       # 石があるマス
        self.assertIsNone(acc(ev(r=2, c=3), legal=[]))             # 合法手なし(敵の手番など)

    def test_bad_types(self):
        self.assertIsNone(acc(ev(r="2")))
        self.assertIsNone(acc(ev(c=3.0)))
        self.assertIsNone(acc(ev(r=True, c=True), legal=[(1, 1)]))  # bool は整数として扱わない
        self.assertIsNone(acc(ev(ply="0")))
        self.assertIsNone(acc(ev(ply=False)))
        self.assertIsNone(acc(ev(turn=None)))
        self.assertIsNone(acc({k: v for k, v in ev().items() if k != "r"}))

    def test_duplicate_is_rejected_after_ply_advances(self):
        v = ev()
        self.assertEqual(acc(v, ply=0), (2, 3))   # 1回目は受理
        self.assertIsNone(acc(v, ply=1))          # 着手で ply が進んだ後の再送は無効

    def test_nonce_ignored(self):
        self.assertEqual(acc(ev(nonce=999)), (2, 3))
        d = ev()
        del d["nonce"]
        self.assertEqual(acc(d), (2, 3))


if __name__ == "__main__":
    unittest.main()
