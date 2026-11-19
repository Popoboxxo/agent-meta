"""Rebaseline helper internals: root resolution, subprocess runner, snapshots,
diff gate and pin registry (issue #1237).

This module is pure logic for ``scripts/rebaseline.py``. It contains no
``print()`` and no provider-specific dispatch; results are returned to the
entrypoint. Python 3.9 compatible, standard library only.
"""
from __future__ import annotations

import fnmatch
import glob as glob_module
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


_GLOB_MAGIC = frozenset("*?[")


def _normalize_rel(root: Path, spec: object) -> Optional[str]:
    """Return a POSIX repo-relative path for *spec*, or None if outside root."""
    path = Path(str(spec))
    if path.is_absolute():
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return None
    return path.as_posix()


class Snapshot:
    """Byte-exact snapshot of a set of repo-relative paths for rollback.

    Only files under the requested paths are captured or touched: files that
    existed at :meth:`take` are restored byte-for-byte (and recreated if
    deleted afterwards), while files created afterwards under the same paths
    are removed.  Pure filesystem I/O -- no git writes.
    """

    def __init__(self) -> None:
        self._root = Path(".")
        self._specs: List[Tuple[str, bool]] = []
        self._saved: dict = {}

    @classmethod
    def take(cls, root: Path, paths: Iterable[object]) -> "Snapshot":
        snap = cls()
        snap._root = Path(root)
        raw = [paths] if isinstance(paths, (str, Path)) else list(paths)
        for spec in raw:
            rel = _normalize_rel(snap._root, spec)
            if rel is None:
                continue
            magic = any(char in rel for char in _GLOB_MAGIC)
            snap._specs.append((rel, magic))
            for found in snap._matches(rel, magic):
                snap._saved[found] = (snap._root / found).read_bytes()
        return snap

    def _matches(self, rel: str, magic: bool) -> List[str]:
        """Current files matching a path spec, as POSIX relative paths."""
        if magic:
            pattern = str(self._root / rel)
            candidates = glob_module.glob(pattern, recursive=True)
            result = []
            for candidate in candidates:
                path = Path(candidate)
                if not path.is_file():
                    continue
                normalized = _normalize_rel(self._root, path)
                if normalized is not None:
                    result.append(normalized)
            return sorted(set(result))
        return [rel] if (self._root / rel).is_file() else []

    def restore(self) -> None:
        """Undo every change under the snapshotted paths."""
        # 1. Remove files that appeared after ``take`` (not part of the baseline).
        for rel, magic in self._specs:
            for current in self._matches(rel, magic):
                if current not in self._saved:
                    (self._root / current).unlink()
        # 2. Restore baseline bytes (also recreates deleted files).
        for rel, data in self._saved.items():
            target = self._root / rel
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_bytes(data)


#: Repo-relative path globs whose changes the gate tolerates (spec "Diff-Gate",
#: section 1). This is also the definition of "rebaseline artifacts" used by
#: preflight; hand-patched goldens and ceiling tables are deliberately absent.
CLASS_ALLOWLIST: Tuple[str, ...] = (
    "tests/fixtures/ac01-baseline/hashes.json",
    ".meta-config/generated-file-hashes.json",
    ".meta-config/context-hashes.json",
    "standalone/**",
    "tests/test_opencode_v2_surface.py",
    "tests/fixtures/topology-golden/a2a-delegation-gates.role-*.md",
    ".meta-config/rebaseline-log.jsonl",
    # Sync side effects (derived expectation; spec section Diff-Gate 1).
    "CLAUDE.md",
    "AGENTS.md",
)

_STEM_SOURCE_PREFIXES = ("agents/", "rules/", "hooks/", "templates/")


def derive_expected_stems(changed_sources: Iterable[object]) -> Set[str]:
    """Map changed source paths to role/rule/hook stems.

    Sources without a stem mapping (``config/**``, ``scripts/lib/**``) produce
    nothing: the caller must pass an explicit ``--expect-key`` for them, so an
    unanticipated hash key cannot slip through the gate (fail-closed).
    """
    stems: Set[str] = set()
    for source in changed_sources:
        rel = Path(str(source)).as_posix()
        if any(rel.startswith(prefix) for prefix in _STEM_SOURCE_PREFIXES):
            stem = Path(rel).stem
            if stem:
                stems.add(stem)
    return stems


def check_gate(
    changed_files: Iterable[object],
    changed_keys: Iterable[object],
    expect: Iterable[object],
    expect_key: Iterable[object],
    stems: Iterable[str],
) -> List[str]:
    """Return gate violations; an empty list means the diff is allowed.

    File paths are matched against the class allowlist plus explicit
    ``--expect`` globs. Hash keys are matched against explicit ``--expect-key``
    globs plus the derived stems (``**/<stem>*``); with no stem and no glob a
    key is always a violation.
    """
    violations: List[str] = []
    file_globs = list(CLASS_ALLOWLIST) + [str(g) for g in (expect or [])]
    key_globs = [str(g) for g in (expect_key or [])]
    expected_stems = set(stems)

    for changed in changed_files:
        rel = Path(str(changed)).as_posix()
        if not any(fnmatch.fnmatch(rel, pattern) for pattern in file_globs):
            violations.append("unexpected file: {}".format(rel))

    for raw_key in changed_keys:
        key = str(raw_key)
        allowed = any(fnmatch.fnmatch(key, pattern) for pattern in key_globs)
        if not allowed:
            for stem in expected_stems:
                if fnmatch.fnmatch(key, "*/{}*".format(stem)):
                    allowed = True
                    break
        if not allowed:
            violations.append("unexpected key: {}".format(key))
    return violations
