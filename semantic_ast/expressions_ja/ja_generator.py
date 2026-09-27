"""Combine expression-dictionary entries into one Japanese instruction per
semantic AST (ja_generator_plan.md "2. 組み合わせ型（テンプレート合成規則）").

This is the deterministic half of the two-stage design: the teacher model is
only ever asked for *atomic* expressions (one prompt per dictionary key,
ja_teacher.py), and every semantic AST is turned into Japanese here, by
rule, by sampling one approved expression per primitive and concatenating
the clauses in the AST's op order.

A semantic AST is an ordered sequence of 1-3 atomic ops, repeats allowed
(schema.py). The sentence always tells the ops in exactly that order: two
ASTs that differ only in order are different problems with different code,
so they must get different instructions, and an instruction that told the
ops in another order -- even an order that computes the same function --
would describe the other AST.

Composition rules, from ja_generator_plan.md section 2:

* filter (2.1): each filter op is a clause of its own -- its ADNOMINAL
  fragment substituted into ``frame:filter_verb``'s ``{frag}``. Consecutive
  filters are *not* stacked into one 連体修飾 (「k以上の偶数の要素」):
  stacked modifiers have a natural reading order of their own, which would
  hide the op order the AST fixes.
* map / slice (2.2): a run of consecutive map ops (or slice ops) is an
  ordered chain of ACTION_PAIRs; every op but the last in the chain uses the
  ``te`` form plus the connective ``から`` ("kを加えてから2倍する").
* order (2.3): a single ACTION_PAIR per op, no chaining.
* across clauses (2.4): the last clause uses ``terminal``, every earlier
  one uses ``te``; ``frame:opening`` leads and ``frame:closing`` closes.
* placeholders (2.5): ``k`` stays the literal string ``k``; ``N`` is replaced
  by ``mul_const``'s actual constant.

Decision on ja_generator_plan.md's open question ("読点「、」を表現辞書側の
文字列に含めるか、生成器側で一律付与するか", section 5): the **generator**
inserts ``、`` uniformly between the opening frame and each non-final clause,
and strips one trailing ``、`` off those parts first so a dictionary entry
that happens to end with a comma (frame:opening's prompt asks for exactly
that) does not produce ``、、``. Nothing else about a stored expression is
rewritten -- an odd expression stays odd, visibly, which is the point of the
human approval step.

Sentence types (文型)
--------------------
The rules above are the ``sequential`` type. A single sentence shape that
always walks the ops left to right teaches the model that clause position
*is* the order, so a rendering picks a **sentence type** (``TEMPLATES``),
each of which states the op order explicitly, in a different way:

  ``sequential``  連用連接型  「A-te、B-te、C-terminal」+ closing
  ``ordinal``     順序副詞型  「まずA-te、次にB-te、最後にC-terminal」+ closing
  ``procedure``   手順列挙型  「次の手順で処理する」+ closing +
                              「まず、A-terminal。次に、B-terminal。…」
  ``goal_first``  後段先行型  「Z-terminal」+ closing +
                              「ただし、Z-terminal前に、A-te、…Y-terminalこと。」

``ordinal``/``procedure``/``goal_first`` work on *units* -- one per op, so
a map or slice chain is split into its ops (「まずkを加えて、次に2倍して」)
-- and need at least two of them. The glue they add
(``GLUE``: まず/次に/最後に, 前に, こと, ...) is fixed here, like 「から」:
it is grammar, not vocabulary, and only ever attaches to the two forms the
contract below already guarantees -- a ``terminal`` (終止形 = 連体形, so it
takes 「前に」「こと」「。」 and the closing's noun) and a ``te`` (takes
「、」). A dictionary that satisfies ``contract_problems`` therefore
composes under every type.

Division of labour with the teacher model: the model only ever writes
*atomic* expressions, so every problem that is structural -- a clause that
cannot attach to the next one -- has to be the joining rules' problem, not
the model's. The rules above are stated so that a dictionary meeting the
contract in ``contract_problems`` always composes into grammatical Japanese;
``contract_problems`` names that contract and checks the mechanically
checkable half of it, so a violation is reported against the dictionary
entry instead of showing up as a broken sentence in every AST that uses it.
"""

from __future__ import annotations

import json
import random
import sys
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union

# schema.py lives one level up (semantic_ast/), which is not on sys.path when
# a module in this directory is imported or run directly.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from ja_dictionary import ExpressionDictionary  # noqa: E402
from ja_prompts import ACTION_PAIR, ADNOMINAL, FRAG_PLACEHOLDER, PRIMITIVES, TEXT  # noqa: E402
from schema import AtomicOp, SemanticAST  # noqa: E402

CLAUSE_SEPARATOR = "、"
SENTENCE_END = "。"
CHAIN_CONNECTIVE = "から"  # ja_generator_plan.md 2.2: te形 + から
CONST_PLACEHOLDER = "N"  # ja_generator_plan.md 2.5 (mul_const only)

TERMINAL = "terminal"
TE = "te"

# Sentence types (module docstring). Order matters: a rendering records the
# index into this tuple.
SEQUENTIAL = "sequential"
ORDINAL = "ordinal"
PROCEDURE = "procedure"
GOAL_FIRST = "goal_first"
TEMPLATES: tuple[str, ...] = (SEQUENTIAL, ORDINAL, PROCEDURE, GOAL_FIRST)
MULTI_UNIT_TEMPLATES = frozenset({ORDINAL, PROCEDURE, GOAL_FIRST})

# Fixed glue of the sentence types. Every entry attaches to a terminal / te
# form only as described in the module docstring, so none of them can break
# a join the contract allows.
GLUE: dict[str, tuple[str, ...]] = {
    # ordinal / procedure step markers
    "glue:first": ("まず", "最初に", "はじめに"),
    "glue:middle": ("次に", "続いて", "その後", "それから"),
    "glue:last": ("最後に", "最終的に"),
    # procedure: the 連体 clause the closing frame's noun follows
    "glue:procedure_lead": ("次の手順で処理する", "以下の手順で処理する", "次の順に処理を行う"),
    # procedure: step markers as words (まず、…) or numbers ((1) …)
    "glue:procedure_style": ("words", "numbers"),
    # goal_first: the second sentence that adds the earlier steps
    "glue:goal_lead": ("ただし、", "その際、"),
    "glue:goal_tail": ("こと。", "ようにしてください。"),
}
BEFORE = "前に"

# Categories whose consecutive ops are told as one から-chain (2.2).
CHAIN_CATEGORIES = frozenset({"map", "slice"})


class JaRenderError(ValueError):
    """Raised when a semantic AST cannot be rendered from the dictionary at
    hand (missing key, empty expression list, unusable entry shape)."""


@dataclass(frozen=True)
class ExpressionChoice:
    """Which stored expression was used where -- enough to re-derive the
    sentence from the dictionary, and to tell which dictionary entries a
    saved instruction depends on (needed for the "言い換えテスト" reservation
    described in ja_generator_plan.md section 3)."""

    key: str
    index: int
    form: Optional[str] = None  # "terminal" / "te" for ACTION_PAIR, else None
    arg: Optional[int] = None  # mul_const's constant, substituted for N

    def to_dict(self) -> dict:
        d: dict = {"key": self.key, "index": self.index}
        if self.form is not None:
            d["form"] = self.form
        if self.arg is not None:
            d["arg"] = self.arg
        return d


@dataclass(frozen=True)
class Rendering:
    """One Japanese instruction plus the choices that produced it.
    ``template`` repeats the sentence-type choice in readable form;
    ``narration`` is the op order the sentence tells (always the AST's)."""

    text: str
    choices: tuple[ExpressionChoice, ...]
    template: str = SEQUENTIAL
    narration: tuple[str, ...] = ()

    def to_dict(self) -> dict:
        return {
            "text": self.text,
            "template": self.template,
            "narration": list(self.narration),
            "choices": [c.to_dict() for c in self.choices],
        }


# key -> the expression indices a rendering may draw from; a key that is not
# listed may use any of its expressions.
AllowedIndices = Mapping[str, Sequence[int]]


class _Picker:
    """Samples one expression per key and records what it picked."""

    def __init__(
        self,
        dictionary: ExpressionDictionary,
        rng: random.Random,
        allowed: Optional[AllowedIndices] = None,
    ) -> None:
        self.dictionary = dictionary
        self.rng = rng
        self.allowed = allowed or {}
        self.choices: list[ExpressionChoice] = []

    def _index(self, key: str, n: int, candidates: Optional[Sequence[int]] = None) -> int:
        """Sample an index in ``range(n)``, from ``candidates`` if given,
        and from the ``allowed`` indices of ``key`` if it has any."""
        indices = list(candidates) if candidates is not None else list(range(n))
        allowed = self.allowed.get(key)
        if allowed:
            indices = [i for i in indices if i in allowed]
        if not indices:
            raise JaRenderError(f"{key}: no candidate left to choose from")
        return self.rng.choice(indices) if allowed or candidates is not None else self.rng.randrange(n)

    def _pick(self, key: str) -> tuple[object, int]:
        expressions = self.dictionary.expressions(key)  # raises if key absent
        if not expressions:
            raise JaRenderError(f"expression dictionary entry {key!r} has no expressions")
        index = self._index(key, len(expressions))
        return expressions[index], index

    def choose(self, key: str, options: Sequence, candidates: Optional[Sequence[int]] = None):
        """Pick one of ``options`` (glue, sentence type) and
        record it like an expression, so a replay reproduces it."""
        index = self._index(key, len(options), candidates)
        self.choices.append(ExpressionChoice(key=key, index=index))
        return options[index]

    def glue(self, key: str, exclude: Iterable[str] = ()) -> str:
        options = GLUE[key]
        excluded = set(exclude)
        return self.choose(key, options, [i for i, text in enumerate(options) if text not in excluded])

    def text(self, key: str) -> str:
        """Pick a plain-string expression (ADNOMINAL / TEXT)."""
        expression, index = self._pick(key)
        if not isinstance(expression, str):
            raise JaRenderError(f"{key}[{index}]: expected a string expression, got {type(expression).__name__}")
        self.choices.append(ExpressionChoice(key=key, index=index))
        return expression

    def pair(self, key: str, form: str, arg: Optional[int] = None) -> str:
        """Pick an ACTION_PAIR expression and take one of its two forms."""
        expression, index = self._pick(key)
        if not isinstance(expression, dict) or form not in expression:
            raise JaRenderError(
                f"{key}[{index}]: expected a {{terminal, te}} pair with a {form!r} form, got {expression!r}"
            )
        text = expression[form]
        if arg is not None:
            text = text.replace(CONST_PLACEHOLDER, str(arg))
        self.choices.append(ExpressionChoice(key=key, index=index, form=form, arg=arg))
        return text


def _form(is_last: bool) -> str:
    return TERMINAL if is_last else TE


def _dictionary_key(op: AtomicOp) -> str:
    """The expression-dictionary key of ``op``: its tag, except that
    ``mul_const``'s constant is a placeholder (2.5), not part of the key."""
    return f"{op.category}:{op.name}"


def _render_filter(op: AtomicOp, picker: _Picker, form: str) -> str:
    """ja_generator_plan.md 2.1: the filter's ADNOMINAL fragment substituted
    into the shared filter frame."""
    fragment = picker.text(_dictionary_key(op))
    frame = picker.pair("frame:filter_verb", form)
    return frame.replace(FRAG_PLACEHOLDER, fragment)


def _unit_text(op: AtomicOp, picker: _Picker, form: str) -> str:
    """One op as a clause in ``form`` (``terminal`` / ``te``)."""
    if op.category == "filter":
        return _render_filter(op, picker, form)
    return picker.pair(_dictionary_key(op), form, arg=op.arg)


def _render_chain(ops: Sequence[AtomicOp], picker: _Picker, is_last_clause: bool) -> str:
    """ja_generator_plan.md 2.2: an ordered ACTION_PAIR chain (a run of map /
    slice ops). Non-final links are ``te`` + ``から``; the final link is
    ``terminal`` only if this is also the last clause."""
    parts: list[str] = []
    for position, op in enumerate(ops):
        is_last_op = position == len(ops) - 1
        text = _unit_text(op, picker, _form(is_last_clause and is_last_op))
        if not is_last_op:
            text += CHAIN_CONNECTIVE
        parts.append(text)
    return "".join(parts)


def _clause_groups(ast: SemanticAST) -> list[tuple[AtomicOp, ...]]:
    """``ast.ops`` split into the clauses of the ``sequential`` type: a run of
    consecutive map (or slice) ops is one chain, every other op a clause of
    its own."""
    groups: list[list[AtomicOp]] = []
    for op in ast.ops:
        if groups and op.category in CHAIN_CATEGORIES and groups[-1][-1].category == op.category:
            groups[-1].append(op)
        else:
            groups.append([op])
    return [tuple(group) for group in groups]


def _sentence(text: str) -> str:
    """``text`` as a sentence of its own: one trailing 、/。 dropped, 。 added."""
    return text.rstrip(CLAUSE_SEPARATOR).rstrip(SENTENCE_END) + SENTENCE_END


def _assemble(opening: str, clauses: Sequence[str], closing: str) -> str:
    """ja_generator_plan.md 2.4 + the 読点 decision in this module's docstring.

    The final clause runs straight into the closing frame's noun phrase
    (「…昇順に並べる」+「solve関数を書いてください。」): that juncture is a
    連体修飾, so a 読点 on either side of it would cut the modifier loose from
    the noun it modifies, and both sides are stripped of one.
    """
    leading = [opening, *clauses[:-1]]
    parts = [part.rstrip(CLAUSE_SEPARATOR) for part in leading]
    parts.append(clauses[-1].rstrip(CLAUSE_SEPARATOR))
    return CLAUSE_SEPARATOR.join(parts) + closing.lstrip(CLAUSE_SEPARATOR)


def _step_marker(picker: _Picker, position: int, count: int, used_middle: list[str]) -> str:
    """まず / 次に / 最後に for unit ``position`` of ``count``; middle markers
    are not repeated within one sentence while unused ones remain."""
    if position == 0:
        return picker.glue("glue:first")
    if position == count - 1:
        return picker.glue("glue:last")
    exclude = used_middle if len(used_middle) < len(GLUE["glue:middle"]) else ()
    marker = picker.glue("glue:middle", exclude=exclude)
    used_middle.append(marker)
    return marker


def _sequential(ast: SemanticAST, picker: _Picker, units: Sequence[AtomicOp], opening: str) -> str:
    """連用連接型: 「A-te、B-te、C-terminal」+ closing (ja_generator_plan.md 2.4)."""
    groups = _clause_groups(ast)
    clauses = [
        _render_chain(group, picker, is_last_clause=(i == len(groups) - 1))
        for i, group in enumerate(groups)
    ]
    return _assemble(opening, clauses, picker.text("frame:closing"))


def _ordinal(ast: SemanticAST, picker: _Picker, units: Sequence[AtomicOp], opening: str) -> str:
    """順序副詞型: 「まずA-te、次にB-te、最後にC-terminal」+ closing."""
    used_middle: list[str] = []
    clauses = []
    for i, unit in enumerate(units):
        is_last = i == len(units) - 1
        marker = _step_marker(picker, i, len(units), used_middle)
        clauses.append(marker + _unit_text(unit, picker, _form(is_last)))
    return _assemble(opening, clauses, picker.text("frame:closing"))


def _procedure(ast: SemanticAST, picker: _Picker, units: Sequence[AtomicOp], opening: str) -> str:
    """手順列挙型: 「次の手順で処理する」+ closing, then one sentence per unit
    (「まず、A。次に、B。…」 or 「(1) A。(2) B。…」)."""
    lead = picker.glue("glue:procedure_lead")
    head = _assemble(opening, [lead], picker.text("frame:closing"))
    numbered = picker.glue("glue:procedure_style") == "numbers"
    used_middle: list[str] = []
    steps = []
    for i, unit in enumerate(units):
        marker = f"({i + 1}) " if numbered else _step_marker(picker, i, len(units), used_middle) + CLAUSE_SEPARATOR
        steps.append(marker + _sentence(_unit_text(unit, picker, TERMINAL)))
    return head + "".join(steps)


def _goal_first(ast: SemanticAST, picker: _Picker, units: Sequence[AtomicOp], opening: str) -> str:
    """後段先行型: the last unit first, 「Z-terminal」+ closing, then the
    earlier units in a second sentence: 「ただし、Z-terminal前に、A-te、…、
    Y-terminalこと。」. 「前に」 is what keeps the order explicit although Z is
    read before A."""
    *earlier, final = units
    final_text = _unit_text(final, picker, TERMINAL).rstrip(CLAUSE_SEPARATOR)
    head = _assemble(opening, [final_text], picker.text("frame:closing"))
    lead = picker.glue("glue:goal_lead")
    clauses = [
        _unit_text(unit, picker, _form(i == len(earlier) - 1)).rstrip(CLAUSE_SEPARATOR)
        for i, unit in enumerate(earlier)
    ]
    tail = picker.glue("glue:goal_tail")
    return head + lead + final_text + BEFORE + CLAUSE_SEPARATOR + CLAUSE_SEPARATOR.join(clauses) + tail


_TEMPLATE_BUILDERS = {
    SEQUENTIAL: _sequential,
    ORDINAL: _ordinal,
    PROCEDURE: _procedure,
    GOAL_FIRST: _goal_first,
}


def applicable_templates(ast: SemanticAST) -> tuple[str, ...]:
    """The sentence types ``ast`` can be told in: the unit-based ones need
    at least two units (ops)."""
    return tuple(t for t in TEMPLATES if t not in MULTI_UNIT_TEMPLATES or ast.num_ops() >= 2)


def _compose(
    ast: SemanticAST,
    picker: _Picker,
    templates: Optional[Sequence[str]] = None,
) -> Rendering:
    """Shared by ``render`` and ``render_from_record``: sentence type, then
    the sentence itself, every choice through ``picker``."""
    usable = applicable_templates(ast)
    if templates is not None:
        unknown = set(templates) - set(TEMPLATES)
        if unknown:
            raise JaRenderError(f"unknown sentence type(s): {sorted(unknown)}")
        usable = tuple(t for t in usable if t in templates)
    if not usable:
        raise JaRenderError(f"none of the sentence types {templates} applies to {ast.to_dict()}")
    template = picker.choose("template", TEMPLATES, [TEMPLATES.index(t) for t in usable])

    opening = picker.text("frame:opening")
    text = _TEMPLATE_BUILDERS[template](ast, picker, ast.ops, opening)
    return Rendering(text=text, choices=tuple(picker.choices), template=template, narration=ast.tags())


def render(
    ast: SemanticAST,
    dictionary: ExpressionDictionary,
    rng: Optional[random.Random] = None,
    allowed: Optional[AllowedIndices] = None,
    templates: Optional[Sequence[str]] = None,
) -> Rendering:
    """Render one Japanese instruction for ``ast`` by sampling the dictionary
    (restricted to ``allowed`` indices per key, if given) and a sentence type
    (from ``templates``, default all that apply). The ops are always told in
    ``ast.ops`` order."""
    rng = rng or random.Random()
    picker = _Picker(dictionary, rng, allowed)
    return _compose(ast, picker, templates)


def seed_for(ast: SemanticAST, seed: int = 0) -> int:
    """Per-AST seed derived from the semantic hash (not the randomized
    builtin ``hash()``), so renderings are reproducible across runs and
    machines -- same convention as demo.py's test-case seeding."""
    return seed ^ int(ast.semantic_hash()[:8], 16)


def render_variants(
    ast: SemanticAST,
    dictionary: ExpressionDictionary,
    n: int = 1,
    seed: int = 0,
    max_attempts: Optional[int] = None,
    allowed: Optional[AllowedIndices] = None,
    templates: Optional[Sequence[str]] = None,
) -> list[Rendering]:
    """Up to ``n`` *distinct* instructions for one semantic AST
    (``allowed`` / ``templates`` as in ``render``).

    Distinctness is by sentence text, so two different expression choices
    that happen to spell the same sentence count once. With a small
    dictionary the number of distinct sentences can be lower than ``n``;
    this returns what it found rather than looping forever.
    """
    rng = random.Random(seed_for(ast, seed))
    attempts = max_attempts if max_attempts is not None else max(20, n * 10)
    out: list[Rendering] = []
    seen: set[str] = set()
    for _ in range(attempts):
        if len(out) >= n:
            break
        rendering = render(ast, dictionary, rng, allowed, templates)
        if rendering.text in seen:
            continue
        seen.add(rendering.text)
        out.append(rendering)
    return out


# ---------------------------------------------------------------------------
# 言い換えテスト: templates reserved away from training
# ---------------------------------------------------------------------------

PARAPHRASE_RATIO = 0.25

# Keys every split draws on in full. The 言い換え being tested is the wording of
# the *operations*, and the frames are the boilerplate around them, so reserving
# a quarter of the frames buys no paraphrase signal while it multiplies down how
# many distinct sentences a split can spell: a reserved quarter of 11 openings
# and 5 closings leaves a one-op AST 3 x 1 x (its op's reserved wordings)
# sentences, far short of the 20+ codes that AST has in expressions_code/.
SHARED_KEY_PREFIX = "frame:"


@dataclass(frozen=True)
class TemplatePools:
    """How each dictionary key's expressions are divided between the training
    splits and the 言い換えテスト (ja_generator_plan.md section 3).

    ``train`` and ``paraphrase`` map a key to the indices it may use in the
    respective splits. A key that is not divided -- a ``frame:`` key, or one
    with a single expression -- is absent from both mappings (so both may use
    it) and listed in ``shared_keys`` so a report can say how much of the
    sentence is genuinely new."""

    train: dict[str, tuple[int, ...]]
    paraphrase: dict[str, tuple[int, ...]]
    shared_keys: tuple[str, ...]


def template_pools(
    dictionary: ExpressionDictionary, ratio: float = PARAPHRASE_RATIO, seed: int = 0
) -> TemplatePools:
    """Reserve ``ratio`` of every operation key's expressions (at least one,
    never all) for the paraphrase test. The choice is a seeded shuffle of the
    indices, so it does not depend on the order the human reviewer left them
    in. ``SHARED_KEY_PREFIX`` keys and keys with a single expression are not
    divided at all."""
    train: dict[str, tuple[int, ...]] = {}
    paraphrase: dict[str, tuple[int, ...]] = {}
    shared: list[str] = []
    for key in dictionary.keys():
        n = len(dictionary.expressions(key))
        if n < 2 or key.startswith(SHARED_KEY_PREFIX):
            shared.append(key)
            continue
        indices = list(range(n))
        random.Random(repr((seed, key))).shuffle(indices)
        n_reserved = min(max(1, round(n * ratio)), n - 1)
        paraphrase[key] = tuple(sorted(indices[:n_reserved]))
        train[key] = tuple(sorted(indices[n_reserved:]))
    return TemplatePools(train=train, paraphrase=paraphrase, shared_keys=tuple(shared))


def pool_violations(rendering_choices: Iterable[Mapping], pool: AllowedIndices) -> list[str]:
    """Choices (as stored in a record's ``renderings``) that fall outside
    ``pool`` -- the check that a saved training sentence never used a reserved
    template and a paraphrase sentence used nothing but reserved ones."""
    return [
        f"{c['key']}[{c['index']}]"
        for c in rendering_choices
        if c["key"] in pool and c["index"] not in pool[c["key"]]
    ]


def leftover_placeholders(text: str) -> list[str]:
    """Placeholders that should have been substituted but are still in the
    sentence. ``{frag}`` means a filter frame was used without substitution;
    ``k`` is intentionally left literal (2.5) and ``N`` is unrecoverable once
    rendered, so neither is reported here."""
    return [FRAG_PLACEHOLDER] if FRAG_PLACEHOLDER in text else []


# ---------------------------------------------------------------------------
# The contract the joining rules depend on
# ---------------------------------------------------------------------------
#
# Each rule below is a *join* rule: break it and the sentences this module
# builds are ungrammatical however good the dictionary otherwise is, because
# the renderer glues the neighbouring clause on with nothing in between.
# Judgement calls are deliberately absent -- a clumsy paraphrase, a closing
# that asks the reader to *run* solve rather than write it, a fragment that is
# fine alone but stiff when stacked. Those belong to the prompts
# (THIRD_PARTY.md) and to the human approval step, so a clean report means
# "nothing here can break a join", not "this dictionary is good Japanese".

# A noun at the end of an expression collides with the noun the renderer
# writes next: 「要素」 after a filter fragment, 「solve関数」 after a terminal.
TRAILING_NOUNS: tuple[str, ...] = (
    "要素", "もの", "物", "値", "数", "こと", "事", "とき", "操作", "処理", "動作", "方法", "行為",
)

# frame:filter_verb supplies the narrowing itself (「{frag}要素だけを残す」), so
# a fragment carrying it too says it twice: 「k以上の要素だけ」 + 「要素を抽出する」.
NARROWING_MARKERS: tuple[str, ...] = ("だけ", "のみ", "を残す", "を抽出", "を選ぶ")

# A 連体修飾 cannot end in a case particle, so a fragment ending in one does
# not attach to the noun the frame puts after it: 「k以上であるものから」 +
# 「要素だけを選ぶ」. 「の」 is excluded -- it is *the* adnominal particle.
TRAILING_PARTICLES: tuple[str, ...] = ("から", "まで", "より", "へ", "に", "を", "と", "は", "が", "で")

# frame:opening is picked independently of which category happens to come
# first, so an opening that governs the next clause only works for one of
# them: 「整数リストxsから、」 wants something taken *out of* xs, which reads
# fine before 「偶数の要素だけを残す」 and wrong before 「kを加える」.
NON_NEUTRAL_OPENING_ENDINGS: tuple[str, ...] = ("から", "より")


def _ends_with(text: str, suffixes: Sequence[str]) -> Optional[str]:
    return next((s for s in suffixes if text.endswith(s)), None)


def _adnominal_contract(where: str, expr: str) -> list[str]:
    problems = []
    noun = _ends_with(expr, TRAILING_NOUNS)
    if noun:
        problems.append(
            f"{where}: ends with the noun 「{noun}」, which runs straight into the filter "
            f"frame's own noun (「{expr}要素だけを残す」)"
        )
    particle = _ends_with(expr, TRAILING_PARTICLES)
    if particle and not noun:
        problems.append(
            f"{where}: ends with the case particle 「{particle}」, so it is not a 連体修飾 and "
            f"does not attach to the frame's noun (「{expr}要素だけを残す」)"
        )
    marker = next((m for m in NARROWING_MARKERS if m in expr), None)
    if marker:
        problems.append(
            f"{where}: contains 「{marker}」, but the filter frame already supplies the "
            f"narrowing -- the fragment only states the condition"
        )
    return problems


def _action_pair_contract(where: str, key: str, expr: dict) -> list[str]:
    terminal, te = expr.get(TERMINAL), expr.get(TE)
    if not isinstance(terminal, str) or not isinstance(te, str):
        return []  # shape problem: ExpressionDictionary.validate() reports it
    problems = []
    noun = _ends_with(terminal, TRAILING_NOUNS)
    if noun:
        problems.append(
            f"{where}.terminal: ends with the noun 「{noun}」; the closing frame's noun "
            f"phrase follows it directly (「{terminal}solve関数を書いてください。」)"
        )
    elif terminal.endswith(("て", "で")):
        # a て形 in the terminal slot: 「先頭からk個を取得して」 cannot head the
        # 連体修飾 the closing frame's noun phrase needs
        problems.append(
            f"{where}.terminal: is a て形, not a 終止形, so the closing frame's noun phrase "
            f"cannot attach to it (「{terminal}solve関数を書いてください。」)"
        )
    if key == "frame:filter_verb":
        # the frame contributes the verb, the fragment contributes the
        # condition; text in front of {frag} is a second, contradictory copy
        # of the condition (「k以上の偶数の{frag}要素だけを残す」)
        for form, text in ((TERMINAL, terminal), (TE, te)):
            if FRAG_PLACEHOLDER in text and not text.startswith(FRAG_PLACEHOLDER):
                problems.append(
                    f"{where}.{form}: has text in front of {FRAG_PLACEHOLDER} "
                    f"(「{text.split(FRAG_PLACEHOLDER)[0]}」), which the renderer would read as a "
                    f"second condition in front of the one it substitutes"
                )
    if te == terminal:
        problems.append(f"{where}.te: identical to terminal, so it cannot carry a following clause")
    if key.startswith(("map:", "slice:")):
        if te.endswith(CHAIN_CONNECTIVE):
            problems.append(
                f"{where}.te: already ends with the chain connective 「{CHAIN_CONNECTIVE}」, "
                f"which the renderer adds itself (「{te}{CHAIN_CONNECTIVE}」)"
            )
        elif not te.endswith(("て", "で")):
            problems.append(
                f"{where}.te: not a て形, so the chain connective cannot attach to it "
                f"(「{te}{CHAIN_CONNECTIVE}」)"
            )
    return problems


def _frame_contract(where: str, key: str, expr: str) -> list[str]:
    problems = []
    body = expr.rstrip().rstrip(CLAUSE_SEPARATOR)
    if key == "frame:opening":
        if body.endswith("。"):
            problems.append(f"{where}: ends the sentence with 「。」, but clauses follow it")
        ending = _ends_with(body, NON_NEUTRAL_OPENING_ENDINGS)
        if ending:
            problems.append(
                f"{where}: ends with 「{ending}」, which presupposes that something is taken "
                f"out of xs; the opening has to read as well before 「kを加える」 as before "
                f"「偶数の要素だけを残す」"
            )
    elif key == "frame:closing":
        if not expr.rstrip().endswith("。"):
            problems.append(f"{where}: does not end with 「。」, but it ends the sentence")
        if "solve" not in expr:
            problems.append(
                f"{where}: does not name solve; the closing carries the noun phrase that the "
                f"last clause modifies"
            )
    return problems


def contract_problems(dictionary: ExpressionDictionary) -> list[str]:
    """Entries the joining rules cannot combine into grammatical Japanese,
    as human-readable strings (empty list == everything composes).

    Complements ``ExpressionDictionary.validate()``, which checks the file's
    *shape*: this checks what the shape cannot -- whether a well-formed entry
    attaches to the clause the renderer will put next to it. Nothing is
    repaired, for the reason ja_teacher.py saves broken responses verbatim:
    editing the dictionary is the human reviewer's call.
    """
    problems: list[str] = []
    for key in dictionary.keys():
        spec = PRIMITIVES.get(key)
        if spec is None:
            continue  # unknown key: validate() reports it
        for i, expr in enumerate(dictionary.entries[key].get("expressions") or []):
            where = f"{key}[{i}]"
            if spec.slot_type == ADNOMINAL and isinstance(expr, str):
                problems.extend(_adnominal_contract(where, expr))
            elif spec.slot_type == ACTION_PAIR and isinstance(expr, dict):
                problems.extend(_action_pair_contract(where, key, expr))
            elif spec.slot_type == TEXT and isinstance(expr, str):
                problems.extend(_frame_contract(where, key, expr))
    return problems


# ---------------------------------------------------------------------------
# Saving the combined expressions
# ---------------------------------------------------------------------------


def instruction_record(
    ast: SemanticAST,
    renderings: Sequence[Rendering],
    dictionary: ExpressionDictionary,
    spec_id: Optional[str] = None,
    seed: int = 0,
) -> dict:
    """One JSONL record: the semantic AST, its rendered instructions, and the
    provenance needed to reproduce them (dictionary hash + seed + the exact
    expression indices used).

    Field names line up with homework.md's データレコード example, so these
    records can be joined onto demo.py's ``out/ast_{split}.jsonl`` by
    ``semantic_hash`` / ``spec_id``.
    """
    record: dict = {
        "semantic_ast": ast.to_dict(),
        "semantic_hash": ast.semantic_hash(),
        "instruction_ja": [r.text for r in renderings],
        "renderings": [r.to_dict() for r in renderings],
        "dictionary_sha256": dictionary.content_sha256(),
        "render_seed": seed,
    }
    if spec_id is not None:
        record = {"spec_id": spec_id, **record}
    return record


def save_instructions(records: Iterable[dict], path: Union[str, Path]) -> Path:
    """Write instruction records as JSONL (UTF-8, unescaped Japanese)."""
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as f:
        for record in records:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
    return path


def load_instructions(path: Union[str, Path]) -> list[dict]:
    """Read back what ``save_instructions`` wrote (used by ja_demo.py to
    verify the round trip)."""
    path = Path(path)
    with path.open(encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]


def render_from_record(record: dict, dictionary: ExpressionDictionary) -> list[str]:
    """Re-derive the sentences of a saved record from its stored choices.

    A pure replay -- no sampling -- so it doubles as a check that the saved
    instruction really is reproducible from (dictionary, choices) alone.
    """
    ast = SemanticAST.from_dict(record["semantic_ast"])
    out: list[str] = []
    for rendering in record["renderings"]:
        picker = _ReplayPicker(dictionary, list(rendering["choices"]))
        out.append(_compose(ast, picker).text)
    return out


class _ReplayPicker(_Picker):
    """A ``_Picker`` that replays recorded choices instead of sampling."""

    def __init__(self, dictionary: ExpressionDictionary, queue: list[dict]) -> None:
        super().__init__(dictionary, random.Random(0))
        self.queue = queue

    def _index(self, key: str, n: int, candidates: Optional[Sequence[int]] = None) -> int:
        if not self.queue:
            raise JaRenderError(f"replay ran out of recorded choices at key {key!r}")
        choice = self.queue.pop(0)
        if choice["key"] != key:
            raise JaRenderError(f"replay expected key {choice['key']!r}, renderer asked for {key!r}")
        index = choice["index"]
        if not 0 <= index < n:
            raise JaRenderError(
                f"{key}: recorded index {index} is out of range for {n} options "
                f"(dictionary or renderer changed since the record was written?)"
            )
        return index
