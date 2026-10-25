"""AC-11: every framework subprocess start pins the tmp-sink env or is allowlisted.

Normative source: ``docs/specs/2026-10-24-tmp-sink-injection-spec.md`` AC-11
(scope ``scripts/**``), IC-18, ADR-01/ADR-12 and ``.meta-config/
temp-env-allowlist.yaml`` (list entries ``{path, symbol, reason}``).

The guard is deliberately static (AST, no imports of the scanned modules, no
subprocess execution): a subprocess call either receives an environment that
is derived from :func:`lib.tmp_paths.tmp_env` — directly or through a helper
whose name carries ``tmp_env``/``tmp_sink_env`` — or it has a *complete*
allowlist entry. A partial entry (missing ``reason``, unknown field such as
``expires``) suppresses nothing.

Selection criterion encoded here (kept machine-checkable through the entry
``reason`` prefix so a reviewer sees *why* a call is exempt):

* ``git-plumbing:``      — the call runs a ``git`` plumbing command; git owns
                           its own temp handling, no framework-side temp file.
* ``pure-read:``         — a read-only probe (``--version``, ``gh ... view``,
                           ``git show``/``diff``/``ls-files``).
* ``process-control:``   — ``taskkill``/``kill``; no files are created.
* ``external-cli:``      — delegates to an external CLI (``gh`` create, plugin
                           handshake) that manages its own temp files.
* ``deferred:``          — out of this task's file ownership; the reason must
                           name the owning task so the entry is actionable.

Run: python3 -m pytest tests/test_tmp_sink_env_coverage.py -q
"""

from __future__ import annotations

import ast
import fnmatch
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_ROOT = _REPO_ROOT / "scripts"
_ALLOWLIST_PATH = _REPO_ROOT / ".meta-config" / "temp-env-allowlist.yaml"

#: Functions of the ``subprocess`` module that start a child process.
_LAUNCHERS = frozenset({"run", "Popen", "call", "check_call", "check_output"})

#: A call is pinned when its ``env`` expression mentions one of these.
_PIN_TOKENS = ("tmp_env", "tmp_sink_env")

#: Strict allowlist schema (Q6): ``expires`` is not a schema field.
_REQUIRED_ENTRY_FIELDS = ("path", "symbol", "reason")
_ALLOWED_ENTRY_FIELDS = frozenset({"path", "symbol", "reason"})

#: Encoded selection criterion — the reason must open with a sanctioned category.
_REASON_CATEGORIES = (
    "git-plumbing",
    "pure-read",
    "process-control",
    "external-cli",
    "deferred",
)
_DEFERRED_MARKER = "task"


# ---------------------------------------------------------------------------
# Allowlist loading / validation
# ---------------------------------------------------------------------------

def load_allowlist() -> dict:
    """Return the raw allowlist payload (``{"entries": [...]}``)."""
    if not _ALLOWLIST_PATH.is_file():
        return {}
    with _ALLOWLIST_PATH.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def load_allowlist_entries() -> list:
    """Return the allowlist entries, tolerating a missing payload."""
    payload = load_allowlist()
    if not isinstance(payload, dict):
        return []
    entries = payload.get("entries")
    return entries if isinstance(entries, list) else []


def entry_is_valid(entry) -> bool:
    """True only for a complete, supported allowlist entry with a reason category."""
    if not isinstance(entry, dict):
        return False
    if set(entry) - _ALLOWED_ENTRY_FIELDS:
        return False
    for field in _REQUIRED_ENTRY_FIELDS:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            return False
    reason = entry["reason"].strip()
    category, sep, detail = reason.partition(":")
    if not sep or category not in _REASON_CATEGORIES or not detail.strip():
        return False
    if category == "deferred" and _DEFERRED_MARKER not in detail.lower():
        return False
    return True


def entry_matches(entry, relpath: str, symbol: str) -> bool:
    """A complete entry suppresses exactly its own path and enclosing symbol."""
    if not entry_is_valid(entry):
        return False
    if not fnmatch.fnmatch(relpath, entry["path"]):
        return False
    return entry["symbol"] == symbol


# ---------------------------------------------------------------------------
# AST scan
# ---------------------------------------------------------------------------

def _enclosing_scopes(tree: ast.AST) -> tuple[dict[ast.AST, ast.AST], dict[ast.AST, str]]:
    """Map every node to its nearest enclosing scope node and symbol name."""
    scopes: dict[ast.AST, ast.AST] = {tree: tree}
    symbols: dict[ast.AST, str] = {tree: "<module>"}

    def walk(node: ast.AST, scope: ast.AST, name: str) -> None:
        for child in ast.iter_child_nodes(node):
            child_scope, child_name = scope, name
            if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                child_scope, child_name = child, child.name
            scopes[child] = child_scope
            symbols[child] = child_name
            walk(child, child_scope, child_name)

    walk(tree, tree, "<module>")
    return scopes, symbols


def _collect_assignments(tree: ast.AST) -> dict[int, dict[str, list[ast.expr]]]:
    """Collect simple ``name = <expr>`` assignments, keyed by enclosing scope."""
    scopes, _ = _enclosing_scopes(tree)
    assignments: dict[int, dict[str, list[ast.expr]]] = {}
    for node in ast.walk(tree):
        targets: list[ast.expr] = []
        value: ast.expr | None = None
        if isinstance(node, ast.Assign):
            targets = node.targets
            value = node.value
        elif isinstance(node, ast.AnnAssign):
            targets = [node.target]
            value = node.value
        if value is None:
            continue
        bucket = assignments.setdefault(id(scopes.get(node, tree)), {})
        for target in targets:
            if isinstance(target, ast.Name):
                bucket.setdefault(target.id, []).append(value)
    return assignments


def _env_is_pinned(call: ast.Call, assignments: dict[str, list[ast.expr]]) -> bool:
    """True when the call's ``env=`` expression is derived from ``tmp_env``."""
    env_value = next((kw.value for kw in call.keywords if kw.arg == "env"), None)
    if env_value is None:
        return False

    def mentions_pin(node: ast.AST) -> bool:
        source = ast.unparse(node)
        return any(token in source for token in _PIN_TOKENS)

    if mentions_pin(env_value):
        return True
    if isinstance(env_value, ast.Name):
        for assigned in assignments.get(env_value.id, []):
            if mentions_pin(assigned):
                return True
    return False


def collect_call_sites() -> list[dict]:
    """Return one record per ``subprocess.<launcher>()`` call under ``scripts/``."""
    sites: list[dict] = []
    for source in sorted(_SCRIPTS_ROOT.rglob("*.py")):
        if "__pycache__" in source.parts:
            continue
        tree = ast.parse(source.read_text(encoding="utf-8"))
        scopes, symbols = _enclosing_scopes(tree)
        assignments = _collect_assignments(tree)
        relpath = source.relative_to(_REPO_ROOT).as_posix()
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            func = node.func
            if not (
                isinstance(func, ast.Attribute)
                and isinstance(func.value, ast.Name)
                and func.value.id == "subprocess"
                and func.attr in _LAUNCHERS
            ):
                continue
            sites.append(
                {
                    "path": relpath,
                    "symbol": symbols.get(node, "<module>"),
                    "line": node.lineno,
                    "pinned": _env_is_pinned(
                        node, assignments.get(id(scopes.get(node, tree)), {})
                    ),
                }
            )
    return sites


def collect_offenders(entries=None) -> list[str]:
    """Return ``path:symbol (line N)`` for every unpinned, unallowlisted call."""
    entries = load_allowlist_entries() if entries is None else entries
    offenders = []
    for site in collect_call_sites():
        if site["pinned"]:
            continue
        if any(
            entry_matches(entry, site["path"], site["symbol"]) for entry in entries
        ):
            continue
        offenders.append(
            "{path}:{symbol} (line {line})".format(**site)
        )
    return offenders


# ---------------------------------------------------------------------------
# AC-11 guard
# ---------------------------------------------------------------------------

def test_subprocess_calls_pin_temp_env():
    """AC-11: every ``scripts/**`` subprocess start is pinned or allowlisted."""
    offenders = collect_offenders()
    assert not offenders, (
        "subprocess calls without a tmp-sink env pin (AC-11/IC-18). Pass "
        "env=tmp_env(paths) (merging the inherited env) or add a complete "
        "entry {path, symbol, reason} to .meta-config/temp-env-allowlist.yaml:\n"
        + "\n".join(offenders)
    )


def test_allowlist_file_exists_with_entry_list():
    """IC-18: the allowlist file exists and carries an ``entries`` list."""
    assert _ALLOWLIST_PATH.is_file(), "missing allowlist: {}".format(_ALLOWLIST_PATH)
    payload = load_allowlist()
    assert isinstance(payload, dict), "allowlist root must be a mapping"
    assert isinstance(payload.get("entries"), list), "allowlist 'entries' must be a list"


def test_allowlist_schema_is_strict():
    """The allowlist never carries a partial entry or an unsupported field."""
    entries = load_allowlist_entries()
    assert isinstance(entries, list)
    for entry in entries:
        assert entry_is_valid(entry), (
            "invalid temp-env allowlist entry (needs path, symbol, reason; "
            "reason must start with a sanctioned category; 'expires' is not "
            "part of the schema): {!r}".format(entry)
        )


def test_partial_allowlist_entry_does_not_suppress():
    """AC-11: a missing reason (or an ``expires`` field) suppresses nothing."""
    site = {"path": "scripts/admin-server.py", "symbol": "_stop", "line": 1}
    partial = {"path": site["path"], "symbol": site["symbol"]}
    complete = {
        "path": site["path"],
        "symbol": site["symbol"],
        "reason": "process-control: taskkill creates no files",
    }
    assert not entry_matches(partial, site["path"], site["symbol"])
    assert not entry_matches(dict(complete, expires="2026-12-31"), site["path"], site["symbol"])
    assert not entry_matches(dict(complete, reason="because"), site["path"], site["symbol"])
    assert not entry_matches(dict(complete, reason="deferred: later"), site["path"], site["symbol"])
    assert entry_matches(complete, site["path"], site["symbol"])
    assert not entry_matches(complete, "scripts/other.py", site["symbol"])
    assert not entry_matches(complete, site["path"], "other_symbol")


def test_allowlist_entries_match_a_current_call_site():
    """No stale allowlist entry: every entry covers a real unpinned call site."""
    entries = load_allowlist_entries()
    sites = [site for site in collect_call_sites() if not site["pinned"]]
    for entry in entries:
        assert entry_is_valid(entry), entry
        assert any(
            entry_matches(entry, site["path"], site["symbol"]) for site in sites
        ), "allowlist entry matches no unpinned call site: {!r}".format(entry)
