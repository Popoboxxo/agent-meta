"""Consistency tests for the ``reference_standards`` frontmatter field.

SPEC-REFERENCE-STANDARDS-2026-09-15 (IC-02), AC-09 … AC-13.

The field is optional; only structure/format is checked (no registry, OQ-5).
The check must never raise and must not double-report a malformed frontmatter
block (that stays the exclusive domain of ``check_agent_frontmatter``).

Run: python -m pytest tests/test_consistency_reference_standards.py -v
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.consistency.reference_standards import (  # noqa: E402
    REFERENCE_STANDARDS_FORMAT_HINT,
    check_reference_standards,
    parse_reference_standards_entry,
)
from lib.consistency.report import Severity  # noqa: E402


def _tmpl(field_yaml: str = "") -> str:
    """Minimal otherwise-valid agent template with a raw ``reference_standards`` block."""
    return (
        "---\n"
        "name: template-x\n"
        'version: "1.0.0"\n'
        "description: test template\n"
        + field_yaml
        + "tools:\n"
        "  - Read\n"
        "---\n"
        "\n"
        "Body content.\n"
    )


def _check(content: str, path: Path | None = None) -> list:
    return check_reference_standards(path or (_REPO_ROOT / "agents" / "1-generic" / "x.md"),
                                     content, _REPO_ROOT, None)


# --- parse_reference_standards_entry ---------------------------------------

@pytest.mark.parametrize("entry,expected", [
    ("arc42", ("arc42", None, None)),
    ("ISTQB@4.0", ("ISTQB", "4.0", None)),
    ("IEEE 1012@2016#7", ("IEEE 1012", "2016", "7")),
    ("ASVS@4.0.3", ("ASVS", "4.0.3", None)),
    ("C4 model", ("C4 model", None, None)),
    ("Diátaxis", ("Diátaxis", None, None)),
])
def test_parse_reference_standards_entry_valid(entry, expected):
    assert parse_reference_standards_entry(entry) == expected


@pytest.mark.parametrize("entry", [
    "",
    "   ",
    " arc42",
    "arc42 ",
    "@1.0",
    "arc42@",
    "x@@",
    "x#",
    "y##",
    "arc42#1@2",
    "a@ b",
    "a@b#",
    "#section",
    "arc42#Section 5",
])
def test_parse_reference_standards_entry_invalid(entry):
    assert parse_reference_standards_entry(entry) is None


def test_format_hint_constant():
    assert REFERENCE_STANDARDS_FORMAT_HINT == "<STANDARD>[@<version>][#<section>]"


# --- AC-09 / AC-10 / AC-13 -------------------------------------------------

def test_absent_field_is_optional():
    """AC-09: absent field → no findings."""
    assert _check(_tmpl()) == []


@pytest.mark.parametrize("values", [
    'reference_standards:\n  - "Diátaxis"\n  - "C4 model"\n  - "arc42"\n',
    (
        'reference_standards:\n  - "ISTQB@4.0"\n'
        '  - "IEEE 1012@2016#7"\n  - "ASVS@4.0.3"\n'
    ),
    'reference_standards:\n  - "Some Unknown Standard"\n',
])
def test_valid_entries_pass(values):
    """AC-10: structurally valid entries pass, incl. unknown-but-valid names."""
    assert _check(_tmpl(values)) == []


def test_no_frontmatter_or_yaml_error_yields_no_extra_finding():
    """AC-13: malformed/absent frontmatter → [], no double ERROR."""
    assert _check("no frontmatter here\n") == []
    assert _check("---\nname: t\nreference_standards: [unterminated\n---\n\nBody.\n") == []


# --- AC-11 -----------------------------------------------------------------

@pytest.mark.parametrize("field_yaml,severity,check_id", [
    ("reference_standards: arc42\n", Severity.ERROR, "reference-standards.not-list"),
    ("reference_standards: {}\n", Severity.ERROR, "reference-standards.not-list"),
    ("reference_standards: []\n", Severity.WARNING, "reference-standards.empty"),
    ("reference_standards:\n  - 42\n", Severity.ERROR, "reference-standards.entry-not-string"),
    ('reference_standards:\n  - ""\n', Severity.ERROR, "reference-standards.entry-empty"),
    ('reference_standards:\n  - "  "\n', Severity.ERROR, "reference-standards.entry-empty"),
    ('reference_standards:\n  - "arc42#1@2"\n', Severity.ERROR, "reference-standards.entry-format"),
    ('reference_standards:\n  - "@1.0"\n', Severity.ERROR, "reference-standards.entry-format"),
    ('reference_standards:\n  - "x@@"\n', Severity.ERROR, "reference-standards.entry-format"),
    ('reference_standards:\n  - "y##"\n', Severity.ERROR, "reference-standards.entry-format"),
    ('reference_standards:\n  - "x#"\n', Severity.ERROR, "reference-standards.entry-format"),
    ("reference_standards:\n  - arc42\n  - arc42\n", Severity.WARNING,
     "reference-standards.duplicate"),
])
def test_invalid_entry_matrix(field_yaml, severity, check_id):
    """AC-11: each malformed input yields exactly one finding of the stated kind."""
    findings = _check(_tmpl(field_yaml))
    assert len(findings) == 1, [str(f) for f in findings]
    assert findings[0].severity == severity
    assert findings[0].check == check_id


# --- AC-12: CLI exit-code contract -----------------------------------------

def _write_template(root: Path, field_yaml: str) -> Path:
    path = root / "agents" / "1-generic" / "cli-test.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(_tmpl(field_yaml), encoding="utf-8")
    return path


def _run_cli(file_path: Path, root: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_REPO_ROOT / "scripts" / "consistency-check.py"),
         "--file", str(file_path), "--root", str(root), *extra],
        capture_output=True, text=True, cwd=str(_REPO_ROOT), timeout=120,
    )


def test_cli_file_flag_exit_code(tmp_path):
    """AC-12: ERROR → rc 1; warning-only → rc 0; --strict → rc 1; absent → rc 0."""
    error_file = _write_template(tmp_path, "reference_standards: arc42\n")
    result = _run_cli(error_file, tmp_path)
    assert result.returncode == 1, result.stdout + result.stderr
    assert "reference-standards.not-list" in result.stdout

    warn_file = _write_template(tmp_path, "reference_standards: []\n")
    assert _run_cli(warn_file, tmp_path).returncode == 0
    assert _run_cli(warn_file, tmp_path, "--strict").returncode == 1

    absent_file = _write_template(tmp_path, "")
    assert _run_cli(absent_file, tmp_path).returncode == 0
