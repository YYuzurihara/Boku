import sys
import tempfile
import unittest
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from data import Batcher  # noqa: E402


class BatcherTest(unittest.TestCase):
    def test_loss_mask_only_after_code(self):
        # 例0: [10, 11, 99(code), 20, 21, 2(eos)], 例1: [10, 99, 20, 2]
        ids = np.array([10, 11, 99, 20, 21, 2, 10, 99, 20, 2], dtype=np.uint16)
        offsets = np.array([0, 6, 10])
        code_pos = np.array([2, 1])
        b = Batcher(ids, offsets, code_pos, pad_id=0, batch_size=2, seed=0, shuffle=False)
        x, y, real = b.next()
        self.assertEqual(real, 10)
        self.assertEqual(y[0].tolist(), [-100, -100, -100, 20, 21, 2])
        self.assertEqual(y[1].tolist(), [-100, -100, 20, 2, -100, -100])
        self.assertEqual(x[1].tolist(), [10, 99, 20, 2, 0, 0])

    def test_wraps_epoch(self):
        ids = np.array([1, 99, 2], dtype=np.uint16)
        b = Batcher(ids, np.array([0, 3]), np.array([1]), 0, batch_size=3, seed=0)
        x, _, _ = b.next()
        self.assertEqual(x.shape[0], 3)
        self.assertGreaterEqual(b.epoch, 1)


if __name__ == "__main__":
    unittest.main()
