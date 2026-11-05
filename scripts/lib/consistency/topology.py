"""Consistency checks for the resolved orchestrator topology (IC-5).

SPEC-orchestrator-topology-2026-11-03 (issue #1077), P2.

The sync resolves a position per provider (``lib.topology.resolve_topology``)
and emits/gates on that single value. This module reports the conditions the
render cannot express as a diff:

``orchestrator-topology.degraded``
    A declared value was really degraded (``degraded_from is not None``).
    An unchanged ``UNVERIFIED => no`` cell of an undeclared project is not a
    degradation and stays silent (D9, AC-16).

``orchestrator-topology.hybrid-unverified``
    ``hybrid`` was declared while its capability cell is ``UNVERIFIED``.

``orchestrator-topology.main-chat-supersedes``
    Cross-scope dominance: the project declares a topology and a provider
    override selects ``main-chat``. The validator only rejects the SAME scope;
    this is the loud cross-scope WARNING (AC-7).

``orchestrator-topology.gate-inactive``
    The runtime gate would be wanted, but the effective topology is not
    ``primary`` — the entry point (and therefore the deny) is deliberately not
    written (AC-20).

``orchestrator-topology.default-agent-conflict``
    A user-owned ``default_agent`` names the orchestrator role while the
    effective topology is not ``primary``. The value is never auto-deleted;
    the finding names the action (AC-14).

Contract: no writes, no ``sys.exit``, only :class:`Finding` objects. Each
check ID is emitted at most once per provider and run; different IDs may fire
for the same provider in the same run. The checker never raises — malformed
input degrades to the findings collected so far.

``instances-clamped`` and ``unresolved-global-flags`` are P3/deferred (they
need ``max-instances`` and provider-less render provenance respectively) and
are deliberately not implemented in the v1 checker.
"""
from __future__ import annotations

from pathlib import Path
from typing import Optional

from .report import Finding, Severity
from ..topology import resolve_topology

_PROJECT_CONFIG = ".meta-config/project.yaml"

# Stable check IDs (IC-5).
CHECK_DEGRADED = "orchestrator-topology.degraded"
CHECK_HYBRID_UNVERIFIED = "orchestrator-topology.hybrid-unverified"
CHECK_MAIN_CHAT_SUPERSEDES = "orchestrator-topology.main-chat-supersedes"
CHECK_GATE_INACTIVE = "orchestrator-topology.gate-inactive"
CHECK_DEFAULT_AGENT_CONFLICT = "orchestrator-topology.default-agent-conflict"


def _orchestrator_block(config: dict) -> dict:
    block = config.get("orchestrator") if isinstance(config, dict) else None
    return block if isinstance(block, dict) else {}


def _provider_override(orch: dict, provider: str) -> Optional[dict]:
    overrides = orch.get("provider-overrides")
    if not isinstance(overrides, dict):
        return None
    override = overrides.get(provider)
    return override if isinstance(override, dict) else None


def _main_chat_override(override: Optional[dict]) -> bool:
    if not isinstance(override, dict):
        return False
    mode = override.get("mode")
    return isinstance(mode, str) and mode.strip().lower() == "main-chat"


def _gate_wanted(orch: dict, provider: str, pc: dict, caps: dict, agent_meta_root: Path) -> bool:
    """Whether the runtime gate would be requested for *provider*.

    Mirrors ``isolation._opencode_runtime_gate_entries``: tier ``permission``
    AND strict effectively active. Data-driven — no provider-name branch.
    """
    from ..providers import provider_runtime_gate_tier
    from .orchestrator_strict import _resolve_effective_strict

    if provider_runtime_gate_tier(pc, caps) != "permission":
        return False
    return _resolve_effective_strict(orch, provider, agent_meta_root)


def _settings_path(agent_meta_root: Path, pc: dict) -> Optional[str]:
    """The managed gate document's project-relative path, or ``None``."""
    mcp_config = pc.get("mcp-config")
    committed = mcp_config.get("committed-file") if isinstance(mcp_config, dict) else None
    for candidate in (pc.get("settings_file"), committed):
        if isinstance(candidate, str) and candidate:
            return candidate
    return None


def _user_owned_default_agent(
    agent_meta_root: Path, provider_config: dict, provider: str, pc: dict, effective: str
) -> Optional[str]:
    """The user-owned ``default_agent`` that conflicts with *effective*, else None.

    User-owned means: the key names the provider's orchestrator role (``primary-
    role``) and no ``default-agent`` state record claims the same value. A
    still-managed value is rolled back by the sync, so it is not a conflict.
    """
    if effective == "primary":
        return None

    from ..isolation import (
        _OPENCODE_STATE_FILE,
        _STATE_DEFAULT_AGENT_KEY,
        _read_state,
        owns_gate_surface,
    )
    from ..io import read_json_lenient
    from ..providers import explicit_primary_role

    if not owns_gate_surface(provider_config, provider):
        return None
    role = explicit_primary_role(provider_config, provider)
    if role is None:
        return None
    rel = _settings_path(agent_meta_root, pc)
    if rel is None:
        return None
    path = agent_meta_root / rel
    if not path.is_file():
        return None
    try:
        document = read_json_lenient(path)
    except OSError:
        return None
    if not isinstance(document, dict):
        return None
    current = document.get("default_agent")
    if not (isinstance(current, str) and current) or current != role:
        return None
    state = _read_state(agent_meta_root / _OPENCODE_STATE_FILE, _STATE_DEFAULT_AGENT_KEY)
    managed = isinstance(state, dict) and state.get("value") == current
    return None if managed else current


def _append_once(
    findings: list, seen: set, check: str, file: str, message: str, suggestion: str
) -> None:
    """Append at most one WARNING per (check ID, provider) and run."""
    if check in seen:
        return
    seen.add(check)
    findings.append(Finding(
        severity=Severity.WARNING,
        check=check,
        file=file,
        message=message,
        suggestion=suggestion,
    ))


def check_orchestrator_topology(
    agent_meta_root: Path,
    project_config: dict,
    *,
    provider_config: Optional[dict] = None,
    capabilities: Optional[dict] = None,
    providers: Optional[list] = None,
    active_set=None,
) -> list:
    """Read-only WARNING findings for the resolved orchestrator topology.

    Args:
        agent_meta_root: Framework checkout that holds ``config/`` and (for a
            self-hosted project) the emitted provider documents.
        project_config: Loaded ``.meta-config/project.yaml`` mapping.
        provider_config: Pre-loaded ``ai-providers.yaml`` mapping. Loaded when
            omitted.
        capabilities: Pre-loaded ``provider-capabilities.yaml`` mapping.
            Loaded when omitted.
        providers: Pre-resolved active providers. Resolved from *config* when
            omitted.
        active_set: The per-run ActiveSet (or any object exposing ``roles``).
            Computed from *project_config* when omitted.

    Returns:
        WARNING findings; never raises.
    """
    findings: list = []
    try:
        config = project_config if isinstance(project_config, dict) else {}
        orch = _orchestrator_block(config)

        if provider_config is None:
            from ..providers import load_providers_config

            provider_config = load_providers_config(agent_meta_root, config)
        if not isinstance(provider_config, dict):
            provider_config = {}
        if capabilities is None:
            from ..providers import load_provider_capabilities

            capabilities = load_provider_capabilities(agent_meta_root)
        if not isinstance(capabilities, dict):
            capabilities = {}
        if providers is None:
            from ..providers import resolve_providers

            providers = resolve_providers(config, provider_config)
        if active_set is None:
            from ..active_set import compute_active_set

            active_set = compute_active_set(
                config, agent_meta_root, agent_meta_root, warn_sink=[]
            )

        from ..providers import explicit_primary_role
        from ..variables import _resolve_orch_mode

        project_topology = orch.get("topology")
        for provider in providers:
            pc = provider_config.get(provider)
            pc = pc if isinstance(pc, dict) else {}
            caps = capabilities.get(provider)
            caps = caps if isinstance(caps, dict) else {}
            override = _provider_override(orch, provider)
            mode = _resolve_orch_mode(orch, override, validate=False)
            resolution = resolve_topology(
                config,
                provider,
                provider_config=provider_config,
                capabilities=caps,
                mode=mode,
                active_set=active_set,
                validate=False,
            )
            seen: set = set()

            if resolution.degraded_from is not None:
                _append_once(
                    findings,
                    seen,
                    CHECK_DEGRADED,
                    _PROJECT_CONFIG,
                    f"orchestrator topology for provider '{provider}' was declared "
                    f"as '{resolution.degraded_from}' but resolves to "
                    f"'{resolution.effective}'"
                    + (
                        f" ({resolution.degradation_reason})"
                        if resolution.degradation_reason
                        else ""
                    )
                    + ".",
                    "The capability cell cannot support the declared position; "
                    "the sync uses the fail-safe/degrade value. Accept it, or "
                    "upgrade the provider capability with recorded evidence.",
                )

            verified = caps.get("topology_verified_state")
            verified = verified if isinstance(verified, dict) else {}
            if resolution.declared == "hybrid" and verified.get("hybrid") == "UNVERIFIED":
                _append_once(
                    findings,
                    seen,
                    CHECK_HYBRID_UNVERIFIED,
                    _PROJECT_CONFIG,
                    f"orchestrator topology 'hybrid' is declared for provider "
                    f"'{provider}' while topology_verified_state.hybrid is "
                    "UNVERIFIED; it resolves to "
                    f"'{resolution.effective}'.",
                    "Treat 'hybrid' as designed-but-not-shipped until a recorded "
                    "probe upgrades the cell, or declare 'primary'/'subagent'.",
                )

            if (
                project_topology is not None
                and _main_chat_override(override)
                and override.get("topology") is None
            ):
                _append_once(
                    findings,
                    seen,
                    CHECK_MAIN_CHAT_SUPERSEDES,
                    _PROJECT_CONFIG,
                    f"orchestrator.topology is set at project scope, but "
                    f"provider-overrides.{provider}.mode is 'main-chat'; the "
                    "provider-scoped mode wins and the topology is inert for "
                    f"provider '{provider}'.",
                    f"Remove provider-overrides.{provider}.mode: main-chat to "
                    "honour the topology, or move the topology into that provider "
                    "override and remove the project key.",
                )

            role = explicit_primary_role(provider_config, provider)
            gate_role_emitted = False
            if role is not None:
                from ..active_set import role_emitted_for_provider

                gate_role_emitted = role_emitted_for_provider(
                    role, active_set, config, provider
                )
            if (
                resolution.effective != "primary"
                and gate_role_emitted
                and _gate_wanted(orch, provider, pc, caps, agent_meta_root)
            ):
                _append_once(
                    findings,
                    seen,
                    CHECK_GATE_INACTIVE,
                    _PROJECT_CONFIG,
                    f"runtime gate is wanted for provider '{provider}', but the "
                    f"effective orchestrator topology is '{resolution.effective}', "
                    "so no default_agent/entry point is written and the deny is "
                    "deliberately withheld.",
                    "Set orchestrator.topology: primary to activate the gate, or "
                    "disable the runtime gate for this provider via "
                    "orchestrator.provider-overrides.",
                )

            conflict = _user_owned_default_agent(
                agent_meta_root, provider_config, provider, pc, resolution.effective
            )
            if conflict is not None:
                settings = _settings_path(agent_meta_root, pc) or _PROJECT_CONFIG
                _append_once(
                    findings,
                    seen,
                    CHECK_DEFAULT_AGENT_CONFLICT,
                    settings,
                    f"default_agent '{conflict}' names the orchestrator role, but "
                    f"the effective orchestrator topology for provider "
                    f"'{provider}' is '{resolution.effective}'.",
                    "The user value is left untouched (no auto-delete); remove "
                    "the key or set orchestrator.topology: primary.",
                )
    except Exception:  # noqa: BLE001 — a checker must never fail the suite
        return findings

    return findings
