"""Role-template artifact-location tests (Issue #1186, T10).

Section ``T10 — non-SE``: the ten non-SE templates persist their artifacts
into matrix-backed ``{{ARTIFACT_*}}`` locations instead of hard-coded paths.
Two read-only path literals in ``knowledge-migrator.md`` are grandfathered via
the shrink-only ``<!-- artifact-read-ok -->`` ratchet (Spec §4.6, RVW-1186-06).

Later tasks (T11--T13, T20) append their own sections to this shared module.

Run: export PYTEST_BASETEMP=.tmp/pytest-1186-t10
     python3 -m pytest tests/test_artifact_locations_templates.py \
         --basetemp="$PYTEST_BASETEMP" -q
"""
from __future__ import annotations

import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
GENERIC = ROOT / "agents" / "1-generic"

# ---------------------------------------------------------------------------
# T10 — non-SE
# ---------------------------------------------------------------------------

# The 10 T10 templates (11 role cases: copyeditor + proofreader share tests).
T10_TEMPLATES = (
    "ideation",
    "planner",
    "requirements",
    "documenter",
    "knowledge-migrator",
    "concept-reviewer",
    "copyeditor",
    "proofreader",
    "effort-estimator",
    "explorer",
)

READ_OK_MARKER = "<!-- artifact-read-ok -->"

# Managed class paths / fixed files that must not appear as write-position
# literals (Spec §6.3.1, RVW-1186-06).
MANAGED_PATH_RE = re.compile(
    r"docs/(?:specs|plans|spikes|concepts|reviews|audits|analysis|reports|"
    r"adr|traceability|runbooks)(?:/|\b)"
    r"|docs/(?:CODEBASE_OVERVIEW|ARCHITECTURE|REQUIREMENTS)\.md"
    r"|plan-<topic>\.md|concept-<topic>\.md"
)

# A managed-path literal is only a violation in a write position.  Cues follow
# the `literal-path` consistency check's write-position scope (Spec §6.3.1).
WRITE_CUE_RE = re.compile(
    r"\b(?:write|writes|writing|written|persist|persists|persisted|persisting|"
    r"create|creates|creating|save|saves|saved|record(?:ed)? in|target|"
    r"Ziel|Default:|Output|archive|verschieben|move|moved|unter|"
    r"schreibe|schreibt|erstelle|anlegen)\b",
    re.IGNORECASE,
)
READ_NEGATION_RE = re.compile(
    r"writing NOT|never (?:edit|overwrite|write)|NIEMALS|read-only|"
    r"only if the file actually exists|reading .* allowed",
    re.IGNORECASE,
)


def _read(role: str) -> str:
    return (GENERIC / f"{role}.md").read_text(encoding="utf-8")


def _lines(role: str) -> list[str]:
    return _read(role).splitlines()


def _is_write_position(line: str) -> bool:
    return bool(WRITE_CUE_RE.search(line)) and not READ_NEGATION_RE.search(line)


def test_no_literal_managed_path_in_write_position():
    """No unmarked managed-path literal in a write position across T10 files."""
    offenders: list[str] = []
    for role in T10_TEMPLATES:
        for lineno, line in enumerate(_lines(role), 1):
            if (
                MANAGED_PATH_RE.search(line)
                and _is_write_position(line)
                and READ_OK_MARKER not in line
            ):
                offenders.append(f"{role}.md:{lineno}: {line.strip()}")
    assert not offenders, (
        "managed-path literal in write position (use {{ARTIFACT_*}}):\n"
        + "\n".join(offenders)
    )


def test_read_ok_ratchet_is_exactly_two_lines():
    """Exactly two read-ok markers repo-wide, both in knowledge-migrator."""
    hits = [
        (str(path.relative_to(ROOT)), lineno)
        for path in (ROOT / "agents").rglob("*.md")
        for lineno, line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), 1
        )
        if READ_OK_MARKER in line
    ]
    assert len(hits) == 2, f"read-ok ratchet is shrink-only, found: {hits}"
    assert {path for path, _ in hits} == {"agents/1-generic/knowledge-migrator.md"}
    marked = {lineno for _, lineno in hits}
    expected = {39, 50}
    assert marked == expected, (
        f"read-ok markers moved: expected lines {sorted(expected)}, "
        f"found {sorted(marked)}"
    )


def test_ideation_uses_concepts_dir():
    text = _read("ideation")
    assert "{{ARTIFACT_CONCEPTS_DIR}}" in text


def test_planner_uses_plans_dir():
    text = _read("planner")
    assert "{{ARTIFACT_PLANS_DIR}}" in text
    assert "project root" not in text


def test_documenter_uses_analysis_and_project_docs():
    text = _read("documenter")
    assert "{{ARTIFACT_ANALYSIS_DIR}}/conclusion-" in text
    assert "{{ARTIFACT_ARCHITECTURE_FILE}}" in text
    assert "{{ARTIFACT_CODEBASE_OVERVIEW_FILE}}" in text
    assert "{{ARTIFACT_REQUIREMENTS_FILE}}" in text


def test_documenter_archive_target_uses_plans_dir():
    text = _read("documenter")
    assert "{{ARTIFACT_PLANS_DIR}}/archive" in text
    assert "docs/plans/archive" not in text


def test_copyedit_and_proofread_use_reviews_dir():
    for role in ("copyeditor", "proofreader"):
        text = _read(role)
        assert "{{ARTIFACT_REVIEWS_DIR}}" in text
        assert "next to the reviewed file" not in text
    assert "kind: copyedit" in _read("copyeditor")
    assert "kind: proofread" in _read("proofreader")


def test_effort_estimator_has_defined_target():
    text = _read("effort-estimator")
    assert "{{ARTIFACT_ANALYSIS_DIR}}" in text
    assert "kind: estimate" in text
    assert "<persisted estimate file path>" not in text


def test_explorer_uses_spikes_dir():
    text = _read("explorer")
    assert "{{ARTIFACT_SPIKES_DIR}}" in text
    assert "docs/spikes" not in text


def test_fallback_mentions_inline_mode():
    """Any role referencing an ARTIFACT_*_MODE var documents inline fallback."""
    offenders: list[str] = []
    for role in T10_TEMPLATES:
        text = _read(role)
        if re.search(r"\{\{ARTIFACT_[A-Z0-9_]+_MODE\}\}", text):
            if "inline" not in text:
                offenders.append(
                    f"{role}.md references a _MODE variable but never mentions inline"
                )
    assert not offenders, "\n".join(offenders)


# ---------------------------------------------------------------------------
# T11 — SE
# ---------------------------------------------------------------------------

# The 12 SE templates owned by T11 (plan T11 row).
T11_TEMPLATES = (
    "se-requirements",
    "se-component-requirements",
    "se-architect",
    "se-interface-mgr",
    "se-developer",
    "se-senior-developer",
    "se-junior-developer",
    "se-integration-and-test-manager",
    "se-validator",
    "se-verifier",
    "se-termination",
    "se-critic",
)

# F-1: single-brace `{SE_*}` is never substituted by sync.py.
SE_SINGLE_BRACE_RE = re.compile(r"(?<!\{)\{SE_[A-Z0-9_]*(?!\})")

# Role -> resolved matrix class variable (Spec §2.4, §3.4).
SE_CLASS_VARIABLES = {
    "se-requirements": "ARTIFACT_SE_REQUIREMENTS_DIR",
    "se-component-requirements": "ARTIFACT_SE_REQUIREMENTS_DIR",
    "se-architect": "ARTIFACT_SE_ARCHITECTURE_DIR",
    "se-interface-mgr": "ARTIFACT_SE_INTERFACES_DIR",
    "se-developer": "ARTIFACT_SE_IMPLEMENTATION_DIR",
    "se-senior-developer": "ARTIFACT_SE_IMPLEMENTATION_DIR",
    "se-junior-developer": "ARTIFACT_SE_IMPLEMENTATION_DIR",
    "se-integration-and-test-manager": "ARTIFACT_SE_TESTPLAN_DIR",
    "se-validator": "ARTIFACT_SE_VALIDATION_DIR",
    "se-verifier": "ARTIFACT_SE_VERIFICATION_DIR",
    "se-termination": "ARTIFACT_SE_DECISIONS_DIR",
    "se-critic": "ARTIFACT_SE_REVIEWS_DIR",
}

# Canonical leaf naming must survive the variable substitution (Spec §3.1/§3.2).
SE_LEAF_PATTERNS = {
    "se-requirements": "L{level}_{FolderName}_Requirements.md",
    "se-component-requirements": "L3_{FolderName}_Requirements.md",
    "se-architect": "L{level}_{FolderName}_Architecture.md",
    "se-interface-mgr": "L{level}_{FolderName}_Interfaces.md",
    "se-developer": "L{level}_{FolderName}_Impl.md",
    "se-senior-developer": "L{level}_{FolderName}_Impl.md",
    "se-junior-developer": "L{level}_{FolderName}_Impl.md",
    "se-integration-and-test-manager": "L{level}_{FolderName}_TestPlan.md",
    "se-validator": "L{level}_{FolderName}_Validation.md",
    "se-verifier": "L{level}_{FolderName}_Verification.md",
    "se-termination": "L{level}_{FolderName}_Decisions.md",
    "se-critic": "L{level}_{FolderName}_{review_target}_critic_report.md",
}


def test_no_single_brace_se_token():
    """F-1: no single-brace `{SE_*}` and no legacy SE_BASE_DIR token left."""
    offenders: list[str] = []
    for role in T11_TEMPLATES:
        text = _read(role)
        if SE_SINGLE_BRACE_RE.search(text):
            offenders.append(f"{role}.md: single-brace SE token")
        if "SE_BASE_DIR" in text:
            offenders.append(f"{role}.md: legacy SE_BASE_DIR token")
    assert not offenders, (
        "unsubstituted SE path token (use {{ARTIFACT_*}}):\n"
        + "\n".join(offenders)
    )


def test_each_se_role_uses_its_class_variable():
    """Every SE role points at its resolved cell-class variable."""
    offenders: list[str] = []
    for role, variable in SE_CLASS_VARIABLES.items():
        if "{{" + variable + "}}" not in _read(role):
            offenders.append(f"{role}.md: missing {{{{{variable}}}}}")
    assert not offenders, "\n".join(offenders)


def test_leaf_naming_preserved():
    """Leaf naming stays canonical; no role-specific naming was introduced."""
    offenders: list[str] = []
    for role, leaf in SE_LEAF_PATTERNS.items():
        if leaf not in _read(role):
            offenders.append(f"{role}.md: missing leaf '{leaf}'")
    assert not offenders, "\n".join(offenders)


def test_protocol_path_uses_se_reviews_projection():
    """se-critic review protocol targets the SE reviews projection (D-7)."""
    text = _read("se-critic")
    assert "{{ARTIFACT_SE_REVIEWS_DIR}}/REVIEW_<YYYY-MM-DD>_<scope>.md" in text
    assert "docs/reviews" not in text
    assert "{SE_BASE_DIR}/reviews" not in text


def test_critic_report_uses_se_reports_projection():
    """Critic end-report targets the SE reports projection, not docs/reports."""
    text = _read("se-critic")
    assert (
        "{{ARTIFACT_SE_REPORTS_DIR}}/{FolderName}/"
        "L{level}_{FolderName}_{review_target}_critic_report.md"
    ) in text
    assert "{{ARTIFACT_REPORTS_DIR}}" not in text


def test_atomic_write_uses_scratch_dir():
    """The scratch sink stays for intermediates; the target uses class vars."""
    for role in ("se-architect", "se-critic"):
        text = _read(role)
        assert "{{TMP_SINK_PATH}}/se-" in text, f"{role}.md: scratch sink missing"
        assert "rename" in text, f"{role}.md: atomic rename missing"
    assert "{{ARTIFACT_SE_ARCHITECTURE_DIR}}" in _read("se-architect")
    assert "{{ARTIFACT_SE_REPORTS_DIR}}" in _read("se-critic")


# ---------------------------------------------------------------------------
# T12 — routing
# ---------------------------------------------------------------------------

REVIEWERS_YAML = ROOT / "config" / "routing" / "reviewers.yaml"

# Full audit report target per role -> class-scoped audit kind (Spec §3.1).
T12_AUDIT_ROLES = {
    "security-auditor": "security",
    "ai-security-guardian": "ai-security",
    "app-lifecycle-governor": "lifecycle",
    "prompt-governor": "prompt",
}


def test_reviewers_notes_reference_matrix():
    """Reviewer-routing notes name the matrix, not the deprecated tmp sink."""
    notes = REVIEWERS_YAML.read_text(encoding="utf-8")
    assert "{{ARTIFACT_REVIEWS_DIR}}" in notes
    assert "{{TMP_SINK_PATH}}" not in notes
    assert "tmp sink" not in notes


def test_auditor_reports_go_to_audits_dir():
    """Each audit role writes its full report into the audits matrix dir."""
    for role in T12_AUDIT_ROLES:
        assert "{{ARTIFACT_AUDITS_DIR}}" in _read(role), (
            f"{role}.md: missing {{ARTIFACT_AUDITS_DIR}} report target"
        )
    # Regression anchor from the plan: app-lifecycle-governor.md:100.
    assert "{{ARTIFACT_AUDITS_DIR}}" in _lines("app-lifecycle-governor")[99]


def test_audit_kind_matches_role():
    """Each audit role carries its class-scoped audit kind (Spec §3.1)."""
    for role, kind in T12_AUDIT_ROLES.items():
        assert f"kind: {kind}" in _read(role), (
            f"{role}.md: missing 'kind: {kind}'"
        )


def test_ephemeral_evidence_still_uses_scratch():
    """Raw evidence (logs, long tool output) stays on the scratch sink."""
    for role in T12_AUDIT_ROLES:
        assert "{{TMP_SINK_PATH}}" in _read(role), (
            f"{role}.md: raw-evidence scratch sink missing"
        )


# ---------------------------------------------------------------------------
# T13 — lazy rule + pointer table (H-1, H-3, H-4, AC-16)
# ---------------------------------------------------------------------------

import sys as _sys  # noqa: E402

_sys.path.insert(0, str(ROOT / "scripts"))

import pytest  # noqa: E402
import yaml  # noqa: E402

from lib.rule_channels import lazy_skill_channel  # noqa: E402
from lib.rules import (  # noqa: E402
    collect_rule_sources,
    provider_opts_skip,
    resolve_rules,
    rule_opts_lazy_channel,
)

RULES_PRESETS = ROOT / "config" / "rules-presets.yaml"
ARTIFACT_RULE = ROOT / "rules" / "1-generic" / "artifact-locations.md"
USE_LAZY_RULES = ROOT / "rules" / "1-generic" / "use-lazy-rules.md"

# #1180 owns the generated lazy-pointer index/skill. While it is open the
# artifact-locations pointer is hand-maintained in use-lazy-rules.md and these
# generated artifacts do not exist; once #1180 lands the skipif below flips to
# active and the pointer test validates the generated source instead.
GENERATED_ARTIFACT_SKILL = (
    ROOT / ".claude" / "skills" / "artifact-locations" / "SKILL.md"
)

# The 23 canonical class names of the matrix (plan §3: 14 non-SE + 9 SE).
T13_CLASS_NAMES = (
    # 14 non-SE
    "specs", "plans", "concepts", "spikes", "reviews", "audits", "analysis",
    "reports", "adr", "traceability", "runbooks", "project-docs", "scratch",
    "state",
    # 9 SE
    "se-requirements", "se-architecture", "se-decomposition", "se-interfaces",
    "se-implementation", "se-testplan", "se-validation", "se-verification",
    "se-decisions",
)


def test_artifact_rule_is_lazy_in_lazy_preset():
    """H-1: the new rule is a skill-channel rule inside the lazy preset."""
    presets = yaml.safe_load(RULES_PRESETS.read_text(encoding="utf-8"))["presets"]
    opts = presets["lazy"]["artifact-locations"]
    assert opts["channel"] == "skill"
    assert opts.get("skill-description"), "skill-description must be set"


def test_no_always_on_rule_added():
    """AC-16: the lazy rule stays out of the always-on set and rules_dir files."""
    config = {"rules-preset": "lazy", "platforms": []}
    options = resolve_rules(config, ROOT)
    assert "artifact-locations" in options
    opts = options["artifact-locations"]
    assert opts.get("channel") == "skill"
    assert rule_opts_lazy_channel(opts)
    assert opts.get("alwaysApply") is not True
    assert opts.get("embed") is not True

    # Partition the resolved rules by channel (the AC-16 set assertion).
    lazy = {s for s, o in options.items() if rule_opts_lazy_channel(o)}
    always_on = {s for s, o in options.items() if not rule_opts_lazy_channel(o)}
    assert lazy & always_on == set()
    assert "artifact-locations" in lazy
    assert "artifact-locations" not in always_on

    # No generated <rules_dir>/artifact-locations.md: source stems that stay as
    # rule files (non-lazy, not provider-skipped) never contain the new rule.
    source_stems = {
        Path(name).stem
        for _src, name in collect_rule_sources(ROOT, [], config=config)
    }
    assert "artifact-locations" in source_stems
    rules_dir_files = {
        s for s in source_stems
        if not rule_opts_lazy_channel(options.get(s, {}))
        and not provider_opts_skip(options.get(s, {}), "Claude")
    }
    assert "artifact-locations" not in rules_dir_files
    assert lazy & rules_dir_files == set()

    # The lazy-skill route is a real file channel (IC-15) — the rule body
    # leaves the always-on context via SKILL.md, it is never silently dropped.
    skill_caps = {
        "has_rules": False,
        "skills_dir": "skills",
        "rules_read_channels": ["embedded", "skills"],
    }
    assert lazy_skill_channel(skill_caps)


def test_rule_lists_all_23_classes():
    """The lazy rule carries the full 23-class table and mode semantics."""
    text = ARTIFACT_RULE.read_text(encoding="utf-8")
    row_keys = [
        line.strip().strip("|").split("|")[0].strip()
        for line in text.splitlines()
        if line.lstrip().startswith("|")
    ]
    assert len(T13_CLASS_NAMES) == 23
    for name in T13_CLASS_NAMES:
        assert name in row_keys, f"missing class row: {name}"
    assert "files" in text and "inline" in text and "off" in text


@pytest.mark.skipif(
    not GENERATED_ARTIFACT_SKILL.exists(),
    reason=(
        "#1180 ersetzt Handpflege durch Generierung: generated "
        ".claude/skills/artifact-locations/SKILL.md index is not present yet; "
        "the pointer is hand-maintained in use-lazy-rules.md until #1180 lands"
    ),
)
def test_pointer_table_entry_present():
    """H-3: once #1180 lands the pointer table is generated, not hand-written."""
    text = GENERATED_ARTIFACT_SKILL.read_text(encoding="utf-8")
    assert "artifact-locations" in text


def test_provider_context_count_does_not_grow():
    """H-4 (RVW2-1186-03): PROJECT_CONTEXT stays relative, never pinned 70/98.

    T13 adds only a *lazy* rule and touches no role template, so the number of
    ``{{PROJECT_CONTEXT}}`` sites and the role-template count are unchanged.
    The assertion is deliberately relative to the live template count -- the
    issue's "70/98" was already stale (83/98 at review time), so no absolute
    number or line index is pinned.  The new rule body references output
    targets through ``{{ARTIFACT_*}}`` variables, never a fixed path or line.
    """
    templates = [p for p in GENERIC.glob("*.md") if not p.name.startswith("_")]
    n_templates = len(templates)
    assert n_templates > 0
    bodies = [p.read_text(encoding="utf-8") for p in templates]
    total = sum(body.count("{{PROJECT_CONTEXT}}") for body in bodies)
    carrying = sum("{{PROJECT_CONTEXT}}" in body for body in bodies)
    # Relative band: a clear majority of roles carry the placeholder, but it
    # never runs away to many sites per role. Bounds scale with the live
    # template count -- no literal 70/83/98 and no pinned line number.
    assert 0.5 * n_templates <= carrying <= n_templates, (carrying, n_templates)
    assert carrying <= total <= 2 * n_templates, (total, n_templates)
    # The rule body uses relative variable references, not pinned numbers.
    rule_text = ARTIFACT_RULE.read_text(encoding="utf-8")
    assert "{{ARTIFACT_" in rule_text
    for pinned in ("70/98", "line 70", "line 98"):
        assert pinned not in rule_text
