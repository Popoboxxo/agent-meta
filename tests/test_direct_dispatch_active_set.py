"""IC-18 no. 7 (Task 1.15, AC-49 part): ``DIRECT_DISPATCH_SECTION`` rows per active role.

Each row of ``templates/direct-dispatch-section.md`` sits under
``{{#if ROLE_<ROLE>_ACTIVE}}``; the builder resolves the conditionals with
``active_set_variables`` so the variable value is final for every consumer
(orchestrator agent and the ``use-orchestrator`` rule).
"""
from __future__ import annotations

import re
from pathlib import Path

from scripts.lib.active_set import compute_active_set
from scripts.lib.config import build_variables
from tests.active_set_render import REPO_ROOT, all_roles, default_config, fixture_config

_ALL_ACTIVE = REPO_ROOT / "tests" / "fixtures" / "active-set-prose" / "direct-dispatch-section-all-active.md"
_ROW_ROLE_RE = re.compile(r"^\|[^|]*\|\s*`([a-z0-9-]+)`\s*\|", re.MULTILINE)


def _section(config: dict, tmp_path: Path) -> str:
    active = compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])
    variables, _ = build_variables(config, REPO_ROOT, tmp_path, active_set=active)
    return variables["DIRECT_DISPATCH_SECTION"]


def test_p10_has_no_row_for_an_inactive_role(tmp_path):
    config = fixture_config("p10")
    active = compute_active_set(config, REPO_ROOT, tmp_path, warn_sink=[])
    rows = _ROW_ROLE_RE.findall(_section(config, tmp_path))
    assert rows, "p10 keeps at least the git/documenter rows"
    assert [r for r in rows if not active.has(r)] == []
    assert "agent-meta-manager" not in rows and "feedback" not in rows


def test_all_active_section_is_byte_identical_to_pre_change(tmp_path):
    config = default_config()
    config["roles"] = all_roles()
    assert _section(config, tmp_path) == _ALL_ACTIVE.read_text(encoding="utf-8")


def test_default_section_is_byte_identical_to_pre_change(tmp_path):
    # All four row roles are active in the default project.
    assert _section(default_config(), tmp_path) == _ALL_ACTIVE.read_text(encoding="utf-8")


def test_no_conditional_marker_leaks(tmp_path):
    for config in (fixture_config("p10"), default_config()):
        assert "{{" not in _section(config, tmp_path)


def test_every_row_is_gated_on_its_role():
    template = (REPO_ROOT / "templates" / "direct-dispatch-section.md").read_text(encoding="utf-8")
    lines = template.splitlines()
    for i, line in enumerate(lines):
        match = _ROW_ROLE_RE.match(line + "\n")
        if not match:
            continue
        flag = "ROLE_%s_ACTIVE" % match.group(1).upper().replace("-", "_")
        assert lines[i - 1] == "{{#if %s}}" % flag, line
        assert lines[i + 1] == "{{/if}}", line
