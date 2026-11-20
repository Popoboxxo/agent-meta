"""Unit tests for the rebaseline helper (Tasks 1-9).

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


# --- Task 6: ceiling report, log and exit codes ------------------------------


def test_ceiling_block_names_provider_artifact_old_new(rb):
    report = {"alpha": {"entry-file": {"bytes": 900}}}
    ist_full = {"alpha": {"entry-file": 400}}

    block = rb.ceiling_repin_block(report, ist_full, {})

    assert "alpha" in block
    assert "entry-file" in block
    assert "400" in block
    assert "900" in block


def test_ceiling_block_tolerance_and_file_unchanged(rb):
    tolerance_file = _REPO_ROOT / "tests" / "test_context_budgets.py"
    before = tolerance_file.read_bytes()
    small = rb.ceiling_repin_block(
        {"alpha": {"entry-file": {"bytes": 410}}},
        {"alpha": {"entry-file": 400}},
        {},
    )

    assert small == ""
    assert tolerance_file.read_bytes() == before


def test_exit_codes_cover_zero_to_six(rb):
    assert [
        rb.EXIT_OK, rb.EXIT_DRIFT, rb.EXIT_USAGE, rb.EXIT_GATE,
        rb.EXIT_SUBPROCESS, rb.EXIT_VERIFY, rb.EXIT_RESIDUAL,
    ] == [0, 1, 2, 3, 4, 5, 6]


def test_append_log_valid_line_only_on_change(rb, tmp_path):
    root = _step_root(tmp_path)
    log = root / ".meta-config" / "rebaseline-log.jsonl"
    entry = {
        "ts": "2026-11-19T00:00:00+00:00",
        "reason": "intentional rebaseline",
        "base": "origin/main",
        "head": "abc",
        "steps": ["ac01"],
        "changed_files": ["tests/fixtures/ac01-baseline/hashes.json"],
        "changed_keys": ["alpha/a.md"],
        "gate": "ok",
        "verify": "ok",
        "idempotency": "ok",
    }

    path = rb.append_log(root, entry)

    assert path == log
    line = log.read_text(encoding="utf-8").splitlines()
    assert len(line) == 1
    parsed = __import__("json").loads(line[0])
    assert parsed["reason"] == "intentional rebaseline"
    assert parsed["idempotency"] == "ok"

    rb.append_log(root, dict(entry, changed_files=[]))
    assert len(log.read_text(encoding="utf-8").splitlines()) == 1


def test_json_report_fields(rb):
    report = rb.build_json_report(
        [{"klass": "AC", "status": "ok"}],
        [{"name": "ac01", "wrote": 1}],
        [{"klass": "AC", "status": "ok"}],
        {"changed": 1, "gate": "ok", "verify": "ok", "idempotent": "ok"},
    )

    assert set(report) == {"pre", "steps", "post", "result"}


# --- Task 7: pipeline, verify and idempotency --------------------------------


@pytest.fixture()
def pbp():
    """Import the pipeline module under test."""
    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))
    from lib import rebaseline_pipeline

    return rebaseline_pipeline


def _patch_pipeline(rb, pbp, monkeypatch, tmp_path, **overrides):
    """Mock every side-effecting collaborator; return shared event log."""
    events = []
    logs = []
    scratch = tmp_path / ".tmp" / "rebaseline"
    scratch.mkdir(parents=True, exist_ok=True)
    monkeypatch.setattr(pbp, "_scratch_dir", lambda root, options: scratch)

    dirty = overrides.get("dirty", [])
    pf = rb.Preflight(overrides.get("base", "origin/main"), "", list(dirty))
    monkeypatch.setattr(
        rb, "preflight",
        lambda root, options, runner: (events.append("preflight"), pf)[1],
    )

    def fake_impact(root, runner):
        events.append("pre")
        return [rb.PinStatus("AC", "artifact", "ok", "auto")]

    monkeypatch.setattr(rb, "impact_report", fake_impact)

    step_seq = overrides.get("steps") or [
        [rb.StepResult("ac01", 0, "done", "ok")]
    ]
    counter = {"n": 0}

    def fake_run_steps(root, options, runner):
        count = counter["n"] + 1
        counter["n"] = count
        events.append("steps{}".format(count))
        return list(step_seq[min(count - 1, len(step_seq) - 1)])

    monkeypatch.setattr(rb, "run_steps", fake_run_steps)

    statuses = overrides.get("verify") or [
        rb.PinStatus("AC", "artifact", "ok", "auto")
    ]
    monkeypatch.setattr(
        pbp, "verify",
        lambda root, runner: (events.append("verify"), list(statuses))[1],
    )
    monkeypatch.setattr(
        pbp, "_changed_files",
        lambda root, pf, runner: list(overrides.get("changed_files", [])),
    )
    monkeypatch.setattr(
        pbp, "_changed_keys",
        lambda root, files, before: list(overrides.get("changed_keys", [])),
    )

    class FakeSnap:
        @classmethod
        def take(cls, root, paths):
            events.append("snapshot")
            return cls()

        def restore(self):
            events.append("restore")

    monkeypatch.setattr(pbp, "Snapshot", FakeSnap)
    monkeypatch.setattr(
        pbp, "append_log",
        lambda root, entry: (events.append("log"), logs.append(entry))[1],
    )
    return events, logs


def test_pipeline_order_preflight_steps_idempotency_verify_log(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    events, _ = _patch_pipeline(
        rb, pbp, monkeypatch, tmp_path,
        changed_files=["tests/fixtures/ac01-baseline/hashes.json"],
    )

    result = pbp.run_pipeline(
        root, {"base": "origin/main", "reason": "intentional rebaseline"},
        runner=lambda *a, **k: SimpleNamespace(returncode=0, stdout=""),
    )

    assert result.exit_code == 0
    assert events == [
        "preflight", "pre", "snapshot", "steps1", "steps2", "verify", "log"
    ]


def test_pipeline_dirty_baseline_exits_two(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    events, _ = _patch_pipeline(
        rb, pbp, monkeypatch, tmp_path, dirty=["standalone/agents/x.md"]
    )

    result = pbp.run_pipeline(root, {"reason": "intentional rebaseline"})

    assert result.exit_code == 2
    assert events == ["preflight"]
    assert "standalone/agents/x.md" in " ".join(result.warnings)


def test_pipeline_missing_config_exits_two(rb, pbp, tmp_path, monkeypatch):
    root = tmp_path / "no-config"
    root.mkdir()
    _patch_pipeline(rb, pbp, monkeypatch, tmp_path)

    result = pbp.run_pipeline(root, {"reason": "intentional rebaseline"})

    assert result.exit_code == 2


def test_pipeline_gate_violation_exits_three_and_rolls_back(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    events, _ = _patch_pipeline(
        rb, pbp, monkeypatch, tmp_path,
        changed_files=["src/unexpected.txt"],
    )

    result = pbp.run_pipeline(root, {"reason": "intentional rebaseline"})

    assert result.exit_code == 3
    assert "restore" in events
    assert "verify" not in events
    assert "log" not in events


def test_pipeline_unexpected_key_exits_three(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    events, _ = _patch_pipeline(
        rb, pbp, monkeypatch, tmp_path,
        changed_keys=["alpha/agents/unknown.md"],
    )

    result = pbp.run_pipeline(
        root, {"reason": "intentional rebaseline", "expect_key": ["alpha/known/*"]}
    )

    assert result.exit_code == 3
    assert "restore" in events


def test_pipeline_subprocess_failure_exits_four_and_rolls_back(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    events, _ = _patch_pipeline(
        rb, pbp, monkeypatch, tmp_path,
        steps=[[rb.StepResult("sync", 0, "sync failed", "failed")]],
    )

    result = pbp.run_pipeline(root, {"reason": "intentional rebaseline"})

    assert result.exit_code == 4
    assert "restore" in events
    assert "steps2" not in events


def test_pipeline_residual_drift_exits_six_but_verifies_and_logs(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    changed = "tests/fixtures/ac01-baseline/hashes.json"
    events, logs = _patch_pipeline(
        rb, pbp, monkeypatch, tmp_path,
        steps=[
            [rb.StepResult("ac01", 1, "wrote 1", "ok")],
            [rb.StepResult("ac01", 1, "wrote 1 again", "ok")],
        ],
        changed_files=[changed],
    )

    result = pbp.run_pipeline(root, {"reason": "intentional rebaseline"})

    assert result.exit_code == 6
    assert result.idempotency == "drift"
    assert result.residual
    assert "verify" in events and "log" in events
    assert logs[0]["idempotency"] == "failed"


def test_pipeline_red_pin_test_exits_five(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    changed = "tests/fixtures/ac01-baseline/hashes.json"
    events, logs = _patch_pipeline(
        rb, pbp, monkeypatch, tmp_path,
        verify=[rb.PinStatus("AC", "artifact", "betroffen", "auto")],
        changed_files=[changed],
    )

    result = pbp.run_pipeline(root, {"reason": "intentional rebaseline"})

    assert result.exit_code == 5
    assert result.verify == "failed"
    assert logs[0]["verify"] == "failed"


def test_pipeline_residual_and_red_verify_prefers_five(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    changed = "tests/fixtures/ac01-baseline/hashes.json"
    _patch_pipeline(
        rb, pbp, monkeypatch, tmp_path,
        steps=[
            [rb.StepResult("ac01", 1, "wrote 1", "ok")],
            [rb.StepResult("ac01", 1, "wrote 1 again", "ok")],
        ],
        verify=[rb.PinStatus("AC", "artifact", "betroffen", "auto")],
        changed_files=[changed],
    )

    result = pbp.run_pipeline(root, {"reason": "intentional rebaseline"})

    assert result.exit_code == 5
    assert result.idempotency == "drift"


def test_pipeline_check_only_writes_nothing(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    events, logs = _patch_pipeline(rb, pbp, monkeypatch, tmp_path)

    result = pbp.run_pipeline(root, {"check_only": True})

    assert result.exit_code == 0
    assert logs == []
    assert "log" not in events


def test_pipeline_skip_verify_marks_skipped(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    events, _ = _patch_pipeline(rb, pbp, monkeypatch, tmp_path)

    result = pbp.run_pipeline(
        root, {"reason": "intentional rebaseline", "skip_verify": True}
    )

    assert result.verify == "skipped"
    assert "verify" not in events


def test_verify_uses_impact_report(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)
    calls = []
    monkeypatch.setattr(
        rb, "impact_report",
        lambda r, runner: (calls.append(r), [
            rb.PinStatus("AC", "artifact", "ok", "auto")
        ])[1],
    )

    statuses = pbp.verify(root, runner=lambda *a, **k: None)

    assert calls and statuses[0].status == "ok"


def test_pipeline_allows_uncommitted_sources(rb, pbp, tmp_path, monkeypatch):
    root = _step_root(tmp_path)

    def runner(argv, cwd=None, **kwargs):
        text = " ".join(str(part) for part in argv)
        if "rev-parse" in text:
            return SimpleNamespace(returncode=0, stdout="origin/main")
        if "status --porcelain" in text:
            return SimpleNamespace(
                returncode=0, stdout=" M agents/1-generic/developer.md\n"
            )
        return SimpleNamespace(returncode=0, stdout="")

    monkeypatch.setattr(pbp, "_scratch_dir", lambda r, o: tmp_path / ".tmp")
    monkeypatch.setattr(rb, "impact_report", lambda r, run: [])
    monkeypatch.setattr(
        pbp, "verify", lambda r, run: []
    )
    monkeypatch.setattr(
        rb, "run_steps",
        lambda r, o, run: [rb.StepResult("ac01", 0, "done", "ok")],
    )
    monkeypatch.setattr(pbp, "_changed_files", lambda r, pf, run: [])
    monkeypatch.setattr(pbp, "_changed_keys", lambda r, files, before: [])

    result = pbp.run_pipeline(
        root, {"reason": "intentional rebaseline"}, runner=runner
    )

    assert result.exit_code == 0


# --- Task 8: entrypoint and CLI ----------------------------------------------


@pytest.fixture()
def entry():
    """Load the entrypoint script as a module (fresh per test)."""
    import importlib.util

    if str(_SCRIPTS) not in sys.path:
        sys.path.insert(0, str(_SCRIPTS))
    path = _SCRIPTS / "rebaseline.py"
    spec = importlib.util.spec_from_file_location("rebaseline_entry", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_entry_help_via_subprocess():
    import subprocess

    result = subprocess.run(
        [sys.executable, str(_SCRIPTS / "rebaseline.py"), "--help"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0
    for flag in ("--reason", "--expect", "--expect-key", "--base", "--check-only",
                 "--dry-run", "--root", "--steps", "--skip-verify", "--json"):
        assert flag in result.stdout


def test_entry_missing_reason_exits_two(entry, tmp_path):
    assert entry.main(["--root", str(tmp_path)]) == 2


def test_entry_unknown_step_exits_two(entry, tmp_path):
    assert (
        entry.main(
            ["--root", str(tmp_path), "--reason", "intentional rebaseline",
             "--steps", "ac01,nope"]
        )
        == 2
    )


def test_entry_check_only_exit_codes_with_mocked_pipeline(entry, tmp_path, monkeypatch, capsys):
    rb = pytest.importorskip("lib.rebaseline")
    pbp = pytest.importorskip("lib.rebaseline_pipeline")
    seen = []

    def fake_pipeline(root, options, runner=None):
        seen.append(options)
        code = rb.EXIT_DRIFT if options.get("_drift") else rb.EXIT_OK
        return pbp.PipelineResult(exit_code=code, pre=[], steps=[], post=[])

    monkeypatch.setattr(entry.pipeline, "run_pipeline", fake_pipeline)

    assert entry.main(["--check-only", "--root", str(tmp_path)]) == 0
    assert "RESULT" in capsys.readouterr().out
    assert seen[0]["check_only"] is True

    monkeypatch.setattr(
        entry.pipeline, "run_pipeline",
        lambda root, options, runner=None: pbp.PipelineResult(
            exit_code=rb.EXIT_DRIFT, pre=[], steps=[], post=[]),
    )
    assert entry.main(["--dry-run", "--root", str(tmp_path)]) == 1


def test_entry_json_fields(entry, tmp_path, monkeypatch, capsys):
    pbp = pytest.importorskip("lib.rebaseline_pipeline")
    monkeypatch.setattr(
        entry.pipeline, "run_pipeline",
        lambda root, options, runner=None: pbp.PipelineResult(
            exit_code=0, pre=[{"klass": "AC", "status": "ok"}], steps=[],
            post=[{"klass": "AC", "status": "ok"}], changed_files=[]),
    )

    entry.main(["--check-only", "--json", "--root", str(tmp_path)])

    payload = __import__("json").loads(capsys.readouterr().out.splitlines()[-1])
    assert set(payload) == {"pre", "steps", "post", "result"}


# --- Task 9: structure checks and provider/model agnosticism -----------------


_RB_LIB_PATHS = tuple(
    _SCRIPTS / "lib" / name
    for name in ("rebaseline.py", "rebaseline_pipeline.py")
)
_RB_ENTRY_PATH = _SCRIPTS / "rebaseline.py"
_LINE_CEILING = 600


def _parse_module(path):
    """Parse a source file into an AST (comments/docstrings stay inert)."""
    import ast

    return ast.parse(path.read_text(encoding="utf-8"))


def _forbidden_literals():
    """Registered provider names plus the repo's canonical model tiers.

    Provider names come from config/ai-providers.yaml (single source of truth),
    not from a hardcoded list, so a newly registered provider is covered.
    """
    import yaml

    data = yaml.safe_load(
        (_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8")
    )
    providers = set((data.get("providers") or {}).keys())
    models = {"haiku", "sonnet", "opus"}
    return providers | models


def _literal_offenders(path, forbidden):
    """String constants exactly equal to a provider/model name, with lines."""
    import ast

    found = []
    for node in ast.walk(_parse_module(path)):
        if (
            isinstance(node, ast.Constant)
            and isinstance(node.value, str)
            and node.value in forbidden
        ):
            found.append("{}:{}: {!r}".format(path.name, node.lineno, node.value))
    return found


def test_rebaseline_lib_modules_within_line_ceiling():
    """Both rebaseline lib modules stay at or below the 600-line ceiling."""
    for path in _RB_LIB_PATHS:
        count = len(path.read_text(encoding="utf-8").splitlines())
        assert count <= _LINE_CEILING, "{}: {} lines > {}".format(
            path.name, count, _LINE_CEILING
        )


def test_no_print_in_rebaseline_lib():
    """No print() in lib modules — output goes through return values / log."""
    import ast

    offenders = []
    for path in _RB_LIB_PATHS:
        for node in ast.walk(_parse_module(path)):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id == "print"
            ):
                offenders.append("{}:{}".format(path.name, node.lineno))
    assert not offenders, "print() in lib modules: {}".format(offenders)


def test_no_provider_or_model_literals_in_rebaseline_lib():
    """No hardcoded provider/model name in the rebaseline lib modules."""
    forbidden = _forbidden_literals()
    offenders = []
    for path in _RB_LIB_PATHS:
        offenders.extend(_literal_offenders(path, forbidden))
    assert not offenders, (
        "provider/model literal(s) in lib modules:\n" + "\n".join(offenders)
    )


def test_rebaseline_lib_imports_stdlib_only():
    """No new third-party dependency in lib modules (ADR 0001 allows only
    transitive PyYAML via the importlib-loaded test module, not a direct import)."""
    import ast

    stdlib = set(getattr(sys, "stdlib_module_names", ()))
    allowed = stdlib | {"lib", "__future__"}
    offenders = []
    for path in _RB_LIB_PATHS:
        for node in ast.walk(_parse_module(path)):
            if isinstance(node, ast.Import):
                roots = [alias.name.split(".")[0] for alias in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                roots = [(node.module or "").split(".")[0]]
            else:
                continue
            for root in roots:
                if root and root not in allowed:
                    offenders.append("{}:{}: {}".format(path.name, node.lineno, root))
    assert not offenders, (
        "non-stdlib import(s) in lib modules (ADR 0001: transitive PyYAML via "
        "importlib is allowed, a direct import is not):\n" + "\n".join(offenders)
    )


def test_rebaseline_entrypoint_is_provider_agnostic():
    """test_provider_agnostic_dispatch.py sweeps only scripts/lib/**; the
    argparse entrypoint is covered here (print() is allowed there per spec C1)."""
    offenders = _literal_offenders(_RB_ENTRY_PATH, _forbidden_literals())
    assert not offenders, (
        "provider/model literal(s) in entrypoint:\n" + "\n".join(offenders)
    )

