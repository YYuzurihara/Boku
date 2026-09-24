# Boku-nano モデル・学習 (`model/`)

`homework.md`のモデル仕様表の必修モデル Boku-nano(約1,600万パラメータ)。

| 項目 | 値 |
|---|---|
| d_model / 層 / head / d_ff | 384 / 8 / 6 (MHA) / 1024 (SwiGLU) |
| 語彙 / 文脈長 | 2,048 / 512 |
| 位置 / 正規化 / 埋め込み | RoPE / RMSNorm / weight tying |
| パラメータ数 | 15,735,168 |

`homework.md`本文の「推奨」(約70M, d=768)は仕様表と食い違うため、表の値を採用した。変更は`configs/boku_nano.toml`だけでよい(`n_kv_heads`でGQAも可)。

## 構成
- `config.py` / `configs/boku_nano.toml` 設定(model/train/data/mlflow)
- `model.py` Decoder-only Transformer(PyTorch素のモジュール。常にランダム初期化)
- `data.py` `data/{train,val}.jsonl`のトークナイズ(`model/out/cache`にキャッシュ)。`<|code|>`まではラベル`-100`
- `train.py` 学習ループ。AdamW, BF16, warmup 3% + cosine, grad clip 1.0, 勾配累積

## 実行
```bash
python tokenizer/demo.py --vocab-size 2048 --percent 100   # 先にトークナイザ(語彙2048)
python model/train.py                                      # total_tokensは設定ファイル/--total-tokens
mlflow ui --backend-store-uri sqlite:///model/out/mlflow.db
python -m unittest discover -s model/tests -v
```

## MLflowに記録するもの
- params: 全設定、パラメータ数、訓練例数、固有トークン数、tokens/step、git rev、GPU名
- metrics: `train/loss` `train/lr` `train/grad_norm` `train/tokens_seen`、`val/loss`(+`epoch`)、`perf/tokens_per_s` `perf/max_gpu_mem_mb`
- artifacts: 設定TOML、tokenizer.json、`final.pt`(途中は`model/out/checkpoints/<run_id>/last.pt`、`--resume`で再開)

`tokens_seen`は延べトークン数(パディング除く)、`train_unique_tokens`は固有トークン数で、報告時に分けて使える。

## 未実装
生成評価(pass@k、hidden test)は「学習・評価」タスクで、`BokuModel.generate`(greedy)を使って実装する。
