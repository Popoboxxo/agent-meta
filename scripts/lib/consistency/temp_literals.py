"""Consistency check for system temp literals in shipped framework text.

Normative source: ``docs/specs/2026-10-24-tmp-sink-injection-spec.md``
AC-21, AC-11, IC-11, IC-18, ADR-06, ADR-12 and ADR-14/Q6.

This module is the **single source of the AC-01 pattern**
(:data:`SYSTEM_TEMP_LITERAL_RE`); every other consumer imports it instead of
declaring its own copy. The scan covers exactly the six scope roots named in
IC-11:

* ``agents/**``
* ``standalone/**``
* ``rules/1-generic/**``
* ``config/**``
* ``tests/fixtures/slimming-golden/**``
* ``tests/conftest.py``

All findings are :class:`~lib.consistency.report.Severity.WARNING`
(ADR-06): a literal is a shipped instruction that points at the machine temp
directory instead of the configured sink, not a reason to fail the run.

Codes (IC-11):

``temp-literal.system-temp``
    The AC-01 literal (``/tmp/``, ``%TEMP%``, ``C:\\Temp\\``) appears in the
    scanned text. Write to ``{{TMP_SINK_PATH}}`` instead, or declare a
    complete allowlist entry.

``temp-literal.sink-relative``
    A temp-dir variable (``TMPDIR``/``TEMP``/``TMP``) or ``--basetemp`` is
    pinned to a *relative* value (e.g. ``TMPDIR=.tmp``). ADR-12 requires
    absolute child-process values; a relative value resolves against the
    child's cwd and silently drifts.

``temp-literal.subprocess-env``
    A ``subprocess`` start under ``scripts/**`` inherits the parent
    environment instead of a pin derived from :func:`lib.tmp_paths.tmp_env`
    and is not declared in ``.meta-config/temp-env-allowlist.yaml``
    (inventory 3 / IC-18). The strict guard for this lives in
    ``tests/test_tmp_sink_env_coverage.py``; this finding makes the same gap
    visible in ``--validate``.

``temp-literal.allowlist-entry``
    An entry in ``.meta-config/temp-literal-allowlist.yaml`` cannot be applied:
    a mandatory field (``path``, ``pattern``, ``reason``) is missing or empty,
    the ``pattern`` does not compile, or the entry carries a field outside the
    schema — ``expires`` included (Q6/ADR-14, AC-39). It suppresses nothing and
    the violation keeps its own WARNING; always a WARNING, never a hard exit.

``temp-literal.toolchain-cache-in-repo``
    ``system-temp-exception.toolchain-caches`` is opted in, so pip/npm caches
    live inside the sink. Task 19 owns the opt-in itself; this module only
    reports it (the default stays ``false``, ADR-13).

``temp-literal.provider-advisory``
    A *primary* agent is generated for a provider without a verified hook
    protocol while carrying a scalar ``edit: allow`` without any path scope.
    Such a role cannot be gated at runtime, so the unlimited write scope is
    advisory only (spec §Provider-Agnostik). A path-scoped primary (the
    tmp-sink glob derived in Task 13) is silent, which is why this check is
    quiet on a correctly configured tree.

Allowlist (ADR-14/Q6): ``.meta-config/temp-literal-allowlist.yaml`` carries
entries ``{path, pattern, reason}`` (optional ``owner``). A *complete* entry
suppresses only its own file (glob in ``path``) and its matching line (regex).
Strict schema (Task 22): no ``expires``; an unappliable entry is reported as its
own ``temp-literal.allowlist-entry`` WARNING while the violation stays visible.
"""

from __future__ import annotations

import ast
import fnmatch
import re
from pathlib import Path
from typing import Iterable, List, Optional

from .. import providers as providers_lib
from ..frontmatter import parse_frontmatter_file
from ..io import load_yaml_file
from ..repo_containment import TmpSinkError
from ..tmp_paths import resolve_tmp_paths
from .report import Finding, Severity

#: AC-01 pattern — the one definition in the repository. The boundary class
#: excludes word characters, dots, underscores and hyphens, so ``Template``,
#: ``temporary`` and ``my/tmp/x`` never match; the trailing slash is required.
SYSTEM_TEMP_LITERAL_RE = re.compile(
    r"(^|[^A-Za-z0-9_.-])(/tmp/|%TEMP%|[A-Za-z]:\\\\Temp\\\\)"
)

#: IC-11 scope: directory roots scanned recursively.
_SCOPE_DIRS = (
    "agents",
    "standalone",
    "rules/1-generic",
    "config",
    "tests/fixtures/slimming-golden",
)

#: IC-11 scope: single files scanned explicitly.
_SCOPE_FILES = ("tests/conftest.py",)

#: Only text artefacts can carry an instruction; binaries are skipped.
_TEXT_SUFFIXES = frozenset(
    {".md", ".markdown", ".yaml", ".yml", ".json", ".py", ".sh", ".toml", ".txt"}
)

#: Directories never worth descending into inside a scope root.
_IGNORED_PARTS = frozenset({".git", "__pycache__", ".venv", "node_modules"})

_ALLOWLIST_RELPATH = Path(".meta-config") / "temp-literal-allowlist.yaml"

#: Q6/ADR-14 schema — Task 22 validates these fields; Task 14 only uses them.
_REQUIRED_ENTRY_FIELDS = ("path", "pattern", "reason")
_ALLOWED_ENTRY_FIELDS = frozenset({"path", "pattern", "reason", "owner"})

#: ADR-12: pinned values must be absolute. These prefixes are not relative.
_ABSOLUTE_VALUE_PREFIXES = ("/", "\\", "~", "$", "%", "{{")

_ENV_PIN_RE = re.compile(
    r"(?:^|[\s;&|])(?:export\s+)?(?P<key>TMPDIR|TEMP|TMP)\s*=\s*(?P<value>[^\s;&|]+)"
)
_BASETEMP_RE = re.compile(r"--basetemp(?:=|\s+)(?P<value>[^\s;&|]+)")
_WINDOWS_ABSOLUTE_RE = re.compile(r"^[A-Za-z]:[\\/]")
_LAUNCHERS = frozenset({"run", "Popen", "call", "check_call", "check_output"})
_PIN_TOKENS = ("tmp_env", "tmp_sink_env")


# ---------------------------------------------------------------------------
# Allowlist
# ---------------------------------------------------------------------------

def _load_allowlist_entries(root: Path) -> list:
    """Raw ``entries`` list; an allowlist problem never crashes the check.

    Missing file, malformed YAML or a non-list payload yields an empty list.
    Schema enforcement lives in :func:`_entry_problems`.
    """
    payload = load_yaml_file(root / _ALLOWLIST_RELPATH, on_error="default", default={})
    if not isinstance(payload, dict):
        return []
    entries = payload.get("entries")
    return entries if isinstance(entries, list) else []


def _entry_problems(entry: object) -> List[str]:
    """Every reason an entry cannot be applied (empty ⇒ complete, Q6/ADR-14).

    ``path``/``pattern``/``reason`` are mandatory non-empty strings,
    ``pattern`` must compile, ``owner`` is optional, every other field
    (``expires`` included) invalidates the entry.
    """
    if not isinstance(entry, dict):
        return ["entry is not a mapping"]
    problems: List[str] = []
    unknown = sorted(str(field) for field in set(entry) - _ALLOWED_ENTRY_FIELDS)
    if unknown:
        hint = " ('expires' is not part of the schema)" if "expires" in unknown else ""
        problems.append("unsupported field(s): " + ", ".join(unknown) + hint)
    for field in _REQUIRED_ENTRY_FIELDS:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            problems.append(f"missing non-empty '{field}'")
    pattern = entry.get("pattern")
    if isinstance(pattern, str) and pattern.strip():
        try:
            re.compile(pattern)
        except re.error as exc:
            problems.append(f"invalid 'pattern' regex: {exc}")
    return problems


def _entry_is_complete(entry: object) -> bool:
    """Whether an entry satisfies the strict Q6/ADR-14 schema."""
    return not _entry_problems(entry)


def _allowlist_entry_findings(entries: list) -> List[Finding]:
    """One WARNING per unappliable entry, independent of any violation (AC-39)."""
    findings: List[Finding] = []
    for index, entry in enumerate(entries, start=1):
        problems = _entry_problems(entry)
        if not problems:
            continue
        path = entry.get("path") if isinstance(entry, dict) else None
        findings.append(Finding(
            Severity.WARNING,
            "temp-literal.allowlist-entry",
            _ALLOWLIST_RELPATH.as_posix(),
            f"allowlist entry #{index}"
            + (f" ({path})" if isinstance(path, str) and path.strip() else "")
            + " suppresses nothing: " + "; ".join(problems),
            "Declare path, pattern and reason (owner optional); 'expires' is not "
            "part of the schema (Q6/ADR-14), so the violation keeps its own "
            "temp-literal.system-temp warning until the entry is fixed.",
        ))
    return findings


def _entry_suppresses(entry: object, relpath: str, line: str) -> bool:
    """A complete entry suppresses only its own path (glob) and line (regex)."""
    if not _entry_is_complete(entry):
        return False
    if not fnmatch.fnmatch(relpath, entry["path"]):
        return False
    return re.search(entry["pattern"], line) is not None


# ---------------------------------------------------------------------------
# Scope traversal
# ---------------------------------------------------------------------------

def _is_scannable(path: Path) -> bool:
    if any(part in _IGNORED_PARTS for part in path.parts):
        return False
    return path.suffix.lower() in _TEXT_SUFFIXES


def _iter_scope_files(root: Path) -> Iterable[Path]:
    """Yield every in-scope text file below *root* (IC-11)."""
    for rel_dir in _SCOPE_DIRS:
        base = root / rel_dir
        if not base.is_dir():
            continue
        for path in sorted(base.rglob("*")):
            if path.is_file() and _is_scannable(path):
                yield path
    for rel_file in _SCOPE_FILES:
        path = root / rel_file
        if path.is_file() and _is_scannable(path):
            yield path


def _iter_scan_roots(agent_meta_root: Path, project_root: Path) -> List[Path]:
    """The framework tree first, then a distinct project tree (deduped)."""
    roots = [Path(agent_meta_root)]
    project = Path(project_root)
    if project.resolve() != roots[0].resolve():
        roots.append(project)
    return roots


def _read_lines(path: Path) -> Optional[List[str]]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return None


def _relpath(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


# ---------------------------------------------------------------------------
# Literal scanners
# ---------------------------------------------------------------------------

def _system_temp_findings(lines: List[str], relpath: str, entries: list) -> List[Finding]:
    findings: List[Finding] = []
    for lineno, line in enumerate(lines, start=1):
        if not SYSTEM_TEMP_LITERAL_RE.search(line):
            continue
        if any(_entry_suppresses(entry, relpath, line) for entry in entries):
            continue
        findings.append(Finding(
            Severity.WARNING,
            "temp-literal.system-temp",
            relpath,
            f"system temp literal in shipped text on line {lineno}: {line.strip()}",
            "Write to {{TMP_SINK_PATH}} instead (ADR-06); if the literal is "
            "intentional, add a complete entry {path, pattern, reason} to "
            ".meta-config/temp-literal-allowlist.yaml.",
        ))
    return findings


def _looks_like_path(value: str) -> bool:
    """Heuristic: prose like ``--basetemp to use`` must not read as a pin."""
    candidate = value.strip().strip("\"'")
    if not candidate:
        return False
    if candidate.startswith(("./", "../", "/", "~", "$", "%", "{{", "\\")):
        return True
    if _WINDOWS_ABSOLUTE_RE.match(candidate):
        return True
    return "/" in candidate or "\\" in candidate or "." in candidate


def _is_relative_pin(value: str) -> bool:
    """True for a temp-pin value that resolves against the child's cwd."""
    if not _looks_like_path(value):
        return False
    candidate = value.strip().strip("\"'")
    if candidate.startswith(_ABSOLUTE_VALUE_PREFIXES):
        return False
    if _WINDOWS_ABSOLUTE_RE.match(candidate):
        return False
    return True


def _sink_relative_findings(lines: List[str], relpath: str) -> List[Finding]:
    findings: List[Finding] = []
    for lineno, line in enumerate(lines, start=1):
        values = [m.group("value") for m in _ENV_PIN_RE.finditer(line)]
        values += [m.group("value") for m in _BASETEMP_RE.finditer(line)]
        offenders = [value for value in values if _is_relative_pin(value)]
        if not offenders:
            continue
        findings.append(Finding(
            Severity.WARNING,
            "temp-literal.sink-relative",
            relpath,
            f"relative temp pin on line {lineno}: {', '.join(offenders)} — a "
            "relative TMPDIR/TEMP/TMP/--basetemp resolves against the child's "
            "cwd (ADR-12 requires absolute values).",
            "Use the absolute sink value (TMP_SINK_ABS_PATH / "
            "TMP_SINK_ENV_PIN_BLOCK) instead of a relative literal.",
        ))
    return findings


# ---------------------------------------------------------------------------
# Subprocess env pin (inventory 3 / IC-18)
# ---------------------------------------------------------------------------

_ENV_ALLOWLIST_RELPATH = Path(".meta-config") / "temp-env-allowlist.yaml"


def _load_env_allowlist_entries(root: Path) -> list:
    payload = load_yaml_file(root / _ENV_ALLOWLIST_RELPATH, on_error="default", default={})
    if not isinstance(payload, dict):
        return []
    entries = payload.get("entries")
    return entries if isinstance(entries, list) else []


def _env_entry_matches(entry: object, relpath: str, symbol: str) -> bool:
    if not isinstance(entry, dict):
        return False
    if not isinstance(entry.get("path"), str) or not isinstance(entry.get("symbol"), str):
        return False
    if not str(entry.get("reason", "")).strip():
        return False
    return fnmatch.fnmatch(relpath, entry["path"]) and entry["symbol"] == symbol


def _nodes_with_symbols(tree: ast.AST) -> dict:
    """Map every node to the name of its nearest enclosing function/class."""
    symbols: dict = {tree: "<module>"}

    def walk(node: ast.AST, name: str) -> None:
        for child in ast.iter_child_nodes(node):
            child_name = name
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                child_name = child.name
            symbols[child] = child_name
            walk(child, child_name)

    walk(tree, "<module>")
    return symbols


def _scope_map(tree: ast.AST) -> dict:
    """Map every node to its nearest enclosing scope node (module/function/class)."""
    scopes: dict = {tree: tree}

    def walk(node: ast.AST, scope: ast.AST) -> None:
        for child in ast.iter_child_nodes(node):
            child_scope = child if isinstance(
                child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)
            ) else scope
            scopes[child] = child_scope
            walk(child, child_scope)

    walk(tree, tree)
    return scopes


def _collect_env_assignments(tree: ast.AST, scopes: dict) -> dict:
    """Collect ``name = <expr>`` per scope so ``env=env`` resolves its origin."""
    assignments: dict = {}
    for node in ast.walk(tree):
        targets = ()
        value = None
        if isinstance(node, ast.Assign):
            targets, value = node.targets, node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = (node.target,), node.value
        if value is None:
            continue
        bucket = assignments.setdefault(id(scopes.get(node, tree)), {})
        for target in targets:
            if isinstance(target, ast.Name):
                bucket.setdefault(target.id, []).append(value)
    return assignments


def _is_subprocess_launch(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    func = node.func
    return (
        isinstance(func, ast.Attribute)
        and isinstance(func.value, ast.Name)
        and func.value.id == "subprocess"
        and func.attr in _LAUNCHERS
    )


def _mentions_pin(node: ast.AST) -> bool:
    try:
        source = ast.unparse(node)
    except (AttributeError, ValueError):  # pragma: no cover - Python < 3.9 guard
        return False
    return any(token in source for token in _PIN_TOKENS)


def _env_is_pinned(call: ast.Call, assignments: dict) -> bool:
    """True when ``env=`` mentions a tmp pin directly or via a local variable."""
    env_value = next((kw.value for kw in call.keywords if kw.arg == "env"), None)
    if env_value is None:
        return False
    if _mentions_pin(env_value):
        return True
    if isinstance(env_value, ast.Name):
        return any(_mentions_pin(value) for value in assignments.get(env_value.id, []))
    return False


def _subprocess_env_findings(agent_meta_root: Path) -> List[Finding]:
    """WARNING for every unpinned, unallowlisted subprocess start in ``scripts/``."""
    scripts = Path(agent_meta_root) / "scripts"
    if not scripts.is_dir():
        return []
    entries = _load_env_allowlist_entries(Path(agent_meta_root))
    findings: List[Finding] = []
    for source in sorted(scripts.rglob("*.py")):
        if any(part in _IGNORED_PARTS for part in source.parts):
            continue
        try:
            tree = ast.parse(source.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        symbols = _nodes_with_symbols(tree)
        scopes = _scope_map(tree)
        assignments = _collect_env_assignments(tree, scopes)
        relpath = _relpath(source, Path(agent_meta_root))
        for node in ast.walk(tree):
            if not _is_subprocess_launch(node) or not isinstance(node, ast.Call):
                continue
            scope_assignments = assignments.get(id(scopes.get(node, tree)), {})
            if _env_is_pinned(node, scope_assignments):
                continue
            symbol = symbols.get(node, "<module>")
            if any(_env_entry_matches(entry, relpath, symbol) for entry in entries):
                continue
            findings.append(Finding(
                Severity.WARNING,
                "temp-literal.subprocess-env",
                relpath,
                f"subprocess start without a tmp-sink env pin in {symbol}() "
                f"on line {node.lineno}",
                "Pass env=tmp_env(paths) (merging the inherited environment) "
                "or add a complete entry {path, symbol, reason} to "
                ".meta-config/temp-env-allowlist.yaml.",
            ))
    return findings


# ---------------------------------------------------------------------------
# Config-derived findings
# ---------------------------------------------------------------------------

def _toolchain_cache_findings(project_root: Path, config: Optional[dict]) -> List[Finding]:
    """WARNING when the toolchain caches are opted into the repository (ADR-13)."""
    if not isinstance(config, dict):
        return []
    try:
        paths = resolve_tmp_paths(Path(project_root), config)
    except TmpSinkError:
        # Configuration errors are reported by sync.py --validate as ERROR.
        return []
    if not paths.system_temp_exception.toolchain_cache:
        return []
    return [Finding(
        Severity.WARNING,
        "temp-literal.toolchain-cache-in-repo",
        ".meta-config/project.yaml",
        "system-temp-exception.toolchain-caches is enabled: pip/npm caches are "
        "pinned inside the repository sink and grow with backup, CI cache and "
        "submodule mount (and a repo move leaves a dead cache path).",
        "Keep toolchain-caches: false unless the in-repo cache is a deliberate "
        "trade-off; the default keeps the warm user cache outside the repo.",
    )]


def _provider_advisory_findings(
    agent_meta_root: Path, project_root: Path, config: Optional[dict]
) -> List[Finding]:
    """WARNING for an unscoped primary ``edit: allow`` on a hook-less provider.

    Only the *primary* surface is covered: the global deny rule that a scalar
    ``edit: allow`` would overrule applies to it (Task 13 derives a path scope
    from the tmp-sink). Subagent roles were never gated by that deny, so
    reporting them here would add noise without information.
    """
    if not isinstance(config, dict) or not config:
        return []
    try:
        provider_config = providers_lib.load_providers_config(Path(agent_meta_root), config)
        active = providers_lib.resolve_providers(config, provider_config, tolerate_unknown=True)
    except Exception:  # noqa: BLE001 - a read-only check must not crash on the registry
        return []

    findings: List[Finding] = []
    for provider in active:
        entry = provider_config.get(provider) or {}
        if providers_lib.provider_hooks_supported(entry):
            continue
        agents_dir = entry.get("agents_dir")
        if not isinstance(agents_dir, str) or not agents_dir:
            continue
        directory = Path(project_root) / agents_dir
        if not directory.is_dir():
            continue
        extension = entry.get("agent_ext") or ".md"
        for path in sorted(directory.glob(f"*{extension}")):
            frontmatter = parse_frontmatter_file(path)
            if not isinstance(frontmatter, dict):
                continue
            if frontmatter.get("mode") != "primary":
                continue
            permission = frontmatter.get("permission")
            if not isinstance(permission, dict) or permission.get("edit") != "allow":
                continue
            relpath = _relpath(path, Path(project_root))
            findings.append(Finding(
                Severity.WARNING,
                "temp-literal.provider-advisory",
                relpath,
                f"role '{frontmatter.get('name')}' is generated for provider "
                f"'{provider}' with a scalar 'edit: allow' and no path scope, "
                "but this provider has no verified hook protocol — the write "
                "scope is advisory only.",
                "Derive a path-scoped edit allow-list (tmp-sink glob) or accept "
                "that writes are not gated at runtime on this provider.",
            ))
    return findings


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def check_temp_literals(
    agent_meta_root: Path,
    project_root: Path,
    config: Optional[dict],
) -> List[Finding]:
    """Return every ``temp-literal.*`` finding for the framework text (IC-11).

    *agent_meta_root* is the framework checkout; *project_root* is the synced
    project (identical when agent-meta validates itself). Every root is
    scanned once per repo-relative path, so a self-hosting run does not
    duplicate findings. *config* feeds the two config-derived codes only
    (toolchain cache, provider advisory); all literal findings are
    config-independent.

    Never raises: this is a read-only consistency check (ADR-06).
    """
    roots = _iter_scan_roots(Path(agent_meta_root), Path(project_root))
    allowlist_root = roots[0]
    if not (allowlist_root / _ALLOWLIST_RELPATH).is_file() and len(roots) > 1:
        allowlist_root = roots[1]
    entries = _load_allowlist_entries(allowlist_root)
    findings: List[Finding] = _allowlist_entry_findings(entries)

    seen: set = set()
    for root in roots:
        for path in _iter_scope_files(root):
            relpath = _relpath(path, root)
            if relpath in seen:
                continue
            seen.add(relpath)
            lines = _read_lines(path)
            if lines is None:
                continue
            findings.extend(_system_temp_findings(lines, relpath, entries))
            findings.extend(_sink_relative_findings(lines, relpath))

    findings.extend(_subprocess_env_findings(Path(agent_meta_root)))
    findings.extend(_toolchain_cache_findings(Path(project_root), config))
    findings.extend(
        _provider_advisory_findings(Path(agent_meta_root), Path(project_root), config)
    )
    return findings
