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


# ---------------------------------------------------------------------------
# T5 — matrix / apply_scope
# ---------------------------------------------------------------------------


def _t5_impl():
    """Lazy imports: before T5 lands only these tests fail, T4 stays green."""
    from lib.config import project_context_injected_for_role
    from lib.agent_sync import apply_project_context_scope

    return project_context_injected_for_role, apply_project_context_scope


def _pc_scope(mode="all", whitelist=(), orchestrator="inherit",
              orchestrator_roles=("orchestrator",)):
    """Minimal resolved scope (spec §3.1) for matrix/scope tests."""
    return {
        "mode": mode,
        "whitelist": list(whitelist),
        "orchestrator": orchestrator,
        "orchestrator_roles": tuple(orchestrator_roles),
        "pointer_text": _PROJECT_CONTEXT_POINTER_TEXTS["en"],
        "pointer_language": "en",
        "present": True,
    }


# (mode, whitelist, orchestrator, role, expected) — spec §3.1 tables.
_MATRIX_CASES = [
    # all: everyone, except orchestrator roles when exclude wins (D6).
    ("all", (), "inherit", "developer", True),
    ("all", (), "inherit", "orchestrator", True),
    ("all", (), "exclude", "developer", True),
    ("all", (), "exclude", "orchestrator", False),
    # core: nobody, unless include promotes the orchestrator set.
    ("core", (), "inherit", "orchestrator", False),
    ("core", (), "include", "orchestrator", True),
    ("core", (), "include", "developer", False),
    # core+orchestrator: only the orchestrator set; exclude degenerates to core.
    ("core+orchestrator", (), "inherit", "orchestrator", True),
    ("core+orchestrator", (), "inherit", "developer", False),
    ("core+orchestrator", (), "exclude", "orchestrator", False),
    # core+whitelist: only the whitelist; orchestrator set only with include.
    ("core+whitelist", ("developer",), "inherit", "developer", True),
    ("core+whitelist", ("developer",), "inherit", "orchestrator", False),
    ("core+whitelist", ("developer",), "inherit", "planner", False),
    ("core+whitelist", ("developer",), "include", "orchestrator", True),
    ("core+whitelist", ("developer",), "exclude", "orchestrator", False),
    # A whitelisted role that is also a primary-role stays included on inherit.
    ("core+whitelist", ("orchestrator", "developer"), "inherit",
     "orchestrator", True),
]


@pytest.mark.parametrize(
    "mode, whitelist, orchestrator, role, expected",
    _MATRIX_CASES,
    ids=[f"{c[0]}-{c[2]}-{c[3]}" for c in _MATRIX_CASES],
)
def test_injection_matrix(mode, whitelist, orchestrator, role, expected):
    """Pure decision matrix from spec §3.1 (all mode × orchestrator combos)."""
    decision, _ = _t5_impl()
    scope = _pc_scope(mode, whitelist, orchestrator)
    assert decision(scope, role) is expected


def test_injection_matrix_uses_overridden_orchestrator_roles():
    """D5: an override replaces the default set — no silent mixing in."""
    decision, _ = _t5_impl()
    scope = _pc_scope(
        "core+orchestrator", orchestrator_roles=("senior-developer",))
    assert decision(scope, "senior-developer") is True
    assert decision(scope, "orchestrator") is False


def test_injection_matrix_empty_orchestrator_roles():
    """D5: an explicitly empty orchestrator set injects nothing."""
    decision, _ = _t5_impl()
    scope = _pc_scope("core+orchestrator", orchestrator_roles=())
    for role in ("orchestrator", "senior-developer", "developer"):
        assert decision(scope, role) is False


def test_apply_scope_blanks_context_for_excluded_role():
    """Excluded roles lose their paragraph and carry injected=false."""
    _, apply_scope = _t5_impl()
    merged = {"PROJECT_CONTEXT": "PARA", "PROJECT_CONTEXT_INJECTED": "true"}
    result = apply_scope(merged, "developer", _pc_scope("core"))
    assert result is False
    assert merged["PROJECT_CONTEXT"] == ""
    assert merged["PROJECT_CONTEXT_INJECTED"] == "false"


def test_apply_scope_keeps_paragraph_for_included_role():
    """Included roles keep their paragraph and carry injected=true."""
    _, apply_scope = _t5_impl()
    merged = {"PROJECT_CONTEXT": "PARA", "PROJECT_CONTEXT_INJECTED": "false"}
    result = apply_scope(merged, "developer", _pc_scope("all"))
    assert result is True
    assert merged["PROJECT_CONTEXT"] == "PARA"
    assert merged["PROJECT_CONTEXT_INJECTED"] == "true"


def test_apply_scope_does_not_mutate_shared_variables():
    """The caller's variables dict keeps PROJECT_CONTEXT (no role leakage)."""
    _, apply_scope = _t5_impl()
    variables = {"PROJECT_CONTEXT": "PARA", "PROJECT_CONTEXT_INJECTED": "true"}
    merged = dict(variables)
    apply_scope(merged, "developer", _pc_scope("core"))
    assert variables["PROJECT_CONTEXT"] == "PARA"
    assert variables["PROJECT_CONTEXT_INJECTED"] == "true"

