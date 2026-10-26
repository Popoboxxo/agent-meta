"""Central tmp-sink path resolver — the single source of truth (ADR-01, IC-01).

Everything that needs a tmp-sink path form asks this module instead of
interpreting ``repo_containment.tmp-sink`` on its own:

* ``relative``  — the validated project-relative form for templates/agents
                  (move-safe, ADR-02).
* ``absolute``  — the realpath-resolved directory for env, backup, diagnostics.
* ``pytest_basetemp`` — the finished argv value for ``--basetemp`` (IC-04).
* ``env``       — ``TMPDIR``/``TEMP``/``TMP`` pinned to ``absolute`` (IC-06).

Error policy (ADR-07): a *disabled* sink is a valid configuration and never
raises — the consuming write APIs (``resolve_output_dir``,
``resolve_work_dir``, ``resolve_out_path``, ``tmp_env``,
``tmp_sink_env_pin_block``) raise ``tmp-sink.disabled`` instead. Configuration
errors keep failing loudly, even while the sink is disabled, so enabling it
later never surfaces a dormant misconfiguration (IC-03).

Like :mod:`lib.repo_containment`, this module is a library: it never calls
``sys.exit`` and never writes to stderr. The sync validator maps
:class:`lib.repo_containment.TmpSinkError` to a hard ``_fail`` (Exit 1).
"""
from __future__ import annotations

import getpass
import os
import shlex
import tempfile
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Optional

from . import repo_containment as rc

#: Environment keys pinned to the absolute sink (IC-06/ADR-12).
TMP_ENV_KEYS = ("TMPDIR", "TEMP", "TMP")

#: Toolchain caches pinned below ``<sink>/cache`` when opted in (Q3/ADR-13).
#: Data-driven (env key, subdirectory) pairs: no provider names, no docker.
TOOLCHAIN_CACHE_ENV_KEYS = (
    ("PIP_CACHE_DIR", "pip"),
    ("npm_config_cache", "npm"),
)

#: Framework default reason for the system-temp exception (Q1: enabled, ADR-03).
#: Projects without the key inherit this text; it keeps the justification in
#: the config instead of losing it from the rulebook.
DEFAULT_SYSTEM_TEMP_EXCEPTION_REASON = (
    "pytest basetemp must stay outside the repo "
    "(ancestor-collision, 13 failures 2026-09-20)"
)

_PYTEST_BASETEMP_DIRNAME = "pytest-agent-meta"
_PYTEST_SINK_SUBDIR = "pytest"


@dataclass(frozen=True)
class SystemTempException:
    """The one sanctioned system-temp exception: pytest's ``--basetemp``.

    ``toolchain_cache`` reads the YAML key ``toolchain-caches`` (plural,
    kebab-case; Q3/ADR-13) and is a pure data field — the resolver only
    rejects the contradictory combination with ``enabled: false``.
    """

    enabled: bool = True
    reason: str = DEFAULT_SYSTEM_TEMP_EXCEPTION_REASON
    pytest_basetemp: bool = True
    toolchain_cache: bool = False


@dataclass(frozen=True)
class TmpPaths:
    """Resolved tmp-sink paths in every form consumers need (IC-01/IC-02).

    Invariants: ``enabled is False`` ⇔ ``absolute is None`` ⇔ ``env == {}``.
    ``relative`` is always set (and validated) so ``TMP_SINK_PATH`` can be
    rendered even when the sink is disabled.
    """

    relative: str
    absolute: Optional[Path]
    enabled: bool
    system_temp_exception: SystemTempException
    pytest_basetemp: str
    env: dict[str, str]


def _as_bool(value: object, default: bool) -> bool:
    """Accept only real booleans; anything else falls back to the default."""
    return value if isinstance(value, bool) else default


def _resolve_system_temp_exception(config: Optional[dict]) -> SystemTempException:
    """Read ``repo_containment.tmp-sink.system-temp-exception`` defensively.

    Missing block ⇒ framework defaults (Q1: enabled + ``pytest-basetemp``), so
    projects that predate the key behave exactly like before (ADR-03/§5.5).
    Structural contradictions raise ``tmp-sink.system-temp-exception``; the
    sync validator reports the same combinations as hard config errors
    (IC-12, AC-15/AC-38).
    """
    raw = config.get("repo_containment") if isinstance(config, dict) else None
    block = raw if isinstance(raw, dict) else {}
    sink = block.get("tmp-sink")
    sink = sink if isinstance(sink, dict) else {}
    raw_exception = sink.get("system-temp-exception")

    if raw_exception is None:
        return SystemTempException()
    if not isinstance(raw_exception, dict):
        raise rc.TmpSinkError(
            "tmp-sink.system-temp-exception",
            "'repo_containment.tmp-sink.system-temp-exception': expected a "
            f"mapping, got {type(raw_exception).__name__}.",
        )

    enabled = _as_bool(raw_exception.get("enabled"), True)
    reason = raw_exception.get("reason")
    if not isinstance(reason, str) or not reason.strip():
        reason = DEFAULT_SYSTEM_TEMP_EXCEPTION_REASON
    pytest_basetemp = _as_bool(raw_exception.get("pytest-basetemp"), True)
    toolchain_cache = _as_bool(raw_exception.get("toolchain-caches"), False)

    if pytest_basetemp and not enabled:
        raise rc.TmpSinkError(
            "tmp-sink.system-temp-exception",
            "'repo_containment.tmp-sink.system-temp-exception': "
            "'pytest-basetemp: true' requires 'enabled: true'.",
        )
    if toolchain_cache and not enabled:
        raise rc.TmpSinkError(
            "tmp-sink.system-temp-exception",
            "'repo_containment.tmp-sink.system-temp-exception': "
            "'toolchain-caches: true' requires 'enabled: true'.",
        )

    return SystemTempException(
        enabled=enabled,
        reason=reason,
        pytest_basetemp=pytest_basetemp,
        toolchain_cache=toolchain_cache,
    )


def resolve_tmp_paths(project_root: Path, config: Optional[dict]) -> TmpPaths:
    """Resolve the tmp-sink into a :class:`TmpPaths` (IC-01/IC-02/IC-03).

    Never raises because the sink is *disabled* (that is a valid state); raises
    :class:`~lib.repo_containment.TmpSinkError` for configuration errors:
    ``tmp-sink.invalid-path`` (lexical/path/location checks, also while
    disabled) and ``tmp-sink.system-temp-exception``.

    Resolution is **pure**: it never creates the sink directory, so a
    ``sync.py --dry-run`` (which builds variables and runs this resolver) stays
    free of filesystem mutations. Provisioning lives in the consuming APIs
    that actually need an existing directory — :func:`tmp_env` (AC-12) — while
    :func:`tmp_sink_env_pin_block` renders the existence check instead (AC-36).
    """
    root = Path(project_root)
    effective = rc.resolve_effective_repo_containment(config)

    relative = effective.tmp_sink_path
    path_findings = [
        finding
        for finding in effective.findings
        if finding.code == "repo-containment.tmp-sink-path"
    ]
    if path_findings:  # the resolver fell back to the default: never silent
        raise rc.TmpSinkError("tmp-sink.invalid-path", path_findings[0].message)

    error = rc.tmp_sink_path_error(relative, root)
    if error is None:
        error = rc.tmp_sink_location_error(relative, root)
    if error is not None:
        raise rc.TmpSinkError(
            "tmp-sink.invalid-path",
            f"repo_containment.tmp-sink.path {relative!r}: {error}",
        )

    exception = _resolve_system_temp_exception(config)

    absolute: Optional[Path] = None
    env: dict[str, str] = {}
    if effective.tmp_sink_enabled:
        absolute = rc._resolve_sink_dir(  # noqa: SLF001 - single resolution (ADR-01)
            root, effective
        )
        if absolute is None:
            raise rc.TmpSinkError(
                "tmp-sink.invalid-path",
                f"repo_containment.tmp-sink.path {relative!r}: "
                "not resolvable (link escape or invalid segment)",
            )
        env = rc.work_dir_env(absolute)

    paths = TmpPaths(
        relative=relative,
        absolute=absolute,
        enabled=bool(effective.tmp_sink_enabled),
        system_temp_exception=exception,
        pytest_basetemp="",
        env=env,
    )
    return replace(paths, pytest_basetemp=resolve_pytest_basetemp(root, paths))


def _current_user() -> str:
    """Return ``USER``/``USERNAME`` with a ``getpass`` fallback (IC-04)."""
    for key in ("USER", "USERNAME"):
        value = os.environ.get(key, "").strip()
        if value:
            return value
    try:
        return getpass.getuser().strip() or "user"
    except Exception:  # noqa: BLE001 - getpass raises without a passwd entry
        return "user"


def _system_temp_basetemp() -> str:
    """``<tempfile.gettempdir()>/<user>/pytest-agent-meta`` — no literal."""
    return os.path.join(
        tempfile.gettempdir(), _current_user(), _PYTEST_BASETEMP_DIRNAME
    )


def _is_inside(base: str, candidate: str) -> bool:
    try:
        return os.path.commonpath([base, candidate]) == base
    except ValueError:  # different drives or mixed absolute/relative
        return False


def resolve_pytest_basetemp(project_root: Path, paths: TmpPaths) -> str:
    """Return the finished ``--basetemp`` value (IC-04).

    Precedence per the resolver contract:

    1. system-temp exception active for pytest ⇒ platform temp root;
    2. otherwise an enabled sink ⇒ ``<absolute>/pytest``;
    3. otherwise (disabled sink) only the exception can supply a location,
       anything else is ``tmp-sink.system-temp-exception`` — a disabled sink
       must never silently become the basetemp location.

    Raises ``tmp-sink.system-temp-exception`` when the platform temp root lies
    inside the project (the exception cannot take effect, AC-15) or when the
    value would contain a ``"`` (it is embedded as ``--basetemp="<path>"``,
    AC-34).
    """
    exception = paths.system_temp_exception
    uses_system_temp = False
    if exception.enabled and exception.pytest_basetemp:
        value = _system_temp_basetemp()
        uses_system_temp = True
    elif paths.enabled and paths.absolute is not None:
        value = os.path.join(str(paths.absolute), _PYTEST_SINK_SUBDIR)
    elif exception.pytest_basetemp:
        value = _system_temp_basetemp()
        uses_system_temp = True
    else:
        raise rc.TmpSinkError(
            "tmp-sink.system-temp-exception",
            "no pytest basetemp location: the sink is disabled and the "
            "system-temp exception does not cover 'pytest-basetemp'.",
        )

    if '"' in value or "\n" in value or "\r" in value:
        raise rc.TmpSinkError(
            "tmp-sink.system-temp-exception",
            f"pytest basetemp {value!r} must not contain a double quote or "
            "line break (it is embedded as --basetemp=\"<path>\").",
        )

    if uses_system_temp:
        project_real = os.path.realpath(os.fspath(project_root))
        temp_real = os.path.realpath(tempfile.gettempdir())
        if _is_inside(project_real, temp_real):
            raise rc.TmpSinkError(
                "tmp-sink.system-temp-exception",
                f"platform temp root {tempfile.gettempdir()!r} is inside the "
                "project root — the exception cannot take effect.",
            )

    return value


def _require_enabled(paths: TmpPaths, what: str) -> Path:
    """Return the absolute sink or raise ``tmp-sink.disabled`` (ADR-07)."""
    if not paths.enabled or paths.absolute is None:
        raise rc.TmpSinkError(
            "tmp-sink.disabled",
            f"tmp-sink is disabled; {what} has no location "
            "(opt in with repo_containment.tmp-sink.enabled: true)",
        )
    return paths.absolute


def tmp_env(paths: TmpPaths, base: Optional[dict] = None) -> dict[str, str]:
    """Return an env pinning ``TMPDIR``/``TEMP``/``TMP`` to the absolute sink.

    Delegates to :func:`lib.repo_containment.work_dir_env` so the three-key
    logic exists once (IC-06). Values are always absolute (ADR-12). Raises
    ``tmp-sink.disabled`` for a disabled sink.
    """
    absolute = _require_enabled(paths, "tmp_env")
    # AC-12: the pinned values must *exist* as directories. Provisioning happens
    # here (not in resolve_tmp_paths) so resolution stays read-only and dry-run
    # never mutates the filesystem. Idempotent; never deletes (ADR-02).
    absolute.mkdir(parents=True, exist_ok=True)
    env = rc.work_dir_env(absolute, base)
    for key in TMP_ENV_KEYS:
        env[key] = str(absolute)
    return env


def tmp_sink_env_pin_block(paths: TmpPaths) -> str:
    """Return the POSIX-sh block pinning the temp vars to the absolute sink.

    ``TMPDIR``/``TEMP``/``TMP`` all receive the same absolute value
    (``str(paths.absolute)``, ADR-12/IC-19). The block checks the directory
    *before* exporting: when the sink is gone (repo moved, no re-sync) the
    variables stay untouched and a repair hint naming
    ``python scripts/sync.py`` goes to stderr (AC-36). Values are quoted with
    :func:`shlex.quote`, so spaces and quotes cannot break the block.

    The toolchain-cache opt-in (Q3/ADR-13) adds ``PIP_CACHE_DIR`` and
    ``npm_config_cache`` below ``<absolute>/cache`` — only when the exception
    is enabled *and* ``toolchain-caches`` is on. ``TmpPaths.env`` never carries
    these keys; they belong to this block alone. ``docker`` is never redirected
    (its daemon configuration lives outside the repo).
    """
    absolute = _require_enabled(paths, "tmp_sink_env_pin_block")
    value = str(absolute)
    quoted = shlex.quote(value)
    message = (
        f"tmp-sink: {value} does not exist; TMPDIR/TEMP/TMP left unchanged "
        "(repair: python scripts/sync.py)"
    )
    lines = [
        "# tmp-sink env pin (absolute values, ADR-12)",
        f"if [ -d {quoted} ]; then",
        f"  export TMPDIR={quoted}",
        f"  export TEMP={quoted}",
        f"  export TMP={quoted}",
    ]
    exception = paths.system_temp_exception
    if exception.enabled and exception.toolchain_cache:
        for key, subdir in TOOLCHAIN_CACHE_ENV_KEYS:
            cache_value = os.path.join(value, "cache", subdir)
            lines.append(f"  export {key}={shlex.quote(cache_value)}")
    lines.extend([
        "else",
        f"  printf '%s\\n' {shlex.quote(message)} >&2",
        "fi",
    ])
    return "\n".join(lines) + "\n"
