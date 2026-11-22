"""Description-only lint for agent templates (PR 6.1 / H5, rubric R1 + E-29).

Pure, stdlib-only helpers. The only contract enforced here is the frontmatter
``description`` scalar of an agent template:

* R1 — at most :data:`MAX_DESCRIPTION_LENGTH` characters (plan §4 :95, §5 :119,
  Batch 1 Task 2.3).
* E-29 — no ``Issue #N`` provenance inside the prompt description; issue
  numbers belong in HTML comments or the CHANGELOG (rubric R9).

Providers are data (caller-supplied text/path), never named in branches.
"""
from __future__ import annotations

import re
from pathlib import Path

MAX_DESCRIPTION_LENGTH = 160

_DESCRIPTION_RE = re.compile(r"^description:\s*(.*)$", re.MULTILINE)
_ISSUE_RE = re.compile(r"\b[Ii]ssue\s*#\s*\d+\b")


def extract_frontmatter(text: str) -> str:
    """Return the leading YAML frontmatter block, or an empty string."""
    lines = text.splitlines()
    if not lines or lines[0].strip() != "---":
        return ""
    for index in range(1, len(lines)):
        if lines[index].strip() == "---":
            return "\n".join(lines[1:index])
    return ""


def extract_description(text: str) -> str | None:
    """Return the unquoted description scalar, or ``None`` when absent."""
    match = _DESCRIPTION_RE.search(extract_frontmatter(text))
    if match is None:
        return None
    value = match.group(1).strip()
    if len(value) >= 2 and value[0] == value[-1] and value[0] in "\"'":
        value = value[1:-1]
    return value


def lint_description(text: str, path: str = "") -> list[str]:
    """Return zero or more findings for the description in *text*.

    Findings are plain strings so callers can render them without importing
    any project-specific finding type.
    """
    prefix = f"{path}: " if path else ""
    description = extract_description(text)
    if description is None:
        return [f"{prefix}missing frontmatter description"]
    findings: list[str] = []
    length = len(description)
    if length > MAX_DESCRIPTION_LENGTH:
        findings.append(
            f"{prefix}description has {length} chars (max {MAX_DESCRIPTION_LENGTH})"
        )
    issue = _ISSUE_RE.search(description)
    if issue is not None:
        findings.append(f"{prefix}issue reference in description: {issue.group(0)!r}")
    return findings


def lint_template_files(directory: Path, ext: str = ".md") -> dict[str, list[str]]:
    """Lint every role template ``*<ext>`` directly inside *directory*.

    Files starting with ``_`` (README/reference helpers) are not agent roles
    and carry no frontmatter description, so they are excluded.
    """
    if not directory.is_dir():
        return {}
    return {
        path.name: lint_description(path.read_text(encoding="utf-8"), path.name)
        for path in sorted(directory.iterdir())
        if path.is_file()
        and path.name.endswith(ext)
        and not path.name.startswith("_")
    }
