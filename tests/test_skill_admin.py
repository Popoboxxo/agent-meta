"""Tests for scripts/lib/skill_admin.py::add_skill's config-loading cascade.

Regression coverage for a code-review finding: add_skill() used to hand-roll
its own yaml/legacy-yaml/json fallback cascade instead of reusing
lib.io._load_yaml_or_json — which meant a malformed config file raised an
unhandled exception here instead of the shared, well-defined SyncError every
other loader in the codebase produces (including skills.py reading the exact
same three paths via load_external_skills_config).
"""

from pathlib import Path

import pytest
import yaml

from scripts.lib.io import SyncError
from scripts.lib.log import SyncLog
from scripts.lib.skill_admin import add_skill


def _run_add_skill(agent_meta_root: Path, dry_run: bool) -> None:
    add_skill(
        agent_meta_root=agent_meta_root,
        repo_url="https://example.invalid/org/some-skill.git",
        skill_name="some-skill",
        source_path="skills/some-skill",
        role="some-skill-agent",
        entry="SKILL.md",
        log=SyncLog(),
        dry_run=dry_run,
    )


def _fake_existing_submodule(agent_meta_root: Path) -> None:
    # Pre-create the submodule dir so add_skill's "already exists" branch
    # fires and the real `git clone` subprocess call is never reached —
    # lets these tests exercise the config-loading cascade with dry_run=False
    # (needed to assert on the write) without any network/git dependency.
    (agent_meta_root / "external" / "some-skill").mkdir(parents=True)
    # config/ always exists in a real agent-meta checkout (holds
    # ai-providers.yaml, mcp-registry.yaml, ...); add_skill's bootstrap path
    # doesn't mkdir it itself, so mirror that real precondition here.
    (agent_meta_root / "config").mkdir(exist_ok=True)


def test_add_skill_raises_sync_error_on_malformed_yaml(tmp_path):
    config_path = tmp_path / "config" / "skills-registry.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text("repos: [this is: not: valid: yaml", encoding="utf-8")

    with pytest.raises(SyncError):
        _run_add_skill(tmp_path, dry_run=True)


def test_add_skill_reads_legacy_path_writes_new_path(tmp_path):
    _fake_existing_submodule(tmp_path)
    legacy_path = tmp_path / "external-skills.config.yaml"
    legacy_path.write_text(
        yaml.dump({"repos": {"old-repo": {"repo": "https://x"}}, "skills": {}}),
        encoding="utf-8",
    )

    _run_add_skill(tmp_path, dry_run=False)

    new_path = tmp_path / "config" / "skills-registry.yaml"
    assert new_path.exists()
    data = yaml.safe_load(new_path.read_text(encoding="utf-8"))
    # Existing legacy entry preserved, new skill added, written to the NEW
    # path (not back to legacy_path) — matches the pre-refactor behavior.
    assert "old-repo" in data["repos"]
    assert "some-skill" in data["skills"]


def test_add_skill_bootstraps_when_no_config_exists(tmp_path):
    _fake_existing_submodule(tmp_path)

    _run_add_skill(tmp_path, dry_run=False)

    new_path = tmp_path / "config" / "skills-registry.yaml"
    assert new_path.exists()
    data = yaml.safe_load(new_path.read_text(encoding="utf-8"))
    assert "some-skill" in data["skills"]
