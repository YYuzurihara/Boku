"""Check generated code against the reference interpreter.

homework.md, 「コードの構造的変換」: 「すべてのコードを実行し、参照インタプリタ
と同じ結果になる場合だけ採用する」, and, about the two independently written
programs, 「両者の出力をランダムテストで比較する。これにより、コード生成器自身
のバグを検出する」. This module is that comparison.

What it checks, per snippet:

    syntax_ok    ast.parse succeeds                      (sandbox/ast_safety)
    ast_safe     only the allowlisted syntax/builtins     (sandbox/ast_safety)
    executable   solve() loads in a restricted namespace  (sandbox/runner)
    tests_passed every case matches the interpreter       (sandbox/runner)
    pure         no case mutated its input list           (sandbox/runner)

All five come from ``sandbox/``: the static checker and the test runner are
imported rather than reimplemented, so the code generator is held to exactly
the same bar that model-generated code will be held to at evaluation time.

In-process execution, and where the Docker sandbox belongs
----------------------------------------------------------
``sandbox/client.py`` is emphatic that untrusted, model-generated code only
ever runs inside the container. The snippets checked here are neither:
they are emitted by ``code_generator.py`` from a closed vocabulary in this
repository, and they pass ``ast_safety.verify_static`` before being executed
in ``runner.build_restricted_globals()``'s namespace with a per-test alarm.
Running the corpus in-process is what makes verifying every rendering of all
40,589 semantic ASTs feasible at all (a container per snippet would be
several orders of magnitude slower). ``verify_in_sandbox`` routes a snippet
through the real container for spot checks, and ``code_demo.py --sandbox``
uses it on a sample to confirm the two paths agree; model-generated code
still goes through the container, always.
"""

from __future__ import annotations

import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any, Optional

_SEMANTIC_AST = Path(__file__).resolve().parent.parent
_SANDBOX = _SEMANTIC_AST.parent / "sandbox"
sys.path.insert(0, str(_SEMANTIC_AST))
sys.path.insert(0, str(_SANDBOX))

import ast_safety  # noqa: E402  (sandbox/ast_safety.py)
import runner  # noqa: E402  (sandbox/runner.py)

from code_generator import CodeVariant  # noqa: E402
from schema import SemanticAST  # noqa: E402
from testcases import TestCase, generate_test_cases  # noqa: E402

PER_TEST_TIMEOUT_SEC = 2.0
MAX_REPORTED_FAILURES = 3


def verify(
    code: str,
    tests: Sequence[TestCase],
    per_test_timeout_sec: float = PER_TEST_TIMEOUT_SEC,
) -> dict:
    """Verify one snippet against ``tests`` (whose ``expected`` values come
    from the reference interpreter).

    Returns homework.md's ``verification`` record -- ``syntax_ok`` /
    ``ast_safe`` / ``tests_passed`` -- plus ``executable``, ``pure`` and,
    when something failed, ``error`` and up to ``MAX_REPORTED_FAILURES``
    failing cases. Never raises on bad code: a snippet that cannot even be
    parsed is a result, not an exception, because the caller is verifying a
    whole corpus and wants the report.
    """
    result: dict[str, Any] = {
        "syntax_ok": False,
        "ast_safe": False,
        "executable": False,
        "tests_passed": False,
        "pure": None,
        "error": None,
    }

    try:
        tree = ast_safety.check_syntax(code)
        result["syntax_ok"] = True
    except SyntaxError as exc:
        result["error"] = f"SyntaxError: {exc}"
        return result

    try:
        ast_safety.check_safety(tree)
        ast_safety.check_signature(tree)
        result["ast_safe"] = True
    except ast_safety.UnsafeCodeError as exc:
        result["error"] = f"UnsafeCodeError: {exc}"
        return result

    try:
        solve_fn = runner.load_solve_function(code)
        result["executable"] = True
    except Exception as exc:  # noqa: BLE001 - report, never propagate
        result["error"] = f"load error: {type(exc).__name__}: {exc}"
        return result

    if not tests:
        result["error"] = "no test cases to check against"
        return result

    outcomes = [
        runner.run_one_test(solve_fn, case["xs"], case["k"], case["expected"], per_test_timeout_sec)
        for case in tests
    ]
    result["tests_passed"] = all(outcome["passed"] for outcome in outcomes)
    # solve() must be a pure function of (xs, k): homework.md's 対象とする問題
    # promises the caller's list is not modified, and the interpreter copies.
    result["pure"] = all(not outcome["mutated_input"] for outcome in outcomes)
    failures = [
        {
            "xs": outcome["xs"],
            "k": outcome["k"],
            "expected": outcome["expected"],
            "actual": outcome["actual"],
            "error": outcome["error"],
        }
        for outcome in outcomes
        if not outcome["passed"] or outcome["mutated_input"]
    ]
    if failures:
        result["failures"] = failures[:MAX_REPORTED_FAILURES]
        result["num_failures"] = len(failures)
        result["error"] = result["error"] or "output differs from the reference interpreter"
    return result


def ok(verification: dict) -> bool:
    """Whether a verification record clears every bar (homework.md: 「参照イン
    タプリタと同じ結果になる場合だけ採用する」)."""
    return bool(
        verification["syntax_ok"]
        and verification["ast_safe"]
        and verification["executable"]
        and verification["tests_passed"]
        and verification["pure"]
    )


def verify_variant(
    variant: CodeVariant,
    tests: Sequence[TestCase],
    per_test_timeout_sec: float = PER_TEST_TIMEOUT_SEC,
) -> dict:
    """``verify`` for one rendering, tagged with the style that produced it
    so a failing report names the catalogue entry to fix."""
    verification = verify(variant.code, tests, per_test_timeout_sec)
    verification["code_style"] = variant.style.name
    return verification


def cross_check(
    ast: SemanticAST,
    code: str,
    seed: int = 0,
    n_random: int = 32,
    per_test_timeout_sec: float = PER_TEST_TIMEOUT_SEC,
) -> dict:
    """Compare ``code`` with the reference interpreter on *fresh* random
    inputs (homework.md: 「両者の出力をランダムテストで比較する」).

    Independent of whatever ``tests`` a record already carries: those are
    generated once per semantic AST and stored, so re-checking against them
    can only re-confirm what the corpus was built with. Passing a different
    ``seed`` here samples inputs the stored suite never contained, which is
    how a generator bug that the stored suite happens to miss gets caught.
    """
    tests = generate_test_cases(ast, seed=seed, n_random=n_random)
    return verify(code, tests, per_test_timeout_sec)


def verify_in_sandbox(code: str, tests: Sequence[TestCase], config: Optional[Any] = None) -> dict:
    """Run one snippet through the real Docker sandbox (``sandbox/client.py``).

    Spot-check path only -- see the module docstring. Requires the
    ``boku-sandbox`` image to have been built; raises ``SandboxError`` if
    Docker is unavailable.
    """
    import client  # noqa: PLC0415 - imported lazily: only this path needs Docker

    return client.run_in_sandbox(code, list(tests), config)
