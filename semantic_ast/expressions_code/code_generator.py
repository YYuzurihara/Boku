"""Render a ``SemanticAST`` into Python source, once per ``CodeStyle``
(homework.md 「コードの構造的変換」: 「同じ意味ASTから複数の等価コードを生成
する」).

This is the second of homework.md's "独立した二つのプログラム": the first is
``reference_interpreter.py``, which computes the answer directly from the
semantic AST, and this one emits the ``solve(xs, k)`` source that the model
is trained to produce. The two are written independently on purpose -- they
are cross-checked against each other in ``code_verifier.py``, which is what
turns "the generator has a bug" into a test failure instead of into thousands of
subtly wrong training examples.

Everything here is rule-based, as homework.md requires (「正解の意味構造、コー
ド、テストはルールベースで作成し、教師は自然言語（日本語）表現を増やす役割に
限定する」): the teacher model never sees a line of this.

Order-preserving rendering
--------------------------
The code follows ``ast.ops`` left to right, one atomic operation at a time,
so two ASTs that use the same operations in a different order always get
different code in every style (schema.py, "Order is identity") -- even when
the two orders happen to compute the same function.

Consecutive ops are grouped into *stages* (``_stages``): a run of filters
followed by a run of maps is one comprehension / ``for`` loop (the filters
become one ``and``-joined condition, the maps one composed element
expression), a run of slices is one chain of subscripts, and every order op
is a stage of its own. Grouping never reorders anything: the conditions are
joined, and the maps nested, in op order, and a filter that comes *after* a
map starts a new stage. What the styles vary is *how* the stages are
spelled, never what they compute or in which order.

Operator precedence
-------------------
Chained map operations compose into one element expression, so the text has
to be parenthesised by precedence rather than by concatenation: ``add_k``
then ``mul_const(2)`` is ``(x + k) * 2``, and ``negate`` then ``square`` is
``(-x) ** 2`` -- without those parens Python would read ``-x ** 2`` as
``-(x ** 2)``. ``_Expr`` carries a precedence level with the text and wraps
only where it must.

Generated comments
------------------
The comment axis emits fixed, category-level Japanese comments (「条件に合う
要素だけを残す」), not a description of the specific operations. Two reasons:
a per-operation comment would be a second natural-language rendering of the
instruction living inside the label the model must produce, and the wording
of natural language is the teacher model's and the human reviewer's job
(expressions_ja/), not this generator's. Category-level comments carry no
information the semantic AST does not already fix, so they cannot drift away
from the code they sit above.
"""

from __future__ import annotations

import hashlib
import json
import sys
from collections.abc import Iterable, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

# schema.py lives one level up (semantic_ast/), which is not on sys.path when
# a module in this directory is imported or run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from code_styles import (  # noqa: E402
    FORM_COMPREHENSION,
    FORM_LOOP,
    ORDER_EXPLICIT,
    STYLES,
    STYLES_BY_NAME,
    TEMP_NONE,
    TEMP_STAGED,
    CodeStyle,
    select_styles,
)
from schema import AtomicOp, SemanticAST  # noqa: E402

INDENT = "    "

SIGNATURE_ANNOTATED = "def solve(xs: list[int], k: int) -> list[int]:"
SIGNATURE_BARE = "def solve(xs, k):"
LIST_ANNOTATION = ": list[int]"


class CodeGenError(ValueError):
    """Raised when a semantic AST cannot be rendered (unknown operation --
    i.e. the vocabulary grew and this module was not updated)."""


# ---------------------------------------------------------------------------
# Expressions
# ---------------------------------------------------------------------------

# Precedence levels, ordered as Python's grammar orders them. Only the levels
# the map vocabulary can produce are needed.
PREC_ADD = 1
PREC_MUL = 2
PREC_UNARY = 3
PREC_POW = 4
PREC_ATOM = 5


@dataclass(frozen=True)
class _Expr:
    """A piece of Python source plus the precedence of its top-level operator
    (``PREC_ATOM`` for names, calls, subscripts and displays)."""

    text: str
    prec: int = PREC_ATOM

    def wrapped(self, min_prec: int) -> str:
        """``text``, parenthesised if it binds more loosely than the context
        it is about to be dropped into requires."""
        return self.text if self.prec >= min_prec else f"({self.text})"


# One condition per filter predicate, as a format string over the element
# variable. Mirrors reference_interpreter._FILTER_FUNCS one for one.
FILTER_CONDITIONS: dict[str, str] = {
    "even": "{x} % 2 == 0",
    "odd": "{x} % 2 != 0",
    "gt_k": "{x} > k",
    "ge_k": "{x} >= k",
    "lt_k": "{x} < k",
    "le_k": "{x} <= k",
    "multiple_of_k": "{x} % k == 0",
    "positive": "{x} > 0",
    "negative": "{x} < 0",
    "zero": "{x} == 0",
}


def _apply_map(expr: _Expr, name: str, arg: Optional[int]) -> _Expr:
    """``expr`` with one map operation applied around it. Mirrors
    reference_interpreter._MAP_FUNCS one for one."""
    if name == "add_k":
        return _Expr(f"{expr.wrapped(PREC_ADD)} + k", PREC_ADD)
    if name == "sub_k":
        return _Expr(f"{expr.wrapped(PREC_ADD)} - k", PREC_ADD)
    if name == "mul_k":
        return _Expr(f"{expr.wrapped(PREC_MUL)} * k", PREC_MUL)
    if name == "mul_const":
        return _Expr(f"{expr.wrapped(PREC_MUL)} * {arg}", PREC_MUL)
    if name == "negate":
        # a unary operand is parenthesised too: -(-x), not --x
        return _Expr(f"-{expr.wrapped(PREC_POW)}", PREC_UNARY)
    if name == "abs":
        return _Expr(f"abs({expr.text})", PREC_ATOM)
    if name == "square":
        # ``**`` binds tighter than unary minus on its left operand, so
        # anything but an atom has to be parenthesised: (-x) ** 2, not -x ** 2.
        return _Expr(f"{expr.wrapped(PREC_ATOM)} ** 2", PREC_POW)
    raise CodeGenError(f"unknown map op: {name!r}")


def element_expr(maps: Sequence[AtomicOp], variable: str) -> _Expr:
    """The element expression of a comprehension / ``append`` call: every map
    operation applied to ``variable`` in op order."""
    expr = _Expr(variable, PREC_ATOM)
    for op in maps:
        expr = _apply_map(expr, op.name, op.arg)
    return expr


def condition_text(filters: Sequence[AtomicOp], variable: str) -> str:
    """The ``if`` condition of a comprehension / loop body: the predicates
    joined with ``and`` in op order, or ``""`` for none (``x % k == 0`` is
    safe for the same reason the interpreter is: ``k`` is contractually 1-10,
    never 0).
    """
    parts = []
    for op in filters:
        template = FILTER_CONDITIONS.get(op.name)
        if template is None:
            raise CodeGenError(f"unknown filter op: {op.name!r}")
        parts.append(template.format(x=variable))
    return " and ".join(parts)


def _order_expr(expr: _Expr, name: str, spelling: str) -> _Expr:
    """Order op ``name`` applied to ``expr`` as an expression (the functional
    spelling, used by the comprehension form and by staged variables).

    Only ``reverse`` has a second spelling. Spelling ``descending`` as
    ``sorted(...)[::-1]`` would make it byte-identical to ``ascending`` then
    ``reverse`` -- two different ASTs, one code."""
    if name == "ascending":
        return _Expr(f"sorted({expr.text})", PREC_ATOM)
    if name == "descending":
        return _Expr(f"sorted({expr.text}, reverse=True)", PREC_ATOM)
    if name == "reverse":
        if spelling == ORDER_EXPLICIT:
            return _Expr(f"list(reversed({expr.text}))", PREC_ATOM)
        return _Expr(f"{expr.wrapped(PREC_ATOM)}[::-1]", PREC_ATOM)
    raise CodeGenError(f"unknown order op: {name!r}")


SLICE_SUBSCRIPTS: dict[str, str] = {
    "take_first_k": "[:k]",
    "take_last_k": "[-k:]",  # k >= 1 by schema, so this is never the empty [-0:]
    "step_2": "[::2]",
}


def _slice_expr(expr: _Expr, slices: Sequence[AtomicOp]) -> _Expr:
    """Every slice operation as a chain of subscripts, in op order."""
    text = expr.wrapped(PREC_ATOM)
    for op in slices:
        subscript = SLICE_SUBSCRIPTS.get(op.name)
        if subscript is None:
            raise CodeGenError(f"unknown slice op: {op.name!r}")
        text += subscript
    return _Expr(text, PREC_ATOM)


@dataclass(frozen=True)
class _Stage:
    """One statement-sized group of consecutive ops. ``kind`` is
    ``"collect"`` (filters then maps: one comprehension or ``for`` loop),
    ``"order"`` (one order op) or ``"slice"`` (consecutive slice ops)."""

    kind: str
    ops: tuple[AtomicOp, ...]

    @property
    def filters(self) -> tuple[AtomicOp, ...]:
        return tuple(op for op in self.ops if op.category == "filter")

    @property
    def maps(self) -> tuple[AtomicOp, ...]:
        return tuple(op for op in self.ops if op.category == "map")


def _stages(ast: SemanticAST, fuse: bool = True) -> list[_Stage]:
    """``ast.ops`` grouped into stages, in op order (module docstring).

    With ``fuse``, a collect stage takes a run of filters followed by a run
    of maps (it filters on the incoming values and maps the survivors,
    exactly filters-then-maps), and a slice stage takes a run of slices.
    Without it every op is a stage of its own."""
    out: list[_Stage] = []
    ops = ast.ops
    i = 0
    while i < len(ops):
        op = ops[i]
        if op.category in ("filter", "map"):
            j = i + 1
            if fuse:
                if op.category == "filter":
                    while j < len(ops) and ops[j].category == "filter":
                        j += 1
                while j < len(ops) and ops[j].category == "map":
                    j += 1
            out.append(_Stage("collect", ops[i:j]))
        elif op.category == "slice":
            j = i + 1
            while fuse and j < len(ops) and ops[j].category == "slice":
                j += 1
            out.append(_Stage("slice", ops[i:j]))
        else:
            j = i + 1
            out.append(_Stage("order", ops[i:j]))
        i = j
    return out


def _comprehension(stage: _Stage, style: CodeStyle, source: _Expr) -> _Expr:
    """``[<element> for <x> in <source> if <cond>]``."""
    variable = style.names.element
    element = element_expr(stage.maps, variable)
    text = f"[{element.text} for {variable} in {source.text}"
    condition = condition_text(stage.filters, variable)
    if condition:
        text += f" if {condition}"
    return _Expr(text + "]", PREC_ATOM)


def _stage_expr(stage: _Stage, style: CodeStyle, source: _Expr) -> _Expr:
    """``stage`` applied to ``source`` as one expression."""
    if stage.kind == "collect":
        return _comprehension(stage, style, source)
    if stage.kind == "order":
        return _order_expr(source, stage.ops[0].name, style.order_spelling)
    return _slice_expr(source, stage.ops)


def single_expression(ast: SemanticAST, style: CodeStyle) -> _Expr:
    """The whole pipeline as one expression (the ``TEMP_NONE`` body)."""
    expr = _Expr("xs", PREC_ATOM)
    for stage in _stages(ast):
        expr = _stage_expr(stage, style, expr)
    return expr


# ---------------------------------------------------------------------------
# Comments (see the module docstring for why they are category-level)
# ---------------------------------------------------------------------------

CATEGORY_LABELS = {"filter": "抽出", "map": "変換", "order": "並べ替え", "slice": "切り出し"}

COMMENT_FILTER = "# 条件に合う要素だけを残す"
COMMENT_MAP = "# 各要素を変換する"
COMMENT_FILTER_MAP = "# 条件に合う要素を変換して集める"
COMMENT_COPY = "# 元のリストを複製する"
COMMENT_ORDER = "# 並べ替える"
COMMENT_SLICE = "# 必要な範囲を取り出す"


def _overview_comment(ast: SemanticAST) -> str:
    """The single comment a one-expression body can carry: the category of
    every op, in execution order."""
    return "# " + "→".join(CATEGORY_LABELS[c] for c in ast.categories()) + "の順に処理する"


def _stage_comment(stage: _Stage) -> str:
    if stage.kind == "order":
        return COMMENT_ORDER
    if stage.kind == "slice":
        return COMMENT_SLICE
    if stage.filters and stage.maps:
        return COMMENT_FILTER_MAP
    if stage.filters:
        return COMMENT_FILTER
    return COMMENT_MAP


# ---------------------------------------------------------------------------
# Statement bodies
# ---------------------------------------------------------------------------


class _Body:
    """The indented statements of ``solve``, with the comment axis applied."""

    def __init__(self, style: CodeStyle) -> None:
        self.style = style
        self.lines: list[str] = []
        self.declared: set[str] = set()

    def comment(self, text: str) -> None:
        if self.style.comments:
            self.lines.append(text)

    def line(self, text: str) -> None:
        self.lines.append(text)

    def assign(self, variable: str, text: str) -> None:
        """``variable = text``, with the list annotation on the variable's
        first assignment."""
        target = variable
        if variable not in self.declared:
            self.declared.add(variable)
            if self.style.annotations:
                target = f"{variable}{LIST_ANNOTATION}"
        self.line(f"{target} = {text}")

    def render(self) -> str:
        return "".join(f"{INDENT}{line}\n" for line in self.lines)


# Index into ``NameScheme.stages`` per stage kind (a collect stage without
# filters is a map stage).
_STAGE_NAME_INDEX = {"filter": 0, "map": 1, "order": 2, "slice": 3}


class _Namer:
    """Target variable per stage. ``TEMP_STAGED`` gives each stage its own
    name (a second stage of the same kind gets ``_2``, ``_3``); every other
    setting reuses one accumulator."""

    def __init__(self, style: CodeStyle) -> None:
        self.style = style
        self.used: dict[str, int] = {}

    def target(self, stage: _Stage) -> str:
        if self.style.temporaries != TEMP_STAGED:
            return self.style.names.result
        kind = stage.kind if stage.kind != "collect" else ("filter" if stage.filters else "map")
        base = self.style.names.stages[_STAGE_NAME_INDEX[kind]]
        self.used[base] = self.used.get(base, 0) + 1
        count = self.used[base]
        return base if count == 1 else f"{base}_{count}"


def _comprehension_body(ast: SemanticAST, style: CodeStyle) -> _Body:
    body = _Body(style)
    namer = _Namer(style)
    current = _Expr("xs", PREC_ATOM)
    # staged: one statement per op -- the point of the staged style is one
    # statement per pipeline step.
    for stage in _stages(ast, fuse=style.temporaries != TEMP_STAGED):
        body.comment(_stage_comment(stage))
        target = namer.target(stage)
        body.assign(target, _stage_expr(stage, style, current).text)
        current = _Expr(target, PREC_ATOM)
    body.line(f"return {current.text}")
    return body


def _order_statements(variable: str, name: str, spelling: str) -> list[str]:
    """Order op ``name`` as in-place statements on ``variable`` -- the loop
    form's spelling, and the half of homework.md's 「``reverse=True``と逆順操
    作」 axis that the expression form cannot show."""
    if name == "ascending":
        return [f"{variable}.sort()"]
    if name == "descending":
        return [f"{variable}.sort(reverse=True)"]
    if name == "reverse":
        if spelling == ORDER_EXPLICIT:
            return [f"{variable} = {variable}[::-1]"]
        return [f"{variable}.reverse()"]
    raise CodeGenError(f"unknown order op: {name!r}")


def _loop_body(ast: SemanticAST, style: CodeStyle) -> _Body:
    body = _Body(style)
    staged = style.temporaries == TEMP_STAGED
    namer = _Namer(style)
    variable = style.names.element
    stages = _stages(ast)

    # When the pipeline does not start with a loop, the list is copied first
    # (a copy, not an alias: solve must never hand back or mutate ``xs``, and
    # the order statements below sort in place).
    current = "xs"
    if stages[0].kind != "collect":
        current = style.names.result  # a plain copy belongs to no stage
        body.comment(COMMENT_COPY)
        body.assign(current, "list(xs)")

    for stage in stages:
        body.comment(_stage_comment(stage))
        if stage.kind == "collect":
            target = namer.target(stage)
            # a loop cannot fill the list it iterates over, so a reused
            # accumulator is rebuilt in a buffer and rebound afterwards
            fill = style.names.buffer if target == current else target
            body.assign(fill, "[]")
            body.line(f"for {variable} in {current}:")
            element = element_expr(stage.maps, variable)
            condition = condition_text(stage.filters, variable)
            if condition:
                body.line(f"{INDENT}if {condition}:")
                body.line(f"{INDENT}{INDENT}{fill}.append({element.text})")
            else:
                body.line(f"{INDENT}{fill}.append({element.text})")
            if fill != target:
                body.assign(target, fill)
            current = target
        elif stage.kind == "order" and not staged:
            for line in _order_statements(current, stage.ops[0].name, style.order_spelling):
                body.line(line)
        else:
            target = namer.target(stage)
            body.assign(target, _stage_expr(stage, style, _Expr(current)).text)
            current = target

    body.line(f"return {current}")
    return body


def render(ast: SemanticAST, style: CodeStyle) -> str:
    """The ``solve(xs, k)`` source for ``ast`` in ``style``.

    Semantics are the style's only invariant: every style renders the same
    ops in the same order, so any two renderings of one semantic AST agree
    with ``reference_interpreter.interpret`` on every input
    (``code_verifier.py`` checks exactly that), and no rendering of one AST
    equals any rendering of another.
    """
    signature = SIGNATURE_ANNOTATED if style.annotations else SIGNATURE_BARE
    if style.form == FORM_LOOP:
        body = _loop_body(ast, style)
    elif style.form == FORM_COMPREHENSION:
        if style.temporaries == TEMP_NONE:
            body = _Body(style)
            body.comment(_overview_comment(ast))
            body.line(f"return {single_expression(ast, style).text}")
        else:
            body = _comprehension_body(ast, style)
    else:
        raise CodeGenError(f"unknown code form: {style.form!r}")

    return f"{signature}\n{body.render()}"


# ---------------------------------------------------------------------------
# Variants
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CodeVariant:
    """One rendering: the style that produced it and the source it produced."""

    style: CodeStyle
    code: str

    @property
    def code_sha256(self) -> str:
        """Identity of the source text, for homework.md's 「完全重複コードで
        ない」 selection rule."""
        return hashlib.sha256(self.code.encode("utf-8")).hexdigest()

    def to_dict(self) -> dict:
        return {"code_style": self.style.name, "code": self.code, "code_sha256": self.code_sha256}


def variants(
    ast: SemanticAST,
    n: Optional[int] = None,
    catalogue: Sequence[CodeStyle] = STYLES,
) -> list[CodeVariant]:
    """Up to ``n`` distinct renderings of ``ast`` (all applicable styles when
    ``n`` is ``None``).

    Styles are chosen by ``code_styles.select_styles`` (tag-gated, then
    rotated per AST so the catalogue is used evenly). Renderings that come
    out byte-identical are collapsed to the first style that produced them:
    the tag gate already removes the cases where that is expected, so a
    collapse here means two catalogue entries genuinely coincide on this AST
    and the corpus should not carry the same source twice under two
    ``code_style`` labels.
    """
    out: list[CodeVariant] = []
    seen: set[str] = set()
    for style in select_styles(ast, n, catalogue):
        code = render(ast, style)
        if code in seen:
            continue
        seen.add(code)
        out.append(CodeVariant(style=style, code=code))
    return out


# ---------------------------------------------------------------------------
# Saving the generated code
# ---------------------------------------------------------------------------


def code_record(
    ast: SemanticAST,
    generated: Sequence[CodeVariant],
    spec_id: Optional[str] = None,
    verifications: Optional[Sequence[dict]] = None,
) -> dict:
    """One JSONL record: the semantic AST and every rendering of it.

    Field names line up with homework.md's データレコード so these records
    join onto ``out/ast_{split}.jsonl`` (and onto
    ``out/instructions_{split}.jsonl``) by ``spec_id`` / ``semantic_hash``.
    homework.md's record carries a single ``reference_code`` + ``code_style``
    pair; here that is ``codes[0]`` (the catalogue's first applicable style),
    with the remaining equivalent renderings after it -- one record per
    semantic AST keeps the split boundary at the semantic AST, exactly as
    ``expressions_ja`` stores its instruction variants.
    """
    codes = [variant.to_dict() for variant in generated]
    if verifications is not None:
        if len(verifications) != len(codes):
            raise CodeGenError(
                f"got {len(verifications)} verification(s) for {len(codes)} rendering(s)"
            )
        for entry, verification in zip(codes, verifications):
            entry["verification"] = verification
    record: dict = {
        "semantic_ast": ast.to_dict(),
        "semantic_hash": ast.semantic_hash(),
        "codes": codes,
    }
    if spec_id is not None:
        record = {"spec_id": spec_id, **record}
    return record


def save_codes(records: Iterable[dict], path: Union[str, Path]) -> Path:
    """Write code records as JSONL (UTF-8, unescaped Japanese comments)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def load_codes(path: Union[str, Path]) -> list[dict]:
    """Read back what ``save_codes`` wrote."""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def render_from_record(record: dict) -> list[str]:
    """Re-derive a saved record's sources from ``(semantic_ast, code_style)``
    alone.

    The generator is deterministic, so a saved snippet that does not come
    back identical means the generator changed since it was written -- which
    is worth catching, because the stored code is what the model gets trained
    on. ``code_demo.py`` runs this over everything it writes.
    """
    ast = SemanticAST.from_dict(record["semantic_ast"])
    out: list[str] = []
    for entry in record["codes"]:
        style = STYLES_BY_NAME.get(entry["code_style"])
        if style is None:
            raise CodeGenError(f"unknown code_style in record: {entry['code_style']!r}")
        out.append(render(ast, style))
    return out
