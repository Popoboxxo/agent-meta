"""IC-15 Nr. 25 / Task 1.44 (AC-85): ``--deactivation-status`` is read-only.

The mode reports provider deactivation status, but it used to fall through to
the common sync tail, which wrote the four ``.meta-config/env.*`` scripts and
``sync.log`` into the project. ``sync.log`` is an input of the doctor
(``finding-ref`` source ``sync-log``), so the command corrupted the very file a
measurement reads -- the reason AC-85 keeps it out of the doctor ``command``
allowlist (IC-21) and the ``meta-doctor`` Bash allowlist (IC-23) until this fix.

Mirrors the ``--cleanup-preview`` precedent (``scripts/sync.py``,
``_STDOUT_CLEAN_MODES``): the mode forces ``--dry-run`` and redirects
``_build_context``'s stdout to stderr *before* the context is built, and the
handler sets ``ctx.read_only = True`` so ``_run_common_tail`` is skipped.

Red: the self-hosting snapshot shows a changed ``sync.log``/env scripts.
Green: before == after; the handler sets ``read_only``.

Run: python -m pytest tests/test_deactivation_status_read_only.py -q
"""
from __future__ import annotations

import hashlib
import os
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import sync
from lib import cli_commands
from lib.log import SyncLog

_ENV_FILES = ("env.sh", "env.ps1", "env.unset.sh", "env.unset.ps1")

# Same source set the doctor self-hosting snapshot copies (AC-39).
_AGENT_META_PARTS = (
    "agents", "commands", "config", "hooks", "rules", "schemas", "scripts",
    "snippets", "speech", "templates", "platform-configs", "VERSION",
)

_MINIMAL_PROJECT_YAML = (
    "ai-providers: [Claude]\n"
    "dod-preset: rapid-prototyping\n"
    "roles: [developer]\n"
    "project: {name: deactivation-status-ro, prefix: ds, short: ds-ro}\n"
    "variables: {PROJECT_NAME: deactivation-status-ro}\n"
)


def _copy_agent_meta(dst: Path) -> Path:
    """Copy the agent-meta sources into *dst* (mirrors test_doctor_cli.py)."""
    dst.mkdir(parents=True, exist_ok=True)
    ignore = shutil.ignore_patterns("__pycache__", "*.pyc")
    for part in _AGENT_META_PARTS:
        src = _REPO_ROOT / part
        if src.is_dir():
            shutil.copytree(src, dst / part, ignore=ignore)
        else:
            shutil.copy2(src, dst / part)
    return dst


def _write_minimal_project(root: Path) -> Path:
    meta = root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    config = meta / "project.yaml"
    config.write_text(_MINIMAL_PROJECT_YAML, encoding="utf-8")
    return config


def _snapshot(root: Path) -> dict:
    """SHA-256 of every tracked file below *root* (bytecode excluded)."""
    result = {}
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        if "__pycache__" in path.parts or path.suffix == ".pyc":
            continue
        result[str(path.relative_to(root))] = hashlib.sha256(path.read_bytes()).hexdigest()
    return result


def test_handler_sets_read_only(tmp_path, monkeypatch):
    """AC-85: the ``--deactivation-status`` handler sets ``ctx.read_only = True``.

    Runs ``_build_context`` in-process with cwd *outside* the agent-meta root so
    the self-hosting schema-enum update is skipped (``cli_commands.py``) and does
    not touch the real repository.
    """
    project = tmp_path / "project"
    config = _write_minimal_project(project)
    monkeypatch.chdir(project)

    args = sync._build_arg_parser().parse_args(
        ["--config", str(config), "--deactivation-status"])
    ctx = cli_commands._build_context(args, _REPO_ROOT, SyncLog())
    assert ctx is not None

    sync._handle_deactivation_status(ctx)

    assert ctx.read_only is True
    assert ctx.mode == "deactivation-status"
    assert not (project / "sync.log").exists()


def test_deactivation_status_writes_nothing_self_hosting(tmp_path):
    """AC-85: self-hosting snapshot is byte-identical before/after the run."""
    meta = _copy_agent_meta(tmp_path / "self-hosting")
    _write_minimal_project(meta)
    before = _snapshot(meta)

    env = dict(os.environ)
    env["PYTHONDONTWRITEBYTECODE"] = "1"
    result = subprocess.run(
        [sys.executable, str(meta / "scripts" / "sync.py"),
         "--config", str(meta / ".meta-config" / "project.yaml"),
         "--deactivation-status"],
        capture_output=True, text=True, cwd=str(meta), env=env, timeout=300,
    )

    assert result.returncode == 0, result.stderr
    assert '"providers"' in result.stdout, result.stdout
    assert "Traceback" not in result.stderr, result.stderr

    assert _snapshot(meta) == before, "read-only mode modified rendered artifacts"
    assert not (meta / "sync.log").exists(), "unexpected sync.log written"
    env_dir = meta / ".meta-config"
    for name in _ENV_FILES:
        assert not (env_dir / name).exists(), f"unexpected env file: {name}"
