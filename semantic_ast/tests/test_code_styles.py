"""Unit tests for code_styles.py -- the style catalogue and the tag gate
that decides which styles a semantic AST actually exercises. Pure stdlib.

Run with: python -m unittest discover -s semantic_ast/tests
"""

from __future__ import annotations

import sys
import unittest
from collections import Counter
from pathlib import Path

_SEMANTIC_AST = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_SEMANTIC_AST))
sys.path.insert(0, str(_SEMANTIC_AST / "expressions_code"))
sys.path.insert(0, str(_SEMANTIC_AST.parent / "sandbox"))

import ast_safety  # noqa: E402  (sandbox/ast_safety.py)

from code_styles import (  # noqa: E402
    COND_AST_ORDER,
    COND_SWAPPED,
    FORM_COMPREHENSION,
    FORM_LOOP,
    NAME_SCHEMES,
    ORDER_BUILTIN,
    ORDER_EXPLICIT,
    STYLES,
    STYLES_BY_NAME,
    TEMP_NONE,
    TEMP_REUSED,
    TEMP_STAGED,
    select_styles,
    styles_for,
)
from generator import enumerate_all  # noqa: E402
from schema import SemanticAST  # noqa: E402


class CatalogueTest(unittest.TestCase):
    def test_names_are_unique(self):
        names = [style.name for style in STYLES]
        self.assertEqual(len(names), len(set(names)))
        self.assertEqual(set(names), set(STYLES_BY_NAME))

    def test_every_axis_value_is_represented(self):
        """homework.md lists the axes it wants varied; a catalogue that never
        takes one of the values silently drops that variation from the whole
        corpus."""
        for axis, values in (
            ("form", (FORM_COMPREHENSION, FORM_LOOP)),
            ("temporaries", (TEMP_NONE, TEMP_REUSED, TEMP_STAGED)),
            ("condition_order", (COND_AST_ORDER, COND_SWAPPED)),
            ("order_spelling", (ORDER_BUILTIN, ORDER_EXPLICIT)),
            ("annotations", (True, False)),
            ("comments", (True, False)),
        ):
            used = {getattr(style, axis) for style in STYLES}
            self.assertEqual(used, set(values), f"axis {axis}: catalogue uses {used}")

    def test_every_name_scheme_is_used(self):
        used = {style.names.name for style in STYLES}
        self.assertEqual(used, {scheme.name for scheme in NAME_SCHEMES})


class NameSchemeTest(unittest.TestCase):
    def test_names_are_identifiers_and_distinct(self):
        for scheme in NAME_SCHEMES:
            names = (scheme.element, scheme.result, *scheme.stages)
            for name in names:
                self.assertTrue(name.isidentifier(), f"{scheme.name}: {name!r}")
            self.assertEqual(len(set(names)), len(names), f"{scheme.name}: duplicate names")

    def test_names_do_not_shadow_the_builtins_generated_code_calls(self):
        """A variable named ``sorted`` or ``list`` would shadow the builtin the
        very next line calls."""
        for scheme in NAME_SCHEMES:
            for name in (scheme.element, scheme.result, *scheme.stages):
                self.assertNotIn(name, ast_safety.ALLOWED_CALL_NAMES, f"{scheme.name}: {name!r}")
                self.assertNotIn(name, ("xs", "k", "solve"), f"{scheme.name}: {name!r}")


class TagGateTest(unittest.TestCase):
    def test_condition_swap_needs_two_predicates(self):
        one = SemanticAST(filters=("even",))
        two = SemanticAST(filters=("even", "ge_k"))
        self.assertNotIn("condition_swapped", [s.name for s in styles_for(one)])
        self.assertIn("condition_swapped", [s.name for s in styles_for(two)])

    def test_alternative_reverse_spelling_needs_an_ordering_op(self):
        for order_op, expected in (("ascending", False), ("descending", True), ("reverse", True), (None, False)):
            ast = SemanticAST(filters=("even",), order_op=order_op)
            names = [style.name for style in styles_for(ast)]
            self.assertEqual("explicit_reverse" in names, expected, f"order_op={order_op}")
            self.assertEqual("for_loop_explicit_reverse" in names, expected, f"order_op={order_op}")

    def test_ungated_styles_apply_to_every_semantic_ast(self):
        ungated = {style.name for style in STYLES if not style.requires.any_tags and not style.requires.min_filters}
        for ast in enumerate_all()[:500]:
            self.assertTrue(ungated <= {style.name for style in styles_for(ast)})


class SelectStylesTest(unittest.TestCase):
    def test_selection_is_deterministic_and_bounded(self):
        ast = SemanticAST(filters=("even", "ge_k"), order_op="descending")
        first = select_styles(ast, 3)
        self.assertEqual(first, select_styles(ast, 3))
        self.assertEqual(len(first), 3)
        self.assertEqual(len(set(style.name for style in first)), 3)

    def test_n_none_or_too_large_returns_every_applicable_style(self):
        ast = SemanticAST(map_ops=(("add_k", None),))
        self.assertEqual(select_styles(ast, None), styles_for(ast))
        self.assertEqual(select_styles(ast, 99), styles_for(ast))
        self.assertEqual(select_styles(ast, 0), ())

    def test_rotation_spreads_the_catalogue_over_many_asts(self):
        """Taking the first n applicable styles would pin every record to the
        head of the catalogue (homework.md: 「コード形式を均す」)."""
        counts = Counter()
        for ast in enumerate_all()[:2000]:
            for style in select_styles(ast, 2):
                counts[style.name] += 1
        ungated = [s.name for s in STYLES if not s.requires.any_tags and not s.requires.min_filters]
        for name in ungated:
            self.assertGreater(counts[name], 0, f"{name} never selected")
        share = [counts[name] for name in ungated]
        self.assertLess(max(share) / min(share), 2.0, f"uneven style usage: {counts}")


if __name__ == "__main__":
    unittest.main()
