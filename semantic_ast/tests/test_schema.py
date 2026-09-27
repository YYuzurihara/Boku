"""Unit tests for schema.py. Pure stdlib, no Docker required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schema import ATOMIC_OPS, AtomicOp, SemanticAST, SemanticASTError  # noqa: E402


class AtomicOps(unittest.TestCase):
    def test_there_are_24_distinct_atomic_ops(self):
        self.assertEqual(len(ATOMIC_OPS), 24)
        self.assertEqual(len({op.tag for op in ATOMIC_OPS}), 24)
        by_category = {}
        for op in ATOMIC_OPS:
            by_category[op.category] = by_category.get(op.category, 0) + 1
        self.assertEqual(by_category, {"filter": 10, "map": 8, "order": 3, "slice": 3})

    def test_mul_const_constants_are_separate_ops(self):
        self.assertIn(AtomicOp("map", "mul_const", 2), ATOMIC_OPS)
        self.assertIn(AtomicOp("map", "mul_const", 3), ATOMIC_OPS)

    def test_tag_round_trip(self):
        for op in ATOMIC_OPS:
            self.assertEqual(AtomicOp.from_tag(op.tag), op)
            self.assertEqual(AtomicOp.from_json(op.to_json()), op)

    def test_rejects_unknown_ops(self):
        for category, name in (("filter", "nonsense"), ("map", "nonsense"), ("order", "nonsense"),
                               ("slice", "nonsense"), ("nonsense", "even"), ("map", "even")):
            with self.assertRaises(SemanticASTError, msg=(category, name)):
                AtomicOp(category, name)

    def test_rejects_mul_const_with_bad_arg(self):
        with self.assertRaises(SemanticASTError):
            AtomicOp("map", "mul_const", 11)
        with self.assertRaises(SemanticASTError):
            AtomicOp("map", "mul_const")

    def test_rejects_no_arg_op_with_arg(self):
        with self.assertRaises(SemanticASTError):
            AtomicOp("map", "negate", 3)
        with self.assertRaises(SemanticASTError):
            AtomicOp("filter", "even", 2)


class SemanticASTValidation(unittest.TestCase):
    def test_valid_three_op_problem(self):
        ast = SemanticAST.of("filter:even", "map:mul_const:2", "order:ascending")
        self.assertEqual(ast.num_ops(), 3)
        self.assertEqual(ast.categories(), ("filter", "map", "order"))

    def test_rejects_empty_ast(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST(())

    def test_rejects_four_ops(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST.of("filter:even", "map:negate", "order:ascending", "slice:step_2")

    def test_repetition_is_allowed(self):
        """1-3 ops *with* repetition: the same op, or the same category, may
        occur more than once."""
        for tags in (
            ("filter:even", "filter:even"),
            ("filter:even", "filter:odd"),
            ("map:mul_const:2", "map:mul_const:2", "map:mul_const:2"),
            ("order:reverse", "order:reverse"),
            ("slice:take_first_k", "map:add_k", "slice:take_first_k"),
        ):
            self.assertEqual(SemanticAST.of(*tags).tags(), tags)


class SemanticASTRoundTrip(unittest.TestCase):
    def test_to_dict_shape(self):
        ast = SemanticAST.of("filter:even", "map:mul_const:2", "order:ascending")
        self.assertEqual(
            ast.to_dict(),
            {"ops": [["filter", "even"], ["map", "mul_const", 2], ["order", "ascending"]]},
        )

    def test_from_dict_round_trip(self):
        for ast in [
            SemanticAST.of("filter:even", "map:mul_const:2", "order:ascending"),
            SemanticAST.of("slice:take_first_k"),
            SemanticAST.of("slice:step_2", "map:add_k", "slice:step_2"),
        ]:
            restored = SemanticAST.from_dict(ast.to_dict())
            self.assertEqual(ast, restored)
            self.assertEqual(ast.semantic_hash(), restored.semantic_hash())

    def test_from_dict_rejects_the_old_category_slot_format(self):
        with self.assertRaises(SemanticASTError):
            SemanticAST.from_dict({"filter": ["even"], "order": "ascending"})


class SemanticHash(unittest.TestCase):
    def test_hash_differs_for_different_ops(self):
        self.assertNotEqual(SemanticAST.of("filter:even").semantic_hash(), SemanticAST.of("filter:odd").semantic_hash())

    def test_hash_differs_for_a_different_order_of_the_same_ops(self):
        """schema.py "Order is identity": even when both orders compute the
        same function (filter and sort commute)."""
        a = SemanticAST.of("filter:even", "order:ascending")
        b = SemanticAST.of("order:ascending", "filter:even")
        self.assertNotEqual(a, b)
        self.assertNotEqual(a.semantic_hash(), b.semantic_hash())

    def test_hash_differs_for_a_repeated_op(self):
        self.assertNotEqual(
            SemanticAST.of("filter:even").semantic_hash(),
            SemanticAST.of("filter:even", "filter:even").semantic_hash(),
        )

    def test_op_tags_are_order_free_but_tags_are_not(self):
        a = SemanticAST.of("filter:even", "order:ascending")
        b = SemanticAST.of("order:ascending", "filter:even")
        self.assertEqual(a.op_tags(), b.op_tags())
        self.assertNotEqual(a.tags(), b.tags())

    def test_hash_is_stable_hex_sha256(self):
        h = SemanticAST.of("filter:even").semantic_hash()
        self.assertEqual(len(h), 64)
        int(h, 16)  # must not raise


if __name__ == "__main__":
    unittest.main()
