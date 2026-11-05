"""AC-15 / AC-16 + P0 gate — the topology probe evidence rule.

SPEC-orchestrator-topology-2026-11-03, P0 (issue #1077), Task 4.

The evidence document is the single source of truth for claims that go beyond
the normative pre-P0 matrix (spec section "Provider-Matrix (Stand vor P0)").
This module pins four things against the *live* repository:

* the document exists at its normative path and records exactly the five probes
  ``P0-1`` ... ``P0-5``;
* every provider record carries one of the three verdicts (``evidence``,
  ``not run — CLI unavailable``, ``inconclusive``) plus a non-empty observed
  result;
* the three-condition P0 gate: a cell that deviates from ``PRE_P0_BASELINE``
  ("upgrade", plan K-2) needs a recorded ``evidence`` verdict for its probe
  *and* a ``DOCUMENTED``/``VERIFIED-RUNTIME`` state; unchanged baseline cells
  are derived from existing capability keys (not from probes) and are exempt;
* AC-16 counting: 40 cells, ``25 + N`` data-derived / ``15 - N``
  ``UNVERIFIED => no``, with ``N`` recomputed from the capability data, never
  asserted.

A synthetic document with a fake ``evidence`` verdict proves the gate has
teeth: `evidence` is only accepted when command, date, provider version and
observed result are all recorded.
"""

from __future__ import annotations

import copy
import re
from collections import Counter
from pathlib import Path

import pytest
import yaml

_ROOT = Path(__file__).resolve().parent.parent
_SPIKE = _ROOT / "docs" / "spikes" / "2026-11-03-issue-1077-topology-probe.md"
_SPIKE_OLD_PATH = _ROOT / "docs" / "spikes" / "2026-11-04-issue-1077-topology-probe.md"
_CAPABILITIES = _ROOT / "config" / "provider-capabilities.yaml"
_AI_PROVIDERS = _ROOT / "config" / "ai-providers.yaml"

_PROBE_IDS = frozenset({"P0-1", "P0-2", "P0-3", "P0-4", "P0-5"})
_VERDICTS = frozenset(
    {"evidence", "not run — CLI unavailable", "inconclusive"}
)
_EVIDENCE_STATES = frozenset({"DOCUMENTED", "VERIFIED-RUNTIME"})
_AXES = ("primary", "subagent", "hybrid")
_CELLS = _AXES + ("multiple",)
_CUSTOM_PROVIDER_CELLS = 4
_PLACEHOLDERS = frozenset({"", "—", "-", "n/a", "none", "tbd", "todo"})

# ---------------------------------------------------------------------------
# Normative pre-P0 baseline (plan K-2) — transcribed ONCE from the spec table
# "Provider-Matrix (Stand vor P0)". A cell is (support, verified_state).
# Any deviation from this mapping is an upgrade and must satisfy the P0 gate.
# ---------------------------------------------------------------------------
PRE_P0_BASELINE = {
    ("Claude", "primary"): (True, "DOCUMENTED"),
    ("Claude", "subagent"): (True, "DOCUMENTED"),
    ("Claude", "hybrid"): (False, "UNVERIFIED"),
    ("Claude", "multiple"): (True, "DOCUMENTED"),
    ("Opencode", "primary"): (True, "DOCUMENTED"),
    ("Opencode", "subagent"): (True, "DOCUMENTED"),
    ("Opencode", "hybrid"): (False, "UNVERIFIED"),
    ("Opencode", "multiple"): (True, "DOCUMENTED"),
    ("Gemini", "primary"): (False, "DOCUMENTED"),
    ("Gemini", "subagent"): (True, "DOCUMENTED"),
    ("Gemini", "hybrid"): (False, "UNVERIFIED"),
    ("Gemini", "multiple"): (True, "DOCUMENTED"),
    ("Continue", "primary"): (True, "DOCUMENTED"),
    ("Continue", "subagent"): (False, "DOCUMENTED"),
    ("Continue", "hybrid"): (False, "UNVERIFIED"),
    ("Continue", "multiple"): (False, "DOCUMENTED"),
    ("Copilot", "primary"): (False, "DOCUMENTED"),
    ("Copilot", "subagent"): (True, "DOCUMENTED"),
    ("Copilot", "hybrid"): (False, "UNVERIFIED"),
    ("Copilot", "multiple"): (False, "DOCUMENTED"),
    ("Mammouth", "primary"): (False, "UNVERIFIED"),
    ("Mammouth", "subagent"): (True, "DOCUMENTED"),
    ("Mammouth", "hybrid"): (False, "UNVERIFIED"),
    ("Mammouth", "multiple"): (False, "DOCUMENTED"),
    ("Codex", "primary"): (False, "UNVERIFIED"),
    ("Codex", "subagent"): (True, "DOCUMENTED"),
    ("Codex", "hybrid"): (False, "UNVERIFIED"),
    ("Codex", "multiple"): (True, "DOCUMENTED"),
    ("ZCode", "primary"): (False, "DOCUMENTED"),
    ("ZCode", "subagent"): (True, "DOCUMENTED"),
    ("ZCode", "hybrid"): (False, "UNVERIFIED"),
    ("ZCode", "multiple"): (False, "DOCUMENTED"),
    ("KimiCode", "primary"): (True, "DOCUMENTED"),
    ("KimiCode", "subagent"): (True, "DOCUMENTED"),
    ("KimiCode", "hybrid"): (False, "UNVERIFIED"),
    ("KimiCode", "multiple"): (True, "DOCUMENTED"),
}


# ---------------------------------------------------------------------------
# Document parsing
# ---------------------------------------------------------------------------
_PROBE_HEADING = re.compile(r"^## (P0-[1-5])\s*$", re.MULTILINE)
_RESULT_ROW = re.compile(
    r"^\|\s*(P0-[1-5])\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*([^|]+?)\s*\|\s*$",
    re.MULTILINE,
)
_OBSERVED = re.compile(
    r"\*\*Beobachtetes Ergebnis:\*\*(.*?)(?=\n- \*\*Verdikt:\*\*|\Z)",
    re.DOTALL,
)
_VERDICT = re.compile(r"\*\*Verdikt:\*\*\s*`([^`]+)`")
_BALANCE = re.compile(
    r"\*\*Bilanz:\s*(\d+)\s*`evidence`\s*·\s*(\d+)\s*`inconclusive`"
    r"\s*·\s*(\d+)\s*`not run`"
)


def _line_field(body, label):
    match = re.search(
        r"^- \*\*" + re.escape(label) + r":\*\*\s*(.*)$", body, re.MULTILINE
    )
    return match.group(1).strip() if match else ""


def _observed(body):
    match = _OBSERVED.search(body)
    if not match:
        return ""
    return re.sub(r"\s+", " ", match.group(1)).strip()


def _evidence_problems(record):
    """Why an ``evidence`` verdict is not yet real evidence.

    The P0 gate requires command, date, provider version and observed result
    for every evidence claim. A bare verdict is a fake evidence row.
    """
    if record["verdict"] != "evidence":
        return []
    problems = []
    for field, label in (
        ("command", "Befehl"),
        ("date", "Datum"),
        ("version", "Provider-Version"),
        ("observed", "Beobachtetes Ergebnis"),
    ):
        value = (record.get(field) or "").strip()
        if not value or value.lower() in _PLACEHOLDERS or value.startswith("—"):
            problems.append(f"missing {label}")
    return problems


def parse_probe_records(text):
    """Parse ``## P0-n`` sections into records keyed by probe id."""
    headings = list(_PROBE_HEADING.finditer(text))
    ids = [match.group(1) for match in headings]
    if len(ids) != len(set(ids)):
        raise ValueError(f"duplicate probe headings: {ids}")

    records = {}
    for index, heading in enumerate(headings):
        end = headings[index + 1].start() if index + 1 < len(headings) else len(text)
        body = text[heading.end():end]
        record = {
            "probe_id": heading.group(1),
            "command": _line_field(body, "Befehl"),
            "date": _line_field(body, "Datum"),
            "version": _line_field(body, "Provider-Version").strip("`"),
            "observed": _observed(body),
            "verdict": (_VERDICT.search(body).group(1) if _VERDICT.search(body) else ""),
        }
        record["problems"] = _evidence_problems(record)
        record["valid_evidence"] = (
            record["verdict"] == "evidence" and not record["problems"]
        )
        records[record["probe_id"]] = record
    return records


def parse_result_table(text):
    """Parse the ``Ergebnis-Tabelle``: probe -> provider, verdict, cells."""
    rows = {}
    for match in _RESULT_ROW.finditer(text):
        probe_id, provider, verdict_cell, cell_cell = match.groups()
        verdict_match = re.search(r"`([^`]+)`", verdict_cell)
        rows[probe_id] = {
            "provider": provider.strip(),
            "verdict": (
                verdict_match.group(1) if verdict_match else verdict_cell.strip()
            ),
            "cells": tuple(
                re.findall(r"`(primary|subagent|hybrid|multiple)`", cell_cell)
            ),
        }
    return rows


def evidence_map_from_table(rows):
    """Map ``(provider, cell)`` -> probe id, as declared by the document."""
    return {
        (row["provider"], cell): probe_id
        for probe_id, row in rows.items()
        for cell in row["cells"]
    }


# ---------------------------------------------------------------------------
# Capability data helpers
# ---------------------------------------------------------------------------
def _load_yaml(path):
    with path.open(encoding="utf-8") as handle:
        return yaml.safe_load(handle) or {}


def capabilities():
    return _load_yaml(_CAPABILITIES).get("capabilities") or {}


def registered_providers():
    return sorted((_load_yaml(_AI_PROVIDERS).get("providers") or {}).keys())


def _cell_state(caps, cell):
    return caps["topology_verified_state"][cell]


def _cell_support(caps, cell):
    if cell == "multiple":
        return caps["orchestrator_instances"]["multiple"]
    return caps["topology_support"][cell]


def matrix_counts(caps):
    """Return ``(data_derived, unverified)`` for the 40 normative cells."""
    derived = 0
    unverified = 0
    for provider_caps in caps.values():
        states = provider_caps["topology_verified_state"]
        for cell in _CELLS:
            if states[cell] == "UNVERIFIED":
                unverified += 1
            else:
                derived += 1
    return derived, unverified + _CUSTOM_PROVIDER_CELLS


def baseline_counts():
    derived = sum(
        1 for _, state in PRE_P0_BASELINE.values() if state != "UNVERIFIED"
    )
    unverified = sum(
        1 for _, state in PRE_P0_BASELINE.values() if state == "UNVERIFIED"
    )
    return derived, unverified + _CUSTOM_PROVIDER_CELLS


def upgrade_count(caps):
    """N = cells that left UNVERIFIED relative to the normative baseline."""
    count = 0
    for (provider, cell), (_, base_state) in PRE_P0_BASELINE.items():
        if base_state == "UNVERIFIED" and _cell_state(caps[provider], cell) != "UNVERIFIED":
            count += 1
    return count


# ---------------------------------------------------------------------------
# The three-condition gate
# ---------------------------------------------------------------------------
def _rejection_reason(record):
    if record["verdict"] != "evidence":
        return f"verdict is {record['verdict']!r}, not 'evidence'"
    return "malformed evidence record: " + ", ".join(record["problems"])


def gate_violations(records, evidence_map, caps, baseline=PRE_P0_BASELINE):
    """Return every P0-gate violation; an empty list is the invariant.

    Conditions checked for every cell:
    * AC-15: ``support == true`` requires a ``DOCUMENTED``/``VERIFIED-RUNTIME``
      state (no speculative ``yes``);
    * plan K-2: a deviation from ``PRE_P0_BASELINE`` is an upgrade and needs a
      recorded ``evidence`` verdict for its probe *and* an evidence-grade
      state. Unchanged baseline cells are data-derived from existing
      capability keys and are not probe claims.
    """
    violations = []
    for provider, provider_caps in caps.items():
        for cell in _CELLS:
            supported = _cell_support(provider_caps, cell)
            state = _cell_state(provider_caps, cell)
            if supported and state not in _EVIDENCE_STATES:
                violations.append(
                    f"{provider}.{cell}: support is true but state is {state}"
                )

            baseline_cell = baseline.get((provider, cell))
            if baseline_cell is None:
                violations.append(
                    f"{provider}.{cell}: cell is absent from the normative "
                    "pre-P0 baseline — transcribe it before claiming it"
                )
                continue
            if (supported, state) == baseline_cell:
                continue

            probe_id = evidence_map.get((provider, cell))
            if probe_id is None:
                violations.append(
                    f"{provider}.{cell}: upgrade without a probe recorded for "
                    "this cell"
                )
                continue
            record = records.get(probe_id)
            if record is None:
                violations.append(
                    f"{provider}.{cell}: upgrade cites {probe_id} but the "
                    "evidence document has no such record"
                )
                continue
            if not record["valid_evidence"]:
                violations.append(
                    f"{provider}.{cell}: upgrade cites {probe_id} — "
                    f"{_rejection_reason(record)}"
                )
            if state not in _EVIDENCE_STATES:
                violations.append(
                    f"{provider}.{cell}: upgrade without a DOCUMENTED/"
                    f"VERIFIED-RUNTIME state (got {state})"
                )
    return violations


# ---------------------------------------------------------------------------
# Fixtures and live inputs
# ---------------------------------------------------------------------------
def _spike_text():
    return _SPIKE.read_text(encoding="utf-8") if _SPIKE.is_file() else ""


def _live_records():
    return parse_probe_records(_spike_text())


def _live_evidence_map():
    return evidence_map_from_table(parse_result_table(_spike_text()))


def _synthetic_spike_doc(
    *,
    verdict="evidence",
    observed="Exit 0; --agent documented",
    command="`claude --help`",
    date="2026-11-04T00:00:00Z",
    version="`2.1.318 (Claude Code)`",
    provider="Claude",
    axis="primary",
):
    return (
        "# Synthetic spike\n\n"
        "## P0-2\n\n"
        f"- **Befehl:** {command}\n"
        f"- **Datum:** {date}\n"
        f"- **Provider-Version:** {version}\n"
        f"- **Beobachtetes Ergebnis:** {observed}\n"
        f"- **Verdikt:** `{verdict}`\n\n"
        "## Ergebnis-Tabelle\n\n"
        "| Probe | Provider | Ergebnis | Zelle(n) |\n"
        "|---|---|---|---|\n"
        f"| P0-2 | {provider} | `{verdict}` | {provider} `{axis}` |\n"
    )


def _caps_with_upgrade(provider="Claude", cell="primary", state="VERIFIED-RUNTIME"):
    caps = copy.deepcopy(capabilities())
    caps[provider]["topology_verified_state"][cell] = state
    return caps


# ---------------------------------------------------------------------------
# (a) normative path, exactly five probes
# ---------------------------------------------------------------------------
def test_spike_doc_exists_at_normative_path_with_exactly_five_probes():
    assert _SPIKE.is_file(), f"missing normative evidence document: {_SPIKE}"
    assert not _SPIKE_OLD_PATH.exists(), (
        f"stale duplicate evidence document at {_SPIKE_OLD_PATH.name}; the "
        "normative path is 2026-11-03-issue-1077-topology-probe.md"
    )

    text = _spike_text()
    ids = re.findall(r"^## (P0-[1-5])\s*$", text, re.MULTILINE)
    assert ids == ["P0-1", "P0-2", "P0-3", "P0-4", "P0-5"], (
        f"expected exactly five ordered probe sections, got {ids}"
    )

    table = parse_result_table(text)
    assert set(table) == _PROBE_IDS
    assert {row["provider"] for row in table.values()} == {
        "Opencode",
        "Claude",
        "Codex",
        "Mammouth",
        "KimiCode",
    }
    for probe_id, row in table.items():
        assert row["cells"], f"{probe_id}: no candidate cell declared"
        assert row["verdict"] == _live_records()[probe_id]["verdict"], (
            f"{probe_id}: result table and probe section disagree on the verdict"
        )


# ---------------------------------------------------------------------------
# (b) verdict + observed line
# ---------------------------------------------------------------------------
@pytest.mark.parametrize("probe_id", sorted(_PROBE_IDS))
def test_every_provider_record_has_a_known_verdict_and_observed_line(probe_id):
    record = _live_records()[probe_id]
    assert record["verdict"] in _VERDICTS, (
        f"{probe_id}: unknown verdict {record['verdict']!r}"
    )
    assert record["observed"], f"{probe_id}: empty observed result"


def test_document_balance_line_matches_the_probe_verdicts():
    text = _spike_text()
    match = _BALANCE.search(text)
    assert match, "evidence document must state its Bilanz line"
    counts = Counter(record["verdict"] for record in _live_records().values())
    assert (
        int(match.group(1)),
        int(match.group(2)),
        int(match.group(3)),
    ) == (
        counts.get("evidence", 0),
        counts.get("inconclusive", 0),
        counts.get("not run — CLI unavailable", 0),
    )


# ---------------------------------------------------------------------------
# (c) three-condition gate against the live document
# ---------------------------------------------------------------------------
def test_every_support_yes_cell_passes_the_three_condition_gate():
    caps = capabilities()
    records = _live_records()
    evidence_map = _live_evidence_map()

    assert len(records) == 5, "the gate must see all five probe records"
    assert len(evidence_map) == 5, "the gate must see all five probe cells"

    violations = gate_violations(records, evidence_map, caps)
    assert violations == [], "P0 gate violated:\n" + "\n".join(violations)

    # Teeth: the live matrix really contains support-yes cells, so the gate
    # assertion above is not vacuous.
    support_true = [
        (provider, cell)
        for provider, provider_caps in caps.items()
        for cell in _CELLS
        if _cell_support(provider_caps, cell)
    ]
    assert len(support_true) == 17, (
        f"expected 17 support-yes cells in the live matrix, got {len(support_true)}"
    )
    for provider, cell in support_true:
        assert _cell_state(caps[provider], cell) in _EVIDENCE_STATES

    assert upgrade_count(caps) == 0, (
        "the live capability data must still be the pre-P0 baseline (N = 0)"
    )


# ---------------------------------------------------------------------------
# (d) AC-16 counting rule, recomputed from the data
# ---------------------------------------------------------------------------
def test_ac16_counts_are_measured_from_the_capability_data():
    caps = capabilities()
    assert len(caps) == len(registered_providers()) == 9
    assert len(PRE_P0_BASELINE) == 36

    base_derived, base_unverified = baseline_counts()
    assert (base_derived, base_unverified) == (25, 15), (
        "PRE_P0_BASELINE must transcribe the normative 25/15 matrix"
    )

    derived, unverified = matrix_counts(caps)
    assert derived + unverified == 40, (
        f"matrix must have 40 cells, got {derived + unverified}"
    )

    upgrade_n = upgrade_count(caps)
    assert 0 <= upgrade_n <= 15
    assert derived == base_derived + upgrade_n, (
        f"data-derived cells must be 25 + N ({base_derived} + {upgrade_n}), "
        f"got {derived}"
    )
    assert unverified == base_unverified - upgrade_n, (
        f"UNVERIFIED => no cells must be 15 - N ({base_unverified} - "
        f"{upgrade_n}), got {unverified}"
    )
    assert upgrade_n == derived - base_derived, "N must come from the data"

    speculative = [
        f"{provider}.{cell}"
        for provider, provider_caps in caps.items()
        for cell in _CELLS
        if _cell_support(provider_caps, cell)
        and _cell_state(provider_caps, cell) == "UNVERIFIED"
    ]
    assert speculative == [], f"speculative yes cells: {speculative}"


# ---------------------------------------------------------------------------
# (e) negative controls — prove the gate has teeth
# ---------------------------------------------------------------------------
def test_negative_control_fake_evidence_verdict_is_rejected():
    """A synthetic ``evidence`` verdict without a recorded observation is fake.

    The parser must downgrade it (``valid_evidence`` is false) and the gate
    must reject the upgrade that cites it.
    """
    doc = _synthetic_spike_doc(observed="")
    records = parse_probe_records(doc)
    assert records["P0-2"]["verdict"] == "evidence"
    assert records["P0-2"]["valid_evidence"] is False
    assert records["P0-2"]["problems"], "a bare evidence verdict must be flagged"

    evidence_map = evidence_map_from_table(parse_result_table(doc))
    violations = gate_violations(
        records, evidence_map, _caps_with_upgrade("Claude", "primary")
    )
    assert any("P0-2" in violation for violation in violations), (
        f"fake evidence was accepted: {violations}"
    )


def test_negative_control_gate_accepts_a_genuine_upgrade():
    """Counter-case: a complete evidence record + verified state is allowed."""
    doc = _synthetic_spike_doc()
    records = parse_probe_records(doc)
    assert records["P0-2"]["valid_evidence"] is True

    evidence_map = evidence_map_from_table(parse_result_table(doc))
    assert (
        gate_violations(
            records, evidence_map, _caps_with_upgrade("Claude", "primary")
        )
        == []
    )


def test_upgrade_with_evidence_but_unverified_state_is_rejected():
    doc = _synthetic_spike_doc()
    records = parse_probe_records(doc)
    evidence_map = evidence_map_from_table(parse_result_table(doc))
    violations = gate_violations(
        records, evidence_map, _caps_with_upgrade("Claude", "primary", "UNVERIFIED")
    )
    assert any("UNVERIFIED" in violation for violation in violations)


def test_upgrade_without_an_evidence_verdict_is_rejected():
    doc = _synthetic_spike_doc(
        verdict="inconclusive", observed="not observable by this command"
    )
    records = parse_probe_records(doc)
    evidence_map = evidence_map_from_table(parse_result_table(doc))
    violations = gate_violations(
        records, evidence_map, _caps_with_upgrade("Claude", "primary")
    )
    assert any("not 'evidence'" in violation for violation in violations)


def test_not_run_verdict_never_justifies_an_upgrade_and_cells_stay_green():
    """A ``not run — CLI unavailable`` record is valid but never evidence.

    It leaves the cell `no` (no upgrade) and, for unmodified data, produces
    zero gate findings — the loudness rule is elsewhere (AC-16).
    """
    records = _live_records()
    evidence_map = _live_evidence_map()
    assert gate_violations(records, evidence_map, capabilities()) == []

    caps = copy.deepcopy(capabilities())
    caps["Mammouth"]["topology_support"]["primary"] = True
    caps["Mammouth"]["topology_verified_state"]["primary"] = "DOCUMENTED"
    violations = gate_violations(records, evidence_map, caps)
    assert any(
        "Mammouth.primary" in violation and "P0-4" in violation
        for violation in violations
    ), f"a not-run verdict was accepted as evidence: {violations}"
