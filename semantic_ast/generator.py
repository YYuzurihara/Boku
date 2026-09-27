"""Enumerate every valid ``SemanticAST`` in the Boku-nano DSL.

A semantic AST is an ordered sequence of 1-3 of the 24 atomic operations,
repetition allowed (schema.py, "1〜3個を組み合わせた問題"), so the space is

    length 1:  24
    length 2:  24 ** 2 =    576
    length 3:  24 ** 3 = 13,824
               ------------------
                         14,424   (``count_all()`` confirms this exactly)

Every sequence is its own AST: order and repetition are part of the
identity (schema.py, "Order is identity"), so nothing is collapsed.
"""

from __future__ import annotations

import itertools

from schema import ATOMIC_OPS, MAX_OPS, MIN_OPS, SemanticAST


def enumerate_all() -> list[SemanticAST]:
    """Return every valid ``SemanticAST``, shortest first, each length in
    ``ATOMIC_OPS`` order. Safe to call repeatedly -- pure enumeration, no
    randomness."""
    return [
        SemanticAST(ops)
        for length in range(MIN_OPS, MAX_OPS + 1)
        for ops in itertools.product(ATOMIC_OPS, repeat=length)
    ]


def count_all() -> int:
    return len(enumerate_all())


def label(ast: SemanticAST) -> dict:
    """Stratification label for one semantic AST: used by ``split.py`` to
    keep train/val/test proportional across problem characteristics
    (homework.md: "train,val,testへの分割と問題の特性に応じたラベル付与").

    The label is the *category sequence* (e.g. ``("filter", "map",
    "order")``): 4 + 16 + 64 = 84 labels, 3-1,000 ASTs each."""
    return {
        "num_ops": ast.num_ops(),
        "categories": ast.categories(),
    }
