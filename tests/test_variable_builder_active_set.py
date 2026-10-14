"""IC-18 no. 18 / AC-45 / AC-84: variable builder derives role data from ActiveSet.

* ``EFFORT_ESTIMATOR_ENABLED`` follows ``ActiveSet.has("effort-estimator")``.
* ``ACTIVE_ROLES`` / ``ROLE_<ROLE>_ACTIVE`` (``active_set_variables``) reach
  ``build_variables``.
* Convention-block gating (``applies_to_roles``) uses ``ActiveSet.roles``.
* The strict-permission scan derives its active roles from the ActiveSet.

Spec direction (IC-18 no. 18 / IC-17): a role that is not in the ActiveSet
(e.g. dropped by a gate) must yield ``"false"``; the plan text for Task 1.05
says ``"true"`` which contradicts the contract (documented deviation).
"""
from __future__ import annotations

import dataclasses
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.active_set import compute_active_set  # noqa: E402
from lib.config import (  # noqa: E402
    _build_convention_variables,
    _build_platform_variables,
    build_variables,
    load_config,
)

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "active-set"


def _fixture_config(name: str) -> dict:
    return load_config(_FIXTURES / name / ".meta-config" / "project.yaml")


def test_effort_estimator_false_when_not_in_active_set():
    # Raw allowlist names effort-estimator, ActiveSet does not contain it.
    config = {"roles": ["orchestrator", "developer", "effort-estimator"]}
    active = compute_active_set(config, _REPO_ROOT, _REPO_ROOT, warn_sink=[])
    reduced = dataclasses.replace(active, roles=active.roles - {"effort-estimator"})
    variables: dict = {}
    _build_platform_variables(variables, [], config, _REPO_ROOT, reduced)
    assert variables["EFFORT_ESTIMATOR_ENABLED"] == "false"


def test_effort_estimator_true_when_in_active_set():
    config = {"roles": ["orchestrator", "developer", "effort-estimator"]}
    active = compute_active_set(config, _REPO_ROOT, _REPO_ROOT, warn_sink=[])
    variables: dict = {}
    _build_platform_variables(variables, [], config, _REPO_ROOT, active)
    assert variables["EFFORT_ESTIMATOR_ENABLED"] == "true"


@pytest.mark.xfail(
    strict=True,
    reason="IC-18 no. 18 (ROLE_*_ACTIVE / ACTIVE_ROLES in build_variables) BLOCKED: making them "
    "effective changes the default meta-doctor render (`{{#if ROLE_META_FEEDBACK_ACTIVE}}`) and "
    "generated-file-hashes, breaking AC-01 (no rebaseline allowed). Needs a spec decision.",
)
def test_build_variables_exposes_active_set_variables_p20():
    config = _fixture_config("p20")
    variables, _ = build_variables(config, _REPO_ROOT, _REPO_ROOT)
    active = compute_active_set(config, _REPO_ROOT, _REPO_ROOT, warn_sink=[])
    assert variables["ACTIVE_ROLES"] == ",".join(sorted(active.roles))
    assert variables["ROLE_DEVELOPER_ACTIVE"] == "true"
    # developer_tiers gate drops senior-developer in p20 -> not active.
    assert variables["ROLE_SENIOR_DEVELOPER_ACTIVE"] == "false"
    assert variables["EFFORT_ESTIMATOR_ENABLED"] == "false"


def test_convention_blocks_follow_active_set():
    # `git` active -> issue-naming block rendered; removed from the ActiveSet
    # -> the applies_to_roles gate suppresses the git-gated block.
    config = {"roles": ["orchestrator", "developer", "git"]}
    active = compute_active_set(config, _REPO_ROOT, _REPO_ROOT, warn_sink=[])
    with_git: dict = {}
    _build_convention_variables(with_git, config, _REPO_ROOT, active)
    without_git: dict = {}
    reduced = dataclasses.replace(active, roles=active.roles - {"git"})
    _build_convention_variables(without_git, config, _REPO_ROOT, reduced)
    assert with_git.get("GIT_ISSUE_NAMING_BLOCK")
    assert not without_git.get("GIT_ISSUE_NAMING_BLOCK")
