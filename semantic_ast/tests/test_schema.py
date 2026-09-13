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
        ast = SemanticAST(filters=("even", "ge_k"), map_ops=(("mul_const", 2),), order_op="ascending")
        self.assertEqual(ast.num_categories(), 3)

    def test_rejects_empty_ast(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST()

    def test_rejects_four_categories(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(
                filters=("even",),
                map_ops=(("negate", None),),
                order_op="ascending",
                slice_ops=("step_2",),
            )

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
            SemanticAST(map_ops=(("nonsense", None),))
        with self.assertRaises(SemanticASTError):
            SemanticAST(order_op="nonsense")
        with self.assertRaises(SemanticASTError):
            SemanticAST(slice_ops=("nonsense",))

    def test_rejects_mul_const_with_bad_arg(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(map_ops=(("mul_const", 11),))

    def test_rejects_no_arg_map_with_arg(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(map_ops=(("negate", 3),))

    def test_rejects_too_many_map_ops(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(map_ops=(("negate", None), ("abs", None), ("square", None)))

    def test_rejects_duplicate_map_op_type(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(map_ops=(("mul_const", 2), ("mul_const", 3)))

    def test_rejects_too_many_slice_ops(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(slice_ops=("take_first_k", "take_last_k", "step_2"))

    def test_rejects_duplicate_slice_op(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(slice_ops=("step_2", "step_2"))

    def test_accepts_chained_map_ops(self):
        ast = SemanticAST(map_ops=(("add_k", None), ("mul_const", 2)))
        self.assertEqual(ast.num_categories(), 1)

    def test_accepts_chained_slice_ops(self):
        ast = SemanticAST(slice_ops=("take_first_k", "step_2"))
        self.assertEqual(ast.num_categories(), 1)


class SemanticASTRoundTrip(unittest.TestCase):
    def test_to_dict_matches_homework_shape(self):
        ast = SemanticAST(filters=("even", "ge_k"), map_ops=(("mul_const", 2),), order_op="ascending")
        self.assertEqual(
            ast.to_dict(),
            {"filter": ["even", "ge_k"], "map": [["mul_const", 2]], "order": "ascending"},
        )

    def test_to_dict_reflects_chained_map_ops(self):
        ast = SemanticAST(map_ops=(("add_k", None), ("mul_const", 2)))
        self.assertEqual(ast.to_dict(), {"map": [["add_k"], ["mul_const", 2]]})

    def test_from_dict_round_trip(self):
        for ast in [
            SemanticAST(filters=("even", "ge_k"), map_ops=(("mul_const", 2),), order_op="ascending"),
            SemanticAST(slice_ops=("take_first_k",)),
            SemanticAST(map_ops=(("add_k", None),), slice_ops=("step_2",)),
            SemanticAST(map_ops=(("add_k", None), ("mul_const", 2))),
            SemanticAST(slice_ops=("take_first_k", "step_2")),
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

    def test_hash_is_order_sensitive_for_map_ops(self):
        a = SemanticAST(map_ops=(("add_k", None), ("mul_const", 2)))
        b = SemanticAST(map_ops=(("mul_const", 2), ("add_k", None)))
        self.assertNotEqual(a.semantic_hash(), b.semantic_hash())

    def test_hash_is_order_sensitive_for_slice_ops(self):
        a = SemanticAST(slice_ops=("take_first_k", "step_2"))
        b = SemanticAST(slice_ops=("step_2", "take_first_k"))
        self.assertNotEqual(a.semantic_hash(), b.semantic_hash())

    def test_hash_is_stable_hex_sha256(self):
        h = SemanticAST(filters=("even",)).semantic_hash()
        self.assertEqual(len(h), 64)
        int(h, 16)  # must not raise


if __name__ == "__main__":
    unittest.main()
