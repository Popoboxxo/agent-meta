"""T15: resolved data file + ``--status-artifacts`` (Issue #1186, AC-14).

Covers the machine contract of ``scripts/lib/artifact_status.py`` and the
``sync.py --status-artifacts [--json]`` CLI wiring:

* JSON required fields for all 23 classes, ``schema_version: "1"``;
* exit 0 (all resolved) vs. exit 2 (an unresolvable class named on stderr);
* 23-row human table, ``--status`` collision, CLI-flag documentation;
* Stage 14c writes ``.meta-config/artifact-locations.resolved.json`` after
  hash-capture + auto-commit-allowlist, and never in dry-run;
* ``*.sync-backup-*`` siblings excluded from counts (#1195);
* ``unmanaged``/``naming``/``field_sources`` reported additively (D1/D3/D8).

Run: python3 -m pytest tests/test_artifact_status_cli.py -q
"""
from __future__ import annotations

import argparse
import inspect
import json
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib import cli_commands  # noqa: E402
from lib.artifact_status import (  # noqa: E402
    SCHEMA_VERSION,
    build_report,
    build_resolved_payload,
    render_table,
)
from lib.log import SyncLog  # noqa: E402
from lib.sync_pipeline import _sync_stage_artifact_locations_resolved  # noqa: E402

_SYNC_PY = _REPO_ROOT / "scripts" / "sync.py"
_CLI_REF = _REPO_ROOT / "docs" / "api" / "cli-reference.md"
_RESOLVED_REL = ".meta-config/artifact-locations.resolved.json"

_MINIMAL_CONFIG = (
    "ai-providers: [Claude]\n"
    "dod-preset: rapid-prototyping\n"
    "roles: [developer]\n"
    "project: {name: artifact-status-test, prefix: as, short: ast}\n"
    "variables: {PROJECT_NAME: artifact-status-test}\n"
)


def _project(tmp_path: Path, extra: str = "") -> Path:
    root = tmp_path / "project"
    meta = root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "project.yaml").write_text(_MINIMAL_CONFIG + extra, encoding="utf-8")
    return root


def _run(project_root: Path, *flags: str) -> subprocess.CompletedProcess:
    config = project_root / ".meta-config" / "project.yaml"
    return subprocess.run(
        [sys.executable, str(_SYNC_PY), "--config", str(config), *flags],
        capture_output=True, text=True, cwd=str(project_root),
    )


def _status(project_root: Path, *flags: str) -> dict:
    result = _run(project_root, "--status-artifacts", "--json", *flags)
    assert result.returncode == 0, result.stderr
    return json.loads(result.stdout)


# ---------------------------------------------------------------------------
# JSON contract
# ---------------------------------------------------------------------------

def test_json_has_schema_version_and_preset(tmp_path: Path) -> None:
    report = _status(_project(tmp_path))
    assert report["schema_version"] == SCHEMA_VERSION == "1"
    assert report.get("preset")


def test_each_class_has_path_mode_source_exists(tmp_path: Path) -> None:
    classes = _status(_project(tmp_path))["classes"]
    assert len(classes) == 23
    for name, entry in classes.items():
        assert "mode" in entry and "source" in entry and "exists" in entry, name
        # project-docs carries ``files`` (incl. issue-labels) instead of ``path``.
        if name == "project-docs":
            assert "path" not in entry
            assert "issue-labels" in entry["files"]
        else:
            assert "path" in entry, name


def test_kinds_key_is_closed_and_additive(tmp_path: Path) -> None:
    classes = _status(_project(tmp_path))["classes"]
    for name, entry in classes.items():
        assert isinstance(entry.get("kinds"), list), name
        assert "kind" not in entry, name  # singular never appears in the JSON
    assert set(classes["reviews"]["kinds"]) == {
        "code", "concept", "domain", "copyedit", "proofread", "se",
    }
    assert classes["specs"]["kinds"] == []


def test_json_is_additive_stable(tmp_path: Path) -> None:
    report = _status(_project(tmp_path))
    required_top = {"schema_version", "preset", "enabled", "classes", "unmanaged", "legacy"}
    assert required_top <= set(report)
    required_class = {"mode", "source", "exists", "kinds", "violations"}
    for entry in report["classes"].values():
        assert required_class <= set(entry)
    # Unknown future fields must not break the human renderer (additive contract).
    report["classes"]["specs"]["future_field"] = 1
    assert "specs" in render_table(report)


# ---------------------------------------------------------------------------
# Exit codes
# ---------------------------------------------------------------------------

def test_exit_zero_when_all_resolved(tmp_path: Path) -> None:
    result = _run(_project(tmp_path), "--status-artifacts")
    assert result.returncode == 0, result.stderr
    assert "specs" in result.stdout


def test_exit_two_names_key_and_reason_on_stderr(tmp_path: Path) -> None:
    # An empty path is accepted by the Python validator (it only checks
    # non-empty paths) but leaves the class unresolvable for the report.
    extra = (
        "\nartifact-locations:\n"
        "  enabled: true\n"
        "  classes:\n"
        "    specs:\n"
        '      path: ""\n'
    )
    result = _run(_project(tmp_path, extra), "--status-artifacts", "--json")
    assert result.returncode == 2
    assert result.stdout == ""
    assert "specs" in result.stderr
    assert "path" in result.stderr.lower()


# ---------------------------------------------------------------------------
# Human table / parser
# ---------------------------------------------------------------------------

def test_human_table_has_one_row_per_class(tmp_path: Path) -> None:
    report = build_report({}, _REPO_ROOT, _project(tmp_path))
    table = render_table(report)
    names = report["classes"]
    rows = [
        line for line in table.splitlines()
        if any(line.lstrip().startswith(name + " ") for name in names)
    ]
    assert len(rows) == 23, table


def test_status_flag_is_not_abbreviated_to_status() -> None:
    source = (_SYNC_PY).read_text(encoding="utf-8")
    assert 'parser.add_argument("--status-artifacts"' in source
    # --status keeps its original plan-ledger meaning (distinct argument).
    assert 'parser.add_argument("--status", metavar="STATUS"' in source
    assert "--status-artifacts" in cli_commands.__doc__ or hasattr(
        cli_commands, "_handle_status_artifacts")


# ---------------------------------------------------------------------------
# Stage 14c wiring / dry-run
# ---------------------------------------------------------------------------

def test_resolved_json_written_after_hash_capture() -> None:
    source = inspect.getsource(cli_commands._handle_sync)
    hash_pos = source.index("_sync_stage_generated_file_hash_capture(")
    allow_pos = source.index("_sync_stage_auto_commit_allowlist(")
    context_pos = source.index("_sync_stage_context_checks(")
    resolved_pos = source.index("_sync_stage_artifact_locations_resolved(")
    assert hash_pos < allow_pos < context_pos < resolved_pos, (
        "Stage 14c must hang directly after hash-capture (13), "
        "auto-commit-allowlist (14) and context-checks (14b)"
    )


def test_resolved_json_written_and_skipped_on_dry_run(tmp_path: Path) -> None:
    project = _project(tmp_path)
    resolved = project / _RESOLVED_REL

    _sync_stage_artifact_locations_resolved(
        _REPO_ROOT, project, {}, argparse.Namespace(dry_run=True), SyncLog())
    assert not resolved.exists(), "dry-run must not write the resolved file"

    _sync_stage_artifact_locations_resolved(
        _REPO_ROOT, project, {}, argparse.Namespace(dry_run=False), SyncLog())
    assert resolved.exists()
    payload = json.loads(resolved.read_text(encoding="utf-8"))
    assert payload["schema_version"] == "1"
    assert len(payload["classes"]) == 23


# ---------------------------------------------------------------------------
# Counting / baseline / alias / docs
# ---------------------------------------------------------------------------

def test_backup_siblings_do_not_skew_counts(tmp_path: Path) -> None:
    project = _project(tmp_path)
    specs = project / "docs" / "specs"
    specs.mkdir(parents=True)
    (specs / "a.md").write_text("a", encoding="utf-8")
    (specs / "b.md").write_text("b", encoding="utf-8")
    (specs / "b.md.sync-backup-2026-11-17").write_text("x", encoding="utf-8")

    entry = build_report({}, _REPO_ROOT, project)["classes"]["specs"]
    assert entry["file_count"] == 2
    assert entry["newest"] == "b.md"


def test_violations_array_shape(tmp_path: Path) -> None:
    config = {
        "artifact-locations": {
            "enabled": True,
            "classes": {"specs": {"path": ""}},
        }
    }
    entry = build_report(config, _REPO_ROOT, _project(tmp_path))["classes"]["specs"]
    assert isinstance(entry["violations"], list)
    assert entry["violations"]
    for violation in entry["violations"]:
        assert set(violation) == {"code", "path", "expected"}


def test_resolved_json_has_unmanaged_and_baseline(tmp_path: Path) -> None:
    project = _project(tmp_path)
    legacy_dir = project / "docs" / "conclusions"
    legacy_dir.mkdir(parents=True)
    (legacy_dir / ".gitkeep").write_text("", encoding="utf-8")
    (legacy_dir / "old-note.md").write_text("note", encoding="utf-8")
    (legacy_dir / "old-note.md.sync-backup-1").write_text("x", encoding="utf-8")

    payload = build_resolved_payload({}, _REPO_ROOT, project)
    assert isinstance(payload["unmanaged"], list) and payload["unmanaged"]
    assert set(payload["baseline"]) == {"generated_at", "legacy_files"}
    assert "docs/conclusions/old-note.md" in payload["baseline"]["legacy_files"]
    assert ".gitkeep" not in str(payload["baseline"]["legacy_files"])
    assert not any(".sync-backup-" in f for f in payload["baseline"]["legacy_files"])


def test_status_json_reports_unmanaged_list(tmp_path: Path) -> None:
    report = _status(_project(tmp_path))
    assert isinstance(report["unmanaged"], list)
    assert "unmanaged" not in report["classes"]


def test_status_json_reports_naming(tmp_path: Path) -> None:
    classes = _status(_project(tmp_path))["classes"]
    assert classes["adr"]["naming"] == "ADR-{nnn}_{slug}.md"
    for name in ("project-docs", "scratch", "state"):
        assert "naming" not in classes[name], name


def test_status_json_reports_alias_attribution(tmp_path: Path) -> None:
    extra = (
        "\nartifact-locations:\n"
        "  enabled: true\n"
        "repo_containment:\n"
        "  tmp-sink:\n"
        "    path: .tmp-aliased\n"
    )
    scratch = _status(_project(tmp_path, extra))["classes"]["scratch"]
    assert scratch["source"] == "project"
    assert scratch["field_sources"]["path"] == (
        "project-alias:repo_containment.tmp-sink.path"
    )


def test_cli_flag_is_documented() -> None:
    text = _CLI_REF.read_text(encoding="utf-8")
    assert "`--status-artifacts`" in text
    assert "`--json`" in text
