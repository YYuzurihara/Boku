"""学習済みBoku-nanoの生成評価 (サンドボックス実行)。

pass@1はhomework.md指定どおりtemperature 0 (greedy) の1発生成。pass@5は
`--pass-k`本の独立サンプル (`--temperature`, 既定0.8) のうち1本でも
hidden testに全通過すれば成功とする -- greedy 1本だけでは5本とも同じ出力に
なり判定の意味がないため、pass@5専用にサンプリングする。

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

SPLITS = ["test_paraphrase", "test_boundary", "test_compositional"]


def generate(model, tok, ids, instruction, device, max_new=192, temperature=0.0):
    text = f"<|task|>\n{instruction}\n<|code|>\n"
    x = torch.tensor([tok.encode(text).ids], device=device)
    with torch.autocast(device.type, dtype=torch.bfloat16, enabled=device.type == "cuda"):
        out = model.generate(x, max_new, ids[EOS], temperature=temperature)
    new = out[0, x.size(1):].tolist()
    if ids[EOS] in new:
        new = new[: new.index(ids[EOS])]
    return tok.decode(new)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--ckpt", required=True)
    ap.add_argument("--tokenizer", default=str(ROOT / "tokenizer/out/tokenizer.json"))
    ap.add_argument("--n", type=int, default=200, help="splitごとの問題数")
    ap.add_argument("--pass-k", type=int, default=5, help="pass@k のk (既定5)")
    ap.add_argument("--temperature", type=float, default=0.8,
                     help="pass@k用サンプリングのtemperature (pass@1は常にgreedy=0)。"
                          "homework.mdはpass@kのtemperatureを指定していないため既定0.8")
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--workers", type=int, default=8)
    ap.add_argument("--out", default=None)
    ap.add_argument("--splits", nargs="+", choices=SPLITS, default=SPLITS, help="評価するテスト集合 (default: 全部)")
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
    torch.manual_seed(args.seed)
    records = []
    summary = {}
    for split in args.splits:
        rows = [json.loads(l) for l in open(ROOT / "data" / f"{split}.jsonl")]
        rows = rng.sample(rows, min(args.n, len(rows)))
        jobs = []
        with torch.no_grad():
            for r in rows:
                inst = r["instruction_ja"][0]
                greedy_code = generate(model, tok, ids, inst, device)
                sampled_codes = [
                    generate(model, tok, ids, inst, device, temperature=args.temperature)
                    for _ in range(args.pass_k)
                ]
                jobs.append((r, inst, greedy_code, sampled_codes))

        def judge(job):
            r, inst, greedy_code, sampled_codes = job
            greedy_res = run_in_sandbox(greedy_code, r["tests"], SandboxConfig())
            sampled_res = [run_in_sandbox(c, r["tests"], SandboxConfig()) for c in sampled_codes]
            return greedy_res, sampled_res

        with ThreadPoolExecutor(args.workers) as ex:
            results = list(ex.map(judge, jobs))
        c = Counter()
        pass_k_hits = 0
        for (r, inst, greedy_code, sampled_codes), (greedy_res, sampled_res) in zip(jobs, results):
            for k in ("syntax_ok", "ast_safe", "signature_valid", "executable", "tests_passed"):
                c[k] += bool(greedy_res.get(k))
            passed_any = any(bool(res.get("tests_passed")) for res in sampled_res)
            pass_k_hits += passed_any
            records.append({
                "split": split, "spec_id": r["spec_id"], "instruction": inst,
                "code": greedy_code, "passed": bool(greedy_res.get("tests_passed")), "error": greedy_res.get("error"),
                "pass_at_k": {
                    "k": args.pass_k,
                    "passed_any": passed_any,
                    "samples": [
                        {"code": code, "passed": bool(res.get("tests_passed")), "error": res.get("error")}
                        for code, res in zip(sampled_codes, sampled_res)
                    ],
                },
            })
        n = len(jobs)
        summary[split] = {k: c[k] / n for k in c} | {f"pass@{args.pass_k}": pass_k_hits / n, "n": n}
        print(split, {k: (f"{v:.3f}" if isinstance(v, float) else v) for k, v in summary[split].items()})

    out = Path(args.out or Path(args.ckpt).with_name("eval.json"))
    out.write_text(json.dumps({"summary": summary, "records": records}, ensure_ascii=False, indent=1))
    print("saved", out)


if __name__ == "__main__":
    main()
