"""Emission follows the RESOLVED orchestrator topology (IC-6).

SPEC-orchestrator-topology-2026-11-03, P2 (issue #1077), Task 11.

The transform's ``mode`` is the resolved position, never the declared word:

* ``effective == "primary"`` and the role is the provider's explicit
  ``primary-role`` -> ``mode: primary`` (v1 and v2, the historic path).
* ``effective == "subagent"`` -> no ``mode: primary``; the frozen v1 shape
  still carries its default ``mode: subagent`` and v2 pins it to
  ``mode: subagent``. ``hybrid`` follows its effective value; on the v1
  capability data that is ``subagent`` (evidence gate).
* unset key on a provider whose primary role is in the active set -> derived
  ``primary`` -> byte-identical to the explicit ``primary`` output.

Run: python3 -m pytest tests/test_provider_transform_topology.py -q
"""
from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace

import yaml

from scripts.lib.log import SyncLog
from scripts.lib.provider_transform import transform_agent_content_for_provider
from scripts.lib.providers import (
    load_provider_capabilities,
    load_providers_config,
)

REPO_ROOT = Path(__file__).resolve().parents[1]
_AGENT_CONTENT = (
    "---\n"
    "name: template-orchestrator\n"
    'version: "0.101.0"\n'
    "description: old description\n"
    "tools:\n"
    "  - Read\n"
    "  - Bash\n"
    "  - Grep\n"
    "---\n"
    "\n"
    "Koordiniert alle Entwicklungsaufgaben.\n"
    "Body-Ende.\n"
)

_ACTIVE_SET = SimpleNamespace(
    roles=frozenset({"orchestrator", "developer"}),
    known_roles=frozenset({"orchestrator", "developer"}),
)
_CAPABILITIES = load_provider_capabilities(REPO_ROOT)


def _provider_config(*, v2: bool) -> dict:
    config = copy.deepcopy(load_providers_config(REPO_ROOT))
    if v2:
        config["Opencode"]["surface-version"] = "v2"
        config["Opencode"]["agent-transform"]["frontmatter-mechanism"] = (
            "opencode-native-v2"
        )
    return config


def _project_config(topology: str | None) -> dict:
    if topology is None:
        return {}
    return {"orchestrator": {"topology": topology}}


def _transform(
    *,
    v2: bool,
    topology: str | None,
    role: str = "orchestrator",
    active_set=_ACTIVE_SET,
) -> str:
    provider_config = _provider_config(v2=v2)
    target_path = (
        REPO_ROOT
        / provider_config["Opencode"]["agents_dir"]
        / f"{role}{provider_config['Opencode']['agent_ext']}"
    )
    return transform_agent_content_for_provider(
        _AGENT_CONTENT,
        "Opencode",
        role,
        role,
        "desc",
        "1-generic/orchestrator.md@0.101.0",
        _project_config(topology),
        REPO_ROOT,
        REPO_ROOT,
        target_path,
        provider_config,
        SyncLog(),
        active_set=active_set,
        provider_capabilities=_CAPABILITIES,
    )


def _frontmatter(text: str) -> dict:
    parsed = yaml.safe_load(text.split("---", 2)[1])
    assert isinstance(parsed, dict)
    return parsed


# --- subagent ---------------------------------------------------------------


def test_subagent_topology_omits_primary_mode_on_v1() -> None:
    # v1's frozen shape always writes `mode`; the point is that it is no longer
    # `primary` for the declared entry-point role.
    fm = _frontmatter(_transform(v2=False, topology="subagent"))
    assert fm["mode"] == "subagent"


def test_subagent_topology_emits_subagent_mode_on_v2() -> None:
    fm = _frontmatter(_transform(v2=True, topology="subagent"))
    assert fm["mode"] == "subagent"


# --- primary ----------------------------------------------------------------


def test_primary_topology_keeps_primary_mode_on_v1() -> None:
    fm = _frontmatter(_transform(v2=False, topology="primary"))
    assert fm["mode"] == "primary"


def test_primary_topology_keeps_primary_mode_on_v2() -> None:
    fm = _frontmatter(_transform(v2=True, topology="primary"))
    assert fm["mode"] == "primary"


def test_primary_topology_does_not_promote_other_roles() -> None:
    # v1: non-primary roles keep the frozen `subagent`; v2: same.
    assert (
        _frontmatter(_transform(v2=False, topology="primary", role="developer"))[
            "mode"
        ]
        == "subagent"
    )
    assert (
        _frontmatter(_transform(v2=True, topology="primary", role="developer"))[
            "mode"
        ]
        == "subagent"
    )


# --- hybrid follows the effective value -------------------------------------


def test_hybrid_topology_follows_effective_subagent() -> None:
    # Opencode declares topology_support.hybrid=false and degrades it to
    # subagent; the emission follows the EFFECTIVE value, not the word.
    capability = _CAPABILITIES["Opencode"]
    assert capability["topology_support"]["hybrid"] is False
    assert capability["topology_degrade"]["hybrid"] == "subagent"

    assert _frontmatter(_transform(v2=False, topology="hybrid"))["mode"] == "subagent"
    assert (
        _frontmatter(_transform(v2=True, topology="hybrid"))["mode"] == "subagent"
    )


# --- unset key: byte identity ----------------------------------------------


def test_unset_key_is_byte_identical_to_explicit_primary_on_v1() -> None:
    assert _transform(v2=False, topology=None) == _transform(
        v2=False, topology="primary"
    )


def test_unset_key_is_byte_identical_to_explicit_primary_on_v2() -> None:
    assert _transform(v2=True, topology=None) == _transform(
        v2=True, topology="primary"
    )


def test_unset_key_without_active_set_keeps_historic_primary() -> None:
    # No active-set information: the derived topology must not silently demote
    # the explicit primary role (historic emission stays byte-identical).
    fm = _frontmatter(
        _transform(v2=False, topology=None, active_set=None)
    )
    assert fm["mode"] == "primary"
