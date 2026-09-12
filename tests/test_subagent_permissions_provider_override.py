"""M2 regression: per-provider subagent-permission bundle + standalone (M4).

``agent_sync._build_provider_vars`` must carry the provider-correct flags AND
``SUBAGENT_PERMISSIONS_BLOCK`` together; standalone rendering must never leak a
policy marker (off has no text).
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.agent_sync import _build_provider_vars  # noqa: E402
from lib.standalone import (  # noqa: E402
    _CONDITIONAL_FALSE_FLAGS,
    _ORCHESTRATION_FALLBACKS,
    render_standalone_agent,
)
from lib.subagent_permissions import render_subagent_permission_block  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent


def test_build_provider_vars_uses_provider_override_bundle():
    config = {
        "subagent_permissions": {
            "mode": "off",
            "provider-overrides": {"Opencode": {"mode": "strict"}},
        },
    }
    opencode = _build_provider_vars({}, "Opencode", {}, _REPO_ROOT, config=config)
    assert opencode["SUBAGENT_PERMISSIONS_MODE"] == "strict"
    assert opencode["SUBAGENT_PERMISSIONS_STRICT"] == "true"
    assert opencode["SUBAGENT_PERMISSIONS_BLOCK"] == render_subagent_permission_block("strict")

    claude = _build_provider_vars({}, "Claude", {}, _REPO_ROOT, config=config)
    assert claude["SUBAGENT_PERMISSIONS_MODE"] == "off"
    assert claude["SUBAGENT_PERMISSIONS_BLOCK"] == ""
    assert claude["SUBAGENT_PERMISSIONS_ENABLED"] == "false"


def test_build_provider_vars_without_config_keeps_backward_compat():
    # Omitting config keeps the historic 4-arg behavior (no bundle injected).
    merged = _build_provider_vars({}, "Claude", {"X": "1"}, _REPO_ROOT)
    assert merged["X"] == "1"
    assert "SUBAGENT_PERMISSIONS_MODE" not in merged


def test_standalone_fallbacks_present():
    assert _ORCHESTRATION_FALLBACKS["SUBAGENT_PERMISSIONS_BLOCK"] == ""
    for flag in (
        "SUBAGENT_PERMISSIONS_STRICT",
        "SUBAGENT_PERMISSIONS_WARN",
        "SUBAGENT_PERMISSIONS_OFF",
        "SUBAGENT_PERMISSIONS_ENABLED",
    ):
        assert _CONDITIONAL_FALSE_FLAGS[flag] == "false"


def test_standalone_orchestrator_has_no_policy_marker():
    rendered = render_standalone_agent("orchestrator", _REPO_ROOT)
    assert "SUBAGENT_PERMISSIONS" not in rendered
    assert "Subagent Permission Policy" not in rendered
