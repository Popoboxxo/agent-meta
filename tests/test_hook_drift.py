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

from lib.consistency.hook_drift import check_stale_deployed_hooks
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
