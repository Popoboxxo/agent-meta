"""#1203: --backup-label is canonical, --label a deprecated alias."""

import json
import subprocess
import sys
from pathlib import Path

_SYNC = Path(__file__).resolve().parent.parent / "scripts" / "sync.py"


def _run(*args):
    return subprocess.run(
        [sys.executable, str(_SYNC), "--backup", "--dry-run", *args],
        capture_output=True, text=True, timeout=120,
    )


def _label(proc):
    assert proc.returncode == 0, proc.stderr
    out = proc.stdout
    return json.JSONDecoder().raw_decode(out[out.index("{"):])[0].get("label")


def test_both_flags_same_label_and_deprecation_on_stderr():
    new = _run("--backup-label", "x1")
    old = _run("--label", "x1")
    assert _label(new) == _label(old) == "x1"
    assert "--label is deprecated" in old.stderr
    assert "--label is deprecated" not in new.stderr


def test_help_names_backup_label():
    proc = subprocess.run([sys.executable, str(_SYNC), "--help"],
                          capture_output=True, text=True, timeout=60)
    assert "--backup-label" in proc.stdout and "--label" in proc.stdout


def test_last_flag_wins_when_both_given():
    assert _label(_run("--backup-label", "new", "--label", "old")) == "old"
