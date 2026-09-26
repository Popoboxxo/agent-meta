"""Routing-pattern overlap detector (#779 IT-7).

SPEC ``dynamic-routing-template-slimming`` AC A5 / risk R5 (Task 4): keywords or
examples shared by more than one role are ambiguity candidates. The detector is
GREEN against the current real config because every existing cross-role token is
covered by an explicit, documented exception set below — an UNCONTROLLED overlap
fails the test and prints the full overlap map.

Policy (deliberate, per IT-7): the detector does not ignore whole roles; it only
excuses individual tokens with a named reason. New overlaps (for example from the
freshly added ``openscad-developer`` patterns, R5) must be added explicitly here
with a reason, or the test fails.
"""
from __future__ import annotations

import json
from collections import defaultdict
from pathlib import Path

from scripts.lib.roles import load_roles_config

REPO_ROOT = Path(__file__).resolve().parents[1]

# Deliberate, documented cross-role keyword overlaps.
# Each entry excuses exactly one normalized token for exactly the listed roles;
# the test also fails when an exception is stale (no longer overlapping) so the
# exception set cannot silently weaken detection.
KNOWN_KEYWORD_OVERLAPS: dict[str, frozenset[str]] = {
    # accessibility-specialist and e2e-tester both legitimately gate on the
    # same WCAG vocabulary; the audit surface differs (static a11y vs. E2E).
    "a11y": frozenset({"accessibility-specialist", "e2e-tester"}),
    "accessibility": frozenset({"accessibility-specialist", "e2e-tester"}),
    # ideation explores architecture up-front; senior-developer decides it.
    "architektur": frozenset({"ideation", "senior-developer"}),
    # code-reviewer audits code; security-auditor audits security posture.
    # Candidate for sharpening (IT-3 "audit" -> "security audit" vs. "code review").
    "audit": frozenset({"code-reviewer", "security-auditor"}),
    # ideation and ui-ux-designer both own the generic word "Design".
    "design": frozenset({"ideation", "ui-ux-designer"}),
    # incident-responder and sre-engineer share the post-incident ritual.
    "post-mortem": frozenset({"incident-responder", "sre-engineer"}),
    # developer refactors; refactoring-specialist owns large transformations.
    "refactoring": frozenset({"developer", "refactoring-specialist"}),
    # database-engineer and knowledge-curator use "schema" in different domains.
    "schema": frozenset({"database-engineer", "knowledge-curator"}),
    # se-developer and se-junior-developer split SE work by difficulty.
    "se leaf": frozenset({"se-developer", "se-junior-developer"}),
}

# Example overlaps are currently none. The freshly added openscad-developer
# patterns (SPEC R5) were checked against every existing role and are deliberately
# specific (OpenSCAD / 3D-Modell / CAD-Modell / ...), so they introduce no
# overlap — no openscad-developer exception is required. Any future collision
# MUST be added here with a reason instead of weakening the detector.
KNOWN_EXAMPLE_OVERLAPS: dict[str, frozenset[str]] = {}


def _normalize(token: object) -> str:
    return str(token).strip().casefold()


def _collect_overlaps(tokens_by_role: dict[str, list]) -> dict[str, set[str]]:
    """token → roles for every normalized token owned by >1 role."""
    index: dict[str, set[str]] = defaultdict(set)
    for role, tokens in tokens_by_role.items():
        for token in tokens or []:
            index[_normalize(token)].add(role)
    return {token: roles for token, roles in index.items() if len(roles) > 1}


def _keywords_by_role() -> dict[str, list]:
    return {
        name: (info.get("routing_patterns") or {}).get("keywords") or []
        for name, info in load_roles_config(REPO_ROOT)["roles"].items()
    }


def _examples_by_role() -> dict[str, list]:
    return {
        name: (info.get("routing_patterns") or {}).get("examples") or []
        for name, info in load_roles_config(REPO_ROOT)["roles"].items()
    }


def test_overlap_detector_flags_injected_duplicate_and_normalizes():
    overlaps = _collect_overlaps(
        {
            "role-a": ["Shared Token"],
            "role-b": ["shared token", "unique-b"],
            "role-c": ["unique-c"],
        }
    )
    assert overlaps == {"shared token": {"role-a", "role-b"}}


def test_keyword_overlaps_are_controlled_and_documented():
    overlaps = _collect_overlaps(_keywords_by_role())
    uncontrolled = {
        token: sorted(roles)
        for token, roles in overlaps.items()
        if roles != set(KNOWN_KEYWORD_OVERLAPS.get(token, frozenset()))
    }
    assert not uncontrolled, (
        "Uncontrolled keyword overlap between roles — sharpen the keyword or add "
        "a documented exception in KNOWN_KEYWORD_OVERLAPS.\n"
        f"uncontrolled: {json.dumps(uncontrolled, sort_keys=True, ensure_ascii=False)}\n"
        "full overlap map: "
        f"{json.dumps({t: sorted(r) for t, r in sorted(overlaps.items())}, ensure_ascii=False)}"
    )
    # No stale exceptions: the set must not excuse tokens that no longer overlap.
    stale = sorted(set(KNOWN_KEYWORD_OVERLAPS) - set(overlaps))
    assert not stale, f"stale overlap exceptions: {stale}"


def test_example_overlaps_are_controlled_and_documented():
    overlaps = _collect_overlaps(_examples_by_role())
    uncontrolled = {
        token: sorted(roles)
        for token, roles in overlaps.items()
        if roles != set(KNOWN_EXAMPLE_OVERLAPS.get(token, frozenset()))
    }
    assert not uncontrolled, (
        "Uncontrolled example overlap between roles.\n"
        f"uncontrolled: {json.dumps(uncontrolled, sort_keys=True, ensure_ascii=False)}\n"
        "full overlap map: "
        f"{json.dumps({t: sorted(r) for t, r in sorted(overlaps.items())}, ensure_ascii=False)}"
    )
    stale = sorted(set(KNOWN_EXAMPLE_OVERLAPS) - set(overlaps))
    assert not stale, f"stale overlap exceptions: {stale}"


def test_openscad_developer_patterns_deliberately_introduce_no_overlap():
    """SPEC R5: the freshly added ``openscad-developer`` patterns are checked
    against every other role. They are deliberately domain-specific and unique,
    so no openscad-developer entry is needed in the exception maps above; this
    test pins that deliberate non-collision (an accidental collision would fail
    ``test_keyword_overlaps_are_controlled_and_documented`` first)."""
    roles = load_roles_config(REPO_ROOT)["roles"]
    openscad_tokens = {
        _normalize(t)
        for t in (roles["openscad-developer"].get("routing_patterns") or {}).get("keywords") or []
    }
    assert openscad_tokens, "openscad-developer must keep keyword patterns"

    other_tokens: dict[str, set[str]] = defaultdict(set)
    for name, info in roles.items():
        if name == "openscad-developer":
            continue
        for token in (info.get("routing_patterns") or {}).get("keywords") or []:
            other_tokens[_normalize(token)].add(name)

    collisions = {t: sorted(other_tokens[t]) for t in openscad_tokens if t in other_tokens}
    assert not collisions, (
        "openscad-developer keywords collide with other roles — either sharpen the "
        f"keyword or document the deliberate exception per SPEC R5: {collisions}"
    )

