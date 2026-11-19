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


# --- Task 4: pin registry and detectors -------------------------------------


def _make_pin_root(root):
    """Create a throw-away tree in which every registered pin path exists."""
    paths = [
        "tests/fixtures/ac01-baseline/hashes.json",
        "tests/fixtures/slimming-golden/role.md",
        "tests/fixtures/compact-golden/agents-managed.md",
        "tests/fixtures/topology-golden/a2a-delegation-gates.role-active.md",
        "tests/fixtures/topology-golden/schema-property-paths.json",
        ".meta-config/generated-file-hashes.json",
        ".meta-config/context-hashes.json",
        "standalone/agents/role.md",
        "tests/test_context_budgets.py",
        "tests/test_opencode_v2_surface.py",
    ]
    for rel in paths:
        target = root / rel
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text("fixture", encoding="utf-8")


def _fake_ac_t4(rb, monkeypatch):
    """Avoid importing the large real test module: inject a matching digester."""
    monkeypatch.setattr(
        rb,
        "_load_fixture_digester",
        lambda root: (
            lambda path: "digest",
            {"ac01-baseline": "digest"},
        ),
    )


def test_pin_registry_covers_all_nine_classes(rb):
    classes = {pin.klass for pin in rb.PINS}
    assert classes == {"AC", "AC-T4", "SG", "CG", "TG", "H1", "H2", "SA", "CE"}


def test_pin_registry_includes_key_fixtures(rb):
    all_paths = {path for pin in rb.PINS for path in pin.paths}
    assert "tests/fixtures/compact-golden/agents-managed.md" in all_paths
    assert "tests/fixtures/topology-golden/schema-property-paths.json" in all_paths


def test_pin_registry_actions(rb):
    tg = [pin for pin in rb.PINS if pin.klass == "TG"]
    assert any(pin.action == "auto" for pin in tg)
    assert any(pin.action == "report-only" for pin in tg)
    actions = {pin.klass: pin.action for pin in rb.PINS}
    assert actions["AC"] == "auto"
    assert actions["SG"] == "report-only"
    assert actions["CE"] == "report-only"


def test_impact_report_red_detector_is_betroffen(rb, tmp_path, monkeypatch):
    _make_pin_root(tmp_path)
    _fake_ac_t4(rb, monkeypatch)

    statuses = rb.impact_report(
        tmp_path,
        runner=lambda cmd, cwd=None: SimpleNamespace(returncode=1),
    )

    assert any(status.status == "betroffen" for status in statuses)
    assert all(status.status in {"ok", "betroffen", "n/a"} for status in statuses)


def test_impact_report_green_detector_is_ok(rb, tmp_path, monkeypatch):
    _make_pin_root(tmp_path)
    _fake_ac_t4(rb, monkeypatch)

    statuses = rb.impact_report(
        tmp_path,
        runner=lambda cmd, cwd=None: SimpleNamespace(returncode=0),
    )

    assert statuses
    assert all(status.status == "ok" for status in statuses)


def test_impact_report_missing_paths_are_na(rb, tmp_path, monkeypatch):
    _fake_ac_t4(rb, monkeypatch)

    statuses = rb.impact_report(
        tmp_path,
        runner=lambda cmd, cwd=None: SimpleNamespace(returncode=0),
    )

    assert statuses
    assert all(status.status == "n/a" for status in statuses)


def test_ac_t4_detector_uses_importlib_loader(rb, tmp_path, monkeypatch):
    calls = []

    class FakeLoader:
        def exec_module(self, module):
            module._fixture_tree_sha256 = lambda root: "digest"
            module._FIXTURE_TREES = {"ac01-baseline": "digest"}

    class FakeSpec:
        loader = FakeLoader()

    def fake_spec(name, path):
        calls.append((name, path))
        return FakeSpec()

    monkeypatch.setattr(rb.importlib.util, "spec_from_file_location", fake_spec)
    monkeypatch.setattr(
        rb.importlib.util, "module_from_spec", lambda spec: SimpleNamespace()
    )
    _make_pin_root(tmp_path)

    statuses = rb.impact_report(
        tmp_path,
        runner=lambda cmd, cwd=None: SimpleNamespace(returncode=0),
    )
    ac_t4 = [status for status in statuses if status.klass == "AC-T4"]

    assert calls
    assert Path(calls[0][1]) == tmp_path / "tests" / "test_opencode_v2_surface.py"
    assert len(ac_t4) == 1
    assert ac_t4[0].status == "ok"


# --- Task 5: write steps and preflight ---------------------------------------


def _step_root(root):
    """Throw-away tree with a config and the files the steps touch."""
    cfg = root / ".meta-config" / "project.yaml"
    cfg.parent.mkdir(parents=True, exist_ok=True)
    cfg.write_text("dummy", encoding="utf-8")
    manifest = root / "tests" / "fixtures" / "ac01-baseline" / "hashes.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text("{}", encoding="utf-8")
    return root


def _ok_runner(calls):
    def runner(argv, cwd=None, **kwargs):
        calls.append(" ".join(str(part) for part in argv))
        return SimpleNamespace(returncode=0, stdout="")

    return runner


def test_step_order_recorded(rb, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    order = []

    monkeypatch.setattr(
        rb, "_render_matrix", lambda *a, **k: (order.append("ac01"), {})[1]
    )
    monkeypatch.setattr(
        rb, "_render_topology", lambda *a, **k: (order.append("topology"), {})[1]
    )
    monkeypatch.setattr(
        rb,
        "_load_fixture_digester",
        lambda r: (order.append("digests"), (lambda p: "d"), {})[1:],
    )

    def runner(argv, cwd=None, **kwargs):
        text = " ".join(str(part) for part in argv)
        order.append("standalone" if "--render-standalone" in text else "sync")
        return SimpleNamespace(returncode=0, stdout="")

    assert rb.STEP_ORDER == (
        "ac01", "standalone", "sync", "topology", "digests", "ceilings"
    )
    results = rb.run_steps(
        root,
        {
            "check_only": True,
            "steps": ("ac01", "standalone", "sync", "topology", "digests"),
        },
        runner,
    )

    assert [result.name for result in results] == list(results and [
        "ac01", "standalone", "sync", "topology", "digests"
    ])
    assert order == ["ac01", "standalone", "sync", "topology", "digests"]


def test_step_ac01_writes_only_differing_keys(rb, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    manifest = root / "tests" / "fixtures" / "ac01-baseline" / "hashes.json"
    baseline = {"alpha/a.md": "old", "alpha/b.md": "same", "alpha/c.md": "same"}
    manifest.write_text(
        __import__("json").dumps(baseline, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    current = dict(baseline, **{"alpha/a.md": "new"})
    monkeypatch.setattr(rb, "_render_matrix", lambda *a, **k: current)

    result = rb.step_ac01(root, {"check_only": False}, lambda *a, **k: None)

    written = __import__("json").loads(manifest.read_text(encoding="utf-8"))
    assert written == current
    assert result.wrote == 1
    assert manifest.read_bytes().endswith(b"\n")
    assert '\n "alpha/b.md": "same"' in manifest.read_text(encoding="utf-8")


def test_step_ac01_idempotent_second_run(rb, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    manifest = root / "tests" / "fixtures" / "ac01-baseline" / "hashes.json"
    baseline = {"alpha/a.md": "hash"}
    manifest.write_text(
        __import__("json").dumps(baseline, indent=1, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    before = manifest.read_bytes()
    monkeypatch.setattr(rb, "_render_matrix", lambda *a, **k: dict(baseline))

    result = rb.step_ac01(root, {"check_only": False}, lambda *a, **k: None)

    assert result.wrote == 0
    assert manifest.read_bytes() == before


def test_step_digests_patches_only_fixture_trees_line(rb, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    surface = root / "tests" / "test_opencode_v2_surface.py"
    surface.parent.mkdir(parents=True, exist_ok=True)
    content = (
        "# log comment line one\n"
        "# log comment line two\n"
        "_FIXTURE_TREES = {\n"
        '    "ac01-baseline": "OLD_DIGEST",\n'
        '    "compact-golden": "KEEP_DIGEST",\n'
        "}\n"
    )
    surface.write_text(content, encoding="utf-8")
    fixture = root / "tests" / "fixtures" / "ac01-baseline"
    fixture.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(
        rb,
        "_load_fixture_digester",
        lambda r: (lambda p: "NEW_DIGEST", {"ac01-baseline": "OLD_DIGEST"}),
    )

    result = rb.step_digests(root, {"check_only": False}, lambda *a, **k: None)

    after = surface.read_text(encoding="utf-8")
    lines = after.splitlines(keepends=True)
    assert lines[0] == "# log comment line one\n"
    assert lines[1] == "# log comment line two\n"
    assert lines[2] == "_FIXTURE_TREES = {\n"
    assert lines[3] == '    "ac01-baseline": "NEW_DIGEST",\n'
    assert lines[4] == '    "compact-golden": "KEEP_DIGEST",\n'
    assert "OLD_DIGEST" not in after
    assert result.wrote == 1


def test_preflight_allows_uncommitted_sources_and_hand_goldens(rb, tmp_path):
    root = _step_root(tmp_path)

    def runner(argv, cwd=None, **kwargs):
        text = " ".join(str(part) for part in argv)
        if "rev-parse" in text:
            return SimpleNamespace(returncode=0, stdout="origin/main")
        return SimpleNamespace(
            returncode=0,
            stdout=" M agents/1-generic/developer.md\n M tests/fixtures/compact-golden/agents-managed.md\n",
        )

    result = rb.preflight(root, {"base": "origin/main"}, runner)

    assert result.dirty == []
    assert result.base == "origin/main"
    assert result.warning == ""


def test_preflight_blocks_dirty_artifact(rb, tmp_path):
    root = _step_root(tmp_path)

    def runner(argv, cwd=None, **kwargs):
        text = " ".join(str(part) for part in argv)
        if "rev-parse" in text:
            return SimpleNamespace(returncode=0, stdout="origin/main")
        return SimpleNamespace(returncode=0, stdout=" M standalone/agents/x.md\n")

    result = rb.preflight(root, {"base": "origin/main"}, runner)

    assert result.dirty


def test_preflight_fixture_trees_linewise(rb, tmp_path):
    root = _step_root(tmp_path)

    def make_runner(diff_text):
        def runner(argv, cwd=None, **kwargs):
            text = " ".join(str(part) for part in argv)
            if "rev-parse" in text:
                return SimpleNamespace(returncode=0, stdout="origin/main")
            if "status --porcelain" in text:
                return SimpleNamespace(
                    returncode=0, stdout=" M tests/test_opencode_v2_surface.py\n"
                )
            return SimpleNamespace(returncode=0, stdout=diff_text)

        return runner

    allowed = make_runner(
        "@@ -5518,1 +5518,1 @@\n-    \"ac01-baseline\": \"OLD\",\n+    \"ac01-baseline\": \"NEW\",\n"
    )
    blocked = make_runner("@@ -10,1 +10,1 @@\n-def helper():\n+def helper2():\n")

    assert rb.preflight(root, {"base": "origin/main"}, allowed).dirty == []
    assert rb.preflight(root, {"base": "origin/main"}, blocked).dirty


def test_resolve_base_falls_back_to_local_main_with_warning(rb, tmp_path):
    root = _step_root(tmp_path)

    def runner(argv, cwd=None, **kwargs):
        text = " ".join(str(part) for part in argv)
        code = 1 if "origin/main" in text else 0
        return SimpleNamespace(returncode=code, stdout="main")

    base, warning = rb.resolve_base(root, {"base": "origin/main"}, runner)

    assert base == "main"
    assert "main" in warning

