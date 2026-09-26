"""End-to-end run of the structural code transformation: semantic ASTs in,
verified ``solve(xs, k)`` source out.

Pipeline exercised here:

    out/{train,val,test}.jsonl  (demo.py output: semantic AST + tests)
        -> code_styles.select_styles   (tag-gated, rotated per AST)
        -> code_generator.variants     (one rendering per style)
        -> code_verifier.verify        (vs. the reference interpreter)
        -> out/code_<split>.jsonl      (save)
        -> load back + re-render each record  (verify the save round trip)

and, alongside it, a small committed gallery under ``expressions_code/``
(``samples.jsonl`` / ``samples.md``) covering every style and every
structural shape -- the corpus itself is far too large to commit, so that
gallery is what a reviewer reads.

Input semantic ASTs come from ``out/{train,val,test}.jsonl`` when demo.py
has been run; otherwise a deterministic sample is enumerated on the spot and
its test cases generated here, so this script is useful before the full
dataset exists.

Usage:
    python semantic_ast/expressions_code/code_demo.py
    python semantic_ast/expressions_code/code_demo.py --limit 0                 # whole corpus
    python semantic_ast/expressions_code/code_demo.py --sandbox 5             # also spot-check in Docker
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Optional

# generator.py / schema.py live one level up (semantic_ast/), which is not on
# sys.path when this script is run from its own directory.
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from code_generator import (  # noqa: E402
    CodeVariant,
    code_record,
    load_codes,
    render_from_record,
    save_codes,
    variants,
)
from code_styles import STYLES, styles_for  # noqa: E402
from code_verifier import cross_check, ok, verify_variant  # noqa: E402
from generator import enumerate_all  # noqa: E402
from schema import SemanticAST, SemanticASTError  # noqa: E402
from split import ALL_SPLITS  # noqa: E402
from testcases import generate_test_cases  # noqa: E402

# demo.py's splits and this script's corpus output both live in semantic_ast/out/.
OUT_DIR = _HERE.parent / "out"
SPLITS = ALL_SPLITS
SAMPLES_JSONL = _HERE / "samples.jsonl"
SAMPLES_MD = _HERE / "samples.md"
SEED = 0

# An AST + its test suite (from the split file, or generated here).
Item = tuple[str, SemanticAST, list]


def _sample_asts(limit: int) -> list[Item]:
    """A deterministic coverage set: semantic ASTs picked greedily until every
    structural shape, every atomic operation and every style has appeared at
    least once.

    Used when out/*.jsonl is absent, and for the committed gallery -- so the
    gallery shows every composition pattern the generator has to handle
    (single category, chains, filter+map+order, ...), every operation of the
    vocabulary and every catalogue entry (including the tag-gated ones),
    rather than whatever the first N ASTs happen to be.
    """
    every = enumerate_all()

    def styles_of(ast: SemanticAST) -> set:
        return {style.name for style in styles_for(ast)}

    def shape_of(ast: SemanticAST) -> set:
        return {(ast.active_categories(), len(ast.filters), len(ast.map_ops), len(ast.slice_ops))}

    def tags_of(ast: SemanticAST) -> set:
        return set(ast.op_tags())

    def sweep(novelty) -> list[SemanticAST]:
        picked, seen = [], set()
        for ast in every:
            keys = novelty(ast)
            if keys <= seen:
                continue
            seen |= keys
            picked.append(ast)
        return picked

    # Each sweep alone covers one axis in tens of entries, and ``limit`` cuts
    # the gallery long before that, so the three are interleaved rather than
    # concatenated: taking them in turn keeps a truncated gallery balanced
    # across styles, structural shapes and atomic operations instead of
    # spending every slot on the first axis. The 作問例 from homework.md leads,
    # since that is the snippet a reader will want to compare against.
    sweeps = [
        [SemanticAST(filters=("even", "ge_k"), map_ops=(("mul_const", 2),), order_op="ascending")],
        sweep(styles_of),
        sweep(shape_of),
        sweep(tags_of),
    ]
    chosen: dict[str, SemanticAST] = {}
    for row in range(max(len(s) for s in sweeps)):
        for picked in sweeps:
            if row < len(picked):
                chosen.setdefault(picked[row].semantic_hash(), picked[row])

    ordered = list(chosen.values())[: limit or None]
    return [
        (f"sample-{i:06d}", ast, generate_test_cases(ast, seed=SEED ^ int(ast.semantic_hash()[:8], 16)))
        for i, ast in enumerate(ordered)
    ]


def _items_from_split(path: Path, limit: int) -> list[Item]:
    """Semantic ASTs and their stored test suites from one split file."""
    out: list[Item] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            if limit and len(out) >= limit:
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
            out.append((record["spec_id"], ast, record["tests"]))
    return out


def _generate(items: list[Item], extra_seed: Optional[int]) -> tuple[list[dict], list[str], Counter]:
    """Render and verify every item; return (records, problems, style counts)."""
    records: list[dict] = []
    problems: list[str] = []
    style_counts: Counter = Counter()

    for spec_id, ast, tests in items:
        generated = variants(ast)
        if not generated:  # pragma: no cover - the catalogue always applies
            problems.append(f"{spec_id}: no applicable code style")
            continue
        verifications = []
        for variant in generated:
            verification = verify_variant(variant, tests)
            if extra_seed is not None and ok(verification):
                # fresh random inputs the stored suite never contained
                verification["cross_check_ok"] = ok(cross_check(ast, variant.code, seed=extra_seed))
                if not verification["cross_check_ok"]:
                    problems.append(f"{spec_id} [{variant.style.name}]: cross-check against the interpreter failed")
            verifications.append(verification)
            style_counts[variant.style.name] += 1
            if not ok(verification):
                problems.append(_failure_report(spec_id, variant, verification))
        records.append(code_record(ast, generated, spec_id=spec_id, verifications=verifications))
    return records, problems, style_counts


def _failure_report(spec_id: str, variant: CodeVariant, verification: dict) -> str:
    lines = [f"{spec_id} [{variant.style.name}]: {verification.get('error')}"]
    for failure in verification.get("failures", []):
        lines.append(
            f"    xs={failure['xs']} k={failure['k']} expected={failure['expected']} actual={failure['actual']}"
        )
    lines.append("".join(f"    | {line}\n" for line in variant.code.splitlines()).rstrip())
    return "\n".join(lines)


def _verify_round_trip(path: Path) -> list[str]:
    """Every saved snippet must re-render byte-identically from its
    ``(semantic_ast, code_style)`` pair -- the generator is deterministic, so
    a mismatch means the corpus on disk no longer matches the generator that
    is supposed to have produced it."""
    problems: list[str] = []
    for record in load_codes(path):
        rendered = render_from_record(record)
        saved = [entry["code"] for entry in record["codes"]]
        if rendered != saved:
            problems.append(f"{record.get('spec_id')}: saved code does not match a fresh rendering")
    return problems


def _write_gallery(records: list[dict]) -> None:
    """The committed 出力されたコード: every rendering of the coverage set."""
    save_codes(records, SAMPLES_JSONL)
    lines = [
        "# 生成コードのサンプル",
        "",
        "`code_demo.py` が生成したコードの抜粋（自動生成。手で編集しない）。",
        "意味ASTの構成パターンと原子操作を網羅するように選んだ意味ASTについて、",
        "適用できる`code_style`すべてでレンダリングしたもの。全件は",
        "`semantic_ast/out/code_{train,val,test}.jsonl`（生成物、gitignore済み）にある。",
        "",
        "各コードは参照インタプリタと全テストケースで一致することを確認済み",
        "（`verification`は`samples.jsonl`側に入っている）。",
        "",
    ]
    for record in records:
        lines.append(f"## `{json.dumps(record['semantic_ast'], ensure_ascii=False)}`")
        lines.append("")
        for entry in record["codes"]:
            lines.append(f"### {entry['code_style']}")
            lines.append("")
            lines.append("```python")
            lines.append(entry["code"].rstrip("\n"))
            lines.append("```")
            lines.append("")
    SAMPLES_MD.write_text("\n".join(lines), encoding="utf-8")


def _spot_check_sandbox(records: list[dict], count: int) -> list[str]:
    """Run a few snippets through the real Docker sandbox and confirm it
    agrees with the in-process verification (see code_verifier's docstring)."""
    from code_verifier import verify_in_sandbox  # noqa: PLC0415 - Docker only on this path

    problems: list[str] = []
    checked = 0
    for record in records:
        ast = SemanticAST.from_dict(record["semantic_ast"])
        tests = generate_test_cases(ast, seed=SEED ^ int(ast.semantic_hash()[:8], 16))
        for entry in record["codes"]:
            if checked >= count:
                return problems
            verdict = verify_in_sandbox(entry["code"], tests)
            checked += 1
            if not verdict.get("tests_passed"):
                problems.append(
                    f"{record.get('spec_id')} [{entry['code_style']}]: sandbox verdict "
                    f"{json.dumps({k: verdict.get(k) for k in ('syntax_ok', 'ast_safe', 'executable', 'tests_passed', 'error')}, ensure_ascii=False)}"
                )
    return problems


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--limit", type=int, default=200, help="semantic ASTs per split, 0 for all (default: 200)")
    parser.add_argument("--sample-limit", type=int, default=16, help="semantic ASTs in the committed gallery (default: 16)")
    parser.add_argument("--no-gallery", action="store_true", help="do not rewrite samples.jsonl / samples.md")
    parser.add_argument("--cross-check-seed", type=int, default=SEED + 1, help="seed for the extra random comparison against the reference interpreter (-1 to skip)")
    parser.add_argument("--sandbox", type=int, default=0, help="also run N gallery snippets through the Docker sandbox")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR)
    parser.add_argument("--show", type=int, default=2, help="example snippets to print per split")
    args = parser.parse_args(argv)

    extra_seed = None if args.cross_check_seed < 0 else args.cross_check_seed
    failures = 0

    print(f"style catalogue: {len(STYLES)} styles ({', '.join(style.name for style in STYLES)})")

    # -- the committed gallery ------------------------------------------------
    gallery_items = _sample_asts(args.sample_limit)
    gallery_records, gallery_problems, gallery_styles = _generate(gallery_items, extra_seed=extra_seed)
    snippets = sum(len(r["codes"]) for r in gallery_records)
    print(f"\ngallery: {len(gallery_records)} semantic ASTs -> {snippets} snippets")
    print(f"  styles used: {dict(sorted(gallery_styles.items()))}")
    if gallery_problems:
        failures += len(gallery_problems)
        print(f"  VERIFY FAILED ({len(gallery_problems)}):")
        for problem in gallery_problems[:5]:
            print(f"    - {problem}")
    else:
        print(f"  verify ok: every snippet matches the reference interpreter on its full test suite")
    if not args.no_gallery:
        _write_gallery(gallery_records)
        print(f"  wrote {SAMPLES_JSONL.name} and {SAMPLES_MD.name}")

    if args.sandbox:
        sandbox_problems = _spot_check_sandbox(gallery_records, args.sandbox)
        failures += len(sandbox_problems)
        for problem in sandbox_problems:
            print(f"  SANDBOX FAILED - {problem}")
        if not sandbox_problems:
            print(f"  sandbox spot check ok ({args.sandbox} snippet(s) agree with the in-process run)")

    # -- the corpus -----------------------------------------------------------
    sources: list[tuple[str, list[Item]]] = []
    for split in SPLITS:
        path = args.out_dir / f"ast_{split}.jsonl"
        if path.exists():
            sources.append((split, _items_from_split(path, args.limit)))
    if not sources:
        print(f"\nno {args.out_dir}/*.jsonl (run demo.py first); the gallery above is all that was generated")
        return 1 if failures else 0

    for split, items in sources:
        records, problems, style_counts = _generate(items, extra_seed)
        path = save_codes(records, args.out_dir / f"code_{split}.jsonl")
        snippets = sum(len(r["codes"]) for r in records)
        distinct = len({entry["code_sha256"] for r in records for entry in r["codes"]})
        print(f"\n{split}: {len(records)} semantic ASTs -> {snippets} snippets ({distinct} distinct) -> {path}")
        print(f"  styles used: {dict(sorted(style_counts.items()))}")

        for record in records[: args.show]:
            print(f"  {json.dumps(record['semantic_ast'], ensure_ascii=False)}")
            for entry in record["codes"][:1]:
                print(f"    [{entry['code_style']}]")
                for line in entry["code"].splitlines():
                    print(f"    {line}")

        problems += _verify_round_trip(path)
        if problems:
            failures += len(problems)
            print(f"  VERIFY FAILED ({len(problems)} problem(s)):")
            for problem in problems[:5]:
                print(f"    - {problem}")
        else:
            print(f"  verify ok: {snippets} snippets match the reference interpreter and re-render identically")

    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
