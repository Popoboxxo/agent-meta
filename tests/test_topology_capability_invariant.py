"""AC-13 / AC-15 / AC-16 — orchestrator topology capability structures.

SPEC-orchestrator-topology-2026-11-03, P0 (issue #1077), Task 1.

Every provider registered in ``config/ai-providers.yaml`` MUST carry four
topology structures in ``config/provider-capabilities.yaml``:

    topology_support        {primary, subagent, hybrid} -> bool
    topology_degrade        {primary, subagent, hybrid} -> mechanism word|null
    orchestrator_instances  {multiple: bool, reason: str|null}
    topology_verified_state {primary, subagent, hybrid, multiple} -> state

Rules pinned here:
* AC-13 — all four structures exist for every registered provider.
* AC-15 — ``topology_support.* == true`` implies
  ``topology_verified_state.* != UNVERIFIED``; equivalently ``UNVERIFIED``
  cells are always ``no`` (0 speculative ``yes``).
* AC-16 — the normative pre-P0 matrix (spec §"Provider-Matrix (Stand vor P0)")
  has 40 cells: 25 data-derived / 15 ``UNVERIFIED => no``. Task 3 upgrades
  cells by measured evidence, so the numbers below are the N=0 snapshot; the
  moving ``25 + N`` rule is asserted by ``test_topology_probe_evidence.py``
  (Task 4). A cell upgrade must consciously update this snapshot.

Values are conservative by construction: ``topology_support`` mirrors the
existing data keys (``main_agent_selectable`` / ``subagent_dispatch``),
``orchestrator_instances.multiple`` mirrors ``parallel_execution``, and
``hybrid`` is ``false`` for every provider in v1 (no data basis anywhere).
"""

from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_AI_PROVIDERS = _ROOT / "config" / "ai-providers.yaml"
_CAPABILITIES = _ROOT / "config" / "provider-capabilities.yaml"

_AXES = ("primary", "subagent", "hybrid")
_REQUIRED_KEYS = (
    "topology_support",
    "topology_degrade",
    "orchestrator_instances",
    "topology_verified_state",
)
_MECHANISMS = {"primary", "subagent", "sequential-text"}
_STATES = {"VERIFIED-RUNTIME", "DOCUMENTED", "UNVERIFIED"}

# Spec "Provider-Matrix (Stand vor P0)": the custom/unregistered row carries no
# capability data and contributes four UNVERIFIED => no cells.
_CUSTOM_PROVIDER_CELLS = 4

# Normative pre-P0 snapshot (N = 0). AC-16 asserts the moving rule 25 + N /
# 15 - N; Task 3 must bump these two numbers when a probe earns an upgrade.
_PRE_P0_DATA_DERIVED = 25
_PRE_P0_UNVERIFIED = 15


def _load(rel_path):
    with rel_path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


_CAPS = _load(_CAPABILITIES).get("capabilities") or {}


def _registered_providers():
    """Provider keys from the live registry, sorted for stable test ids."""
    data = _load(_AI_PROVIDERS)
    return sorted((data.get("providers") or {}).keys())


_REGISTERED = _registered_providers()


def test_registry_and_capability_registry_are_not_vacuous():
    """Guard against a vacuous pass: both registries must be populated and
    cover the same providers, otherwise the per-provider sweep collects zero
    cases and AC-13/AC-15 would hold trivially."""
    assert _REGISTERED, "config/ai-providers.yaml has no providers"
    assert _CAPS, "provider-capabilities.yaml has no capabilities section"
    assert set(_REGISTERED) == set(_CAPS), (
        "provider registry and capability registry diverge: "
        f"only in registry={sorted(set(_REGISTERED) - set(_CAPS))}, "
        f"only in capabilities={sorted(set(_CAPS) - set(_REGISTERED))}"
    )


@pytest.mark.parametrize("provider", _REGISTERED)
def test_provider_topology_capability_contract(provider):
    """AC-13 + AC-15 + conservative derivation for one registered provider."""
    caps = _CAPS.get(provider)
    assert isinstance(caps, dict), f"{provider}: no capability entry"

    missing = [key for key in _REQUIRED_KEYS if key not in caps]
    assert not missing, (
        f"{provider}: missing topology structures {missing} — every registered "
        "provider must carry topology_support, topology_degrade, "
        "orchestrator_instances and topology_verified_state (AC-13)"
    )

    support = caps["topology_support"]
    degrade = caps["topology_degrade"]
    instances = caps["orchestrator_instances"]
    states = caps["topology_verified_state"]

    # --- shape and enum checks -------------------------------------------------
    assert isinstance(support, dict) and set(support) == set(_AXES), (
        f"{provider}: topology_support must have exactly {list(_AXES)}"
    )
    for axis in _AXES:
        assert isinstance(support[axis], bool), (
            f"{provider}: topology_support.{axis} must be a bool"
        )

    assert isinstance(degrade, dict) and set(degrade) == set(_AXES), (
        f"{provider}: topology_degrade must have exactly {list(_AXES)}"
    )
    for axis in _AXES:
        mechanism = degrade[axis]
        assert mechanism is None or (
            isinstance(mechanism, str) and mechanism in _MECHANISMS
        ), (
            f"{provider}: topology_degrade.{axis} must be null or one of "
            f"{sorted(_MECHANISMS)}, got {mechanism!r}"
        )

    assert isinstance(instances, dict), (
        f"{provider}: orchestrator_instances must be a mapping "
        "{multiple: bool, reason: str|null}"
    )
    assert isinstance(instances.get("multiple"), bool), (
        f"{provider}: orchestrator_instances.multiple must be a bool"
    )
    reason = instances.get("reason")
    assert reason is None or (isinstance(reason, str) and reason), (
        f"{provider}: orchestrator_instances.reason must be null or a "
        "non-empty string"
    )

    assert isinstance(states, dict) and set(states) == set(_AXES) | {"multiple"}, (
        f"{provider}: topology_verified_state must have exactly "
        f"{sorted(set(_AXES) | {'multiple'})}"
    )
    for axis, state in states.items():
        assert state in _STATES, (
            f"{provider}: topology_verified_state.{axis} must be one of "
            f"{sorted(_STATES)}, got {state!r}"
        )

    # --- AC-15: no `yes` without a non-UNVERIFIED state ----------------------
    for axis in _AXES:
        if support[axis]:
            assert states[axis] != "UNVERIFIED", (
                f"{provider}: topology_support.{axis} is true but "
                f"topology_verified_state.{axis} is UNVERIFIED (AC-15)"
            )
        else:
            # UNVERIFIED => no: an unverified cell may never claim support.
            assert degrade[axis] is not None, (
                f"{provider}: topology_support.{axis} is false "
                f"(state={states[axis]}) but topology_degrade.{axis} is null — "
                "a degraded axis needs its mechanism word"
            )

    if instances["multiple"]:
        assert states["multiple"] != "UNVERIFIED", (
            f"{provider}: orchestrator_instances.multiple is true but "
            "topology_verified_state.multiple is UNVERIFIED (AC-15)"
        )

    # --- conservative derivation from existing capability keys ---------------
    assert support["primary"] == caps["main_agent_selectable"], (
        f"{provider}: topology_support.primary must mirror "
        f"main_agent_selectable ({caps['main_agent_selectable']})"
    )
    assert support["subagent"] == caps["subagent_dispatch"], (
        f"{provider}: topology_support.subagent must mirror "
        f"subagent_dispatch ({caps['subagent_dispatch']})"
    )
    assert support["hybrid"] is False, (
        f"{provider}: hybrid has no data basis anywhere in v1 — support must "
        "stay false until probe evidence earns the upgrade"
    )
    assert states["hybrid"] == "UNVERIFIED", (
        f"{provider}: topology_verified_state.hybrid must stay UNVERIFIED "
        "until probe evidence earns the upgrade"
    )
    assert instances["multiple"] == caps["parallel_execution"], (
        f"{provider}: orchestrator_instances.multiple must mirror "
        f"parallel_execution ({caps['parallel_execution']})"
    )

    # A supported axis needs no degradation mechanism.
    for axis in _AXES:
        if support[axis]:
            assert degrade[axis] is None, (
                f"{provider}: topology_support.{axis} is true, so "
                f"topology_degrade.{axis} must be null, got {degrade[axis]!r}"
            )


def _assert_structures_present():
    """Turn a missing structure into one readable failure (not a KeyError)."""
    incomplete = []
    for provider in _REGISTERED:
        caps = _CAPS.get(provider) or {}
        missing = [key for key in _REQUIRED_KEYS if key not in caps]
        if missing:
            incomplete.append(f"{provider}: {missing}")
    assert not incomplete, (
        "cannot evaluate the topology matrix — missing capability structures: "
        + "; ".join(incomplete)
    )


def _matrix_counts():
    """Recompute the AC-16 cell balance from the capability data.

    Cells: three topology axes per registered provider, one multiple cell per
    registered provider, plus the four custom/unregistered cells of the
    normative matrix.
    """
    per_axis_derived = {axis: 0 for axis in _AXES}
    per_axis_unverified = {axis: 0 for axis in _AXES}
    multiple_derived = 0
    multiple_unverified = 0

    for provider in _REGISTERED:
        caps = _CAPS[provider]
        states = caps["topology_verified_state"]
        for axis in _AXES:
            if states[axis] == "UNVERIFIED":
                per_axis_unverified[axis] += 1
            else:
                per_axis_derived[axis] += 1
        if states["multiple"] == "UNVERIFIED":
            multiple_unverified += 1
        else:
            multiple_derived += 1

    derived = sum(per_axis_derived.values()) + multiple_derived
    unverified = (
        sum(per_axis_unverified.values())
        + multiple_unverified
        + _CUSTOM_PROVIDER_CELLS
    )
    return derived, unverified, per_axis_derived, per_axis_unverified


def test_ac16_matrix_count_is_measured_not_asserted():
    """AC-16: 40 cells = 25 + N data-derived / 15 - N UNVERIFIED => no, with
    N = 0 before the P0 probes. The balance is recomputed from the data, never
    guessed."""
    _assert_structures_present()
    derived, unverified, per_axis_derived, per_axis_unverified = _matrix_counts()

    assert derived + unverified == 40, (
        f"matrix must have 40 cells, got {derived + unverified} "
        f"({derived} derived + {unverified} unverified)"
    )
    assert derived == _PRE_P0_DATA_DERIVED, (
        f"pre-P0 data-derived cells: expected {_PRE_P0_DATA_DERIVED}, got "
        f"{derived} (per axis: {per_axis_derived}). An upgrade needs documented "
        "probe evidence (Task 3) — update this snapshot deliberately."
    )
    assert unverified == _PRE_P0_UNVERIFIED, (
        f"pre-P0 UNVERIFIED => no cells: expected {_PRE_P0_UNVERIFIED}, got "
        f"{unverified} (per axis: {per_axis_unverified} + "
        f"{_CUSTOM_PROVIDER_CELLS} custom cells)"
    )

    # Exact per-axis split of the normative pre-P0 matrix.
    assert per_axis_derived == {
        "primary": 7,
        "subagent": 9,
        "hybrid": 0,
    }, f"unexpected per-axis derived split: {per_axis_derived}"
    assert per_axis_unverified == {
        "primary": 2,
        "subagent": 0,
        "hybrid": 9,
    }, f"unexpected per-axis UNVERIFIED split: {per_axis_unverified}"


def test_no_speculative_yes_cell():
    """AC-16 invariant: 0 speculative `yes` — a support cell may only be true
    when its verified state is documented or runtime-verified."""
    _assert_structures_present()
    speculative = [
        f"{provider}.{axis}"
        for provider in _REGISTERED
        for axis in _AXES
        if _CAPS[provider]["topology_support"][axis]
        and _CAPS[provider]["topology_verified_state"][axis] == "UNVERIFIED"
    ]
    assert speculative == [], (
        f"speculative yes cells without evidence: {speculative} (AC-15/AC-16)"
    )
