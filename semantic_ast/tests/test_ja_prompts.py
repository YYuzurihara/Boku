"""Unit tests for ja_prompts.py. Pure stdlib, no GPU or model required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import enumerate_all  # noqa: E402
from ja_prompts import (  # noqa: E402
    ACTION_PAIR,
    ADNOMINAL,
    FRAG_PLACEHOLDER,
    PRIMITIVES,
    SYSTEM_PROMPT,
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
                for name in ("{count}", "{description}", "{var_note}", "{role}", "{role_description}", "{boundary_note}")
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

    def test_messages_are_system_plus_user(self):
        messages = build_messages(PRIMITIVES["filter:even"])
        self.assertEqual([m["role"] for m in messages], ["system", "user"])
        self.assertEqual(messages[0]["content"], SYSTEM_PROMPT)
        self.assertEqual(messages[1]["content"], render_user_prompt(PRIMITIVES["filter:even"]))


class Schemas(unittest.TestCase):
    def test_action_pair_keys_get_pair_schemas(self):
        schema = json_schema(PRIMITIVES["map:add_k"])
        self.assertEqual(schema, action_pair_schema(10, 30))
        self.assertEqual(
            sorted(schema["properties"]["expressions"]["items"]["properties"]), ["te", "terminal"]
        )

    def test_adnominal_and_text_keys_get_string_list_schemas(self):
        self.assertEqual(json_schema(PRIMITIVES["filter:even"]), string_list_schema(10, 30))
        self.assertEqual(json_schema(PRIMITIVES["frame:opening"]), string_list_schema(10, 30))

    def test_filter_verb_uses_the_smaller_bounds(self):
        self.assertEqual(json_schema(PRIMITIVES["frame:filter_verb"]), action_pair_schema(5, 10))

    def test_schemas_forbid_extra_properties(self):
        for spec in PRIMITIVES.values():
            self.assertFalse(json_schema(spec)["additionalProperties"], spec.key)


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
        self.assertEqual(record["substitutions"]["count"], "10〜30")
        self.assertIn("k以上", record["substitutions"]["description"])
        self.assertEqual(len(record["prompt_sha256"]), 64)
        self.assertEqual(len(record["system_prompt_sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
