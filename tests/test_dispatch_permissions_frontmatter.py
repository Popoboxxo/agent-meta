"""IC-15 Nr. 6 / AC-17 (F-11): the Mammouth orchestrator dispatches subagents.

Mammouth is an OpenCode fork. Its generated agents previously carried the
Claude-cased ``tools:`` object from ``tools-format: map`` (inert — OpenCode/Mammouth
read lowercase permission keys such as ``task``/``todowrite``/``read``), no
``mode`` and no ``subagent_depth`` (study 3.4). The fix is data-driven through the
Mammouth ``agent-transform`` block plus the ``required_depth`` capability — never
a provider literal in ``scripts/lib``.

Provider-agnostic by construction: the behaviour comes from
``frontmatter-mechanism: opencode-native`` (the resolved ``agent-transform``
value) and ``inject-subagent-depth`` (consuming the ``required_depth``
capability), so ``tests/test_provider_agnostic_dispatch.py`` stays green.

Run: python3 -m pytest tests/test_dispatch_permissions_frontmatter.py -q
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.active_set import compute_active_set
from lib.log import SyncLog
from lib.provider_transform import transform_agent_content_for_provider
from lib.providers import load_provider_capabilities, load_providers_config

_PROVIDER = "Mammouth"
_PC = load_providers_config(REPO_ROOT)
_CAPS = load_provider_capabilities(REPO_ROOT)
_ORCHESTRATOR_TEMPLATE = (
    REPO_ROOT / "agents" / "1-generic" / "orchestrator.md"
).read_text(encoding="utf-8")
_DEVELOPER_TEMPLATE = (
    REPO_ROOT / "agents" / "1-generic" / "developer.md"
).read_text(encoding="utf-8")

# PascalCase Claude tool names that must never surface as permission keys.
_CLAUDE_TOOL_NAMES = {
    "Agent", "TodoWrite", "Read", "Write", "Edit", "Bash", "Grep", "Glob",
    "WebFetch", "WebSearch",
}

_DEFAULT_CONFIG = {
    "agent-meta-version": "2.0.0-beta.1",
    "ai-providers": [_PROVIDER],
    "dod-preset": "rapid-prototyping",
    "variables": {"PROJECT_NAME": "matrix", "PROJECT_PREFIX": "mx"},
}


def _active():
    return compute_active_set(_DEFAULT_CONFIG, REPO_ROOT, REPO_ROOT, warn_sink=[])


def _render(template: str, role: str, provider: str = _PROVIDER,
            provider_config: dict | None = None, capabilities: dict | None = None):
    log = SyncLog()
    out = transform_agent_content_for_provider(
        template, provider, role, role,
        "desc", f"1-generic/{role}.md@0.0.0", _DEFAULT_CONFIG,
        REPO_ROOT, REPO_ROOT,
        REPO_ROOT / f".{provider.lower()}" / "agents" / f"{role}.md",
        provider_config if provider_config is not None else _PC, log,
        active_set=_active(),
        provider_capabilities=capabilities if capabilities is not None else _CAPS,
    )
    return out, log


def _frontmatter(out: str) -> dict:
    return yaml.safe_load(out.split("---", 2)[1])


def test_mammouth_capability_declares_dispatch_and_depth():
    caps = _CAPS[_PROVIDER]
    assert caps["subagent_dispatch"] is True, (
        "study 3.4 verified the native `task` tool — the capability was an under-claim"
    )
    assert caps["required_depth"] >= 2, "an orchestrator -> worker chain needs depth >= 2"


def test_orchestrator_has_lowercase_permission_with_task_and_todowrite():
    fm = _frontmatter(_render(_ORCHESTRATOR_TEMPLATE, "orchestrator")[0])
    perms = fm.get("permission")
    assert isinstance(perms, dict), (
        "Mammouth agents need a native `permission` map (not the inert Claude `tools:` object)"
    )
    assert perms.get("task") == "allow", "the orchestrator cannot delegate without `task: allow`"
    assert perms.get("todowrite") == "allow", "the orchestrator needs `todowrite: allow`"
    leaked = set(perms) & _CLAUDE_TOOL_NAMES
    assert not leaked, f"Claude-cased permission keys leaked: {sorted(leaked)}"
    assert all(k == k.lower() for k in perms), f"permission keys must be lowercase: {perms}"


def test_orchestrator_has_mode_set():
    fm = _frontmatter(_render(_ORCHESTRATOR_TEMPLATE, "orchestrator")[0])
    assert fm.get("mode"), "every Mammouth agent needs an explicit mode (study 3.4: mode 'all')"


def test_orchestrator_has_subagent_depth_from_required_depth():
    fm = _frontmatter(_render(_ORCHESTRATOR_TEMPLATE, "orchestrator")[0])
    depth = fm.get("subagent_depth")
    assert isinstance(depth, int) and not isinstance(depth, bool), (
        f"the orchestrator needs an integer subagent_depth, got {depth!r}"
    )
    assert depth >= 2, f"subagent_depth too low: {depth}"
    assert depth >= _CAPS[_PROVIDER]["required_depth"], (
        "subagent_depth must be at least the declared required_depth"
    )


def test_every_agent_gets_mode_and_depth():
    """The mechanism is uniform: a worker gets the same surface, not only the orchestrator."""
    out, _ = _render(_DEVELOPER_TEMPLATE, "developer")
    fm = _frontmatter(out)
    assert fm.get("mode")
    assert isinstance(fm.get("subagent_depth"), int)


def test_mammouth_spec_keys_are_wired():
    spec = _PC[_PROVIDER]["agent-transform"]
    assert spec["frontmatter-mechanism"] == "opencode-native"
    assert spec.get("inject-subagent-depth") is True


def test_depth_emission_is_data_driven():
    """A synthetic provider declaring the same keys gets the depth — no name branch."""
    provider = "ZCode"
    config = copy.deepcopy(_PC)
    config[provider]["agent-transform"]["frontmatter-mechanism"] = "opencode-native"
    config[provider]["agent-transform"]["inject-subagent-depth"] = True
    caps = copy.deepcopy(_CAPS)
    caps[provider] = dict(caps.get(provider) or {})
    caps[provider]["required_depth"] = 3
    out, _ = _render(_ORCHESTRATOR_TEMPLATE, "orchestrator", provider=provider,
                     provider_config=config, capabilities=caps)
    assert _frontmatter(out)["subagent_depth"] == 3


def test_only_the_depth_provider_declares_the_key():
    """The render difference stays in data: no other provider gets the depth key."""
    for provider, entry in _PC.items():
        if provider == _PROVIDER:
            continue
        spec = (entry or {}).get("agent-transform") or {}
        assert not spec.get("inject-subagent-depth"), provider
