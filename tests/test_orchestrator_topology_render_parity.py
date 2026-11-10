"""Provider parity in the rules + context render seams (G3/G2, AC-14/18/20/30).

Issue #1190, plan §5 Tasks 4 and 5.

``rules._merged_rule_vars`` (T4) and the Stage-4 context seam (T5) overwrite the
provider-less (non-authoritative) ``ORCH_TOPOLOGY_EFFECTIVE_*`` basis from
``config._build_orch_variables`` with the *provider-scoped* resolution — via the
one helper ``variables._provider_topology_flags``. The same per-sync ActiveSet
used by the emission side reaches both seams (AC-30); the helper never resolves
an ActiveSet and never re-resolves the orchestrator mode.

Contract under test:

* a provider override changes ``EFFECTIVE`` for THAT provider only, while the
  declaration flags keep their existing semantics;
* a derived position needs the ActiveSet — without the role the derivation
  fails safe to ``subagent`` even though ``primary-role`` is declared;
* the ActiveSet object passed by the caller is the object the resolver sees
  (identity, not an equal copy);
* ``sync_pipeline._sync_stage_contexts`` hands the provider-scoped effective
  flags to ``sync_context_for_provider`` (Stage 4, not Stage 6) and requires the
  per-sync ActiveSet as a keyword — no default that would neuter AC-30;
* one physical ``AGENTS.md`` renders ONE deterministic block with no
  position-specific statement (G5/AC-20).

Run: python3 -m pytest tests/test_orchestrator_topology_render_parity.py -q
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))
# ``sync_pipeline``/``context`` import their peers as ``lib.*`` (scripts root
# on sys.path); the ``scripts.lib.*`` aliases below stay resolvable through the
# repo root entry.
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import scripts.lib.sync_pipeline as sync_pipeline  # noqa: E402
import scripts.lib.topology as topology_module  # noqa: E402
from scripts.lib.agent_sync import _build_provider_vars  # noqa: E402
from scripts.lib.config import load_config  # noqa: E402
from scripts.lib.context import _build_managed_block  # noqa: E402
from scripts.lib.log import SyncLog  # noqa: E402
from scripts.lib.providers import load_providers_config  # noqa: E402
from scripts.lib.rules import _merged_rule_vars  # noqa: E402
from scripts.lib.topology import VALID_TOPOLOGIES  # noqa: E402
from scripts.lib.variables import (  # noqa: E402
    _provider_topology_flags,
    _resolve_orch_mode,
)


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


# ---------------------------------------------------------------------------
# Task 5 — Stage-4 context seam + one deterministic block per physical file
# ---------------------------------------------------------------------------


def _stage_context_variables(monkeypatch, tmp_path, config, providers, active_set,
                             variables=None):
    """Run Stage 4 with a spy on ``sync_context_for_provider``.

    Returns ``(captured_provider_variables, shared_variables)``: the dict each
    provider's context render actually received, plus the caller-owned shared
    ``variables`` dict (to prove no provider-scoped key leaks into it).
    ``captured["__active_set__"]`` holds the set object the renderer received.
    """
    captured: dict = {}
    variables = {} if variables is None else variables

    def _context_spy(agent_meta_root, project_root, config, variables, log, dry_run,
                     provider, provider_config, **kwargs):
        captured[provider] = dict(variables)
        captured["__active_set__"] = kwargs.get("active_set")

    monkeypatch.setattr(sync_pipeline, "sync_context_for_provider", _context_spy)

    provider_config = {
        provider: {"context_file": f"{provider}.md", "has_rules": True}
        for provider in providers
    }
    sync_pipeline._sync_stage_contexts(
        _REPO_ROOT, tmp_path, config, provider_config, list(providers), variables,
        argparse.Namespace(dry_run=False), SyncLog(),
        active_set=active_set,
    )
    return captured, variables


def test_context_render_effective_flags_per_provider(tmp_path, monkeypatch):
    """Stage 4 hands each provider ITS effective position (G3, AC-18/AC-20)."""
    config = {
        "orchestrator": {
            "topology": "primary",
            "provider-overrides": {"Opencode": {"topology": "subagent"}},
        },
    }
    shared = {"PROBE": "unchanged"}

    captured, shared_after = _stage_context_variables(
        monkeypatch, tmp_path, config, ["Opencode", "Claude"], frozenset(), shared,
    )

    opencode = captured["Opencode"]
    assert opencode["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "true"
    assert opencode["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "false"

    claude = captured["Claude"]
    assert claude["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "true"
    assert claude["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "false"

    # The provider-scoped re-resolution happens on a copy; the shared dict the
    # other stages receive must not carry one provider's position (AC-30).
    assert shared_after == {"PROBE": "unchanged"}


def test_shared_context_renders_one_deterministic_block():
    """One physical AGENTS.md => ONE position-neutral block (G5/AC-20).

    Two sharers with a *different* effective position still render the same
    text: the shared file must never state a per-provider position (that is the
    oscillation/false ``--check`` failure mode of #638/#794). This is the
    ratchet the G5/T10 wording has to keep intact.
    """
    config = load_config(_REPO_ROOT / ".meta-config" / "project.yaml")
    provider_config = load_providers_config(_REPO_ROOT)
    shared = dict(config.get("variables") or {})

    override_config = {
        "orchestrator": {
            "topology": "primary",
            "provider-overrides": {"Gemini": {"topology": "subagent"}},
        },
    }
    mode = _resolve_orch_mode(override_config["orchestrator"], None)
    active_set = frozenset({"orchestrator"})

    def _flags(provider: str) -> dict:
        return _provider_topology_flags(
            override_config, provider,
            agent_meta_root=_REPO_ROOT, mode=mode, active_set=active_set,
        )

    opencode_flags = _flags("Opencode")
    gemini_flags = _flags("Gemini")
    assert opencode_flags["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "true"
    assert gemini_flags["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "true"

    def _render(provider: str, variables: dict) -> str:
        return _build_managed_block(
            _REPO_ROOT, config, dict(variables), SyncLog(),
            provider=provider, provider_config=provider_config,
            project_root=_REPO_ROOT, target_name="AGENTS.md",
            active_set=active_set,
        )

    shared_vars = dict(shared)
    shared_vars.update(opencode_flags)
    primary_a = _render("Opencode", shared_vars)
    primary_b = _render("Gemini", shared_vars)

    # Byte-identical regardless of which sharer renders the SAME input dict ...
    assert primary_a == primary_b, (
        "the two AGENTS.md sharers render different blocks from the same "
        "variables => each sync overwrites the other forever (#638)"
    )
    # ... and regardless of provider order.
    forward = [_render(p, shared_vars) for p in ("Opencode", "Gemini")]
    backward = [_render(p, shared_vars) for p in ("Gemini", "Opencode")]
    assert len(set(forward + backward)) == 1

    # ... and independently of the injected position (no position-specific
    # statement in the shared file, G5/T10 wording not present yet).
    subagent_vars = dict(shared)
    subagent_vars.update(gemini_flags)
    assert _render("Opencode", subagent_vars) == primary_a
    assert _render("Gemini", subagent_vars) == primary_a

    assert primary_a.strip()
    assert "Diese Session startet im" not in primary_a
    assert "er **ist** der Session-Einstieg" not in primary_a


def test_context_uses_the_shared_active_set(tmp_path, monkeypatch):
    """The per-sync ActiveSet decides the effective position (AC-30)."""
    empty = frozenset()
    captured, _ = _stage_context_variables(
        monkeypatch, tmp_path, {}, ["Opencode"], empty,
    )
    assert captured["Opencode"]["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert captured["Opencode"]["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "true"
    # Same seam, same set: the object reaches the renderer unchanged.
    assert captured["__active_set__"] is empty

    with_role = frozenset({"orchestrator"})
    captured, _ = _stage_context_variables(
        monkeypatch, tmp_path, {}, ["Opencode"], with_role,
    )
    assert captured["Opencode"]["ORCH_TOPOLOGY_EFFECTIVE"] == "primary"
    assert captured["Opencode"]["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "true"
    assert captured["__active_set__"] is with_role


def test_stage4_requires_active_set(tmp_path):
    """``active_set`` is a required keyword — no default that would neuter AC-30."""
    provider_config = {"Opencode": {"context_file": "AGENTS.md"}}
    with pytest.raises(TypeError):
        sync_pipeline._sync_stage_contexts(
            _REPO_ROOT, tmp_path, {}, provider_config, ["Opencode"], {},
            argparse.Namespace(dry_run=False), SyncLog(),
        )


# ---------------------------------------------------------------------------
# Task 6 — agent-template seam + pipeline override branch (G3, AC-18/AC-30)
# ---------------------------------------------------------------------------


_TOPOLOGY_OVERRIDE_CONFIG = {
    "orchestrator": {
        "topology": "primary",
        "provider-overrides": {"Opencode": {"topology": "subagent"}},
    },
}


def test_agent_templates_carry_provider_scoped_effective_flags():
    """``_build_provider_vars`` hands each provider ITS effective position (AC-18).

    The agent-template seam used the provider-less global basis before T6; a
    provider override must flip ``EFFECTIVE`` for that provider only, exactly as
    the rules (T4) and context (T5) seams already do.
    """
    providers = load_providers_config(_REPO_ROOT)
    active_set = frozenset({"orchestrator"})

    opencode = _build_provider_vars(
        providers["Opencode"], "Opencode", {}, _REPO_ROOT,
        config=_TOPOLOGY_OVERRIDE_CONFIG, active_set=active_set,
    )
    assert opencode["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "true"
    assert opencode["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "false"

    claude = _build_provider_vars(
        providers["Claude"], "Claude", {}, _REPO_ROOT,
        config=_TOPOLOGY_OVERRIDE_CONFIG, active_set=active_set,
    )
    assert claude["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "true"
    assert claude["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "false"


def test_sync_pipeline_override_branch_carries_topology_flags():
    """The override branch sets all seven effective flags, not only ``ORCH_MODE_*``.

    Behavioural check through the extracted helper the branch calls: the
    provider-resolved mode decides ``ORCH_TOPOLOGY_INERT`` and the position
    flags stay mutually exclusive / in ``VALID_TOPOLOGIES``.
    """
    providers = load_providers_config(_REPO_ROOT)
    for mode, expected_inert in (("strict", "false"), ("main-chat", "true")):
        config = {
            "orchestrator": {
                "provider-overrides": {"Opencode": {"mode": mode}},
            },
        }
        flags = sync_pipeline._provider_override_vars(
            config, "Opencode", _REPO_ROOT,
            active_set=frozenset({"orchestrator"}),
        )

        for key in (
            "ORCH_TOPOLOGY_EFFECTIVE",
            "ORCH_TOPOLOGY_EFFECTIVE_SOURCE",
            "ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT",
            "ORCH_TOPOLOGY_EFFECTIVE_PRIMARY",
            "ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT",
            "ORCH_TOPOLOGY_EFFECTIVE_HYBRID",
            "ORCH_TOPOLOGY_INERT",
        ):
            assert key in flags, f"{key} missing from the override branch for {mode}"

        assert flags["ORCH_MODE_%s" % mode.replace("-", "_").upper()] == "true"
        assert flags["ORCH_TOPOLOGY_EFFECTIVE"] in VALID_TOPOLOGIES
        positions = [
            flags["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"],
            flags["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"],
            flags["ORCH_TOPOLOGY_EFFECTIVE_HYBRID"],
        ]
        assert positions.count("true") == 1, positions
        assert flags["ORCH_TOPOLOGY_INERT"] == expected_inert


def test_agents_use_the_shared_active_set():
    """Derived position needs the per-sync ActiveSet in the agent templates (AC-30)."""
    providers = load_providers_config(_REPO_ROOT)
    pc = providers["Opencode"]  # registry: primary-role: orchestrator

    empty = frozenset()
    derived_subagent = _build_provider_vars(
        pc, "Opencode", {}, _REPO_ROOT, active_set=empty,
    )
    assert derived_subagent["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"

    with_role = frozenset({"orchestrator"})
    derived_primary = _build_provider_vars(
        pc, "Opencode", {}, _REPO_ROOT, active_set=with_role,
    )
    assert derived_primary["ORCH_TOPOLOGY_EFFECTIVE"] == "primary"
