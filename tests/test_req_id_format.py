"""REQ-ID format validator (issue #1167, Phase H Task 20).

Binding format (O-H2 decision 22.11, spec SPEC-REQ-ID-FORMAT-1167-2026-11-11
IC-1): ``^REQ-[A-Z][A-Z0-9]*-\\d{2,3}$`` with ``re.fullmatch``. One uppercase
area segment without ``-``, 2 or 3 digits.

The check is silent when ``dod.req-traceability`` is off and emits one
``Severity.ERROR`` finding per malformed occurrence when it is on.

Run: python3 -m pytest tests/test_req_id_format.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.consistency.report import Severity  # noqa: E402
from lib.consistency.req_format import REQ_ID_PATTERN, check_req_ids  # noqa: E402


def _run(tmp_path: Path, body: str, *, traceability: bool):
    """Write a synthetic REQUIREMENTS.md and run the check against it."""
    framework = tmp_path / "framework"
    framework.mkdir(parents=True, exist_ok=True)
    project = tmp_path / "project"
    (project / "docs").mkdir(parents=True)
    (project / "docs" / "REQUIREMENTS.md").write_text(body, encoding="utf-8")
    config = {"platforms": [], "dod": {"req-traceability": traceability}}
    return check_req_ids(framework, project, config)


def test_malformed_req_id_fails_when_traceability_on(tmp_path):
    findings = _run(tmp_path, "- REQ-1 (too few digits)\n", traceability=True)
    assert len(findings) == 1
    assert findings[0].severity is Severity.ERROR
    assert findings[0].check == "req-id.format"


def test_malformed_req_id_ignored_when_off(tmp_path):
    assert _run(tmp_path, "- REQ-1 (too few digits)\n", traceability=False) == []


def test_valid_ids_pass_both_states(tmp_path):
    # AC1: the constant is byte-identical to the binding O-H2 form.
    assert REQ_ID_PATTERN == r"^REQ-[A-Z][A-Z0-9]*-\d{2,3}$"
    body = "- REQ-CMD-01 (two digits)\n- REQ-COM-123 (three digits)\n"
    assert _run(tmp_path, body, traceability=True) == []
    assert _run(tmp_path / "off", body, traceability=False) == []


def test_multi_part_area_rejected(tmp_path):
    findings = _run(tmp_path, "- REQ-L2-AT-018 (multi-part area)\n", traceability=True)
    assert len(findings) == 1
    assert findings[0].severity is Severity.ERROR
    assert "REQ-L2-AT-018" in findings[0].message


def test_single_area_accepted(tmp_path):
    assert _run(tmp_path, "- REQ-CMD-01 (single area)\n", traceability=True) == []


def test_three_digit_accepted(tmp_path):
    assert _run(tmp_path, "- REQ-COM-123 (three digits)\n", traceability=True) == []


def test_four_digit_rejected(tmp_path):
    findings = _run(tmp_path, "- REQ-COM-1234 (four digits)\n", traceability=True)
    assert len(findings) == 1
    assert findings[0].severity is Severity.ERROR
    assert "REQ-COM-1234" in findings[0].message
