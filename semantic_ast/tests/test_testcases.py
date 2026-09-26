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
from generator import enumerate_all  # noqa: E402
from testcases import generate_boundary_test_cases, generate_test_cases, has_reject_all_case  # noqa: E402


class GenerateTestCases(unittest.TestCase):
    def setUp(self):
        self.ast = SemanticAST(filters=("even", "ge_k"), map_ops=(("mul_const", 2),), order_op="ascending")

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


class GenerateBoundaryTestCases(unittest.TestCase):
    def setUp(self):
        self.ast = SemanticAST(filters=("even", "ge_k"), map_ops=(("mul_const", 2),), order_op="ascending")
        self.cases = generate_boundary_test_cases(self.ast, seed=1)

    def test_covers_the_homework_boundary_kinds(self):
        xss = [c["xs"] for c in self.cases]
        self.assertIn([], xss)
        self.assertTrue(any(len(x) == 1 for x in xss))
        self.assertTrue(any(len(x) > 1 and len(set(x)) == 1 for x in xss), "all elements equal")
        self.assertTrue(any(x and all(v < 0 for v in x) for x in xss), "negatives only")
        self.assertTrue(any(any(v < 0 for v in x) and any(v > 0 for v in x) for x in xss), "mixed signs")
        self.assertTrue(any(len(x) == XS_MAX_LEN for x in xss))

    def test_has_a_case_where_every_element_fails_the_filter(self):
        self.assertTrue(has_reject_all_case(self.ast, self.cases))

    def test_every_case_matches_the_reference_interpreter_and_stays_in_domain(self):
        for case in self.cases:
            self.assertEqual(interpret(self.ast, case["xs"], case["k"]), case["expected"])
            self.assertTrue(K_MIN <= case["k"] <= K_MAX)
            self.assertTrue(all(ELEMENT_MIN <= v <= ELEMENT_MAX for v in case["xs"]))

    def test_no_duplicate_inputs_and_deterministic(self):
        keys = [(tuple(c["xs"]), c["k"]) for c in self.cases]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertEqual(self.cases, generate_boundary_test_cases(self.ast, seed=1))

    def test_every_filtered_ast_in_the_dsl_has_an_all_rejected_case(self):
        for ast in enumerate_all():
            if ast.filters:
                self.assertTrue(has_reject_all_case(ast, generate_boundary_test_cases(ast)), ast.to_dict())


if __name__ == "__main__":
    unittest.main()
