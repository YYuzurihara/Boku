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
import types
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
from code_verifier import MAX_CODE_LINES, MAX_LINE_CHARS, check_length, cross_check, ok, verify, verify_variant  # noqa: E402
from generator import enumerate_all  # noqa: E402
from reference_interpreter import interpret  # noqa: E402
from schema import AtomicOp, SemanticAST  # noqa: E402
from testcases import generate_test_cases  # noqa: E402

# homework.md's worked example ("整数リストxsからk以上の偶数だけを残し、それ
# ぞれを2倍して昇順に並べる") in 3 ops: k以上 is dropped.
WORKED_EXAMPLE = SemanticAST.of("filter:even", "map:mul_const:2", "order:ascending")


def sample_asts(n: int) -> list[SemanticAST]:
    """One semantic AST per category sequence (84), then a deterministic
    spread -- enough coverage for a unit test without verifying all 14,424."""
    by_shape: dict[tuple, SemanticAST] = {}
    every = enumerate_all()
    for ast in every:
        by_shape.setdefault(ast.categories(), ast)
    chosen = list(by_shape.values())
    step = max(1, len(every) // n)
    chosen += every[::step][: max(0, n - len(chosen))]
    return chosen


class RenderTest(unittest.TestCase):
    def test_worked_example_matches_homework_md(self):
        """homework.md's 期待されるコードの一例, byte for byte, minus the
        second condition."""
        expected = (
            "def solve(xs: list[int], k: int) -> list[int]:\n"
            "    return sorted([x * 2 for x in xs if x % 2 == 0])\n"
        )
        self.assertEqual(render(WORKED_EXAMPLE, STYLES_BY_NAME["list_comprehension"]), expected)

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
            ast = SemanticAST.of("filter:even", "order:reverse")
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
        reverse = SemanticAST.of("filter:even", "order:reverse")
        self.assertIn("[::-1]", render(reverse, STYLES_BY_NAME["list_comprehension"]))
        self.assertIn("list(reversed(", render(reverse, STYLES_BY_NAME["explicit_reverse"]))
        self.assertIn("result.reverse()", render(reverse, STYLES_BY_NAME["for_loop"]))
        self.assertIn("result = result[::-1]", render(reverse, STYLES_BY_NAME["for_loop_explicit_reverse"]))

    def test_descending_has_one_spelling_distinct_from_ascending_then_reverse(self):
        """``sorted(xs)[::-1]`` is what ascending-then-reverse renders to, so
        descending never uses it (two ASTs must not share a code)."""
        descending = SemanticAST.of("order:descending")
        for style in styles_for(descending):
            code = render(descending, style)
            self.assertIn("reverse=True", code, style.name)
            self.assertNotIn("[::-1]", code, style.name)

    def test_unknown_operation_is_rejected(self):
        with self.assertRaises(CodeGenError):
            element_expr((types.SimpleNamespace(category="map", name="teleport", arg=None),), "x")


class MapExpressionTest(unittest.TestCase):
    def test_each_map_op(self):
        for tag, expected in (
            ("map:add_k", "x + k"),
            ("map:sub_k", "x - k"),
            ("map:mul_k", "x * k"),
            ("map:mul_const:3", "x * 3"),
            ("map:negate", "-x"),
            ("map:abs", "abs(x)"),
            ("map:square", "x ** 2"),
        ):
            self.assertEqual(element_expr((AtomicOp.from_tag(tag),), "x").text, expected, tag)

    def test_chained_maps_are_parenthesised_by_precedence_in_op_order(self):
        for tags, expected in (
            (("map:add_k", "map:mul_const:2"), "(x + k) * 2"),
            (("map:mul_const:2", "map:add_k"), "x * 2 + k"),
            (("map:negate", "map:square"), "(-x) ** 2"),
            (("map:square", "map:negate"), "-x ** 2"),
            (("map:negate", "map:negate"), "-(-x)"),
            (("map:square", "map:square"), "(x ** 2) ** 2"),
            (("map:add_k", "map:sub_k", "map:abs"), "abs(x + k - k)"),
        ):
            self.assertEqual(element_expr(tuple(AtomicOp.from_tag(t) for t in tags), "x").text, expected, tags)

    def test_every_map_op_agrees_with_the_interpreter(self):
        maps = [ast for ast in enumerate_all() if ast.categories() == ("map",)]
        self.assertEqual(len(maps), 8)
        for semantic_ast in maps:
            code = render(semantic_ast, STYLES_BY_NAME["list_comprehension"])
            namespace: dict = {}
            exec(compile(code, "<test>", "exec"), namespace)  # noqa: S102 - our own generated code
            for xs, k in (([-3, 0, 2, 7], 3), ([-100, 100], 10), ([], 1)):
                self.assertEqual(
                    namespace["solve"](list(xs), k),
                    interpret(semantic_ast, xs, k),
                    f"{semantic_ast.to_dict()} on xs={xs} k={k}\n{code}",
                )


class LengthCheckTest(unittest.TestCase):
    """homework.md's 「長さ上限を超えない」."""

    def test_every_generated_variant_is_within_limits(self):
        for semantic_ast in sample_asts(60):
            for variant in variants(semantic_ast):
                self.assertIsNone(check_length(variant.code), variant.code)

    def test_too_many_lines_is_rejected(self):
        code = "def solve(xs, k):\n" + "    pass\n" * MAX_CODE_LINES
        reason = check_length(code)
        self.assertIsNotNone(reason)
        self.assertIn("too many lines", reason)

    def test_line_too_long_is_rejected(self):
        code = f"def solve(xs, k):\n    return [{'x, ' * MAX_LINE_CHARS}]\n"
        reason = check_length(code)
        self.assertIsNotNone(reason)
        self.assertIn("line too long", reason)

    def test_verify_reports_length_ok_and_short_circuits_on_failure(self):
        too_long = "def solve(xs, k):\n" + "    pass\n" * (MAX_CODE_LINES + 1)
        verification = verify(too_long, [])
        self.assertFalse(verification["length_ok"])
        self.assertFalse(verification["syntax_ok"])  # never reached
        self.assertIn("length limit exceeded", verification["error"])

        ok_code = "def solve(xs, k):\n    return xs\n"
        self.assertTrue(verify(ok_code, [])["length_ok"])


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
        semantic_ast = SemanticAST.of("order:ascending", "slice:take_first_k")
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
        semantic_ast = SemanticAST.of("filter:even", "order:descending")
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


class OrderPreservingTest(unittest.TestCase):
    """The code follows ``ast.ops`` in order, so ASTs that differ only in the
    order (or repetition) of their ops never share a code (code_generator.py,
    "Order-preserving rendering")."""

    def test_no_two_asts_share_a_rendering_in_any_style(self):
        owner: dict[str, str] = {}
        for semantic_ast in enumerate_all():
            h = semantic_ast.semantic_hash()
            for style in styles_for(semantic_ast):
                code = render(semantic_ast, style)
                other = owner.setdefault(code, h)
                self.assertEqual(other, h, f"{semantic_ast.tags()} [{style.name}] renders like another AST:\n{code}")

    def test_reordering_the_same_ops_changes_the_code_in_every_style(self):
        a = SemanticAST.of("filter:even", "order:ascending")
        b = SemanticAST.of("order:ascending", "filter:even")
        for style in styles_for(a):
            self.assertNotEqual(render(a, style), render(b, style), style.name)

    def test_every_style_matches_the_interpreter_on_reordered_and_repeated_asts(self):
        for tags in (
            ("order:ascending", "map:negate"),
            ("slice:take_first_k", "filter:even", "slice:take_first_k"),
            ("map:square", "filter:gt_k", "map:sub_k"),
            ("order:reverse", "order:reverse", "order:reverse"),
            ("filter:odd", "filter:odd", "map:abs"),
            ("map:mul_const:3", "order:descending", "filter:multiple_of_k"),
        ):
            semantic_ast = SemanticAST.of(*tags)
            tests = generate_test_cases(semantic_ast, seed=5, n_random=8)
            for variant in variants(semantic_ast):
                verification = verify_variant(variant, tests)
                self.assertTrue(ok(verification), f"{tags} [{variant.style.name}]: {verification}\n{variant.code}")

    def test_consecutive_filters_join_their_conditions_in_op_order(self):
        style = STYLES_BY_NAME["list_comprehension"]
        self.assertIn("if x % 2 == 0 and x > 0]", render(SemanticAST.of("filter:even", "filter:positive"), style))
        self.assertIn("if x > 0 and x % 2 == 0]", render(SemanticAST.of("filter:positive", "filter:even"), style))

    def test_a_filter_after_a_map_is_a_new_stage(self):
        code = render(SemanticAST.of("map:mul_const:2", "filter:even"), STYLES_BY_NAME["list_comprehension"])
        self.assertIn("return [x for x in [x * 2 for x in xs] if x % 2 == 0]", code)

    def test_a_loop_after_a_slice_refills_a_buffer(self):
        semantic_ast = SemanticAST.of("slice:take_first_k", "filter:even")
        code = render(semantic_ast, STYLES_BY_NAME["for_loop"])
        self.assertIn("for x in result:", code)
        self.assertIn("tmp.append(x)", code)
        self.assertIn("result = tmp", code)

    def test_one_expression_nests_in_op_order(self):
        semantic_ast = SemanticAST.of("slice:take_first_k", "filter:even")
        self.assertIn("return [x for x in xs[:k] if x % 2 == 0]", render(semantic_ast, STYLES_BY_NAME["list_comprehension"]))

    def test_staged_names_of_a_repeated_category_get_a_suffix(self):
        code = render(SemanticAST.of("filter:even", "order:ascending", "filter:positive"), STYLES_BY_NAME["comprehension_staged_typed"])
        self.assertIn("kept: list[int] = [x for x in xs if x % 2 == 0]", code)
        self.assertIn("kept_2: list[int] = [x for x in ordered if x > 0]", code)
        self.assertIn("return kept_2", code)

if __name__ == "__main__":
    unittest.main()
