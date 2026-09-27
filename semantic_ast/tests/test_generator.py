"""Unit tests for generator.py. Pure stdlib, no Docker required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import enumerate_all, label  # noqa: E402
from schema import SemanticAST  # noqa: E402


class EnumerateAll(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_asts = enumerate_all()

    def test_exact_count_matches_documented_combinatorics(self):
        # generator.py's module docstring: 24 + 24**2 + 24**3
        self.assertEqual(len(self.all_asts), 14_424)
        self.assertEqual(Counter(ast.num_ops() for ast in self.all_asts), {1: 24, 2: 576, 3: 13_824})

    def test_no_duplicate_semantic_hashes(self):
        hashes = [ast.semantic_hash() for ast in self.all_asts]
        self.assertEqual(len(hashes), len(set(hashes)))

    def test_every_order_of_the_same_ops_is_its_own_ast(self):
        """The 3! orders of three distinct ops are 6 ASTs; repeats are kept."""
        by_multiset = Counter(ast.op_tags() for ast in self.all_asts)
        self.assertEqual(by_multiset[tuple(sorted(("filter:even", "map:mul_const:2", "order:ascending")))], 6)
        self.assertEqual(by_multiset[("filter:even", "filter:even", "order:reverse")], 3)
        self.assertEqual(by_multiset[("order:reverse",) * 3], 1)

    def test_worked_example_and_its_reorderings_are_present(self):
        hashes = {a.semantic_hash() for a in self.all_asts}
        for tags in (
            ("filter:even", "map:mul_const:2", "order:ascending"),
            ("order:ascending", "map:mul_const:2", "filter:even"),
            ("filter:even", "filter:even"),
        ):
            self.assertIn(SemanticAST.of(*tags).semantic_hash(), hashes)

    def test_deterministic(self):
        self.assertEqual(
            [a.semantic_hash() for a in enumerate_all()],
            [a.semantic_hash() for a in self.all_asts],
        )


class Label(unittest.TestCase):
    def test_label_is_the_category_sequence(self):
        ast = SemanticAST.of("order:ascending", "filter:even", "filter:odd")
        self.assertEqual(label(ast), {"num_ops": 3, "categories": ("order", "filter", "filter")})

    def test_there_are_84_labels(self):
        labels = {tuple(sorted(label(ast).items())) for ast in enumerate_all()}
        self.assertEqual(len(labels), 4 + 16 + 64)


if __name__ == "__main__":
    unittest.main()
