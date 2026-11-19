"""Rebaseline pipeline: preflight and write steps (issue #1237).

Kept separate from the primitives in :mod:`lib.rebaseline` so both modules stay
under the 600-line limit. Every subprocess goes through the injected runner.
"""
from __future__ import annotations

import fnmatch
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, List, NamedTuple, Optional, Tuple

from lib import rebaseline as base_mod

# --- Task 5: preflight and write steps ---------------------------------------


class Preflight(NamedTuple):
    """Resolved base ref, optional warning and blocking dirty artifacts."""

    base: str
    warning: str
    dirty: List[str]
    baseline: Tuple[str, ...] = ()


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
    paths = _porcelain_paths(root, runner)
    for path in paths:
        if not any(fnmatch.fnmatch(path, pattern) for pattern in base_mod.CLASS_ALLOWLIST):
            continue
        if path == "tests/test_opencode_v2_surface.py":
            if _surface_dirty_lines(root, runner):
                dirty.append(path)
        else:
            dirty.append(path)
    return Preflight(base, warning, dirty, tuple(paths))


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


EXIT_OK = 0
EXIT_DRIFT = 1
EXIT_USAGE = 2
EXIT_GATE = 3
EXIT_SUBPROCESS = 4
EXIT_VERIFY = 5
EXIT_RESIDUAL = 6

_TOLERANCE_MIN_BYTES = 256
_TOLERANCE_RATIO = 0.02
_TOLERANCE_MAX_BYTES = 4096


def _pin_value(pins: Any, provider: str, artifact: str) -> Any:
    """Look up an Ist pin in a nested, flat or tuple-keyed pin mapping."""
    if not pins:
        return None
    if (provider, artifact) in pins:
        return pins[(provider, artifact)]
    provider_map = pins.get(provider)
    if isinstance(provider_map, dict):
        return provider_map.get(artifact)
    return pins.get("{}/{}".format(provider, artifact))


def ceiling_repin_block(report: Any, ist_full: Any, ist_compact: Any) -> str:
    """Render the ready-to-apply ceiling re-pin block (output only).

    Artifacts whose measured value stays within the documented tolerance are
    skipped. No file is written, so tolerance constants and ceiling tables stay
    byte-identical (issue #1115: verification remains a human step).
    """
    lines: List[str] = []
    for provider, artifacts in dict(report or {}).items():
        for artifact, stat in dict(artifacts or {}).items():
            measured = stat.get("bytes") if isinstance(stat, dict) else stat
            old = _pin_value(ist_full, provider, artifact)
            base = "full"
            if old is None:
                old = _pin_value(ist_compact, provider, artifact)
                base = "compact"
            if old is None or measured is None:
                continue
            tolerance = min(
                max(_TOLERANCE_MIN_BYTES, int(_TOLERANCE_RATIO * int(old))),
                _TOLERANCE_MAX_BYTES,
            )
            if abs(int(measured) - int(old)) <= tolerance:
                continue
            lines.append(
                "CE {} {} {} old={} new={}".format(
                    base, provider, artifact, old, measured
                )
            )
    return "\n".join(lines)


def step_ceilings(root: Path, options: Any, runner: Any = subprocess.run) -> StepResult:
    """Print the ceiling re-pin block without applying it."""
    options = options or {}
    block = ceiling_repin_block(
        options.get("ceiling_report") or {},
        options.get("ist_full") or {},
        options.get("ist_compact") or {},
    )
    return StepResult(
        "ceilings", 0, block or "RE-PIN-BLOCK not applied", "ok"
    )


def append_log(root: Path, entry: Any) -> Optional[Path]:
    """Append one JSON line to the rebaseline log, only when files changed."""
    entry = dict(entry or {})
    if not entry.get("changed_files"):
        return None
    path = Path(root) / ".meta-config" / "rebaseline-log.jsonl"
    line = {
        "ts": entry.get("ts") or datetime.now(timezone.utc).isoformat(),
        "reason": entry.get("reason", ""),
        "base": entry.get("base", ""),
        "head": entry.get("head", ""),
        "steps": list(entry.get("steps") or []),
        "changed_files": list(entry.get("changed_files") or []),
        "changed_keys": list(entry.get("changed_keys") or []),
        "gate": entry.get("gate", "ok"),
        "verify": entry.get("verify", "skipped"),
        "idempotency": entry.get("idempotency", "ok"),
    }
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(line, sort_keys=True) + "\n")
    return path


def build_json_report(pre: Any, steps: Any, post: Any, result: Any) -> dict:
    """Machine-readable report with the four fields required by AC 14."""
    return {
        "pre": list(pre or []),
        "steps": list(steps or []),
        "post": list(post or []),
        "result": dict(result or {}),
    }


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


# --- Task 7: pipeline, verify and idempotency --------------------------------

Snapshot = base_mod.Snapshot
_HASH_FILES = (
    "tests/fixtures/ac01-baseline/hashes.json", ".meta-config/generated-file-hashes.json",
    ".meta-config/context-hashes.json",
)


class PipelineResult(NamedTuple):
    """Complete outcome of one rebaseline run."""
    exit_code: int = EXIT_OK
    pre: List[Any] = []
    steps: List[StepResult] = []
    post: List[Any] = []
    residual: List[str] = []
    changed_files: List[str] = []
    changed_keys: List[str] = []
    gate: str = "ok"
    verify: str = "skipped"
    idempotency: str = "ok"
    log: Optional[str] = None
    warnings: List[str] = []


def _scratch_dir(root: Path, options: Any) -> Path:
    """Provision the scratch directory inside the repository tmp sink."""
    from lib.tmp_paths import resolve_tmp_paths
    paths = resolve_tmp_paths(Path(root), (options or {}).get("config"))
    if not paths.enabled or paths.absolute is None:
        raise base_mod.RebaselineError(
            "tmp sink disabled: the rebaseline helper requires an enabled .tmp sink"
        )
    scratch = Path(paths.absolute) / "rebaseline"
    scratch.mkdir(parents=True, exist_ok=True)
    return scratch


def _json_state(root: Path) -> dict:
    """Read the three JSON hash files as a ``{rel: {key: value}}`` mapping."""
    state = {}
    for rel in _HASH_FILES:
        path = Path(root) / rel
        if not path.is_file():
            continue
        try:
            value = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):  # malformed file is treated as empty
            value = {}
        state[rel] = value if isinstance(value, dict) else {}
    return state


def _changed_files(root: Path, pf: Preflight, runner: Any) -> List[str]:
    """Files changed by this run, as a difference to the preflight baseline."""
    baseline = set(pf.baseline)
    return sorted(set(_porcelain_paths(root, runner)) - baseline)


def _changed_keys(root: Path, files: Any, before: Any) -> List[str]:
    """Hash keys added, removed or re-valued by this run."""
    after = _json_state(root)
    changed = set()
    for rel in set(files or ()) & set(_HASH_FILES):
        old = dict(before.get(rel) or {})
        new = dict(after.get(rel) or {})
        for key in set(old) | set(new):
            if old.get(key) != new.get(key):
                changed.add(key)
    return sorted(changed)


def _changed_sources(root: Path, pf: Preflight, runner: Any) -> List[str]:
    """Sources changed against ``--base`` (used to derive allowed key stems)."""
    result = _git_runner(
        root,
        ["git", "diff", "--name-only", "{}...HEAD".format(pf.base)],
        runner,
    )
    return [Path(line).as_posix() for line in _stdout(result).splitlines() if line]


def verify(root: Path, runner: Any = subprocess.run) -> List[PinStatus]:
    """Run the targeted pin detectors from the registry."""
    return base_mod.impact_report(root, runner)


def run_pipeline(root: Path, options: Any, runner: Any = subprocess.run) -> PipelineResult:
    """Preflight, write, re-check, verify and log in the specified order.

    Exit codes follow spec C3: 2 usage/preflight, 3 gate, 4 subprocess, 5 red
    verification, 6 residual drift; priority 5 over 6.
    """
    root = Path(root)
    options = dict(options or {})
    check_only = bool(options.get("check_only"))
    warnings: List[str] = list(options.get("warnings") or [])

    if not (root / base_mod.CONFIG_REL).is_file():
        return PipelineResult(EXIT_USAGE, warnings=["missing project config"])
    try:
        options["scratch"] = _scratch_dir(root, options)
    except Exception as exc:  # sink disabled/invalid (OF-6: exit 2)
        return PipelineResult(EXIT_USAGE, warnings=[str(exc)])

    try:
        pf = base_mod.preflight(root, options, runner)
    except base_mod.RebaselineError as exc:
        return PipelineResult(EXIT_USAGE, warnings=[str(exc)])
    if pf.warning:
        warnings.append(pf.warning)
    if pf.dirty:
        return PipelineResult(
            EXIT_USAGE, warnings=warnings + ["dirty artifacts: " + ", ".join(pf.dirty)])

    pre = base_mod.impact_report(root, runner)
    key_before = _json_state(root)
    snap = Snapshot.take(root, base_mod.CLASS_ALLOWLIST)

    try:
        steps = base_mod.run_steps(root, options, runner)
    except base_mod.RebaselineError as exc:
        snap.restore()
        return PipelineResult(EXIT_USAGE, warnings=warnings + [str(exc)])

    if any(step.gate == "failed" for step in steps):
        snap.restore()
        return PipelineResult(
            EXIT_SUBPROCESS, pre=list(pre), steps=list(steps), warnings=warnings)

    changed_files = _changed_files(root, pf, runner)
    changed_keys = _changed_keys(root, changed_files, key_before)
    stems = base_mod.derive_expected_stems(_changed_sources(root, pf, runner))
    gate_violations = base_mod.check_gate(
        changed_files, changed_keys, options.get("expect") or (),
        options.get("expect_key") or (), stems)
    if gate_violations:
        snap.restore()
        return PipelineResult(
            EXIT_GATE,
            pre=list(pre),
            steps=list(steps),
            changed_files=changed_files,
            changed_keys=changed_keys,
            gate="failed",
            warnings=warnings + gate_violations,
        )

    check_options = dict(options, check_only=True)
    second = base_mod.run_steps(root, check_options, runner)
    residual = [
        "{}: {}".format(step.name, step.detail)
        for step in second if step.wrote
    ]
    idempotency = "drift" if residual else "ok"

    if options.get("skip_verify"):
        post: List[PinStatus] = list(pre)
        verify_state = "skipped"
    else:
        post = verify(root, runner)
        verify_state = (
            "failed"
            if any(status.status == "betroffen" for status in post)
            else "ok"
        )

    log_path = None
    if not check_only and changed_files:
        log_path = append_log(
            root,
            {
                "reason": options.get("reason", ""),
                "base": pf.base,
                "head": options.get("head", ""),
                "steps": [step.name for step in steps],
                "changed_files": changed_files,
                "changed_keys": changed_keys,
                "gate": "ok",
                "verify": verify_state,
                "idempotency": "failed" if idempotency == "drift" else "ok",
            },
        )

    if verify_state == "failed":
        exit_code = EXIT_VERIFY
    elif idempotency == "drift":
        exit_code = EXIT_RESIDUAL
    elif check_only and any(step.wrote for step in steps + second):
        exit_code = EXIT_DRIFT
    else:
        exit_code = EXIT_OK

    return PipelineResult(
        exit_code,
        pre=list(pre),
        steps=list(steps),
        post=list(post),
        residual=residual,
        changed_files=changed_files,
        changed_keys=changed_keys,
        gate="ok",
        verify=verify_state,
        idempotency=idempotency,
        log=str(log_path) if log_path is not None else None,
        warnings=warnings,
    )
