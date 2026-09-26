"""学習済みBoku-nanoの生成評価 (greedy, サンドボックス実行)。

    python model/evaluate.py --ckpt model/out/checkpoints/<run_id>/final.pt --n 200
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import torch
from tokenizers import Tokenizer

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "model"))
sys.path.insert(0, str(ROOT))

from config import ModelConfig  # noqa: E402
from data import CODE, EOS, special_ids  # noqa: E402
from model import BokuModel  # noqa: E402
from sandbox.client import SandboxConfig, run_in_sandbox  # noqa: E402

SPLITS = ["test", "test_paraphrase", "test_boundary", "test_compositional"]


def generate(model, tok, ids, instruction, device, max_new=192):
    text = f"<|task|>\n{instruction}\n<|code|>\n"
    x = torch.tensor([tok.encode(text).ids], device=device)
    with torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
        out = model.generate(x, max_new, ids[EOS])
    new = out[0, x.size(1):].tolist()
    if ids[EOS] in new:
        new = new[: new.index(ids[EOS])]
    return tok.decode(new)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--tokenizer", default=str(ROOT / "tokenizer/out/tokenizer.json"))
    ap.add_argument("--n", type=int, default=200, help="splitごとの問題数")
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    ck = torch.load(args.ckpt, map_location="cpu", weights_only=False)
    model = BokuModel(ModelConfig(**ck["config"]["model"])).to(device)
    model.load_state_dict(ck["model"])
    model.eval()
    tok = Tokenizer.from_file(args.tokenizer)
    ids = special_ids(tok)
    print(f"ckpt step={ck['step']} tokens={ck['tokens']}")

    rng = random.Random(0)
    records = []
    summary = {}
    for split in SPLITS:
        rows = [json.loads(l) for l in open(ROOT / "data" / f"{split}.jsonl")]
        rows = rng.sample(rows, min(args.n, len(rows)))
        jobs = []
        with torch.no_grad():
            for r in rows:
                inst = r["instruction_ja"][0]
                jobs.append((r, inst, generate(model, tok, ids, inst, device)))

        def judge(job):
            r, inst, code = job
            return run_in_sandbox(code, r["tests"], SandboxConfig())

        with ThreadPoolExecutor(args.workers) as ex:
            results = list(ex.map(judge, jobs))
        c = Counter()
        for (r, inst, code), res in zip(jobs, results):
            for k in ("syntax_ok", "ast_safe", "signature_valid", "executable", "tests_passed"):
                c[k] += bool(res.get(k))
            records.append({"split": split, "spec_id": r["spec_id"], "instruction": inst, "code": code,
                            "passed": bool(res.get("tests_passed")), "error": res.get("error")})
        n = len(jobs)
        summary[split] = {k: c[k] / n for k in c} | {"n": n}
        print(split, {k: (f"{v:.3f}" if isinstance(v, float) else v) for k, v in summary[split].items()})

    out = Path(args.out or Path(args.ckpt).with_name("eval.json"))
    out.write_text(json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=1))
    print("saved", out)


if __name__ == "__main__":
    main()
