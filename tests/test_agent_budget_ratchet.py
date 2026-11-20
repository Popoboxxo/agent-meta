"""Batch-0 budget ratchet tests (SPEC-AGENT-LOOP-BATCH0-2026-11-20, IC-5, #1244 Pkt 1).

Two independent layers:

1. Pure helpers (:func:`load_baseline`, :func:`check_no_growth`,
   :func:`check_session_ceiling`) are exercised with synthetic data and always run.
2. Integration tests read ``.tmp/plans/scratch/baseline-batch-0.json`` (produced by
   Task 1.1) and skip with an explicit reason when it is missing (spec AC-10).

§5 target values are held as ``xfail(strict=True)`` until Batch 11 hardens them
(detail plan :228-229, ADR-2). XPASS therefore fails the build and forces the
marker to be removed.

Constants are source-cited (detail plan §5 :108-120, §1.3 :67) and NOT invented.
OQ-1: only the §5 Gesamtziele are parametrized; H1-H7 levers are not separate
targets and AGENTS.md <= 12 KB is out of scope (H6/P30, spec :41).
OQ-3: the single always-on ceiling is 19,500 B DECIMAL (review major-1:
19.5 KB = 19500 B, NOT 19500*1024), aggregated as entry + rules + descriptions.

Deliberately disjoint from tests/test_context_budgets.py: the 2 % tolerance,
_IST_FULL and FULL_BUDGET_CEILINGS there are untouched (this module uses 1 %).

Run: python3 -m pytest tests/test_agent_budget_ratchet.py -q
"""

from __future__ import annotations

import json
from collections.abc import Mapping
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
BASELINE_DIR = REPO_ROOT / ".tmp" / "plans" / "scratch"
DEFAULT_BASELINE = BASELINE_DIR / "baseline-batch-0.json"

# Detailplan E7 :238 — 1 % growth tolerance. NOT the 2 % of test_context_budgets.py.
NO_GROWTH_TOLERANCE = 0.01

# --- §5 Gesamtziele, source-cited constants (detailplan :108-120). Decimal KB. ---
SESSION_CEILING_BYTES = 19_500  # §5 :120 / §1.3 :67 "24,3 KB -> <= 19,5 KB" (OQ-3).
ORCHESTRATOR_RENDER_TARGET_BYTES = 28_000  # §5 :120 "Orchestrator-Render -60 % (73 KB -> <= 28 KB)".
ROSTER_TARGET_BYTES = 300_000  # §5 :120 "Roster -45 % (553 KB -> <= 300 KB)".
WORKER_AVG_REDUCTION_TARGET = 0.35  # §5 :120 "O Worker-Render -35 %" (relative reduction).
AGENTS_MD_TARGET_BYTES = 12_000  # §5 :120 / H6 — documented, NOT parametrized (out of scope).

# Documented Ist-values used as the "not yet reached" candidate for the xfail checks.
_ORCHESTRATOR_IST_BYTES = 73_000  # §5 :120 "73 KB".
_ROSTER_IST_BYTES = 553_000  # §5 :120 "553 KB".
_WORKER_IST_BYTES = 81_000  # §5 H3 :114 "~81 KB im Roster" (proxy for O worker render).
_WORKER_TARGET_BYTES = int(_WORKER_IST_BYTES * (1 - WORKER_AVG_REDUCTION_TARGET))  # 52,650.
_ALWAYS_ON_IST_BYTES = 24_317  # §1.3 :67 "24,3 KB" = 24,317 B (OQ-3 aggregate).


# ---------------------------------------------------------------------------
# Helpers — RED stubs (implemented in the GREEN step below)
# ---------------------------------------------------------------------------

def _as_bytes(value):
    """Normalize a baseline int or a report stat mapping to integer bytes."""
    if isinstance(value, Mapping):
        return int(value["bytes"])
    return int(value)


def load_baseline(path):
    """Read a {provider: {artifact: int}} baseline JSON file."""
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    return {
        provider: {artifact: int(size) for artifact, size in artifacts.items()}
        for provider, artifacts in data.items()
    }


def check_no_growth(measured, baseline, max_growth_ratio=NO_GROWTH_TOLERANCE):
    """Return one message per (provider, artifact) grown beyond baseline*(1+ratio)."""
    violations = []
    for provider, artifacts in measured.items():
        provider_baseline = baseline.get(provider, {})
        for artifact, current in artifacts.items():
            base = provider_baseline.get(artifact)
            if base is None:
                continue  # no baseline value to ratchet against
            current_bytes = _as_bytes(current)
            limit = base * (1 + max_growth_ratio)
            if current_bytes > limit:
                delta = current_bytes - base
                pct = ((current_bytes / base) - 1) * 100 if base else float("inf")
                violations.append(
                    f"{provider}/{artifact}: {current_bytes} B > {limit:.2f} B "
                    f"(baseline {base} B, +{delta} B / +{pct:.1f} % "
                    f"> {max_growth_ratio:.0%} tolerance)"
                )
    return violations


def check_session_ceiling(session_sum, ceilings):
    """Return one message per provider whose session-sum bytes exceed its ceiling."""
    violations = []
    for provider, stats in session_sum.items():
        ceiling = ceilings.get(provider)
        if ceiling is None:
            continue
        value = _as_bytes(stats)
        if value > ceiling:
            violations.append(
                f"{provider}: session-sum {value} B > ceiling {ceiling} B")
    return violations


# ---------------------------------------------------------------------------
# Unit tests — pure helpers (always run)
# ---------------------------------------------------------------------------

def test_load_baseline_parses_provider_artifact_ints(tmp_path):
    payload = {
        "Claude": {"orchestrator": 72_000, "rules": 20_690},
        "Opencode": {"orchestrator": 71_000},
    }
    path = tmp_path / "baseline-batch-0.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    assert load_baseline(path) == payload


def test_check_no_growth_within_tolerance_is_clean():
    baseline = {"P": {"a": 1000, "b": 2000}}
    measured = {"P": {"a": 1005, "b": 2010}}  # +0.5 %, +0.5 % -> below 1 %
    assert check_no_growth(measured, baseline) == []


def test_check_no_growth_boundary_exactly_one_percent_is_clean():
    baseline = {"P": {"a": 1000}}
    measured = {"P": {"a": 1010}}  # exactly +1 % -> strict '>' means clean
    assert check_no_growth(measured, baseline) == []


def test_check_no_growth_flags_growth_with_provider_artifact_delta():
    baseline = {"P": {"a": 1000}}
    measured = {"P": {"a": 1020}}  # +2 % -> above 1 %
    violations = check_no_growth(measured, baseline)
    assert len(violations) == 1
    assert "P/a" in violations[0]
    assert "1020" in violations[0]
    assert "+20" in violations[0]


def test_check_no_growth_accepts_report_stat_mappings():
    baseline = {"P": {"a": 1000}}
    measured = {"P": {"a": {"bytes": 1000, "lines": 10, "tokens_approx": 250}}}
    assert check_no_growth(measured, baseline) == []


def test_check_session_ceiling_within_and_above():
    session_sum = {"Claude": {"bytes": 19_500}, "Opencode": {"bytes": 24_000}}
    assert check_session_ceiling(session_sum, {"Claude": 19_500, "Opencode": 25_000}) == []
    violations = check_session_ceiling(session_sum, {"Claude": 19_500, "Opencode": 23_000})
    assert len(violations) == 1
    assert "Opencode" in violations[0] and "24000" in violations[0]


# ---------------------------------------------------------------------------
# Constant-contract tests (always run, PASS)
# ---------------------------------------------------------------------------

def test_growth_tolerance_is_one_percent_not_two():
    assert NO_GROWTH_TOLERANCE == 0.01
    # Deliberately different from tests/test_context_budgets.py TOLERANCE_RATIO = 0.02.
    assert NO_GROWTH_TOLERANCE != 0.02


def test_session_ceiling_has_no_growth_buffer():
    # OQ-3: single decimal ceiling, no *1.01 variant (review major-1).
    assert SESSION_CEILING_BYTES == 19_500
    assert SESSION_CEILING_BYTES != 19_500 * 1024
    assert SESSION_CEILING_BYTES != int(19_500 * (1 + NO_GROWTH_TOLERANCE))


def test_agents_md_target_documented_but_out_of_scope():
    # §5 :120 / H6 — recorded for traceability, NOT parametrized (H6/P30 out of scope).
    assert AGENTS_MD_TARGET_BYTES == 12_000


# ---------------------------------------------------------------------------
# Integration tests — need Task 1.1 baseline + measurement (skip per AC-10)
# ---------------------------------------------------------------------------

@pytest.fixture(scope="module")
def baseline():
    if not DEFAULT_BASELINE.is_file():
        pytest.skip(
            f"baseline-batch-0.json missing — run Task 1.1 first ({DEFAULT_BASELINE})")
    return load_baseline(DEFAULT_BASELINE)


def _measure_current():
    """Flatten Task 1.1's per-agent report to {provider: {artifact: bytes}}."""
    import importlib.util
    import sys

    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    report_path = REPO_ROOT / "scripts" / "lib" / "agent_report.py"
    if not report_path.is_file():
        pytest.skip("Task 1.1 agent_report.py missing — cannot measure current artifacts")
    spec = importlib.util.spec_from_file_location("agent_report", report_path)
    agent_report = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(agent_report)
    from lib import context_report as cr
    from lib.providers import load_provider_capabilities, load_providers_config

    mappings = cr.merge_provider_mappings(
        load_providers_config(REPO_ROOT, {}), load_provider_capabilities(REPO_ROOT))
    report = agent_report.measure_agents(REPO_ROOT, sorted(mappings), mappings)
    return {
        provider: {artifact: _as_bytes(stats) for artifact, stats in artifacts.items()}
        for provider, artifacts in report.items()
    }


def test_no_artifact_grows(baseline):
    current = _measure_current()
    assert check_no_growth(current, baseline) == []


# ---------------------------------------------------------------------------
# §5 target values as xfail(strict=True) — OQ-1 (binding)
# The candidate values are documented §5 Ist-values; the check asserts the goal is
# reached, so it fails (xfail) today. Batch 11 achieveing a goal -> XPASS -> build
# fails and forces removal of the marker (ADR-2). AGENTS.md is NOT parametrized.
#
# Quality fix: `current_bytes` is no longer a frozen constant compared to another
# frozen constant. It is resolved through the `measurement_override` fixture
# (default = documented Ist value), so a real measurement reaching a §5 target
# makes the assertion PASS -> XPASS(strict) -> build failure (ADR-2). The
# `target_reached` helper is shared with the helper-level proof test below.
# ---------------------------------------------------------------------------

@pytest.fixture
def measurement_override():
    """Injectable {target_name: current_bytes} measurement; defaults to {}.

    Empty by default -> the documented Ist fallback is used and every xfail
    stays xfail. Override a key to the §5 limit to simulate a reached goal;
    the xfail(strict) assertion then passes and pytest reports XPASS -> fail.
    """
    return {}


def target_reached(current_bytes, limit_bytes):
    """The assertion body of the xfail(strict) target checks: goal reached?"""
    return current_bytes <= limit_bytes


@pytest.mark.parametrize(
    "target_name,ist_bytes,limit_bytes",
    [
        pytest.param(
            "orchestrator-render", _ORCHESTRATOR_IST_BYTES, ORCHESTRATOR_RENDER_TARGET_BYTES,
            marks=pytest.mark.xfail(
                strict=True,
                reason="§5 target 'Orchestrator-Render <=28 KB' not yet reached")),
        pytest.param(
            "roster", _ROSTER_IST_BYTES, ROSTER_TARGET_BYTES,
            marks=pytest.mark.xfail(
                strict=True,
                reason="§5 target 'Roster <=300 KB' not yet reached")),
        pytest.param(
            "worker-average", _WORKER_IST_BYTES, _WORKER_TARGET_BYTES,
            marks=pytest.mark.xfail(
                strict=True,
                reason="§5 target 'O Worker -35 %' not yet reached")),
        pytest.param(
            "always-on-session", _ALWAYS_ON_IST_BYTES, SESSION_CEILING_BYTES,
            marks=pytest.mark.xfail(
                strict=True,
                reason="§5 target 'Always-on <=19,5 KB' not yet reached")),
    ],
)
def test_target_values_are_xfail_strict(target_name, ist_bytes, limit_bytes,
                                        measurement_override):
    current_bytes = measurement_override.get(target_name, ist_bytes)
    assert target_reached(current_bytes, limit_bytes), (
        f"§5 target {target_name}: {current_bytes} B > {limit_bytes} B")


@pytest.mark.xfail(
    strict=True,
    reason="§5 target 'Always-on Claude <=19,5 KB' (OQ-3 session-sum) not yet reached")
def test_session_sum_ceiling(measurement_override):
    # OQ-3: single 19,500 B ceiling; session_sum = entry + rules + descriptions
    # (§1.3 :67 = 24,317 B). No *1.01 variant.
    current = measurement_override.get("always-on-session", _ALWAYS_ON_IST_BYTES)
    session_sum = {"Claude": {"bytes": current}}
    ceilings = {"Claude": SESSION_CEILING_BYTES}
    assert check_session_ceiling(session_sum, ceilings) == []


def test_xfail_assertions_flip_when_target_is_reached():
    """Helper-level proof: reaching the target makes the xfail assertion PASS.

    XPASS(strict) is then a build failure (ADR-2), so the marker must be removed.
    This test runs green (not xfail) and documents that signal explicitly.
    """
    # Parametrized-target path: the assertion is `current_bytes <= limit_bytes`.
    assert target_reached(ORCHESTRATOR_RENDER_TARGET_BYTES,
                          ORCHESTRATOR_RENDER_TARGET_BYTES) is True      # -> XPASS
    assert target_reached(ORCHESTRATOR_RENDER_TARGET_BYTES + 1,
                          ORCHESTRATOR_RENDER_TARGET_BYTES) is False     # -> xfail
    assert target_reached(SESSION_CEILING_BYTES, SESSION_CEILING_BYTES) is True
    assert target_reached(SESSION_CEILING_BYTES + 1, SESSION_CEILING_BYTES) is False

    # Fixture override resolves current_bytes to the target (default stays Ist).
    override = {"orchestrator-render": ORCHESTRATOR_RENDER_TARGET_BYTES}
    effective = override.get("orchestrator-render", _ORCHESTRATOR_IST_BYTES)
    assert effective == ORCHESTRATOR_RENDER_TARGET_BYTES
    assert target_reached(effective, ORCHESTRATOR_RENDER_TARGET_BYTES) is True

    # Session-sum path: check_session_ceiling returns [] only at/below ceiling.
    ceilings = {"Claude": SESSION_CEILING_BYTES}
    at_limit = {"Claude": {"bytes": SESSION_CEILING_BYTES}}
    above_limit = {"Claude": {"bytes": SESSION_CEILING_BYTES + 1}}
    assert check_session_ceiling(at_limit, ceilings) == []                # -> XPASS
    assert len(check_session_ceiling(above_limit, ceilings)) == 1         # -> xfail
