"""I/O helpers for loading YAML/JSON config files."""
from __future__ import annotations

import hashlib
import json
import os
import re
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Any, TypeVar


class SyncError(Exception):
    """Fatal sync error — sync cannot continue safely."""


def _normalize_enabled_config(raw) -> dict:
    """Normalize a project activation config to dict format.

    Accepts both the flat list shorthand ['name-a', 'name-b'] (alias for
    {'name-a': {'enabled': True}, 'name-b': {'enabled': True}}) and the
    canonical dict form {'name': {'enabled': True|False, ...}}. Shared by
    every registry with this activation shape (external-skills, external-
    tools, ...) — previously duplicated verbatim in each.
    """
    if isinstance(raw, list):
        return {name: {"enabled": True} for name in raw}
    if isinstance(raw, dict):
        return raw
    return {}


def _deep_merge(dict1: dict, dict2: dict) -> dict:
    """Recursively merge dict2 into dict1. Mutates and returns dict1.

    Shared by every registry loader that layers project overrides onto a
    framework default (mcp.py, external_tools.py, ...) — previously
    duplicated verbatim in each.
    """
    for k, v in dict2.items():
        if isinstance(v, dict) and k in dict1 and isinstance(dict1[k], dict):
            _deep_merge(dict1[k], v)
        else:
            dict1[k] = v
    return dict1

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


def _load_yaml_or_json(*paths: Path) -> tuple[dict, Path]:
    """Load the first existing file from paths (YAML or JSON). Returns (data, used_path).

    Accepts 1..N paths tried in order — first existing file wins.
    Preferred path (for "not found" return) is always paths[0].
    """
    preferred = paths[0]
    for path in paths:
        if not path.exists():
            continue
        if path.suffix.lower() in (".yaml", ".yml"):
            if not _YAML_AVAILABLE:
                print(f"WARNING: PyYAML not installed, skipping {path.name}.", file=sys.stderr)
                continue
            try:
                with path.open(encoding="utf-8") as f:
                    data = _yaml.safe_load(f)
            except _yaml.YAMLError as exc:
                raise SyncError(f"Invalid YAML in '{path}': {exc}") from exc
        else:
            try:
                with path.open(encoding="utf-8") as f:
                    data = json.load(f)
            except json.JSONDecodeError as exc:
                raise SyncError(f"Invalid JSON in '{path}': {exc}") from exc
        # Every caller immediately does data.get(...) — a top-level list or
        # scalar would blow up there with an opaque AttributeError instead.
        if data is None:
            data = {}
        if not isinstance(data, dict):
            raise SyncError(
                f"Invalid config '{path}': expected a mapping at the top level, "
                f"got {type(data).__name__}."
            )
        return data, path
    return {}, preferred  # none found — return empty + preferred path


def _yaml_error_location(exc: Exception) -> str:
    """Format a ``(line X, col Y)`` suffix from a PyYAML error's problem_mark.

    Mirrors the location information config.py::load_config puts into its
    messages — single-file loaders raise SyncError with the same context
    (Issue #479).
    """
    mark = getattr(exc, "problem_mark", None)
    if mark is None:
        return ""
    return f" (line {mark.line + 1}, col {mark.column + 1})"


_DefaultT = TypeVar("_DefaultT")


def _validate_on_error(on_error: str) -> None:
    """Validate the ``on_error`` mode shared by load_yaml_file/load_json_file."""
    if on_error not in ("raise", "default", "warn"):
        raise ValueError(
            f"on_error must be 'raise', 'default' or 'warn', got {on_error!r}"
        )


def _loader_fail(
    on_error: str,
    message: str,
    default: Any,
    log: "SyncLog | None",  # noqa: F821
) -> Any:
    """Shared failure handler for the single-file loaders (Issue #479).

    ``"raise"`` raises SyncError with the given message; ``"warn"`` emits
    ``log.warning`` (ValueError when no log was supplied); every mode
    returns ``default`` — silently for ``"default"``, after the warning for
    ``"warn"``.
    """
    if on_error == "raise":
        raise SyncError(message)
    if on_error == "warn":
        if log is None:
            raise ValueError('on_error="warn" requires a log instance')
        log.warning(message)
    return default


def load_yaml_file(
    path: Path,
    *,
    on_error: str = "raise",
    default: "dict | _DefaultT | None" = None,
    log: "SyncLog | None" = None,  # noqa: F821
) -> "dict | _DefaultT | None":
    """Load a single known-path YAML file into a dict (Issue #479).

    Companion to `_load_yaml_or_json` (multi-path YAML-or-JSON dispatch —
    kept unchanged for its 15+ callers): this loader is for single files at
    a known path with a well-defined, caller-chosen failure behavior,
    replacing the ~7 hand-rolled per-module YAML loaders.

    Failure handling (``on_error``) applies to unreadable files (OSError),
    malformed YAML (``yaml.YAMLError``), non-mapping top-level documents, and
    missing PyYAML — chosen per call site:

    - ``"raise"``   — SyncError with file + ``problem_mark`` location
                      (fail-closed; config-audit style).
    - ``"default"`` — return ``default`` silently (optional-file semantics).
    - ``"warn"``    — ``log.warning`` + return ``default``.

    Missing file is never an error in any mode: ``default`` is returned
    (mirrors `_load_yaml_or_json`'s missing-file contract and the
    ``if not path.exists(): return {}`` guards of the replaced loaders).
    An *empty* YAML document (parses to ``None``) yields ``{}`` in every
    mode — it mirrors the ``yaml.safe_load(f) or {}`` idiom of the replaced
    loaders, independently of ``default``.

    Args:
        path: YAML file to load.
        on_error: One of ``"raise"``, ``"default"``, ``"warn"``.
        default: Failure/missing-file fallback, returned exactly as passed
            (pass ``{}`` for the common empty-dict case; pass ``None`` to use
            None as a failure sentinel).
        log: SyncLog for ``on_error="warn"`` (ignored otherwise).

    Returns:
        Parsed mapping, ``{}`` for an empty document, or ``default``.
    """
    _validate_on_error(on_error)
    if not path.exists():
        return default
    if not _YAML_AVAILABLE:
        return _loader_fail(
            on_error,
            f"PyYAML not installed, cannot load {path} — install it with: pip install pyyaml",
            default,
            log,
        )
    try:
        with path.open(encoding="utf-8") as f:
            data = _yaml.safe_load(f)
    except OSError as exc:
        return _loader_fail(on_error, f"Cannot read YAML file '{path}': {exc}", default, log)
    except _yaml.YAMLError as exc:
        return _loader_fail(
            on_error,
            f"Invalid YAML in '{path}'{_yaml_error_location(exc)}: {exc}",
            default,
            log,
        )
    if data is None:
        return {}
    if not isinstance(data, dict):
        return _loader_fail(
            on_error,
            f"Invalid YAML config '{path}': expected a mapping at the top "
            f"level, got {type(data).__name__}.",
            default,
            log,
        )
    return data


def load_json_file(
    path: Path,
    *,
    on_error: str = "raise",
    default: "dict | list | _DefaultT | None" = None,
    log: "SyncLog | None" = None,  # noqa: F821
) -> "dict | list | _DefaultT | None":
    """Load a single known-path JSON file (Issue #479).

    Same ``on_error`` contract as `load_yaml_file` (missing file → ``default``,
    ``"raise"``/``"default"``/``"warn"`` for OSError/JSONDecodeError). Unlike
    the YAML loader there is no mapping check — JSON lists/scalars are
    legitimate documents and are returned as-is. An empty file raises
    JSONDecodeError (JSON has no empty-document concept).

    Args:
        path: JSON file to load.
        on_error: One of ``"raise"``, ``"default"``, ``"warn"``.
        default: Failure/missing-file fallback, returned exactly as passed.
        log: SyncLog for ``on_error="warn"`` (ignored otherwise).

    Returns:
        Parsed JSON document, or ``default``.
    """
    _validate_on_error(on_error)
    if not path.exists():
        return default
    try:
        with path.open(encoding="utf-8") as f:
            return json.load(f)
    except OSError as exc:
        return _loader_fail(on_error, f"Cannot read JSON file '{path}': {exc}", default, log)
    except json.JSONDecodeError as exc:
        return _loader_fail(
            on_error,
            f"Invalid JSON in '{path}' (line {exc.lineno}, col {exc.colno}): {exc.msg}",
            default,
            log,
        )


def strip_jsonc_comments(text: str) -> str:
    """Remove // line comments from JSONC text without touching string values.

    A regex cannot do this safely: a string value may legitimately contain
    ``//`` (a URL, a regex, a path), and a quote-excluding pattern truncates
    the line instead — silently corrupting the document (issue #474). This
    walks the text once, tracking whether the cursor is inside a quoted
    string, and only strips ``//`` runs found outside one.
    """
    out: list[str] = []
    in_string = False
    escape = False
    i = 0
    length = len(text)
    while i < length:
        char = text[i]
        if escape:
            out.append(char)
            escape = False
        elif char == "\\":
            out.append(char)
            escape = in_string  # backslash only escapes inside a string
        elif char == '"':
            out.append(char)
            in_string = not in_string
        elif not in_string and char == "/" and i + 1 < length and text[i + 1] == "/":
            # Drop everything up to (but not including) the line break, so
            # line structure — and therefore JSON error line numbers — survive.
            while i < length and text[i] != "\n":
                i += 1
            continue
        else:
            out.append(char)
        i += 1
    return "".join(out)


def read_json_lenient(path: Path) -> dict | None:
    """Read a JSON file, tolerating JSONC-style // comments, trailing commas and a BOM.

    Settings files like opencode.json(c) are JSONC: full-line and inline
    // comments plus trailing commas left behind after commenting out entries.
    Returns None when the file cannot be parsed even after cleanup.
    """
    text = path.read_text(encoding="utf-8-sig")
    stripped = strip_jsonc_comments(text)
    stripped = re.sub(r',\s*([}\]])', r'\1', stripped)
    try:
        return json.loads(stripped)
    except (json.JSONDecodeError, ValueError):
        return None


def write_atomic(path: Path, content: str, mode: str = "w") -> None:
    """Write content to path atomically via temp file + os.replace() (#573).

    A plain ``path.write_text()`` truncates the target file in place — a
    process crash/kill/OS-interrupt mid-write leaves a corrupted (partial or
    empty) file behind. This writes to a temp file in the same directory
    (guaranteeing the same filesystem, required for ``os.replace`` to be
    atomic) and only swaps it into place once the write has fully
    succeeded and been flushed to disk. On any failure the original file
    is left untouched and the temp file is cleaned up.

    mode: "w" (text, default) or "wb" (binary).
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    binary = "b" in mode
    fd, tmp_name = tempfile.mkstemp(dir=str(path.parent), prefix=f".{path.name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "wb" if binary else "w", **({} if binary else {"encoding": "utf-8"})) as f:
            f.write(content)
            f.flush()
            os.fsync(f.fileno())
        os.replace(tmp_name, path)
    except BaseException:
        try:
            os.unlink(tmp_name)
        except OSError:
            pass
        raise


def _write_yaml(path: Path, data: dict) -> None:
    """Write data as YAML with consistent formatting."""
    write_atomic(path, _yaml.dump(data, allow_unicode=True, default_flow_style=False,
                                   sort_keys=False, indent=2))


def content_hash(text: str) -> str:
    """Return a short SHA-256 hex digest of text (first 16 chars)."""
    return hashlib.sha256(text.encode("utf-8")).hexdigest()[:16]


def is_unchanged(path: Path, new_content: str) -> bool:
    """Return True when path exists and already contains new_content."""
    if not path.exists():
        return False
    return path.read_text(encoding="utf-8") == new_content


def write_checked(
    path: Path,
    content: str,
    log: "SyncLog",  # noqa: F821
    rel_label: str,
    force: bool = False,
    allow_secrets: bool = False,
    config: dict | None = None,
    dry_run: bool = False,
    verify_gitignored: bool = False,
) -> bool:
    """Write content to path unless it is already identical (incremental sync).

    Scans for potential secrets before writing.
    - allow_secrets=False (default): raises SyncError when a secret is detected.
      Use this for committed files — secrets must never land in version control.
    - allow_secrets=True: emits a warning only (use for gitignored local files).

    Set allow-committed-secrets: true in project.yaml to override for a project
    (not recommended — prefer ${ENV_VAR} references in committed configs). Note
    this reuses allow_secrets=True for a *committed* file, which is why the
    gitignore verification below is a separate, explicitly opted-in flag
    rather than being implied by allow_secrets — the two "allow_secrets=True"
    call sites mean different things (genuinely-local file vs. an explicit
    committed-secrets override).

    config: optional project config dict — extends secret detection with
            security.secret-patterns from project.yaml.

    dry_run: when True, perform only the change detection — skip the secret
             scan and the actual write. Returns True when the file *would* be
             written (content differs / missing), False when unchanged. This
             lets callers report accurate action/skip counts in dry-run mode
             (used by ``sync.py --dry-run --check`` for CI).

    verify_gitignored: when True, warn (never block) if `path` is not actually
             covered by .gitignore (#586) — use for files that are genuinely
             expected to be local-only (e.g. secrets.local.yaml-derived
             provider configs), not for the allow-committed-secrets override
             above.

    Returns True when the file was written, False when skipped as unchanged.
    """
    if not force and is_unchanged(path, content):
        return False
    if dry_run:
        # Change detected but do not touch the filesystem (or scan secrets —
        # dry-run must never fail on secrets it would not write).
        return True
    from .secrets import scan_for_secrets
    findings = scan_for_secrets(content, config=config)
    if findings:
        if not allow_secrets:
            raise SyncError(
                f"Secret detected in committed file '{rel_label}': "
                + ", ".join(findings)
                + "\n  Use allow-committed-secrets: true in project.yaml to bypass (not recommended)."
            )
        for finding in findings:
            log.warning(f"potential secret in {rel_label}: {finding} — verify before committing")
    if verify_gitignored:
        # Informational only (#586): never blocks the write, since this is
        # not a security boundary, just an early warning for a misconfigured
        # provider ignore-file.
        _warn_if_not_gitignored(path, rel_label, log)
    write_atomic(path, content)
    return True


def _warn_if_not_gitignored(path: Path, rel_label: str, log: "SyncLog") -> None:  # noqa: F821
    """Warn when a file expected to be gitignored is not actually ignored (#586).

    Fail-safe: any problem running git (not installed, not a repo, timeout)
    is silently ignored — this check is informational, never a hard gate.
    """
    try:
        result = subprocess.run(  # noqa: S603
            ["git", "check-ignore", "-q", str(path)],
            cwd=str(path.parent) if path.parent.exists() else str(Path.cwd()),
            capture_output=True,
            timeout=5,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return
    if result.returncode == 1:
        # 0 = ignored, 1 = not ignored, >1 = git error (no repo, bad options, ...)
        log.warning(
            f"{rel_label} looks like a local secrets file but is not covered by "
            ".gitignore — verify it is excluded from version control."
        )


def safe_path(base: Path, *parts: str) -> Path:
    """Join base with parts and validate the result stays within base.

    Raises ValueError if the resolved path escapes the base directory.
    This prevents path traversal via malicious config values (e.g. prefix='../../evil').
    """
    path = base.joinpath(*parts).resolve()
    base_resolved = base.resolve()
    try:
        path.relative_to(base_resolved)
    except ValueError:
        raise ValueError(
            f"Path traversal detected: attempted to write outside project root. "
            f"Resolved path: {path}, base: {base_resolved}"
        )
    return path
