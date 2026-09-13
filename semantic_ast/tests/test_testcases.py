"""Unit tests for testcases.py. Pure stdlib, no Docker required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reference_interpreter import interpret  # noqa: E402
from schema import ELEMENT_MAX, ELEMENT_MIN, K_MAX, K_MIN, XS_MAX_LEN, SemanticAST  # noqa: E402
from testcases import generate_test_cases  # noqa: E402


class GenerateTestCases(unittest.TestCase):
    def setUp(self):
        self.ast = SemanticAST(filters=("even", "ge_k"), map_op=("mul_const", 2), order_op="ascending")

    def test_at_least_20_random_cases_worth_of_coverage(self):
        cases = generate_test_cases(self.ast, seed=42, n_random=24)
        self.assertGreaterEqual(len(cases), 20)

    def test_every_case_matches_reference_interpreter(self):
        cases = generate_test_cases(self.ast, seed=42)
        for case in cases:
            self.assertEqual(interpret(self.ast, case["xs"], case["k"]), case["expected"])

    def test_includes_empty_list_boundary_case(self):
        cases = generate_test_cases(self.ast, seed=42)
        self.assertTrue(any(case["xs"] == [] for case in cases))

    def test_cases_respect_domain_bounds(self):
        cases = generate_test_cases(self.ast, seed=7)
        for case in cases:
            self.assertLessEqual(len(case["xs"]), XS_MAX_LEN)
            self.assertGreaterEqual(len(case["xs"]), 0)
            self.assertTrue(K_MIN <= case["k"] <= K_MAX)
            for x in case["xs"]:
                self.assertTrue(ELEMENT_MIN <= x <= ELEMENT_MAX)

    def test_deterministic_given_seed(self):
        self.assertEqual(generate_test_cases(self.ast, seed=1), generate_test_cases(self.ast, seed=1))

    def test_different_seeds_can_differ(self):
        a = generate_test_cases(self.ast, seed=1)
        b = generate_test_cases(self.ast, seed=2)
        self.assertNotEqual(a, b)

    def test_no_duplicate_xs_k_pairs(self):
        cases = generate_test_cases(self.ast, seed=42)
        keys = [(tuple(c["xs"]), c["k"]) for c in cases]
        self.assertEqual(len(keys), len(set(keys)))


if __name__ == "__main__":
    unittest.main()
