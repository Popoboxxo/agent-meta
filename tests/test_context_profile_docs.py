"""Docs guardrail for the opt-in context profile (2a.7, AC-29 and AC-86).

``context-profile: compact`` ships as an *opt-in, unverified* feature: the
role-routing eval that would evidence AC-25 (2f.2) has not run because its
``full`` baseline (AC-02) was skipped by the user (0f.3, ``SKIPPED-BY-USER``);
the deterministic parts are asserted hermetically, the verification claim is
planned for package 2f. The documentation must name that status *with* the
reason (missing baseline/AC-02, proof planned in 2f), tie it to the
``context-profile.unverified`` INFO and never claim verification, validation
or a recommendation (IC-36 no. 3).

These tests are intentionally source assertions, mirroring
``tests/test_runtime_gate_docs.py``: docs that over-promise are a defect, so
the wording is pinned here.

Run: python -m pytest tests/test_context_profile_docs.py -v
"""

import re
from pathlib import Path

from tests.changelog_sections import latest_changelog_section

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CLI_REFERENCE = _REPO_ROOT / "docs" / "api" / "cli-reference.md"
_CHANGELOG = _REPO_ROOT / "CHANGELOG.md"
_README = _REPO_ROOT / "README.md"


def _normalized(text: str) -> str:
    """Lower-case + collapse whitespace so phrases split across wrapped lines
    still match."""
    return " ".join(text.split()).lower()


def _cli_reference_text() -> str:
    return _CLI_REFERENCE.read_text(encoding="utf-8")


def _context_profile_section() -> str:
    """The level-2 cli-reference section whose heading names ``context-profile``."""
    text = _cli_reference_text()
    heading = re.search(r"(?m)^## .*context-profile.*$", text)
    assert heading, (
        "docs/api/cli-reference.md must carry a level-2 'context-profile' "
        "section (2a.7): the opt-in profile and its unverified status need a "
        "documented home."
    )
    rest = text[heading.end():]
    next_heading = re.search(r"(?m)^## ", rest)
    return rest[: next_heading.start()] if next_heading else rest


def _unreleased_section() -> str:
    """The current changelog block: ``[Unreleased]`` plus the next release."""
    text = _CHANGELOG.read_text(encoding="utf-8")
    assert "## [Unreleased]" in text, (
        "CHANGELOG.md must keep an [Unreleased] section."
    )
    return latest_changelog_section(text)


def test_cli_reference_documents_opt_in_unverified_with_reason():
    lowered = _normalized(_context_profile_section())
    assert "opt-in" in lowered, (
        "The context-profile section must name the opt-in character of "
        "`context-profile: compact`."
    )
    assert "unverified" in lowered, (
        "The context-profile section must state the unverified status "
        "(IC-36 no. 3 / AC-86)."
    )
    assert "ac-02" in lowered and "baseline" in lowered, (
        "The section must give the reason: the `full` baseline (AC-02) was "
        "skipped by the user (0f.3)."
    )
    assert "2f" in lowered, (
        "The section must name the planned proof (package 2f) so the status "
        "stays traceable."
    )


def test_cli_reference_documents_keys_and_precedence():
    section = _context_profile_section()
    lowered = _normalized(section)
    assert "context-profile" in lowered, (
        "The section must document the top-level `context-profile` key."
    )
    assert "provider-overrides" in lowered, (
        "The section must document the per-provider override "
        "`provider-overrides.<Provider>.context-profile`."
    )
    assert "full" in lowered and "compact" in lowered, (
        "The section must name both profile values (`full`, `compact`)."
    )
    assert "precedence" in lowered, (
        "The section must document the resolution precedence."
    )
    assert "context_file.mode" in section, (
        "The section must name the explicit `context_file.mode` sub-setting as "
        "the highest-precedence input."
    )


def test_cli_reference_names_the_gate_messages():
    section = _context_profile_section()
    assert "context-profile.unverified" in section, (
        "The section must name the INFO `context-profile.unverified` that a "
        "`compact` sync writes to sync.log."
    )
    assert "context-profile.shared-file-downgrade" in section, (
        "The section must name the WARN `context-profile.shared-file-downgrade` "
        "of the shared-file downgrade (ADR-5)."
    )


def test_cli_reference_never_claims_verification():
    lowered = _normalized(_context_profile_section())
    without_unverified = lowered.replace("unverified", "")
    assert "verified" not in without_unverified, (
        "The context-profile section must not claim 'verified' "
        "(IC-36 no. 3): `compact` stays unverified until 2f.3."
    )
    assert "validated" not in without_unverified, (
        "The context-profile section must not claim 'validated'."
    )
    assert "recommended" not in without_unverified, (
        "The context-profile section must not recommend `compact`."
    )


def test_changelog_unreleased_documents_the_opt_in_profile():
    lowered = _normalized(_unreleased_section())
    assert "context-profile" in lowered, (
        "CHANGELOG.md [Unreleased] must document the opt-in context profile "
        "(2a.7)."
    )
    assert "unverified" in lowered, (
        "The CHANGELOG entry must carry the unverified status (AC-86)."
    )
    assert "ac-25" in lowered or "2f" in lowered, (
        "The CHANGELOG entry must reference the planned AC-25 proof (package "
        "2f)."
    )


_INVENTORY = _REPO_ROOT / "docs" / "guides" / "context-block-inventory.md"

# The four generic rules whose REFERENCE portion leaves the managed block for
# the skills channel in the `compact` opt-in (IC-07; 2b.4 implements, 2b.6
# documents).
_IC07_REFERENCE_RULES = (
    "a2a-delegation-gates",
    "branch-guard",
    "submodule-protection",
    "security-paved-roads",
)
# Of those, the ones with a removable REFERENCE portion written as
# ``<skills_dir>/<rule>/SKILL.md``; ``submodule-protection`` has no H2 section,
# so its whole body stays embedded and no skill is written (2b.4).
_IC07_SKILLS_CHANNEL_RULES = (
    "a2a-delegation-gates",
    "branch-guard",
    "security-paved-roads",
)


def _inventory_text() -> str:
    return _INVENTORY.read_text(encoding="utf-8")


def _ic07_classification_section() -> str:
    """The inventory section that classifies the IC-07 REFERENCE rules."""
    text = _inventory_text()
    heading = re.search(r"(?m)^#{2,4} .*IC-07.*$", text)
    assert heading, (
        "docs/guides/context-block-inventory.md must carry an IC-07 "
        "classification section (2b.6): the REFERENCE parts moved to the skills "
        "channel need a documented home."
    )
    rest = text[heading.end():]
    next_heading = re.search(r"(?m)^#{2,4} ", rest)
    return rest[: next_heading.start()] if next_heading else rest


def test_inventory_classifies_the_ic07_reference_rules():
    section = _normalized(_ic07_classification_section())
    for rule in _IC07_REFERENCE_RULES:
        assert rule in section, (
            f"docs/guides/context-block-inventory.md must classify the "
            f"REFERENCE rule `{rule}` (IC-07, 2b.6)."
        )
    assert "instruktion" in section and "embedded" in section, (
        "The IC-07 table must state that the INSTRUCTION cores stay embedded."
    )
    assert "reference" in section, (
        "The IC-07 table must classify the removable REFERENCE parts."
    )
    for rule in _IC07_SKILLS_CHANNEL_RULES:
        assert f"{rule}/skill.md" in section, (
            f"The IC-07 table must route the REFERENCE part of `{rule}` to the "
            f"skills channel (`<skills_dir>/{rule}/SKILL.md`)."
        )


def test_inventory_keeps_compact_opt_in_and_unverified():
    lowered = _normalized(_ic07_classification_section())
    assert "opt-in" in lowered, (
        "The IC-07 section must keep `compact` opt-in (IC-36 no. 3)."
    )
    assert "unverified" in lowered or "unverifiziert" in lowered, (
        "The IC-07 section must carry the unverified status (AC-86)."
    )
    unwrapped = lowered.replace("unverified", "").replace("unverifiziert", "")
    for claim in ("verified", "validated", "recommended",
                  "verifiziert", "validiert", "empfohlen"):
        assert claim not in unwrapped, (
            f"The IC-07 section must not claim `{claim}` (IC-36 no. 3): "
            "`compact` stays opt-in and unverified."
        )


def test_changelog_documents_the_compact_render_package():
    lowered = _normalized(_unreleased_section())
    assert "package 2b" in lowered, (
        "CHANGELOG.md [Unreleased] must record package 2b (the compact render "
        "densification)."
    )
    assert "compact" in lowered and "skills" in lowered, (
        "The 2b entry must name `compact` and the REFERENCE sections delivered "
        "through the skills channel."
    )


# --- 2c.4: the published `compact` profile (cli-reference, README, CHANGELOG) ---


def _readme_text() -> str:
    return _README.read_text(encoding="utf-8")


def _readme_profile_section() -> str:
    """The level-2 README section whose heading names the context profile."""
    text = _readme_text()
    heading = re.search(r"(?m)^## .*[Cc]ontext [Pp]rofiles?.*$", text)
    assert heading, (
        "README.md must carry a level-2 'Context Profiles' section (2c.4): the "
        "opt-in profile and its unverified status need an English home."
    )
    rest = text[heading.end():]
    next_heading = re.search(r"(?m)^## ", rest)
    return rest[: next_heading.start()] if next_heading else rest


def _changelog_bullet(marker: str) -> str:
    """The [Unreleased] bullet (plus its continuation lines) containing *marker*."""
    lines = _unreleased_section().splitlines()
    index = next((i for i, line in enumerate(lines) if marker in line), None)
    assert index is not None, (
        f"CHANGELOG.md [Unreleased] must carry a bullet naming '{marker}' (2c.4)."
    )
    block = [lines[index]]
    for line in lines[index + 1:]:
        if line.startswith("- ") or line.startswith("### "):
            break
        block.append(line)
    return "\n".join(block)


def test_cli_reference_lifts_profile_out_of_reserved_status():
    lowered = _normalized(_cli_reference_text())
    assert "reserved for phase 2" not in lowered, (
        "docs/api/cli-reference.md must drop the stale 'reserved for Phase 2' "
        "wording for `--profile compact|both` (2c.4): the flag really renders "
        "the profile."
    )
    assert "work directory" in lowered, (
        "cli-reference must state that `--profile compact|both` renders into a "
        "work directory below the tmp-sink."
    )
    assert "delta" in lowered, (
        "cli-reference must state that `--profile both` reports the full/compact "
        "delta."
    )
    assert "never modified" in lowered, (
        "cli-reference must state that the project config on disk is never "
        "modified (the injected key lands in the work-dir copy only)."
    )


def test_cli_reference_labels_ac26_targets_as_estimates():
    section = _context_profile_section()
    lowered = _normalized(section)
    assert "estimate" in lowered, (
        "The context-profile section must label the AC-26 size targets as "
        "ESTIMATES (Spec section 11), not measurements."
    )
    assert "not measurements" in lowered, (
        "The section must state explicitly that the targets are estimates, not "
        "measurements."
    )
    assert "--context-report" in section, (
        "The section must point at `--context-report` as the source of the "
        "measured values."
    )
    assert "ceiling" in lowered, (
        "The section must state that the measured values are pinned as "
        "regression ceilings."
    )
    assert "not claim" in lowered or "no claim" in lowered, (
        "The section must state that it does not claim the targets are met."
    )


def test_readme_documents_opt_in_unverified_with_reason_and_estimate():
    lowered = _normalized(_readme_profile_section())
    assert "opt-in" in lowered, (
        "The README profile section must name the opt-in character of "
        "`context-profile: compact`."
    )
    assert "unverified" in lowered, (
        "The README profile section must state the unverified status (IC-36 "
        "no. 3 / AC-86)."
    )
    assert "ac-02" in lowered and "baseline" in lowered, (
        "The README section must give the reason: the `full` baseline (AC-02) "
        "was skipped by the user (0f.3)."
    )
    assert "2f" in lowered, (
        "The README section must name the planned proof (package 2f)."
    )
    assert "estimate" in lowered and "ac-26" in lowered, (
        "The README section must label the AC-26 targets as estimates."
    )


def test_readme_never_claims_verification():
    lowered = _normalized(_readme_profile_section())
    without_unverified = lowered.replace("unverified", "")
    for claim in ("verified", "validated", "recommended"):
        assert claim not in without_unverified, (
            f"README.md must not claim `{claim}` for `compact` (IC-36 no. 3): "
            "the profile stays opt-in and unverified."
        )


def test_changelog_documents_the_compact_anchors_report_package():
    lowered = _normalized(_unreleased_section())
    assert "package 2c" in lowered, (
        "CHANGELOG.md [Unreleased] must record package 2c (anchor registry, "
        "budgets/report, provider matrix)."
    )
    assert "anchor" in lowered and "provider matrix" in lowered, (
        "The 2c entry must name the anchor registry and the provider matrix."
    )
    assert "estimate" in lowered, (
        "The 2c entry must label the AC-26 targets as estimates (Spec section "
        "11)."
    )


def test_changelog_2c_entry_keeps_compact_opt_in_and_unverified():
    lowered = _normalized(_changelog_bullet("package 2c"))
    assert "opt-in" in lowered and "unverified" in lowered, (
        "The 2c entry must keep `compact` opt-in and unverified (IC-36)."
    )
    without_unverified = lowered.replace("unverified", "")
    for claim in ("verified", "validated", "recommended"):
        assert claim not in without_unverified, (
            f"The 2c entry must not claim `{claim}` (IC-36 no. 3)."
        )
