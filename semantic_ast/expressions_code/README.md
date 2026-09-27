# コードの構造的変換（`semantic_ast/expressions_code/`）

意味AST（`semantic_ast/schema.py`、パッケージ全体は[../README.md](../README.md)）から学習対象のPythonコード（`solve(xs, k)`）を作る部分。`homework.md`「コードの構造的変換」と`task_list.md`の

- 意味ASTに基づいてコードを構造的変換(タグに基づいて複数種類用意する)

を実装したもの。**同じ意味ASTから複数の等価コード**を生成し、**すべて参照インタプリタと突き合わせてから**保存する。

日本語指示文の生成（`../expressions_ja/`）と違い、ここに教師モデルは一切関与しない。`homework.md`が「正解の意味構造、コード、テストはルールベースで作成し、教師は自然言語（日本語）表現を増やす役割に限定する」と明示しているとおり、コードは完全にルールベースで生成する。

## ファイル構成

```
semantic_ast/expressions_code/
  code_styles.py      スタイル軸（内包表記/forループ、一時変数、変数名、条件順、reverse、注釈、コメント）とスタイルカタログ
  code_generator.py   意味AST × CodeStyle → Pythonソース、レコード化・保存・再生成
  code_verifier.py    参照インタプリタとの突き合わせ（ast.parse・安全性・実行・純粋性）
  code_demo.py        一気通貫（生成→検証→保存→読み戻して再生成一致を確認）

  samples.jsonl       生成コードのサンプル（コミット対象。code_demo.pyの出力）
  samples.md          同じサンプルを読みやすくしたもの（自動生成）
```

単体テストは`../tests/test_code_styles.py`と`../tests/test_code_generator.py`（パッケージ共通の`tests/`に置く慣習に合わせている。Docker不要）:

```bash
python -m unittest discover -s semantic_ast/tests -v
```

## 1. スタイル軸とカタログ（`code_styles.py`）

`homework.md`が挙げる変換軸をそのまま軸にしている。

| 軸 | 値 | homework.mdの記述 |
| --- | --- | --- |
| `form` | `comprehension` / `loop` | 内包表記と通常の`for`ループ |
| `temporaries` | `none` / `reused` / `staged` | 一時変数の有無、1行の`return`と複数行形式 |
| `names` | `default` / `terse` / `verbose` | 変数名の変更 |
| `order_spelling` | `builtin` / `explicit` | `reverse=True`と逆順操作 |
| `annotations` | あり / なし | 型注釈の有無 |
| `comments` | あり / なし | コメントの有無 |

「条件式の順序変更」は軸にしていない。連続する抽出は操作列の順に`and`でつなぐが、その順序は意味ASTの一部（`../README.md`「順序が違えば別の意味AST」）なので、入れ替えると**順序違いの別の意味AST**のコードになってしまう。

「一時変数の有無」と「1行の`return`と複数行形式」は実際には同じ軸になる（一時変数を使わないことが1行`return`を可能にしている）ので1つにまとめ、代わりに`staged`（段ごとに別名の変数を置く）を加えて3値にしている。

全軸の直積は144通りだが、`order_spelling`は`order:reverse`を持つ意味ASTでしか意味を持たない（下記タグ）ので、残りは`form`×`temporaries`×`names`×`annotations`×`comments`の72通りになる。このうち`loop`×`none`の6通りは書き分けようがない——`for`ループは反復をまたいで`append`する先が必要なので、`_loop_body`は`none`を`reused`とまったく同じに描画し、別の`code_style`名で1バイト違わず同一のコードができてしまう。残る**30種の基本形**（`comprehension`が3×3×2、`loop`が2×3×2）にコメントなし／ありの2通り（`_commented`が付く方が固定のカテゴリ別コメント入り）を掛けた**60種**が`STYLES`の本体で、さらに下記タグで出し分ける2種が続く。

内包表記・ループ・一時変数・変数名・注釈・コメントの直積を**間引かずに埋めている**のは、日本語側が意味ASTあたり数百〜数千通りの異なる指示文を書けるため、1つの意味ASTから取れる(指示文, コード)の組数がこのカタログだけで決まるから（`data/corpus_generator.py`はコード1件に指示文1件を対応させる）。適用可能なスタイルは互いに必ず異なるコードを出す（`annotations`はシグネチャと各変数の初出、`names`は識別子、`comments`はコメント行を必ず動かす）ので、**どの意味ASTからも52〜62種類**のコードができる（順序・切り出しだけの155件は52種類、大半は60種類、`order:reverse`を持てば62種類）。各軸の各値が最低2回は現れ、名前から形が分かり、軸の定数は公開したままなので別のカタログを組むこともできる。スタイル名がそのまま`homework.md`のデータレコードの`code_style`になる。

### タグによる出し分け

一部のスタイルは、特定の意味ASTでしか**別物にならない**:

- `explicit_reverse` / `for_loop_explicit_reverse`（`list(reversed(...))`、`result = result[::-1]`）は`order:reverse`がないと書き分けようがない
- `temporaries=none`の内包表記のうち4種（`list_comprehension_default_bare` / `_terse_typed` / `_verbose_typed` / `_verbose_bare`）は、抽出も変換もない意味AST（`sorted(xs)[:k]`のように何も内包しないコードになる）では変数名を動かす先がなく、注釈の値が同じ他方と一致してしまう。そこで`filter`か`map`の操作を持つ意味ASTだけに出す（`NEEDS_ELEMENT`）。`reused`と`staged`は操作に関係なく必ず変数を名付けるので、この制限は`none`の行だけに要る

`descending`の別表記（`sorted(xs)[::-1]`や`.sort()`+`.reverse()`）は**使わない**。これは`ascending`→`reverse`という別の意味ASTのコードと1バイト違わず一致してしまい、「異なる意味ASTには異なるコード」が崩れるため。`descending`は常に`reverse=True`で書く。

該当しない意味ASTでこれらをレンダリングすると、**別の`code_style`名を持つバイト単位で同一のコード**ができてしまい、コーパスのスタイル分布が静かに壊れる。そこで各スタイルは`SemanticAST.op_tags()`／`SemanticAST.categories()`に対する条件（`StyleRequirement`）を宣言し、`styles_for(ast)`がその意味ASTが実際に行使できるスタイルだけを返す。全意味AST14,424件について、適用可能なスタイルが互いに異なるコードを出すことは`tests/test_code_styles.py`が網羅的に検査する。

`select_styles(ast, n)`は、適用可能なスタイルの列を**意味ハッシュ由来のオフセットで回転させてから**n個取る。先頭からn個取ると`list_comprehension`が全レコードに現れてカタログ後半がほぼ使われず、`homework.md`の「コード形式を均す」と逆のことになるため。回転量は`semantic_hash`から取る（実行ごとに変わる組み込み`hash()`ではない）ので、再現性がある。

## 2. コード生成（`code_generator.py`）

```python
from code_generator import render, variants
from code_styles import STYLES_BY_NAME
from schema import SemanticAST

ast = SemanticAST.of("filter:even", "map:mul_const:2", "order:ascending")
print(render(ast, STYLES_BY_NAME["list_comprehension"]))
# def solve(xs: list[int], k: int) -> list[int]:
#     return sorted([x * 2 for x in xs if x % 2 == 0])   ← homework.mdの作問例から条件 x >= k を外したもの

for variant in variants(ast, n=3):   # タグで絞ったうえで回転して3種類
    print(variant.style.name, variant.code_sha256[:12])
```

**順序を保つ生成**: コードは意味ASTの操作列（`ast.ops`）を**左から順に1つずつ**書き下す。したがって同じ原子操作の組でも順序が違えば、どのスタイルでも必ず別のコードになる（同じ関数を計算する順序違い、例えば抽出とソートの入れ替えでも）。全14,424意味AST×全スタイル（291,890件）で、異なる意味ASTのコードが1件も一致しないことを`tests/test_code_generator.py`が毎回検査している。

隣り合う操作は次の規則で**段**（`_stages`）にまとめるが、まとめても順序は失われない:

| 段 | まとめ方 | 例 |
| --- | --- | --- |
| 抽出の連続→変換の連続 | 1つの内包表記/ループ。条件は操作順に`and`でつなぎ、変換は操作順に入れ子にする | `[(x + k) * 2 for x in xs if x % 2 == 0 and x > 0]` |
| 変換の後の抽出 | 新しい段（外側の内包表記） | `[x for x in [x * 2 for x in xs] if x % 2 == 0]` |
| 切り出しの連続 | 添字の連鎖 | `xs[:k][::2]` |
| 並べ替え | 1操作1段 | `sorted(sorted(xs), reverse=True)` |

`staged`スタイルは操作1つにつき1文で、同じカテゴリが2回目以降に現れると変数名に`_2`、`_3`を付ける（`kept`, `kept_2`）。reusedのループ形式で別の段の後にループが来るときは、反復中のリストに追記しないよう`NameScheme.buffer`に集めてから差し替える。スタイルが変えるのは**その書き方**だけで、計算する内容と操作の順序は絶対に変えない。

**演算子の優先順位**: 連結された`map`は1つの式に合成されるので、文字列連結ではなく優先順位で括弧を付ける必要がある。`add_k`→`mul_const(2)`は`(x + k) * 2`、`negate`→`square`は`(-x) ** 2`（括弧なしの`-x ** 2`はPythonでは`-(x ** 2)`と読まれてしまう）。`_Expr`がテキストと一緒に優先順位を持ち回り、必要な箇所だけ括弧で包む。

**生成されるコメント**: コメント軸はカテゴリ単位の固定文（「# 条件に合う要素だけを残す」）だけを出す。操作ごとの説明コメントにすると、モデルが出力すべきラベルの内部に**指示文のもう一つの言い換え**が入り込むことになり、自然言語の文面は教師モデルと人間チェック（`../expressions_ja/`）の担当であってこの生成器の担当ではない。カテゴリ単位のコメントは意味ASTが既に確定させている情報しか持たないので、コードとずれようがない。

## 3. 検証（`code_verifier.py`）

`homework.md`:「すべてのコードを実行し、参照インタプリタと同じ結果になる場合だけ採用する」「両者の出力をランダムテストで比較する。これにより、コード生成器自身のバグを検出する」。

| 項目 | 内容 | 由来 |
| --- | --- | --- |
| `syntax_ok` | `ast.parse`が通る | `sandbox/ast_safety.py` |
| `ast_safe` | 許可構文・許可ビルトイン・シグネチャだけ | `sandbox/ast_safety.py` |
| `executable` | 制限名前空間で`solve`が取り出せる | `sandbox/runner.py` |
| `tests_passed` | 全テストケースで参照インタプリタと一致 | `sandbox/runner.py` |
| `pure` | どのケースでも`xs`を書き換えていない | `sandbox/runner.py` |

5項目とも`sandbox/`のものを**再実装せずにimportして**使う。モデル生成コードが評価時に通されるのと同じ基準でコード生成器を測るため。

`cross_check(ast, code, seed=...)`は、レコードが持っているテストとは**別の乱数入力**で比較する。保存済みテストは意味ASTごとに1回生成したものなので、それで再確認してもコーパスを作ったときの結果をなぞるだけになる。別シードで引き直した入力で比べることで、保存済みテストがたまたま見逃す生成器のバグを捕まえられる。

### なぜDockerサンドボックスの外で実行するのか

`sandbox/client.py`は「信頼できないモデル生成コードはコンテナの中でしか実行しない」と明記している。ここで実行するのはそのどちらでもない——このリポジトリの閉じた語彙から`code_generator.py`が生成したコードであり、実行前に`ast_safety.verify_static`を通し、`runner.build_restricted_globals()`の制限名前空間でテストごとにアラーム付きで走らせている。全意味ASTの全レンダリングを検証できるのはこの速さがあるからで、スニペット1つにつきコンテナを1つ立てると数桁遅くなる。`verify_in_sandbox()`（`code_demo.py --sandbox N`）が本物のコンテナでの抜き取り検査を行い、2つの経路が一致することを確認する。モデルが生成したコードは今までどおり常にコンテナで実行する。

## 4. 一気通貫（`code_demo.py`）

```bash
python semantic_ast/expressions_code/code_demo.py                    # 各split 200件、各意味ASTに適用可能な全スタイル
python semantic_ast/expressions_code/code_demo.py --limit 0          # 全件
python semantic_ast/expressions_code/code_demo.py --sandbox 5        # Dockerでの抜き取り検査つき
```

`semantic_ast/out/ast_{split}.jsonl`（`demo.py`の出力）の意味ASTとテストを読み、スタイルを選んでレンダリングし、検証して`semantic_ast/out/code_{split}.jsonl`に保存し、読み戻して**保存されたコードが今の生成器から1バイト違わず再生成できるか**を確認する（生成器は決定的なので、ずれたらディスク上のコーパスが生成器と合っていないということ）。`demo.py`未実行なら、列挙した網羅サンプルだけを生成する。

同時に、コミット対象の`samples.jsonl` / `samples.md`（下記）も書き出す。

保存レコードの形式:

```json
{"spec_id": "train-000042",
 "semantic_ast": {"ops": [["filter", "even"], ["map", "mul_const", 2], ["order", "ascending"]]},
 "semantic_hash": "...",
 "codes": [{"code_style": "for_loop", "code": "def solve(...)...", "code_sha256": "...",
            "verification": {"syntax_ok": true, "ast_safe": true, "executable": true,
                             "tests_passed": true, "pure": true, "error": null}}]}
```

`homework.md`のデータレコードは`reference_code`と`code_style`を1つずつ持つ形になっているが、ここでは`codes[0]`がそれに当たる（カタログ順で最初に適用できたスタイル）。1意味AST1レコードにしてあるのは、分割の単位が意味ASTだからで、`expressions_ja`が日本語の言い換えを1レコードに束ねているのと同じ理由。`spec_id` / `semantic_hash`で`out/{split}.jsonl`にも`out/instructions_{split}.jsonl`にも結合できる。

## 5. 生成されたコード（`samples.jsonl` / `samples.md`）

コーパス全体（全件・全スタイルで約33万スニペット）はコミットするには大きすぎるので、`semantic_ast/out/code_{split}.jsonl`（gitignore済みの生成物）に置き、**レビュー用の抜粋**を`samples.md`（読む用）と`samples.jsonl`（`verification`つきの機械可読版）としてこのディレクトリに置いている。抜粋する意味ASTは、`homework.md`の作問例を先頭に、スタイル・構成パターン・原子操作の3軸をそれぞれ網羅する列を交互に取って選ぶ（どれか1軸に枠を使い切らないようにするため）。どちらも`code_demo.py`が生成するので、手で編集しない。

## このディレクトリが担っていないこと（後続のタスクリスト項目）

- Dockerサンドボックスでの本番検証（タイムアウト・メモリ上限つきの全件実行。`sandbox/`とタスクリストの「コードを検証」）
- 訓練候補の選抜（長さ上限、完全重複コードの除去、意味ASTごとの上限、コード形式を均す抽出。`homework.md`「データの検証と選抜」）
- 日本語指示文との結合（`../expressions_ja/`の`instruction_ja`と`codes`を`spec_id`で突き合わせて学習例にする）
- BPEトークナイザ・モデル本体・学習・評価
