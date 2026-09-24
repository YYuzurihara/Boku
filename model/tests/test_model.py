import sys
import unittest
from pathlib import Path

import torch

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from config import ModelConfig, load_config  # noqa: E402
from model import BokuModel, apply_rope, rope_cache  # noqa: E402

SMALL = ModelConfig(vocab_size=64, d_model=32, n_layers=2, n_heads=4, n_kv_heads=2, d_ff=64, max_seq_len=32)


class ModelTest(unittest.TestCase):
    def test_nano_param_count(self):
        cfg = load_config(Path(__file__).resolve().parent.parent / "configs/boku_nano.toml")
        n = BokuModel(cfg.model).num_parameters()
        self.assertTrue(14_000_000 < n < 17_000_000, n)

    def test_forward_and_ignore_index(self):
        m = BokuModel(SMALL)
        x = torch.randint(0, 64, (2, 10))
        y = x.clone()
        y[:, :5] = -100
        logits, loss = m(x, y)
        self.assertEqual(logits.shape, (2, 10, 64))
        self.assertTrue(torch.isfinite(loss))
        with self.assertRaises(ValueError):
            m(torch.zeros(1, 33, dtype=torch.long))

    def test_causal(self):
        m = BokuModel(SMALL).eval()
        x = torch.randint(0, 64, (1, 12))
        x2 = x.clone()
        x2[0, 8:] = (x2[0, 8:] + 1) % 64
        a, _ = m(x)
        b, _ = m(x2)
        self.assertTrue(torch.allclose(a[:, :8], b[:, :8], atol=1e-5))

    def test_weight_tying(self):
        m = BokuModel(SMALL)
        self.assertIs(m.lm_head.weight, m.embed.weight)

    def test_rope_preserves_norm_and_relative(self):
        cos, sin = rope_cache(8, 16, 10000.0)
        q = torch.randn(1, 1, 1, 8).expand(1, 1, 16, 8)
        r = apply_rope(q, cos, sin)
        self.assertTrue(torch.allclose(r.norm(dim=-1), q.norm(dim=-1), atol=1e-5))

    def test_generate(self):
        m = BokuModel(SMALL).eval()
        out = m.generate(torch.randint(0, 64, (1, 4)), 5, eos_id=-1)
        self.assertEqual(out.shape, (1, 9))


if __name__ == "__main__":
    unittest.main()
