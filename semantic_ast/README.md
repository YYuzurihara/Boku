# 意味AST (Semantic AST) パッケージ

`homework.md` の「データ生成 > 意味表現の生成」、および `task_list.md` の

- 意味ASTを作成
    - train,val,testへの分割と問題の特性に応じたラベル付与
    - テストケース作成
    - 意味ASTレベルでtrain/val/testのhashに重複がないかを確認する(データ漏洩検査)
    - 重複除去
    - 均等抽出のためにラベルごとに上限を設けておく

を実装したもの。日本語指示文や生成コードより **先に** 存在する、問題の意味を表す中間表現（原子操作の列 `{"ops": [[...], ...]}`）と、それを軸にしたデータパイプラインの土台を提供する。

## ファイル構成

```
semantic_ast/
  schema.py                 意味ASTのデータ構造・検証・正規化・ハッシュ
  reference_interpreter.py  意味ASTを (xs, k) に対して直接実行する「正解を計算する参照インタプリタ」
  generator.py               意味ASTの全列挙 + ラベル付与
  testcases.py               境界値+ランダムなテストケース生成、境界値テスト専用スイート生成（参照インタプリタでexpectedを計算）
  split.py                   重複除去・層化train/val分割・3種のテスト集合（言い換え/組合せ汎化/境界値）・漏洩検査
  demo.py                    上記を一気通貫で実行し semantic_ast/out/*.jsonl を書き出す

  expressions_ja/            意味AST→日本語指示文（instruction_ja）の生成。コードも表現辞書もここ（expressions_ja/README.md）
  expressions_code/          意味AST→Pythonコードの構造的変換（複数スタイル）と参照インタプリタとの突き合わせ（expressions_code/README.md）
  tests/                     単体テスト（外部依存なし。expressions_ja/のテストもGPU・モデル不要、expressions_code/のテストもDocker不要）
```

日本語指示文の生成は[expressions_ja/README.md](expressions_ja/README.md)に、コードの構造的変換は[expressions_code/README.md](expressions_code/README.md)に分けてある。テストだけはパッケージ共通の`tests/`に置いたままにしている。

## 意味ASTのスキーマ

```json
{
  "ops": [["filter", "even"], ["map", "mul_const", 2], ["order", "ascending"]]
}
```

意味ASTは**24種類の原子操作から1〜3個を、重複を許して、順序つきで並べた列**で、左から順に実行する（`schema.py`）。

| カテゴリ | 原子操作 | 数 |
|---|---|---|
| `filter`（抽出） | `even` `odd` `gt_k` `ge_k` `lt_k` `le_k` `multiple_of_k` `positive` `negative` `zero` | 10 |
| `map`（変換） | `add_k` `sub_k` `mul_k` `negate` `abs` `square` `mul_const(2)` `mul_const(3)` | 8 |
| `order`（並べ替え） | `ascending` `descending` `reverse` | 3 |
| `slice`（切り出し） | `take_first_k` `take_last_k` `step_2` | 3 |

- 各操作は`[カテゴリ, 名前]`（`mul_const`だけ`[カテゴリ, 名前, 定数]`）。`mul_const(2)`と`mul_const(3)`は別の原子操作として数える。`descending`はソートだが`reverse`は現在の並び順をひっくり返すだけで、意味的に異なる操作として区別している。
- **重複可**: 同じ原子操作・同じカテゴリを何度使ってもよい（`[filter:even, filter:even]`、`[order:reverse, order:reverse]`、`[slice:take_first_k, map:add_k, slice:take_first_k]`）。カテゴリの並びにも制約はない。
- 全体の数は 24 + 24² + 24³ = **14,424種類**（`generator.enumerate_all()`）。
- コードで作るときは`SemanticAST.of("filter:even", "map:mul_const:2", "order:ascending")`のように原子操作のタグ（`AtomicOp.tag`）を並べる。

### 順序が違えば別の意味AST

同じ原子操作の組み合わせでも、**順序が異なれば異なる意味AST**として扱う。`semantic_hash`は操作列をその順のままハッシュするので、`[filter:even, order:ascending]`と`[order:ascending, filter:even]`は別のハッシュ・別の日本語指示文・別のコードになる。

- 結果として同じ関数になる順序違い（抽出とソートの入れ替えなど）や、冗長な重複（`[filter:even, filter:even]`）、打ち消し合う重複（`[order:reverse, order:reverse]`＝恒等写像）も、正準形に畳まずそのまま別の意味ASTとして残す。指示文に書かれた順序が、コードが従うべき順序だからである。
- 日本語指示文は常に操作列の順に語る（`expressions_ja/README.md`）。コードも操作列の順に書き下し、全14,424意味AST×全スタイルで**異なる意味ASTのコードが1件も一致しない**ことをテストで保証している（`expressions_code/README.md`）。
- 注意: 計算結果が同じ順序違いの2つの意味ASTが、trainとtestに分かれて入ることはありうる（ハッシュが別なので漏洩検査はこれを漏洩とみなさない）。

## 使い方

### 全列挙

```python
from generator import enumerate_all

all_asts = enumerate_all()   # 14,424種類（長さ1: 24、長さ2: 576、長さ3: 13,824。全て相異なるsemantic_hashを持つ）
```

`homework.md`のデータ規模表の「生成する意味AST 30,000〜100,000種類」には届かないが、語彙は`homework.md`が明示する24の原子操作に留め、水増しはしていない。

`generator.label(ast)`は**カテゴリの並び**（例: `("filter", "map", "order")`）を層化ラベルにする。ラベルは4 + 16 + 64 = 84種類で、1ラベルあたり3〜1,000件。

### 参照インタプリタ

```python
from reference_interpreter import interpret
from schema import SemanticAST

ast = SemanticAST.of("filter:even", "map:mul_const:2", "order:ascending")
interpret(ast, xs=[1, 5, 2, 8, -4, 10, 3], k=3)  # -> [-8, 4, 16, 20]
interpret(SemanticAST.of("order:ascending", "map:mul_const:2", "filter:even"), xs=[1, 5, 2, 8, -4, 10, 3], k=3)
# -> [-8, 2, 4, 6, 10, 16, 20]（先に並べ替え、全要素を2倍してから偶数を残すので結果が変わる）
```

### テストケース生成

```python
from testcases import generate_test_cases

cases = generate_test_cases(ast, seed=42)
# 空リスト・要素1個・全要素同値・境界値などの固定ケース + ランダムケース(既定24件)
# 各ケースは {"xs": ..., "k": ..., "expected": ...} で、expectedは参照インタプリタが計算
```

### 分割・重複除去・漏洩検査

```python
from split import stratified_split, dedup_by_hash, check_no_leakage, SplitRatios

deduped = dedup_by_hash(all_asts)
splits = stratified_split(deduped, ratios=SplitRatios(0.9, 0.1), seed=0)  # train / val
check_no_leakage(splits)  # 同じ意味ASTが複数のsplitに跨っていないかを検査
```

`stratified_split`は意味AST単位で分割する（`homework.md`: 「意味ASTを分割した後で言い換えやコード変換を行わないと...データ漏洩...」）。分割の基本単位が意味AST全体なので、後続で1つの意味ASTから何個の日本語言い換え・コード変換を生成しても、それらは自動的に同じsplitに属し、原理的に漏洩しにくい構造になっている。`check_no_leakage`はそれでも万一の重複混入（例: 分割前の重複除去漏れ）を検出するための独立した安全網。

### 3種のテスト集合（`homework.md`「訓練・検証・テスト分割」）

`build_eval_splits`が意味ASTを次の5グループに**互いに素**に分ける（`split.ALL_SPLITS`）。どのグループも意味AST単位なので、`check_no_leakage`が5グループ全体に効く。

通常テスト（`test`）は置かない。テスト集合の意味ASTはどれも訓練で未見なので、「未見の意味ASTで解けるか」は3つのテスト集合がすべて測っており、別に分けても同じことを測るだけになるため。訓練から外した意味ASTは、3つのテスト集合のどれか1つにだけ入る。

| split | 内容 | 何を測るか |
|---|---|---|
| `train` / `val` | 3つのテスト集合を除いた残りを90/10に層化分割 | 学習・検証 |
| `test_paraphrase`（言い換えテスト） | 訓練で使わない日本語テンプレートだけで作った指示文（意味ASTは未見） | 言い回しへの頑健性 |
| `test_compositional`（組合せ汎化テスト） | `split.HOLDOUT_PAIRS`の演算ペア（例: `filter:even`と`order:descending`）を**同時に含む**意味AST全て | 別々に学んだ演算の組み合わせ |
| `test_boundary`（境界値テスト） | 空リスト・要素1個・全要素同値・負数のみ・全要素不合格などの入力だけをテストケースにした意味AST | 端の場合の正しさ |

- **組合せ汎化**: ペアは4組（全て異なるカテゴリ間、どちらの順序で現れても該当）。各ペアが140件、計554件。ペアを含む意味ASTは`test_compositional`にしか入らず、train/val/他のテスト集合には**1件も**入らない。一方でペアの各演算は単独ではtrainに出現する。両方を`check_holdout_pairs`が検査する（demo.pyでも毎回実行）。
- **言い換え**: 表現辞書の**操作キー**（`filter:*`/`map:*`/`order:*`/`slice:*`で表現が2件以上あるもの）から`ja_generator.PARAPHRASE_RATIO`（25%、最低1件・全件は不可）を`template_pools`が予約する。`test_paraphrase`はその予約分だけ、他の全split（train/val/test_compositional/test_boundary）は予約分を**使わない**。予約しないのは、表現が1件しかないキー（`map:mul_const`など）と、`frame:`で始まる枠キー（`opening`/`closing`/`filter_verb`）で、どちらも全splitで共有し`shared_keys`に出る。枠を予約対象から外しているのは、言い換えの対象は**操作の言い方**であって枠は定型文だからで、枠まで4分の1に絞ると1操作の意味ASTが作れる異なる文が opening 3種 × closing 1種まで落ち、コード件数（1意味ASTあたり20〜22件）に届かなくなる。共有した状態では全14,424件が自分のコード件数以上の異なる文を持てるので、`corpus_generator.py`の繰り返し補完（下記）は発火しない。`ja_demo.py`は保存した各文が自分のsplitのプール内かを検証し、コード件数に足りない意味ASTがあれば報告する。
- **境界値**: `testcases.generate_boundary_test_cases`が、フィルタを持つ意味ASTには「最初のフィルタが全要素を落とす」入力を含める（空でない入力に限る）。フィルタ付き11,470件のうち11,356件で見つかる。見つからない114件は、フィルタより前の変換がフィルタを恒真にしているもの（`map:mul_const:2`→`filter:even`など、どんな入力でも全要素が残る）。

**分割の順序と件数**: 8:1:1 に分けてからテストを3つに割るのではなく、**先にテスト集合3つを分離し、残りを90/10で train/val に分ける**。組合せ汎化の件数は`HOLDOUT_PAIRS`で決まる（比率ではない）ので、テスト全体が10%ちょうどにはならず、割合は多少ずれる。ずれは許容している。

| split | 件数 | 全体（14,424）に対する割合 | 決め方 |
|---|---|---|---|
| `train` | 11,234 | 77.9% | テスト3種を除いた残りの90% |
| `val` | 1,248 | 8.7% | 同・残りの10% |
| `test_paraphrase` | 694 | 4.8% | 組合せ汎化を除いた残りの5%（`EvalRatios`） |
| `test_compositional` | 554 | 3.8% | `HOLDOUT_PAIRS`の4ペア×140件 |
| `test_boundary` | 694 | 4.8% | 組合せ汎化を除いた残りの5%（`EvalRatios`） |
| テスト計 | 1,942 | 13.5% | |

`split._partition`は、小さいラベルでも比率が崩れないよう割り当ての端数をラベル間で持ち越し、全体の比率を保つ。

**テスト集合ごとの個別生成**: 各意味ASTがどのsplitに入るかは、常に全意味ASTに対する分割（`seed`だけで決まる）で決める。そのため、一部のsplitだけを書き出しても、中身は全部まとめて生成したときと同じで、split同士が互いに素なのも変わらない。どのスクリプトも`--splits`で対象を選べる。

```bash
python semantic_ast/demo.py --splits test_boundary
python semantic_ast/expressions_ja/ja_demo.py --splits test_boundary
python semantic_ast/expressions_code/code_demo.py --splits test_boundary --limit 0
python data/corpus_generator.py --splits test_boundary
python model/evaluate.py --ckpt ... --splits test_boundary
```

### 一気通貫デモ

```bash
python semantic_ast/demo.py
```

全列挙→重複除去→層化分割→漏洩検査→テストケース生成、を実行して`semantic_ast/out/ast_{split}.jsonl`（5 split、`--splits`で一部だけも可）を書き出す（`out/`は生成物なので`.gitignore`済み）。各レコードは`homework.md`のデータレコード例のうち`spec_id`/`semantic_ast`/`semantic_hash`/`tests`に対応する。`instruction_ja`は`expressions_ja/`が`out/instructions_{split}.jsonl`に、`reference_code`/`code_style`は`expressions_code/`が`out/code_{split}.jsonl`に、それぞれ同じ`spec_id`で書き出す。

### 日本語指示文の生成

表現辞書の生成（教師モデルへの問い合わせ）と、意味AST→`instruction_ja`の結合は`expressions_ja/`に分けてある。プロンプト・表現辞書の形式・結合規則・結合契約は[expressions_ja/README.md](expressions_ja/README.md)を参照。

```bash
python semantic_ast/expressions_ja/ja_teacher.py   # 表現辞書を生成（要GPU）
python semantic_ast/expressions_ja/ja_demo.py      # 表現辞書→結合→保存→再現性検証
```

### コードの構造的変換

同じ意味ASTから複数の等価なPythonコード（スタイル違い）を生成し、参照インタプリタと突き合わせる部分は`expressions_code/`に分けてある。スタイル軸・タグによる出し分け・検証の詳細は[expressions_code/README.md](expressions_code/README.md)を参照。

```python
from code_generator import variants
from schema import SemanticAST

ast = SemanticAST.of("filter:even", "map:mul_const:2", "order:ascending")
for variant in variants(ast, n=3):
    print(variant.style.name)
    print(variant.code)
```

```bash
python semantic_ast/expressions_code/code_demo.py  # 生成→検証→out/code_{split}.jsonl→再生成一致の確認
```

### 単体テスト

```bash
python -m unittest discover -s semantic_ast/tests -v
```

## このパッケージが担っていないこと（後続のタスクリスト項目）

- 生成された日本語表現の人間によるチェック・承認（`expressions_ja/README.md`「このディレクトリが担っていないこと」）
- 生成コードの`sandbox/`（Docker）による本番検証と、訓練候補の選抜（`expressions_code/README.md`「このディレクトリが担っていないこと」）
- BPEトークナイザ・モデル本体・学習・評価
