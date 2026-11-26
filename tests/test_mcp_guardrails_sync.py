"""Task T30 / #1263a: the prose guardrail and the machine deny list must agree.

``rules/1-generic/mcp-guardrails.md`` is the always-on prose channel; the
provider's ``permissions.deny`` is the machine channel. Both are derived from
the SAME source — the ``tools.blocked`` list of the ACTIVE servers in
``config/plugin-catalog.yaml``:

* prose  → ``lib.registry_query.build_mcp_guardrails_list`` (placeholder
  ``{{MCP_GUARDRAILS_LIST}}`` in the shipped rule template)
* machine → ``lib.mcp_deny.build_mcp_deny_rules`` (``mcp__<server>__<tool>``)

The two consumers live in different modules, so nothing but a test stops them
from drifting apart (a hand-edited rule bullet, a changed prefix, a filtered
server list). These tests pin the equality at three levels: pure functions on
one registry, the repository's real catalog, and a synced temp project where
the rendered rule file and the settings file are compared byte-set-wise.

Run: python3 -m pytest tests/test_mcp_guardrails_sync.py -q
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402
from lib.mcp_deny import (  # noqa: E402
    MCP_DENY_CAPABILITY,
    MCP_TOOL_PREFIX,
    build_mcp_deny_rules,
    sync_mcp_deny,
)
from lib.registry_query import (  # noqa: E402
    build_mcp_guardrails_list,
    load_mcp_registry,
    resolve_active_mcp_servers,
)

_TEMPLATE = _REPO_ROOT / "rules" / "1-generic" / "mcp-guardrails.md"
_GUARDRAILS_PLACEHOLDER = "{{MCP_GUARDRAILS_LIST}}"
_PROJECT_CONFIG = _REPO_ROOT / ".meta-config" / "project.yaml"

# One bullet per server: "- **<server>:** `t1`, `t2` — absolut verboten."
_PROSE_BULLET_RE = re.compile(
    r"^- \*\*(?P<server>[^*]+):\*\* (?P<tools>.+?) — absolut verboten\.$"
)
_PROSE_TOOL_RE = re.compile(r"`([^`]+)`")
# The generator's own "nothing to prohibit" sentinel — never a tool entry.
_PROSE_EMPTY_SENTINEL = "- (keine aktiven MCP-Server mit gesperrten Tools)"

_PROVIDER_CONFIG = {
    "Claude": {
        "settings_file": ".claude/settings.json",
        "isolation-mechanism": "claude-settings-deny",
    },
}
_CAPABILITIES = {"Claude": {MCP_DENY_CAPABILITY: True}}


# --- parsing helpers -------------------------------------------------------


def _pairs_from_prose(text: str) -> set[tuple[str, str]]:
    """Return {(server, tool)} from the rendered hard-prohibitions bullets."""
    pairs: set[tuple[str, str]] = set()
    for line in text.splitlines():
        match = _PROSE_BULLET_RE.match(line.strip())
        if not match:
            continue
        server = match.group("server").strip()
        for tool in _PROSE_TOOL_RE.findall(match.group("tools")):
            pairs.add((server, tool))
    return pairs


def _pairs_from_deny_rules(rules: list[str]) -> set[tuple[str, str]]:
    """Return {(server, tool)} from ``mcp__<server>__<tool>`` deny entries."""
    pairs: set[tuple[str, str]] = set()
    for rule in rules:
        assert rule.startswith(MCP_TOOL_PREFIX), rule
        server, _, tool = rule[len(MCP_TOOL_PREFIX):].partition("__")
        assert server and tool, rule
        pairs.add((server, tool))
    return pairs


def _write_catalog(agent_meta_root: Path, servers: dict) -> None:
    """Write a minimal config/plugin-catalog.yaml with the given mcp servers."""
    plugins = {name: {**sdef, "kind": "mcp-server"} for name, sdef in servers.items()}
    path = agent_meta_root / "config" / "plugin-catalog.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(yaml.dump({"plugins": plugins}), encoding="utf-8")


# --- 1. one registry, both surfaces ---------------------------------------


def test_prose_and_deny_list_agree_for_same_registry():
    registry = {
        "alpha": {"tools": {"allowed": ["read"], "blocked": ["delete", "admin.restore"]}},
        "beta": {"tools": {"blocked": ["drop"]}},
        "quiet": {"tools": {"blocked": []}},
    }
    active = ["beta", "alpha", "quiet", "missing"]

    prose = build_mcp_guardrails_list(registry, active)
    deny = build_mcp_deny_rules(registry, active)

    assert _pairs_from_prose(prose) == _pairs_from_deny_rules(deny)
    assert _pairs_from_prose(prose) == {
        ("alpha", "delete"),
        ("alpha", "admin.restore"),
        ("beta", "drop"),
    }


def test_empty_blocked_list_renders_no_entry_on_either_surface():
    registry = {"quiet": {"tools": {"blocked": []}}, "also-quiet": {"tools": {}}}
    active = ["quiet", "also-quiet"]

    prose = build_mcp_guardrails_list(registry, active)
    deny = build_mcp_deny_rules(registry, active)

    assert _pairs_from_prose(prose) == set()
    assert deny == []
    assert _PROSE_EMPTY_SENTINEL in prose


# --- 2. the repository's real catalog -------------------------------------


def test_real_catalog_prose_matches_deny_list():
    """Guard against a hand-edited bullet or a changed deny prefix in-repo."""
    if not _PROJECT_CONFIG.exists():
        pytest.skip("not self-hosting: no .meta-config/project.yaml in this checkout")
    config = yaml.safe_load(_PROJECT_CONFIG.read_text(encoding="utf-8")) or {}
    registry = load_mcp_registry(_REPO_ROOT, config, _REPO_ROOT)
    active = resolve_active_mcp_servers(config, _REPO_ROOT, _REPO_ROOT, registry=registry)

    prose = build_mcp_guardrails_list(registry, active)
    deny = build_mcp_deny_rules(registry, active)

    assert _pairs_from_prose(prose) == _pairs_from_deny_rules(deny)


def test_shipped_template_delegates_the_list_to_the_generator():
    """The rule template must not carry hand-maintained bullets.

    Any literal "**<server>:** ... absolut verboten." line in the source rule
    would bypass the generator and could silently diverge from the deny list.
    """
    template = _TEMPLATE.read_text(encoding="utf-8")
    assert template.count(_GUARDRAILS_PLACEHOLDER) == 1
    assert _pairs_from_prose(template) == set()


# --- 3. synced project: rule file vs settings file ------------------------


def test_rendered_rule_matches_deny_list_in_synced_project(tmp_path):
    agent_meta_root = tmp_path / "meta"
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_catalog(agent_meta_root, {
        "alpha": {"tools": {"blocked": ["delete", "admin.restore"]}},
        "beta": {"tools": {"blocked": ["drop"]}},
        "quiet": {"tools": {"blocked": []}},
    })
    config = {"plugins": {"alpha": {"enabled": True}, "beta": {"enabled": True}}}
    registry = load_mcp_registry(agent_meta_root, config, project_root)
    active = resolve_active_mcp_servers(
        config, agent_meta_root, project_root, registry=registry,
    )

    rendered_rule = _TEMPLATE.read_text(encoding="utf-8").replace(
        _GUARDRAILS_PLACEHOLDER, build_mcp_guardrails_list(registry, active),
    )
    sync_mcp_deny(
        project_root, "Claude", _PROVIDER_CONFIG, registry, active,
        SyncLog(), False, capabilities=_CAPABILITIES,
    )

    deny = json.loads(
        (project_root / ".claude" / "settings.json").read_text(encoding="utf-8")
    )["permissions"]["deny"]
    machine = {entry for entry in deny if entry.startswith(MCP_TOOL_PREFIX)}

    assert _pairs_from_prose(rendered_rule) == _pairs_from_deny_rules(sorted(machine))
    assert _pairs_from_prose(rendered_rule) == {
        ("alpha", "delete"),
        ("alpha", "admin.restore"),
        ("beta", "drop"),
    }


def test_inactive_and_allowed_tools_never_reach_either_surface(tmp_path):
    agent_meta_root = tmp_path / "meta"
    project_root = tmp_path / "project"
    project_root.mkdir()
    _write_catalog(agent_meta_root, {
        "alpha": {"tools": {"allowed": ["read"], "blocked": ["delete"]}},
        "off": {"tools": {"blocked": ["nuke"]}},
    })
    config = {"plugins": {"alpha": {"enabled": True}, "off": {"enabled": False}}}
    registry = load_mcp_registry(agent_meta_root, config, project_root)
    active = resolve_active_mcp_servers(
        config, agent_meta_root, project_root, registry=registry,
    )

    prose = build_mcp_guardrails_list(registry, active)
    sync_mcp_deny(
        project_root, "Claude", _PROVIDER_CONFIG, registry, active,
        SyncLog(), False, capabilities=_CAPABILITIES,
    )
    deny = json.loads(
        (project_root / ".claude" / "settings.json").read_text(encoding="utf-8")
    )["permissions"]["deny"]

    # Both surfaces carry exactly the one active blocked tool — the inactive
    # server's blocked tool and the active server's allowed tool stay out.
    assert _pairs_from_prose(prose) == {("alpha", "delete")}
    assert _pairs_from_deny_rules(deny) == {("alpha", "delete")}
