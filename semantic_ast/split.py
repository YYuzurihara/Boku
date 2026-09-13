"""Dedup, stratified train/val/test split, leakage check, and per-label
capping -- all operating at the semantic-AST level, *before* any Japanese
instruction or code variant is generated.

homework.md is explicit that this ordering matters: "意味ASTを分割した後で
言い換えやコード変換を行わないと、同じ問題の表記違いが訓練とテストに混入
するため注意する". Because the split unit here is the whole semantic AST
(never an individual instruction/code sample), every instruction and code
variant generated later from a given AST inherits that AST's split
assignment wholesale, so leakage across train/val/test can only happen if
the *same* semantic AST is (a) duplicated before splitting, or (b) placed
in two splits at once. ``dedup_by_hash`` prevents (a); ``check_no_leakage``
is a cheap, independent assertion that (b) never happened -- this is the
"意味ASTレベルでtrain/val/testのhashに重複がないかを確認する
(データ漏洩検査)" task-list item.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from generator import label as default_label_fn
from schema import SemanticAST

LabelFn = Callable[[SemanticAST], dict]


class LeakageError(ValueError):
    """Raised when the same semantic AST (by hash) appears in more than one split."""


def dedup_by_hash(asts: Sequence[SemanticAST]) -> list[SemanticAST]:
    """Drop exact duplicates (same ``semantic_hash``), keeping first occurrence."""
    seen: set[str] = set()
    out: list[SemanticAST] = []
    for ast in asts:
        h = ast.semantic_hash()
        if h not in seen:
            seen.add(h)
            out.append(ast)
    return out


@dataclass(frozen=True)
class SplitRatios:
    train: float = 0.8
    val: float = 0.1
    test: float = 0.1

    def __post_init__(self) -> None:
        total = self.train + self.val + self.test
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"ratios must sum to 1.0, got {total}")


def _label_key(ast: SemanticAST, label_fn: LabelFn) -> tuple:
    d = label_fn(ast)
    return tuple(sorted(d.items()))


def stratified_split(
    asts: Sequence[SemanticAST],
    ratios: SplitRatios = SplitRatios(),
    seed: int = 0,
    label_fn: LabelFn = default_label_fn,
) -> dict[str, list[SemanticAST]]:
    """Split ``asts`` into train/val/test, keeping the ``label_fn``
    distribution (num_categories, which ops are used, ...) approximately
    proportional across all three splits rather than skewed by chance.

    Each semantic AST is assigned to exactly one split -- this is what
    makes leakage structurally hard to introduce later, per this module's
    docstring.
    """
    groups: dict[tuple, list[SemanticAST]] = defaultdict(list)
    for ast in asts:
        groups[_label_key(ast, label_fn)].append(ast)

    splits: dict[str, list[SemanticAST]] = {"train": [], "val": [], "test": []}
    for key, group in groups.items():
        rng = random.Random(repr((seed, key)))
        shuffled = list(group)
        rng.shuffle(shuffled)
        n = len(shuffled)
        n_val = round(n * ratios.val)
        n_test = round(n * ratios.test)
        n_val = min(n_val, n)
        n_test = min(n_test, n - n_val)
        n_train = n - n_val - n_test
        splits["train"].extend(shuffled[:n_train])
        splits["val"].extend(shuffled[n_train : n_train + n_val])
        splits["test"].extend(shuffled[n_train + n_val :])
    return splits


def check_no_leakage(splits: dict[str, list[SemanticAST]]) -> None:
    """Raise ``LeakageError`` if any semantic-AST hash appears in more than
    one split. Call this right after splitting (and again just before
    writing out final JSONL files, in case a later dedup/cap step was
    applied per-split and reintroduced overlap by mistake)."""
    owner: dict[str, str] = {}
    for split_name, split_asts in splits.items():
        for ast in split_asts:
            h = ast.semantic_hash()
            if h in owner and owner[h] != split_name:
                raise LeakageError(
                    f"semantic AST {ast.to_dict()} (hash {h[:12]}...) "
                    f"appears in both {owner[h]!r} and {split_name!r}"
                )
            owner[h] = split_name


def cap_per_label(
    asts: Sequence[SemanticAST],
    max_per_label: int,
    label_fn: LabelFn = default_label_fn,
    seed: int = 0,
) -> list[SemanticAST]:
    """Cap the number of semantic ASTs sharing the same label to
    ``max_per_label`` (homework.md: "均等抽出のためにラベルごとに上限を設
    けておく"), so that e.g. 1-category ASTs don't drown out 3-category
    ones just because there happen to be more of them. Selection within an
    over-represented label is randomized (seeded) rather than
    order-dependent."""
    groups: dict[tuple, list[SemanticAST]] = defaultdict(list)
    for ast in asts:
        groups[_label_key(ast, label_fn)].append(ast)

    out: list[SemanticAST] = []
    for key, group in groups.items():
        if len(group) <= max_per_label:
            out.extend(group)
            continue
        rng = random.Random(repr((seed, key)))
        out.extend(rng.sample(group, max_per_label))
    return out
