"""Style axes for the structural code transformation (homework.md
「コードの構造的変換」) and the named style catalogue built out of them.

homework.md lists the axes it wants varied:

    内包表記と通常の ``for`` ループ / 一時変数の有無 / 変数名の変更 /
    条件式の順序変更 / ``reverse=True`` と逆順操作 /
    1行の ``return`` と複数行形式 / コメントおよび型注釈の有無

Each of those is one axis below. A ``CodeStyle`` is one point in that space
and carries a *name* -- the ``code_style`` field of homework.md's データ
レコード -- so every generated snippet can be traced back to the exact
combination of axes that produced it, and so selection can balance code
shapes later ("コード形式を均す").

Why a curated catalogue instead of the full product
---------------------------------------------------
The axes multiply out to 2 x 3 x 3 x 2 x 2 x 2 x 2 = 288 combinations, far
more code shapes per semantic AST than the データ規模 table wants (it caps
examples per semantic AST, not per style). Most of those points also differ
only in ways that do not change the *shape* of the code (annotations and
comments toggled on a snippet that is otherwise identical). ``STYLES`` is
therefore a hand-picked spread of ~10 named styles that hits every value of
every axis at least twice, keeps each style recognisable from its name, and
leaves the axis constants public so a different catalogue can be assembled
without touching the generator.

Tags ("タグに基づいて複数種類用意する")
--------------------------------------
Two of the axes only exist for certain semantic ASTs: swapping the order of
a condition needs two predicates to swap, and an alternative spelling of
"descending"/"reverse" needs an ordering operation to spell. Rendering such
a style against an AST that lacks the feature would produce a byte-identical
duplicate of another style's output under a second ``code_style`` name --
which would quietly corrupt the per-style balance of the corpus. Each style
therefore declares a ``StyleRequirement`` over ``SemanticAST.op_tags()``, and
``styles_for(ast)`` returns only the styles that AST actually exercises.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

# schema.py lives one level up (semantic_ast/), which is not on sys.path when
# a module in this directory is imported or run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from schema import SemanticAST  # noqa: E402

# -- axis: 内包表記と通常の for ループ ---------------------------------------
FORM_COMPREHENSION = "comprehension"
FORM_LOOP = "loop"

# -- axis: 一時変数の有無 + 1行の return と複数行形式 -------------------------
# The two axes are one axis in practice: "no temporaries" is exactly what
# makes a single-expression ``return`` possible, and giving every stage its
# own name is what makes the body longest.
TEMP_NONE = "none"  # one expression, one ``return``
TEMP_REUSED = "reused"  # one variable, reassigned once per stage
TEMP_STAGED = "staged"  # a differently named variable per stage

# -- axis: 条件式の順序変更 ---------------------------------------------------
COND_AST_ORDER = "ast_order"
COND_SWAPPED = "swapped"

# -- axis: reverse=True と逆順操作 -------------------------------------------
ORDER_BUILTIN = "builtin"  # sorted(..., reverse=True) / list.reverse()
ORDER_EXPLICIT = "explicit"  # sorted(...)[::-1] / list(reversed(...))


@dataclass(frozen=True)
class NameScheme:
    """One 変数名の変更 point: the names a rendered snippet uses.

    ``stages`` is indexed by pipeline category (filter, map, order, slice)
    and is only used by ``TEMP_STAGED``. No name here may collide with a
    builtin the generated code calls (``sorted``, ``list``, ``reversed``,
    ...) -- ``tests/test_code_styles.py`` checks that.
    """

    name: str
    element: str  # the comprehension / for-loop variable
    result: str  # the accumulator (``TEMP_NONE`` / ``TEMP_REUSED``)
    stages: tuple[str, str, str, str]


NAMES_DEFAULT = NameScheme(
    name="default",
    element="x",
    result="result",
    stages=("kept", "mapped", "ordered", "picked"),
)
NAMES_TERSE = NameScheme(
    name="terse",
    element="v",
    result="out",
    stages=("sel", "conv", "srt", "cut"),
)
NAMES_VERBOSE = NameScheme(
    name="verbose",
    element="value",
    result="values",
    stages=("filtered", "transformed", "reordered", "trimmed"),
)

NAME_SCHEMES: tuple[NameScheme, ...] = (NAMES_DEFAULT, NAMES_TERSE, NAMES_VERBOSE)


@dataclass(frozen=True)
class StyleRequirement:
    """What a semantic AST must contain for a style to be *distinct*.

    Stated over ``SemanticAST.op_tags()`` (plus the filter count, which the
    tags carry as their ``filter:`` prefix) so the condition is phrased in
    the same vocabulary the rest of the pipeline labels ASTs with.
    """

    any_tags: tuple[str, ...] = ()  # at least one of these tags must be present
    min_filters: int = 0

    def satisfied_by(self, ast: SemanticAST) -> bool:
        tags = ast.op_tags()
        if self.any_tags and not any(tag in tags for tag in self.any_tags):
            return False
        return len(ast.filters) >= self.min_filters


# An ordering operation has to exist before it can be spelled a second way.
NEEDS_ORDER = StyleRequirement(any_tags=("order:descending", "order:reverse"))
# ``and`` is commutative and these predicates are side-effect free, so the
# two predicates of a 2-filter AST can be written either way round; with one
# predicate (or none) there is nothing to swap.
NEEDS_TWO_FILTERS = StyleRequirement(min_filters=2)


@dataclass(frozen=True)
class CodeStyle:
    """One named point in the style space. ``name`` is homework.md's
    ``code_style``; ``requires`` is the tag condition described in the module
    docstring."""

    name: str
    form: str = FORM_COMPREHENSION
    temporaries: str = TEMP_NONE
    names: NameScheme = NAMES_DEFAULT
    condition_order: str = COND_AST_ORDER
    order_spelling: str = ORDER_BUILTIN
    annotations: bool = True
    comments: bool = False
    requires: StyleRequirement = field(default_factory=StyleRequirement)

    def applies_to(self, ast: SemanticAST) -> bool:
        return self.requires.satisfied_by(ast)


# The catalogue. ``list_comprehension`` is first because it is the shape
# homework.md's worked example shows, which makes it the natural "reference"
# rendering (``codes[0]`` of a saved record).
STYLES: tuple[CodeStyle, ...] = (
    CodeStyle(
        name="list_comprehension",
        form=FORM_COMPREHENSION,
        temporaries=TEMP_NONE,
        names=NAMES_DEFAULT,
        annotations=True,
    ),
    CodeStyle(
        name="list_comprehension_bare",
        form=FORM_COMPREHENSION,
        temporaries=TEMP_NONE,
        names=NAMES_TERSE,
        annotations=False,
    ),
    CodeStyle(
        name="comprehension_steps",
        form=FORM_COMPREHENSION,
        temporaries=TEMP_REUSED,
        names=NAMES_DEFAULT,
        annotations=True,
    ),
    CodeStyle(
        name="comprehension_staged",
        form=FORM_COMPREHENSION,
        temporaries=TEMP_STAGED,
        names=NAMES_VERBOSE,
        annotations=False,
        comments=True,
    ),
    CodeStyle(
        name="for_loop",
        form=FORM_LOOP,
        temporaries=TEMP_REUSED,
        names=NAMES_DEFAULT,
        annotations=True,
    ),
    CodeStyle(
        name="for_loop_commented",
        form=FORM_LOOP,
        temporaries=TEMP_REUSED,
        names=NAMES_TERSE,
        annotations=False,
        comments=True,
    ),
    CodeStyle(
        name="for_loop_staged",
        form=FORM_LOOP,
        temporaries=TEMP_STAGED,
        names=NAMES_VERBOSE,
        annotations=True,
    ),
    CodeStyle(
        name="condition_swapped",
        form=FORM_COMPREHENSION,
        temporaries=TEMP_NONE,
        names=NAMES_DEFAULT,
        condition_order=COND_SWAPPED,
        annotations=True,
        requires=NEEDS_TWO_FILTERS,
    ),
    CodeStyle(
        name="explicit_reverse",
        form=FORM_COMPREHENSION,
        temporaries=TEMP_NONE,
        names=NAMES_TERSE,
        order_spelling=ORDER_EXPLICIT,
        annotations=False,
        requires=NEEDS_ORDER,
    ),
    CodeStyle(
        name="for_loop_explicit_reverse",
        form=FORM_LOOP,
        temporaries=TEMP_REUSED,
        names=NAMES_DEFAULT,
        order_spelling=ORDER_EXPLICIT,
        annotations=False,
        comments=True,
        requires=NEEDS_ORDER,
    ),
)

STYLES_BY_NAME: dict[str, CodeStyle] = {style.name: style for style in STYLES}


def styles_for(ast: SemanticAST, catalogue: Sequence[CodeStyle] = STYLES) -> tuple[CodeStyle, ...]:
    """The styles of ``catalogue`` that ``ast``'s tags actually exercise, in
    catalogue order."""
    return tuple(style for style in catalogue if style.applies_to(ast))


def select_styles(
    ast: SemanticAST,
    n: Optional[int] = None,
    catalogue: Sequence[CodeStyle] = STYLES,
) -> tuple[CodeStyle, ...]:
    """Up to ``n`` applicable styles for ``ast`` (all of them when ``n`` is
    ``None``), rotated by the semantic hash.

    Always taking the first ``n`` applicable styles would make
    ``list_comprehension`` appear in every record and the tail of the
    catalogue almost never -- the opposite of homework.md's 「コード形式を均
    す」. Rotating the applicable list by a per-AST offset spreads the styles
    evenly while staying deterministic (the offset comes from
    ``semantic_hash``, not the randomized builtin ``hash()``, so it is stable
    across runs and machines -- same convention as demo.py's test seeding).
    """
    applicable = styles_for(ast, catalogue)
    if n is None or n >= len(applicable):
        return applicable
    if n <= 0 or not applicable:
        return ()
    offset = int(ast.semantic_hash()[:8], 16) % len(applicable)
    rotated = applicable[offset:] + applicable[:offset]
    return rotated[:n]
