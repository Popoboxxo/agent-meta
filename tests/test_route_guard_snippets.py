"""Guard regression: the route guard also covers ``snippets/**/*.md`` (Spec A6).

Snippets are inlined into agent prompts at sync time, so they sit on the same
routing-source-of-truth boundary as the templates: a route table or a
``roleA → roleB`` chain must not be seeded there either.

This module is the scope/regression complement to
``tests/test_no_role_routes_in_templates.py``. The detector logic and the
``D-*`` exemptions are intentionally reused unchanged — this test only proves
that every snippet file is actually scanned and that the snippet corpus stays
free of uncovered routing constructs.
"""

from __future__ import annotations

from pathlib import Path

from tests.test_no_role_routes_in_templates import (
    _SCOPE_GLOBS,
    boundary_lines,
    classify_line,
    iter_scope_files,
    load_pipeline_ids,
    load_roles,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
_SNIPPET_GLOB = "snippets/**/*.md"


def _snippet_files() -> list[Path]:
    """All markdown snippets, nested subdirectories included."""
    return sorted(REPO_ROOT.glob(_SNIPPET_GLOB))


def test_snippet_corpus_is_not_empty() -> None:
    """Guard against a vacuous pass if the glob or directory layout changes."""
    assert _snippet_files(), f"no snippet markdown files matched {_SNIPPET_GLOB!r}"


def test_scope_globs_include_snippets() -> None:
    """The guard scope must name the snippet corpus explicitly (A6)."""
    assert _SNIPPET_GLOB in _SCOPE_GLOBS


def test_all_snippet_files_are_scanned_by_the_guard() -> None:
    """Every snippet on disk must be reachable through ``iter_scope_files``."""
    scoped = {path.resolve() for path in iter_scope_files()}
    missing = [
        path.relative_to(REPO_ROOT).as_posix()
        for path in _snippet_files()
        if path.resolve() not in scoped
    ]
    assert missing == [], f"snippet files outside the route-guard scope: {missing}"


def test_no_uncovered_routing_constructs_in_snippets() -> None:
    """The snippet corpus contains no uncovered ``T-*`` routing construct."""
    roles = load_roles()
    pipeline_ids = load_pipeline_ids()
    findings: list[str] = []
    for path in _snippet_files():
        rel = path.relative_to(REPO_ROOT).as_posix()
        text = path.read_text(encoding="utf-8")
        boundary = boundary_lines(text)
        for number, line in enumerate(text.splitlines(), start=1):
            for kind, reasons in classify_line(
                line,
                roles=roles,
                pipeline_ids=pipeline_ids,
                is_boundary=number in boundary,
                workflow_file=False,
            ):
                if not reasons:
                    findings.append(f"{rel}:{number}: {kind}: {line.strip()}")
    assert findings == [], "Uncovered routing constructs in snippets:\n" + "\n".join(
        findings
    )
