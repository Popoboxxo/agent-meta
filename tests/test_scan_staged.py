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


def test_scan_staged_ignores_preexisting_flagged_line(tmp_path):
    """issue #831: a pre-existing flagged line in the index must not block a
    commit that only adds clean lines."""
    _init_repo(tmp_path)
    target = tmp_path / "settings.py"
    target.write_text('api_key = "sk-abcdefghijklmnop1234"\n', encoding="utf-8")
    subprocess.run(["git", "add", "settings.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    # Stage only a clean addition; the flagged line is untouched.
    target.write_text(
        'api_key = "sk-abcdefghijklmnop1234"\nprint("clean")\n', encoding="utf-8",
    )
    subprocess.run(["git", "add", "settings.py"], cwd=tmp_path, check=True)

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--scan-staged"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout


def test_scan_staged_flags_newly_added_secret_line(tmp_path):
    """issue #831: a staged diff that introduces a flagged line fails and the
    output names the file and the new line number."""
    _init_repo(tmp_path)
    target = tmp_path / "settings.py"
    target.write_text('print("clean")\n', encoding="utf-8")
    subprocess.run(["git", "add", "settings.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    target.write_text(
        'print("clean")\napi_key = "sk-abcdefghijklmnop1234"\n', encoding="utf-8",
    )
    subprocess.run(["git", "add", "settings.py"], cwd=tmp_path, check=True)

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--scan-staged"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 1, result.stdout
    assert "settings.py:2:" in result.stdout


def test_scan_staged_multihunk_reports_correct_new_line_number(tmp_path):
    """issue #831: a flagged line in the second hunk must report its real new
    line number (25), not the running counter left over from the first hunk."""
    _init_repo(tmp_path)
    target = tmp_path / "settings.py"
    target.write_text("".join(f"line {i}\n" for i in range(1, 31)), encoding="utf-8")
    subprocess.run(["git", "add", "settings.py"], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-q", "-m", "init"], cwd=tmp_path, check=True)

    lines = [f"line {i}\n" for i in range(1, 31)]
    lines[2] = "line 3 changed\n"  # first hunk (clean)
    lines[24] = 'api_key = "sk-abcdefghijklmnop1234"\n'  # second hunk (secret)
    target.write_text("".join(lines), encoding="utf-8")
    subprocess.run(["git", "add", "settings.py"], cwd=tmp_path, check=True)

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--scan-staged"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 1, result.stdout
    assert "settings.py:25:" in result.stdout


def test_scan_staged_non_utf8_text_file_fails_open(tmp_path):
    """issue #831 regression: a staged text file with non-UTF8 (Latin-1) bytes
    must not crash the scan -- non-UTF8/binary must never block a commit."""
    _init_repo(tmp_path)
    (tmp_path / "latin1.py").write_bytes(b"# caf\xe9\nprint('hi')\n")
    subprocess.run(["git", "add", "latin1.py"], cwd=tmp_path, check=True)

    result = subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "sync.py"), "--scan-staged"],
        cwd=tmp_path, capture_output=True, text=True,
    )
    assert result.returncode == 0, result.stdout
    assert "Traceback" not in result.stderr
