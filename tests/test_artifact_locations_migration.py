"""T23: alias migration ``--migrate-artifact-aliases [--write]`` (Issue #1186, D1).

Covers the pure migration library (``scripts/lib/artifact_migration.py``) and the
``sync.py`` CLI wiring:

* dry-run prints the ready ``artifact-locations`` snippet but writes nothing;
* ``--write`` migrates the scratch alias comment-preservingly and stays valid;
* ``--write`` is idempotent ("already migrated", zero bytes written);
* divergence and ``enabled: false`` are refused (T5 is the authority);
* all six legacy alias groups are covered (D1);
* both CLI flags are documented (``docs.cli_reference`` gate).

Run: python3 -m pytest tests/test_artifact_locations_migration.py -q
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.artifact_migration import (  # noqa: E402
    MigrationError,
    apply_migration,
    build_migration_plan,
    render_snippets,
)
from lib.yaml_roundtrip import assert_roundtrip_preserved  # noqa: E402

_SYNC_PY = _SCRIPTS / "sync.py"
_CLI_REF = _REPO_ROOT / "docs" / "api" / "cli-reference.md"

_MINIMAL_CONFIG = (
    "ai-providers: [Claude]\n"
    "dod-preset: rapid-prototyping\n"
    "roles: [developer]\n"
    "project: {name: migration-test, prefix: mt, short: migt}\n"
    "variables: {PROJECT_NAME: migration-test}\n"
)


def _project(tmp_path: Path, extra: str = "") -> tuple[Path, Path]:
    root = tmp_path / "project"
    meta = root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    config = meta / "project.yaml"
    config.write_text(_MINIMAL_CONFIG + extra, encoding="utf-8")
    return root, config


def _run(root: Path, config: Path, *flags: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC_PY), "--config", str(config), *flags],
        capture_output=True, text=True, cwd=str(root),
    )


# ---------------------------------------------------------------------------
# CLI: dry-run / write / idempotency
# ---------------------------------------------------------------------------

def test_dry_run_prints_snippet_without_writing(tmp_path: Path) -> None:
    extra = "repo_containment:\n  tmp-sink:\n    path: .tmp-aliased\n"
    root, config = _project(tmp_path, extra)
    before = config.read_bytes()

    result = _run(root, config, "--migrate-artifact-aliases")

    assert result.returncode == 0, result.stderr
    assert "artifact-locations.classes.scratch.path" in result.stdout
    assert ".tmp-aliased" in result.stdout
    assert config.read_bytes() == before, "dry-run must not touch project.yaml"


def test_write_migrates_scratch_alias(tmp_path: Path) -> None:
    extra = (
        "# keep this header comment\n"
        "repo_containment:\n  tmp-sink:\n    path: .tmp-aliased\n"
        "# keep this trailing comment\n"
    )
    root, config = _project(tmp_path, extra)
    original = config.read_text(encoding="utf-8")

    result = _run(root, config, "--migrate-artifact-aliases", "--write")

    assert result.returncode == 0, result.stderr
    updated = config.read_text(encoding="utf-8")
    # Round-trip guard: comments and mapping-key order survive the write.
    assert_roundtrip_preserved(original, updated, context=str(config))
    doc = yaml.safe_load(updated)
    assert doc["artifact-locations"]["classes"]["scratch"]["path"] == ".tmp-aliased"
    # The migrated config still validates (same validator as `sync.py --validate`).
    from lib.config import load_config  # noqa: WPS433 (local import keeps tests isolated)
    assert isinstance(load_config(config), dict)


def test_write_is_idempotent(tmp_path: Path) -> None:
    extra = "repo_containment:\n  tmp-sink:\n    path: .tmp-aliased\n"
    root, config = _project(tmp_path, extra)

    first = _run(root, config, "--migrate-artifact-aliases", "--write")
    assert first.returncode == 0, first.stderr
    after_first = config.read_bytes()

    second = _run(root, config, "--migrate-artifact-aliases", "--write")
    assert second.returncode == 0, second.stderr
    assert "already migrated" in second.stdout
    assert config.read_bytes() == after_first, "second run must write zero bytes"


# ---------------------------------------------------------------------------
# Refusals (T5 is the authority; the migration never repairs silently)
# ---------------------------------------------------------------------------

def test_write_refuses_on_divergent_values(tmp_path: Path) -> None:
    config = {
        "artifact-locations": {
            "enabled": True,
            "classes": {"scratch": {"path": "sink-a"}},
        },
        "repo_containment": {"tmp-sink": {"path": "sink-b"}},
    }
    with pytest.raises(MigrationError) as exc:
        build_migration_plan(config)
    assert exc.value.code == "artifact-locations.scratch-sink-divergence"

    extra = (
        "artifact-locations:\n  enabled: true\n  classes:\n"
        "    scratch:\n      path: sink-a\n"
        "repo_containment:\n  tmp-sink:\n    path: sink-b\n"
    )
    root, config_path = _project(tmp_path, extra)
    before = config_path.read_bytes()
    result = _run(root, config_path, "--migrate-artifact-aliases", "--write")
    assert result.returncode == 1
    assert "artifact-locations.scratch-sink-divergence" in (result.stderr + result.stdout)
    assert config_path.read_bytes() == before, "refusal must not write"


def test_write_refuses_when_matrix_disabled(tmp_path: Path) -> None:
    config = {
        "artifact-locations": {"enabled": False},
        "repo_containment": {"tmp-sink": {"path": ".tmp-aliased"}},
    }
    with pytest.raises(MigrationError) as exc:
        build_migration_plan(config)
    message = exc.value.message
    for hint in ("spec-plan-workflow.paths", "se_output", "tmp-sink", "enabled: false"):
        assert hint in message

    extra = (
        "artifact-locations:\n  enabled: false\n"
        "repo_containment:\n  tmp-sink:\n    path: .tmp-aliased\n"
    )
    root, config_path = _project(tmp_path, extra)
    before = config_path.read_bytes()
    result = _run(root, config_path, "--migrate-artifact-aliases", "--write")
    assert result.returncode == 1
    assert config_path.read_bytes() == before, "refusal must not write"


# ---------------------------------------------------------------------------
# Coverage + docs
# ---------------------------------------------------------------------------

def test_migration_covers_all_aliases() -> None:
    config = {
        "spec-plan-workflow": {
            "paths": {
                "specs": "docs/specs-old",
                "plans": "docs/plans-old",
                "spikes": "docs/spikes-old",
            },
        },
        "se_output": {"base_dir": "SE-old"},
        "repo_containment": {"tmp-sink": {"path": ".tmp-old"}},
        "progress": {
            "dir": ".meta-viz/progress-old",
            "checkpoint-dir": ".meta-viz/checkpoints-old",
            "handoffs-dir": ".meta-viz/handoffs-old",
        },
        "viz": {"event_log": ".meta-viz/events-old.jsonl"},
    }
    plan = build_migration_plan(config)
    text = render_snippets(plan)

    expected = {
        "spec-plan-workflow.paths": "artifact-locations.classes.specs.path",
        "se_output.base_dir": "artifact-locations.classes.se-*.path",
        "repo_containment.tmp-sink.path": "artifact-locations.classes.scratch.path",
        "progress.dir": "artifact-locations.classes.state.subdirs.progress",
        "progress.checkpoint-dir": "artifact-locations.classes.state.subdirs.checkpoints",
        "viz.event_log": "artifact-locations.classes.state.event-log",
    }
    for source, target in expected.items():
        assert source in text, source
        assert target in text, target
    for entry in plan.entries:
        assert entry.source_key and entry.target_key and entry.value and entry.reason
    assert "deprecated" in text and "D1" in text


def test_cli_flag_is_documented() -> None:
    text = _CLI_REF.read_text(encoding="utf-8")
    assert "`--migrate-artifact-aliases`" in text
    assert "`--write`" in text
