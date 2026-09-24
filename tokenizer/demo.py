"""End-to-end run of the tokenizer training mechanism:

    data/train.jsonl
        -> sampling.sample_pairs      (train split only, p% of the records)
        -> train_tokenizer.pair_to_text
        -> train_tokenizer.train_from_texts  (byte-level BPE, shared ja+code vocab)
        -> tokenizer/out/tokenizer.json

Usage:
    python tokenizer/demo.py
    python tokenizer/demo.py --percent 5 --vocab-size 8192
"""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Optional

from sampling import DEFAULT_TRAIN, sample_pairs
from train_tokenizer import SPECIAL_TOKENS, pair_to_text, save, train_from_texts

_HERE = Path(__file__).resolve().parent
DEFAULT_OUT = _HERE / "out" / "tokenizer.json"


def main(argv: Optional[list[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--train", type=Path, default=DEFAULT_TRAIN)
    parser.add_argument("--percent", type=float, default=10.0, help="train.jsonlから取るレコードの割合 [%%] (既定: 10)")
    parser.add_argument("--vocab-size", type=int, default=2048)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--out", type=Path, default=DEFAULT_OUT)
    args = parser.parse_args(argv)

    if not args.train.exists():
        print(f"missing input: {args.train} (run data/corpus_generator.py first)")
        return 1

    pairs = sample_pairs(args.train, percent=args.percent, seed=args.seed)
    if not pairs:
        print(f"no verified pairs sampled from {args.train} at {args.percent}%")
        return 1

    print(f"sampled {len(pairs)} pairs ({args.percent}% of {args.train.name})")

    texts = [pair_to_text(p.instruction_ja, p.code) for p in pairs]
    print(f"corpus: {len(texts)} records, {sum(len(t) for t in texts)} characters")

    tokenizer = train_from_texts(texts, vocab_size=args.vocab_size)
    print(f"trained vocab size: {tokenizer.get_vocab_size()}")

    out_path = save(tokenizer, args.out)
    print(f"saved -> {out_path}")

    for token in SPECIAL_TOKENS:
        print(f"  special token {token!r} -> id {tokenizer.token_to_id(token)}")

    sample = texts[0]
    encoded = tokenizer.encode(sample)
    decoded = tokenizer.decode(encoded.ids)
    stripped = sample
    for token in ("<|task|>", "<|code|>", "<|eos|>"):
        stripped = stripped.replace(token, "")
    print(f"\nexample record ({len(encoded.ids)} tokens):")
    print(f"  tokens: {encoded.tokens[:24]}{' ...' if len(encoded.tokens) > 24 else ''}")
    print(f"  byte-fallback roundtrip ok: {decoded == stripped}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
