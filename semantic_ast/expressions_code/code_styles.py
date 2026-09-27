"""Style axes for the structural code transformation (homework.md
「コードの構造的変換」) and the named style catalogue built out of them.

homework.md lists the axes it wants varied:

    内包表記と通常の ``for`` ループ / 一時変数の有無 / 変数名の変更 /
    条件式の順序変更 / ``reverse=True`` と逆順操作 /
    1行の ``return`` と複数行形式 / コメントおよび型注釈の有無

Each of those is one axis below, except 条件式の順序変更: consecutive filters
are joined into one condition in op order, and that order is part of the
AST's identity (schema.py, "Order is identity") -- swapping the two
conditions would spell the *other* AST, so every rendering keeps them in op
order. A ``CodeStyle`` is one point in that space
and carries a *name* -- the ``code_style`` field of homework.md's データ
レコード -- so every generated snippet can be traced back to the exact
combination of axes that produced it, and so selection can balance code
shapes later ("コード形式を均す").

Why the catalogue is the whole grid minus what cannot be spelled
---------------------------------------------------------------
The axes multiply out to 2 x 3 x 3 x 2 x 2 x 2 = 144 combinations, but
``order_spelling`` only says anything about an AST that has a reverse op to
spell (see the tag gate below), which leaves ``form`` x ``temporaries`` x
``names`` x ``annotations`` x ``comments`` = 72 universal points. Six of those
cannot be spelled: ``FORM_LOOP`` with ``TEMP_NONE`` has no loop shape of its
own -- a ``for`` loop needs a list to append to across iterations, so
``_loop_body`` renders it exactly as it renders ``TEMP_REUSED`` and the two
styles would be byte-identical under two ``code_style`` names, which is the
quiet per-style corruption the gates below exist to avoid. That leaves
**30 base points** (3 temporaries x 3 name schemes x 2 annotations for the
comprehension form, 2 x 3 x 2 for the loop form), each emitted with and
without comments: **60 styles**, of which 8 are gated on the AST having
something to comprehend (``NEEDS_ELEMENT``), plus the 2 gated on a reverse op
(``NEEDS_ORDER``). Every semantic AST therefore renders **52 to 62 styles**
(52 for the 155 order/slice-only ASTs, 60 for most, 62 with a reverse op).

The grid is filled rather than sampled because the Japanese side can already
spell hundreds to thousands of distinct instructions per semantic AST, so the
number of (instruction, code) pairs a semantic AST yields is bounded by this
catalogue alone (``data/corpus_generator.py`` pairs one instruction per code).
Every point left applicable differs from every other in the rendered source --
``annotations`` always moves the signature (and the first assignment of each
variable), ``names`` always moves the identifiers, ``comments`` always adds the
category comments -- so no two styles can collapse onto one snippet
(``tests/test_code_styles.py`` checks that over the whole enumeration). The
axis constants stay public so a different catalogue can be assembled without
touching the generator.

Names: the ten oldest styles keep the names they were introduced with
(``list_comprehension`` is the reference rendering, ``codes[0]`` of a saved
record); the rest are named ``{form and temporaries}_{name scheme}_{typed or
bare}`` after the axis values they carry.

Tags ("タグに基づいて複数種類用意する")
--------------------------------------
Some axes only say something about certain semantic ASTs. An alternative
spelling of "reverse" needs a reverse operation to spell ("descending" has one
spelling only: ``sorted(...)[::-1]`` / ``sort()`` + ``reverse()`` is exactly
what ``ascending`` then ``reverse`` renders to, so it would give two ASTs one
code -- see ``code_generator._order_expr``); the 変数名 axis needs a variable
to move, which the ``TEMP_NONE`` comprehension only has when the pipeline
comprehends something. Rendering such a style against an AST that lacks the
feature would produce a byte-identical duplicate of another style's output
under a second ``code_style`` name -- which would quietly corrupt the per-style
balance of the corpus. Each style therefore declares a ``StyleRequirement``
over ``SemanticAST.op_tags()`` / ``SemanticAST.categories()``, and
``styles_for(ast)`` returns only the styles that AST actually exercises.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from dataclasses import dataclass, field, replace
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

# -- axis: reverse=True と逆順操作 -------------------------------------------
ORDER_BUILTIN = "builtin"  # reverse: xs[::-1] / list.reverse()
ORDER_EXPLICIT = "explicit"  # reverse: list(reversed(xs)) / xs = xs[::-1]


@dataclass(frozen=True)
class NameScheme:
    """One 変数名の変更 point: the names a rendered snippet uses.

    ``stages`` is indexed by pipeline category (filter, map, order, slice)
    and is only used by ``TEMP_STAGED`` (a second stage of the same category
    gets a ``_2`` suffix). ``buffer`` is the list a ``for`` loop fills when
    its source is the reused accumulator itself (a loop that runs after
    another stage). No name
    here may collide with a builtin the generated code calls (``sorted``,
    ``list``, ``reversed``, ...) -- ``tests/test_code_styles.py`` checks that.
    """

    name: str
    element: str  # the comprehension / for-loop variable
    result: str  # the accumulator (``TEMP_NONE`` / ``TEMP_REUSED``)
    stages: tuple[str, str, str, str]
    buffer: str


NAMES_DEFAULT = NameScheme(
    name="default",
    element="x",
    result="result",
    stages=("kept", "mapped", "ordered", "picked"),
    buffer="tmp",
)
NAMES_TERSE = NameScheme(
    name="terse",
    element="v",
    result="out",
    stages=("sel", "conv", "srt", "cut"),
    buffer="nxt",
)
NAMES_VERBOSE = NameScheme(
    name="verbose",
    element="value",
    result="values",
    stages=("filtered", "transformed", "reordered", "trimmed"),
    buffer="collected",
)

NAME_SCHEMES: tuple[NameScheme, ...] = (NAMES_DEFAULT, NAMES_TERSE, NAMES_VERBOSE)


@dataclass(frozen=True)
class StyleRequirement:
    """What a semantic AST must contain for a style to be *distinct*.

    Stated over ``SemanticAST.op_tags()`` so the condition is phrased in the
    same vocabulary the rest of the pipeline labels ASTs with.
    """

    any_tags: tuple[str, ...] = ()  # at least one of these tags must be present
    any_categories: tuple[str, ...] = ()  # at least one op of these categories

    def gates(self) -> bool:
        """Whether this requirement rules any semantic AST out at all."""
        return bool(self.any_tags or self.any_categories)

    def satisfied_by(self, ast: SemanticAST) -> bool:
        if self.any_tags and not any(tag in ast.op_tags() for tag in self.any_tags):
            return False
        if self.any_categories and not any(c in ast.categories() for c in self.any_categories):
            return False
        return True


# A reverse operation has to exist before it can be spelled a second way.
NEEDS_ORDER = StyleRequirement(any_tags=("order:reverse",))

# The comprehension element variable only exists when there is something to
# comprehend: a pipeline of nothing but order and slice ops renders as
# ``sorted(xs)[:k]``, which names nothing. ``TEMP_NONE`` has no accumulator to
# name either, so on such an AST two ``TEMP_NONE`` styles that differ only in
# their name scheme come out byte-identical -- the duplication under two
# ``code_style`` labels that this gate exists to prevent. Every other
# ``temporaries`` value names its accumulator whatever the ops are, so only
# the ``TEMP_NONE`` row needs the gate.
NEEDS_ELEMENT = StyleRequirement(any_categories=("filter", "map"))


@dataclass(frozen=True)
class CodeStyle:
    """One named point in the style space. ``name`` is homework.md's
    ``code_style``; ``requires`` is the tag condition described in the module
    docstring."""

    name: str
    form: str = FORM_COMPREHENSION
    temporaries: str = TEMP_NONE
    names: NameScheme = NAMES_DEFAULT
    order_spelling: str = ORDER_BUILTIN
    annotations: bool = True
    comments: bool = False
    requires: StyleRequirement = field(default_factory=StyleRequirement)

    def applies_to(self, ast: SemanticAST) -> bool:
        return self.requires.satisfied_by(ast)


# The universal base shapes: the whole (form x temporaries x names x
# annotations) grid minus the loop x TEMP_NONE row that has no loop spelling
# of its own (module docstring). Each is distinct from every other on every
# semantic AST it applies to, and each is emitted twice -- without comments and
# with the fixed category-level comments -- so 2 x 30 = 60 styles in all.
# ``list_comprehension`` is first because it is the shape homework.md's worked
# example shows, which makes it the natural "reference" rendering
# (``codes[0]`` of a saved record). Grouped by form and temporaries; within a
# group the three name schemes each appear with and without annotations.
_BASES: tuple[CodeStyle, ...] = (
    # comprehension, no temporaries: one expression, one ``return``
    CodeStyle(name="list_comprehension", form=FORM_COMPREHENSION, temporaries=TEMP_NONE, names=NAMES_DEFAULT, annotations=True),
    CodeStyle(name="list_comprehension_default_bare", form=FORM_COMPREHENSION, temporaries=TEMP_NONE, names=NAMES_DEFAULT, annotations=False, requires=NEEDS_ELEMENT),
    CodeStyle(name="list_comprehension_terse_typed", form=FORM_COMPREHENSION, temporaries=TEMP_NONE, names=NAMES_TERSE, annotations=True, requires=NEEDS_ELEMENT),
    CodeStyle(name="list_comprehension_bare", form=FORM_COMPREHENSION, temporaries=TEMP_NONE, names=NAMES_TERSE, annotations=False),
    CodeStyle(name="list_comprehension_verbose_typed", form=FORM_COMPREHENSION, temporaries=TEMP_NONE, names=NAMES_VERBOSE, annotations=True, requires=NEEDS_ELEMENT),
    CodeStyle(name="list_comprehension_verbose_bare", form=FORM_COMPREHENSION, temporaries=TEMP_NONE, names=NAMES_VERBOSE, annotations=False, requires=NEEDS_ELEMENT),
    # comprehension, one reused accumulator
    CodeStyle(name="comprehension_steps", form=FORM_COMPREHENSION, temporaries=TEMP_REUSED, names=NAMES_DEFAULT, annotations=True),
    CodeStyle(name="comprehension_steps_default_bare", form=FORM_COMPREHENSION, temporaries=TEMP_REUSED, names=NAMES_DEFAULT, annotations=False),
    CodeStyle(name="comprehension_steps_terse_typed", form=FORM_COMPREHENSION, temporaries=TEMP_REUSED, names=NAMES_TERSE, annotations=True),
    CodeStyle(name="comprehension_steps_bare", form=FORM_COMPREHENSION, temporaries=TEMP_REUSED, names=NAMES_TERSE, annotations=False),
    CodeStyle(name="comprehension_steps_verbose_typed", form=FORM_COMPREHENSION, temporaries=TEMP_REUSED, names=NAMES_VERBOSE, annotations=True),
    CodeStyle(name="comprehension_steps_verbose_bare", form=FORM_COMPREHENSION, temporaries=TEMP_REUSED, names=NAMES_VERBOSE, annotations=False),
    # comprehension, one variable per stage
    CodeStyle(name="comprehension_staged_typed", form=FORM_COMPREHENSION, temporaries=TEMP_STAGED, names=NAMES_DEFAULT, annotations=True),
    CodeStyle(name="comprehension_staged_default_bare", form=FORM_COMPREHENSION, temporaries=TEMP_STAGED, names=NAMES_DEFAULT, annotations=False),
    CodeStyle(name="comprehension_staged_terse_typed", form=FORM_COMPREHENSION, temporaries=TEMP_STAGED, names=NAMES_TERSE, annotations=True),
    CodeStyle(name="comprehension_staged_terse_bare", form=FORM_COMPREHENSION, temporaries=TEMP_STAGED, names=NAMES_TERSE, annotations=False),
    CodeStyle(name="comprehension_staged_verbose_typed", form=FORM_COMPREHENSION, temporaries=TEMP_STAGED, names=NAMES_VERBOSE, annotations=True),
    CodeStyle(name="comprehension_staged", form=FORM_COMPREHENSION, temporaries=TEMP_STAGED, names=NAMES_VERBOSE, annotations=False),
    # for loop, one reused accumulator
    CodeStyle(name="for_loop", form=FORM_LOOP, temporaries=TEMP_REUSED, names=NAMES_DEFAULT, annotations=True),
    CodeStyle(name="for_loop_default_bare", form=FORM_LOOP, temporaries=TEMP_REUSED, names=NAMES_DEFAULT, annotations=False),
    CodeStyle(name="for_loop_terse_typed", form=FORM_LOOP, temporaries=TEMP_REUSED, names=NAMES_TERSE, annotations=True),
    CodeStyle(name="for_loop_bare", form=FORM_LOOP, temporaries=TEMP_REUSED, names=NAMES_TERSE, annotations=False),
    CodeStyle(name="for_loop_verbose_typed", form=FORM_LOOP, temporaries=TEMP_REUSED, names=NAMES_VERBOSE, annotations=True),
    CodeStyle(name="for_loop_verbose_bare", form=FORM_LOOP, temporaries=TEMP_REUSED, names=NAMES_VERBOSE, annotations=False),
    # for loop, one variable per stage
    CodeStyle(name="for_loop_staged_default_typed", form=FORM_LOOP, temporaries=TEMP_STAGED, names=NAMES_DEFAULT, annotations=True),
    CodeStyle(name="for_loop_staged_default_bare", form=FORM_LOOP, temporaries=TEMP_STAGED, names=NAMES_DEFAULT, annotations=False),
    CodeStyle(name="for_loop_staged_terse_typed", form=FORM_LOOP, temporaries=TEMP_STAGED, names=NAMES_TERSE, annotations=True),
    CodeStyle(name="for_loop_staged_bare", form=FORM_LOOP, temporaries=TEMP_STAGED, names=NAMES_TERSE, annotations=False),
    CodeStyle(name="for_loop_staged", form=FORM_LOOP, temporaries=TEMP_STAGED, names=NAMES_VERBOSE, annotations=True),
    CodeStyle(name="for_loop_staged_verbose_bare", form=FORM_LOOP, temporaries=TEMP_STAGED, names=NAMES_VERBOSE, annotations=False),
)

COMMENTED_SUFFIX = "_commented"


def _with_comments(styles: Sequence[CodeStyle]) -> tuple[CodeStyle, ...]:
    """Each style followed by its twin that differs only in carrying the
    comments (the コメントの有無 axis)."""
    out: list[CodeStyle] = []
    for style in styles:
        out.append(style)
        out.append(replace(style, name=style.name + COMMENTED_SUFFIX, comments=True))
    return tuple(out)


# Styles that are only distinct on ASTs with a reverse op (see the tag gate
# above). They come last, so the ASTs that exercise the feature get these on
# top of whatever the grid above already gave them.
_GATED: tuple[CodeStyle, ...] = (
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

STYLES: tuple[CodeStyle, ...] = _with_comments(_BASES) + _GATED
UNIVERSAL_STYLE_COUNT = sum(1 for style in STYLES if not style.requires.gates())

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
