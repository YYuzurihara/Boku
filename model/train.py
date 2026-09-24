"""Boku-nano の事前学習 (MLflowでパラメータ・メトリクス・checkpointを管理)。

    python model/train.py --config model/configs/boku_nano.toml
    python model/train.py --config model/configs/boku_nano.toml --total-tokens 5_000_000 --run-name smoke
    mlflow ui --backend-store-uri sqlite:///model/out/mlflow.db

重みは常にランダム初期化。`--resume` は同じ実験の checkpoint からの再開用。
"""

from __future__ import annotations

import argparse
import json
import math
import random
import subprocess
import time
from pathlib import Path

import mlflow
import numpy as np
import torch
from tokenizers import Tokenizer

from config import Config, load_config
from data import Batcher, load_tokenized, special_ids
from model import BokuModel

ROOT = Path(__file__).resolve().parent.parent


def lr_at(step: int, total: int, cfg) -> float:
    warm = max(1, int(total * cfg.warmup_ratio))
    if step < warm:
        return cfg.max_lr * (step + 1) / warm
    prog = (step - warm) / max(1, total - warm)
    min_lr = cfg.max_lr * cfg.min_lr_ratio
    return min_lr + 0.5 * (cfg.max_lr - min_lr) * (1 + math.cos(math.pi * prog))


def make_optimizer(model: torch.nn.Module, cfg) -> torch.optim.AdamW:
    decay = [p for p in model.parameters() if p.requires_grad and p.ndim >= 2]
    no_decay = [p for p in model.parameters() if p.requires_grad and p.ndim < 2]
    return torch.optim.AdamW(
        [{"params": decay, "weight_decay": cfg.weight_decay}, {"params": no_decay, "weight_decay": 0.0}],
        lr=cfg.max_lr,
        betas=cfg.betas,
        fused=torch.cuda.is_available(),
    )


@torch.no_grad()
def evaluate(model, batcher: Batcher, n_batches: int, device, dtype) -> float:
    model.eval()
    tot, cnt = 0.0, 0
    for _ in range(n_batches):
        x, y, _ = batcher.next()
        x, y = x.to(device), y.to(device)
        with torch.autocast(device.type, dtype=dtype, enabled=device.type == "cuda"):
            _, loss = model(x, y)
        n = int((y[:, 1:] != -100).sum())
        tot += loss.item() * n
        cnt += n
    model.train()
    return tot / max(cnt, 1)


def save_checkpoint(path: Path, model, opt, step: int, tokens: int, cfg: Config) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(
        {"model": model.state_dict(), "opt": opt.state_dict(), "step": step, "tokens": tokens, "config": cfg.to_dict()},
        path,
    )


def git_rev() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unknown"


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--config", type=Path, default=ROOT / "model/configs/boku_nano.toml")
    ap.add_argument("--run-name", default=None)
    ap.add_argument("--total-tokens", type=lambda s: int(s.replace("_", "")), default=None)
    ap.add_argument("--resume", type=Path, default=None, help="checkpoint(.pt) から再開")
    ap.add_argument("--out-dir", type=Path, default=ROOT / "model/out/checkpoints")
    args = ap.parse_args()

    cfg = load_config(args.config)
    if args.total_tokens is not None:
        cfg.train.total_tokens = args.total_tokens
    t = cfg.train

    torch.manual_seed(t.seed)
    np.random.seed(t.seed)
    random.seed(t.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    dtype = getattr(torch, t.dtype)
    torch.backends.cuda.matmul.allow_tf32 = True

    tok_path = ROOT / cfg.data.tokenizer
    tok = Tokenizer.from_file(str(tok_path))
    if tok.get_vocab_size() > cfg.model.vocab_size:
        raise SystemExit(
            f"トークナイザ語彙({tok.get_vocab_size()})が model.vocab_size({cfg.model.vocab_size})を超えています"
        )
    pad_id = special_ids(tok)["<|pad|>"]
    cache_dir = ROOT / cfg.data.cache_dir
    tr = load_tokenized(ROOT / cfg.data.train, tok_path, cache_dir, t.seq_len)
    va = load_tokenized(ROOT / cfg.data.val, tok_path, cache_dir, t.seq_len)
    train_b = Batcher(*tr, pad_id, t.micro_batch_size, t.seed)
    val_b = Batcher(*va, pad_id, t.micro_batch_size, t.seed, shuffle=False)

    model = BokuModel(cfg.model).to(device)
    n_params = model.num_parameters()
    opt = make_optimizer(model, t)
    step, tokens = 0, 0
    if args.resume:
        ck = torch.load(args.resume, map_location=device)
        model.load_state_dict(ck["model"])
        opt.load_state_dict(ck["opt"])
        step, tokens = ck["step"], ck["tokens"]
    fwd = torch.compile(model) if t.compile else model

    # 1 step あたりの平均トークン数から総step数を決める(パディングを除く実トークンで数える)
    avg_len = len(tr[0]) / len(tr[2])
    tok_per_step = int(avg_len * t.micro_batch_size * t.grad_accum_steps)
    total_steps = max(1, t.total_tokens // tok_per_step)

    uri = cfg.mlflow.tracking_uri
    if uri.startswith("sqlite:///") and not uri.startswith("sqlite:////"):
        db = ROOT / uri.removeprefix("sqlite:///")  # 相対パスはリポジトリルート基準
        db.parent.mkdir(parents=True, exist_ok=True)
        uri = f"sqlite:///{db}"
    mlflow.set_tracking_uri(uri)
    mlflow.set_experiment(cfg.mlflow.experiment)
    with mlflow.start_run(run_name=args.run_name) as run:
        flat = {f"{sec}.{k}": v for sec, d in cfg.to_dict().items() if sec != "mlflow" for k, v in d.items()}
        mlflow.log_params(flat)
        mlflow.log_params(
            {
                "n_params": n_params,
                "train_examples": len(tr[2]),
                "train_unique_tokens": int(len(tr[0])),
                "avg_tokens_per_example": round(avg_len, 2),
                "tokens_per_step": tok_per_step,
                "total_steps": total_steps,
                "torch": torch.__version__,
                "device": torch.cuda.get_device_name(0) if device.type == "cuda" else "cpu",
                "git_rev": git_rev(),
            }
        )
        mlflow.log_artifact(str(args.config), "config")
        mlflow.log_artifact(str(tok_path), "tokenizer")
        print(f"params={n_params:,} steps={total_steps} tokens/step≈{tok_per_step:,} device={device}")

        ckpt_dir = args.out_dir / run.info.run_id
        model.train()
        t0, seen_window = time.time(), 0
        while step < total_steps:
            lr = lr_at(step, total_steps, t)
            for g in opt.param_groups:
                g["lr"] = lr
            loss_sum, n_micro = 0.0, t.grad_accum_steps
            for _ in range(n_micro):
                x, y, real = train_b.next()
                x, y = x.to(device, non_blocking=True), y.to(device, non_blocking=True)
                with torch.autocast(device.type, dtype=dtype, enabled=device.type == "cuda"):
                    _, loss = fwd(x, y)
                (loss / n_micro).backward()
                loss_sum += loss.item() / n_micro
                tokens += real
                seen_window += real
            gnorm = torch.nn.utils.clip_grad_norm_(model.parameters(), t.grad_clip).item()
            opt.step()
            opt.zero_grad(set_to_none=True)
            step += 1

            if step % 20 == 0 or step == 1:
                if device.type == "cuda":
                    torch.cuda.synchronize()
                dt = time.time() - t0
                mlflow.log_metrics(
                    {
                        "train/loss": loss_sum,
                        "train/lr": lr,
                        "train/grad_norm": gnorm,
                        "train/tokens_seen": tokens,
                        "perf/tokens_per_s": seen_window / dt,
                        "perf/max_gpu_mem_mb": torch.cuda.max_memory_allocated() / 2**20 if device.type == "cuda" else 0,
                    },
                    step=step,
                )
                print(f"step {step}/{total_steps} loss {loss_sum:.4f} lr {lr:.2e} tok/s {seen_window / dt:,.0f}")
                t0, seen_window = time.time(), 0
            if step % t.eval_interval == 0 or step == total_steps:
                val_loss = evaluate(model, val_b, t.eval_batches, device, dtype)
                mlflow.log_metrics({"val/loss": val_loss, "epoch": train_b.epoch}, step=step)
                print(f"  val loss {val_loss:.4f}")
            if step % t.checkpoint_interval == 0:
                save_checkpoint(ckpt_dir / "last.pt", model, opt, step, tokens, cfg)

        save_checkpoint(ckpt_dir / "final.pt", model, opt, step, tokens, cfg)
        mlflow.log_artifact(str(ckpt_dir / "final.pt"), "checkpoint")
        mlflow.log_metrics({"final/tokens_seen": tokens, "final/epochs": train_b.epoch + train_b._i / train_b.n})
        print(f"done: {ckpt_dir / 'final.pt'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
