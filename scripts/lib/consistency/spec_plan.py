"""Spec/Plan-Workflow consistency parser (design §7.3, decision D9).

Reads the human-readable ledger of a plan document — the checkbox list and the
``Status:`` header line — and exposes it as structured data. The plan/ledger
view is the human-readable recovery source; the machine-readable recovery
source is the :class:`~lib.checkpoint.CheckpointStore` round-trip (D2).

Finding/Severity are imported here as the module grows into the full
``check_spec_plan_workflow`` check (Task 10); the parser below does not use
them yet.
"""
from __future__ import annotations

import re
from pathlib import Path

from .report import Finding, Severity

REQUIRED_SPEC_SECTIONS = (
    "## Problem", "## Ziel", "## Nicht-Ziele", "## Interface Contracts",
    "## Datenfluss", "## Acceptance Criteria", "## Offene Fragen",
    "## Trace-Anker",
)
REQUIRED_PLAN_SECTIONS = (
    "**Goal:**", "**Architecture:**", "**Tech Stack:**", "**Spec:**",
    "## Global Constraints", "## File Structure", "pipeline_stages",
)


def parse_plan_ledger(plan_path: Path) -> dict:
    text = plan_path.read_text(encoding="utf-8") if plan_path.exists() else ""
    checkboxes = re.findall(r"^- \[( |x|X)\]", text, flags=re.MULTILINE)
    checked = sum(1 for box in checkboxes if box.lower() == "x")
    match = re.search(r"^\s*>?\s*Status:\s*(.+?)\s*$", text, flags=re.MULTILINE)
    status = match.group(1).strip() if match else None
    return {
        "checkboxes": len(checkboxes),
        "checked": checked,
        "complete": bool(checkboxes) and checked == len(checkboxes),
        "status": status,
    }
