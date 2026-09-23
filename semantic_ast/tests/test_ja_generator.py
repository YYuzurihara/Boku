"""Unit tests for ja_generator.py -- combining dictionary expressions into
one Japanese instruction per semantic AST, and saving the result. Pure
stdlib, no GPU or model required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import random
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import enumerate_all  # noqa: E402
from ja_dictionary import ExpressionDictionary  # noqa: E402
from ja_fixture import fixture_dictionary  # noqa: E402
from ja_generator import (  # noqa: E402
    JaRenderError,
    instruction_record,
    leftover_placeholders,
    load_instructions,
    render,
    render_from_record,
    render_variants,
    save_instructions,
    seed_for,
)
from schema import SemanticAST  # noqa: E402


def text_of(ast: SemanticAST, dictionary: ExpressionDictionary) -> str:
    return render(ast, dictionary, random.Random(0)).text


class CompositionRules(unittest.TestCase):
    """ja_generator_plan.md section 2, rule by rule."""

    @classmethod
    def setUpClass(cls):
        cls.d = fixture_dictionary()

    def test_worked_example_from_the_plan(self):
        # ja_generator_plan.md 2.6, verbatim
        ast = SemanticAST(
            filters=("ge_k", "even"),
            map_ops=(("add_k", None), ("mul_const", 2)),
            order_op="ascending",
        )
        self.assertEqual(
            text_of(ast, self.d),
            "整数リストxsから、k以上の偶数の要素だけを残し、kを加えてから2倍して、昇順に並べるsolve関数を書いてください。",
        )

    def test_single_filter_uses_the_terminal_frame_when_it_is_the_only_category(self):
        ast = SemanticAST(filters=("even",))
        self.assertEqual(
            text_of(ast, self.d), "整数リストxsから、偶数の要素だけを残すsolve関数を書いてください。"
        )

    def test_two_filters_are_concatenated_into_one_fragment(self):
        ast = SemanticAST(filters=("ge_k", "even"))
        self.assertIn("k以上の偶数の要素だけを残す", text_of(ast, self.d))

    def test_last_category_uses_terminal_and_earlier_ones_use_te(self):
        ast = SemanticAST(map_ops=(("abs", None),), order_op="descending")
        text = text_of(ast, self.d)
        self.assertIn("絶対値を取って", text)  # te: not the last category
        self.assertIn("降順に並べる", text)  # terminal: last category
        self.assertNotIn("絶対値を取る", text)

    def test_chain_inserts_the_kara_connective(self):
        ast = SemanticAST(map_ops=(("add_k", None), ("square", None)))
        self.assertIn("kを加えてから二乗する", text_of(ast, self.d))

    def test_chain_keeps_the_semantic_ast_order(self):
        forward = SemanticAST(slice_ops=("take_first_k", "step_2"))
        backward = SemanticAST(slice_ops=("step_2", "take_first_k"))
        self.assertIn("先頭からk個を取り出してから1個おきに取り出す", text_of(forward, self.d))
        self.assertIn("1個おきに取り出してから先頭からk個を取り出す", text_of(backward, self.d))

    def test_mul_const_substitutes_its_constant_for_N(self):
        for const in (2, 3):
            ast = SemanticAST(map_ops=(("mul_const", const),))
            text = text_of(ast, self.d)
            self.assertIn(f"{const}倍する", text)
            self.assertNotIn("N倍", text)

    def test_k_stays_a_literal_k(self):
        ast = SemanticAST(filters=("ge_k",), slice_ops=("take_last_k",))
        self.assertIn("k以上の", text_of(ast, self.d))
        self.assertIn("末尾からk個", text_of(ast, self.d))

    def test_categories_appear_in_pipeline_order(self):
        ast = SemanticAST(filters=("odd",), map_ops=(("negate", None),), slice_ops=("step_2",))
        text = text_of(ast, self.d)
        self.assertLess(text.index("奇数の"), text.index("符号を反転"))
        self.assertLess(text.index("符号を反転"), text.index("1個おきに"))

    def test_opening_and_closing_frames_wrap_the_sentence(self):
        ast = SemanticAST(order_op="reverse")
        text = text_of(ast, self.d)
        self.assertTrue(text.startswith("整数リストxsから、"))
        self.assertTrue(text.endswith("solve関数を書いてください。"))

    def test_clause_separator_is_not_doubled(self):
        # frame:opening already ends with 、 and the generator adds one too
        ast = SemanticAST(filters=("even",), order_op="ascending")
        self.assertNotIn("、、", text_of(ast, self.d))


class EveryAstRenders(unittest.TestCase):
    def test_a_spread_of_semantic_asts_renders_without_leftovers(self):
        dictionary = fixture_dictionary()
        rng = random.Random(0)
        all_asts = enumerate_all()
        for ast in rng.sample(all_asts, 500):
            text = render(ast, dictionary, rng).text
            self.assertEqual(leftover_placeholders(text), [], text)
            self.assertTrue(text.endswith("。"), text)
            self.assertNotIn("{", text, text)

    def test_every_op_is_reachable_from_the_fixture_dictionary(self):
        dictionary = fixture_dictionary()
        rng = random.Random(0)
        for ast in enumerate_all()[:2000]:
            render(ast, dictionary, rng)  # must not raise


class Variants(unittest.TestCase):
    def test_variants_are_distinct_and_reproducible(self):
        ast = SemanticAST(filters=("even",), map_ops=(("add_k", None),))
        dictionary = fixture_dictionary(extra_variants=True)
        first = [r.text for r in render_variants(ast, dictionary, n=4, seed=0)]
        second = [r.text for r in render_variants(ast, dictionary, n=4, seed=0)]
        self.assertEqual(first, second)
        self.assertEqual(len(set(first)), len(first))

    def test_a_one_expression_dictionary_yields_exactly_one_variant(self):
        ast = SemanticAST(order_op="ascending")
        self.assertEqual(len(render_variants(ast, fixture_dictionary(), n=5, seed=0)), 1)

    def test_seed_is_derived_from_the_semantic_hash(self):
        a = SemanticAST(order_op="ascending")
        b = SemanticAST(order_op="descending")
        self.assertNotEqual(seed_for(a), seed_for(b))
        self.assertEqual(seed_for(a), seed_for(SemanticAST(order_op="ascending")))


class MissingEntries(unittest.TestCase):
    def test_missing_key_raises_with_the_key_named(self):
        dictionary = ExpressionDictionary.from_expressions({"filter:even": ["偶数の"]})
        with self.assertRaises(Exception) as ctx:
            render(SemanticAST(filters=("even",)), dictionary, random.Random(0))
        self.assertIn("frame:", str(ctx.exception))

    def test_empty_expression_list_raises(self):
        entries = dict(fixture_dictionary().entries)
        entries["order:ascending"] = {"slot_type": "ACTION_PAIR", "expressions": []}
        with self.assertRaises(JaRenderError):
            render(SemanticAST(order_op="ascending"), ExpressionDictionary(entries), random.Random(0))


class Saving(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "instructions.jsonl"
        self.dictionary = fixture_dictionary(extra_variants=True)
        self.asts = [
            SemanticAST(filters=("ge_k", "even"), map_ops=(("add_k", None), ("mul_const", 2)), order_op="ascending"),
            SemanticAST(order_op="reverse"),
            SemanticAST(map_ops=(("square", None),), slice_ops=("step_2", "take_last_k")),
        ]

    def tearDown(self):
        self.tmp.cleanup()

    def _records(self):
        return [
            instruction_record(
                ast,
                render_variants(ast, self.dictionary, n=3, seed=0),
                self.dictionary,
                spec_id=f"test-{i:03d}",
                seed=0,
            )
            for i, ast in enumerate(self.asts)
        ]

    def test_records_round_trip_through_jsonl(self):
        records = self._records()
        save_instructions(records, self.path)
        self.assertEqual(load_instructions(self.path), records)

    def test_record_carries_ast_hash_and_dictionary_provenance(self):
        record = self._records()[0]
        self.assertEqual(record["spec_id"], "test-000")
        self.assertEqual(record["semantic_hash"], self.asts[0].semantic_hash())
        self.assertEqual(record["semantic_ast"], self.asts[0].to_dict())
        self.assertEqual(record["dictionary_sha256"], self.dictionary.content_sha256())
        self.assertEqual(len(record["instruction_ja"]), len(record["renderings"]))

    def test_saved_sentences_replay_from_their_recorded_choices(self):
        save_instructions(self._records(), self.path)
        for record in load_instructions(self.path):
            self.assertEqual(render_from_record(record, self.dictionary), record["instruction_ja"])

    def test_replay_detects_a_changed_dictionary(self):
        records = self._records()
        shrunk = ExpressionDictionary.from_expressions({k: [] for k in self.dictionary.keys()})
        with self.assertRaises(JaRenderError):
            render_from_record(records[0], shrunk)

    def test_japanese_is_saved_unescaped(self):
        save_instructions(self._records(), self.path)
        self.assertIn("整数リストxsから", self.path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
