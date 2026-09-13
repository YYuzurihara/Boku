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
        # exact combinatorics documented in generator.py's module docstring;
        # a loose bound here just guards against a wildly broken enumeration.
        self.assertGreater(len(self.all_asts), 1000)
        self.assertLess(len(self.all_asts), 10000)

    def test_every_ast_has_1_to_3_categories(self):
        for ast in self.all_asts:
            self.assertGreaterEqual(ast.num_categories(), 1)
            self.assertLessEqual(ast.num_categories(), 3)

    def test_no_duplicate_semantic_hashes(self):
        hashes = [ast.semantic_hash() for ast in self.all_asts]
        self.assertEqual(len(hashes), len(set(hashes)))

    def test_worked_example_is_present(self):
        target = SemanticAST(filters=("even", "ge_k"), map_op=("mul_const", 2), order_op="ascending")
        self.assertIn(target.semantic_hash(), {a.semantic_hash() for a in self.all_asts})

    def test_deterministic(self):
        self.assertEqual(
            [a.semantic_hash() for a in enumerate_all()],
            [a.semantic_hash() for a in self.all_asts],
        )


class Label(unittest.TestCase):
    def test_label_reflects_active_ops(self):
        ast = SemanticAST(filters=("even", "ge_k"), map_op=("mul_const", 2), order_op="ascending")
        l = label(ast)
        self.assertEqual(l["num_categories"], 3)
        self.assertEqual(l["num_filters"], 2)
        self.assertEqual(l["map_op"], "mul_const")
        self.assertEqual(l["order_op"], "ascending")
        self.assertIsNone(l["slice_op"])


if __name__ == "__main__":
    unittest.main()
