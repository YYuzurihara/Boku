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


class InterpretMatchesHomeworkExample(unittest.TestCase):
    def test_worked_example(self):
        # "整数リストxsからk以上の偶数だけを残し、それぞれを2倍して昇順に並べる"
        ast = SemanticAST(filters=("even", "ge_k"), map_ops=(("mul_const", 2),), order_op="ascending")
        xs = [1, 5, 2, 8, -4, 10, 3]
        k = 3
        self.assertEqual(
            interpret(ast, xs, k),
            sorted([x * 2 for x in xs if x >= k and x % 2 == 0]),
        )


class InterpretDoesNotMutateInput(unittest.TestCase):
    def test_pure(self):
        ast = SemanticAST(order_op="ascending")
        xs = [3, 1, 2]
        original = list(xs)
        interpret(ast, xs, 1)
        self.assertEqual(xs, original)


class InterpretFilters(unittest.TestCase):
    def setUp(self):
        self.xs = [-4, -3, -2, -1, 0, 1, 2, 3, 4, 5, 6, 9, 10]
        self.k = 4

    def test_even_odd(self):
        self.assertEqual(interpret(SemanticAST(filters=("even",)), self.xs, self.k), [x for x in self.xs if x % 2 == 0])
        self.assertEqual(interpret(SemanticAST(filters=("odd",)), self.xs, self.k), [x for x in self.xs if x % 2 != 0])

    def test_k_compare(self):
        k = self.k
        self.assertEqual(interpret(SemanticAST(filters=("gt_k",)), self.xs, k), [x for x in self.xs if x > k])
        self.assertEqual(interpret(SemanticAST(filters=("ge_k",)), self.xs, k), [x for x in self.xs if x >= k])
        self.assertEqual(interpret(SemanticAST(filters=("lt_k",)), self.xs, k), [x for x in self.xs if x < k])
        self.assertEqual(interpret(SemanticAST(filters=("le_k",)), self.xs, k), [x for x in self.xs if x <= k])

    def test_multiple_of_k(self):
        k = self.k
        self.assertEqual(
            interpret(SemanticAST(filters=("multiple_of_k",)), self.xs, k),
            [x for x in self.xs if x % k == 0],
        )

    def test_sign(self):
        self.assertEqual(interpret(SemanticAST(filters=("positive",)), self.xs, self.k), [x for x in self.xs if x > 0])
        self.assertEqual(interpret(SemanticAST(filters=("negative",)), self.xs, self.k), [x for x in self.xs if x < 0])
        self.assertEqual(interpret(SemanticAST(filters=("zero",)), self.xs, self.k), [x for x in self.xs if x == 0])


class InterpretMapOps(unittest.TestCase):
    def setUp(self):
        self.xs = [-3, -1, 0, 2, 5]
        self.k = 4

    def test_arithmetic(self):
        self.assertEqual(interpret(SemanticAST(map_ops=(("add_k", None),)), self.xs, self.k), [x + self.k for x in self.xs])
        self.assertEqual(interpret(SemanticAST(map_ops=(("sub_k", None),)), self.xs, self.k), [x - self.k for x in self.xs])
        self.assertEqual(interpret(SemanticAST(map_ops=(("mul_k", None),)), self.xs, self.k), [x * self.k for x in self.xs])
        self.assertEqual(interpret(SemanticAST(map_ops=(("mul_const", 3),)), self.xs, self.k), [x * 3 for x in self.xs])
        self.assertEqual(interpret(SemanticAST(map_ops=(("negate", None),)), self.xs, self.k), [-x for x in self.xs])
        self.assertEqual(interpret(SemanticAST(map_ops=(("abs", None),)), self.xs, self.k), [abs(x) for x in self.xs])
        self.assertEqual(interpret(SemanticAST(map_ops=(("square", None),)), self.xs, self.k), [x ** 2 for x in self.xs])

    def test_chained_ops_apply_in_sequence(self):
        # add_k then mul_const(2): (x + k) * 2, not x + k*2
        ast = SemanticAST(map_ops=(("add_k", None), ("mul_const", 2)))
        self.assertEqual(interpret(ast, self.xs, self.k), [(x + self.k) * 2 for x in self.xs])


class InterpretOrderOps(unittest.TestCase):
    def test_ascending_descending_reverse(self):
        xs = [3, 1, 4, 1, 5]
        self.assertEqual(interpret(SemanticAST(order_op="ascending"), xs, 1), sorted(xs))
        self.assertEqual(interpret(SemanticAST(order_op="descending"), xs, 1), sorted(xs, reverse=True))
        self.assertEqual(interpret(SemanticAST(order_op="reverse"), xs, 1), list(reversed(xs)))


class InterpretSliceOps(unittest.TestCase):
    def test_take_first_last_and_step(self):
        xs = list(range(10))
        k = 3
        self.assertEqual(interpret(SemanticAST(slice_ops=("take_first_k",)), xs, k), xs[:k])
        self.assertEqual(interpret(SemanticAST(slice_ops=("take_last_k",)), xs, k), xs[-k:])
        self.assertEqual(interpret(SemanticAST(slice_ops=("step_2",)), xs, k), xs[::2])

    def test_take_last_k_longer_than_list(self):
        xs = [1, 2]
        self.assertEqual(interpret(SemanticAST(slice_ops=("take_last_k",)), xs, 10), xs)

    def test_chained_slice_ops_apply_in_sequence(self):
        xs = list(range(10))
        k = 4
        ast = SemanticAST(slice_ops=("take_first_k", "step_2"))
        self.assertEqual(interpret(ast, xs, k), xs[:k][::2])
        reversed_ast = SemanticAST(slice_ops=("step_2", "take_first_k"))
        self.assertEqual(interpret(reversed_ast, xs, k), xs[::2][:k])


class InterpretPipelineOrder(unittest.TestCase):
    def test_filter_then_map_then_order(self):
        # at most 3 active categories (schema.py's design note), so this
        # exercises filter -> map -> order; slice ordering is covered below.
        ast = SemanticAST(filters=("positive",), map_ops=(("mul_const", 2),), order_op="descending")
        xs = [-5, 1, -2, 3, 8, 2]
        k = 2
        expected_filtered = [x for x in xs if x > 0]
        expected_mapped = [x * 2 for x in expected_filtered]
        expected = sorted(expected_mapped, reverse=True)
        self.assertEqual(interpret(ast, xs, k), expected)

    def test_order_then_slice(self):
        ast = SemanticAST(order_op="ascending", slice_ops=("take_first_k",))
        xs = [9, -1, 4, 2, 7]
        k = 3
        expected = sorted(xs)[:k]
        self.assertEqual(interpret(ast, xs, k), expected)


if __name__ == "__main__":
    unittest.main()
