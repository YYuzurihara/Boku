"""意味ASTベースの最終コーパス生成。

train/val/testそれぞれについて、意味AST（`spec_id`）を20件サンプリングし、
その意味ASTに紐づく日本語表現・生成コードを**すべて**1レコードにまとめて
``data/{train,val,test}.jsonl`` に書き出す。

入力は ``semantic_ast/out/`` にある3種類の生成物（いずれも `spec_id` で結合できる）。

    ast_{split}.jsonl           意味AST本体 + テストケース（semantic_ast/demo.py）
    instructions_{split}.jsonl  日本語表現（言い換え複数）（expressions_ja/ja_demo.py）
    code_{split}.jsonl          生成コード（スタイル複数）（expressions_code/code_demo.py）

日本語表現の生成は教師モデルへの問い合わせを伴うため、
``instructions_{split}.jsonl`` は各splitの意味ASTのうち一部（既定200件）にしか
存在しない。そのため、サンプリング対象となる意味ASTは3ファイルすべてに
`spec_id` が存在するものに限られ、実質的に ``instructions_{split}.jsonl`` が
上限を決める。

サンプリングの単位は意味AST（`spec_id`）そのものであり、1つの意味ASTに
紐づく日本語表現の言い換えとコードのスタイル違いは分割せず1レコードに
まとめる。意味ASTを分割した後で言い換えやコード変換を行うことで
train/val/testにまたがる表記違いの混入（データ漏洩）を避ける、という
``semantic_ast`` パッケージ全体の方針（`semantic_ast/README.md`）を
ここでも踏襲している。

再現性のため、出力の各行には必ず ``semantic_ast`` / ``semantic_hash`` /
サンプリングに使った ``sample_seed`` を含める。

使い方:
    python data/corpus_generator.py
    python data/corpus_generator.py --sample-size 20 --seed 0
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections.abc import Iterable, Sequence
from pathlib import Path
from typing import Optional

SPLITS = ("train", "val", "test")
SAMPLE_SIZE = 20
SEED = 0

_HERE = Path(__file__).resolve().parent
SRC_DIR = _HERE.parent / "semantic_ast" / "out"
OUT_DIR = _HERE


def load_jsonl(path: Path) -> list[dict]:
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def save_jsonl(records: Iterable[dict], path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def _index_by_spec_id(records: Sequence[dict]) -> dict[str, dict]:
    return {record["spec_id"]: record for record in records}


def sample_spec_ids(spec_ids: Iterable[str], n: int, seed: int) -> list[str]:
    """``n``件を決定的にサンプリングする。集合/辞書の反復順序に依存しない
    よう、シャッフル前に必ずソートしてから ``random.Random(seed)`` で選ぶ。"""
    ordered = sorted(spec_ids)
    rng = random.Random(seed)
    return rng.sample(ordered, min(n, len(ordered)))


def build_record(spec_id: str, ast_record: dict, instr_record: dict, code_record: dict, seed: int) -> dict:
    """1つの意味ASTについて、日本語表現・生成コードをすべて合わせた1レコード。"""
    semantic_ast = ast_record["semantic_ast"]
    semantic_hash = ast_record["semantic_hash"]
    if not (instr_record["semantic_hash"] == semantic_hash and code_record["semantic_hash"] == semantic_hash):
        raise ValueError(f"{spec_id}: ast/instructions/code の semantic_hash が一致しません")
    return {
        "spec_id": spec_id,
        "semantic_ast": semantic_ast,
        "semantic_hash": semantic_hash,
        "sample_seed": seed,
        "instruction_ja": instr_record["instruction_ja"],
        "codes": code_record["codes"],
        "tests": ast_record["tests"],
    }


def build_split_corpus(split: str, *, src_dir: Path, n: int, seed: int) -> list[dict]:
    ast_path = src_dir / f"ast_{split}.jsonl"
    instr_path = src_dir / f"instructions_{split}.jsonl"
    code_path = src_dir / f"code_{split}.jsonl"
    missing_paths = [p for p in (ast_path, instr_path, code_path) if not p.exists()]
    if missing_paths:
        raise SystemExit(
            "以下の入力ファイルがありません: " + ", ".join(str(p) for p in missing_paths) + "\n"
            "先に `python semantic_ast/demo.py`、"
            "`python semantic_ast/expressions_ja/ja_demo.py`、"
            "`python semantic_ast/expressions_code/code_demo.py` を実行してください。"
        )

    ast_by_id = _index_by_spec_id(load_jsonl(ast_path))
    instr_by_id = _index_by_spec_id(load_jsonl(instr_path))
    code_by_id = _index_by_spec_id(load_jsonl(code_path))

    # instructions_{split}.jsonl は各splitの一部の意味ASTにしか存在しない
    # （教師モデル問い合わせのコストのため）ので、サンプリング対象はここが上限になる。
    candidates = set(instr_by_id) & set(ast_by_id) & set(code_by_id)
    missing = set(instr_by_id) - candidates
    if missing:
        raise SystemExit(
            f"{split}: instructions_{split}.jsonl の spec_id が ast/code に見つかりません "
            f"(例: {sorted(missing)[:5]})。生成物が古い可能性があるため、"
            f"semantic_ast/demo.py 以降を再実行してください。"
        )

    sampled_ids = sample_spec_ids(candidates, n, seed)
    return [
        build_record(spec_id, ast_by_id[spec_id], instr_by_id[spec_id], code_by_id[spec_id], seed)
        for spec_id in sampled_ids
    ]


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--sample-size", type=int, default=SAMPLE_SIZE, help=f"split毎のサンプル件数 (default: {SAMPLE_SIZE})")
    parser.add_argument("--seed", type=int, default=SEED, help=f"サンプリングのrandom seed (default: {SEED})")
    parser.add_argument("--src-dir", type=Path, default=SRC_DIR, help="semantic_ast/out/ の場所")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="出力先ディレクトリ (default: data/)")
    args = parser.parse_args(argv)

    for split in SPLITS:
        records = build_split_corpus(split, src_dir=args.src_dir, n=args.sample_size, seed=args.seed)
        path = save_jsonl(records, args.out_dir / f"{split}.jsonl")
        print(f"{split}: {len(records)}件の意味AST -> {path} (seed={args.seed})")

    return 0


if __name__ == "__main__":
    sys.exit(main())
