"""Unit tests for ja_generator.py -- combining dictionary expressions into
one Japanese instruction per semantic AST, and saving the result. Pure
stdlib, no GPU or model required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import random
import re
import sys
import tempfile
import unittest
from pathlib import Path

_SEMANTIC_AST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SEMANTIC_AST))
sys.path.insert(0, str(_SEMANTIC_AST / "expressions_ja"))

from generator import enumerate_all  # noqa: E402
from ja_dictionary import ExpressionDictionary  # noqa: E402
from ja_fixture import fixture_dictionary  # noqa: E402
from ja_generator import (  # noqa: E402
    GOAL_FIRST,
    ORDINAL,
    PROCEDURE,
    SEQUENTIAL,
    TEMPLATES,
    JaRenderError,
    applicable_templates,
    contract_problems,
    instruction_record,
    leftover_placeholders,
    load_instructions,
    pool_violations,
    render,
    render_from_record,
    render_variants,
    save_instructions,
    seed_for,
    template_pools,
)
from schema import SemanticAST  # noqa: E402

A = SemanticAST.of


def text_of(ast: SemanticAST, dictionary: ExpressionDictionary) -> str:
    """The sequential type -- the composition rules of ja_generator_plan.md
    section 2, which the tests below check rule by rule."""
    return render(ast, dictionary, random.Random(0), templates=(SEQUENTIAL,)).text


def _replacing(dictionary: ExpressionDictionary, key: str, expressions: list) -> ExpressionDictionary:
    """A copy of ``dictionary`` with one key's expressions swapped out."""
    entries = dict(dictionary.entries)
    entries[key] = {"slot_type": entries[key]["slot_type"], "expressions": expressions}
    return ExpressionDictionary(entries)


class CompositionRules(unittest.TestCase):
    """ja_generator_plan.md section 2, rule by rule."""

    @classmethod
    def setUpClass(cls):
        cls.d = fixture_dictionary()

    def test_worked_example_from_the_plan(self):
        # ja_generator_plan.md 2.6 in 3 ops
        ast = A("filter:ge_k", "map:mul_const:2", "order:ascending")
        self.assertEqual(
            text_of(ast, self.d),
            "整数のリストxsについて、k以上の要素だけを残し、2倍して、昇順に並べるsolve関数を書いてください。",
        )

    def test_single_filter_uses_the_terminal_frame_when_it_is_the_only_op(self):
        ast = A("filter:even")
        self.assertEqual(
            text_of(ast, self.d), "整数のリストxsについて、偶数の要素だけを残すsolve関数を書いてください。"
        )

    def test_consecutive_filters_are_separate_clauses_in_op_order(self):
        """Stacking them into one 連体修飾 would impose the modifiers' natural
        reading order and hide the op order."""
        self.assertEqual(
            text_of(A("filter:even", "filter:gt_k"), self.d),
            "整数のリストxsについて、偶数の要素だけを残し、kより大きい要素だけを残すsolve関数を書いてください。",
        )
        self.assertEqual(
            text_of(A("filter:gt_k", "filter:even"), self.d),
            "整数のリストxsについて、kより大きい要素だけを残し、偶数の要素だけを残すsolve関数を書いてください。",
        )

    def test_consecutive_maps_chain_with_kara(self):
        self.assertIn("kを加えてから2倍して、", text_of(A("map:add_k", "map:mul_const:2", "order:ascending"), self.d))
        self.assertIn("2倍してからkを加える", text_of(A("order:ascending", "map:mul_const:2", "map:add_k"), self.d))

    def test_maps_separated_by_another_op_do_not_chain(self):
        text = text_of(A("map:add_k", "order:reverse", "map:add_k"), self.d)
        self.assertNotIn("から", text.removeprefix("整数のリストxsについて、"))
        self.assertEqual(text.count("kを加え"), 2)

    def test_last_op_uses_terminal_and_earlier_ones_use_te(self):
        ast = A("map:abs", "order:descending")
        text = text_of(ast, self.d)
        self.assertIn("絶対値を取って", text)  # te: not the last category
        self.assertIn("降順に並べる", text)  # terminal: last category
        self.assertNotIn("絶対値を取る", text)

    def test_mul_const_substitutes_its_constant_for_N(self):
        for const in (2, 3):
            ast = A(f"map:mul_const:{const}")
            text = text_of(ast, self.d)
            self.assertIn(f"{const}倍する", text)
            self.assertNotIn("N倍", text)

    def test_k_stays_a_literal_k(self):
        ast = A("filter:ge_k", "slice:take_last_k")
        self.assertIn("k以上の", text_of(ast, self.d))
        self.assertIn("末尾からk個", text_of(ast, self.d))

    def test_ops_appear_in_op_order(self):
        text = text_of(A("filter:odd", "map:negate", "slice:step_2"), self.d)
        self.assertLess(text.index("奇数の"), text.index("符号を反転"))
        self.assertLess(text.index("符号を反転"), text.index("1個おきに"))
        text = text_of(A("slice:step_2", "map:negate", "filter:odd"), self.d)
        self.assertLess(text.index("1個おきに"), text.index("符号を反転"))
        self.assertLess(text.index("符号を反転"), text.index("奇数の"))

    def test_opening_and_closing_frames_wrap_the_sentence(self):
        ast = A("order:reverse")
        text = text_of(ast, self.d)
        self.assertTrue(text.startswith("整数のリストxsについて、"))
        self.assertTrue(text.endswith("solve関数を書いてください。"))

    def test_clause_separator_is_not_doubled(self):
        # frame:opening already ends with 、 and the generator adds one too
        ast = A("filter:even", "order:ascending")
        self.assertNotIn("、、", text_of(ast, self.d))

    def test_no_comma_between_the_last_clause_and_the_noun_it_modifies(self):
        # that juncture is a 連体修飾 (「昇順に並べる」+「solve関数を…」): a 読点
        # on either side of it would cut the modifier loose from its noun
        dictionary = _replacing(
            self.d,
            "order:ascending",
            [{"terminal": "昇順に並べる、", "te": "昇順に並べて"}],
        )
        text = text_of(A("order:ascending"), dictionary)
        self.assertIn("昇順に並べるsolve関数", text)


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


class Contract(unittest.TestCase):
    """``contract_problems``: the entries the joining rules cannot join.

    Every rule is a *join* rule -- an entry that would come out ungrammatical
    no matter what the rest of the dictionary looks like. Judgement calls stay
    out (see the last test), because those are the human reviewer's.
    """

    def setUp(self):
        self.d = fixture_dictionary()

    def _problems(self, key: str, expressions: list) -> list[str]:
        return contract_problems(_replacing(self.d, key, expressions))

    def test_the_fixture_dictionary_composes(self):
        self.assertEqual(contract_problems(self.d), [])
        self.assertEqual(contract_problems(fixture_dictionary(extra_variants=True)), [])

    def test_a_fragment_ending_in_a_noun_is_reported(self):
        # "2で割り切れる値" + the frame's noun -> "...値要素だけを残す"
        problems = self._problems("filter:even", ["2で割り切れる値"])
        self.assertEqual(len(problems), 1)
        self.assertIn("filter:even[0]", problems[0])
        self.assertIn("値", problems[0])

    def test_a_fragment_that_narrows_by_itself_is_reported(self):
        # the frame already says 「だけを残す」
        self.assertTrue(self._problems("filter:ge_k", ["k以上の要素だけ"]))
        self.assertTrue(self._problems("filter:zero", ["0に等しいものだけを残す"]))

    def test_a_terminal_ending_in_a_noun_is_reported(self):
        problems = self._problems("map:add_k", [{"terminal": "kを加える動作", "te": "kを加えて"}])
        self.assertEqual(len(problems), 1)
        self.assertIn("map:add_k[0].terminal", problems[0])

    def test_a_fragment_ending_in_a_case_particle_is_reported(self):
        # 「k以上であるものから」 + 「要素だけを選ぶ」: a 連体修飾 never ends in a
        # case particle -- 「の」 excepted, since that is the adnominal one
        self.assertTrue(self._problems("filter:ge_k", ["k以上であるものから"]))
        self.assertEqual(self._problems("filter:ge_k", ["k以上の"]), [])

    def test_a_terminal_in_te_form_is_reported(self):
        # 「先頭からk個を取得して」 cannot head the 連体修飾 the closing needs
        problems = self._problems(
            "slice:take_first_k",
            [{"terminal": "先頭からk個を取得して", "te": "先頭からk個を取得して"}],
        )
        self.assertTrue(any("終止形" in p for p in problems), problems)

    def test_a_te_form_the_chain_connective_cannot_attach_to_is_reported(self):
        problems = self._problems("map:abs", [{"terminal": "絶対値にする", "te": "絶対値にします"}])
        self.assertEqual(len(problems), 1)
        self.assertIn("絶対値にしますから", problems[0])

    def test_order_te_forms_are_not_held_to_the_chain_rule(self):
        # order ops never chain (each is a clause of its own), so its te form
        # only ever meets a 読点 -- 連用形 without て is fine there
        self.assertEqual(
            self._problems("order:reverse", [{"terminal": "並びを逆にする", "te": "並びを逆にし"}]), []
        )

    def test_an_opening_that_presupposes_extraction_is_reported(self):
        problems = self._problems("frame:opening", ["整数リストxsから、"])
        self.assertEqual(len(problems), 1)
        self.assertIn("frame:opening[0]", problems[0])
        self.assertEqual(self._problems("frame:opening", ["整数のリストxsについて、"]), [])

    def test_a_closing_that_drops_solve_or_the_full_stop_is_reported(self):
        self.assertTrue(self._problems("frame:closing", ["この関数を書いてください。"]))
        self.assertTrue(self._problems("frame:closing", ["solve関数を書いてください"]))

    def test_judgement_calls_are_left_to_the_human_reviewer(self):
        # "実行してください" asks for solve to be *run* rather than written and
        # "求めしてください" is broken keigo: both are wrong, neither breaks a
        # join, so neither is this function's business
        self.assertEqual(
            self._problems(
                "frame:closing",
                ["solve関数を実行してください。", "solve関数を実行するよう求めしてください。"],
            ),
            [],
        )


class Variants(unittest.TestCase):
    def test_variants_are_distinct_and_reproducible(self):
        ast = A("filter:even", "map:add_k")
        dictionary = fixture_dictionary(extra_variants=True)
        first = [r.text for r in render_variants(ast, dictionary, n=4, seed=0)]
        second = [r.text for r in render_variants(ast, dictionary, n=4, seed=0)]
        self.assertEqual(first, second)
        self.assertEqual(len(set(first)), len(first))

    def test_a_one_expression_dictionary_yields_exactly_one_variant(self):
        ast = A("order:ascending")
        self.assertEqual(len(render_variants(ast, fixture_dictionary(), n=5, seed=0)), 1)

    def test_seed_is_derived_from_the_semantic_hash(self):
        a = A("order:ascending")
        b = A("order:descending")
        self.assertNotEqual(seed_for(a), seed_for(b))
        self.assertEqual(seed_for(a), seed_for(A("order:ascending")))


class ParaphrasePools(unittest.TestCase):
    def setUp(self):
        self.dictionary = fixture_dictionary(extra_variants=True)  # two expressions per key
        self.pools = template_pools(self.dictionary)

    def test_every_divisible_key_is_split_into_disjoint_non_empty_pools(self):
        for key in self.dictionary.keys():
            if key in self.pools.shared_keys:
                continue
            train, para = set(self.pools.train[key]), set(self.pools.paraphrase[key])
            self.assertTrue(train and para, key)
            self.assertFalse(train & para, key)
            self.assertEqual(train | para, set(range(len(self.dictionary.expressions(key)))))

    def test_frame_keys_are_shared_by_every_split(self):
        # the 言い換え is in the operation wording; reserving a quarter of the
        # frames only divides down how many sentences a split can spell
        frames = [k for k in self.dictionary.keys() if k.startswith("frame:")]
        self.assertTrue(frames)
        for key in frames:
            self.assertIn(key, self.pools.shared_keys)
            self.assertNotIn(key, self.pools.train)
            self.assertNotIn(key, self.pools.paraphrase)

    def test_a_single_expression_key_is_shared_and_reported(self):
        pools = template_pools(fixture_dictionary())
        self.assertEqual(set(pools.shared_keys), set(fixture_dictionary().keys()))
        self.assertEqual(pools.train, {})

    def test_training_renderings_never_use_a_reserved_template(self):
        for ast in enumerate_all()[:200]:
            for r in render_variants(ast, self.dictionary, n=4, seed=0, allowed=self.pools.train):
                self.assertEqual(pool_violations([c.to_dict() for c in r.choices], self.pools.train), [])
                self.assertNotEqual(pool_violations([c.to_dict() for c in r.choices], self.pools.paraphrase), [])

    def test_paraphrase_renderings_use_only_reserved_templates(self):
        for ast in enumerate_all()[:200]:
            for r in render_variants(ast, self.dictionary, n=4, seed=0, allowed=self.pools.paraphrase):
                self.assertEqual(pool_violations([c.to_dict() for c in r.choices], self.pools.paraphrase), [])

    def test_no_sentence_is_shared_between_the_two_pools(self):
        ast = A("filter:even", "map:add_k", "order:ascending")
        train = {r.text for r in render_variants(ast, self.dictionary, n=50, seed=0, allowed=self.pools.train)}
        para = {r.text for r in render_variants(ast, self.dictionary, n=50, seed=0, allowed=self.pools.paraphrase)}
        self.assertTrue(train and para)
        self.assertFalse(train & para)

    def test_pools_are_deterministic(self):
        self.assertEqual(self.pools, template_pools(self.dictionary))

    def test_restricted_renderings_still_replay_from_their_choices(self):
        ast = A("filter:even", "order:ascending")
        for r in render_variants(ast, self.dictionary, n=3, seed=0, allowed=self.pools.paraphrase):
            record = instruction_record(ast, [r], self.dictionary)
            self.assertEqual(render_from_record(record, self.dictionary), [r.text])


class MissingEntries(unittest.TestCase):
    def test_missing_key_raises_with_the_key_named(self):
        dictionary = ExpressionDictionary.from_expressions({"filter:even": ["偶数の"]})
        with self.assertRaises(Exception) as ctx:
            render(A("filter:even"), dictionary, random.Random(0))
        self.assertIn("frame:", str(ctx.exception))

    def test_empty_expression_list_raises(self):
        entries = dict(fixture_dictionary().entries)
        entries["order:ascending"] = {"slot_type": "ACTION_PAIR", "expressions": []}
        with self.assertRaises(JaRenderError):
            render(A("order:ascending"), ExpressionDictionary(entries), random.Random(0))


class SentenceTypes(unittest.TestCase):
    """The sentence types (ja_generator's module docstring). The fixture
    dictionary has one expression per key, so the only variance left is the
    glue."""

    @classmethod
    def setUpClass(cls):
        cls.d = fixture_dictionary()
        cls.fixed = A("filter:positive", "map:negate", "order:ascending")

    def _text(self, ast, template, seed=0):
        return render(ast, self.d, random.Random(seed), templates=(template,)).text

    def test_ordinal_marks_every_unit_in_order(self):
        text = self._text(self.fixed, ORDINAL)
        self.assertRegex(text, r"^整数のリストxsについて、(まず|最初に|はじめに)正の要素だけを残し、")
        self.assertRegex(text, r"(最後に|最終的に)昇順に並べるsolve関数を書いてください。$")
        self.assertLess(text.index("正の"), text.index("符号を反転"))
        self.assertLess(text.index("符号を反転"), text.index("昇順"))

    def test_procedure_puts_one_step_per_sentence(self):
        for seed in range(6):
            text = self._text(self.fixed, PROCEDURE, seed)
            head, _, steps = text.partition("solve関数を書いてください。")
            self.assertRegex(head, r"(次の手順で処理する|以下の手順で処理する|次の順に処理を行う)$")
            self.assertEqual(steps.count("。"), 3, text)
            self.assertTrue(
                steps.startswith("(1) 正の要素だけを残す。") or re.match(r"(まず|最初に|はじめに)、正", steps), text
            )

    def test_goal_first_reads_the_last_step_first_and_marks_it_with_mae_ni(self):
        text = self._text(self.fixed, GOAL_FIRST)
        self.assertTrue(text.startswith("整数のリストxsについて、昇順に並べるsolve関数を書いてください。"), text)
        self.assertRegex(text, r"(ただし|その際)、昇順に並べる前に、正の要素だけを残し、符号を反転する(こと。|ようにしてください。)$")

    def test_unit_types_need_two_units(self):
        self.assertEqual(applicable_templates(A("order:reverse")), (SEQUENTIAL,))
        self.assertEqual(applicable_templates(A("order:reverse", "slice:step_2")), TEMPLATES)
        self.assertEqual(applicable_templates(A("map:add_k", "map:add_k")), TEMPLATES)
        with self.assertRaises(JaRenderError):
            self._text(A("order:reverse"), ORDINAL)

    def test_every_type_tells_the_ops_in_op_order(self):
        for tags in (("filter:even", "slice:take_first_k"), ("slice:take_first_k", "filter:even")):
            first, second = ("偶数の", "先頭から") if tags[0] == "filter:even" else ("先頭から", "偶数の")
            for template in TEMPLATES:
                for seed in range(4):
                    text = self._text(A(*tags), template, seed)
                    if template == GOAL_FIRST:
                        # the last op is read first, and 「前に」 restores the order
                        self.assertRegex(text, f"{second}[^。]*前に、{first}", (template, text))
                    else:
                        self.assertLess(text.index(first), text.index(second), (template, text))

    def test_a_reordered_ast_never_gets_the_same_sentence(self):
        """Even ops that commute (filter and sort) are told in the AST's order,
        so the two orders are two different instructions."""
        dictionary = fixture_dictionary(extra_variants=True)
        a, b = A("filter:even", "order:ascending"), A("order:ascending", "filter:even")
        texts_a = {r.text for r in render_variants(a, dictionary, n=40, seed=0)}
        texts_b = {r.text for r in render_variants(b, dictionary, n=40, seed=0)}
        self.assertTrue(texts_a and texts_b)
        self.assertFalse(texts_a & texts_b)

    def test_narration_is_the_ast_order(self):
        for seed in range(10):
            self.assertEqual(render(self.fixed, self.d, random.Random(seed)).narration, self.fixed.tags())

    def test_every_type_renders_and_replays(self):
        dictionary = fixture_dictionary(extra_variants=True)
        rng = random.Random(0)
        used = set()
        for ast in rng.sample(enumerate_all(), 300):
            renderings = render_variants(ast, dictionary, n=6, seed=0)
            record = instruction_record(ast, renderings, dictionary)
            self.assertEqual(render_from_record(record, dictionary), record["instruction_ja"])
            for rendering in renderings:
                used.add(rendering.template)
                text = rendering.text
                self.assertEqual(leftover_placeholders(text), [], text)
                self.assertTrue(text.endswith("。"), text)
                for broken in ("、、", "。。", "、。", "{"):
                    self.assertNotIn(broken, text)
        self.assertEqual(used, set(TEMPLATES))


class Saving(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "instructions.jsonl"
        self.dictionary = fixture_dictionary(extra_variants=True)
        self.asts = [
            A("filter:ge_k", "map:mul_const:2", "order:ascending"),
            A("order:reverse"),
            A("map:square", "slice:take_last_k", "map:square"),
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
        self.assertIn("整数のリストxsについて", self.path.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
