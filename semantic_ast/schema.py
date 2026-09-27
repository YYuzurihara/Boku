"""Semantic AST schema for the Boku-nano ``solve(xs, k)`` problem domain.

homework.md calls this intermediate representation "意味AST" (a small DSL
between natural-language instructions and generated code). A semantic AST is
an **ordered sequence of 1-3 atomic operations**:

    {
      "ops": [["filter", "even"], ["map", "mul_const", 2], ["order", "ascending"]]
    }

Everything downstream -- the reference interpreter, the Japanese instruction
templates, the structural code generator, and train/val/test splitting --
is keyed off of this representation, so it is defined once here and
imported everywhere else.

Design note on "1〜3個を組み合わせた問題"
------------------------------------------
homework.md restricts problems to combining "1〜3個" of the operations listed
under 抽出/変換/並べ替え/切り出し. Those lists contain 24 atomic operations
(``ATOMIC_OPS``):

    抽出 (filter)  10  even odd gt_k ge_k lt_k le_k multiple_of_k positive negative zero
    変換 (map)      8  add_k sub_k mul_k negate abs square mul_const(2) mul_const(3)
    並べ替え (order) 3  ascending descending reverse
    切り出し (slice) 3  take_first_k take_last_k step_2

A semantic AST picks 1-3 of them **with repetition** and **in order**: the
same operation may occur more than once (``filter:even`` twice,
``order:reverse`` twice, ...), any category may follow any other, and the
list is executed left to right. The space is therefore

    24 + 24**2 + 24**3 = 14,424 semantic ASTs.

Order is identity
-----------------
Two ASTs that use the same atomic operations in a different order are
different ASTs -- different ``semantic_hash``, different Japanese
instruction, different code -- even when they happen to compute the same
function (``[filter:even, order:ascending]`` and ``[order:ascending,
filter:even]``), and a repeated operation is kept even when it is redundant
(``[filter:even, filter:even]``) or cancels out (``[order:reverse,
order:reverse]``). The sequence written in the instruction is the sequence
the code has to follow, so nothing is canonicalized here.
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

CATEGORIES: tuple[str, ...] = ("filter", "map", "order", "slice")

ALL_FILTER_OPS: tuple[str, ...] = (
    "even", "odd", "gt_k", "ge_k", "lt_k", "le_k", "multiple_of_k", "positive", "negative", "zero",
)

# Map (transform) operations. Most take no extra argument (they act on k or
# are fixed); "mul_const" additionally needs an integer argument -- kept to
# exactly homework.md's literal "2倍、3倍する" example.
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

MIN_OPS = 1
MAX_OPS = 3


class SemanticASTError(ValueError):
    """Raised when a semantic AST fails schema validation."""


@dataclass(frozen=True)
class AtomicOp:
    """One of the 24 atomic operations. ``arg`` is ``None`` except for
    ``map:mul_const``, whose constant is part of the operation's identity
    (``mul_const(2)`` and ``mul_const(3)`` are two atomic operations)."""

    category: str
    name: str
    arg: Optional[int] = None

    def __post_init__(self) -> None:
        _validate_op(self)

    @property
    def tag(self) -> str:
        """``"filter:even"``, ``"map:mul_const:2"``, ... -- the spelling used
        for labels, held-out pairs, style gating and dictionary keys."""
        base = f"{self.category}:{self.name}"
        return base if self.arg is None else f"{base}:{self.arg}"

    def to_json(self) -> list:
        return [self.category, self.name] if self.arg is None else [self.category, self.name, self.arg]

    @classmethod
    def from_json(cls, item: list) -> "AtomicOp":
        if not isinstance(item, (list, tuple)) or len(item) not in (2, 3):
            raise SemanticASTError(f"an op is [category, name] or [category, name, arg], got {item!r}")
        return cls(item[0], item[1], item[2] if len(item) == 3 else None)

    @classmethod
    def from_tag(cls, tag: str) -> "AtomicOp":
        parts = tag.split(":")
        if len(parts) == 3:
            return cls(parts[0], parts[1], int(parts[2]))
        if len(parts) == 2:
            return cls(parts[0], parts[1])
        raise SemanticASTError(f"malformed op tag: {tag!r}")


def _validate_op(op: AtomicOp) -> None:
    if op.category == "filter":
        known = op.name in ALL_FILTER_OPS
    elif op.category == "map":
        known = op.name in ALL_MAP_OP_NAMES
        if op.name == "mul_const":
            if op.arg not in MAP_CONST_ARGS:
                raise SemanticASTError(f"mul_const argument must be one of {MAP_CONST_ARGS}, got {op.arg!r}")
            return
    elif op.category == "order":
        known = op.name in ORDER_OPS
    elif op.category == "slice":
        known = op.name in SLICE_OPS
    else:
        raise SemanticASTError(f"unknown category: {op.category!r}")
    if not known:
        raise SemanticASTError(f"unknown {op.category} op: {op.name!r}")
    if op.arg is not None:
        raise SemanticASTError(f"{op.category} op {op.name!r} takes no argument, got {op.arg!r}")


ATOMIC_OPS: tuple[AtomicOp, ...] = (
    *(AtomicOp("filter", name) for name in ALL_FILTER_OPS),
    *(AtomicOp("map", name) for name in MAP_OPS_NO_ARG),
    *(AtomicOp("map", "mul_const", c) for c in MAP_CONST_ARGS),
    *(AtomicOp("order", name) for name in ORDER_OPS),
    *(AtomicOp("slice", name) for name in SLICE_OPS),
)
ATOMIC_OPS_BY_TAG: dict[str, AtomicOp] = {op.tag: op for op in ATOMIC_OPS}


@dataclass(frozen=True)
class SemanticAST:
    """An ordered sequence of ``MIN_OPS``-``MAX_OPS`` atomic operations,
    executed left to right. Repetition is allowed and order is part of the
    identity (module docstring)."""

    ops: tuple[AtomicOp, ...]

    def __post_init__(self) -> None:
        object.__setattr__(self, "ops", tuple(self.ops))
        validate(self)

    @classmethod
    def of(cls, *tags: str) -> "SemanticAST":
        """``SemanticAST.of("filter:even", "map:mul_const:2")``."""
        return cls(tuple(AtomicOp.from_tag(tag) for tag in tags))

    # -- helpers --------------------------------------------------------------

    def num_ops(self) -> int:
        return len(self.ops)

    def categories(self) -> tuple[str, ...]:
        """The category of every op, in execution order (repeats included)."""
        return tuple(op.category for op in self.ops)

    def tags(self) -> tuple[str, ...]:
        """Every op's tag, in execution order."""
        return tuple(op.tag for op in self.ops)

    def op_tags(self) -> tuple[str, ...]:
        """Sorted tags (a multiset, repeats kept). Order-free on purpose:
        used where only *which* operations occur matters -- held-out pairs,
        style gating, per-operator balance. Use ``tags()`` for the order."""
        return tuple(sorted(self.tags()))

    def has(self, category: str) -> bool:
        return category in self.categories()

    # -- (de)serialization ---------------------------------------------------

    def to_dict(self) -> dict:
        return {"ops": [op.to_json() for op in self.ops]}

    @classmethod
    def from_dict(cls, d: dict) -> "SemanticAST":
        if "ops" not in d:
            raise SemanticASTError(f"a semantic AST is {{\"ops\": [...]}}, got {d!r}")
        return cls(tuple(AtomicOp.from_json(item) for item in d["ops"]))

    def canonical_json(self) -> str:
        """JSON form used for hashing: the op list in execution order (order
        is identity, so nothing is sorted), no incidental whitespace."""
        return json.dumps(self.to_dict(), sort_keys=True, separators=(",", ":"))

    def semantic_hash(self) -> str:
        """Stable identity used for dedup and train/val/test leakage checks."""
        return hashlib.sha256(self.canonical_json().encode("utf-8")).hexdigest()


def validate(ast: SemanticAST) -> None:
    """Raise SemanticASTError if ``ast`` violates the schema.

    Called automatically from ``SemanticAST.__post_init__`` so an invalid
    instance can never exist.
    """
    if not (MIN_OPS <= len(ast.ops) <= MAX_OPS):
        raise SemanticASTError(f"expected {MIN_OPS}-{MAX_OPS} atomic ops, got {len(ast.ops)}")
    for op in ast.ops:
        if not isinstance(op, AtomicOp):
            raise SemanticASTError(f"expected AtomicOp, got {op!r}")
