"""Post-sync FANOUT/PARALLEL_GROUP backend-contract check (issue #265).

Cross-validates the FANOUT/BARRIER wiring across the three config surfaces:

* ``config/provider-capabilities.yaml`` — ``fanout_mechanism`` /
  ``barrier_collect`` (the backend capability contract),
* ``config/delegation-syntax.yaml`` — the per-provider ``fanout`` /
  ``parallel_group`` syntax (the prompt-side pattern),
* ``agents/1-generic/orchestrator.md`` — the §7 result wrapper that
  ``scripts.lib.orchestration.render_barrier_result`` emits.

Drift between these surfaces fails closed as ERROR findings — this is a
**convention boundary** (fail-closed against accidental drift, per the
guard-terminologie in AGENTS.md), not a security boundary.

The registry input itself is validated fail-closed too: a missing, empty,
or unparseable ``config/provider-capabilities.yaml`` is an ERROR finding
(``fanout.capabilities-missing``) and the registry-dependent per-provider
checks are skipped in that case — an unusable registry never passes
silently as "no drift".

Checks:

1. Mechanism validity — every capability entry's ``fanout_mechanism`` key
   must be one of the known mechanisms (unknown key = ERROR via the
   ``DelegationSyntaxEngine.get_fanout_mechanism`` validation); providers
   with ``parallel_execution: true`` must have a mechanism at all.
2. Mechanism/capability consistency — ``sequential-fallback`` must not
   coexist with ``parallel_execution: true``; async mechanisms must not
   coexist with ``parallel_execution: false``; ``barrier_collect`` must be
   true exactly for async mechanisms.
3. Syntax coverage — async mechanisms require non-empty ``fanout`` and
   ``parallel_group`` syntax; ``sequential-fallback`` fanout text must carry
   sequential wording (a parallel-batch instruction on a provider whose
   parallelism is unverified would reintroduce the "Parallel Illusion").
   Syntax keys defined WITHOUT a mechanism mapping are flagged as a gap.
4. §7 marker drift — the ``||| agent=`` marker emitted by
   ``render_barrier_result`` (``BARRIER_ENTRY_MARKER``) must still be
   referenced by the orchestrator template.
5. Native tool surface — ``tool-mediated``/``swarm`` mechanisms need a
   non-empty ``native_agent_tools`` list (a named tool must exist to
   dispatch/collect through).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any

from ..delegation_syntax import (
    FANOUT_MECHANISMS,
    DelegationSyntaxEngine,
)
from ..orchestration import BARRIER_ENTRY_MARKER
from .report import Finding, Severity

_PROVIDER_CAPABILITIES = "config/provider-capabilities.yaml"
_DELEGATION_SYNTAX = "config/delegation-syntax.yaml"
_ORCHESTRATOR_TEMPLATE = "agents/1-generic/orchestrator.md"

# Mechanisms that dispatch in parallel (mirror of
# delegation_syntax._ASYNC_FANOUT_MECHANISMS — the private constant is not
# imported on purpose so the check states its own contract).
_ASYNC_MECHANISMS = frozenset(FANOUT_MECHANISMS - {"sequential-fallback"})

# Wording that a sequential-fallback fanout/parallel_group text must contain
# (case-insensitive). Aligned with the delegation-syntax.yaml fallback texts
# ("nacheinander", "der Reihe nach", "sequenziell").
_SEQUENTIAL_FALLBACK_MARKERS = (
    "nacheinander",
    "der reihe nach",
    "sequenziell",
    "sequential",
    "sequentially",
)


def check_fanout_backend_contract(agent_meta_root: Path) -> list[Finding]:
    """Validate FANOUT/BARRIER backend contracts against the syntax registry.

    Fail-closed on the registry input itself: a missing, empty, or
    unparseable ``config/provider-capabilities.yaml`` is reported as an
    ERROR finding (``fanout.capabilities-missing``) and the
    registry-dependent per-provider checks are skipped — the §7
    marker-drift check is registry-independent and still runs.
    """
    findings: list[Finding] = []
    config_dir = agent_meta_root / "config"
    capabilities_file = config_dir / "provider-capabilities.yaml"

    capabilities: dict[str, Any] = {}
    missing_registry = not capabilities_file.exists()
    if not missing_registry:
        engine = DelegationSyntaxEngine(config_dir=config_dir)
        loaded = engine.capabilities_registry.get("capabilities")
        if isinstance(loaded, dict) and loaded:
            capabilities = loaded

    # ── 0. Registry input itself (fail-closed) ─────────────────────────
    if not capabilities:
        if missing_registry:
            message = (
                f"{_PROVIDER_CAPABILITIES} does not exist — the "
                "per-provider FANOUT backend contract (fanout_mechanism / "
                "barrier_collect) cannot be validated (fail-closed)."
            )
            suggestion = (
                "Restore config/provider-capabilities.yaml (framework "
                "config shipped with agent-meta)."
            )
        else:
            message = (
                f"{_PROVIDER_CAPABILITIES} exists but yields no usable "
                "'capabilities' mapping (empty file, invalid YAML, or "
                "missing/empty key) — the per-provider FANOUT backend "
                "contract cannot be validated (fail-closed)."
            )
            suggestion = (
                "Fix config/provider-capabilities.yaml: top-level "
                "'capabilities' mapping with one entry per provider."
            )
        findings.append(Finding(
            Severity.ERROR, "fanout.capabilities-missing",
            _PROVIDER_CAPABILITIES,
            message,
            suggestion,
        ))

    # ── 1-3, 5. Per-provider checks — skipped entirely when the registry
    #    input is unusable (they cannot produce meaningful findings). ────
    for provider, caps in sorted(capabilities.items()):
        if not isinstance(caps, dict):
            continue
        parallel_execution = bool(caps.get("parallel_execution", False))
        barrier_collect = bool(caps.get("barrier_collect", False))

        # ── 1. Mechanism validity ────────────────────────────────────────
        try:
            mechanism = engine.get_fanout_mechanism(provider)
        except ValueError as exc:
            findings.append(Finding(
                Severity.ERROR, "fanout.unknown-mechanism",
                _PROVIDER_CAPABILITIES,
                str(exc),
                "Use one of: " + ", ".join(sorted(FANOUT_MECHANISMS)) + ".",
            ))
            mechanism = None

        if mechanism is None and parallel_execution:
            findings.append(Finding(
                Severity.ERROR, "fanout.mechanism-missing",
                _PROVIDER_CAPABILITIES,
                f"Provider '{provider}' has parallel_execution: true but no "
                "fanout_mechanism mapping — FANOUT patterns have no backend contract.",
                f"Set fanout_mechanism for '{provider}' in provider-capabilities.yaml "
                "(conservative default when unverified: sequential-fallback).",
            ))

        # ── 2. Mechanism/capability consistency ──────────────────────────
        if mechanism == "sequential-fallback" and parallel_execution:
            findings.append(Finding(
                Severity.ERROR, "fanout.mechanism-capability-mismatch",
                _PROVIDER_CAPABILITIES,
                f"Provider '{provider}' has parallel_execution: true but "
                "fanout_mechanism: sequential-fallback — contradictory contract.",
                "Verify and declare the real mechanism, or set "
                "parallel_execution: false.",
            ))
        if mechanism in _ASYNC_MECHANISMS and not parallel_execution:
            findings.append(Finding(
                Severity.ERROR, "fanout.mechanism-capability-mismatch",
                _PROVIDER_CAPABILITIES,
                f"Provider '{provider}' declares fanout_mechanism: {mechanism} "
                "but parallel_execution: false — the async mechanism has no "
                "verified parallel contract.",
                "Verify parallel_execution first, or map "
                "fanout_mechanism: sequential-fallback.",
            ))
        expected_barrier = mechanism in _ASYNC_MECHANISMS
        if barrier_collect != expected_barrier:
            findings.append(Finding(
                Severity.ERROR, "fanout.barrier-collect-mismatch",
                _PROVIDER_CAPABILITIES,
                f"Provider '{provider}': barrier_collect is {barrier_collect} "
                f"but fanout_mechanism '{mechanism}' implies {expected_barrier}.",
                f"Set barrier_collect: {str(expected_barrier).lower()} for "
                f"mechanism '{mechanism}'.",
            ))

        # ── 3. Syntax coverage ───────────────────────────────────────────
        syntax = engine.get_syntax(provider)
        fanout_text = syntax.get("fanout") or ""
        parallel_group_text = syntax.get("parallel_group") or ""
        if mechanism in _ASYNC_MECHANISMS:
            if not fanout_text.strip():
                findings.append(Finding(
                    Severity.ERROR, "fanout.syntax-missing",
                    _DELEGATION_SYNTAX,
                    f"Provider '{provider}' uses async mechanism '{mechanism}' "
                    "but has no fanout syntax in delegation-syntax.yaml — "
                    "generated agents would receive no FANOUT pattern.",
                    f"Add a 'fanout' entry under delegation_syntax.{provider} "
                    "matching the mechanism.",
                ))
            if not parallel_group_text.strip():
                findings.append(Finding(
                    Severity.ERROR, "fanout.syntax-missing",
                    _DELEGATION_SYNTAX,
                    f"Provider '{provider}' uses async mechanism '{mechanism}' "
                    "but has no parallel_group syntax in delegation-syntax.yaml.",
                    f"Add a 'parallel_group' entry under "
                    f"delegation_syntax.{provider} matching the mechanism.",
                ))
        elif mechanism == "sequential-fallback":
            for key, text in (("fanout", fanout_text), ("parallel_group", parallel_group_text)):
                lowered = text.lower()
                if lowered and not any(marker in lowered for marker in _SEQUENTIAL_FALLBACK_MARKERS):
                    findings.append(Finding(
                        Severity.ERROR, "fanout.sequential-wording-missing",
                        _DELEGATION_SYNTAX,
                        f"Provider '{provider}' is sequential-fallback but its "
                        f"'{key}' syntax reads like a parallel-dispatch "
                        "instruction — reintroduces the Parallel Illusion.",
                        f"Rewrite delegation_syntax.{provider}.{key} as an "
                        "explicitly sequential instruction "
                        "(e.g. 'der Reihe nach' / 'nacheinander').",
                    ))
        elif mechanism is None and (fanout_text.strip() or parallel_group_text.strip()):
            findings.append(Finding(
                Severity.WARNING, "fanout.syntax-without-mechanism",
                _PROVIDER_CAPABILITIES,
                f"Provider '{provider}' defines fanout/parallel_group syntax "
                "but has no fanout_mechanism mapping — the backend contract "
                "for these patterns is undeclared.",
                f"Map fanout_mechanism for '{provider}' "
                "(sequential-fallback when unverified).",
            ))

        # ── 5. Native tool surface for tool-mediated/swarm ────────────────
        if mechanism in ("tool-mediated", "swarm") and not (caps.get("native_agent_tools") or []):
            findings.append(Finding(
                Severity.ERROR, "fanout.tool-surface-missing",
                _PROVIDER_CAPABILITIES,
                f"Provider '{provider}' uses mechanism '{mechanism}' but "
                "native_agent_tools is empty — no named tool exists to "
                "dispatch/collect through.",
                "Declare the dispatch/collect tools in native_agent_tools, or "
                "downgrade to sequential-fallback.",
            ))

    # ── 4. §7 marker drift (registry-independent — runs even when the
    #    capabilities registry is unusable) ──────────────────────────────
    template_path = agent_meta_root / _ORCHESTRATOR_TEMPLATE
    if template_path.exists():
        try:
            template = template_path.read_text(encoding="utf-8")
        except OSError:
            template = ""
        if BARRIER_ENTRY_MARKER not in template:
            findings.append(Finding(
                Severity.ERROR, "fanout.barrier-marker-drift",
                _ORCHESTRATOR_TEMPLATE,
                f"orchestrator template does not reference the §7 result "
                f"wrapper marker '{BARRIER_ENTRY_MARKER}' emitted by "
                "orchestration.render_barrier_result — BARRIER results would "
                "render in a format the prompt no longer documents.",
                "Restore the '||| agent=<name> result_key=<key> |||' wrapper "
                "in orchestrator.md §7 (or update BARRIER_ENTRY_MARKER in "
                "scripts/lib/orchestration.py deliberately).",
            ))
    return findings
