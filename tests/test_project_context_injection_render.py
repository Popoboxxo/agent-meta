"""Render-side tests for project-context injection (issue #1187).

Shared by T4-T10. Each task adds its own section; keep section boundaries so
later tasks can append without disturbing existing tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.agent_sync import _build_provider_vars  # noqa: E402
from lib.config import _PROJECT_CONTEXT_POINTER_TEXTS  # noqa: E402


# ---------------------------------------------------------------------------
# T4 — provider_vars
# ---------------------------------------------------------------------------


def test_provider_vars_default_injected_true_without_config():
    """No config/scope: conservative default is injected=true + mode=all.

    Backward compatibility for tests/test_orchestrator_name_dispatch.py:56.
    """
    merged = _build_provider_vars(
        {}, "Claude", {"PROJECT_CONTEXT": "P"}, _ROOT, active_set=frozenset()
    )
    assert merged["PROJECT_CONTEXT_INJECTED"] == "true"
    assert merged["PROJECT_CONTEXT_MODE"] == "all"


def test_provider_vars_carry_scope_from_variables():
    """A resolved scope travels through; INJECTED stays true here (T5 decides
    the per-role value)."""
    scope = {
        "mode": "core",
        "whitelist": ["developer"],
        "orchestrator": "inherit",
        "orchestrator_roles": ("orchestrator",),
        "pointer_text": _PROJECT_CONTEXT_POINTER_TEXTS["en"],
        "pointer_language": "en",
        "present": True,
    }
    merged = _build_provider_vars(
        {}, "Claude", {"_PROJECT_CONTEXT_SCOPE": scope}, _ROOT,
        active_set=frozenset(),
    )
    assert merged["PROJECT_CONTEXT_INJECTED"] == "true"
    assert merged["PROJECT_CONTEXT_MODE"] == "core"


def test_provider_vars_carry_formatted_pointer_per_provider():
    """The per-provider context file is substituted into the pointer, and a
    configured German pointer_text stays German (D8)."""
    cases = [
        ("Claude", "CLAUDE.md", None, "Project context"),
        ("Gemini", "AGENTS.md", None, "Project context"),
        ("Opencode", ".continue/rules/project-context.md",
         _PROJECT_CONTEXT_POINTER_TEXTS["de"], "Projektkontext"),
    ]
    for provider, context_file, pointer_text, expected_lead in cases:
        variables = {}
        if pointer_text is not None:
            variables["_PROJECT_CONTEXT_SCOPE"] = {"pointer_text": pointer_text}
        merged = _build_provider_vars(
            {"context_file": context_file}, provider, variables, _ROOT,
            active_set=frozenset(),
        )
        pointer = merged["_PROJECT_CONTEXT_POINTER"]
        assert context_file in pointer
        assert "{context_file}" not in pointer
        assert pointer.startswith(expected_lead)
