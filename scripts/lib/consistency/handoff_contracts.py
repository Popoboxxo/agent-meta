"""Handoff-contract cross-validation over config/role-defaults.yaml.

Validates the A2A handoff wiring declared under each role's ``handoff`` block:

* target_roles existence  — referenced roles must be defined roles.
* output -> input matching — a role's output_contract should be consumed by
  at least one of its declared target_roles.
* input without producer   — a declared input_contract should be produced by
  some role as its output_contract.

Roles without a ``handoff`` block are skipped. ``task-spec-v1`` is produced
by the orchestrator at runtime and is exempt from the producer check.
"""
from __future__ import annotations

from pathlib import Path

from .report import Finding, Severity

_ROLE_DEFAULTS = "config/role-defaults.yaml"

# Contracts that are produced outside of role-defaults.yaml (e.g. emitted by
# the orchestrator at runtime) and must not trigger a "no producer" warning.
# blocked-review-v1 is emitted by the reflection-loop machinery when a loop hits
# its on_blocked threshold and escalates to principal-developer — there is no
# single role that declares it as output_contract.
_RUNTIME_CONTRACTS = {"task-spec-v1", "blocked-review-v1"}


def _load_roles(agent_meta_root: Path) -> dict | None:
    """Load the ``roles`` mapping from role-defaults.yaml, or None on failure."""
    roles_path = agent_meta_root / "config" / "role-defaults.yaml"
    if not roles_path.exists():
        return None
    try:
        import yaml
    except ImportError:
        return None
    try:
        data = yaml.safe_load(roles_path.read_text(encoding="utf-8")) or {}
    except Exception:  # noqa: BLE001
        return None
    roles = data.get("roles", {})
    return roles if isinstance(roles, dict) else {}


def _handoff(cfg: dict) -> dict | None:
    """Return the handoff block of a role config, or None when absent."""
    if not isinstance(cfg, dict):
        return None
    h = cfg.get("handoff")
    return h if isinstance(h, dict) else None


def check_handoff_contracts(agent_meta_root: Path) -> list[Finding]:
    """Cross-validate handoff contracts declared in role-defaults.yaml."""
    findings: list[Finding] = []
    roles = _load_roles(agent_meta_root)
    if roles is None:
        return findings

    role_names = set(roles.keys())

    # Collect all output_contracts offered by any role → set of producer roles.
    producers: dict[str, set[str]] = {}
    for name, cfg in roles.items():
        h = _handoff(cfg)
        if not h:
            continue
        oc = h.get("output_contract")
        if oc:
            producers.setdefault(oc, set()).add(name)

    for name, cfg in roles.items():
        h = _handoff(cfg)
        if not h:
            continue  # roles without handoff are skipped

        targets = h.get("target_roles") or []
        if not isinstance(targets, list):
            targets = []
        output_contract = h.get("output_contract")
        input_contracts = h.get("input_contracts") or []
        if not isinstance(input_contracts, list):
            input_contracts = []

        # 2a) target_roles existence
        for target in targets:
            if target not in role_names:
                findings.append(Finding(
                    Severity.ERROR, "handoff.target-role-missing",
                    _ROLE_DEFAULTS,
                    f"target_role '{target}' referenced by '{name}' does not exist.",
                    f"Add a '{target}:' role to config/role-defaults.yaml or "
                    f"fix the target_roles entry of '{name}'.",
                ))

        # 2b) output -> input matching among declared target_roles
        if output_contract and targets:
            consumed = any(
                output_contract in ((_handoff(roles.get(t)) or {}).get("input_contracts") or [])
                for t in targets
                if t in role_names
            )
            if not consumed:
                findings.append(Finding(
                    Severity.WARNING, "handoff.output-not-consumed",
                    _ROLE_DEFAULTS,
                    f"output_contract '{output_contract}' of '{name}' is not "
                    f"consumed by any target_role (possible silent handoff failure).",
                    f"Add '{output_contract}' to the input_contracts of one of: "
                    f"{', '.join(targets)}.",
                ))

        # 2c) input_contracts without producer
        for contract in input_contracts:
            if contract in _RUNTIME_CONTRACTS:
                continue  # runtime-produced, no role-level producer expected
            if contract not in producers:
                findings.append(Finding(
                    Severity.WARNING, "handoff.input-no-producer",
                    _ROLE_DEFAULTS,
                    f"input_contract '{contract}' of '{name}' has no producer.",
                    f"Declare '{contract}' as output_contract on the producing "
                    f"role, or remove it from the input_contracts of '{name}'.",
                ))

    return findings
