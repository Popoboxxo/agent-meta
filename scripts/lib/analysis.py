"""AST-based file affinity analysis for parallelization hints.

Analyzes Python source files to find import dependencies between project files.
Used by the Orchestrator to make evidence-based parallelization decisions instead
of relying on LLM guesses.

Activated via project.yaml:
    analysis:
      enabled: true  # default: false

Usage:
    from scripts.lib.analysis import FileAffinityAnalyzer, analyze_project

    analyzer = FileAffinityAnalyzer("/path/to/project")
    deps = analyzer.get_file_dependencies(["scripts/lib/config.py", "scripts/lib/agents.py"])
    hint = analyzer.format_hint(deps)
"""
from __future__ import annotations

import ast
from pathlib import Path


class FileAffinityAnalyzer:
    """Analyzes Python AST imports to find file-to-file dependencies.

    Only uses Python stdlib — no external dependencies required.
    """

    def __init__(self, project_root: Path | str | None = None) -> None:
        self.project_root = Path(project_root) if project_root else Path.cwd()
        # Cache: module_name -> relative_path
        self._module_index: dict[str, str] = {}
        self._index_built = False

    def _build_module_index(self) -> None:
        """Build a mapping from module name to relative file path."""
        if self._index_built:
            return
        for py_file in self.project_root.rglob("*.py"):
            try:
                rel = py_file.relative_to(self.project_root)
                # Convert path to dotted module name: scripts/lib/config.py -> scripts.lib.config
                parts = list(rel.with_suffix("").parts)
                module_name = ".".join(parts)
                self._module_index[module_name] = str(rel)
                # Also index by last component for simple imports
                self._module_index[parts[-1]] = str(rel)
            except ValueError:
                pass
        self._index_built = True

    def _extract_imports(self, filepath: Path) -> list[str]:
        """Extract all imported module names from a Python file.

        Returns list of dotted module names. Skips files with syntax errors.
        """
        try:
            source = filepath.read_text(encoding="utf-8", errors="replace")
            tree = ast.parse(source, filename=str(filepath))
        except (SyntaxError, OSError, UnicodeDecodeError):
            return []

        imports: list[str] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    imports.append(alias.name)
            elif isinstance(node, ast.ImportFrom) and node.module:
                imports.append(node.module)
        return imports

    def _resolve_import(self, import_name: str, relative_to: Path) -> str | None:
        """Try to resolve an import name to a project-relative file path.

        Returns the relative path string if found within the project, else None.
        """
        self._build_module_index()

        # Direct match
        if import_name in self._module_index:
            return self._module_index[import_name]

        # Try suffixes: e.g. "scripts.lib.config" -> "lib.config" -> "config"
        parts = import_name.split(".")
        for i in range(1, len(parts)):
            suffix = ".".join(parts[i:])
            if suffix in self._module_index:
                return self._module_index[suffix]

        return None

    def get_file_dependencies(self, file_list: list[str]) -> dict[str, list[str]]:
        """Return which files in file_list import from other files in file_list.

        Args:
            file_list: List of project-relative file paths (e.g. ["scripts/lib/config.py"]).

        Returns:
            Dict mapping each file to a list of files it depends on (both in file_list).
            Example: {"scripts/lib/agents.py": ["scripts/lib/config.py", "scripts/lib/log.py"]}
        """
        file_set = set(file_list)
        result: dict[str, list[str]] = {}

        for rel_path_str in file_list:
            abs_path = self.project_root / rel_path_str
            if not abs_path.exists() or not rel_path_str.endswith(".py"):
                result[rel_path_str] = []
                continue

            imports = self._extract_imports(abs_path)
            deps: list[str] = []
            for imp in imports:
                resolved = self._resolve_import(imp, abs_path)
                if resolved and resolved in file_set and resolved != rel_path_str:  # noqa: SIM102
                    if resolved not in deps:
                        deps.append(resolved)
            result[rel_path_str] = deps

        return result

    def format_hint(self, dependencies: dict[str, list[str]]) -> str:
        """Format dependency dict as a Markdown summary for the orchestrator.

        Returns a short human-readable hint listing the top 5 most-imported files
        and which files depend on each other (relevant for parallelization).
        """
        if not dependencies:
            return ""

        # Count how often each file is imported
        import_counts: dict[str, int] = {}
        for deps in dependencies.values():
            for dep in deps:
                import_counts[dep] = import_counts.get(dep, 0) + 1

        lines = ["**File Affinity Map** (AST-based, top dependencies):"]
        lines.append("")
        lines.append("| File | Imports | Imported by |")
        lines.append("|------|---------|-------------|")

        # Sort by most-imported first, then alphabetically
        sorted_files = sorted(
            dependencies.keys(),
            key=lambda f: (-import_counts.get(f, 0), f),
        )

        for filepath in sorted_files[:5]:
            deps = dependencies[filepath]
            imported_by = [f for f, d in dependencies.items() if filepath in d]
            deps_str = ", ".join(f"`{d}`" for d in deps[:3]) or "—"
            imported_by_str = ", ".join(f"`{f}`" for f in imported_by[:2]) or "—"
            short = filepath.split("/")[-1]
            lines.append(f"| `{short}` | {deps_str} | {imported_by_str} |")

        if any(v for v in dependencies.values()):
            lines.append("")
            lines.append(
                "_Files with shared imports have potential parallelization conflicts — "
                "check before FANOUT._"
            )

        return "\n".join(lines)


def analyze_project(root: Path) -> dict[str, list[str]]:
    """Analyze all Python files in a project and return their dependencies.

    Entry point for use from sync.py / config.py.

    Args:
        root: Project root directory.

    Returns:
        Dependency dict as returned by FileAffinityAnalyzer.get_file_dependencies().
    """
    analyzer = FileAffinityAnalyzer(root)
    py_files = [
        str(f.relative_to(root))
        for f in root.rglob("*.py")
        if not any(part.startswith(".") for part in f.parts)
        and "__pycache__" not in f.parts
    ]
    return analyzer.get_file_dependencies(py_files)


# ---------------------------------------------------------------------------
# Public module-level API (Issue #275)
# ---------------------------------------------------------------------------

def is_available() -> bool:
    """AST is always available (Python stdlib — no external dependencies)."""
    return True


def analyze_file_dependencies(root: Path) -> dict[str, list[str]]:
    """Parse Python imports in scripts/lib/*.py and return a dependency graph.

    Scans all *.py files under scripts/lib/ and resolves intra-package imports
    to build a directed dependency map.

    Args:
        root: Project root directory.

    Returns:
        Dict mapping each relative file path to a list of relative file paths
        it imports from (restricted to files found in scripts/lib/).
        Example: {"scripts/lib/agents.py": ["scripts/lib/config.py"]}
    """
    scripts_lib = root / "scripts" / "lib"
    if not scripts_lib.exists():
        return {}

    analyzer = FileAffinityAnalyzer(root)
    lib_files = [
        str(f.relative_to(root))
        for f in scripts_lib.glob("*.py")
        if f.is_file()
    ]
    return analyzer.get_file_dependencies(lib_files)


def find_shared_files(changed_files: list[str], root: Path) -> list[str]:
    """Find files that are imported by or import from the given changed files.

    Returns project files that share a dependency relationship with any of
    the changed_files — useful for blast-radius analysis before FANOUT.

    Args:
        changed_files: List of project-relative file paths that changed.
        root: Project root directory.

    Returns:
        Sorted list of project-relative paths that have a dependency
        relationship with at least one file in changed_files (excluding the
        changed files themselves).
    """
    if not changed_files:
        return []

    all_deps = analyze_project(root)
    changed_set = set(changed_files)
    shared: set[str] = set()

    for filepath, deps in all_deps.items():
        if filepath in changed_set:
            # Files imported by a changed file
            for dep in deps:
                if dep not in changed_set:
                    shared.add(dep)
        else:
            # Files that import a changed file
            if any(dep in changed_set for dep in deps):
                shared.add(filepath)

    return sorted(shared)
