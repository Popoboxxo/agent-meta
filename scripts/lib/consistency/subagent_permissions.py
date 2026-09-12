"""Consistency checks for the subagent-permission policy (Feature A).

Two checks:

* ``check_subagent_permission_support`` — project-aware, WARNING-only. Reports
  an invalid mode value, a ``strict`` provider without a subagent-dispatch
  surface, or a ``strict`` provider without mirrored PreToolUse hooks.
* ``check_subagent_permission_templates`` — framework-source drift, ERROR-only.
  Verifies the rule/orchestrator templates still carry the conditional markers
  and the boolean-flag allowlist, per file (M5).

Capability sources (B1): ``subagent_dispatch`` is a TOP-LEVEL boolean read via
``load_provider_capabilities`` (``config/provider-capabilities.yaml``); the hook
question is answered by ``provider_hooks_supported`` on the provider's
``ai-providers.yaml`` entry. ``provider_has_capability(pc, "subagent_dispatch")``
is wrong by construction — that list lives in a different registry.

Fail-soft (M3): this module never calls ``sys.exit`` and never uses
``try/except SystemExit``; invalid values resolve to ``"off"`` plus a WARNING.
"""
from __future__ import annotations

import re
from pathlib import Path

from ..providers import (
    load_provider_capabilities,
    provider_hooks_supported,
    resolve_providers,
)
from ..subagent_permissions import (
    invalid_subagent_permission_entries,
    resolve_effective_subagent_permission_mode,
)
from ..variables import _BOOLEAN_SUBAGENT_PERMISSION_FLAGS
from .report import Finding, Severity

_CONFIG_FILE = "config/provider-capabilities.yaml"
_PROJECT_FILE = ".meta-config/project.yaml"
_RULE_TEMPLATE = "rules/1-generic/a2a-delegation-gates.md"
_ORCHESTRATOR_TEMPLATE = "agents/1-generic/orchestrator.md"

# The single non-boolean SUBAGENT_PERMISSIONS_* variable — a mode STRING, never
# a usable {{#if}} conditional, but explicitly not an "unknown flag" either.
_SUBAGENT_PERMISSIONS_MODE_VAR = "SUBAGENT_PERMISSIONS_MODE"

_CONDITIONAL_RE = re.compile(r"\{\{#if\s+(SUBAGENT_PERMISSIONS_[A-Z0-9_]+)\s*\}\}")


def check_subagent_permission_support(
    project_root: Path,
    agent_meta_root: Path,
    config: dict,
    provider_config: dict,
) -> list[Finding]:
    """WARNING-only support check for the effective subagent-permission modes.

    ``project_root`` is accepted for signature parity with the other
    project-aware checks; the report anchors findings at ``.meta-config``.
    """
    del project_root  # reserved for future project-relative paths
    findings: list[Finding] = []

    for path in invalid_subagent_permission_entries(config):
        findings.append(Finding(
            Severity.WARNING,
            "subagent-permissions.invalid-mode",
            _PROJECT_FILE,
            f"Invalid subagent-permissions mode value at '{path}' — "
            "it resolves to 'off' (safe-side).",
            "Use one of: strict, warn, off (quote the value in YAML).",
        ))

    caps = load_provider_capabilities(agent_meta_root)
    try:
        active_providers = resolve_providers(config, provider_config)
    except ValueError:
        # Unknown provider names are hard-rejected by config._validate_providers
        # on the sync path; direct callers just get no per-provider findings.
        return findings

    for provider in active_providers:
        if resolve_effective_subagent_permission_mode(config, provider) != "strict":
            continue

        provider_caps = caps.get(provider) or {}
        if provider_caps.get("subagent_dispatch") is not True:
            findings.append(Finding(
                Severity.WARNING,
                "subagent-permissions.no-dispatch-surface",
                _CONFIG_FILE,
                f"Provider '{provider}' has subagent_permissions.mode='strict' "
                "but provider-capabilities.yaml does not declare "
                "subagent_dispatch: true — there is no verified subagent "
                "dispatch surface to gate.",
                "Verify/declare subagent_dispatch for this provider, or set "
                "subagent_permissions.mode to 'warn'/'off'.",
            ))

        if not provider_hooks_supported(provider_config.get(provider, {}) or {}):
            findings.append(Finding(
                Severity.WARNING,
                "subagent-permissions.no-hook-support",
                _CONFIG_FILE,
                f"Provider '{provider}' has subagent_permissions.mode='strict' "
                "but no verified PreToolUse hook wiring (has_hooks + verified "
                "hook_protocol). The policy remains prompt-based here; only the "
                "optional hook secondary stage is unavailable.",
                "Confirm the provider's hook_protocol, or accept the "
                "prompt-only enforcement (WARNING, never a hard fail).",
            ))

    return findings


def check_subagent_permission_templates(agent_meta_root: Path) -> list[Finding]:
    """ERROR-only drift check of the framework-source policy templates.

    Only runs when at least one provider declares a subagent-dispatch surface;
    a framework without one has no policy to ship. Per-file checks (M5): the
    rule's conditional marker and the orchestrator's block placeholder are
    validated independently, never with a combined ``or``.
    """
    caps = load_provider_capabilities(agent_meta_root)
    if not any(
        isinstance(entry, dict) and entry.get("subagent_dispatch") is True
        for entry in caps.values()
    ):
        return []

    findings: list[Finding] = []

    rule_path = agent_meta_root / _RULE_TEMPLATE
    rule_text = _read(rule_path)
    if rule_text is None or not (
        "{{#if SUBAGENT_PERMISSIONS_STRICT}}" in rule_text
        or "{{#if SUBAGENT_PERMISSIONS_WARN}}" in rule_text
    ):
        findings.append(Finding(
            Severity.ERROR,
            "subagent-permissions.template-missing",
            _RULE_TEMPLATE,
            "The A2A delegation-gates rule is missing (or no longer carries "
            "the {{#if SUBAGENT_PERMISSIONS_STRICT}} / "
            "{{#if SUBAGENT_PERMISSIONS_WARN}} markers) — the subagent "
            "permission policy would never be delivered.",
            "Restore the strict/warn conditional blocks in "
            "rules/1-generic/a2a-delegation-gates.md.",
        ))

    orch_path = agent_meta_root / _ORCHESTRATOR_TEMPLATE
    orch_text = _read(orch_path)
    if orch_text is None or "{{SUBAGENT_PERMISSIONS_BLOCK}}" not in orch_text:
        findings.append(Finding(
            Severity.ERROR,
            "subagent-permissions.template-missing",
            _ORCHESTRATOR_TEMPLATE,
            "The orchestrator template does not reference "
            "{{SUBAGENT_PERMISSIONS_BLOCK}} — the policy would never reach the "
            "orchestrator prompt.",
            "Add {{#if SUBAGENT_PERMISSIONS_ENABLED}}{{SUBAGENT_PERMISSIONS_BLOCK}}"
            "{{/if}} after §5 of agents/1-generic/orchestrator.md.",
        ))

    findings.extend(_check_strippable_flags(rule_text, _RULE_TEMPLATE))
    findings.extend(_check_strippable_flags(orch_text, _ORCHESTRATOR_TEMPLATE))

    return findings


def _check_strippable_flags(text: str | None, label: str) -> list[Finding]:
    """ERROR for unknown ``{{#if SUBAGENT_PERMISSIONS_*}}`` flags (m2/n1).

    Only booleans are strippable; ``SUBAGENT_PERMISSIONS_MODE`` is a known
    non-boolean and is therefore not flagged as an unknown flag.
    """
    if not text:
        return []
    findings: list[Finding] = []
    for name in sorted(set(_CONDITIONAL_RE.findall(text))):
        if name in _BOOLEAN_SUBAGENT_PERMISSION_FLAGS:
            continue
        if name == _SUBAGENT_PERMISSIONS_MODE_VAR:
            continue
        findings.append(Finding(
            Severity.ERROR,
            "subagent-permissions.flag-not-strippable",
            label,
            f"{{{{#if {name}}}}} uses a SUBAGENT_PERMISSIONS_* name that is not "
            "a strippable boolean flag — the conditional block would never be "
            "removed.",
            "Use only SUBAGENT_PERMISSIONS_STRICT/WARN/OFF/ENABLED as "
            "conditionals.",
        ))
    return findings


def _read(path: Path) -> str | None:
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None
