"""Regression test for issue #715: full-mode project-metadata.md must show
the actual {{PROJECT_STRUCTURE}} content, not just the generic lazy-load
pointer -- while compact mode keeps exactly the #437 pointer-only behavior.

NOTE (plan-test defect corrected): the plan's _render called only
resolve_conditionals, which leaves {{PROJECT_STRUCTURE}} an unsubstituted
literal so `"src/" in rendered` could never pass. This mirrors the real
render pipeline order (build(): resolve_conditionals -> resolve_variables)
so the test actually verifies the VALUE appears in full mode.
"""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.context_templates.builder import TemplateBuilder
from lib.frontmatter import strip_frontmatter

_PARTIAL_PATH = REPO_ROOT / "templates" / "context" / "partials" / "project-metadata.md"


def _render(variables: dict) -> str:
    body = strip_frontmatter(_PARTIAL_PATH.read_text(encoding="utf-8"))
    builder = TemplateBuilder(REPO_ROOT / "templates" / "context")
    body = builder.resolve_conditionals(body, variables)
    return builder.resolve_variables(body, variables)


_BASE_VARS = {
    "COMPACT_MODE": "false",
    "PROJECT_NAME": "demo", "PREFIX": "dm", "PLATFORM": "CLI",
    "PROJECT_DESCRIPTION": "demo project", "ENTRY_POINT_PATTERN": "main.py",
    "KEY_PATTERNS": "- none", "CODE_CONVENTIONS": "- none",
    "BUILD_COMMAND": "make build", "TEST_COMMAND": "make test",
    "DEV_STACK_START": "-", "DEV_STACK_RELOAD": "-",
    "REQ_CATEGORIES_LIST": "- none",
}


def test_full_mode_renders_actual_project_structure_when_set():
    variables = {**_BASE_VARS, "PROJECT_STRUCTURE": "src/\n  main.py\ntests/\n  test_main.py"}
    rendered = _render(variables)
    assert "src/" in rendered
    assert "test_main.py" in rendered
    # The pointer line stays too (#437 discoverability, unrelated to this fix).
    assert "> Struktur: siehe Verzeichnisstruktur im Repo" in rendered


def test_full_mode_falls_back_to_pointer_only_when_structure_unset():
    variables = {**_BASE_VARS, "PROJECT_STRUCTURE": ""}
    rendered = _render(variables)
    assert "> Struktur: siehe Verzeichnisstruktur im Repo" in rendered
    assert "**Verzeichnisstruktur:**" not in rendered


def test_compact_mode_untouched_by_437_pointer_contract():
    variables = {**_BASE_VARS, "COMPACT_MODE": "true",
                 "PROJECT_STRUCTURE": "src/\n  main.py"}
    rendered = _render(variables)
    assert "> Struktur: siehe Verzeichnisstruktur im Repo" in rendered
    assert "src/\n  main.py" not in rendered  # full-mode-only addition must not leak
