"""Naming disambiguation of the two ``topology`` config keys (#1243, A1)."""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lib import topology

jsonschema = pytest.importorskip("jsonschema")

_SCHEMA = json.loads(
    (Path(__file__).resolve().parent.parent / "config" / "project-config.schema.json")
    .read_text(encoding="utf-8")
)
_ORCH = _SCHEMA["properties"]["orchestrator"]["properties"]["topology"]
_CTX = _SCHEMA["properties"]["context_file"]["properties"]["topology"]


def test_descriptions_are_distinct_and_cross_reference():
    assert _ORCH["description"] != _CTX["description"]
    assert "context_file.topology" in _ORCH["description"]
    assert "orchestrator.topology" in _CTX["description"]


def test_both_keys_set_validates():
    cfg = {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude"],
        "orchestrator": {"topology": "subagent"},
        "context_file": {"topology": "per-provider"},
    }
    jsonschema.validate(cfg, _SCHEMA)


def test_docstring_delimits_from_context_file_topology():
    doc = topology.__doc__ or ""
    assert "context_file.topology" in doc
    assert "file layout" in doc
