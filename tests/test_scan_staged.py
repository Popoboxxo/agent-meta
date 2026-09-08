"""sync.py --scan-staged (issue #694): exposes the existing
scan_for_secrets() to agents as a pre-commit check, without requiring a
Python import inside a Bash instruction block."""

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _init_repo(tmp_path):
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.email", "t@example.com"], cwd=tmp_path, check=True)
    subprocess.run(["git", "config", "user.name", "t"], cwd=tmp_path, check=True)


def test_scan_staged_passes_on_clean_diff(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "file.py").write_text("print('hello')\n", encoding="utf-8")
    subprocess.run(["git", "add", "file.py"], cwd=tmp_path, check=True)

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--scan-staged"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0


def test_scan_staged_fails_on_secret_looking_content(tmp_path):
    _init_repo(tmp_path)
    (tmp_path / "config.py").write_text(
        'AWS_SECRET_ACCESS_KEY = "AKIAABCDEFGHIJKLMNOP"\n', encoding="utf-8",
    )
    subprocess.run(["git", "add", "config.py"], cwd=tmp_path, check=True)

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--scan-staged"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 1
    assert "config.py" in result.stdout or "config.py" in result.stderr
