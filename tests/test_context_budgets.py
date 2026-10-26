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
from lib.tmp_paths import resolve_tmp_paths  # noqa: E402
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
# Re-pinned in Task 30 (2e.4, IC-27/AC-90): the `agent-meta-manager` template gains the section
# `## 10c. Optimizer-Vorschläge anwenden (Advisory Mode)` (the Analyse/Vorschau/Anwendung chain) —
# ~2.3 KB on every provider roster (the 6 providers with a harness-roster; 2,346 B in the Claude
# render, measured — the placeholder substitutions make the exact value provider-dependent) and on
# their always-loaded set; every other artifact is unchanged by this task. The re-pin additionally
# absorbs the stale pins left by the Phase-2 tasks 2e.2/2e.3 (registration of the new role
# `meta-optimizer`: roster rows in the orchestrator, the AGENTS.md agent table and the per-provider
# agent files, ~+7.5 KB roster) and by the compact-profile work: at HEAD the gate was already RED
# before this task started (e.g. Claude/harness-roster 588,854 B vs. ceiling 585,370 B; compact
# 534,875 B vs. 532,390 B). The pins below are therefore re-measured from the current state, not
# extrapolated.
# The polish round of Task 30 (2e.4) completes the §10c "No manual edit" rule by the §13 reference
# ("§3/§5/§8" -> "§3/§5/§8/§13 (confirmation, schema check, re-sync, SE cascade)"): +17 B on every
# provider roster and on the always-loaded set, no other artifact changes.
#
# ABSORBED DELTAS OF THIS RE-PIN (measured, not extrapolated — HEAD pin -> measured Ist).
# The list is COMPLETE for both profiles: every artifact with a non-zero delta is named below.
# A later re-pin must nevertheless re-measure EVERY artifact — this list documents THIS re-pin, it
# is not a maintenance promise. That is what keeps a stale pin from being inherited silently.
# `full` profile:
#   * harness-roster (the `meta-optimizer` registration + the new §10c section):
#     Claude 581,274 -> 591,201 (+9,927), Codex 575,241 -> 585,156 (+9,915),
#     KimiCode 566,366 -> 577,663 (+11,297), Mammouth 568,677 -> 573,719 (+5,042),
#     Opencode 577,758 -> 587,666 (+9,908), ZCode 565,162 -> 575,003 (+9,841).
#   * always-loaded (roster + entry-file + rules deltas):
#     Claude +9,927, Codex +9,932, Continue -50, Copilot +14, KimiCode +11,314, Mammouth +5,059,
#     Opencode +9,925, ZCode +9,858.
#   * orchestrator (the `meta-optimizer` routing rows):
#     Claude 85,147 -> 85,530 (+383), Codex 84,587 -> 85,145 (+558),
#     Continue 69,871 -> 70,180 (+309), Copilot 69,747 -> 70,056 (+309),
#     Gemini 85,169 -> 85,552 (+383), KimiCode 70,468 -> 71,943 (+1,475),
#     Mammouth 70,242 -> 70,481 (+239), Opencode 84,835 -> 85,218 (+383),
#     ZCode 70,443 -> 70,752 (+309).
#   * entry-file: Codex/KimiCode/Mammouth/Opencode/ZCode +17 B each (the `meta-optimizer` row in the
#     agent table), Continue 374 -> 358 (-16), Copilot 9,425 -> 9,457 (+32),
#     Gemini 31,715 -> 31,841 (+126); Claude unchanged.
#   * rules: Continue 20,174 -> 20,140 (-34), Copilot 19,954 -> 19,936 (-18); Claude/Gemini unchanged.
#   * `Gemini/always-loaded` 48,983 -> 31,841 B (-17,142 B) — the largest absorbed delta, a
#     **pre-existing stale pin** from the Phase-1 / compact-profile work (the Gemini rules are
#     embedded into the shared AGENTS.md, so no separate rules artifact counts into the
#     always-loaded set). NOT caused by Task 30; the next re-pin must not inherit it silently.
# RE-PIN (literature evidence gates, review round 2): eight new review roles registered (roster +85 KB, orchestrator +5.9 KB, agent-table rows +864 B)
# Absorbed deltas of this re-pin (measured, not extrapolated):
#   * Claude/always-loaded: 610980 -> 696038 (+85058)
#   * Claude/harness-roster: 591201 -> 676259 (+85058)
#   * Claude/orchestrator: 85530 -> 91418 (+5888)
#   * Codex/always-loaded: 609316 -> 694297 (+84981)
#   * Codex/entry-file: 24160 -> 25024 (+864)
#   * Codex/harness-roster: 585156 -> 669273 (+84117)
#   * Codex/orchestrator: 85145 -> 91033 (+5888)
#   * Continue/orchestrator: 70180 -> 75570 (+5390)
#   * Copilot/always-loaded: 29393 -> 30823 (+1430)
#   * Copilot/entry-file: 9457 -> 10887 (+1430)
#   * Copilot/orchestrator: 70056 -> 75446 (+5390)
#   * Gemini/always-loaded: 31841 -> 33667 (+1826)
#   * Gemini/entry-file: 31841 -> 33667 (+1826)
#   * Gemini/orchestrator: 85552 -> 91440 (+5888)
#   * KimiCode/always-loaded: 601837 -> 687531 (+85694)
#   * KimiCode/entry-file: 24174 -> 25038 (+864)
#   * KimiCode/harness-roster: 577663 -> 662493 (+84830)
#   * KimiCode/orchestrator: 71943 -> 77499 (+5556)
#   * Mammouth/always-loaded: 597890 -> 682788 (+84898)
#   * Mammouth/entry-file: 24171 -> 25035 (+864)
#   * Mammouth/harness-roster: 573719 -> 657753 (+84034)
#   * Mammouth/orchestrator: 70481 -> 75871 (+5390)
#   * Opencode/always-loaded: 611901 -> 697208 (+85307)
#   * Opencode/entry-file: 24235 -> 25099 (+864)
#   * Opencode/harness-roster: 587666 -> 672109 (+84443)
#   * Opencode/orchestrator: 85218 -> 91105 (+5887)
#   * ZCode/always-loaded: 600076 -> 685404 (+85328)
#   * ZCode/entry-file: 25073 -> 25937 (+864)
#   * ZCode/harness-roster: 575003 -> 659467 (+84464)
#   * ZCode/orchestrator: 70752 -> 76142 (+5390)
# RE-PIN (literature round 2 follow-up, fixes A-F, 2026-10-26): every artifact re-measured
# on the provider matrix, not extrapolated. Cause split, verified by re-rendering the
# pre-fix merge state (c7be7616) and the working tree file by file:
#   * A (name-only roles excluded from the rendered agent table): -1,177 B on the
#     orchestrator of every provider and -1,177 B on each AGENTS.md entry file (Codex,
#     Gemini, KimiCode, Mammouth, Opencode, ZCode). The table drops the 12 name-only rows
#     active in the matrix (the eight literature roles plus intern-developer, meta-doctor,
#     meta-optimizer, template-auditor). Claude's CLAUDE.md carries no agent table.
#   * C/D (arrow decoupling in the literature templates): chaos-engineer -79 B,
#     reproducible-builds-engineer -76 B, ux-researcher +29 B per provider artifact.
#     E's gated dispatch rows are render-neutral in the matrix (every role active, so the
#     rows stay), F only touches the standalone export: 0 B here.
#   * Pre-existing post-merge drift (f9e3f3e5, tmp-sink): test-executor.md shrank 17 B
#     (7,215 -> 7,198), so the roster/always-loaded pins were 17 B high before this
#     re-pin. Absorbed here; not caused by A-F.
# Absorbed deltas (old pin -> measured Ist), `full` profile:
#   * orchestrator, all nine: -1,177 B each (Claude 91418 -> 90241, Codex 91033 -> 89856,
#     Continue 75570 -> 74393, Copilot 75446 -> 74269, Gemini 91440 -> 90263,
#     KimiCode 77499 -> 76322, Mammouth 75871 -> 74694, Opencode 91105 -> 89928,
#     ZCode 76142 -> 74965).
#   * entry-file, six AGENTS.md providers: -1,177 B each (Codex 25024 -> 23847,
#     Gemini 33667 -> 32490, KimiCode 25038 -> 23861, Mammouth 25035 -> 23858,
#     Opencode 25099 -> 23922, ZCode 25937 -> 24760); Claude/Continue/Copilot unchanged.
#   * harness-roster, six roster providers: -1,303 B each (Claude 676259 -> 674939,
#     Codex 669273 -> 667953, KimiCode 662493 -> 661173, Mammouth 657753 -> 656433,
#     Opencode 672109 -> 670789, ZCode 659467 -> 658147) = -1,177 orchestrator -126 roles.
#   * always-loaded: Claude 696038 -> 694718 (-1,303, roster only); Codex
#     694297 -> 691800, KimiCode 687531 -> 685034, Mammouth 682788 -> 680291,
#     Opencode 697208 -> 694711, ZCode 685404 -> 682907 (-2,480 each: entry + roster);
#     Gemini 33667 -> 32490 (-1,177, entry only); Continue/Copilot unchanged.
# RE-PIN (literature evidence gates, review round 2): one evidence-gate rule per role in eight role templates (+7,228 B roster, +1,258 B orchestrator)
# Absorbed deltas of this re-pin (measured, not extrapolated):
#   * Claude/always-loaded: 610980 -> 618208 (+7228)
#   * Claude/harness-roster: 591201 -> 598429 (+7228)
#   * Claude/orchestrator: 85530 -> 86788 (+1258)
#   * Codex/always-loaded: 609316 -> 616544 (+7228)
#   * Codex/harness-roster: 585156 -> 592384 (+7228)
#   * Codex/orchestrator: 85145 -> 86403 (+1258)
#   * Continue/orchestrator: 70180 -> 71438 (+1258)
#   * Copilot/orchestrator: 70056 -> 71314 (+1258)
#   * Gemini/orchestrator: 85552 -> 86810 (+1258)
#   * KimiCode/always-loaded: 601837 -> 609065 (+7228)
#   * KimiCode/harness-roster: 577663 -> 584891 (+7228)
#   * KimiCode/orchestrator: 71943 -> 73201 (+1258)
#   * Mammouth/always-loaded: 597890 -> 605118 (+7228)
#   * Mammouth/harness-roster: 573719 -> 580947 (+7228)
#   * Mammouth/orchestrator: 70481 -> 71739 (+1258)
#   * Opencode/always-loaded: 611901 -> 619145 (+7244)
#   * Opencode/harness-roster: 587666 -> 594910 (+7244)
#   * Opencode/orchestrator: 85218 -> 86476 (+1258)
#   * ZCode/always-loaded: 600076 -> 607304 (+7228)
#   * ZCode/harness-roster: 575003 -> 582231 (+7228)
#   * ZCode/orchestrator: 70752 -> 72010 (+1258)
# RE-PIN (merge of origin/main, tmp-sink injection; 2026-10-25): the merge changed the
# rendered text of the git/tester/security-auditor/database-reviewer/incident-responder/
# performance-optimizer/se-senior-developer role files, so every aggregate that contains
# those files shrank by 16-17 B (the replacement of the system-temp paths is shorter than
# the old literals). Measured, not extrapolated. Complete list of non-zero deltas:
#   * harness-roster: Claude 598429 -> 598413 (-16), Codex 592384 -> 592368 (-16),
#     KimiCode 584891 -> 584875 (-16), Mammouth 580947 -> 580931 (-16),
#     Opencode 594910 -> 594893 (-17), ZCode 582231 -> 582215 (-16).
#   * always-loaded: Claude 618208 -> 618192 (-16), Codex 616544 -> 616528 (-16),
#     KimiCode 609065 -> 609049 (-16), Mammouth 605118 -> 605102 (-16),
#     Opencode 619145 -> 619128 (-17), ZCode 607304 -> 607288 (-16).
#   * orchestrator: Opencode 86476 -> 86475 (-1). Every other artifact is unchanged
#     (entry-file, rules, Continue/Copilot/Gemini and all their artifacts).
# MERGE RE-PIN (main bb92039f / #1013 into feat/lit-r2-new-roles / #1015, 2026-10-26):
# measured on the merged tree with `measure_artifacts`, not merged arithmetically. The two
# parents had rebaselined independently; against the main (#1013 + tmp-sink) pin the merged
# tree absorbs #1015's eight review roles and follow-up series A-F:
#   * roster/always-loaded: Claude +82,497 (598,413 -> 680,910), Codex +81,556
#     (592,368 -> 673,924), KimiCode +82,269 (584,875 -> 667,144), Mammouth +81,473
#     (580,931 -> 662,404), Opencode +81,867 (594,893 -> 676,760), ZCode +81,903
#     (582,215 -> 664,118).
#   * orchestrator: +3,453 Claude/Codex/Gemini/Opencode, +3,121 KimiCode, +2,955
#     Continue/Copilot/Mammouth/ZCode — the #1015 routing rows net of the 12 name-only
#     table rows removed by fix A.
#   * entry-file: -313 on the six AGENTS.md providers (+864 from #1015's rows, -1,177
#     from fix A), Copilot +1,430; Continue/Gemini and every `rules` artifact unchanged.
# Against the branch (#1015 + A-F) pin the same tree adds exactly #1013's evidence gates:
# +5,971 B roster/always-loaded on the six roster providers (seven of the eight enriched
# roles are active in the matrix; `se-senior-developer` is gated off), orchestrator,
# entry-file and rules unchanged.
_IST_FULL: Dict[str, Dict[str, int]] = {
    "Claude": {"always-loaded": 700689, "entry-file": 2511, "harness-roster": 680910, "orchestrator": 90241, "rules": 17268},
    "Codex": {"always-loaded": 697771, "entry-file": 23847, "harness-roster": 673924, "orchestrator": 89856},
    "Continue": {"always-loaded": 20498, "entry-file": 358, "orchestrator": 74393, "rules": 20140},
    "Copilot": {"always-loaded": 30823, "entry-file": 10887, "orchestrator": 74269, "rules": 19936},
    "Gemini": {"always-loaded": 32490, "entry-file": 32490, "orchestrator": 90263},
    "KimiCode": {"always-loaded": 691005, "entry-file": 23861, "harness-roster": 667144, "orchestrator": 76322},
    "Mammouth": {"always-loaded": 686262, "entry-file": 23858, "harness-roster": 662404, "orchestrator": 74694},
    "Opencode": {"always-loaded": 700682, "entry-file": 23922, "harness-roster": 676760, "orchestrator": 89928},
    "ZCode": {"always-loaded": 688878, "entry-file": 24760, "harness-roster": 664118, "orchestrator": 74965},
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
# Re-pinned in Task 30 (2e.4) together with ``_IST_FULL``: the `agent-meta-manager`
# section ``## 10c. Optimizer-Vorschläge anwenden (Advisory Mode)`` adds ~2.3 KB
# to every provider roster (2,346 B in the Claude render, measured), and the pins
# left by the Phase-2 tasks 2e.2/2e.3 (registration of ``meta-optimizer``) were
# stale at HEAD (the gate was already red before this task, e.g. Claude/harness-roster
# 534,875 B vs. ceiling 532,390 B). Measured values, not extrapolated.
# The polish round of Task 30 (2e.4) adds the §13 reference to the §10c "No manual
# edit" rule: +17 B on every provider roster and on the always-loaded set.
#
# ABSORBED DELTAS OF THIS RE-PIN (measured, not extrapolated — HEAD pin -> measured Ist).
# Complete for this profile as well: every artifact with a non-zero delta is named
# below. A later re-pin must nevertheless re-measure EVERY artifact — this list
# documents THIS re-pin, it is not a maintenance promise.
#   * harness-roster (the `meta-optimizer` registration + the new §10c section):
#     Claude 528,294 -> 537,222 (+8,928), Codex 522,159 -> 531,078 (+8,919),
#     KimiCode 529,039 -> 537,997 (+8,958), Mammouth 525,127 -> 534,094 (+8,967),
#     Opencode 524,707 -> 533,661 (+8,954), ZCode 526,417 -> 535,333 (+8,916).
#   * always-loaded: Claude +8,841, Codex +2,698, Continue -50, Copilot -29,
#     Gemini -96, KimiCode +2,737, Mammouth +2,746, Opencode +2,732, ZCode +2,675.
#   * orchestrator: Continue 31,836 -> 31,991 (+155), Copilot 31,710 -> 31,865 (+155),
#     Gemini 32,584 -> 32,739 (+155) — the `meta-optimizer` routing rows;
#     Claude 32,450 -> 31,551 (-899), Codex 31,967 -> 31,067 (-900),
#     KimiCode 33,159 -> 32,277 (-882), Mammouth 31,755 -> 30,856 (-899),
#     Opencode 32,112 -> 31,213 (-899), ZCode 31,981 -> 31,082 (-899) — pre-existing
#     compact-profile drift (the compact orchestrator is the slimmed one), not a
#     Task-30 effect.
#   * entry-file: Codex/KimiCode/Mammouth/Opencode/ZCode -6,221..-6,241 B each (the
#     compact entry file no longer embeds the provider agent table), Continue
#     374 -> 358 (-16), Copilot 9,468 -> 9,457 (-11), Gemini 10,108 -> 10,012 (-96),
#     Claude 2,530 -> 2,461 (-69).
#   * rules: Claude 17,286 -> 17,268 (-18), Continue 20,174 -> 20,140 (-34),
#     Copilot 19,954 -> 19,936 (-18); Gemini writes no rules artifact in `compact`.
# Re-pinned after Task 31 (2e.5) for the orchestrator ONLY.
#
# ABSORBED DELTAS OF THIS RE-PIN (measured, not extrapolated — old Ist -> new Ist).
# Task 31 (2e.5, IC-27/AC-90): mandatory orchestrator preview gate §3a adds exactly
# +1258 B to the compact orchestrator on every provider (old Ist -> new Ist:
# Claude 31551->32809, Codex 31067->32325, Continue 31991->33249,
# Copilot 31865->33123, Gemini 32739->33997, KimiCode 32277->33535,
# Mammouth 30856->32114, Opencode 31213->32471, ZCode 31082->32340).
# No other compact artifact changes: entry-file and rules are unchanged. The
# orchestrator is part of `harness-roster` (all agent files) and hence of
# `always-loaded`, so those two aggregates also measure +1258 B for Claude, Codex,
# KimiCode, Mammouth, Opencode and ZCode just above; their pins stay unchanged on
# purpose because the ceilings' tolerance absorbs the delta.
# AC-26 size TARGETS are unchanged and remain ESTIMATE data / unmet (opt-in,
# unverified). Re-pinned from measured Ist, not extrapolated.
# RE-PIN (literature evidence gates, review round 2): eight new review roles registered (roster +85 KB, orchestrator +5.9 KB, agent-table rows +864 B)
# Absorbed deltas of this re-pin (measured, not extrapolated):
#   * Claude/always-loaded: 556951 -> 638601 (+81650)
#   * Claude/harness-roster: 537222 -> 618872 (+81650)
#   * Claude/orchestrator: 32809 -> 34031 (+1222)
#   * Codex/always-loaded: 534491 -> 615200 (+80709)
#   * Codex/harness-roster: 531078 -> 611787 (+80709)
#   * Codex/orchestrator: 32325 -> 33547 (+1222)
#   * Continue/orchestrator: 33249 -> 34621 (+1372)
#   * Copilot/always-loaded: 29393 -> 30823 (+1430)
#   * Copilot/entry-file: 9457 -> 10887 (+1430)
#   * Copilot/orchestrator: 33123 -> 34495 (+1372)
#   * Gemini/always-loaded: 10012 -> 10948 (+936)
#   * Gemini/entry-file: 10012 -> 10948 (+936)
#   * Gemini/orchestrator: 33997 -> 35369 (+1372)
#   * KimiCode/always-loaded: 541420 -> 623340 (+81920)
#   * KimiCode/harness-roster: 537997 -> 619917 (+81920)
#   * KimiCode/orchestrator: 33535 -> 34923 (+1388)
#   * Mammouth/always-loaded: 537515 -> 618639 (+81124)
#   * Mammouth/harness-roster: 534094 -> 615218 (+81124)
#   * Mammouth/orchestrator: 32114 -> 33336 (+1222)
#   * Opencode/always-loaded: 537142 -> 618177 (+81035)
#   * Opencode/harness-roster: 533661 -> 614696 (+81035)
#   * Opencode/orchestrator: 32471 -> 33692 (+1221)
#   * ZCode/always-loaded: 539659 -> 621213 (+81554)
#   * ZCode/harness-roster: 535333 -> 616887 (+81554)
#   * ZCode/orchestrator: 32340 -> 33562 (+1222)
# RE-PIN (literature round 2 follow-up, fixes A-F, 2026-10-26): measured, not extrapolated.
# The compact orchestrator carries no agent table, so A (name-only exclusion) is 0 B here;
# the only compact deltas are C/D role text plus the pre-existing 17 B tmp-sink drift.
# Absorbed deltas (old pin -> measured Ist):
#   * harness-roster, six roster providers: -143 B each (Claude 618872 -> 618729,
#     Codex 611787 -> 611644, KimiCode 619917 -> 619774, Mammouth 615218 -> 615075,
#     Opencode 614696 -> 614553, ZCode 616887 -> 616744) = -126 role text -17 pre-existing.
#   * always-loaded: the same -143 B for those six (Claude 638601 -> 638458,
#     Codex 615200 -> 615057, KimiCode 623340 -> 623197, Mammouth 618639 -> 618496,
#     Opencode 618177 -> 618034, ZCode 621213 -> 621070).
#   * entry-file, rules and orchestrator: unchanged on every provider (0 B).
# RE-PIN (literature evidence gates, review round 2): one evidence-gate rule per role in eight role templates (+7,228 B roster, +1,258 B orchestrator)
# Absorbed deltas of this re-pin (measured, not extrapolated):
#   * Claude/always-loaded: 556951 -> 564179 (+7228)
#   * Claude/harness-roster: 537222 -> 544450 (+7228)
#   * Codex/always-loaded: 534491 -> 541719 (+7228)
#   * Codex/harness-roster: 531078 -> 538306 (+7228)
#   * KimiCode/always-loaded: 541420 -> 548648 (+7228)
#   * KimiCode/harness-roster: 537997 -> 545225 (+7228)
#   * Mammouth/always-loaded: 537515 -> 544743 (+7228)
#   * Mammouth/harness-roster: 534094 -> 541322 (+7228)
#   * Opencode/always-loaded: 537142 -> 544386 (+7244)
#   * Opencode/harness-roster: 533661 -> 540905 (+7244)
#   * ZCode/always-loaded: 539659 -> 546887 (+7228)
#   * ZCode/harness-roster: 535333 -> 542561 (+7228)
# RE-PIN (merge of origin/main, tmp-sink injection; 2026-10-25) — measured, not
# extrapolated. Same cause as the `full` re-pin above; non-zero deltas only:
#   * harness-roster: Claude 544450 -> 544434 (-16), Codex 538306 -> 538290 (-16),
#     KimiCode 545225 -> 545209 (-16), Mammouth 541322 -> 541306 (-16),
#     Opencode 540905 -> 540888 (-17), ZCode 542561 -> 542545 (-16).
#   * always-loaded: Claude 564179 -> 564163 (-16), Codex 541719 -> 541703 (-16),
#     KimiCode 548648 -> 548632 (-16), Mammouth 544743 -> 544727 (-16),
#     Opencode 544386 -> 544369 (-17), ZCode 546887 -> 546871 (-16).
#   * orchestrator: Opencode 32471 -> 32470 (-1). Every other artifact unchanged.
# MERGE RE-PIN (main bb92039f / #1013 into the literature-round-2 branch / #1015,
# 2026-10-26): measured on the merged tree, not merged arithmetically. Against the main
# pin the merged compact tree absorbs #1015's roles and A-F: roster/always-loaded
# Claude +80,266 (544,434 -> 624,700), Codex +79,325, KimiCode +80,536,
# Mammouth +79,740, Opencode +79,636, ZCode +80,170; orchestrator +1,222 (most
# providers; +1,372 Continue/Copilot/Gemini, +1,388 KimiCode); Copilot entry-file
# +1,430, Gemini entry-file +936; all other artifacts unchanged.
# Against the branch pin the merged tree adds exactly #1013's evidence gates: +5,971 B
# roster/always-loaded on the six roster providers, nothing else changes.
_IST_COMPACT: Dict[str, Dict[str, int]] = {
    "Claude": {"always-loaded": 644429, "entry-file": 2461, "harness-roster": 624700, "orchestrator": 34031, "rules": 17268},
    "Codex": {"always-loaded": 621028, "entry-file": 3413, "harness-roster": 617615, "orchestrator": 33547},
    "Continue": {"always-loaded": 20498, "entry-file": 358, "orchestrator": 34621, "rules": 20140},
    "Copilot": {"always-loaded": 30823, "entry-file": 10887, "orchestrator": 34495, "rules": 19936},
    "Gemini": {"always-loaded": 10948, "entry-file": 10948, "orchestrator": 35369},
    "KimiCode": {"always-loaded": 629168, "entry-file": 3423, "harness-roster": 625745, "orchestrator": 34923},
    "Mammouth": {"always-loaded": 624467, "entry-file": 3421, "harness-roster": 621046, "orchestrator": 33336},
    "Opencode": {"always-loaded": 624005, "entry-file": 3481, "harness-roster": 620524, "orchestrator": 33692},
    "ZCode": {"always-loaded": 627041, "entry-file": 4326, "harness-roster": 622715, "orchestrator": 33562},
}

COMPACT_BUDGET_CEILINGS: Dict[str, Dict[str, int]] = {
    provider: {artifact: _ceiling(size) for artifact, size in artifacts.items()}
    for provider, artifacts in _IST_COMPACT.items()
}

# The AGENTS.md providers share one context file; measured in a single project
# with all of them active (`compact`).
_AGENTS_MD_PROVIDERS = ("Codex", "Gemini", "KimiCode", "Mammouth", "Opencode", "ZCode")
# MERGE RE-PIN (2026-10-26): measured 12,193 B on the merged tree; the branch value
# already carried #1015 + fix A, and #1013's evidence gates are role-body text that
# does not enter this shared entry file. Main's 11,257 B predates the #1015 roles.
_IST_COMPACT_MULTI_AGENTS_MD = 12193

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
        paths = resolve_tmp_paths(root / provider, {})
        cr.render_into_work_dir(REPO_ROOT, config, work, profile="compact", paths=paths)
        works[provider] = work
        report.update(cr.measure_artifacts(work, [provider], mappings))
    return report, mappings, works


@pytest.fixture(scope="module")
def measured_compact_multi(tmp_path_factory):
    root = tmp_path_factory.mktemp("budgets-compact-multi")
    mappings = _matrix_mappings()
    config = _matrix_config(root, "multi", _AGENTS_MD_PROVIDERS)
    work = root / "work"
    paths = resolve_tmp_paths(root / "multi", {})
    cr.render_into_work_dir(REPO_ROOT, config, work, profile="compact", paths=paths)
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
