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
"""

from __future__ import annotations

import json
import random
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

from ja_dictionary import ExpressionDictionary
from ja_prompts import FRAG_PLACEHOLDER
from schema import SemanticAST

CLAUSE_SEPARATOR = "、"
CHAIN_CONNECTIVE = "から"  # ja_generator_plan.md 2.2: te形 + から
CONST_PLACEHOLDER = "N"  # ja_generator_plan.md 2.5 (mul_const only)

TERMINAL = "terminal"
TE = "te"


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


def _render_filter(ast: SemanticAST, picker: _Picker, is_last_category: bool) -> str:
    """ja_generator_plan.md 2.1: concatenate the ADNOMINAL fragments, then
    substitute them into the shared filter frame."""
    fragment = "".join(picker.text(f"filter:{op}") for op in ast.filters)
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
    """ja_generator_plan.md 2.4 + the 読点 decision in this module's docstring."""
    leading = [opening, *clauses[:-1]]
    parts = [part.rstrip(CLAUSE_SEPARATOR) for part in leading]
    parts.append(clauses[-1])
    return CLAUSE_SEPARATOR.join(parts) + closing


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
