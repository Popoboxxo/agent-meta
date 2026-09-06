"""Unit tests for the SE-cascade validator (--validate-se, issue #338).

Covers every check of ``scripts/lib/consistency/se_cascade.py`` (positive +
negative) plus the CLI wiring in ``scripts/sync.py`` and the runner in
``scripts/lib/se_validate.py``. Fixtures build SE cascade artifacts under
pytest ``tmp_path`` — no network, no subprocesses.

Normative references: knowledge/wiki/concepts/se-cascade-optimization-339.md
(findings B1-B5) and schemas/se-requirements.schema.json.

Canonical invocation: ``python3 -m pytest -q tests/test_se_validate.py``
(rootdir-wide pytest is broken by external/ collection errors — invoke the
tests/ directory explicitly).
"""
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

from scripts.lib.consistency.report import Severity
from scripts.lib.consistency.se_cascade import (
    ADR_STATUSES,
    REQ_ENUMS,
    check_adr_conventions,
    check_l2_separation,
    check_open_adrs,
    check_req_frontmatter,
    check_review_conventions,
    check_taxonomy,
    has_se_artifacts,
    resolve_se_roots,
    run_se_cascade_checks,
)

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.log import SyncLog  # noqa: E402  (needs scripts/ on sys.path)
from lib.se_validate import (  # noqa: E402
    MODE,
    _handle_validate_se,
    validate_se_cascade,
)
from sync import _MODE_HANDLERS, _build_arg_parser  # noqa: E402

REQ_CLEAN = """\
---
req_id: REQ-L1-007
implementation_state: not_implemented
test_status: missing
review_state: open
open_adrs: [ADR-001]
review_iteration: 0
---
# User authentication

## Beschreibung

The system shall authenticate users.

## Akzeptanzkriterien

- Login within 2 seconds.
"""


def _adr_clean(adr_id: str = "ADR-001") -> str:
    return (
        "---\n"
        f"adr_id: {adr_id}\n"
        "status: accepted\n"
        "date: 2026-06-28\n"
        "deciders: [se-architect]\n"
        f"affected_reqs: [REQ-L1-007]\n"
        "---\n"
        "# Decision\n"
    )


REVIEW_CLEAN = """\
---
review_id: RVW-2026-06-28-001
target_req: REQ-L1-007
iteration: 1
status: open
---
# Review protocol
"""


# ── fixture helpers ──────────────────────────────────────────────────────────

def _write(root: Path, rel: str, content: str) -> Path:
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")
    return path


def _standard_project(root: Path) -> Path:
    """A fully compliant docs/se fixture: REQ + ADR + review, no findings."""
    _write(root, "docs/se/L1/REQ-L1-007_user-auth.md", REQ_CLEAN)
    _write(root, "docs/se/ADR/ADR-001_user-auth-storage.md", _adr_clean())
    _write(root, "docs/se/reviews/REVIEW_2026-06-28_req-l1-007.md",
           REVIEW_CLEAN)
    return root


def _checks(findings, check: str):
    """All findings with the given check id."""
    return [f for f in findings if f.check == check]


def _doc_by_name(tmp_path: Path, name: str):
    """Scan the standard docs/se root and return one doc by filename."""
    from scripts.lib.consistency.se_cascade import _scan_inventory
    inv = _scan_inventory(tmp_path / "docs" / "se", "docs/se", tmp_path)
    matches = [d for d in inv.docs if d.name == name]
    assert len(matches) == 1, f"expected exactly one {name}, got {matches}"
    return matches[0]


def _single(findings, check: str):
    """Exactly one finding with the given check id (asserts and returns it)."""
    matching = _checks(findings, check)
    assert len(matching) == 1, f"expected 1x {check}, got {matching}"
    return matching[0]


# ═══ resolve_se_roots / has_se_artifacts ═════════════════════════════════════

class TestSeRootResolution:
    def test_default_root_is_docs_se(self):
        assert resolve_se_roots(None) == ["docs/se"]
        assert resolve_se_roots({}) == ["docs/se"]

    def test_output_dir_from_config(self):
        config = {"se-export": {"output_dir": "out/se"}}
        assert resolve_se_roots(config) == ["out/se"]

    def test_ignores_non_string_output_dir(self):
        assert resolve_se_roots({"se-export": {"output_dir": 42}}) == ["docs/se"]

    def test_absent_root_has_no_artifacts(self, tmp_path: Path):
        assert has_se_artifacts(tmp_path) is False

    def test_empty_root_has_no_artifacts(self, tmp_path: Path):
        (tmp_path / "docs" / "se").mkdir(parents=True)
        assert has_se_artifacts(tmp_path) is False

    def test_md_artifact_is_detected(self, tmp_path: Path):
        _standard_project(tmp_path)
        assert has_se_artifacts(tmp_path) is True

    def test_custom_root_is_honored(self, tmp_path: Path):
        _write(tmp_path, "out/se/L1/REQ-L1-001_a.md",
               REQ_CLEAN.replace("REQ-L1-007", "REQ-L1-001"))
        config = {"se-export": {"output_dir": "out/se"}}
        assert has_se_artifacts(tmp_path, config) is True
        assert has_se_artifacts(tmp_path) is False


# ═══ B3: taxonomy ════════════════════════════════════════════════════════════

class TestTaxonomy:
    def _inv(self, tmp_path: Path):
        from scripts.lib.consistency.se_cascade import _scan_inventory
        base = tmp_path / "docs" / "se"
        return _scan_inventory(base, "docs/se", tmp_path)

    def test_clean_layout_no_findings(self, tmp_path: Path):
        _standard_project(tmp_path)
        assert check_taxonomy(self._inv(tmp_path)) == []

    def test_version_suffix_banned(self, tmp_path: Path):
        _write(tmp_path, "docs/se/VV/VV_Strategy_new_needs_v6.md", "# vv\n")
        finding = _single(check_taxonomy(self._inv(tmp_path)),
                          "se-cascade.version-suffix-banned")
        assert finding.severity is Severity.ERROR
        assert "VV_Strategy_new_needs_v6.md" in finding.message

    def test_iter_suffix_is_allowed(self, tmp_path: Path):
        _write(tmp_path, "docs/se/L1/L1_clarifications_iter-3.md", "# c\n")
        findings = check_taxonomy(self._inv(tmp_path))
        assert _checks(findings, "se-cascade.version-suffix-banned") == []

    def test_root_level_file_warns(self, tmp_path: Path):
        _write(tmp_path, "docs/se/loose.md", "# x\n")
        finding = _single(check_taxonomy(self._inv(tmp_path)),
                          "se-cascade.file-outside-taxonomy")
        assert finding.severity is Severity.WARNING

    def test_index_md_is_exempt(self, tmp_path: Path):
        _write(tmp_path, "docs/se/index.md", "# index\n")
        assert check_taxonomy(self._inv(tmp_path)) == []

    def test_reports_dir_is_accepted(self, tmp_path: Path):
        # rules/1-generic/se-cascade-artifact-taxonomy.md lists reports/ as a
        # first-class taxonomy dir — se-critic/se-architect write their
        # status/audit/critic reports there, so it must not warn.
        _write(tmp_path, "docs/se/reports/audit_2026-06-28.md", "# a\n")
        _write(tmp_path, "docs/se/reports/AuthSystem/critic-report.md", "# c\n")
        assert check_taxonomy(self._inv(tmp_path)) == []

    def test_unknown_top_level_dir_warns_once(self, tmp_path: Path):
        _write(tmp_path, "docs/se/archive/old_2026-06-28.md", "# a\n")
        _write(tmp_path, "docs/se/archive/more.md", "# m\n")
        findings = _checks(check_taxonomy(self._inv(tmp_path)),
                           "se-cascade.unknown-taxonomy-dir")
        assert len(findings) == 1  # one per directory, not per file
        assert findings[0].severity is Severity.WARNING
        assert "archive" in findings[0].message


# ═══ B2: REQ frontmatter ═════════════════════════════════════════════════════

class TestReqFrontmatter:
    def _req_doc(self, tmp_path: Path, fm: str, body: str = "# T\n\n## Beschreibung\n"):
        _write(tmp_path, "docs/se/L1/REQ-L1-007_user-auth.md",
               f"---\n{fm}---\n{body}")
        return _doc_by_name(tmp_path, "REQ-L1-007_user-auth.md")

    def test_valid_frontmatter_no_findings(self, tmp_path: Path):
        doc = self._req_doc(tmp_path, REQ_CLEAN.split("---\n")[1])
        assert check_req_frontmatter([doc]) == []

    def test_missing_required_keys(self, tmp_path: Path):
        fm = "req_id: REQ-L1-007\n"
        findings = check_req_frontmatter([self._req_doc(tmp_path, fm)])
        missing = _checks(findings, "se-cascade.req-frontmatter-missing-required")
        assert {f.message for f in missing} == {
            f"REQ frontmatter is missing required key '{key}' (B2)."
            for key in REQ_ENUMS
        }
        assert all(f.severity is Severity.ERROR for f in missing)

    def test_invalid_enum_value(self, tmp_path: Path):
        fm = ("req_id: REQ-L1-007\nimplementation_state: done\n"
              "test_status: missing\nreview_state: open\n")
        finding = _single(check_req_frontmatter([self._req_doc(tmp_path, fm)]),
                          "se-cascade.req-enum-invalid")
        assert finding.severity is Severity.ERROR
        assert "implementation_state: done" in finding.message

    def test_open_adrs_not_a_list(self, tmp_path: Path):
        _write(tmp_path, "docs/se/L1/REQ-L1-007_user-auth.md",
               REQ_CLEAN.replace("open_adrs: [ADR-001]", "open_adrs: ADR-001"))
        findings = check_open_adrs(self._inv(tmp_path))
        bad = _checks(findings, "se-cascade.req-open-adrs-format")
        # The scalar value itself is rejected; "ADR-001" is a well-formed id
        # and therefore produces exactly one not-a-list finding.
        assert len(bad) == 1
        assert all(f.severity is Severity.ERROR for f in bad)

    def test_open_adrs_invalid_entry(self, tmp_path: Path):
        _write(tmp_path, "docs/se/L1/REQ-L1-007_user-auth.md",
               REQ_CLEAN.replace("open_adrs: [ADR-001]",
                                 "open_adrs: [ADR1, ADR-01]"))
        findings = check_open_adrs(self._inv(tmp_path))
        assert len(_checks(findings, "se-cascade.req-open-adrs-format")) == 2

    def test_open_adrs_absent_is_clean(self, tmp_path: Path):
        _write(tmp_path, "docs/se/L1/REQ-L1-007_user-auth.md",
               REQ_CLEAN.replace("open_adrs: [ADR-001]\n", ""))
        assert check_open_adrs(self._inv(tmp_path)) == []

    def _inv(self, tmp_path: Path):
        from scripts.lib.consistency.se_cascade import _scan_inventory
        return _scan_inventory(tmp_path / "docs" / "se", "docs/se", tmp_path)

    def test_review_iteration_invalid(self, tmp_path: Path):
        fm = ("req_id: REQ-L1-007\nimplementation_state: not_implemented\n"
              "test_status: missing\nreview_state: open\nreview_iteration: -1\n")
        finding = _single(check_req_frontmatter([self._req_doc(tmp_path, fm)]),
                          "se-cascade.req-review-iteration-invalid")
        assert finding.severity is Severity.ERROR

    def test_review_iteration_bool_rejected(self, tmp_path: Path):
        fm = ("req_id: REQ-L1-007\nimplementation_state: not_implemented\n"
              "test_status: missing\nreview_state: open\nreview_iteration: true\n")
        finding = _single(check_req_frontmatter([self._req_doc(tmp_path, fm)]),
                          "se-cascade.req-review-iteration-invalid")
        assert finding.severity is Severity.ERROR

    def test_last_reviewed_bad_format_warns(self, tmp_path: Path):
        fm = ("req_id: REQ-L1-007\nimplementation_state: not_implemented\n"
              "test_status: missing\nreview_state: open\nlast_reviewed: soon\n")
        finding = _single(check_req_frontmatter([self._req_doc(tmp_path, fm)]),
                          "se-cascade.req-last-reviewed-format")
        assert finding.severity is Severity.WARNING

    def test_last_reviewed_unquoted_iso_date_is_valid(self, tmp_path: Path):
        # PyYAML parses unquoted dates into datetime.date — must not warn.
        fm = ("req_id: REQ-L1-007\nimplementation_state: not_implemented\n"
              "test_status: missing\nreview_state: open\nlast_reviewed: 2026-06-28\n")
        assert check_req_frontmatter([self._req_doc(tmp_path, fm)]) == []


# ═══ B1/B2: open_adrs referential integrity ══════════════════════════════════

class TestOpenAdrsIntegrity:
    def test_dangling_reference_is_error(self, tmp_path: Path):
        _write(tmp_path, "docs/se/L1/REQ-L1-007_user-auth.md", REQ_CLEAN)
        findings = run_se_cascade_checks(tmp_path)
        finding = _single(findings, "se-cascade.open-adr-missing")
        assert finding.severity is Severity.ERROR
        assert "ADR-001" in finding.message

    def test_existing_reference_is_clean(self, tmp_path: Path):
        _standard_project(tmp_path)
        findings = run_se_cascade_checks(tmp_path)
        assert _checks(findings, "se-cascade.open-adr-missing") == []


# ═══ B1: ADR conventions ═════════════════════════════════════════════════════

class TestAdrConventions:
    def _adr(self, tmp_path: Path, name: str, fm: str) -> Path:
        """Write an ADR file; *fm* is the inner YAML (no fences)."""
        assert not fm.startswith("---"), "pass inner YAML without fences"
        return _write(tmp_path, f"docs/se/ADR/{name}", f"---\n{fm}---\n# D\n")

    def _inv_for(self, tmp_path: Path):
        from scripts.lib.consistency.se_cascade import _scan_inventory
        return _scan_inventory(tmp_path / "docs" / "se", "docs/se", tmp_path)

    def test_valid_adr_no_findings(self, tmp_path: Path):
        _standard_project(tmp_path)
        findings = run_se_cascade_checks(tmp_path)
        assert _checks(findings, "se-cascade.adr-naming") == []
        assert _checks(findings, "se-cascade.adr-status-missing") == []
        assert _checks(findings, "se-cascade.adr-date-missing") == []
        assert _checks(findings, "se-cascade.adr-deciders-missing") == []

    def test_bad_naming_is_error(self, tmp_path: Path):
        self._adr(tmp_path, "ADR-1_database.md", _adr_clean()[4:])
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-naming")
        assert finding.severity is Severity.ERROR

    def test_missing_status(self, tmp_path: Path):
        fm = _adr_clean().split("---\n")[1].replace("status: accepted\n", "")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-status-missing")
        assert finding.severity is Severity.ERROR

    def test_invalid_status(self, tmp_path: Path):
        fm = _adr_clean().split("---\n")[1].replace(
            "status: accepted", "status: done")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-status-invalid")
        assert finding.severity is Severity.ERROR

    def test_missing_date(self, tmp_path: Path):
        fm = _adr_clean().split("---\n")[1].replace("date: 2026-06-28\n", "")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-date-missing")
        assert finding.severity is Severity.ERROR

    def test_bad_date_format(self, tmp_path: Path):
        fm = _adr_clean().split("---\n")[1].replace(
            "date: 2026-06-28", "date: June 2026")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-date-format")
        assert finding.severity is Severity.ERROR

    def test_missing_deciders(self, tmp_path: Path):
        fm = _adr_clean().split("---\n")[1].replace(
            "deciders: [se-architect]\n", "")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-deciders-missing")
        assert finding.severity is Severity.ERROR

    def test_deciders_not_a_list(self, tmp_path: Path):
        fm = _adr_clean().split("---\n")[1].replace(
            "deciders: [se-architect]", "deciders: se-architect")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-deciders-invalid")
        assert finding.severity is Severity.ERROR

    def test_duplicate_adr_number(self, tmp_path: Path):
        _write(tmp_path, "docs/se/ADR/ADR-001_first.md", _adr_clean())
        _write(tmp_path, "docs/se/ADR/ADR-001_second.md", _adr_clean())
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-duplicate-number")
        assert finding.severity is Severity.ERROR
        assert "ADR-001_first.md" in finding.message
        assert "ADR-001_second.md" in finding.message

    def test_adr_id_mismatch_with_filename(self, tmp_path: Path):
        self._adr(tmp_path, "ADR-001_db.md",
                  _adr_clean("ADR-007").split("---\n")[1])
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-id-mismatch")
        assert finding.severity is Severity.ERROR

    def test_superseded_requires_superseded_by(self, tmp_path: Path):
        fm = _adr_clean().split("---\n")[1].replace(
            "status: accepted", "status: superseded")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-superseded-by-missing")
        assert finding.severity is Severity.ERROR

    def test_superseded_by_bad_format(self, tmp_path: Path):
        fm = (_adr_clean().split("---\n")[1].replace(
            "status: accepted", "status: superseded")
            + "superseded_by: ADR2\n")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-superseded-by-format")
        assert finding.severity is Severity.ERROR

    def test_superseded_by_unknown_target_warns(self, tmp_path: Path):
        fm = (_adr_clean().split("---\n")[1].replace(
            "status: accepted", "status: superseded")
            + "superseded_by: ADR-099\n")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-superseded-target-missing")
        assert finding.severity is Severity.WARNING

    def test_superseded_by_existing_target_is_clean(self, tmp_path: Path):
        fm = (_adr_clean().split("---\n")[1].replace(
            "status: accepted", "status: superseded")
            + "superseded_by: ADR-002\n")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        _write(tmp_path, "docs/se/ADR/ADR-002_replacement.md",
               _adr_clean("ADR-002"))
        findings = check_adr_conventions(self._inv_for(tmp_path))
        assert _checks(findings, "se-cascade.adr-superseded-target-missing") == []

    def test_affected_reqs_unknown_warns(self, tmp_path: Path):
        fm = _adr_clean().split("---\n")[1].replace(
            "affected_reqs: [REQ-L1-007]", "affected_reqs: [REQ-L1-999]")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-affected-req-missing")
        assert finding.severity is Severity.WARNING

    def test_affected_reqs_not_a_list(self, tmp_path: Path):
        fm = _adr_clean().split("---\n")[1].replace(
            "affected_reqs: [REQ-L1-007]", "affected_reqs: REQ-L1-007")
        self._adr(tmp_path, "ADR-001_db.md", fm)
        finding = _single(check_adr_conventions(self._inv_for(tmp_path)),
                          "se-cascade.adr-affected-reqs-invalid")
        assert finding.severity is Severity.ERROR

    def test_all_statuses_accepted(self, tmp_path: Path):
        for status in ADR_STATUSES:
            fm = _adr_clean().split("---\n")[1].replace(
                "status: accepted", f"status: {status}")
            self._adr(tmp_path, f"ADR-001_{status}.md", fm)
            findings = check_adr_conventions(self._inv_for(tmp_path))
            assert _checks(findings, "se-cascade.adr-status-invalid") == []
            (tmp_path / "docs" / "se" / "ADR" / f"ADR-001_{status}.md").unlink()


# ═══ B4: L2 separation ═══════════════════════════════════════════════════════

class TestL2Separation:
    def _req(self, tmp_path: Path, body: str):
        _write(tmp_path, "docs/se/L1/REQ-L1-007_user-auth.md",
               "---\n" + REQ_CLEAN.split("---\n")[1] + "---\n" + body)
        return _doc_by_name(tmp_path, "REQ-L1-007_user-auth.md")

    def test_allowed_sections_german(self, tmp_path: Path):
        doc = self._req(tmp_path, "## Beschreibung\n\ntext\n\n## Akzeptanzkriterien\n")
        assert check_l2_separation([doc]) == []

    def test_allowed_sections_english(self, tmp_path: Path):
        doc = self._req(tmp_path, "## Description\n\ntext\n\n## Acceptance Criteria\n")
        assert check_l2_separation([doc]) == []

    def test_foreign_section_warns(self, tmp_path: Path):
        doc = self._req(tmp_path, "## Beschreibung\n\ntext\n\n## Review Findings\n\nx\n")
        finding = _single(check_l2_separation([doc]),
                          "se-cascade.req-disallowed-section")
        assert finding.severity is Severity.WARNING
        assert "Review Findings" in finding.message

    def test_architecture_term_warns(self, tmp_path: Path):
        doc = self._req(tmp_path,
                        "## Beschreibung\n\nThe deployment uses Kubernetes.\n")
        finding = _single(check_l2_separation([doc]),
                          "se-cascade.req-architecture-terms")
        assert finding.severity is Severity.WARNING
        assert "deployment" in finding.message

    def test_interface_registry_reference_is_clean(self, tmp_path: Path):
        # se-component-requirements output legitimately carries interface-
        # registry contract references (the contract itself lives with
        # se-interface-mgr) — both spellings must not trigger B4 findings.
        doc = self._req(
            tmp_path,
            "## Beschreibung\n\nIncoming internal interface from COMP-01-001 "
            "(data: target_temperature_c) — interface registry contract per "
            "Schnittstellen-Registry entry IF-001.\n")
        assert check_l2_separation([doc]) == []

    def test_term_match_is_case_insensitive_and_whole_word(self, tmp_path: Path):
        doc = self._req(tmp_path, "## Beschreibung\n\nThe ARCHITECTURE is TBD.\n")
        findings = check_l2_separation([doc])
        assert "architecture" in _single(
            findings, "se-cascade.req-architecture-terms").message

    def test_non_architecture_text_is_clean(self, tmp_path: Path):
        doc = self._req(tmp_path,
                        "## Beschreibung\n\nUsers log in with a password.\n")
        assert check_l2_separation([doc]) == []


# ═══ B5: reviews ═════════════════════════════════════════════════════════════

class TestReviewConventions:
    def _inv(self, tmp_path: Path):
        from scripts.lib.consistency.se_cascade import _scan_inventory
        return _scan_inventory(tmp_path / "docs" / "se", "docs/se", tmp_path)

    def test_valid_review_no_findings(self, tmp_path: Path):
        _standard_project(tmp_path)
        assert check_review_conventions(self._inv(tmp_path)) == []

    def test_missing_review_id_and_filename_id(self, tmp_path: Path):
        _write(tmp_path, "docs/se/reviews/note.md", "# n\n")
        finding = _single(check_review_conventions(self._inv(tmp_path)),
                          "se-cascade.review-id-missing")
        assert finding.severity is Severity.ERROR

    def test_review_filename_without_id_is_clean(self, tmp_path: Path):
        # REVIEW_<YYYY-MM-DD>_<scope>.md carries no RVW id in the filename —
        # the frontmatter review_id is the sole id source (normative B5).
        _write(tmp_path, "docs/se/reviews/REVIEW_2026-06-28_req-l1-007.md",
               REVIEW_CLEAN)
        findings = check_review_conventions(self._inv(tmp_path))
        assert _checks(findings, "se-cascade.review-id-missing") == []
        assert _checks(findings, "se-cascade.review-id-format") == []
        assert _checks(findings, "se-cascade.review-id-mismatch") == []

    def test_legacy_rvw_filename_id_still_tolerated(self, tmp_path: Path):
        # Legacy files from before the REVIEW_<YYYY-MM-DD>_<scope>.md naming
        # convention may carry the id in an RVW-prefixed filename — the
        # checker keeps tolerating it (no enforcement change for old files).
        _write(tmp_path, "docs/se/reviews/RVW-2026-06-28-002_REQ-L1-007.md",
               "# n\n")
        findings = check_review_conventions(self._inv(tmp_path))
        assert _checks(findings, "se-cascade.review-id-missing") == []
        assert _checks(findings, "se-cascade.review-id-format") == []

    def test_review_id_bad_format(self, tmp_path: Path):
        _write(tmp_path, "docs/se/reviews/REVIEW_2026-06-28_req-l1-007.md",
               "---\nreview_id: RVW-20260628-1\n---\n# n\n")
        finding = _single(check_review_conventions(self._inv(tmp_path)),
                          "se-cascade.review-id-format")
        assert finding.severity is Severity.ERROR

    def test_legacy_rvw_filename_id_mismatch_warns(self, tmp_path: Path):
        # Frontmatter says -06-28-001, legacy RVW filename carries -06-29-003.
        _write(tmp_path, "docs/se/reviews/RVW-2026-06-29-003_REQ-L1-007.md",
               REVIEW_CLEAN)
        finding = _single(check_review_conventions(self._inv(tmp_path)),
                          "se-cascade.review-id-mismatch")
        assert finding.severity is Severity.WARNING

    def test_target_req_unknown_warns(self, tmp_path: Path):
        _write(tmp_path, "docs/se/reviews/REVIEW_2026-06-28_req-l1-007.md",
               REVIEW_CLEAN.replace("target_req: REQ-L1-007",
                                    "target_req: REQ-L1-999"))
        finding = _single(check_review_conventions(self._inv(tmp_path)),
                          "se-cascade.review-target-missing")
        assert finding.severity is Severity.WARNING

    def test_reviewed_req_without_review_file_warns(self, tmp_path: Path):
        _write(tmp_path, "docs/se/L1/REQ-L1-007_user-auth.md",
               REQ_CLEAN.replace("review_state: open",
                                 "review_state: reviewed"))
        finding = _single(check_review_conventions(self._inv(tmp_path)),
                          "se-cascade.review-coverage-missing")
        assert finding.severity is Severity.WARNING

    def test_reviewed_req_with_review_file_is_clean(self, tmp_path: Path):
        _standard_project(tmp_path)
        _write(tmp_path, "docs/se/L1/REQ-L1-007_user-auth.md",
               REQ_CLEAN.replace("review_state: open",
                                 "review_state: reviewed"))
        assert check_review_conventions(self._inv(tmp_path)) == []


# ═══ run_se_cascade_checks (integration) ═════════════════════════════════════

class TestRunSECascadeChecks:
    def test_absent_root_returns_empty(self, tmp_path: Path):
        assert run_se_cascade_checks(tmp_path) == []
        assert run_se_cascade_checks(tmp_path, None) == []

    def test_standard_project_is_clean(self, tmp_path: Path):
        _standard_project(tmp_path)
        assert run_se_cascade_checks(tmp_path) == []

    def test_nested_req_layout_is_supported(self, tmp_path: Path):
        _write(tmp_path,
               "docs/se/L1/AuthServiceSystem/L1_Auth_Requirements.md",
               REQ_CLEAN)
        _write(tmp_path, "docs/se/ADR/ADR-001_storage.md", _adr_clean())
        assert run_se_cascade_checks(tmp_path) == []

    def test_nested_hidden_files_are_ignored(self, tmp_path: Path):
        _write(tmp_path, "docs/se/L1/AuthServiceSystem/.se-state.yaml",
               "current_level: L2\n")
        assert run_se_cascade_checks(tmp_path) == []

    def test_multiple_violations_reported_together(self, tmp_path: Path):
        _write(tmp_path, "docs/se/VV/VV_Strategy_new_needs_v6.md", "# vv\n")
        _write(tmp_path, "docs/se/L1/REQ-L1-007_user-auth.md",
               "req_id: REQ-L1-007\n---\n# broken frontmatter\n")
        findings = run_se_cascade_checks(tmp_path)
        check_ids = {f.check for f in findings}
        assert "se-cascade.version-suffix-banned" in check_ids
        assert "se-cascade.req-frontmatter-missing-required" in check_ids

    def test_custom_root_from_config(self, tmp_path: Path):
        _write(tmp_path, "out/se/VV/VV_bad_v2.md", "# vv\n")
        config = {"se-export": {"output_dir": "out/se"}}
        findings = run_se_cascade_checks(tmp_path, config)
        assert _single(findings, "se-cascade.version-suffix-banned")


# ═══ validate_se_cascade (runner) ════════════════════════════════════════════

class TestValidateSECascade:
    def test_no_artifacts_returns_zero_and_notes(self, tmp_path: Path):
        log = SyncLog()
        code = validate_se_cascade(tmp_path, None, log)
        assert code == 0
        assert any("nothing to check" in line for line in log.infos)

    def test_clean_project_returns_zero(self, tmp_path: Path):
        _standard_project(tmp_path)
        code = validate_se_cascade(tmp_path, None, SyncLog())
        assert code == 0

    def test_findings_return_one(self, tmp_path: Path):
        _write(tmp_path, "docs/se/VV/VV_Strategy_new_needs_v6.md", "# vv\n")
        code = validate_se_cascade(tmp_path, None, SyncLog())
        assert code == 1

    def test_warning_alone_fails_the_gate(self, tmp_path: Path):
        # Task contract: exit non-zero whenever findings exist — warnings count.
        _write(tmp_path, "docs/se/loose.md", "# x\n")
        assert validate_se_cascade(tmp_path, None, SyncLog()) == 1


# ═══ CLI wiring ══════════════════════════════════════════════════════════════

class TestCliWiring:
    def test_parser_accepts_validate_se(self):
        args = _build_arg_parser().parse_args(["--validate-se"])
        assert args.validate_se is True
        assert _build_arg_parser().parse_args([]).validate_se is False

    def test_mode_handler_registered(self):
        routes = {id(handler): handler for _, handler in _MODE_HANDLERS}
        from lib.se_validate import _handle_validate_se as handler
        assert handler in routes.values()

    def test_flag_is_separate_from_validate(self):
        args = _build_arg_parser().parse_args(["--validate-se"])
        assert args.validate is False
        assert args.validate_se is True

    def test_handle_validate_se_exits_zero_when_clean(self, tmp_path: Path,
                                                      monkeypatch):
        _standard_project(tmp_path)
        log = SyncLog()
        ctx = SimpleNamespace(args=SimpleNamespace(), log=log,
                              project_root=tmp_path, config=None, mode=None)
        with pytest.raises(SystemExit) as excinfo:
            _handle_validate_se(ctx)
        assert excinfo.value.code == 0
        assert ctx.mode == MODE

    def test_handle_validate_se_exits_one_on_findings(self, tmp_path: Path):
        _write(tmp_path, "docs/se/VV/VV_Strategy_new_needs_v6.md", "# vv\n")
        ctx = SimpleNamespace(args=SimpleNamespace(), log=SyncLog(),
                              project_root=tmp_path, config=None, mode=None)
        with pytest.raises(SystemExit) as excinfo:
            _handle_validate_se(ctx)
        assert excinfo.value.code == 1

    def test_handle_validate_se_graceful_without_artifacts(self, tmp_path: Path):
        ctx = SimpleNamespace(args=SimpleNamespace(), log=SyncLog(),
                              project_root=tmp_path, config=None, mode=None)
        with pytest.raises(SystemExit) as excinfo:
            _handle_validate_se(ctx)
        assert excinfo.value.code == 0
        assert any("nothing to check" in line for line in ctx.log.infos)
