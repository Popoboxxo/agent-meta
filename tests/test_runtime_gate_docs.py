"""Docs guardrail: the runtime-gate tier semantics must be documented honestly.

Background (SPEC-OPENCODE-RUNTIME-GATE-2026-09-13, Task 6): the CRITICAL GATE
("MAIN CHAT darf nicht selbst editieren. ALLES -> ``orchestrator``.") is only
as strong as the runtime that backs it. The documentation must therefore name
the four tiers, mark ``permission`` as PARTIAL (never as fully enforced), keep
the Phase-1 ``plugin`` tier marked observe/P6-gated, and restate that the gate
is a convention boundary, not a security boundary.

These tests are intentionally source-assertions: an honest doc that
over-promises is a defect, so the wording is pinned here.

Run: python -m pytest tests/test_runtime_gate_docs.py -v
"""

from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_CONCEPT_DOC = _REPO_ROOT / "docs" / "concepts" / "runtime-gate-tiers.md"
_GAPS_DOC = _REPO_ROOT / "docs" / "process-capability-gaps.md"


def _normalized(text: str) -> str:
    """Lower-case + collapse whitespace so a phrase split across a wrapped
    Markdown line still matches."""
    return " ".join(text.split()).lower()


def _concept_text() -> str:
    return _CONCEPT_DOC.read_text(encoding="utf-8")


def _gaps_text() -> str:
    return _GAPS_DOC.read_text(encoding="utf-8")


def test_tier_concept_doc_exists():
    assert _CONCEPT_DOC.is_file(), (
        "docs/concepts/runtime-gate-tiers.md must exist (Task 6): the four "
        "tiers and the PARTIAL boundary need a single documented home."
    )


def test_tier_concept_doc_lists_four_tiers():
    content = _concept_text()
    for tier in ("hook", "plugin", "permission", "advisory"):
        assert tier in content, (
            f"runtime-gate-tiers.md must name the '{tier}' tier: the tier "
            "vocabulary is the contract every consumer speaks."
        )


def test_tier_concept_doc_states_partial_not_fully_enforced():
    content = _concept_text()
    lowered = _normalized(content)
    assert "partial" in lowered, (
        "runtime-gate-tiers.md must label the 'permission' tier as PARTIAL."
    )
    assert "permission" in content, (
        "runtime-gate-tiers.md must tie the PARTIAL label to the 'permission' tier."
    )
    assert "fully enforced" not in lowered, (
        "runtime-gate-tiers.md must not claim the 'permission' tier is fully "
        "enforced -- only Main-Chat writes are blocked; delegation provenance "
        "(#765) is unverified."
    )
    assert "niemals als vollständig erzwungen" in lowered, (
        "runtime-gate-tiers.md must explicitly forbid the overclaim for the "
        "'permission' tier (it stays PARTIAL)."
    )
    assert "765" in content and "unverifiziert" in lowered, (
        "runtime-gate-tiers.md must record that child-session propagation "
        "(deriveSubagentSessionPermission, #765) is UNVERIFIED."
    )


def test_tier_concept_doc_states_convention_boundary():
    lowered = _normalized(_concept_text())
    assert "convention boundary" in lowered, (
        "runtime-gate-tiers.md must state that the gate is a convention boundary."
    )
    assert "security boundary" in lowered, (
        "runtime-gate-tiers.md must contrast the convention boundary with a "
        "security boundary (it is not one)."
    )


def test_tier_concept_doc_marks_plugin_phase1_observe():
    content = _concept_text()
    lowered = _normalized(content)
    assert "observe" in lowered, (
        "runtime-gate-tiers.md must state that the Phase-1 plugin runs in "
        "observe mode by default."
    )
    assert "p6" in lowered, (
        "runtime-gate-tiers.md must name the P6 real-repo verification that "
        "gates the plugin tier flip and MODE=enforce."
    )
    assert "phase 1" in lowered or "phase-1" in lowered, (
        "runtime-gate-tiers.md must mark the 'plugin' tier as Phase 1."
    )


def test_tier_concept_doc_documents_747_avoidance():
    content = _concept_text()
    assert "747" in content, (
        "runtime-gate-tiers.md must document the #747 avoidance: A2 merges via "
        "the existing isolation path, never the create-only initializer."
    )
    assert "isolation.py" in content, (
        "runtime-gate-tiers.md must name the existing merge path in isolation.py."
    )


def test_capability_gaps_doc_reflects_opencode_status():
    content = _gaps_text()
    lowered = _normalized(content)
    assert "runtime-gate-tiers" in content, (
        "docs/process-capability-gaps.md must link the tier concept doc so the "
        "gap status and the tier semantics stay in sync."
    )
    assert "permission" in lowered, (
        "docs/process-capability-gaps.md must reflect the current 'permission' "
        "gate status."
    )
    assert "partial" in lowered, (
        "docs/process-capability-gaps.md must keep the PARTIAL qualification."
    )
    assert "phase 1" in lowered, (
        "docs/process-capability-gaps.md must record that the plugin tier is "
        "Phase 1 and still open."
    )
    assert "observe" in lowered, (
        "docs/process-capability-gaps.md must state the Phase-1 plugin runs in "
        "observe mode."
    )
    assert "765" in content, (
        "docs/process-capability-gaps.md must name the unverified child-session "
        "propagation (#765) as an open Phase-0 risk."
    )
