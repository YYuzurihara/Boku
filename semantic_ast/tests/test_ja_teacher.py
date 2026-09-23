"""Unit tests for ja_teacher.py's non-GPU parts (response parsing, key
selection, run metadata). The model itself is never loaded: ``generate()``
imports vLLM lazily, so these run anywhere.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ja_prompts import PRIMITIVES  # noqa: E402
from ja_teacher import SamplingConfig, _specs_for, parse_response  # noqa: E402


class ParseResponse(unittest.TestCase):
    def test_string_list_response(self):
        spec = PRIMITIVES["filter:ge_k"]
        expressions, error = parse_response(spec, json.dumps({"expressions": ["k以上の", "k以上である"]}))
        self.assertIsNone(error)
        self.assertEqual(expressions, ["k以上の", "k以上である"])

    def test_action_pair_response(self):
        spec = PRIMITIVES["map:add_k"]
        payload = {"expressions": [{"terminal": "kを加える", "te": "kを加えて"}]}
        expressions, error = parse_response(spec, json.dumps(payload, ensure_ascii=False))
        self.assertIsNone(error)
        self.assertEqual(expressions, payload["expressions"])

    def test_malformed_json_is_reported_not_raised(self):
        expressions, error = parse_response(PRIMITIVES["filter:even"], "これはJSONではありません")
        self.assertEqual(expressions, [])
        self.assertIn("not valid JSON", error)

    def test_missing_expressions_key_is_reported(self):
        expressions, error = parse_response(PRIMITIVES["filter:even"], json.dumps({"items": []}))
        self.assertEqual(expressions, [])
        self.assertIn("no 'expressions' key", error)

    def test_wrong_expressions_type_is_reported(self):
        expressions, error = parse_response(PRIMITIVES["filter:even"], json.dumps({"expressions": "偶数の"}))
        self.assertEqual(expressions, [])
        self.assertIn("expected list", error)

    def test_content_is_not_repaired_or_filtered(self):
        # whatever the model returned is what gets stored; judging it is the
        # human reviewer's job
        payload = {"expressions": ["", "  ", "kより大きい"]}
        expressions, error = parse_response(PRIMITIVES["filter:ge_k"], json.dumps(payload, ensure_ascii=False))
        self.assertIsNone(error)
        self.assertEqual(expressions, payload["expressions"])


class KeySelection(unittest.TestCase):
    def test_no_keys_means_every_primitive(self):
        self.assertEqual([s.key for s in _specs_for(None)], list(PRIMITIVES))

    def test_subset_is_kept_in_the_requested_order(self):
        self.assertEqual([s.key for s in _specs_for(["map:add_k", "filter:even"])], ["map:add_k", "filter:even"])

    def test_unknown_key_exits_with_a_message(self):
        with self.assertRaises(SystemExit) as ctx:
            _specs_for(["filter:nope"])
        self.assertIn("filter:nope", str(ctx.exception))


class Sampling(unittest.TestCase):
    def test_defaults_are_recordable(self):
        config = SamplingConfig()
        self.assertEqual(config.temperature, 0.8)
        self.assertEqual(config.top_p, 0.95)
        self.assertEqual(config.seed, 0)


if __name__ == "__main__":
    unittest.main()
