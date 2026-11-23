"""Issue #1329 (SPEC-DECISION-1329-SHELL-GRANT) — Opencode worker shell grant.

AC-1: a runtime-verified ``subagent-shell`` capability turns a role's template
``Bash`` into a real shell permission (v1 ``permission.bash``, v2
``permissions[shell].effect``).
AC-2: a missing / false / invalid capability or a non-VERIFIED-RUNTIME state
fails safe to ``deny`` (never ``allow``) and the render path emits a WARNING.

Run: python3 -m pytest tests/test_opencode_worker_shell_grant.py -q
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from scripts.lib.frontmatter import _parse_frontmatter_yaml
from scripts.lib.log import SyncLog
from scripts.lib.provider_transform import (
    _map_claude_tools_to_opencode_permissions,
    map_tools_to_opencode_v2_permissions,
    transform_agent_content_for_provider,
)
from scripts.lib.providers import load_providers_config

REPO_ROOT = Path(__file__).resolve().parents[1]
PROVIDER = "Opencode"
VERIFIED = "VERIFIED-RUNTIME"

_SHIPPED_CAPS = yaml.safe_load(
    (REPO_ROOT / "config" / "provider-capabilities.yaml").read_text(encoding="utf-8")
)["capabilities"]


def _template(tools=("Read", "Bash")) -> str:
    tool_lines = "".join(f"  - {t}\n" for t in tools)
    return (
        '---\nname: template-exec\nversion: "1.0.0"\n'
        "description: execution role\nhint: run things\n"
        f"tools:\n{tool_lines}---\n\nBody.\n"
    )


def _caps(shell, state=VERIFIED):
    cap = {}
    if shell is not ...:
        cap["subagent-shell"] = shell
    if state is not ...:
        cap["subagent-shell-verified-state"] = state
    return {PROVIDER: cap}


def _render(template: str, caps: dict, *, v2: bool = False):
    pc = copy.deepcopy(load_providers_config(REPO_ROOT))
    entry = pc[PROVIDER]
    if v2:
        entry["agent-transform"]["frontmatter-mechanism"] = "opencode-native-v2"
    log = SyncLog()
    content = transform_agent_content_for_provider(
        template, PROVIDER, "test-executor", "test-executor", "desc",
        "1-generic/test-executor.md@1.0.0", {}, REPO_ROOT, REPO_ROOT,
        REPO_ROOT / "test-executor.md", {PROVIDER: entry}, log,
        provider_capabilities=caps,
    )
    return content, log, _parse_frontmatter_yaml(content)


# --- AC-1: verified grant -------------------------------------------------

def test_v1_mapper_allows_bash_only_with_verified_capability():
    perms = _map_claude_tools_to_opencode_permissions(
        ["Read", "Bash"],
        subagent_shell=True,
        subagent_shell_verified_state=VERIFIED,
    )
    assert perms["bash"] == "allow"
    assert perms["read"] == "allow"


def test_v2_mapper_allows_shell_only_with_verified_capability():
    entries = map_tools_to_opencode_v2_permissions(
        ["Bash", "Write"],
        subagent_shell=True,
        subagent_shell_verified_state=VERIFIED,
    )
    actions = {e["action"]: e["effect"] for e in entries}
    assert actions["shell"] == "allow"
    assert actions["edit"] == "allow"
    assert actions["subagent"] == "deny"


@pytest.mark.parametrize("v2", [False, True], ids=["v1", "v2"])
def test_render_path_honours_shipped_opencode_capability(v2):
    content, log, fm = _render(_template(), _SHIPPED_CAPS, v2=v2)
    if v2:
        shell = [e for e in fm["permissions"] if e["action"] == "shell"][0]
        assert shell["effect"] == "allow"
    else:
        assert fm["permission"]["bash"] == "allow"
    assert not [w for w in log.warnings if "subagent shell" in w.lower()]


# --- AC-2: fail-safe deny, never allow ------------------------------------

@pytest.mark.parametrize(
    "shell,state",
    [
        (False, VERIFIED),
        (None, VERIFIED),
        ("yes", VERIFIED),            # invalid type
        (1, VERIFIED),                # bool-lookalike is not a bool
        (True, "UNVERIFIED"),
        (True, "DOCUMENTED"),
        (True, None),
        (True, ...),                  # state key absent
        (..., VERIFIED),              # capability key absent
    ],
    ids=[
        "false", "none", "invalid-str", "invalid-int", "unverified",
        "documented", "state-none", "state-absent", "key-absent",
    ],
)
@pytest.mark.parametrize("v2", [False, True], ids=["v1", "v2"])
def test_mapper_fails_safe_for_non_granting_capability(shell, state, v2):
    kwargs = {"subagent_shell": shell}
    if state is not ...:
        kwargs["subagent_shell_verified_state"] = state
    if v2:
        entries = map_tools_to_opencode_v2_permissions(["Bash"], **kwargs)
        effect = [e["effect"] for e in entries if e["action"] == "shell"][0]
        assert effect == "deny"
    else:
        perms = _map_claude_tools_to_opencode_permissions(["Bash"], **kwargs)
        assert perms.get("bash") != "allow"


@pytest.mark.parametrize("v2", [False, True], ids=["v1", "v2"])
def test_role_without_bash_never_gains_shell(v2):
    kwargs = {"subagent_shell": True, "subagent_shell_verified_state": VERIFIED}
    if v2:
        entries = map_tools_to_opencode_v2_permissions(["Read"], **kwargs)
        effect = [e["effect"] for e in entries if e["action"] == "shell"][0]
        assert effect == "deny"
    else:
        perms = _map_claude_tools_to_opencode_permissions(["Read"], **kwargs)
        assert "bash" not in perms


def test_v1_deny_list_parity_survives_the_grant():
    kwargs = {"subagent_shell": True, "subagent_shell_verified_state": VERIFIED}
    explicit = _map_claude_tools_to_opencode_permissions(
        ["Bash", "Read"], deny_list=["Bash", "Write"], **kwargs
    )
    assert explicit["bash"] == "allow"        # explicit allow wins (frozen rule)
    assert explicit["edit"] == "deny"         # deny still closes unmapped tools


def test_v2_deny_list_parity_survives_the_grant():
    kwargs = {"subagent_shell": True, "subagent_shell_verified_state": VERIFIED}
    with_deny = map_tools_to_opencode_v2_permissions(["Bash"], deny_list=["Bash"], **kwargs)
    without = map_tools_to_opencode_v2_permissions(["Bash"], **kwargs)
    assert with_deny == without


@pytest.mark.parametrize("v2", [False, True], ids=["v1", "v2"])
def test_render_path_warns_and_denies_when_capability_is_false(v2):
    content, log, fm = _render(_template(), _caps(False, "UNVERIFIED"), v2=v2)
    assert [w for w in log.warnings if "subagent shell" in w.lower()]
    if v2:
        shell = [e for e in fm["permissions"] if e["action"] == "shell"][0]
        assert shell["effect"] == "deny"
    else:
        assert fm["permission"]["bash"] != "allow"


@pytest.mark.parametrize("v2", [False, True], ids=["v1", "v2"])
def test_render_path_warns_when_capability_key_is_missing(v2):
    _content, log, fm = _render(_template(), _caps(..., ...), v2=v2)
    assert [w for w in log.warnings if "subagent shell" in w.lower()]
    if v2:
        shell = [e for e in fm["permissions"] if e["action"] == "shell"][0]
        assert shell["effect"] == "deny"
    else:
        assert fm["permission"].get("bash") != "allow"


def test_every_registered_provider_declares_both_shell_keys():
    """#1113-style obligation: no silent omission in the registry."""
    missing = []
    for provider, cap in _SHIPPED_CAPS.items():
        if "subagent-shell" not in cap or "subagent-shell-verified-state" not in cap:
            missing.append(provider)
    assert missing == []
