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

from sampling import sample_pairs  # noqa: E402


def _record(i: int, **verification_overrides) -> dict:
    verification = {
        "syntax_ok": True,
        "ast_safe": True,
        "executable": True,
        "tests_passed": True,
        "pure": True,
        "error": None,
        "cross_check_ok": True,
    }
    verification.update(verification_overrides)
    return {
        "spec_id": f"train-{i:06d}",
        "semantic_hash": f"h{i}",
        "instruction_ja": [f"ja-{i}"],
        "codes": [{"code": f"code-{i}\n", "verification": verification}],
    }


class SamplePairsTest(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.path = Path(self._tmp.name) / "train.jsonl"

    def _write(self, records: list[dict]) -> None:
        with self.path.open("w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r, ensure_ascii=False) + "\n")

    def test_takes_percent_of_records_without_repeats(self) -> None:
        self._write([_record(i) for i in range(200)])
        pairs = sample_pairs(self.path, percent=10, seed=0)
        self.assertEqual(len(pairs), 20)
        self.assertEqual(len({p.spec_id for p in pairs}), 20)

    def test_pair_fields_come_from_the_same_record(self) -> None:
        self._write([_record(i) for i in range(50)])
        for p in sample_pairs(self.path, percent=50, seed=1):
            i = int(p.spec_id.split("-")[1])
            self.assertEqual((p.semantic_hash, p.instruction_ja, p.code), (f"h{i}", f"ja-{i}", f"code-{i}\n"))

    def test_reproducible_and_seed_dependent(self) -> None:
        self._write([_record(i) for i in range(100)])
        a = sample_pairs(self.path, percent=20, seed=7)
        self.assertEqual(a, sample_pairs(self.path, percent=20, seed=7))
        self.assertNotEqual(a, sample_pairs(self.path, percent=20, seed=8))

    def test_percent_bounds(self) -> None:
        self._write([_record(i) for i in range(10)])
        self.assertEqual(sample_pairs(self.path, percent=0), [])
        self.assertEqual(len(sample_pairs(self.path, percent=100)), 10)
        with self.assertRaises(ValueError):
            sample_pairs(self.path, percent=101)

    def test_unverified_records_are_dropped(self) -> None:
        bad = [
            _record(0, syntax_ok=False),
            _record(1, tests_passed=False),
            _record(2, error="boom"),
            _record(3, cross_check_ok=False),
        ]
        self._write(bad + [_record(4)])
        self.assertEqual([p.spec_id for p in sample_pairs(self.path, percent=100)], ["train-000004"])

    def test_missing_cross_check_key_is_accepted(self) -> None:
        r = _record(0)
        del r["codes"][0]["verification"]["cross_check_ok"]
        self._write([r])
        self.assertEqual(len(sample_pairs(self.path, percent=100)), 1)


if __name__ == "__main__":
    unittest.main()
