"""Integration tests that run real code through the boku-sandbox Docker
container -- i.e. assertions on what ``demo.py`` otherwise only prints.

``demo.py``'s CASES already exercise exactly what homework.md's 「制限時間内
に実行できる」「import、属性アクセス、ファイル操作などを含まない」and the
purity check need (a correct solution, a wrong one, two escape attempts, an
infinite loop, a memory bomb, an input-mutating one); reused here instead of
duplicated so there is one source of truth for the cases. What was missing
was turning "print the verdict" into "assert the verdict is what it should
be" -- this file is that, not a new sandbox.

Requires Docker and the ``boku-sandbox`` image (built once in
``setUpClass``, same as ``demo.py`` does). The whole class is skipped when
Docker itself is unavailable; a build failure (e.g. no network to pull the
base image) skips it too rather than failing the run.

Run with: python -m unittest discover -s sandbox/tests
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from client import SandboxConfig, build_image, run_in_sandbox  # noqa: E402
from demo import CASES  # noqa: E402

_CONFIG = SandboxConfig(timeout_sec=8.0, per_test_timeout_sec=1.5)


def _docker_available() -> bool:
    if shutil.which("docker") is None:
        return False
    try:
        subprocess.run(["docker", "info"], capture_output=True, timeout=5, check=True)
    except (subprocess.SubprocessError, OSError):
        return False
    return True


@unittest.skipUnless(_docker_available(), "Docker is not available")
class SandboxContainerTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        try:
            build_image()
        except (subprocess.SubprocessError, OSError) as exc:
            raise unittest.SkipTest(f"could not build boku-sandbox image: {exc}")

    def _run(self, case_name: str) -> dict:
        code, tests = CASES[case_name]
        return run_in_sandbox(code, tests, _CONFIG)

    def test_correct_list_comprehension_passes(self):
        verdict = self._run("correct (list comprehension)")
        self.assertTrue(verdict["syntax_ok"])
        self.assertTrue(verdict["ast_safe"])
        self.assertTrue(verdict["executable"])
        self.assertTrue(verdict["tests_passed"])
        self.assertTrue(verdict["pure"])

    def test_correct_for_loop_append_passes(self):
        verdict = self._run("correct (for loop + append)")
        self.assertTrue(verdict["tests_passed"])
        self.assertTrue(verdict["pure"])

    def test_incorrect_output_fails_tests_not_safety(self):
        verdict = self._run("incorrect (off-by-one on k comparison)")
        self.assertTrue(verdict["ast_safe"])
        self.assertTrue(verdict["executable"])
        self.assertFalse(verdict["tests_passed"])

    def test_import_escape_is_rejected_before_running(self):
        verdict = self._run("sandbox escape attempt (import os)")
        self.assertTrue(verdict["syntax_ok"])
        self.assertFalse(verdict["ast_safe"])
        self.assertFalse(verdict["executable"])

    def test_dunder_escape_is_rejected(self):
        verdict = self._run("dunder escape attempt")
        self.assertFalse(verdict["ast_safe"])

    def test_infinite_loop_times_out_instead_of_hanging(self):
        verdict = self._run("infinite loop (timeout)")
        self.assertTrue(verdict["executable"])
        self.assertFalse(verdict["tests_passed"])
        self.assertEqual(verdict["tests"][0]["error"], "timeout")

    def test_memory_bomb_is_caught(self):
        verdict = self._run("memory bomb")
        self.assertFalse(verdict["tests_passed"])
        self.assertEqual(verdict["tests"][0]["error"], "memory_limit_exceeded")

    def test_impure_mutation_is_detected(self):
        verdict = self._run("impure (mutates input)")
        self.assertTrue(verdict["tests_passed"])  # xs.sort() also happens to match `expected`
        self.assertFalse(verdict["pure"])
        self.assertTrue(verdict["tests"][0]["mutated_input"])


if __name__ == "__main__":
    unittest.main()
