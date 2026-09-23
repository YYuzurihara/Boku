"""Unit tests for ja_dictionary.py -- saving/loading the expression
dictionary. Pure stdlib, no GPU or model required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

_SEMANTIC_AST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SEMANTIC_AST))
sys.path.insert(0, str(_SEMANTIC_AST / "expressions_ja"))

from ja_dictionary import ExpressionDictionary, ExpressionDictionaryError, merge  # noqa: E402
from ja_fixture import fixture_dictionary  # noqa: E402
from ja_prompts import PRIMITIVES  # noqa: E402


class RoundTrip(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / "expressions.json"

    def tearDown(self):
        self.tmp.cleanup()

    def test_save_then_load_preserves_every_entry(self):
        original = fixture_dictionary(extra_variants=True)
        original.save(self.path)
        reloaded = ExpressionDictionary.load(self.path)
        self.assertEqual(reloaded.entries, original.entries)
        self.assertEqual(reloaded.content_sha256(), original.content_sha256())

    def test_file_has_the_shape_ja_generator_plan_specifies(self):
        fixture_dictionary().save(self.path)
        raw = json.loads(self.path.read_text(encoding="utf-8"))
        self.assertEqual(sorted(raw), sorted(PRIMITIVES))
        entry = raw["map:add_k"]
        self.assertEqual(entry["slot_type"], "ACTION_PAIR")
        self.assertEqual(entry["expressions"][0], {"terminal": "kを加える", "te": "kを加えて"})
        self.assertEqual(raw["filter:ge_k"], {"slot_type": "ADNOMINAL", "expressions": ["k以上の"]})

    def test_japanese_is_written_unescaped(self):
        fixture_dictionary().save(self.path)
        self.assertIn("偶数の", self.path.read_text(encoding="utf-8"))

    def test_odd_but_well_formed_expressions_survive_unchanged(self):
        # a reviewer's job is to catch bad Japanese; storage must not silently
        # "fix" anything, including whitespace, duplicates and strange wording
        weird = ["  へんな  表現 ", "以上の", "以上の", "🙂の"]
        dictionary = ExpressionDictionary.from_expressions({"filter:ge_k": weird})
        dictionary.save(self.path)
        self.assertEqual(ExpressionDictionary.load(self.path).expressions("filter:ge_k"), weird)

    def test_load_reports_a_missing_file_clearly(self):
        with self.assertRaises(ExpressionDictionaryError) as ctx:
            ExpressionDictionary.load(self.path)
        self.assertIn("not found", str(ctx.exception))

    def test_content_hash_changes_with_content(self):
        a = fixture_dictionary()
        b = fixture_dictionary(extra_variants=True)
        self.assertNotEqual(a.content_sha256(), b.content_sha256())


class Validation(unittest.TestCase):
    def test_fixture_dictionary_is_structurally_clean(self):
        self.assertEqual(fixture_dictionary().validate(), [])
        self.assertEqual(fixture_dictionary().missing_keys(), [])

    def test_wrong_shape_for_slot_type_is_reported(self):
        dictionary = ExpressionDictionary.from_expressions(
            {"filter:ge_k": [{"terminal": "k以上の", "te": "k以上で"}]}
        )
        problems = dictionary.validate()
        self.assertTrue(any("expected a string" in p for p in problems), problems)

    def test_action_pair_missing_a_form_is_reported(self):
        dictionary = ExpressionDictionary.from_expressions({"map:add_k": [{"terminal": "kを加える"}]})
        problems = dictionary.validate()
        self.assertTrue(any("te" in p for p in problems), problems)

    def test_filter_verb_without_the_frag_placeholder_is_reported(self):
        dictionary = ExpressionDictionary.from_expressions(
            {"frame:filter_verb": [{"terminal": "要素だけを残す", "te": "{frag}要素だけを残し"}]}
        )
        problems = dictionary.validate()
        self.assertTrue(any("{frag}" in p and "terminal" in p for p in problems), problems)

    def test_empty_expression_list_is_reported(self):
        dictionary = ExpressionDictionary.from_expressions({"filter:even": []})
        self.assertTrue(any("empty" in p for p in dictionary.validate()))

    def test_unknown_key_is_reported(self):
        dictionary = ExpressionDictionary({"filter:nonexistent": {"slot_type": "ADNOMINAL", "expressions": ["x"]}})
        self.assertTrue(any("unknown" in p for p in dictionary.validate()))

    def test_strict_load_raises_on_structural_problems(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "broken.json"
            ExpressionDictionary.from_expressions({"map:add_k": ["kを加える"]}).save(path)
            with self.assertRaises(ExpressionDictionaryError):
                ExpressionDictionary.load(path, strict=True)
            # non-strict still loads it, so a broken run can be inspected
            self.assertEqual(len(ExpressionDictionary.load(path, strict=False)), 1)

    def test_duplicates_are_reported_but_not_dropped(self):
        dictionary = ExpressionDictionary.from_expressions({"filter:even": ["偶数の", "偶数の", "2の倍数の"]})
        self.assertEqual(dictionary.duplicate_report(), {"filter:even": ["偶数の"]})
        self.assertEqual(dictionary.validate(), [])  # duplicates are not a structural error
        self.assertEqual(len(dictionary.expressions("filter:even")), 3)


class PartialDictionaries(unittest.TestCase):
    def test_missing_keys_are_listed(self):
        dictionary = ExpressionDictionary.from_expressions({"filter:even": ["偶数の"]})
        self.assertNotIn("filter:even", dictionary.missing_keys())
        self.assertIn("frame:opening", dictionary.missing_keys())
        self.assertEqual(len(dictionary.missing_keys()), len(PRIMITIVES) - 1)

    def test_entry_lookup_names_the_missing_key(self):
        dictionary = ExpressionDictionary.from_expressions({"filter:even": ["偶数の"]})
        with self.assertRaises(ExpressionDictionaryError) as ctx:
            dictionary.expressions("map:add_k")
        self.assertIn("map:add_k", str(ctx.exception))

    def test_merge_overlays_later_dictionaries(self):
        base = fixture_dictionary()
        overlay = ExpressionDictionary.from_expressions({"filter:even": ["2で割り切れる"]})
        merged = merge([base, overlay])
        self.assertEqual(merged.expressions("filter:even"), ["2で割り切れる"])
        self.assertEqual(merged.expressions("filter:odd"), base.expressions("filter:odd"))
        self.assertEqual(len(merged), len(base))

    def test_keys_come_back_in_table_order(self):
        dictionary = ExpressionDictionary.from_expressions(
            {"frame:closing": ["。"], "filter:even": ["偶数の"]}
        )
        self.assertEqual(dictionary.keys(), ["filter:even", "frame:closing"])


if __name__ == "__main__":
    unittest.main()
