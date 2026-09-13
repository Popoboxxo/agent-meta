"""Regression tests for deterministic LF newlines in synced text files (#754).

Covers:
- ``io.write_atomic()`` must write LF on every platform. In text mode Python
  otherwise translates ``\\n`` to ``os.linesep`` during encoding, so on
  Windows every synced file — deployed hook scripts in particular — would
  land as CRLF and fail at runtime with ``$'\\r': command not found``.
- ``io.is_unchanged()`` must treat a CRLF file as *different* from LF content
  so newline drift is corrected by ``write_checked()`` instead of being
  silently reported as "unchanged" (universal-newline reads made both compare
  equal before the fix).
- No tracked hook script (``hooks/**/*.sh`` source, ``.agents/hooks/**/*.sh``
  self-hosted deployment) may contain a carriage return.
"""

import os
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import env as env_mod  # noqa: E402
from lib import hooks as hooks_mod  # noqa: E402
from lib import io as io_mod  # noqa: E402
from lib.io import is_unchanged, write_atomic, write_checked  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_LF_CONTENT = "#!/bin/bash\necho one\necho two\n"
_CRLF_CONTENT = b"#!/bin/bash\r\necho one\r\necho two\r\n"


# --- write_atomic: deterministic LF text output -----------------------------

def test_write_atomic_writes_lf_only(tmp_path):
    path = tmp_path / "hook.sh"
    write_atomic(path, _LF_CONTENT)
    raw = path.read_bytes()
    assert b"\r" not in raw, f"unexpected CR byte in {raw!r}"
    assert raw == _LF_CONTENT.encode("utf-8")


def test_write_atomic_passes_lf_newline_to_text_mode(tmp_path, monkeypatch):
    """The text branch must pass ``newline="\\n"`` to ``os.fdopen``.

    This is the mechanism that makes the LF guarantee hold on a CRLF platform;
    the spy delegates to the real ``os.fdopen`` so the actual write effect is
    still exercised (no mock hides it).
    """
    seen = {}
    real_fdopen = os.fdopen

    def spy(fd, mode="r", *args, **kwargs):
        seen["mode"] = mode
        seen["kwargs"] = kwargs
        return real_fdopen(fd, mode, *args, **kwargs)

    monkeypatch.setattr(os, "fdopen", spy)
    write_atomic(tmp_path / "hook.sh", _LF_CONTENT)

    assert seen["mode"] == "w"
    assert seen["kwargs"].get("newline") == "\n"


def test_write_atomic_binary_branch_unaffected(tmp_path):
    """Binary mode writes bytes verbatim (no newline knob, CR preserved)."""
    path = tmp_path / "blob.bin"
    write_atomic(path, _CRLF_CONTENT, mode="wb")
    assert path.read_bytes() == _CRLF_CONTENT


# --- is_unchanged: newline-transparent comparison ---------------------------

def test_is_unchanged_false_for_crlf_file(tmp_path):
    path = tmp_path / "hook.sh"
    path.write_bytes(_CRLF_CONTENT)
    assert is_unchanged(path, _LF_CONTENT) is False


def test_is_unchanged_true_for_identical_lf_file(tmp_path):
    path = tmp_path / "hook.sh"
    path.write_bytes(_LF_CONTENT.encode("utf-8"))
    assert is_unchanged(path, _LF_CONTENT) is True


def test_is_unchanged_false_for_missing_file(tmp_path):
    assert is_unchanged(tmp_path / "nope.sh", _LF_CONTENT) is False


def test_write_checked_rewrites_crlf_drift_to_lf(tmp_path):
    """End-to-end: a CRLF target is detected as changed and rewritten as LF."""
    path = tmp_path / "hook.sh"
    path.write_bytes(_CRLF_CONTENT)

    wrote = write_checked(path, _LF_CONTENT, SyncLog(), "hooks/demo.sh")

    assert wrote is True
    assert b"\r" not in path.read_bytes()
    assert path.read_bytes() == _LF_CONTENT.encode("utf-8")


# --- tracked hook scripts must be CR-free -----------------------------------

def _tracked_hook_scripts() -> list[Path]:
    """Hook scripts tracked by git (source + self-hosted deployment).

    Scoped to the git index rather than the working tree, so the assertion is
    about what would actually be committed (an untracked CRLF scratch file must
    not fail it). Robust when git is unavailable: returns [] and the test then
    fails with a clear "no tracked hook script" message.
    """
    try:
        result = subprocess.run(
            ["git", "-C", str(_REPO_ROOT), "ls-files", "-z", "--",
             "hooks", ".agents/hooks"],
            capture_output=True,
            timeout=30,
        )
    except (OSError, subprocess.SubprocessError):
        return []
    if result.returncode != 0:
        return []
    scripts = []
    for rel in result.stdout.decode("utf-8", "surrogateescape").split(chr(0)):
        if rel.endswith(".sh"):
            path = _REPO_ROOT / rel
            if path.is_file():
                scripts.append(path)
    return scripts


def _contains_cr(path: Path) -> bool:
    """True when the file contains a CR byte (0x0D) — no text decoding."""
    return 13 in path.read_bytes()


def test_no_tracked_hook_script_contains_carriage_return():
    scripts = _tracked_hook_scripts()
    assert scripts, "expected at least one tracked hook script to scan"
    offenders = [
        str(p.relative_to(_REPO_ROOT))
        for p in scripts
        if _contains_cr(p)
    ]
    assert offenders == [], f"tracked hook scripts contain CR: {offenders}"


def test_antigravity_adapter_is_lf_everywhere_present():
    candidates = [
        _REPO_ROOT / "hooks" / "1-generic" / "antigravity-json-adapter.sh",
        _REPO_ROOT / ".agents" / "hooks" / "antigravity-json-adapter.sh",
    ]
    found = [p for p in candidates if p.is_file()]
    assert found, "antigravity-json-adapter.sh not found in source or deployment"
    for path in found:
        assert b"\r" not in path.read_bytes(), (
            f"CR byte in {path.relative_to(_REPO_ROOT)}"
        )


# --- caller paths: LF-deterministic writes + no churn on a second run -------


def _demo_env_config() -> dict:
    return {
        "environments": {
            "DEMO_VAR": {
                "description": "demo",
                "default": "value",
                "required": False,
                "secret": False,
            }
        }
    }


def test_generate_env_scripts_writes_lf_and_skips_second_run(tmp_path, monkeypatch):
    """The env-script caller must write LF and not rewrite unchanged files.

    Regression guard for the Windows rewrite loop: when this caller still used
    ``Path.write_text``, text mode translated each newline to ``os.linesep``
    (CRLF on Windows). With ``is_unchanged`` now being CRLF-sensitive, that
    CRLF file no longer matched the LF render, so every sync rewrote it.
    """
    config = _demo_env_config()

    first = env_mod.generate_env_scripts(config, tmp_path)
    assert first[env_mod.SET_SH] == "created"
    assert first[env_mod.SET_PS1] == "created"

    for rel in (env_mod.SET_SH, env_mod.SET_PS1, env_mod.UNSET_SH, env_mod.UNSET_PS1):
        raw = (tmp_path / rel).read_bytes()
        assert 13 not in raw, f"{rel} contains a CR byte: {raw!r}"

    calls = []
    real = io_mod.write_atomic

    def spy(path, content, mode="w"):
        calls.append(Path(path))
        return real(path, content, mode)

    monkeypatch.setattr(io_mod, "write_atomic", spy)

    second = env_mod.generate_env_scripts(config, tmp_path)
    assert second[env_mod.SET_SH] == "skipped"
    assert second[env_mod.SET_PS1] == "skipped"
    assert calls == [], f"unchanged env scripts were rewritten: {calls}"


def test_settings_json_writer_writes_lf_and_skips_second_run(tmp_path, monkeypatch):
    """The settings.json caller must write LF and not rewrite on a second run."""
    entry = {
        "name": "demo-hook",
        "event": "PreToolUse",
        "matcher": "",
        "command": "bash .claude/hooks/demo-hook.sh",
    }
    kwargs = dict(
        project_root=tmp_path,
        previously_managed=set(),
        now_managed={"demo-hook.sh"},
        active_entries=[entry],
        log=SyncLog(),
        dry_run=False,
    )

    hooks_mod._update_settings_hooks(**kwargs)
    settings = tmp_path / ".claude" / "settings.json"
    assert settings.is_file()
    assert 13 not in settings.read_bytes(), "settings.json contains a CR byte"

    calls = []
    real = hooks_mod.write_atomic

    def spy(path, content, mode="w"):
        calls.append(Path(path))
        return real(path, content, mode)

    monkeypatch.setattr(hooks_mod, "write_atomic", spy)

    hooks_mod._update_settings_hooks(**kwargs)
    assert calls == [], f"unchanged settings.json was rewritten: {calls}"
