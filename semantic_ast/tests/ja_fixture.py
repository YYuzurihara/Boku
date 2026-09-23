"""A hand-written expression dictionary for the ja_* tests.

Deliberately one expression per key, using the exact examples from
ja_generator_plan.md, so a rendered sentence is fully determined (no
sampling variance) and can be compared against the worked example in that
document's section 2.6.
"""

from __future__ import annotations

import sys
from pathlib import Path

_SEMANTIC_AST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SEMANTIC_AST))
sys.path.insert(0, str(_SEMANTIC_AST / "expressions_ja"))

from ja_dictionary import ExpressionDictionary  # noqa: E402
from ja_prompts import ACTION_PAIR, PRIMITIVES  # noqa: E402

# Expressions taken from ja_generator_plan.md's tables where it gives one;
# the rest follow the same shape so every key is covered.
_ADNOMINAL = {
    "filter:even": "偶数の",
    "filter:odd": "奇数の",
    "filter:gt_k": "kより大きい",
    "filter:ge_k": "k以上の",
    "filter:lt_k": "kより小さい",
    "filter:le_k": "k以下の",
    "filter:multiple_of_k": "kの倍数の",
    "filter:positive": "正の",
    "filter:negative": "負の",
    "filter:zero": "ゼロの",
}

_ACTION_PAIRS = {
    "map:add_k": ("kを加える", "kを加えて"),
    "map:sub_k": ("kを引く", "kを引いて"),
    "map:mul_k": ("kを掛ける", "kを掛けて"),
    "map:negate": ("符号を反転する", "符号を反転して"),
    "map:abs": ("絶対値を取る", "絶対値を取って"),
    "map:square": ("二乗する", "二乗して"),
    "map:mul_const": ("N倍する", "N倍して"),
    "order:ascending": ("昇順に並べる", "昇順に並べて"),
    "order:descending": ("降順に並べる", "降順に並べて"),
    "order:reverse": ("順序を逆にする", "順序を逆にして"),
    "slice:take_first_k": ("先頭からk個を取り出す", "先頭からk個を取り出して"),
    "slice:take_last_k": ("末尾からk個を取り出す", "末尾からk個を取り出して"),
    "slice:step_2": ("1個おきに取り出す", "1個おきに取り出して"),
    "frame:filter_verb": ("{frag}要素だけを残す", "{frag}要素だけを残し"),
}

_TEXT = {
    # neutral on purpose: the opening is picked without knowing which category
    # comes first, so 「整数リストxsから、」 (which presupposes extraction) is
    # exactly what ja_generator.contract_problems rejects
    "frame:opening": "整数のリストxsについて、",
    "frame:closing": "solve関数を書いてください。",
}

# Second ACTION_PAIR variants that a generic prefix cannot produce.
_SECOND_PAIRS = {
    "frame:filter_verb": {"terminal": "{frag}要素を抽出する", "te": "{frag}要素を抽出し"},
}


def fixture_dictionary(extra_variants: bool = False) -> ExpressionDictionary:
    """One expression per key (deterministic rendering).

    With ``extra_variants`` each key gets a second expression as well, for
    tests that need more than one distinct sentence per semantic AST.
    """
    expressions: dict[str, list] = {}
    for key, spec in PRIMITIVES.items():
        if spec.slot_type == ACTION_PAIR:
            terminal, te = _ACTION_PAIRS[key]
            entry: list = [{"terminal": terminal, "te": te}]
            if extra_variants:
                # the second variant has to be a different string that still
                # satisfies ja_generator.contract_problems: a terminal ending
                # in a verb, a te form 「から」 can attach to, and -- for the
                # filter frame -- nothing in front of {frag}
                entry.append(_SECOND_PAIRS.get(key) or {"terminal": "きちんと" + terminal, "te": "きちんと" + te})
        else:
            text = _ADNOMINAL.get(key) or _TEXT[key]
            entry = [text]
            if extra_variants:
                entry.append("別の" + text)
        expressions[key] = entry
    return ExpressionDictionary.from_expressions(expressions)
