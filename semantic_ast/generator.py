"""Enumerate every valid ``SemanticAST`` in the Boku-nano DSL.

The combinatorial space of *structurally distinct* semantic ASTs is small
(a few thousand -- see ``count_all()``), because homework.md deliberately
keeps the operation vocabulary closed. Reaching the 30,000-100,000 target
in homework.md's "データ規模" table happens one level up the pipeline, by
pairing each structural semantic AST with several Japanese instruction
phrasings and several structurally-varied code renderings -- that is a
later task-list item and out of scope here. This module's job is just to
produce the complete, deduplicated set of DSL points those later stages
will draw from.
"""

from __future__ import annotations

import itertools
from collections.abc import Iterator

from schema import (
    ALL_FILTER_OPS,
    MAP_CONST_ARGS,
    MAP_OPS_NO_ARG,
    MAX_FILTER_PREDICATES,
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


def _all_map_ops() -> Iterator[MapOp | None]:
    yield None
    for name in MAP_OPS_NO_ARG:
        yield (name, None)
    for arg in MAP_CONST_ARGS:
        yield ("mul_const", arg)


def _all_order_ops() -> Iterator[str | None]:
    yield None
    yield from ORDER_OPS


def _all_slice_ops() -> Iterator[str | None]:
    yield None
    yield from SLICE_OPS


def enumerate_all() -> list[SemanticAST]:
    """Return every valid ``SemanticAST`` (1-3 active categories), in a
    deterministic order. Safe to call repeatedly -- pure enumeration, no
    randomness."""
    out: list[SemanticAST] = []
    for filters in _valid_filter_combos():
        for map_op in _all_map_ops():
            for order_op in _all_order_ops():
                for slice_op in _all_slice_ops():
                    try:
                        ast = SemanticAST(
                            filters=filters,
                            map_op=map_op,
                            order_op=order_op,
                            slice_op=slice_op,
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
    map_name = ast.map_op[0] if ast.map_op else None
    return {
        "num_categories": ast.num_categories(),
        "num_filters": len(ast.filters),
        "map_op": map_name,
        "order_op": ast.order_op,
        "slice_op": ast.slice_op,
    }
