"""Unit tests for ja_teacher.py's non-GPU parts (response parsing, key
selection, run metadata). The model itself is never loaded: ``generate()``
imports vLLM lazily, so these run anywhere.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

_SEMANTIC_AST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SEMANTIC_AST))
sys.path.insert(0, str(_SEMANTIC_AST / "expressions_ja"))

import ja_teacher  # noqa: E402
from ja_prompts import PRIMITIVES  # noqa: E402
from ja_teacher import SamplingConfig, _specs_for, parse_response, salvage_expressions  # noqa: E402

# A response cut off mid-item, as produced when the model tries to stop
# early and the structured-output grammar terminates the request.
TRUNCATED = """{
  "expressions": [
    {"terminal": "符号を反転する", "te": "符号を反転して"},
    {"terminal": "正負を入れ替える", "te": "正負を入れ替えて"},
    {"terminal": "正負の向きを逆にする", "te": "正]]}"""


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


class Salvage(unittest.TestCase):
    """A truncated response must not cost us the expressions that did arrive."""

    def test_complete_items_are_recovered_from_a_truncated_response(self):
        expressions, error = parse_response(PRIMITIVES["map:negate"], TRUNCATED)
        self.assertEqual(
            expressions,
            [
                {"terminal": "符号を反転する", "te": "符号を反転して"},
                {"terminal": "正負を入れ替える", "te": "正負を入れ替えて"},
            ],
        )
        self.assertIn("salvaged 2", error)

    def test_the_half_written_item_is_not_repaired(self):
        # stop at the break; never invent the missing half
        for item in salvage_expressions(TRUNCATED):
            self.assertEqual(sorted(item), ["te", "terminal"])
            self.assertTrue(item["te"].endswith("て"), item)

    def test_string_lists_are_salvaged_too(self):
        text = '{"expressions": ["偶数の", "2で割り切れる", "2の倍'
        self.assertEqual(salvage_expressions(text), ["偶数の", "2で割り切れる"])

    def test_nothing_salvageable_still_reports_the_error(self):
        expressions, error = parse_response(PRIMITIVES["filter:even"], '{"expressions": [')
        self.assertEqual(expressions, [])
        self.assertIn("not valid JSON", error)
        self.assertNotIn("salvaged", error)

    def test_valid_responses_are_untouched(self):
        payload = {"expressions": ["偶数の", "2で割り切れる"]}
        expressions, error = parse_response(PRIMITIVES["filter:even"], json.dumps(payload, ensure_ascii=False))
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


class SingleKeyRerun(unittest.TestCase):
    """``--keys <key> --merge`` regenerates one primitive in place.

    This is how a key with its own prompt (``filter:zero``, template (e)) is
    re-generated without touching the other 25: it writes into the same
    ``candidates.json`` and appends to the same generation log.
    """

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.out = self.tmp / "candidates.json"
        self.log = self.tmp / "generation_log.jsonl"
        self.out.write_text(
            json.dumps(
                {
                    "filter:even": {"slot_type": "ADNOMINAL", "expressions": ["偶数の"]},
                    "filter:zero": {"slot_type": "ADNOMINAL", "expressions": ["0に等しいの"]},
                },
                ensure_ascii=False,
            ),
            encoding="utf-8",
        )
        self.log.write_text(json.dumps({"prompt": {"key": "filter:even"}}) + "\n", encoding="utf-8")

    def _run(self, response: dict) -> dict:
        with mock.patch.object(
            ja_teacher, "generate", return_value=[json.dumps(response, ensure_ascii=False)]
        ):
            code = ja_teacher.main(
                ["--keys", "filter:zero", "--merge", "--out", str(self.out), "--log", str(self.log)]
            )
        self.assertEqual(code, 0)
        return json.loads(self.out.read_text(encoding="utf-8"))

    def test_only_the_requested_key_is_replaced(self):
        entries = self._run({"expressions": ["0に等しい", "0である", "ちょうど0の"]})
        self.assertEqual(entries["filter:even"]["expressions"], ["偶数の"])
        self.assertEqual(entries["filter:zero"]["expressions"], ["0に等しい", "0である", "ちょうど0の"])

    def test_the_log_keeps_the_other_keys_records(self):
        self._run({"expressions": ["0に等しい"]})
        records = [json.loads(line) for line in self.log.read_text(encoding="utf-8").splitlines()]
        self.assertEqual([r["prompt"]["key"] for r in records], ["filter:even", "filter:zero"])
        self.assertEqual(records[-1]["prompt"]["template_id"], "e")


class Sampling(unittest.TestCase):
    def test_defaults_are_recordable(self):
        config = SamplingConfig()
        self.assertEqual(config.temperature, 0.8)
        self.assertEqual(config.top_p, 0.95)
        self.assertEqual(config.seed, 0)


if __name__ == "__main__":
    unittest.main()
