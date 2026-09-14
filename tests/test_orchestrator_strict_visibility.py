"""Tests for scripts/lib/consistency/orchestrator_strict.py.

Covers Entscheidung 7 of docs/superpowers/specs/2026-08-02-agent-orchestration-refinement-design.md:
`orchestrator.strict: true` has zero runtime effect on providers whose
config/ai-providers.yaml entry has no hook support (e.g. Opencode) --
this must surface as a finding, not stay a silent no-op.

Severity is derived from the resolved runtime-gate tier
(SPEC-OPENCODE-RUNTIME-GATE-2026-09-13, IC-11):
- `permission` -> INFO (partially enforced; delegation provenance not enforced)
- `advisory`   -> WARNING by default, ERROR when
  `orchestrator.require-runtime-gate` is true
- `hook` / `plugin` -> no finding

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


def _check(config, agent_meta_root=None):
    return check_orchestrator_strict_hook_support(
        _REPO_ROOT, config, _provider_config(),
        _REPO_ROOT if agent_meta_root is None else agent_meta_root,
    )


def test_warns_for_active_provider_without_hook_support():
    """AC-13: Opencode is now the `permission` tier -> INFO, not WARNING."""
    config = {"ai-providers": ["Claude", "Opencode"],
              "orchestrator": {"enabled": True, "strict": True}}
    findings = _check(config)
    assert any(f.severity == Severity.INFO and "Opencode" in f.message for f in findings)


def test_no_warning_when_only_hook_capable_providers_active():
    config = {"ai-providers": ["Claude"],
              "orchestrator": {"enabled": True, "strict": True}}
    assert _check(config) == []


def test_no_warning_when_strict_mode_off():
    config = {"ai-providers": ["Claude", "Opencode"],
              "orchestrator": {"enabled": True, "strict": False}}
    assert _check(config) == []


def test_provider_override_narrows_strict_mode_to_claude_only():
    config = {
        "ai-providers": ["Claude", "Opencode"],
        "orchestrator": {
            "enabled": True,
            "strict": True,
            "provider-overrides": {"Opencode": {"mode": "advisory"}},
        },
    }
    assert _check(config) == []


def test_provider_override_turns_strict_on_despite_global_off():
    """Provider-overrides must be able to widen strict mode too, not just narrow it --
    global orchestrator.strict is False here, but the Opencode override sets
    mode: 'strict' explicitly. AC-13: Opencode -> INFO."""
    config = {
        "ai-providers": ["Claude", "Opencode"],
        "orchestrator": {
            "enabled": True,
            "strict": False,
            "provider-overrides": {"Opencode": {"mode": "strict"}},
        },
    }
    assert any(f.severity == Severity.INFO and "Opencode" in f.message for f in _check(config))


def test_global_mode_key_triggers_warning_without_legacy_booleans():
    """Regression test for the missing precedence tier: orchestrator.mode (global)
    must be honored even when no legacy strict/enabled booleans are present at all.
    AC-13: Opencode -> INFO."""
    config = {
        "ai-providers": ["Claude", "Opencode"],
        "orchestrator": {"mode": "strict"},
    }
    assert any(f.severity == Severity.INFO and "Opencode" in f.message for f in _check(config))


def test_malformed_provider_overrides_null_does_not_crash():
    """provider-overrides: null (whole key empty) must not raise AttributeError.
    AC-13: Opencode -> INFO."""
    config = {
        "ai-providers": ["Claude", "Opencode"],
        "orchestrator": {"enabled": True, "strict": True, "provider-overrides": None},
    }
    assert any(f.severity == Severity.INFO and "Opencode" in f.message for f in _check(config))


def test_malformed_orchestrator_as_plain_string_does_not_crash():
    """orchestrator: "strict" (a plain string instead of a dict) must not raise
    AttributeError -- treated as absent/malformed, no finding (safer than crashing)."""
    config = {"ai-providers": ["Claude", "Opencode"], "orchestrator": "strict"}
    assert _check(config) == []


def test_malformed_provider_override_null_entry_does_not_crash():
    """provider-overrides: {Opencode: null} must not raise AttributeError when
    resolving the override for the active 'Opencode' provider. AC-13: INFO."""
    config = {
        "ai-providers": ["Claude", "Opencode"],
        "orchestrator": {
            "enabled": True,
            "strict": True,
            "provider-overrides": {"Opencode": None},
        },
    }
    assert any(f.severity == Severity.INFO and "Opencode" in f.message for f in _check(config))


# ---------------------------------------------------------------------------
# Tier-derived severity (SPEC-OPENCODE-RUNTIME-GATE-2026-09-13, IC-11/AC-12)
# ---------------------------------------------------------------------------


def test_permission_tier_yields_info():
    """AC-12: a `permission`-tier provider yields INFO stating partial enforcement."""
    config = {"ai-providers": ["Opencode"], "orchestrator": {"mode": "strict"}}
    findings = _check(config)
    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity == Severity.INFO
    assert finding.check == "orchestrator-strict.no-hook-support"
    assert "partial" in finding.message
    assert "delegation provenance" in finding.message


def test_advisory_tier_warning_by_default_error_with_optin():
    """AC-12: an `advisory`-tier provider warns by default and errors with the opt-in."""
    base = {"ai-providers": ["Mammouth"], "orchestrator": {"mode": "strict"}}
    default_findings = _check(base)
    assert any(f.severity == Severity.WARNING and "Mammouth" in f.message
               for f in default_findings)

    optin = {
        "ai-providers": ["Mammouth"],
        "orchestrator": {"mode": "strict", "require-runtime-gate": True},
    }
    optin_findings = _check(optin)
    assert any(f.severity == Severity.ERROR and "Mammouth" in f.message
               for f in optin_findings)


def test_hook_tier_yields_no_finding():
    """AC-12: hook/plugin providers yield no finding."""
    config = {"ai-providers": ["Claude", "Gemini"], "orchestrator": {"mode": "strict"}}
    assert _check(config) == []


def test_unreadable_capabilities_registry_degrades_to_advisory(tmp_path):
    """Fail-safe (IC-11): a missing capability registry must not crash and must
    fall back to `advisory` (WARNING), never a stronger guarantee."""
    config = {"ai-providers": ["Opencode"], "orchestrator": {"mode": "strict"}}
    findings = _check(config, agent_meta_root=tmp_path)
    assert any(f.severity == Severity.WARNING and "Opencode" in f.message
               for f in findings)


# ---------------------------------------------------------------------------
# Gemini Antigravity hook protocol (issue #674 Phase 3.1) — the
# orchestrator-strict.no-hook-support finding must disappear for Gemini while
# Opencode/Mammouth keep it.
# ---------------------------------------------------------------------------

def test_gemini_no_warning_after_antigravity_hook_protocol():
    config = {"ai-providers": ["Claude", "Gemini"],
              "orchestrator": {"enabled": True, "strict": True}}
    findings = _check(config)
    assert not any("Gemini" in f.message for f in findings), (
        "Gemini now mirrors hooks via hook_protocol antigravity-hooks-json "
        "(issue #674 Phase 3.1) — the no-hook-support warning must be gone"
    )
    assert findings == []


def test_gemini_and_opencode_active_warning_only_for_opencode():
    """AC-13: Gemini (hook) -> no finding; Opencode (permission) -> INFO."""
    config = {"ai-providers": ["Gemini", "Opencode"],
              "orchestrator": {"mode": "strict"}}
    findings = _check(config)
    assert any(f.severity == Severity.INFO and "Opencode" in f.message for f in findings)
    assert not any("Gemini" in f.message for f in findings)


def test_mammouth_still_warns_without_hook_protocol():
    config = {"ai-providers": ["Claude", "Mammouth"],
              "orchestrator": {"mode": "strict"}}
    findings = _check(config)
    assert any(f.severity == Severity.WARNING and "Mammouth" in f.message for f in findings)
