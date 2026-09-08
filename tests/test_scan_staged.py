"""sync.py --scan-staged (issue #694): exposes the existing
scan_for_secrets() to agents as a pre-commit check, without requiring a
Python import inside a Bash instruction block."""

import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib import cli_commands  # noqa: E402

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


def test_scan_reads_staged_content_not_working_tree(tmp_path):
    # Secret staged, then scrubbed in the working tree WITHOUT re-adding:
    # the commit would still contain the secret, so the scan must fail.
    _init_repo(tmp_path)
    target = tmp_path / "config.py"
    target.write_text('AWS_SECRET_ACCESS_KEY = "AKIAABCDEFGHIJKLMNOP"\n', encoding="utf-8")
    subprocess.run(["git", "add", "config.py"], cwd=tmp_path, check=True)
    target.write_text("# scrubbed\n", encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--scan-staged"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 1, result.stdout
    assert "config.py" in result.stdout


def test_scan_ignores_unstaged_working_tree_secret(tmp_path):
    # Mirror image: clean content staged, secret only in the working tree.
    # Nothing secret is about to be committed, so the scan must pass.
    _init_repo(tmp_path)
    target = tmp_path / "config.py"
    target.write_text("# clean\n", encoding="utf-8")
    subprocess.run(["git", "add", "config.py"], cwd=tmp_path, check=True)
    target.write_text('AWS_SECRET_ACCESS_KEY = "AKIAABCDEFGHIJKLMNOP"\n', encoding="utf-8")

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--scan-staged"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout


def test_scan_outside_git_repo_skips_instead_of_crashing(monkeypatch):
    def _boom(*args, **kwargs):
        raise subprocess.CalledProcessError(128, args[0] if args else "git")

    monkeypatch.setattr(cli_commands.subprocess, "run", _boom)
    assert cli_commands.handle_scan_staged() == 0


def test_scan_without_git_binary_skips_instead_of_crashing(monkeypatch):
    def _boom(*args, **kwargs):
        raise FileNotFoundError("git")

    monkeypatch.setattr(cli_commands.subprocess, "run", _boom)
    assert cli_commands.handle_scan_staged() == 0
