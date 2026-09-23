"""Prompt construction for the teacher model (THIRD_PARTY.md "プリミティブ
への問い合わせプロンプト").

THIRD_PARTY.md fixes, in prose, the exact strings this module has to build:
one common system prompt, five user-prompt templates (one per slot type,
plus (e) for ``filter:zero``, whose equality condition template (a) could
only paraphrase by padding -- see ``TEMPLATE_EQUALITY``), and the
substitution table (one row per expression-dictionary key).
Everything here is a literal transcription of that document -- the document
is the normative source, this module is only the machine-readable copy of
it, so *any* wording change belongs in THIRD_PARTY.md first.

Note on the count: THIRD_PARTY.md (and ja_generator_plan.md section 4) says
"27プロンプト", arriving there via "map 7 + mul_const 1", but ``mul_const``
is already one of ``schema.ALL_MAP_OP_NAMES``' 7 entries, and the document's
own table has 26 rows (filter 10 + map 7 + order 3 + slice 3 + frame 3).
This module transcribes the table, so ``PRIMITIVES`` holds those 26 keys --
one per dictionary key that ja_generator.py can actually ask for. The
discrepancy is left for the document to resolve; nothing here depends on
the count.

The wording of the system prompt and of templates (a)-(e) is checked
against THIRD_PARTY.md by ``tests/test_ja_prompts.py``, so the two cannot
drift apart silently.

Because a prompt is fully determined by (template id, substitution values),
its hash is reproducible at any time; ``prompt_record()`` emits that hash
together with the values it came from, which is the "プロンプトのハッシュ
値" that homework.md requires in the generation log.

Usage:

    from ja_prompts import PRIMITIVES, build_messages, json_schema

    spec = PRIMITIVES["filter:ge_k"]
    messages = build_messages(spec)      # [{"role": "system", ...}, {"role": "user", ...}]
    schema = json_schema(spec)           # for StructuredOutputsParams(json=...)
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Slot types (ja_generator_plan.md 1.1). ``TEXT`` is the frame-only slot type
# for frame:opening / frame:closing, which are stored as plain strings like
# ADNOMINAL but are whole clauses rather than 連体修飾フラグメント.
# ---------------------------------------------------------------------------

ADNOMINAL = "ADNOMINAL"
ACTION_PAIR = "ACTION_PAIR"
TEXT = "TEXT"
SLOT_TYPES: tuple[str, ...] = (ADNOMINAL, ACTION_PAIR, TEXT)

# ---------------------------------------------------------------------------
# 共通system prompt (THIRD_PARTY.md "### 共通system prompt")
# ---------------------------------------------------------------------------

SYSTEM_PROMPT = """あなたは、Pythonの整数リスト処理関数 solve(xs, k) について説明文を作成するための、日本語文生成アシスタントです。

- 与えられた1つの操作について、日本語の言い換え表現をできるだけ多様に、かつ指定された件数の範囲で列挙してください。
- 表現は日本語として自然で、指定された文法的な形（連体形・終止形・連用中止形など）を厳密に守ってください。
- 操作の意味を変えてはいけません。特に、境界値の扱いを変える言い換え（例:「以上」と「より大きい」の混同、「より小さい」と「以下」の混同）は禁止します。
- 操作を特定するために必要な語（例:「先頭から」「末尾から」「昇順に」「降順に」「1個おきに」）を省略してはいけません。省略すると別の操作と区別がつかなくなります。
- 同じ表現を2回出力してはいけません。また、件数を満たすためだけに「操作」「処理」「動作」「こと」などを付け足した水増し表現も出力しないでください。自然な言い換えが尽きたら、指定された最小件数で止めて構いません。
- 変数名（k, xs, N, solve など）がプロンプト中で指定されている場合は、必ずアルファベットの文字列のまま出力に含めてください。日本語の数詞や別の記号に置き換えないでください。
- 出力は指定されたJSONスキーマに厳密に従ってください。JSON以外の文章（説明、前置き、コードブロックの記法など）は一切出力しないでください。
- 思考の過程は出力せず、最終的なJSONのみを返してください。"""

# ---------------------------------------------------------------------------
# user promptテンプレート (a)-(d) (THIRD_PARTY.md "### user promptテンプレート")
#
# ``{...}`` marks a substitution site filled from the table below. Template
# (c) additionally contains ``{{frag}}``, which is *not* a substitution site
# -- it renders to the literal placeholder ``{frag}`` that the generated
# expression must carry through to ja_generator.py.
# ---------------------------------------------------------------------------

TEMPLATE_ADNOMINAL = """Python関数 solve(xs, k) の中で、リスト xs の要素に対する次の条件を表す日本語表現を、{count}種類、重複なく列挙してください。

条件: {description}

出力する表現は、直後に「要素」という名詞が続く連体修飾のフラグメントです。生成器側が「（別の条件の連体修飾）＋（この表現）＋要素だけを残す」のように前後を補って一文にするので、この表現自体には名詞も、絞り込みを表す述語も含めないでください。

制約:
- 末尾は、直後に名詞を置ける形（「〜の」「〜い」「〜な」「〜ない」や動詞の連体形）にすること。良い例:「偶数の」「2で割り切れる」「k以上の」。
- 末尾を名詞で終えないこと。特に「要素」「もの」「値」「数」「こと」「とき」で終わる表現は出力しないこと。悪い例:「偶数の値」「k以上の要素」「2で割り切れる数」。
- 名詞で終わる言い方しか思いつかない場合は、その名詞を削るか、末尾に「の」を付けて連体形にすること（「kの倍数」→「kの倍数の」、「2で割り切れる値」→「2で割り切れる」）。
- 「だけ」「のみ」「を残す」「を抽出する」「を選ぶ」のような、絞り込みそのものを表す語を含めないこと（それは生成器側が付ける）。悪い例:「k以上の要素だけ」「0に等しいものだけを残す」。
- 断定の「〜である」で終えないこと。別の条件と重ねたときに読みづらくなるので、「〜の」で終える形に直すこと（「k以上である」→「k以上の」、「奇数である」→「奇数の」）。
- 別の条件の連体修飾が前に付くことがあるため、2つ重ねて「（別の条件）（この表現）要素」と読んでも自然な形にすること（「k以上の」＋「偶数の」→「k以上の偶数の要素」は可）。
- 「値が」「要素が」のような主語や、「〜こと」のような名詞化を含めないこと。悪い例:「値が偶数である」「偶数であること」。
- 文末に置く終止形や、連用中止形は出力しないこと。
- {var_note}
- 意味を変えないこと（特に境界値の扱いに注意）。

出力はJSONスキーマに従うこと。"""

TEMPLATE_ACTION_PAIR = """Python関数 solve(xs, k) の中で、リストの要素に対する次の操作を表す日本語表現を、{count}ペア、重複なく列挙してください。

操作: {description}

各表現について、次の2つの形を対応づけて生成すること。
- terminal: 文末に置く終止形（例: 「kを加える」）
- te: 直後に別の操作の説明が続く場合に使う、連用中止形（例: 「kを加えて」）

生成器側は、terminalを「…kを加えるsolve関数を実装してください。」のように直後の名詞に係る形で使い、teの後ろには「から」や読点を生成器が補って「kを加えてから2倍する」「kを加えて、昇順に並べる」のように次の節へ繋ぎます。

制約:
- terminalは動詞で言い切る形にすること。直後に「solve関数」のような名詞が続くので、「操作」「処理」「動作」「方法」「こと」などの名詞で終える表現は、件数が足りなくなっても出力しないこと。悪い例:「kを加える操作」（「kを加える操作solve関数」となり後ろに繋がらない）。
- teは「〜て」で終わる連用中止形にすること。接続詞「から」は生成器が後ろに付けるので、te自体に「から」を含めてはいけない。「〜から」「〜で」「〜ます」「〜です」で終える形は出力しないこと。悪い例:「kを加えてから」（生成器が付けるので「〜からから」になる）「kを加える処理で」「kを加えます」。
- 同じ表現のterminalとteは、必ず同じ意味・同じ操作を指す対でなければならない（片方だけ違う言い方に変えない）。
- teはterminalと必ず異なる連用中止形にすること（「〜する」→「〜して」、「〜させる」→「〜させて」、「〜く」→「〜いて」）。terminalと同じ文字列をteに入れないこと。
- 操作を特定する語（「先頭から」「末尾から」「昇順に」「降順に」「1個おきに」など）を省略しないこと。省略すると別の操作と区別がつかなくなる。
- {var_note}
- 意味を変えないこと。

出力はJSONスキーマに従うこと。"""

TEMPLATE_FILTER_VERB = """Python関数 solve(xs, k) の問題文で、抽出条件（連体修飾の形で表現済みの、例:「k以上の偶数の」のような文字列）を受けて、それを使って「〜要素だけを残す」という意味の一文にまとめる言い方を、{count}種類、重複なく列挙してください。

条件を差し込む位置をプレースホルダ {{frag}} として、各表現に必ず1回含めてください（例:「{{frag}}要素だけを残す」）。

各表現について、terminal（文末に置く終止形、例:「{{frag}}要素だけを残す」）と te（直後に別の操作が続く場合の連用中止形、例:「{{frag}}要素だけを残し」）の両方を対応づけて生成すること。

制約:
- プレースホルダ {{frag}} の文字列自体は改変・省略しないこと。
- 表現は必ず {{frag}} という文字列で始めること。{{frag}} より前には1文字も書かないこと。条件そのものは生成器が {{frag}} の位置に差し込むので、「k以上の」「偶数の」のような具体的な条件を表現に含めてはいけない。悪い例:「k以上の{{frag}}要素だけを残す」（条件が二重になる）。
- {{frag}} の直後には「要素」「もの」「値」のような名詞を置き、もとの条件を名詞的に受ける形にする（{{frag}}には「k以上の偶数の」のような連体形の文字列が入る前提）。
- 「残す／抽出する／選ぶ」のように、要素を絞り込むという意味を保つこと。
- terminalは、直後に「solve関数」のような名詞が続く（「…要素だけを残すsolve関数を実装してください。」）ため、動詞で言い切る形にすること。名詞で終える表現は出力しないこと。
- teは、直後に読点「、」と次の操作の説明が続く（「…要素だけを残し、kを加える」）ため、そこで文が切れない連用中止形にすること。
- teはterminalと必ず異なる連用中止形にすること（「〜する」→「〜し」、「〜む」→「〜み」）。terminalと同じ文字列をteに入れないこと。

出力はJSONスキーマに従うこと。"""

TEMPLATE_TEXT = """Python関数 solve(xs, k) を実装させるための、日本語の問題文における「{role}」部分の言い方を、{count}種類、重複なく列挙してください。

{role_description}

制約:
- {ending_note}
- {var_note}
- {boundary_note}

出力はJSONスキーマに従うこと。"""

# filter:zero only. Template (a) is written for predicates that describe a
# *range* (「k以上の」「偶数の」), and every one of its escape hatches is closed
# for an equality with one number: 「0に等しい」「0と一致する」 are already
# 連体形 with nowhere to put (a)'s 「の」, and the one remaining natural form,
# 「0である」, is what (a) forbids. The model was left with padding -- all 11
# responses came back as 「0に等しいの」 / 「0に等しいこと」 and the human
# approval step dropped the key to zero entries (filtered.json). This template
# lists the endings that are allowed instead of describing them, names the
# stray 「の」 as the bad example, and asks for 3〜8 rather than 5〜15, because
# there are only a handful of genuine paraphrases of 「ちょうど0」 and a higher
# floor is itself an instruction to pad.
#
# A second run with this template fixed the endings themselves
# (「0に等しい」「0である」「0と一致する」) but appended the frame's own noun to
# every one of the 6: 「0に等しい要素」. The template was writing 「要素」 right
# after a finished fragment -- 「その末尾のまま直後に「要素」を置ける」 and, worse,
# 「「k以上の」＋「0に等しい」→「k以上の0に等しい要素」は可」, a complete wrong
# answer presented as a good example. That is exactly how frame:filter_verb's
# condition-copying started, so the template no longer writes any 「…要素」
# string at all. (frame:filter_verb's other remedy, a structured-output
# pattern, does not work for this key -- see FRAG_PREFIX_PATTERN's note.)
TEMPLATE_EQUALITY = """Python関数 solve(xs, k) の中で、リスト xs の要素に対する次の条件を表す日本語表現を、{count}種類、重複なく列挙してください。

条件: {description}

これは大小の比較ではなく、ちょうど1つの値と一致するかどうかを問う等値条件です。「0以上」「0より大きい」「0以下」「0より小さい」のような大小の条件や、「0でない」のような否定は、意味が変わるので出力しないでください。

出力する表現は、条件そのものだけを述べた連体修飾のフラグメントです。修飾される名詞と、絞り込みを表す述語は、生成器側が後ろに補います。表現自体には名詞も述語も含めないでください。

出力してよい末尾は次の4つだけです。下の例はそれぞれ完成した1件の表現であり、この形のまま出力できます。
- 「〜の」で終える形。例:「ちょうど0の」
- 形容詞の連体形。例:「0に等しい」「0と等しい」
- 動詞の連体形。例:「0と一致する」
- 断定の連体形「〜である」。例:「0である」

制約:
- 「0」または「ゼロ」を必ず表現に含めること。
- 上の4つの例の後ろに、何も書き足さないこと。特に「の」を足さないこと。悪い例:「0に等しいの」「0と一致するの」「0であるの」。
- 修飾される名詞は生成器側が補うので、表現に含めないこと。「要素」「もの」「値」「数」「こと」「とき」で終わる表現は出力しないこと。悪い例:「0に等しい要素」「0と等しい値」「0であること」。
- 「だけ」「のみ」「を残す」「を抽出する」「を選ぶ」のような、絞り込みそのものを表す語を含めないこと（それは生成器側が付ける）。悪い例:「0に等しいものだけ」。
- 「値が」「要素が」のような主語を含めないこと。悪い例:「値が0である」。
- 「0です」のような丁寧形や、「0であり」「0に等しく」のような連用中止形は出力しないこと。
- 別の条件の連体修飾が前に付くことがあるため、前に別の条件を置いて読んでも自然な形にすること（「k以上の」＋「0に等しい」の順に並ぶ）。
- この条件の自然な言い換えは多くない。件数を満たすために語を付け足した表現を作らず、自然な言い換えが尽きたら指定された件数の下限で止めること。

出力はJSONスキーマに従うこと。"""

TEMPLATES: dict[str, str] = {
    "a": TEMPLATE_ADNOMINAL,
    "b": TEMPLATE_ACTION_PAIR,
    "c": TEMPLATE_FILTER_VERB,
    "d": TEMPLATE_TEXT,
    "e": TEMPLATE_EQUALITY,
}

# The placeholder that frame:filter_verb expressions must carry (rendered
# from ``{{frag}}`` in template (c)); ja_generator.py substitutes the
# concatenated ADNOMINAL fragment for it.
FRAG_PLACEHOLDER = "{frag}"

# ---------------------------------------------------------------------------
# 出力JSONスキーマ (THIRD_PARTY.md "### 出力JSONスキーマ")
# ---------------------------------------------------------------------------


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


def action_pair_schema(min_items: int, max_items: int, pattern: Optional[str] = None) -> dict:
    form = {"type": "string"} if pattern is None else {"type": "string", "pattern": pattern}
    return {
        "type": "object",
        "properties": {
            "expressions": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "terminal": dict(form),
                        "te": dict(form),
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


# frame:filter_verb only. The frame contributes the verb and ja_generator.py
# substitutes the condition for the placeholder, so anything the model writes
# in front of {frag} becomes a second condition in front of the real one
# (「k以上の{frag}要素だけを残す」 -> 「k以上のk以上の偶数の要素だけを残す」).
# Asking for that in prose did not hold -- the model copies the condition out
# of the template's own example -- so the structured-output grammar enforces
# it instead: start with the placeholder, then at least one more character,
# and no other braces anywhere.
FRAG_PREFIX_PATTERN = r"^\{frag\}[^{}]+$"

# A note on why filter:zero does *not* get the same treatment, even though its
# prose was ignored the same way frame:filter_verb's was. Two patterns were
# tried and neither held at generation time:
#
# * The first was written as "any character except 「い」「る」...". xgrammar's
#   negated character classes are ASCII-only: it clamped the class ("Negative
#   Character class contains byte greater than 127, clamping to 127",
#   grammar_functor.cc), dropped the exclusions, and warned rather than failed.
# * The second used positive alternatives only, and compiled without a
#   warning. Checked offline through ``xgr.Grammar.from_json_schema``, it
#   accepts the four intended endings and rejects every bad response we had
#   seen -- and yet the run it produced was byte-identical to the run with the
#   broken pattern: the same violating expressions, and the array closed with a
#   full-width 「｝」 followed by free prose, which is what an unconstrained
#   request looks like. The recognizer is right and the mask does not follow
#   it, so the constraint is not something this pipeline can rely on here.
#
# What holds the shape for filter:zero is therefore the prose of template (e),
# plus the two steps that already exist for every other key:
# ``ja_generator.contract_problems`` names the entries that cannot join, and
# the human approval step drops them (filtered.json).


# ---------------------------------------------------------------------------
# 27プリミティブの代入値 (THIRD_PARTY.md "### 27プリミティブの代入値")
# ---------------------------------------------------------------------------

# Repeated ``{var_note}`` values; the table in THIRD_PARTY.md writes these as
# 「同上」 after their first occurrence.
K_NOTE = "変数kを使う場合は、必ずアルファベットの「k」という文字列のまま埋め込むこと"
N_NOTE = "定数を使う場合は、必ずアルファベット大文字の「N」という文字列のまま埋め込むこと"
XS_NOTE = "変数xsを使う場合は、必ずアルファベットの「xs」という文字列のまま埋め込むこと"
SOLVE_NOTE = "関数名solveを使う場合は、必ずアルファベットの「solve」という文字列のまま埋め込むこと"
NO_VAR_NOTE = "変数の埋め込みなし"


@dataclass(frozen=True)
class PrimitiveSpec:
    """One row of THIRD_PARTY.md's per-primitive substitution table.

    ``key`` is the expression-dictionary key, which is also ``schema.py``'s
    op tag (``filter:even``, ``map:mul_const``, ...) for real primitives and
    a ``frame:*`` pseudo-key for the three frame entries.
    """

    key: str
    slot_type: str
    template_id: str
    min_items: int
    max_items: int
    description: str = ""
    var_note: str = ""
    role: str = ""
    role_description: str = ""
    ending_note: str = ""
    boundary_note: str = ""

    def count(self) -> str:
        """The ``{count}`` substitution, e.g. ``"10〜30"`` -- the 生成件数
        目安 column, reused verbatim as the JSON schema's item bounds."""
        return f"{self.min_items}〜{self.max_items}"

    def substitutions(self) -> dict[str, str]:
        """Every value substituted into the template, for the generation log
        (the prompt hash is reproducible from template id + these values)."""
        values = {"count": self.count()}
        for name in ("description", "var_note", "role", "role_description", "ending_note", "boundary_note"):
            value = getattr(self, name)
            if value:
                values[name] = value
        return values


# 生成件数目安. Kept well inside what the model can actually produce without
# repeating itself: a first run at 10〜30 padded the arrays with duplicates
# and degenerate growth ("...ものであるものである"), because the schema's
# minItems forces the model to keep emitting after it has run out of
# genuine paraphrases.
MIN_ITEMS = 5
MAX_ITEMS = 15

# filter:zero (template (e)). 「ちょうど0」 has only a handful of natural
# paraphrases, so the (a) floor of 5 was itself padding the array; see
# TEMPLATE_EQUALITY.
ZERO_MIN_ITEMS = 3
ZERO_MAX_ITEMS = 8


def _filter_spec(op: str, description: str, var_note: str) -> PrimitiveSpec:
    return PrimitiveSpec(
        key=f"filter:{op}",
        slot_type=ADNOMINAL,
        template_id="a",
        min_items=MIN_ITEMS,
        max_items=MAX_ITEMS,
        description=description,
        var_note=var_note,
    )


def _action_spec(key: str, description: str, var_note: str) -> PrimitiveSpec:
    return PrimitiveSpec(
        key=key,
        slot_type=ACTION_PAIR,
        template_id="b",
        min_items=MIN_ITEMS,
        max_items=MAX_ITEMS,
        description=description,
        var_note=var_note,
    )


_SPECS: tuple[PrimitiveSpec, ...] = (
    # --- filter: ADNOMINAL x10, template (a) -------------------------------
    _filter_spec("even", "2で割り切れる（2で割った余りが0になる）こと", NO_VAR_NOTE),
    _filter_spec("odd", "2で割った余りが0でないこと（奇数である）", NO_VAR_NOTE),
    _filter_spec("gt_k", "変数kより真に大きいこと（k自身は含まない）", K_NOTE),
    _filter_spec("ge_k", "変数k以上であること（k自身を含む）", K_NOTE),
    _filter_spec("lt_k", "変数kより真に小さいこと（k自身は含まない）", K_NOTE),
    _filter_spec("le_k", "変数k以下であること（k自身を含む）", K_NOTE),
    _filter_spec("multiple_of_k", "変数kで割り切れること（kの倍数である）", K_NOTE),
    _filter_spec("positive", "0より真に大きいこと（正である。0自体は含まない）", NO_VAR_NOTE),
    _filter_spec("negative", "0より真に小さいこと（負である。0自体は含まない）", NO_VAR_NOTE),
    # The one filter that does not use template (a): an equality, not a range.
    # ``var_note`` is left empty because (e) has no {var_note} site -- an
    # unused value would still be recorded in the generation log as if it had
    # been part of the prompt.
    PrimitiveSpec(
        key="filter:zero",
        slot_type=ADNOMINAL,
        template_id="e",
        min_items=ZERO_MIN_ITEMS,
        max_items=ZERO_MAX_ITEMS,
        description="ちょうど0であること（0に等しい）",
    ),
    # --- map: ACTION_PAIR x7, template (b) ---------------------------------
    _action_spec("map:add_k", "各要素に変数kを足す（加算する）", K_NOTE),
    _action_spec(
        "map:sub_k",
        "各要素から変数kを引く（減算する。「k引く要素」ではなく「要素引くk」の向き）",
        K_NOTE,
    ),
    _action_spec("map:mul_k", "各要素に変数kを掛ける（乗算する）", K_NOTE),
    _action_spec(
        "map:negate", "各要素の符号を反転する（正負を入れ替える。絶対値は変えない）", NO_VAR_NOTE
    ),
    _action_spec("map:abs", "各要素を絶対値に変換する（符号を外す）", NO_VAR_NOTE),
    _action_spec("map:square", "各要素を2乗する", NO_VAR_NOTE),
    _action_spec("map:mul_const", "各要素を定数N倍する", N_NOTE),
    # --- order: ACTION_PAIR x3, template (b) -------------------------------
    _action_spec("order:ascending", "リスト全体を、小さい順（昇順）に並べ替える（「昇順」「小さい順」にあたる語を必ず表現に含めること）", NO_VAR_NOTE),
    _action_spec("order:descending", "リスト全体を、大きい順（降順）に並べ替える（「降順」「大きい順」にあたる語を必ず表現に含めること）", NO_VAR_NOTE),
    _action_spec(
        "order:reverse",
        "現在の並び順の大小関係に関わらず、要素の並びをそのまま逆転させる（ソートではない。「逆」「反転」にあたる語を必ず表現に含めること）",
        NO_VAR_NOTE,
    ),
    # --- slice: ACTION_PAIR x3, template (b) -------------------------------
    _action_spec("slice:take_first_k", "リストの先頭から変数k個の要素を取り出す（「先頭」にあたる語と「k個」を必ず表現に含めること。これを落とすと末尾から取る操作と区別がつかない）", K_NOTE),
    _action_spec("slice:take_last_k", "リストの末尾から変数k個の要素を取り出す（「末尾」にあたる語と「k個」を必ず表現に含めること。これを落とすと先頭から取る操作と区別がつかない）", K_NOTE),
    _action_spec(
        "slice:step_2",
        "リストの先頭（0番目）の要素から1個おきに要素を取り出す（0, 2, 4, ...番目の要素を残す。「1個おき」にあたる語を必ず表現に含めること）",
        NO_VAR_NOTE,
    ),
    # --- frames ------------------------------------------------------------
    # Template (c) takes only {count}: the operation description and the
    # {frag} handling are written into the template itself.
    PrimitiveSpec(
        key="frame:filter_verb",
        slot_type=ACTION_PAIR,
        template_id="c",
        min_items=4,
        max_items=8,
    ),
    PrimitiveSpec(
        key="frame:opening",
        slot_type=TEXT,
        template_id="d",
        min_items=MIN_ITEMS,
        max_items=MAX_ITEMS,
        role="書き出し",
        role_description=(
            "整数のリストxsを読み手に導入する一文（の前半）。直後にどの操作の節が続くかは決まっておらず、"
            "抽出（「偶数の要素だけを残し、」）・変換（「kを加えて、」）・並べ替え（「昇順に並べて、」）・"
            "切り出し（「先頭からk個を取り出して、」）のどれが続いても成り立つ必要がある。"
            "読点「、」で終える自然な接続にすること。"
            "例:「整数のリストxsについて、」「xsという整数のリストに対して、」"
        ),
        ending_note=(
            "必ず読点「、」で終えること。句点「。」で終わる、それだけで完結した文にはしないこと"
        ),
        var_note=XS_NOTE,
        boundary_note=(
            "後続の節がどの操作であっても成り立つ、中立な書き出しに限ること。"
            "特定の操作を前提とする言い方は出力しないこと"
            "（例:「整数リストxsから、」は「〜から取り出す」という抽出を前提にしてしまうため、"
            "変換や並べ替えが続くと繋がらない）。"
            "条件・操作を表す語を文中に含めないこと（書き出しは入力の導入のみを行う）"
        ),
    ),
    PrimitiveSpec(
        key="frame:closing",
        slot_type=TEXT,
        template_id="d",
        min_items=MIN_ITEMS,
        max_items=MAX_ITEMS,
        role="結び",
        role_description=(
            "直前には、solveがどんな関数かを述べる動詞の連体形が置かれている。"
            "それを受けて、その連体形が係る名詞句を与え、一文を締めくくる後半部分。"
            "必ず「solve」を含む名詞句（例:「solve関数」「Python関数solve」）から始めること。"
            "solveの中身は直前の連体形がすでに述べ切っているので、"
            "この後半部分は処理の内容に一切触れない。"
            "solveはまだ存在せず、この一文を読んだ人が、これからそのコードを新しく用意する立場にある。"
            "全体の形の例:「Python関数solveを実装してください。」"
            "表現の違いは、名詞句の言い方と動詞の選び方だけで作ること。"
        ),
        ending_note=(
            "文末は「〜てください。」の形にし、句点「。」で終えること。"
            "先頭の名詞句の直後に助詞「を」を1つだけ置き、その後ろに動詞のて形と「ください」を続けること"
            "（助詞「を」を2回以上使わないこと）。"
            "読み手自身にその動作をさせる文にし、読み手以外の誰かにその動作をさせる形"
            "（「〜よう」「〜ように」を挟んで別の動詞に繋ぐ形や、"
            "伝達・要請・仲介を表す動詞を重ねる形）は出力しないこと。"
            "終止形で言い切る形は出力しないこと"
        ),
        var_note=SOLVE_NOTE,
        boundary_note=(
            "読点「、」を使わず、名詞句と動詞1つだけの短い形にすること。"
            "solveが扱うデータや、solveが行う処理を指す語は1つも含めないこと"
            "（それらは直前の連体形がすでに述べている）。"
            "動詞は、まだ存在しないコードを新しく生み出す意味のものに限ること。"
            "すでに存在するものを動かす・使う・当てはめる意味の動詞"
            "（「実行する」「呼び出す」「処理する」「動作させる」「実施する」など）は、"
            "件数が足りなくなっても出力しないこと"
        ),
    ),
)

PRIMITIVES: dict[str, PrimitiveSpec] = {spec.key: spec for spec in _SPECS}

# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def render_user_prompt(spec: PrimitiveSpec) -> str:
    """Fill ``spec``'s template with its substitution values.

    ``str.format`` is what turns template (c)'s ``{{frag}}`` into the literal
    ``{frag}`` the model is asked to echo, so every template goes through
    ``format`` even when it has a single substitution site.
    """
    return TEMPLATES[spec.template_id].format(**spec.substitutions())


def build_messages(spec: PrimitiveSpec) -> list[dict[str, str]]:
    """The chat messages for one primitive, in the shape ``LLM.chat`` wants."""
    return [
        {"role": "system", "content": SYSTEM_PROMPT},
        {"role": "user", "content": render_user_prompt(spec)},
    ]


def json_schema(spec: PrimitiveSpec) -> dict:
    """The structured-output schema for one primitive: string list for
    ADNOMINAL/TEXT, ``{terminal, te}`` pairs for ACTION_PAIR (THIRD_PARTY.md
    "### 出力JSONスキーマ")."""
    if spec.slot_type == ACTION_PAIR:
        pattern = FRAG_PREFIX_PATTERN if spec.key == "frame:filter_verb" else None
        return action_pair_schema(spec.min_items, spec.max_items, pattern)
    return string_list_schema(spec.min_items, spec.max_items)


def prompt_sha256(spec: PrimitiveSpec) -> str:
    """Hash of the full prompt (system + user) actually sent to the model --
    homework.md's "プロンプトのハッシュ値". Reproducible from template id +
    substitution values, both of which ``prompt_record`` stores alongside."""
    payload = SYSTEM_PROMPT + "\n\n" + render_user_prompt(spec)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def system_prompt_sha256() -> str:
    return hashlib.sha256(SYSTEM_PROMPT.encode("utf-8")).hexdigest()


def prompt_record(spec: PrimitiveSpec) -> dict:
    """Everything about one prompt that belongs in the generation log."""
    return {
        "key": spec.key,
        "slot_type": spec.slot_type,
        "template_id": spec.template_id,
        "substitutions": spec.substitutions(),
        "min_items": spec.min_items,
        "max_items": spec.max_items,
        "prompt_sha256": prompt_sha256(spec),
        "system_prompt_sha256": system_prompt_sha256(),
    }


def get(key: str) -> PrimitiveSpec:
    """Look up a primitive by expression-dictionary key, with a message that
    names the key (``schema.py`` op tags carry a ``:arg`` suffix for
    ``mul_const``, which must be stripped before calling this)."""
    try:
        return PRIMITIVES[key]
    except KeyError:
        raise KeyError(f"unknown expression-dictionary key: {key!r}") from None


def dictionary_key_for_op_tag(op_tag: str) -> str:
    """Map a ``SemanticAST.op_tags()`` entry to its dictionary key.

    Only ``map:mul_const:2`` / ``map:mul_const:3`` differ: the constant is a
    placeholder inside the expression (``N``), not part of the key
    (ja_generator_plan.md 1.3).
    """
    if op_tag.startswith("map:mul_const:"):
        return "map:mul_const"
    return op_tag


def all_prompts() -> list[tuple[PrimitiveSpec, list[dict[str, str]]]]:
    """Every (spec, messages) pair, in table order -- one request each."""
    return [(spec, build_messages(spec)) for spec in _SPECS]


def _main(argv: Optional[list[str]] = None) -> None:
    """``python semantic_ast/expressions_ja/ja_prompts.py [key]`` prints prompts for eyeballing."""
    import sys

    args = sys.argv[1:] if argv is None else argv
    specs = [get(args[0])] if args else list(_SPECS)
    for spec in specs:
        print("=" * 72)
        print(f"{spec.key}  [slot_type={spec.slot_type} template=({spec.template_id}) "
              f"items={spec.min_items}-{spec.max_items} hash={prompt_sha256(spec)[:12]}]")
        print("=" * 72)
        print(render_user_prompt(spec))
        print()


if __name__ == "__main__":
    _main()
