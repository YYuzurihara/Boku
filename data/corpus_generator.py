"""意味ASTベースの最終コーパス生成。

train/val/testそれぞれについて、``ast_{split}.jsonl`` の意味AST（`spec_id`）を
1行ずつ取り出し、その意味ASTに紐づく日本語表現7件 × 生成コード3件の
全組み合わせ（21件）をそれぞれ1レコードとして ``data/{train,val,test}.jsonl``
に書き出す。意味ASTが約3万件あれば、コーパス全体は約63万レコードになる。

入力は ``semantic_ast/out/`` にある3種類の生成物（いずれも `spec_id` で結合できる）。

    ast_{split}.jsonl           意味AST本体 + テストケース（semantic_ast/demo.py）
    instructions_{split}.jsonl  日本語表現（言い換え複数）（expressions_ja/ja_demo.py）
                                ``instruction_ja``: 文字列のリスト
    code_{split}.jsonl          生成コード（スタイル複数）（expressions_code/code_demo.py）
                                ``codes``: {code_style, code, code_sha256, verification} のリスト

``ast_{split}.jsonl`` のすべての意味ASTについて、日本語表現・生成コードが
揃っている必要がある（欠けていればエラーで止める）。

1つの意味ASTに紐づく日本語表現の言い換えとコードのスタイル違いは同じsplitに
まとめて展開する。意味ASTを分割した後で言い換えやコード変換を行うことで
train/val/testにまたがる表記違いの混入（データ漏洩）を避ける、という
``semantic_ast`` パッケージ全体の方針（`semantic_ast/README.md`）を
ここでも踏襲している。

再現性のため、出力の各行には必ず ``semantic_ast`` / ``semantic_hash`` を含める。

使い方:
    python data/corpus_generator.py
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Iterator
from pathlib import Path
from typing import Optional

SPLITS = ("train", "val", "test")
# 1つの意味ASTあたりの日本語表現・コード表現の件数（組み合わせで 7 × 3 = 21件）
N_INSTRUCTIONS = 7
N_CODES = 3

_HERE = Path(__file__).resolve().parent
SRC_DIR = _HERE.parent / "semantic_ast" / "out"
OUT_DIR = _HERE


def iter_jsonl(path: Path) -> Iterator[dict]:
    with path.open(encoding="utf-8") as f:
        for line in f:
            if line.strip():
                yield json.loads(line)


def _index_by_spec_id(path: Path, field: str) -> dict[str, tuple[str, list]]:
    """``spec_id -> (semantic_hash, record[field])``。約3万件を保持するため、
    結合に必要なフィールドだけを残す。"""
    return {record["spec_id"]: (record["semantic_hash"], record[field]) for record in iter_jsonl(path)}


def build_records(
    ast_record: dict, instr_entry: tuple[str, list], code_entry: tuple[str, list]
) -> list[dict]:
    """1つの意味ASTについて、日本語表現 × 生成コードの全組み合わせ（21件）のレコード。"""
    spec_id = ast_record["spec_id"]
    semantic_hash = ast_record["semantic_hash"]
    instr_hash, instructions = instr_entry
    code_hash, codes = code_entry
    if not (instr_hash == semantic_hash and code_hash == semantic_hash):
        raise ValueError(f"{spec_id}: ast/instructions/code の semantic_hash が一致しません")
    if len(instructions) != N_INSTRUCTIONS or len(codes) != N_CODES:
        raise ValueError(
            f"{spec_id}: 日本語表現{len(instructions)}件・コード{len(codes)}件です"
            f"（期待値: 日本語表現{N_INSTRUCTIONS}件・コード{N_CODES}件）"
        )
    return [
        {
            "spec_id": spec_id,
            "semantic_ast": ast_record["semantic_ast"],
            "semantic_hash": semantic_hash,
            "instruction_ja": instruction,
            "codes": code,
            "tests": ast_record["tests"],
        }
        for instruction in instructions
        for code in codes
    ]


def build_split_corpus(split: str, *, src_dir: Path, out_path: Path) -> tuple[int, int]:
    """``ast_{split}.jsonl`` を1行ずつ21レコードに展開して ``out_path`` に書き出す。
    戻り値は (意味AST件数, レコード件数)。"""
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

    instr_by_id = _index_by_spec_id(instr_path, "instruction_ja")
    code_by_id = _index_by_spec_id(code_path, "codes")

    n_specs = n_records = 0
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for ast_record in iter_jsonl(ast_path):
            spec_id = ast_record["spec_id"]
            if spec_id not in instr_by_id or spec_id not in code_by_id:
                raise SystemExit(
                    f"{split}: {spec_id} の日本語表現またはコードが "
                    f"instructions_{split}.jsonl / code_{split}.jsonl に見つかりません。"
                    f"生成物が古い可能性があるため、semantic_ast/demo.py 以降を再実行してください。"
                )
            for record in build_records(ast_record, instr_by_id[spec_id], code_by_id[spec_id]):
                f.write(json.dumps(record, ensure_ascii=False) + "\n")
                n_records += 1
            n_specs += 1
    return n_specs, n_records


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--src-dir", type=Path, default=SRC_DIR, help="semantic_ast/out/ の場所")
    parser.add_argument("--out-dir", type=Path, default=OUT_DIR, help="出力先ディレクトリ (default: data/)")
    args = parser.parse_args(argv)

    for split in SPLITS:
        path = args.out_dir / f"{split}.jsonl"
        n_specs, n_records = build_split_corpus(split, src_dir=args.src_dir, out_path=path)
        print(f"{split}: {n_specs}件の意味AST / {n_records}レコード -> {path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
