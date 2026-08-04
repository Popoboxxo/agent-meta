"""Tests for scripts/lib/consistency/orchestrator_strict.py.

Covers Entscheidung 7 of docs/superpowers/specs/2026-08-02-agent-orchestration-refinement-design.md:
`orchestrator.strict: true` has zero runtime effect on providers whose
config/ai-providers.yaml entry has `has_hooks: false` (e.g. Opencode, Gemini) --
this must surface as a WARNING, not stay a silent no-op.

Run: python -m pytest tests/test_orchestrator_strict_visibility.py -v
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.consistency.orchestrator_strict import check_orchestrator_strict_hook_support
from lib.consistency.report import Severity

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _provider_config():
    from lib.providers import load_providers_config
    return load_providers_config(_REPO_ROOT)


def test_warns_for_active_provider_without_hook_support():
    config = {"ai-providers": ["Claude", "Opencode"],
              "orchestrator": {"enabled": True, "strict": True}}
    findings = check_orchestrator_strict_hook_support(_REPO_ROOT, config, _provider_config())
    assert any(f.severity == Severity.WARNING and "Opencode" in f.message for f in findings)


def test_no_warning_when_only_hook_capable_providers_active():
    config = {"ai-providers": ["Claude"],
              "orchestrator": {"enabled": True, "strict": True}}
    findings = check_orchestrator_strict_hook_support(_REPO_ROOT, config, _provider_config())
    assert findings == []


def test_no_warning_when_strict_mode_off():
    config = {"ai-providers": ["Claude", "Opencode"],
              "orchestrator": {"enabled": True, "strict": False}}
    findings = check_orchestrator_strict_hook_support(_REPO_ROOT, config, _provider_config())
    assert findings == []


def test_provider_override_narrows_strict_mode_to_claude_only():
    config = {
        "ai-providers": ["Claude", "Opencode"],
        "orchestrator": {
            "enabled": True,
            "strict": True,
            "provider-overrides": {"Opencode": {"mode": "advisory"}},
        },
    }
    findings = check_orchestrator_strict_hook_support(_REPO_ROOT, config, _provider_config())
    assert findings == []


def test_provider_override_turns_strict_on_despite_global_off():
    """Provider-overrides must be able to widen strict mode too, not just narrow it --
    global orchestrator.strict is False here, but the Opencode override sets
    mode: 'strict' explicitly."""
    config = {
        "ai-providers": ["Claude", "Opencode"],
        "orchestrator": {
            "enabled": True,
            "strict": False,
            "provider-overrides": {"Opencode": {"mode": "strict"}},
        },
    }
    findings = check_orchestrator_strict_hook_support(_REPO_ROOT, config, _provider_config())
    assert any(f.severity == Severity.WARNING and "Opencode" in f.message for f in findings)


def test_global_mode_key_triggers_warning_without_legacy_booleans():
    """Regression test for the missing precedence tier: orchestrator.mode (global)
    must be honored even when no legacy strict/enabled booleans are present at all."""
    config = {
        "ai-providers": ["Claude", "Opencode"],
        "orchestrator": {"mode": "strict"},
    }
    findings = check_orchestrator_strict_hook_support(_REPO_ROOT, config, _provider_config())
    assert any(f.severity == Severity.WARNING and "Opencode" in f.message for f in findings)
