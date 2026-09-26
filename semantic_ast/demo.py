"""End-to-end demo / manual smoke test for the semantic_ast package.

Enumerates the full DSL space, dedups, splits it into train/val/test plus the
three extra test sets of homework.md (言い換え / 組合せ汎化 / 境界値; stratified
by problem characteristics), verifies no semantic AST leaked across splits,
caps each split so no single characteristic dominates, generates a test
suite per semantic AST via the reference interpreter, and writes one JSONL
file per split under ``semantic_ast/out/``.

This does not touch the teacher model, Japanese instructions, or code
generation -- those are later task-list items. It only produces the
``semantic_ast`` (+ generated ``tests``) fields of homework.md's データ
レコード schema, for every split.

Usage: python semantic_ast/demo.py
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

from generator import count_all, enumerate_all, label
from split import (
    BOUNDARY_SPLIT,
    SplitRatios,
    build_eval_splits,
    cap_per_label,
    check_holdout_pairs,
    check_no_leakage,
    dedup_by_hash,
)
from testcases import generate_boundary_test_cases, generate_test_cases

SEED = 0
MAX_PER_LABEL = 500  # generous cap; tightened once instruction/code counts are known
OUT_DIR = Path(__file__).resolve().parent / "out"


def main() -> None:
    print(f"enumerating full semantic AST space... {count_all()} distinct semantic ASTs")
    all_asts = enumerate_all()

    deduped = dedup_by_hash(all_asts)
    print(f"after dedup: {len(deduped)} (dropped {len(all_asts) - len(deduped)})")

    splits = build_eval_splits(deduped, ratios=SplitRatios(0.8, 0.1, 0.1), seed=SEED)
    check_no_leakage(splits)
    check_holdout_pairs(splits)
    print("leakage check passed: no semantic AST hash appears in more than one split")
    print("holdout check passed: no held-out operation pair occurs outside test_compositional")

    capped = {
        name: cap_per_label(group, max_per_label=MAX_PER_LABEL, seed=SEED)
        for name, group in splits.items()
    }
    check_no_leakage(capped)
    check_holdout_pairs(capped)

    OUT_DIR.mkdir(exist_ok=True)
    for split_name, group in capped.items():
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

        by_num_categories = Counter(ast.num_categories() for ast in group)
        print(f"{split_name}: {len(group)} semantic ASTs -> {path} (by num_categories: {dict(sorted(by_num_categories.items()))})")


if __name__ == "__main__":
    main()
