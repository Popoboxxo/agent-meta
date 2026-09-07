"""Tests for scripts/lib/generated_file_drift.py.

Detects when a sync.py-generated file (anything tracked via
.agent-meta-managed) was manually edited since the last sync, via a
content-hash sidecar store. Warn-only -- write behavior is unaffected.
Spec: docs/superpowers/specs/2026-09-07-generated-file-drift-detection-design.md
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.generated_file_drift import (
    _hashes_path,
    _load_allowlist_patterns,
    _load_hashes,
    _save_hashes,
    is_allowlisted,
    is_drift_detection_enabled,
)


def test_hashes_path_is_meta_config_generated_file_hashes_json(tmp_path: Path) -> None:
    assert _hashes_path(tmp_path) == tmp_path / ".meta-config" / "generated-file-hashes.json"


def test_load_hashes_returns_empty_dict_when_file_absent(tmp_path: Path) -> None:
    assert _load_hashes(tmp_path) == {}


def test_save_then_load_hashes_round_trips(tmp_path: Path) -> None:
    _save_hashes(tmp_path, {".claude/agents/developer.md": "abc123"}, dry_run=False)
    assert _load_hashes(tmp_path) == {".claude/agents/developer.md": "abc123"}


def test_save_hashes_is_noop_in_dry_run(tmp_path: Path) -> None:
    _save_hashes(tmp_path, {"x": "y"}, dry_run=True)
    assert not _hashes_path(tmp_path).exists()


def test_load_hashes_returns_empty_dict_on_malformed_json(tmp_path: Path) -> None:
    path = _hashes_path(tmp_path)
    path.parent.mkdir(parents=True)
    path.write_text("not json", encoding="utf-8")
    assert _load_hashes(tmp_path) == {}


def test_load_allowlist_patterns_returns_empty_list_when_file_absent(tmp_path: Path) -> None:
    assert _load_allowlist_patterns(tmp_path) == []


def test_load_allowlist_patterns_reads_yaml_list(tmp_path: Path) -> None:
    meta = tmp_path / ".meta-config"
    meta.mkdir()
    (meta / "drift-allowlist.yaml").write_text(
        "allow-edits:\n  - .claude/commands/my-cmd.md\n  - .opencode/rules/*.md\n",
        encoding="utf-8",
    )
    assert _load_allowlist_patterns(tmp_path) == [
        ".claude/commands/my-cmd.md", ".opencode/rules/*.md",
    ]


def test_is_allowlisted_matches_exact_path() -> None:
    assert is_allowlisted(".claude/commands/my-cmd.md", [".claude/commands/my-cmd.md"])


def test_is_allowlisted_matches_glob() -> None:
    assert is_allowlisted(".opencode/rules/foo.md", [".opencode/rules/*.md"])


def test_is_allowlisted_false_when_no_pattern_matches() -> None:
    assert not is_allowlisted(".claude/agents/developer.md", [".claude/commands/*.md"])


def test_is_allowlisted_false_for_empty_patterns() -> None:
    assert not is_allowlisted(".claude/agents/developer.md", [])


def test_is_drift_detection_enabled_defaults_true_when_key_absent() -> None:
    assert is_drift_detection_enabled({}) is True


def test_is_drift_detection_enabled_false_when_explicitly_disabled() -> None:
    assert is_drift_detection_enabled({"drift-detection": {"enabled": False}}) is False


def test_is_drift_detection_enabled_true_when_explicitly_enabled() -> None:
    assert is_drift_detection_enabled({"drift-detection": {"enabled": True}}) is True
