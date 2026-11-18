"""T14: the artifact-locations consistency check (Issue #1186, Spec §4.6).

Five checks with a fixed severity mapping:

* ``artifact-locations.literal-path``            ERROR
* ``artifact-locations.legacy-write``            WARNING (baseline-based)
* ``artifact-locations.inline-with-path-promise`` ERROR
* ``artifact-locations.missing-dir``             INFO
* ``artifact-locations.alias-divergence``        WARNING

The legacy-write check is deliberately **baseline-based**
(``baseline.legacy_files`` from ``.meta-config/artifact-locations.resolved.json``),
never mtime-based (RVW2-1186-02). A missing baseline fails open (no findings,
one stderr notice). ``unmanaged[]`` targets and directory markers never trigger
any of the five checks (D-8 / RVW-1186-01).

Run:
    export PYTEST_BASETEMP=.tmp/pytest-1186-t14
    python3 -m pytest tests/test_consistency_artifact_locations.py \
        --basetemp="$PYTEST_BASETEMP" -q
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.consistency.artifact_locations import check_artifact_locations
from lib.consistency.report import Severity
from lib.consistency.temp_literals import check_temp_literals

#: The 11 managed directory classes scaffolded by a clean sync (T8).
_DEFAULT_DIRS = (
    "docs/specs", "docs/plans", "docs/concepts", "docs/spikes",
    "docs/reviews", "docs/audits", "docs/analysis", "docs/reports",
    "docs/adr", "docs/traceability", "docs/runbooks",
)

_WRITE_LINE = "**Output file:** docs/specs/foo.md"
_READ_OK = "<!-- artifact-read-ok -->"

#: Minimal framework preset so the T4 resolver sees the framework-owned
#: legacy[]/unmanaged[] lists (the real repo ships the full preset file).
_PRESET = """version: 1
presets:
  default:
    classes: {}
    legacy:
      - "docs/conclusions/"
    unmanaged:
      - ".meta-config/issue-labels-state.json"
      - "docs/api/**"
"""


def _write(root: Path, relpath: str, body: str) -> Path:
    path = root / relpath
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")
    return path


def _framework(tmp_path: Path, templates: dict[str, str] | None = None) -> Path:
    """A minimal framework tree with synthetic role templates."""
    root = tmp_path / "framework"
    root.mkdir()
    _write(root, "config/artifact-locations-presets.yaml", _PRESET)
    for relpath, body in (templates or {}).items():
        _write(root, relpath, body)
    return root


def _project(
    tmp_path: Path,
    *,
    baseline: list[str] | None = None,
    with_baseline: bool = True,
    extra_files: dict[str, str] | None = None,
    legacy_markers: bool = False,
) -> Path:
    """A synced-looking project: class dirs + markers, optional baseline data."""
    root = tmp_path / "project"
    for rel in _DEFAULT_DIRS:
        (root / rel).mkdir(parents=True, exist_ok=True)
        (root / rel / ".gitkeep").write_text("", encoding="utf-8")
    if legacy_markers:
        target = root / "docs" / "conclusions"
        target.mkdir(parents=True, exist_ok=True)
        (target / ".gitkeep").write_text("", encoding="utf-8")
    if with_baseline:
        payload = {
            "schema_version": "1",
            "baseline": {
                "generated_at": "2026-11-17T00:00:00Z",
                "legacy_files": list(baseline or []),
            },
        }
        _write(
            root,
            ".meta-config/artifact-locations.resolved.json",
            json.dumps(payload),
        )
    for relpath, body in (extra_files or {}).items():
        _write(root, relpath, body)
    return root


def _by_check(findings: list, check: str) -> list:
    return [f for f in findings if f.check == check]


# ---------------------------------------------------------------------------
# literal-path (ERROR)
# ---------------------------------------------------------------------------

def test_literal_path_in_write_position_is_violation(tmp_path: Path) -> None:
    """A class-path literal in a write line yields an ERROR with file + line."""
    framework = _framework(tmp_path, {
        "agents/1-generic/documenter.md": f"# Doc\n\n{_WRITE_LINE}\n",
    })
    project = _project(tmp_path)

    findings = _by_check(
        check_artifact_locations(framework, project, {}),
        "artifact-locations.literal-path",
    )

    assert len(findings) == 1, findings
    finding = findings[0]
    assert finding.severity == Severity.ERROR
    assert "documenter.md" in finding.file
    assert "line 3" in finding.message


def test_read_ok_marker_exempts_scan_line(tmp_path: Path) -> None:
    """A marked read/scan line is exempt; the same line unmarked is a finding."""
    framework = _framework(tmp_path, {
        "agents/1-generic/reader.md": (
            f"Scan `docs/adr/` here {_READ_OK}\n"
            "**Output file:** docs/adr/decision.md\n"
        ),
    })
    project = _project(tmp_path)

    findings = _by_check(
        check_artifact_locations(framework, project, {}),
        "artifact-locations.literal-path",
    )

    assert len(findings) == 1, findings
    assert "line 2" in findings[0].message


def test_read_ok_ratchet_does_not_grow(tmp_path: Path) -> None:
    """The read-ok marker set is a shrinking ratchet starting at exactly two."""
    project = _project(tmp_path)
    base = "".join(f"- scan `docs/adr/` {_READ_OK}\n" for _ in range(2))
    framework = _framework(tmp_path, {"agents/1-generic/reader.md": base})

    assert _by_check(
        check_artifact_locations(framework, project, {}),
        "artifact-locations.literal-path",
    ) == []

    grown = framework
    _write(
        grown,
        "agents/1-generic/reader.md",
        base + f"- scan `docs/api/` {_READ_OK}\n",
    )
    assert _by_check(
        check_artifact_locations(grown, project, {}),
        "artifact-locations.literal-path",
    ), "a third marker line must be reported (ratchet)"

    # Avoid tmp_path name collision with the next test's fixtures.
    del tmp_path


def test_literal_path_ignores_escaped_reference_agent(tmp_path: Path) -> None:
    """Escapes inside _reference-agent.md do not trigger literal-path."""
    framework = _framework(tmp_path, {
        "agents/1-generic/_reference-agent.md": _WRITE_LINE + "\n",
        "agents/1-generic/normal.md": _WRITE_LINE + "\n",
    })
    project = _project(tmp_path)

    findings = _by_check(
        check_artifact_locations(framework, project, {}),
        "artifact-locations.literal-path",
    )

    assert len(findings) == 1, findings
    assert "normal.md" in findings[0].file


# ---------------------------------------------------------------------------
# legacy-write (WARNING, baseline-based)
# ---------------------------------------------------------------------------

def test_legacy_write_is_warning_reported_once(tmp_path: Path) -> None:
    """A legacy-tree artifact absent from the baseline yields ONE WARNING."""
    project = _project(
        tmp_path,
        baseline=[],
        extra_files={"docs/conclusions/new-note.md": "new content\n"},
    )
    framework = _framework(tmp_path)

    findings = _by_check(
        check_artifact_locations(framework, project, {}),
        "artifact-locations.legacy-write",
    )

    assert len(findings) == 1, findings
    assert findings[0].severity == Severity.WARNING
    assert "docs/conclusions/new-note.md" in findings[0].message


def test_legacy_write_uses_baseline_not_mtime(tmp_path: Path) -> None:
    """Baseline membership decides, not mtime (RVW2-1186-02)."""
    project = _project(
        tmp_path,
        baseline=["docs/conclusions/known.md"],
        extra_files={
            "docs/conclusions/known.md": "old but in baseline\n",
            "docs/conclusions/unknown.md": "new, not in baseline\n",
        },
    )
    # The known file is even older than the unknown one — mtime must not matter.
    os.utime(project / "docs/conclusions/known.md", (1, 1))
    os.utime(project / "docs/conclusions/unknown.md", (2_000_000_000, 2_000_000_000))

    findings = _by_check(
        check_artifact_locations(_framework(tmp_path), project, {}),
        "artifact-locations.legacy-write",
    )

    assert len(findings) == 1, findings
    assert findings[0].file == "docs/conclusions/unknown.md"
    assert "not in the sync baseline" in findings[0].message
    assert all(f.file != "docs/conclusions/known.md" for f in findings)


def test_baseline_missing_fails_open(
    tmp_path: Path, capsys: pytest.CaptureFixture[str]
) -> None:
    """No resolved.json / no baseline key ⇒ 0 findings + one stderr notice."""
    project = _project(
        tmp_path,
        with_baseline=False,
        extra_files={"docs/conclusions/orphan.md": "content\n"},
    )

    findings = check_artifact_locations(_framework(tmp_path), project, {})

    assert findings == []
    err = capsys.readouterr().err.strip().splitlines()
    assert len(err) == 1, err
    assert "baseline" in err[0].lower()


def test_unmanaged_is_never_reported(tmp_path: Path) -> None:
    """unmanaged[] paths trigger none of the five checks (D-8)."""
    project = _project(tmp_path, extra_files={
        ".meta-config/issue-labels-state.json": "{}\n",
        "docs/api/x.md": "docs\n",
    })
    framework = _framework(tmp_path, {
        "agents/1-generic/reader.md": "**Output file:** docs/api/x.md\n",
    })

    findings = check_artifact_locations(framework, project, {})

    assert findings == [], findings


def test_legacy_marker_files_are_never_reported(tmp_path: Path) -> None:
    """A .gitkeep in a legacy tree is exempt; a .md artifact is reported."""
    project = _project(
        tmp_path,
        baseline=[],
        legacy_markers=True,
        extra_files={"docs/conclusions/note.md": "artifact\n"},
    )

    findings = _by_check(
        check_artifact_locations(_framework(tmp_path), project, {}),
        "artifact-locations.legacy-write",
    )

    assert len(findings) == 1, findings
    assert "note.md" in findings[0].message
    assert ".gitkeep" not in findings[0].message


def test_clean_repo_sync_produces_no_legacy_write(tmp_path: Path) -> None:
    """A freshly scaffolded project (all class dirs + markers) has 0 findings."""
    project = _project(tmp_path, baseline=[], legacy_markers=True)

    findings = _by_check(
        check_artifact_locations(_framework(tmp_path), project, {}),
        "artifact-locations.legacy-write",
    )

    assert findings == [], findings


def test_legacy_markers_produce_no_legacy_write(tmp_path: Path) -> None:
    """The docs/conclusions marker from T8 never becomes a legacy-write hit."""
    project = _project(tmp_path, baseline=[], legacy_markers=True)

    findings = _by_check(
        check_artifact_locations(_framework(tmp_path), project, {}),
        "artifact-locations.legacy-write",
    )

    assert findings == [], findings
    assert (project / "docs/conclusions/.gitkeep").exists()


# ---------------------------------------------------------------------------
# inline-with-path-promise / missing-dir / alias-divergence
# ---------------------------------------------------------------------------

def test_inline_with_path_promise_is_violation(tmp_path: Path) -> None:
    """inline mode + an output-file promise in a template is an ERROR."""
    framework = _framework(tmp_path, {
        "agents/1-generic/writer.md": "**Output file:** docs/specs/foo.md\n",
    })
    project = _project(tmp_path)
    config = {
        "artifact-locations": {"classes": {"specs": {"mode": "inline"}}},
    }

    findings = _by_check(
        check_artifact_locations(framework, project, config),
        "artifact-locations.inline-with-path-promise",
    )

    assert len(findings) == 1, findings
    assert findings[0].severity == Severity.ERROR
    assert "specs" in findings[0].message


def test_missing_dir_is_info(tmp_path: Path) -> None:
    """A files-mode class whose directory is absent yields an INFO finding."""
    project = _project(tmp_path)
    config = {
        "artifact-locations": {
            "classes": {"specs": {"path": "docs/specs-custom", "mode": "files"}},
        },
    }

    findings = _by_check(
        check_artifact_locations(_framework(tmp_path), project, config),
        "artifact-locations.missing-dir",
    )

    assert len(findings) == 1, findings
    assert findings[0].severity == Severity.INFO
    assert "docs/specs-custom" in findings[0].message


def test_alias_divergence_is_warning(tmp_path: Path) -> None:
    """progress.dir diverging from state.subdirs.progress is a WARNING."""
    config = {
        "progress": {"dir": "custom-progress"},
        "artifact-locations": {
            "classes": {"state": {"subdirs": {"progress": "other-progress"}}},
        },
    }

    findings = _by_check(
        check_artifact_locations(_framework(tmp_path), _project(tmp_path), config),
        "artifact-locations.alias-divergence",
    )

    assert len(findings) == 1, findings
    assert findings[0].severity == Severity.WARNING
    assert "progress" in findings[0].message


# ---------------------------------------------------------------------------
# cross-cutting
# ---------------------------------------------------------------------------

def test_disabled_matrix_is_silent(tmp_path: Path) -> None:
    """enabled: false silences all five checks (Issue-Auflage)."""
    framework = _framework(tmp_path, {
        "agents/1-generic/writer.md": "**Output file:** docs/specs/foo.md\n",
    })
    project = _project(
        tmp_path,
        with_baseline=False,
        extra_files={"docs/conclusions/orphan.md": "artifact\n"},
    )
    config = {
        "progress": {"dir": "a"},
        "artifact-locations": {
            "enabled": False,
            "classes": {
                "specs": {"path": "docs/specs-custom", "mode": "inline"},
                "state": {"subdirs": {"progress": "b"}},
            },
        },
    }

    findings = check_artifact_locations(framework, project, config)

    assert findings == [], findings


def test_abgrenzung_temp_literals(tmp_path: Path) -> None:
    """/tmp/x stays with temp-literal.system-temp, not literal-path."""
    framework = _framework(tmp_path, {
        "agents/1-generic/writer.md": "**Output file:** /tmp/foo.md\n",
    })
    project = _project(tmp_path)

    findings = check_artifact_locations(framework, project, {})

    assert _by_check(findings, "artifact-locations.literal-path") == []
    temp_findings = [
        f for f in check_temp_literals(framework, framework, {})
        if f.check == "temp-literal.system-temp"
    ]
    assert temp_findings, "temp_literals must still own the /tmp literal"


def test_project_docs_files_are_not_violations(tmp_path: Path) -> None:
    """docs/issue-labels.md is a valid project-docs target, not a literal."""
    framework = _framework(tmp_path, {
        "agents/1-generic/writer.md": "**Output file:** docs/issue-labels.md\n",
    })
    project = _project(
        tmp_path,
        extra_files={"docs/issue-labels.md": "labels\n"},
    )

    findings = check_artifact_locations(framework, project, {})

    assert _by_check(findings, "artifact-locations.literal-path") == []
    assert _by_check(findings, "artifact-locations.missing-dir") == []


def test_registered_in_consistency_check() -> None:
    """check_artifact_locations is imported and called in consistency-check.py."""
    import ast

    source = (_REPO_ROOT / "scripts/consistency-check.py").read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported = any(
        isinstance(node, ast.ImportFrom)
        and node.module == "lib.consistency.artifact_locations"
        and any(alias.name == "check_artifact_locations" for alias in node.names)
        for node in ast.walk(tree)
    )
    called = any(
        isinstance(node, ast.Call)
        and isinstance(node.func, ast.Name)
        and node.func.id == "check_artifact_locations"
        for node in ast.walk(tree)
    )

    assert imported, "missing import of check_artifact_locations"
    assert called, "missing call of check_artifact_locations in run_checks"
