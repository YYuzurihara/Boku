"""End-to-end check that expression dictionary + combined Japanese survive a
save/load round trip.

Pipeline exercised here (the right-hand half of ja_generator_plan.md's
diagram):

    candidates.json  (ja_teacher.py output, or --dictionary)
        -> ja_dictionary.ExpressionDictionary  (structural validation)
        -> ja_generator.render_variants        (per semantic AST)
        -> out/instructions_<split>.jsonl      (save)
        -> load back + replay each record's recorded choices  (verify)

The verification step is the point of this script: a saved instruction is
only trustworthy if the exact same sentence can be rebuilt from the saved
(dictionary, choices) pair, so every record is replayed after being read
back and any mismatch is reported as a failure.

Input semantic ASTs come from ``out/{train,val,test}.jsonl`` when demo.py
has been run; otherwise a small deterministic sample is enumerated on the
spot, so this script is useful before the full dataset exists.

Usage:
    python semantic_ast/expressions_ja/ja_demo.py
    python semantic_ast/expressions_ja/ja_demo.py --dictionary semantic_ast/expressions_ja/approved.json
    python semantic_ast/expressions_ja/ja_demo.py --limit 50 --variants 5
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Optional

# generator.py / schema.py live one level up (semantic_ast/), which is not on
# sys.path when this script is run from its own directory.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from generator import enumerate_all  # noqa: E402
from ja_dictionary import CANDIDATES_PATH, ExpressionDictionary, ExpressionDictionaryError  # noqa: E402
from ja_generator import (  # noqa: E402
    contract_problems,
    instruction_record,
    leftover_placeholders,
    load_instructions,
    render_from_record,
    render_variants,
    save_instructions,
)
from schema import SemanticAST, SemanticASTError  # noqa: E402

# demo.py's splits and this script's output both live in semantic_ast/out/.
OUT_DIR = Path(__file__).resolve().parent.parent / "out"
SPLITS = ("train", "val", "test")
SEED = 0


def _sample_asts(limit: int) -> list[tuple[str, SemanticAST]]:
    """A deterministic spread of semantic ASTs, used when out/*.jsonl is
    absent: the first AST of each distinct (num_categories, category tuple)
    shape, so every composition rule in ja_generator_plan.md section 2 gets
    exercised (single category, chains, filter+map+order, ...)."""
    by_shape: dict[tuple, SemanticAST] = {}
    for ast in enumerate_all():
        shape = (ast.active_categories(), len(ast.filters), len(ast.map_ops), len(ast.slice_ops))
        by_shape.setdefault(shape, ast)
    chosen = list(by_shape.values())[:limit]
    return [(f"sample-{i:06d}", ast) for i, ast in enumerate(chosen)]


def _asts_from_split(path: Path, limit: int) -> list[tuple[str, SemanticAST]]:
    out: list[tuple[str, SemanticAST]] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if len(out) >= limit:
                break
            record = json.loads(line)
            try:
                ast = SemanticAST.from_dict(record["semantic_ast"])
            except SemanticASTError as exc:
                # e.g. a file written before schema.py narrowed the vocabulary
                raise SystemExit(
                    f"{path} holds a semantic AST the current schema rejects "
                    f"({record.get('spec_id')}: {exc}).\n"
                    f"Re-run `python semantic_ast/demo.py` to regenerate the splits."
                ) from None
            out.append((record["spec_id"], ast))
    return out


def _verify(path: Path, dictionary: ExpressionDictionary) -> list[str]:
    """Read back a saved JSONL file and check every record replays exactly."""
    problems: list[str] = []
    records = load_instructions(path)
    for record in records:
        replayed = render_from_record(record, dictionary)
        if replayed != record["instruction_ja"]:
            problems.append(f"{record.get('spec_id')}: replay mismatch\n  saved:    {record['instruction_ja']}\n  replayed: {replayed}")
        if record["dictionary_sha256"] != dictionary.content_sha256():
            problems.append(f"{record.get('spec_id')}: dictionary hash does not match the dictionary in use")
        for text in record["instruction_ja"]:
            leftover = leftover_placeholders(text)
            if leftover:
                problems.append(f"{record.get('spec_id')}: unsubstituted placeholder(s) {leftover} in: {text}")
    return problems


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--dictionary", type=Path, default=CANDIDATES_PATH)
    parser.add_argument("--limit", type=int, default=200, help="semantic ASTs per split (default: 200)")
    parser.add_argument("--variants", type=int, default=3, help="Japanese variants per semantic AST (default: 3)")
    parser.add_argument("--show", type=int, default=5, help="example sentences to print per split")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    args = parser.parse_args(argv)

    try:
        dictionary = ExpressionDictionary.load(args.dictionary, strict=True)
    except ExpressionDictionaryError as exc:
        print(f"cannot use the expression dictionary:\n{exc}", file=sys.stderr)
        print("\n(run: python semantic_ast/expressions_ja/ja_teacher.py  to generate one)", file=sys.stderr)
        return 1

    missing = dictionary.missing_keys()
    print(f"dictionary {args.dictionary} : {len(dictionary)} keys, sha256 {dictionary.content_sha256()[:12]}")
    print(f"  expressions per key: {dictionary.counts()}")
    if missing:
        print(f"  missing keys (renders needing them will fail): {', '.join(missing)}")

    # Not a failure: the dictionary is still the candidates file until a human
    # has been through it. Reported up front so the odd sentences printed
    # below can be read off against the entries that caused them.
    contract = contract_problems(dictionary)
    if contract:
        print(f"  {len(contract)} expression(s) break the combination contract, e.g.:")
        for problem in contract[:3]:
            print(f"    - {problem}")
        print("    (full list: python semantic_ast/expressions_ja/ja_teacher.py --report-contract)")

    sources: list[tuple[str, list[tuple[str, SemanticAST]]]] = []
    for split in SPLITS:
        path = args.out_dir / f"{split}.jsonl"
        if path.exists():
            sources.append((split, _asts_from_split(path, args.limit)))
    if not sources:
        print(f"\nno {args.out_dir}/*.jsonl (run demo.py first); using an enumerated sample instead")
        sources.append(("sample", _sample_asts(args.limit)))

    failures = 0
    for split, items in sources:
        records = []
        for spec_id, ast in items:
            renderings = render_variants(ast, dictionary, n=args.variants, seed=SEED)
            records.append(instruction_record(ast, renderings, dictionary, spec_id=spec_id, seed=SEED))

        path = save_instructions(records, args.out_dir / f"instructions_{split}.jsonl")
        total = sum(len(r["instruction_ja"]) for r in records)
        distinct = len({text for r in records for text in r["instruction_ja"]})
        print(f"\n{split}: {len(records)} semantic ASTs -> {total} instructions ({distinct} distinct) -> {path}")

        for record in records[: args.show]:
            print(f"  {json.dumps(record['semantic_ast'], ensure_ascii=False)}")
            for text in record["instruction_ja"]:
                print(f"    {text}")

        problems = _verify(path, dictionary)
        if problems:
            failures += len(problems)
            print(f"  VERIFY FAILED ({len(problems)} problem(s)):")
            for problem in problems[:10]:
                print(f"    - {problem}")
        else:
            print(f"  verify ok: all {len(records)} records reload and replay to the same sentences")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
