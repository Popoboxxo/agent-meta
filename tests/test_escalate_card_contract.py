"""Contract test: senior-developer ESCALATE card vs. orchestrator intake rule.

SR-C-06 / W1-T5. The orchestrator rejects any ESCALATE card lacking a
categorical reason and a quantifiable metric. The senior-developer's
last-resort card (-> principal-developer) must carry both, using the
canonical field names from developer.md, and every orchestrator description
of the principal gate must name reason + metric (no "task summary + failure
log" only variant left).

Proximity window: the same line. Every gate description is a single
table row / paragraph / list item, so same-line is the natural unit.
"""
from __future__ import annotations

import re
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
_GENERIC = _ROOT / "agents" / "1-generic"
_CANONICAL = ("ESCALATE_REASON", "ESCALATE_METRIC")
_GATE_MARKERS = re.compile(r"task summary|failure log", re.IGNORECASE)


def _read(name: str) -> str:
    return (_GENERIC / name).read_text(encoding="utf-8")


def _escalate_block(text: str) -> str:
    """Return the fenced block that contains `STATUS: escalate`."""
    for block in re.findall(r"```\n(.*?)```", text, re.DOTALL):
        if "STATUS: escalate" in block:
            return block
    raise AssertionError("no fenced STATUS: escalate block found")


def _field_names(block: str) -> set[str]:
    return set(re.findall(r"^([A-Z_]+):", block, re.MULTILINE))


def test_developer_defines_canonical_fields():
    fields = _field_names(_escalate_block(_read("developer.md")))
    assert set(_CANONICAL) <= fields


def test_senior_escalate_block_has_reason_and_metric():
    block = _escalate_block(_read("senior-developer.md"))
    for name in _CANONICAL:
        assert f"{name}:" in block, f"senior-developer card lacks {name}"


def test_senior_field_names_match_developer():
    dev = _field_names(_escalate_block(_read("developer.md")))
    senior = _field_names(_escalate_block(_read("senior-developer.md")))
    canonical_in_dev = {f for f in dev if f.startswith("ESCALATE_")}
    canonical_in_senior = {f for f in senior if f.startswith("ESCALATE_")}
    assert canonical_in_senior == canonical_in_dev


def _gate_lines_without_reason_metric(text: str) -> list[str]:
    bad = []
    for line in text.splitlines():
        if not _GATE_MARKERS.search(line):
            continue
        low = line.lower()
        if "reason" not in low or "metric" not in low:
            bad.append(line.strip())
    return bad


def test_orchestrator_gate_descriptions_name_reason_and_metric():
    text = _read("orchestrator.md")
    assert _GATE_MARKERS.search(text), "gate description vanished"
    assert _gate_lines_without_reason_metric(text) == []


def test_senior_escalation_prose_names_reason_and_metric():
    # Workflow step 7 + constraint must not describe the card as
    # "task summary + failure log" alone.
    text = _read("senior-developer.md")
    bad = [
        line for line in _gate_lines_without_reason_metric(text)
        if "Compile a failure log" not in line  # step 7.1: log content only
    ]
    assert bad == []
