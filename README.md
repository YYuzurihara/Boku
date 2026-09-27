# Boku

日本語の指示文から `solve(xs: list[int], k: int) -> list[int]` を生成する小型言語モデル Boku-nano を、データ生成から学習・評価まで一貫して作るリポジトリ。各ディレクトリの設計の詳細はそれぞれの README を参照。

| ディレクトリ | 内容 |
|---|---|
| [semantic_ast/](semantic_ast/README.md) | 意味ASTの列挙・分割・テストケース生成、参照インタプリタ |
| [semantic_ast/expressions_ja/](semantic_ast/expressions_ja/README.md) | 意味AST → 日本語指示文 |
| [semantic_ast/expressions_code/](semantic_ast/expressions_code/README.md) | 意味AST → Pythonコード |
| [data/](data/corpus_generator.py) | 日本語とコードを結合したコーパスの作成 |
| [tokenizer/](tokenizer/README.md) | BPEトークナイザ |
| [model/](model/README.md) | モデル・学習・評価 |
| [sandbox/](sandbox/README.md) | 生成コードを実行するDockerサンドボックス |

## 環境構築

必要なもの:

- [uv](https://docs.astral.sh/uv/)（Python 3.14 は `.python-version` に従って uv が用意する）
- NVIDIA GPU + CUDA（教師モデルによる日本語表現の生成と、モデルの学習に使う）
- Docker（評価時に生成コードをサンドボックスで実行するのに使う）

```bash
uv sync                                   # .venv に依存パッケージ（vLLM・PyTorch・tokenizers・MLflow）を入れる
docker build -t boku-sandbox sandbox      # 評価用サンドボックスのイメージ
```

以下のコマンドはすべてリポジトリのルートで実行する。

## 結果だけを見る場合

データ生成と学習をやり直さずに、配布している学習記録・学習済みモデル・データで結果を確認する手順。GPU は無くてもよい（評価は CPU でも動くが遅い）。環境構築の `uv sync` は先に済ませておく。

配布ファイルは次の Google Drive フォルダにある。

https://drive.google.com/drive/folders/1WSb8G-XjItU6msLVw1YDv_k-h4S3xfjU?usp=drive_link

### 学習記録を見る（MLflow）

1. Drive から `mlruns/` フォルダと `mlflow.db` をダウンロードする（ブラウザでフォルダを右クリック →「ダウンロード」。フォルダは zip で落ちてくるので展開する）。
2. 次のように配置する。

   ```
   Boku/
     mlflow.db          ← Drive の mlflow.db（各runのパラメタと損失などのメトリクス）
     mlruns/            ← Drive の mlruns/ をそのまま置く（学習済みモデル・トークナイザ・設定ファイル）
   ```

3. リポジトリのルートで MLflow の UI を起動し、ブラウザで http://127.0.0.1:5000 を開く。

   ```bash
   uv run mlflow ui --backend-store-uri sqlite:///mlflow.db --artifacts-destination ./mlruns
   ```

   実験 `boku-nano` の各 run で、設定値（Parameters）、`train/loss`・`val/loss` などの曲線（Model metrics）、成果物（Artifacts）を確認できる。記録される項目は [model/README.md](model/README.md) を参照。

> **注意：配布用の `mlflow.db` は閲覧専用**
>
> 配布している `mlflow.db` は、学習時に記録した `model/out/mlflow.db` のコピー。どこにクローンしても成果物が見つかるように、成果物の場所を絶対パスから `mlflow-artifacts:/1/<run_id>/artifacts` に書き換えてある。この形式のパスは `--artifacts-destination ./mlruns` を付けて起動した UI からしか解決できないので、起動コマンドからこのオプションを外さないこと。
>
> また、このファイルを学習の記録先（`model/configs/*.toml` の `[mlflow] tracking_uri`）にしないこと。`model/train.py` は MLflow サーバーを介さずに SQLite へ直接記録するため、書き換え後のパスには成果物を保存できない。学習をやり直す場合は、設定どおり `model/out/mlflow.db` に新しく記録される。

各 run の学習済みモデルは `mlruns/1/<run_id>/artifacts/checkpoint/final.pt`、そのモデルで使ったトークナイザは `mlruns/1/<run_id>/artifacts/tokenizer/tokenizer.json` にある。`<run_id>` は MLflow UI の run 画面に表示される Run ID で、`mlruns/1/` 直下のディレクトリ名と同じ。

### 学習・テストデータを置いて評価する

1. Drive から5つの jsonl ファイルをダウンロードし、`data/` に置く。split（`train` / `val` / `test_*`）の意味は下の「1. 意味ASTの生成」を参照。

   ```
   Boku/
     data/
       train.jsonl                ← 学習用（評価には不要。学習やトークナイザの学習をやり直すときに使う）
       val.jsonl                  ← 検証用（同上）
       test_paraphrase.jsonl      ← 評価に使う
       test_compositional.jsonl   ← 評価に使う
       test_boundary.jsonl        ← 評価に使う
   ```

   各行は1つの意味ASTで、日本語指示文（`instruction_ja`）・コード（`codes`）・テストケース（`tests`）を持つ。

2. 評価用のサンドボックスイメージを作る（Docker が必要。環境構築で済ませていれば不要）。

   ```bash
   docker build -t boku-sandbox sandbox
   ```

3. 評価を実行する。`<run_id>` は評価したい run のもの。トークナイザは `tokenizer/out/` には無いので、`--tokenizer` で同じ run のものを指定する。

   ```bash
   uv run python model/evaluate.py \
     --ckpt mlruns/1/<run_id>/artifacts/checkpoint/final.pt \
     --tokenizer mlruns/1/<run_id>/artifacts/tokenizer/tokenizer.json
   ```

   3つのテスト用 split から各200問を解かせ、pass@1・pass@5 などを表示する。結果は `final.pt` と同じディレクトリの `eval.json` に保存される。オプションと指標の意味は下の「9. 評価」を参照。

## データ合成から学習までの実行手順

上から順に実行する（5の参照インタプリタのテストはいつ実行してもよい）。**コード生成（3）は日本語指示文の生成（4の(c)）より先に行う**こと。`ja_demo.py` は意味ASTごとのコード件数を `code_{split}.jsonl` から読み、それと同じ数の日本語文を作るため。

### 1. 意味ASTの生成

```bash
uv run python semantic_ast/demo.py
```

全14,424件の意味ASTを列挙し、重複除去・split への分割・漏洩検査・テストケース生成を行って `semantic_ast/out/ast_{split}.jsonl` に書き出す。

**split** は次の5つで、分割は意味AST単位で行う。以降の手順では、1つの意味ASTから作ったコードや日本語文はすべてその意味ASTと同じ split に入る。そのため、同じ問題の言い換えやスタイル違いが train とテストにまたがること（データ漏洩）はない。ファイル名の `{split}` はこの名前を指す。

| split | 件数 | 用途 |
|---|---|---|
| `train` | 11,234 | 学習（トークナイザの学習もこれだけを使う） |
| `val` | 1,248 | 学習中の検証損失 |
| `test_paraphrase` | 694 | 言い換えテスト：訓練で使わない日本語の言い回しだけで書いた指示文 |
| `test_compositional` | 554 | 組合せ汎化テスト：訓練では別々にしか現れない演算の組（例：`filter:even` と `order:descending`）を含む問題 |
| `test_boundary` | 694 | 境界値テスト：空リスト・要素1個・全要素が条件を満たさない、などの入力 |

各 split にどの意味ASTが入るかはシードだけで決まる。そのため、1・3・4(c)・6・9 のスクリプトは `--splits test_boundary` のように一部の split だけを対象にしても、全部まとめて実行したときと同じ中身になる。

### 2. 漏洩検査

1 の `demo.py` が split 直後に自動実行するため、独立に実行するコマンドはない。何を保証しているかは次の2つ。

- `check_no_leakage`：同じ `semantic_hash` の意味ASTが2つ以上のsplitに現れないことを確認する。
- `check_holdout_pairs`：組合せ汎化テスト用に取り置いた演算の組（例：`filter:even` と `order:descending`）が `test_compositional` 以外に漏れていないこと、かつ各演算単体は `train` に含まれていることを確認する。

検査に失敗すると `LeakageError` で止まる。成功すると 1 の実行時に標準出力へ次の2行が出る。

```
leakage check passed: no semantic AST hash appears in more than one split
holdout check passed: no held-out operation pair occurs outside test_compositional
```

### 3. コード生成

```bash
uv run python semantic_ast/expressions_code/code_demo.py --limit 0
```

各意味ASTから複数スタイルのPythonコードを生成し、参照インタプリタと突き合わせて検証してから `semantic_ast/out/code_{split}.jsonl` に保存する。`--limit 0` で全件（省略すると各split 200件だけ）。`--sandbox 5` を付けると、5件をDockerサンドボックスでも抜き取り検査する。

### 4. 日本語表現の生成と人間によるチェック

日本語は2段階で作る。教師モデル（Qwen3-4B-AWQ, vLLM）には原子操作の言い方（表現辞書）だけを問い合わせ、指示文はその辞書から決定的に組み立てる。

**(a) 表現辞書の生成（要GPU）**

```bash
uv run python semantic_ast/expressions_ja/ja_teacher.py                            # 全26キーを生成
uv run python semantic_ast/expressions_ja/ja_teacher.py --keys filter:zero --merge # 一部のキーだけ作り直して既存の辞書に上書き
uv run python semantic_ast/expressions_ja/ja_teacher.py --report-contract          # 生成済みの辞書を結合契約で検査するだけ（GPU不要）
```

**(b) 人間によるチェック**

人間がチェック・編集するのは `semantic_ast/expressions_ja/filtered.json` だけ。これが (c) で使う表現辞書になる。

1. 新しく生成した辞書から始めるときは、`candidates.json` を `filtered.json` にコピーする。
2. `filtered.json` をキーごとに確認し、不自然な表現・意味が変わった表現・結合できない表現を削除または修正する。各キーに表現が最低1件残るようにする。
3. 結合契約違反（名詞で終わる連体修飾、「から」を付けられないte形など）は次のコマンドで一覧できる。

```bash
uv run python semantic_ast/expressions_ja/ja_teacher.py --report-contract --out semantic_ast/expressions_ja/filtered.json
```

`candidates.json`（教師モデルの生の出力）と `generation_log.jsonl`（生成ログ）はチェック対象ではない。必要なら記録として参照できるが、無くても以降の手順には影響しない。

**(c) 日本語指示文の生成（3のコード生成の後）**

```bash
uv run python semantic_ast/expressions_ja/ja_demo.py
```

`filtered.json`（`--dictionary` で変更可）を使って各意味ASTの日本語指示文をコード件数分生成し、`semantic_ast/out/instructions_{split}.jsonl` に保存する。保存後に読み戻して、辞書から同じ文が再現できるかを検証する。

### 5. 参照インタプリタのテスト

```bash
uv run python -m unittest discover -s semantic_ast/tests -p "test_reference_interpreter.py" -v
```

`semantic_ast/` の単体テストをすべて実行する場合は `-p` を外す（GPU・Docker不要）。

### 6. 日本語とコードを結合したコーパスの作成

```bash
uv run python data/corpus_generator.py
```

`semantic_ast/out/` の `ast_*` / `code_*` / `instructions_*` を `spec_id` で結合し、split ごとに `data/{split}.jsonl`（`train.jsonl`・`val.jsonl`・`test_*.jsonl` の5ファイル）を作る。1行が1意味ASTで、`codes[i]` と `instruction_ja[i]` が対になる。`--splits test_boundary` のように一部のsplitだけ作ることもできる。

### 7. トークナイザの学習

```bash
uv run python tokenizer/demo.py --percent 100 --vocab-size 2048
```

`data/train.jsonl` だけから byte-level BPE トークナイザを学習し（val やテストの文面が語彙に混ざらないようにするため）、`tokenizer/out/tokenizer.json` に保存する。`--percent` は学習に使う train レコードの割合（既定10）。`--vocab-size` はモデル設定の `vocab_size` と一致させる。

### 8. モデルの学習

```bash
uv run python model/train.py
uv run python model/train.py --total-tokens 50_000_000 --run-name short-run          # 学習トークン数を上書き
uv run python model/train.py --config model/configs/my_config.toml                   # 別の設定ファイル
uv run python model/train.py --resume model/out/checkpoints/<run_id>/last.pt         # 中断した学習の再開
```

チェックポイントは `model/out/checkpoints/<run_id>/`（途中は `last.pt`、完了時に `final.pt`）に保存される。学習の記録は MLflow で確認できる。

```bash
uv run mlflow ui --backend-store-uri sqlite:///model/out/mlflow.db
```

#### パラメタの設定方法

パラメタはすべて [model/configs/boku_nano.toml](model/configs/boku_nano.toml) で設定する。変更したいときは、このファイルを直接編集するか、コピーして `--config` で渡す。コマンドラインで上書きできるのは `--total-tokens` だけ。

| セクション | 主なキー | 内容 |
|---|---|---|
| `[model]` | `vocab_size` `d_model` `n_layers` `n_heads` `n_kv_heads` `d_ff` `max_seq_len` | モデル構造。`vocab_size` はトークナイザの語彙数上限と合わせる。`n_kv_heads` を `n_heads` の約数にするとGQA |
| `[train]` | `max_lr` `warmup_ratio` `min_lr_ratio` `weight_decay` `grad_clip` | 最適化（AdamW, warmup + cosine） |
| | `micro_batch_size` `grad_accum_steps` `seq_len` | バッチサイズと系列長（`seq_len` を超える例は捨てる） |
| | `total_tokens` | 学習で見る延べトークン数 |
| | `eval_interval` `eval_batches` `checkpoint_interval` | 検証・保存の頻度 |
| | `dtype` `compile` `seed` | 精度・`torch.compile`・乱数シード |
| `[data]` | `train` `val` `tokenizer` `cache_dir` | 入力ファイルのパス。`train` で学習し、`val` で検証損失を計算する（テスト用の split は学習では使わない） |
| `[mlflow]` | `tracking_uri` `experiment` | MLflowの記録先 |

### 9. 評価

```bash
uv run python model/evaluate.py --ckpt model/out/checkpoints/<run_id>/final.pt
uv run python model/evaluate.py --ckpt model/out/checkpoints/<run_id>/final.pt --n 200 --pass-k 5 --splits test_boundary
```

3つのテスト用 split（`test_paraphrase` / `test_compositional` / `test_boundary`）の意味ASTはどれも学習で使っていない。そのそれぞれから、split ごとに `--n` 問（既定200）を取り、モデルが生成したコードをDockerサンドボックス（`boku-sandbox` イメージ）で hidden test に通して pass@1（greedy）と pass@k（`--pass-k` 本をtemperature `--temperature` でサンプリング）を計算する。結果はチェックポイントと同じディレクトリの `eval.json`（`--out` で変更可）に保存される。

split ごとに次の指標を表示し、`eval.json` の `summary` にも保存する。pass@k 以外は greedy 生成1本に対する割合。

| 指標 | 意味 |
|---|---|
| `syntax_ok` | `ast.parse` が通った割合 |
| `ast_safe` | 静的安全性チェック（import・禁止された属性アクセス・許可外の関数呼び出しなどを含まない）を通った割合 |
| `signature_valid` | `solve(xs, k)` のシグネチャを持つ割合 |
| `executable` | サンドボックス内で実行できた割合 |
| `tests_passed` | hidden test に全通過した割合（= pass@1） |
| `pass@k` | `--pass-k` 本のサンプルのうち1本でも hidden test に全通過した割合 |

問題ごとの生成コード・合否・エラーは `eval.json` の `records` に残る。
