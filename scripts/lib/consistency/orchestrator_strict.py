"""Consistency check: is orchestrator.strict actually enforceable on every active provider?

hooks/1-generic/orchestrator-guard.sh is the only runtime enforcement of
orchestrator.strict -- and scripts/lib/hooks.py only wires PreToolUse hooks
for providers whose config/ai-providers.yaml entry sets has_hooks: true
(currently Claude, Mammouth). On every other active provider (Opencode,
Gemini, Continue, Copilot as of this writing), orchestrator.strict is a
silent no-op: the setting exists in .meta-config/project.yaml, but nothing
enforces it. This mirrors the mode-resolution logic in
hooks/1-generic/orchestrator-guard.sh's resolve_mode() so the two stay in
sync -- provider-overrides can legitimately narrow strict mode to a subset
of providers.
"""

from pathlib import Path

from .. import providers as providers_lib
from .report import Finding, Severity


def _resolve_effective_strict(orch: dict, provider: str) -> bool:
    """Mirror resolve_mode() in hooks/1-generic/orchestrator-guard.sh.

    Three precedence tiers, checked in order:
    1. orchestrator.provider-overrides.<provider>.mode
    2. orchestrator.mode (global)
    3. legacy orchestrator.strict + orchestrator.enabled booleans
    """
    override = orch.get("provider-overrides", {}).get(provider, {})
    mode = override.get("mode")
    if mode is None:
        mode = orch.get("mode")
    if mode is not None:
        return str(mode).strip().lower() == "strict"
    strict = orch.get("strict", False)
    enabled = orch.get("enabled", True)
    return bool(strict) and bool(enabled)


def check_orchestrator_strict_hook_support(project_root: Path, config: dict,
                                            provider_config: dict) -> list[Finding]:
    """Warn when orchestrator.strict is effectively active for a provider with no
    PreToolUse hook wiring (config/ai-providers.yaml has_hooks: false)."""
    findings: list[Finding] = []
    orch = config.get("orchestrator", {})
    if not orch:
        return findings

    active_providers = providers_lib.resolve_providers(config, provider_config)
    for provider in active_providers:
        if not _resolve_effective_strict(orch, provider):
            continue
        pc = provider_config.get(provider, {})
        if pc.get("has_hooks", False):
            continue
        findings.append(Finding(
            Severity.WARNING,
            "orchestrator-strict.no-hook-support",
            ".meta-config/project.yaml",
            f"orchestrator.strict is active for provider '{provider}', but this "
            f"provider has no PreToolUse hook wiring (config/ai-providers.yaml: "
            f"has_hooks: false) -- the setting has no runtime effect there.",
            f"Add a provider-overrides entry to scope strict mode to hook-capable "
            f"providers only, or accept that delegation is not enforced on '{provider}'.",
        ))
    return findings
