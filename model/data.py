"""学習データ: data/{train,val}.jsonl -> トークン列 (キャッシュ) -> バッチ。

1例 = ``<|task|>\\n{指示}\\n<|code|>\\n{コード}<|eos|>`` (tokenizer/train_tokenizer.py と同じ形式)。
``<|code|>`` までは損失を計算せず(ラベル -100)、それ以降のコードと <|eos|> だけを予測する。
バッチは右パディング(因果マスクなので前方トークンには影響しない)。
"""

from __future__ import annotations

import hashlib
import json
import sys
from pathlib import Path

import numpy as np
import torch
from tokenizers import Tokenizer

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tokenizer"))
from train_tokenizer import pair_to_text  # noqa: E402

IGNORE = -100
PAD, EOS, CODE = "<|pad|>", "<|eos|>", "<|code|>"


def special_ids(tok: Tokenizer) -> dict[str, int]:
    ids = {name: tok.token_to_id(name) for name in (PAD, EOS, CODE)}
    missing = [n for n, i in ids.items() if i is None]
    if missing:
        raise ValueError(f"トークナイザに特殊トークンがありません: {missing}")
    return ids


def _cache_key(jsonl: Path, tok_path: Path, max_len: int) -> str:
    h = hashlib.sha256()
    for p in (jsonl, tok_path):
        st = p.stat()
        h.update(f"{p.resolve()}:{st.st_size}:{st.st_mtime_ns}".encode())
    h.update(str(max_len).encode())
    return h.hexdigest()[:16]


def load_tokenized(jsonl: Path, tok_path: Path, cache_dir: Path, max_len: int, batch: int = 20000):
    """(flat_ids uint16, offsets int64[N+1], code_pos int32[N]) を返す。max_len超の例は除外。"""
    jsonl, tok_path = Path(jsonl), Path(tok_path)
    cache = Path(cache_dir) / f"{jsonl.stem}-{_cache_key(jsonl, tok_path, max_len)}.npz"
    if cache.exists():
        z = np.load(cache)
        return z["ids"], z["offsets"], z["code_pos"]

    tok = Tokenizer.from_file(str(tok_path))
    if tok.get_vocab_size() > 65535:
        raise ValueError("uint16に収まらない語彙です")
    code_id = special_ids(tok)[CODE]
    chunks: list[np.ndarray] = []
    lengths: list[int] = []
    code_pos: list[int] = []
    dropped = 0

    def flush(texts: list[str]) -> None:
        nonlocal dropped
        for enc in tok.encode_batch(texts, add_special_tokens=False):
            ids = enc.ids
            if len(ids) > max_len or code_id not in ids:
                dropped += 1
                continue
            chunks.append(np.asarray(ids, dtype=np.uint16))
            lengths.append(len(ids))
            code_pos.append(ids.index(code_id))

    buf: list[str] = []
    with jsonl.open(encoding="utf-8") as f:
        for line in f:
            r = json.loads(line)
            for instruction_ja, entry in zip(r["instruction_ja"], r["codes"], strict=True):
                buf.append(pair_to_text(instruction_ja, entry["code"]))
            if len(buf) >= batch:
                flush(buf)
                buf = []
    if buf:
        flush(buf)
    if dropped:
        print(f"[data] {jsonl.name}: max_len={max_len} 超過などで {dropped} 件を除外")

    ids = np.concatenate(chunks)
    offsets = np.concatenate([[0], np.cumsum(lengths)]).astype(np.int64)
    Path(cache_dir).mkdir(parents=True, exist_ok=True)
    np.savez(cache, ids=ids, offsets=offsets, code_pos=np.asarray(code_pos, dtype=np.int32))
    return ids, offsets, np.asarray(code_pos, dtype=np.int32)


class Batcher:
    """例のランダム順(エポックごとにシャッフル)を無限に回すバッチ供給器。"""

    def __init__(self, ids, offsets, code_pos, pad_id: int, batch_size: int, seed: int, shuffle: bool = True):
        self.ids, self.offsets, self.code_pos = ids, offsets, code_pos
        self.pad_id, self.batch_size, self.shuffle = pad_id, batch_size, shuffle
        self.n = len(code_pos)
        self.rng = np.random.default_rng(seed)
        self.epoch = 0
        self._order = self._new_order()
        self._i = 0

    def _new_order(self) -> np.ndarray:
        return self.rng.permutation(self.n) if self.shuffle else np.arange(self.n)

    def next(self) -> tuple[torch.Tensor, torch.Tensor, int]:
        """(input_ids, labels, 実トークン数)"""
        idx = []
        while len(idx) < self.batch_size:
            if self._i >= self.n:
                self._order, self._i, self.epoch = self._new_order(), 0, self.epoch + 1
            take = min(self.batch_size - len(idx), self.n - self._i)
            idx.extend(self._order[self._i : self._i + take])
            self._i += take
        seqs = [self.ids[self.offsets[j] : self.offsets[j + 1]] for j in idx]
        T = max(len(s) for s in seqs)
        x = torch.full((len(seqs), T), self.pad_id, dtype=torch.long)
        y = torch.full((len(seqs), T), IGNORE, dtype=torch.long)
        for r, (j, s) in enumerate(zip(idx, seqs)):
            t = torch.from_numpy(s.astype(np.int64))
            x[r, : len(s)] = t
            c = int(self.code_pos[j])
            y[r, c + 1 : len(s)] = t[c + 1 :]
        return x, y, sum(len(s) for s in seqs)
