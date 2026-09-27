"""Unit tests for reference_interpreter.py. Pure stdlib, no Docker required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reference_interpreter import interpret  # noqa: E402
from schema import SemanticAST  # noqa: E402

A = SemanticAST.of


class InterpretMatchesHomeworkExample(unittest.TestCase):
    def test_worked_example(self):
        # homework.md's "k以上の偶数だけを残し、それぞれを2倍して昇順に並べる"
        # has four ops; its first three are one AST of at most 3 ops
        ast = A("filter:ge_k", "filter:even", "map:mul_const:2")
        xs = [1, 5, 2, 8, -4, 10, 3]
        k = 3
        self.assertEqual(interpret(ast, xs, k), [x * 2 for x in xs if x >= k and x % 2 == 0])


class InterpretDoesNotMutateInput(unittest.TestCase):
    def test_pure(self):
        xs = [3, 1, 2]
        original = list(xs)
        interpret(A("order:ascending", "order:reverse"), xs, 1)
        self.assertEqual(xs, original)


class InterpretFilters(unittest.TestCase):
    def setUp(self):
        self.xs = [-4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 9, 10]
        self.k = 4

    def check(self, name, pred):
        self.assertEqual(interpret(A(f"filter:{name}"), self.xs, self.k), [x for x in self.xs if pred(x)], name)

    def test_every_filter(self):
        k = self.k
        self.check("even", lambda x: x % 2 == 0)
        self.check("odd", lambda x: x % 2 != 0)
        self.check("gt_k", lambda x: x > k)
        self.check("ge_k", lambda x: x >= k)
        self.check("lt_k", lambda x: x < k)
        self.check("le_k", lambda x: x <= k)
        self.check("multiple_of_k", lambda x: x % k == 0)
        self.check("positive", lambda x: x > 0)
        self.check("negative", lambda x: x < 0)
        self.check("zero", lambda x: x == 0)


class InterpretMapOps(unittest.TestCase):
    def test_every_map(self):
        xs, k = [-3, -1, 0, 2, 5], 4
        for tag, fn in (
            ("map:add_k", lambda x: x + k),
            ("map:sub_k", lambda x: x - k),
            ("map:mul_k", lambda x: x * k),
            ("map:mul_const:2", lambda x: x * 2),
            ("map:mul_const:3", lambda x: x * 3),
            ("map:negate", lambda x: -x),
            ("map:abs", abs),
            ("map:square", lambda x: x ** 2),
        ):
            self.assertEqual(interpret(A(tag), xs, k), [fn(x) for x in xs], tag)


class InterpretOrderOps(unittest.TestCase):
    def test_ascending_descending_reverse(self):
        xs = [3, 1, 4, 1, 5]
        self.assertEqual(interpret(A("order:ascending"), xs, 1), sorted(xs))
        self.assertEqual(interpret(A("order:descending"), xs, 1), sorted(xs, reverse=True))
        self.assertEqual(interpret(A("order:reverse"), xs, 1), list(reversed(xs)))


class InterpretSliceOps(unittest.TestCase):
    def test_take_first_last_and_step(self):
        xs = list(range(10))
        k = 3
        self.assertEqual(interpret(A("slice:take_first_k"), xs, k), xs[:k])
        self.assertEqual(interpret(A("slice:take_last_k"), xs, k), xs[-k:])
        self.assertEqual(interpret(A("slice:step_2"), xs, k), xs[::2])

    def test_take_last_k_longer_than_list(self):
        xs = [1, 2]
        self.assertEqual(interpret(A("slice:take_last_k"), xs, 10), xs)


class InterpretOpOrder(unittest.TestCase):
    """Ops run left to right, in ``ast.ops`` order."""

    def test_filter_then_map_then_order(self):
        xs, k = [-5, 1, -2, 3, 8, 2], 2
        ast = A("filter:positive", "map:mul_const:2", "order:descending")
        self.assertEqual(interpret(ast, xs, k), sorted([x * 2 for x in xs if x > 0], reverse=True))

    def test_the_order_of_the_ops_changes_the_result(self):
        xs, k = [1, 2, 3, 4, 5, 6], 3
        self.assertEqual(interpret(A("filter:even", "slice:take_first_k"), xs, k), [2, 4, 6])
        self.assertEqual(interpret(A("slice:take_first_k", "filter:even"), xs, k), [2])

    def test_sort_before_a_non_monotone_map(self):
        self.assertEqual(interpret(A("order:ascending", "map:negate"), [3, -1, 2], 1), [1, -2, -3])
        self.assertEqual(interpret(A("map:negate", "order:ascending"), [3, -1, 2], 1), [-3, -2, 1])

    def test_repeated_ops_are_applied_every_time(self):
        xs, k = [1, 2, 3, 4, 5], 2
        self.assertEqual(interpret(A("map:add_k", "map:add_k"), xs, k), [x + 2 * k for x in xs])
        self.assertEqual(interpret(A("map:mul_const:3", "map:mul_const:3", "map:mul_const:3"), xs, k), [x * 27 for x in xs])
        self.assertEqual(interpret(A("slice:step_2", "slice:step_2"), xs, k), [1, 5])
        self.assertEqual(interpret(A("order:reverse", "order:reverse"), xs, k), xs)

    def test_interleaved_categories(self):
        xs, k = [9, -1, 4, 2, 7, 6], 3
        ast = A("slice:take_first_k", "map:square", "slice:take_last_k")
        self.assertEqual(interpret(ast, xs, k), [x ** 2 for x in xs[:k]][-k:])


if __name__ == "__main__":
    unittest.main()
