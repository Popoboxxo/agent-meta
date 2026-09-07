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


from scripts.lib.generated_file_drift import scan_generated_file_drift


def _write(root: Path, rel: str, content: str) -> None:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _managed_index(root: Path, dir_rel: str, *names: str) -> None:
    index_path = root / dir_rel / ".agent-meta-managed"
    index_path.parent.mkdir(parents=True, exist_ok=True)
    index_path.write_text("\n".join(names) + "\n", encoding="utf-8")


def _provider_config() -> dict:
    return {"Claude": {
        "agents_dir": ".claude/agents", "skills_dir": ".claude/skills",
        "hooks_dir": ".claude/hooks", "rules_dir": ".claude/rules",
        "commands_dir": ".claude/commands",
        "has_hooks": True, "has_rules": True, "has_commands": True,
    }}


def test_scan_flags_agent_file_whose_content_changed_since_last_hash(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "edited by hand")
    _managed_index(project_root, ".claude/agents", "developer.md")
    from scripts.lib.generated_file_drift import content_hash
    _save_hashes(project_root, {".claude/agents/developer.md": content_hash("original content")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = [f["path"] for f in findings]
    assert ".claude/agents/developer.md" in paths


def test_scan_does_not_flag_file_with_no_stored_hash_yet(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "brand new")
    _managed_index(project_root, ".claude/agents", "developer.md")

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    assert findings == []


def test_scan_does_not_flag_unchanged_file(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "same content")
    _managed_index(project_root, ".claude/agents", "developer.md")
    _save_hashes(project_root, {".claude/agents/developer.md": content_hash("same content")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    assert findings == []


def test_scan_respects_allowlist(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/commands/my-cmd.md", "edited by hand")
    _managed_index(project_root, ".claude/commands", "my-cmd.md")
    _save_hashes(project_root, {".claude/commands/my-cmd.md": content_hash("original")}, dry_run=False)
    meta = project_root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "drift-allowlist.yaml").write_text(
        "allow-edits:\n  - .claude/commands/*.md\n", encoding="utf-8",
    )

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    assert findings == []


def test_scan_covers_rules_dir_hooks_dir_and_pipeline_details(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/rules/branch-guard.md", "edited")
    _managed_index(project_root, ".claude/rules", "branch-guard.md")
    _write(project_root, ".claude/hooks/dod-push-check.sh", "edited")
    _managed_index(project_root, ".claude/hooks", "dod-push-check.sh")
    _write(project_root, ".claude/pipeline-details/bugfix.md", "edited")
    _managed_index(project_root, ".claude/pipeline-details", "bugfix.md")
    _save_hashes(project_root, {
        ".claude/rules/branch-guard.md": content_hash("orig"),
        ".claude/hooks/dod-push-check.sh": content_hash("orig"),
        ".claude/pipeline-details/bugfix.md": content_hash("orig"),
    }, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = {f["path"] for f in findings}
    assert paths == {
        ".claude/rules/branch-guard.md",
        ".claude/hooks/dod-push-check.sh",
        ".claude/pipeline-details/bugfix.md",
    }


def test_scan_covers_nested_managed_subdirs(tmp_path: Path) -> None:
    """hooks/lib/ and hooks/release-gates/ carry their OWN .agent-meta-managed
    index (issue #558) -- must be recursed into, not just the top-level hooks/."""
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/hooks/lib/hook_common.sh", "edited")
    _managed_index(project_root, ".claude/hooks/lib", "hook_common.sh")
    _managed_index(project_root, ".claude/hooks")  # empty top-level index
    _save_hashes(project_root, {".claude/hooks/lib/hook_common.sh": content_hash("orig")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = {f["path"] for f in findings}
    assert ".claude/hooks/lib/hook_common.sh" in paths


def test_scan_unions_rules_sidecar_indexes(tmp_path: Path) -> None:
    """rules/ has THREE index files (.agent-meta-managed, -mcp, -tools) for
    three different writers -- all three contribute managed filenames."""
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".claude/rules/mcp-honcho.md", "edited")
    (project_root / ".claude" / "rules").mkdir(parents=True, exist_ok=True)
    (project_root / ".claude" / "rules" / ".agent-meta-managed").write_text("", encoding="utf-8")
    (project_root / ".claude" / "rules" / ".agent-meta-managed-mcp").write_text("mcp-honcho.md\n", encoding="utf-8")
    _save_hashes(project_root, {".claude/rules/mcp-honcho.md": content_hash("orig")}, dry_run=False)

    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())
    paths = {f["path"] for f in findings}
    assert ".claude/rules/mcp-honcho.md" in paths


def test_scan_only_covers_active_providers(tmp_path: Path) -> None:
    from scripts.lib.generated_file_drift import content_hash
    project_root = tmp_path / "project"
    _write(project_root, ".gemini/agents/developer.md", "edited")
    _managed_index(project_root, ".gemini/agents", "developer.md")
    _save_hashes(project_root, {".gemini/agents/developer.md": content_hash("orig")}, dry_run=False)

    provider_config = {
        "Claude": _provider_config()["Claude"],
        "Gemini": {"agents_dir": ".gemini/agents", "skills_dir": ".gemini/skills"},
    }
    # config has no "ai-providers" key -> resolve_providers() defaults to
    # ["Claude"] only (see scripts/lib/providers.py) -- Gemini is not active.
    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, provider_config)
    assert findings == []


from scripts.lib.generated_file_drift import capture_generated_file_hashes, content_hash


def test_capture_writes_hash_for_every_managed_file(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "fresh content")
    _managed_index(project_root, ".claude/agents", "developer.md")

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=False)

    assert _load_hashes(project_root) == {
        ".claude/agents/developer.md": content_hash("fresh content"),
    }


def test_capture_is_noop_in_dry_run(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "fresh content")
    _managed_index(project_root, ".claude/agents", "developer.md")

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=True)

    assert _load_hashes(project_root) == {}


def test_capture_then_scan_round_trip_finds_no_drift(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "content v1")
    _managed_index(project_root, ".claude/agents", "developer.md")

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=False)
    findings = scan_generated_file_drift(tmp_path / "agent-meta", project_root, {}, _provider_config())

    assert findings == []


def test_capture_overwrites_stale_hash_for_regenerated_content(tmp_path: Path) -> None:
    project_root = tmp_path / "project"
    _write(project_root, ".claude/agents/developer.md", "content v1")
    _managed_index(project_root, ".claude/agents", "developer.md")
    _save_hashes(project_root, {".claude/agents/developer.md": content_hash("stale")}, dry_run=False)

    capture_generated_file_hashes(tmp_path / "agent-meta", project_root, {}, _provider_config(), dry_run=False)

    assert _load_hashes(project_root) == {
        ".claude/agents/developer.md": content_hash("content v1"),
    }
