"""Regression guards for template defects #932, #933, #934, #935."""

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_AGENTS = sorted((_ROOT / "agents").rglob("*.md"))


def _grep(pattern: str) -> list[str]:
    rx = re.compile(pattern, re.M)
    return [f"{p.relative_to(_ROOT)}" for p in _AGENTS if rx.search(p.read_text(encoding="utf-8"))]


def test_933_no_unresolvable_role_placeholder():
    assert _grep(r"\{\{ROLE\}\}") == []


def test_934_no_windows_only_py_launcher_in_role_templates():
    assert _grep(r"^py ") == []


def test_935_no_nonexistent_spec_section_references():
    assert _grep(r"§7\.[12]") == []


def test_932_orchestrator_reference_resolves_through_rel_path():
    orch = (_ROOT / "agents" / "1-generic" / "orchestrator.md").read_text(encoding="utf-8")
    refs = re.findall(r"`([^`]*_wf-orchestrator-reference\.md)`", orch)
    assert refs, "orchestrator must still point at the lazy-load reference"
    for ref in refs:
        assert ref.startswith("{{AGENT_META_REL_PATH}}agents/1-generic/"), ref
        assert (_ROOT / ref.removeprefix("{{AGENT_META_REL_PATH}}")).is_file(), ref
