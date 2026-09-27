"""End-to-end demo / manual smoke test for the semantic_ast package.

Enumerates the full DSL space, dedups, splits it into train/val plus the
three test sets of homework.md (言い換え / 組合せ汎化 / 境界値; stratified
by problem characteristics), verifies no semantic AST leaked across splits,
generates a test
suite per semantic AST via the reference interpreter, and writes one JSONL
file per split under ``semantic_ast/out/``.

This does not touch the teacher model, Japanese instructions, or code
generation -- those are later task-list items. It only produces the
``semantic_ast`` (+ generated ``tests``) fields of homework.md's データ
レコード schema, for every split.

Usage:
    python semantic_ast/demo.py                                  # every split
    python semantic_ast/demo.py --splits test_boundary           # one test set only
    python semantic_ast/demo.py --splits train val test_paraphrase

The split assignment is always computed over the whole AST space, so a split
written on its own is identical to the same split written together with the
others, and the splits stay disjoint however they are generated.
"""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path

from generator import enumerate_all, label
from split import (
    ALL_SPLITS,
    BOUNDARY_SPLIT,
    SplitRatios,
    build_eval_splits,
    check_holdout_pairs,
    check_no_leakage,
    dedup_by_hash,
)
from testcases import generate_boundary_test_cases, generate_test_cases

SEED = 0
OUT_DIR = Path(__file__).resolve().parent / "out"


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--splits", nargs="+", choices=ALL_SPLITS, default=list(ALL_SPLITS),
                        help="splits to write (default: all)")
    args = parser.parse_args()

    all_asts = enumerate_all()
    print(f"enumerating full semantic AST space... {len(all_asts)} distinct semantic ASTs")

    deduped = dedup_by_hash(all_asts)
    print(f"after dedup: {len(deduped)} (dropped {len(all_asts) - len(deduped)})")

    splits = build_eval_splits(deduped, ratios=SplitRatios(0.9, 0.1), seed=SEED)
    check_no_leakage(splits)
    check_holdout_pairs(splits)
    print("leakage check passed: no semantic AST hash appears in more than one split")
    print("holdout check passed: no held-out operation pair occurs outside test_compositional")

    OUT_DIR.mkdir(exist_ok=True)
    for split_name, group in splits.items():
        if split_name not in args.splits:
            continue
        path = OUT_DIR / f"ast_{split_name}.jsonl"
        with path.open("w", encoding="utf-8") as f:
            for i, ast in enumerate(group):
                record = {
                    "spec_id": f"{split_name}-{i:06d}",
                    "semantic_ast": ast.to_dict(),
                    "semantic_hash": ast.semantic_hash(),
                    "label": label(ast),
                    # derived from the semantic hash (not the randomized builtin
                    # hash()) so the test suite is reproducible across runs/machines
                    "tests": (generate_boundary_test_cases if split_name == BOUNDARY_SPLIT else generate_test_cases)(
                        ast, seed=SEED ^ int(ast.semantic_hash()[:8], 16)
                    ),
                }
                f.write(json.dumps(record, ensure_ascii=False) + "\n")

        by_num_ops = Counter(ast.num_ops() for ast in group)
        print(f"{split_name}: {len(group)} semantic ASTs -> {path} (by num_ops: {dict(sorted(by_num_ops.items()))})")


if __name__ == "__main__":
    main()
