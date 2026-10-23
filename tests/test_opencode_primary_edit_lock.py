"""Task 8 (#1006, AC-11) — edit lock for the primary orchestrator.

While the runtime gate is active (``orchestrator.mode: strict`` AND the
provider's resolved tier is ``permission``), the primary orchestrator's
``permission.edit: allow`` must not survive: a primary agent that can write
everywhere defeats the gate for the Main Chat. The write scope is therefore
replaced by the scoped allow-list from ``config/provider-tools.yaml``
(``opencode_primary_edit_allow``, ADR-5 option B), or by the scalar ``deny``
when that list is empty (option A, fail-closed).

Contract (IC-3):

* only ``perms.get("edit") == "allow"`` is ever replaced — a role without
  ``Write``/``Edit`` already carries the scalar ``deny`` from
  ``opencode_deny_critical`` and MUST NOT gain the allow-list mapping (a lock
  must never widen a privilege);
* ``"*"`` comes first inside the mapping (last match wins in Opencode);
* the key order of all other permissions is untouched (dict copy, no mutation
  of shared state);
* ``deny_edit=False`` (the default call path) is byte-identical to before.

Run: python3 -m pytest tests/test_opencode_primary_edit_lock.py -q
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from scripts.lib.frontmatter import load_provider_tools_config
from scripts.lib.log import SyncLog
from scripts.lib.provider_transform import (
    _transform_frontmatter_for_opencode,
    transform_agent_content_for_provider,
)
from scripts.lib.providers import load_providers_config

REPO_ROOT = Path(__file__).resolve().parents[1]

_PROVIDER_CONFIG = load_providers_config(REPO_ROOT)

# The gate is requested: tier `permission` (provider-capabilities.yaml) plus an
# effectively strict orchestrator (three-tier precedence resolver).
STRICT = {"orchestrator": {"mode": "strict"}}

_SCOPED = {"*": "deny", ".tmp/**": "allow", ".meta-viz/**": "allow"}


def _agent_content(tools: tuple[str, ...] = ("Read", "Bash", "Grep", "Write")) -> str:
    """Template-shaped content with a writable tool set by default."""
    tool_lines = "".join(f"  - {tool}\n" for tool in tools)
    return (
        "---\n"
        "name: template-orchestrator\n"
        'version: "0.101.0"\n'
        "description: old description\n"
        "tools:\n"
        f"{tool_lines}"
        "---\n"
        "\n"
        "Koordiniert alle Entwicklungsaufgaben.\n"
    )


def _render(
    role: str = "orchestrator",
    project_config: dict | None = None,
    provider_config: dict | None = None,
    content: str | None = None,
) -> str:
    """Run the full Opencode transform against the real config (or a copy)."""
    config = provider_config if provider_config is not None else _PROVIDER_CONFIG
    entry = config["Opencode"]
    ext = entry.get("agent_ext", ".md")
    return transform_agent_content_for_provider(
        content if content is not None else _agent_content(),
        "Opencode",
        role,
        role,
        "desc",
        f"1-generic/{role}.md@0.101.0",
        project_config if project_config is not None else {},
        REPO_ROOT,
        REPO_ROOT,
        REPO_ROOT / entry["agents_dir"] / f"{role}{ext}",
        config,
        SyncLog(),
    )


def _permission(output: str) -> dict:
    """Parse the rendered frontmatter and return its ``permission`` block."""
    block = output.split("---", 2)[1]
    parsed = yaml.safe_load(block)
    assert isinstance(parsed, dict), parsed
    return parsed["permission"]


# ---------------------------------------------------------------------------
# AC-11 — the lock itself
# ---------------------------------------------------------------------------


def test_primary_orchestrator_edit_is_scoped_under_active_gate() -> None:
    """AC-11: strict orchestrator + permission tier scopes `edit` to the list."""
    permission = _permission(_render(project_config=STRICT))

    assert permission["edit"] == _SCOPED
    assert list(permission["edit"]) == ["*", ".tmp/**", ".meta-viz/**"], (
        "the root deny must come first — last match wins in Opencode"
    )


def test_empty_allow_list_falls_back_to_scalar_deny(monkeypatch: pytest.MonkeyPatch) -> None:
    """ADR-5: an empty path list degrades to the scalar `edit: deny` (option A)."""
    real = load_provider_tools_config(REPO_ROOT)
    monkeypatch.setattr(
        "scripts.lib.provider_transform.load_provider_tools_config",
        lambda root: {**real, "opencode_primary_edit_allow": []},
    )

    permission = _permission(_render(project_config=STRICT))

    assert permission["edit"] == "deny"


def test_no_lock_without_strict() -> None:
    """No active gate -> the template-derived `allow` is untouched."""
    permission = _permission(_render(project_config={}))

    assert permission["edit"] == "allow"


def test_no_lock_for_non_primary_role() -> None:
    """Only the primary entry is locked; subagents keep their write scope."""
    permission = _permission(_render(role="developer", project_config=STRICT))

    assert permission["edit"] == "allow"


def test_no_lock_when_tier_is_not_permission() -> None:
    """A hook-capable provider resolves to tier `hook`: no permission lock."""
    config = copy.deepcopy(_PROVIDER_CONFIG)
    config["Opencode"].update(has_hooks=True, hook_protocol="claude-code-json")

    permission = _permission(_render(project_config=STRICT, provider_config=config))

    assert permission["edit"] == "allow"


def test_other_permissions_unchanged_under_lock() -> None:
    """The lock replaces exactly one value: every other key and its order stays."""
    content = _agent_content(("Read", "Bash", "Grep", "Write", "Agent", "TodoWrite"))
    locked = _permission(_render(project_config=STRICT, content=content))
    unlocked = _permission(_render(project_config={}, content=content))

    assert list(locked) == list(unlocked)
    for key, value in unlocked.items():
        if key == "edit":
            continue
        assert locked[key] == value, f"permission.{key} must not change under the lock"
    assert locked["edit"] != "allow"
    assert {"bash", "task", "read", "todowrite"} <= set(locked)


def test_role_without_write_tool_keeps_edit_deny_under_lock() -> None:
    """Regression: the lock must never widen a read-only role's `deny` to allow."""
    permission = _permission(
        _render(project_config=STRICT, content=_agent_content(("Read",))),
    )

    assert permission["edit"] == "deny"
    assert not isinstance(permission["edit"], dict), (
        "a role without Write/Edit must not gain the allow-list mapping"
    )


def test_default_call_is_byte_identical() -> None:
    """`deny_edit=False` (the default path) renders exactly as before."""
    args = (
        _agent_content(),
        "orchestrator",
        "desc",
        "",
        "",
        "1-generic/orchestrator.md@0.101.0",
        REPO_ROOT,
    )

    default = _transform_frontmatter_for_opencode(*args)
    explicit_off = _transform_frontmatter_for_opencode(*args, deny_edit=False)

    assert explicit_off == default
