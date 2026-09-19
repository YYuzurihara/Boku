# THIRD_PARTY

`task_list.md` の「意味ASTに基づいてQwen3系モデルで日本語表現を生成」、および `homework.md` の「教師モデル」節にある

> 教師生成時には以下を固定・記録する。
> モデル名 / モデルのrevisionまたはコミットID / 量子化方式 / 推論ライブラリのバージョン / system prompt / sampling設定 / seed / 生成日時 / プロンプトのハッシュ値

を受けて、教師モデル（日本語表現の生成に使用する大規模言語モデル）に関する第三者ライセンス・実行条件を記録するファイル。

プロンプト本文・system prompt・プロンプトのハッシュ値は別途整理して追記する（本ファイルでは扱わない）。

## ライセンス

### Qwen/Qwen3-4B-AWQ

- 配布元: [Qwen/Qwen3-4B-AWQ (Hugging Face)](https://huggingface.co/Qwen/Qwen3-4B-AWQ)
- ライセンス: Apache License 2.0
- ライセンス原文: [LICENSE](https://huggingface.co/Qwen/Qwen3-4B-AWQ/blob/main/LICENSE)

## モデル・実行環境の記録

`homework.md` が要求する固定・記録項目のうち、プロンプト関連（system prompt・プロンプトのハッシュ値）を除いたもの。実際に生成を実行するスクリプト側で、実行時点の値を以下の表に追記・更新すること。

| 項目                       | 値                                                                 |
| -------------------------- | ------------------------------------------------------------------ |
| モデル名                   | `Qwen/Qwen3-4B-AWQ`                                                 |
| モデルのrevision/コミットID | TBD（実行時にHugging Face上のrevisionハッシュを記録する）           |
| 量子化方式                 | AWQ（4-bit）                                                        |
| 推論ライブラリ             | [vLLM](https://github.com/vllm-project/vllm)                       |
| 推論ライブラリのバージョン | `0.29.0`（`pyproject.toml` / `uv.lock` に固定、本リポジトリの依存） |
| sampling設定               | TBD（実行時に記録: temperature / top_p / top_k など）              |
| seed                       | TBD（実行時に固定・記録）                                          |
| 生成日時                   | TBD（実行のたびに記録）                                             |
| thinkingモード             | 非thinkingモードを使用し、最終的な指示文・解説文のみを保存する（`homework.md` 203行目） |

### vLLM のライセンス

- 配布元: [vllm-project/vllm](https://github.com/vllm-project/vllm)
- ライセンス: Apache License 2.0
