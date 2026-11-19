"""盤面コンポーネント(reversi/frontend/index.html)を実ブラウザで検証する。

Streamlit の代わりに tests/frontend_harness.html が親ページになり、
postMessage のプロトコルでコンポーネントとやり取りする。
playwright と chromium がない環境ではスキップされる。
"""

import functools
import http.server
import threading
import time
import unittest
from pathlib import Path

from reversi.board import BLACK, WHITE, apply_move, initial_board, legal_moves
from reversi.kanji import hint_cells

ROOT = Path(__file__).resolve().parent.parent

try:
    from playwright.sync_api import sync_playwright
    HAVE_PLAYWRIGHT = True
except Exception:  # pragma: no cover
    HAVE_PLAYWRIGHT = False


class _Quiet(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a):
        pass


def make_args(board, human, turn, enabled, glyph="", hint=None, ply=0, game_id="g1"):
    legal = [list(m) for m in legal_moves(board, turn)] if enabled else []
    if hint is None:
        hint = hint_cells(board, human)
    return {
        "board": [list(r) for r in board],
        "human": human, "turn": turn, "enabled": enabled,
        "legal": legal, "hint": [list(m) for m in hint],
        "glyph": glyph, "game_id": game_id, "ply": ply,
    }


@unittest.skipUnless(HAVE_PLAYWRIGHT, "playwright がありません")
class TestFrontend(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        handler = functools.partial(_Quiet, directory=str(ROOT))
        cls.server = http.server.ThreadingHTTPServer(("127.0.0.1", 0), handler)
        threading.Thread(target=cls.server.serve_forever, daemon=True).start()
        cls.base = f"http://127.0.0.1:{cls.server.server_address[1]}"
        cls.pw = sync_playwright().start()
        try:
            cls.browser = cls.pw.chromium.launch()
        except Exception as e:  # pragma: no cover
            cls.pw.stop()
            cls.server.shutdown()
            raise unittest.SkipTest(f"chromium を起動できません: {e}")

    @classmethod
    def tearDownClass(cls):
        cls.browser.close()
        cls.pw.stop()
        cls.server.shutdown()

    def setUp(self):
        self.page = self.browser.new_page(viewport={"width": 600, "height": 700})
        self.page.goto(f"{self.base}/tests/frontend_harness.html")
        self.page.wait_for_function("window.__msgs.some(m => m.type === 'streamlit:componentReady')")
        self.frame = [f for f in self.page.frames if "index.html" in f.url][0]

    def tearDown(self):
        self.page.close()

    # ---- 補助 ----
    def msgs(self, type_=None):
        m = self.page.evaluate("window.__msgs")
        return [x for x in m if type_ is None or x["type"] == type_]

    def render(self, args):
        n = len(self.msgs("streamlit:setFrameHeight"))
        self.page.evaluate("a => window.sendRender(a)", args)
        self.page.wait_for_function(
            "n => window.__msgs.filter(m => m.type === 'streamlit:setFrameHeight').length > n", arg=n)

    def canvas_rect(self):
        return self.frame.evaluate(
            "() => { const r = document.getElementById('board').getBoundingClientRect();"
            " return [r.left, r.top, r.width]; }")

    def click_cell(self, r, c):
        box = self.page.locator("#f").bounding_box()
        left, top, w = self.canvas_rect()
        cell = (w - 2) / 8
        self.page.mouse.click(box["x"] + left + 1 + (c + 0.5) * cell,
                              box["y"] + top + 1 + (r + 0.5) * cell)
        self.page.wait_for_timeout(150)   # postMessage の到達を待つ(「送られない」ことの検証のため)

    def pixels(self, r, c, radius_ratio=0.8):
        """(r,c) の石の円の内側(半径 0.42*cell*radius_ratio)の全画素 [R,G,B,A]。"""
        return self.frame.evaluate(
            """([r, c, ratio]) => {
                const cv = document.getElementById('board');
                const ctx = cv.getContext('2d');
                const dpr = cv.width / (parseFloat(cv.style.width));
                const cell = (parseFloat(cv.style.width) - 2) / 8;
                const cx = (1 + (c + 0.5) * cell) * dpr, cy = (1 + (r + 0.5) * cell) * dpr;
                const rad = cell * 0.42 * ratio * dpr;
                const x0 = Math.floor(cx - rad), y0 = Math.floor(cy - rad), n = Math.ceil(rad * 2) + 1;
                const d = ctx.getImageData(x0, y0, n, n).data, out = [];
                for (let j = 0; j < n; j++) for (let i = 0; i < n; i++) {
                    const dx = x0 + i + 0.5 - cx, dy = y0 + j + 0.5 - cy;
                    if (dx * dx + dy * dy <= rad * rad) {
                        const k = (j * n + i) * 4;
                        out.push([d[k], d[k + 1], d[k + 2], d[k + 3]]);
                    }
                }
                return out;
            }""", [r, c, radius_ratio])

    def center_pixel(self, r, c):
        return self.frame.evaluate(
            """([r, c]) => {
                const cv = document.getElementById('board');
                const dpr = cv.width / parseFloat(cv.style.width);
                const cell = (parseFloat(cv.style.width) - 2) / 8;
                const x = Math.floor((1 + (c + 0.5) * cell) * dpr);
                const y = Math.floor((1 + (r + 0.5) * cell) * dpr);
                return Array.from(cv.getContext('2d').getImageData(x, y, 1, 1).data);
            }""", [r, c])

    # ---- 通信 ----
    def test_handshake_and_height(self):
        ready = self.msgs("streamlit:componentReady")
        self.assertEqual(len(ready), 1)
        self.assertEqual(ready[0]["apiVersion"], 1)
        self.render(make_args(initial_board(), BLACK, BLACK, True))
        h = self.msgs("streamlit:setFrameHeight")[-1]["height"]
        self.assertEqual(h, 482)
        _, _, w = self.canvas_rect()
        self.assertEqual(w, 482)

    def test_resize_changes_height(self):
        self.render(make_args(initial_board(), BLACK, BLACK, True))
        n = len(self.msgs("streamlit:setFrameHeight"))
        self.page.evaluate("document.getElementById('f').style.width = '300px'")
        self.page.wait_for_function(
            "n => window.__msgs.filter(m => m.type === 'streamlit:setFrameHeight').length > n", arg=n)
        self.assertEqual(self.msgs("streamlit:setFrameHeight")[-1]["height"], 298)  # 296 + 2

    # ---- 描画: 置ける場所 ----
    def test_legal_dots_only_when_enabled(self):
        b = initial_board()
        self.render(make_args(b, BLACK, BLACK, True))
        for r, c in legal_moves(b, BLACK):
            R, G, B, A = self.center_pixel(r, c)
            self.assertTrue(R > 200 and G > 150 and B < 80 and A == 255, (r, c, R, G, B, A))
        self.assertEqual(self.center_pixel(0, 0)[3], 0)   # 置けない空きマスは何も描かない
        # 敵の手番: legal を渡しても点は出ない
        args = make_args(b, BLACK, WHITE, False)
        args["legal"] = [[2, 3], [3, 2]]
        self.render(args)
        self.assertEqual(self.center_pixel(2, 3)[3], 0)

    # ---- クリック ----
    def test_click_legal_sends_value(self):
        self.render(make_args(initial_board(), BLACK, BLACK, True, ply=0))
        self.click_cell(2, 3)
        vals = self.msgs("streamlit:setComponentValue")
        self.assertEqual(len(vals), 1)
        v = vals[0]["value"]
        self.assertEqual(vals[0]["dataType"], "json")
        self.assertEqual({k: v[k] for k in ("game_id", "ply", "turn", "r", "c")},
                         {"game_id": "g1", "ply": 0, "turn": BLACK, "r": 2, "c": 3})
        self.assertIn("nonce", v)

    def test_illegal_clicks_send_nothing(self):
        self.render(make_args(initial_board(), BLACK, BLACK, True))
        self.click_cell(0, 0)      # 置けない空きマス
        self.click_cell(3, 3)      # 石があるマス
        self.click_cell(4, 4)
        box = self.page.locator("#f").bounding_box()
        left, top, _ = self.canvas_rect()
        self.page.mouse.click(box["x"] + left + 0.2, box["y"] + top + 0.2)   # 盤の外周の余白
        self.page.mouse.click(box["x"] + 2, box["y"] + 2)                     # キャンバスの外
        self.page.wait_for_timeout(150)
        self.assertEqual(self.msgs("streamlit:setComponentValue"), [])

    def test_disabled_ignores_clicks(self):
        args = make_args(initial_board(), BLACK, WHITE, False)
        args["legal"] = [[2, 3]]
        self.render(args)
        self.click_cell(2, 3)
        self.assertEqual(self.msgs("streamlit:setComponentValue"), [])

    def test_double_click_sends_once_then_unlocks_on_render(self):
        b = initial_board()
        self.render(make_args(b, BLACK, BLACK, True, ply=0))
        self.click_cell(2, 3)
        self.click_cell(2, 3)
        self.click_cell(3, 2)
        self.assertEqual(len(self.msgs("streamlit:setComponentValue")), 1)
        # 次の局面が描画されると、再び受け付ける
        b2 = apply_move(b, 2, 3, BLACK)
        self.render(make_args(b2, BLACK, BLACK, True, ply=2))
        self.click_cell(*legal_moves(b2, BLACK)[0])
        vals = self.msgs("streamlit:setComponentValue")
        self.assertEqual(len(vals), 2)
        self.assertEqual(vals[1]["value"]["ply"], 2)
        self.assertNotEqual(vals[0]["value"]["nonce"], vals[1]["value"]["nonce"])

    def test_lock_times_out_without_render(self):
        self.render(make_args(initial_board(), BLACK, BLACK, True))
        self.click_cell(2, 3)
        time.sleep(1.5)
        self.click_cell(3, 2)
        self.assertEqual(len(self.msgs("streamlit:setComponentValue")), 2)

    # ---- 描画: 漢字ヒント ----
    @staticmethod
    def _dark(p):   # 白石の上のインク(暗い画素)
        return p[3] == 255 and p[0] < 128

    @staticmethod
    def _bright(p):  # 黒石の上のインク(明るい画素)
        return p[3] == 255 and p[0] > 128

    def test_hint_on_own_white_stones(self):
        b = initial_board()
        self.render(make_args(b, WHITE, WHITE, True, glyph="田"))
        own = [(3, 3), (4, 4)]
        self.assertTrue(any(any(self._dark(p) for p in self.pixels(r, c)) for r, c in own))

    def test_hint_on_own_black_stones(self):
        b = initial_board()
        self.render(make_args(b, BLACK, BLACK, True, glyph="田"))
        own = [(3, 4), (4, 3)]
        self.assertTrue(any(any(self._bright(p) for p in self.pixels(r, c)) for r, c in own))

    def test_no_hint_on_opponent_stones(self):
        b = initial_board()
        # 人間=白。敵の黒石 (3,4),(4,3) にはインク(明るい画素)が出ない。
        self.render(make_args(b, WHITE, WHITE, True, glyph="田"))
        for r, c in [(3, 4), (4, 3)]:
            self.assertFalse(any(self._bright(p) for p in self.pixels(r, c)), (r, c))
        # hint に敵のマスを誤って含めても描かない
        self.render(make_args(b, WHITE, WHITE, True, glyph="田", hint=[(3, 4), (4, 3), (3, 3), (4, 4)], ply=1))
        for r, c in [(3, 4), (4, 3)]:
            self.assertFalse(any(self._bright(p) for p in self.pixels(r, c)), (r, c))

    def test_no_hint_without_glyph_or_hint_cells(self):
        b = initial_board()
        self.render(make_args(b, WHITE, WHITE, True, glyph=""))
        for r, c in [(3, 3), (4, 4)]:
            self.assertFalse(any(self._dark(p) for p in self.pixels(r, c)))
        self.render(make_args(b, WHITE, WHITE, True, glyph="田", hint=[], ply=1))
        for r, c in [(3, 3), (4, 4)]:
            self.assertFalse(any(self._dark(p) for p in self.pixels(r, c)))

    def test_empty_cells_show_no_glyph(self):
        b = initial_board()
        every = [(r, c) for r in range(8) for c in range(8)]
        self.render(make_args(b, WHITE, WHITE, False, glyph="田", hint=every))
        for r, c in [(0, 0), (1, 1), (6, 6), (7, 7), (2, 2), (5, 5)]:
            self.assertEqual(self.center_pixel(r, c)[3], 0, (r, c))

    def test_flipped_stone_loses_hint(self):
        # 人間=白。黒が (2,3) に打って (3,3) の白が黒に反転 → そのマスに漢字は出ない
        b = apply_move(initial_board(), 2, 3, BLACK)
        args = make_args(b, WHITE, WHITE, True, glyph="田")
        self.render(args)
        self.assertEqual(args["hint"], [[4, 4]])
        self.assertFalse(any(self._bright(p) for p in self.pixels(3, 3)))   # 黒石になったマス
        self.assertTrue(any(self._dark(p) for p in self.pixels(4, 4)))       # 白石のまま


if __name__ == "__main__":
    unittest.main()
