"""Import-acyclicity guard for scripts/lib (Issue #478).

Builds the module graph from TOP-LEVEL relative imports and TOP-LEVEL
absolute ``lib.*`` imports (stdlib ``ast``, Tarjan SCC) and asserts the
graph is a DAG: no strongly connected component with more than one module.
Absolute imports are collected because the #481 strangler refactor moved
``lib/cli_commands.py`` and ``lib/sync_pipeline.py`` to the absolute
``from lib.x import ...`` style — with relative-only collection both
modules would be edge-less nodes and the guard vacuously green.
Function-local (lazy) imports are deliberately
excluded — they carry no import-time cycle; remaining lazy-carried soft
cycles are tracked and resolved in Issue #478's follow-up work.

This is the permanent guard introduced by the #478 retargeting: the historic
agents ↔ config ↔ viz cycles were already dissolved (Issue #561/#565 agent
split); the guard keeps it that way for every future refactor.
"""

import ast
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = REPO_ROOT / "scripts"
LIB_DIR = SCRIPTS_DIR / "lib"
sys.path.insert(0, str(SCRIPTS_DIR))


def _iter_lib_modules():
    """Yield (module_name, path) for every Python module under scripts/lib.

    Module names are ``lib.*``-dotted (e.g. ``lib.frontmatter``,
    ``lib.consistency.report``); package ``__init__.py`` files map to their
    package name.
    """
    for path in sorted(LIB_DIR.rglob("*.py")):
        rel = path.relative_to(LIB_DIR)  # e.g. foo.py / consistency/report.py
        parts = ["lib"] + list(rel.with_suffix("").parts)
        if parts[-1] == "__init__":
            parts = parts[:-1]
        yield ".".join(parts), path


def _top_level_lib_imports(tree: ast.Module) -> list[tuple[int, str | None, str | None]]:
    """Top-level relative and absolute ``lib.*`` imports as (level, module,
    alias_name) triples.

    ``from .x import y``      → (1, "x", "y")
    ``from . import x``       → (1, None, "x")
    ``from ..x.y import z``   → (2, "x.y", "z")
    ``from lib.x import y``   → (0, "lib.x", "y")
    ``import lib.x``          → (0, "lib.x", None)

    Absolute non-lib imports (stdlib/third-party) are ignored — they cannot
    take part in a lib-internal cycle. ``if TYPE_CHECKING:`` blocks are
    skipped — type-only back-edges are not import-time edges.
    """
    found: list[tuple[int, str | None, str | None]] = []
    for node in tree.body:  # top-level statements only
        if isinstance(node, ast.ImportFrom) and (
            node.level > 0 or (node.module or "").startswith("lib")
        ):
            for alias in node.names:
                found.append((node.level, node.module, alias.name))
        elif isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "lib" or alias.name.startswith("lib."):
                    found.append((0, alias.name, None))
        elif (
            isinstance(node, ast.If)
            and isinstance(node.test, ast.Name)
            and node.test.id == "TYPE_CHECKING"
        ):
            continue
    return found


def _exists_as_module(mod: str) -> bool:
    """True when ``mod`` (lib.* form) exists as module or package on disk."""
    parts = mod.split(".")
    if parts[0] != "lib":
        return False
    base = LIB_DIR.joinpath(*parts[1:])
    return (base.with_suffix(".py")).exists() or (base / "__init__.py").exists()


def _build_graph() -> dict[str, set[str]]:
    graph: dict[str, set[str]] = {}
    for mod_name, path in _iter_lib_modules():
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        parts = mod_name.split(".")
        is_package = path.name == "__init__.py"
        package_parts = parts if is_package else parts[:-1]
        deps: set[str] = set()
        for level, module, alias in _top_level_lib_imports(tree):
            if level == 0:
                # Absolute ``lib.*`` import: the module path is already
                # fully qualified, anchored at the lib package root.
                base_parts = []
                candidate_parts = module.split(".") if module else [alias or ""]
            else:
                # Anchor relative to the importer's package, walking up
                # (level - 1) package levels — proper relative-import semantics
                # for subpackages (consistency/, context_templates/, se_export/).
                base_parts = package_parts[: len(package_parts) - (level - 1)]
                candidate_parts = base_parts + (
                    module.split(".") if module else [alias]
                )
            # Trim trailing components until an existing module boundary is
            # found (``from .x.y import z`` may import through a package).
            while len(candidate_parts) >= 1:
                candidate = ".".join(candidate_parts)
                if _exists_as_module(candidate):
                    if candidate != mod_name:
                        deps.add(candidate)
                    break
                if len(candidate_parts) <= len(base_parts):
                    break  # nothing resolvable under the anchor — skip
                candidate_parts = candidate_parts[:-1]
        graph[mod_name] = deps
    return graph


def _strongly_connected_components(graph: dict[str, set[str]]) -> list[set[str]]:
    """Tarjan SCC over the top-level import graph (recursive strongconnect —
    the lib graph is shallow, well below Python's recursion limit)."""
    index_counter = [0]
    stack: list[str] = []
    lowlink: dict[str, int] = {}
    index: dict[str, int] = {}
    on_stack: set[str] = set()
    result: list[set[str]] = []

    def strongconnect(node: str) -> None:
        index[node] = lowlink[node] = index_counter[0]
        index_counter[0] += 1
        stack.append(node)
        on_stack.add(node)

        for successor in sorted(graph.get(node, ())):
            if successor not in index:
                strongconnect(successor)
                lowlink[node] = min(lowlink[node], lowlink[successor])
            elif successor in on_stack:
                lowlink[node] = min(lowlink[node], index[successor])

        if lowlink[node] == index[node]:
            component: set[str] = set()
            while True:
                member = stack.pop()
                on_stack.discard(member)
                component.add(member)
                if member == node:
                    break
            result.append(component)

    for node in sorted(graph):
        if node not in index:
            strongconnect(node)
    return result


def test_top_level_import_graph_is_acyclic():
    graph = _build_graph()
    sccs = _strongly_connected_components(graph)
    cycles = [sorted(scc) for scc in sccs if len(scc) > 1]
    assert not cycles, (
        "Import-time cycles detected in scripts/lib (top-level relative/absolute "
        f"lib.* imports): {cycles}. Break the cycle with a leaf/orchestration module "
        "(see tests/test_import_acyclicity.py docstring, Issue #478)."
    )


def test_guard_covers_the_lib_tree():
    """Sanity: the guard must actually see the lib modules (not silently
    scan an empty tree after a layout change)."""
    modules = {name for name, _ in _iter_lib_modules()}
    assert "lib.frontmatter" in modules
    assert "lib.io" in modules
    assert "lib.consistency.frontmatter" in modules
    assert "lib.context_templates.builder" in modules
    assert len(modules) > 40


def test_known_edges_are_resolved():
    """Sanity: relative and absolute ``lib.*`` imports must resolve to real
    lib modules (a silent resolution failure would make the acyclicity check
    vacuous)."""
    graph = _build_graph()
    assert "lib.frontmatter" in graph["lib.pipelines"]
    assert "lib.io" in graph["lib.pipelines"]
    assert "lib.consistency.report" in graph["lib.consistency.crossrefs"]
    assert "lib.frontmatter" in graph["lib.context_templates.builder"]
    # Non-vacuity for the absolute-import modules (Issue #481 review M1):
    # before absolute-import collection both were edge-less nodes and the
    # cycle check never actually saw their dependency edges.
    assert graph["lib.cli_commands"], (
        "lib.cli_commands has no resolved top-level edges — absolute "
        "lib.* imports are no longer collected?"
    )
    assert "lib.sync_pipeline" in graph["lib.cli_commands"]
    assert graph["lib.sync_pipeline"], (
        "lib.sync_pipeline has no resolved top-level edges — absolute "
        "lib.* imports are no longer collected?"
    )
