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
    ALL_SPLITS,
    BOUNDARY_SPLIT,
    COMPOSITIONAL_SPLIT,
    HOLDOUT_PAIRS,
    PARAPHRASE_SPLIT,
    LeakageError,
    SplitRatios,
    cap_per_label,
    check_no_leakage,
    dedup_by_hash,
    build_eval_splits,
    check_holdout_pairs,
    matches_holdout,
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


class EvalSplits(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.all_asts = enumerate_all()
        cls.splits = build_eval_splits(cls.all_asts, seed=0)

    def test_has_the_six_splits_and_covers_every_ast_exactly_once(self):
        self.assertEqual(tuple(self.splits), ALL_SPLITS)
        hashes = [a.semantic_hash() for group in self.splits.values() for a in group]
        self.assertEqual(len(hashes), len(set(hashes)))
        self.assertEqual(len(hashes), len(self.all_asts))

    def test_no_leakage_between_any_two_splits(self):
        check_no_leakage(self.splits)

    def test_compositional_split_is_exactly_the_asts_with_a_held_out_pair(self):
        expected = {a.semantic_hash() for a in self.all_asts if matches_holdout(a)}
        actual = {a.semantic_hash() for a in self.splits[COMPOSITIONAL_SPLIT]}
        self.assertEqual(actual, expected)
        self.assertTrue(actual)

    def test_held_out_pairs_never_occur_together_elsewhere_but_each_op_is_in_train(self):
        check_holdout_pairs(self.splits)
        for a, b in HOLDOUT_PAIRS:
            train = [set(x.op_tags()) for x in self.splits["train"]]
            self.assertTrue(any(a in t for t in train), a)
            self.assertTrue(any(b in t for t in train), b)
            self.assertFalse(any(a in t and b in t for t in train))

    def test_the_papers_example_is_held_out(self):
        even_desc = SemanticAST(filters=("even",), order_op="descending")
        self.assertIn(even_desc.semantic_hash(), {a.semantic_hash() for a in self.splits[COMPOSITIONAL_SPLIT]})

    def test_check_holdout_pairs_rejects_a_pair_in_train(self):
        bad = {**self.splits, "train": self.splits["train"] + [SemanticAST(filters=("even",), order_op="descending")]}
        with self.assertRaises(LeakageError):
            check_holdout_pairs(bad)

    def test_check_holdout_pairs_rejects_an_op_missing_from_train(self):
        bad = {**self.splits, "train": [a for a in self.splits["train"] if "order:descending" not in a.op_tags()]}
        with self.assertRaises(LeakageError):
            check_holdout_pairs(bad)

    def test_extra_sets_are_sized_and_the_remainder_is_split_80_10_10(self):
        n_rest = len(self.all_asts) - len(self.splits[COMPOSITIONAL_SPLIT])
        for name in (PARAPHRASE_SPLIT, BOUNDARY_SPLIT):
            self.assertAlmostEqual(len(self.splits[name]) / n_rest, 0.05, delta=0.01)  # per-label rounding of small groups
        n_main = sum(len(self.splits[n]) for n in ("train", "val", "test"))
        self.assertAlmostEqual(len(self.splits["val"]) / n_main, 0.1, delta=0.01)
        self.assertAlmostEqual(len(self.splits["test"]) / n_main, 0.1, delta=0.01)

    def test_deterministic_given_the_seed(self):
        again = build_eval_splits(self.all_asts, seed=0)
        for name in ALL_SPLITS:
            self.assertEqual([a.semantic_hash() for a in again[name]], [a.semantic_hash() for a in self.splits[name]])


if __name__ == "__main__":
    unittest.main()
