# 意味AST (Semantic AST) パッケージ

`homework.md` の「データ生成 > 意味表現の生成」、および `task_list.md` の

- 意味ASTを作成
    - train,val,testへの分割と問題の特性に応じたラベル付与
    - テストケース作成
    - 意味ASTレベルでtrain/val/testのhashに重複がないかを確認する(データ漏洩検査)
    - 重複除去
    - 均等抽出のためにラベルごとに上限を設けておく

を実装したもの。日本語指示文や生成コードより **先に** 存在する、問題の意味を表す中間表現（`{"filter": [...], "map": [...], "order": ..., "slice": [...]}`）と、それを軸にしたデータパイプラインの土台を提供する。

## ファイル構成

```
semantic_ast/
  schema.py                 意味ASTのデータ構造・検証・正規化・ハッシュ
  reference_interpreter.py  意味ASTを (xs, k) に対して直接実行する「正解を計算する参照インタプリタ」
  generator.py               意味ASTの全列挙 + ラベル付与
  testcases.py               境界値+ランダムなテストケース生成（参照インタプリタでexpectedを計算）
  split.py                   重複除去・層化train/val/test分割・漏洩検査・ラベル別上限
  demo.py                    上記を一気通貫で実行し semantic_ast/out/*.jsonl を書き出す

  expressions_ja/            意味AST→日本語指示文（instruction_ja）の生成。コードも表現辞書もここ（expressions_ja/README.md）
  expressions_code/          意味AST→参照コード（reference_code）の生成（未着手）
  tests/                     単体テスト（164件、外部依存なし。expressions_ja/のテストもGPU・モデル不要）
```

日本語指示文の生成は[expressions_ja/README.md](expressions_ja/README.md)に分けてある（プロンプト・表現辞書・結合規則・結合契約）。テストだけはパッケージ共通の`tests/`に置いたままにしている。

## 意味ASTのスキーマ

```json
{
  "filter": ["even", "ge_k"],
  "map": ["mul_const", 2],
  "order": "ascending",
  "slice": ["take_first_k"]
}
```

- `filter`: 0〜2個のAND結合された抽出述語（`even`/`odd`/`gt_k`/`ge_k`/`lt_k`/`le_k`/`multiple_of_k`/`positive`/`negative`/`zero`）。同じ排他グループ（例: `even`と`odd`）から2つ選ぶことはできない（常に空集合になるなど無意味な組み合わせを排除するため）。
- `map`: 0〜2個の変換を**順序付きで連結**（`add_k`/`sub_k`/`mul_k`/`negate`/`abs`/`square`、または定数`2`〜`10`のいずれかを取る`mul_const`）。同じ演算タイプを2回使うことはできない（例: `mul_const`を2回連結するのは別の`mul_const`の冗長な言い換えになってしまうため）。順序は結果に影響する（`add_k`してから`mul_const(2)` ≠ `mul_const(2)`してから`add_k`）。
- `order`: `ascending`/`descending`/`reverse`のいずれか、または無し。`descending`はソートだが`reverse`は現在の並び順をひっくり返すだけで、意味的に異なる操作として区別している。ソートや反転を連結しても意味のある多様性は生まれないため、こちらは単一選択のまま。
- `slice`: 0〜2個の切り出し操作を**順序付きで連結**（`take_first_k`/`take_last_k`/`step_2`）。同じ演算を2回使うことはできない。順序は結果に影響する（例: 先頭k個を取ってから1個おき ≠ 1個おきに取ってから先頭k個）。
- パイプラインは常に **filter → map → order → slice** の順で実行される（`reference_interpreter.py`）。`map`と`slice`はそれぞれ内部で連結順に適用される。

## 設計判断: 「1〜3個を組み合わせた問題」の解釈

`homework.md`は「以下から1〜3個を組み合わせた問題だけを扱う」と書いているが、これを字義通り取ると同じ文書内の作問例（`ge_k`・`even`・`mul_const(2)`・`ascending`の4つの原子操作を組み合わせている）と矛盾する。`sandbox/ast_safety.py`が属性アクセス制限について行ったのと同様の解決をしており、「1〜3個」を **filter/map/order/sliceという4つのカテゴリスロットのうち1〜3個が有効であること** として解釈した（`filter`スロット自体は最大2つの述語をAND結合できる。作問例は抽出+変換+並べ替え=3カテゴリなので、この解釈と整合する）。この判断は`schema.py`のモジュールdocstringに明記している。

## 使い方

### 全列挙

```python
from generator import enumerate_all

all_asts = enumerate_all()  # 40,589種類の意味AST（全て相異なるsemantic_hashを持つ）
```

`homework.md`の「生成する意味AST 30,000〜100,000種類」という目安は、この構造的な意味ASTの集合そのものの数量を指す。閉じた原子操作の語彙（filter述語10種・mapタイプ7種［`mul_const`の定数は`homework.md`の例示どおり2,3のみ］・order 3種・slice 3種、カテゴリ1〜3個有効）だけでは約3,383種類にしかならず約9倍不足するため、`map`と`slice`をそれぞれ「同一カテゴリ内で最大2個の演算を順序付きで連結できる」ように拡張することで40,589種類まで増やしている（`homework.md`が明示する操作リストの外側に新しい演算を追加せず、`mul_const`の定数も`homework.md`の例示（2倍、3倍）から広げない範囲での拡張）。設計判断の詳細と正確な組み合わせ計算は`schema.py`と`generator.py`のモジュールdocstringを参照。

### 参照インタプリタ

```python
from reference_interpreter import interpret
from schema import SemanticAST

ast = SemanticAST(filters=("even", "ge_k"), map_ops=(("mul_const", 2),), order_op="ascending")
interpret(ast, xs=[1, 5, 2, 8, -4, 10, 3], k=3)  # -> [8, 10]
```

### テストケース生成

```python
from testcases import generate_test_cases

cases = generate_test_cases(ast, seed=42)
# 空リスト・要素1個・全要素同値・境界値などの固定ケース + ランダムケース(既定24件)
# 各ケースは {"xs": ..., "k": ..., "expected": ...} で、expectedは参照インタプリタが計算
```

### 分割・重複除去・漏洩検査・上限

```python
from split import stratified_split, dedup_by_hash, check_no_leakage, cap_per_label, SplitRatios

deduped = dedup_by_hash(all_asts)
splits = stratified_split(deduped, ratios=SplitRatios(0.8, 0.1, 0.1), seed=0)
check_no_leakage(splits)  # 同じ意味ASTがtrain/val/testに跨っていないかを検査
capped = {name: cap_per_label(group, max_per_label=500, seed=0) for name, group in splits.items()}
```

`stratified_split`は意味AST単位で分割する（`homework.md`: 「意味ASTを分割した後で言い換えやコード変換を行わないと...データ漏洩...」）。分割の基本単位が意味AST全体なので、後続で1つの意味ASTから何個の日本語言い換え・コード変換を生成しても、それらは自動的に同じsplitに属し、原理的に漏洩しにくい構造になっている。`check_no_leakage`はそれでも万一の重複混入（例: 分割前の重複除去漏れ）を検出するための独立した安全網。

### 一気通貫デモ

```bash
python semantic_ast/demo.py
```

全列挙→重複除去→層化分割→漏洩検査→ラベル別上限→テストケース生成、を実行して`semantic_ast/out/{train,val,test}.jsonl`を書き出す（`out/`は生成物なので`.gitignore`済み）。各レコードは`homework.md`のデータレコード例のうち`spec_id`/`semantic_ast`/`semantic_hash`/`tests`に対応する。`instruction_ja`/`reference_code`/`code_style`等は、教師モデルによる日本語表現生成・コードの構造的変換という後続のタスクリスト項目で埋める。

### 日本語指示文の生成

表現辞書の生成（教師モデルへの問い合わせ）と、意味AST→`instruction_ja`の結合は`expressions_ja/`に分けてある。プロンプト・表現辞書の形式・結合規則・結合契約は[expressions_ja/README.md](expressions_ja/README.md)を参照。

```bash
python semantic_ast/expressions_ja/ja_teacher.py   # 表現辞書を生成（要GPU）
python semantic_ast/expressions_ja/ja_demo.py      # 表現辞書→結合→保存→再現性検証
```

### 単体テスト

```bash
python -m unittest discover -s semantic_ast/tests -v
```

## このパッケージが担っていないこと（後続のタスクリスト項目）

- 生成された日本語表現の人間によるチェック・承認（`expressions_ja/README.md`「このディレクトリが担っていないこと」）
- 意味ASTに基づくコードの構造的変換（コード生成器。`expressions_code/`）
- 生成コードの`sandbox/`によるサンドボックス実行検証
- BPEトークナイザ・モデル本体・学習・評価
