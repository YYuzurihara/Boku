"""Unit tests for split.py. Pure stdlib, no Docker required.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import enumerate_all, label  # noqa: E402
from schema import SemanticAST  # noqa: E402
from split import (  # noqa: E402
    LeakageError,
    SplitRatios,
    cap_per_label,
    check_no_leakage,
    dedup_by_hash,
    stratified_split,
)


class DedupByHash(unittest.TestCase):
    def test_drops_exact_duplicates(self):
        a = SemanticAST(filters=("even",))
        b = SemanticAST(filters=("even",))
        c = SemanticAST(filters=("odd",))
        out = dedup_by_hash([a, b, c])
        self.assertEqual(len(out), 2)


class StratifiedSplit(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_asts = enumerate_all()

    def test_every_ast_assigned_exactly_once(self):
        splits = stratified_split(self.all_asts, seed=0)
        total = sum(len(v) for v in splits.values())
        self.assertEqual(total, len(self.all_asts))
        all_hashes = [a.semantic_hash() for group in splits.values() for a in group]
        self.assertEqual(len(all_hashes), len(set(all_hashes)))

    def test_roughly_matches_requested_ratios(self):
        splits = stratified_split(self.all_asts, ratios=SplitRatios(0.8, 0.1, 0.1), seed=0)
        n = len(self.all_asts)
        train_frac = len(splits["train"]) / n
        val_frac = len(splits["val"]) / n
        test_frac = len(splits["test"]) / n
        self.assertAlmostEqual(train_frac, 0.8, delta=0.03)
        self.assertAlmostEqual(val_frac, 0.1, delta=0.03)
        self.assertAlmostEqual(test_frac, 0.1, delta=0.03)

    def test_num_categories_distribution_is_stratified(self):
        splits = stratified_split(self.all_asts, seed=0)
        for split_name, group in splits.items():
            counts = {1: 0, 2: 0, 3: 0}
            for ast in group:
                counts[ast.num_categories()] += 1
            for n in (1, 2, 3):
                self.assertGreater(counts[n], 0, f"{split_name} has zero examples with num_categories={n}")

    def test_deterministic_given_seed(self):
        a = stratified_split(self.all_asts, seed=5)
        b = stratified_split(self.all_asts, seed=5)
        self.assertEqual(
            {k: [x.semantic_hash() for x in v] for k, v in a.items()},
            {k: [x.semantic_hash() for x in v] for k, v in b.items()},
        )

    def test_bad_ratios_rejected(self):
        with self.assertRaises(ValueError):
            SplitRatios(0.8, 0.1, 0.2)


class CheckNoLeakage(unittest.TestCase):
    def test_passes_on_disjoint_splits(self):
        splits = {
            "train": [SemanticAST(filters=("even",))],
            "val": [SemanticAST(filters=("odd",))],
            "test": [SemanticAST(order_op="ascending")],
        }
        check_no_leakage(splits)  # must not raise

    def test_raises_on_overlap(self):
        shared = SemanticAST(filters=("even",))
        splits = {"train": [shared], "val": [shared], "test": []}
        with self.assertRaises(LeakageError):
            check_no_leakage(splits)


class CapPerLabel(unittest.TestCase):
    def test_caps_each_label_group(self):
        all_asts = enumerate_all()
        capped = cap_per_label(all_asts, max_per_label=5, seed=0)
        counts: dict[tuple, int] = {}
        for ast in capped:
            key = tuple(sorted(label(ast).items()))
            counts[key] = counts.get(key, 0) + 1
        self.assertTrue(all(c <= 5 for c in counts.values()))

    def test_leaves_small_groups_untouched(self):
        asts = [SemanticAST(filters=("even",)), SemanticAST(filters=("odd",))]
        out = cap_per_label(asts, max_per_label=100)
        self.assertEqual(len(out), 2)


if __name__ == "__main__":
    unittest.main()
