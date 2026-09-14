"""Runtime-gate tier resolver + rendering-bundle contract.

Covers the Phase-0 resolver seam (SPEC-OPENCODE-RUNTIME-GATE-2026-09-13,
IC-01/IC-03):

- AC-01: every registered provider declares an explicit tier (the
  parametrized provider sweep lives in ``test_provider_agnostic_dispatch.py``).
- AC-02: the declared tier agrees with the machine flags in
  ``config/ai-providers.yaml`` (hook iff hooks supported; plugin iff plugin
  supported and not hook-supported).
- AC-03: resolver semantics + fail-safe (never raises, never silently
  stronger than ``advisory``).
- AC-22: the plugin tier is unreachable without verified plugin flags.
- IC-03/IC-04: ``runtime_gate_vars`` produces the five string keys the
  rules/context renderers consume, with a fail-safe ``observe`` plugin mode.

Run: python -m pytest tests/test_runtime_gate_config.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.providers import (  # noqa: E402
    SUPPORTED_PLUGIN_PROTOCOLS,
    provider_hooks_supported,
    provider_runtime_gate_supported,
    provider_runtime_gate_tier,
    runtime_gate_vars,
)
from lib.runtime_gate import RUNTIME_GATE_TIERS  # noqa: E402


def _ai_providers() -> dict:
    data = yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))
    return data.get("providers") or {}


def _capabilities() -> dict:
    data = yaml.safe_load(
        (_REPO_ROOT / "config" / "provider-capabilities.yaml").read_text(encoding="utf-8")
    )
    return data.get("capabilities") or {}


def _registered_providers() -> list:
    return sorted(_ai_providers().keys())


def test_runtime_gate_tiers_vocabulary_is_canonical():
    """The canonical vocabulary is the single contract consumers import."""
    assert RUNTIME_GATE_TIERS == ("hook", "plugin", "permission", "advisory")


@pytest.mark.parametrize("provider", _registered_providers())
def test_declared_tier_matches_machine_flags(provider):
    """AC-02: the declared ``runtime_gate`` must agree with the machine flags.

    ``hook`` iff ``provider_hooks_supported(pc)``; ``plugin`` iff
    ``provider_runtime_gate_supported(pc)`` **and not**
    ``provider_hooks_supported(pc)`` (hook precedence wins, F-06); every other
    provider is ``permission`` or ``advisory``. The resolved tier must equal
    the declaration for the live registry.
    """
    pc = _ai_providers().get(provider, {})
    declared = _capabilities().get(provider, {}).get("runtime_gate")

    hooks = provider_hooks_supported(pc)
    plugin = provider_runtime_gate_supported(pc)

    assert (declared == "hook") == hooks, (
        f"Provider '{provider}': runtime_gate={declared!r} but "
        f"provider_hooks_supported={hooks} — the declaration must match the flags"
    )
    assert (declared == "plugin") == (plugin and not hooks), (
        f"Provider '{provider}': runtime_gate={declared!r} but "
        f"provider_runtime_gate_supported={plugin}, hooks={hooks} — hook "
        "precedence wins, so plugin requires plugin support and no hook support"
    )
    if declared not in ("hook", "plugin"):
        assert declared in ("permission", "advisory"), (
            f"Provider '{provider}': runtime_gate={declared!r} must be one of "
            f"{RUNTIME_GATE_TIERS}"
        )

    assert provider_runtime_gate_tier(pc, _capabilities().get(provider, {})) == declared, (
        f"Provider '{provider}': resolver tier disagrees with the declared "
        f"contract {declared!r}"
    )


def test_resolver_precedence():
    """AC-03: first match wins — hook > plugin > permission > advisory."""
    hook_pc = {"has_hooks": True, "hook_protocol": "claude-code-json"}
    plugin_pc = {"has_plugins": True, "plugin_protocol": "opencode-plugin-js"}

    assert provider_runtime_gate_tier(hook_pc) == "hook"
    assert provider_runtime_gate_tier(plugin_pc) == "plugin"
    assert provider_runtime_gate_tier({}, {"runtime_gate": "permission"}) == "permission"
    assert provider_runtime_gate_tier({}, {"runtime_gate": "advisory"}) == "advisory"
    assert provider_runtime_gate_tier({}) == "advisory"

    # hook precedence wins when a provider supports both mechanisms.
    both = dict(hook_pc, has_plugins=True, plugin_protocol="opencode-plugin-js")
    assert provider_runtime_gate_tier(both) == "hook"

    # plugin precedence wins over a declared `permission` capability.
    assert (
        provider_runtime_gate_tier(plugin_pc, {"runtime_gate": "permission"})
        == "plugin"
    )


@pytest.mark.parametrize(
    "pc, capabilities",
    [
        (None, None),
        (None, {}),
        ({}, None),
        ({}, {}),
        ([], []),
        ("Claude", None),
        ({}, {"runtime_gate": None}),
        ({"has_hooks": "yes"}, None),
    ],
)
def test_resolver_failsafe_never_raises(pc, capabilities):
    """AC-03: non-mapping/None inputs resolve to ``advisory``, never raise.

    Notably ``provider_runtime_gate_tier(None)`` and ``({}, None)`` are the
    spec's pinned fail-safe cases.
    """
    tier = provider_runtime_gate_tier(pc, capabilities)
    assert tier == "advisory", f"fail-safe must be advisory, got {tier!r}"
    assert tier in RUNTIME_GATE_TIERS


def test_resolver_ignores_non_permission_declarations_without_flags():
    """AC-03/AC-22: only a ``permission`` declaration is read beyond the flags.

    A provider that declares ``hook``/``plugin``/an unknown value without the
    matching machine flags must not be upgraded at runtime.
    """
    assert provider_runtime_gate_tier({}, {"runtime_gate": "hook"}) == "advisory"
    assert provider_runtime_gate_tier({}, {"runtime_gate": "plugin"}) == "advisory"
    assert provider_runtime_gate_tier({}, {"runtime_gate": "bogus"}) == "advisory"


def test_plugin_tier_unreachable_without_has_plugins():
    """AC-22: no ``has_plugins`` (or an unverified protocol) means no plugin tier.

    A declared ``runtime_gate: plugin`` alone can never produce the plugin tier
    — a stronger tier is only reachable through verified machine flags.
    """
    assert provider_runtime_gate_supported({}) is False
    assert provider_runtime_gate_supported({"has_plugins": True}) is False
    assert (
        provider_runtime_gate_supported(
            {"has_plugins": True, "plugin_protocol": "unknown-plugin-js"}
        )
        is False
    )
    assert (
        provider_runtime_gate_supported(
            {"has_plugins": True, "plugin_protocol": "opencode-plugin-js"}
        )
        is True
    )
    assert "opencode-plugin-js" in SUPPORTED_PLUGIN_PROTOCOLS
    assert provider_runtime_gate_tier({"has_plugins": False}) == "advisory"
    # has_plugins true but no verified protocol -> still not plugin.
    assert provider_runtime_gate_tier({"has_plugins": True}) == "advisory"


def test_runtime_gate_vars_bundle_is_strings():
    """IC-03/IC-04: the five keys are strings and truth-consistent per tier."""
    keys = {
        "ENFORCEMENT_TIER",
        "GATE_ENFORCED",
        "GATE_PARTIAL",
        "GATE_ADVISORY",
        "RUNTIME_GATE_PLUGIN_MODE",
    }

    hook_vars = runtime_gate_vars(
        {"has_hooks": True, "hook_protocol": "claude-code-json"}, {}, {}
    )
    assert set(hook_vars) == keys
    assert all(isinstance(v, str) for v in hook_vars.values())
    assert hook_vars["ENFORCEMENT_TIER"] == "hook"
    assert hook_vars["GATE_ENFORCED"] == "true"
    assert hook_vars["GATE_PARTIAL"] == "false"
    assert hook_vars["GATE_ADVISORY"] == "false"

    partial_vars = runtime_gate_vars({}, {"runtime_gate": "permission"}, {})
    assert all(isinstance(v, str) for v in partial_vars.values())
    assert partial_vars["ENFORCEMENT_TIER"] == "permission"
    assert partial_vars["GATE_ENFORCED"] == "false"
    assert partial_vars["GATE_PARTIAL"] == "true"
    assert partial_vars["GATE_ADVISORY"] == "false"

    advisory_vars = runtime_gate_vars({}, {}, {})
    assert all(isinstance(v, str) for v in advisory_vars.values())
    assert advisory_vars["ENFORCEMENT_TIER"] == "advisory"
    assert advisory_vars["GATE_ENFORCED"] == "false"
    assert advisory_vars["GATE_PARTIAL"] == "false"
    assert advisory_vars["GATE_ADVISORY"] == "true"

    # Plugin tier counts as enforced (Phase 1; unreachable without flags).
    plugin_vars = runtime_gate_vars(
        {"has_plugins": True, "plugin_protocol": "opencode-plugin-js"}, {}, {}
    )
    assert plugin_vars["ENFORCEMENT_TIER"] == "plugin"
    assert plugin_vars["GATE_ENFORCED"] == "true"


def test_runtime_gate_vars_plugin_mode_failsafe():
    """AC-24 (resolver side): ``plugin-mode`` is enum-validated, default observe.

    The schema key itself is covered by the Task-5 schema tests; here the
    rendering bundle must never emit an out-of-enum mode.
    """
    assert (
        runtime_gate_vars({}, {}, {"runtime-gate": {"plugin-mode": "enforce"}})[
            "RUNTIME_GATE_PLUGIN_MODE"
        ]
        == "enforce"
    )
    assert (
        runtime_gate_vars({}, {}, {"runtime-gate": {"plugin-mode": "observe"}})[
            "RUNTIME_GATE_PLUGIN_MODE"
        ]
        == "observe"
    )
    assert (
        runtime_gate_vars({}, {}, {"runtime-gate": {}})["RUNTIME_GATE_PLUGIN_MODE"]
        == "observe"
    )
    assert runtime_gate_vars({}, {}, {})["RUNTIME_GATE_PLUGIN_MODE"] == "observe"
    assert (
        runtime_gate_vars({}, {}, {"runtime-gate": {"plugin-mode": "bogus"}})[
            "RUNTIME_GATE_PLUGIN_MODE"
        ]
        == "observe"
    )
    assert (
        runtime_gate_vars({}, {}, {"runtime-gate": "not-a-mapping"})[
            "RUNTIME_GATE_PLUGIN_MODE"
        ]
        == "observe"
    )
    assert runtime_gate_vars({}, {}, None)["RUNTIME_GATE_PLUGIN_MODE"] == "observe"
