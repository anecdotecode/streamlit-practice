"""漢字の読み込み・選択・正誤判定・ヒント表示位置。画面・Streamlitには依存しない。

漢字の描画自体は画面側(段階4のコンポーネント)が行う。
ここでは「どのマスに漢字の一部を見せるか」を決める。
漢字は盤面全体(8x8)に広げた1枚の絵とみなし、各マスは (row, col) に対応する
1/64の領域を持つ。見せるのは、プレイヤー自身の石があるマスだけ。
"""

from __future__ import annotations

import json
import random
import unicodedata
from pathlib import Path

from reversi.board import EMPTY, SIZE, Board, Move

DEFAULT_PATH = Path(__file__).resolve().parent.parent / "sample_data" / "kanji.json"


def load_kanji(path: str | Path | None = None) -> list[str]:
    """JSON {"kanji": ["挨", ...]} から漢字のリストを読む。形式が不正なら ValueError。

    要素は漢字(CJK)1文字で、重複なし。"kanji" 以外のキーは無視する。
    """
    path = Path(path) if path is not None else DEFAULT_PATH
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, dict) or "kanji" not in data:
        raise ValueError('"kanji" キーがありません')
    items = data["kanji"]
    if not isinstance(items, list) or not items:
        raise ValueError('"kanji" は空でないリストにしてください')
    seen: set[str] = set()
    for i, ch in enumerate(items):
        if not isinstance(ch, str) or len(ch) != 1:
            raise ValueError(f"{i}番目が1文字の文字列ではありません: {ch!r}")
        if not unicodedata.name(ch, "").startswith("CJK"):
            raise ValueError(f"{i}番目が漢字ではありません: {ch!r}")
        if ch in seen:
            raise ValueError(f"重複しています: {ch!r}")
        seen.add(ch)
    return list(items)


def pick_kanji(kanji: list[str], rng: random.Random | None = None) -> str:
    """漢字を1文字ランダムに選ぶ。"""
    if not kanji:
        raise ValueError("漢字のリストが空です")
    return (rng or random).choice(kanji)


def normalize_guess(text: str) -> str:
    """入力の正規化: NFKC にして、空白をすべて除く。"""
    return "".join(unicodedata.normalize("NFKC", text).split())


def is_correct(answer: str, guess: str) -> bool:
    """予想の正誤。空入力・複数文字は不正解。"""
    g = normalize_guess(guess)
    return len(g) == 1 and g == normalize_guess(answer)


def hint_cells(board: Board, player: int) -> list[Move]:
    """漢字の一部を見せるマス(player の石がある (row, col))。行優先の順。

    相手の石と空きマスは含まない。石が反転して相手のものになれば、そのマスは外れる。
    """
    if player == EMPTY:
        raise ValueError("invalid player: 0")
    return [
        (r, c)
        for r in range(SIZE)
        for c in range(SIZE)
        if board[r][c] == player
    ]
