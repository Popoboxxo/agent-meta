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
