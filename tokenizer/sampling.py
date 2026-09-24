"""Sample (instruction_ja, code) pairs for tokenizer training from
``data/train.jsonl``.

homework.md (トークナイザ節): 「訓練データだけを用いて、BPEまたはUnigramトークナイザを作成する」。
``data/train.jsonl`` は1行 = 1レコード（``instruction_ja`` 1件 + ``codes`` 1件）で、
train splitのみを含む。そこから全体の ``percent`` % をレコード単位で一様に
（非復元で）取り出す。val/testのファイルはこのモジュールに登場しない。
"""

from __future__ import annotations

import json
import random
from dataclasses import dataclass
from pathlib import Path

_HERE = Path(__file__).resolve().parent
DEFAULT_TRAIN = _HERE.parent / "data" / "train.jsonl"

# code_verifier が書き込むフラグのうち「学習コーパスに入れてよい」最低限の組。
# cross_check_ok はキー自体が無いことがあるので個別に扱う（無ければ通す）。
_REQUIRED_VERIFICATION_FLAGS = ("syntax_ok", "ast_safe", "executable", "tests_passed", "pure")


@dataclass(frozen=True)
class Pair:
    spec_id: str
    semantic_hash: str
    instruction_ja: str
    code: str


def _code_is_verified(entry: dict) -> bool:
    verification = entry.get("verification", {})
    if verification.get("error") is not None:
        return False
    if not all(verification.get(flag) for flag in _REQUIRED_VERIFICATION_FLAGS):
        return False
    return verification.get("cross_check_ok", True) is not False


def sample_pairs(
    train_path: Path | str = DEFAULT_TRAIN,
    percent: float = 10.0,
    seed: int = 0,
) -> list[Pair]:
    """Take ``percent`` % of the records of ``train_path`` uniformly at random.

    The number of records taken is ``round(N * percent / 100)`` where N is the
    number of non-empty lines; which ones is decided by ``random.Random(seed)``
    over line indices, so the sample is reproducible. Unverified records are
    dropped *after* sampling (so the fraction is of the file, not of the
    verified subset). The file is read twice (count, then pick) and only the
    selected lines are parsed, so memory stays proportional to the sample.
    """
    if not 0 <= percent <= 100:
        raise ValueError(f"percent must be in [0, 100], got {percent}")
    path = Path(train_path)

    with path.open(encoding="utf-8") as f:
        total = sum(1 for line in f if line.strip())
    chosen = set(random.Random(seed).sample(range(total), round(total * percent / 100)))

    pairs: list[Pair] = []
    index = 0
    with path.open(encoding="utf-8") as f:
        for line in f:
            if not line.strip():
                continue
            if index in chosen:
                record = json.loads(line)
                if _code_is_verified(record["codes"]):
                    pairs.append(
                        Pair(
                            spec_id=record["spec_id"],
                            semantic_hash=record.get("semantic_hash", ""),
                            instruction_ja=record["instruction_ja"],
                            code=record["codes"]["code"],
                        )
                    )
            index += 1
    return pairs
