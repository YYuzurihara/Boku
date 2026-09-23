"""Render a ``SemanticAST`` into Python source, once per ``CodeStyle``
(homework.md 「コードの構造的変換」: 「同じ意味ASTから複数の等価コードを生成
する」).

This is the second of homework.md's "独立した二つのプログラム": the first is
``reference_interpreter.py``, which computes the answer directly from the
semantic AST, and this one emits the ``solve(xs, k)`` source that the model
is trained to produce. The two are written independently on purpose -- they
are cross-checked against each other in ``code_verifier.py``, which is what
turns "the generator has a bug" into a test failure instead of into 40,589
subtly wrong training examples.

Everything here is rule-based, as homework.md requires (「正解の意味構造、コー
ド、テストはルールベースで作成し、教師は自然言語（日本語）表現を増やす役割に
限定する」): the teacher model never sees a line of this.

Pipeline order is the schema's: filter -> map -> order -> slice. What the
styles vary is *how* that pipeline is spelled, never what it computes.

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
    COND_SWAPPED,
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
from schema import MapOp, SemanticAST  # noqa: E402

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
        return _Expr(f"-{expr.wrapped(PREC_UNARY)}", PREC_UNARY)
    if name == "abs":
        return _Expr(f"abs({expr.text})", PREC_ATOM)
    if name == "square":
        # ``**`` binds tighter than unary minus on its left operand, so
        # anything but an atom has to be parenthesised: (-x) ** 2, not -x ** 2.
        return _Expr(f"{expr.wrapped(PREC_ATOM)} ** 2", PREC_POW)
    raise CodeGenError(f"unknown map op: {name!r}")


def element_expr(map_ops: Sequence[MapOp], variable: str) -> _Expr:
    """The element expression of a comprehension / ``append`` call: every map
    operation applied to ``variable`` in pipeline order."""
    expr = _Expr(variable, PREC_ATOM)
    for name, arg in map_ops:
        expr = _apply_map(expr, name, arg)
    return expr


def condition_text(ast: SemanticAST, style: CodeStyle, variable: str) -> str:
    """The ``if`` condition of a comprehension / loop body, or ``""`` when the
    AST has no filter.

    ``and`` is commutative and every predicate here is side-effect free and
    total, so the 条件式の順序変更 axis can reverse the order without changing
    the result (``x % k == 0`` is safe for the same reason the interpreter is:
    ``k`` is contractually 1-10, never 0).
    """
    filters = tuple(ast.filters)
    if style.condition_order == COND_SWAPPED:
        filters = tuple(reversed(filters))
    parts = []
    for name in filters:
        template = FILTER_CONDITIONS.get(name)
        if template is None:
            raise CodeGenError(f"unknown filter op: {name!r}")
        parts.append(template.format(x=variable))
    return " and ".join(parts)


def _comprehension(ast: SemanticAST, style: CodeStyle, source: _Expr, *, with_filter: bool, with_map: bool) -> _Expr:
    """``[<element> for <x> in <source> if <cond>]``."""
    variable = style.names.element
    element = element_expr(ast.map_ops if with_map else (), variable)
    text = f"[{element.text} for {variable} in {source.text}"
    if with_filter:
        condition = condition_text(ast, style, variable)
        if condition:
            text += f" if {condition}"
    return _Expr(text + "]", PREC_ATOM)


def _order_expr(expr: _Expr, order_op: str, spelling: str) -> _Expr:
    """``order_op`` applied to ``expr`` as an expression (the functional
    spelling, used by the comprehension form and by staged variables)."""
    if order_op == "ascending":
        return _Expr(f"sorted({expr.text})", PREC_ATOM)
    if order_op == "descending":
        if spelling == ORDER_EXPLICIT:
            return _Expr(f"sorted({expr.text})[::-1]", PREC_ATOM)
        return _Expr(f"sorted({expr.text}, reverse=True)", PREC_ATOM)
    if order_op == "reverse":
        if spelling == ORDER_EXPLICIT:
            return _Expr(f"list(reversed({expr.text}))", PREC_ATOM)
        return _Expr(f"{expr.wrapped(PREC_ATOM)}[::-1]", PREC_ATOM)
    raise CodeGenError(f"unknown order op: {order_op!r}")


SLICE_SUBSCRIPTS: dict[str, str] = {
    "take_first_k": "[:k]",
    "take_last_k": "[-k:]",  # k >= 1 by schema, so this is never the empty [-0:]
    "step_2": "[::2]",
}


def _slice_expr(expr: _Expr, slice_ops: Sequence[str]) -> _Expr:
    """Every slice operation as a chain of subscripts, in pipeline order."""
    text = expr.wrapped(PREC_ATOM)
    for op in slice_ops:
        subscript = SLICE_SUBSCRIPTS.get(op)
        if subscript is None:
            raise CodeGenError(f"unknown slice op: {op!r}")
        text += subscript
    return _Expr(text, PREC_ATOM)


def single_expression(ast: SemanticAST, style: CodeStyle) -> _Expr:
    """The whole pipeline as one expression (the ``TEMP_NONE`` body)."""
    expr = _Expr("xs", PREC_ATOM)
    if ast.filters or ast.map_ops:
        expr = _comprehension(ast, style, expr, with_filter=True, with_map=True)
    if ast.order_op is not None:
        expr = _order_expr(expr, ast.order_op, style.order_spelling)
    if ast.slice_ops:
        expr = _slice_expr(expr, ast.slice_ops)
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
    """The single comment a one-expression body can carry: the pipeline's
    active categories, in order."""
    return "# " + "→".join(CATEGORY_LABELS[c] for c in ast.active_categories()) + "の順に処理する"


def _collect_comment(ast: SemanticAST) -> str:
    if ast.filters and ast.map_ops:
        return COMMENT_FILTER_MAP
    if ast.filters:
        return COMMENT_FILTER
    if ast.map_ops:
        return COMMENT_MAP
    return COMMENT_COPY


# ---------------------------------------------------------------------------
# Statement bodies
# ---------------------------------------------------------------------------


class _Body:
    """The indented statements of ``solve``, with the comment axis applied."""

    def __init__(self, style: CodeStyle) -> None:
        self.style = style
        self.lines: list[str] = []

    def comment(self, text: str) -> None:
        if self.style.comments:
            self.lines.append(text)

    def line(self, text: str) -> None:
        self.lines.append(text)

    def annotated(self, variable: str) -> str:
        """``variable`` with the list annotation, for a *first* assignment."""
        return f"{variable}{LIST_ANNOTATION}" if self.style.annotations else variable

    def render(self) -> str:
        return "".join(f"{INDENT}{line}\n" for line in self.lines)


def _stage_names(ast: SemanticAST, style: CodeStyle) -> dict[str, str]:
    """Variable name per pipeline category. ``TEMP_STAGED`` gives each
    category its own name; every other setting reuses one accumulator."""
    if style.temporaries == TEMP_STAGED:
        by_index = dict(zip(("filter", "map", "order", "slice"), style.names.stages))
        return {category: by_index[category] for category in ("filter", "map", "order", "slice")}
    return {category: style.names.result for category in ("filter", "map", "order", "slice")}


def _comprehension_body(ast: SemanticAST, style: CodeStyle) -> _Body:
    body = _Body(style)
    staged = style.temporaries == TEMP_STAGED
    names = _stage_names(ast, style)
    first_assignment = True

    def assign(variable: str, expr: _Expr) -> None:
        nonlocal first_assignment
        target = body.annotated(variable) if first_assignment else variable
        body.line(f"{target} = {expr.text}")
        first_assignment = False

    current = _Expr("xs", PREC_ATOM)
    if staged:
        # filter and map become separate comprehensions -- the point of the
        # staged style is one statement per pipeline stage.
        if ast.filters:
            body.comment(COMMENT_FILTER)
            assign(names["filter"], _comprehension(ast, style, current, with_filter=True, with_map=False))
            current = _Expr(names["filter"], PREC_ATOM)
        if ast.map_ops:
            body.comment(COMMENT_MAP)
            assign(names["map"], _comprehension(ast, style, current, with_filter=False, with_map=True))
            current = _Expr(names["map"], PREC_ATOM)
    elif ast.filters or ast.map_ops:
        body.comment(_collect_comment(ast))
        assign(names["filter"], _comprehension(ast, style, current, with_filter=True, with_map=True))
        current = _Expr(names["filter"], PREC_ATOM)

    if ast.order_op is not None:
        body.comment(COMMENT_ORDER)
        assign(names["order"], _order_expr(current, ast.order_op, style.order_spelling))
        current = _Expr(names["order"], PREC_ATOM)

    if ast.slice_ops:
        body.comment(COMMENT_SLICE)
        assign(names["slice"], _slice_expr(current, ast.slice_ops))
        current = _Expr(names["slice"], PREC_ATOM)

    body.line(f"return {current.text}")
    return body


def _order_statements(variable: str, order_op: str, spelling: str) -> list[str]:
    """``order_op`` as in-place statements on ``variable`` -- the loop form's
    spelling, and the half of homework.md's 「``reverse=True``と逆順操作」 axis
    that the expression form cannot show."""
    if order_op == "ascending":
        return [f"{variable}.sort()"]
    if order_op == "descending":
        if spelling == ORDER_EXPLICIT:
            return [f"{variable}.sort()", f"{variable}.reverse()"]
        return [f"{variable}.sort(reverse=True)"]
    if order_op == "reverse":
        if spelling == ORDER_EXPLICIT:
            return [f"{variable} = {variable}[::-1]"]
        return [f"{variable}.reverse()"]
    raise CodeGenError(f"unknown order op: {order_op!r}")


def _loop_body(ast: SemanticAST, style: CodeStyle) -> _Body:
    body = _Body(style)
    staged = style.temporaries == TEMP_STAGED
    names = _stage_names(ast, style)
    variable = style.names.element

    # The accumulator the loop fills. With neither filter nor map there is
    # nothing to loop over element by element, so the list is copied instead
    # (a copy, not an alias: solve must never hand back or mutate ``xs``).
    if ast.filters:
        collected = names["filter"]
    elif ast.map_ops:
        collected = names["map"]
    else:
        collected = style.names.result  # a plain copy belongs to no stage
    body.comment(_collect_comment(ast))
    if ast.filters or ast.map_ops:
        body.line(f"{body.annotated(collected)} = []")
        body.line(f"for {variable} in xs:")
        element = element_expr(ast.map_ops, variable)
        condition = condition_text(ast, style, variable)
        if condition:
            body.line(f"{INDENT}if {condition}:")
            body.line(f"{INDENT}{INDENT}{collected}.append({element.text})")
        else:
            body.line(f"{INDENT}{collected}.append({element.text})")
    else:
        body.line(f"{body.annotated(collected)} = list(xs)")
    current = collected

    if ast.order_op is not None:
        body.comment(COMMENT_ORDER)
        if staged:
            body.line(f"{names['order']} = {_order_expr(_Expr(current), ast.order_op, style.order_spelling).text}")
            current = names["order"]
        else:
            for line in _order_statements(current, ast.order_op, style.order_spelling):
                body.line(line)

    if ast.slice_ops:
        body.comment(COMMENT_SLICE)
        target = names["slice"] if staged else current
        body.line(f"{target} = {_slice_expr(_Expr(current), ast.slice_ops).text}")
        current = target

    body.line(f"return {current}")
    return body


def render(ast: SemanticAST, style: CodeStyle) -> str:
    """The ``solve(xs, k)`` source for ``ast`` in ``style``.

    Semantics are the style's only invariant: every style renders the same
    pipeline, so any two renderings of one semantic AST agree with
    ``reference_interpreter.interpret`` on every input (``code_verifier.py``
    checks exactly that).
    """
    if not ast.active_categories():  # pragma: no cover - schema forbids it
        raise CodeGenError(f"semantic AST has no active category: {ast.to_dict()}")

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
    join onto ``out/{train,val,test}.jsonl`` (and onto
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
