"""Structure/format check for the ``reference_standards`` agent-frontmatter field.

SPEC-REFERENCE-STANDARDS-2026-09-15 (IC-02). The field is optional and holds a
list of strings in the MVP grammar ``<STANDARD>[@<version>][#<section>]``:

* ``STANDARD``: non-empty, no leading/trailing whitespace, no ``@``/``#``
  delimiter, internal spaces allowed (``"C4 model"``, ``"IEEE 1012"``).
* ``@version`` / ``#section``: optional, each non-empty, without whitespace,
  without further delimiters; the order is fixed (``@`` before ``#``).

No registry is consulted (OQ-5) — any structurally valid name passes. The field
is checked in the template source, not in generated provider files (OQ-7).
"""
from __future__ import annotations

import re
from pathlib import Path

from ..frontmatter import REFERENCE_STANDARDS_FIELD, _parse_frontmatter_yaml
from .report import Finding, Severity

REFERENCE_STANDARDS_FORMAT_HINT: str = "<STANDARD>[@<version>][#<section>]"

# STANDARD is anchored by a non-space/non-delimiter at both ends (internal
# spaces allowed); version/section are optional single tokens without
# whitespace or further delimiters. An empty version/section (``x@``, ``x#``)
# fails the ``+`` of its group and therefore the overall anchor.
_ENTRY_RE = re.compile(
    r"^(?P<standard>[^\s@#](?:[^@#]*[^\s@#])?)"
    r"(?:@(?P<version>[^\s@#]+))?"
    r"(?:#(?P<section>[^\s@#]+))?$"
)


def parse_reference_standards_entry(entry: str) -> tuple[str, str | None, str | None] | None:
    """Parse one entry against the MVP grammar.

    ``('arc42', None, None)`` / ``('ISTQB', '4.0', None)`` /
    ``('IEEE 1012', '2016', '7')``, or ``None`` when the entry does not match.
    Never raises.
    """
    if not isinstance(entry, str):
        return None
    match = _ENTRY_RE.match(entry)
    if match is None:
        return None
    return match.group("standard"), match.group("version"), match.group("section")


def check_reference_standards(
    path: Path,
    content: str,
    agent_meta_root: Path,
    changed_files: set[str] | None,
) -> list[Finding]:
    """Findings for the ``reference_standards`` field of one agent template.

    The field is optional: absent (or explicit ``null``) → no findings. A
    missing/malformed frontmatter block yields no finding here — that stays the
    exclusive domain of ``check_agent_frontmatter`` (no double ERROR). This
    function never raises; ``changed_files`` is accepted for call-signature
    parity with ``check_agent_frontmatter`` and is currently unused.
    """
    findings: list[Finding] = []

    fm = _parse_frontmatter_yaml(content)
    if not isinstance(fm, dict):
        return findings

    value = fm.get(REFERENCE_STANDARDS_FIELD)
    if value is None:
        return findings

    rel = _rel(path, agent_meta_root)

    if not isinstance(value, list):
        findings.append(Finding(
            Severity.ERROR, "reference-standards.not-list", rel,
            f"'{REFERENCE_STANDARDS_FIELD}' must be a YAML list, got: {type(value).__name__}.",
            'Use a YAML list, e.g. ["Diátaxis", "C4 model"]',
        ))
        return findings

    if not value:
        findings.append(Finding(
            Severity.WARNING, "reference-standards.empty", rel,
            f"'{REFERENCE_STANDARDS_FIELD}' is an empty list.",
            "Remove the field or add at least one entry.",
        ))
        return findings

    seen: set[str] = set()
    for entry in value:
        if not isinstance(entry, str):
            findings.append(Finding(
                Severity.ERROR, "reference-standards.entry-not-string", rel,
                f"'{REFERENCE_STANDARDS_FIELD}' entry is not a string: {entry!r}.",
                'Quote the entry: "arc42@1.0"',
            ))
            continue

        trimmed = entry.strip()
        if not trimmed:
            findings.append(Finding(
                Severity.ERROR, "reference-standards.entry-empty", rel,
                f"'{REFERENCE_STANDARDS_FIELD}' contains an empty entry.",
                "Remove the empty entry.",
            ))
            continue

        if parse_reference_standards_entry(entry) is None:
            findings.append(Finding(
                Severity.ERROR, "reference-standards.entry-format", rel,
                f"'{REFERENCE_STANDARDS_FIELD}' entry {entry!r} does not match "
                f"{REFERENCE_STANDARDS_FORMAT_HINT}.",
                f"Use format {REFERENCE_STANDARDS_FORMAT_HINT}",
            ))

        if trimmed in seen:
            findings.append(Finding(
                Severity.WARNING, "reference-standards.duplicate", rel,
                f"'{REFERENCE_STANDARDS_FIELD}' contains a duplicate entry: '{trimmed}'.",
                "Remove the duplicate.",
            ))
        else:
            seen.add(trimmed)

    return findings


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root)).replace("\\", "/")
    except ValueError:
        return str(path)
