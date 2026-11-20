"""Structure test for the hook latency benchmark (#1169, Task 6).

The benchmark must report spawn counts without any wall-clock assertion in the
test suite (trap #1116); timing numbers are documentation only.
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_BENCH = _REPO_ROOT / "scripts" / "bench_hooks.py"


def test_bench_reports_spawn_count_for_fixed_payloads():
    r = subprocess.run(
        [sys.executable, str(_BENCH), "--runs", "1", "--json"],
        capture_output=True,
        text=True,
        cwd=str(_REPO_ROOT),
        timeout=120,
    )
    assert r.returncode == 0, r.stderr
    data = json.loads(r.stdout)
    for payload in ("bash-simple", "read-simple"):
        assert payload in data
        assert data[payload]["python_spawns"] >= 1
        assert data[payload]["median_ms"] >= 0
        assert data[payload]["p95_ms"] >= 0


def test_bench_source_has_no_wall_clock_assertion():
    """#1116: the benchmark is diagnostic, never a CI timing gate."""
    tree = ast.parse(_BENCH.read_text(encoding="utf-8"))
    assert not [node for node in ast.walk(tree) if isinstance(node, ast.Assert)]
