"""Reference interpreter: executes a ``SemanticAST`` directly against
``(xs, k)``, without going through any generated Python code.

This is the "正解を計算する参照インタプリタ" from homework.md's データ生成
section. It is the ground truth used to:

  * generate ``expected`` outputs for test cases (``testcases.py``);
  * cross-check the structural code generator's output once it exists
    (homework.md: "両者の出力をランダムテストで比較する");
  * judge model-generated code at evaluation time (pass@1 / pass@5).

Pipeline order is fixed: filter -> map -> order -> slice (see the design
note in ``schema.py``).
"""

from __future__ import annotations

from schema import SemanticAST, validate

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
    result = list(xs)

    for name in ast.filters:
        pred = _FILTER_FUNCS[name]
        result = [x for x in result if pred(x, k)]

    if ast.map_op is not None:
        name, arg = ast.map_op
        fn = _MAP_FUNCS[name]
        result = [fn(x, k, arg) for x in result]

    if ast.order_op == "ascending":
        result = sorted(result)
    elif ast.order_op == "descending":
        result = sorted(result, reverse=True)
    elif ast.order_op == "reverse":
        result = list(reversed(result))

    if ast.slice_op == "take_first_k":
        result = result[:k]
    elif ast.slice_op == "take_last_k":
        result = result[-k:]
    elif ast.slice_op == "step_2":
        result = result[::2]

    return result
