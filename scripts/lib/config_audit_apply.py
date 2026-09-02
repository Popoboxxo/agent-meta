"""Line-based remediation for :mod:`config_audit` findings.

Split out of ``config_audit.py`` (which crossed the 600-line module limit,
see ``.claude/skills/conventions`` / CLAUDE.md) -- detection (``audit_config``)
and remediation (``apply_audit``) are separate concerns and the only coupling
between them is the :class:`~config_audit.AuditReport` data shape.

Design constraint: :func:`apply_audit` edits ``project.yaml`` line-by-line
instead of re-dumping via ``yaml.dump`` so hand-written comments survive
untouched. Idempotent: lines already carrying the ``# AUTO-DISABLED`` marker
are skipped on re-runs.
"""
from __future__ import annotations

import re
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from .io import write_atomic

if TYPE_CHECKING:
    from .config_audit import AuditReport

# Marker written into disabled role lines — also used to detect already-disabled
# lines for idempotency.
_AUTO_DISABLED_MARKER = "# AUTO-DISABLED"

# Matches a YAML list item inside the ``roles:`` block, e.g. ``  - developer``.
# Captures leading indentation (group "indent") and the role name (group "role").
_ROLE_LINE_RE = re.compile(r"^(?P<indent>\s*)-\s+(?P<role>[A-Za-z0-9_-]+)\s*$")


def apply_audit(report: AuditReport, project_config_path: Path) -> int:
    """Comment out deprecated role lines in project.yaml (line-based, idempotent).

    Only roles flagged under the ``deprecated_roles`` category are disabled.
    Each matching ``  - <role>`` line is rewritten as::

        # - <role>  # AUTO-DISABLED YYYY-MM-DD: deprecated

    The file is read and written line-by-line so YAML comments are preserved.
    Lines already carrying the ``# AUTO-DISABLED`` marker are skipped, making
    repeated invocations a no-op.

    Args:
        report: The :class:`config_audit.AuditReport` whose deprecated roles
            should be disabled.
        project_config_path: Path to ``.meta-config/project.yaml``.

    Returns:
        The number of lines that were changed.
    """
    deprecated = set(report.deprecated_roles)
    if not deprecated:
        return 0
    if not project_config_path.exists():
        return 0

    text = project_config_path.read_text(encoding="utf-8")
    # Preserve the original line endings split; keepends=True retains "\n".
    lines = text.splitlines(keepends=True)
    today = date.today().isoformat()  # noqa: DTZ011
    changed = 0

    for index, line in enumerate(lines):
        # Idempotency: never touch lines we already disabled.
        if _AUTO_DISABLED_MARKER in line:
            continue
        # Separate the line body from its trailing newline to rebuild cleanly.
        stripped_newline = ""
        body = line
        if body.endswith("\r\n"):
            stripped_newline = "\r\n"
            body = body[:-2]
        elif body.endswith("\n"):
            stripped_newline = "\n"
            body = body[:-1]

        match = _ROLE_LINE_RE.match(body)
        if not match:
            continue
        if match.group("role") not in deprecated:
            continue

        indent = match.group("indent")
        role = match.group("role")
        lines[index] = (
            f"{indent}# - {role}  "
            f"{_AUTO_DISABLED_MARKER} {today}: deprecated{stripped_newline}"
        )
        changed += 1

    if changed:
        write_atomic(project_config_path, "".join(lines))

    return changed
