"""Semantic AST schema for the Boku-nano ``solve(xs, k)`` problem domain.

homework.md calls this intermediate representation "意味AST" (a small DSL
between natural-language instructions and generated code):

    {
      "filter": ["even", "ge_k"],
      "map": ["mul_const", 2],
      "order": "ascending"
    }

Everything downstream -- the reference interpreter, the Japanese instruction
templates, the structural code generator, and train/val/test splitting --
is keyed off of this representation, so it is defined once here and
imported everywhere else.

Design note on "1〜3個を組み合わせた問題"
------------------------------------------
homework.md restricts problems to combining "1〜3個" of the operations
listed under 抽出/変換/並べ替え/切り出し. Taken completely literally this
is inconsistent with homework.md's own worked example, which combines four
atomic predicates/transforms (`ge_k`, `even`, `mul_const(2)`, `ascending`).
We resolve this the same way ``sandbox/ast_safety.py`` resolves its own
literal-reading tension: a semantic AST has (up to) four *category* slots --
``filters`` (抽出), ``map_ops`` (変換), ``order_op`` (並べ替え), ``slice_ops``
(切り出し) -- and "1〜3個の組み合わせ" is enforced as 1-3 *active category
slots*, matching the worked example (抽出+変換+並べ替え = 3 categories,
even though ``filters`` itself carries two AND'd predicates). Within the
``filters`` slot we still cap at 2 predicates (matching the worked example)
and forbid combining two predicates from the same mutually-exclusive group
(see ``FILTER_GROUPS``), so we never generate an always-empty filter like
"even and odd".

Pipeline order is fixed as filter -> map -> order -> slice. This is the
order the Japanese problem statements read in (抽出してから変換して並べ替
えて切り出す) and is what ``reference_interpreter.py`` implements.

Design note on chaining within ``map_ops`` / ``slice_ops``
------------------------------------------------------------
homework.md's データ規模 table asks for 30,000-100,000 *distinct* semantic
ASTs, but the closed vocabulary above (10 filter predicates, 8 map choices
with ``mul_const``'s constant fixed to homework.md's literal ``{2, 3}``
example, 3 order ops, 3 slice ops, 1-3 active categories) only enumerates
to ~3,383 structurally distinct points -- about 9x short. Rather than
inventing new atomic operations outside homework.md's explicit lists (which
would also grow the tokenizer's vocabulary), or widening ``mul_const``
beyond its literal "2倍、3倍する" example, we widen the one dimension
already implied by chaining several operations together: ``map_ops`` and
``slice_ops`` are each a short *ordered sequence* (0-2 distinct op
**types**) instead of a single optional op, e.g. "kを加えてから2倍する"
(``add_k`` then ``mul_const(2)``) or "先頭からk個を1個おきに取得する"
(``take_first_k`` then ``step_2``). Order matters (it's a pipeline), and
each op *type* may appear at most once per sequence -- e.g. two
``mul_const`` entries are rejected, since ``mul_const(2)`` then
``mul_const(3)`` is just a redundant spelling of ``mul_const(6)`` and would
silently duplicate another semantic AST's meaning. ``order_op`` is left a
single choice: composing two sorts/reverses collapses to one of them, so
chaining there would only manufacture fake variety.

This raises ``generator.enumerate_all()`` from 3,383 to 40,589 -- within
homework.md's stated 30,000-100,000 range and ~12x the previous count,
while ``mul_const``'s constant stays exactly homework.md's literal
``{2, 3}``. See ``generator.py``'s module docstring for the exact
combinatorics.
"""

from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from typing import Optional

# ---------------------------------------------------------------------------
# Problem domain constants (homework.md "対象とする問題")
# ---------------------------------------------------------------------------

XS_MIN_LEN = 0
XS_MAX_LEN = 20
ELEMENT_MIN = -100
ELEMENT_MAX = 100
K_MIN = 1
K_MAX = 10

# ---------------------------------------------------------------------------
# Atomic operation vocabulary (homework.md "対象とするプログラミング上の操作")
# ---------------------------------------------------------------------------

# Filter predicates, grouped by mutual exclusivity: at most one predicate per
# group may appear in the same semantic AST (picking two from the same group
# is either redundant or contradictory, e.g. {even, odd} is always empty).
FILTER_GROUPS: dict[str, tuple[str, ...]] = {
    "parity": ("even", "odd"),
    "sign": ("positive", "negative", "zero"),
    "k_compare": ("gt_k", "ge_k", "lt_k", "le_k"),
    "k_multiple": ("multiple_of_k",),
}
ALL_FILTER_OPS: tuple[str, ...] = tuple(
    op for ops in FILTER_GROUPS.values() for op in ops
)
FILTER_OP_TO_GROUP: dict[str, str] = {
    op: group for group, ops in FILTER_GROUPS.items() for op in ops
}
MAX_FILTER_PREDICATES = 2

# Map (transform) operations. Most take no extra argument (they act on k or
# are fixed); "mul_const" additionally needs an integer argument -- kept to
# exactly homework.md's literal "2倍、3倍する" example rather than widened
# (see schema.py's module docstring "chaining" design note).
MAP_OPS_NO_ARG: tuple[str, ...] = ("add_k", "sub_k", "mul_k", "negate", "abs", "square")
MAP_CONST_ARGS: tuple[int, ...] = (2, 3)
ALL_MAP_OP_NAMES: tuple[str, ...] = MAP_OPS_NO_ARG + ("mul_const",)
MAX_MAP_OPS = 2

# Ordering operations. "descending" sorts; "reverse" merely reverses
# whatever order the elements are already in (distinct operations per
# homework.md's separate 降順/逆順 bullets).
ORDER_OPS: tuple[str, ...] = ("ascending", "descending", "reverse")

# Slicing operations. take_first_k / take_last_k use k implicitly;
# step_2 implements "1個おきに取得する".
SLICE_OPS: tuple[str, ...] = ("take_first_k", "take_last_k", "step_2")
MAX_SLICE_OPS = 2

MapOp = tuple[str, Optional[int]]


class SemanticASTError(ValueError):
    """Raised when a semantic AST fails schema validation."""


@dataclass(frozen=True)
class SemanticAST:
    """A single point in the (filter, map, order, slice) DSL.

    ``filters`` is an AND-combined tuple of 0-2 predicate names (order does
    not matter -- it's a set).
    ``map_ops`` is an ordered sequence of 0-``MAX_MAP_OPS`` ``(name, arg)``
    pairs (``arg`` is ``None`` except for ``mul_const``); order matters, and
    each op *name* may appear at most once.
    ``order_op`` is ``None`` or one atomic op name.
    ``slice_ops`` is an ordered sequence of 0-``MAX_SLICE_OPS`` op names;
    order matters, and each name may appear at most once.
    """

    filters: tuple[str, ...] = ()
    map_ops: tuple[MapOp, ...] = ()
    order_op: Optional[str] = None
    slice_ops: tuple[str, ...] = ()

    def __post_init__(self) -> None:
        validate(self)

    # -- category / label helpers -----------------------------------------

    def active_categories(self) -> tuple[str, ...]:
        cats = []
        if self.filters:
            cats.append("filter")
        if self.map_ops:
            cats.append("map")
        if self.order_op is not None:
            cats.append("order")
        if self.slice_ops:
            cats.append("slice")
        return tuple(cats)

    def num_categories(self) -> int:
        return len(self.active_categories())

    def op_tags(self) -> tuple[str, ...]:
        """Sorted, flattened list of every atomic op used, e.g.
        ``("filter:even", "filter:ge_k", "map:mul_const:2", "order:ascending")``.
        Used to balance per-operator frequency when sampling/capping.
        Pipeline position within ``map_ops``/``slice_ops`` is not encoded
        here (each op type appears at most once per sequence anyway)."""
        tags = [f"filter:{f}" for f in self.filters]
        for name, arg in self.map_ops:
            tags.append(f"map:{name}" if arg is None else f"map:{name}:{arg}")
        if self.order_op is not None:
            tags.append(f"order:{self.order_op}")
        for s in self.slice_ops:
            tags.append(f"slice:{s}")
        return tuple(sorted(tags))

    # -- (de)serialization ---------------------------------------------------

    def to_dict(self) -> dict:
        """Matches the shape of homework.md's worked example as closely as
        the schema allows (``filter``/``map``/``order``/``slice`` keys,
        omitted when inactive). ``map`` and ``slice`` are lists of ops in
        pipeline order -- e.g. ``"map": [["add_k"], ["mul_const", 2]]``."""
        d: dict = {}
        if self.filters:
            d["filter"] = list(self.filters)
        if self.map_ops:
            d["map"] = [
                [name] if arg is None else [name, arg] for name, arg in self.map_ops
            ]
        if self.order_op is not None:
            d["order"] = self.order_op
        if self.slice_ops:
            d["slice"] = list(self.slice_ops)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "SemanticAST":
        filters = tuple(d.get("filter", []))
        map_raw = d.get("map") or []
        map_ops = tuple(
            (item[0], item[1] if len(item) > 1 else None) for item in map_raw
        )
        order_op = d.get("order")
        slice_ops = tuple(d.get("slice") or [])
        return cls(filters=filters, map_ops=map_ops, order_op=order_op, slice_ops=slice_ops)

    def canonical_json(self) -> str:
        """JSON form used for hashing: filters sorted (AND is commutative,
        so {even, ge_k} and {ge_k, even} must hash identically), map/slice
        left in pipeline order (order changes the result), keys sorted, no
        incidental whitespace."""
        d = self.to_dict()
        if "filter" in d:
            d["filter"] = sorted(d["filter"])
        return json.dumps(d, sort_keys=True, separators=(",", ":"))

    def semantic_hash(self) -> str:
        """Stable identity used for dedup and train/val/test leakage checks."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def validate(ast: SemanticAST) -> None:
    """Raise SemanticASTError if ``ast`` violates the schema.

    Called automatically from ``SemanticAST.__post_init__`` so an invalid
    instance can never exist.
    """
    if len(ast.filters) > MAX_FILTER_PREDICATES:
        raise SemanticASTError(
            f"at most {MAX_FILTER_PREDICATES} filter predicates allowed, got {len(ast.filters)}"
        )
    seen_groups: set[str] = set()
    for f in ast.filters:
        if f not in FILTER_OP_TO_GROUP:
            raise SemanticASTError(f"unknown filter op: {f!r}")
        group = FILTER_OP_TO_GROUP[f]
        if group in seen_groups:
            raise SemanticASTError(
                f"filters combine two predicates from the same group {group!r}: {ast.filters}"
            )
        seen_groups.add(group)
    if len(set(ast.filters)) != len(ast.filters):
        raise SemanticASTError(f"duplicate filter predicate in {ast.filters}")

    if len(ast.map_ops) > MAX_MAP_OPS:
        raise SemanticASTError(f"at most {MAX_MAP_OPS} map ops allowed, got {len(ast.map_ops)}")
    seen_map_names: set[str] = set()
    for name, arg in ast.map_ops:
        if name in MAP_OPS_NO_ARG:
            if arg is not None:
                raise SemanticASTError(f"map op {name!r} takes no argument, got {arg!r}")
        elif name == "mul_const":
            if arg not in MAP_CONST_ARGS:
                raise SemanticASTError(f"mul_const argument must be one of {MAP_CONST_ARGS}, got {arg!r}")
        else:
            raise SemanticASTError(f"unknown map op: {name!r}")
        if name in seen_map_names:
            raise SemanticASTError(f"map op {name!r} appears more than once in {ast.map_ops}")
        seen_map_names.add(name)

    if ast.order_op is not None and ast.order_op not in ORDER_OPS:
        raise SemanticASTError(f"unknown order op: {ast.order_op!r}")

    if len(ast.slice_ops) > MAX_SLICE_OPS:
        raise SemanticASTError(f"at most {MAX_SLICE_OPS} slice ops allowed, got {len(ast.slice_ops)}")
    seen_slice_names: set[str] = set()
    for s in ast.slice_ops:
        if s not in SLICE_OPS:
            raise SemanticASTError(f"unknown slice op: {s!r}")
        if s in seen_slice_names:
            raise SemanticASTError(f"slice op {s!r} appears more than once in {ast.slice_ops}")
        seen_slice_names.add(s)

    num_categories = ast.num_categories()
    if not (1 <= num_categories <= 3):
        raise SemanticASTError(
            f"expected 1-3 active categories (filter/map/order/slice), got {num_categories}: {ast.to_dict()}"
        )
