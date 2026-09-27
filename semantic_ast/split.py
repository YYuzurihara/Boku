"""Dedup, stratified train/val/test-set split and leakage check -- all operating at the semantic-AST level, *before* any Japanese
instruction or code variant is generated.

homework.md is explicit that this ordering matters: "意味ASTを分割した後で
言い換えやコード変換を行わないと、同じ問題の表記違いが訓練とテストに混入
するため注意する". Because the split unit here is the whole semantic AST
(never an individual instruction/code sample), every instruction and code
variant generated later from a given AST inherits that AST's split
assignment wholesale, so leakage across the splits can only happen if
the *same* semantic AST is (a) duplicated before splitting, or (b) placed
in two splits at once. ``dedup_by_hash`` prevents (a); ``check_no_leakage``
is a cheap, independent assertion that (b) never happened -- this is the
"意味ASTレベルでtrain/val/testのhashに重複がないかを確認する
(データ漏洩検査)" task-list item.
"""

from __future__ import annotations

import random
from collections import defaultdict
from collections.abc import Callable, Mapping, Sequence
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
    """How the ASTs left after carving out the three test sets are divided
    between training and validation."""

    train: float = 0.9
    val: float = 0.1

    def __post_init__(self) -> None:
        total = self.train + self.val
        if abs(total - 1.0) > 1e-9:
            raise ValueError(f"ratios must sum to 1.0, got {total}")


def _label_key(ast: SemanticAST, label_fn: LabelFn) -> tuple:
    d = label_fn(ast)
    return tuple(sorted(d.items()))


def _partition(
    asts: Sequence[SemanticAST],
    fractions: Mapping[str, float],
    remainder: str,
    seed: int,
    label_fn: LabelFn,
) -> dict[str, list[SemanticAST]]:
    """Split every ``label_fn`` group into ``fractions`` (name -> share of the
    group, taken in mapping order); whatever is left goes to ``remainder``.
    Shared by ``stratified_split`` and ``build_eval_splits``.

    Groups are small (a few ASTs per label), so rounding each group's share
    on its own would round a 5% share to 0 almost everywhere. Instead the
    fractional part is carried from group to group: each group gets the
    floor or ceiling of its share, and every split's total matches its
    fraction of all ASTs to within one."""
    groups: dict[tuple, list[SemanticAST]] = defaultdict(list)
    for ast in asts:
        groups[_label_key(ast, label_fn)].append(ast)

    out: dict[str, list[SemanticAST]] = {name: [] for name in (remainder, *fractions)}
    expected = {name: 0.0 for name in fractions}  # running target per split
    for key, group in groups.items():
        rng = random.Random(repr((seed, key)))
        shuffled = list(group)
        rng.shuffle(shuffled)
        start = len(shuffled)
        # carve from the tail so the remainder keeps the head of the shuffle
        for name, share in reversed(list(fractions.items())):
            expected[name] += len(shuffled) * share
            n = min(max(round(expected[name]) - len(out[name]), 0), start)
            start -= n
            out[name].extend(shuffled[start : start + n])
        out[remainder].extend(shuffled[:start])
    return out


def stratified_split(
    asts: Sequence[SemanticAST],
    ratios: SplitRatios = SplitRatios(),
    seed: int = 0,
    label_fn: LabelFn = default_label_fn,
) -> dict[str, list[SemanticAST]]:
    """Split ``asts`` into train/val, keeping the ``label_fn`` distribution
    (the category sequence of the ops) approximately proportional across
    both splits rather than skewed by chance.

    Each semantic AST is assigned to exactly one split -- this is what
    makes leakage structurally hard to introduce later, per this module's
    docstring.
    """
    return _partition(
        asts, {"val": ratios.val}, "train", seed, label_fn
    )


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


# ---------------------------------------------------------------------------
# homework.md's test sets
# ---------------------------------------------------------------------------
#
# There is no catch-all ``test`` split: every AST held out of training goes to
# exactly one of the three test sets, each of which measures one thing of its
# own. A plain "unseen AST" test would only repeat what all three already
# measure (every test AST is unseen in training).

TRAIN_SPLITS: tuple[str, ...] = ("train", "val")
PARAPHRASE_SPLIT = "test_paraphrase"
COMPOSITIONAL_SPLIT = "test_compositional"
BOUNDARY_SPLIT = "test_boundary"
TEST_SPLITS: tuple[str, ...] = (PARAPHRASE_SPLIT, COMPOSITIONAL_SPLIT, BOUNDARY_SPLIT)
ALL_SPLITS: tuple[str, ...] = (*TRAIN_SPLITS, *TEST_SPLITS)

# Pairs of atomic operations (``SemanticAST.op_tags`` spelling) that never
# occur together in train/val/paraphrase/boundary: every AST containing
# both goes to ``test_compositional``. Each operation still occurs elsewhere
# in train, so the test asks whether the model can combine two skills it has
# only seen apart -- homework.md's example is 偶数抽出 x 降順整列. A pair
# matches in either order (``op_tags`` is order-free). All four are
# cross-category and each holds back 140 of the 14,424 ASTs (554 together).
HOLDOUT_PAIRS: tuple[tuple[str, str], ...] = (
    ("filter:even", "order:descending"),
    ("filter:positive", "order:reverse"),
    ("map:abs", "order:ascending"),
    ("order:ascending", "slice:take_last_k"),
)


@dataclass(frozen=True)
class EvalRatios:
    """Share of the (non-compositional) pool given to each sampled test set.
    ``train``/``val`` are then split by ``SplitRatios`` from what remains."""

    paraphrase: float = 0.05
    boundary: float = 0.05


def matches_holdout(ast: SemanticAST, pairs: Sequence[tuple[str, str]] = HOLDOUT_PAIRS) -> bool:
    tags = set(ast.op_tags())
    return any(a in tags and b in tags for a, b in pairs)


def check_holdout_pairs(
    splits: Mapping[str, Sequence[SemanticAST]],
    pairs: Sequence[tuple[str, str]] = HOLDOUT_PAIRS,
) -> None:
    """Raise ``LeakageError`` unless (a) no held-out pair occurs outside
    ``test_compositional``, and (b) every operation of every pair occurs in
    ``train`` on its own -- otherwise the test would measure an operation the
    model never saw rather than the combination."""
    for name, group in splits.items():
        if name == COMPOSITIONAL_SPLIT:
            continue
        for ast in group:
            if matches_holdout(ast, pairs):
                raise LeakageError(f"{name!r} holds a held-out operation pair: {ast.to_dict()}")
    train_tags = {tag for ast in splits["train"] for tag in ast.op_tags()}
    for a, b in pairs:
        for tag in (a, b):
            if tag not in train_tags:
                raise LeakageError(f"held-out pair ({a}, {b}): {tag} never occurs in train")
    for ast in splits[COMPOSITIONAL_SPLIT]:
        if not matches_holdout(ast, pairs):
            raise LeakageError(f"{COMPOSITIONAL_SPLIT!r} holds an AST with no held-out pair: {ast.to_dict()}")


def build_eval_splits(
    asts: Sequence[SemanticAST],
    ratios: SplitRatios = SplitRatios(),
    eval_ratios: EvalRatios = EvalRatios(),
    holdout_pairs: Sequence[tuple[str, str]] = HOLDOUT_PAIRS,
    seed: int = 0,
    label_fn: LabelFn = default_label_fn,
) -> dict[str, list[SemanticAST]]:
    """Five disjoint groups of semantic ASTs (``ALL_SPLITS``):

    * ``test_compositional`` -- every AST containing a held-out operation pair;
    * ``test_paraphrase`` / ``test_boundary`` -- stratified slices of the rest.
      Their ASTs are rendered with the reserved Japanese templates
      (``ja_generator.template_pools``) and tested with boundary inputs
      (``testcases.generate_boundary_test_cases``) respectively;
    * ``train`` / ``val`` -- what remains, split by ``ratios``.

    The assignment of every AST is fixed by ``seed`` alone, so a caller may
    write out any subset of the test sets (``demo.py --splits``) and each one
    comes out the same as when all are generated together.

    Dedup first, so the groups are disjoint by hash; ``check_no_leakage`` and
    ``check_holdout_pairs`` are run before returning.
    """
    pool = dedup_by_hash(asts)
    held = [ast for ast in pool if matches_holdout(ast, holdout_pairs)]
    rest = [ast for ast in pool if not matches_holdout(ast, holdout_pairs)]

    extras = _partition(
        rest,
        {PARAPHRASE_SPLIT: eval_ratios.paraphrase, BOUNDARY_SPLIT: eval_ratios.boundary},
        "main",
        seed,
        label_fn,
    )
    main = stratified_split(extras.pop("main"), ratios, seed=seed, label_fn=label_fn)
    splits = {**main, **extras, COMPOSITIONAL_SPLIT: held}
    splits = {name: splits[name] for name in ALL_SPLITS}
    check_no_leakage(splits)
    check_holdout_pairs(splits, holdout_pairs)
    return splits
