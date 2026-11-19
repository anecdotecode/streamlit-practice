import json
import os
import random
import tempfile
import unittest
import unicodedata

from reversi.board import BLACK, EMPTY, WHITE, apply_move, count, initial_board
from reversi.kanji import (
    DEFAULT_PATH, hint_cells, is_correct, load_kanji, normalize_guess, pick_kanji,
)


def write_json(obj):
    f = tempfile.NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8")
    json.dump(obj, f, ensure_ascii=False)
    f.close()
    return f.name


class TestLoad(unittest.TestCase):
    def test_real_file(self):
        self.assertTrue(os.path.exists(DEFAULT_PATH), DEFAULT_PATH)
        kanji = load_kanji()
        self.assertGreater(len(kanji), 0)
        self.assertEqual(len(kanji), len(set(kanji)))
        for ch in kanji:
            self.assertEqual(len(ch), 1)
            self.assertTrue(unicodedata.name(ch).startswith("CJK"))

    def test_valid_and_extra_keys_ignored(self):
        p = write_json({"level": "x", "count": 99, "kanji": ["挨", "曖"]})
        self.assertEqual(load_kanji(p), ["挨", "曖"])

    def test_invalid_files(self):
        cases = [
            [],                          # dict でない
            {},                          # キーなし
            {"kanji": []},               # 空
            {"kanji": "挨曖"},            # リストでない
            {"kanji": [1, 2]},           # 文字列でない
            {"kanji": ["挨曖"]},          # 2文字
            {"kanji": [""]},             # 空文字
            {"kanji": ["あ"]},            # ひらがな
            {"kanji": ["a"]},            # 英字
            {"kanji": [" "]},            # 空白
            {"kanji": ["挨", "挨"]},      # 重複
        ]
        for obj in cases:
            with self.subTest(obj=obj):
                with self.assertRaises(ValueError):
                    load_kanji(write_json(obj))

    def test_missing_file(self):
        with self.assertRaises(FileNotFoundError):
            load_kanji("no_such_file.json")


class TestPick(unittest.TestCase):
    def test_pick_is_member_and_reproducible(self):
        kanji = load_kanji()
        a = [pick_kanji(kanji, random.Random(3)) for _ in range(3)]
        self.assertEqual(len(set(a)), 1)
        self.assertIn(a[0], kanji)

    def test_all_reachable(self):
        kanji = load_kanji()
        rng = random.Random(0)
        seen = {pick_kanji(kanji, rng) for _ in range(6000)}
        self.assertEqual(seen, set(kanji))

    def test_empty(self):
        with self.assertRaises(ValueError):
            pick_kanji([])


class TestGuess(unittest.TestCase):
    def test_correct(self):
        self.assertTrue(is_correct("挨", "挨"))
        self.assertTrue(is_correct("挨", " 挨 "))
        self.assertTrue(is_correct("挨", "　挨\n"))  # 全角空白・改行

    def test_wrong(self):
        self.assertFalse(is_correct("挨", "曖"))
        self.assertFalse(is_correct("挨", "挨挨"))
        self.assertFalse(is_correct("挨", ""))
        self.assertFalse(is_correct("挨", "   "))
        self.assertFalse(is_correct("挨", "あ"))
        self.assertFalse(is_correct("槌", "鎚"))  # 別字

    def test_normalize(self):
        self.assertEqual(normalize_guess(" 挨 　"), "挨")
        self.assertEqual(normalize_guess("\uf900"), "\u8c48")


class TestHint(unittest.TestCase):
    def test_initial(self):
        b = initial_board()
        self.assertEqual(hint_cells(b, BLACK), [(3, 4), (4, 3)])
        self.assertEqual(hint_cells(b, WHITE), [(3, 3), (4, 4)])

    def test_matches_stone_count_and_excludes_others(self):
        b = initial_board()
        b = apply_move(b, 2, 3, BLACK)          # 黒が(3,3)を反転
        black = hint_cells(b, BLACK)
        white = hint_cells(b, WHITE)
        self.assertEqual(len(black), count(b, BLACK))
        self.assertEqual(len(white), count(b, WHITE))
        self.assertEqual(set(black) & set(white), set())
        self.assertIn((3, 3), black)
        self.assertNotIn((3, 3), white)        # 反転で白のヒントから外れる
        for r, c in black:
            self.assertEqual(b[r][c], BLACK)
        # 空きマスは含まれない
        for r, c in black + white:
            self.assertNotEqual(b[r][c], EMPTY)

    def test_order_is_row_major(self):
        b = apply_move(initial_board(), 2, 3, BLACK)
        cells = hint_cells(b, BLACK)
        self.assertEqual(cells, sorted(cells))

    def test_invalid_player(self):
        with self.assertRaises(ValueError):
            hint_cells(initial_board(), EMPTY)


if __name__ == "__main__":
    unittest.main()
