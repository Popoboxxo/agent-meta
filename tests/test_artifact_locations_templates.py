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
