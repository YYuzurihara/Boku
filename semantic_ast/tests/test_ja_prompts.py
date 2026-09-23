"""Unit tests for ja_prompts.py. Pure stdlib, no GPU or model required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

_SEMANTIC_AST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SEMANTIC_AST))
sys.path.insert(0, str(_SEMANTIC_AST / "expressions_ja"))

from generator import enumerate_all  # noqa: E402
from ja_prompts import (  # noqa: E402
    ACTION_PAIR,
    FRAG_PREFIX_PATTERN,
    ADNOMINAL,
    FRAG_PLACEHOLDER,
    PRIMITIVES,
    SYSTEM_PROMPT,
    TEMPLATES,
    TEXT,
    action_pair_schema,
    build_messages,
    dictionary_key_for_op_tag,
    json_schema,
    prompt_record,
    prompt_sha256,
    render_user_prompt,
    string_list_schema,
)
from schema import ALL_FILTER_OPS, ALL_MAP_OP_NAMES, ORDER_OPS, SLICE_OPS  # noqa: E402


class PrimitiveTable(unittest.TestCase):
    def test_covers_every_op_in_the_schema_vocabulary(self):
        expected = (
            {f"filter:{op}" for op in ALL_FILTER_OPS}
            | {f"map:{op}" for op in ALL_MAP_OP_NAMES}
            | {f"order:{op}" for op in ORDER_OPS}
            | {f"slice:{op}" for op in SLICE_OPS}
            | {"frame:filter_verb", "frame:opening", "frame:closing"}
        )
        self.assertEqual(set(PRIMITIVES), expected)

    def test_row_count_matches_the_documented_table(self):
        # filter 10 + map 7 + order 3 + slice 3 + frame 3
        self.assertEqual(len(PRIMITIVES), 26)

    def test_slot_types_match_ja_generator_plan(self):
        for key, spec in PRIMITIVES.items():
            if key.startswith("filter:"):
                self.assertEqual(spec.slot_type, ADNOMINAL, key)
            elif key in ("frame:opening", "frame:closing"):
                self.assertEqual(spec.slot_type, TEXT, key)
            else:
                self.assertEqual(spec.slot_type, ACTION_PAIR, key)

    def test_every_op_tag_of_every_ast_maps_to_a_known_key(self):
        # the dictionary must be able to answer for any semantic AST the
        # generator can produce -- mul_const's constant lives in the
        # expression (placeholder N), not in the key
        tags = {tag for ast in enumerate_all() for tag in ast.op_tags()}
        for tag in tags:
            self.assertIn(dictionary_key_for_op_tag(tag), PRIMITIVES, tag)

    def test_mul_const_op_tags_collapse_to_one_key(self):
        self.assertEqual(dictionary_key_for_op_tag("map:mul_const:2"), "map:mul_const")
        self.assertEqual(dictionary_key_for_op_tag("map:mul_const:3"), "map:mul_const")
        self.assertEqual(dictionary_key_for_op_tag("filter:even"), "filter:even")


class Rendering(unittest.TestCase):
    def test_no_substitution_site_is_left_unfilled(self):
        for key, spec in PRIMITIVES.items():
            prompt = render_user_prompt(spec)
            leftovers = [
                name
                for name in (
                    "{count}",
                    "{description}",
                    "{var_note}",
                    "{role}",
                    "{role_description}",
                    "{ending_note}",
                    "{boundary_note}",
                )
                if name in prompt
            ]
            self.assertEqual(leftovers, [], f"{key} left {leftovers} unfilled")

    def test_count_matches_the_schema_bounds(self):
        for key, spec in PRIMITIVES.items():
            self.assertIn(f"{spec.min_items}〜{spec.max_items}", render_user_prompt(spec), key)
            schema = json_schema(spec)
            self.assertEqual(schema["properties"]["expressions"]["minItems"], spec.min_items)
            self.assertEqual(schema["properties"]["expressions"]["maxItems"], spec.max_items)

    def test_filter_verb_prompt_keeps_the_literal_frag_placeholder(self):
        # {{frag}} in the template must survive .format() as {frag}, which is
        # what the model has to echo back for ja_generator.py to substitute
        prompt = render_user_prompt(PRIMITIVES["frame:filter_verb"])
        self.assertIn(FRAG_PLACEHOLDER, prompt)
        self.assertNotIn("{{frag}}", prompt)

    def test_frame_prompts_carry_their_role_text(self):
        opening = render_user_prompt(PRIMITIVES["frame:opening"])
        self.assertIn("「書き出し」", opening)
        self.assertIn("読点「、」で終える", opening)
        closing = render_user_prompt(PRIMITIVES["frame:closing"])
        self.assertIn("「結び」", closing)
        self.assertIn("句点「。」で終える", closing)

    def test_k_primitives_ask_for_the_literal_variable_name(self):
        for key in ("filter:ge_k", "map:add_k", "slice:take_first_k"):
            self.assertIn("アルファベットの「k」", render_user_prompt(PRIMITIVES[key]), key)
        self.assertIn("アルファベット大文字の「N」", render_user_prompt(PRIMITIVES["map:mul_const"]))

    def test_adnominal_prompt_forbids_the_forms_that_broke_combination(self):
        # a first run returned "2で割り切れる値" / "値が偶数である", which
        # concatenate into "...値要素だけを残す"; these constraints are what
        # keep the fragment attachable to the frame's noun
        prompt = render_user_prompt(PRIMITIVES["filter:even"])
        self.assertIn("末尾を名詞で終えないこと", prompt)
        self.assertIn("「値が」「要素が」のような主語", prompt)

    def test_adnominal_prompt_leaves_the_narrowing_to_the_frame(self):
        # "k以上の要素だけ" + the frame's own "要素を抽出する" says it twice --
        # the fragment states the condition and nothing else
        prompt = render_user_prompt(PRIMITIVES["filter:ge_k"])
        self.assertIn("「だけ」「のみ」", prompt)
        self.assertIn("それは生成器側が付ける", prompt)

    def test_adnominal_prompt_asks_for_stackable_fragments(self):
        # two predicates are concatenated into one 連体修飾 (ja_generator's
        # adnominal_order), so each fragment has to read with another in front
        prompt = render_user_prompt(PRIMITIVES["filter:even"])
        self.assertIn("2つ重ねて", prompt)
        self.assertIn("「k以上の偶数の要素」は可", prompt)

    def test_zero_gets_its_own_template(self):
        # 「ちょうど0」 is an equality, and template (a)'s rules for a range
        # left the model nothing but padding: all 11 responses were
        # 「0に等しいの」/「0に等しいこと」 and the key survived the human
        # approval step with zero entries
        self.assertEqual(PRIMITIVES["filter:zero"].template_id, "e")
        for key in ("filter:even", "filter:ge_k", "filter:positive", "filter:negative"):
            self.assertEqual(PRIMITIVES[key].template_id, "a", key)

    def test_zero_prompt_lists_the_endings_instead_of_describing_them(self):
        prompt = render_user_prompt(PRIMITIVES["filter:zero"])
        for ending in ("「ちょうど0の」", "「0に等しい」", "「0と一致する」", "「0である」"):
            self.assertIn(ending, prompt, ending)
        # the form template (a) forbids is the one that survives here: it is
        # the only natural 連体形 left once 「の」 cannot be appended
        self.assertIn("断定の連体形「〜である」", prompt)
        self.assertNotIn("断定の「〜である」で終えないこと", prompt)

    def test_zero_prompt_forbids_the_appended_no(self):
        # 「0に等しい」 is already a 連体形; (a)'s "append 「の」" advice turned
        # it into 「0に等しいの」, which is what every response did
        prompt = render_user_prompt(PRIMITIVES["filter:zero"])
        self.assertIn("何も書き足さないこと。特に「の」を足さないこと", prompt)
        self.assertIn("悪い例:「0に等しいの」「0と一致するの」「0であるの」", prompt)

    def test_zero_prompt_never_writes_a_fragment_followed_by_the_nown(self):
        # the run that fixed the endings still lost 6 responses out of 6 to
        # 「0に等しい要素」: the template was writing the renderer's own noun
        # right after a finished fragment, once as a *good* example
        # (「→「k以上の0に等しい要素」は可」), and the model copied it -- the
        # same way frame:filter_verb's condition-copying started
        prompt = render_user_prompt(PRIMITIVES["filter:zero"])
        for good_example in ("0に等しい要素」は可", "直後に「要素」を置ける"):
            self.assertNotIn(good_example, prompt, good_example)
        self.assertIn("悪い例:「0に等しい要素」", prompt)

    def test_zero_prompt_keeps_the_equality_meaning(self):
        prompt = render_user_prompt(PRIMITIVES["filter:zero"])
        self.assertIn("等値条件", prompt)
        for wrong in ("「0以上」", "「0より大きい」", "「0以下」", "「0より小さい」", "「0でない」"):
            self.assertIn(wrong, prompt, wrong)

    def test_zero_asks_for_fewer_expressions_than_the_range_predicates(self):
        # a floor of 5 is an instruction to pad when only a handful of genuine
        # paraphrases exist
        zero = PRIMITIVES["filter:zero"]
        self.assertEqual((zero.min_items, zero.max_items), (3, 8))
        self.assertIn("この条件の自然な言い換えは多くない", render_user_prompt(zero))
        self.assertEqual(json_schema(zero), string_list_schema(3, 8))

    def test_zero_prompt_still_meets_the_adnominal_slot_contract(self):
        # (e) is a different prompt, not a different slot type: the fragment
        # is still concatenated with other fragments and handed to
        # frame:filter_verb's noun
        prompt = render_user_prompt(PRIMITIVES["filter:zero"])
        self.assertIn("「要素」「もの」「値」「数」「こと」「とき」で終わる表現は出力しないこと", prompt)
        self.assertIn("「だけ」「のみ」", prompt)
        self.assertIn("それは生成器側が付ける", prompt)
        self.assertIn("前に別の条件を置いて読んでも自然な形にすること", prompt)
        self.assertIn("「値が」「要素が」のような主語", prompt)

    def test_zero_prompt_has_no_unused_substitution_value(self):
        # every value in substitutions() is recorded in the generation log as
        # part of the prompt, so (e), which has no {var_note} site, must not
        # carry one
        self.assertEqual(
            set(PRIMITIVES["filter:zero"].substitutions()), {"count", "description"}
        )

    def test_action_pair_prompt_pins_down_the_pair_forms(self):
        # a first run returned "kを加える操作" as a terminal and te == terminal
        prompt = render_user_prompt(PRIMITIVES["map:add_k"])
        self.assertIn("terminalは動詞で言い切る形にすること", prompt)
        self.assertIn("terminalと同じ文字列をteに入れないこと", prompt)
        # the filter frame is an ACTION_PAIR too, and hit the same bug
        self.assertIn(
            "terminalと同じ文字列をteに入れないこと",
            render_user_prompt(PRIMITIVES["frame:filter_verb"]),
        )

    def test_action_pair_prompt_names_both_joins_the_generator_makes(self):
        # ja_generator glues the closing frame's noun onto terminal and the
        # chain connective 「から」 onto te; both prompts say so, because a
        # form that ignores either one cannot be joined at all
        prompt = render_user_prompt(PRIMITIVES["map:mul_const"])
        self.assertIn("直後に「solve関数」のような名詞が続く", prompt)
        self.assertIn("te自体に「から」を含めてはいけない", prompt)
        frame = render_user_prompt(PRIMITIVES["frame:filter_verb"])
        self.assertIn("直後に「solve関数」のような名詞が続く", frame)

    def test_every_action_prompt_forbids_dropping_the_distinguishing_words(self):
        # without this, take_first_k and take_last_k both came back as
        # "k個の要素を取り出す" -- indistinguishable operations
        for key in ("slice:take_first_k", "slice:take_last_k", "order:ascending"):
            self.assertIn("省略しないこと", render_user_prompt(PRIMITIVES[key]), key)
        self.assertIn("省略してはいけません", SYSTEM_PROMPT)

    def test_frame_prompts_pin_down_their_final_character(self):
        self.assertIn("必ず読点「、」で終えること", render_user_prompt(PRIMITIVES["frame:opening"]))
        closing = render_user_prompt(PRIMITIVES["frame:closing"])
        self.assertIn("「〜てください。」", closing)
        self.assertIn("終止形で言い切る形は出力しないこと", closing)

    def test_opening_prompt_demands_a_category_neutral_opening(self):
        # the opening is sampled without knowing which category comes first,
        # so 「整数リストxsから、」 (fine before an extraction, wrong before
        # 「kを足す」) must not be generated at all
        prompt = render_user_prompt(PRIMITIVES["frame:opening"])
        self.assertIn("中立な書き出しに限ること", prompt)
        self.assertIn("整数リストxsから、", prompt)  # named as the bad example
        for category in ("抽出", "変換", "並べ替え", "切り出し"):
            self.assertIn(category, prompt, category)

    def test_closing_prompt_keeps_the_noun_the_last_clause_modifies(self):
        # the last clause is a 連体修飾 and the closing has to supply the noun
        # it modifies, so the closing starts with the solve noun phrase
        prompt = render_user_prompt(PRIMITIVES["frame:closing"])
        self.assertIn("「solve」を含む名詞句", prompt)
        self.assertIn("その連体形が係る名詞句", prompt)

    def test_closing_prompt_asks_for_an_implementation_request(self):
        # a first run returned "solve関数を実行してください。" -- run the
        # function, not write it; the verb has to be a writing one
        prompt = render_user_prompt(PRIMITIVES["frame:closing"])
        self.assertIn("まだ存在しないコードを新しく生み出す意味のものに限ること", prompt)
        self.assertIn("「実行する」「呼び出す」「処理する」", prompt)

    def test_closing_prompt_forbids_the_relayed_request(self):
        # a run returned "solve関数を書くよう依頼してください。" /
        # "...するようお願いしてください。" -- an order to relay the request
        # to a third party, which the reader cannot answer with code. The
        # model was copying 依頼/お願い out of the prompt's own 悪い例, so the
        # prompt no longer writes a bad example at all: it states the shape
        # (one verb, addressed to the reader) instead.
        prompt = render_user_prompt(PRIMITIVES["frame:closing"])
        self.assertIn("読み手自身にその動作をさせる文", prompt)
        self.assertIn("「〜よう」「〜ように」を挟んで別の動詞に繋ぐ形", prompt)
        self.assertIn("助詞「を」を2回以上使わないこと", prompt)
        for word in ("依頼", "お願い", "求め"):
            self.assertNotIn(word, prompt, word)

    def test_closing_prompt_shows_exactly_one_example_sentence(self):
        # dropping every example made a 4B model fall back to whatever
        # concrete words were nearby -- the template's own "solve(xs, k)"
        # ("solve関数は、xsリストをkに応じて処理してください。") and, once the
        # banned verbs were the only ones written down, those
        # ("solve関数をを実行してください。"). One well-formed example anchors
        # the shape; a second one for the bad case is what started the
        # 依頼 copying, so there is none.
        prompt = render_user_prompt(PRIMITIVES["frame:closing"])
        self.assertIn("全体の形の例:「Python関数solveを実装してください。」", prompt)
        self.assertNotIn("悪い例", prompt)

    def test_messages_are_system_plus_user(self):
        messages = build_messages(PRIMITIVES["filter:even"])
        self.assertEqual([m["role"] for m in messages], ["system", "user"])
        self.assertEqual(messages[0]["content"], SYSTEM_PROMPT)
        self.assertEqual(messages[1]["content"], render_user_prompt(PRIMITIVES["filter:even"]))


class Schemas(unittest.TestCase):
    def test_action_pair_keys_get_pair_schemas(self):
        schema = json_schema(PRIMITIVES["map:add_k"])
        self.assertEqual(schema, action_pair_schema(5, 15))
        self.assertEqual(
            sorted(schema["properties"]["expressions"]["items"]["properties"]), ["te", "terminal"]
        )

    def test_adnominal_and_text_keys_get_string_list_schemas(self):
        self.assertEqual(json_schema(PRIMITIVES["filter:even"]), string_list_schema(5, 15))
        self.assertEqual(json_schema(PRIMITIVES["frame:opening"]), string_list_schema(5, 15))

    def test_filter_verb_uses_the_smaller_bounds(self):
        self.assertEqual(
            json_schema(PRIMITIVES["frame:filter_verb"]),
            action_pair_schema(4, 8, FRAG_PREFIX_PATTERN),
        )

    def test_only_the_filter_frame_constrains_its_strings_by_pattern(self):
        # the grammar, not the prose, is what keeps a condition from being
        # written in front of {frag} (it was ignored in prose 6 times out of 6)
        forms = json_schema(PRIMITIVES["frame:filter_verb"])["properties"]["expressions"]["items"]["properties"]
        for form in ("terminal", "te"):
            self.assertEqual(forms[form]["pattern"], FRAG_PREFIX_PATTERN, form)
        self.assertRegex("{frag}要素だけを残す", FRAG_PREFIX_PATTERN)
        self.assertNotRegex("k以上の{frag}要素だけを残す", FRAG_PREFIX_PATTERN)
        other = json_schema(PRIMITIVES["map:add_k"])["properties"]["expressions"]["items"]["properties"]
        self.assertNotIn("pattern", other["terminal"])

    def test_schemas_forbid_extra_properties(self):
        for spec in PRIMITIVES.values():
            self.assertFalse(json_schema(spec)["additionalProperties"], spec.key)


class DocumentIsTheSourceOfTruth(unittest.TestCase):
    """THIRD_PARTY.md defines the prompts; this module only transcribes them.

    These tests fail if the two drift apart -- in either direction.
    """

    @classmethod
    def setUpClass(cls):
        cls.doc = (Path(__file__).resolve().parents[2] / "THIRD_PARTY.md").read_text(encoding="utf-8")

    def _block_after(self, heading: str) -> str:
        after = self.doc.split(heading, 1)[1]
        return after.split("```text\n", 1)[1].split("\n```", 1)[0]

    def test_system_prompt_matches_the_document(self):
        self.assertEqual(self._block_after("### 共通system prompt"), SYSTEM_PROMPT)

    def test_templates_match_the_document(self):
        for heading, template in (
            ("#### (a) ", TEMPLATES["a"]),
            ("#### (b) ", TEMPLATES["b"]),
            ("#### (c) ", TEMPLATES["c"]),
            ("#### (d) ", TEMPLATES["d"]),
            ("#### (e) ", TEMPLATES["e"]),
        ):
            self.assertEqual(self._block_after(heading), template, heading)

    def test_every_primitive_has_a_row_in_the_document_table(self):
        for key in PRIMITIVES:
            self.assertIn(f"| `{key}` |", self.doc, key)

    def test_item_counts_match_the_document_table(self):
        for key, spec in PRIMITIVES.items():
            row = next(line for line in self.doc.splitlines() if line.startswith(f"| `{key}` |"))
            self.assertIn(f"| {spec.min_items}〜{spec.max_items} |", row, key)


class PromptHashes(unittest.TestCase):
    def test_hash_is_stable_and_distinct_per_primitive(self):
        hashes = {key: prompt_sha256(spec) for key, spec in PRIMITIVES.items()}
        self.assertEqual(len(set(hashes.values())), len(PRIMITIVES))
        for key, spec in PRIMITIVES.items():
            self.assertEqual(prompt_sha256(spec), hashes[key])

    def test_record_carries_everything_needed_to_reproduce_the_prompt(self):
        record = prompt_record(PRIMITIVES["filter:ge_k"])
        self.assertEqual(record["key"], "filter:ge_k")
        self.assertEqual(record["template_id"], "a")
        self.assertEqual(record["substitutions"]["count"], "5〜15")
        self.assertIn("k以上", record["substitutions"]["description"])
        self.assertEqual(len(record["prompt_sha256"]), 64)
        self.assertEqual(len(record["system_prompt_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
