"""Lint for config/plugin-catalog.yaml (#1266): no entry may start a process
with a flag its script does not know, overlap allowed/blocked tools, or use a
placeholder variable that is not declared under ``secrets``."""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.plugins import load_plugin_catalog  # noqa: E402

_VAR = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def lint_entry(name: str, entry: dict, repo_root: Path) -> list:
    """Return human-readable problems for one catalog entry."""
    problems = []
    conn = entry.get("connection") or {}
    if conn.get("type") == "stdio":
        args = [str(a) for a in conn.get("args") or []]
        scripts = [a for a in args if a.startswith("scripts/")]
        for script in scripts:
            path = repo_root / script
            if not path.is_file():
                problems.append(f"{name}: script {script} does not exist")
                continue
            text = path.read_text(encoding="utf-8")
            for flag in (a for a in args if a.startswith("--")):
                if flag not in text:
                    problems.append(f"{name}: flag {flag} not found in {script}")
    tools = entry.get("tools") or {}
    both = set(tools.get("allowed") or []) & set(tools.get("blocked") or [])
    if both:
        problems.append(f"{name}: tools both allowed and blocked: {sorted(both)}")
    used = set(_VAR.findall(str(conn.get("url", ""))))
    for value in (conn.get("headers") or {}).values():
        used |= set(_VAR.findall(str(value)))
    undeclared = used - set(entry.get("secrets") or [])
    if undeclared:
        problems.append(f"{name}: variables not declared in secrets: {sorted(undeclared)}")
    return problems


def test_real_catalog_has_no_lint_problems():
    catalog = load_plugin_catalog(agent_meta_root=REPO_ROOT)
    problems = [p for name, entry in catalog.items() for p in lint_entry(name, entry, REPO_ROOT)]
    assert problems == []


@pytest.mark.parametrize("entry, needle", [
    ({"connection": {"type": "stdio", "command": "python3",
                     "args": ["scripts/viz-logger.py", "--mcp", "--no-such-flag"]}},
     "--no-such-flag"),
    ({"connection": {"type": "stdio", "command": "python3", "args": ["scripts/nope.py"]}},
     "does not exist"),
    ({"tools": {"allowed": ["a", "b"], "blocked": ["b"]}}, "both allowed and blocked"),
    ({"connection": {"type": "http", "url": "{{MCP_X_URL}}/mcp"}, "secrets": []},
     "MCP_X_URL"),
])
def test_lint_catches_problems(entry, needle):
    problems = lint_entry("fake", entry, REPO_ROOT)
    assert any(needle in p for p in problems), problems
