"""IC-15 Nr. 9 (F-07, AC-19): no generated directory outside the provider's read channels.

* A provider whose rules directory is not read (no ``native-rules-dir`` /
  ``path-scoped`` in ``rules_read_channels``) and that embeds its rules in the
  shared context file no longer gets a rules directory written
  (``.mammouth/rules``, the project-root ``rules/`` of Codex). A directory
  written by an earlier version is cleaned up through its managed indexes only
  -- files the project put there itself stay.
* Personal files only where the provider reads them: Claude Code reads
  ``CLAUDE.local.md``, not ``CLAUDE.personal.md``.

Two unread directories are owned by later fixes and listed in ``_PENDING``
(path -> fix); they must disappear from that list when the fix lands.

Run: python3 -m pytest tests/test_unread_channels_removed.py -q
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import context_report as cr  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402
from lib.consistency import context_budget as cb  # noqa: E402
from lib.providers import load_provider_capabilities, load_providers_config  # noqa: E402
from tests.active_set_render import preset_config, synced_projects  # noqa: E402

_PROVIDERS = sorted(load_providers_config(REPO_ROOT, {}))
_MAPPINGS = cr.merge_provider_mappings(
    load_providers_config(REPO_ROOT, {}), load_provider_capabilities(REPO_ROOT))
# Unread directories with a planned fix of their own (not part of IC-15 Nr. 9).
_PENDING = {
    ".github/instructions": "IC-15 Nr. 3 (Task 1.29: .instructions.md suffix + applyTo)",
}


@pytest.fixture(scope="module")
def projects(tmp_path_factory):
    return synced_projects(tmp_path_factory, {p: preset_config(p) for p in _PROVIDERS})


def _sync(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync.py"), "--config",
         str(project / ".meta-config" / "project.yaml")],
        cwd=project, capture_output=True, text=True, timeout=600)


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_no_unread_channel_outside_pending_fixes(projects, provider):
    project = projects[provider]
    active = compute_active_set(preset_config(provider), REPO_ROOT, project)
    findings = cb.check_unread_channel(project, [provider], _MAPPINGS, active)
    unexpected = [f.file for f in findings if f.file not in _PENDING]
    assert not unexpected, f"{provider}: generated but unread: {unexpected}"


def test_pending_entries_are_still_real():
    # a pending entry whose provider stopped writing the directory must be removed here
    rules_dirs = {str(c.get("rules_dir")) for c in _MAPPINGS.values() if c.get("has_rules")}
    assert set(_PENDING) <= rules_dirs


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_retired_rules_dir_is_not_written(projects, provider):
    for retired in _MAPPINGS[provider].get("retired_rules_dirs") or []:
        assert not (projects[provider] / retired).exists(), f"{provider}: {retired} still written"


def test_retired_rules_dirs_are_declared_for_unread_rules():
    retired = {p: c.get("retired_rules_dirs") for p, c in _MAPPINGS.items() if c.get("retired_rules_dirs")}
    assert len(retired) >= 2, retired  # the two embedded AGENTS.md providers of IC-15 Nr. 9
    for provider, dirs in retired.items():
        caps = _MAPPINGS[provider]
        assert not caps.get("has_rules"), provider
        assert "embedded" in (caps.get("rules_read_channels") or []), provider
        assert all(isinstance(d, str) and d for d in dirs)


def test_legacy_rules_dir_cleanup_keeps_foreign_files(projects, tmp_path):
    provider = next(p for p in _PROVIDERS if _MAPPINGS[p].get("retired_rules_dirs"))
    retired = _MAPPINGS[provider]["retired_rules_dirs"][0]
    project = tmp_path / "legacy"
    shutil.copytree(projects[provider], project)
    legacy = project / retired
    legacy.mkdir(parents=True, exist_ok=True)
    (legacy / "branch-guard.md").write_text("# Branch-Guard\n", encoding="utf-8")
    (legacy / "mcp-honcho.md").write_text("# MCP: honcho\n", encoding="utf-8")
    (legacy / ".agent-meta-managed").write_text("branch-guard.md\n", encoding="utf-8")
    (legacy / ".agent-meta-managed-mcp").write_text("mcp-honcho.md\n", encoding="utf-8")
    (legacy / "own-rule.md").write_text("# Project rule\n", encoding="utf-8")
    result = _sync(project)
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    assert sorted(p.name for p in legacy.iterdir()) == ["own-rule.md"]
    # a fully managed legacy directory disappears completely
    (legacy / "own-rule.md").unlink()
    (legacy / "branch-guard.md").write_text("# Branch-Guard\n", encoding="utf-8")
    (legacy / ".agent-meta-managed").write_text("branch-guard.md\n", encoding="utf-8")
    result = _sync(project)
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    assert not legacy.exists()


def _dedicated_provider() -> str:
    return next(p for p in _PROVIDERS if _MAPPINGS[p].get("has_dedicated_context_file"))


def _uses_agents_personal_writer(provider: str) -> bool:
    """True for providers routed through the shared embedded-rules AGENTS.md writer."""
    caps = _MAPPINGS[provider]
    if "context-embedded-rules" in (caps.get("capabilities") or []):
        return True
    return any(
        p != provider
        and c.get("context_file") == caps.get("context_file")
        and "context-embedded-rules" in (c.get("capabilities") or [])
        for p, c in _MAPPINGS.items()
    )


@pytest.mark.parametrize("provider", _PROVIDERS)
def test_agents_personal_file_only_for_reading_providers(projects, provider):
    """The AGENTS.personal.md writer runs only for providers whose harness reads it."""
    if not _uses_agents_personal_writer(provider):
        pytest.skip("provider does not use the shared AGENTS.md personal writer")
    caps = _MAPPINGS[provider]
    target = projects[provider] / "AGENTS.personal.md"
    if caps.get("personal_agents_file", True):
        assert target.is_file(), f"{provider}: reads AGENTS.personal.md but none was created"
    else:
        assert not target.exists(), f"{provider}: AGENTS.personal.md written although the harness ignores it"


def test_claude_local_md_replaces_unread_personal_file(projects):
    project = projects[_dedicated_provider()]
    assert (project / "CLAUDE.local.md").is_file()
    assert not (project / "CLAUDE.personal.md").exists()
    ignored = subprocess.run(["git", "check-ignore", "-q", "CLAUDE.local.md"], cwd=project)
    assert ignored.returncode == 0, "CLAUDE.local.md must be gitignored"


def test_existing_personal_file_is_kept_and_reported(projects, tmp_path):
    project = tmp_path / "legacy-personal"
    shutil.copytree(projects[_dedicated_provider()], project)
    (project / "CLAUDE.local.md").unlink()
    (project / "CLAUDE.personal.md").write_text("# my notes\n", encoding="utf-8")
    result = _sync(project)
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    assert (project / "CLAUDE.personal.md").read_text(encoding="utf-8") == "# my notes\n"
    assert not (project / "CLAUDE.local.md").exists()
    assert "CLAUDE.local.md" in result.stdout + result.stderr
