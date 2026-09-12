"""Integration test: the two generated-file-drift stages are wired into
_handle_sync in the right order relative to _sync_stage_per_provider (the
stage that does all the actual overwriting) -- see
docs/superpowers/specs/2026-09-07-generated-file-drift-detection-design.md
("early scan before overwrite, late capture after everything is written").
"""
from __future__ import annotations

import inspect
import sys
from pathlib import Path

# cli_commands / sync_pipeline use absolute `from lib.xxx import ...` imports
# (not relative), so `lib` must be importable as a top-level package -- same
# bootstrap as tests/test_sync_test_plugin_cli.py.
REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import cli_commands  # noqa: E402


def test_drift_scan_stage_runs_before_per_provider_write_stage() -> None:
    source = inspect.getsource(cli_commands._handle_sync)
    scan_pos = source.index("_sync_stage_generated_file_drift_scan(")
    per_provider_pos = source.index("_sync_stage_per_provider(")
    assert scan_pos < per_provider_pos, (
        "the drift-scan stage must run BEFORE _sync_stage_per_provider "
        "overwrites anything, or it can never see a manual edit"
    )


def test_hash_capture_stage_runs_after_every_other_stage() -> None:
    source = inspect.getsource(cli_commands._handle_sync)
    capture_pos = source.index("_sync_stage_generated_file_hash_capture(")
    other_stage_calls = [
        "_sync_stage_per_provider(", "_sync_stage_drift_and_plugins(",
        "_sync_stage_knowledge_and_isolation(", "_sync_stage_gitignore(",
        "_sync_stage_config_audit(",
    ]
    for call in other_stage_calls:
        assert capture_pos > source.index(call), (
            f"hash-capture must run after {call} so it captures fully "
            "post-write state"
        )


def _write(root, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def test_drift_scan_stage_skips_and_warns_nothing_when_disabled(tmp_path) -> None:
    from scripts.lib.log import SyncLog
    from scripts.lib.sync_pipeline import _sync_stage_generated_file_drift_scan
    import argparse

    project_root = tmp_path / "project"
    from scripts.lib.generated_file_drift import content_hash
    _write(project_root, ".claude/agents/developer.md", "edited by hand")
    index_path = project_root / ".claude" / "agents" / ".agent-meta-managed"
    index_path.write_text("developer.md\n", encoding="utf-8")
    hashes_path = project_root / ".meta-config" / "generated-file-hashes.json"
    hashes_path.parent.mkdir(parents=True, exist_ok=True)
    hashes_path.write_text(
        '{"version": 1, "hashes": {".claude/agents/developer.md": "' + content_hash("original") + '"}}',
        encoding="utf-8",
    )
    provider_config = {"Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}}
    log = SyncLog()
    args = argparse.Namespace(dry_run=False)

    _sync_stage_generated_file_drift_scan(
        tmp_path / "agent-meta", project_root, {"drift-detection": {"enabled": False}},
        provider_config, args, log,
    )

    assert log.warnings == []


def test_hash_capture_stage_writes_nothing_when_disabled(tmp_path) -> None:
    from scripts.lib.log import SyncLog
    from scripts.lib.sync_pipeline import _sync_stage_generated_file_hash_capture
    import argparse

    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "fresh content")
    index_path = project_root / ".claude" / "agents" / ".agent-meta-managed"
    index_path.write_text("developer.md\n", encoding="utf-8")
    provider_config = {"Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}}
    log = SyncLog()
    args = argparse.Namespace(dry_run=False)

    _sync_stage_generated_file_hash_capture(
        tmp_path / "agent-meta", project_root, {"drift-detection": {"enabled": False}},
        provider_config, args, log,
    )

    assert not (project_root / ".meta-config" / "generated-file-hashes.json").exists()


def _drifted_agent_project(tmp_path):
    from scripts.lib.generated_file_drift import content_hash

    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "edited by hand")
    index_path = project_root / ".claude" / "agents" / ".agent-meta-managed"
    index_path.write_text("developer.md\n", encoding="utf-8")
    hashes_path = project_root / ".meta-config" / "generated-file-hashes.json"
    hashes_path.parent.mkdir(parents=True, exist_ok=True)
    hashes_path.write_text(
        '{"version": 1, "hashes": {".claude/agents/developer.md": "'
        + content_hash("original") + '"}}',
        encoding="utf-8",
    )
    provider_config = {"Claude": {"agents_dir": ".claude/agents", "skills_dir": ".claude/skills"}}
    return project_root, provider_config


def test_drift_scan_stage_writes_backup_and_names_it_in_warning(tmp_path) -> None:
    """Issue #734: the stage writes the `.sync-backup-<ts>` sibling BEFORE
    the writers run and names it in the warning."""
    from scripts.lib.log import SyncLog
    from scripts.lib.sync_pipeline import _sync_stage_generated_file_drift_scan
    import argparse

    project_root, provider_config = _drifted_agent_project(tmp_path)
    log = SyncLog()
    args = argparse.Namespace(dry_run=False)

    _sync_stage_generated_file_drift_scan(
        tmp_path / "agent-meta", project_root, {}, provider_config, args, log,
    )

    backup_files = list(
        (project_root / ".claude" / "agents").glob("developer.md.sync-backup-*")
    )
    assert len(backup_files) == 1
    assert backup_files[0].read_text(encoding="utf-8") == "edited by hand"
    assert any(
        f"Backup written to {backup_files[0].name}." in warning
        for warning in log.warnings
    ), log.warnings


def test_drift_scan_stage_writes_no_backup_in_dry_run(tmp_path) -> None:
    from scripts.lib.log import SyncLog
    from scripts.lib.sync_pipeline import _sync_stage_generated_file_drift_scan
    import argparse

    project_root, provider_config = _drifted_agent_project(tmp_path)
    log = SyncLog()
    args = argparse.Namespace(dry_run=True)

    _sync_stage_generated_file_drift_scan(
        tmp_path / "agent-meta", project_root, {}, provider_config, args, log,
    )

    assert list((project_root / ".claude" / "agents").glob("*.sync-backup-*")) == []
    assert any("Backup written to" in warning for warning in log.warnings), log.warnings

