"""Host-side driver for the Boku-nano code-execution sandbox.

Spins up a short-lived, network-isolated Docker container from the
``boku-sandbox`` image (see ``Dockerfile``) to execute one candidate
``solve(xs, k)`` implementation against a list of test cases, and returns
the parsed JSON verdict produced by ``runner.py``.

This is the only supported way to run untrusted, model-generated code in
this project -- do not ``exec()`` candidate code outside of this sandbox.

Usage::

    from client import SandboxConfig, build_image, run_in_sandbox

    build_image()  # once, or whenever runner.py/ast_safety.py/Dockerfile change

    verdict = run_in_sandbox(
        code="def solve(xs, k):\\n    return sorted(x for x in xs if x >= k)\\n",
        tests=[{"xs": [1, 5, 2, 8], "k": 3, "expected": [5, 8]}],
    )
"""

from __future__ import annotations

import dataclasses
import json
import subprocess
import uuid
from pathlib import Path
from typing import Any

IMAGE_NAME = "boku-sandbox"
SANDBOX_DIR = Path(__file__).resolve().parent


@dataclasses.dataclass
class SandboxConfig:
    timeout_sec: float = 10.0  # wall-clock budget for the whole `docker run`, incl. startup
    per_test_timeout_sec: float = 2.0
    memory_mb: int = 256
    cpu_sec: int = 5  # RLIMIT_CPU applied inside the container by runner.py
    cpus: float = 0.5  # docker --cpus
    pids_limit: int = 64


class SandboxError(RuntimeError):
    """Infrastructure failure: docker missing, container killed before
    producing output, malformed result, etc. Candidate code failing its
    tests is *not* an error -- that is reported in the returned dict."""


def run_in_sandbox(
    code: str,
    tests: list[dict[str, Any]],
    config: SandboxConfig | None = None,
) -> dict[str, Any]:
    """Execute ``code``'s ``solve(xs, k)`` against ``tests`` inside the
    sandbox container and return the JSON verdict from ``runner.py``.

    Each item of ``tests`` looks like ``{"xs": [...], "k": <int>, "expected": [...]}``.
    """
    config = config or SandboxConfig()
    payload = json.dumps(
        {
            "code": code,
            "tests": tests,
            "per_test_timeout_sec": config.per_test_timeout_sec,
            "memory_mb": config.memory_mb,
            "cpu_sec": config.cpu_sec,
        }
    )

    container_name = f"boku-sandbox-{uuid.uuid4().hex[:12]}"
    cmd = [
        "docker", "run",
        "--rm",
        "-i",
        "--name", container_name,
        "--network", "none",
        "--read-only",
        "--tmpfs", "/tmp:rw,noexec,nosuid,size=16m",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--pids-limit", str(config.pids_limit),
        "--memory", f"{config.memory_mb}m",
        "--memory-swap", f"{config.memory_mb}m",  # total = memory limit -> no swap
        "--cpus", str(config.cpus),
        IMAGE_NAME,
    ]

    try:
        proc = subprocess.run(
            cmd,
            input=payload,
            capture_output=True,
            text=True,
            timeout=config.timeout_sec,
        )
    except subprocess.TimeoutExpired:
        _force_kill(container_name)
        return {
            "syntax_ok": None,
            "ast_safe": None,
            "signature_valid": None,
            "executable": False,
            "tests_passed": False,
            "pure": None,
            "tests": [],
            "error": "sandbox_timeout: container did not finish within timeout_sec",
        }

    if proc.returncode != 0:
        raise SandboxError(
            f"sandbox container exited with code {proc.returncode}: "
            f"stderr={proc.stderr.strip()[:2000]}"
        )

    try:
        return json.loads(proc.stdout)
    except json.JSONDecodeError as exc:
        raise SandboxError(
            "sandbox produced non-JSON output: "
            f"{exc}\nstdout={proc.stdout[:2000]}\nstderr={proc.stderr[:2000]}"
        ) from exc


def _force_kill(container_name: str) -> None:
    subprocess.run(["docker", "kill", container_name], capture_output=True)
    subprocess.run(["docker", "rm", "-f", container_name], capture_output=True)


def build_image(dockerfile_dir: str | Path = SANDBOX_DIR) -> None:
    """Build (or rebuild) the sandbox image. Run once before using
    ``run_in_sandbox``, and again whenever runner.py/ast_safety.py/Dockerfile
    change.

    ``dockerfile_dir`` defaults to this file's own directory (where the
    Dockerfile lives), so it resolves correctly regardless of the caller's
    current working directory."""
    subprocess.run(["docker", "build", "-t", IMAGE_NAME, str(dockerfile_dir)], check=True)
