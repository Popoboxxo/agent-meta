"""Contract-label language-invariance tests for agents/1-generic (issue #541).

Issue #541: refactoring-specialist answered with localized protocol markers
("STATUS: erledigt" / "ERGEBNIS:") although the protocol tokens must stay
literal English regardless of the response language. Fix: a hard anchor in
the template's <output_contract> plus this fleet-wide structure check.

Detection rule (empirical, defined per the issue #541 task):

A template in agents/1-generic/*.md has a *contract section* if either
  * it contains an ``<output_contract>`` block, or
  * it contains a literal line starting with ``STATUS:`` (contract line).

Every contract-section template MUST contain the three literal English
protocol markers ``STATUS:``, ``RESULT:`` and ``ARTIFACTS:``. Marker
matching is word-boundary anchored: the marker must appear as a standalone
label, so ``NEW_ARTIFACTS:`` does NOT satisfy the ``ARTIFACTS:`` marker
(it is a different label). Localization of the marker itself is a protocol
violation; only the value after each colon may follow the response language.

Issue #528/#552 closure: the contract-less templates from #528 and all
deviant contract sections from #552 (classes A–F) have been brought to full
marker compliance. _CONTRACT_EXCEPTIONS below is therefore empty; the
registry stays in place as a ratchet — newly added deviant templates fail
this test until consciously exempted. Remaining contract-less files are the
helper docs (_README.md, _wf-orchestrator-reference.md), consciously exempt
per issue #528 (no required frontmatter fields, not worker roles).
"""

import re
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
AGENTS_1_GENERIC = _REPO_ROOT / "agents" / "1-generic"

REQUIRED_MARKERS = ("STATUS:", "RESULT:", "ARTIFACTS:")

# Issue #541 regression target — must stay covered by the contract rule.
REGRESSION_TARGET = "refactoring-specialist.md"

# P1-contract fleet from docs/concepts/planned/review-agent-fleet.md — the
# original "contract complete" cohort; must never regress into exceptions.
FLEET_P1_ROLES = (
    "frontend-reviewer.md",
    "backend-reviewer.md",
    "database-reviewer.md",
    "ui-reviewer.md",
    "security-auditor.md",
)

# --- Exception registry (ratchet) ------------------------------------------
# Issue #552/#528 closure (2026-09-06): every previously listed deviation
# (classes A–F, 34 templates) was brought to full STATUS/RESULT/ARTIFACTS
# marker compliance; all entries were consciously removed. The empty
# registry is the ratchet baseline: any template that gains a contract
# section without all three markers now fails
# test_contract_templates_contain_all_three_protocol_markers until it is
# either fixed or consciously registered here with its deviation reason.

# Class A — <output_contract> defines a non-IResult structured report
#           envelope without any STATUS contract line (different format,
#           not an incomplete IResult contract):
_CLASS_A_NO_STATUS_ENVELOPE: dict[str, str] = {}

# Class B — SE-cascade roles: STATUS contract line present but no
#           RESULT/ARTIFACTS. SE-cascade roles are a deliberate deviation
#           zone (see .claude/skills/conventions/SKILL.md, Audit #412):
_CLASS_B_SE_CASCADE: dict[str, str] = {}

# Class C — STATUS contract line present, but domain fields replace the
#           RESULT and ARTIFACTS markers entirely:
_CLASS_C_DOMAIN_FIELDS: dict[str, str] = {}

# Class D — STATUS and ARTIFACTS present, RESULT replaced by a domain
#           verdict/summary field:
_CLASS_D_NO_RESULT: dict[str, str] = {}

# Class E — STATUS and RESULT present, ARTIFACTS missing:
_CLASS_E_NO_ARTIFACTS: dict[str, str] = {}

# Class F — embedded marker variant: NEW_ARTIFACTS: is a different label
#           and does not satisfy the bare ARTIFACTS: marker (plus RESULT
#           missing):
_CLASS_F_EMBEDDED_VARIANT: dict[str, str] = {}

_CONTRACT_EXCEPTIONS: dict[str, str] = {
    **_CLASS_A_NO_STATUS_ENVELOPE,
    **_CLASS_B_SE_CASCADE,
    **_CLASS_C_DOMAIN_FIELDS,
    **_CLASS_D_NO_RESULT,
    **_CLASS_E_NO_ARTIFACTS,
    **_CLASS_F_EMBEDDED_VARIANT,
}


def _template_text(name: str) -> str:
    return (AGENTS_1_GENERIC / name).read_text(encoding="utf-8")


def _has_contract_section(text: str) -> bool:
    """Empirical detection rule documented in the module docstring."""
    return "<output_contract>" in text or bool(re.search(r"^STATUS:", text, re.M))


def _missing_markers(text: str) -> list[str]:
    """Markers must appear as standalone labels (word-boundary anchored)."""
    return [m for m in REQUIRED_MARKERS if not re.search(rf"\b{re.escape(m)}", text)]


def _contract_scope() -> dict[str, str]:
    """All templates with a contract section -> their content."""
    return {
        p.name: p.read_text(encoding="utf-8")
        for p in sorted(AGENTS_1_GENERIC.glob("*.md"))
        if _has_contract_section(p.read_text(encoding="utf-8"))
    }


# --- issue #541 regression ------------------------------------------------


def test_refactoring_specialist_has_language_invariant_markers():
    text = _template_text(REGRESSION_TARGET)
    assert _has_contract_section(text), "regression target lost its contract section"
    missing = _missing_markers(text)
    assert not missing, f"{REGRESSION_TARGET}: missing markers {missing}"
    # Hard anchor added by #541: markers are language-invariant, and the
    # localized variants reported in the issue are named as forbidden.
    assert "Marker language-invariance (mandatory)" in text, (
        "hard anchor against marker localization missing"
    )
    assert "STATUS: erledigt" in text and "ERGEBNIS:" in text, (
        "forbidden localized variants no longer named as examples in the anchor"
    )


# --- fleet-wide contract-label structure ----------------------------------


def test_contract_scope_is_not_empty_and_covers_fleet():
    scope = _contract_scope()
    # Vacuum guard: if this floor ever fails, the detection rule broke or
    # the fleet lost its contracts wholesale -- do not just lower it.
    assert len(scope) >= 20, f"contract scope collapsed to {len(scope)} files"
    assert REGRESSION_TARGET in scope
    for role in FLEET_P1_ROLES:
        assert role in scope, f"{role}: P1 fleet role lost its contract section"


def test_contract_templates_contain_all_three_protocol_markers():
    scope = _contract_scope()
    failures = []
    for name, text in scope.items():
        if name in _CONTRACT_EXCEPTIONS:
            continue
        missing = _missing_markers(text)
        if missing:
            failures.append(f"{name}: missing {missing}")
    assert not failures, (
        "contract-section templates must contain literal English protocol "
        "markers "
        + ", ".join(REQUIRED_MARKERS)
        + " (localize values, never markers) -- offenders: "
        + "; ".join(failures)
        + " -- if a deviation is deliberate, document it in "
        "_CONTRACT_EXCEPTIONS and file a follow-up"
    )


def test_exception_registry_entries_are_still_deviating():
    """Ratchet hygiene: no stale entries.

    When a template gains all three markers, its exception entry must be
    removed consciously -- the registry must only ever contain real
    deviations (follow-up candidates).
    """
    scope = _contract_scope()
    stale = [
        name
        for name in _CONTRACT_EXCEPTIONS
        if name not in scope or not _missing_markers(scope[name])
    ]
    assert not stale, (
        f"stale exception entries (template now compliant or out of scope, "
        f"remove from _CONTRACT_EXCEPTIONS): {stale}"
    )


def test_exception_registry_files_exist():
    orphans = [
        name for name in _CONTRACT_EXCEPTIONS
        if not (AGENTS_1_GENERIC / name).exists()
    ]
    assert not orphans, f"exception entries point to deleted templates: {orphans}"
