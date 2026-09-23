# THIRD_PARTY

`task_list.md` の「意味ASTに基づいてQwen3系モデルで日本語表現を生成」、および `homework.md` の「教師モデル」節にある

> 教師生成時には以下を固定・記録する。
> モデル名 / モデルのrevisionまたはコミットID / 量子化方式 / 推論ライブラリのバージョン / system prompt / sampling設定 / seed / 生成日時 / プロンプトのハッシュ値

を受けて、教師モデル（日本語表現の生成に使用する大規模言語モデル）に関する第三者ライセンス・実行条件を記録するファイル。

プロンプト本文・system prompt は「## プリミティブへの問い合わせプロンプト」に記載する。プロンプトのハッシュ値は実行時に確定するため、生成ログ側に記録する（本ファイルでは各プロンプトの構成規則までを扱う）。

## ライセンス

### Qwen/Qwen3-4B-AWQ

- 配布元: [Qwen/Qwen3-4B-AWQ (Hugging Face)](https://huggingface.co/Qwen/Qwen3-4B-AWQ)
- ライセンス: Apache License 2.0
- ライセンス原文: [LICENSE](https://huggingface.co/Qwen/Qwen3-4B-AWQ/blob/main/LICENSE)

## モデル・実行環境の記録

`homework.md` が要求する固定・記録項目のうち、プロンプト関連（system prompt・プロンプトのハッシュ値）を除いたもの。実際に生成を実行するスクリプト側で、実行時点の値を以下の表に追記・更新すること。

| 項目                       | 値                                                                 |
| -------------------------- | ------------------------------------------------------------------ |
| モデル名                   | `Qwen/Qwen3-4B-AWQ`                                                 |
| モデルのrevision/コミットID | TBD（実行時にHugging Face上のrevisionハッシュを記録する）           |
| 量子化方式                 | AWQ（4-bit）                                                        |
| 推論ライブラリ             | [vLLM](https://github.com/vllm-project/vllm)                       |
| 推論ライブラリのバージョン | `0.29.0`（`pyproject.toml` / `uv.lock` に固定、本リポジトリの依存） |
| sampling設定               | TBD（実行時に記録: temperature / top_p / top_k など）              |
| seed                       | TBD（実行時に固定・記録）                                          |
| 生成日時                   | TBD（実行のたびに記録）                                             |
| thinkingモード             | 非thinkingモードを使用し、最終的な指示文・解説文のみを保存する（`homework.md` 203行目） |

### vLLM のライセンス

- 配布元: [vllm-project/vllm](https://github.com/vllm-project/vllm)
- ライセンス: Apache License 2.0

## プリミティブへの問い合わせプロンプト

`ja_generator_plan.md`「4. Qwen3への問い合わせ設計」で定めた27プリミティブ（表現辞書キー）それぞれについて、vLLM経由でQwen3-4B-AWQに投げるプロンプトを定義する。1プリミティブ＝1リクエストとし、「共通system prompt」＋「スロット型ごとのuser promptテンプレート」＋「プリミティブごとの代入値（下表）」を機械的に結合してプロンプト本文を確定させる。この結合はテンプレート＋パラメータの決定的な処理なので、`homework.md`が要求する「プロンプトのハッシュ値」はテンプレートIDと代入値からいつでも再現できる。

### 呼び出し方法（vLLM 0.29.0）

- 非thinkingモード: `LLM.chat(...)`の`chat_template_kwargs={"enable_thinking": False}`で指定する（プロンプト文字列側に`/no_think`等を書き込む方式は使わない）。
- 出力形式の強制: vLLMの構造化出力機能（`vllm.sampling_params.StructuredOutputsParams`）で下記JSONスキーマを`SamplingParams(structured_outputs=...)`に渡し、モデルにJSON以外の文字列を出力させない。

```python
from vllm import LLM, SamplingParams
from vllm.sampling_params import StructuredOutputsParams

llm = LLM(model="Qwen/Qwen3-4B-AWQ", quantization="awq")

sampling_params = SamplingParams(
    temperature=0.8,   # TBD: 実行時に確定・記録する
    top_p=0.95,        # TBD
    seed=0,             # TBD: 実行時に固定・記録する
    structured_outputs=StructuredOutputsParams(json=SCHEMA),  # SCHEMAはスロット型ごとの下記JSONスキーマ
)

outputs = llm.chat(
    [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},  # テンプレート×代入値表から生成
    ],
    sampling_params=sampling_params,
    chat_template_kwargs={"enable_thinking": False},
)
```

### 共通system prompt

全27プロンプトで共通のsystem promptを1つ固定して使う。

```text
あなたは、Pythonの整数リスト処理関数 solve(xs, k) について説明する日本語の問題文を作成するための、表現バリエーション生成アシスタントです。

- 与えられた1つの操作について、日本語の言い換え表現をできるだけ多様に、かつ指定された件数の範囲で列挙してください。
- 表現は日本語として自然で、指定された文法的な形（連体形・終止形・連用中止形など）を厳密に守ってください。
- 操作の意味を変えてはいけません。特に、境界値の扱いを変える言い換え（例:「以上」と「より大きい」の混同、「より小さい」と「以下」の混同）は禁止します。
- 変数名（k, xs, N, solve など）がプロンプト中で指定されている場合は、必ずアルファベットの文字列のまま出力に含めてください。日本語の数詞や別の記号に置き換えないでください。
- 出力は指定されたJSONスキーマに厳密に従ってください。JSON以外の文章（説明、前置き、コードブロックの記法など）は一切出力しないでください。
- 思考の過程は出力せず、最終的なJSONのみを返してください。
```

### user promptテンプレート

スロット型ごとに4種類のテンプレートを用意する。`{...}`が下表「代入値」からの埋め込み箇所。

#### (a) `ADNOMINAL`用（filterの10プリミティブに使用）

```text
Python関数 solve(xs, k) の中で、リストの要素に対する次の条件を表す日本語表現を、{count}種類、重複なく列挙してください。

条件: {description}

制約:
- 出力は名詞（「要素」「値」など）に直接かかる連体修飾の形（「〜の」「〜い」のように名詞の直前に置ける形）のみとする。文末に置く終止形や、連用中止形は出力しないこと。
- {var_note}
- 意味を変えないこと（特に境界値の扱いに注意）。

出力はJSONスキーマに従うこと。
```

#### (b) `ACTION_PAIR`用（map/order/sliceの13プリミティブに使用）

```text
Python関数 solve(xs, k) の中で、リストの要素に対する次の操作を表す日本語表現を、{count}ペア、重複なく列挙してください。

操作: {description}

各表現について、次の2つの形を対応づけて生成すること。
- terminal: 文末に置く終止形（例: 「kを加える」）
- te: 直後に別の操作の説明が続く場合に使う、連用中止形（例: 「kを加えて」）

制約:
- 同じ表現のterminalとteは、必ず同じ意味・同じ操作を指す対でなければならない（片方だけ違う言い方に変えない）。
- {var_note}
- 意味を変えないこと。

出力はJSONスキーマに従うこと。
```

#### (c) `ACTION_PAIR`（`{frag}`埋め込み）用（`frame:filter_verb`専用）

```text
Python関数 solve(xs, k) の問題文で、抽出条件（連体修飾の形で表現済みの、例:「k以上の偶数の」のような文字列）を受けて、それを使って「〜要素だけを残す」という意味の一文にまとめる言い方を、{count}種類、重複なく列挙してください。

条件を差し込む位置をプレースホルダ {{frag}} として、各表現に必ず1回含めてください（例:「{{frag}}要素だけを残す」）。

各表現について、terminal（文末に置く終止形、例:「{{frag}}要素だけを残す」）と te（直後に別の操作が続く場合の連用中止形、例:「{{frag}}要素だけを残し」）の両方を対応づけて生成すること。

制約:
- プレースホルダ {{frag}} の文字列自体は改変・省略しないこと。
- {{frag}} の直後は名詞的にもとの条件を受ける形にする（{{frag}}には「k以上の偶数の」のような連体形の文字列が入る前提）。
- 「残す／抽出する／選ぶ」のように、要素を絞り込むという意味を保つこと。

出力はJSONスキーマに従うこと。
```

#### (d) `TEXT`用（`frame:opening` / `frame:closing`専用）

```text
Python関数 solve(xs, k) を実装させるための、日本語の問題文における「{role}」部分の言い方を、{count}種類、重複なく列挙してください。

{role_description}

制約:
- {var_note}
- {boundary_note}

出力はJSONスキーマに従うこと。
```

### 出力JSONスキーマ

`ADNOMINAL`と`TEXT`は同じ形（文字列の配列）、`ACTION_PAIR`は`{terminal, te}`ペアの配列。件数の上下限は下表「生成件数目安」で差し替える。

```python
def string_list_schema(min_items: int, max_items: int) -> dict:
    return {
        "type": "object",
        "properties": {
            "expressions": {
                "type": "array",
                "items": {"type": "string"},
                "minItems": min_items,
                "maxItems": max_items,
            }
        },
        "required": ["expressions"],
        "additionalProperties": False,
    }

def action_pair_schema(min_items: int, max_items: int) -> dict:
    return {
        "type": "object",
        "properties": {
            "expressions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "terminal": {"type": "string"},
                        "te": {"type": "string"},
                    },
                    "required": ["terminal", "te"],
                    "additionalProperties": False,
                },
                "minItems": min_items,
                "maxItems": max_items,
            }
        },
        "required": ["expressions"],
        "additionalProperties": False,
    }
```

`ADNOMINAL`・`frame:opening`・`frame:closing` → `string_list_schema(...)`、`ACTION_PAIR`（`frame:filter_verb`含む）→ `action_pair_schema(...)`を使う。

### 27プリミティブの代入値

| 表現辞書キー | スロット型 | テンプレート | 生成件数目安 | `{description}` に入れる操作の説明 | `{var_note}` |
| --- | --- | --- | --- | --- | --- |
| `filter:even` | ADNOMINAL | (a) | 10〜30 | 値が2で割り切れる（2で割った余りが0になる）こと | 変数の埋め込みなし |
| `filter:odd` | ADNOMINAL | (a) | 10〜30 | 値を2で割った余りが0でないこと | 変数の埋め込みなし |
| `filter:gt_k` | ADNOMINAL | (a) | 10〜30 | 値が変数kより真に大きいこと（k自身は含まない） | 変数kを使う場合は、必ずアルファベットの「k」という文字列のまま埋め込むこと |
| `filter:ge_k` | ADNOMINAL | (a) | 10〜30 | 値が変数k以上であること（k自身を含む） | 同上 |
| `filter:lt_k` | ADNOMINAL | (a) | 10〜30 | 値が変数kより真に小さいこと（k自身は含まない） | 同上 |
| `filter:le_k` | ADNOMINAL | (a) | 10〜30 | 値が変数k以下であること（k自身を含む） | 同上 |
| `filter:multiple_of_k` | ADNOMINAL | (a) | 10〜30 | 値が変数kで割り切れる（kの倍数である）こと | 同上 |
| `filter:positive` | ADNOMINAL | (a) | 10〜30 | 値が0より真に大きいこと（正の数。0自体は含まない） | 変数の埋め込みなし |
| `filter:negative` | ADNOMINAL | (a) | 10〜30 | 値が0より真に小さいこと（負の数。0自体は含まない） | 変数の埋め込みなし |
| `filter:zero` | ADNOMINAL | (a) | 10〜30 | 値がちょうど0であること | 変数の埋め込みなし |
| `map:add_k` | ACTION_PAIR | (b) | 10〜30 | 各要素に変数kを足す（加算する） | 変数kを使う場合は、必ずアルファベットの「k」という文字列のまま埋め込むこと |
| `map:sub_k` | ACTION_PAIR | (b) | 10〜30 | 各要素から変数kを引く（減算する。「k引く要素」ではなく「要素引くk」の向き） | 同上 |
| `map:mul_k` | ACTION_PAIR | (b) | 10〜30 | 各要素に変数kを掛ける（乗算する） | 同上 |
| `map:negate` | ACTION_PAIR | (b) | 10〜30 | 各要素の符号を反転する（正負を入れ替える。絶対値は変えない） | 変数の埋め込みなし |
| `map:abs` | ACTION_PAIR | (b) | 10〜30 | 各要素を絶対値に変換する（符号を外す） | 変数の埋め込みなし |
| `map:square` | ACTION_PAIR | (b) | 10〜30 | 各要素を2乗する | 変数の埋め込みなし |
| `map:mul_const` | ACTION_PAIR | (b) | 10〜30 | 各要素を定数N倍する（Nは2または3のいずれかで、変数kとは無関係の固定の整数） | 定数を使う場合は、必ずアルファベット大文字の「N」という文字列のまま埋め込むこと（「2倍する」のように具体的な数値2・3を書かないこと） |
| `order:ascending` | ACTION_PAIR | (b) | 10〜30 | リスト全体を、小さい順（昇順）に並べ替える | 変数の埋め込みなし |
| `order:descending` | ACTION_PAIR | (b) | 10〜30 | リスト全体を、大きい順（降順）に並べ替える | 変数の埋め込みなし |
| `order:reverse` | ACTION_PAIR | (b) | 10〜30 | 現在の並び順の大小関係に関わらず、要素の並びをそのまま逆転させる（ソートではない） | 変数の埋め込みなし |
| `slice:take_first_k` | ACTION_PAIR | (b) | 10〜30 | リストの先頭から変数k個の要素を取り出す | 変数kを使う場合は、必ずアルファベットの「k」という文字列のまま埋め込むこと |
| `slice:take_last_k` | ACTION_PAIR | (b) | 10〜30 | リストの末尾から変数k個の要素を取り出す | 同上 |
| `slice:step_2` | ACTION_PAIR | (b) | 10〜30 | リストの先頭（0番目）の要素から1個おきに要素を取り出す（0, 2, 4, ...番目の要素を残す） | 変数の埋め込みなし |
| `frame:filter_verb` | ACTION_PAIR（`{frag}`あり） | (c) | 5〜10 | （テンプレート(c)に説明済み。抽出条件フラグメントを受けて「〜要素だけを残す」という意味にまとめる枠） | プレースホルダ`{frag}`をそのまま保持すること |
| `frame:opening` | TEXT | (d) | 10〜30 | `{role}`=「書き出し」。`{role_description}`=「整数のリストxsを読み手に導入する一文（の前半）。直後に抽出条件などの節（例:「偶数の要素だけを残し、」）が続くことを前提に、読点「、」で終える自然な接続にすること。」 | 変数xsを使う場合は、必ずアルファベットの「xs」という文字列のまま埋め込むこと |
| `frame:closing` | TEXT | (d) | 10〜30 | `{role}`=「結び」。`{role_description}`=「直前に置かれる動詞の連体形（例:「昇順に並べる」）を受けて、solve関数の実装を依頼する一文の後半としてまとめる言い方。句点「。」で終えること。」 | 関数名solveを使う場合は、必ずアルファベットの「solve」という文字列のまま埋め込むこと |

`{boundary_note}`（テンプレート(d)のみ）: `frame:opening`では「文中に条件・操作を表す語を含めないこと（書き出しは入力の導入のみを行う）」、`frame:closing`では「直前の動詞の連体形に自然に接続する形にし、それ自体で条件や操作の内容を新たに追加しないこと」を指定する。

### 具体例（テンプレート(a)・(b)・(c)・(d)のレンダリング結果）

`filter:ge_k`（テンプレート(a)、`string_list_schema(10, 30)`使用）:

```text
Python関数 solve(xs, k) の中で、リストの要素に対する次の条件を表す日本語表現を、10〜30種類、重複なく列挙してください。

条件: 値が変数k以上であること（k自身を含む）

制約:
- 変数kを使う場合は、必ずアルファベットの「k」という文字列のまま埋め込むこと
- 出力は名詞（「要素」「値」など）に直接かかる連体修飾の形（「〜の」「〜い」のように名詞の直前に置ける形）のみとする。文末に置く終止形や、連用中止形は出力しないこと。
- 意味を変えないこと（特に境界値の扱いに注意）。

出力はJSONスキーマに従うこと。
```

`map:add_k`（テンプレート(b)、`action_pair_schema(10, 30)`使用）:

```text
Python関数 solve(xs, k) の中で、リストの要素に対する次の操作を表す日本語表現を、10〜30ペア、重複なく列挙してください。

操作: 各要素に変数kを足す（加算する）

各表現について、次の2つの形を対応づけて生成すること。
- terminal: 文末に置く終止形（例: 「kを加える」）
- te: 直後に別の操作の説明が続く場合に使う、連用中止形（例: 「kを加えて」）

制約:
- 同じ表現のterminalとteは、必ず同じ意味・同じ操作を指す対でなければならない（片方だけ違う言い方に変えない）。
- 変数kを使う場合は、必ずアルファベットの「k」という文字列のまま埋め込むこと
- 意味を変えないこと。

出力はJSONスキーマに従うこと。
```

`frame:opening`（テンプレート(d)、`string_list_schema(10, 30)`使用）:

```text
Python関数 solve(xs, k) を実装させるための、日本語の問題文における「書き出し」部分の言い方を、10〜30種類、重複なく列挙してください。

整数のリストxsを読み手に導入する一文（の前半）。直後に抽出条件などの節（例:「偶数の要素だけを残し、」）が続くことを前提に、読点「、」で終える自然な接続にすること。

制約:
- 変数xsを使う場合は、必ずアルファベットの「xs」という文字列のまま埋め込むこと
- 文中に条件・操作を表す語を含めないこと（書き出しは入力の導入のみを行う）

出力はJSONスキーマに従うこと。
```
