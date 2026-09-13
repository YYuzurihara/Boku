"""Unit tests for ast_safety.py. Pure stdlib, no Docker required.

Run with: python -m unittest discover -s sandbox/tests
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import ast_safety  # noqa: E402


class VerifyStaticAcceptsValidSolve(unittest.TestCase):
    def test_list_comprehension_style(self):
        code = (
            "def solve(xs: list[int], k: int) -> list[int]:\n"
            "    return sorted(x * 2 for x in xs if x >= k and x % 2 == 0)\n"
        )
        ast_safety.verify_static(code)  # must not raise

    def test_for_loop_with_append_style(self):
        code = (
            "def solve(xs, k):\n"
            "    result = []\n"
            "    for x in xs:\n"
            "        if x % k == 0:\n"
            "            result.append(x)\n"
            "    return result\n"
        )
        ast_safety.verify_static(code)  # must not raise

    def test_lambda_sort_key(self):
        code = (
            "def solve(xs, k):\n"
            "    return sorted(xs, key=lambda x: abs(x - k))\n"
        )
        ast_safety.verify_static(code)  # must not raise


class VerifyStaticRejectsUnsafeCode(unittest.TestCase):
    def assert_rejected(self, code: str):
        with self.assertRaises((SyntaxError, ast_safety.UnsafeCodeError)):
            ast_safety.verify_static(code)

    def test_import_statement(self):
        self.assert_rejected("import os\ndef solve(xs, k):\n    return xs\n")

    def test_import_from(self):
        self.assert_rejected("from os import system\ndef solve(xs, k):\n    return xs\n")

    def test_dunder_attribute_escape(self):
        self.assert_rejected("def solve(xs, k):\n    return [().__class__ for x in xs]\n")

    def test_dunder_name(self):
        self.assert_rejected("def solve(xs, k):\n    return __builtins__\n")

    def test_disallowed_builtin_call(self):
        self.assert_rejected("def solve(xs, k):\n    return eval('1')\n")

    def test_open_call(self):
        self.assert_rejected("def solve(xs, k):\n    open('/etc/passwd')\n    return xs\n")

    def test_disallowed_attribute_method(self):
        self.assert_rejected("def solve(xs, k):\n    return xs.__str__()\n")

    def test_recursive_call(self):
        self.assert_rejected("def solve(xs, k):\n    return solve(xs, k)\n")

    def test_second_top_level_function(self):
        self.assert_rejected(
            "def helper(x):\n    return x\n\ndef solve(xs, k):\n    return [helper(x) for x in xs]\n"
        )

    def test_nested_function_def(self):
        self.assert_rejected(
            "def solve(xs, k):\n    def helper(x):\n        return x\n    return [helper(x) for x in xs]\n"
        )

    def test_class_def(self):
        self.assert_rejected("class Foo:\n    pass\ndef solve(xs, k):\n    return xs\n")

    def test_wrong_function_name(self):
        self.assert_rejected("def run(xs, k):\n    return xs\n")

    def test_wrong_params(self):
        self.assert_rejected("def solve(xs, n):\n    return xs\n")

    def test_extra_top_level_statement(self):
        self.assert_rejected("x = 1\ndef solve(xs, k):\n    return xs\n")

    def test_with_statement(self):
        self.assert_rejected(
            "def solve(xs, k):\n    with open('x') as f:\n        pass\n    return xs\n"
        )

    def test_try_except(self):
        self.assert_rejected(
            "def solve(xs, k):\n    try:\n        return xs\n    except Exception:\n        return []\n"
        )

    def test_global_statement(self):
        self.assert_rejected("g = []\ndef solve(xs, k):\n    global g\n    return xs\n")

    def test_decorator(self):
        self.assert_rejected(
            "def deco(f):\n    return f\n@deco\ndef solve(xs, k):\n    return xs\n"
        )

    def test_syntax_error(self):
        with self.assertRaises(SyntaxError):
            ast_safety.verify_static("def solve(xs, k)\n    return xs\n")


if __name__ == "__main__":
    unittest.main()
