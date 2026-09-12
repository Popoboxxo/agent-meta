"""Consistency checks for the subagent-permission policy (Feature A).

Covers B1 (capability source), M5 (per-file template check) and m2/n1
(flag-not-strippable scoping), all WARNING/ERROR-only, never SystemExit (M3).
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.consistency.report import Severity  # noqa: E402
from lib.consistency.subagent_permissions import (  # noqa: E402
    check_subagent_permission_support,
    check_subagent_permission_templates,
)
from lib.providers import load_providers_config  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PROVIDER_CONFIG = load_providers_config(_REPO_ROOT)


def _checks(findings) -> set[str]:
    return {f.check for f in findings}


def test_b1_continue_strict_warns_no_dispatch_surface():
    config = {"ai-providers": ["Continue"], "subagent_permissions": {"mode": "strict"}}
    findings = check_subagent_permission_support(_REPO_ROOT, _REPO_ROOT, config, _PROVIDER_CONFIG)
    assert any(
        f.check == "subagent-permissions.no-dispatch-surface" and f.severity == Severity.WARNING
        for f in findings
    )


def test_b1_opencode_strict_warns_no_hook_support():
    config = {"ai-providers": ["Opencode"], "subagent_permissions": {"mode": "strict"}}
    findings = check_subagent_permission_support(_REPO_ROOT, _REPO_ROOT, config, _PROVIDER_CONFIG)
    checks = _checks(findings)
    assert "subagent-permissions.no-hook-support" in checks
    assert "subagent-permissions.no-dispatch-surface" not in checks


def test_b1_claude_and_gemini_strict_have_no_dispatch_warning():
    # Claude/Gemini capabilities list in ai-providers.yaml has no
    # subagent_dispatch entry; the check reads provider-capabilities.yaml.
    for provider in ("Claude", "Gemini"):
        config = {"ai-providers": [provider], "subagent_permissions": {"mode": "strict"}}
        findings = check_subagent_permission_support(
            _REPO_ROOT, _REPO_ROOT, config, _PROVIDER_CONFIG
        )
        assert "subagent-permissions.no-dispatch-surface" not in _checks(findings)


def test_invalid_mode_warns_without_exit():
    config = {"ai-providers": ["Claude"], "subagent_permissions": {"mode": "sometimes"}}
    findings = check_subagent_permission_support(_REPO_ROOT, _REPO_ROOT, config, _PROVIDER_CONFIG)
    assert any(f.check == "subagent-permissions.invalid-mode" for f in findings)


def test_off_has_no_findings():
    config = {"ai-providers": ["Claude"], "subagent_permissions": {"mode": "off"}}
    assert check_subagent_permission_support(_REPO_ROOT, _REPO_ROOT, config, _PROVIDER_CONFIG) == []


def test_templates_current_repo_are_clean():
    assert check_subagent_permission_templates(_REPO_ROOT) == []


# ── framework-drift fixtures ────────────────────────────────────────────────

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def _templates_fixture(root: Path, *, rule: str, orchestrator: str) -> None:
    _write(root / "config/provider-capabilities.yaml", """\
        capabilities:
          Claude:
            subagent_dispatch: true
        """)
    _write(root / "rules/1-generic/a2a-delegation-gates.md", rule)
    _write(root / "agents/1-generic/orchestrator.md", orchestrator)


_GOOD_RULE = """\
    {{#if SUBAGENT_PERMISSIONS_STRICT}}
    ## Subagent Permission Policy (strict)
    {{/if}}
    {{#if SUBAGENT_PERMISSIONS_WARN}}
    ## Subagent Permission Policy (warn)
    {{/if}}
    """
_GOOD_ORCH = """\
    ## 5.
    {{#if SUBAGENT_PERMISSIONS_ENABLED}}
    {{SUBAGENT_PERMISSIONS_BLOCK}}
    {{/if}}
    """


def test_m5_rule_missing_marker_errors_only_for_rule(tmp_path):
    _templates_fixture(tmp_path, rule="## no markers here\n", orchestrator=_GOOD_ORCH)
    findings = check_subagent_permission_templates(tmp_path)
    errors = [f for f in findings if f.severity == Severity.ERROR]
    assert len(errors) == 1
    assert errors[0].check == "subagent-permissions.template-missing"
    assert errors[0].file == "rules/1-generic/a2a-delegation-gates.md"


def test_m5_orchestrator_missing_block_errors_only_for_orchestrator(tmp_path):
    _templates_fixture(tmp_path, rule=_GOOD_RULE, orchestrator="## no block here\n")
    findings = check_subagent_permission_templates(tmp_path)
    errors = [f for f in findings if f.severity == Severity.ERROR]
    assert len(errors) == 1
    assert errors[0].file == "agents/1-generic/orchestrator.md"


def test_unknown_flag_is_error(tmp_path):
    _templates_fixture(
        tmp_path,
        rule=_GOOD_RULE + "{{#if SUBAGENT_PERMISSIONS_UNKNOWN}}x{{/if}}\n",
        orchestrator=_GOOD_ORCH,
    )
    findings = check_subagent_permission_templates(tmp_path)
    assert any(f.check == "subagent-permissions.flag-not-strippable" for f in findings)


def test_mode_flag_is_not_flagged(tmp_path):
    _templates_fixture(
        tmp_path,
        rule=_GOOD_RULE + "{{#if SUBAGENT_PERMISSIONS_MODE}}x{{/if}}\n",
        orchestrator=_GOOD_ORCH,
    )
    findings = check_subagent_permission_templates(tmp_path)
    assert not any(f.check == "subagent-permissions.flag-not-strippable" for f in findings)


def test_no_dispatch_surface_skips_template_checks(tmp_path):
    _write(tmp_path / "config/provider-capabilities.yaml", "capabilities:\n  Continue:\n    subagent_dispatch: false\n")
    assert check_subagent_permission_templates(tmp_path) == []
