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

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted([v * 2 for v in xs if v % 2 == 0 and v >= k])
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x * 2 for x in xs if x % 2 == 0 and x >= k]
    result = sorted(result)
    return result
```

### comprehension_staged

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

### list_comprehension_bare

```python
def solve(xs, k):
    return xs[:k]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = xs[:k]
    return result
```

### comprehension_staged

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

## `{"order": "descending"}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted(xs, reverse=True)
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted(xs, reverse=True)
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = sorted(xs, reverse=True)
    return result
```

### comprehension_staged

```python
def solve(xs, k):
    # 並べ替える
    reordered = sorted(xs, reverse=True)
    return reordered
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

### list_comprehension_bare

```python
def solve(xs, k):
    return xs[:k][-k:]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = xs[:k][-k:]
    return result
```

### comprehension_staged

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    trimmed = xs[:k][-k:]
    return trimmed
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

## `{"slice": ["take_last_k"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return xs[-k:]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return xs[-k:]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = xs[-k:]
    return result
```

### comprehension_staged

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    trimmed = xs[-k:]
    return trimmed
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

## `{"filter": ["even", "positive"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x for x in xs if x % 2 == 0 and x > 0]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v for v in xs if v % 2 == 0 and v > 0]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x for x in xs if x % 2 == 0 and x > 0]
    return result
```

### comprehension_staged

```python
def solve(xs, k):
    # 条件に合う要素だけを残す
    filtered = [value for value in xs if value % 2 == 0 and value > 0]
    return filtered
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

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted(xs)
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = sorted(xs)
    return result
```

### comprehension_staged

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

## `{"slice": ["step_2"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return xs[::2]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return xs[::2]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = xs[::2]
    return result
```

### comprehension_staged

```python
def solve(xs, k):
    # 必要な範囲を取り出す
    trimmed = xs[::2]
    return trimmed
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

## `{"order": "ascending", "slice": ["take_first_k"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted(xs)[:k]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted(xs)[:k]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = sorted(xs)
    result = result[:k]
    return result
```

### comprehension_staged

```python
def solve(xs, k):
    # 並べ替える
    reordered = sorted(xs)
    # 必要な範囲を取り出す
    trimmed = reordered[:k]
    return trimmed
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

## `{"order": "ascending", "slice": ["take_first_k", "take_last_k"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted(xs)[:k][-k:]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted(xs)[:k][-k:]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = sorted(xs)
    result = result[:k][-k:]
    return result
```

### comprehension_staged

```python
def solve(xs, k):
    # 並べ替える
    reordered = sorted(xs)
    # 必要な範囲を取り出す
    trimmed = reordered[:k][-k:]
    return trimmed
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

## `{"map": [["add_k"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x + k for x in xs]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v + k for v in xs]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x + k for x in xs]
    return result
```

### comprehension_staged

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

## `{"order": "reverse"}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return xs[::-1]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return xs[::-1]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = xs[::-1]
    return result
```

### comprehension_staged

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

### list_comprehension_bare

```python
def solve(xs, k):
    return [v + k for v in xs][:k]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x + k for x in xs]
    result = result[:k]
    return result
```

### comprehension_staged

```python
def solve(xs, k):
    # 各要素を変換する
    transformed = [value + k for value in xs]
    # 必要な範囲を取り出す
    trimmed = transformed[:k]
    return trimmed
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

## `{"map": [["add_k"]], "slice": ["take_first_k", "take_last_k"]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x + k for x in xs][:k][-k:]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v + k for v in xs][:k][-k:]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x + k for x in xs]
    result = result[:k][-k:]
    return result
```

### comprehension_staged

```python
def solve(xs, k):
    # 各要素を変換する
    transformed = [value + k for value in xs]
    # 必要な範囲を取り出す
    trimmed = transformed[:k][-k:]
    return trimmed
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

## `{"map": [["sub_k"]]}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return [x - k for x in xs]
```

### list_comprehension_bare

```python
def solve(xs, k):
    return [v - k for v in xs]
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x - k for x in xs]
    return result
```

### comprehension_staged

```python
def solve(xs, k):
    # 各要素を変換する
    transformed = [value - k for value in xs]
    return transformed
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

## `{"map": [["add_k"]], "order": "ascending"}`

### list_comprehension

```python
def solve(xs: list[int], k: int) -> list[int]:
    return sorted([x + k for x in xs])
```

### list_comprehension_bare

```python
def solve(xs, k):
    return sorted([v + k for v in xs])
```

### comprehension_steps

```python
def solve(xs: list[int], k: int) -> list[int]:
    result: list[int] = [x + k for x in xs]
    result = sorted(result)
    return result
```

### comprehension_staged

```python
def solve(xs, k):
    # 各要素を変換する
    transformed = [value + k for value in xs]
    # 並べ替える
    reordered = sorted(transformed)
    return reordered
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
