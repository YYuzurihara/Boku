"""Unit tests for code_generator.py / code_verifier.py -- rendering a
semantic AST into Python source in every style, and holding the result to
the reference interpreter. Pure stdlib (the verifier runs snippets in
sandbox/runner.py's restricted namespace, no Docker needed).

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import ast
import sys
import tempfile
import unittest
from pathlib import Path

_SEMANTIC_AST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SEMANTIC_AST))
sys.path.insert(0, str(_SEMANTIC_AST / "expressions_code"))
sys.path.insert(0, str(_SEMANTIC_AST.parent / "sandbox"))

import ast_safety  # noqa: E402  (sandbox/ast_safety.py)

from code_generator import (  # noqa: E402
    CodeGenError,
    code_record,
    element_expr,
    load_codes,
    render,
    render_from_record,
    save_codes,
    variants,
)
from code_styles import STYLES, STYLES_BY_NAME, styles_for  # noqa: E402
from code_verifier import cross_check, ok, verify, verify_variant  # noqa: E402
from generator import enumerate_all  # noqa: E402
from reference_interpreter import interpret  # noqa: E402
from schema import SemanticAST  # noqa: E402
from testcases import generate_test_cases  # noqa: E402

# homework.md's worked example: "整数リストxsからk以上の偶数だけを残し、それ
# ぞれを2倍して昇順に並べる".
WORKED_EXAMPLE = SemanticAST(
    filters=("even", "ge_k"), map_ops=(("mul_const", 2),), order_op="ascending"
)


def sample_asts(n: int) -> list[SemanticAST]:
    """One semantic AST per structural shape, then a deterministic spread --
    enough coverage for a unit test without enumerating all 40,589."""
    by_shape: dict[tuple, SemanticAST] = {}
    every = enumerate_all()
    for ast in every:
        shape = (ast.active_categories(), len(ast.filters), len(ast.map_ops), len(ast.slice_ops))
        by_shape.setdefault(shape, ast)
    chosen = list(by_shape.values())
    step = max(1, len(every) // n)
    chosen += every[::step][: max(0, n - len(chosen))]
    return chosen


class RenderTest(unittest.TestCase):
    def test_worked_example_matches_homework_md(self):
        """homework.md's 期待されるコードの一例, byte for byte."""
        expected = (
            "def solve(xs: list[int], k: int) -> list[int]:\n"
            "    return sorted([x * 2 for x in xs if x >= k and x % 2 == 0])\n"
        )
        self.assertEqual(render(WORKED_EXAMPLE, STYLES_BY_NAME["condition_swapped"]), expected)

    def test_condition_order_axis_swaps_the_predicates(self):
        plain = render(WORKED_EXAMPLE, STYLES_BY_NAME["list_comprehension"])
        swapped = render(WORKED_EXAMPLE, STYLES_BY_NAME["condition_swapped"])
        self.assertIn("if x % 2 == 0 and x >= k", plain)
        self.assertIn("if x >= k and x % 2 == 0", swapped)

    def test_every_style_renders_valid_safe_code(self):
        for ast in sample_asts(120):
            for style in styles_for(ast):
                code = render(ast, style)
                try:
                    ast_safety.verify_static(code)
                except (SyntaxError, ast_safety.UnsafeCodeError) as exc:
                    self.fail(f"{ast.to_dict()} [{style.name}]: {exc}\n{code}")

    def test_annotation_axis(self):
        annotated = render(WORKED_EXAMPLE, STYLES_BY_NAME["list_comprehension"])
        bare = render(WORKED_EXAMPLE, STYLES_BY_NAME["list_comprehension_bare"])
        self.assertIn("def solve(xs: list[int], k: int) -> list[int]:", annotated)
        self.assertIn("def solve(xs, k):", bare)
        self.assertNotIn("list[int]", bare)

    def test_comment_axis(self):
        for style in STYLES:
            ast = SemanticAST(filters=("even",), order_op="reverse")
            if not style.applies_to(ast):
                continue
            code = render(ast, style)
            self.assertEqual("#" in code, style.comments, f"{style.name}:\n{code}")

    def test_loop_styles_use_a_for_loop_and_comprehension_styles_do_not(self):
        for style in STYLES:
            code = render(WORKED_EXAMPLE, style) if style.applies_to(WORKED_EXAMPLE) else None
            if code is None:
                continue
            tree = ast.parse(code)
            has_loop = any(isinstance(node, ast.For) for node in ast.walk(tree))
            has_comprehension = any(isinstance(node, ast.ListComp) for node in ast.walk(tree))
            self.assertEqual(has_loop, style.form == "loop", f"{style.name}:\n{code}")
            self.assertEqual(has_comprehension, style.form == "comprehension", f"{style.name}:\n{code}")

    def test_reverse_spelling_axis(self):
        descending = SemanticAST(filters=("even",), order_op="descending")
        self.assertIn("reverse=True", render(descending, STYLES_BY_NAME["list_comprehension"]))
        self.assertIn("[::-1]", render(descending, STYLES_BY_NAME["explicit_reverse"]))
        self.assertIn(".sort(reverse=True)", render(descending, STYLES_BY_NAME["for_loop"]))
        self.assertIn(".reverse()", render(descending, STYLES_BY_NAME["for_loop_explicit_reverse"]))

    def test_unknown_operation_is_rejected(self):
        with self.assertRaises(CodeGenError):
            element_expr((("teleport", None),), "x")


class PrecedenceTest(unittest.TestCase):
    """Chained map operations compose into one expression, so the text has to
    be parenthesised by precedence -- ``-x ** 2`` is not ``(-x) ** 2``."""

    def test_chains_are_parenthesised_correctly(self):
        for map_ops, expected in (
            ((("add_k", None), ("mul_const", 2)), "(x + k) * 2"),
            ((("mul_const", 2), ("add_k", None)), "x * 2 + k"),
            ((("negate", None), ("square", None)), "(-x) ** 2"),
            ((("square", None), ("negate", None)), "-x ** 2"),
            ((("abs", None), ("sub_k", None)), "abs(x) - k"),
            ((("sub_k", None), ("abs", None)), "abs(x - k)"),
            ((("add_k", None), ("square", None)), "(x + k) ** 2"),
            ((("mul_k", None), ("negate", None)), "-(x * k)"),
        ):
            self.assertEqual(element_expr(map_ops, "x").text, expected, map_ops)

    def test_parenthesisation_agrees_with_the_interpreter(self):
        """Every ordered pair of map ops, against the interpreter."""
        pairs = [ast for ast in enumerate_all() if len(ast.map_ops) == 2 and not ast.filters]
        self.assertGreater(len(pairs), 0)
        for semantic_ast in pairs:
            code = render(semantic_ast, STYLES_BY_NAME["list_comprehension"])
            namespace: dict = {}
            exec(compile(code, "<test>", "exec"), namespace)  # noqa: S102 - our own generated code
            for xs, k in (([-3, 0, 2, 7], 3), ([-100, 100], 10), ([], 1)):
                self.assertEqual(
                    namespace["solve"](list(xs), k),
                    interpret(semantic_ast, xs, k),
                    f"{semantic_ast.to_dict()} on xs={xs} k={k}\n{code}",
                )


class VerificationTest(unittest.TestCase):
    """The cross-check homework.md asks for: 「両者の出力をランダムテストで比較
    する。これにより、コード生成器自身のバグを検出する」."""

    def test_every_style_of_a_sample_matches_the_reference_interpreter(self):
        for semantic_ast in sample_asts(60):
            tests = generate_test_cases(semantic_ast, seed=7, n_random=8)
            for variant in variants(semantic_ast):
                verification = verify_variant(variant, tests)
                self.assertTrue(
                    ok(verification),
                    f"{semantic_ast.to_dict()} [{variant.style.name}]: {verification}\n{variant.code}",
                )

    def test_generated_code_does_not_mutate_its_input(self):
        """The loop styles build their own list; ``xs.sort()`` would pass the
        tests and still be wrong (the interpreter copies)."""
        semantic_ast = SemanticAST(order_op="ascending", slice_ops=("take_first_k",))
        for variant in variants(semantic_ast):
            verification = verify_variant(variant, generate_test_cases(semantic_ast, seed=3, n_random=4))
            self.assertTrue(verification["pure"], f"{variant.style.name}\n{variant.code}")

    def test_verify_reports_instead_of_raising(self):
        broken = verify("def solve(xs, k)\n    return xs\n", [])
        self.assertFalse(broken["syntax_ok"])
        self.assertIn("SyntaxError", broken["error"])

        unsafe = verify("import os\ndef solve(xs, k):\n    return xs\n", [])
        self.assertTrue(unsafe["syntax_ok"])
        self.assertFalse(unsafe["ast_safe"])

        wrong = verify(
            "def solve(xs, k):\n    return []\n",
            generate_test_cases(WORKED_EXAMPLE, seed=1, n_random=4),
        )
        self.assertTrue(wrong["ast_safe"])
        self.assertFalse(wrong["tests_passed"])
        self.assertIn("failures", wrong)

    def test_cross_check_uses_fresh_inputs(self):
        code = render(WORKED_EXAMPLE, STYLES_BY_NAME["for_loop"])
        self.assertTrue(ok(cross_check(WORKED_EXAMPLE, code, seed=99, n_random=8)))


class VariantTest(unittest.TestCase):
    def test_n_bounds_and_distinctness(self):
        semantic_ast = SemanticAST(filters=("even", "ge_k"), order_op="descending")
        some = variants(semantic_ast, n=3)
        self.assertEqual(len(some), 3)
        self.assertEqual(len({v.code for v in some}), 3)
        self.assertEqual(len({v.style.name for v in some}), 3)

    def test_all_variants_are_distinct_sources(self):
        for semantic_ast in sample_asts(60):
            generated = variants(semantic_ast)
            self.assertEqual(
                len({v.code for v in generated}),
                len(generated),
                f"{semantic_ast.to_dict()}: two styles rendered the same source",
            )

    def test_code_sha256_identifies_the_source(self):
        generated = variants(WORKED_EXAMPLE, n=2)
        self.assertNotEqual(generated[0].code_sha256, generated[1].code_sha256)
        self.assertEqual(generated[0].code_sha256, variants(WORKED_EXAMPLE, n=2)[0].code_sha256)


class RecordTest(unittest.TestCase):
    def test_round_trip_through_jsonl(self):
        generated = variants(WORKED_EXAMPLE, n=3)
        record = code_record(WORKED_EXAMPLE, generated, spec_id="train-000042")
        with tempfile.TemporaryDirectory() as tmp:
            path = save_codes([record], Path(tmp) / "code_train.jsonl")
            loaded = load_codes(path)
        self.assertEqual(loaded, [record])
        self.assertEqual(render_from_record(loaded[0]), [v.code for v in generated])
        self.assertEqual(loaded[0]["spec_id"], "train-000042")
        self.assertEqual(loaded[0]["semantic_hash"], WORKED_EXAMPLE.semantic_hash())

    def test_verifications_are_attached_per_snippet(self):
        generated = variants(WORKED_EXAMPLE, n=2)
        tests = generate_test_cases(WORKED_EXAMPLE, seed=5, n_random=4)
        record = code_record(
            WORKED_EXAMPLE, generated, verifications=[verify_variant(v, tests) for v in generated]
        )
        self.assertTrue(all(entry["verification"]["tests_passed"] for entry in record["codes"]))
        with self.assertRaises(CodeGenError):
            code_record(WORKED_EXAMPLE, generated, verifications=[{}])

    def test_unknown_style_in_a_record_is_rejected(self):
        record = code_record(WORKED_EXAMPLE, variants(WORKED_EXAMPLE, n=1))
        record["codes"][0]["code_style"] = "handwritten"
        with self.assertRaises(CodeGenError):
            render_from_record(record)


if __name__ == "__main__":
    unittest.main()
