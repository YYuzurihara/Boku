"""Enumerate every valid ``SemanticAST`` in the Boku-nano DSL.

homework.md's データ規模 table asks for 30,000-100,000 *distinct* semantic
ASTs. The closed atomic-operation vocabulary alone (10 filter predicates, 8
map choices with ``mul_const`` fixed to homework.md's literal ``{2, 3}``
example, 3 order ops, 3 slice op types, 1-3 active categories) only reaches
~3,383 structurally distinct points. To close that gap without inventing
operations outside homework.md's explicit lists, or widening ``mul_const``
beyond its literal "2倍、3倍する" example, ``map_ops`` and ``slice_ops`` are
each an ordered sequence of up to ``MAX_MAP_OPS`` / ``MAX_SLICE_OPS``
distinct op types (see schema.py's module docstring, "Design note on
chaining"). This raises the total to:

    filters:  46  (0, 1, or 2 AND'd predicates from different groups)
    map_ops:  63  (0, 1, or 2 ordered distinct-type ops; mul_const x2 consts)
    order:     4  (none, or one of 3 ops -- no chaining, see schema.py)
    slice:    10  (0, 1, or 2 ordered distinct-type ops)

    46 * 63 * 4 * 10 = 115,920 raw combinations, of which 40,589 keep to
    1-3 active categories (``count_all()`` confirms this exactly).
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator

from schema import (
    ALL_FILTER_OPS,
    ALL_MAP_OP_NAMES,
    MAP_CONST_ARGS,
    MAX_FILTER_PREDICATES,
    MAX_MAP_OPS,
    MAX_SLICE_OPS,
    ORDER_OPS,
    SLICE_OPS,
    MapOp,
    SemanticAST,
    SemanticASTError,
    FILTER_OP_TO_GROUP,
)


def _valid_filter_combos() -> Iterator[tuple[str, ...]]:
    """Every filter-predicate subset of size 0..MAX_FILTER_PREDICATES with
    no two predicates from the same mutually-exclusive group."""
    yield ()
    for size in range(1, MAX_FILTER_PREDICATES + 1):
        for combo in itertools.combinations(ALL_FILTER_OPS, size):
            groups = [FILTER_OP_TO_GROUP[op] for op in combo]
            if len(set(groups)) == len(groups):
                yield combo


def _map_atom_variants(name: str) -> list[MapOp]:
    """Concrete ``(name, arg)`` variants for one map op type -- several for
    ``mul_const`` (one per constant), exactly one for every other type."""
    if name == "mul_const":
        return [("mul_const", c) for c in MAP_CONST_ARGS]
    return [(name, None)]


def _all_map_op_sequences() -> Iterator[tuple[MapOp, ...]]:
    """Every ordered sequence of 0..MAX_MAP_OPS map ops, using each op
    *type* at most once per sequence (see schema.py: stacking the same type
    twice, e.g. two ``mul_const``s, just redundantly spells out another
    single op)."""
    yield ()
    for size in range(1, MAX_MAP_OPS + 1):
        for names in itertools.permutations(ALL_MAP_OP_NAMES, size):
            for combo in itertools.product(*(_map_atom_variants(n) for n in names)):
                yield combo


def _all_order_ops() -> Iterator[str | None]:
    yield None
    yield from ORDER_OPS


def _all_slice_op_sequences() -> Iterator[tuple[str, ...]]:
    """Every ordered sequence of 0..MAX_SLICE_OPS slice ops, each type used
    at most once per sequence (order matters: "先頭からk個を1個おきに取得
    する" differs from "1個おきに取得してから先頭k個")."""
    yield ()
    for size in range(1, MAX_SLICE_OPS + 1):
        yield from itertools.permutations(SLICE_OPS, size)


def enumerate_all() -> list[SemanticAST]:
    """Return every valid ``SemanticAST`` (1-3 active categories), in a
    deterministic order. Safe to call repeatedly -- pure enumeration, no
    randomness."""
    out: list[SemanticAST] = []
    for filters in _valid_filter_combos():
        for map_ops in _all_map_op_sequences():
            for order_op in _all_order_ops():
                for slice_ops in _all_slice_op_sequences():
                    try:
                        ast = SemanticAST(
                            filters=filters,
                            map_ops=map_ops,
                            order_op=order_op,
                            slice_ops=slice_ops,
                        )
                    except SemanticASTError:
                        continue  # e.g. 0 or 4 active categories
                    out.append(ast)
    return out


def count_all() -> int:
    return len(enumerate_all())


def label(ast: SemanticAST) -> dict:
    """Stratification label for one semantic AST: used by ``split.py`` to
    keep train/val/test proportional across problem characteristics
    (homework.md: "train,val,testへの分割と問題の特性に応じたラベル付与"),
    and by ``cap_per_label`` to bound how many examples share a
    characteristic (homework.md: "均等抽出のためにラベルごとに上限")."""
    return {
        "num_categories": ast.num_categories(),
        "num_filters": len(ast.filters),
        "map_ops": tuple(name for name, _ in ast.map_ops),
        "order_op": ast.order_op,
        "slice_ops": ast.slice_ops,
    }
