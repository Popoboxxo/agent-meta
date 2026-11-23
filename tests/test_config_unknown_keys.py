"""Regression tests for issue #1141 — unknown top-level config keys warn only.

A misspelled top-level key in ``.meta-config/project.yaml`` (e.g.
``dod-presett``) must produce exactly one ``config.unknown-key`` WARNING with
a ``did you mean`` suggestion — and must never change the exit code of
``--validate`` / ``--audit-config``.

Run: python3 -m pytest tests/test_config_unknown_keys.py -q
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SYNC_PY = _REPO_ROOT / "scripts" / "sync.py"
_SCENARIO_CONFIG = (
    _REPO_ROOT / "tests" / "scenarios" / "configs" / "01-minimal-claude.project.yaml"
)
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.consistency.config_unknown_keys import check_unknown_config_keys  # noqa: E402
from lib.consistency.report import Severity, print_report  # noqa: E402


def _cfg(tmp_path: Path, body: str) -> Path:
    path = tmp_path / ".meta-config" / "project.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _unknown(findings):
    return [f for f in findings if f.check == "config.unknown-key"]


_BASE = "project:\n  name: p\n  prefix: p\n  short: p\n"


# ---------------------------------------------------------------------------
# Unit level
# ---------------------------------------------------------------------------


def test_valid_config_has_no_unknown_key_finding(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path, _BASE)
    assert _unknown(check_unknown_config_keys(_REPO_ROOT, cfg)) == []


def test_typo_dod_presett_warns_with_suggestion(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path, _BASE + "dod-presett: full\n")
    findings = _unknown(check_unknown_config_keys(_REPO_ROOT, cfg))
    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    assert "dod-presett" in findings[0].message
    assert "did you mean" in findings[0].message
    assert "dod-preset" in findings[0].message


def test_orchestator_typo_suggests_orchestrator(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path, _BASE + "orchestator:\n  max_depth: 3\n")
    findings = _unknown(check_unknown_config_keys(_REPO_ROOT, cfg))
    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    assert "orchestrator" in findings[0].message


def test_warning_only_does_not_change_exit_code(tmp_path: Path, capsys) -> None:
    cfg = _cfg(tmp_path, _BASE + "dod-presett: full\n")
    findings = check_unknown_config_keys(_REPO_ROOT, cfg)
    assert print_report(findings, cfg.parent, changed_only=False) == 0
    output = capsys.readouterr().out
    assert "WRN" in output
    assert "1 warning(s) found" in output
    assert "did you mean" in output


def test_no_close_match_omits_suggestion(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path, _BASE + "zzzqqqxyz: true\n")
    findings = _unknown(check_unknown_config_keys(_REPO_ROOT, cfg))
    assert len(findings) == 1
    assert findings[0].severity == Severity.WARNING
    assert "did you mean" not in findings[0].message


def test_nested_unknown_key_is_not_reported(tmp_path: Path) -> None:
    cfg = _cfg(tmp_path, _BASE + "dod:\n  typo: full\n")
    assert _unknown(check_unknown_config_keys(_REPO_ROOT, cfg)) == []


def test_missing_config_is_silent(tmp_path: Path) -> None:
    missing = tmp_path / ".meta-config" / "project.yaml"
    assert check_unknown_config_keys(_REPO_ROOT, missing) == []


# ---------------------------------------------------------------------------
# CLI level — rc must stay 0 on both paths
# ---------------------------------------------------------------------------


def _run_cli(tmp_path: Path, *flags: str) -> subprocess.CompletedProcess[str]:
    config_dir = tmp_path / ".meta-config"
    config_dir.mkdir(parents=True, exist_ok=True)
    body = _SCENARIO_CONFIG.read_text(encoding="utf-8")
    (config_dir / "project.yaml").write_text(
        body + "\ndod-presett: full\n", encoding="utf-8"
    )
    env = os.environ.copy()
    env["TMPDIR"] = str(tmp_path / "tmp")
    (tmp_path / "tmp").mkdir(exist_ok=True)
    return subprocess.run(
        [sys.executable, str(_SYNC_PY), *flags],
        cwd=tmp_path,
        env=env,
        capture_output=True,
        text=True,
        timeout=120,
    )


def test_validate_cli_warns_and_returns_zero(tmp_path: Path) -> None:
    result = _run_cli(tmp_path, "--validate")
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "config.unknown-key" in output
    assert "dod-presett" in output
    assert "did you mean" in output
    assert "dod-preset" in output


def test_audit_config_cli_warns_and_returns_zero(tmp_path: Path) -> None:
    result = _run_cli(tmp_path, "--audit-config")
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "config.unknown-key" in output
    assert "dod-presett" in output
    assert "did you mean" in output


def test_validate_config_only_cli_warns_and_returns_zero(tmp_path: Path) -> None:
    result = _run_cli(tmp_path, "--validate-config-only")
    output = result.stdout + result.stderr
    assert result.returncode == 0, output
    assert "config.unknown-key" in output
    assert "dod-preset" in output
