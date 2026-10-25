"""Task 15 aggregation guard: no system temp sink on any write path.

Normative source: ``docs/specs/2026-10-24-tmp-sink-injection-spec.md``
AC-01/AC-09/AC-10/AC-11/AC-26 and the plan section "Guard-Tests" (Task 15).

The four guards live together here so a single run covers every write path:

a. ``agents/**`` and ``standalone/**`` carry no unsuppressed AC-01 literal
   (the production scanner is the measuring instrument; a complete allowlist
   entry is the only exemption).
b. The repo-containment hook fails closed when the payload ``cwd`` resolves to
   no project at all — the fixture is created *outside* the repository tree so
   no ancestor can accidentally carry ``.meta-config/``.
c. ``scripts/lib/backup.py`` stages inside the sink; the only call without
   ``dir=`` is the documented ``tmp-sink.disabled`` fallback (AC-10), and
   ``gettempdir()`` is never used as a staging base.
d. Every ``subprocess`` start under ``scripts/**`` receives an env derived from
   ``tmp_env``/``tmp_sink_env`` or owns a complete entry in
   ``.meta-config/temp-env-allowlist.yaml``.

The fifth test, ``test_temp_literal_pattern_has_single_source_of_truth``,
proves the AC-01 pattern is declared exactly once
(``scripts/lib/consistency/temp_literals.py``); every consumer imports it.

Run: python3 -m pytest tests/test_tmp_sink_injection.py -q
"""

from __future__ import annotations

import ast
import fnmatch
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Dict, List, Optional

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_ROOT = _REPO_ROOT / "scripts"
_BACKUP_PATH = _SCRIPTS_ROOT / "lib" / "backup.py"
_ENV_ALLOWLIST_PATH = _REPO_ROOT / ".meta-config" / "temp-env-allowlist.yaml"
_HOOK_PATH = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment.sh"

# The production scanner is the single consumer of the AC-01 pattern; importing
# it here is also the behavioural half of the single-source proof.
if str(_SCRIPTS_ROOT) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_ROOT))

from lib.consistency.temp_literals import (  # noqa: E402
    SYSTEM_TEMP_LITERAL_RE,
    check_temp_literals,
)

_BASH = shutil.which("bash") or "bash"

#: Directories that never contain framework source (sink, VCS, caches, mounts).
_IGNORED_PARTS = frozenset(
    {".git", ".tmp", "__pycache__", ".venv", "node_modules", "external", ".agent-meta"}
)

_SUBPROCESS_LAUNCHERS = frozenset({"run", "Popen", "call", "check_call", "check_output"})
_PIN_TOKENS = ("tmp_env", "tmp_sink_env")
_ENV_ENTRY_FIELDS = ("path", "symbol", "reason")


# ---------------------------------------------------------------------------
# a) agent templates and standalone export
# ---------------------------------------------------------------------------

def _findings(check: str, prefix: str) -> list:
    """Findings of *check* whose repo-relative file starts with *prefix*."""
    return [
        finding
        for finding in check_temp_literals(_REPO_ROOT, _REPO_ROOT, {})
        if finding.check == check and finding.file.startswith(prefix)
    ]


def test_agents_carry_no_unsuppressed_temp_literal():
    """AC-01: no literal survives in ``agents/**`` outside a complete entry."""
    hits = _findings("temp-literal.system-temp", "agents/")
    assert not hits, (
        "system temp literal in agents/** (AC-01/ADR-06). Use "
        "{{TMP_SINK_PATH}} or a complete {path, pattern, reason} allowlist "
        "entry:\n" + "\n".join(f"{f.file}: {f.message}" for f in hits)
    )
    incomplete = _findings("temp-literal.allowlist-entry", "")
    assert not incomplete, (
        "incomplete temp-literal allowlist entry (Q6/AC-39) suppresses "
        "nothing:\n" + "\n".join(f"{f.file}: {f.message}" for f in incomplete)
    )


def test_standalone_export_carries_no_unsuppressed_temp_literal():
    """AC-26: the rendered standalone export is literal-free."""
    hits = _findings("temp-literal.system-temp", "standalone/")
    assert not hits, (
        "system temp literal in standalone/** (AC-26). Fix the source template "
        "and regenerate (`python3 scripts/sync.py --render-standalone`):\n"
        + "\n".join(f"{f.file}: {f.message}" for f in hits)
    )


# ---------------------------------------------------------------------------
# b) hook fails closed without a project root
# ---------------------------------------------------------------------------

def _external_dir() -> Path:
    """A directory outside every project root (AC-03/AC-05/AC-07).

    ``tmp_path`` is unsuitable: the pytest basetemp may itself live inside a
    project root. ``tempfile.mkdtemp(dir=gettempdir())`` follows the spec, and
    the ancestor assertion turns a pathological basetemp into a loud failure
    instead of a silently passing guard.
    """
    fixture = Path(
        tempfile.mkdtemp(dir=tempfile.gettempdir(), prefix="am-tmp-sink-guard-")
    )
    for ancestor in (fixture, *fixture.parents):
        assert not (ancestor / ".meta-config").is_dir(), (
            f"external fixture {fixture} is not isolated: {ancestor} carries "
            ".meta-config/ — the guard would anchor on a real project"
        )
    return fixture


def test_hook_blocks_cwd_outside_project():
    """AC-03/AC-05: a foreign ``cwd`` is never adopted as repo root."""
    fixture = _external_dir()
    try:
        payload = {
            "tool_name": "Write",
            "tool_input": {"file_path": str(fixture / "x.py")},
            "cwd": str(fixture),
        }
        # Process cwd is the real repo (it carries .meta-config/) on purpose:
        # a pass here proves the verdict came from the payload, never from $PWD.
        result = subprocess.run(
            [_BASH, str(_HOOK_PATH)],
            input=json.dumps(payload),
            capture_output=True,
            text=True,
            cwd=str(_REPO_ROOT),
        )
        assert result.returncode == 2, (
            f"hook allowed a write with no project root (AC-03/AC-05): "
            f"exit={result.returncode}\nstdout:\n{result.stdout}\nstderr:\n{result.stderr}"
        )
        assert "repo-containment.no-root" in result.stderr, result.stderr
    finally:
        shutil.rmtree(fixture, ignore_errors=True)


# ---------------------------------------------------------------------------
# c) backup staging has no system-temp remainder
# ---------------------------------------------------------------------------

def _is_call(node: ast.AST, module: str, attribute: str) -> bool:
    return (
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and isinstance(node.func.value, ast.Name)
        and node.func.value.id == module
        and node.func.attr == attribute
    )


def _checks_disabled_sink(handler: ast.ExceptHandler) -> bool:
    """Whether an ``except`` body branches on ``<exc>.code == "tmp-sink.disabled"``."""
    for node in ast.walk(handler):
        if not isinstance(node, ast.Compare):
            continue
        left = node.left
        if not (isinstance(left, ast.Attribute) and left.attr == "code"):
            continue
        for comparator in node.comparators:
            if (
                isinstance(comparator, ast.Constant)
                and comparator.value == "tmp-sink.disabled"
            ):
                return True
    return False


def _tempdir_call_records(tree: ast.AST) -> List[Dict[str, object]]:
    """Every ``tempfile.TemporaryDirectory(...)`` with its enclosing context."""
    records: List[Dict[str, object]] = []

    def visit(node: ast.AST, function: str, disabled_handler: bool) -> None:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            function = node.name
        if isinstance(node, ast.ExceptHandler):
            disabled_handler = disabled_handler or _checks_disabled_sink(node)
        if _is_call(node, "tempfile", "TemporaryDirectory"):
            dir_arg = next(
                (keyword.value for keyword in node.keywords if keyword.arg == "dir"),
                None,
            )
            records.append(
                {
                    "function": function,
                    "in_disabled_handler": disabled_handler,
                    "has_dir": dir_arg is not None,
                    "dir_source": ast.unparse(dir_arg) if dir_arg is not None else None,
                    "lineno": getattr(node, "lineno", 0),
                }
            )
        for child in ast.iter_child_nodes(node):
            visit(child, function, disabled_handler)

    visit(tree, "<module>", False)
    return records


def _uses_gettempdir(tree: ast.AST) -> bool:
    for node in ast.walk(tree):
        if _is_call(node, "tempfile", "gettempdir"):
            return True
        if isinstance(node, ast.Attribute) and node.attr == "gettempdir":
            return True
        if isinstance(node, ast.Name) and node.id == "gettempdir":
            return True
    return False


def _staging_parent_comes_from_sink(tree: ast.AST) -> bool:
    """``staging_parent = resolve_output_dir(..., "backup-staging")`` exists."""
    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue
        if not any(
            isinstance(target, ast.Name) and target.id == "staging_parent"
            for target in node.targets
        ):
            continue
        value = node.value
        if not (
            isinstance(value, ast.Call)
            and isinstance(value.func, ast.Name)
            and value.func.id == "resolve_output_dir"
            and len(value.args) >= 3
            and isinstance(value.args[2], ast.Constant)
            and value.args[2].value == "backup-staging"
        ):
            continue
        return True
    return False


def test_backup_module_has_no_system_temp_remainder():
    """AC-09/AC-10: sink staging, one sanctioned no-``dir=`` fallback only."""
    tree = ast.parse(_BACKUP_PATH.read_text(encoding="utf-8"))
    records = _tempdir_call_records(tree)
    assert records, "backup.py has no TemporaryDirectory() call — guard is vacuous"

    bare = [record for record in records if not record["has_dir"]]
    pinned = [record for record in records if record["has_dir"]]
    assert pinned, (
        "AC-09 requires the staging TemporaryDirectory to pass dir= into the "
        f"sink; observed calls: {records}"
    )
    assert len(bare) == 1, (
        "only the documented tmp-sink.disabled fallback may omit dir= "
        f"(AC-10); observed calls: {records}"
    )
    fallback = bare[0]
    assert fallback["function"] == "_backup_staging", records
    assert fallback["in_disabled_handler"] is True, (
        "the no-dir= TemporaryDirectory must live inside the except handler "
        f"that branches on tmp-sink.disabled; observed: {records}"
    )
    assert not _uses_gettempdir(tree), (
        "backup.py must not use tempfile.gettempdir() as a staging base (AC-09)"
    )
    assert all(
        "gettempdir" not in str(record["dir_source"]) for record in pinned
    ), records
    assert any(
        "staging_parent" in str(record["dir_source"]) for record in pinned
    ), records
    assert _staging_parent_comes_from_sink(tree), (
        "staging_parent must be derived from resolve_output_dir(..., "
        "'backup-staging') (AC-09)"
    )


# ---------------------------------------------------------------------------
# d) every subprocess start pins the tmp env or is allowlisted
# ---------------------------------------------------------------------------

def _scopes_and_symbols(tree: ast.AST):
    """Map every node to its enclosing scope node and symbol name."""
    scopes = {tree: tree}
    symbols = {tree: "<module>"}

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


def _scope_assignments(tree: ast.AST) -> Dict[int, Dict[str, List[ast.AST]]]:
    """Collect ``name = <expr>`` per enclosing scope so ``env=env`` resolves."""
    scopes, _ = _scopes_and_symbols(tree)
    assignments: Dict[int, Dict[str, List[ast.AST]]] = {}
    for node in ast.walk(tree):
        targets: tuple = ()
        value: Optional[ast.AST] = None
        if isinstance(node, ast.Assign):
            targets, value = tuple(node.targets), node.value
        elif isinstance(node, ast.AnnAssign):
            targets, value = (node.target,), node.value
        if value is None:
            continue
        bucket = assignments.setdefault(id(scopes.get(node, tree)), {})
        for target in targets:
            if isinstance(target, ast.Name):
                bucket.setdefault(target.id, []).append(value)
    return assignments


def _mentions_pin(node: ast.AST) -> bool:
    return any(token in ast.unparse(node) for token in _PIN_TOKENS)


def _env_is_pinned(call: ast.Call, assignments: Dict[str, List[ast.AST]]) -> bool:
    env_value = next(
        (keyword.value for keyword in call.keywords if keyword.arg == "env"), None
    )
    if env_value is None:
        return False
    if _mentions_pin(env_value):
        return True
    if isinstance(env_value, ast.Name):
        return any(
            _mentions_pin(value) for value in assignments.get(env_value.id, [])
        )
    return False


def _subprocess_sites() -> List[Dict[str, object]]:
    """One record per ``subprocess.<launcher>()`` call under ``scripts/**``."""
    sites: List[Dict[str, object]] = []
    for source in sorted(_SCRIPTS_ROOT.rglob("*.py")):
        if any(part in _IGNORED_PARTS for part in source.relative_to(_SCRIPTS_ROOT).parts):
            continue
        tree = ast.parse(source.read_text(encoding="utf-8"))
        scopes, symbols = _scopes_and_symbols(tree)
        assignments = _scope_assignments(tree)
        relpath = source.relative_to(_REPO_ROOT).as_posix()
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "subprocess"
                and node.func.attr in _SUBPROCESS_LAUNCHERS
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


def _load_env_allowlist() -> list:
    if not _ENV_ALLOWLIST_PATH.is_file():
        return []
    with _ENV_ALLOWLIST_PATH.open(encoding="utf-8") as handle:
        payload = yaml.safe_load(handle) or {}
    entries = payload.get("entries") if isinstance(payload, dict) else None
    return entries if isinstance(entries, list) else []


def _env_entry_is_complete(entry: object) -> bool:
    if not isinstance(entry, dict):
        return False
    if set(entry) - set(_ENV_ENTRY_FIELDS):
        return False
    return all(
        isinstance(entry.get(field), str) and entry[field].strip()
        for field in _ENV_ENTRY_FIELDS
    )


def _env_entry_matches(entry: object, relpath: str, symbol: str) -> bool:
    if not _env_entry_is_complete(entry):
        return False
    return (
        fnmatch.fnmatch(relpath, entry["path"])
        and entry["symbol"] == symbol
    )


def test_every_subprocess_start_pins_tmp_env():
    """AC-11/IC-18: no unpinned, unallowlisted subprocess start in scripts/**."""
    sites = _subprocess_sites()
    assert sites, "AST scan found no subprocess starts — guard is vacuous"
    entries = _load_env_allowlist()
    offenders = []
    for site in sites:
        if site["pinned"]:
            continue
        if any(
            _env_entry_matches(entry, site["path"], site["symbol"])
            for entry in entries
        ):
            continue
        offenders.append("{path}:{symbol} (line {line})".format(**site))
    assert not offenders, (
        "subprocess start without a tmp-sink env pin (AC-11/IC-18). Pass "
        "env=tmp_env(paths) or add a complete {path, symbol, reason} entry to "
        ".meta-config/temp-env-allowlist.yaml:\n" + "\n".join(offenders)
    )


# ---------------------------------------------------------------------------
# e) the AC-01 pattern has exactly one definition
# ---------------------------------------------------------------------------

#: Marker substrings of the normative AC-01 pattern (not a compiled copy).
_AC01_MARKERS = ("/tmp/", "%TEMP%", r"[A-Za-z]:\\\\Temp\\\\")


def _is_ac01_definition(source: str) -> bool:
    """True for a compiled regex whose text carries every AC-01 marker."""
    return all(marker in source for marker in _AC01_MARKERS)


def _ac01_pattern_definitions() -> List[str]:
    """Repo-relative files that compile the AC-01 pattern themselves."""
    definitions: List[str] = []
    for path in sorted(_REPO_ROOT.rglob("*.py")):
        relative = path.relative_to(_REPO_ROOT)
        if any(part in _IGNORED_PARTS for part in relative.parts):
            continue
        try:
            tree = ast.parse(path.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError, SyntaxError):
            continue
        for node in ast.walk(tree):
            if not (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and isinstance(node.func.value, ast.Name)
                and node.func.value.id == "re"
                and node.func.attr == "compile"
                and node.args
            ):
                continue
            argument = node.args[0]
            if not (
                isinstance(argument, ast.Constant)
                and isinstance(argument.value, str)
                and _is_ac01_definition(argument.value)
            ):
                continue
            definitions.append(path.relative_to(_REPO_ROOT).as_posix())
            break
    return definitions


def test_temp_literal_pattern_has_single_source_of_truth():
    """AC-01: exactly one compiled definition, in the consistency module."""
    definitions = _ac01_pattern_definitions()
    assert definitions == ["scripts/lib/consistency/temp_literals.py"], (
        "the AC-01 pattern must be defined exactly once in "
        "scripts/lib/consistency/temp_literals.py; consumers import it. "
        f"Observed definitions: {definitions}"
    )
    # Behavioural half: the imported object is the real AC-01 pattern.
    assert SYSTEM_TEMP_LITERAL_RE.search("/tmp/x.log")
    assert SYSTEM_TEMP_LITERAL_RE.search("%TEMP%\\x")
    assert not SYSTEM_TEMP_LITERAL_RE.search("Template")
    assert not SYSTEM_TEMP_LITERAL_RE.search("my/tmp/x")
