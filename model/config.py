"""Boku-nano の設定 (TOMLから読む)。"""

from __future__ import annotations

import tomllib
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class ModelConfig:
    vocab_size: int = 2048
    d_model: int = 384
    n_layers: int = 8
    n_heads: int = 6
    n_kv_heads: int = 6
    d_ff: int = 1024
    max_seq_len: int = 512
    rope_theta: float = 1000.0
    norm_eps: float = 1e-5
    tie_embeddings: bool = True

    def __post_init__(self) -> None:
        if self.d_model % self.n_heads:
            raise ValueError("d_model は n_heads で割り切れる必要があります")
        if self.n_heads % self.n_kv_heads:
            raise ValueError("n_heads は n_kv_heads で割り切れる必要があります")
        if (self.d_model // self.n_heads) % 2:
            raise ValueError("head_dim は偶数である必要があります(RoPE)")


@dataclass
class TrainConfig:
    seed: int = 0
    max_lr: float = 3e-4
    min_lr_ratio: float = 0.1
    warmup_ratio: float = 0.03
    weight_decay: float = 0.1
    grad_clip: float = 1.0
    betas: tuple[float, float] = (0.9, 0.95)
    seq_len: int = 256
    micro_batch_size: int = 64
    grad_accum_steps: int = 2
    total_tokens: int = 300_000_000
    eval_interval: int = 200
    eval_batches: int = 50
    checkpoint_interval: int = 500
    dtype: str = "bfloat16"
    compile: bool = False


@dataclass
class DataConfig:
    train: str = "data/train.jsonl"
    val: str = "data/val.jsonl"
    tokenizer: str = "tokenizer/out/tokenizer.json"
    cache_dir: str = "model/out/cache"


@dataclass
class MlflowConfig:
    tracking_uri: str = "sqlite:///model/out/mlflow.db"
    experiment: str = "boku-nano"


@dataclass
class Config:
    model: ModelConfig = field(default_factory=ModelConfig)
    train: TrainConfig = field(default_factory=TrainConfig)
    data: DataConfig = field(default_factory=DataConfig)
    mlflow: MlflowConfig = field(default_factory=MlflowConfig)

    def to_dict(self) -> dict:
        return asdict(self)


def load_config(path: Path | str) -> Config:
    with open(path, "rb") as f:
        raw = tomllib.load(f)
    train = dict(raw.get("train", {}))
    if "betas" in train:
        train["betas"] = tuple(train["betas"])
    return Config(
        model=ModelConfig(**raw.get("model", {})),
        train=TrainConfig(**train),
        data=DataConfig(**raw.get("data", {})),
        mlflow=MlflowConfig(**raw.get("mlflow", {})),
    )
