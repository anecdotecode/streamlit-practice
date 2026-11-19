"""漢字リバーシの対局の状態管理。画面・Streamlitには依存しない。

Streamlit のページ(pages/kanji_reversi.py)は、この Game を session_state に保持して
操作を呼び出すだけにする。手番・パス・勝敗・漢字予想のルールはすべてここにある。
"""

from __future__ import annotations

import random
import uuid
from dataclasses import dataclass, field

from reversi.ai import LEVELS, choose_move
from reversi.board import (
    Board,
    Move,
    apply_move,
    count,
    BLACK,
    initial_board,
    legal_moves,
    next_player,
    opponent,
)
from reversi.click import accept_click
from reversi.kanji import is_correct, normalize_guess, pick_kanji

HUMAN = "human"
ENEMY = "enemy"
DRAW = "draw"

# 敵の待機時間(秒)の基準。難しいほど長い。
_BASE_DELAY = {"激よわ": 0.5, "よわ": 0.6, "ふつー": 0.8, "つよ": 1.0, "げきつよ": 1.3}

GUESS_CORRECT = "correct"
GUESS_WRONG = "wrong"
GUESS_INVALID = "invalid"          # 空・複数文字。予想として数えない
GUESS_NOT_ALLOWED = "not_allowed"  # 自分の手番でない/対局終了後


@dataclass(frozen=True)
class Outcome:
    reason: str        # "kanji"(漢字の正解) or "discs"(石数)
    winner: str        # HUMAN / ENEMY / DRAW
    human_discs: int
    enemy_discs: int


@dataclass
class Game:
    game_id: str
    human: int
    level_name: str
    answer: str
    board: Board = field(default_factory=initial_board)
    turn: int | None = BLACK          # 黒が先手。終局後は None
    ply: int = 0                      # これまでに打たれた手数(パスは数えない)
    outcome: Outcome | None = None
    enemy_history: list[Move] = field(default_factory=list)
    guesses: list[str] = field(default_factory=list)
    notice: str = ""

    # ---- 状態 ----
    @property
    def enemy(self) -> int:
        return opponent(self.human)

    @property
    def is_over(self) -> bool:
        return self.outcome is not None

    @property
    def is_human_turn(self) -> bool:
        return not self.is_over and self.turn == self.human

    @property
    def is_enemy_turn(self) -> bool:
        return not self.is_over and self.turn == self.enemy

    def legal(self) -> list[Move]:
        """現在の手番の合法手。終局後は空。"""
        if self.is_over or self.turn is None:
            return []
        return legal_moves(self.board, self.turn)

    def discs(self) -> tuple[int, int]:
        """(自分の石数, 敵の石数)"""
        return count(self.board, self.human), count(self.board, self.enemy)

    # ---- 操作 ----
    def human_move(self, click_value) -> bool:
        """コンポーネントから届いた値が有効なら着手して True。無効なら何も変えず False。"""
        if not self.is_human_turn:
            return False
        move = accept_click(
            click_value,
            game_id=self.game_id,
            ply=self.ply,
            turn=self.turn,
            legal=self.legal(),
        )
        if move is None:
            return False
        self._play(move, self.human)
        return True

    def choose_enemy_move(self, rng: random.Random | None = None) -> Move:
        """敵の手を選ぶ(盤面は変えない)。敵の手番でなければ ValueError。"""
        if not self.is_enemy_turn:
            raise ValueError("敵の手番ではありません")
        move = choose_move(self.board, self.enemy, LEVELS[self.level_name], rng)
        if move is None:  # 敵の手番なら合法手があるはず
            raise RuntimeError("敵の合法手がありません")
        return move

    def play_enemy_move(self, move: Move) -> None:
        """選んだ手を打つ。敵の手番でない・合法手でない場合は ValueError。"""
        if not self.is_enemy_turn:
            raise ValueError("敵の手番ではありません")
        if move not in self.legal():
            raise ValueError(f"合法手ではありません: {move}")
        self._play(move, self.enemy)
        self.enemy_history.append(move)

    def enemy_move(self, rng: random.Random | None = None) -> Move:
        move = self.choose_enemy_move(rng)
        self.play_enemy_move(move)
        return move

    def guess(self, text: str) -> str:
        """漢字の予想。自分の手番のときだけ受け付ける。手番は消費しない。"""
        if not self.is_human_turn:
            return GUESS_NOT_ALLOWED
        g = normalize_guess(text)
        if len(g) != 1:
            self.notice = "漢字を1文字で入力してください"
            return GUESS_INVALID
        if is_correct(self.answer, g):
            h, e = self.discs()
            self.outcome = Outcome("kanji", HUMAN, h, e)
            self.turn = None
            self.notice = ""
            return GUESS_CORRECT
        self.guesses.append(g)
        self.notice = f"「{g}」ではありません"
        return GUESS_WRONG

    # ---- 内部 ----
    def _play(self, move: Move, mover: int) -> None:
        self.board = apply_move(self.board, move[0], move[1], mover)
        self.ply += 1
        self.notice = ""
        nxt = next_player(self.board, mover)
        if nxt is None:
            self._finish_by_discs()
            return
        self.turn = nxt
        if nxt == mover:  # 相手に置く場所がなくパス
            self.notice = "相手はパスしました" if mover == self.human else "あなたはパスしました"

    def _finish_by_discs(self) -> None:
        h, e = self.discs()
        who = HUMAN if h > e else ENEMY if e > h else DRAW
        self.outcome = Outcome("discs", who, h, e)
        self.turn = None


def new_game(
    human: int,
    level_name: str,
    kanji: list[str],
    rng: random.Random | None = None,
) -> Game:
    """新しい対局。盤面・漢字・手番・履歴・予想状態をすべて初期化する。"""
    if level_name not in LEVELS:
        raise ValueError(f"未定義の強さ: {level_name}")
    if human not in (BLACK, opponent(BLACK)):
        raise ValueError(f"不正な色: {human}")
    return Game(
        game_id=uuid.uuid4().hex,
        human=human,
        level_name=level_name,
        answer=pick_kanji(kanji, rng),
    )


def enemy_delay(level_name: str, n_legal: int, ply: int) -> float:
    """敵が着手するまでの待機時間(秒)。強いほど長く、序盤と候補が1手のときは短く、候補が多いと長い。"""
    delay = _BASE_DELAY[level_name]
    if n_legal <= 1:
        return delay * 0.5
    if ply < 6:
        delay *= 0.7
    if n_legal >= 10:
        delay *= 1.2
    return delay


def outcome_text(game: Game) -> str:
    """結果表示の文言。"""
    o = game.outcome
    if o is None:
        return ""
    if o.reason == "kanji":
        return "漢字を当てました。あなたの勝ちです！"
    score = f"（あなた {o.human_discs} - 相手 {o.enemy_discs}）"
    if o.winner == HUMAN:
        return f"あなたの勝ちです！{score}"
    if o.winner == ENEMY:
        return f"あなたの負けです。{score}"
    return f"引き分けです。{score}"
