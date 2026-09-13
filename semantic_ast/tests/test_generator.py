"""Unit tests for generator.py. Pure stdlib, no Docker required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import enumerate_all, label  # noqa: E402
from schema import SemanticAST  # noqa: E402


class EnumerateAll(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_asts = enumerate_all()

    def test_nonempty_and_reasonably_sized(self):
        # exact combinatorics documented in generator.py's module docstring
        # (97,464); a loose bound here just guards against a wildly broken
        # enumeration.
        self.assertGreater(len(self.all_asts), 30000)
        self.assertLess(len(self.all_asts), 150000)

    def test_exact_count_matches_documented_combinatorics(self):
        self.assertEqual(len(self.all_asts), 97464)

    def test_every_ast_has_1_to_3_categories(self):
        for ast in self.all_asts:
            self.assertGreaterEqual(ast.num_categories(), 1)
            self.assertLessEqual(ast.num_categories(), 3)

    def test_no_duplicate_semantic_hashes(self):
        hashes = [ast.semantic_hash() for ast in self.all_asts]
        self.assertEqual(len(hashes), len(set(hashes)))

    def test_worked_example_is_present(self):
        target = SemanticAST(filters=("even", "ge_k"), map_ops=(("mul_const", 2),), order_op="ascending")
        self.assertIn(target.semantic_hash(), {a.semantic_hash() for a in self.all_asts})

    def test_chained_map_and_slice_examples_are_present(self):
        chained_map = SemanticAST(map_ops=(("add_k", None), ("mul_const", 2)))
        chained_slice = SemanticAST(slice_ops=("take_first_k", "step_2"))
        hashes = {a.semantic_hash() for a in self.all_asts}
        self.assertIn(chained_map.semantic_hash(), hashes)
        self.assertIn(chained_slice.semantic_hash(), hashes)

    def test_deterministic(self):
        self.assertEqual(
            [a.semantic_hash() for a in enumerate_all()],
            [a.semantic_hash() for a in self.all_asts],
        )


class Label(unittest.TestCase):
    def test_label_reflects_active_ops(self):
        ast = SemanticAST(filters=("even", "ge_k"), map_ops=(("mul_const", 2),), order_op="ascending")
        l = label(ast)
        self.assertEqual(l["num_categories"], 3)
        self.assertEqual(l["num_filters"], 2)
        self.assertEqual(l["map_ops"], ("mul_const",))
        self.assertEqual(l["order_op"], "ascending")
        self.assertEqual(l["slice_ops"], ())

    def test_label_reflects_chained_map_ops(self):
        ast = SemanticAST(map_ops=(("add_k", None), ("mul_const", 2)))
        l = label(ast)
        self.assertEqual(l["map_ops"], ("add_k", "mul_const"))


if __name__ == "__main__":
    unittest.main()
