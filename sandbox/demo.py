"""Smoke test / usage demo for the sandbox.

Runs a handful of representative cases through ``run_in_sandbox`` and
prints the verdict for each: a correct solution, an incorrect solution, an
attempted sandbox escape (import os), an infinite loop (timeout), and a
memory bomb. Requires the ``boku-sandbox`` image to already be built
(``python client.py`` -> ``build_image()``, or ``docker build -t
boku-sandbox sandbox``).
"""

from __future__ import annotations

import json

from client import SandboxConfig, build_image, run_in_sandbox

CASES = {
    "correct (list comprehension)": (
        "def solve(xs: list[int], k: int) -> list[int]:\n"
        "    return sorted(x * 2 for x in xs if x >= k and x % 2 == 0)\n",
        [
            {"xs": [1, 4, 6, 9, 10, -2], "k": 3, "expected": [8, 12, 20]},
            {"xs": [], "k": 5, "expected": []},
        ],
    ),
    "correct (for loop + append)": (
        "def solve(xs: list[int], k: int) -> list[int]:\n"
        "    result = []\n"
        "    for x in xs:\n"
        "        if x >= k and x % 2 == 0:\n"
        "            result.append(x * 2)\n"
        "    result.sort()\n"
        "    return result\n"
        "\n",
        [
            {"xs": [1, 4, 6, 9, 10, -2], "k": 3, "expected": [8, 12, 20]},
        ],
    ),
    "incorrect (off-by-one on k comparison)": (
        "def solve(xs: list[int], k: int) -> list[int]:\n"
        "    return sorted(x for x in xs if x > k)\n",
        [
            {"xs": [1, 3, 5], "k": 3, "expected": [3, 5]},
        ],
    ),
    "sandbox escape attempt (import os)": (
        "import os\n"
        "def solve(xs, k):\n"
        "    return os.listdir('/')\n",
        [{"xs": [1], "k": 1, "expected": []}],
    ),
    "dunder escape attempt": (
        "def solve(xs, k):\n"
        "    return [().__class__ for x in xs]\n",
        [{"xs": [1], "k": 1, "expected": []}],
    ),
    "infinite loop (timeout)": (
        "def solve(xs, k):\n"
        "    while True:\n"
        "        pass\n",
        [{"xs": [1], "k": 1, "expected": []}],
    ),
    "memory bomb": (
        "def solve(xs, k):\n"
        "    return [0] * (10 ** 12)\n",
        [{"xs": [1], "k": 1, "expected": []}],
    ),
    "impure (mutates input)": (
        "def solve(xs, k):\n"
        "    xs.sort()\n"
        "    return xs\n",
        [{"xs": [3, 1, 2], "k": 1, "expected": [1, 2, 3]}],
    ),
}


def main() -> None:
    print("Building boku-sandbox image...")
    build_image()

    for name, (code, tests) in CASES.items():
        verdict = run_in_sandbox(code, tests, SandboxConfig(timeout_sec=8.0, per_test_timeout_sec=1.5))
        print(f"\n=== {name} ===")
        print(json.dumps(verdict, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
