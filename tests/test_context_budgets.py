"""Per-provider context budgets as ceilings (QG-4, AC-07 of SPEC-CONTEXT-PROFILES-2026-10-11).

``FULL_BUDGET_CEILINGS`` pins the measured Ist-values of the ``full`` profile
(Spec section 2, re-measured with ``measure_artifacts`` on the provider-matrix
projects of tests/test_ac01_render_identity.py) as upper bounds. Any change
that grows an artifact beyond its ceiling turns this test red.

Tolerance rationale: the measured projects contain the scratch root path and a
date stamp, so sizes vary by a few bytes between runs. The ceiling is
Ist + max(``TOLERANCE_MIN_BYTES``, ``TOLERANCE_RATIO`` * Ist), i.e. small
enough to catch real growth, large enough to be path-length independent.

Run: python3 -m pytest tests/test_context_budgets.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Mapping

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import context_report as cr  # noqa: E402
from lib.providers import load_provider_capabilities, load_providers_config  # noqa: E402
from tests.test_ac01_render_identity import _make_project  # noqa: E402

TOLERANCE_MIN_BYTES = 256
TOLERANCE_RATIO = 0.02

# Ist-values in bytes (data table). Matches Spec section 2 (Claude orchestrator
# 90,691 B, CLAUDE.md ~2.5 KB, rules 17.9-18.3 KB, AGENTS.md 25.6 KB / Gemini 33 KB).
_IST_FULL: Dict[str, Dict[str, int]] = {
    "Claude": {"entry-file": 2511, "rules": 18297, "orchestrator": 90691,
               "harness-roster": 577570, "always-loaded": 598378},
    "Codex": {"entry-file": 25562, "rules": 18380, "orchestrator": 90111,
              "harness-roster": 571549, "always-loaded": 615491},
    "Continue": {"entry-file": 617, "rules": 19004, "orchestrator": 74620,
                 "always-loaded": 19621},
    "Copilot": {"entry-file": 9245, "rules": 18405, "orchestrator": 74500,
                "always-loaded": 27650},
    "Gemini": {"entry-file": 33031, "rules": 18297, "orchestrator": 90553,
               "always-loaded": 51328},
    "KimiCode": {"entry-file": 25562, "orchestrator": 75743,
                 "harness-roster": 562388, "always-loaded": 587950},
    "Mammouth": {"entry-file": 25562, "rules": 18387, "orchestrator": 75457,
                 "harness-roster": 564604, "always-loaded": 608553},
    "Opencode": {"entry-file": 25626, "orchestrator": 90419,
                 "harness-roster": 574085, "always-loaded": 599711},
    "ZCode": {"entry-file": 26476, "orchestrator": 75778,
              "harness-roster": 561254, "always-loaded": 587730},
}


def _ceiling(ist: int) -> int:
    return ist + max(TOLERANCE_MIN_BYTES, int(ist * TOLERANCE_RATIO))


FULL_BUDGET_CEILINGS: Dict[str, Dict[str, int]] = {
    provider: {artifact: _ceiling(size) for artifact, size in artifacts.items()}
    for provider, artifacts in _IST_FULL.items()
}


def check_ceilings(report: Mapping[str, Mapping], ceilings: Mapping[str, Mapping[str, int]]) -> List[str]:
    """Return violation messages for artifacts above their ceiling or without one."""
    violations = []
    for provider, artifacts in report.items():
        for artifact, stat in artifacts.items():
            limit = (ceilings.get(provider) or {}).get(artifact)
            if limit is None:
                violations.append(f"{provider}/{artifact}: no ceiling pinned")
            elif stat["bytes"] > limit:
                violations.append(f"{provider}/{artifact}: {stat['bytes']} > {limit} bytes")
    return violations


_PROVIDERS = sorted(
    yaml.safe_load((REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
)


@pytest.fixture(scope="module")
def measured(tmp_path_factory):
    root = tmp_path_factory.mktemp("budgets")
    mappings = cr.merge_provider_mappings(
        load_providers_config(REPO_ROOT, {}), load_provider_capabilities(REPO_ROOT))
    projects = {p: _make_project(root, p) for p in _PROVIDERS}
    return projects, mappings


def _measure(projects, mappings) -> dict:
    report: dict = {}
    for provider, project in projects.items():
        report.update(cr.measure_artifacts(project, [provider], mappings))
    return report


def test_ac07_every_registered_provider_has_ceilings():
    assert sorted(FULL_BUDGET_CEILINGS) == _PROVIDERS


def test_ac07_full_profile_within_ceilings(measured):
    projects, mappings = measured
    assert check_ceilings(_measure(projects, mappings), FULL_BUDGET_CEILINGS) == []


def test_ac07_inflated_artifact_exceeds_ceiling(measured):
    """Meta-test: really growing a rendered artifact makes the check fail."""
    projects, mappings = measured
    provider = _PROVIDERS[0]
    caps = mappings[provider]
    target = projects[provider] / caps["agents_dir"] / ("orchestrator" + (caps.get("agent_ext") or ".md"))
    original = target.read_bytes()
    try:
        target.write_bytes(original + b"x" * (_ceiling(len(original)) - len(original) + 1))
        violations = check_ceilings(_measure(projects, mappings), FULL_BUDGET_CEILINGS)
    finally:
        target.write_bytes(original)
    assert any(v.startswith(f"{provider}/orchestrator:") for v in violations), violations
    assert check_ceilings(_measure(projects, mappings), FULL_BUDGET_CEILINGS) == []


def test_ac07_missing_ceiling_is_a_violation():
    report = {"Alpha": {"entry-file": {"bytes": 1}}}
    assert check_ceilings(report, {}) == ["Alpha/entry-file: no ceiling pinned"]
