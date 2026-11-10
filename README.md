# app-practice

Streamlit の練習用マルチページアプリ。

公開URL: https://app-practice-8da4fnwuy2hjuejq3dbnwm.streamlit.app/

## ページ構成

| ページ | 内容 |
|---|---|
| app | 2つの整数を入力し、積と和を表示する。`reset` ボタンで入力を戻す |
| hangman | 英単語を当てるハングマン。A〜Z のボタンで文字を選ぶ。ミスは8回まで(8回目でゲームオーバー)。正解・ゲームオーバーのどちらでも答えの単語と日本語の意味が表示される |
| high and low | トランプ(画像カード)を使った High & Low。`high` / `draw` / `low` から選んで予想する。得点・問題数・正解数・誤答数を表示する |

## High & Low のルール

- 2枚のカード(`enemy` と `result`)の数字(rank)を比較する。スートは spades / hearts / diamonds / clubs。
- `result` の rank が `enemy` より大きければ答えは `high`、小さければ `low`、同じなら `draw`。
- `high` / `draw` / `low` のいずれかを選ぶ。選択するとボタンが無効になり、正解・不正解と答え(カードと high/low/draw)が表示される。
- 得点・カウント:

| 結果 | 得点 | 正解数 | 問題数 |
|---|---|---|---|
| high / low 正解 | +1 | +1 | +1 |
| draw 正解 | (現在の得点 + 1) × 2 | +1 | +1 |
| 不正解 | 変化なし | 変化なし | +1 |

## 実行方法

```bash
pip install streamlit
streamlit run app.py
```

## 技術

- Python 3.12 以上(f-string 内で同種の引用符をネストしているため)
- Streamlit

## 素材

- ハングマンの単語リスト: 作者が作成
- カード画像: PixAI の Tsubaki.3 で生成し、数字は作者が書き加えた
- スートのアイコン: Claude が作成

## ライセンス

- カード画像(PixAI 生成、数字は作者が加筆): 作者は第三者による利用(転載・再配布・商用利用を含む)を許可しない。
- コードおよびその他の素材(スートのアイコンなど): 個人利用のみ可。
