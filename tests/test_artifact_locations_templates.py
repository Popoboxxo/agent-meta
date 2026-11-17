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
