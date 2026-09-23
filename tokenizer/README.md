# BPEトークナイザ (`tokenizer/`)

`homework.md`の「トークナイザ」節、および`task_list.md`の「日本語表現とコードからBPEトークナイザを作成」を実装したもの。`semantic_ast/`が作った**訓練データだけ**（`semantic_ast/out/instructions_train.jsonl` / `code_train.jsonl`）から、日本語指示文とPythonコードを同一語彙で扱うbyte-level BPEトークナイザを学習する。

## ファイル構成

```
tokenizer/
  sampling.py         instructions_train.jsonl と code_train.jsonl を spec_id で突き合わせ、
                       意味ASTごとに (instruction_ja, code) のペアをサンプリング
  train_tokenizer.py  ペアを1レコードのテキストに整形し、byte-level BPEトークナイザを学習
  demo.py             上記を一気通貫で実行し tokenizer/out/tokenizer.json を書き出す
  tests/               単体テスト（外部データ・GPU・Docker不要）
```

## なぜ train split だけか

`homework.md`: 「訓練データだけを用いて、BPEまたはUnigramトークナイザを作成する」。`sampling.py`は`instructions_train.jsonl`/`code_train.jsonl`という**ファイル名レベル**でtrain splitしか受け取らない作りになっており、val/test側のファイルを渡さない限り、その内容がトークナイザの語彙に混ざることは構造的に起こらない（`semantic_ast/split.py`が意味ASTレベルで分割し、`expressions_ja`/`expressions_code`がそれをそのまま`{instructions,code}_{train,val,test}.jsonl`に反映しているので、split単位の一貫性はそちらで担保済み）。

## サンプリング（`sampling.py`)

`instructions_train.jsonl`は1レコードにつき`instruction_ja`（言い換え3件）、`code_train.jsonl`は1レコードにつき`codes`（検証済みコードスタイル、通常3件）を持つ。両ファイルに共通する`spec_id`（=同じ意味AST）ごとに、その直積（例: 3×3=9通り）から`n_per_ast`件（既定5件）を、`(seed, spec_id)`から作った`random.Random`でシャッフルして取り出す（`semantic_ast/split.py`の「キーごとに独立したseed付きRNGを使う」という慣習を踏襲）。組み合わせ数が`n_per_ast`未満のときは、重複させずに全通りを返す。

コード側は`verification`（`syntax_ok`/`ast_safe`/`executable`/`tests_passed`/`pure`が真、`error`が`None`、`cross_check_ok`があれば真）を満たすものだけを対象にする。日本語側は`expressions_ja`の人間チェック済み表現辞書（`filtered.json`)からすでに生成されているため、追加のフィルタは行わない。

現状、日本語表現の生成はコード生成より進んでいないため（`instructions_train.jsonl`は約200件、`code_train.jsonl`は約32,000件)、実際に使われるのは両者に共通する約200件の意味ASTだけになる。日本語表現の生成が進めば、`sample_pairs`は何も変更せずに使えるペア数を増やせる。

```python
from sampling import sample_pairs

pairs = sample_pairs(n_per_ast=5, seed=0)  # 既定で instructions_train.jsonl / code_train.jsonl を読む
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
- **特殊トークン**: `SPECIAL_TOKENS = ("<|pad|>", "<|bos|>", "<|eos|>", "<|task|>", "<|code|>", "<|explanation|>")`。BPEのマージ対象にはならず、常に1トークンとしてエンコードされる。
- **語彙数**: `train_from_texts(..., vocab_size=8192)`が既定（`homework.md`のBoku-nano仕様に合わせた値）。実際に学習される語彙数はコーパスサイズによって`vocab_size`未満で頭打ちになることがある（マージできるペアが尽きた場合）。

```python
from sampling import sample_pairs
from train_tokenizer import pair_to_text, train_from_texts, save

pairs = sample_pairs(n_per_ast=5, seed=0)
texts = [pair_to_text(p.instruction_ja, p.code) for p in pairs]
tokenizer = train_from_texts(texts, vocab_size=8192)
save(tokenizer, "tokenizer/out/tokenizer.json")
```

## 一気通貫デモ

```bash
python tokenizer/demo.py
python tokenizer/demo.py --n-per-ast 5 --vocab-size 8192 --seed 0
```

サンプリング件数、コーパス文字数、学習後の語彙数、特殊トークンのID、1レコードのエンコード例とbyte-fallbackのラウンドトリップ確認を表示し、`tokenizer/out/tokenizer.json`（生成物、`.gitignore`済み）に保存する。

## 単体テスト

```bash
python -m unittest discover -s tokenizer/tests -v
```

## このディレクトリが担っていないこと

- 学習データの均等抽出・上限設定（現状は意味ASTあたり固定`n_per_ast`件のみ。「いったん」の暫定実装で、`homework.md`が求める操作数・演算子・コード形式・日本語テンプレートの均し方は未実装）
- トークナイザの評価（圧縮率、未知語率、語彙の質など）
- Unigramトークナイザとの比較
- モデル本体・学習・評価（`semantic_ast/README.md`と同様、これらは対象外）
