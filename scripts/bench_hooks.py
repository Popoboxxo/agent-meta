#!/usr/bin/env python3
"""Reproducible hook-latency / spawn-count benchmark (issue #1169, Task 6).

Counts Python interpreter starts with a PATH shim and records wall-clock
median/p95. The numbers are DIAGNOSTIC only: no threshold is enforced here or
in the tests (trap #1116 -- wall-clock assertions are load-dependent).

Usage::

    python3 scripts/bench_hooks.py --runs 5 --json
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
GUARD = ROOT / "hooks" / "1-generic" / "orchestrator-guard.sh"

_SCRIPTS = Path(__file__).resolve().parent
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.config import load_config  # noqa: E402
from lib.tmp_paths import resolve_tmp_paths, tmp_env  # noqa: E402


def _bench_tmp_env() -> dict:
    """Pin the subprocess temp dirs to the repo sink (AC-11/IC-18)."""
    paths = resolve_tmp_paths(ROOT, load_config(ROOT / ".meta-config" / "project.yaml"))
    return tmp_env(paths, dict(os.environ))

PAYLOADS = {
    "bash-simple": {
        "tool_name": "Bash",
        "tool_input": {"command": "echo benchmark"},
    },
    "read-simple": {
        "tool_name": "Read",
        "tool_input": {"file_path": "foo.txt"},
    },
}

_SHIM = """#!/bin/sh
printf 'x' >> "$BENCH_SPAWN_COUNTER"
exec "$BENCH_REAL_PYTHON" "$@"
"""


def _percentile(values: list[float], fraction: float) -> float:
    ordered = sorted(values)
    if not ordered:
        return 0.0
    index = min(len(ordered) - 1, int(round(fraction * (len(ordered) - 1))))
    return ordered[index]


def _benchmark(project: Path, payload: dict, runs: int) -> dict:
    shim_dir = project / "shim"
    shim_dir.mkdir(parents=True, exist_ok=True)
    counter = shim_dir / "count"
    for name in ("python3", "python"):
        wrapper = shim_dir / name
        wrapper.write_text(_SHIM, encoding="utf-8")
        wrapper.chmod(0o755)

    env = _bench_tmp_env()
    env["PATH"] = str(shim_dir) + os.pathsep + env.get("PATH", "")
    env["BENCH_SPAWN_COUNTER"] = str(counter)
    env["BENCH_REAL_PYTHON"] = sys.executable
    env.pop("CLAUDE_PROJECT_DIR", None)

    result = dict(payload["tool_input"])
    full_payload = dict(payload)
    full_payload["tool_input"] = result
    full_payload["cwd"] = project.as_posix()

    durations: list[float] = []
    spawns: list[int] = []
    for _ in range(max(1, runs)):
        counter.write_bytes(b"")
        start = time.perf_counter()
        subprocess.run(
            ["bash", str(GUARD)],
            input=json.dumps(full_payload),
            capture_output=True,
            text=True,
            encoding="utf-8",
            cwd=str(project),
            env=env,
            timeout=30,
        )
        durations.append((time.perf_counter() - start) * 1000.0)
        spawns.append(counter.stat().st_size if counter.exists() else 0)

    return {
        "median_ms": round(statistics.median(durations), 3),
        "p95_ms": round(_percentile(durations, 0.95), 3),
        "python_spawns": int(statistics.median(spawns)),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Hook latency benchmark (#1169)")
    parser.add_argument("--runs", type=int, default=5)
    parser.add_argument("--json", action="store_true", help="emit JSON only")
    args = parser.parse_args()

    report: dict[str, dict] = {}
    with tempfile.TemporaryDirectory(prefix="am-hook-bench-") as tmp:
        project = Path(tmp)
        (project / ".meta-config").mkdir()
        (project / ".meta-config" / "project.yaml").write_text(
            "orchestrator:\n  strict: false\n", encoding="utf-8"
        )
        for name, payload in PAYLOADS.items():
            report[name] = _benchmark(project, payload, args.runs)

    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        for name, values in report.items():
            print("{}: median={}ms p95={}ms spawns={}".format(
                name, values["median_ms"], values["p95_ms"], values["python_spawns"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
