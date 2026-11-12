"""Opt-in --fail-on-p0 flag (#1085b / #1155 F5, AC-FOP-1..8)."""
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402

_FIX = Path(__file__).resolve().parent / "fixtures" / "active-set" / "p10"
_SYNC = _ROOT / "scripts" / "sync.py"


def test_warn_p0_recorded_once():
    log = SyncLog()
    log.warn("x", p0=True)
    log.warn("x", p0=True)
    assert log.p0 == ["x"]
    assert len(log.warnings) == 1


def test_warning_alias_p0_and_default():
    log = SyncLog()
    log.warning("y", p0=True)
    log.warning("z")
    assert log.p0 == ["y"]
    assert len(log.warnings) == 2


@pytest.fixture
def project(tmp_path):
    p = tmp_path / "p10"
    (p / ".meta-config").mkdir(parents=True)
    shutil.copy(_FIX / ".meta-config" / "project.yaml", p / ".meta-config" / "project.yaml")
    subprocess.run(["git", "init", "-q"], cwd=p, check=True)
    return p


def _run(project, monkeypatch, capsys, *extra):
    import sync as sync_mod

    monkeypatch.chdir(project)
    monkeypatch.setattr(sys, "argv", [
        "sync.py", "--config", str(project / ".meta-config" / "project.yaml"), *extra])
    try:
        sync_mod.main()
        rc = 0
    except SystemExit as exc:
        rc = int(exc.code or 0)
    return rc, capsys.readouterr().err


def _fake_shadow(monkeypatch):
    import lib.gitignore as gi

    monkeypatch.setattr(gi, "detect_shadowed_provider_roots", lambda *a, **k: ["shadowed root"])


def test_p0_plain_sync_exit_zero_flag_exit_one(project, monkeypatch, capsys):
    _fake_shadow(monkeypatch)
    rc, _ = _run(project, monkeypatch, capsys, "--init")
    assert rc == 0
    rc, err = _run(project, monkeypatch, capsys, "--init", "--fail-on-p0")
    assert rc == 1
    assert "[P0]" in err and "--fail-on-p0" in err


def test_no_p0_flag_exit_zero(project, monkeypatch, capsys):
    rc, err = _run(project, monkeypatch, capsys, "--init", "--fail-on-p0")
    assert rc == 0, err[-1500:]


def test_check_accepts_flag_and_follows_check_path(project, monkeypatch, capsys):
    _run(project, monkeypatch, capsys, "--init")
    _fake_shadow(monkeypatch)
    rc, err = _run(project, monkeypatch, capsys, "--check", "--fail-on-p0")
    assert rc == 0, err[-1500:]


def test_strict_without_doctor_still_rejected():
    r = subprocess.run([sys.executable, str(_SYNC), "--fail-on-p0", "--strict"],
                       capture_output=True, text=True, encoding="utf-8", errors="replace",
                       timeout=60)
    assert r.returncode != 0
    assert "--doctor" in r.stderr


def test_ci_workflow_uses_flag():
    import yaml

    text = (_ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
    data = yaml.safe_load(text)
    assert data
    assert "python scripts/sync.py --fail-on-p0" in text
