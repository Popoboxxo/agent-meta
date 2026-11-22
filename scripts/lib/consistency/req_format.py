"""REQ-ID format validator for ``--validate`` (issue #1167, Task 20).

The one binding pattern lives here (:data:`REQ_ID_PATTERN`) and is applied
with :func:`re.fullmatch`: ``^REQ-[A-Z][A-Z0-9]*-\\d{2,3}$``
(spec ``SPEC-REQ-ID-FORMAT-1167-2026-11-11`` IC-1; O-H2 decision 22.11).
Exactly one uppercase area segment without ``-``, followed by 2 or 3 digits.
Thus ``REQ-CMD-01`` and ``REQ-COM-123`` are valid while ``REQ-1``,
``REQ-COM-1234`` and the multi-part ``REQ-L2-AT-018`` are not.

Gating has a single source: :func:`lib.dod.resolve_dod`. When
``dod.req-traceability`` is off the check is silent (no findings, no exit-code
change); when it is on every malformed occurrence is a ``Severity.ERROR``
finding with check id ``req-id.format`` (IC-2/IC-3).

Scope is the canonical REQ-ID registry ``docs/REQUIREMENTS.md`` of the
framework and, when distinct, of the synced project. Placeholder prose
(``REQ-xxx``, ``REQ-CMD-xx``) is deliberately not treated as an ID: only
uppercase/digit tokens are extracted before ``fullmatch`` runs.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import List, Optional

from ..dod import resolve_dod
from .report import Finding, Severity

#: Binding REQ-ID form — O-H2 = ``\d{2,3}`` (user decision 22.11.). Byte-identical
#: to the constant in spec IC-1; do not loosen or duplicate elsewhere.
REQ_ID_PATTERN = r"^REQ-[A-Z][A-Z0-9]*-\d{2,3}$"
REQ_ID_RE = re.compile(REQ_ID_PATTERN)

#: Candidate tokens in prose: ``REQ-`` plus uppercase/digit segments. The
#: trailing boundary keeps format placeholders such as ``REQ-xxx`` and
#: ``REQ-CMD-xx`` out of the ``fullmatch`` step (a bare ``REQ-CMD`` prefix of
#: ``REQ-CMD-xx`` must not be reported as a malformed ID).
_REQ_TOKEN_RE = re.compile(r"REQ-[A-Z0-9]+(?:-[A-Z0-9]+)*?(?![A-Za-z0-9_-])")

#: Canonical REQ-ID registry relative to each root.
_REGISTRY_RELPATH = Path("docs") / "REQUIREMENTS.md"

#: Finding check identifier (spec IC-3).
CHECK_ID = "req-id.format"

_SUGGESTION = (
    "Use REQ-<AREA>-<NN>: exactly one uppercase area segment without '-' "
    "followed by 2 or 3 digits (e.g. REQ-CMD-01, REQ-COM-123)."
)


def _traceability_enabled(agent_meta_root: Path, config: Optional[dict]) -> bool:
    """Read the gate from the single DoD source, never a second config key."""
    resolved = resolve_dod(config if isinstance(config, dict) else {}, agent_meta_root)
    return bool(resolved.get("req-traceability", True))


def _read_lines(path: Path) -> List[str]:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []


def _relative(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return path.as_posix()


def _registry_findings(path: Path, root: Path) -> List[Finding]:
    """One ERROR finding per malformed REQ token in the registry."""
    relpath = _relative(path, root)
    findings: List[Finding] = []
    for lineno, line in enumerate(_read_lines(path), start=1):
        for match in _REQ_TOKEN_RE.finditer(line):
            token = match.group(0)
            if REQ_ID_RE.fullmatch(token):
                continue
            findings.append(Finding(
                Severity.ERROR,
                CHECK_ID,
                relpath,
                f"malformed REQ-ID '{token}' on line {lineno}: {line.strip()}",
                _SUGGESTION,
            ))
    return findings


def check_req_ids(
    agent_meta_root: Path,
    project_root: Path,
    config: Optional[dict],
) -> List[Finding]:
    """Return ``req-id.format`` findings for the REQ-ID registry (IC-3).

    Silent (empty list) when ``dod.req-traceability`` is off. Otherwise scans
    each distinct root's ``docs/REQUIREMENTS.md`` and reports every token that
    fails :data:`REQ_ID_RE`. Never raises: this is a read-only check.
    """
    roots = [Path(agent_meta_root), Path(project_root)]
    if not _traceability_enabled(roots[0], config):
        return []

    findings: List[Finding] = []
    seen: set = set()
    for root in roots:
        path = root / _REGISTRY_RELPATH
        try:
            key = path.resolve()
        except OSError:  # pragma: no cover - defensive for unusual mounts
            key = path
        if key in seen or not path.is_file():
            continue
        seen.add(key)
        findings.extend(_registry_findings(path, root))
    return findings
