"""Runtime-gate seam: canonical tier vocabulary for provider gate enforcement.

The CRITICAL GATE ("MAIN CHAT darf nicht selbst editieren. ALLES ->
``orchestrator``. Keine Ausnahmen.") is only as strong as the provider runtime
that backs it. This module owns the canonical vocabulary that names **how** a
provider enforces the gate, so every consumer (resolver, rendering, consistency)
speaks the same four tiers:

``hook``
    Verified PreToolUse hook contract (the provider mirrors the framework hook
    scripts and the runtime blocks the tool call).
``plugin``
    Verified native plugin runtime (Phase 1, capability-gated; DEFERRED until
    the P6 real-repo verification is recorded).
``permission``
    Native permission layer blocks Main-Chat writes. **Partial**: the block
    carries no delegation provenance (a delegated child session is not
    distinguishable from the Main Chat).
``advisory``
    Prompt adherence only — no runtime enforcement. This is the fail-safe
    default for a provider without a resolved, stronger tier.

Seam boundary (IC-03): this module owns the vocabulary only. The tier
*resolver* (`provider_runtime_gate_tier`) lives in ``providers.py`` next to the
other capability resolvers, so there is exactly one source of truth. Phase 1
extends this module with the plugin generator (IC-08); Phase 0 ships only the
vocabulary below.
"""
from __future__ import annotations

from typing import Tuple

#: Canonical gate tiers, ordered strongest first. Consumers must treat any
#: value outside this tuple as an unknown tier and fail safe to ``advisory``.
RUNTIME_GATE_TIERS: Tuple[str, ...] = ("hook", "plugin", "permission", "advisory")
