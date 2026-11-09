"""Provider parity in the rules render seam (G3/G2, AC-14/AC-18/AC-30).

Issue #1190, plan §5 Task 4.

``rules._merged_rule_vars`` overwrites the provider-less (non-authoritative)
``ORCH_TOPOLOGY_EFFECTIVE_*`` basis from ``config._build_orch_variables`` with
the *provider-scoped* resolution — via the one helper
``variables._provider_topology_flags``. The same per-sync ActiveSet used by the
emission side reaches the rules seam (AC-30); the helper never resolves an
ActiveSet and never re-resolves the orchestrator mode.

Contract under test:

* a provider override changes ``EFFECTIVE`` for THAT provider only, while the
  declaration flags keep their existing semantics;
* a derived position needs the ActiveSet — without the role the derivation
  fails safe to ``subagent`` even though ``primary-role`` is declared;
* the ActiveSet object passed by the caller is the object the resolver sees
  (identity, not an equal copy).

Run: python3 -m pytest tests/test_orchestrator_topology_render_parity.py -q
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

import scripts.lib.topology as topology_module  # noqa: E402
from scripts.lib.rules import _merged_rule_vars  # noqa: E402


def test_rules_render_effective_flags_per_provider():
    """Provider override wins for its provider; another provider keeps the project value."""
    config = {
        "orchestrator": {
            "topology": "primary",
            "provider-overrides": {"Opencode": {"topology": "subagent"}},
        },
    }

    opencode = _merged_rule_vars(
        _REPO_ROOT, _REPO_ROOT, config, "Opencode", {}, {},
        active_set=frozenset(),
    )
    assert opencode["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "true"
    assert opencode["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "false"

    claude = _merged_rule_vars(
        _REPO_ROOT, _REPO_ROOT, config, "Claude", {}, {},
        active_set=frozenset(),
    )
    assert claude["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "true"
    assert claude["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "project"


def test_rules_derivation_uses_active_set():
    """Derived position: declared stays "" while effective follows the ActiveSet."""
    merged = _merged_rule_vars(
        _REPO_ROOT, _REPO_ROOT, {}, "Opencode", {}, None,
        active_set=frozenset({"orchestrator"}),
    )

    assert merged["ORCH_TOPOLOGY_EFFECTIVE"] == "primary"
    # ``Opencode`` declares ``primary-role: orchestrator``; nothing was written
    # to the config, so the DECLARED axis must stay empty (fail-closed).
    assert merged["ORCH_TOPOLOGY"] == ""


def test_rules_passes_the_shared_active_set(monkeypatch):
    """The caller's ActiveSet object reaches ``resolve_topology`` unchanged (AC-30)."""
    seen = []
    original = topology_module.resolve_topology

    def recording_resolve_topology(*args, **kwargs):
        seen.append(kwargs.get("active_set"))
        return original(*args, **kwargs)

    monkeypatch.setattr(topology_module, "resolve_topology", recording_resolve_topology)

    sentinel = frozenset({"sentinel-role"})

    opencode = _merged_rule_vars(
        _REPO_ROOT, _REPO_ROOT, {}, "Opencode", {}, None, active_set=sentinel,
    )
    claude = _merged_rule_vars(
        _REPO_ROOT, _REPO_ROOT, {}, "Claude", {}, None, active_set=sentinel,
    )

    # Neither provider's primary role is in the set => both fail safe.
    assert opencode["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert claude["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert any(record is sentinel for record in seen), (
        f"the caller's ActiveSet never reached resolve_topology: {seen!r}"
    )
