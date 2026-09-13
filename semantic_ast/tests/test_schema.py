"""Unit tests for schema.py. Pure stdlib, no Docker required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schema import SemanticAST, SemanticASTError  # noqa: E402


class SemanticASTValidation(unittest.TestCase):
    def test_valid_worked_example_from_homework(self):
        ast = SemanticAST(filters=("even", "ge_k"), map_op=("mul_const", 2), order_op="ascending")
        self.assertEqual(ast.num_categories(), 3)

    def test_rejects_empty_ast(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST()

    def test_rejects_four_categories(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(filters=("even",), map_op=("negate", None), order_op="ascending", slice_op="step_2")

    def test_rejects_same_group_filter_pair(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(filters=("even", "odd"))
        with self.assertRaises(SemanticASTError):
            SemanticAST(filters=("positive", "zero"))
        with self.assertRaises(SemanticASTError):
            SemanticAST(filters=("gt_k", "le_k"))

    def test_rejects_too_many_filters(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(filters=("even", "positive", "multiple_of_k"))

    def test_rejects_unknown_ops(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(filters=("nonsense",))
        with self.assertRaises(SemanticASTError):
            SemanticAST(map_op=("nonsense", None))
        with self.assertRaises(SemanticASTError):
            SemanticAST(order_op="nonsense")
        with self.assertRaises(SemanticASTError):
            SemanticAST(slice_op="nonsense")

    def test_rejects_mul_const_with_bad_arg(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(map_op=("mul_const", 5))

    def test_rejects_no_arg_map_with_arg(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(map_op=("negate", 3))


class SemanticASTRoundTrip(unittest.TestCase):
    def test_to_dict_matches_homework_shape(self):
        ast = SemanticAST(filters=("even", "ge_k"), map_op=("mul_const", 2), order_op="ascending")
        self.assertEqual(
            ast.to_dict(),
            {"filter": ["even", "ge_k"], "map": ["mul_const", 2], "order": "ascending"},
        )

    def test_from_dict_round_trip(self):
        for ast in [
            SemanticAST(filters=("even", "ge_k"), map_op=("mul_const", 2), order_op="ascending"),
            SemanticAST(slice_op="take_first_k"),
            SemanticAST(map_op=("add_k", None), slice_op="step_2"),
        ]:
            restored = SemanticAST.from_dict(ast.to_dict())
            self.assertEqual(ast, restored)
            self.assertEqual(ast.semantic_hash(), restored.semantic_hash())


class SemanticHash(unittest.TestCase):
    def test_hash_is_order_independent_within_filters(self):
        a = SemanticAST(filters=("even", "ge_k"))
        b = SemanticAST(filters=("ge_k", "even"))
        self.assertEqual(a.semantic_hash(), b.semantic_hash())

    def test_hash_differs_for_different_semantics(self):
        a = SemanticAST(filters=("even",))
        b = SemanticAST(filters=("odd",))
        self.assertNotEqual(a.semantic_hash(), b.semantic_hash())

    def test_hash_is_stable_hex_sha256(self):
        h = SemanticAST(filters=("even",)).semantic_hash()
        self.assertEqual(len(h), 64)
        int(h, 16)  # must not raise


if __name__ == "__main__":
    unittest.main()
