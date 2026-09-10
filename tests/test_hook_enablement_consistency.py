"""Unit tests for lib.consistency.hook_drift.check_hook_enablement_consistency
(#712 + #714): a hook that SHOULD be active (enabled_by_default header or a
project.yaml hooks.<name>.enabled override) but is missing from disk and/or
unregistered in settings.json currently fails OPEN -- the tool call it should
guard goes through unguarded, silently.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.consistency.hook_drift import check_hook_enablement_consistency
from lib.consistency.report import Severity

_HOOK_SOURCE = """\
#!/bin/bash
# hook: my-guard
# version: 1.0.0
# event: PreToolUse
# enabled_by_default: {enabled}
exit 0
"""

_PROVIDER_CONFIG = {
    "Claude": {"hooks_dir": ".claude/hooks", "settings_file": ".claude/settings.json"},
}
_CONFIG = {"platforms": []}


def _write_source(agent_meta_root: Path, name: str, enabled: str = "true") -> None:
    d = agent_meta_root / "hooks" / "1-generic"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(_HOOK_SOURCE.format(enabled=enabled), encoding="utf-8")


def _write_managed(project_root: Path, names: list[str]) -> Path:
    d = project_root / ".claude" / "hooks"
    d.mkdir(parents=True, exist_ok=True)
    (d / ".agent-meta-managed").write_text("\n".join(names) + "\n", encoding="utf-8")
    return d


def _write_settings(project_root: Path, commands: list[str]) -> None:
    hooks = [{"hooks": [{"type": "command", "command": c}]} for c in commands]
    settings_dir = project_root / ".claude"
    settings_dir.mkdir(parents=True, exist_ok=True)
    import json
    (settings_dir / "settings.json").write_text(
        json.dumps({"hooks": {"PreToolUse": hooks}}), encoding="utf-8"
    )


def test_enabled_hook_missing_from_disk_is_an_error(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_source(agent_meta_root, "my-guard.sh", enabled="true")
    _write_managed(project_root, ["my-guard.sh"])  # deployed per index, but...
    _write_settings(project_root, ["bash .claude/hooks/my-guard.sh"])
    # ... the file itself was never actually written to disk.

    findings = check_hook_enablement_consistency(project_root, agent_meta_root, _CONFIG, _PROVIDER_CONFIG)

    assert len(findings) == 1
    assert findings[0].severity == Severity.ERROR
    assert findings[0].check == "hooks.enabled-but-missing-file"
    assert "my-guard.sh" in findings[0].message


def test_enabled_hook_deployed_but_not_registered_is_an_error(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_source(agent_meta_root, "my-guard.sh", enabled="true")
    hooks_dir = _write_managed(project_root, ["my-guard.sh"])
    (hooks_dir / "my-guard.sh").write_text(_HOOK_SOURCE.format(enabled="true"), encoding="utf-8")
    _write_settings(project_root, [])  # settings.json has no entry for it

    findings = check_hook_enablement_consistency(project_root, agent_meta_root, _CONFIG, _PROVIDER_CONFIG)

    assert len(findings) == 1
    assert findings[0].severity == Severity.ERROR
    assert findings[0].check == "hooks.enabled-but-not-registered"


def test_enabled_and_registered_hook_has_no_findings(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_source(agent_meta_root, "my-guard.sh", enabled="true")
    hooks_dir = _write_managed(project_root, ["my-guard.sh"])
    (hooks_dir / "my-guard.sh").write_text(_HOOK_SOURCE.format(enabled="true"), encoding="utf-8")
    _write_settings(project_root, ["bash .claude/hooks/my-guard.sh"])

    findings = check_hook_enablement_consistency(project_root, agent_meta_root, _CONFIG, _PROVIDER_CONFIG)

    assert findings == []


def test_disabled_by_default_hook_is_never_flagged(tmp_path):
    # This is the #714 "false reproduction" case: enabled_by_default:false and
    # no project.yaml opt-in is normal "copied but not enabled" state.
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_source(agent_meta_root, "graphify-read-guard.sh", enabled="false")
    hooks_dir = _write_managed(project_root, ["graphify-read-guard.sh"])
    (hooks_dir / "graphify-read-guard.sh").write_text(
        _HOOK_SOURCE.format(enabled="false"), encoding="utf-8"
    )
    _write_settings(project_root, [])  # correctly not registered

    findings = check_hook_enablement_consistency(project_root, agent_meta_root, _CONFIG, _PROVIDER_CONFIG)

    assert findings == []


def test_antigravity_protocol_registration_is_read_from_hooks_config_file(tmp_path):
    # Provider-agnostic (#712/#714): a provider whose hook_protocol is
    # antigravity-hooks-json registers hooks as top-level keys in its
    # hooks_config_file, NOT as `bash <dir>/<file>` in settings.json.
    # Applying the Claude convention to it would false-positive. Mirrors the
    # real Gemini config in config/ai-providers.yaml.
    import json

    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_source(agent_meta_root, "my-guard.sh", enabled="true")
    hooks_dir = project_root / ".agents" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / ".agent-meta-managed").write_text("my-guard.sh\n", encoding="utf-8")
    (hooks_dir / "my-guard.sh").write_text(_HOOK_SOURCE.format(enabled="true"), encoding="utf-8")
    (project_root / ".agents" / "hooks.json").write_text(
        json.dumps({"my-guard": {"PreToolUse": []}}), encoding="utf-8"
    )
    provider_config = {
        "Gemini": {
            "hooks_dir": ".agents/hooks",
            "settings_file": ".gemini/settings.json",
            "hook_protocol": "antigravity-hooks-json",
            "hooks_config_file": ".agents/hooks.json",
        }
    }

    findings = check_hook_enablement_consistency(project_root, agent_meta_root, _CONFIG, provider_config)

    assert findings == []


def test_antigravity_protocol_unregistered_hook_is_still_flagged(tmp_path):
    import json

    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_source(agent_meta_root, "my-guard.sh", enabled="true")
    hooks_dir = project_root / ".agents" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / ".agent-meta-managed").write_text("my-guard.sh\n", encoding="utf-8")
    (hooks_dir / "my-guard.sh").write_text(_HOOK_SOURCE.format(enabled="true"), encoding="utf-8")
    (project_root / ".agents" / "hooks.json").write_text(json.dumps({}), encoding="utf-8")
    provider_config = {
        "Gemini": {
            "hooks_dir": ".agents/hooks",
            "settings_file": ".gemini/settings.json",
            "hook_protocol": "antigravity-hooks-json",
            "hooks_config_file": ".agents/hooks.json",
        }
    }

    findings = check_hook_enablement_consistency(project_root, agent_meta_root, _CONFIG, provider_config)

    assert len(findings) == 1
    assert findings[0].check == "hooks.enabled-but-not-registered"


def test_project_yaml_opt_in_override_is_respected(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_source(agent_meta_root, "dod-push-check.sh", enabled="false")
    _write_managed(project_root, ["dod-push-check.sh"])  # not deployed, no settings entry
    _write_settings(project_root, [])
    config = {"platforms": [], "hooks": {"dod-push-check": {"enabled": True}}}

    findings = check_hook_enablement_consistency(project_root, agent_meta_root, config, _PROVIDER_CONFIG)

    assert len(findings) == 1
    assert findings[0].check == "hooks.enabled-but-missing-file"
