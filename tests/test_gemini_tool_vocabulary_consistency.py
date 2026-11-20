"""Consistency checks for the terminal/command tool vocabulary (#1171).

Issue #1171 pins the invariant that a provider's Bash tool name is spelled
identically across its three configuration surfaces. That target spelling is
still undecided (blocked on #1160), so the single-surface invariant test is
marked xfail(strict=True): it becomes a hard failure the moment the values
are aligned, prompting removal of the marker.

The second test is data-driven over the YAML keys: any provider that declares
a ``tool-name-map["Bash"]`` override must also carry a ``terminal_tool`` entry.
It contains no provider-name branching (E-26: one Gemini CLI surface only).

Run: python3 -m pytest tests/test_gemini_tool_vocabulary_consistency.py -q
"""

from pathlib import Path

import pytest

from scripts.lib.frontmatter import load_provider_tools_config
from scripts.lib.providers import load_providers_config

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.mark.xfail(strict=True, reason="#1171 pending #1160 target decision")
def test_bash_vocabulary_is_single_per_gemini_surface():
    """Pin the target invariant: one spelling of the Bash tool per surface.

    Today ``bash_tool_name == terminal_tool == code_execution`` but the
    agent-transform map says ``run_command`` — the assertion fails, which is
    the expected xfail until #1160 decides the canonical name.
    """
    pc = load_providers_config(REPO_ROOT)["Gemini"]
    mapped = pc["agent-transform"]["tool-name-map"]["Bash"]
    terminal = load_provider_tools_config(REPO_ROOT)["terminal_tool"]["Gemini"]
    assert pc["bash_tool_name"] == terminal == mapped


def test_every_provider_with_bash_tool_map_has_terminal_tool():
    """Data-driven: a Bash name override implies a non-empty terminal_tool.

    Iterates the provider keys from ``ai-providers.yaml`` itself — no provider
    name is hardcoded here, so the check holds for any added surface.
    """
    providers = load_providers_config(REPO_ROOT)
    terminal_tools = load_provider_tools_config(REPO_ROOT)["terminal_tool"]

    for name, cfg in providers.items():
        tool_name_map = (cfg.get("agent-transform") or {}).get("tool-name-map") or {}
        if not tool_name_map.get("Bash"):
            continue
        assert terminal_tools.get(name), (
            f"{name}: tool-name-map['Bash'] is set but terminal_tool is missing/empty"
        )
