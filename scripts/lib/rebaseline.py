"""Rebaseline helper internals: root resolution, subprocess runner, snapshots,
diff gate and pin registry (issue #1237).

This module is pure logic for ``scripts/rebaseline.py``. It contains no
``print()`` and no provider-specific dispatch; results are returned to the
entrypoint. Python 3.9 compatible, standard library only.
"""
from __future__ import annotations

import fnmatch
import importlib.util
import subprocess
import sys
from pathlib import Path
from typing import Any, Iterable, List, NamedTuple, Optional, Set, Tuple

CONFIG_REL = Path(".meta-config") / "project.yaml"
SYNC_REL = Path("scripts") / "sync.py"


class RebaselineError(Exception):
    """Raised on invocation/preflight errors that map to CLI exit code 2."""


def resolve_root(script_file: Path, override: Optional[Path] = None) -> Path:
    """Return the repository root, derived from the helper's own location.

    ``cwd`` is deliberately never consulted: a helper invoked from a foreign
    working tree must still operate on the checkout it lives in.  An explicit
    ``override`` (CLI ``--root``) wins, used by tests for isolated fixtures.
    """
    if override is not None:
        return Path(override).resolve()
    return Path(script_file).resolve().parents[1]


def _config_path(root: Path) -> Path:
    return Path(root) / CONFIG_REL


def build_sync_cmd(root: Path, *extra: object) -> List[str]:
    """Build the argument vector for a ``sync.py`` subprocess.

    Every call carries an explicit ``--config`` so config auto-detection via
    ``cwd`` (and its setup wizard) can never fire in the helper's worktree.
    """
    parts: List[str] = [
        sys.executable,
        str(Path(root) / SYNC_REL),
        "--config",
        str(_config_path(root)),
    ]
    parts.extend(str(part) for part in extra)
    return parts


def run_step(cmd: Iterable[object], root: Path, runner: Any = subprocess.run) -> Any:
    """Run *cmd* with the helper's interpreter and ``cwd=root``.

    Missing project config is an invocation error (``RebaselineError``), never
    a trigger for the interactive setup wizard.
    """
    root = Path(root)
    if not _config_path(root).is_file():
        raise RebaselineError(
            "missing project config: {}".format(_config_path(root))
        )
    argv = [str(part) for part in cmd]
    if not argv or argv[0] != sys.executable:
        argv.insert(0, sys.executable)
    return runner(argv, cwd=str(root))
