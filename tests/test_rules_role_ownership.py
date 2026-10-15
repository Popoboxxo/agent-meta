"""IC-18 no. 10 (Task 1.18, AC-49 part): rule owner lines follow the ActiveSet.

``security-paved-roads``, ``threat-model-4-questions`` and ``a2a-delegation-gates``
name owner roles; those lines sit under ``{{#if ROLE_<ROLE>_ACTIVE}}`` (IC-03
conditionals are resolved in the rules path). With every role active the
rendered rules are unchanged.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from scripts.lib.active_set import compute_active_set
from tests.active_set_render import (
    REPO_ROOT,
    default_config,
    fixture_config,
    synced_project,
    tiers_on_config,
)

_RULES = ("security-paved-roads", "threat-model-4-questions", "a2a-delegation-gates")
_KNOWN = sorted(
    yaml.safe_load((REPO_ROOT / "config" / "role-defaults.yaml").read_text(encoding="utf-8"))["roles"],
    key=len, reverse=True)
_TOKEN = re.compile(r"(?<![\w-])(" + "|".join(re.escape(r) for r in _KNOWN) + r")(?![\w-])")


@pytest.fixture(scope="module")
def projects(tmp_path_factory):
    out = {}
    for name, config in (("p10", fixture_config("p10")), ("default", default_config()),
                         ("all", tiers_on_config())):
        out[name] = (synced_project(tmp_path_factory, config), config)
    return out


def _rule(project: Path, stem: str) -> str:
    return (project / ".claude" / "rules" / f"{stem}.md").read_text(encoding="utf-8")


@pytest.mark.parametrize("stem", _RULES)
def test_p10_rule_names_no_inactive_owner(projects, stem):
    project, config = projects["p10"]
    active = compute_active_set(config, REPO_ROOT, project, warn_sink=[])
    named = set(_TOKEN.findall(_rule(project, stem)))
    assert sorted(named - set(active.roles)) == [], stem


def test_p10_paved_roads_keep_the_block_catalog(projects):
    text = _rule(projects["p10"][0], "security-paved-roads")
    for block in ("auth-flow", "dependency-check", "input-validation", "rate-limiting",
                  "cors-config", "secret-scanning"):
        assert f"| `{block}` |" in text, block
    assert "{{" not in text


_PINNED = REPO_ROOT / "tests" / "fixtures" / "active-set-prose" / "rules-all-active"


@pytest.mark.parametrize("name", ["default", "all"])
@pytest.mark.parametrize("stem", _RULES)
def test_rules_unchanged_when_owners_active(projects, name, stem):
    # Every owner role is active in the default and the all-roles project, so the
    # render equals the pre-change render (pinned from main 8f2ecb2, default project).
    text = _rule(projects[name][0], stem)
    assert text == (_PINNED / f"{stem}.md").read_text(encoding="utf-8")
    assert "keine aktive Eigentümer-Rolle" not in text


@pytest.mark.parametrize("sa,cr,expected", [
    ("true", "true", "Default: `security-auditor`, `code-reviewer`)"),
    ("true", "false", "Default: `security-auditor`)"),
    ("false", "true", "Default: `code-reviewer`)"),
    ("false", "false", "Default: keine aktive Rolle)"),
])
def test_a2a_default_roles_render_for_every_combination(sa, cr, expected):
    from scripts.lib.variables import strip_inactive_conditional_blocks

    source = (REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md").read_text(encoding="utf-8")
    line = next(ln for ln in source.splitlines() if "security-critical-roles" in ln and "Default:" in ln)
    rendered = strip_inactive_conditional_blocks(
        line, {"ROLE_SECURITY_AUDITOR_ACTIVE": sa, "ROLE_CODE_REVIEWER_ACTIVE": cr})
    assert expected in rendered
