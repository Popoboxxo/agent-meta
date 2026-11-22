"""Tests for scripts/measure_context_repin.py (issue #1115 helper)."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts import measure_context_repin as helper

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_format_repin_block_lists_only_changed_artifacts():
    report = {"Claude": {"orchestrator": {"bytes": 80000}}}
    pins = {"Claude": {"orchestrator": 72183}}
    block = helper.format_repin_block(report, pins, "full")
    assert '"Claude": {' in block
    assert '"orchestrator": 80000' in block
    assert "Claude/orchestrator: 72183 -> 80000 (+7817)" in block


def test_no_delta_returns_empty():
    report = {"Claude": {"orchestrator": {"bytes": 72183}}}
    pins = {"Claude": {"orchestrator": 72183}}
    assert helper.format_repin_block(report, pins, "full") == ""


def test_tolerance_constants_untouched():
    text = (REPO_ROOT / "tests" / "test_context_budgets.py").read_text(encoding="utf-8")
    assert "TOLERANCE_MAX_BYTES = 4096" in text
    assert "TOLERANCE_MIN_BYTES = 256" in text
    assert "TOLERANCE_RATIO = 0.02" in text
