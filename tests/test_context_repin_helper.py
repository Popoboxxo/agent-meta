"""Tests for scripts/measure_context_repin.py (issue #1115 helper)."""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts import measure_context_repin as helper
from tests.test_context_budgets import _IST_COMPACT, _IST_FULL

REPO_ROOT = Path(__file__).resolve().parents[1]
CONVENTIONS_SOURCE = REPO_ROOT / "rules" / "2-platform" / "agent-meta-conventions.md"


def _report_from_pins(pins):
    return {
        provider: {artifact: {"bytes": size} for artifact, size in artifacts.items()}
        for provider, artifacts in pins.items()
    }


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


def test_default_profile_is_full():
    assert helper._parse_args([]).profile == "full"


def test_unknown_profile_is_rejected():
    with pytest.raises(SystemExit):
        helper._parse_args(["--profile", "medium"])


def test_main_full_prints_full_block_and_exits_1(monkeypatch, capsys):
    pin = _IST_FULL["Claude"]["orchestrator"]
    report = {"Claude": {"orchestrator": {"bytes": pin + 10}}}
    seen = {}

    def fake_measure(profile, root):
        seen["profile"] = profile
        return report

    monkeypatch.setattr(helper, "_measure_report", fake_measure)
    assert helper.main([]) == 1
    out = capsys.readouterr().out
    assert seen["profile"] == "full"
    assert "# Re-pin full (verification is human):" in out
    assert f"Claude/orchestrator: {pin} -> {pin + 10} (+10)" in out


def test_main_compact_prints_compact_block_against_compact_pins(monkeypatch, capsys):
    pin = _IST_COMPACT["Claude"]["orchestrator"]
    assert pin != _IST_FULL["Claude"]["orchestrator"], "pins must differ for this test"
    report = {"Claude": {"orchestrator": {"bytes": pin + 25}}}
    seen = {}

    def fake_measure(profile, root):
        seen["profile"] = profile
        return report

    monkeypatch.setattr(helper, "_measure_report", fake_measure)
    assert helper.main(["--profile", "compact"]) == 1
    out = capsys.readouterr().out
    assert seen["profile"] == "compact"
    assert "# Re-pin compact (verification is human):" in out
    assert f"Claude/orchestrator: {pin} -> {pin + 25} (+25)" in out


def test_second_run_after_adoption_is_silent_and_exits_0(monkeypatch, capsys):
    """Adopting the printed block makes the next run print nothing (exit 0)."""
    monkeypatch.setattr(
        helper, "_measure_report", lambda profile, root: _report_from_pins(_IST_COMPACT)
    )
    assert helper.main(["--profile", "compact"]) == 0
    assert capsys.readouterr().out == ""


def test_second_run_after_adoption_is_silent_and_exits_0_full(monkeypatch, capsys):
    monkeypatch.setattr(
        helper, "_measure_report", lambda profile, root: _report_from_pins(_IST_FULL)
    )
    assert helper.main(["--profile", "full"]) == 0
    assert capsys.readouterr().out == ""


def test_conventions_rule_source_names_the_compact_command():
    text = CONVENTIONS_SOURCE.read_text(encoding="utf-8")
    assert "python3 scripts/measure_context_repin.py --profile compact" in text
