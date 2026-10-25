"""AC-21: the temp-literal consistency check warns but never fails the run.

Normative source: ``docs/specs/2026-10-24-tmp-sink-injection-spec.md``
AC-21 (warning + allowlist), IC-11 (scope and codes), ADR-06 (WARNING, no hard
exit) and ADR-14/Q6 (allowlist entry ``{path, pattern, reason}``).

The check keeps the AC-01 pattern in exactly one place
(``lib.consistency.temp_literals.SYSTEM_TEMP_LITERAL_RE``); Task 15 imports it
from here instead of declaring a second copy.

Run: python3 -m pytest tests/test_consistency_temp_literals.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.consistency.report import Severity, print_json_report, print_report
from lib.consistency.temp_literals import (
    SYSTEM_TEMP_LITERAL_RE,
    check_temp_literals,
)

#: One offending line — the literal sits on line 3 of a probe template.
_LITERAL_LINE = "Run: docker logs c > /tmp/probe.log 2>&1"

#: The six roots the check must cover, one probe file each (IC-11).
_SCOPE_SAMPLES = (
    "agents/1-generic/scope-probe.md",
    "standalone/agents/scope-probe.md",
    "rules/1-generic/scope-probe.md",
    "config/scope-probe.yaml",
    "tests/fixtures/slimming-golden/scope-probe.md",
    "tests/conftest.py",
)

#: A complete allowlist entry (Q6/ADR-14 shape: path, pattern, reason).
_COMPLETE_ENTRY = {
    "path": "agents/1-generic/demo.md",
    "pattern": r"/tmp/probe\.log",
    "reason": "probe fixture: the literal is intentional in this synthetic template",
}


def _write(root: Path, relpath: str, body: str) -> Path:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _write_allowlist(root: Path, entries: list[dict]) -> None:
    path = root / ".meta-config" / "temp-literal-allowlist.yaml"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        yaml.safe_dump({"entries": list(entries)}, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )


def _framework_root(tmp_path: Path) -> Path:
    """A minimal framework tree under the check's scope, with one literal."""
    root = tmp_path / "framework"
    root.mkdir()
    _write(root, "agents/1-generic/demo.md", f"# Demo\n\n{_LITERAL_LINE}\n")
    _write_allowlist(root, [])
    return root


def _literal_findings(findings: list) -> list:
    return [f for f in findings if f.check == "temp-literal.system-temp"]


def _invalid_entry_findings(findings: list) -> list:
    return [f for f in findings if f.check == "temp-literal.allowlist-entry"]


# ---------------------------------------------------------------------------
# AC-21 — warning with file + line, suppressed only by a complete entry
# ---------------------------------------------------------------------------

def test_warning_and_allowlist(tmp_path: Path) -> None:
    """AC-21: ``/tmp/x`` yields a WARNING naming file and line; a complete
    allowlist entry (path, pattern, reason) suppresses it."""
    root = _framework_root(tmp_path)

    findings = check_temp_literals(root, root, {})
    literal = _literal_findings(findings)

    assert len(literal) == 1, f"expected exactly one hit, got: {literal}"
    finding = literal[0]
    assert finding.severity is Severity.WARNING
    assert finding.check == "temp-literal.system-temp"
    assert finding.file == "agents/1-generic/demo.md"
    assert "line 3" in finding.message
    assert "/tmp/probe.log" in finding.message

    # The CLI path must stay green: a WARNING never becomes exit != 0 (ADR-06).
    assert print_report(findings, root, changed_only=False) == 0

    _write_allowlist(root, [_COMPLETE_ENTRY])
    suppressed = check_temp_literals(root, root, {})
    assert _literal_findings(suppressed) == [], (
        "a complete allowlist entry (path, pattern, reason) must suppress the "
        f"hit, got: {_literal_findings(suppressed)}"
    )


# ---------------------------------------------------------------------------
# AC-39 / Q6 / ADR-14 — strict allowlist schema
# ---------------------------------------------------------------------------

def test_allowlist_requires_reason(tmp_path: Path) -> None:
    """AC-39: an entry without ``reason`` suppresses nothing and is itself
    reported as a WARNING of the same check family."""
    root = _framework_root(tmp_path)
    incomplete = {
        "path": _COMPLETE_ENTRY["path"],
        "pattern": _COMPLETE_ENTRY["pattern"],
    }
    _write_allowlist(root, [incomplete])

    findings = check_temp_literals(root, root, {})

    literal = _literal_findings(findings)
    assert len(literal) == 1, (
        "an entry without 'reason' must not suppress the violation, got: "
        f"{literal}"
    )

    invalid = _invalid_entry_findings(findings)
    assert len(invalid) == 1, (
        "the invalid entry must be reported as an additional WARNING, got: "
        f"{invalid}"
    )
    finding = invalid[0]
    assert finding.severity is Severity.WARNING
    assert finding.file == ".meta-config/temp-literal-allowlist.yaml"
    assert "reason" in finding.message
    assert print_report(findings, root, changed_only=False) == 0, (
        "an invalid allowlist entry must never turn the run red (ADR-06)"
    )


def test_allowlist_rejects_expires_field(tmp_path: Path) -> None:
    """AC-39: ``expires`` is not part of the schema — it is treated like any
    other unsupported field (no suppression, extra WARNING)."""
    root = _framework_root(tmp_path)
    entry = dict(_COMPLETE_ENTRY, expires="2026-12-31")
    _write_allowlist(root, [entry])

    findings = check_temp_literals(root, root, {})

    literal = _literal_findings(findings)
    assert len(literal) == 1, (
        "an entry carrying 'expires' must not suppress the violation, got: "
        f"{literal}"
    )

    invalid = _invalid_entry_findings(findings)
    assert len(invalid) == 1, f"expected one invalid-entry warning, got: {invalid}"
    assert invalid[0].severity is Severity.WARNING
    assert "expires" in invalid[0].message
    assert print_report(findings, root, changed_only=False) == 0


def test_allowlist_owner_is_optional_and_changes_nothing(tmp_path: Path) -> None:
    """AC-39: ``owner`` stays optional — a complete entry with ``owner``
    suppresses exactly like the same entry without it."""
    root = _framework_root(tmp_path)
    _write_allowlist(root, [dict(_COMPLETE_ENTRY, owner="developer")])

    findings = check_temp_literals(root, root, {})

    assert _literal_findings(findings) == [], (
        "a complete entry (path, pattern, reason) plus optional owner must "
        f"suppress the hit, got: {_literal_findings(findings)}"
    )
    assert _invalid_entry_findings(findings) == [], (
        "'owner' is a schema field and must not be reported as invalid, got: "
        f"{_invalid_entry_findings(findings)}"
    )


@pytest.mark.parametrize("field", ["expires-at", "review_by", "ticket", "pattern2"])
def test_allowlist_rejects_unknown_fields(tmp_path: Path, field: str) -> None:
    """AC-39: every field outside the whitelist invalidates the entry — it
    suppresses nothing and is reported, exactly like ``expires``."""
    root = _framework_root(tmp_path)
    _write_allowlist(root, [dict(_COMPLETE_ENTRY, **{field: "x"})])

    findings = check_temp_literals(root, root, {})

    assert len(_literal_findings(findings)) == 1, (
        f"unknown field {field!r} must not suppress the violation"
    )
    invalid = _invalid_entry_findings(findings)
    assert len(invalid) == 1, (
        f"unknown field {field!r} must produce exactly one invalid-entry "
        f"warning, got: {invalid}"
    )
    assert field in invalid[0].message


def test_allowlist_entry_index_reported_for_multiple_entries(tmp_path: Path) -> None:
    """The invalid-entry WARNING names the offending entry by 1-based index."""
    root = _framework_root(tmp_path)
    _write_allowlist(root, [
        _COMPLETE_ENTRY,
        {"path": _COMPLETE_ENTRY["path"], "pattern": _COMPLETE_ENTRY["pattern"]},
    ])

    findings = check_temp_literals(root, root, {})

    assert _literal_findings(findings) == [], "entry #1 is complete: no hit"
    invalid = _invalid_entry_findings(findings)
    assert len(invalid) == 1, f"only entry #2 is invalid, got: {invalid}"
    assert "#2" in invalid[0].message
    assert "#1" not in invalid[0].message


# ---------------------------------------------------------------------------
# IC-11 — every one of the six scope roots is scanned
# ---------------------------------------------------------------------------

def test_every_scope_root_is_scanned(tmp_path: Path) -> None:
    """IC-11: each of the six roots is scanned on its own, not just in a
    combined run; text outside the scope stays invisible."""
    root = tmp_path / "framework"
    root.mkdir()
    _write_allowlist(root, [])

    for relpath in _SCOPE_SAMPLES:
        _write(root, relpath, f"# probe\n{_LITERAL_LINE}\n")

    # Negative control: same literal, but outside the declared scope.
    _write(root, "scripts/out-of-scope.py", f"{_LITERAL_LINE}\n")
    _write(root, "README.md", f"{_LITERAL_LINE}\n")

    findings = _literal_findings(check_temp_literals(root, root, {}))
    files = [f.file for f in findings]

    for relpath in _SCOPE_SAMPLES:
        assert relpath in files, (
            f"scope root not scanned (IC-11): {relpath}; got {sorted(files)}"
        )
    assert len(findings) == len(_SCOPE_SAMPLES), (
        "exactly one hit per in-scope probe file expected, got "
        f"{len(findings)}: {sorted(files)}"
    )
    assert "scripts/out-of-scope.py" not in files
    assert "README.md" not in files


# ---------------------------------------------------------------------------
# Fixture completeness + WARNING-only policy
# ---------------------------------------------------------------------------

def test_fixture_entry_carries_path_pattern_reason() -> None:
    """The allowlist fixture used above is a complete Q6/ADR-14 entry."""
    assert set(_COMPLETE_ENTRY) == {"path", "pattern", "reason"}
    for field in ("path", "pattern", "reason"):
        value = _COMPLETE_ENTRY[field]
        assert isinstance(value, str) and value.strip(), f"{field} must be non-empty"


def test_findings_are_warnings_and_never_change_the_exit_code(tmp_path: Path) -> None:
    """ADR-06: every temp-literal finding is a WARNING; the report stays green."""
    root = tmp_path / "framework"
    root.mkdir()
    _write_allowlist(root, [])
    for relpath in _SCOPE_SAMPLES:
        _write(root, relpath, f"# probe\n{_LITERAL_LINE}\n")

    findings = check_temp_literals(root, root, {})

    assert findings, "the synthetic tree must produce findings"
    assert all(f.severity is Severity.WARNING for f in findings), [
        (f.check, f.severity) for f in findings
    ]
    assert not [f for f in findings if f.severity is Severity.ERROR]
    assert print_report(findings, root, changed_only=False) == 0
    assert print_json_report(findings) == 0


def test_pattern_is_exported_for_the_single_source_guard() -> None:
    """Task 15 imports ``SYSTEM_TEMP_LITERAL_RE`` — it must match AC-01."""
    assert SYSTEM_TEMP_LITERAL_RE.search("/tmp/x.log")
    assert SYSTEM_TEMP_LITERAL_RE.search("> /tmp/a")
    assert SYSTEM_TEMP_LITERAL_RE.search("%TEMP%\\x")
    for word in ("Template", "temporary", "attempt", "my/tmp/x", "tmp/"):
        assert not SYSTEM_TEMP_LITERAL_RE.search(word), word
