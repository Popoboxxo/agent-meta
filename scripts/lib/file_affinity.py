"""Task-level static file-affinity analysis (deterministic, stdlib-only).

Deterministic replacement for the LLM-guided "Check file ranges for
overlap" step before FANOUT / PARALLEL_GROUP dispatch (issue #266,
roadmap phase 4b). Every reported conflict is backed by parsed file
content or parsed task context — never by a model guess.

Boundary (IMPORTANT):
    This module only ANALYSES. The real enforcement point — calling
    ``check_file_overlap()`` before a REAL dispatch — is harness-side:
    agent-meta ships this analysis plus a dry-run integration in
    ``tests/orchestration/dry_run/engine.py`` (conflicted tasks are
    sequentialized there before simulated FANOUT/PARALLEL_GROUP).
    Handoff note for a central orchestrator.md consolidation (NOT part
    of this change): the prompt should say "File-Affinity Check
    validated via static analysis" instead of instructing the model to
    "check file ranges for overlap" itself.

Task input format (``tasks`` — an iterable of any of these):

    - ``str``: task description text. Id synthesized as ``task_N``
      (1-based, input order).
    - ``dict``: keys ``id``/``task_id``/``name`` (identity, stringified),
      ``files`` (explicit write set, str or list of str) and
      ``description``/``task_description``/``task``/``text`` (context
      text). Mirrors ``Checkpoint.to_dict()`` (``task_description``) and
      delegation-style dicts (see ``scripts/lib/delegation_table.py``).
    - object exposing ``name``/``task_id`` and
      ``description``/``task_description`` (+ optional ``files``) —
      duck-typed for the dry-run engine's ``SubTask`` dataclass.

Analysis procedure (all stdlib):

    1. File paths in task context: regex over the task text plus the
       explicit ``files`` field. Path-like tokens with known extensions
       (py, md, yaml, json, toml, ...) are treated as file references.
    2. Python files via ``ast``: top-level defined symbols (functions,
       classes, module-level assignments) build a symbol->file index;
       task texts mentioning a defined symbol (word-boundary match,
       minimum length 6) inherit the defining file(s).
    3. Markdown/YAML files via regex: existing ``.md``/``.markdown``/
       ``.yaml``/``.yml`` files inside a write set are scanned for file
       references — inline text, fenced code blocks and YAML frontmatter
       are covered by one normalized pass (all are plain text to the
       regex).
    4. Import-graph relationships via ``scripts.lib.analysis``:
       ``FileAffinityAnalyzer`` resolves which write-set files import
       each other.

Conflict semantics (conservative, fail-closed — documented for the
harness consumer):

    - hard overlap: both tasks' write sets contain the same file.
    - coupling: an import edge (``a.py`` imports ``b.py``) or a doc
      reference edge (``docs/x.md`` mentions ``b.py``) connects the two
      write sets. Reported with the linking file pair(s) so the caller
      can sequentialize or order the affected tasks.

Performance note: the symbol index parses every project ``*.py`` file
once per call. There is no global cache on purpose — results must stay
correct while the session edits files. Repository scale (a few hundred
files) stays well under a second with the stdlib parser.
"""
from __future__ import annotations

import ast
import re
from collections.abc import Iterable
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .analysis import FileAffinityAnalyzer

__all__ = [
    "BOUNDARY_NOTE",
    "check_file_overlap",
    "extract_file_references",
    "format_overlap_report",
]

# Documented enforcement boundary: analysis here, enforcement harness-side.
BOUNDARY_NOTE = (
    "Boundary: static analysis only — real enforcement (call before actual "
    "dispatch) is harness-side; agent-meta ships the analysis plus the "
    "dry-run integration in tests/orchestration/dry_run/engine.py."
)

KNOWN_FILE_EXTENSIONS = (
    "py", "md", "markdown", "yaml", "yml", "json", "toml", "cfg", "ini",
    "txt", "sh", "mjs", "js", "ts", "html", "css", "xml", "rst", "csv",
    "example",
)

# Path-like token with a known extension: "scripts/lib/config.py",
# "docs/x.md", ".claude/skills/foo/SKILL.md", "README.md", backslash
# paths are normalized afterwards. Trailing punctuation is not part of
# the character class, so "config.py." matches as "config.py".
_FILE_REF_RE = re.compile(
    r"[A-Za-z0-9_.\-/\\]+\.(?:" + "|".join(KNOWN_FILE_EXTENSIONS) + r")\b",
    re.IGNORECASE,
)

# Files scanned with the Markdown/YAML reference pass (issue #266:
# "Markdown/YAML via Regex — Dateireferenzen, Code-Fences,
# Frontmatter-Pfade"). Frontmatter and fenced blocks are plain text to
# the regex, so a single pass covers all three.
_DOC_EXTENSIONS = frozenset({"md", "markdown", "yaml", "yml"})

_PYTHON_SUFFIX = ".py"

# Symbols shorter than this are too generic to map from task prose
# ("Path", "re", "main", ...); longer names (or precise constants like
# "INTENT_MAP") are safe word-boundary matches.
_SYMBOL_MIN_LENGTH = 6

# Files larger than 1 MB are skipped for AST/doc analysis (safety bound).
_MAX_FILE_BYTES = 1_000_000

# Directories excluded from the project-wide symbol index. "external"
# holds third-party submodules — their symbols must never leak into
# this project's affinity map.
_INDEX_SKIP_DIRS = frozenset({"__pycache__", "external", "node_modules", "venv"})

_ID_KEYS = ("id", "task_id", "name")
_TEXT_KEYS = ("description", "task_description", "task", "text")


@dataclass(frozen=True)
class TaskDescriptor:
    """Normalized task input (accepted input shapes: module docstring)."""

    id: str
    text: str
    files: tuple[str, ...] = ()


def extract_file_references(text: str) -> list[str]:
    """Extract file paths from free task text (regex pass, see module doc).

    Returns a de-duplicated, order-preserving list of references with
    backslashes normalized to forward slashes.
    """
    refs: list[str] = []
    for match in _FILE_REF_RE.findall(text or ""):
        ref = match.replace("\\", "/")
        if ref not in refs:
            refs.append(ref)
    return refs


def format_overlap_report(overlap: dict[str, Any]) -> str:
    """Render a ``check_file_overlap`` result as a Markdown summary.

    Includes the enforcement-boundary note (see ``BOUNDARY_NOTE``) so
    reports never suggest this module dispatches anything itself.
    """
    safe = overlap.get("safe", [])
    conflicts = overlap.get("conflict", [])
    lines = ["**File Affinity Check** (static analysis, issue #266)"]
    safe_str = ", ".join(f"`{task_id}`" for task_id in safe) or "—"
    lines.append(f"- Safe for parallel dispatch: {safe_str}")
    if conflicts:
        for task_a, task_b, files in conflicts:
            files_str = ", ".join(f"`{f}`" for f in files) or "—"
            lines.append(f"- Conflict: `{task_a}` ↔ `{task_b}` — {files_str}")
    else:
        lines.append("- Conflicts: none")
    lines.append(f"_{BOUNDARY_NOTE}_")
    return "\n".join(lines)


def check_file_overlap(
    tasks: Iterable[Any] | None,
    project_root: Path | str | None = None,
) -> dict[str, Any]:
    """Static file-affinity check before parallel dispatch (issue #266).

    Args:
        tasks: Iterable of task inputs (``str`` | ``dict`` | duck-typed
            task object, see module docstring). A single ``str``/``dict``
            is accepted as a one-element list. ``None`` yields no tasks.
        project_root: Project used for AST symbol indexing, doc-file
            reference parsing and import-graph resolution. Defaults to
            the current working directory (harness and the dry-run
            engine both run from the project root).

    Returns:
        Dict with exactly the keys required by issue #266:
        ``{"safe": [task_id, ...], "conflict": [(task_a, task_b, [files]), ...]}``.
        Deterministic: "safe" preserves input order; "conflict" is in
        ascending pair order (i < j, input order) with sorted file
        lists. Conflicted task ids never appear in "safe".

    Raises:
        TypeError: for items that are neither ``str``, ``dict`` nor an
            object exposing an id-ish or text-ish attribute.
    """
    descriptors = _normalize_tasks(tasks)
    root = Path(project_root) if project_root else Path.cwd()
    context = _ProjectContext(root)

    # Write sets: explicit files + file references from text + files
    # defining a symbol named in the text (module docstring, steps 1-2).
    write_sets: list[list[str]] = []
    for task in descriptors:
        files: list[str] = list(task.files)
        for ref in extract_file_references(task.text):
            if ref not in files:
                files.append(ref)
        for rel in context.resolve_symbol_files(task.text):
            if rel not in files:
                files.append(rel)
        write_sets.append(files)

    # Coupling edges over the union of all write sets (steps 3-4).
    union = sorted({ref for files in write_sets for ref in files})
    import_edges: dict[str, set[str]] = {
        file_path: set(deps) for file_path, deps in context.import_dependencies(union).items()
    }
    doc_edges: dict[str, set[str]] = {}
    for doc_file in union:
        refs = _extract_doc_references(root, doc_file)
        if refs:
            doc_edges[doc_file] = set(refs)

    conflicts: list[tuple[str, str, list[str]]] = []
    conflicted_ids: set[str] = set()
    for i, task_a in enumerate(descriptors):
        for j in range(i + 1, len(descriptors)):
            link = _pair_conflict_files(
                write_sets[i], write_sets[j], import_edges, doc_edges
            )
            if link:
                conflicts.append((task_a.id, descriptors[j].id, link))
                conflicted_ids.update((task_a.id, descriptors[j].id))

    safe = [task.id for task in descriptors if task.id not in conflicted_ids]
    return {"safe": safe, "conflict": conflicts}


def _as_file_tuple(files: Any) -> tuple[str, ...]:
    """Coerce a ``files`` input (str | iterable) into a normalized tuple."""
    if not files:
        return ()
    if isinstance(files, str):
        files = [files]
    result: list[str] = []
    for item in files:
        ref = str(item).replace("\\", "/")
        if ref and ref not in result:
            result.append(ref)
    return tuple(result)


def _normalize_tasks(tasks: Iterable[Any] | None) -> list[TaskDescriptor]:
    """Normalize all supported task input shapes into ``TaskDescriptor``."""
    if tasks is None:
        return []
    if isinstance(tasks, (str, dict, TaskDescriptor)):
        tasks = [tasks]
    normalized: list[TaskDescriptor] = []
    for position, task in enumerate(tasks, start=1):
        if isinstance(task, str):
            normalized.append(TaskDescriptor(id=f"task_{position}", text=task))
            continue
        if isinstance(task, dict):
            task_id = next(
                (str(task[key]) for key in _ID_KEYS if task.get(key)), f"task_{position}"
            )
            text = next(
                (str(task[key]) for key in _TEXT_KEYS if task.get(key)), ""
            )
            normalized.append(
                TaskDescriptor(id=task_id, text=text, files=_as_file_tuple(task.get("files")))
            )
            continue
        # Duck-typed objects (e.g. the dry-run engine's SubTask).
        has_id = any(getattr(task, key, None) for key in _ID_KEYS)
        has_text = any(getattr(task, key, None) for key in _TEXT_KEYS)
        has_files = bool(getattr(task, "files", None))
        if not (has_id or has_text or has_files):
            raise TypeError(f"Unsupported task input: {task!r}")
        task_id = next(
            (str(getattr(task, key)) for key in _ID_KEYS if getattr(task, key, None)),
            f"task_{position}",
        )
        text = next(
            (str(getattr(task, key)) for key in _TEXT_KEYS if getattr(task, key, None)),
            "",
        )
        normalized.append(
            TaskDescriptor(
                id=task_id, text=text, files=_as_file_tuple(getattr(task, "files", ()))
            )
        )
    return normalized


def _pair_conflict_files(
    files_a: list[str],
    files_b: list[str],
    import_edges: dict[str, set[str]],
    doc_edges: dict[str, set[str]],
) -> list[str]:
    """Return the sorted conflicting/linking files between two write sets.

    Hard overlap (same file in both sets) wins; otherwise import edges
    and doc-reference edges contribute the linking file pair(s).
    """
    set_a, set_b = set(files_a), set(files_b)
    link: set[str] = set_a & set_b
    if not link:
        # Import edges: a.py imports b.py couples BOTH endpoints.
        for a in set_a:
            for b in import_edges.get(a, ()):
                if b in set_b:
                    link.update((a, b))
        for a in set_b:
            for b in import_edges.get(a, ()):
                if b in set_a:
                    link.update((a, b))
        # Doc-reference edges: a doc referencing a file couples both.
        for doc, refs in doc_edges.items():
            if doc in set_a:
                hits = [ref for ref in refs if ref in set_b]
                if hits:
                    link.update(hits)
                    link.add(doc)
            elif doc in set_b:
                hits = [ref for ref in refs if ref in set_a]
                if hits:
                    link.update(hits)
                    link.add(doc)
    return sorted(link)


def _extract_doc_references(project_root: Path, doc_file: str) -> list[str]:
    """File references inside an existing Markdown/YAML file (one pass)."""
    path = project_root / doc_file
    if path.suffix.lower().lstrip(".") not in _DOC_EXTENSIONS:
        return []
    try:
        if path.stat().st_size > _MAX_FILE_BYTES:
            return []
        content = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return extract_file_references(content)


class _ProjectContext:
    """Per-call project view: symbol index + import analyzer (lazy builds).

    Built once per ``check_file_overlap`` call — no module-level cache,
    so results stay correct while the session edits files (module
    docstring, performance note).
    """

    def __init__(self, project_root: Path) -> None:
        self.project_root = project_root
        self._analyzer: FileAffinityAnalyzer | None = None
        self._symbols: dict[str, list[str]] | None = None
        self._symbol_re: re.Pattern[str] | None = None

    def resolve_symbol_files(self, text: str) -> list[str]:
        """Project files defining a top-level symbol named in ``text``."""
        if not text:
            return []
        if self._symbols is None:
            self._build_symbol_index()
        if self._symbol_re is None or self._symbols is None:
            return []
        files: list[str] = []
        for match in sorted({m.group(0) for m in self._symbol_re.finditer(text)}):
            for rel in self._symbols.get(match, []):
                if rel not in files:
                    files.append(rel)
        return files

    def import_dependencies(self, file_paths: Iterable[str]) -> dict[str, list[str]]:
        """Import-graph edges (file -> imported project files) among inputs."""
        py_files = [f for f in file_paths if f.endswith(_PYTHON_SUFFIX)]
        if not py_files:
            return {}
        if self._analyzer is None:
            self._analyzer = FileAffinityAnalyzer(self.project_root)
        return self._analyzer.get_file_dependencies(py_files)

    def _build_symbol_index(self) -> None:
        """Parse project Python files into a symbol -> [relative paths] map."""
        symbols: dict[str, set[str]] = {}
        for py_file in self._iter_project_files(_PYTHON_SUFFIX):
            rel = self._relative_path(py_file)
            if rel is None:
                continue
            tree = _parse_python(py_file)
            if tree is None:
                continue
            for name in _extract_defined_symbols(tree):
                if len(name) >= _SYMBOL_MIN_LENGTH:
                    symbols.setdefault(name, set()).add(rel)
        self._symbols = {name: sorted(paths) for name, paths in symbols.items()}
        if not self._symbols:
            self._symbol_re = None
            return
        alternatives = "|".join(
            re.escape(name) for name in sorted(self._symbols, key=lambda n: (-len(n), n))
        )
        self._symbol_re = re.compile(r"\b(?:" + alternatives + r")\b")

    def _iter_project_files(self, suffix: str) -> Iterable[Path]:
        """Yield project files with ``suffix``, skipping junk/large files."""
        for path in self.project_root.rglob(f"*{suffix}"):
            if not path.is_file():
                continue
            parts = set(path.parts)
            if parts & _INDEX_SKIP_DIRS:
                continue
            if any(part.startswith(".") for part in path.parts[:-1]):
                continue
            try:
                if path.stat().st_size > _MAX_FILE_BYTES:
                    continue
            except OSError:
                continue
            yield path

    def _relative_path(self, path: Path) -> str | None:
        """Project-relative POSIX path, or None when outside the root."""
        try:
            return path.relative_to(self.project_root).as_posix()
        except ValueError:
            return None


def _parse_python(path: Path) -> ast.Module | None:
    """Parse a Python file with ``ast``; None on any parse/IO problem."""
    try:
        source = path.read_text(encoding="utf-8", errors="replace")
        return ast.parse(source, filename=str(path))
    except (OSError, SyntaxError, UnicodeDecodeError, ValueError):
        return None


def _extract_defined_symbols(tree: ast.Module) -> list[str]:
    """Top-level defined symbol names (functions, classes, assignments).

    Only module-level definitions are indexed: nested/conditional defs
    are too noisy for prose matching, and dunder names (``__all__``,
    ``__version__``) are excluded.
    """
    names: list[str] = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
            names.append(node.name)
        elif isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name):
                    names.append(target.id)
        elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name):
            names.append(node.target.id)
    return [name for name in names if not name.startswith("__")]
