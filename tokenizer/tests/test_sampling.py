"""Unit tests for sampling.py. Pure stdlib, no GPU/Docker required.

Run with: python -m unittest discover -s tokenizer/tests
"""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sampling import Pair, sample_pairs  # noqa: E402


def _verification(**overrides) -> dict:
    base = {
        "syntax_ok": True,
        "ast_safe": True,
        "executable": True,
        "tests_passed": True,
        "pure": True,
        "error": None,
        "cross_check_ok": True,
    }
    base.update(overrides)
    return base


def _write_jsonl(path: Path, records: list[dict]) -> None:
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")


class SamplePairsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.dir = Path(self._tmp.name)
        self.instructions_path = self.dir / "instructions_train.jsonl"
        self.code_path = self.dir / "code_train.jsonl"

    def _write(self, instructions: list[dict], codes: list[dict]) -> None:
        _write_jsonl(self.instructions_path, instructions)
        _write_jsonl(self.code_path, codes)

    def test_cartesian_product_capped_at_n(self) -> None:
        self._write(
            instructions=[
                {
                    "spec_id": "train-000000",
                    "semantic_hash": "h0",
                    "instruction_ja": ["ja-a", "ja-b", "ja-c"],
                }
            ],
            codes=[
                {
                    "spec_id": "train-000000",
                    "semantic_hash": "h0",
                    "codes": [
                        {"code": "code-1\n", "verification": _verification()},
                        {"code": "code-2\n", "verification": _verification()},
                        {"code": "code-3\n", "verification": _verification()},
                    ],
                }
            ],
        )
        pairs = sample_pairs(self.instructions_path, self.code_path, n_per_ast=5, seed=0)
        self.assertEqual(len(pairs), 5)
        # every pair actually comes from the declared cartesian product
        for p in pairs:
            self.assertIn(p.instruction_ja, ("ja-a", "ja-b", "ja-c"))
            self.assertIn(p.code, ("code-1\n", "code-2\n", "code-3\n"))
        # no duplicate (instruction, code) combination
        self.assertEqual(len({(p.instruction_ja, p.code) for p in pairs}), 5)

    def test_fewer_combinations_than_n_returns_all(self) -> None:
        self._write(
            instructions=[{"spec_id": "s", "semantic_hash": "h", "instruction_ja": ["only-ja"]}],
            codes=[
                {
                    "spec_id": "s",
                    "semantic_hash": "h",
                    "codes": [{"code": "only-code\n", "verification": _verification()}],
                }
            ],
        )
        pairs = sample_pairs(self.instructions_path, self.code_path, n_per_ast=5, seed=0)
        self.assertEqual(pairs, [Pair(spec_id="s", semantic_hash="h", instruction_ja="only-ja", code="only-code\n")])

    def test_unverified_code_is_excluded(self) -> None:
        self._write(
            instructions=[{"spec_id": "s", "semantic_hash": "h", "instruction_ja": ["ja"]}],
            codes=[
                {
                    "spec_id": "s",
                    "semantic_hash": "h",
                    "codes": [
                        {"code": "bad\n", "verification": _verification(tests_passed=False)},
                        {"code": "also-bad\n", "verification": _verification(error="boom")},
                        {"code": "good\n", "verification": _verification()},
                    ],
                }
            ],
        )
        pairs = sample_pairs(self.instructions_path, self.code_path, n_per_ast=5, seed=0)
        self.assertEqual([p.code for p in pairs], ["good\n"])

    def test_ast_with_no_verified_code_is_skipped_entirely(self) -> None:
        self._write(
            instructions=[{"spec_id": "s", "semantic_hash": "h", "instruction_ja": ["ja"]}],
            codes=[
                {
                    "spec_id": "s",
                    "semantic_hash": "h",
                    "codes": [{"code": "bad\n", "verification": _verification(ast_safe=False)}],
                }
            ],
        )
        self.assertEqual(sample_pairs(self.instructions_path, self.code_path), [])

    def test_only_specs_common_to_both_files_are_used(self) -> None:
        self._write(
            instructions=[
                {"spec_id": "only-in-instructions", "semantic_hash": "h1", "instruction_ja": ["ja"]},
                {"spec_id": "shared", "semantic_hash": "h2", "instruction_ja": ["ja"]},
            ],
            codes=[
                {
                    "spec_id": "only-in-code",
                    "semantic_hash": "h3",
                    "codes": [{"code": "c\n", "verification": _verification()}],
                },
                {
                    "spec_id": "shared",
                    "semantic_hash": "h2",
                    "codes": [{"code": "c\n", "verification": _verification()}],
                },
            ],
        )
        pairs = sample_pairs(self.instructions_path, self.code_path)
        self.assertEqual({p.spec_id for p in pairs}, {"shared"})

    def test_deterministic_given_seed(self) -> None:
        self._write(
            instructions=[{"spec_id": "s", "semantic_hash": "h", "instruction_ja": ["a", "b", "c"]}],
            codes=[
                {
                    "spec_id": "s",
                    "semantic_hash": "h",
                    "codes": [
                        {"code": "1\n", "verification": _verification()},
                        {"code": "2\n", "verification": _verification()},
                        {"code": "3\n", "verification": _verification()},
                    ],
                }
            ],
        )
        first = sample_pairs(self.instructions_path, self.code_path, n_per_ast=4, seed=7)
        second = sample_pairs(self.instructions_path, self.code_path, n_per_ast=4, seed=7)
        self.assertEqual(first, second)


if __name__ == "__main__":
    unittest.main()
