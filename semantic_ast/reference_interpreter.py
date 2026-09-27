"""Reference interpreter: executes a ``SemanticAST`` directly against
``(xs, k)``, without going through any generated Python code.

This is the "正解を計算する参照インタプリタ" from homework.md's データ生成
section. It is the ground truth used to:

  * generate ``expected`` outputs for test cases (``testcases.py``);
  * cross-check the structural code generator's output once it exists
    (homework.md: "両者の出力をランダムテストで比較する");
  * judge model-generated code at evaluation time (pass@1 / pass@5).

The atomic operations run one at a time, in ``ast.ops`` order.
"""

from __future__ import annotations

from collections.abc import Sequence

from schema import AtomicOp, SemanticAST, validate

_FILTER_FUNCS = {
    "even": lambda x, k: x % 2 == 0,
    "odd": lambda x, k: x % 2 != 0,
    "gt_k": lambda x, k: x > k,
    "ge_k": lambda x, k: x >= k,
    "lt_k": lambda x, k: x < k,
    "le_k": lambda x, k: x <= k,
    "multiple_of_k": lambda x, k: x % k == 0,
    "positive": lambda x, k: x > 0,
    "negative": lambda x, k: x < 0,
    "zero": lambda x, k: x == 0,
}

_MAP_FUNCS = {
    "add_k": lambda x, k, arg: x + k,
    "sub_k": lambda x, k, arg: x - k,
    "mul_k": lambda x, k, arg: x * k,
    "negate": lambda x, k, arg: -x,
    "abs": lambda x, k, arg: abs(x),
    "square": lambda x, k, arg: x ** 2,
    "mul_const": lambda x, k, arg: x * arg,
}


def interpret(ast: SemanticAST, xs: list[int], k: int) -> list[int]:
    """Return the expected ``solve(xs, k)`` output for ``ast``.

    Does not mutate ``xs``. Raises ``SemanticASTError`` (via ``validate``)
    if ``ast`` is malformed, and ``ZeroDivisionError`` never occurs since
    ``k`` is contractually 1-10 (never 0) per homework.md's input domain.
    """
    validate(ast)
    return apply_ops(ast.ops, xs, k)


def apply_ops(ops: Sequence[AtomicOp], xs: list[int], k: int) -> list[int]:
    """``ops`` applied to a copy of ``xs`` left to right (also used on a
    prefix of an AST, e.g. by ``testcases.py``)."""
    result = list(xs)
    for op in ops:
        result = apply_op(op, result, k)
    return result


def apply_op(op: AtomicOp, result: list[int], k: int) -> list[int]:
    if op.category == "filter":
        pred = _FILTER_FUNCS[op.name]
        return [x for x in result if pred(x, k)]
    if op.category == "map":
        fn = _MAP_FUNCS[op.name]
        return [fn(x, k, op.arg) for x in result]
    if op.category == "order":
        if op.name == "ascending":
            return sorted(result)
        if op.name == "descending":
            return sorted(result, reverse=True)
        return list(reversed(result))
    if op.name == "take_first_k":
        return result[:k]
    if op.name == "take_last_k":
        return result[-k:]
    return result[::2]  # step_2
