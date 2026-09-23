"""Combine expression-dictionary entries into one Japanese instruction per
semantic AST (ja_generator_plan.md "2. 組み合わせ型（テンプレート合成規則）").

This is the deterministic half of the two-stage design: the teacher model is
only ever asked for *atomic* expressions (one prompt per dictionary key,
ja_teacher.py), and every one of the 40,589 semantic ASTs is turned into
Japanese here, by
rule, by sampling one approved expression per primitive and concatenating
the clauses in the pipeline order ``filter -> map -> order -> slice``.

Composition rules, straight from ja_generator_plan.md section 2:

* filter (2.1): the ADNOMINAL fragments of all filter predicates are
  concatenated as-is and substituted into ``frame:filter_verb``'s ``{frag}``.
  The plan leaves their order open ("順不同"); this module fixes it (see
  ``ADNOMINAL_GROUP_ORDER``) because stacked 連体修飾 are *not* order-free
  in Japanese.
* map / slice (2.2): an ordered chain of ACTION_PAIRs; every op but the last
  in the chain uses the ``te`` form plus the connective ``から``
  ("kを加えてから2倍する").
* order (2.3): a single ACTION_PAIR, no chaining.
* across categories (2.4): the last active category uses ``terminal``,
  every earlier one uses ``te``; ``frame:opening`` leads and
  ``frame:closing`` closes.
* placeholders (2.5): ``k`` stays the literal string ``k``; ``N`` is replaced
  by ``mul_const``'s actual constant.

Decision on ja_generator_plan.md's open question ("読点「、」を表現辞書側の
文字列に含めるか、生成器側で一律付与するか", section 5): the **generator**
inserts ``、`` uniformly between the opening frame and each non-final clause,
and strips one trailing ``、`` off those parts first so a dictionary entry
that happens to end with a comma (frame:opening's prompt asks for exactly
that) does not produce ``、、``. Nothing else about a stored expression is
rewritten -- an odd expression stays odd, visibly, which is the point of the
human approval step.

Division of labour with the teacher model: the model only ever writes
*atomic* expressions, so every problem that is structural -- a clause that
cannot attach to the next one -- has to be the joining rules' problem, not
the model's. The rules above are stated so that a dictionary meeting the
contract in ``contract_problems`` always composes into grammatical Japanese;
``contract_problems`` names that contract and checks the mechanically
checkable half of it, so a violation is reported against the dictionary
entry instead of showing up as a broken sentence 40,589 times.
"""

from __future__ import annotations

import json
import random
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

# schema.py lives one level up (semantic_ast/), which is not on sys.path when
# a module in this directory is imported or run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ja_dictionary import ExpressionDictionary  # noqa: E402
from ja_prompts import ACTION_PAIR, ADNOMINAL, FRAG_PLACEHOLDER, PRIMITIVES, TEXT  # noqa: E402
from schema import FILTER_OP_TO_GROUP, SemanticAST  # noqa: E402

CLAUSE_SEPARATOR = "、"
CHAIN_CONNECTIVE = "から"  # ja_generator_plan.md 2.2: te形 + から
CONST_PLACEHOLDER = "N"  # ja_generator_plan.md 2.5 (mul_const only)

TERMINAL = "terminal"
TE = "te"

# Reading order of the stacked 連体修飾 fragments of a multi-predicate filter
# (schema.py caps it at two, one per mutually-exclusive group).
#
# ``filters`` is a set semantically -- AND is commutative, and
# ``schema.canonical_json`` sorts it for hashing -- so the renderer is free to
# choose the order it reads them in, and it has to: stacked 連体修飾 are not
# order-free in Japanese. The modifier that classifies the element sits
# closest to the noun and the one that restricts its range sits outermost, so
# 「k以上の偶数の要素」 reads naturally where 「偶数のk以上の要素」 does not.
# generator.py enumerates predicates in schema.py's vocabulary order (parity
# before k_compare), which is exactly the wrong way round, so the order is
# imposed here rather than left to enumeration order.
ADNOMINAL_GROUP_ORDER: tuple[str, ...] = ("k_compare", "sign", "k_multiple", "parity")


class JaRenderError(ValueError):
    """Raised when a semantic AST cannot be rendered from the dictionary at
    hand (missing key, empty expression list, unusable entry shape)."""


@dataclass(frozen=True)
class ExpressionChoice:
    """Which stored expression was used where -- enough to re-derive the
    sentence from the dictionary, and to tell which dictionary entries a
    saved instruction depends on (needed for the "言い換えテスト" reservation
    described in ja_generator_plan.md section 3)."""

    key: str
    index: int
    form: Optional[str] = None  # "terminal" / "te" for ACTION_PAIR, else None
    arg: Optional[int] = None  # mul_const's constant, substituted for N

    def to_dict(self) -> dict:
        d: dict = {"key": self.key, "index": self.index}
        if self.form is not None:
            d["form"] = self.form
        if self.arg is not None:
            d["arg"] = self.arg
        return d


@dataclass(frozen=True)
class Rendering:
    """One Japanese instruction plus the choices that produced it."""

    text: str
    choices: tuple[ExpressionChoice, ...]

    def to_dict(self) -> dict:
        return {"text": self.text, "choices": [c.to_dict() for c in self.choices]}


class _Picker:
    """Samples one expression per key and records what it picked."""

    def __init__(self, dictionary: ExpressionDictionary, rng: random.Random) -> None:
        self.dictionary = dictionary
        self.rng = rng
        self.choices: list[ExpressionChoice] = []

    def _pick(self, key: str) -> tuple[object, int]:
        expressions = self.dictionary.expressions(key)  # raises if key absent
        if not expressions:
            raise JaRenderError(f"expression dictionary entry {key!r} has no expressions")
        index = self.rng.randrange(len(expressions))
        return expressions[index], index

    def text(self, key: str) -> str:
        """Pick a plain-string expression (ADNOMINAL / TEXT)."""
        expression, index = self._pick(key)
        if not isinstance(expression, str):
            raise JaRenderError(f"{key}[{index}]: expected a string expression, got {type(expression).__name__}")
        self.choices.append(ExpressionChoice(key=key, index=index))
        return expression

    def pair(self, key: str, form: str, arg: Optional[int] = None) -> str:
        """Pick an ACTION_PAIR expression and take one of its two forms."""
        expression, index = self._pick(key)
        if not isinstance(expression, dict) or form not in expression:
            raise JaRenderError(
                f"{key}[{index}]: expected a {{terminal, te}} pair with a {form!r} form, got {expression!r}"
            )
        text = expression[form]
        if arg is not None:
            text = text.replace(CONST_PLACEHOLDER, str(arg))
        self.choices.append(ExpressionChoice(key=key, index=index, form=form, arg=arg))
        return text


def _form(is_last: bool) -> str:
    return TERMINAL if is_last else TE


def adnominal_order(filters: Sequence[str]) -> tuple[str, ...]:
    """``filters`` in the order their fragments are read out (see
    ``ADNOMINAL_GROUP_ORDER``). Predicates of an unknown group keep their
    position at the end; the sort is stable, so the AST's own order decides
    any tie."""
    def rank(op: str) -> int:
        group = FILTER_OP_TO_GROUP.get(op)
        return ADNOMINAL_GROUP_ORDER.index(group) if group in ADNOMINAL_GROUP_ORDER else len(ADNOMINAL_GROUP_ORDER)

    return tuple(sorted(filters, key=rank))


def _render_filter(ast: SemanticAST, picker: _Picker, is_last_category: bool) -> str:
    """ja_generator_plan.md 2.1: concatenate the ADNOMINAL fragments, then
    substitute them into the shared filter frame."""
    fragment = "".join(picker.text(f"filter:{op}") for op in adnominal_order(ast.filters))
    frame = picker.pair("frame:filter_verb", _form(is_last_category))
    return frame.replace(FRAG_PLACEHOLDER, fragment)


def _render_chain(
    ops: Sequence[tuple[str, Optional[int]]], picker: _Picker, is_last_category: bool
) -> str:
    """ja_generator_plan.md 2.2: an ordered ACTION_PAIR chain (map / slice).
    Non-final links are ``te`` + ``から``; the final link is ``terminal`` only
    if this is also the last active category."""
    parts: list[str] = []
    for position, (key, arg) in enumerate(ops):
        is_last_op = position == len(ops) - 1
        text = picker.pair(key, _form(is_last_category and is_last_op), arg=arg)
        if not is_last_op:
            text += CHAIN_CONNECTIVE
        parts.append(text)
    return "".join(parts)


def _clause(ast: SemanticAST, category: str, picker: _Picker, is_last_category: bool) -> str:
    if category == "filter":
        return _render_filter(ast, picker, is_last_category)
    if category == "map":
        ops = [(f"map:{name}", arg) for name, arg in ast.map_ops]
        return _render_chain(ops, picker, is_last_category)
    if category == "order":
        return picker.pair(f"order:{ast.order_op}", _form(is_last_category))
    if category == "slice":
        ops = [(f"slice:{name}", None) for name in ast.slice_ops]
        return _render_chain(ops, picker, is_last_category)
    raise JaRenderError(f"unknown category: {category!r}")  # pragma: no cover - schema-guarded


def _assemble(opening: str, clauses: Sequence[str], closing: str) -> str:
    """ja_generator_plan.md 2.4 + the 読点 decision in this module's docstring.

    The final clause runs straight into the closing frame's noun phrase
    (「…昇順に並べる」+「solve関数を書いてください。」): that juncture is a
    連体修飾, so a 読点 on either side of it would cut the modifier loose from
    the noun it modifies, and both sides are stripped of one.
    """
    leading = [opening, *clauses[:-1]]
    parts = [part.rstrip(CLAUSE_SEPARATOR) for part in leading]
    parts.append(clauses[-1].rstrip(CLAUSE_SEPARATOR))
    return CLAUSE_SEPARATOR.join(parts) + closing.lstrip(CLAUSE_SEPARATOR)


def render(
    ast: SemanticAST, dictionary: ExpressionDictionary, rng: Optional[random.Random] = None
) -> Rendering:
    """Render one Japanese instruction for ``ast`` by sampling the dictionary."""
    rng = rng or random.Random()
    picker = _Picker(dictionary, rng)

    categories = ast.active_categories()  # already in pipeline order
    if not categories:  # pragma: no cover - schema forbids it
        raise JaRenderError(f"semantic AST has no active category: {ast.to_dict()}")

    opening = picker.text("frame:opening")
    clauses = [
        _clause(ast, category, picker, is_last_category=(i == len(categories) - 1))
        for i, category in enumerate(categories)
    ]
    closing = picker.text("frame:closing")

    return Rendering(text=_assemble(opening, clauses, closing), choices=tuple(picker.choices))


def seed_for(ast: SemanticAST, seed: int = 0) -> int:
    """Per-AST seed derived from the semantic hash (not the randomized
    builtin ``hash()``), so renderings are reproducible across runs and
    machines -- same convention as demo.py's test-case seeding."""
    return seed ^ int(ast.semantic_hash()[:8], 16)


def render_variants(
    ast: SemanticAST,
    dictionary: ExpressionDictionary,
    n: int = 1,
    seed: int = 0,
    max_attempts: Optional[int] = None,
) -> list[Rendering]:
    """Up to ``n`` *distinct* instructions for one semantic AST.

    Distinctness is by sentence text, so two different expression choices
    that happen to spell the same sentence count once. With a small
    dictionary the number of distinct sentences can be lower than ``n``;
    this returns what it found rather than looping forever.
    """
    rng = random.Random(seed_for(ast, seed))
    attempts = max_attempts if max_attempts is not None else max(20, n * 10)
    out: list[Rendering] = []
    seen: set[str] = set()
    for _ in range(attempts):
        if len(out) >= n:
            break
        rendering = render(ast, dictionary, rng)
        if rendering.text in seen:
            continue
        seen.add(rendering.text)
        out.append(rendering)
    return out


def leftover_placeholders(text: str) -> list[str]:
    """Placeholders that should have been substituted but are still in the
    sentence. ``{frag}`` means a filter frame was used without substitution;
    ``k`` is intentionally left literal (2.5) and ``N`` is unrecoverable once
    rendered, so neither is reported here."""
    return [FRAG_PLACEHOLDER] if FRAG_PLACEHOLDER in text else []


# ---------------------------------------------------------------------------
# The contract the joining rules depend on
# ---------------------------------------------------------------------------
#
# Each rule below is a *join* rule: break it and the sentences this module
# builds are ungrammatical however good the dictionary otherwise is, because
# the renderer glues the neighbouring clause on with nothing in between.
# Judgement calls are deliberately absent -- a clumsy paraphrase, a closing
# that asks the reader to *run* solve rather than write it, a fragment that is
# fine alone but stiff when stacked. Those belong to the prompts
# (THIRD_PARTY.md) and to the human approval step, so a clean report means
# "nothing here can break a join", not "this dictionary is good Japanese".

# A noun at the end of an expression collides with the noun the renderer
# writes next: 「要素」 after a filter fragment, 「solve関数」 after a terminal.
TRAILING_NOUNS: tuple[str, ...] = (
    "要素", "もの", "物", "値", "数", "こと", "事", "とき", "操作", "処理", "動作", "方法", "行為",
)

# frame:filter_verb supplies the narrowing itself (「{frag}要素だけを残す」), so
# a fragment carrying it too says it twice: 「k以上の要素だけ」 + 「要素を抽出する」.
NARROWING_MARKERS: tuple[str, ...] = ("だけ", "のみ", "を残す", "を抽出", "を選ぶ")

# A 連体修飾 cannot end in a case particle, so a fragment ending in one does
# not attach to the noun the frame puts after it: 「k以上であるものから」 +
# 「要素だけを選ぶ」. 「の」 is excluded -- it is *the* adnominal particle.
TRAILING_PARTICLES: tuple[str, ...] = ("から", "まで", "より", "へ", "に", "を", "と", "は", "が", "で")

# frame:opening is picked independently of which category happens to come
# first, so an opening that governs the next clause only works for one of
# them: 「整数リストxsから、」 wants something taken *out of* xs, which reads
# fine before 「偶数の要素だけを残す」 and wrong before 「kを加える」.
NON_NEUTRAL_OPENING_ENDINGS: tuple[str, ...] = ("から", "より")


def _ends_with(text: str, suffixes: Sequence[str]) -> Optional[str]:
    return next((s for s in suffixes if text.endswith(s)), None)


def _adnominal_contract(where: str, expr: str) -> list[str]:
    problems = []
    noun = _ends_with(expr, TRAILING_NOUNS)
    if noun:
        problems.append(
            f"{where}: ends with the noun 「{noun}」, which runs straight into the filter "
            f"frame's own noun (「{expr}要素だけを残す」)"
        )
    particle = _ends_with(expr, TRAILING_PARTICLES)
    if particle and not noun:
        problems.append(
            f"{where}: ends with the case particle 「{particle}」, so it is not a 連体修飾 and "
            f"does not attach to the frame's noun (「{expr}要素だけを残す」)"
        )
    marker = next((m for m in NARROWING_MARKERS if m in expr), None)
    if marker:
        problems.append(
            f"{where}: contains 「{marker}」, but the filter frame already supplies the "
            f"narrowing -- the fragment only states the condition"
        )
    return problems


def _action_pair_contract(where: str, key: str, expr: dict) -> list[str]:
    terminal, te = expr.get(TERMINAL), expr.get(TE)
    if not isinstance(terminal, str) or not isinstance(te, str):
        return []  # shape problem: ExpressionDictionary.validate() reports it
    problems = []
    noun = _ends_with(terminal, TRAILING_NOUNS)
    if noun:
        problems.append(
            f"{where}.terminal: ends with the noun 「{noun}」; the closing frame's noun "
            f"phrase follows it directly (「{terminal}solve関数を書いてください。」)"
        )
    elif terminal.endswith(("て", "で")):
        # a て形 in the terminal slot: 「先頭からk個を取得して」 cannot head the
        # 連体修飾 the closing frame's noun phrase needs
        problems.append(
            f"{where}.terminal: is a て形, not a 終止形, so the closing frame's noun phrase "
            f"cannot attach to it (「{terminal}solve関数を書いてください。」)"
        )
    if key == "frame:filter_verb":
        # the frame contributes the verb, the fragment contributes the
        # condition; text in front of {frag} is a second, contradictory copy
        # of the condition (「k以上の偶数の{frag}要素だけを残す」)
        for form, text in ((TERMINAL, terminal), (TE, te)):
            if FRAG_PLACEHOLDER in text and not text.startswith(FRAG_PLACEHOLDER):
                problems.append(
                    f"{where}.{form}: has text in front of {FRAG_PLACEHOLDER} "
                    f"(「{text.split(FRAG_PLACEHOLDER)[0]}」), which the renderer would read as a "
                    f"second condition in front of the one it substitutes"
                )
    if te == terminal:
        problems.append(f"{where}.te: identical to terminal, so it cannot carry a following clause")
    if key.startswith(("map:", "slice:")):
        if te.endswith(CHAIN_CONNECTIVE):
            problems.append(
                f"{where}.te: already ends with the chain connective 「{CHAIN_CONNECTIVE}」, "
                f"which the renderer adds itself (「{te}{CHAIN_CONNECTIVE}」)"
            )
        elif not te.endswith(("て", "で")):
            problems.append(
                f"{where}.te: not a て形, so the chain connective cannot attach to it "
                f"(「{te}{CHAIN_CONNECTIVE}」)"
            )
    return problems


def _frame_contract(where: str, key: str, expr: str) -> list[str]:
    problems = []
    body = expr.rstrip().rstrip(CLAUSE_SEPARATOR)
    if key == "frame:opening":
        if body.endswith("。"):
            problems.append(f"{where}: ends the sentence with 「。」, but clauses follow it")
        ending = _ends_with(body, NON_NEUTRAL_OPENING_ENDINGS)
        if ending:
            problems.append(
                f"{where}: ends with 「{ending}」, which presupposes that something is taken "
                f"out of xs; the opening has to read as well before 「kを加える」 as before "
                f"「偶数の要素だけを残す」"
            )
    elif key == "frame:closing":
        if not expr.rstrip().endswith("。"):
            problems.append(f"{where}: does not end with 「。」, but it ends the sentence")
        if "solve" not in expr:
            problems.append(
                f"{where}: does not name solve; the closing carries the noun phrase that the "
                f"last clause modifies"
            )
    return problems


def contract_problems(dictionary: ExpressionDictionary) -> list[str]:
    """Entries the joining rules cannot combine into grammatical Japanese,
    as human-readable strings (empty list == everything composes).

    Complements ``ExpressionDictionary.validate()``, which checks the file's
    *shape*: this checks what the shape cannot -- whether a well-formed entry
    attaches to the clause the renderer will put next to it. Nothing is
    repaired, for the reason ja_teacher.py saves broken responses verbatim:
    editing the dictionary is the human reviewer's call.
    """
    problems: list[str] = []
    for key in dictionary.keys():
        spec = PRIMITIVES.get(key)
        if spec is None:
            continue  # unknown key: validate() reports it
        for i, expr in enumerate(dictionary.entries[key].get("expressions") or []):
            where = f"{key}[{i}]"
            if spec.slot_type == ADNOMINAL and isinstance(expr, str):
                problems.extend(_adnominal_contract(where, expr))
            elif spec.slot_type == ACTION_PAIR and isinstance(expr, dict):
                problems.extend(_action_pair_contract(where, key, expr))
            elif spec.slot_type == TEXT and isinstance(expr, str):
                problems.extend(_frame_contract(where, key, expr))
    return problems


# ---------------------------------------------------------------------------
# Saving the combined expressions
# ---------------------------------------------------------------------------


def instruction_record(
    ast: SemanticAST,
    renderings: Sequence[Rendering],
    dictionary: ExpressionDictionary,
    spec_id: Optional[str] = None,
    seed: int = 0,
) -> dict:
    """One JSONL record: the semantic AST, its rendered instructions, and the
    provenance needed to reproduce them (dictionary hash + seed + the exact
    expression indices used).

    Field names line up with homework.md's データレコード example, so these
    records can be joined onto demo.py's ``out/{train,val,test}.jsonl`` by
    ``semantic_hash`` / ``spec_id``.
    """
    record: dict = {
        "semantic_ast": ast.to_dict(),
        "semantic_hash": ast.semantic_hash(),
        "instruction_ja": [r.text for r in renderings],
        "renderings": [r.to_dict() for r in renderings],
        "dictionary_sha256": dictionary.content_sha256(),
        "render_seed": seed,
    }
    if spec_id is not None:
        record = {"spec_id": spec_id, **record}
    return record


def save_instructions(records: Iterable[dict], path: Union[str, Path]) -> Path:
    """Write instruction records as JSONL (UTF-8, unescaped Japanese)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def load_instructions(path: Union[str, Path]) -> list[dict]:
    """Read back what ``save_instructions`` wrote (used by ja_demo.py to
    verify the round trip)."""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def render_from_record(record: dict, dictionary: ExpressionDictionary) -> list[str]:
    """Re-derive the sentences of a saved record from its stored choices.

    A pure replay -- no sampling -- so it doubles as a check that the saved
    instruction really is reproducible from (dictionary, choices) alone.
    """
    ast = SemanticAST.from_dict(record["semantic_ast"])
    out: list[str] = []
    for rendering in record["renderings"]:
        queue = list(rendering["choices"])
        picker = _ReplayPicker(dictionary, queue)
        categories = ast.active_categories()
        opening = picker.text("frame:opening")
        clauses = [
            _clause(ast, category, picker, is_last_category=(i == len(categories) - 1))
            for i, category in enumerate(categories)
        ]
        closing = picker.text("frame:closing")
        out.append(_assemble(opening, clauses, closing))
    return out


class _ReplayPicker(_Picker):
    """A ``_Picker`` that replays recorded choices instead of sampling."""

    def __init__(self, dictionary: ExpressionDictionary, queue: list[dict]) -> None:
        super().__init__(dictionary, random.Random(0))
        self.queue = queue

    def _pick(self, key: str) -> tuple[object, int]:
        if not self.queue:
            raise JaRenderError(f"replay ran out of recorded choices at key {key!r}")
        choice = self.queue.pop(0)
        if choice["key"] != key:
            raise JaRenderError(f"replay expected key {choice['key']!r}, renderer asked for {key!r}")
        index = choice["index"]
        expressions = self.dictionary.expressions(key)
        if not 0 <= index < len(expressions):
            raise JaRenderError(
                f"{key}: recorded index {index} is out of range for a dictionary with "
                f"{len(expressions)} expressions (dictionary changed since the record was written?)"
            )
        return expressions[index], index
