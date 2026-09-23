"""Sample (instruction_ja, code) pairs per semantic AST, from the *train*
split only.

homework.md (トークナイザ節): 「訓練データだけを用いて、BPEまたはUnigram
トークナイザを作成する」。ここでの「訓練データ」は
``semantic_ast/out/instructions_train.jsonl`` と ``semantic_ast/out/code_train.jsonl``
の交差（同じ ``spec_id`` = 同じ意味AST）を指す。val/test側のファイルはこの
モジュールに一切登場しない -- 呼び出し側が誤って渡さない限りトークナイザの
語彙にval/testの文字列が混ざることは構造的に起こらない。

現状は日本語表現の生成（``expressions_ja/``）がコード生成（``expressions_code/``）
より進んでいないため、``instructions_train.jsonl`` の件数は ``code_train.jsonl``
よりずっと少ない。両ファイルに共通する ``spec_id`` だけが対象になる。
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from itertools import product
from pathlib import Path

_HERE = Path(__file__).resolve().parent
DEFAULT_OUT_DIR = _HERE.parent / "semantic_ast" / "out"
DEFAULT_INSTRUCTIONS_TRAIN = DEFAULT_OUT_DIR / "instructions_train.jsonl"
DEFAULT_CODE_TRAIN = DEFAULT_OUT_DIR / "code_train.jsonl"

# code_verifier.verify_variant / cross_check が書き込むフラグのうち、
# 「学習コーパスに入れてよい」と言える最低限の組。cross_check_ok は
# 呼び出し側が cross-check を省略した場合キー自体が無いことがあるので
# 個別に扱う（無ければ通す、あれば True を要求する）。
_REQUIRED_VERIFICATION_FLAGS = ("syntax_ok", "ast_safe", "executable", "tests_passed", "pure")


@dataclass(frozen=True)
class Pair:
    spec_id: str
    semantic_hash: str
    instruction_ja: str
    code: str


def _read_jsonl(path: Path) -> list[dict]:
    records: list[dict] = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                records.append(json.loads(line))
    return records


def _code_is_verified(entry: dict) -> bool:
    verification = entry.get("verification", {})
    if verification.get("error") is not None:
        return False
    if not all(verification.get(flag) for flag in _REQUIRED_VERIFICATION_FLAGS):
        return False
    return verification.get("cross_check_ok", True) is not False


def sample_pairs(
    instructions_path: Path | str = DEFAULT_INSTRUCTIONS_TRAIN,
    code_path: Path | str = DEFAULT_CODE_TRAIN,
    n_per_ast: int = 5,
    seed: int = 0,
) -> list[Pair]:
    """Take up to ``n_per_ast`` (instruction_ja, code) pairs per semantic AST.

    For each ``spec_id`` present in *both* files, pairs are sampled from the
    cartesian product of that AST's instruction renderings and its verified
    code variants (typically 3 x 3 = 9), using a seed derived from
    ``(seed, spec_id)`` -- the same per-key-RNG convention as
    ``semantic_ast/split.py`` -- so the sample is reproducible regardless of
    file ordering. If fewer than ``n_per_ast`` combinations exist, all of
    them are returned (no repeats).

    Records with no instructions or no verified code are skipped.
    """
    instructions_by_id = {r["spec_id"]: r for r in _read_jsonl(Path(instructions_path))}
    codes_by_id = {r["spec_id"]: r for r in _read_jsonl(Path(code_path))}

    pairs: list[Pair] = []
    for spec_id in sorted(set(instructions_by_id) & set(codes_by_id)):
        instr_record = instructions_by_id[spec_id]
        code_record = codes_by_id[spec_id]
        instructions: list[str] = instr_record["instruction_ja"]
        codes = [entry["code"] for entry in code_record["codes"] if _code_is_verified(entry)]
        if not instructions or not codes:
            continue

        combos = list(product(instructions, codes))
        rng = random.Random(repr((seed, spec_id)))
        rng.shuffle(combos)

        semantic_hash = instr_record.get("semantic_hash") or code_record.get("semantic_hash", "")
        for instruction_ja, code in combos[:n_per_ast]:
            pairs.append(
                Pair(
                    spec_id=spec_id,
                    semantic_hash=semantic_hash,
                    instruction_ja=instruction_ja,
                    code=code,
                )
            )
    return pairs
