"""K-12 (#1159): ``mcp-registry`` is documented as deprecated and unread.

The schema marks it DEPRECATED and no runtime code reads it from the project
config. Only log-label strings may mention the key.
"""
from __future__ import annotations

import json
import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_schema_marks_mcp_registry_deprecated():
    schema = json.loads(
        (REPO_ROOT / "config" / "project-config.schema.json").read_text(encoding="utf-8")
    )
    description = schema["properties"]["mcp-registry"]["description"]
    assert "DEPRECATED" in description
    assert "no longer read" in description


def test_no_runtime_reader_of_mcp_registry_key():
    # A real read is a subscript or a .get() call on the config object; log
    # labels such as "mcp-registry → ..." or "mcp-registry/<name>" are allowed.
    read_pattern = re.compile(
        r"""\[\s*["']mcp-registry["']\s*\]|\.get\(\s*["']mcp-registry["']"""
    )
    offenders = []
    for path in (REPO_ROOT / "scripts" / "lib").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        for match in read_pattern.finditer(text):
            line = text.count("\n", 0, match.start()) + 1
            offenders.append(f"{path.relative_to(REPO_ROOT)}:{line}")
    assert offenders == [], "unexpected mcp-registry reader: " + ", ".join(offenders)
