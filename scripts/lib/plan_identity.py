"""Stable plan/task identity primitives for the progress/ledger system.

Leaf module (standard library only). The identities produced here are the
shared key between the plan parser, the ledger writer, the checkpoint writer
and the validator, so they must be deterministic -- never random, never
timestamp-based.
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Optional

#: Valid plan id: starts alphanumeric, then alphanumerics, dot, underscore or dash.
PLAN_ID_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

#: Canonical normalized task id, e.g. ``task-3``.
TASK_ID_RE = re.compile(r"^task-[0-9]+$")

# Explicit ``plan-id:`` field in frontmatter or a ``> plan-id:`` header line.
_PLAN_ID_FIELD_RE = re.compile(
    r"(?im)^[ \t]*>?[ \t]*\**plan-id\**:[ \t]*([A-Za-z0-9][A-Za-z0-9._-]*)"
)

# Hyphen-aware plan task header. Group 1 is the raw task id (may contain
# ``-``, ``.`` and ``_``), group 2 is the title. At most one header per line.
TASK_HEADER_RE = re.compile(
    r"(?m)^###[ \t]+Task[ \t]+([A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*)"
    r"[ \t]*(?::|[—–-])?[ \t]*(.*?)[ \t]*$"
)

_SLUG_SEPARATORS_RE = re.compile(r"[^a-z0-9]+")


def _slugify(value: str) -> str:
    """Deterministic lowercase slug: every non ``[a-z0-9]`` run becomes ``-``."""
    return _SLUG_SEPARATORS_RE.sub("-", value.lower()).strip("-")


def derive_plan_id(plan_path: Path, text: Optional[str] = None) -> str:
    """Return a stable plan id for ``plan_path``.

    Precedence: an explicit ``plan-id:`` field in the document text
    (frontmatter or a ``> plan-id:`` header line) when it matches
    :data:`PLAN_ID_RE`; otherwise a deterministic slug of ``plan_path.stem``
    (``[^a-z0-9]+`` -> ``-``, trim, lowercase).

    When ``text`` is ``None`` the file is read; an unreadable file
    (``OSError``) falls back to the stem slug. The function never raises and
    never returns a random or timestamp-based value.
    """
    if text is None:
        try:
            text = plan_path.read_text(encoding="utf-8")
        except OSError:
            text = ""
    match = _PLAN_ID_FIELD_RE.search(text)
    if match is not None and PLAN_ID_RE.fullmatch(match.group(1)):
        return match.group(1)
    return _slugify(plan_path.stem)


def normalize_task_id(raw: str) -> str:
    """Normalize a raw task id.

    ``"3"`` -> ``"task-3"`` and ``"TASK-3"`` -> ``"task-3"``; anything else is
    returned unchanged. Single implementation shared with the plan parser.
    """
    if re.fullmatch(r"[0-9]+", raw):
        return "task-" + raw
    if TASK_ID_RE.fullmatch(raw.lower()):
        return raw.lower()
    return raw


def make_task_ref(plan_id: Optional[str], task_id: str) -> Optional[str]:
    """Build the composite ``<plan_id>#<task_id>`` reference.

    Returns ``None`` when ``plan_id`` is falsy. A ``task_id`` that already
    contains ``#`` is returned unchanged.
    """
    if not plan_id:
        return None
    if "#" in task_id:
        return task_id
    return plan_id + "#" + task_id
