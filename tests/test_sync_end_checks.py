"""Task 0b.6: context/active-set checks run at sync end and only report (AC-08, AC-43)."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.active_set import compute_active_set  # noqa: E402
from lib.consistency import active_set_refs  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.sync_pipeline import _sync_stage_context_checks  # noqa: E402

_FIX = Path(__file__).resolve().parent / "fixtures" / "active-set" / "p10"
_SYNC = _ROOT / "scripts" / "sync.py"


def _project(tmp_path: Path) -> Path:
    project = tmp_path / "p10"
    (project / ".meta-config").mkdir(parents=True)
    shutil.copy(_FIX / ".meta-config" / "project.yaml", project / ".meta-config" / "project.yaml")
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    return project


def _sync_cli(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC), "--config", str(project / ".meta-config" / "project.yaml"), "--init"],
        cwd=project, capture_output=True, text=True, timeout=300)


def _sync_in_process(project: Path, monkeypatch) -> int:
    """Run sync.main() in-process (allows monkeypatching); returns the exit code."""
    import sync as sync_mod

    monkeypatch.chdir(project)
    monkeypatch.setattr(sys, "argv", [
        "sync.py", "--config", str(project / ".meta-config" / "project.yaml"), "--init"])
    try:
        sync_mod.main()
    except SystemExit as exc:
        return int(exc.code or 0)
    return 0


@pytest.fixture(scope="module")
def p10_synced(tmp_path_factory):
    project = _project(tmp_path_factory.mktemp("p10sync"))
    result = _sync_cli(project)
    return project, result


def test_p10_sync_exit_zero_without_dangling_dispatch(p10_synced):
    # Task 1.20 (AC-49): p10 renders no dispatch to an inactive role any more.
    project, result = p10_synced
    assert result.returncode == 0, result.stdout[-1000:] + result.stderr[-1000:]
    text = (project / "sync.log").read_text(encoding="utf-8")
    assert "active-set.dangling-dispatch" not in text


def test_dangling_dispatch_is_logged_as_error_report_only(p10_synced):
    # ERROR level (Task 1.20) is still report-only: it lands in sync.log's error
    # list, never in the warnings and never changes the exit code.
    project, _ = p10_synced
    agent = project / ".claude" / "agents" / "developer.md"
    original = agent.read_text(encoding="utf-8")
    try:
        agent.write_text(original + "\nDelegiere an `validator`.\n", encoding="utf-8")
        log = SyncLog()
        _stage(project, log)
    finally:
        agent.write_text(original, encoding="utf-8")
    assert any("active-set.dangling-dispatch" in e and "validator" in e for e in log.errors)
    assert not any("active-set.dangling-dispatch" in w for w in log.warnings)


def test_error_finding_keeps_real_sync_exit_code_zero(tmp_path, monkeypatch):
    # A real (in-process) sync with an injected ERROR-level dangling dispatch:
    # the finding lands in sync.log as [ERROR], the exit code stays 0.
    from lib.consistency.report import Finding, Severity

    monkeypatch.setattr(active_set_refs, "check_dangling_dispatch", lambda *a, **k: [
        Finding(Severity.ERROR, "active-set.dangling-dispatch", ".claude/agents/x.md",
                "dispatch to inactive role 'validator' (1x, first line 1)")])
    project = _project(tmp_path)
    assert _sync_in_process(project, monkeypatch) == 0
    text = (project / "sync.log").read_text(encoding="utf-8")
    assert any(ln.startswith("[ERROR]") and "active-set.dangling-dispatch" in ln
               for ln in text.splitlines())


def test_info_findings_are_logged_as_info_not_warn(p10_synced, monkeypatch):
    from lib.consistency.report import Finding, Severity

    project, _ = p10_synced
    monkeypatch.setattr(active_set_refs, "check_keyword_overlap", lambda *a, **k: [
        Finding(Severity.INFO, "routing.keyword-overlap", "config/role-defaults.yaml", "kw 'x'")])
    log = SyncLog()
    _stage(project, log)
    assert any("routing.keyword-overlap" in i for i in log.infos)
    assert not any("routing.keyword-overlap" in w for w in log.warnings)


def _stage(project: Path, log: SyncLog, **kwargs) -> None:
    config = yaml.safe_load((project / ".meta-config" / "project.yaml").read_text(encoding="utf-8"))
    active = compute_active_set(config, _ROOT, project)
    _sync_stage_context_checks(_ROOT, project, config, active, log, **kwargs)


def test_stage_check_exception_is_fail_soft(p10_synced, monkeypatch):
    project, _ = p10_synced

    def boom(*args, **kwargs):
        raise RuntimeError("kaputt")

    monkeypatch.setattr(active_set_refs, "check_dangling_dispatch", boom)
    log = SyncLog()
    _stage(project, log)  # must not raise
    assert any("check_dangling_dispatch" in w and "kaputt" in w for w in log.warnings)
    # the remaining checks still ran
    assert any("active-set.unresolved-placeholder" in w for w in log.warnings)


def test_stage_measures_artifacts_once(p10_synced, monkeypatch):
    import lib.context_report as cr

    project, _ = p10_synced
    calls = []
    real = cr.measure_artifacts
    monkeypatch.setattr(cr, "measure_artifacts", lambda *a, **k: calls.append(1) or real(*a, **k))
    _stage(project, SyncLog())
    assert len(calls) == 1


def test_stage_drains_info_messages():
    log = SyncLog()
    _sync_stage_context_checks(_ROOT, Path("/nonexistent-project"), {}, None, log,
                               info_messages=["routing.examples-language-fallback: role 'x' ..."])
    assert any("routing.examples-language-fallback" in i for i in log.infos)  # even if setup fails soft


def test_fallback_line_reaches_real_sync_log(tmp_path, monkeypatch):
    import lib.delegation_table as dt

    real = dt.load_roles_config

    def fake(root):
        cfg = dict(real(root))
        roles = dict(cfg["roles"])
        dev = dict(roles["developer"])
        dev["routing_patterns"] = {"keywords": ["k"], "examples": {"Klingon": ["a"]}}
        roles["developer"] = dev
        cfg["roles"] = roles
        return cfg

    monkeypatch.setattr(dt, "load_roles_config", fake)
    project = _project(tmp_path)
    code = _sync_in_process(project, monkeypatch)
    assert code == 0
    text = (project / "sync.log").read_text(encoding="utf-8")
    assert any(ln.startswith("[INFO]") and "routing.examples-language-fallback" in ln
               and "developer" in ln for ln in text.splitlines())


def test_check_exception_does_not_change_exit_code(tmp_path, monkeypatch):
    def boom(*args, **kwargs):
        raise RuntimeError("kaputt")

    monkeypatch.setattr(active_set_refs, "check_dangling_dispatch", boom)
    project = _project(tmp_path)
    assert _sync_in_process(project, monkeypatch) == 0
    text = (project / "sync.log").read_text(encoding="utf-8")
    assert "check_dangling_dispatch: check failed: kaputt" in text


# --- AC-29 (2a.3 review fix): context-profile summary line in sync.log ------


def test_stage_drains_profile_info_messages():
    # The drain must run before (and independently of) the fail-soft setup, so
    # the summary lines survive even when a check module fails to import.
    log = SyncLog()
    _sync_stage_context_checks(
        _ROOT, Path("/nonexistent-project"), {}, None, log,
        profile_info_messages=[
            "context-profile: Claude profile=full mode=full preset=default "
            "(sources: context_file_mode=default, profile=default, "
            "rules_preset=default)"])
    assert any("context-profile: Claude profile=full" in i for i in log.infos)


def test_context_profile_line_single_and_idempotent_across_runs(tmp_path, monkeypatch):
    # Default (full) config: exactly one summary line per active provider --
    # no double log at full -- and a second run must not accumulate lines.
    project = _project(tmp_path)
    for run in range(2):
        assert _sync_in_process(project, monkeypatch) == 0, f"run {run} failed"
        text = (project / "sync.log").read_text(encoding="utf-8")
        hits = [ln for ln in text.splitlines()
                if "context-profile: Claude profile=" in ln]
        assert len(hits) == 1, f"run {run}: {hits}"
        assert hits[0].startswith("[INFO]")
        assert "profile=full mode=full preset=default" in hits[0]
        # Stable provenance core; rules_preset flips to "explicit" only once
        # config auto-fill has persisted the key (second run), so it is not
        # asserted here.
        assert ("sources: context_file_mode=default, profile=default"
                in hits[0])


def test_context_profile_line_reports_explicit_mode_source(tmp_path, monkeypatch):
    # IC-02/AC-29: an explicitly set context_file.mode is visible as
    # source=explicit on the summary line in sync.log.
    project = _project(tmp_path)
    cfg = project / ".meta-config" / "project.yaml"
    cfg.write_text(
        cfg.read_text(encoding="utf-8")
        + "context-profile: compact\ncontext_file:\n  mode: full\n",
        encoding="utf-8")
    assert _sync_in_process(project, monkeypatch) == 0
    text = (project / "sync.log").read_text(encoding="utf-8")
    hits = [ln for ln in text.splitlines()
            if "context-profile: Claude profile=" in ln]
    assert len(hits) == 1, hits
    assert "profile=compact mode=full" in hits[0]
    assert "context_file_mode=explicit" in hits[0]
