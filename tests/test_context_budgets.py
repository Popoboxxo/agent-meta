"""Per-provider context budgets as ceilings (QG-4, AC-07/AC-26 of SPEC-CONTEXT-PROFILES-2026-10-11).

``FULL_BUDGET_CEILINGS`` pins the measured Ist-values of the ``full`` profile
(Spec section 2, re-measured with ``measure_artifacts`` on the provider-matrix
projects of tests/test_ac01_render_identity.py) as upper bounds. Any change
that grows an artifact beyond its ceiling turns this test red.

``COMPACT_BUDGET_CEILINGS`` does the same for the opt-in ``compact`` profile
(measured through ``context_report.render_into_work_dir(..., profile="compact")``),
and ``COMPACT_BUDGET_TARGETS`` records the AC-26 size *targets* as ESTIMATE data
(Spec section 11) -- they are goals, not measurements, and are never asserted as
met while ``compact`` ships opt-in/unverified (IC-36).

Tolerance rationale: the measured projects contain the scratch root path and a
date stamp, so sizes vary by a few bytes between runs. The ceiling is
Ist + max(``TOLERANCE_MIN_BYTES``, ``TOLERANCE_RATIO`` * Ist), i.e. small
enough to catch real growth, large enough to be path-length independent.

The tolerance max(256 B, 2 %) is our interpretation of QG-4/AC-07, which does
not fix a number: it absorbs date and scratch-path jitter. For large artifacts
2 % is wide (e.g. ~11 KB on a 577 KB roster), so the ceiling is a guard against
growth, not an exact pin. To bound that, the tolerance is additionally capped at
``TOLERANCE_MAX_BYTES`` (4 KB). The tolerance could be made precise by a spec
revision of QG-4/AC-07.

Run: python3 -m pytest tests/test_context_budgets.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Dict, List, Mapping, Sequence, Tuple

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import context_report as cr  # noqa: E402
from lib.providers import load_provider_capabilities, load_providers_config  # noqa: E402
from tests.test_ac01_render_identity import _make_project  # noqa: E402

TOLERANCE_MIN_BYTES = 256
TOLERANCE_RATIO = 0.02
TOLERANCE_MAX_BYTES = 4096

# Ist-values in bytes (data table). Matches Spec section 2 (Claude orchestrator
# 90,691 B, CLAUDE.md ~2.5 KB, Claude rules 17.9-18.3 KB, AGENTS.md 25.6 KB / Gemini 33 KB).
# Re-pinned in Task 0e.2 (meta-doctor role + agent-meta-manager 1.24.0 consumer section:
# harness-roster +~9.7 KB, orchestrator +0.5-0.6 KB, AGENTS.md +~90 B).
# Re-pinned again after the review fixes (meta-doctor allowlist text, manager input_contracts without task-spec-v1).
# Known, unexplained deviation: Continue rules measure 19,004 B vs. 18,591 B in the
# spec; the Ist-value below pins the measurement, the delta is not yet clarified.
# Re-pinned for the default pipeline drop (IC-18 no. 2, Task 1.10): orchestrator -3.8..-4.5 KB per provider.
# Re-pinned for the tier-chain gate (IC-18 no. 5, Task 1.13): default orchestrator -762 B per provider.
# Re-pinned for the data-driven anti-recursion block (IC-18 no. 6, Task 1.14): default drops /validator (-10 B).
# Re-pinned for the orchestrator prose gating (IC-18 no. 8, Task 1.16): SE prose off by default, dropped pipelines no longer named.
# Re-pinned for the IC-30 triage (IC-18 no. 11, Task 1.19): documenter KE route and bug-feature-analyzer SE rows drop in the default (harness-roster -263 B).
# Re-pinned for PR E (IC-15 no. 1/9/12, Tasks 1.21/1.23/1.33): AGENTS.md lists only active sharers and
# no hard-wired banner, use-lazy-rules is not rendered without existing skills (-1.0 KB rules/entry file),
# Codex/Mammouth no longer write their unread rules dirs (their `rules` pin is dropped). Only decreases.
_IST_FULL: Dict[str, Dict[str, int]] = {
    "Claude": {"entry-file": 2511, "rules": 17268, "orchestrator": 85147, "harness-roster": 581274, "always-loaded": 601053},
    "Codex": {"entry-file": 24143, "orchestrator": 84587, "harness-roster": 575241, "always-loaded": 599384},
    # Continue: rule files gained `alwaysApply: false` + `description` frontmatter
    # (Task 1.31, IC-15 Nr. 10 / F-14) and `.continue/rules/project-context.md`
    # dropped its unresolved-placeholder lines; the disk-byte metric counts the
    # frontmatter, so `rules`/`always-loaded` grow while the runtime always-on set
    # shrinks (the reader lazy-loads `alwaysApply: false` files).
    "Continue": {"entry-file": 374, "rules": 20174, "orchestrator": 69871, "always-loaded": 20548},
    # Copilot: `.github/instructions/*.instructions.md` gained the required suffix
    # plus `applyTo`/`description` frontmatter and the agent `name:` fix
    # (Task 1.29, IC-15 Nr. 3 / F-13) — pin refreshed to the measured Ist.
    "Copilot": {"entry-file": 9425, "rules": 19954, "orchestrator": 69747, "always-loaded": 29379},
    "Gemini": {"entry-file": 31715, "rules": 17268, "orchestrator": 85169, "always-loaded": 48983},
    "KimiCode": {"entry-file": 24157, "orchestrator": 70468, "harness-roster": 566366, "always-loaded": 590523},
    "Mammouth": {"entry-file": 24154, "orchestrator": 70242, "harness-roster": 568677, "always-loaded": 592831},
    "Opencode": {"entry-file": 24218, "orchestrator": 84835, "harness-roster": 577758, "always-loaded": 601976},
    "ZCode": {"entry-file": 25056, "orchestrator": 70443, "harness-roster": 565162, "always-loaded": 590218},
}


def _ceiling(ist: int) -> int:
    return ist + min(TOLERANCE_MAX_BYTES, max(TOLERANCE_MIN_BYTES, int(ist * TOLERANCE_RATIO)))


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
    # Inflate against the PINNED ceiling, not `_ceiling(len(original))`: after the
    # phase-1 slimming the artifact is smaller than its pinned Ist, so its own
    # tolerance ceiling sits below the pin and would not trip the check.
    limit = FULL_BUDGET_CEILINGS[provider]["orchestrator"]
    try:
        target.write_bytes(original + b"x" * (limit - len(original) + 1))
        violations = check_ceilings(_measure(projects, mappings), FULL_BUDGET_CEILINGS)
    finally:
        target.write_bytes(original)
    assert any(v.startswith(f"{provider}/orchestrator:") for v in violations), violations
    assert check_ceilings(_measure(projects, mappings), FULL_BUDGET_CEILINGS) == []


def test_ac07_missing_ceiling_is_a_violation():
    report = {"Alpha": {"entry-file": {"bytes": 1}}}
    assert check_ceilings(report, {}) == ["Alpha/entry-file: no ceiling pinned"]


# ---------------------------------------------------------------------------
# Profile `compact` (QG-4). `compact` is opt-in and unverified (IC-36); the
# pins below are measurements/targets, never a verification claim.
# ---------------------------------------------------------------------------

# Ist-values in bytes of the rendered `compact` matrix, measured with the shared
# render seam ``context_report.render_into_work_dir(..., profile="compact")``
# plus ``measure_artifacts`` (same basis as ``_IST_FULL``). Data table, not a
# target: the ceiling is Ist + tolerance and guards against growth.
_IST_COMPACT: Dict[str, Dict[str, int]] = {
    "Claude": {"entry-file": 2530, "rules": 17286, "orchestrator": 32450,
               "harness-roster": 528294, "always-loaded": 548110},
    "Codex": {"entry-file": 9634, "orchestrator": 31967,
              "harness-roster": 522159, "always-loaded": 531793},
    "Continue": {"entry-file": 374, "rules": 20174, "orchestrator": 31836,
                 "always-loaded": 20548},
    "Copilot": {"entry-file": 9468, "rules": 19954, "orchestrator": 31710,
                "always-loaded": 29422},
    # Gemini renders its rules embedded into the shared AGENTS.md in `compact`,
    # so no `rules` artifact is written (unlike `full`).
    "Gemini": {"entry-file": 10108, "orchestrator": 32584, "always-loaded": 10108},
    "KimiCode": {"entry-file": 9644, "orchestrator": 33159,
                 "harness-roster": 529039, "always-loaded": 538683},
    "Mammouth": {"entry-file": 9642, "orchestrator": 31755,
                 "harness-roster": 525127, "always-loaded": 534769},
    "Opencode": {"entry-file": 9703, "orchestrator": 32112,
                 "harness-roster": 524707, "always-loaded": 534410},
    "ZCode": {"entry-file": 10567, "orchestrator": 31981,
              "harness-roster": 526417, "always-loaded": 536984},
}

COMPACT_BUDGET_CEILINGS: Dict[str, Dict[str, int]] = {
    provider: {artifact: _ceiling(size) for artifact, size in artifacts.items()}
    for provider, artifacts in _IST_COMPACT.items()
}

# The AGENTS.md providers share one context file; measured in a single project
# with all of them active (`compact`).
_AGENTS_MD_PROVIDERS = ("Codex", "Gemini", "KimiCode", "Mammouth", "Opencode", "ZCode")
_IST_COMPACT_MULTI_AGENTS_MD = 11374

# AC-26 size targets for `compact`, as DATA (never a library constant; C7).
# ESTIMATES (Spec section 11): goals, not measurements. `compact` ships
# opt-in/unverified (IC-36) and AC-24/AC-25 are unfulfilled, so these are
# recorded and checkable but not asserted as met. AC-26 forbids a silent
# adjustment -- a changed value needs a spec revision.
# storage: "pin"        = test-only data (this table);
#          "capability" = already a config key (C7,
#                         config/provider-capabilities.yaml), surfaced by the
#                         report as the artifact's `cap`/`cap_kind`.
COMPACT_BUDGET_TARGETS: Tuple[Tuple[str, int, str, str], ...] = (
    ("Claude orchestrator <= 32 KB", 32 * 1024, "bytes", "pin"),
    ("AGENTS.md single provider <= 8 KB", 8 * 1024, "bytes", "pin"),
    ("AGENTS.md multi provider <= 12 KB", 12 * 1024, "bytes", "pin"),
    ("AGENTS.md multi provider < 32,768 B", 32768, "bytes", "capability"),
    ("Gemini AGENTS.md <= 9 KB", 9 * 1024, "bytes", "pin"),
    ("Continue always-on rules <= 2 KB", 2 * 1024, "bytes", "pin"),
    ("Copilot instruction file <= 4,000 chars", 4000, "chars", "capability"),
)
COMPACT_TARGET_ESTIMATE_LABEL = "ESTIMATE (Spec section 11 / AC-26)"


def measured_in_unit(stat: Mapping[str, int], unit: str) -> int:
    """Return *stat*'s size in *unit*.

    Supported units are ``"bytes"`` (``stat["bytes"]``) and ``"chars"``
    (``stat["chars"]``, the decoded character count); any other unit raises, so a
    byte metric is never silently compared against a target in a different unit.
    """
    if unit == "bytes":
        return stat["bytes"]
    if unit == "chars":
        return stat["chars"]
    raise ValueError(f"unsupported target unit: {unit!r}")


def check_target(stat: Mapping[str, int], target: Tuple[str, int, str, str]) -> str:
    """Return a violation message when *stat* exceeds *target* in the target's unit.

    The comparison uses the unit the target declares (``bytes``/``chars``); the
    stat must carry that metric (see :func:`measured_in_unit`). Targets are
    estimates, so the caller decides whether to assert. Used to prove a grown
    artifact trips the target check (künstliche Vergrößerung ⇒ rot).
    """
    name, limit, unit, _storage = target
    value = measured_in_unit(stat, unit)
    return f"{name}: {value} {unit} > {limit}" if value > limit else ""


def _matrix_config(root: Path, name: str, providers: Sequence[str]) -> Path:
    config = root / name / ".meta-config" / "project.yaml"
    config.parent.mkdir(parents=True, exist_ok=True)
    config.write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        "ai-providers:\n" + "".join(f"- {p}\n" for p in providers) +
        "dod-preset: rapid-prototyping\n"
        "variables:\n  PROJECT_NAME: matrix\n  PROJECT_PREFIX: mx\n",
        encoding="utf-8")
    return config


def _matrix_mappings() -> dict:
    return cr.merge_provider_mappings(
        load_providers_config(REPO_ROOT, {}), load_provider_capabilities(REPO_ROOT))


@pytest.fixture(scope="module")
def measured_compact(tmp_path_factory):
    root = tmp_path_factory.mktemp("budgets-compact")
    mappings = _matrix_mappings()
    report: dict = {}
    works: dict = {}
    for provider in _PROVIDERS:
        config = _matrix_config(root, provider, [provider])
        work = root / (provider + "-work")
        cr.render_into_work_dir(REPO_ROOT, config, work, profile="compact")
        works[provider] = work
        report.update(cr.measure_artifacts(work, [provider], mappings))
    return report, mappings, works


@pytest.fixture(scope="module")
def measured_compact_multi(tmp_path_factory):
    root = tmp_path_factory.mktemp("budgets-compact-multi")
    mappings = _matrix_mappings()
    config = _matrix_config(root, "multi", _AGENTS_MD_PROVIDERS)
    work = root / "work"
    cr.render_into_work_dir(REPO_ROOT, config, work, profile="compact")
    return cr.measure_artifacts(work, _AGENTS_MD_PROVIDERS, mappings)


def test_compact_profile_within_ceilings(measured_compact):
    report, _mappings, _works = measured_compact
    assert check_ceilings(report, COMPACT_BUDGET_CEILINGS) == []


def test_compact_inflated_artifact_exceeds_ceiling(measured_compact):
    """Meta-test: really growing a compact render makes the check fail."""
    _report, mappings, works = measured_compact
    provider = _PROVIDERS[0]
    caps = mappings[provider]
    target = works[provider] / caps["agents_dir"] / (
        "orchestrator" + (caps.get("agent_ext") or ".md"))
    original = target.read_bytes()
    limit = COMPACT_BUDGET_CEILINGS[provider]["orchestrator"]
    try:
        target.write_bytes(original + b"x" * (limit - len(original) + 1))
        violations = check_ceilings(
            cr.measure_artifacts(works[provider], [provider], mappings), COMPACT_BUDGET_CEILINGS)
    finally:
        target.write_bytes(original)
    assert any(v.startswith(f"{provider}/orchestrator:") for v in violations), violations
    assert check_ceilings(
        cr.measure_artifacts(works[provider], [provider], mappings), COMPACT_BUDGET_CEILINGS) == []


def test_compact_targets_are_labelled_estimates():
    """AC-26 targets are recorded as ESTIMATE data, never as a library constant."""
    module = (REPO_ROOT / "scripts" / "lib" / "context_report.py").read_text(encoding="utf-8")
    assert "COMPACT_BUDGET_TARGETS" not in module
    assert all(row[3] in ("pin", "capability") for row in COMPACT_BUDGET_TARGETS)
    assert "ESTIMATE" in COMPACT_TARGET_ESTIMATE_LABEL.upper()


def test_compact_target_check_flags_grown_artifact(measured_compact):
    """A value above its byte target trips the check; the exact target does not."""
    report, _mappings, _works = measured_compact
    provider = _PROVIDERS[0]
    stat = report[provider]["orchestrator"]
    tight = (f"{provider} orchestrator", stat["bytes"] - 1, "bytes", "pin")
    exact = (f"{provider} orchestrator", stat["bytes"], "bytes", "pin")
    assert check_target(stat, tight) != ""
    assert check_target(stat, exact) == ""


def test_compact_target_check_uses_declared_unit():
    """A byte limit and a char limit are evaluated in their own unit."""
    stat = {"bytes": 12, "chars": 8}
    assert check_target(stat, ("bytes t", 10, "bytes", "pin")) != ""
    assert check_target(stat, ("chars t", 10, "chars", "pin")) == ""
    with pytest.raises(ValueError):
        measured_in_unit(stat, "lines")


def test_compact_copilot_target_is_evaluated_in_chars(measured_compact):
    """The 4,000-char Copilot target is checked against the char metric (C7)."""
    report, mappings, works = measured_compact
    caps = mappings["Copilot"]
    stat = dict(report["Copilot"]["entry-file"])
    stat["chars"] = len((works["Copilot"] / caps["context_file"]).read_text(encoding="utf-8"))
    char_target = next(row for row in COMPACT_BUDGET_TARGETS if row[2] == "chars")
    assert char_target[1] == caps["context_soft_cap_chars"] == 4000
    message = check_target(stat, char_target)
    assert message.endswith(" chars > 4000") and str(stat["chars"]) in message


def test_compact_copilot_and_hard_bound_live_as_config_keys(measured_compact):
    """C7: two AC-26 targets are capability config keys, surfaced by the report."""
    caps = load_provider_capabilities(REPO_ROOT)
    assert caps["Copilot"]["context_soft_cap_chars"] == 4000
    assert caps["Codex"]["context_hard_cap_bytes"] == 32768
    report, _mappings, _works = measured_compact
    copilot = report["Copilot"]["entry-file"]
    assert copilot["cap"] == 4000 and copilot["cap_kind"] == "soft-chars"


def test_compact_multi_provider_entry_file_below_hard_cap(measured_compact_multi):
    entry = measured_compact_multi["Codex"]["entry-file"]
    assert entry["cap"] == 32768 and entry["cap_kind"] == "hard-bytes"
    assert entry["bytes"] < 32768
    assert entry["bytes"] <= _ceiling(_IST_COMPACT_MULTI_AGENTS_MD)
    # all AGENTS.md providers read the same shared file
    assert {measured_compact_multi[p]["entry-file"]["bytes"] for p in _AGENTS_MD_PROVIDERS} == {
        entry["bytes"]}
