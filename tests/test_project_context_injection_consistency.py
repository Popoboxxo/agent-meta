"""Consistency-check tests for project-context injection (issue #1187, T11).

Covers the four check IDs (mode-unknown, whitelist-no-effect,
orchestrator-role-no-template, pointer-missing), the fail-soft contract and the
registration in ``scripts/consistency-check.py``.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.config import (  # noqa: E402
    format_project_context_pointer,
    resolve_project_context_scope,
)
from lib.consistency.project_context_injection import (  # noqa: E402
    check_project_context_injection,
)
from lib.consistency.report import Severity  # noqa: E402

_PROVIDERS = {
    "Claude": {"agents_dir": ".claude/agents", "context_file": "CLAUDE.md"},
}
_AGENTS_DIR = ".claude/agents"


def _config(section):
    """Fixture project config with one explicit active provider."""
    return {"ai-providers": ["Claude"], "project-context-injection": section}


def _write_artifact(tmp_path: Path, role: str, content: str = "body\n") -> Path:
    path = tmp_path / _AGENTS_DIR / f"{role}.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _expected_pointer(config: dict, context_file: str = "CLAUDE.md") -> str:
    """Resolve the scope with the production helpers (D8: no literal)."""
    scope = resolve_project_context_scope(config, _ROOT, provider_config=_PROVIDERS)
    return format_project_context_pointer(scope["pointer_text"], context_file)


def test_mode_unknown_is_error():
    """An unknown mode is a hard finding without requiring jsonschema."""
    findings = check_project_context_injection(
        _ROOT, config=_config({"mode": "slim"}), provider_config=_PROVIDERS
    )
    errors = [f for f in findings if f.check == "project-context-injection.mode-unknown"]
    assert len(errors) == 1
    assert errors[0].severity == Severity.ERROR
    assert "slim" in errors[0].message


def test_whitelist_no_effect_warns_for_other_mode():
    """A whitelist under mode=core is ineffective (message names the mode)."""
    findings = check_project_context_injection(
        _ROOT,
        config=_config({"mode": "core", "whitelist": ["developer"]}),
        provider_config=_PROVIDERS,
    )
    hits = [f for f in findings if f.check == "project-context-injection.whitelist-no-effect"]
    assert hits
    assert any(f.severity == Severity.WARNING for f in hits)
    assert any("whitelist ignored (mode=core)" in f.message for f in hits)


def test_whitelist_no_effect_warns_for_role_without_placeholder():
    """A whitelisted role whose template has no PROJECT_CONTEXT placeholder."""
    findings = check_project_context_injection(
        _ROOT,
        config=_config({"mode": "core+whitelist", "whitelist": ["se-architect"]}),
        provider_config=_PROVIDERS,
    )
    hits = [f for f in findings
            if f.check == "project-context-injection.whitelist-no-effect"
            and "se-architect" in f.message]
    assert hits
    assert any("agents/1-generic/se-architect.md" in f.message for f in hits)


def test_pointer_missing_warns_when_artifact_lacks_pointer(tmp_path: Path):
    """A non-injected role whose rendered artifact has no pointer line."""
    _write_artifact(tmp_path, "developer", "body without pointer\n")
    findings = check_project_context_injection(
        tmp_path, config=_config({"mode": "core"}), provider_config=_PROVIDERS
    )
    hits = [f for f in findings if f.check == "project-context-injection.pointer-missing"]
    assert hits
    assert any(f.severity == Severity.WARNING for f in hits)
    assert any("developer" in f.message for f in hits)


def test_pointer_present_is_clean(tmp_path: Path):
    """Exactly one expected pointer line -> no findings at all."""
    config = _config({"mode": "core"})
    pointer = _expected_pointer(config)
    _write_artifact(tmp_path, "developer", f"head\n{pointer}\n")
    findings = check_project_context_injection(
        tmp_path, config=config, provider_config=_PROVIDERS
    )
    assert findings == []
    # Fail-soft: a malformed section shape returns no findings instead of
    # raising (the check is best-effort and must never break --validate).
    assert check_project_context_injection(
        tmp_path,
        config={"project-context-injection": {"mode": "core", "whitelist": 42}},
        provider_config=_PROVIDERS,
    ) == []


def test_pointer_missing_accepts_german_and_overridden_pointer(tmp_path: Path):
    """D8: compare against the configured pointer, never the English literal."""
    for section in (
        {"mode": "core", "pointer-language": "de"},
        {"mode": "core", "pointer-text": "See `{context_file}` for project facts."},
    ):
        config = _config(section)
        pointer = _expected_pointer(config)
        # Configured pointer -> clean.
        _write_artifact(tmp_path, "developer", f"head\n{pointer}\n")
        assert check_project_context_injection(
            tmp_path, config=config, provider_config=_PROVIDERS
        ) == []
        # English default pointer -> missing (the check must not hard-code it).
        english = _expected_pointer(_config({"mode": "core"}))
        if english != pointer:
            _write_artifact(tmp_path, "developer", f"head\n{english}\n")
            hits = [f for f in check_project_context_injection(
                tmp_path, config=config, provider_config=_PROVIDERS
            ) if f.check == "project-context-injection.pointer-missing"]
            assert hits, section


def test_pointer_missing_uses_orchestrator_roles_override(tmp_path: Path):
    """D5: the overridden set decides which roles need a pointer.

    Spec §5.4: a pointer is required only when PROJECT_CONTEXT_INJECTED=false.
    With the override, senior-developer is injected (clean without pointer)
    and orchestrator is not (needs a pointer). The plan's T11 prose swaps
    these two names; the spec and the T5 injection matrix are authoritative.
    """
    config = _config({
        "mode": "core+orchestrator",
        "orchestrator-roles": ["senior-developer"],
    })
    _write_artifact(tmp_path, "senior-developer", "no pointer\n")  # injected -> clean
    _write_artifact(tmp_path, "orchestrator", "no pointer\n")      # not injected -> finding
    findings = check_project_context_injection(
        tmp_path, config=config, provider_config=_PROVIDERS
    )
    hits = [f for f in findings if f.check == "project-context-injection.pointer-missing"]
    assert any("orchestrator" in f.message for f in hits)
    assert not any("senior-developer" in f.message for f in hits)


def test_orchestrator_role_no_template_warns():
    """D5: an orchestrator role without a template placeholder is ineffective."""
    findings = check_project_context_injection(
        _ROOT,
        config=_config({"orchestrator-roles": ["se-architect"]}),
        provider_config=_PROVIDERS,
    )
    hits = [f for f in findings
            if f.check == "project-context-injection.orchestrator-role-no-template"]
    assert hits
    assert any("se-architect" in f.message for f in hits)
    assert any("agents/1-generic/se-architect.md" in f.message for f in hits)


def test_check_registered_in_run_checks():
    """The check must be imported and called in consistency-check.py."""
    source = (_ROOT / "scripts" / "consistency-check.py").read_text(encoding="utf-8")
    assert ("from lib.consistency.project_context_injection import "
            "check_project_context_injection") in source
    assert "check_project_context_injection(root" in source
