#!/usr/bin/env python3
"""In-container test runner for candidate ``solve(xs, k)`` implementations.

Reads a single JSON object from stdin::

    {
      "code": "<candidate python source>",
      "tests": [{"xs": [...], "k": <int>, "expected": [...]}, ...],
      "per_test_timeout_sec": 2.0,
      "memory_mb": 256,
      "cpu_sec": 5
    }

Writes a single JSON object to stdout describing the verification result
(see ``main()`` below for the schema). Never raises out of ``main()``; any
failure is captured and reported as a field in the JSON so the host side
always gets a parseable result, even for hostile input.

This script is meant to run *inside* the locked-down container built from
``Dockerfile``: no network, dropped capabilities, non-root user, and
OS-enforced CPU/memory/pid limits applied by the host's ``docker run``
invocation (see ``client.py``). The ``resource.setrlimit`` calls below and
the restricted ``__builtins__`` used for ``exec`` are a second, independent
line of defense in case those container-level options are ever
misconfigured, and the AST check in ``ast_safety`` is re-run here (not just
host-side) in case a caller ever talks to this image directly.
"""

from __future__ import annotations

import builtins as _builtins_module
import contextlib
import io
import json
import os
import resource
import signal
import sys
import time

# `python -I` (isolated mode, used by the Dockerfile ENTRYPOINT) implies
# `-P`, which stops Python from auto-prepending this script's own directory
# to sys.path. Add it back explicitly so `import ast_safety` resolves.
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import ast_safety  # noqa: E402


class TestTimeout(Exception):
    pass


def _alarm_handler(signum, frame):  # noqa: ARG001 - required signal handler signature
    raise TestTimeout("per-test time limit exceeded")


def apply_self_rlimits(memory_mb: int, cpu_sec: int) -> None:
    """Best-effort second line of defense. The primary limits are enforced
    by ``docker run --memory``/``--cpus``/``--pids-limit`` on the host side."""
    mem_bytes = memory_mb * 1024 * 1024
    for rlimit, value in (
        (resource.RLIMIT_AS, (mem_bytes, mem_bytes)),
        (resource.RLIMIT_CPU, (cpu_sec, cpu_sec)),
        (resource.RLIMIT_NPROC, (0, 0)),
        (resource.RLIMIT_FSIZE, (0, 0)),
    ):
        try:
            resource.setrlimit(rlimit, value)
        except (ValueError, OSError):
            pass  # container-level limits still apply


def build_restricted_globals() -> dict:
    """A ``__builtins__`` containing only ast_safety.ALLOWED_CALL_NAMES,
    so even a bug in the static checker can't hand candidate code access
    to open/eval/exec/__import__/etc. at runtime."""
    safe_builtins = {name: getattr(_builtins_module, name) for name in ast_safety.ALLOWED_CALL_NAMES}
    return {"__builtins__": safe_builtins}


def load_solve_function(code: str):
    """Run the full static check pipeline, then exec the code in a
    restricted namespace and return the resulting ``solve`` function."""
    tree = ast_safety.verify_static(code)
    compiled = compile(tree, "<solve>", "exec")
    restricted_globals = build_restricted_globals()
    exec(compiled, restricted_globals)  # noqa: S102 - this is the sandbox itself
    return restricted_globals["solve"]


def run_one_test(solve_fn, xs, k, expected, per_test_timeout_sec: float) -> dict:
    xs_copy = list(xs)
    before = list(xs_copy)
    result = {"xs": xs, "k": k, "expected": expected}

    old_handler = signal.signal(signal.SIGALRM, _alarm_handler)
    signal.setitimer(signal.ITIMER_REAL, per_test_timeout_sec)
    start = time.perf_counter()
    try:
        with contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
            actual = solve_fn(xs_copy, k)
        result["actual"] = actual
        result["passed"] = actual == expected
        result["error"] = None
    except TestTimeout:
        result["actual"] = None
        result["passed"] = False
        result["error"] = "timeout"
    except MemoryError:
        result["actual"] = None
        result["passed"] = False
        result["error"] = "memory_limit_exceeded"
    except Exception as exc:  # noqa: BLE001 - must always report, never crash the runner
        result["actual"] = None
        result["passed"] = False
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        signal.setitimer(signal.ITIMER_REAL, 0)
        signal.signal(signal.SIGALRM, old_handler)

    result["elapsed_sec"] = time.perf_counter() - start
    result["mutated_input"] = xs_copy != before
    return result


def main() -> int:
    output = {
        "syntax_ok": False,
        "ast_safe": False,
        "signature_valid": False,
        "executable": False,
        "tests_passed": False,
        "pure": None,
        "tests": [],
        "error": None,
        "max_rss_mb": None,
        "elapsed_sec": None,
    }
    start_total = time.perf_counter()

    raw = sys.stdin.read()
    try:
        payload = json.loads(raw)
    except json.JSONDecodeError as exc:
        output["error"] = f"invalid request JSON: {exc}"
        print(json.dumps(output))
        return 0

    code = payload.get("code", "")
    tests = payload.get("tests", [])
    per_test_timeout = float(payload.get("per_test_timeout_sec", 2.0))
    memory_mb = int(payload.get("memory_mb", 256))
    cpu_sec = int(payload.get("cpu_sec", 5))

    apply_self_rlimits(memory_mb, cpu_sec)

    try:
        tree = ast_safety.check_syntax(code)
        output["syntax_ok"] = True
    except SyntaxError as exc:
        output["error"] = f"SyntaxError: {exc}"
        print(json.dumps(output))
        return 0

    try:
        ast_safety.check_safety(tree)
        ast_safety.check_signature(tree)
        output["ast_safe"] = True
        output["signature_valid"] = True
    except ast_safety.UnsafeCodeError as exc:
        output["error"] = str(exc)
        print(json.dumps(output))
        return 0

    try:
        compiled = compile(tree, "<solve>", "exec")
        restricted_globals = build_restricted_globals()
        exec(compiled, restricted_globals)  # noqa: S102 - this is the sandbox itself
        solve_fn = restricted_globals["solve"]
    except Exception as exc:  # noqa: BLE001
        output["error"] = f"load error: {type(exc).__name__}: {exc}"
        print(json.dumps(output))
        return 0

    output["executable"] = True

    results = [run_one_test(solve_fn, case["xs"], case["k"], case["expected"], per_test_timeout) for case in tests]
    output["tests"] = results
    output["tests_passed"] = bool(results) and all(r["passed"] for r in results)
    output["pure"] = all(not r["mutated_input"] for r in results) if results else None
    output["elapsed_sec"] = time.perf_counter() - start_total
    output["max_rss_mb"] = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024

    print(json.dumps(output))
    return 0


if __name__ == "__main__":
    sys.exit(main())
