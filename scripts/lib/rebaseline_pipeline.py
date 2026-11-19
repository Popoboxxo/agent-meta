"""Rebaseline pipeline: preflight and write steps (issue #1237).

Kept separate from the primitives in :mod:`lib.rebaseline` so both modules stay
under the 600-line limit. Every subprocess goes through the injected runner.
"""
from __future__ import annotations

import fnmatch
import json
import re
import subprocess
from pathlib import Path
from typing import Any, List, NamedTuple, Optional, Tuple

from lib import rebaseline as base_mod

# --- Task 5: preflight and write steps ---------------------------------------


class Preflight(NamedTuple):
    """Resolved base ref, optional warning and blocking dirty artifacts."""

    base: str
    warning: str
    dirty: List[str]


class StepResult(NamedTuple):
    """Outcome of one write step (``wrote`` counts changed artifacts)."""

    name: str
    wrote: int
    detail: str
    gate: str


STEP_ORDER: Tuple[str, ...] = (
    "ac01", "standalone", "sync", "topology", "digests", "ceilings"
)


def _git_runner(root: Path, argv: List[str], runner: Any) -> Any:
    return runner(argv, cwd=str(root), capture_output=True, text=True)


def _stdout(result: Any) -> str:
    data = getattr(result, "stdout", "")
    if isinstance(data, bytes):
        return data.decode("utf-8", errors="replace")
    return str(data or "")


def resolve_base(root: Path, options: Any, runner: Any = subprocess.run) -> Tuple[str, str]:
    """Resolve ``--base`` (default ``origin/main``) with a local ``main`` fallback."""
    root = Path(root)
    base = str((options or {}).get("base") or "origin/main")
    result = _git_runner(root, ["git", "rev-parse", "--verify", base], runner)
    if not base_mod._is_failure(result):
        return base, ""
    fallback = "main"
    if base == fallback:
        return base, "base '{}' not reachable".format(base)
    _git_runner(root, ["git", "rev-parse", "--verify", fallback], runner)
    return fallback, "base '{}' not reachable; fell back to '{}'".format(base, fallback)


def _porcelain_paths(root: Path, runner: Any) -> List[str]:
    """Repo-relative paths reported as dirty by ``git status --porcelain``."""
    result = _git_runner(root, ["git", "status", "--porcelain"], runner)
    paths: List[str] = []
    for line in _stdout(result).splitlines():
        if len(line) < 4:
            continue
        raw = line[3:]
        if " -> " in raw:
            raw = raw.split(" -> ", 1)[1]
        paths.append(Path(raw.strip().strip('"')).as_posix())
    return paths


_TREES_ENTRY_RE = re.compile(r'^\s*"[^"]+"\s*:\s*"[^"]*"\s*,?\s*$')


def _surface_dirty_lines(root: Path, runner: Any) -> List[str]:
    """Changed lines of the surface test file outside ``_FIXTURE_TREES`` entries.

    Only digest-literal dictionary entries (``"tree": "digest",``) count as
    allowed line-wise changes; log comment lines and code changes block.
    """
    result = _git_runner(
        root, ["git", "diff", "-U0", "--", "tests/test_opencode_v2_surface.py"], runner
    )
    offenders: List[str] = []
    for line in _stdout(result).splitlines():
        if line.startswith(("+++", "---")):
            continue
        if line.startswith(("+", "-")):
            content = line[1:]
            if not _TREES_ENTRY_RE.match(content):
                offenders.append(content)
    return offenders


def preflight(root: Path, options: Any, runner: Any = subprocess.run) -> Preflight:
    """Check that only source changes and hand-patched goldens are dirty.

    Artifacts in :data:`CLASS_ALLOWLIST` block the run. The AC-T4 surface test
    file is the single exception: it is checked line-wise and only changes
    outside the ``_FIXTURE_TREES`` lines block (decision 3 / AC 10).
    """
    root = Path(root)
    base, warning = resolve_base(root, options, runner)
    dirty: List[str] = []
    for path in _porcelain_paths(root, runner):
        if not any(fnmatch.fnmatch(path, pattern) for pattern in base_mod.CLASS_ALLOWLIST):
            continue
        if path == "tests/test_opencode_v2_surface.py":
            if _surface_dirty_lines(root, runner):
                dirty.append(path)
        else:
            dirty.append(path)
    return Preflight(base, warning, dirty)


def _load_test_module(root: Path, filename: str, alias: str) -> Any:
    """Load a test module by path without going through pytest collection."""
    path = Path(root) / "tests" / filename
    module_spec = importlib.util.spec_from_file_location(alias, path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    return module


def _render_matrix(root: Path, scratch: Optional[Path], runner: Any) -> dict:
    """Render the AC-01 provider matrix into the scratch sink."""
    module = _load_test_module(
        root, "test_ac01_render_identity.py", "_rebaseline_ac01"
    )
    fixture_root = scratch or (Path(root) / "tests" / "fixtures" / "ac01-baseline")
    return module.render_matrix_hashes(Path(fixture_root))


def _render_topology(root: Path, scratch: Optional[Path], runner: Any) -> dict:
    """Render the a2a topology fixtures (``auto`` action, schema paths stay manual)."""
    module = _load_test_module(
        root, "test_ac01_render_identity.py", "_rebaseline_topology"
    )
    prefix = "tests/fixtures/topology-golden/a2a-delegation-gates.role-"
    return {
        "{}active.md".format(prefix): module.render_topology_rule(True, Path(root)),
        "{}inactive.md".format(prefix): module.render_topology_rule(False, Path(root)),
    }


_MANIFEST_REL = "tests/fixtures/ac01-baseline/hashes.json"


def step_ac01(root: Path, options: Any, runner: Any = subprocess.run) -> StepResult:
    """Write only changed hash keys to the AC-01 manifest (indent=1, sorted)."""
    root = Path(root)
    check_only = bool((options or {}).get("check_only"))
    current = base_mod._render_matrix(root, (options or {}).get("scratch"), runner)
    manifest = root / _MANIFEST_REL
    baseline = json.loads(manifest.read_text(encoding="utf-8")) if manifest.is_file() else {}
    changed = {key: value for key, value in current.items() if baseline.get(key) != value}
    if changed and not check_only:
        merged = dict(baseline)
        merged.update(changed)
        manifest.write_text(
            json.dumps(merged, indent=1, sort_keys=True) + "\n", encoding="utf-8"
        )
    return StepResult(
        "ac01",
        len(changed),
        "wrote {} of {} hashes".format(len(changed), len(current)),
        "ok",
    )


def step_standalone(root: Path, options: Any, runner: Any = subprocess.run) -> StepResult:
    """Render standalone artifacts via ``sync.py --render-standalone``."""
    result = base_mod.run_step(
        base_mod.build_sync_cmd(root, "--render-standalone"), root, runner=runner
    )
    failed = base_mod._is_failure(result)
    return StepResult(
        "standalone",
        0 if failed else 1,
        "render-standalone" if not failed else "render-standalone failed",
        "failed" if failed else "ok",
    )


def step_sync(root: Path, options: Any, runner: Any = subprocess.run) -> StepResult:
    """Regenerate generated-file-hashes.json and context-hashes.json via sync."""
    result = base_mod.run_step(base_mod.build_sync_cmd(root), root, runner=runner)
    failed = base_mod._is_failure(result)
    return StepResult(
        "sync", 0 if failed else 1, "sync", "failed" if failed else "ok"
    )


def step_topology(root: Path, options: Any, runner: Any = subprocess.run) -> StepResult:
    """Update only the a2a topology fixtures by rendering them."""
    root = Path(root)
    check_only = bool((options or {}).get("check_only"))
    rendered = base_mod._render_topology(root, (options or {}).get("scratch"), runner)
    changed = 0
    for rel, content in rendered.items():
        target = root / rel
        if target.is_file() and target.read_text(encoding="utf-8") == content:
            continue
        changed += 1
        if not check_only:
            target.parent.mkdir(parents=True, exist_ok=True)
            target.write_text(content, encoding="utf-8")
    return StepResult(
        "topology", changed, "wrote {} a2a fixtures".format(changed), "ok"
    )


def _patch_fixture_trees(root: Path, changes: List[Tuple[str, str, str]]) -> None:
    """Replace only the digest literals of affected ``_FIXTURE_TREES`` lines."""
    path = Path(root) / "tests" / "test_opencode_v2_surface.py"
    lines = path.read_text(encoding="utf-8").splitlines(keepends=True)
    in_block = False
    for index, line in enumerate(lines):
        if line.startswith("_FIXTURE_TREES"):
            in_block = True
            continue
        if in_block and line.startswith("}"):
            in_block = False
        if not in_block:
            continue
        for name, old, new in changes:
            if '"{}"'.format(name) in line:
                lines[index] = line.replace(
                    '"{}"'.format(old), '"{}"'.format(new), 1
                )
    path.write_text("".join(lines), encoding="utf-8")


def step_digests(root: Path, options: Any, runner: Any = subprocess.run) -> StepResult:
    """Re-pin only the changed ``_FIXTURE_TREES`` digest lines."""
    root = Path(root)
    check_only = bool((options or {}).get("check_only"))
    digester, expected = base_mod._load_fixture_digester(root)
    fixtures_root = root / "tests" / "fixtures"
    changes: List[Tuple[str, str, str]] = []
    for name, digest in expected.items():
        fixture = fixtures_root / name
        if not fixture.is_dir():
            continue
        actual = digester(fixture)
        if actual != digest:
            changes.append((name, digest, actual))
    if changes and not check_only:
        _patch_fixture_trees(root, changes)
    detail = (
        "_FIXTURE_TREES: {} patched".format(len(changes))
        if changes else "unchanged"
    )
    return StepResult("digests", len(changes), detail, "ok")


def step_ceilings(root: Path, options: Any, runner: Any = subprocess.run) -> StepResult:
    """Placeholder; the ceiling report block is produced in Task 6."""
    return StepResult("ceilings", 0, "RE-PIN-BLOCK not applied", "ok")


STEP_FUNCS = {
    "ac01": step_ac01,
    "standalone": step_standalone,
    "sync": step_sync,
    "topology": step_topology,
    "digests": step_digests,
    "ceilings": step_ceilings,
}


def run_steps(root: Path, options: Any, runner: Any = subprocess.run) -> List[StepResult]:
    """Run the selected steps in the fixed :data:`STEP_ORDER` order."""
    names = list((options or {}).get("steps") or STEP_ORDER)
    unknown = [name for name in names if name not in STEP_FUNCS]
    if unknown:
        raise base_mod.RebaselineError("unknown step: {}".format(", ".join(unknown)))
    return [STEP_FUNCS[name](root, options, runner) for name in names]
