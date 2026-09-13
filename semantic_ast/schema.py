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
``filters`` (抽出), ``map_op`` (変換), ``order_op`` (並べ替え), ``slice_op``
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
# are fixed); "mul_const" additionally needs an integer argument distinct
# from k ("2倍、3倍する" in homework.md).
MAP_OPS_NO_ARG: tuple[str, ...] = ("add_k", "sub_k", "mul_k", "negate", "abs", "square")
MAP_CONST_ARGS: tuple[int, ...] = (2, 3)
ALL_MAP_OP_NAMES: tuple[str, ...] = MAP_OPS_NO_ARG + ("mul_const",)

# Ordering operations. "descending" sorts; "reverse" merely reverses
# whatever order the elements are already in (distinct operations per
# homework.md's separate 降順/逆順 bullets).
ORDER_OPS: tuple[str, ...] = ("ascending", "descending", "reverse")

# Slicing operations. take_first_k / take_last_k use k implicitly;
# step_2 implements "1個おきに取得する".
SLICE_OPS: tuple[str, ...] = ("take_first_k", "take_last_k", "step_2")

MapOp = tuple[str, Optional[int]]


class SemanticASTError(ValueError):
    """Raised when a semantic AST fails schema validation."""


@dataclass(frozen=True)
class SemanticAST:
    """A single point in the (filter, map, order, slice) DSL.

    ``filters`` is an AND-combined tuple of 0-2 predicate names.
    ``map_op`` is ``None`` or ``(name, arg)`` where ``arg`` is ``None``
    except for ``mul_const``.
    ``order_op`` / ``slice_op`` are ``None`` or one atomic op name.
    """

    filters: tuple[str, ...] = ()
    map_op: Optional[MapOp] = None
    order_op: Optional[str] = None
    slice_op: Optional[str] = None

    def __post_init__(self) -> None:
        validate(self)

    # -- category / label helpers -----------------------------------------

    def active_categories(self) -> tuple[str, ...]:
        cats = []
        if self.filters:
            cats.append("filter")
        if self.map_op is not None:
            cats.append("map")
        if self.order_op is not None:
            cats.append("order")
        if self.slice_op is not None:
            cats.append("slice")
        return tuple(cats)

    def num_categories(self) -> int:
        return len(self.active_categories())

    def op_tags(self) -> tuple[str, ...]:
        """Sorted, flattened list of every atomic op used, e.g.
        ``("filter:even", "filter:ge_k", "map:mul_const:2", "order:ascending")``.
        Used to balance per-operator frequency when sampling/capping."""
        tags = [f"filter:{f}" for f in self.filters]
        if self.map_op is not None:
            name, arg = self.map_op
            tags.append(f"map:{name}" if arg is None else f"map:{name}:{arg}")
        if self.order_op is not None:
            tags.append(f"order:{self.order_op}")
        if self.slice_op is not None:
            tags.append(f"slice:{self.slice_op}")
        return tuple(sorted(tags))

    # -- (de)serialization ---------------------------------------------------

    def to_dict(self) -> dict:
        """Matches the shape of homework.md's worked example as closely as
        the schema allows (``filter``/``map``/``order``/``slice`` keys,
        omitted when inactive)."""
        d: dict = {}
        if self.filters:
            d["filter"] = list(self.filters)
        if self.map_op is not None:
            name, arg = self.map_op
            d["map"] = [name] if arg is None else [name, arg]
        if self.order_op is not None:
            d["order"] = self.order_op
        if self.slice_op is not None:
            d["slice"] = [self.slice_op]
        return d

    @classmethod
    def from_dict(cls, d: dict) -> "SemanticAST":
        filters = tuple(d.get("filter", []))
        map_raw = d.get("map")
        map_op: Optional[MapOp] = None
        if map_raw is not None:
            map_op = (map_raw[0], map_raw[1] if len(map_raw) > 1 else None)
        order_op = d.get("order")
        slice_raw = d.get("slice")
        slice_op = slice_raw[0] if slice_raw else None
        return cls(filters=filters, map_op=map_op, order_op=order_op, slice_op=slice_op)

    def canonical_json(self) -> str:
        """JSON form used for hashing: filters sorted (AND is commutative,
        so {even, ge_k} and {ge_k, even} must hash identically), keys
        sorted, no incidental whitespace."""
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

    if ast.map_op is not None:
        name, arg = ast.map_op
        if name in MAP_OPS_NO_ARG:
            if arg is not None:
                raise SemanticASTError(f"map op {name!r} takes no argument, got {arg!r}")
        elif name == "mul_const":
            if arg not in MAP_CONST_ARGS:
                raise SemanticASTError(f"mul_const argument must be one of {MAP_CONST_ARGS}, got {arg!r}")
        else:
            raise SemanticASTError(f"unknown map op: {name!r}")

    if ast.order_op is not None and ast.order_op not in ORDER_OPS:
        raise SemanticASTError(f"unknown order op: {ast.order_op!r}")

    if ast.slice_op is not None and ast.slice_op not in SLICE_OPS:
        raise SemanticASTError(f"unknown slice op: {ast.slice_op!r}")

    num_categories = ast.num_categories()
    if not (1 <= num_categories <= 3):
        raise SemanticASTError(
            f"expected 1-3 active categories (filter/map/order/slice), got {num_categories}: {ast.to_dict()}"
        )
