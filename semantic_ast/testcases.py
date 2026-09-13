"""Generate concrete ``(xs, k, expected)`` test cases for one ``SemanticAST``.

Combines homework.md's "境界値テスト" boundary cases with random cases, all
labeled with ``expected`` from ``reference_interpreter.interpret`` -- this
*is* the "正解を計算する参照インタプリタ" being put to use, and is what
homework.md's データレコード ``tests`` field and 評価 ``hidden_test`` sets
both build on (hidden tests are generated the same way, from held-out
semantic ASTs / seeds -- keeping them disjoint from training data is the
caller's responsibility, not this module's).
"""

from __future__ import annotations

import random
from typing import TypedDict

from reference_interpreter import interpret
from schema import ELEMENT_MAX, ELEMENT_MIN, K_MAX, K_MIN, XS_MAX_LEN, SemanticAST


class TestCase(TypedDict):
    xs: list[int]
    k: int
    expected: list[int]


def _make_case(ast: SemanticAST, xs: list[int], k: int) -> TestCase:
    return {"xs": xs, "k": k, "expected": interpret(ast, xs, k)}


def _boundary_cases(ast: SemanticAST, rng: random.Random) -> list[TestCase]:
    k_lo, k_hi = K_MIN, K_MAX
    cases: list[tuple[list[int], int]] = [
        ([], k_lo),  # empty list
        ([0], k_lo),  # single element, zero
        ([rng.randint(ELEMENT_MIN, ELEMENT_MAX)], k_hi),  # single random element
        ([5] * 10, k_lo),  # all elements identical
        (list(range(-5, 5)), (k_lo + k_hi) // 2),  # negatives and positives mixed
        ([ELEMENT_MIN, ELEMENT_MAX] * 5, k_lo),  # extreme magnitudes
        ([1, 3, 5, 7, 9], k_lo),  # every element odd/small (may empty out a filter)
        (list(range(XS_MAX_LEN)), k_hi),  # max-length list
    ]
    return [_make_case(ast, xs, k) for xs, k in cases]


def _random_cases(ast: SemanticAST, rng: random.Random, n: int) -> list[TestCase]:
    cases = []
    for _ in range(n):
        length = rng.randint(0, XS_MAX_LEN)
        xs = [rng.randint(ELEMENT_MIN, ELEMENT_MAX) for _ in range(length)]
        k = rng.randint(K_MIN, K_MAX)
        cases.append(_make_case(ast, xs, k))
    return cases


def generate_test_cases(
    ast: SemanticAST, seed: int, n_random: int = 24
) -> list[TestCase]:
    """Boundary cases + ``n_random`` random cases (homework.md: "テスト問題
    ごとに20個以上のランダム入力を生成する"). Deterministic given ``seed``,
    so the same semantic AST always yields the same test suite."""
    rng = random.Random(seed)
    cases = _boundary_cases(ast, rng) + _random_cases(ast, rng, n_random)
    # de-duplicate identical (xs, k) pairs while preserving order
    seen: set[tuple[tuple[int, ...], int]] = set()
    unique_cases: list[TestCase] = []
    for case in cases:
        key = (tuple(case["xs"]), case["k"])
        if key not in seen:
            seen.add(key)
            unique_cases.append(case)
    return unique_cases
