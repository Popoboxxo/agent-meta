"""Consistency-check tests for scripts/lib/consistency/repo_containment.py.

Two checks mirror the orchestrator-strict split (spec §4.4):

* ``check_repo_containment_support`` -- WARNING-only, project/provider-aware.
  It fires when containment is effectively ON for a provider with no mirrored
  PreToolUse hook (hook-capable: Claude/Gemini; hook-less: Opencode/Continue/...).
* ``check_repo_containment_templates`` -- ERROR-only framework drift for the
  wrapper/impl header markers and the rule-template placeholders.

Also asserts the check is registered in scripts/consistency-check.py.

Run: python -m pytest tests/test_repo_containment_consistency.py -v
"""

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.consistency.repo_containment import (
    HOOK_IMPL_RELPATH,
    HOOK_WRAPPER_RELPATH,
    RULE_TEMPLATE_RELPATH,
    check_repo_containment_support,
    check_repo_containment_templates,
)
from lib.consistency.report import Severity
from lib.providers import load_providers_config


def _provider_config() -> dict:
    return load_providers_config(_REPO_ROOT)


# --- Support WARNING ---------------------------------------------------


def test_warns_for_hookless_provider_with_containment_on():
    config = {"ai-providers": ["Opencode"]}
    findings = check_repo_containment_support(
        _REPO_ROOT, config, _provider_config()
    )
    assert any(
        f.severity == Severity.WARNING
        and f.check == "repo-containment.no-hook-support"
        and "Opencode" in f.message
        for f in findings
    )


def test_default_on_warns_even_without_explicit_block():
    """Default ON means the warning fires on a fresh project, not only when the
    project wrote a block (spec §9.1)."""
    findings = check_repo_containment_support(
        _REPO_ROOT, {"ai-providers": ["Continue"]}, _provider_config()
    )
    assert any("Continue" in f.message for f in findings)


def test_no_warning_for_hook_capable_providers():
    for provider in ("Claude", "Gemini"):
        findings = check_repo_containment_support(
            _REPO_ROOT, {"ai-providers": [provider]}, _provider_config()
        )
        assert findings == [], provider


def test_no_warning_when_containment_disabled():
    config = {
        "ai-providers": ["Opencode"],
        "repo_containment": {"enabled": False},
    }
    assert check_repo_containment_support(
        _REPO_ROOT, config, _provider_config()
    ) == []


def test_no_warning_when_provider_override_disables_it():
    config = {
        "ai-providers": ["Opencode"],
        "repo_containment": {
            "enabled": True,
            "provider-overrides": {"Opencode": {"enabled": False}},
        },
    }
    assert check_repo_containment_support(
        _REPO_ROOT, config, _provider_config()
    ) == []


def test_warns_when_provider_override_re_enables_hookless_provider():
    config = {
        "ai-providers": ["Opencode"],
        "repo_containment": {
            "enabled": False,
            "provider-overrides": {"Opencode": {"enabled": True}},
        },
    }
    findings = check_repo_containment_support(
        _REPO_ROOT, config, _provider_config()
    )
    assert any("Opencode" in f.message for f in findings)


# --- Template drift ERROR ----------------------------------------------


def test_real_framework_templates_have_no_drift():
    assert check_repo_containment_templates(_REPO_ROOT) == []


def test_missing_templates_are_errors(tmp_path):
    findings = check_repo_containment_templates(tmp_path)
    files = {f.file for f in findings}
    assert HOOK_WRAPPER_RELPATH in files
    assert HOOK_IMPL_RELPATH in files
    assert all(f.severity == Severity.ERROR for f in findings)
    assert all(f.check == "repo-containment.template-drift" for f in findings)
    # The rule template is gated on existence: absent -> no finding.
    assert RULE_TEMPLATE_RELPATH not in files


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_wrapper_marker_drift_is_error(tmp_path):
    _write(
        tmp_path,
        HOOK_WRAPPER_RELPATH,
        "# hook: wrong-name\n# version: 1.0.0\n# event: PreToolUse\n"
        "# enabled_by_default: true\n",
    )
    _write(tmp_path, HOOK_IMPL_RELPATH, "# version: 1.0.0\n")
    findings = check_repo_containment_templates(tmp_path)
    assert any(
        f.severity == Severity.ERROR and f.file == HOOK_WRAPPER_RELPATH
        for f in findings
    )


def test_impl_version_marker_drift_is_error(tmp_path):
    _write(
        tmp_path,
        HOOK_WRAPPER_RELPATH,
        "# hook: repo-containment\n# version: 1.0.0\n# event: PreToolUse\n"
        "# enabled_by_default: true\n",
    )
    _write(tmp_path, HOOK_IMPL_RELPATH, "#!/bin/bash\n")
    findings = check_repo_containment_templates(tmp_path)
    assert any(
        f.severity == Severity.ERROR and f.file == HOOK_IMPL_RELPATH
        for f in findings
    )


def test_rule_template_without_placeholder_is_error(tmp_path):
    _write(
        tmp_path,
        HOOK_WRAPPER_RELPATH,
        "# hook: repo-containment\n# version: 1.0.0\n# event: PreToolUse\n"
        "# enabled_by_default: true\n",
    )
    _write(tmp_path, HOOK_IMPL_RELPATH, "# version: 1.0.0\n")
    _write(tmp_path, RULE_TEMPLATE_RELPATH, "No placeholders here.\n")
    findings = check_repo_containment_templates(tmp_path)
    assert any(
        f.severity == Severity.ERROR and f.file == RULE_TEMPLATE_RELPATH
        for f in findings
    )


def test_rule_template_with_placeholder_is_accepted(tmp_path):
    _write(
        tmp_path,
        HOOK_WRAPPER_RELPATH,
        "# hook: repo-containment\n# version: 1.0.0\n# event: PreToolUse\n"
        "# enabled_by_default: true\n",
    )
    _write(tmp_path, HOOK_IMPL_RELPATH, "# version: 1.0.0\n")
    _write(tmp_path, RULE_TEMPLATE_RELPATH, "{{REPO_CONTAINMENT_ENABLED}}\n")
    assert check_repo_containment_templates(tmp_path) == []


# --- Registration -------------------------------------------------------


def test_check_is_registered_in_consistency_check():
    source = (_REPO_ROOT / "scripts" / "consistency-check.py").read_text(
        encoding="utf-8"
    )
    assert "from lib.consistency.repo_containment import" in source
    assert "check_repo_containment_templates" in source
    assert "check_repo_containment_templates(_AGENT_META_ROOT)" in source
