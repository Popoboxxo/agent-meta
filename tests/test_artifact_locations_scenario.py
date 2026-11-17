"""T21: one full end-to-end scenario for the artifact-locations matrix (#1186).

A single test drives the real CLI, the resolver, the generated data file, the
consistency checker, the admin write guard, the migration dry-run and both
routing hooks across eight phases A-H. Everything runs inside the sanctioned
scratch root ``.tmp/scenario-artifacts-1186/`` which is cleared before and
removed after the run (try/finally — no repo pollution).

All fixture content is synthetic and deterministic (fixed names/dates); no
production data, no external services and no wall-clock-sensitive assertions.

Run: python3 -m pytest tests/test_artifact_locations_scenario.py -q
"""
from __future__ import annotations

import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib import config as config_module  # noqa: E402
from lib.consistency import placeholders as ph  # noqa: E402
from lib.consistency.artifact_locations import (  # noqa: E402
    CHECK_LEGACY_WRITE,
    check_artifact_locations,
)
from lib.artifact_locations import (  # noqa: E402
    ArtifactLocationsError,
    CLASS_REGISTRY,
    resolve_artifact_cell_path,
    resolve_artifact_locations,
    resolve_scratch_path,
    validate_kind,
)
from lib.consistency.report import Severity  # noqa: E402

_SYNC_PY = _REPO_ROOT / "scripts" / "sync.py"
_RUN_SH = _REPO_ROOT / "tests" / "scenarios" / "run.sh"
_REGISTRY = _REPO_ROOT / "tests" / "scenarios" / "registry.md"
_GUARD_HOOK = _REPO_ROOT / "hooks" / "1-generic" / "artifact-path-guard.sh"
_BASH = shutil.which("bash") or "bash"
_SCRATCH = _REPO_ROOT / ".tmp" / "scenario-artifacts-1186"

_BASE_CONFIG = (
    'agent-meta-version: "1.1.0"\n'
    "ai-providers: [Claude]\n"
    "dod-preset: rapid-prototyping\n"
    "roles: [orchestrator, developer, tester, documenter, git]\n"
    "platforms: []\n"
    "project:\n"
    "  name: scenario-artifacts-1186\n"
    "  prefix: a1186\n"
    "  short: sc1186\n"
    "variables:\n"
    "  PROJECT_NAME: scenario-artifacts-1186\n"
)

# The 11 managed directory classes plus the D-6 conclusions marker.
_SCAFFOLD_DIRS = (
    "docs/specs", "docs/plans", "docs/concepts", "docs/spikes",
    "docs/reviews", "docs/audits", "docs/analysis", "docs/reports",
    "docs/adr", "docs/traceability", "docs/runbooks", "docs/conclusions",
)


def _make_project(name: str, extra: str = "") -> Path:
    """Create an isolated synthetic project inside the scratch root."""
    project = _SCRATCH / name
    meta = project / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "project.yaml").write_text(_BASE_CONFIG + extra, encoding="utf-8")
    return project


def _config_path(project: Path) -> Path:
    return project / ".meta-config" / "project.yaml"


def _run_sync(project: Path, *flags: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(_SYNC_PY), "--config", str(_config_path(project)), *flags],
        capture_output=True, text=True, cwd=str(project), timeout=90,
    )


def _status(project: Path) -> dict:
    result = _run_sync(project, "--status-artifacts", "--json")
    assert result.returncode == 0, result.stderr
    report: dict = json.loads(result.stdout)
    return report


def _resolved(project: Path) -> dict:
    path = project / ".meta-config" / "artifact-locations.resolved.json"
    assert path.is_file(), "Stage 14c data file missing"
    payload: dict = json.loads(path.read_text(encoding="utf-8"))
    return payload


def _legacy_write_findings(project: Path) -> set[str]:
    config = config_module.load_config(_config_path(project))
    findings = check_artifact_locations(_REPO_ROOT, project, config)
    legacy = [finding for finding in findings if finding.check == CHECK_LEGACY_WRITE]
    for finding in legacy:
        assert finding.severity == Severity.WARNING
    return {finding.file for finding in legacy}


def _run_guard_hook(project: Path, target: str) -> subprocess.CompletedProcess[str]:
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(project / target)},
        "cwd": str(project),
    }
    env = dict(os.environ)
    env["CLAUDE_PROJECT_DIR"] = str(project)
    return subprocess.run(
        [_BASH, str(_GUARD_HOOK)],
        input=json.dumps(payload), capture_output=True, text=True,
        cwd=str(project), env=env, timeout=30,
    )


def _admin_guard_rejects_dotdot(project: Path) -> tuple[str, bytes]:
    """Exercise the admin partial-section write guard without starting a server."""
    before = _config_path(project).read_bytes()
    spec = importlib.util.spec_from_file_location(
        "admin_server_scenario_99", _REPO_ROOT / "scripts" / "admin-server.py",
    )
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    try:
        spec.loader.exec_module(module)
        (project / ".meta-config").mkdir(parents=True, exist_ok=True)
        setattr(module.AdminRequestHandler, "root", project)
        setattr(
            module.AdminRequestHandler, "config_manager",
            module.ConfigManager(project, mode="project_admin"),
        )
        handler = module.AdminRequestHandler.__new__(module.AdminRequestHandler)
        setattr(handler, "_send_json", lambda result, status=200: None)
        setattr(handler, "_read_body", lambda: {
            "section": "artifact-locations",
            "data": {"classes": {"specs": {"path": "../x"}}},
        })
        try:
            handler._write_project_section()
        except ValueError as exc:
            return str(exc), before
        return "", before
    finally:
        sys.modules.pop(spec.name, None)


def test_artifact_locations_end_to_end() -> None:
    """Eight phases A-H cover the complete #1186 end-to-end contract."""
    shutil.rmtree(_SCRATCH, ignore_errors=True)
    try:
        _SCRATCH.mkdir(parents=True, exist_ok=True)

        # --- Phase A: default matrix, resolver, variables, allow-list,
        #     scaffold, migration dry-run, containment scratch, admin guard.
        project_a = _make_project("phase-a", "\nartifact-locations:\n  enabled: true\n")

        dry = _run_sync(project_a, "--dry-run")
        assert dry.returncode == 0, dry.stderr
        create_lines = [
            line for line in dry.stdout.splitlines()
            if "artifact scaffolding" in line and ".gitkeep" in line
        ]
        assert len(create_lines) == 12, create_lines
        assert not (project_a / "docs").exists(), "dry-run must not scaffold"

        real = _run_sync(project_a)
        assert real.returncode == 0, real.stderr
        for rel in _SCAFFOLD_DIRS:
            assert (project_a / rel / ".gitkeep").is_file(), rel
        assert not (project_a / ".tmp" / ".gitkeep").exists()
        assert not (project_a / ".meta-viz" / ".gitkeep").exists()

        # Schema/resolver: the registry has 23 classes and the empty config is total.
        assert len(CLASS_REGISTRY) == 23
        empty_matrix = resolve_artifact_locations({}, _REPO_ROOT, project_a)
        assert len(empty_matrix.classes) == 23
        assert empty_matrix.classes["specs"].path == "docs/specs"

        # Variable export: exactly 54 ARTIFACT_* names with the expected aliases.
        variables, _ = config_module.build_variables({}, _REPO_ROOT)
        artifact_names = {key for key in variables if key.startswith("ARTIFACT_")}
        assert len(artifact_names) == 54
        assert variables["ARTIFACT_SPECS_DIR"] == "docs/specs"
        assert variables["SE_BASE_DIR"] == variables["ARTIFACT_SE_ROOT"]
        assert variables["TMP_SINK_PATH"] == variables["ARTIFACT_SCRATCH_DIR"]

        # Placeholder allow-list: every derived name is registered.
        derived = {key for key in ph.derive_builder_vars(_REPO_ROOT) if key.startswith("ARTIFACT_")}
        assert derived == artifact_names
        assert derived <= ph._BUILTIN_VARS

        # Alias migration dry-run prints the snippet but leaves the file untouched.
        migrate_cfg = _SCRATCH / "phase-a" / ".meta-config" / "project-migrate.yaml"
        migrate_cfg.write_text(
            _BASE_CONFIG + "repo_containment:\n  tmp-sink:\n    path: .tmp-aliased\n",
            encoding="utf-8",
        )
        before_migrate = migrate_cfg.read_bytes()
        migrated = subprocess.run(
            [sys.executable, str(_SYNC_PY), "--config", str(migrate_cfg),
             "--migrate-artifact-aliases"],
            capture_output=True, text=True, cwd=str(project_a), timeout=60,
        )
        assert migrated.returncode == 0, migrated.stderr
        assert "artifact-locations.classes.scratch.path" in migrated.stdout
        assert ".tmp-aliased" in migrated.stdout
        assert migrate_cfg.read_bytes() == before_migrate, "dry-run rewrote the config"

        # Containment scratch resolution: one source, alias attribution visible.
        scratch_payload = _resolved(project_a)
        scratch_class = [
            entry for entry in scratch_payload["classes"] if entry["name"] == "scratch"
        ]
        assert len(scratch_class) == 1
        assert scratch_class[0]["path"] == resolve_scratch_path({}, {})[0] == ".tmp"
        alias_path, alias_source = resolve_scratch_path(
            {"repo_containment": {"tmp-sink": {"path": ".tmp-aliased"}}}, {},
        )
        assert alias_path == ".tmp-aliased"
        assert alias_source == "project-alias:repo_containment.tmp-sink.path"

        # Admin config write guard: ../x is refused before any disk write.
        message, config_before = _admin_guard_rejects_dotdot(project_a)
        assert "artifact-locations.classes.specs.path" in message, message
        assert _config_path(project_a).read_bytes() == config_before
        print("PHASE A: default matrix + resolver + vars + allow-list + scaffold "
              "+ migration + scratch + admin guard OK")

        # --- Phase B: preset selection + project override attribution.
        project_b = _make_project("phase-b", (
            "\nartifact-locations:\n"
            "  enabled: true\n"
            "  preset: minimal\n"
            "  classes:\n"
            "    audits:\n"
            "      path: compliance/audits\n"
        ))
        sync_b = _run_sync(project_b)
        assert sync_b.returncode == 0, sync_b.stderr
        assert (project_b / "compliance" / "audits" / ".gitkeep").is_file()
        assert (project_b / "docs" / "reviews" / ".gitkeep").is_file()  # minimal: files
        assert not (project_b / "docs" / "concepts").exists()  # minimal: inline
        report_b = _status(project_b)
        assert report_b["classes"]["audits"]["source"] == "project"
        assert report_b["classes"]["reviews"]["source"] == "project-preset:minimal"
        assert report_b["classes"]["concepts"]["mode"] == "inline"
        print("PHASE B: preset + project override attribution OK")

        # --- Phase C: 9 SE classes, per-cell contrast and AC-11 gate.
        project_c = _make_project("phase-c")
        cell_config = {
            "artifact-locations": {
                "enabled": True,
                "classes": {
                    "se-validation": {"path": "external-evidence"},
                    "se-requirements": {"path": "SE"},
                },
            },
        }
        cell_matrix = resolve_artifact_locations(cell_config, _REPO_ROOT, project_c)
        path_val = resolve_artifact_cell_path(
            "se-validation", 3, "Steuerung", False, matrix=cell_matrix,
        )
        path_req = resolve_artifact_cell_path(
            "se-requirements", 3, "Steuerung", False, matrix=cell_matrix,
        )
        assert path_val.startswith("external-evidence/")
        assert path_val.endswith("/validation/L3_Steuerung_Validation.md")
        assert path_req.startswith("SE/")
        assert path_req.endswith("/L3_Steuerung_Requirements.md")
        assert path_val != path_req

        project_c_off = _make_project("phase-c-off", (
            "\nsystems-engineering:\n  enabled: true\n"
            "artifact-locations:\n  enabled: true\n  classes:\n"
            '    se-requirements: {mode: "off"}\n'
        ))
        refused = _run_sync(project_c_off, "--dry-run")
        assert refused.returncode == 1
        assert "artifact-locations.se-required-off" in (refused.stdout + refused.stderr)
        assert "se-decomposition" in (refused.stdout + refused.stderr)

        project_c_decomp = _make_project("phase-c-decomp", (
            "\nsystems-engineering:\n  enabled: true\n"
            "artifact-locations:\n  enabled: true\n  classes:\n"
            '    se-decomposition: {mode: "off"}\n'
        ))
        allowed = _run_sync(project_c_decomp, "--dry-run")
        assert allowed.returncode == 0, allowed.stderr
        print("PHASE C: SE cell paths + AC-11 gate OK")

        # --- Phase D: baseline-based legacy-write detection.
        project_d = _make_project("phase-d", "\nartifact-locations:\n  enabled: true\n")
        (project_d / "docs" / "estimates").mkdir(parents=True)
        (project_d / "docs" / "estimates" / "baseline-note.md").write_text(
            "legacy note present at baseline time\n", encoding="utf-8",
        )
        sync_d = _run_sync(project_d)
        assert sync_d.returncode == 0, sync_d.stderr
        baseline_payload = _resolved(project_d)
        assert "docs/estimates/baseline-note.md" in baseline_payload["baseline"]["legacy_files"]

        # New writes after the baseline — markers/unmanaged/canonical ADR stay clean.
        (project_d / "docs" / "plans" / "audit-legacy.md").write_text("new\n", encoding="utf-8")
        (project_d / "docs" / "adr" / "0002-neu.md").write_text("new\n", encoding="utf-8")
        (project_d / "docs" / "adr" / "ADR-002_neu.md").write_text("new\n", encoding="utf-8")
        meta_state = project_d / ".meta-config" / "issue-labels-state.json"
        meta_state.write_text("{}", encoding="utf-8")

        legacy_files = _legacy_write_findings(project_d)
        assert legacy_files == {
            "docs/plans/audit-legacy.md", "docs/adr/0002-neu.md",
        }, legacy_files
        assert "docs/estimates/baseline-note.md" not in legacy_files
        assert "docs/conclusions/.gitkeep" not in legacy_files
        assert ".meta-config/issue-labels-state.json" not in legacy_files
        assert "docs/adr/ADR-002_neu.md" not in legacy_files
        assert (project_d / "docs" / "plans" / "audit-legacy.md").is_file(), "no auto-delete"

        report_d = _status(project_d)
        assert "docs/plans/audit-*.md" in report_d["legacy"]
        assert "docs/adr/[0-9][0-9][0-9][0-9]-*.md" in report_d["legacy"]
        assert ".meta-config/issue-labels-state.json" in report_d["unmanaged"]
        print("PHASE D: baseline legacy-write + exemptions OK")

        # --- Phase E: kind enum scoping and legacy kind writes.
        assert validate_kind("estimate", "analysis") == "estimate"
        assert "estimate" in report_d["classes"]["analysis"]["kinds"]
        (project_d / "docs" / "estimates" / "new.md").write_text("new\n", encoding="utf-8")
        assert "docs/estimates/new.md" in _legacy_write_findings(project_d)

        project_e = _make_project("phase-e", (
            "\nartifact-locations:\n  enabled: true\n  classes:\n"
            "    analysis:\n      kind: [bogus]\n"
        ))
        bad_kind = _run_sync(project_e, "--dry-run")
        assert bad_kind.returncode == 1
        assert "artifact-locations.kind-invalid" in (bad_kind.stdout + bad_kind.stderr)
        with pytest.raises(ArtifactLocationsError) as exc_info:
            validate_kind("bogus", "analysis")
        assert exc_info.value.code == "artifact-locations.kind-invalid"
        print("PHASE E: kind enum + legacy kind write OK")

        # --- Phase F: enabled:false is the exact legacy no-op.
        project_f = _make_project("phase-f", "\nartifact-locations:\n  enabled: false\n")
        sync_f = _run_sync(project_f)
        assert sync_f.returncode == 0, sync_f.stderr
        for rel in ("docs/specs", "docs/plans", "docs/spikes"):
            assert (project_f / rel / ".gitkeep").is_file(), rel
        for rel in (
            "docs/concepts", "docs/reviews", "docs/audits", "docs/analysis",
            "docs/reports", "docs/adr", "docs/traceability", "docs/runbooks",
            "docs/conclusions",
        ):
            assert not (project_f / rel).exists(), rel
        report_f = _status(project_f)
        assert report_f["enabled"] is False
        for name in ("specs", "audits", "scratch", "se-validation"):
            assert report_f["classes"][name]["source"] == "disabled", name
        assert _resolved(project_f)["enabled"] is False
        print("PHASE F: enabled:false legacy fallback OK")

        # --- Phase G: PreToolUse routing hook (real subprocess).
        guarded = _run_guard_hook(project_a, "docs/estimates/new.md")
        assert guarded.returncode == 2, guarded.stdout + guarded.stderr
        assert "legacy" in (guarded.stdout + guarded.stderr).lower()
        assert _run_guard_hook(project_a, "docs/audits/x.md").returncode == 0
        assert _run_guard_hook(project_a, "docs/conclusions/.gitkeep").returncode == 0
        print("PHASE G: artifact-path-guard routing OK")

        # --- Phase H: scenario catalog + reserved-ID guard.
        catalog = subprocess.run(
            [str(_RUN_SH), "99"], capture_output=True, text=True,
            cwd=str(_REPO_ROOT), timeout=115,
        )
        assert catalog.returncode == 0, catalog.stdout + catalog.stderr
        assert "PASS  99-artifact-locations-matrix" in catalog.stdout, catalog.stdout

        registry_text = _REGISTRY.read_text(encoding="utf-8")
        assert "| `99-artifact-locations-matrix`" in registry_text
        configs_dir = _REPO_ROOT / "tests" / "scenarios" / "configs"
        asserts_dir = _REPO_ROOT / "tests" / "scenarios" / "asserts"
        for reserved in ("94", "95", "96", "97", "98"):
            assert not list(configs_dir.glob(reserved + "-*.project.yaml")), reserved
            assert not list(asserts_dir.glob(reserved + "-*.sh")), reserved
            assert not has_line_starting(registry_text, "| `" + reserved + "-")
        print("PHASE H: scenario 99 catalog + reserved IDs 94-98 OK")

    finally:
        shutil.rmtree(_SCRATCH, ignore_errors=True)


def has_line_starting(text: str, prefix: str) -> bool:
    """Return True when a line starts with *prefix* (explicit loop, deterministic)."""
    for line in text.splitlines():
        if line.startswith(prefix):
            return True
    return False
