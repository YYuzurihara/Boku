# 生成コードのサンプル

`code_demo.py` が生成したコードの抜粋（自動生成。手で編集しない）。
意味ASTの構成パターンと原子操作を網羅するように選んだ意味ASTについて、
適用できる`code_style`すべてでレンダリングしたもの。全件は
`semantic_ast/out/code_{split}.jsonl`（生成物、gitignore済み）にある。

各コードは参照インタプリタと全テストケースで一致することを確認済み
（`verification`は`samples.jsonl`側に入っている）。

## `{"ops": [["filter", "even"], ["map", "mul_const", 2], ["order", "ascending"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted([x * 2 for x in xs if x % 2 == 0])
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→変換→並べ替えの順に処理する
    return sorted([x * 2 for x in xs if x % 2 == 0])
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return sorted([x * 2 for x in xs if x % 2 == 0])
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 抽出→変換→並べ替えの順に処理する
    return sorted([x * 2 for x in xs if x % 2 == 0])
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted([v * 2 for v in xs if v % 2 == 0])
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→変換→並べ替えの順に処理する
    return sorted([v * 2 for v in xs if v % 2 == 0])
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted([v * 2 for v in xs if v % 2 == 0])
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出→変換→並べ替えの順に処理する
    return sorted([v * 2 for v in xs if v % 2 == 0])
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted([value * 2 for value in xs if value % 2 == 0])
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→変換→並べ替えの順に処理する
    return sorted([value * 2 for value in xs if value % 2 == 0])
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return sorted([value * 2 for value in xs if value % 2 == 0])
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 抽出→変換→並べ替えの順に処理する
    return sorted([value * 2 for value in xs if value % 2 == 0])
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x * 2 for x in xs if x % 2 == 0]
    result = sorted(result)
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    result: list[int] = [x * 2 for x in xs if x % 2 == 0]
    # 並べ替える
    result = sorted(result)
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x * 2 for x in xs if x % 2 == 0]
    result = sorted(result)
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    result = [x * 2 for x in xs if x % 2 == 0]
    # 並べ替える
    result = sorted(result)
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v * 2 for v in xs if v % 2 == 0]
    out = sorted(out)
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    out: list[int] = [v * 2 for v in xs if v % 2 == 0]
    # 並べ替える
    out = sorted(out)
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v * 2 for v in xs if v % 2 == 0]
    out = sorted(out)
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    out = [v * 2 for v in xs if v % 2 == 0]
    # 並べ替える
    out = sorted(out)
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value * 2 for value in xs if value % 2 == 0]
    values = sorted(values)
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    values: list[int] = [value * 2 for value in xs if value % 2 == 0]
    # 並べ替える
    values = sorted(values)
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value * 2 for value in xs if value % 2 == 0]
    values = sorted(values)
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    values = [value * 2 for value in xs if value % 2 == 0]
    # 並べ替える
    values = sorted(values)
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x % 2 == 0]
    mapped: list[int] = [x * 2 for x in kept]
    ordered: list[int] = sorted(mapped)
    return ordered
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x % 2 == 0]
    # 各要素を変換する
    mapped: list[int] = [x * 2 for x in kept]
    # 並べ替える
    ordered: list[int] = sorted(mapped)
    return ordered
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    kept = [x for x in xs if x % 2 == 0]
    mapped = [x * 2 for x in kept]
    ordered = sorted(mapped)
    return ordered
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = [x for x in xs if x % 2 == 0]
    # 各要素を変換する
    mapped = [x * 2 for x in kept]
    # 並べ替える
    ordered = sorted(mapped)
    return ordered
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = [v for v in xs if v % 2 == 0]
    conv: list[int] = [v * 2 for v in sel]
    srt: list[int] = sorted(conv)
    return srt
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in xs if v % 2 == 0]
    # 各要素を変換する
    conv: list[int] = [v * 2 for v in sel]
    # 並べ替える
    srt: list[int] = sorted(conv)
    return srt
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    sel = [v for v in xs if v % 2 == 0]
    conv = [v * 2 for v in sel]
    srt = sorted(conv)
    return srt
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = [v for v in xs if v % 2 == 0]
    # 各要素を変換する
    conv = [v * 2 for v in sel]
    # 並べ替える
    srt = sorted(conv)
    return srt
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = [value for value in xs if value % 2 == 0]
    transformed: list[int] = [value * 2 for value in filtered]
    reordered: list[int] = sorted(transformed)
    return reordered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in xs if value % 2 == 0]
    # 各要素を変換する
    transformed: list[int] = [value * 2 for value in filtered]
    # 並べ替える
    reordered: list[int] = sorted(transformed)
    return reordered
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value % 2 == 0]
    transformed = [value * 2 for value in filtered]
    reordered = sorted(transformed)
    return reordered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value % 2 == 0]
    # 各要素を変換する
    transformed = [value * 2 for value in filtered]
    # 並べ替える
    reordered = sorted(transformed)
    return reordered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x % 2 == 0:
            result.append(x * 2)
    result.sort()
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    result: list[int] = []
    for x in xs:
        if x % 2 == 0:
            result.append(x * 2)
    # 並べ替える
    result.sort()
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        if x % 2 == 0:
            result.append(x * 2)
    result.sort()
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    result = []
    for x in xs:
        if x % 2 == 0:
            result.append(x * 2)
    # 並べ替える
    result.sort()
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        if v % 2 == 0:
            out.append(v * 2)
    out.sort()
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    out: list[int] = []
    for v in xs:
        if v % 2 == 0:
            out.append(v * 2)
    # 並べ替える
    out.sort()
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v % 2 == 0:
            out.append(v * 2)
    out.sort()
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    out = []
    for v in xs:
        if v % 2 == 0:
            out.append(v * 2)
    # 並べ替える
    out.sort()
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        if value % 2 == 0:
            values.append(value * 2)
    values.sort()
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    values: list[int] = []
    for value in xs:
        if value % 2 == 0:
            values.append(value * 2)
    # 並べ替える
    values.sort()
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        if value % 2 == 0:
            values.append(value * 2)
    values.sort()
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    values = []
    for value in xs:
        if value % 2 == 0:
            values.append(value * 2)
    # 並べ替える
    values.sort()
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x * 2)
    ordered: list[int] = sorted(kept)
    return ordered
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    kept: list[int] = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x * 2)
    # 並べ替える
    ordered: list[int] = sorted(kept)
    return ordered
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    kept = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x * 2)
    ordered = sorted(kept)
    return ordered
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    kept = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x * 2)
    # 並べ替える
    ordered = sorted(kept)
    return ordered
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v * 2)
    srt: list[int] = sorted(sel)
    return srt
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    sel: list[int] = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v * 2)
    # 並べ替える
    srt: list[int] = sorted(sel)
    return srt
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v * 2)
    srt = sorted(sel)
    return srt
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    sel = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v * 2)
    # 並べ替える
    srt = sorted(sel)
    return srt
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value * 2)
    reordered: list[int] = sorted(filtered)
    return reordered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value * 2)
    # 並べ替える
    reordered: list[int] = sorted(filtered)
    return reordered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    filtered = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value * 2)
    reordered = sorted(filtered)
    return reordered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    filtered = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value * 2)
    # 並べ替える
    reordered = sorted(filtered)
    return reordered
```

## `{"ops": [["filter", "even"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in xs if x % 2 == 0]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [x for x in xs if x % 2 == 0]
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return [x for x in xs if x % 2 == 0]
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [x for x in xs if x % 2 == 0]
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [v for v in xs if v % 2 == 0]
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [v for v in xs if v % 2 == 0]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v for v in xs if v % 2 == 0]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [v for v in xs if v % 2 == 0]
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [value for value in xs if value % 2 == 0]
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [value for value in xs if value % 2 == 0]
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return [value for value in xs if value % 2 == 0]
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [value for value in xs if value % 2 == 0]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x for x in xs if x % 2 == 0]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = [x for x in xs if x % 2 == 0]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x for x in xs if x % 2 == 0]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = [x for x in xs if x % 2 == 0]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v for v in xs if v % 2 == 0]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = [v for v in xs if v % 2 == 0]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v for v in xs if v % 2 == 0]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = [v for v in xs if v % 2 == 0]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value for value in xs if value % 2 == 0]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = [value for value in xs if value % 2 == 0]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value for value in xs if value % 2 == 0]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = [value for value in xs if value % 2 == 0]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x % 2 == 0]
    return kept
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x % 2 == 0]
    return kept
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    kept = [x for x in xs if x % 2 == 0]
    return kept
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = [x for x in xs if x % 2 == 0]
    return kept
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = [v for v in xs if v % 2 == 0]
    return sel
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in xs if v % 2 == 0]
    return sel
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    sel = [v for v in xs if v % 2 == 0]
    return sel
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = [v for v in xs if v % 2 == 0]
    return sel
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = [value for value in xs if value % 2 == 0]
    return filtered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in xs if value % 2 == 0]
    return filtered
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value % 2 == 0]
    return filtered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value % 2 == 0]
    return filtered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x % 2 == 0:
            result.append(x)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = []
    for x in xs:
        if x % 2 == 0:
            result.append(x)
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        if x % 2 == 0:
            result.append(x)
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = []
    for x in xs:
        if x % 2 == 0:
            result.append(x)
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        if v % 2 == 0:
            out.append(v)
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = []
    for v in xs:
        if v % 2 == 0:
            out.append(v)
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v % 2 == 0:
            out.append(v)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = []
    for v in xs:
        if v % 2 == 0:
            out.append(v)
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        if value % 2 == 0:
            values.append(value)
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = []
    for value in xs:
        if value % 2 == 0:
            values.append(value)
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        if value % 2 == 0:
            values.append(value)
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = []
    for value in xs:
        if value % 2 == 0:
            values.append(value)
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    kept = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    filtered = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value)
    return filtered
```

## `{"ops": [["order", "ascending"], ["map", "mul_const", 2], ["filter", "even"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in [x * 2 for x in sorted(xs)] if x % 2 == 0]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替え→変換→抽出の順に処理する
    return [x for x in [x * 2 for x in sorted(xs)] if x % 2 == 0]
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return [x for x in [x * 2 for x in sorted(xs)] if x % 2 == 0]
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 並べ替え→変換→抽出の順に処理する
    return [x for x in [x * 2 for x in sorted(xs)] if x % 2 == 0]
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [v for v in [v * 2 for v in sorted(xs)] if v % 2 == 0]
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替え→変換→抽出の順に処理する
    return [v for v in [v * 2 for v in sorted(xs)] if v % 2 == 0]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v for v in [v * 2 for v in sorted(xs)] if v % 2 == 0]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 並べ替え→変換→抽出の順に処理する
    return [v for v in [v * 2 for v in sorted(xs)] if v % 2 == 0]
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [value for value in [value * 2 for value in sorted(xs)] if value % 2 == 0]
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替え→変換→抽出の順に処理する
    return [value for value in [value * 2 for value in sorted(xs)] if value % 2 == 0]
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return [value for value in [value * 2 for value in sorted(xs)] if value % 2 == 0]
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 並べ替え→変換→抽出の順に処理する
    return [value for value in [value * 2 for value in sorted(xs)] if value % 2 == 0]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = sorted(xs)
    result = [x * 2 for x in result]
    result = [x for x in result if x % 2 == 0]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    result: list[int] = sorted(xs)
    # 各要素を変換する
    result = [x * 2 for x in result]
    # 条件に合う要素だけを残す
    result = [x for x in result if x % 2 == 0]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = sorted(xs)
    result = [x * 2 for x in result]
    result = [x for x in result if x % 2 == 0]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    result = sorted(xs)
    # 各要素を変換する
    result = [x * 2 for x in result]
    # 条件に合う要素だけを残す
    result = [x for x in result if x % 2 == 0]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = sorted(xs)
    out = [v * 2 for v in out]
    out = [v for v in out if v % 2 == 0]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    out: list[int] = sorted(xs)
    # 各要素を変換する
    out = [v * 2 for v in out]
    # 条件に合う要素だけを残す
    out = [v for v in out if v % 2 == 0]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = sorted(xs)
    out = [v * 2 for v in out]
    out = [v for v in out if v % 2 == 0]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    out = sorted(xs)
    # 各要素を変換する
    out = [v * 2 for v in out]
    # 条件に合う要素だけを残す
    out = [v for v in out if v % 2 == 0]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = sorted(xs)
    values = [value * 2 for value in values]
    values = [value for value in values if value % 2 == 0]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    values: list[int] = sorted(xs)
    # 各要素を変換する
    values = [value * 2 for value in values]
    # 条件に合う要素だけを残す
    values = [value for value in values if value % 2 == 0]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = sorted(xs)
    values = [value * 2 for value in values]
    values = [value for value in values if value % 2 == 0]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    values = sorted(xs)
    # 各要素を変換する
    values = [value * 2 for value in values]
    # 条件に合う要素だけを残す
    values = [value for value in values if value % 2 == 0]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    ordered: list[int] = sorted(xs)
    mapped: list[int] = [x * 2 for x in ordered]
    kept: list[int] = [x for x in mapped if x % 2 == 0]
    return kept
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    ordered: list[int] = sorted(xs)
    # 各要素を変換する
    mapped: list[int] = [x * 2 for x in ordered]
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in mapped if x % 2 == 0]
    return kept
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    ordered = sorted(xs)
    mapped = [x * 2 for x in ordered]
    kept = [x for x in mapped if x % 2 == 0]
    return kept
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    ordered = sorted(xs)
    # 各要素を変換する
    mapped = [x * 2 for x in ordered]
    # 条件に合う要素だけを残す
    kept = [x for x in mapped if x % 2 == 0]
    return kept
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    srt: list[int] = sorted(xs)
    conv: list[int] = [v * 2 for v in srt]
    sel: list[int] = [v for v in conv if v % 2 == 0]
    return sel
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    srt: list[int] = sorted(xs)
    # 各要素を変換する
    conv: list[int] = [v * 2 for v in srt]
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in conv if v % 2 == 0]
    return sel
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    srt = sorted(xs)
    conv = [v * 2 for v in srt]
    sel = [v for v in conv if v % 2 == 0]
    return sel
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    srt = sorted(xs)
    # 各要素を変換する
    conv = [v * 2 for v in srt]
    # 条件に合う要素だけを残す
    sel = [v for v in conv if v % 2 == 0]
    return sel
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    reordered: list[int] = sorted(xs)
    transformed: list[int] = [value * 2 for value in reordered]
    filtered: list[int] = [value for value in transformed if value % 2 == 0]
    return filtered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    reordered: list[int] = sorted(xs)
    # 各要素を変換する
    transformed: list[int] = [value * 2 for value in reordered]
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in transformed if value % 2 == 0]
    return filtered
```

### comprehension_staged

```python
def solve(xs, k):
    reordered = sorted(xs)
    transformed = [value * 2 for value in reordered]
    filtered = [value for value in transformed if value % 2 == 0]
    return filtered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 並べ替える
    reordered = sorted(xs)
    # 各要素を変換する
    transformed = [value * 2 for value in reordered]
    # 条件に合う要素だけを残す
    filtered = [value for value in transformed if value % 2 == 0]
    return filtered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    result.sort()
    tmp: list[int] = []
    for x in result:
        tmp.append(x * 2)
    result = tmp
    tmp = []
    for x in result:
        if x % 2 == 0:
            tmp.append(x)
    result = tmp
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 並べ替える
    result.sort()
    # 各要素を変換する
    tmp: list[int] = []
    for x in result:
        tmp.append(x * 2)
    result = tmp
    # 条件に合う要素だけを残す
    tmp = []
    for x in result:
        if x % 2 == 0:
            tmp.append(x)
    result = tmp
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = list(xs)
    result.sort()
    tmp = []
    for x in result:
        tmp.append(x * 2)
    result = tmp
    tmp = []
    for x in result:
        if x % 2 == 0:
            tmp.append(x)
    result = tmp
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    result = list(xs)
    # 並べ替える
    result.sort()
    # 各要素を変換する
    tmp = []
    for x in result:
        tmp.append(x * 2)
    result = tmp
    # 条件に合う要素だけを残す
    tmp = []
    for x in result:
        if x % 2 == 0:
            tmp.append(x)
    result = tmp
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = list(xs)
    out.sort()
    nxt: list[int] = []
    for v in out:
        nxt.append(v * 2)
    out = nxt
    nxt = []
    for v in out:
        if v % 2 == 0:
            nxt.append(v)
    out = nxt
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    out: list[int] = list(xs)
    # 並べ替える
    out.sort()
    # 各要素を変換する
    nxt: list[int] = []
    for v in out:
        nxt.append(v * 2)
    out = nxt
    # 条件に合う要素だけを残す
    nxt = []
    for v in out:
        if v % 2 == 0:
            nxt.append(v)
    out = nxt
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = list(xs)
    out.sort()
    nxt = []
    for v in out:
        nxt.append(v * 2)
    out = nxt
    nxt = []
    for v in out:
        if v % 2 == 0:
            nxt.append(v)
    out = nxt
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    out.sort()
    # 各要素を変換する
    nxt = []
    for v in out:
        nxt.append(v * 2)
    out = nxt
    # 条件に合う要素だけを残す
    nxt = []
    for v in out:
        if v % 2 == 0:
            nxt.append(v)
    out = nxt
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    values.sort()
    collected: list[int] = []
    for value in values:
        collected.append(value * 2)
    values = collected
    collected = []
    for value in values:
        if value % 2 == 0:
            collected.append(value)
    values = collected
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 並べ替える
    values.sort()
    # 各要素を変換する
    collected: list[int] = []
    for value in values:
        collected.append(value * 2)
    values = collected
    # 条件に合う要素だけを残す
    collected = []
    for value in values:
        if value % 2 == 0:
            collected.append(value)
    values = collected
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = list(xs)
    values.sort()
    collected = []
    for value in values:
        collected.append(value * 2)
    values = collected
    collected = []
    for value in values:
        if value % 2 == 0:
            collected.append(value)
    values = collected
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    values = list(xs)
    # 並べ替える
    values.sort()
    # 各要素を変換する
    collected = []
    for value in values:
        collected.append(value * 2)
    values = collected
    # 条件に合う要素だけを残す
    collected = []
    for value in values:
        if value % 2 == 0:
            collected.append(value)
    values = collected
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    ordered: list[int] = sorted(result)
    mapped: list[int] = []
    for x in ordered:
        mapped.append(x * 2)
    kept: list[int] = []
    for x in mapped:
        if x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 並べ替える
    ordered: list[int] = sorted(result)
    # 各要素を変換する
    mapped: list[int] = []
    for x in ordered:
        mapped.append(x * 2)
    # 条件に合う要素だけを残す
    kept: list[int] = []
    for x in mapped:
        if x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    result = list(xs)
    ordered = sorted(result)
    mapped = []
    for x in ordered:
        mapped.append(x * 2)
    kept = []
    for x in mapped:
        if x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    result = list(xs)
    # 並べ替える
    ordered = sorted(result)
    # 各要素を変換する
    mapped = []
    for x in ordered:
        mapped.append(x * 2)
    # 条件に合う要素だけを残す
    kept = []
    for x in mapped:
        if x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = list(xs)
    srt: list[int] = sorted(out)
    conv: list[int] = []
    for v in srt:
        conv.append(v * 2)
    sel: list[int] = []
    for v in conv:
        if v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    out: list[int] = list(xs)
    # 並べ替える
    srt: list[int] = sorted(out)
    # 各要素を変換する
    conv: list[int] = []
    for v in srt:
        conv.append(v * 2)
    # 条件に合う要素だけを残す
    sel: list[int] = []
    for v in conv:
        if v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_bare

```python
def solve(xs, k):
    out = list(xs)
    srt = sorted(out)
    conv = []
    for v in srt:
        conv.append(v * 2)
    sel = []
    for v in conv:
        if v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    srt = sorted(out)
    # 各要素を変換する
    conv = []
    for v in srt:
        conv.append(v * 2)
    # 条件に合う要素だけを残す
    sel = []
    for v in conv:
        if v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    reordered: list[int] = sorted(values)
    transformed: list[int] = []
    for value in reordered:
        transformed.append(value * 2)
    filtered: list[int] = []
    for value in transformed:
        if value % 2 == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 並べ替える
    reordered: list[int] = sorted(values)
    # 各要素を変換する
    transformed: list[int] = []
    for value in reordered:
        transformed.append(value * 2)
    # 条件に合う要素だけを残す
    filtered: list[int] = []
    for value in transformed:
        if value % 2 == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    values = list(xs)
    reordered = sorted(values)
    transformed = []
    for value in reordered:
        transformed.append(value * 2)
    filtered = []
    for value in transformed:
        if value % 2 == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    values = list(xs)
    # 並べ替える
    reordered = sorted(values)
    # 各要素を変換する
    transformed = []
    for value in reordered:
        transformed.append(value * 2)
    # 条件に合う要素だけを残す
    filtered = []
    for value in transformed:
        if value % 2 == 0:
            filtered.append(value)
    return filtered
```

## `{"ops": [["order", "reverse"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return xs[::-1]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替えの順に処理する
    return xs[::-1]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return xs[::-1]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 並べ替えの順に処理する
    return xs[::-1]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = xs[::-1]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    result: list[int] = xs[::-1]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = xs[::-1]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    result = xs[::-1]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = xs[::-1]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    out: list[int] = xs[::-1]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = xs[::-1]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    out = xs[::-1]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = xs[::-1]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    values: list[int] = xs[::-1]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = xs[::-1]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    values = xs[::-1]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    ordered: list[int] = xs[::-1]
    return ordered
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    ordered: list[int] = xs[::-1]
    return ordered
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    ordered = xs[::-1]
    return ordered
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    ordered = xs[::-1]
    return ordered
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    srt: list[int] = xs[::-1]
    return srt
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    srt: list[int] = xs[::-1]
    return srt
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    srt = xs[::-1]
    return srt
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    srt = xs[::-1]
    return srt
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    reordered: list[int] = xs[::-1]
    return reordered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    reordered: list[int] = xs[::-1]
    return reordered
```

### comprehension_staged

```python
def solve(xs, k):
    reordered = xs[::-1]
    return reordered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 並べ替える
    reordered = xs[::-1]
    return reordered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    result.reverse()
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 並べ替える
    result.reverse()
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = list(xs)
    result.reverse()
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    result = list(xs)
    # 並べ替える
    result.reverse()
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = list(xs)
    out.reverse()
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    out: list[int] = list(xs)
    # 並べ替える
    out.reverse()
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = list(xs)
    out.reverse()
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    out.reverse()
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    values.reverse()
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 並べ替える
    values.reverse()
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = list(xs)
    values.reverse()
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    values = list(xs)
    # 並べ替える
    values.reverse()
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    ordered: list[int] = result[::-1]
    return ordered
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 並べ替える
    ordered: list[int] = result[::-1]
    return ordered
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    result = list(xs)
    ordered = result[::-1]
    return ordered
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    result = list(xs)
    # 並べ替える
    ordered = result[::-1]
    return ordered
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = list(xs)
    srt: list[int] = out[::-1]
    return srt
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    out: list[int] = list(xs)
    # 並べ替える
    srt: list[int] = out[::-1]
    return srt
```

### for_loop_staged_bare

```python
def solve(xs, k):
    out = list(xs)
    srt = out[::-1]
    return srt
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    srt = out[::-1]
    return srt
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    reordered: list[int] = values[::-1]
    return reordered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 並べ替える
    reordered: list[int] = values[::-1]
    return reordered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    values = list(xs)
    reordered = values[::-1]
    return reordered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    values = list(xs)
    # 並べ替える
    reordered = values[::-1]
    return reordered
```

### explicit_reverse

```python
def solve(xs, k):
    return list(reversed(xs))
```

### for_loop_explicit_reverse

```python
def solve(xs, k):
    # 元のリストを複製する
    result = list(xs)
    # 並べ替える
    result = result[::-1]
    return result
```

## `{"ops": [["map", "add_k"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x + k for x in xs]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 変換の順に処理する
    return [x + k for x in xs]
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return [x + k for x in xs]
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 変換の順に処理する
    return [x + k for x in xs]
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [v + k for v in xs]
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 変換の順に処理する
    return [v + k for v in xs]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v + k for v in xs]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 変換の順に処理する
    return [v + k for v in xs]
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [value + k for value in xs]
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 変換の順に処理する
    return [value + k for value in xs]
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return [value + k for value in xs]
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 変換の順に処理する
    return [value + k for value in xs]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x + k for x in xs]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    result: list[int] = [x + k for x in xs]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x + k for x in xs]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    result = [x + k for x in xs]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v + k for v in xs]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    out: list[int] = [v + k for v in xs]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v + k for v in xs]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    out = [v + k for v in xs]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value + k for value in xs]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    values: list[int] = [value + k for value in xs]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value + k for value in xs]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    values = [value + k for value in xs]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    mapped: list[int] = [x + k for x in xs]
    return mapped
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    mapped: list[int] = [x + k for x in xs]
    return mapped
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    mapped = [x + k for x in xs]
    return mapped
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    mapped = [x + k for x in xs]
    return mapped
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    conv: list[int] = [v + k for v in xs]
    return conv
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    conv: list[int] = [v + k for v in xs]
    return conv
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    conv = [v + k for v in xs]
    return conv
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    conv = [v + k for v in xs]
    return conv
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    transformed: list[int] = [value + k for value in xs]
    return transformed
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    transformed: list[int] = [value + k for value in xs]
    return transformed
```

### comprehension_staged

```python
def solve(xs, k):
    transformed = [value + k for value in xs]
    return transformed
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 各要素を変換する
    transformed = [value + k for value in xs]
    return transformed
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        result.append(x + k)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    result: list[int] = []
    for x in xs:
        result.append(x + k)
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        result.append(x + k)
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    result = []
    for x in xs:
        result.append(x + k)
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        out.append(v + k)
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    out: list[int] = []
    for v in xs:
        out.append(v + k)
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        out.append(v + k)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    out = []
    for v in xs:
        out.append(v + k)
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        values.append(value + k)
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    values: list[int] = []
    for value in xs:
        values.append(value + k)
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        values.append(value + k)
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    values = []
    for value in xs:
        values.append(value + k)
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    mapped: list[int] = []
    for x in xs:
        mapped.append(x + k)
    return mapped
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    mapped: list[int] = []
    for x in xs:
        mapped.append(x + k)
    return mapped
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    mapped = []
    for x in xs:
        mapped.append(x + k)
    return mapped
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    mapped = []
    for x in xs:
        mapped.append(x + k)
    return mapped
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    conv: list[int] = []
    for v in xs:
        conv.append(v + k)
    return conv
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    conv: list[int] = []
    for v in xs:
        conv.append(v + k)
    return conv
```

### for_loop_staged_bare

```python
def solve(xs, k):
    conv = []
    for v in xs:
        conv.append(v + k)
    return conv
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    conv = []
    for v in xs:
        conv.append(v + k)
    return conv
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    transformed: list[int] = []
    for value in xs:
        transformed.append(value + k)
    return transformed
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    transformed: list[int] = []
    for value in xs:
        transformed.append(value + k)
    return transformed
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    transformed = []
    for value in xs:
        transformed.append(value + k)
    return transformed
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    transformed = []
    for value in xs:
        transformed.append(value + k)
    return transformed
```

## `{"ops": [["filter", "odd"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in xs if x % 2 != 0]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [x for x in xs if x % 2 != 0]
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return [x for x in xs if x % 2 != 0]
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [x for x in xs if x % 2 != 0]
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [v for v in xs if v % 2 != 0]
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [v for v in xs if v % 2 != 0]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v for v in xs if v % 2 != 0]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [v for v in xs if v % 2 != 0]
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [value for value in xs if value % 2 != 0]
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [value for value in xs if value % 2 != 0]
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return [value for value in xs if value % 2 != 0]
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [value for value in xs if value % 2 != 0]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x for x in xs if x % 2 != 0]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = [x for x in xs if x % 2 != 0]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x for x in xs if x % 2 != 0]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = [x for x in xs if x % 2 != 0]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v for v in xs if v % 2 != 0]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = [v for v in xs if v % 2 != 0]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v for v in xs if v % 2 != 0]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = [v for v in xs if v % 2 != 0]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value for value in xs if value % 2 != 0]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = [value for value in xs if value % 2 != 0]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value for value in xs if value % 2 != 0]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = [value for value in xs if value % 2 != 0]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x % 2 != 0]
    return kept
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x % 2 != 0]
    return kept
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    kept = [x for x in xs if x % 2 != 0]
    return kept
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = [x for x in xs if x % 2 != 0]
    return kept
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = [v for v in xs if v % 2 != 0]
    return sel
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in xs if v % 2 != 0]
    return sel
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    sel = [v for v in xs if v % 2 != 0]
    return sel
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = [v for v in xs if v % 2 != 0]
    return sel
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = [value for value in xs if value % 2 != 0]
    return filtered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in xs if value % 2 != 0]
    return filtered
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value % 2 != 0]
    return filtered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value % 2 != 0]
    return filtered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x % 2 != 0:
            result.append(x)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = []
    for x in xs:
        if x % 2 != 0:
            result.append(x)
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        if x % 2 != 0:
            result.append(x)
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = []
    for x in xs:
        if x % 2 != 0:
            result.append(x)
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        if v % 2 != 0:
            out.append(v)
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = []
    for v in xs:
        if v % 2 != 0:
            out.append(v)
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v % 2 != 0:
            out.append(v)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = []
    for v in xs:
        if v % 2 != 0:
            out.append(v)
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        if value % 2 != 0:
            values.append(value)
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = []
    for value in xs:
        if value % 2 != 0:
            values.append(value)
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        if value % 2 != 0:
            values.append(value)
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = []
    for value in xs:
        if value % 2 != 0:
            values.append(value)
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = []
    for x in xs:
        if x % 2 != 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = []
    for x in xs:
        if x % 2 != 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    kept = []
    for x in xs:
        if x % 2 != 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = []
    for x in xs:
        if x % 2 != 0:
            kept.append(x)
    return kept
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = []
    for v in xs:
        if v % 2 != 0:
            sel.append(v)
    return sel
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = []
    for v in xs:
        if v % 2 != 0:
            sel.append(v)
    return sel
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v % 2 != 0:
            sel.append(v)
    return sel
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = []
    for v in xs:
        if v % 2 != 0:
            sel.append(v)
    return sel
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value % 2 != 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = []
    for value in xs:
        if value % 2 != 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    filtered = []
    for value in xs:
        if value % 2 != 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = []
    for value in xs:
        if value % 2 != 0:
            filtered.append(value)
    return filtered
```

## `{"ops": [["order", "ascending"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted(xs)
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替えの順に処理する
    return sorted(xs)
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted(xs)
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 並べ替えの順に処理する
    return sorted(xs)
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = sorted(xs)
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    result: list[int] = sorted(xs)
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = sorted(xs)
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    result = sorted(xs)
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = sorted(xs)
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    out: list[int] = sorted(xs)
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = sorted(xs)
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    out = sorted(xs)
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = sorted(xs)
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    values: list[int] = sorted(xs)
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = sorted(xs)
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    values = sorted(xs)
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    ordered: list[int] = sorted(xs)
    return ordered
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    ordered: list[int] = sorted(xs)
    return ordered
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    ordered = sorted(xs)
    return ordered
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    ordered = sorted(xs)
    return ordered
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    srt: list[int] = sorted(xs)
    return srt
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    srt: list[int] = sorted(xs)
    return srt
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    srt = sorted(xs)
    return srt
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    srt = sorted(xs)
    return srt
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    reordered: list[int] = sorted(xs)
    return reordered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    reordered: list[int] = sorted(xs)
    return reordered
```

### comprehension_staged

```python
def solve(xs, k):
    reordered = sorted(xs)
    return reordered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 並べ替える
    reordered = sorted(xs)
    return reordered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    result.sort()
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 並べ替える
    result.sort()
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = list(xs)
    result.sort()
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    result = list(xs)
    # 並べ替える
    result.sort()
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = list(xs)
    out.sort()
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    out: list[int] = list(xs)
    # 並べ替える
    out.sort()
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = list(xs)
    out.sort()
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    out.sort()
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    values.sort()
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 並べ替える
    values.sort()
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = list(xs)
    values.sort()
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    values = list(xs)
    # 並べ替える
    values.sort()
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    ordered: list[int] = sorted(result)
    return ordered
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 並べ替える
    ordered: list[int] = sorted(result)
    return ordered
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    result = list(xs)
    ordered = sorted(result)
    return ordered
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    result = list(xs)
    # 並べ替える
    ordered = sorted(result)
    return ordered
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = list(xs)
    srt: list[int] = sorted(out)
    return srt
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    out: list[int] = list(xs)
    # 並べ替える
    srt: list[int] = sorted(out)
    return srt
```

### for_loop_staged_bare

```python
def solve(xs, k):
    out = list(xs)
    srt = sorted(out)
    return srt
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    srt = sorted(out)
    return srt
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    reordered: list[int] = sorted(values)
    return reordered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 並べ替える
    reordered: list[int] = sorted(values)
    return reordered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    values = list(xs)
    reordered = sorted(values)
    return reordered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    values = list(xs)
    # 並べ替える
    reordered = sorted(values)
    return reordered
```

## `{"ops": [["filter", "gt_k"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in xs if x > k]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [x for x in xs if x > k]
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return [x for x in xs if x > k]
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [x for x in xs if x > k]
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [v for v in xs if v > k]
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [v for v in xs if v > k]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v for v in xs if v > k]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [v for v in xs if v > k]
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [value for value in xs if value > k]
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [value for value in xs if value > k]
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return [value for value in xs if value > k]
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [value for value in xs if value > k]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x for x in xs if x > k]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = [x for x in xs if x > k]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x for x in xs if x > k]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = [x for x in xs if x > k]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v for v in xs if v > k]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = [v for v in xs if v > k]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v for v in xs if v > k]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = [v for v in xs if v > k]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value for value in xs if value > k]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = [value for value in xs if value > k]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value for value in xs if value > k]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = [value for value in xs if value > k]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x > k]
    return kept
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x > k]
    return kept
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    kept = [x for x in xs if x > k]
    return kept
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = [x for x in xs if x > k]
    return kept
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = [v for v in xs if v > k]
    return sel
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in xs if v > k]
    return sel
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    sel = [v for v in xs if v > k]
    return sel
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = [v for v in xs if v > k]
    return sel
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = [value for value in xs if value > k]
    return filtered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in xs if value > k]
    return filtered
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value > k]
    return filtered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value > k]
    return filtered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x > k:
            result.append(x)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = []
    for x in xs:
        if x > k:
            result.append(x)
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        if x > k:
            result.append(x)
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = []
    for x in xs:
        if x > k:
            result.append(x)
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        if v > k:
            out.append(v)
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = []
    for v in xs:
        if v > k:
            out.append(v)
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v > k:
            out.append(v)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = []
    for v in xs:
        if v > k:
            out.append(v)
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        if value > k:
            values.append(value)
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = []
    for value in xs:
        if value > k:
            values.append(value)
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        if value > k:
            values.append(value)
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = []
    for value in xs:
        if value > k:
            values.append(value)
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = []
    for x in xs:
        if x > k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = []
    for x in xs:
        if x > k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    kept = []
    for x in xs:
        if x > k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = []
    for x in xs:
        if x > k:
            kept.append(x)
    return kept
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = []
    for v in xs:
        if v > k:
            sel.append(v)
    return sel
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = []
    for v in xs:
        if v > k:
            sel.append(v)
    return sel
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v > k:
            sel.append(v)
    return sel
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = []
    for v in xs:
        if v > k:
            sel.append(v)
    return sel
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value > k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = []
    for value in xs:
        if value > k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    filtered = []
    for value in xs:
        if value > k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = []
    for value in xs:
        if value > k:
            filtered.append(value)
    return filtered
```

## `{"ops": [["slice", "take_first_k"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return xs[:k]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 切り出しの順に処理する
    return xs[:k]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return xs[:k]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 切り出しの順に処理する
    return xs[:k]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = xs[:k]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    result: list[int] = xs[:k]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = xs[:k]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    result = xs[:k]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = xs[:k]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    out: list[int] = xs[:k]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = xs[:k]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    out = xs[:k]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = xs[:k]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    values: list[int] = xs[:k]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = xs[:k]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    values = xs[:k]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    picked: list[int] = xs[:k]
    return picked
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    picked: list[int] = xs[:k]
    return picked
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    picked = xs[:k]
    return picked
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    picked = xs[:k]
    return picked
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    cut: list[int] = xs[:k]
    return cut
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    cut: list[int] = xs[:k]
    return cut
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    cut = xs[:k]
    return cut
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    cut = xs[:k]
    return cut
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    trimmed: list[int] = xs[:k]
    return trimmed
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    trimmed: list[int] = xs[:k]
    return trimmed
```

### comprehension_staged

```python
def solve(xs, k):
    trimmed = xs[:k]
    return trimmed
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    trimmed = xs[:k]
    return trimmed
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    result = result[:k]
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 必要な範囲を取り出す
    result = result[:k]
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = list(xs)
    result = result[:k]
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    result = list(xs)
    # 必要な範囲を取り出す
    result = result[:k]
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = list(xs)
    out = out[:k]
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    out: list[int] = list(xs)
    # 必要な範囲を取り出す
    out = out[:k]
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = list(xs)
    out = out[:k]
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 必要な範囲を取り出す
    out = out[:k]
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    values = values[:k]
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 必要な範囲を取り出す
    values = values[:k]
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = list(xs)
    values = values[:k]
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    values = list(xs)
    # 必要な範囲を取り出す
    values = values[:k]
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    picked: list[int] = result[:k]
    return picked
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 必要な範囲を取り出す
    picked: list[int] = result[:k]
    return picked
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    result = list(xs)
    picked = result[:k]
    return picked
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    result = list(xs)
    # 必要な範囲を取り出す
    picked = result[:k]
    return picked
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = list(xs)
    cut: list[int] = out[:k]
    return cut
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    out: list[int] = list(xs)
    # 必要な範囲を取り出す
    cut: list[int] = out[:k]
    return cut
```

### for_loop_staged_bare

```python
def solve(xs, k):
    out = list(xs)
    cut = out[:k]
    return cut
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 必要な範囲を取り出す
    cut = out[:k]
    return cut
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    trimmed: list[int] = values[:k]
    return trimmed
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 必要な範囲を取り出す
    trimmed: list[int] = values[:k]
    return trimmed
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    values = list(xs)
    trimmed = values[:k]
    return trimmed
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    values = list(xs)
    # 必要な範囲を取り出す
    trimmed = values[:k]
    return trimmed
```

## `{"ops": [["filter", "ge_k"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in xs if x >= k]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [x for x in xs if x >= k]
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return [x for x in xs if x >= k]
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [x for x in xs if x >= k]
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [v for v in xs if v >= k]
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [v for v in xs if v >= k]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v for v in xs if v >= k]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [v for v in xs if v >= k]
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [value for value in xs if value >= k]
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [value for value in xs if value >= k]
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return [value for value in xs if value >= k]
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [value for value in xs if value >= k]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x for x in xs if x >= k]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = [x for x in xs if x >= k]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x for x in xs if x >= k]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = [x for x in xs if x >= k]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v for v in xs if v >= k]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = [v for v in xs if v >= k]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v for v in xs if v >= k]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = [v for v in xs if v >= k]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value for value in xs if value >= k]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = [value for value in xs if value >= k]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value for value in xs if value >= k]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = [value for value in xs if value >= k]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x >= k]
    return kept
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x >= k]
    return kept
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    kept = [x for x in xs if x >= k]
    return kept
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = [x for x in xs if x >= k]
    return kept
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = [v for v in xs if v >= k]
    return sel
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in xs if v >= k]
    return sel
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    sel = [v for v in xs if v >= k]
    return sel
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = [v for v in xs if v >= k]
    return sel
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = [value for value in xs if value >= k]
    return filtered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in xs if value >= k]
    return filtered
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value >= k]
    return filtered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value >= k]
    return filtered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x >= k:
            result.append(x)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = []
    for x in xs:
        if x >= k:
            result.append(x)
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        if x >= k:
            result.append(x)
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = []
    for x in xs:
        if x >= k:
            result.append(x)
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        if v >= k:
            out.append(v)
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = []
    for v in xs:
        if v >= k:
            out.append(v)
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v >= k:
            out.append(v)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = []
    for v in xs:
        if v >= k:
            out.append(v)
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        if value >= k:
            values.append(value)
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = []
    for value in xs:
        if value >= k:
            values.append(value)
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        if value >= k:
            values.append(value)
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = []
    for value in xs:
        if value >= k:
            values.append(value)
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = []
    for x in xs:
        if x >= k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = []
    for x in xs:
        if x >= k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    kept = []
    for x in xs:
        if x >= k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = []
    for x in xs:
        if x >= k:
            kept.append(x)
    return kept
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = []
    for v in xs:
        if v >= k:
            sel.append(v)
    return sel
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = []
    for v in xs:
        if v >= k:
            sel.append(v)
    return sel
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v >= k:
            sel.append(v)
    return sel
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = []
    for v in xs:
        if v >= k:
            sel.append(v)
    return sel
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value >= k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = []
    for value in xs:
        if value >= k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    filtered = []
    for value in xs:
        if value >= k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = []
    for value in xs:
        if value >= k:
            filtered.append(value)
    return filtered
```

## `{"ops": [["filter", "even"], ["filter", "even"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in xs if x % 2 == 0 and x % 2 == 0]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→抽出の順に処理する
    return [x for x in xs if x % 2 == 0 and x % 2 == 0]
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return [x for x in xs if x % 2 == 0 and x % 2 == 0]
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 抽出→抽出の順に処理する
    return [x for x in xs if x % 2 == 0 and x % 2 == 0]
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [v for v in xs if v % 2 == 0 and v % 2 == 0]
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→抽出の順に処理する
    return [v for v in xs if v % 2 == 0 and v % 2 == 0]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v for v in xs if v % 2 == 0 and v % 2 == 0]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出→抽出の順に処理する
    return [v for v in xs if v % 2 == 0 and v % 2 == 0]
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [value for value in xs if value % 2 == 0 and value % 2 == 0]
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→抽出の順に処理する
    return [value for value in xs if value % 2 == 0 and value % 2 == 0]
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return [value for value in xs if value % 2 == 0 and value % 2 == 0]
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 抽出→抽出の順に処理する
    return [value for value in xs if value % 2 == 0 and value % 2 == 0]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x for x in xs if x % 2 == 0 and x % 2 == 0]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = [x for x in xs if x % 2 == 0 and x % 2 == 0]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x for x in xs if x % 2 == 0 and x % 2 == 0]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = [x for x in xs if x % 2 == 0 and x % 2 == 0]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v for v in xs if v % 2 == 0 and v % 2 == 0]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = [v for v in xs if v % 2 == 0 and v % 2 == 0]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v for v in xs if v % 2 == 0 and v % 2 == 0]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = [v for v in xs if v % 2 == 0 and v % 2 == 0]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value for value in xs if value % 2 == 0 and value % 2 == 0]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = [value for value in xs if value % 2 == 0 and value % 2 == 0]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value for value in xs if value % 2 == 0 and value % 2 == 0]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = [value for value in xs if value % 2 == 0 and value % 2 == 0]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x % 2 == 0]
    kept_2: list[int] = [x for x in kept if x % 2 == 0]
    return kept_2
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x % 2 == 0]
    # 条件に合う要素だけを残す
    kept_2: list[int] = [x for x in kept if x % 2 == 0]
    return kept_2
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    kept = [x for x in xs if x % 2 == 0]
    kept_2 = [x for x in kept if x % 2 == 0]
    return kept_2
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = [x for x in xs if x % 2 == 0]
    # 条件に合う要素だけを残す
    kept_2 = [x for x in kept if x % 2 == 0]
    return kept_2
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = [v for v in xs if v % 2 == 0]
    sel_2: list[int] = [v for v in sel if v % 2 == 0]
    return sel_2
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in xs if v % 2 == 0]
    # 条件に合う要素だけを残す
    sel_2: list[int] = [v for v in sel if v % 2 == 0]
    return sel_2
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    sel = [v for v in xs if v % 2 == 0]
    sel_2 = [v for v in sel if v % 2 == 0]
    return sel_2
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = [v for v in xs if v % 2 == 0]
    # 条件に合う要素だけを残す
    sel_2 = [v for v in sel if v % 2 == 0]
    return sel_2
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = [value for value in xs if value % 2 == 0]
    filtered_2: list[int] = [value for value in filtered if value % 2 == 0]
    return filtered_2
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in xs if value % 2 == 0]
    # 条件に合う要素だけを残す
    filtered_2: list[int] = [value for value in filtered if value % 2 == 0]
    return filtered_2
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value % 2 == 0]
    filtered_2 = [value for value in filtered if value % 2 == 0]
    return filtered_2
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value % 2 == 0]
    # 条件に合う要素だけを残す
    filtered_2 = [value for value in filtered if value % 2 == 0]
    return filtered_2
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x % 2 == 0 and x % 2 == 0:
            result.append(x)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = []
    for x in xs:
        if x % 2 == 0 and x % 2 == 0:
            result.append(x)
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        if x % 2 == 0 and x % 2 == 0:
            result.append(x)
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = []
    for x in xs:
        if x % 2 == 0 and x % 2 == 0:
            result.append(x)
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        if v % 2 == 0 and v % 2 == 0:
            out.append(v)
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = []
    for v in xs:
        if v % 2 == 0 and v % 2 == 0:
            out.append(v)
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v % 2 == 0 and v % 2 == 0:
            out.append(v)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = []
    for v in xs:
        if v % 2 == 0 and v % 2 == 0:
            out.append(v)
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        if value % 2 == 0 and value % 2 == 0:
            values.append(value)
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = []
    for value in xs:
        if value % 2 == 0 and value % 2 == 0:
            values.append(value)
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        if value % 2 == 0 and value % 2 == 0:
            values.append(value)
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = []
    for value in xs:
        if value % 2 == 0 and value % 2 == 0:
            values.append(value)
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = []
    for x in xs:
        if x % 2 == 0 and x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = []
    for x in xs:
        if x % 2 == 0 and x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    kept = []
    for x in xs:
        if x % 2 == 0 and x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = []
    for x in xs:
        if x % 2 == 0 and x % 2 == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = []
    for v in xs:
        if v % 2 == 0 and v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = []
    for v in xs:
        if v % 2 == 0 and v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v % 2 == 0 and v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = []
    for v in xs:
        if v % 2 == 0 and v % 2 == 0:
            sel.append(v)
    return sel
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0 and value % 2 == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0 and value % 2 == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    filtered = []
    for value in xs:
        if value % 2 == 0 and value % 2 == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = []
    for value in xs:
        if value % 2 == 0 and value % 2 == 0:
            filtered.append(value)
    return filtered
```

## `{"ops": [["filter", "lt_k"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in xs if x < k]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [x for x in xs if x < k]
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return [x for x in xs if x < k]
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [x for x in xs if x < k]
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [v for v in xs if v < k]
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [v for v in xs if v < k]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v for v in xs if v < k]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [v for v in xs if v < k]
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [value for value in xs if value < k]
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [value for value in xs if value < k]
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return [value for value in xs if value < k]
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [value for value in xs if value < k]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x for x in xs if x < k]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = [x for x in xs if x < k]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x for x in xs if x < k]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = [x for x in xs if x < k]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v for v in xs if v < k]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = [v for v in xs if v < k]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v for v in xs if v < k]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = [v for v in xs if v < k]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value for value in xs if value < k]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = [value for value in xs if value < k]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value for value in xs if value < k]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = [value for value in xs if value < k]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x < k]
    return kept
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x < k]
    return kept
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    kept = [x for x in xs if x < k]
    return kept
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = [x for x in xs if x < k]
    return kept
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = [v for v in xs if v < k]
    return sel
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in xs if v < k]
    return sel
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    sel = [v for v in xs if v < k]
    return sel
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = [v for v in xs if v < k]
    return sel
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = [value for value in xs if value < k]
    return filtered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in xs if value < k]
    return filtered
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value < k]
    return filtered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value < k]
    return filtered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x < k:
            result.append(x)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = []
    for x in xs:
        if x < k:
            result.append(x)
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        if x < k:
            result.append(x)
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = []
    for x in xs:
        if x < k:
            result.append(x)
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        if v < k:
            out.append(v)
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = []
    for v in xs:
        if v < k:
            out.append(v)
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v < k:
            out.append(v)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = []
    for v in xs:
        if v < k:
            out.append(v)
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        if value < k:
            values.append(value)
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = []
    for value in xs:
        if value < k:
            values.append(value)
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        if value < k:
            values.append(value)
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = []
    for value in xs:
        if value < k:
            values.append(value)
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = []
    for x in xs:
        if x < k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = []
    for x in xs:
        if x < k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    kept = []
    for x in xs:
        if x < k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = []
    for x in xs:
        if x < k:
            kept.append(x)
    return kept
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = []
    for v in xs:
        if v < k:
            sel.append(v)
    return sel
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = []
    for v in xs:
        if v < k:
            sel.append(v)
    return sel
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v < k:
            sel.append(v)
    return sel
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = []
    for v in xs:
        if v < k:
            sel.append(v)
    return sel
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value < k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = []
    for value in xs:
        if value < k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    filtered = []
    for value in xs:
        if value < k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = []
    for value in xs:
        if value < k:
            filtered.append(value)
    return filtered
```

## `{"ops": [["filter", "even"], ["map", "add_k"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x + k for x in xs if x % 2 == 0]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→変換の順に処理する
    return [x + k for x in xs if x % 2 == 0]
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return [x + k for x in xs if x % 2 == 0]
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 抽出→変換の順に処理する
    return [x + k for x in xs if x % 2 == 0]
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [v + k for v in xs if v % 2 == 0]
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→変換の順に処理する
    return [v + k for v in xs if v % 2 == 0]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v + k for v in xs if v % 2 == 0]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出→変換の順に処理する
    return [v + k for v in xs if v % 2 == 0]
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [value + k for value in xs if value % 2 == 0]
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→変換の順に処理する
    return [value + k for value in xs if value % 2 == 0]
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return [value + k for value in xs if value % 2 == 0]
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 抽出→変換の順に処理する
    return [value + k for value in xs if value % 2 == 0]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x + k for x in xs if x % 2 == 0]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    result: list[int] = [x + k for x in xs if x % 2 == 0]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x + k for x in xs if x % 2 == 0]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    result = [x + k for x in xs if x % 2 == 0]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v + k for v in xs if v % 2 == 0]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    out: list[int] = [v + k for v in xs if v % 2 == 0]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v + k for v in xs if v % 2 == 0]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    out = [v + k for v in xs if v % 2 == 0]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value + k for value in xs if value % 2 == 0]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    values: list[int] = [value + k for value in xs if value % 2 == 0]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value + k for value in xs if value % 2 == 0]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    values = [value + k for value in xs if value % 2 == 0]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x % 2 == 0]
    mapped: list[int] = [x + k for x in kept]
    return mapped
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x % 2 == 0]
    # 各要素を変換する
    mapped: list[int] = [x + k for x in kept]
    return mapped
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    kept = [x for x in xs if x % 2 == 0]
    mapped = [x + k for x in kept]
    return mapped
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = [x for x in xs if x % 2 == 0]
    # 各要素を変換する
    mapped = [x + k for x in kept]
    return mapped
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = [v for v in xs if v % 2 == 0]
    conv: list[int] = [v + k for v in sel]
    return conv
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in xs if v % 2 == 0]
    # 各要素を変換する
    conv: list[int] = [v + k for v in sel]
    return conv
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    sel = [v for v in xs if v % 2 == 0]
    conv = [v + k for v in sel]
    return conv
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = [v for v in xs if v % 2 == 0]
    # 各要素を変換する
    conv = [v + k for v in sel]
    return conv
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = [value for value in xs if value % 2 == 0]
    transformed: list[int] = [value + k for value in filtered]
    return transformed
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in xs if value % 2 == 0]
    # 各要素を変換する
    transformed: list[int] = [value + k for value in filtered]
    return transformed
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value % 2 == 0]
    transformed = [value + k for value in filtered]
    return transformed
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value % 2 == 0]
    # 各要素を変換する
    transformed = [value + k for value in filtered]
    return transformed
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x % 2 == 0:
            result.append(x + k)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    result: list[int] = []
    for x in xs:
        if x % 2 == 0:
            result.append(x + k)
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        if x % 2 == 0:
            result.append(x + k)
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    result = []
    for x in xs:
        if x % 2 == 0:
            result.append(x + k)
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        if v % 2 == 0:
            out.append(v + k)
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    out: list[int] = []
    for v in xs:
        if v % 2 == 0:
            out.append(v + k)
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v % 2 == 0:
            out.append(v + k)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    out = []
    for v in xs:
        if v % 2 == 0:
            out.append(v + k)
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        if value % 2 == 0:
            values.append(value + k)
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    values: list[int] = []
    for value in xs:
        if value % 2 == 0:
            values.append(value + k)
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        if value % 2 == 0:
            values.append(value + k)
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    values = []
    for value in xs:
        if value % 2 == 0:
            values.append(value + k)
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x + k)
    return kept
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    kept: list[int] = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x + k)
    return kept
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    kept = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x + k)
    return kept
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    kept = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x + k)
    return kept
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v + k)
    return sel
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    sel: list[int] = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v + k)
    return sel
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v + k)
    return sel
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    sel = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v + k)
    return sel
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value + k)
    return filtered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value + k)
    return filtered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    filtered = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value + k)
    return filtered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    filtered = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value + k)
    return filtered
```

## `{"ops": [["filter", "le_k"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in xs if x <= k]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [x for x in xs if x <= k]
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return [x for x in xs if x <= k]
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [x for x in xs if x <= k]
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [v for v in xs if v <= k]
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [v for v in xs if v <= k]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v for v in xs if v <= k]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [v for v in xs if v <= k]
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [value for value in xs if value <= k]
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [value for value in xs if value <= k]
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return [value for value in xs if value <= k]
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [value for value in xs if value <= k]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x for x in xs if x <= k]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = [x for x in xs if x <= k]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x for x in xs if x <= k]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = [x for x in xs if x <= k]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v for v in xs if v <= k]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = [v for v in xs if v <= k]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v for v in xs if v <= k]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = [v for v in xs if v <= k]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value for value in xs if value <= k]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = [value for value in xs if value <= k]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value for value in xs if value <= k]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = [value for value in xs if value <= k]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x <= k]
    return kept
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x <= k]
    return kept
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    kept = [x for x in xs if x <= k]
    return kept
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = [x for x in xs if x <= k]
    return kept
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = [v for v in xs if v <= k]
    return sel
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in xs if v <= k]
    return sel
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    sel = [v for v in xs if v <= k]
    return sel
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = [v for v in xs if v <= k]
    return sel
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = [value for value in xs if value <= k]
    return filtered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in xs if value <= k]
    return filtered
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value <= k]
    return filtered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value <= k]
    return filtered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x <= k:
            result.append(x)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = []
    for x in xs:
        if x <= k:
            result.append(x)
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        if x <= k:
            result.append(x)
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = []
    for x in xs:
        if x <= k:
            result.append(x)
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        if v <= k:
            out.append(v)
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = []
    for v in xs:
        if v <= k:
            out.append(v)
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v <= k:
            out.append(v)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = []
    for v in xs:
        if v <= k:
            out.append(v)
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        if value <= k:
            values.append(value)
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = []
    for value in xs:
        if value <= k:
            values.append(value)
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        if value <= k:
            values.append(value)
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = []
    for value in xs:
        if value <= k:
            values.append(value)
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = []
    for x in xs:
        if x <= k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = []
    for x in xs:
        if x <= k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    kept = []
    for x in xs:
        if x <= k:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = []
    for x in xs:
        if x <= k:
            kept.append(x)
    return kept
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = []
    for v in xs:
        if v <= k:
            sel.append(v)
    return sel
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = []
    for v in xs:
        if v <= k:
            sel.append(v)
    return sel
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v <= k:
            sel.append(v)
    return sel
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = []
    for v in xs:
        if v <= k:
            sel.append(v)
    return sel
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value <= k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = []
    for value in xs:
        if value <= k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    filtered = []
    for value in xs:
        if value <= k:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = []
    for value in xs:
        if value <= k:
            filtered.append(value)
    return filtered
```

## `{"ops": [["filter", "even"], ["order", "ascending"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted([x for x in xs if x % 2 == 0])
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→並べ替えの順に処理する
    return sorted([x for x in xs if x % 2 == 0])
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return sorted([x for x in xs if x % 2 == 0])
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 抽出→並べ替えの順に処理する
    return sorted([x for x in xs if x % 2 == 0])
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted([v for v in xs if v % 2 == 0])
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→並べ替えの順に処理する
    return sorted([v for v in xs if v % 2 == 0])
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted([v for v in xs if v % 2 == 0])
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出→並べ替えの順に処理する
    return sorted([v for v in xs if v % 2 == 0])
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted([value for value in xs if value % 2 == 0])
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→並べ替えの順に処理する
    return sorted([value for value in xs if value % 2 == 0])
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return sorted([value for value in xs if value % 2 == 0])
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 抽出→並べ替えの順に処理する
    return sorted([value for value in xs if value % 2 == 0])
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x for x in xs if x % 2 == 0]
    result = sorted(result)
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = [x for x in xs if x % 2 == 0]
    # 並べ替える
    result = sorted(result)
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x for x in xs if x % 2 == 0]
    result = sorted(result)
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = [x for x in xs if x % 2 == 0]
    # 並べ替える
    result = sorted(result)
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v for v in xs if v % 2 == 0]
    out = sorted(out)
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = [v for v in xs if v % 2 == 0]
    # 並べ替える
    out = sorted(out)
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v for v in xs if v % 2 == 0]
    out = sorted(out)
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = [v for v in xs if v % 2 == 0]
    # 並べ替える
    out = sorted(out)
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value for value in xs if value % 2 == 0]
    values = sorted(values)
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = [value for value in xs if value % 2 == 0]
    # 並べ替える
    values = sorted(values)
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value for value in xs if value % 2 == 0]
    values = sorted(values)
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = [value for value in xs if value % 2 == 0]
    # 並べ替える
    values = sorted(values)
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x % 2 == 0]
    ordered: list[int] = sorted(kept)
    return ordered
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x % 2 == 0]
    # 並べ替える
    ordered: list[int] = sorted(kept)
    return ordered
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    kept = [x for x in xs if x % 2 == 0]
    ordered = sorted(kept)
    return ordered
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = [x for x in xs if x % 2 == 0]
    # 並べ替える
    ordered = sorted(kept)
    return ordered
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = [v for v in xs if v % 2 == 0]
    srt: list[int] = sorted(sel)
    return srt
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in xs if v % 2 == 0]
    # 並べ替える
    srt: list[int] = sorted(sel)
    return srt
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    sel = [v for v in xs if v % 2 == 0]
    srt = sorted(sel)
    return srt
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = [v for v in xs if v % 2 == 0]
    # 並べ替える
    srt = sorted(sel)
    return srt
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = [value for value in xs if value % 2 == 0]
    reordered: list[int] = sorted(filtered)
    return reordered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in xs if value % 2 == 0]
    # 並べ替える
    reordered: list[int] = sorted(filtered)
    return reordered
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value % 2 == 0]
    reordered = sorted(filtered)
    return reordered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value % 2 == 0]
    # 並べ替える
    reordered = sorted(filtered)
    return reordered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x % 2 == 0:
            result.append(x)
    result.sort()
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = []
    for x in xs:
        if x % 2 == 0:
            result.append(x)
    # 並べ替える
    result.sort()
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        if x % 2 == 0:
            result.append(x)
    result.sort()
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = []
    for x in xs:
        if x % 2 == 0:
            result.append(x)
    # 並べ替える
    result.sort()
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        if v % 2 == 0:
            out.append(v)
    out.sort()
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = []
    for v in xs:
        if v % 2 == 0:
            out.append(v)
    # 並べ替える
    out.sort()
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v % 2 == 0:
            out.append(v)
    out.sort()
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = []
    for v in xs:
        if v % 2 == 0:
            out.append(v)
    # 並べ替える
    out.sort()
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        if value % 2 == 0:
            values.append(value)
    values.sort()
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = []
    for value in xs:
        if value % 2 == 0:
            values.append(value)
    # 並べ替える
    values.sort()
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        if value % 2 == 0:
            values.append(value)
    values.sort()
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = []
    for value in xs:
        if value % 2 == 0:
            values.append(value)
    # 並べ替える
    values.sort()
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x)
    ordered: list[int] = sorted(kept)
    return ordered
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x)
    # 並べ替える
    ordered: list[int] = sorted(kept)
    return ordered
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    kept = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x)
    ordered = sorted(kept)
    return ordered
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = []
    for x in xs:
        if x % 2 == 0:
            kept.append(x)
    # 並べ替える
    ordered = sorted(kept)
    return ordered
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v)
    srt: list[int] = sorted(sel)
    return srt
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v)
    # 並べ替える
    srt: list[int] = sorted(sel)
    return srt
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v)
    srt = sorted(sel)
    return srt
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = []
    for v in xs:
        if v % 2 == 0:
            sel.append(v)
    # 並べ替える
    srt = sorted(sel)
    return srt
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value)
    reordered: list[int] = sorted(filtered)
    return reordered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value)
    # 並べ替える
    reordered: list[int] = sorted(filtered)
    return reordered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    filtered = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value)
    reordered = sorted(filtered)
    return reordered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = []
    for value in xs:
        if value % 2 == 0:
            filtered.append(value)
    # 並べ替える
    reordered = sorted(filtered)
    return reordered
```

## `{"ops": [["filter", "multiple_of_k"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in xs if x % k == 0]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [x for x in xs if x % k == 0]
```

### list_comprehension_default_bare

```python
def solve(xs, k):
    return [x for x in xs if x % k == 0]
```

### list_comprehension_default_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [x for x in xs if x % k == 0]
```

### list_comprehension_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [v for v in xs if v % k == 0]
```

### list_comprehension_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [v for v in xs if v % k == 0]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v for v in xs if v % k == 0]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [v for v in xs if v % k == 0]
```

### list_comprehension_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [value for value in xs if value % k == 0]
```

### list_comprehension_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [value for value in xs if value % k == 0]
```

### list_comprehension_verbose_bare

```python
def solve(xs, k):
    return [value for value in xs if value % k == 0]
```

### list_comprehension_verbose_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [value for value in xs if value % k == 0]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x for x in xs if x % k == 0]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = [x for x in xs if x % k == 0]
    return result
```

### comprehension_steps_default_bare

```python
def solve(xs, k):
    result = [x for x in xs if x % k == 0]
    return result
```

### comprehension_steps_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = [x for x in xs if x % k == 0]
    return result
```

### comprehension_steps_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = [v for v in xs if v % k == 0]
    return out
```

### comprehension_steps_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = [v for v in xs if v % k == 0]
    return out
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v for v in xs if v % k == 0]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = [v for v in xs if v % k == 0]
    return out
```

### comprehension_steps_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = [value for value in xs if value % k == 0]
    return values
```

### comprehension_steps_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = [value for value in xs if value % k == 0]
    return values
```

### comprehension_steps_verbose_bare

```python
def solve(xs, k):
    values = [value for value in xs if value % k == 0]
    return values
```

### comprehension_steps_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = [value for value in xs if value % k == 0]
    return values
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x % k == 0]
    return kept
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x % k == 0]
    return kept
```

### comprehension_staged_default_bare

```python
def solve(xs, k):
    kept = [x for x in xs if x % k == 0]
    return kept
```

### comprehension_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = [x for x in xs if x % k == 0]
    return kept
```

### comprehension_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = [v for v in xs if v % k == 0]
    return sel
```

### comprehension_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = [v for v in xs if v % k == 0]
    return sel
```

### comprehension_staged_terse_bare

```python
def solve(xs, k):
    sel = [v for v in xs if v % k == 0]
    return sel
```

### comprehension_staged_terse_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = [v for v in xs if v % k == 0]
    return sel
```

### comprehension_staged_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = [value for value in xs if value % k == 0]
    return filtered
```

### comprehension_staged_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = [value for value in xs if value % k == 0]
    return filtered
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value % k == 0]
    return filtered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value % k == 0]
    return filtered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x % k == 0:
            result.append(x)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = []
    for x in xs:
        if x % k == 0:
            result.append(x)
    return result
```

### for_loop_default_bare

```python
def solve(xs, k):
    result = []
    for x in xs:
        if x % k == 0:
            result.append(x)
    return result
```

### for_loop_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    result = []
    for x in xs:
        if x % k == 0:
            result.append(x)
    return result
```

### for_loop_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    out: list[int] = []
    for v in xs:
        if v % k == 0:
            out.append(v)
    return out
```

### for_loop_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    out: list[int] = []
    for v in xs:
        if v % k == 0:
            out.append(v)
    return out
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v % k == 0:
            out.append(v)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = []
    for v in xs:
        if v % k == 0:
            out.append(v)
    return out
```

### for_loop_verbose_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = []
    for value in xs:
        if value % k == 0:
            values.append(value)
    return values
```

### for_loop_verbose_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    values: list[int] = []
    for value in xs:
        if value % k == 0:
            values.append(value)
    return values
```

### for_loop_verbose_bare

```python
def solve(xs, k):
    values = []
    for value in xs:
        if value % k == 0:
            values.append(value)
    return values
```

### for_loop_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    values = []
    for value in xs:
        if value % k == 0:
            values.append(value)
    return values
```

### for_loop_staged_default_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = []
    for x in xs:
        if x % k == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = []
    for x in xs:
        if x % k == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare

```python
def solve(xs, k):
    kept = []
    for x in xs:
        if x % k == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_default_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    kept = []
    for x in xs:
        if x % k == 0:
            kept.append(x)
    return kept
```

### for_loop_staged_terse_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    sel: list[int] = []
    for v in xs:
        if v % k == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_terse_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    sel: list[int] = []
    for v in xs:
        if v % k == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v % k == 0:
            sel.append(v)
    return sel
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = []
    for v in xs:
        if v % k == 0:
            sel.append(v)
    return sel
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value % k == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = []
    for value in xs:
        if value % k == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare

```python
def solve(xs, k):
    filtered = []
    for value in xs:
        if value % k == 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_verbose_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = []
    for value in xs:
        if value % k == 0:
            filtered.append(value)
    return filtered
```
