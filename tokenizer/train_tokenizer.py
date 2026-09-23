"""Train a single byte-level BPE tokenizer over Japanese instructions *and*
Python code together.

homework.md (トークナイザ節) の推奨設定をそのまま踏襲する:

- 語彙数: 8,192（既定値。呼び出し側で変更可）
- byte fallback: 有効 -- ``pre_tokenizers.ByteLevel`` + 256バイト全てを
  ``initial_alphabet`` として trainer に渡すことで、どんな入力バイト列も
  未知語(UNK)なしで表現できるようにする（``models.BPE(unk_token=None)`` で
  UNKトークン自体を作らない）。
- 日本語とPythonコードを同一語彙で扱う -- ``sampling.sample_pairs`` が返す
  日本語文とコードを区別せず同じイテレータで学習させる。
- 特殊トークンを明示する -- ``SPECIAL_TOKENS``。
"""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, Sequence

from tokenizers import Tokenizer, decoders, models, pre_tokenizers, trainers

SPECIAL_TOKENS: tuple[str, ...] = (
    "<|pad|>",
    "<|bos|>",
    "<|eos|>",
    "<|task|>",
    "<|code|>",
    "<|explanation|>",
)

# homework.mdの学習レコード例（"## モデル仕様"節）と同じ並び:
#   <|task|>
#   {instruction_ja}
#   <|code|>
#   {code}
#   <|eos|>
# code はcode_generator.renderの出力で末尾に改行を含むので、そのまま
# 連結すれば <|eos|> が独立した行になる。
_RECORD_TEMPLATE = "<|task|>\n{instruction_ja}\n<|code|>\n{code}<|eos|>"


def pair_to_text(instruction_ja: str, code: str) -> str:
    """Render one (instruction_ja, code) pair as one training record's text."""
    if not code.endswith("\n"):
        code += "\n"
    return _RECORD_TEMPLATE.format(instruction_ja=instruction_ja, code=code)


def new_tokenizer() -> Tokenizer:
    """A fresh, untrained byte-level BPE tokenizer (no vocab yet)."""
    tokenizer = Tokenizer(models.BPE(unk_token=None))
    tokenizer.pre_tokenizer = pre_tokenizers.ByteLevel(add_prefix_space=False, use_regex=True)
    tokenizer.decoder = decoders.ByteLevel()
    return tokenizer


def build_trainer(vocab_size: int, special_tokens: Sequence[str] = SPECIAL_TOKENS) -> trainers.BpeTrainer:
    return trainers.BpeTrainer(
        vocab_size=vocab_size,
        special_tokens=list(special_tokens),
        initial_alphabet=pre_tokenizers.ByteLevel.alphabet(),
        show_progress=False,
    )


def train_from_texts(
    texts: Iterable[str],
    vocab_size: int = 8192,
    special_tokens: Sequence[str] = SPECIAL_TOKENS,
) -> Tokenizer:
    """Train a byte-level BPE tokenizer on ``texts`` (Japanese and code mixed
    freely -- there is no separate vocabulary per language/domain)."""
    tokenizer = new_tokenizer()
    tokenizer.train_from_iterator(texts, trainer=build_trainer(vocab_size, special_tokens))
    return tokenizer


def save(tokenizer: Tokenizer, path: Path | str) -> Path:
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    tokenizer.save(str(path))
    return path
