"""SE-cascade consistency checks (--validate-se, issue #338).

Validates SE cascade artifacts against the #339 conventions (concept:
knowledge/wiki/concepts/se-cascade-optimization-339.md): B1 ADR naming/
lifecycle/REQ<->ADR integrity, B2 REQ frontmatter enums/required keys, B3
taxonomy + version-number-in-filename ban, B4 L2 separation heuristic, B5
review finding-ID format (RVW-YYYY-MM-DD-NNN). SE root: ``se-export.
output_dir`` (default ``docs/se``); projects without artifacts are skipped
gracefully via :func:`has_se_artifacts`. Hard traceability violations
(naming, enums, referential integrity) are ERROR; heuristics and lifecycle
gaps (L2 separation, review coverage) are WARNING.

Leniency policy (ADR checker, B1): this module is a convention boundary,
not an enforcement gate — deliberately lenient where a strict B1 reading
would flag. Known deviations: (1) a missing frontmatter ``adr_id`` passes
(the ADR-NNN filename numbering is authoritative; ``adr_id`` is only
checked for disagreement with the filename when present); (2) a missing
ADR title passes (H1/titles are not validated); (3) ``affected_reqs: []``
or absent passes — an ADR may legitimately affect no requirement; only
dangling references inside ``affected_reqs`` warn.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date as date_type
from pathlib import Path

from .report import Finding, Severity
from ..frontmatter import parse_frontmatter_text, split_frontmatter

DEFAULT_SE_ROOT = "docs/se"

TAXONOMY_DIRS = ("L0", "L1", "L2", "ADR", "VV", "reviews", "reports",
                 "traceability")

#: REQ lifecycle enums (B2, §10). Keys double as the required-key list.
REQ_ENUMS: dict[str, tuple[str, ...]] = {
    "implementation_state": ("not_implemented", "partially_implemented", "implemented"),
    "test_status": ("missing", "partial", "covered"),
    "review_state": ("open", "reviewed", "approved"),
}

ADR_STATUSES = ("proposed", "review", "accepted", "deprecated", "superseded")

ADR_FILENAME_RE = re.compile(r"^ADR-(?P<num>\d{3})_.+\.md$")
ADR_ID_RE = re.compile(r"^ADR-\d{3}$")
REVIEW_ID_RE = re.compile(r"^RVW-\d{4}-\d{2}-\d{2}-\d{3}$")
REQ_FILENAME_RE = re.compile(r"^REQ-.+\.md$")
LEVEL_REQ_FILENAME_RE = re.compile(r"^L\d_.+_Requirements\.md$")
ISO_DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")

VERSION_SUFFIX_RE = re.compile(r"_v\d+")

ALLOWED_REQ_H2 = frozenset({
    "beschreibung", "description", "akzeptanzkriterien", "acceptance criteria",
})

#: Architecture terms for the L2 heuristic (B4) — strong markers only.
#: Interface-registry mentions are excluded on purpose: se-component-
#: requirements output legitimately carries interface-registry contract
#: references (the contract itself lives with se-interface-mgr; REQ files
#: only reference it), so flagging them would be a false positive.
ARCHITECTURE_TERMS = (
    "architecture", "architektur", "deployment", "datenbankschema", "database schema",
    "component diagram", "komponentendiagramm",
)

ROOT_INDEX_FILES = frozenset({"index.md"})


@dataclass
class SEDoc:
    """One scanned markdown artifact inside the SE root."""

    path: Path
    rel: str                # posix path relative to the project root
    fm: dict
    body: str               # markdown body without the frontmatter block
    top: str | None = None  # first path component under the SE root

    @property
    def name(self) -> str:
        return self.path.name

    @property
    def stem(self) -> str:
        return self.path.stem


@dataclass
class SEInventory:
    """Scanned SE root: docs split by artifact kind plus ID registries."""

    root: Path
    root_label: str
    docs: list[SEDoc] = field(default_factory=list)
    reqs: list[SEDoc] = field(default_factory=list)
    adrs: list[SEDoc] = field(default_factory=list)
    reviews: list[SEDoc] = field(default_factory=list)

    @property
    def adr_ids(self) -> set[str]:
        """Valid ADR-NNN ids declared by filename or frontmatter."""
        ids: set[str] = set()
        for doc in self.adrs:
            fm_id = doc.fm.get("adr_id")
            if isinstance(fm_id, str) and ADR_ID_RE.match(fm_id):
                ids.add(fm_id)
            m = ADR_FILENAME_RE.match(doc.name)
            if m:
                ids.add(f"ADR-{m.group('num')}")
        return ids

    @property
    def req_ids(self) -> set[str]:
        """Requirement ids derivable from REQ documents."""
        return {rid for rid in (_req_id(d) for d in self.reqs) if rid}


def _f(severity: Severity, check: str, doc: SEDoc | str, message: str,
       suggestion: str) -> Finding:
    rel = doc if isinstance(doc, str) else doc.rel
    return Finding(severity, check, rel, message, suggestion)


def resolve_se_roots(config: dict | None) -> list[str]:
    """SE roots to scan: ``se-export.output_dir`` or the default ``docs/se``."""
    root = DEFAULT_SE_ROOT
    se_export = (config or {}).get("se-export")
    out = se_export.get("output_dir") if isinstance(se_export, dict) else None
    if isinstance(out, str) and out.strip():
        root = out.strip().strip("/")
    return [root]


def has_se_artifacts(project_root: Path, config: dict | None = None) -> bool:
    """True when at least one markdown artifact exists under an SE root."""
    for root in resolve_se_roots(config):
        base = project_root / root
        if base.is_dir() and any(base.rglob("*.md")):
            return True
    return False


def run_se_cascade_checks(project_root: Path,
                          config: dict | None = None) -> list[Finding]:
    """Run all SE-cascade checks over every existing SE root."""
    findings: list[Finding] = []
    for root_label in resolve_se_roots(config):
        base = project_root / root_label
        if not base.is_dir():
            continue
        inv = _scan_inventory(base, root_label, project_root)
        if not inv.docs:
            continue  # empty SE root — nothing to check here
        findings += check_taxonomy(inv)
        findings += check_req_frontmatter(inv.reqs)
        findings += check_open_adrs(inv)
        findings += check_adr_conventions(inv)
        findings += check_l2_separation(inv.reqs)
        findings += check_review_conventions(inv)
    return findings


def check_taxonomy(inv: SEInventory) -> list[Finding]:
    """Top-level layout must follow the #339 taxonomy; `_vN` names are banned."""
    findings: list[Finding] = []
    for entry in sorted(inv.root.iterdir()):
        if (entry.is_dir() and not entry.name.startswith(".")
                and entry.name not in TAXONOMY_DIRS):
            findings.append(_f(
                Severity.WARNING, "se-cascade.unknown-taxonomy-dir",
                f"{inv.root_label}/{entry.name}",
                f"Unknown top-level directory '{entry.name}' under "
                f"{inv.root_label}/ (allowed: {', '.join(TAXONOMY_DIRS)}).",
                "Move the files into a taxonomy directory (#339 taxonomy, B3).",
            ))
    for doc in inv.docs:
        if VERSION_SUFFIX_RE.search(doc.name):
            findings.append(_f(
                Severity.ERROR, "se-cascade.version-suffix-banned", doc,
                f"Filename '{doc.name}' contains a version suffix (_v<N>) "
                "— versions live in Git, never in filenames (B3).",
                "Rename without the _v<N> suffix; recover history via Git.",
            ))
        elif doc.top is None and doc.name not in ROOT_INDEX_FILES:
            # unknown dirs are already covered by the dir-level finding
            findings.append(_f(
                Severity.WARNING, "se-cascade.file-outside-taxonomy", doc,
                f"File '{doc.name}' sits directly under {inv.root_label}/ "
                "instead of a taxonomy directory.",
                f"Move it into one of: {', '.join(TAXONOMY_DIRS)}.",
            ))
    return findings


def check_req_frontmatter(reqs: list[SEDoc]) -> list[Finding]:
    """REQ files need the B2 lifecycle keys with valid enum values."""
    findings: list[Finding] = []
    for doc in reqs:
        for key, allowed in REQ_ENUMS.items():
            value = doc.fm.get(key)
            if value is None:
                findings.append(_f(
                    Severity.ERROR,
                    "se-cascade.req-frontmatter-missing-required", doc,
                    f"REQ frontmatter is missing required key '{key}' (B2).",
                    f"Add '{key}: <enum value>' — allowed: {', '.join(allowed)}.",
                ))
            elif value not in allowed:
                findings.append(_f(
                    Severity.ERROR, "se-cascade.req-enum-invalid", doc,
                    f"REQ frontmatter '{key}: {value}' is not a valid enum "
                    f"value (B2). Allowed: {', '.join(allowed)}.",
                    f"Set {key} to one of the allowed values.",
                ))
        findings += _check_optional_req_fields(doc)
    return findings


def _is_iso_date(value: object) -> bool:
    """True for ISO-8601 dates — strings 'YYYY-MM-DD' or PyYAML date objects.

    PyYAML auto-parses unquoted ``2026-06-28`` into a ``datetime.date``, so
    both representations must count as valid (otherwise every unquoted date
    in frontmatter would be a false positive).
    """
    return isinstance(value, date_type) or (
        isinstance(value, str) and ISO_DATE_RE.match(value) is not None)


def _check_optional_req_fields(doc: SEDoc) -> list[Finding]:
    """Optional B2 fields, validated when present: review_iteration, last_reviewed."""
    findings: list[Finding] = []
    iteration = doc.fm.get("review_iteration")
    if iteration is not None and (isinstance(iteration, bool)
                                  or not isinstance(iteration, int)
                                  or iteration < 0):
        findings.append(_f(
            Severity.ERROR, "se-cascade.req-review-iteration-invalid", doc,
            f"REQ frontmatter 'review_iteration: {iteration!r}' must be an "
            "integer >= 0 (B2).",
            "Set review_iteration to the monotonic iteration counter.",
        ))
    last_reviewed = doc.fm.get("last_reviewed")
    if last_reviewed is not None and not _is_iso_date(last_reviewed):
        findings.append(_f(
            Severity.WARNING, "se-cascade.req-last-reviewed-format", doc,
            f"REQ frontmatter 'last_reviewed: {last_reviewed!r}' is not an "
            "ISO-8601 date (YYYY-MM-DD).",
            "Use the ISO format, e.g. last_reviewed: 2026-06-28.",
        ))
    return findings


def check_open_adrs(inv: SEInventory) -> list[Finding]:
    """open_adrs must be a list of ADR-NNN ids referencing existing ADRs (B1/B2)."""
    findings: list[Finding] = []
    adr_ids = inv.adr_ids
    for doc in inv.reqs:
        value = doc.fm.get("open_adrs")
        if value is None:
            continue
        entries = value if isinstance(value, list) else [value]
        if not isinstance(value, list):
            findings.append(_f(
                Severity.ERROR, "se-cascade.req-open-adrs-format", doc,
                f"REQ frontmatter 'open_adrs' must be a list, found: "
                f"{value!r} (B2).",
                "Use a YAML list of ADR ids, e.g. open_adrs: [ADR-001].",
            ))
        for entry in entries:
            if not isinstance(entry, str) or not ADR_ID_RE.match(entry):
                findings.append(_f(
                    Severity.ERROR, "se-cascade.req-open-adrs-format", doc,
                    f"REQ 'open_adrs' entry {entry!r} is not a valid ADR id "
                    "(expected ADR-NNN, B2).",
                    "Use the ADR id exactly as named in the ADR directory.",
                ))
            elif entry not in adr_ids:
                findings.append(_f(
                    Severity.ERROR, "se-cascade.open-adr-missing", doc,
                    f"REQ '{_req_id(doc) or doc.stem}' references '{entry}' "
                    f"in open_adrs, but no such ADR exists under "
                    f"{inv.root_label}/ADR/.",
                    "Create the ADR (ADR-NNN_kurztitel.md) or fix the id.",
                ))
    return findings


def check_adr_conventions(inv: SEInventory) -> list[Finding]:
    """ADR files follow ADR-NNN_kurztitel.md with lifecycle frontmatter."""
    findings = _check_adr_duplicate_numbers(inv)
    req_refs, adr_ids = inv.req_ids, inv.adr_ids
    for doc in inv.adrs:
        if not ADR_FILENAME_RE.match(doc.name):
            findings.append(_f(
                Severity.ERROR, "se-cascade.adr-naming", doc,
                f"ADR filename '{doc.name}' violates the naming convention "
                "ADR-NNN_kurztitel.md (B1).",
                "Rename to ADR-<3-digit-number>_<kurztitel>.md and update "
                "open_adrs references.",
            ))
        findings += _check_adr_required_fields(doc)
        findings += _check_adr_id_mismatch(doc)
        findings += _check_adr_superseded_by(doc, adr_ids)
        findings += _check_adr_affected_reqs(doc, req_refs)
    return findings


def _check_adr_duplicate_numbers(inv: SEInventory) -> list[Finding]:
    """ADR numbers must be unique — monotonic growth needs free numbers."""
    seen: dict[str, str] = {}  # number -> name of the first ADR using it
    findings: list[Finding] = []
    for doc in inv.adrs:
        m = ADR_FILENAME_RE.match(doc.name)
        if not m:
            continue
        number = m.group("num")
        if number in seen:
            findings.append(_f(
                Severity.ERROR, "se-cascade.adr-duplicate-number",
                f"{inv.root_label}/{doc.name}",
                f"ADR number {number} is used by both '{seen[number]}' and "
                f"'{doc.name}' (B1: monotonically increasing, unique).",
                "Renumber one of the ADRs and update all open_adrs refs.",
            ))
        else:
            seen[number] = doc.name
    return findings


def _check_adr_required_fields(doc: SEDoc) -> list[Finding]:
    """Required ADR lifecycle fields: status (enum), date (ISO), deciders (list)."""
    findings: list[Finding] = []
    status = doc.fm.get("status")
    if status is None:
        findings.append(_f(
            Severity.ERROR, "se-cascade.adr-status-missing", doc,
            "ADR frontmatter is missing the lifecycle field 'status' (B1).",
            f"Add 'status: <state>' — allowed: {', '.join(ADR_STATUSES)}.",
        ))
    elif status not in ADR_STATUSES:
        findings.append(_f(
            Severity.ERROR, "se-cascade.adr-status-invalid", doc,
            f"ADR 'status: {status!r}' is not a valid lifecycle state (B1).",
            f"Allowed: {', '.join(ADR_STATUSES)}.",
        ))
    date = doc.fm.get("date")
    if date is None:
        findings.append(_f(
            Severity.ERROR, "se-cascade.adr-date-missing", doc,
            "ADR frontmatter is missing the 'date' field (B1).",
            "Add 'date: YYYY-MM-DD'.",
        ))
    elif not _is_iso_date(date):
        findings.append(_f(
            Severity.ERROR, "se-cascade.adr-date-format", doc,
            f"ADR 'date: {date!r}' is not an ISO-8601 date (YYYY-MM-DD).",
            "Use the ISO format, e.g. date: 2026-06-28.",
        ))
    deciders = doc.fm.get("deciders")
    if deciders is None:
        findings.append(_f(
            Severity.ERROR, "se-cascade.adr-deciders-missing", doc,
            "ADR frontmatter is missing the 'deciders' field (B1).",
            "Add a deciders list, e.g. deciders: [se-architect, user].",
        ))
    elif not isinstance(deciders, list):
        findings.append(_f(
            Severity.ERROR, "se-cascade.adr-deciders-invalid", doc,
            f"ADR 'deciders: {deciders!r}' must be a list (B1).",
            "Use a YAML list of agent/user names.",
        ))
    return findings


def _check_adr_id_mismatch(doc: SEDoc) -> list[Finding]:
    """Frontmatter adr_id must agree with the filename numbering (B1)."""
    fm_id = doc.fm.get("adr_id")
    m = ADR_FILENAME_RE.match(doc.name)
    file_id = f"ADR-{m.group('num')}" if m else None
    if file_id and isinstance(fm_id, str) and fm_id != file_id:
        return [_f(
            Severity.ERROR, "se-cascade.adr-id-mismatch", doc,
            f"ADR frontmatter 'adr_id: {fm_id}' disagrees with the filename "
            f"('{doc.name}' implies {file_id}).",
            "Align the frontmatter adr_id with the filename numbering.",
        )]
    return []


def _check_adr_superseded_by(doc: SEDoc, adr_ids: set[str]) -> list[Finding]:
    """superseded_by is required for status: superseded; must be well-formed."""
    value = doc.fm.get("superseded_by")
    if doc.fm.get("status") == "superseded" and value is None:
        return [_f(
            Severity.ERROR, "se-cascade.adr-superseded-by-missing", doc,
            "ADR status is 'superseded' but 'superseded_by' is missing (B1).",
            "Reference the replacing ADR, e.g. superseded_by: ADR-002.",
        )]
    if value is None:
        return []
    if not (isinstance(value, str) and ADR_ID_RE.match(value)):
        return [_f(
            Severity.ERROR, "se-cascade.adr-superseded-by-format", doc,
            f"ADR 'superseded_by: {value!r}' is not a valid ADR id "
            "(expected ADR-NNN).",
            "Reference the replacing ADR by its ADR-NNN id.",
        )]
    if value not in adr_ids:
        return [_f(
            Severity.WARNING, "se-cascade.adr-superseded-target-missing", doc,
            f"ADR 'superseded_by' references '{value}', but no such ADR exists.",
            "Create the ADR or fix the reference.",
        )]
    return []


def _check_adr_affected_reqs(doc: SEDoc, req_refs: set[str]) -> list[Finding]:
    affected = doc.fm.get("affected_reqs")
    if affected is None:
        return []
    if not isinstance(affected, list):
        return [_f(
            Severity.ERROR, "se-cascade.adr-affected-reqs-invalid", doc,
            f"ADR 'affected_reqs: {affected!r}' must be a list of REQ ids (B1).",
            "Use a YAML list, e.g. affected_reqs: [REQ-L1-007].",
        )]
    return [
        _f(Severity.WARNING, "se-cascade.adr-affected-req-missing", doc,
           f"ADR 'affected_reqs' references '{entry}', but no REQ with that "
           "id was found.",
           "Create the REQ or fix the reference.")
        for entry in affected
        if isinstance(entry, str) and entry not in req_refs
    ]


def check_l2_separation(reqs: list[SEDoc]) -> list[Finding]:
    """REQ files carry requirements only — architecture content is a B4 smell."""
    findings: list[Finding] = []
    for doc in reqs:
        bad_sections = _disallowed_h2_sections(doc)
        if bad_sections:
            findings.append(_f(
                Severity.WARNING, "se-cascade.req-disallowed-section", doc,
                f"REQ file contains non-requirement section(s): "
                f"{', '.join(bad_sections)} (B4: only 'Beschreibung' and "
                "'Akzeptanzkriterien' are allowed).",
                "Move architecture/review/traceability content into the "
                "dedicated taxonomy files (ARCH-*, reviews/, traceability/).",
            ))
        matched = {t for t in ARCHITECTURE_TERMS
                   if re.search(rf"\b{re.escape(t)}\b", doc.body.lower())}
        if matched:
            findings.append(_f(
                Severity.WARNING, "se-cascade.req-architecture-terms", doc,
                f"REQ file mentions architecture term(s): "
                f"{', '.join(sorted(matched))} (B4: architecture decisions "
                "belong to se-architect, not into REQ files).",
                "Rephrase as a problem statement or move it into an ADR "
                "(open_adrs).",
            ))
    return findings


def _disallowed_h2_sections(doc: SEDoc) -> list[str]:
    """H2 headers in a REQ body that are not on the B4 whitelist."""
    return [
        m.group(1).strip()
        for line in doc.body.splitlines()
        if (m := re.match(r"^##\s+(.+?)\s*$", line))
        and m.group(1).strip().lower() not in ALLOWED_REQ_H2
    ]


def check_review_conventions(inv: SEInventory) -> list[Finding]:
    """Review files need RVW-YYYY-MM-DD-NNN ids and REQ traceability."""
    findings: list[Finding] = []
    for doc in inv.reviews:
        findings += _check_review_id(doc)
        target = doc.fm.get("target_req")
        if target is not None and not (isinstance(target, str)
                                       and target in inv.req_ids):
            findings.append(_f(
                Severity.WARNING, "se-cascade.review-target-missing", doc,
                f"Review 'target_req: {target!r}' does not reference an "
                "existing REQ.",
                "Create the REQ or fix the reference.",
            ))
    findings += _check_review_coverage(inv.reqs, inv.reviews)
    return findings


def _check_review_id(doc: SEDoc) -> list[Finding]:
    """review_id must exist and match RVW-YYYY-MM-DD-NNN (B5)."""
    fm_id = doc.fm.get("review_id")
    m = re.search(r"RVW-\d{4}-\d{2}-\d{2}-\d{3}", doc.name)
    file_id = m.group(0) if m else None
    if fm_id is None and file_id is None:
        return [_f(
            Severity.ERROR, "se-cascade.review-id-missing", doc,
            "Review file has neither a 'review_id' frontmatter field nor a "
            "RVW-YYYY-MM-DD-NNN filename (B5).",
            "Add 'review_id: RVW-<date>-<NNN>' to the frontmatter and name "
            "the file REVIEW_<YYYY-MM-DD>_<scope>.md (B5 review protocol "
            "convention).",
        )]
    findings: list[Finding] = []
    if fm_id is not None and not (isinstance(fm_id, str)
                                  and REVIEW_ID_RE.match(fm_id)):
        findings.append(_f(
            Severity.ERROR, "se-cascade.review-id-format", doc,
            f"Review 'review_id: {fm_id!r}' does not match "
            "RVW-YYYY-MM-DD-NNN (B5).",
            "Use the format RVW-2026-06-28-001.",
        ))
    if isinstance(fm_id, str) and file_id is not None and fm_id != file_id:
        findings.append(_f(
            Severity.WARNING, "se-cascade.review-id-mismatch", doc,
            f"Review 'review_id: {fm_id}' disagrees with the filename id "
            f"'{file_id}'.",
            "Align the frontmatter review_id with the filename.",
        ))
    return findings


def _check_review_coverage(req_docs: list[SEDoc],
                           reviews: list[SEDoc]) -> list[Finding]:
    """Every review_state: reviewed REQ needs a corresponding review file (B5)."""
    findings: list[Finding] = []
    for doc in req_docs:
        if doc.fm.get("review_state") != "reviewed":
            continue
        req_id = _req_id(doc) or doc.stem
        if not _has_review_for(req_id, doc, reviews):
            findings.append(_f(
                Severity.WARNING, "se-cascade.review-coverage-missing", doc,
                f"REQ '{req_id}' is review_state: reviewed but has no "
                f"corresponding review file under reviews/ (B5).",
                f"Add docs/se/reviews/REVIEW_<YYYY-MM-DD>_<scope>.md with "
                f"review_id (RVW-YYYY-MM-DD-NNN) and target_req: {req_id}.",
            ))
    return findings


def _scan_inventory(root: Path, root_label: str,
                    project_root: Path) -> SEInventory:
    """Walk the SE root and classify every markdown artifact."""
    inv = SEInventory(root=root, root_label=root_label)
    for path in sorted(root.rglob("*.md")):
        rel_parts = path.relative_to(root).parts
        if any(part.startswith(".") for part in rel_parts):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except OSError:
            content = ""
        _, body = split_frontmatter(content)
        doc = SEDoc(
            path=path,
            rel=str(path.relative_to(project_root)).replace("\\", "/"),
            fm=parse_frontmatter_text(content),
            body=body,
            top=rel_parts[0] if len(rel_parts) > 1 else None,
        )
        inv.docs.append(doc)
        if _is_req(doc):
            inv.reqs.append(doc)
        elif _is_adr(doc):
            inv.adrs.append(doc)
        elif _is_review(doc):
            inv.reviews.append(doc)
    return inv


def _is_req(doc: SEDoc) -> bool:
    if doc.fm.get("type") == "REQ" or isinstance(doc.fm.get("req_id"), str):
        return True
    return bool(REQ_FILENAME_RE.match(doc.name)
                or LEVEL_REQ_FILENAME_RE.match(doc.name))


def _is_adr(doc: SEDoc) -> bool:
    return (doc.fm.get("type") == "ADR" or doc.name.startswith("ADR-")
            or doc.top == "ADR")


def _is_review(doc: SEDoc) -> bool:
    return (doc.fm.get("type") == "REVIEW" or doc.name.startswith("RVW-")
            or doc.name.startswith("REVIEW_") or doc.top == "reviews")


def _req_id(doc: SEDoc) -> str | None:
    """Derive the requirement id: frontmatter req_id or filename prefix."""
    fm_id = doc.fm.get("req_id")
    if isinstance(fm_id, str) and fm_id:
        return fm_id
    return doc.stem.split("_")[0] if doc.stem.startswith("REQ-") else None


def _has_review_for(req_id: str, req_doc: SEDoc, reviews: list[SEDoc]) -> bool:
    """True when any review file targets this REQ (frontmatter, name or body)."""
    return any(
        r.fm.get("target_req") == req_id
        or req_id in r.stem
        or (req_id != req_doc.stem and req_id in r.body)
        for r in reviews
    )
