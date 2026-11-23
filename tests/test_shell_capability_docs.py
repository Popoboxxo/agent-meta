"""Issue #1329 (Contract AC-5) — shell capability matrix documentation.

The docs must state shell availability per provider and per mode
(primary/subagent), the fail-safe ``deny`` + ``WARNING`` fallback, and the
existing default ``mode: subagent`` when no primary-role/mode key is present.
Assertions are purely document-based — no import of a provider code branch.

Run: python3 -m pytest tests/test_shell_capability_docs.py -q
"""
from __future__ import annotations

from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parents[1]
DOC = REPO_ROOT / "docs" / "providers" / "multi-provider.md"
REGISTRY = yaml.safe_load(
    (REPO_ROOT / "config" / "provider-capabilities.yaml").read_text(encoding="utf-8")
)["capabilities"]


def _doc() -> str:
    return DOC.read_text(encoding="utf-8")


def test_shell_capability_section_exists():
    text = _doc()
    assert "Subagent-Shell-Capability" in text


def test_shell_capability_terms_are_documented():
    text = _doc()
    for term in (
        "subagent-shell",
        "subagent-shell-verified-state",
        "VERIFIED-RUNTIME",
        "deny",
        "WARNING",
        "primary",
        "subagent",
    ):
        assert term in text, f"missing documented term: {term}"


def test_default_mode_fallback_is_explained():
    text = _doc()
    assert "primary-role" in text
    assert "mode: subagent" in text
    assert "default" in text.lower() or "Default" in text


def test_matrix_covers_every_registered_provider_in_both_modes():
    text = _doc()
    section = text.split("Subagent-Shell-Capability", 1)[1]
    for provider in REGISTRY:
        row = [line for line in section.splitlines() if f"`{provider}`" in line]
        assert row, f"capability matrix has no row for {provider}"
        assert "primary" in row[0] and "subagent" in row[0], (
            f"{provider} row must cover both modes"
        )


def test_docs_do_not_describe_a_provider_name_branch():
    text = _doc()
    section = text.split("Subagent-Shell-Capability", 1)[1]
    assert 'if provider ==' not in section
    assert 'if provider =="' not in section
