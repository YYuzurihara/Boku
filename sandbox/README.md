# Boku-nano コード実行検証サンドボックス

`homework.md` の「対象とする問題」「データの検証と選抜」、および `task_list.md` の

- コードの検証用サンドbox環境をdockerで作成
- サンドboxでタイムアウト・メモリ上限を管理
- コードを検証（ast.parse / 安全性チェック / テストによるチェック）

を実装したもの。生成された `solve(xs: list[int], k: int) -> list[int]` を、

1. 静的に安全か確認し、
2. ネットワーク遮断・権限最小化した使い捨てDockerコンテナの中で、
3. CPU時間・メモリ・壁時計タイムアウトの上限つきで実行し、
4. 参照インタプリタの期待値と突き合わせて合否判定する。

学習データ生成（コード生成器の自己検証）と、モデル評価（生成コードのpass@1判定）の両方で同じサンドボックスを使う想定。

## ファイル構成

```
sandbox/
  ast_safety.py   静的安全性チェッカ（ast.parseの許可構文ホワイトリスト）
  runner.py       コンテナ内で実行されるテストランナー（stdin→JSON, stdout→JSON）
  Dockerfile      ロックダウンされた実行イメージの定義
  client.py       ホスト側ドライバ（docker runの安全な起動・タイムアウト管理）
  demo.py         動作確認用デモ（正解例・脱獄試行・タイムアウト・メモリ爆弾）
  tests/
    test_ast_safety.py   ast_safety.py の単体テスト（Docker不要）
```

## 多層防御アーキテクチャ

homework.md が要求する「副作用のない純粋関数だけを実行する」「外部入出力を使わせない」を、単一の仕組みではなく独立した複数レイヤーで保証する。どれか1層が抜けても他の層が止める設計。

```
┌─────────────────────────────────────────────────────────────┐
│ Layer 0  ホスト側 事前チェック (ast_safety.verify_static)     │
│          -> 危険なコードはコンテナを起動する前に弾く（安価）   │
├─────────────────────────────────────────────────────────────┤
│ Layer 1  Docker コンテナ分離 (client.py の docker run オプション)│
│          --network none          外部通信不可                 │
│          --read-only + tmpfs     ファイルシステム書き込み不可   │
│          --cap-drop ALL          Linux capability 全剥奪       │
│          --security-opt no-new-privileges                     │
│          非root ユーザ (uid 10001)                             │
│          --memory / --memory-swap  メモリ上限 (既定256MB, swap無効)│
│          --cpus                   CPU上限 (既定0.5コア)         │
│          --pids-limit             fork爆弾対策                 │
├─────────────────────────────────────────────────────────────┤
│ Layer 2  コンテナ内 再チェック + 第二のAST検査 (runner.py)      │
│          resource.setrlimit(RLIMIT_AS/CPU/NPROC/FSIZE)        │
│          exec() 用の最小 __builtins__（許可関数のみ）           │
├─────────────────────────────────────────────────────────────┤
│ Layer 3  テストごとの壁時計タイムアウト (SIGALRM, runner.py)   │
├─────────────────────────────────────────────────────────────┤
│ Layer 4  ホスト側 最終バックストップ (subprocess timeout,       │
│          client.py) -> 上記すべてが機能しなかった場合に         │
│          コンテナを強制kill                                    │
└─────────────────────────────────────────────────────────────┘
```

## 安全性チェックの設計判断: 属性アクセス

homework.md の選抜条件は「import、属性アクセス、ファイル操作などを含まない」だが、これを文字通り適用すると、homework.md 自身が要求する構造的変換の一種「内包表記と通常の`for`ループ」（後者は `result.append(x)` のような属性アクセスを要する）が実装不可能になる。

このため `ast_safety.py` では、`append/extend/insert/remove/pop/clear/sort/reverse/count/index/copy` という安全なリスト変更メソッドのみを許可し、それ以外の属性アクセス（特に `_` で始まるものすべて）を拒否する方式にした。`_` 始まりを一律禁止することで `().__class__.__bases__` のような典型的なサンドボックス脱獄チェーンを防ぎつつ、`import` 自体を禁止しているのでそもそもモジュールオブジェクトへの属性アクセス（`os.system` 等）は発生し得ない。

その他の制約（`ast_safety.ALLOWED_NODES` / `ALLOWED_CALL_NAMES` 参照）:

- `solve(xs, k)` という名前・シグネチャの、トップレベル関数1つだけを許可（複数関数からなるプログラムは対象外という homework.md の方針どおり）
- クラス定義、ネストした関数定義、デコレータ、再帰呼び出し（`solve` の自己呼び出し）を禁止
- `import`/`from...import`、`with`、`try/except`、`global`/`nonlocal`、`yield`/`await` を禁止
- 呼び出せる組み込み関数は `len/range/sorted/sum/min/max/abs/all/any/list/set/tuple/dict/int/float/bool/round/divmod/pow/enumerate/zip/map/filter/reversed` のみ（`open/eval/exec/compile/__import__/input/globals/locals/vars/dir/getattr/setattr` 等は許可リストに無いため呼べない）

## 使い方

### 1. イメージのビルド

```bash
docker build -t boku-sandbox sandbox
```

もしくは Python から:

```python
from client import build_image
build_image("sandbox")
```

### 2. 1件実行して判定を取得

```python
from client import run_in_sandbox, SandboxConfig

verdict = run_in_sandbox(
    code="def solve(xs, k):\n    return sorted(x for x in xs if x >= k)\n",
    tests=[{"xs": [1, 5, 2, 8], "k": 3, "expected": [5, 8]}],
    config=SandboxConfig(timeout_sec=10, per_test_timeout_sec=2, memory_mb=256),
)
print(verdict["tests_passed"], verdict["syntax_ok"], verdict["ast_safe"])
```

`verdict` は `homework.md` のデータレコードにある `verification: {syntax_ok, ast_safe, tests_passed}` にそのまま対応し、加えて `signature_valid`（シグネチャ一致）、`executable`（load/exec自体が成功したか）、`pure`（入力リストを破壊的変更していないか）、テストごとの `actual`/`error`/`elapsed_sec`/`mutated_input`、`max_rss_mb`（最大常駐メモリ）を含む。

### 3. デモを流す

```bash
python sandbox/demo.py
```

正解例・不正解例・`import os` 脱獄試行・`__class__` 脱獄試行・無限ループ（タイムアウト）・メモリ爆弾・非純粋関数（入力破壊）の7ケースを実行し、それぞれの判定結果を表示する。

### 4. 単体テスト（Docker不要）

```bash
python -m unittest discover -s sandbox/tests -v
```

## 動作確認済み事項

このセッションでビルドしたイメージに対し、Docker Desktop 上で実際に以下を確認済み:

- 正解コード（内包表記版・for+append版）が `tests_passed: true` になること
- 不正解コードが `tests_passed: false` になり、実際の出力 (`actual`) が判定結果に残ること
- `import os` を含むコードが実行前に `ast_safe: false` として拒否されること（コンテナ内で1行も評価されない）
- `().__class__` を使った脱獄コードが `disallowed attribute access` として拒否されること
- 無限ループが `per_test_timeout_sec`（既定2秒、デモでは1.5秒）でSIGALRM経由の `timeout` エラーとして安全に打ち切られ、コンテナが正常終了すること（ハングしない）
- `[0] * (10**12)` のようなメモリ確保が `RLIMIT_AS` により即座に `MemoryError` → `memory_limit_exceeded` として捕捉されること
- `xs.sort(); return xs` のような入力破壊的コードが `pure: false` / `mutated_input: true` として検出されること
- `ast_safety.py` の単体テスト22件が全てパスすること

## 既知の制約・今後の拡張

- Windows ホストで Docker Desktop（Linux コンテナモード）を使う前提。`resource` モジュールはコンテナ内（Linux）でのみ動作する。
- `docker run` の起動オーバーヘッドが1回あたり概ね数百ms〜1秒程度発生する。大量データ生成時（30万件規模のテスト実行など）はコンテナをプールする・複数テストケースを1回の `docker run` にまとめる、といった高速化が今後必要になる可能性がある（現状の `runner.py` はコード1件につき複数テストケースをまとめて実行できる設計なので、後者は追加実装なしで活用できる）。
- `ast_safety.py` はホワイトリスト方式の静的検査であり完全性を主張するものではない。真の隔離境界は Docker コンテナ + OS資源制限であり、AST検査はコンテナ起動前の高速なフィルタ、および Layer 2 の二重チェックという位置づけ。
