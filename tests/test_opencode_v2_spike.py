"""Structure contract for the C0 spike result document (issue #1007, AC-C1).

Plan: ``docs/plans/2026-10-22-opencode-v2-support-plan.md`` Task 1 (C0.1).
Spec: ``docs/specs/2026-10-22-opencode-v2-support-spec.md`` 3.6 / AC-C1.

The tests are pure document checks: no network, no runtime probing.
"""

from __future__ import annotations

import re
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]

SPIKE = Path("docs/spikes/2026-10-22-issue-1007-opencode-v2-plugin-api-spike.md")
SPEC = Path("docs/specs/2026-10-22-opencode-v2-support-spec.md")

MARKERS = ("VERIFIED", "DOKU", "UNVERIFIED")
MARKER_TOKEN_RE = re.compile(r"\b(VERIFIED|DOKU|UNVERIFIED)\b")
Q_HEADING_RE = re.compile(r"(?m)^## Q([1-6])\b")
H2_RE = re.compile(r"(?m)^## ")
VERDICT_C3_RE = re.compile(r"(?m)^VERDICT-C3: (GO|NO-GO)$")
VERDICT_FIELDS_RE = re.compile(r"(?m)^VERDICT-FIELDS: (CONFIRMED|AMEND)$")
PROBES_RE = re.compile(r"(?m)^\s*(?:[-*]\s*)?Proben:\s*(\d+)\s*$")
SOURCES_RE = re.compile(r"(?m)^\s*(?:[-*]\s*)?Quellen:\s*(\d+)\s*$")
AMENDMENT_B1_HEADING_RE = re.compile(
    r"(?mi)^#{1,6}\s.*\bAmendment\s+B1\b"
)

Q5_KEYS = ("timeout", "oauth", "disabled", "system", "variant")
Q6_KEYS = (
    "experimental.subagent_depth",
    "experimental.todo",
    "providers",
    "agents.title.model",
    "cli.json",
)


def _read(rel_path: Path) -> str:
    path = REPO_ROOT / rel_path
    assert path.is_file(), f"missing document: {rel_path.as_posix()}"
    return path.read_text(encoding="utf-8")


def _read_spike() -> str:
    return _read(SPIKE)


def _q_sections(text: str) -> dict[int, str]:
    """Return the text of each ``## Qn`` section, up to the next level-2 heading."""
    sections: dict[int, str] = {}
    for match in Q_HEADING_RE.finditer(text):
        number = int(match.group(1))
        next_h2 = H2_RE.search(text, match.start() + 1)
        end = next_h2.start() if next_h2 else len(text)
        sections[number] = text[match.start() : end]
    return sections


def _key_marker_line_re(key: str) -> re.Pattern[str]:
    return re.compile(
        r"(?m)^\s*(?:[-*]\s*)?" + re.escape(key) + r":\s*(VERIFIED|DOKU|UNVERIFIED)\b"
    )


def test_spike_doc_exists() -> None:
    """AC-C1: the spike result document exists and is not empty."""
    path = REPO_ROOT / SPIKE
    assert path.is_file(), f"missing spike document: {SPIKE.as_posix()}"
    assert path.read_text(encoding="utf-8").strip(), (
        f"spike document is empty: {SPIKE.as_posix()}"
    )


def test_q1_to_q6_sections_present() -> None:
    """AC-C1 / Spec 3.6: exactly one ``## Q1`` ... ``## Q6`` heading each."""
    text = _read_spike()
    numbers = [int(m.group(1)) for m in Q_HEADING_RE.finditer(text)]
    assert len(numbers) == 6, f"expected 6 Q headings, found {len(numbers)}: {numbers}"
    assert sorted(numbers) == [1, 2, 3, 4, 5, 6], f"expected Q1..Q6 once each, got {numbers}"


def test_each_answer_has_marker_and_source() -> None:
    """AC-C1 / Spec 3.6: each Q section carries a marker and a ``Quelle:`` line."""
    sections = _q_sections(_read_spike())
    assert sorted(sections) == [1, 2, 3, 4, 5, 6], (
        f"expected sections Q1..Q6, found {sorted(sections)}"
    )
    for number in range(1, 7):
        body = sections[number]
        markers = MARKER_TOKEN_RE.findall(body)
        assert markers, f"Q{number}: no evidence marker (VERIFIED/DOKU/UNVERIFIED)"
        assert re.search(r"(?m)^\s*(?:[-*]\s*)?Quelle:", body), (
            f"Q{number}: missing 'Quelle:' line"
        )


def test_q5_q6_marker_per_key() -> None:
    """Spec 3.6 Q5/Q6: every verified field/key carries its own marker line."""
    sections = _q_sections(_read_spike())
    for number in (5, 6):
        assert number in sections, f"missing section Q{number}"

    for key in Q5_KEYS:
        assert _key_marker_line_re(key).search(sections[5]), (
            f"Q5: missing marker line '{key}: VERIFIED|DOKU|UNVERIFIED'"
        )
    for key in Q6_KEYS:
        assert _key_marker_line_re(key).search(sections[6]), (
            f"Q6: missing marker line '{key}: VERIFIED|DOKU|UNVERIFIED'"
        )


def test_ac_c1_verdict_lines_exactly_once() -> None:
    """AC-C1: each verdict line occurs exactly once in the spike document."""
    text = _read_spike()
    c3 = VERDICT_C3_RE.findall(text)
    fields = VERDICT_FIELDS_RE.findall(text)
    assert len(c3) == 1, f"expected exactly one 'VERDICT-C3:' line, found {len(c3)}"
    assert len(fields) == 1, (
        f"expected exactly one 'VERDICT-FIELDS:' line, found {len(fields)}"
    )


def test_measure_budget_respected() -> None:
    """Spec 3.6 budget: at most 3 probes and 5 sources per question."""
    sections = _q_sections(_read_spike())
    for number in range(1, 7):
        assert number in sections, f"missing section Q{number}"
        body = sections[number]

        probes = [int(value) for value in PROBES_RE.findall(body)]
        sources = [int(value) for value in SOURCES_RE.findall(body)]
        assert probes, f"Q{number}: missing 'Proben: <n>' line"
        assert sources, f"Q{number}: missing 'Quellen: <n>' line"
        assert max(probes) <= 3, f"Q{number}: probe budget exceeded ({probes} > 3)"
        assert max(sources) <= 5, f"Q{number}: source budget exceeded ({sources} > 5)"


def test_verdict_consequences_recorded() -> None:
    """Spec 3.6: AMEND/NO-GO requires an ``Amendment B1`` heading in the spec."""
    text = _read_spike()
    c3 = VERDICT_C3_RE.findall(text)
    fields = VERDICT_FIELDS_RE.findall(text)

    needs_amendment = (fields and fields[0] == "AMEND") or (c3 and c3[0] == "NO-GO")
    if not needs_amendment:
        return

    spec_text = _read(SPEC)
    assert AMENDMENT_B1_HEADING_RE.search(spec_text), (
        "spike verdict requires consequences, but the spec has no "
        "'Amendment B1' heading"
    )
