# 生成コードのサンプル

`code_demo.py` が生成したコードの抜粋（自動生成。手で編集しない）。
意味ASTの構成パターンと原子操作を網羅するように選んだ意味ASTについて、
適用できる`code_style`すべてでレンダリングしたもの。全件は
`semantic_ast/out/code_{train,val,test}.jsonl`（生成物、gitignore済み）にある。

各コードは参照インタプリタと全テストケースで一致することを確認済み
（`verification`は`samples.jsonl`側に入っている）。

## `{"filter": ["even", "ge_k"], "map": [["mul_const", 2]], "order": "ascending"}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted([x * 2 for x in xs if x % 2 == 0 and x >= k])
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出→変換→並べ替えの順に処理する
    return sorted([x * 2 for x in xs if x % 2 == 0 and x >= k])
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted([v * 2 for v in xs if v % 2 == 0 and v >= k])
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出→変換→並べ替えの順に処理する
    return sorted([v * 2 for v in xs if v % 2 == 0 and v >= k])
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x * 2 for x in xs if x % 2 == 0 and x >= k]
    result = sorted(result)
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    result: list[int] = [x * 2 for x in xs if x % 2 == 0 and x >= k]
    # 並べ替える
    result = sorted(result)
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v * 2 for v in xs if v % 2 == 0 and v >= k]
    out = sorted(out)
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素を変換して集める
    out = [v * 2 for v in xs if v % 2 == 0 and v >= k]
    # 並べ替える
    out = sorted(out)
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value % 2 == 0 and value >= k]
    transformed = [value * 2 for value in filtered]
    reordered = sorted(transformed)
    return reordered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value % 2 == 0 and value >= k]
    # 各要素を変換する
    transformed = [value * 2 for value in filtered]
    # 並べ替える
    reordered = sorted(transformed)
    return reordered
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x % 2 == 0 and x >= k]
    mapped = [x * 2 for x in kept]
    ordered = sorted(mapped)
    return ordered
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x % 2 == 0 and x >= k]
    # 各要素を変換する
    mapped = [x * 2 for x in kept]
    # 並べ替える
    ordered = sorted(mapped)
    return ordered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x % 2 == 0 and x >= k:
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
        if x % 2 == 0 and x >= k:
            result.append(x * 2)
    # 並べ替える
    result.sort()
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v % 2 == 0 and v >= k:
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
        if v % 2 == 0 and v >= k:
            out.append(v * 2)
    # 並べ替える
    out.sort()
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0 and value >= k:
            filtered.append(value * 2)
    reordered = sorted(filtered)
    return reordered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素を変換して集める
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0 and value >= k:
            filtered.append(value * 2)
    # 並べ替える
    reordered = sorted(filtered)
    return reordered
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v % 2 == 0 and v >= k:
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
        if v % 2 == 0 and v >= k:
            sel.append(v * 2)
    # 並べ替える
    srt = sorted(sel)
    return srt
```

### condition_swapped

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted([x * 2 for x in xs if x >= k and x % 2 == 0])
```

## `{"slice": ["take_first_k"]}`

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

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    trimmed = values[:k]
    return trimmed
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 必要な範囲を取り出す
    trimmed = values[:k]
    return trimmed
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

## `{"order": "descending"}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted(xs, reverse=True)
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替えの順に処理する
    return sorted(xs, reverse=True)
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted(xs, reverse=True)
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 並べ替えの順に処理する
    return sorted(xs, reverse=True)
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = sorted(xs, reverse=True)
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    result: list[int] = sorted(xs, reverse=True)
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = sorted(xs, reverse=True)
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    out = sorted(xs, reverse=True)
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    reordered = sorted(xs, reverse=True)
    return reordered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 並べ替える
    reordered = sorted(xs, reverse=True)
    return reordered
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    ordered: list[int] = sorted(xs, reverse=True)
    return ordered
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    ordered: list[int] = sorted(xs, reverse=True)
    return ordered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    result.sort(reverse=True)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 並べ替える
    result.sort(reverse=True)
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = list(xs)
    out.sort(reverse=True)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    out.sort(reverse=True)
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    reordered = sorted(values, reverse=True)
    return reordered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 並べ替える
    reordered = sorted(values, reverse=True)
    return reordered
```

### for_loop_staged_bare

```python
def solve(xs, k):
    out = list(xs)
    srt = sorted(out, reverse=True)
    return srt
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    srt = sorted(out, reverse=True)
    return srt
```

### explicit_reverse

```python
def solve(xs, k):
    return sorted(xs)[::-1]
```

### for_loop_explicit_reverse

```python
def solve(xs, k):
    # 元のリストを複製する
    result = list(xs)
    # 並べ替える
    result.sort()
    result.reverse()
    return result
```

## `{"slice": ["take_first_k", "take_last_k"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return xs[:k][-k:]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 切り出しの順に処理する
    return xs[:k][-k:]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return xs[:k][-k:]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 切り出しの順に処理する
    return xs[:k][-k:]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = xs[:k][-k:]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    result: list[int] = xs[:k][-k:]
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = xs[:k][-k:]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    out = xs[:k][-k:]
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    trimmed = xs[:k][-k:]
    return trimmed
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    trimmed = xs[:k][-k:]
    return trimmed
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    picked: list[int] = xs[:k][-k:]
    return picked
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    picked: list[int] = xs[:k][-k:]
    return picked
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    result = result[:k][-k:]
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 必要な範囲を取り出す
    result = result[:k][-k:]
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = list(xs)
    out = out[:k][-k:]
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 必要な範囲を取り出す
    out = out[:k][-k:]
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    trimmed = values[:k][-k:]
    return trimmed
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 必要な範囲を取り出す
    trimmed = values[:k][-k:]
    return trimmed
```

### for_loop_staged_bare

```python
def solve(xs, k):
    out = list(xs)
    cut = out[:k][-k:]
    return cut
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 必要な範囲を取り出す
    cut = out[:k][-k:]
    return cut
```

## `{"slice": ["take_last_k"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return xs[-k:]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 切り出しの順に処理する
    return xs[-k:]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return xs[-k:]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 切り出しの順に処理する
    return xs[-k:]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = xs[-k:]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    result: list[int] = xs[-k:]
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = xs[-k:]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    out = xs[-k:]
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    trimmed = xs[-k:]
    return trimmed
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    trimmed = xs[-k:]
    return trimmed
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    picked: list[int] = xs[-k:]
    return picked
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    picked: list[int] = xs[-k:]
    return picked
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    result = result[-k:]
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 必要な範囲を取り出す
    result = result[-k:]
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = list(xs)
    out = out[-k:]
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 必要な範囲を取り出す
    out = out[-k:]
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    trimmed = values[-k:]
    return trimmed
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 必要な範囲を取り出す
    trimmed = values[-k:]
    return trimmed
```

### for_loop_staged_bare

```python
def solve(xs, k):
    out = list(xs)
    cut = out[-k:]
    return cut
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 必要な範囲を取り出す
    cut = out[-k:]
    return cut
```

## `{"filter": ["even", "positive"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in xs if x % 2 == 0 and x > 0]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 抽出の順に処理する
    return [x for x in xs if x % 2 == 0 and x > 0]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v for v in xs if v % 2 == 0 and v > 0]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 抽出の順に処理する
    return [v for v in xs if v % 2 == 0 and v > 0]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x for x in xs if x % 2 == 0 and x > 0]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = [x for x in xs if x % 2 == 0 and x > 0]
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v for v in xs if v % 2 == 0 and v > 0]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = [v for v in xs if v % 2 == 0 and v > 0]
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    filtered = [value for value in xs if value % 2 == 0 and value > 0]
    return filtered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value % 2 == 0 and value > 0]
    return filtered
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    kept: list[int] = [x for x in xs if x % 2 == 0 and x > 0]
    return kept
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    kept: list[int] = [x for x in xs if x % 2 == 0 and x > 0]
    return kept
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        if x % 2 == 0 and x > 0:
            result.append(x)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    result: list[int] = []
    for x in xs:
        if x % 2 == 0 and x > 0:
            result.append(x)
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        if v % 2 == 0 and v > 0:
            out.append(v)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    out = []
    for v in xs:
        if v % 2 == 0 and v > 0:
            out.append(v)
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0 and value > 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 条件に合う要素だけを残す
    filtered: list[int] = []
    for value in xs:
        if value % 2 == 0 and value > 0:
            filtered.append(value)
    return filtered
```

### for_loop_staged_bare

```python
def solve(xs, k):
    sel = []
    for v in xs:
        if v % 2 == 0 and v > 0:
            sel.append(v)
    return sel
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    sel = []
    for v in xs:
        if v % 2 == 0 and v > 0:
            sel.append(v)
    return sel
```

### condition_swapped

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in xs if x > 0 and x % 2 == 0]
```

## `{"order": "ascending"}`

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

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    reordered = sorted(values)
    return reordered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 並べ替える
    reordered = sorted(values)
    return reordered
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

## `{"slice": ["step_2"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return xs[::2]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 切り出しの順に処理する
    return xs[::2]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return xs[::2]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 切り出しの順に処理する
    return xs[::2]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = xs[::2]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    result: list[int] = xs[::2]
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = xs[::2]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    out = xs[::2]
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    trimmed = xs[::2]
    return trimmed
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    trimmed = xs[::2]
    return trimmed
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    picked: list[int] = xs[::2]
    return picked
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 必要な範囲を取り出す
    picked: list[int] = xs[::2]
    return picked
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    result = result[::2]
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 必要な範囲を取り出す
    result = result[::2]
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = list(xs)
    out = out[::2]
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 必要な範囲を取り出す
    out = out[::2]
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    trimmed = values[::2]
    return trimmed
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 必要な範囲を取り出す
    trimmed = values[::2]
    return trimmed
```

### for_loop_staged_bare

```python
def solve(xs, k):
    out = list(xs)
    cut = out[::2]
    return cut
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 必要な範囲を取り出す
    cut = out[::2]
    return cut
```

## `{"order": "ascending", "slice": ["take_first_k"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted(xs)[:k]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替え→切り出しの順に処理する
    return sorted(xs)[:k]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted(xs)[:k]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 並べ替え→切り出しの順に処理する
    return sorted(xs)[:k]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = sorted(xs)
    result = result[:k]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    result: list[int] = sorted(xs)
    # 必要な範囲を取り出す
    result = result[:k]
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = sorted(xs)
    out = out[:k]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    out = sorted(xs)
    # 必要な範囲を取り出す
    out = out[:k]
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    reordered = sorted(xs)
    trimmed = reordered[:k]
    return trimmed
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 並べ替える
    reordered = sorted(xs)
    # 必要な範囲を取り出す
    trimmed = reordered[:k]
    return trimmed
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    ordered: list[int] = sorted(xs)
    picked = ordered[:k]
    return picked
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    ordered: list[int] = sorted(xs)
    # 必要な範囲を取り出す
    picked = ordered[:k]
    return picked
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    result.sort()
    result = result[:k]
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 並べ替える
    result.sort()
    # 必要な範囲を取り出す
    result = result[:k]
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = list(xs)
    out.sort()
    out = out[:k]
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    out.sort()
    # 必要な範囲を取り出す
    out = out[:k]
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    reordered = sorted(values)
    trimmed = reordered[:k]
    return trimmed
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 並べ替える
    reordered = sorted(values)
    # 必要な範囲を取り出す
    trimmed = reordered[:k]
    return trimmed
```

### for_loop_staged_bare

```python
def solve(xs, k):
    out = list(xs)
    srt = sorted(out)
    cut = srt[:k]
    return cut
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    srt = sorted(out)
    # 必要な範囲を取り出す
    cut = srt[:k]
    return cut
```

## `{"order": "ascending", "slice": ["take_first_k", "take_last_k"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted(xs)[:k][-k:]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替え→切り出しの順に処理する
    return sorted(xs)[:k][-k:]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted(xs)[:k][-k:]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 並べ替え→切り出しの順に処理する
    return sorted(xs)[:k][-k:]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = sorted(xs)
    result = result[:k][-k:]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    result: list[int] = sorted(xs)
    # 必要な範囲を取り出す
    result = result[:k][-k:]
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = sorted(xs)
    out = out[:k][-k:]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 並べ替える
    out = sorted(xs)
    # 必要な範囲を取り出す
    out = out[:k][-k:]
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    reordered = sorted(xs)
    trimmed = reordered[:k][-k:]
    return trimmed
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 並べ替える
    reordered = sorted(xs)
    # 必要な範囲を取り出す
    trimmed = reordered[:k][-k:]
    return trimmed
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    ordered: list[int] = sorted(xs)
    picked = ordered[:k][-k:]
    return picked
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 並べ替える
    ordered: list[int] = sorted(xs)
    # 必要な範囲を取り出す
    picked = ordered[:k][-k:]
    return picked
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = list(xs)
    result.sort()
    result = result[:k][-k:]
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    result: list[int] = list(xs)
    # 並べ替える
    result.sort()
    # 必要な範囲を取り出す
    result = result[:k][-k:]
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = list(xs)
    out.sort()
    out = out[:k][-k:]
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    out.sort()
    # 必要な範囲を取り出す
    out = out[:k][-k:]
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    reordered = sorted(values)
    trimmed = reordered[:k][-k:]
    return trimmed
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 並べ替える
    reordered = sorted(values)
    # 必要な範囲を取り出す
    trimmed = reordered[:k][-k:]
    return trimmed
```

### for_loop_staged_bare

```python
def solve(xs, k):
    out = list(xs)
    srt = sorted(out)
    cut = srt[:k][-k:]
    return cut
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 元のリストを複製する
    out = list(xs)
    # 並べ替える
    srt = sorted(out)
    # 必要な範囲を取り出す
    cut = srt[:k][-k:]
    return cut
```

## `{"map": [["add_k"]]}`

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

## `{"order": "reverse"}`

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

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    values: list[int] = list(xs)
    reordered = values[::-1]
    return reordered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 元のリストを複製する
    values: list[int] = list(xs)
    # 並べ替える
    reordered = values[::-1]
    return reordered
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

## `{"map": [["add_k"]], "slice": ["take_first_k"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x + k for x in xs][:k]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 変換→切り出しの順に処理する
    return [x + k for x in xs][:k]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v + k for v in xs][:k]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 変換→切り出しの順に処理する
    return [v + k for v in xs][:k]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x + k for x in xs]
    result = result[:k]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    result: list[int] = [x + k for x in xs]
    # 必要な範囲を取り出す
    result = result[:k]
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v + k for v in xs]
    out = out[:k]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    out = [v + k for v in xs]
    # 必要な範囲を取り出す
    out = out[:k]
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    transformed = [value + k for value in xs]
    trimmed = transformed[:k]
    return trimmed
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 各要素を変換する
    transformed = [value + k for value in xs]
    # 必要な範囲を取り出す
    trimmed = transformed[:k]
    return trimmed
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    mapped: list[int] = [x + k for x in xs]
    picked = mapped[:k]
    return picked
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    mapped: list[int] = [x + k for x in xs]
    # 必要な範囲を取り出す
    picked = mapped[:k]
    return picked
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        result.append(x + k)
    result = result[:k]
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    result: list[int] = []
    for x in xs:
        result.append(x + k)
    # 必要な範囲を取り出す
    result = result[:k]
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        out.append(v + k)
    out = out[:k]
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    out = []
    for v in xs:
        out.append(v + k)
    # 必要な範囲を取り出す
    out = out[:k]
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    transformed: list[int] = []
    for value in xs:
        transformed.append(value + k)
    trimmed = transformed[:k]
    return trimmed
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    transformed: list[int] = []
    for value in xs:
        transformed.append(value + k)
    # 必要な範囲を取り出す
    trimmed = transformed[:k]
    return trimmed
```

### for_loop_staged_bare

```python
def solve(xs, k):
    conv = []
    for v in xs:
        conv.append(v + k)
    cut = conv[:k]
    return cut
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    conv = []
    for v in xs:
        conv.append(v + k)
    # 必要な範囲を取り出す
    cut = conv[:k]
    return cut
```

## `{"map": [["add_k"]], "slice": ["take_first_k", "take_last_k"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x + k for x in xs][:k][-k:]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 変換→切り出しの順に処理する
    return [x + k for x in xs][:k][-k:]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v + k for v in xs][:k][-k:]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 変換→切り出しの順に処理する
    return [v + k for v in xs][:k][-k:]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x + k for x in xs]
    result = result[:k][-k:]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    result: list[int] = [x + k for x in xs]
    # 必要な範囲を取り出す
    result = result[:k][-k:]
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v + k for v in xs]
    out = out[:k][-k:]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    out = [v + k for v in xs]
    # 必要な範囲を取り出す
    out = out[:k][-k:]
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    transformed = [value + k for value in xs]
    trimmed = transformed[:k][-k:]
    return trimmed
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 各要素を変換する
    transformed = [value + k for value in xs]
    # 必要な範囲を取り出す
    trimmed = transformed[:k][-k:]
    return trimmed
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    mapped: list[int] = [x + k for x in xs]
    picked = mapped[:k][-k:]
    return picked
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    mapped: list[int] = [x + k for x in xs]
    # 必要な範囲を取り出す
    picked = mapped[:k][-k:]
    return picked
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        result.append(x + k)
    result = result[:k][-k:]
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    result: list[int] = []
    for x in xs:
        result.append(x + k)
    # 必要な範囲を取り出す
    result = result[:k][-k:]
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        out.append(v + k)
    out = out[:k][-k:]
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    out = []
    for v in xs:
        out.append(v + k)
    # 必要な範囲を取り出す
    out = out[:k][-k:]
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    transformed: list[int] = []
    for value in xs:
        transformed.append(value + k)
    trimmed = transformed[:k][-k:]
    return trimmed
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    transformed: list[int] = []
    for value in xs:
        transformed.append(value + k)
    # 必要な範囲を取り出す
    trimmed = transformed[:k][-k:]
    return trimmed
```

### for_loop_staged_bare

```python
def solve(xs, k):
    conv = []
    for v in xs:
        conv.append(v + k)
    cut = conv[:k][-k:]
    return cut
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    conv = []
    for v in xs:
        conv.append(v + k)
    # 必要な範囲を取り出す
    cut = conv[:k][-k:]
    return cut
```

## `{"map": [["sub_k"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x - k for x in xs]
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 変換の順に処理する
    return [x - k for x in xs]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v - k for v in xs]
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 変換の順に処理する
    return [v - k for v in xs]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x - k for x in xs]
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    result: list[int] = [x - k for x in xs]
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v - k for v in xs]
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    out = [v - k for v in xs]
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    transformed = [value - k for value in xs]
    return transformed
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 各要素を変換する
    transformed = [value - k for value in xs]
    return transformed
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    mapped: list[int] = [x - k for x in xs]
    return mapped
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    mapped: list[int] = [x - k for x in xs]
    return mapped
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        result.append(x - k)
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    result: list[int] = []
    for x in xs:
        result.append(x - k)
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        out.append(v - k)
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    out = []
    for v in xs:
        out.append(v - k)
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    transformed: list[int] = []
    for value in xs:
        transformed.append(value - k)
    return transformed
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    transformed: list[int] = []
    for value in xs:
        transformed.append(value - k)
    return transformed
```

### for_loop_staged_bare

```python
def solve(xs, k):
    conv = []
    for v in xs:
        conv.append(v - k)
    return conv
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    conv = []
    for v in xs:
        conv.append(v - k)
    return conv
```

## `{"map": [["add_k"]], "order": "ascending"}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted([x + k for x in xs])
```

### list_comprehension_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 変換→並べ替えの順に処理する
    return sorted([x + k for x in xs])
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted([v + k for v in xs])
```

### list_comprehension_bare_commented

```python
def solve(xs, k):
    # 変換→並べ替えの順に処理する
    return sorted([v + k for v in xs])
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x + k for x in xs]
    result = sorted(result)
    return result
```

### comprehension_steps_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    result: list[int] = [x + k for x in xs]
    # 並べ替える
    result = sorted(result)
    return result
```

### comprehension_steps_bare

```python
def solve(xs, k):
    out = [v + k for v in xs]
    out = sorted(out)
    return out
```

### comprehension_steps_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    out = [v + k for v in xs]
    # 並べ替える
    out = sorted(out)
    return out
```

### comprehension_staged

```python
def solve(xs, k):
    transformed = [value + k for value in xs]
    reordered = sorted(transformed)
    return reordered
```

### comprehension_staged_commented

```python
def solve(xs, k):
    # 各要素を変換する
    transformed = [value + k for value in xs]
    # 並べ替える
    reordered = sorted(transformed)
    return reordered
```

### comprehension_staged_typed

```python
def solve(xs: list[int], k: int) -> list[int]:
    mapped: list[int] = [x + k for x in xs]
    ordered = sorted(mapped)
    return ordered
```

### comprehension_staged_typed_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    mapped: list[int] = [x + k for x in xs]
    # 並べ替える
    ordered = sorted(mapped)
    return ordered
```

### for_loop

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = []
    for x in xs:
        result.append(x + k)
    result.sort()
    return result
```

### for_loop_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    result: list[int] = []
    for x in xs:
        result.append(x + k)
    # 並べ替える
    result.sort()
    return result
```

### for_loop_bare

```python
def solve(xs, k):
    out = []
    for v in xs:
        out.append(v + k)
    out.sort()
    return out
```

### for_loop_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    out = []
    for v in xs:
        out.append(v + k)
    # 並べ替える
    out.sort()
    return out
```

### for_loop_staged

```python
def solve(xs: list[int], k: int) -> list[int]:
    transformed: list[int] = []
    for value in xs:
        transformed.append(value + k)
    reordered = sorted(transformed)
    return reordered
```

### for_loop_staged_commented

```python
def solve(xs: list[int], k: int) -> list[int]:
    # 各要素を変換する
    transformed: list[int] = []
    for value in xs:
        transformed.append(value + k)
    # 並べ替える
    reordered = sorted(transformed)
    return reordered
```

### for_loop_staged_bare

```python
def solve(xs, k):
    conv = []
    for v in xs:
        conv.append(v + k)
    srt = sorted(conv)
    return srt
```

### for_loop_staged_bare_commented

```python
def solve(xs, k):
    # 各要素を変換する
    conv = []
    for v in xs:
        conv.append(v + k)
    # 並べ替える
    srt = sorted(conv)
    return srt
```
