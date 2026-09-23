# 日本語指示文の生成（`semantic_ast/expressions_ja/`）

意味AST（`semantic_ast/schema.py`、パッケージ全体は[../README.md](../README.md)）から`instruction_ja`を作る部分。`ja_generator_plan.md`の二段階方式を実装したもので、教師モデルに問い合わせるのは**原子操作の言い方だけ**（表現辞書キー1つにつき1リクエスト、計26件）、40,589件の意味AST→日本語文は表現辞書からのサンプリングとテンプレート結合という決定的な処理で行う。

## ファイル構成

```
semantic_ast/expressions_ja/
  ja_prompts.py         THIRD_PARTY.mdのプロンプト（system prompt・テンプレート(a)〜(d)・代入値表・出力JSONスキーマ）のコード化
  ja_teacher.py         vLLM経由でQwen3-4B-AWQに問い合わせ、表現辞書と生成ログを書き出す
  ja_dictionary.py      表現辞書（JSON）の保存・読み込み・構造検証
  ja_generator.py       意味AST→日本語指示文の結合（ja_generator_plan.md 2章）と、結合結果の保存
  ja_demo.py            表現辞書→結合→保存→読み戻し→再現性検証を一気通貫で実行

  candidates.json       表現辞書本体（ja_teacher.pyの出力、人間チェックの対象）
  generation_log.jsonl  生成ログ（1プリミティブ1行）
```

単体テストは移動せず`semantic_ast/tests/test_ja_*.py`（+ `tests/ja_fixture.py`）に置いてある。実行方法はパッケージ共通:

```bash
python -m unittest discover -s semantic_ast/tests -v
```

## 1. プロンプト（`ja_prompts.py`）

`THIRD_PARTY.md`「プリミティブへの問い合わせプロンプト」のsystem prompt・テンプレート(a)〜(e)・代入値表・出力JSONスキーマをそのまま写したモジュール。**文面の正はあくまで`THIRD_PARTY.md`**で、こちらはその機械可読なコピー。

```bash
python semantic_ast/expressions_ja/ja_prompts.py                # 全プロンプトを表示
python semantic_ast/expressions_ja/ja_prompts.py filter:ge_k    # 1件だけ表示
```

テンプレートはスロット型ごとの(a)〜(d)に加え、`filter:zero`専用の(e)がある。(a)は「k以上の」「偶数の」のような**範囲**を表す述語向けに書かれていて、等値条件の`filter:zero`に当てると逃げ道が塞がる（「0に等しい」はすでに連体形なので(a)の言う「末尾に「の」を付ける」余地がなく、残る自然な形「0である」は(a)が禁じている）。実際、(a)での生成は11件すべてが「0に等しいの」「0に等しいこと」の類になり、人間チェック後に残った表現が0件になった。(e)は許す末尾の形を列挙で示し、余計な「の」を名指しで禁じ、件数を3〜8に下げている。

プロンプトはテンプレートIDと代入値で一意に決まるので、`prompt_sha256()`が`homework.md`の要求する「プロンプトのハッシュ値」になる。

## 2. 表現辞書の生成（`ja_teacher.py`）

```bash
python semantic_ast/expressions_ja/ja_teacher.py                      # 全キーを生成
python semantic_ast/expressions_ja/ja_teacher.py --keys filter:ge_k   # 一部だけ再生成（--merge で既存に上書き）
python semantic_ast/expressions_ja/ja_teacher.py --keys filter:zero --merge   # 専用プロンプト(e)で filter:zero だけ作り直す
python semantic_ast/expressions_ja/ja_teacher.py --dry-run            # モデルを読み込まずプロンプトとログだけ確認
python semantic_ast/expressions_ja/ja_teacher.py --report-contract    # 生成済み辞書を結合契約（下記4.）で検査するだけ
```

`THIRD_PARTY.md`「呼び出し方法（vLLM 0.29.0）」の通り、非thinkingモード（`chat_template_kwargs={"enable_thinking": False}`）と構造化出力（`StructuredOutputsParams(json=...)`）で呼ぶ。1キーあたりの生成件数は5〜15件（`frame:filter_verb`は4〜8件、`filter:zero`は3〜8件）。`--keys`に`--merge`を添えると、指定したキーだけを同じ`candidates.json`に上書きし、生成ログにも追記する（他の25キーは触らない）。出力は2ファイル:

- `candidates.json` — 表現辞書本体（下記の形式。人間チェックの対象）
- `generation_log.jsonl` — 1プリミティブ1行。`homework.md`の記録項目（モデル名・revision・量子化方式・推論ライブラリ+バージョン・system prompt・sampling設定・seed・生成日時・プロンプトのハッシュ値）と**生の応答文字列**を残す

モデルの応答が壊れていてもこの段階では修正せず、そのまま保存してログに問題を書き出す（直すかどうかは人間チェックの判断であり、生成器の仕事ではない）。ただし応答が途中で切れた場合だけは、**完成している要素を回収**して`parse_error`にその旨を残す。壊れた要素を補完・修復することはしない。

生成後（および`--report-contract`）には、構造検証・重複に加えて**結合契約の検査**（`ja_generator.contract_problems`、下記4.）の結果を印字する。人間チェックはこの一覧から見ると早い。

途中で切れる実例: モデルがJSON文字列の内側で`<|endoftext|>`（151643）を出力し、構造化出力のgrammarがその位置では受理できずvLLMがリクエストを打ち切った（`Unexpected: grammar rejected tokens ... Terminating request`）。vLLM側のlogitsビットマスクで選べないはずのトークンなのでvLLM自身も`Unexpected`と記録しており、プロンプト側では防げない。このとき完成していた10ペアは回収できる。

プロンプト本文は`THIRD_PARTY.md`が正で、`ja_prompts.py`はその写し。両者がずれていないことは`tests/test_ja_prompts.py`の`DocumentIsTheSourceOfTruth`が検査する。

## 3. 表現辞書の形式（`ja_dictionary.py`）

```json
{
  "filter:ge_k": {"slot_type": "ADNOMINAL", "expressions": ["k以上の", "kを下回らない"]},
  "map:add_k": {"slot_type": "ACTION_PAIR",
                "expressions": [{"terminal": "kを加える", "te": "kを加えて"}]},
  "frame:opening": {"slot_type": "TEXT", "expressions": ["整数のリストxsについて、"]}
}
```

`ExpressionDictionary.load(path)`は**構造だけ**を検証する（スロット型どおりの形か、空でないか、`frame:filter_verb`が`{frag}`をちょうど1個持つか）。日本語として自然か・意味が変わっていないかは人間チェックの領分なので、変な表現もそのまま保存・往復する。構造は正しいが結合できない表現（名詞で終わる連体修飾フラグメントなど）は、下記4.の`contract_problems`が別途一覧する。

## 4. 意味ASTへの対応づけ（`ja_generator.py`）

```python
from ja_dictionary import ExpressionDictionary
from ja_generator import render_variants, instruction_record, save_instructions
from schema import SemanticAST

d = ExpressionDictionary.load("semantic_ast/expressions_ja/candidates.json")
ast = SemanticAST(filters=("ge_k", "even"), map_ops=(("add_k", None), ("mul_const", 2)), order_op="ascending")
renderings = render_variants(ast, d, n=3, seed=0)
# 辞書が ja_generator_plan.md 2.6 の例どおりの表現を持つ場合の出力:
# 「整数のリストxsについて、k以上の偶数の要素だけを残し、kを加えてから2倍して、昇順に並べるsolve関数を書いてください。」
# 実際の文面は辞書の中身しだいなので、変な表現は人間チェックで辞書側を直す（生成器やプロンプトはいじらない）。
save_instructions([instruction_record(ast, renderings, d, spec_id="train-000000")], "out/instructions_train.jsonl")
```

結合規則は`ja_generator_plan.md`2章そのまま（filter→map→order→sliceの順、最後のアクティブカテゴリだけ終止形、チェインは`te形+から`、`{frag}`と`N`の置換）。`ja_generator_plan.md`5章の未確定事項だった読点の扱いは、**生成器側で一律に「、」を付与する**（表現辞書側の末尾「、」は重複しないよう1つだけ剥がす）方に決めた。最後の節と結びの間だけは「、」を入れない——ここは連体修飾（「昇順に並べる」+「solve関数を…」）なので、読点を挟むと修飾先の名詞から切り離されてしまう。

複数filterの連体修飾フラグメントの**並び順は生成器が決める**（`ADNOMINAL_GROUP_ORDER` = k比較→符号→倍数→偶奇）。ANDは可換なので意味ASTの順序には意味がない一方、日本語の連体修飾を重ねる順序には意味があり（「k以上の偶数の要素」は自然、「偶数のk以上の要素」は不自然）、`generator.py`の列挙順は後者になってしまうため。

**結合契約（`contract_problems`）**: 教師モデルは原子表現しか書かないので、「節と節が繋がらない」種類の問題は結合側の責任になる。そこで結合規則が前提にしていることを`contract_problems(dictionary)`が明文化し、機械的に判定できる分だけ検査する——連体修飾フラグメントが名詞や「だけ」で終わっていないか（終わっていると`…要素要素だけを残す`になる）、`terminal`が名詞で終わっていないか（結びの名詞句が直後に来る）、map/sliceの`te`が「から」を付けられる形か、`frame:opening`が後続カテゴリに依存しない中立形か、`frame:closing`が`solve`を含み「。」で終わるか。検査するのは**壊れる**ものだけで、「言い回しが下手」「`solve`を実行しろと言っている」のような判断は入れない（そこは`THIRD_PARTY.md`のプロンプトと人間チェックの担当）。違反は修正せず一覧するだけ。

保存レコードには文そのもの（`instruction_ja`）に加えて、**どの辞書エントリのどのインデックスを使ったか**（`renderings[].choices`）と辞書のハッシュ（`dictionary_sha256`）を残す。`render_from_record()`はこの記録だけから同じ文を再構成するので、保存された日本語が辞書から再現可能であることを後からいつでも検査できる。

## 5. 一気通貫（`ja_demo.py`）

```bash
python semantic_ast/expressions_ja/ja_demo.py --variants 3
```

表現辞書を読む→`semantic_ast/out/{train,val,test}.jsonl`の意味ASTに対して結合→`semantic_ast/out/instructions_{split}.jsonl`に保存→読み戻して1件ずつ再生成し、保存された文と一致するかを検証する（`demo.py`未実行なら代わりに構成パターン網羅のサンプルを列挙して使う）。

## このディレクトリが担っていないこと

- 生成された表現の人間によるチェック・承認（`candidates.json`を確認して`approved.json`にするフロー。`ja_demo.py --dictionary`で承認済み辞書に差し替えられる）
- 意味ASTに基づくコードの構造的変換（`../expressions_code/`の担当）
