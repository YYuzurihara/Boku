# BPEトークナイザ (`tokenizer/`)

`homework.md`の「トークナイザ」節、および`task_list.md`の「日本語表現とコードからBPEトークナイザを作成」を実装したもの。`data/corpus_generator.py`が作った**訓練データだけ**（`data/train.jsonl`）から、日本語指示文とPythonコードを同一語彙で扱うbyte-level BPEトークナイザを学習する。

## ファイル構成

```
tokenizer/
  sampling.py         data/train.jsonl からレコード（意味AST）単位で
                       (instruction_ja, code) のペアをサンプリング
  train_tokenizer.py  ペアを1レコードのテキストに整形し、byte-level BPEトークナイザを学習
  demo.py             上記を一気通貫で実行し tokenizer/out/tokenizer.json を書き出す
  tests/               単体テスト（外部データ・GPU・Docker不要）
```

## 前提: コーパスの生成

入力の`data/train.jsonl`は`data/corpus_generator.py`の出力なので、先に意味AST→コード→日本語表現→結合を済ませておく必要がある（`semantic_ast/README.md`）。

```bash
python semantic_ast/demo.py
python semantic_ast/expressions_code/code_demo.py --limit 0
python semantic_ast/expressions_ja/ja_demo.py   # コード件数を code_{split}.jsonl から読むので code_demo.py の後
python data/corpus_generator.py
python tokenizer/demo.py
```

## なぜ train split だけか

`homework.md`: 「訓練データだけを用いて、BPEまたはUnigramトークナイザを作成する」。`sampling.py`は`data/train.jsonl`という**ファイル名レベル**でtrain splitしか受け取らない作りになっており（`DEFAULT_TRAIN`）、val/testのファイルはこのモジュールに一切登場しない。そのため、それらの内容がトークナイザの語彙に混ざることは構造的に起こらない（`semantic_ast/split.py`が意味ASTレベルで分割し、`expressions_ja`/`expressions_code`と`corpus_generator.py`がそれをそのまま`data/{train,val,test_*}.jsonl`に反映しているので、split単位の一貫性はそちらで担保済み）。

## サンプリング（`sampling.py`)

`data/train.jsonl`は**1行 = 1意味AST**で、`instruction_ja`と`codes`は同じ長さのリスト、i番目同士が対になっている（対にするのは`corpus_generator.py`）。そこから全体の`percent`%（既定10）を**レコード単位**で一様に、非復元で取り出す。

- 取る件数は`round(N * percent / 100)`（Nは空行を除いた行数）。どの行を取るかは`random.Random(seed)`が行番号に対して決めるので再現可能。
- ファイルは2回読み（件数カウント→抽出）、選ばれた行だけをパースするので、メモリはサンプル数に比例する。
- 検証フィルタはサンプリングの**後**に適用する。したがって`percent`は「ファイル全体に対する割合」であって、検証済み部分集合に対する割合ではない。
- コード側は`verification`が`syntax_ok`/`ast_safe`/`executable`/`tests_passed`/`pure`すべて真で`error`が`None`のものだけを採る。`cross_check_ok`はキー自体が無いことがあるので、あれば真を要求し、無ければ通す。
- 日本語側は`expressions_ja`の人間チェック済み表現辞書（`filtered.json`）からすでに生成されているため、追加のフィルタは行わない。

現在のコーパスでは`train`が11,234意味AST（1意味ASTあたりコード52〜62件）で計675,086ペアあり、その全件が上記の検証を通る。既定の10%では1,123意味AST・67,502ペアになる。

```python
from sampling import sample_pairs

pairs = sample_pairs(percent=10.0, seed=0)  # 既定で data/train.jsonl を読む
```

## トークナイザ学習（`train_tokenizer.py`）

各ペアは`homework.md`の学習レコード例と同じ並びのテキストに整形する。

```text
<|task|>
{instruction_ja}
<|code|>
{code}
<|eos|>
```

このテキスト群を、`tokenizers`（Hugging Face製）の`models.BPE` + `pre_tokenizers.ByteLevel`でそのまま学習する。日本語文とコードを区別する前処理は一切行わず、同じイテレータに混ぜて渡すことで「日本語とPythonコードを同一語彙で扱う」を満たす。

- **byte fallback**: `initial_alphabet=pre_tokenizers.ByteLevel.alphabet()`で256バイト全てを初期語彙に含め、`models.BPE(unk_token=None)`でUNKトークン自体を作らない。どんなUnicode文字（学習データに一度も出てこなかった文字や絵文字を含む）もバイト列に分解して表現でき、`decode`で元のテキストに完全に戻る。
- **特殊トークン**: `SPECIAL_TOKENS = ("<|pad|>", "<|bos|>", "<|eos|>", "<|task|>", "<|code|>", "<|explanation|>")`で、この順にid 0〜5を占める。BPEのマージ対象にはならず、常に1トークンとしてエンコードされる。
- **1トークンの最大長**: `MAX_TOKEN_LENGTH = 16`（byte-level表現での文字数。日本語1文字は3バイト=3文字分なので、日本語では約5文字）。定型の指示文が丸ごと1トークンにマージされるのを防ぐための上限。

### 語彙数は`vocab_size`より小さいところで頭打ちになる

`train_from_texts(..., vocab_size=2048)`が既定だが、**実際に学習される語彙数はマージできるペアが尽きて`vocab_size`未満で止まる**。現在のコーパスでの実測値:

| 学習に使ったtrainの割合 | ペア数 | 文字数 | 実際の語彙数 |
|---|---|---|---|
| 10%（既定） | 67,502 | 19,569,856 | 1,269 |
| 100% | 675,086 | 196,271,696 | 1,307 |

データを10倍にしても38トークンしか増えないので、2048はコーパス量を増やせば届く値ではなく、このコーパスでは**到達不能な上限**である。理由は`MAX_TOKEN_LENGTH = 16`の制約と、扱う言語が狭いこと（意味ASTの語彙は24原子操作、コードは62スタイル、日本語は`filtered.json`の26キー分の表現）で、マージすべき異なるバイト列自体が少ないため。`vocab_size`は上限として2048のままにしてあり、実際の語彙数はその内側で自動的に決まる。

```python
from sampling import sample_pairs
from train_tokenizer import pair_to_text, train_from_texts, save

pairs = sample_pairs(percent=10.0, seed=0)
texts = [pair_to_text(p.instruction_ja, p.code) for p in pairs]
tokenizer = train_from_texts(texts, vocab_size=2048)
save(tokenizer, "tokenizer/out/tokenizer.json")
```

## 一気通貫デモ

```bash
python tokenizer/demo.py
python tokenizer/demo.py --percent 10 --vocab-size 2048 --seed 0
python tokenizer/demo.py --percent 100 --out /tmp/tokenizer_full.json   # 別の設定は --out で分けて保存する
```

サンプリング件数、コーパス文字数、学習後の語彙数、特殊トークンのID、1レコードのエンコード例とbyte-fallbackのラウンドトリップ確認を表示し、`tokenizer/out/tokenizer.json`（生成物、`.gitignore`済み）に保存する。`data/train.jsonl`が無いときは、`data/corpus_generator.py`を先に実行するよう促して終了する。

## 単体テスト

```bash
python -m unittest discover -s tokenizer/tests -v
```

## このディレクトリが担っていないこと

- 学習データの均等抽出・上限設定（現状はレコード単位の一様サンプリングのみ。「いったん」の暫定実装で、`homework.md`が求める操作数・演算子・コード形式・日本語テンプレートの均し方は未実装）
- トークナイザの評価（圧縮率、未知語率、語彙の質など）
- Unigramトークナイザとの比較
- モデル本体・学習・評価（`semantic_ast/README.md`と同様、これらは対象外）
