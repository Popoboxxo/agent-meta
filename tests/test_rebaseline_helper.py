"""Unit tests for the rebaseline helper (Tasks 1-4).

The runner is always injected/mocked: no test spawns a real sync.py or renders
the full provider matrix. Scope mirrors docs/plans/2026-11-15-rebaseline-helper-plan.md.
"""
from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"


@pytest.fixture()
def rb():
    """Import the helper module under test (fresh reference per test)."""
    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))
    from lib import rebaseline

    return rebaseline


# --- Task 1: root resolution and runner ------------------------------------


def test_resolve_root_ignores_cwd(rb, tmp_path, monkeypatch):
    fake_root = tmp_path / "checkout"
    script = fake_root / "scripts" / "rebaseline.py"
    script.parent.mkdir(parents=True)
    script.write_text("", encoding="utf-8")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)

    assert rb.resolve_root(script) == fake_root.resolve()


def test_resolve_root_override(rb, tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    override = tmp_path / "worktree"

    assert (
        rb.resolve_root(tmp_path / "scripts" / "rebaseline.py", override)
        == override.resolve()
    )


def test_build_sync_cmd_includes_config(rb, tmp_path):
    root = tmp_path / "checkout"

    cmd = rb.build_sync_cmd(root, "--dry-run")

    assert cmd[0] == sys.executable
    assert "--config" in cmd
    assert str(root / ".meta-config" / "project.yaml") in cmd
    assert "--dry-run" in cmd
    assert any(part.endswith("sync.py") for part in cmd)


def test_run_step_uses_cwd_and_interpreter(rb, tmp_path):
    root = tmp_path / "checkout"
    cfg = root / ".meta-config" / "project.yaml"
    cfg.parent.mkdir(parents=True)
    cfg.write_text("dummy", encoding="utf-8")
    calls = []

    def runner(argv, cwd=None, **kwargs):
        calls.append((argv, cwd))
        return SimpleNamespace(returncode=0)

    rb.run_step(["some.py", "--flag"], root, runner=runner)

    assert len(calls) == 1
    argv, cwd = calls[0]
    assert argv[0] == sys.executable
    assert argv[1:] == ["some.py", "--flag"]
    assert cwd == str(root)


def test_run_step_missing_config_raises(rb, tmp_path):
    root = tmp_path / "checkout"  # no .meta-config/project.yaml

    with pytest.raises(rb.RebaselineError):
        rb.run_step(["some.py"], root, runner=lambda *args, **kwargs: None)


# --- Task 2: snapshot and rollback ------------------------------------------


def test_snapshot_restores_modified_file_byte_exact(rb, tmp_path):
    root = tmp_path / "checkout"
    target = root / "standalone" / "agents" / "x.md"
    target.parent.mkdir(parents=True)
    original = b"original\n\x00binary\xffbytes"
    target.write_bytes(original)

    snap = rb.Snapshot.take(root, ["standalone/agents/x.md"])
    target.write_bytes(b"changed content")
    snap.restore()

    assert target.read_bytes() == original


def test_snapshot_recreates_deleted_file(rb, tmp_path):
    root = tmp_path / "checkout"
    target = root / "dir" / "gone.md"
    target.parent.mkdir(parents=True)
    original = b"was here"
    target.write_bytes(original)

    snap = rb.Snapshot.take(root, ["dir/gone.md"])
    target.unlink()
    snap.restore()

    assert target.read_bytes() == original


def test_snapshot_deletes_newly_created_file(rb, tmp_path):
    root = tmp_path / "checkout"
    target = root / "dir" / "new.md"
    target.parent.mkdir(parents=True)

    snap = rb.Snapshot.take(root, ["dir/new.md"])
    target.write_bytes(b"created after take")
    snap.restore()

    assert not target.exists()


def test_snapshot_leaves_files_outside_path_list_untouched(rb, tmp_path):
    root = tmp_path / "checkout"
    inside = root / "dir" / "inside.md"
    outside = root / "other" / "outside.md"
    inside.parent.mkdir(parents=True)
    outside.parent.mkdir(parents=True)
    inside.write_bytes(b"inside original")
    outside.write_bytes(b"outside original")

    snap = rb.Snapshot.take(root, ["dir/inside.md"])
    inside.write_bytes(b"inside changed")
    outside.write_bytes(b"outside changed")
    snap.restore()

    assert inside.read_bytes() == b"inside original"
    assert outside.read_bytes() == b"outside changed"


def test_snapshot_handles_directory_and_glob_paths(rb, tmp_path):
    root = tmp_path / "checkout"
    kept = root / "standalone" / "keep.md"
    new = root / "standalone" / "new.md"
    kept.parent.mkdir(parents=True)
    kept.write_bytes(b"keep original")

    snap = rb.Snapshot.take(root, ["standalone/**"])
    kept.write_bytes(b"keep changed")
    new.write_bytes(b"new after take")
    snap.restore()

    assert kept.read_bytes() == b"keep original"
    assert not new.exists()


# --- Task 3: diff gate -------------------------------------------------------


def test_class_allowlist_covers_core_artifacts(rb):
    allow = set(rb.CLASS_ALLOWLIST)
    assert "tests/fixtures/ac01-baseline/hashes.json" in allow
    assert ".meta-config/generated-file-hashes.json" in allow
    assert ".meta-config/context-hashes.json" in allow
    assert "standalone/**" in allow
    assert "tests/test_opencode_v2_surface.py" in allow
    assert ".meta-config/rebaseline-log.jsonl" in allow
    assert any("a2a-delegation-gates.role-" in path for path in allow)


def test_derive_expected_stems_from_sources(rb):
    stems = rb.derive_expected_stems(
        [
            "agents/1-generic/developer.md",
            "rules/1-generic/branch-guard.md",
            "hooks/git-commit.sh",
            "templates/agents/foo.md",
        ]
    )
    assert stems == {"developer", "branch-guard", "git-commit", "foo"}


def test_derive_expected_stems_fails_closed_for_config_and_lib(rb):
    assert rb.derive_expected_stems(
        ["config/project.yaml", "scripts/lib/config.py"]
    ) == set()


def test_check_gate_allowlisted_files_pass(rb):
    violations = rb.check_gate(
        ["tests/fixtures/ac01-baseline/hashes.json", "standalone/agents/x.md"],
        [],
        [],
        [],
        {"developer"},
    )
    assert violations == []


def test_check_gate_unexpected_file_is_violation(rb):
    violations = rb.check_gate(["src/unexpected.txt"], [], [], [], set())
    assert violations and any("src/unexpected.txt" in item for item in violations)


def test_check_gate_expect_glob_allows_file(rb):
    assert rb.check_gate(["docs/extra.md"], [], ["docs/**"], [], set()) == []


def test_check_gate_key_with_matching_stem_passes(rb):
    violations = rb.check_gate(
        [], ["alpha/agents/developer.md"], [], [], {"developer"}
    )
    assert violations == []


def test_check_gate_foreign_key_is_violation(rb):
    violations = rb.check_gate(
        [], ["alpha/agents/unknown.md"], [], [], {"developer"}
    )
    assert violations and any("unknown" in item for item in violations)


def test_check_gate_expect_key_glob_allows(rb):
    assert (
        rb.check_gate([], ["config/custom.yaml"], [], ["config/*"], set()) == []
    )


def test_check_gate_config_source_without_expect_key_fails_closed(rb):
    stems = rb.derive_expected_stems(["config/project.yaml"])
    violations = rb.check_gate(
        [], ["alpha/agents/developer.md"], [], [], stems
    )
    assert violations  # no stem mapping and no --expect-key => fail closed
