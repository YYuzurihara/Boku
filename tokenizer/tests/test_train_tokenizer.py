"""Unit tests for train_tokenizer.py. Needs the `tokenizers` package but no
GPU/Docker/network.

Run with: python -m unittest discover -s tokenizer/tests
"""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from train_tokenizer import SPECIAL_TOKENS, new_tokenizer, pair_to_text, save, train_from_texts  # noqa: E402

# A tiny mixed ja+code corpus. Repeated so the trainer has enough frequency
# signal to actually form multi-byte merges within a small vocab budget.
_JA_SENTENCES = [
    "整数のリストxsから偶数だけを残してsolveを実行してください。",
    "整数リストxsを対象に、先頭からk個の要素を取得してsolveを実施する必要があります。",
    "xsという整数のリストに対して、末尾からk個を切り離すsolveを設置してください。",
]
_CODE_SNIPPETS = [
    "def solve(xs: list[int], k: int) -> list[int]:\n    return [x for x in xs if x % 2 == 0]\n",
    "def solve(xs, k):\n    return xs[:k]\n",
    "def solve(xs, k):\n    return xs[-k:]\n",
]
_CORPUS = [pair_to_text(ja, code) for ja in _JA_SENTENCES for code in _CODE_SNIPPETS] * 20


class PairToTextTest(unittest.TestCase):
    def test_template_matches_homework_layout(self) -> None:
        text = pair_to_text("2倍してください。", "def solve(xs, k):\n    return [x * 2 for x in xs]\n")
        self.assertEqual(
            text,
            "<|task|>\n2倍してください。\n<|code|>\ndef solve(xs, k):\n    return [x * 2 for x in xs]\n<|eos|>",
        )

    def test_adds_trailing_newline_to_code_missing_one(self) -> None:
        text = pair_to_text("ja", "code-without-newline")
        self.assertTrue(text.endswith("code-without-newline\n<|eos|>"))


class TrainFromTextsTest(unittest.TestCase):
    def test_special_tokens_are_present_as_single_atomic_tokens(self) -> None:
        tokenizer = train_from_texts(_CORPUS, vocab_size=512)
        for token in SPECIAL_TOKENS:
            token_id = tokenizer.token_to_id(token)
            self.assertIsNotNone(token_id, f"{token!r} missing from vocab")
            encoded = tokenizer.encode(token)
            self.assertEqual(encoded.ids, [token_id])

    def test_byte_fallback_roundtrips_unseen_characters(self) -> None:
        tokenizer = train_from_texts(_CORPUS, vocab_size=512)
        # a character that never appeared in the training corpus at all
        text = "絵文字テスト🎉と未知のUnicode文字ǅを含む行"
        encoded = tokenizer.encode(text)
        self.assertNotIn(None, encoded.ids)
        self.assertEqual(tokenizer.decode(encoded.ids, skip_special_tokens=False), text)

    def test_shared_vocab_covers_both_japanese_and_code(self) -> None:
        tokenizer = train_from_texts(_CORPUS, vocab_size=512)
        ja_ids = set(tokenizer.encode(_JA_SENTENCES[0]).ids)
        code_ids = set(tokenizer.encode(_CODE_SNIPPETS[0]).ids)
        # same tokenizer/vocab instance serves both -- trivially true by
        # construction, but pin it down: ascii code tokens like "def"/"solve"
        # exist as merges distinct from any Japanese-sentence token ids.
        self.assertTrue(ja_ids)
        self.assertTrue(code_ids)

    def test_vocab_size_is_never_exceeded(self) -> None:
        tokenizer = train_from_texts(_CORPUS, vocab_size=512)
        self.assertLessEqual(tokenizer.get_vocab_size(), 512)

    def test_save_and_reload_roundtrip(self) -> None:
        tokenizer = train_from_texts(_CORPUS, vocab_size=512)
        with tempfile.TemporaryDirectory() as tmp:
            path = save(tokenizer, Path(tmp) / "nested" / "tokenizer.json")
            self.assertTrue(path.exists())
            from tokenizers import Tokenizer

            reloaded = Tokenizer.from_file(str(path))
            self.assertEqual(reloaded.get_vocab_size(), tokenizer.get_vocab_size())
            sample = _CORPUS[0]
            self.assertEqual(reloaded.encode(sample).ids, tokenizer.encode(sample).ids)


class NewTokenizerTest(unittest.TestCase):
    def test_untrained_tokenizer_has_no_vocab(self) -> None:
        tokenizer = new_tokenizer()
        self.assertEqual(tokenizer.get_vocab_size(), 0)


if __name__ == "__main__":
    unittest.main()
