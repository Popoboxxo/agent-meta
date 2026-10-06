"""Locking regression test for issue #844 AC-6 (newline-squashing investigation).

The issue alleged that `{{CODE_CONVENTIONS}}`/`{{KEY_PATTERNS}}` bullet lists
collapse to a single line when `templates/context/partials/project-metadata.md`
renders. The #844 spec (SPEC-844-COMPRESS-ROOT-CONTEXT-2026-10-06, § 5 AC-6)
found this NOT reproducible on `main`: both variables render multi-line, one
bullet per line, in both COMPACT_MODE states. This test does not fix anything —
it locks in the current, correct behavior as a regression guard.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.config import build_variables, load_config
from lib.context_templates.builder import TemplateBuilder


def _render_project_metadata(mode: str) -> str:
    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    config["context_file"] = {"mode": mode}
    variables, _ = build_variables(config, REPO_ROOT)
    builder = TemplateBuilder(REPO_ROOT / "templates" / "context" / "partials")
    return builder.build("project-metadata", variables)


def _bullet_lines(rendered: str, section_heading: str) -> list[str]:
    lines = rendered.splitlines()
    start = lines.index(section_heading) + 1
    bullets = []
    for line in lines[start:]:
        stripped = line.strip()
        if stripped.startswith("- "):
            bullets.append(stripped)
        elif bullets:
            break  # bullet block ended
    return bullets


def test_code_conventions_renders_one_bullet_per_line_compact():
    rendered = _render_project_metadata("compact")
    bullets = _bullet_lines(rendered, "## Code-Konventionen")
    assert len(bullets) >= 5
    assert "; " not in "\n".join(bullets)


def test_code_conventions_renders_one_bullet_per_line_full():
    rendered = _render_project_metadata("full")
    bullets = _bullet_lines(rendered, "## Code-Konventionen")
    assert len(bullets) >= 5
    assert "; " not in "\n".join(bullets)


def test_key_patterns_renders_one_bullet_per_line_both_modes():
    for mode in ("compact", "full"):
        rendered = _render_project_metadata(mode)
        lines = rendered.splitlines()
        start = lines.index("**Besondere Patterns:**") + 1
        bullets = [l for l in lines[start:start + 4] if l.strip().startswith("- ")]
        assert len(bullets) == 4, f"mode={mode}: {bullets}"
