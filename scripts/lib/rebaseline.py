"""Rebaseline helper internals: root resolution, subprocess runner, snapshots,
diff gate and pin registry (issue #1237).

This module is pure logic for ``scripts/rebaseline.py``. It performs no
console output and no provider-specific dispatch; results are returned to the
entrypoint. Python 3.9 compatible, standard library only.
"""
from __future__ import annotations

import fnmatch
import glob as glob_module
import importlib.util
import json
import re
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


class PinSpec(NamedTuple):
    """One rebaseline target: artifacts, detectors and the write action."""

    klass: str
    paths: Tuple[str, ...]
    detector: Tuple[str, ...]
    action: str


#: Pin registry as data (spec C5). A new pin class is one more entry here, not
#: another branch in the pipeline. Topology has two entries: a2a fixtures are
#: regenerated by the helper, the schema path list stays human-patched.
PINS: Tuple[PinSpec, ...] = (
    PinSpec(
        "AC",
        ("tests/fixtures/ac01-baseline/hashes.json",),
        ("tests/test_ac01_render_identity.py",),
        "auto",
    ),
    PinSpec(
        "AC-T4",
        ("tests/test_opencode_v2_surface.py",),
        ("tests/test_opencode_v2_surface.py::test_ac_t4_fixtures_unchanged",),
        "auto",
    ),
    PinSpec(
        "SG",
        ("tests/fixtures/slimming-golden/",),
        ("tests/test_template_slimming_equivalence.py",),
        "report-only",
    ),
    PinSpec(
        "CG",
        (
            "tests/fixtures/compact-golden/",
            "tests/fixtures/compact-golden/agents-managed.md",
        ),
        (
            "tests/test_gate_card_compact.py",
            "tests/test_orchestrator_compact_sections.py",
        ),
        "report-only",
    ),
    PinSpec(
        "TG",
        ("tests/fixtures/topology-golden/a2a-delegation-gates.role-*.md",),
        ("tests/test_orchestrator_topology_docs.py",),
        "auto",
    ),
    PinSpec(
        "TG",
        ("tests/fixtures/topology-golden/schema-property-paths.json",),
        ("tests/test_orchestrator_topology_docs.py",),
        "report-only",
    ),
    PinSpec(
        "H1",
        (".meta-config/generated-file-hashes.json",),
        ("sync:--dry-run",),
        "auto",
    ),
    PinSpec(
        "H2",
        (".meta-config/context-hashes.json",),
        ("sync:--dry-run",),
        "auto",
    ),
    PinSpec(
        "SA",
        ("standalone/",),
        ("sync:--render-standalone:--check",),
        "auto",
    ),
    PinSpec(
        "CE",
        ("tests/test_context_budgets.py",),
        ("tests/test_context_budgets.py",),
        "report-only",
    ),
)


class PinStatus(NamedTuple):
    """Impact of one pin on the current working tree."""

    klass: str
    artifact: str
    status: str
    action: str


def _load_fixture_digester(root: Path) -> Tuple[Any, Any]:
    """Load the AC-T4 digest helpers from the existing test module."""
    module_path = Path(root) / "tests" / "test_opencode_v2_surface.py"
    spec = importlib.util.spec_from_file_location(
        "_rebaseline_ac_t4_surface", module_path
    )
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module._fixture_tree_sha256, module._FIXTURE_TREES


def _ac_t4_status(root: Path) -> str:
    """Compare fixture-tree digests in-process (no subprocess)."""
    if not (root / "tests" / "test_opencode_v2_surface.py").is_file():
        return "n/a"
    try:
        digester, expected = _load_fixture_digester(root)
    except Exception:
        return "n/a"
    fixtures_root = root / "tests" / "fixtures"
    checked = 0
    for name, digest in expected.items():
        fixture = fixtures_root / name
        if not fixture.is_dir():
            continue
        checked += 1
        if digester(fixture) != digest:
            return "betroffen"
    return "ok" if checked else "n/a"


def _is_failure(result: Any) -> bool:
    """Treat a runner result with a non-zero return code as a red detector."""
    code = getattr(result, "returncode", result)
    try:
        return int(code) != 0
    except (TypeError, ValueError):
        return False


def _detector_cmd(root: Path, detector: str) -> List[str]:
    """Build the runner argv for a detector descriptor."""
    if detector.startswith("sync:"):
        return build_sync_cmd(root, *detector.split(":")[1:])
    return [sys.executable, "-m", "pytest", "-q", detector]


def _path_present(root: Path, spec: str) -> bool:
    """Check existence of a pin path, honouring glob specs."""
    if any(char in spec for char in _GLOB_MAGIC):
        return bool(glob_module.glob(str(root / spec), recursive=True))
    return (root / spec).exists()


def impact_report(root: Path, runner: Any = subprocess.run) -> List[PinStatus]:
    """Report ``ok`` / ``betroffen`` / ``n/a`` per registered pin."""
    root = Path(root)
    statuses: List[PinStatus] = []
    for pin in PINS:
        if pin.klass == "AC-T4":
            status = _ac_t4_status(root)
        elif not any(_path_present(root, path) for path in pin.paths):
            status = "n/a"
        else:
            failed = False
            for detector in pin.detector:
                result = runner(_detector_cmd(root, detector), cwd=str(root))
                if _is_failure(result):
                    failed = True
            status = "betroffen" if failed else "ok"
        statuses.append(
            PinStatus(pin.klass, ", ".join(pin.paths), status, pin.action)
        )
    return statuses




def _render_matrix(root: Path, scratch: Optional[Path], runner: Any) -> dict:
    """Delegate to the pipeline implementation (lazy, avoids import cycles)."""
    from lib import rebaseline_pipeline as pipeline

    return pipeline._render_matrix(root, scratch, runner)


def _render_topology(root: Path, scratch: Optional[Path], runner: Any) -> dict:
    """Delegate to the pipeline implementation (lazy, avoids import cycles)."""
    from lib import rebaseline_pipeline as pipeline

    return pipeline._render_topology(root, scratch, runner)


_PIPELINE_EXPORTS = frozenset(
    {
        "Preflight", "StepResult", "STEP_ORDER", "resolve_base", "preflight",
        "step_ac01", "step_standalone", "step_sync", "step_topology",
        "step_digests", "step_ceilings", "STEP_FUNCS", "run_steps",
        "EXIT_OK", "EXIT_DRIFT", "EXIT_USAGE", "EXIT_GATE",
        "EXIT_SUBPROCESS", "EXIT_VERIFY", "EXIT_RESIDUAL",
        "ceiling_repin_block", "append_log", "build_json_report",
        "PipelineResult", "run_pipeline", "verify",
    }
)


def __getattr__(name: str) -> Any:
    """Expose pipeline symbols through this module without an eager import."""
    if name in _PIPELINE_EXPORTS:
        from lib import rebaseline_pipeline as pipeline

        return getattr(pipeline, name)
    raise AttributeError("module '{}' has no attribute '{}'".format(__name__, name))
