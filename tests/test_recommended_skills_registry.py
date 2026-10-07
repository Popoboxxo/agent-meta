"""Regression tests for config/recommended-skills.yaml (issue #680).

This registry is a curated recommendation whitelist — distinct from
config/skills-registry.yaml (installed external skill submodules, governed
by scripts/lib/skills.py). Pure shape/schema validation only; no sync.py
wiring exists yet (Phase 2, deferred).
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_REGISTRY_PATH = _REPO_ROOT / "config" / "recommended-skills.yaml"
_SCOPE_RE = re.compile(r"^(provider:[a-z0-9_-]+|agnostic)$")
_REQUIRED_FIELDS = ("name", "description", "link", "scope")


def _load_entries() -> list[dict]:
    with _REGISTRY_PATH.open(encoding="utf-8") as f:
        data = yaml.safe_load(f)
    return data["recommended-skills"]


def test_registry_has_at_least_ten_entries():
    entries = _load_entries()
    assert len(entries) >= 10


def test_every_entry_has_valid_scope():
    entries = _load_entries()
    for entry in entries:
        scope = entry.get("scope")
        assert scope, f"entry {entry.get('name')!r} missing scope"
        assert _SCOPE_RE.match(scope), f"entry {entry.get('name')!r} has invalid scope {scope!r}"


def test_every_entry_has_required_fields_nonempty():
    entries = _load_entries()
    for entry in entries:
        for field in _REQUIRED_FIELDS:
            assert field in entry, f"entry {entry.get('name')!r} missing field {field!r}"
            value = entry[field]
            assert value not in (None, ""), f"entry {entry.get('name')!r} has empty field {field!r}"


def test_registry_mixes_claude_other_provider_and_agnostic_scopes():
    scopes = {entry["scope"] for entry in _load_entries()}
    assert "provider:claude" in scopes
    assert "agnostic" in scopes
    other_providers = {s for s in scopes if s.startswith("provider:") and s != "provider:claude"}
    assert other_providers, "expected at least one non-Claude provider scope"
