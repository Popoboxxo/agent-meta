"""Consistency check: is orchestrator.strict actually enforceable on every active provider?

``orchestrator.strict`` is only as strong as the runtime gate backing it. The
gate tier per provider is resolved by
``providers.provider_runtime_gate_tier(pc, caps)`` (SPEC-OPENCODE-RUNTIME-GATE-
2026-09-13, IC-03) from the machine flags in ``config/ai-providers.yaml``
(``pc``) plus the declared tier in ``config/provider-capabilities.yaml``
(``caps``). The severity is derived from that tier:

``hook`` / ``plugin``
    Runtime-enforced -> no finding.
``permission``
    Partially enforced: the native permission layer blocks Main-Chat writes,
    but delegation provenance is not enforced (a delegated child session is not
    distinguishable from the Main Chat) -> INFO.
``advisory``
    Prompt adherence only, no runtime enforcement -> WARNING by default, ERROR
    when ``orchestrator.require-runtime-gate`` is ``true`` (opt-in, IC-12).

This mirrors the mode-resolution logic in
hooks/1-generic/orchestrator-guard.sh's resolve_mode() so the two stay in
sync -- provider-overrides can legitimately narrow strict mode to a subset
of providers.
"""

from pathlib import Path

from .. import providers as providers_lib
from .report import Finding, Severity

#: Finding id preserved across the tier re-pointing (IC-11). The id names the
#: historic "no hook support" case; it now covers every non-runtime-enforced tier.
_CHECK_ID = "orchestrator-strict.no-hook-support"


def _resolve_effective_strict(orch: dict, provider: str) -> bool:
    """Mirror resolve_mode() in hooks/1-generic/orchestrator-guard.sh.

    Three precedence tiers, checked in order:
    1. orchestrator.provider-overrides.<provider>.mode
    2. orchestrator.mode (global)
    3. legacy orchestrator.strict + orchestrator.enabled booleans
    """
    if not isinstance(orch, dict):
        return False
    overrides = orch.get("provider-overrides", {}) or {}
    if not isinstance(overrides, dict):
        overrides = {}
    override = overrides.get(provider, {}) or {}
    if not isinstance(override, dict):
        override = {}
    mode = override.get("mode")
    if mode is None:
        mode = orch.get("mode")
    if mode is not None:
        return str(mode).strip().lower() == "strict"
    strict = orch.get("strict", False)
    enabled = orch.get("enabled", True)
    return bool(strict) and bool(enabled)


def _require_runtime_gate(orch: dict) -> bool:
    """Defensive read of the opt-in sibling key (IC-12).

    ``orchestrator`` is an open block in the schema, so the value may be
    missing or malformed at runtime. Anything other than an explicit ``True``
    is the backwards-compatible default ``false``.
    """
    if not isinstance(orch, dict):
        return False
    return orch.get("require-runtime-gate", False) is True


def check_orchestrator_strict_hook_support(project_root: Path, config: dict,
                                            provider_config: dict,
                                            agent_meta_root: Path) -> list[Finding]:
    """Report when orchestrator.strict is active but not runtime-enforced.

    ``project_root`` is used for finding paths only; the capability registry is
    loaded from ``agent_meta_root`` (F-12). An unreadable registry degrades to
    the fail-safe ``advisory`` tier via ``load_provider_capabilities`` -- the
    check never raises.
    """
    findings: list[Finding] = []
    orch = config.get("orchestrator", {})
    if not orch:
        return findings

    capabilities = providers_lib.load_provider_capabilities(agent_meta_root)

    active_providers = providers_lib.resolve_providers(config, provider_config)
    for provider in active_providers:
        if not _resolve_effective_strict(orch, provider):
            continue
        pc = provider_config.get(provider, {})
        caps = capabilities.get(provider, {})
        tier = providers_lib.provider_runtime_gate_tier(pc, caps)
        if tier in ("hook", "plugin"):
            continue
        if tier == "permission":
            findings.append(Finding(
                Severity.INFO,
                _CHECK_ID,
                ".meta-config/project.yaml",
                f"orchestrator.strict is active for provider '{provider}', but "
                f"enforcement is only partial (tier 'permission'): the native "
                f"permission layer blocks Main-Chat writes, but delegation "
                f"provenance is not enforced.",
                f"Accept the partial guarantee for '{provider}', or scope strict "
                f"mode to hook/plugin-capable providers via provider-overrides.",
            ))
            continue
        severity = Severity.ERROR if _require_runtime_gate(orch) else Severity.WARNING
        findings.append(Finding(
            severity,
            _CHECK_ID,
            ".meta-config/project.yaml",
            f"orchestrator.strict is active for provider '{provider}', but this "
            f"provider has no runtime enforcement (tier 'advisory') -- the "
            f"setting is prompt-only and has no runtime effect there.",
            f"Add a provider-overrides entry to scope strict mode to providers "
            f"with runtime enforcement (hook/plugin/permission), or set "
            f"orchestrator.require-runtime-gate to true to fail the check.",
        ))
    return findings
