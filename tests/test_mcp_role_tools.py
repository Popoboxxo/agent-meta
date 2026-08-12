"""Regression tests for MCP tool propagation into agent frontmatter.

Issue #467: `.claude/rules/mcp-playwright.md` documents a full browser toolset
for the e2e-tester role, but nothing ever wrote those tools into the generated
`.claude/agents/e2e-tester.md` frontmatter -- so the agent started every session
with base tools only and browser delegations failed structurally.

`resolve_mcp_tools_for_role()` closes that gap: a role opts in via
`mcp-servers:` in role-defaults.yaml, and only servers actually active for the
project contribute their `tools.allowed` entries.
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.agents import (  # noqa: E402
    append_frontmatter_tools,
    resolve_mcp_tools_for_role,
)
from lib.roles import load_roles_config  # noqa: E402


def _config(**extra):
    cfg = {"mcp-servers": ["playwright"]}
    cfg.update(extra)
    return cfg


# ---------------------------------------------------------------------------
# Role -> MCP server opt-in
# ---------------------------------------------------------------------------

def test_e2e_tester_opts_into_playwright_in_role_defaults():
    roles = load_roles_config(_REPO_ROOT)["roles"]
    assert "playwright" in roles["e2e-tester"].get("mcp-servers", [])


def test_active_server_yields_namespaced_tools():
    tools = resolve_mcp_tools_for_role("e2e-tester", _config(), _REPO_ROOT)
    assert "mcp__playwright__browser_navigate" in tools
    assert "mcp__playwright__browser_snapshot" in tools
    assert all(t.startswith("mcp__playwright__") for t in tools)


def test_blocked_tools_never_leak_in():
    tools = resolve_mcp_tools_for_role("e2e-tester", _config(), _REPO_ROOT)
    for blocked in ("browser_evaluate", "browser_run_code_unsafe",
                    "browser_file_upload", "browser_handle_dialog"):
        assert f"mcp__playwright__{blocked}" not in tools


def test_inactive_server_contributes_nothing():
    # playwright is enabled-by-default: false -- without an explicit opt-in in
    # project.yaml the role must not get browser tools.
    tools = resolve_mcp_tools_for_role("e2e-tester", {"mcp-servers": []}, _REPO_ROOT)
    assert tools == []


def test_role_without_opt_in_gets_nothing():
    tools = resolve_mcp_tools_for_role("developer", _config(), _REPO_ROOT)
    assert tools == []


def test_project_override_wins_over_role_defaults():
    cfg = _config(**{"mcp-role-overrides": {"e2e-tester": []}})
    assert resolve_mcp_tools_for_role("e2e-tester", cfg, _REPO_ROOT) == []

    cfg = _config(**{"mcp-role-overrides": {"developer": ["playwright"]}})
    tools = resolve_mcp_tools_for_role("developer", cfg, _REPO_ROOT)
    assert "mcp__playwright__browser_navigate" in tools


def test_unknown_role_is_not_an_error():
    assert resolve_mcp_tools_for_role("does-not-exist", _config(), _REPO_ROOT) == []


# ---------------------------------------------------------------------------
# Frontmatter merge
# ---------------------------------------------------------------------------

_FM = """---
name: e2e-tester
tools:
- Bash
- Read
---

body
"""


def test_tools_are_appended_after_existing_ones():
    out = append_frontmatter_tools(_FM, ["mcp__playwright__browser_click"])
    assert "mcp__playwright__browser_click" in out
    assert "Bash" in out and "Read" in out
    assert out.endswith("body\n")


def test_append_is_idempotent():
    once = append_frontmatter_tools(_FM, ["mcp__playwright__browser_click"])
    twice = append_frontmatter_tools(once, ["mcp__playwright__browser_click"])
    assert once == twice


def test_wildcard_tools_are_left_alone():
    content = "---\nname: x\ntools: '*'\n---\n\nbody\n"
    assert append_frontmatter_tools(content, ["mcp__playwright__browser_click"]) == content


def test_missing_tools_field_is_left_alone():
    content = "---\nname: x\n---\n\nbody\n"
    assert append_frontmatter_tools(content, ["mcp__playwright__browser_click"]) == content


def test_empty_extra_tools_is_noop():
    assert append_frontmatter_tools(_FM, []) == _FM


# ---------------------------------------------------------------------------
# Registry/rule consistency -- catches future drift (issue #467, AC 3)
# ---------------------------------------------------------------------------

def test_every_role_mcp_server_exists_in_registry():
    from lib.mcp import load_mcp_registry

    registry = load_mcp_registry(_REPO_ROOT)
    roles = load_roles_config(_REPO_ROOT)["roles"]
    unknown = {
        role: server
        for role, cfg in roles.items()
        for server in (cfg or {}).get("mcp-servers", []) or []
        if server not in registry
    }
    assert not unknown, f"role-defaults.yaml references unknown MCP servers: {unknown}"


def test_generated_claude_agent_carries_the_tools():
    # AC 1: the generated file itself -- not just the resolver -- must list
    # them, since that frontmatter is what binds the runtime toolset.
    agent_file = _REPO_ROOT / ".claude" / "agents" / "e2e-tester.md"
    if not agent_file.exists():
        pytest.skip("e2e-tester not generated in this project")
    text = agent_file.read_text(encoding="utf-8")
    assert "mcp__playwright__browser_navigate" in text
    assert "mcp__playwright__browser_snapshot" in text
    assert "mcp__playwright__browser_evaluate" not in text  # blocked


@pytest.mark.parametrize("role,server", [("e2e-tester", "playwright")])
def test_documented_toolset_matches_generated_tools(role, server):
    # The rule file and the frontmatter must not drift apart: every tool the
    # rule advertises as allowed has to be bound in the agent's toolset.
    from lib.mcp import load_mcp_registry

    registry = load_mcp_registry(_REPO_ROOT)
    allowed = registry[server]["tools"]["allowed"]
    tools = resolve_mcp_tools_for_role(role, _config(), _REPO_ROOT)
    assert {f"mcp__{server}__{t}" for t in allowed} <= set(tools)
