"""Prompt construction for the teacher model (THIRD_PARTY.md "プリミティブ
への問い合わせプロンプト").

THIRD_PARTY.md fixes, in prose, the exact strings this module has to build:
one common system prompt, four user-prompt templates (one per slot type),
and the substitution table (one row per expression-dictionary key).
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

Two further spots where THIRD_PARTY.md disagrees with itself, both left
as-is on purpose (the templates are what gets sent):

* template (a) says "リスト xs の要素に対する", while the rendered example
  under "### 具体例" says "リストの要素に対する";
* template (a)/(b) put ``{var_note}`` second in the 制約 list, the examples
  put it first.

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

制約:
- 出力は名詞（「要素」「値」など）に直接かかる連体修飾の形（「〜の」「〜い」のように名詞の直前に置ける形）のみとする。文末に置く終止形や、連用中止形は出力しないこと。
- {var_note}
- 意味を変えないこと（特に境界値の扱いに注意）。

出力はJSONスキーマに従うこと。"""

TEMPLATE_ACTION_PAIR = """Python関数 solve(xs, k) の中で、リストの要素に対する次の操作を表す日本語表現を、{count}ペア、重複なく列挙してください。

操作: {description}

各表現について、次の2つの形を対応づけて生成すること。
- terminal: 文末に置く終止形（例: 「kを加える」）
- te: 直後に別の操作の説明が続く場合に使う、連用中止形（例: 「kを加えて」）

制約:
- 同じ表現のterminalとteは、必ず同じ意味・同じ操作を指す対でなければならない（片方だけ違う言い方に変えない）。
- {var_note}
- 意味を変えないこと。

出力はJSONスキーマに従うこと。"""

TEMPLATE_FILTER_VERB = """Python関数 solve(xs, k) の問題文で、抽出条件（連体修飾の形で表現済みの、例:「k以上の偶数の」のような文字列）を受けて、それを使って「〜要素だけを残す」という意味の一文にまとめる言い方を、{count}種類、重複なく列挙してください。

条件を差し込む位置をプレースホルダ {{frag}} として、各表現に必ず1回含めてください（例:「{{frag}}要素だけを残す」）。

各表現について、terminal（文末に置く終止形、例:「{{frag}}要素だけを残す」）と te（直後に別の操作が続く場合の連用中止形、例:「{{frag}}要素だけを残し」）の両方を対応づけて生成すること。

制約:
- プレースホルダ {{frag}} の文字列自体は改変・省略しないこと。
- {{frag}} の直後は名詞的にもとの条件を受ける形にする（{{frag}}には「k以上の偶数の」のような連体形の文字列が入る前提）。
- 「残す／抽出する／選ぶ」のように、要素を絞り込むという意味を保つこと。

出力はJSONスキーマに従うこと。"""

TEMPLATE_TEXT = """Python関数 solve(xs, k) を実装させるための、日本語の問題文における「{role}」部分の言い方を、{count}種類、重複なく列挙してください。

{role_description}

制約:
- {var_note}
- {boundary_note}

出力はJSONスキーマに従うこと。"""

TEMPLATES: dict[str, str] = {
    "a": TEMPLATE_ADNOMINAL,
    "b": TEMPLATE_ACTION_PAIR,
    "c": TEMPLATE_FILTER_VERB,
    "d": TEMPLATE_TEXT,
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
    boundary_note: str = ""

    def count(self) -> str:
        """The ``{count}`` substitution, e.g. ``"10〜30"`` -- the 生成件数
        目安 column, reused verbatim as the JSON schema's item bounds."""
        return f"{self.min_items}〜{self.max_items}"

    def substitutions(self) -> dict[str, str]:
        """Every value substituted into the template, for the generation log
        (the prompt hash is reproducible from template id + these values)."""
        values = {"count": self.count()}
        for name in ("description", "var_note", "role", "role_description", "boundary_note"):
            value = getattr(self, name)
            if value:
                values[name] = value
        return values


def _filter_spec(op: str, description: str, var_note: str) -> PrimitiveSpec:
    return PrimitiveSpec(
        key=f"filter:{op}",
        slot_type=ADNOMINAL,
        template_id="a",
        min_items=10,
        max_items=30,
        description=description,
        var_note=var_note,
    )


def _action_spec(key: str, description: str, var_note: str) -> PrimitiveSpec:
    return PrimitiveSpec(
        key=key,
        slot_type=ACTION_PAIR,
        template_id="b",
        min_items=10,
        max_items=30,
        description=description,
        var_note=var_note,
    )


_SPECS: tuple[PrimitiveSpec, ...] = (
    # --- filter: ADNOMINAL x10, template (a) -------------------------------
    _filter_spec("even", "値が2で割り切れる（2で割った余りが0になる）こと", NO_VAR_NOTE),
    _filter_spec("odd", "値を2で割った余りが0でないこと", NO_VAR_NOTE),
    _filter_spec("gt_k", "値が変数kより真に大きいこと（k自身は含まない）", K_NOTE),
    _filter_spec("ge_k", "値が変数k以上であること（k自身を含む）", K_NOTE),
    _filter_spec("lt_k", "値が変数kより真に小さいこと（k自身は含まない）", K_NOTE),
    _filter_spec("le_k", "値が変数k以下であること（k自身を含む）", K_NOTE),
    _filter_spec("multiple_of_k", "値が変数kで割り切れる（kの倍数である）こと", K_NOTE),
    _filter_spec("positive", "値が0より真に大きいこと（正の数。0自体は含まない）", NO_VAR_NOTE),
    _filter_spec("negative", "値が0より真に小さいこと（負の数。0自体は含まない）", NO_VAR_NOTE),
    _filter_spec("zero", "値がちょうど0であること", NO_VAR_NOTE),
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
    _action_spec("order:ascending", "リスト全体を、小さい順（昇順）に並べ替える", NO_VAR_NOTE),
    _action_spec("order:descending", "リスト全体を、大きい順（降順）に並べ替える", NO_VAR_NOTE),
    _action_spec(
        "order:reverse",
        "現在の並び順の大小関係に関わらず、要素の並びをそのまま逆転させる（ソートではない）",
        NO_VAR_NOTE,
    ),
    # --- slice: ACTION_PAIR x3, template (b) -------------------------------
    _action_spec("slice:take_first_k", "リストの先頭から変数k個の要素を取り出す", K_NOTE),
    _action_spec("slice:take_last_k", "リストの末尾から変数k個の要素を取り出す", K_NOTE),
    _action_spec(
        "slice:step_2",
        "リストの先頭（0番目）の要素から1個おきに要素を取り出す（0, 2, 4, ...番目の要素を残す）",
        NO_VAR_NOTE,
    ),
    # --- frames ------------------------------------------------------------
    # Template (c) takes only {count}: the operation description and the
    # {frag} handling are written into the template itself.
    PrimitiveSpec(
        key="frame:filter_verb",
        slot_type=ACTION_PAIR,
        template_id="c",
        min_items=5,
        max_items=10,
    ),
    PrimitiveSpec(
        key="frame:opening",
        slot_type=TEXT,
        template_id="d",
        min_items=10,
        max_items=30,
        role="書き出し",
        role_description=(
            "整数のリストxsを読み手に導入する一文（の前半）。直後に抽出条件などの節"
            "（例:「偶数の要素だけを残し、」）が続くことを前提に、読点「、」で終える自然な接続にすること。"
        ),
        var_note=XS_NOTE,
        boundary_note="文中に条件・操作を表す語を含めないこと（書き出しは入力の導入のみを行う）",
    ),
    PrimitiveSpec(
        key="frame:closing",
        slot_type=TEXT,
        template_id="d",
        min_items=10,
        max_items=30,
        role="結び",
        role_description=(
            "直前に置かれる動詞の連体形（例:「昇順に並べる」）を受けて、solve関数の実装を依頼する"
            "一文の後半としてまとめる言い方。句点「。」で終えること。"
        ),
        var_note=SOLVE_NOTE,
        boundary_note=(
            "直前の動詞の連体形に自然に接続する形にし、それ自体で条件や操作の内容を新たに追加しないこと"
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
        return action_pair_schema(spec.min_items, spec.max_items)
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
    """``python semantic_ast/ja_prompts.py [key]`` prints prompts for eyeballing."""
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
