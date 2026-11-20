"""Task 4 (#860) — the Antigravity runtime probe runbook pin.

The runbook is a *documentation-only* deliverable. The external probe itself
is out of scope (G-PR2, issue #860 is blocked by the `agy` SIGILL/pclmul
host limitation). This test only pins that the runbook exists at its
normative path and documents every term the plan requires:

* the ``agy --help`` precondition and the ``pclmul`` prerequisite;
* the verdicts G-1, G-2, G-3, G-7, H2, H3;
* the linked issue #1032;
* the observed "Exit 132" blocker signature.
"""

from __future__ import annotations

from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
_RUNBOOK = _ROOT / "docs" / "analysis" / "runbooks" / "antigravity-runtime-probe.md"


def test_antigravity_probe_runbook_exists():
    """The runbook lives at its normative, plan-defined path."""
    assert _RUNBOOK.is_file(), f"missing runbook: {_RUNBOOK}"


def test_antigravity_probe_runbook_contains_required_terms():
    """The runbook documents every keyword required by plan Task 4."""
    text = _RUNBOOK.read_text(encoding="utf-8")
    required = (
        "agy --help",
        "pclmul",
        "G-1",
        "G-2",
        "G-3",
        "G-7",
        "H2",
        "H3",
        "#1032",
        "Exit 132",
    )
    missing = [term for term in required if term not in text]
    assert not missing, f"runbook missing required terms: {missing}"
