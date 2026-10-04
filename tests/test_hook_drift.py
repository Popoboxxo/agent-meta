"""Unit tests for lib.consistency.hook_drift.check_stale_deployed_hooks (#630, #650).

Covers the version-drift comparison between a project's deployed hook copy
(``.claude/hooks/<name>.sh``) and the current ``hooks/1-generic/`` source:
version match, version mismatch (WARNING), missing deployed file, and a
missing ``.agent-meta-managed`` index (nothing to compare against).
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.consistency.hook_drift import (
    _registered_hook_stems,
    check_hook_enablement_consistency,
    check_stale_deployed_hooks,
)
from lib.consistency.report import Severity

_HOOK_SOURCE = """\
#!/bin/bash
# hook: my-hook
# version: {version}
# event: PreToolUse
exit 0
"""


def _write_source(agent_meta_root: Path, name: str, version: str) -> None:
    d = agent_meta_root / "hooks" / "1-generic"
    d.mkdir(parents=True, exist_ok=True)
    (d / name).write_text(_HOOK_SOURCE.format(version=version), encoding="utf-8")


def _write_deployed(project_root: Path, name: str, version: str, managed: list[str]) -> Path:
    d = project_root / ".claude" / "hooks"
    d.mkdir(parents=True, exist_ok=True)
    deployed = d / name
    deployed.write_text(_HOOK_SOURCE.format(version=version), encoding="utf-8")
    (d / ".agent-meta-managed").write_text("\n".join(managed) + "\n", encoding="utf-8")
    return deployed


_PROVIDER_CONFIG = {"claude": {"hooks_dir": ".claude/hooks"}}
_CONFIG = {"platforms": []}


def test_no_findings_when_deployed_version_matches_source(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_source(agent_meta_root, "my-hook.sh", "2.0.0")
    _write_deployed(project_root, "my-hook.sh", "2.0.0", ["my-hook.sh"])

    findings = check_stale_deployed_hooks(project_root, agent_meta_root, _CONFIG, _PROVIDER_CONFIG)

    assert findings == []


def test_warning_when_deployed_version_is_stale(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_source(agent_meta_root, "my-hook.sh", "2.0.0")
    _write_deployed(project_root, "my-hook.sh", "1.0.0", ["my-hook.sh"])

    findings = check_stale_deployed_hooks(project_root, agent_meta_root, _CONFIG, _PROVIDER_CONFIG)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity == Severity.WARNING
    assert finding.check == "hooks.stale-deployed-version"
    assert finding.file == ".claude/hooks/my-hook.sh"
    assert "1.0.0" in finding.message
    assert "2.0.0" in finding.message


def test_no_findings_when_deployed_file_is_missing(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_source(agent_meta_root, "my-hook.sh", "2.0.0")
    # Managed index references a hook that was deleted/never deployed.
    hooks_dir = project_root / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / ".agent-meta-managed").write_text("my-hook.sh\n", encoding="utf-8")

    findings = check_stale_deployed_hooks(project_root, agent_meta_root, _CONFIG, _PROVIDER_CONFIG)

    assert findings == []


def test_no_findings_when_managed_index_is_absent(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    _write_source(agent_meta_root, "my-hook.sh", "2.0.0")
    hooks_dir = project_root / ".claude" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / "my-hook.sh").write_text(_HOOK_SOURCE.format(version="1.0.0"), encoding="utf-8")
    # No .agent-meta-managed index -> project-owned hook, must not be judged.

    findings = check_stale_deployed_hooks(project_root, agent_meta_root, _CONFIG, _PROVIDER_CONFIG)

    assert findings == []


def test_no_findings_when_no_hook_sources_exist(tmp_path):
    agent_meta_root = tmp_path / "agent-meta"  # hooks/1-generic never created
    project_root = tmp_path / "project"
    _write_deployed(project_root, "my-hook.sh", "1.0.0", ["my-hook.sh"])

    findings = check_stale_deployed_hooks(project_root, agent_meta_root, _CONFIG, _PROVIDER_CONFIG)

    assert findings == []


_ANTIGRAVITY_PROVIDER_CONFIG = {"Codex": {
    "hooks_dir": ".agents/hooks",
    "hook_protocol": "antigravity-hooks-json",
    "hooks_config_file": ".agents/hooks.json",
}}


def test_registered_hook_stems_ignores_underscore_metadata_keys(tmp_path):
    """A `_`-prefixed top-level key in hooks.json is metadata (hooks.py's
    `_agent-meta` provenance marker), never a hook registration (F5)."""
    project_root = tmp_path / "project"
    cfg_dir = project_root / ".agents"
    cfg_dir.mkdir(parents=True)
    (cfg_dir / "hooks.json").write_text(
        "{\n"
        '  "_agent-meta": {"managed": "agent-meta managed — do not edit manually"},\n'
        '  "orchestrator-guard": {"PreToolUse": []}\n'
        "}\n",
        encoding="utf-8",
    )
    pc = {"hook_protocol": "antigravity-hooks-json", "hooks_config_file": ".agents/hooks.json"}

    stems = _registered_hook_stems(project_root, pc, ".agents/hooks")

    assert stems == {"orchestrator-guard"}
    assert "_agent-meta" not in stems


def test_underscore_managed_hook_key_is_not_a_registration(tmp_path):
    """A managed hook whose only hooks.json key is `_`-prefixed (the metadata
    convention) must still be flagged enabled-but-not-registered — a foreign
    `_`-prefixed key must not masquerade as its registration (F5)."""
    agent_meta_root = tmp_path / "agent-meta"
    project_root = tmp_path / "project"
    source_dir = agent_meta_root / "hooks" / "1-generic"
    source_dir.mkdir(parents=True)
    (source_dir / "_hidden.sh").write_text(
        "#!/bin/bash\n"
        "# hook: _hidden\n"
        "# version: 2.0.0\n"
        "# event: PreToolUse\n"
        "# enabled_by_default: true\n"
        "exit 0\n",
        encoding="utf-8",
    )
    hooks_dir = project_root / ".agents" / "hooks"
    hooks_dir.mkdir(parents=True)
    (hooks_dir / ".agent-meta-managed").write_text("_hidden.sh\n", encoding="utf-8")
    (hooks_dir / "_hidden.sh").write_text("#!/bin/bash\nexit 0\n", encoding="utf-8")
    (project_root / ".agents" / "hooks.json").write_text(
        "{\n"
        '  "_agent-meta": {"managed": "agent-meta managed — do not edit manually"},\n'
        '  "_hidden": {"PreToolUse": []}\n'
        "}\n",
        encoding="utf-8",
    )

    findings = check_hook_enablement_consistency(
        project_root, agent_meta_root, _CONFIG, _ANTIGRAVITY_PROVIDER_CONFIG)

    assert any(f.check == "hooks.enabled-but-not-registered" for f in findings), findings
