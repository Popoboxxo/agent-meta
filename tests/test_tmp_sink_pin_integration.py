"""Issue #1189 reproduction as subprocess gates (AC-1189-12/13, I1/I2).

Under the framework pin (``TMPDIR=TEMP=TMP=<repo>/.tmp``) the sync-time
validator and ``load_config`` must not reject the repository: the pin is a
transport detail, never evidence about the system temp root.

Run: python -m pytest tests/test_tmp_sink_pin_integration.py -q
"""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT))

from tests.timeouts import SYNC_VALIDATE_TIMEOUT  # noqa: E402

_FORBIDDEN = "tmp-sink.system-temp-exception"


def _pinned_env() -> dict:
    sink = REPO_ROOT / ".tmp"
    sink.mkdir(exist_ok=True)
    env = dict(os.environ)
    for key in ("TMPDIR", "TEMP", "TMP"):
        env[key] = os.path.realpath(sink)
    return env


def _run(argv: list) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, *argv],
        cwd=str(REPO_ROOT),
        env=_pinned_env(),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=SYNC_VALIDATE_TIMEOUT,
    )


def _assert_ok(result: subprocess.CompletedProcess) -> None:
    out = result.stdout + result.stderr
    assert result.returncode == 0, out
    assert _FORBIDDEN not in out


def test_sync_validate_under_pin_exits_zero():
    _assert_ok(_run([str(REPO_ROOT / "scripts" / "sync.py"), "--validate"]))


def test_load_config_under_pin_exits_zero_fast():
    code = (
        "import sys; sys.path.insert(0, 'scripts'); "
        "from pathlib import Path; from lib.config import load_config; "
        "load_config(Path('.meta-config/project.yaml'))"
    )
    _assert_ok(_run(["-c", code]))


def test_dry_run_validate_under_pin_exits_zero():
    _assert_ok(_run([str(REPO_ROOT / "scripts" / "sync.py"), "--dry-run", "--validate"]))
