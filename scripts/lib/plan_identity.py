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

#: Wave-structured task id, e.g. ``W2-0`` / ``W1-10`` -- **pattern text, not a
#: compiled regex**, because both consumers embed it in a larger alternation:
#: the wave-header gate of :data:`TASK_HEADER_RE` (below) and the dep-token
#: alternation of ``spec_plan._DEP_TOKEN_RE``. Single source of the wave id form
#: (IC-07): the two consumers cannot drift apart. WAVE-ID form only -- neither
#: :data:`TASK_ID_RE` nor :func:`normalize_task_id` is affected (K66).
WAVE_ID_PATTERN = r"W[0-9]+-[0-9]+"

# Explicit ``plan-id:`` field in frontmatter or a ``> plan-id:`` header line.
_PLAN_ID_FIELD_RE = re.compile(
    r"(?im)^[ \t]*>?[ \t]*\**plan-id\**:[ \t]*([A-Za-z0-9][A-Za-z0-9._-]*)"
)

# Hyphen-aware plan task header. Group 1 is the raw task id (may contain
# ``-``, ``.`` and ``_``), group 2 is the title. At most one header per line.
TASK_HEADER_RE = re.compile(
    r"(?m)^###[ \t]+"
    # Form (i) -- ``### Task <id>: <title>``, unchanged, so every plan that
    # already uses the classic header keeps parsing exactly as before.
    r"(?:Task[ \t]+"
    # Form (ii) -- ``### <W>-<k>: <title>`` (wave/task headers, e.g.
    # ``### W2-0: ...``). The zero-width lookahead keeps both forms inside a
    # single capture group: group 1 stays the task id and group 2 the title.
    # Group 1 is the group the ledger path reads: ``_task_blocks()``
    # (``plan_ledger.py:76``) and ``parse_task_ledgers()``
    # (``spec_plan.py:127``) use ``group(1)`` alone; the only ``group(2)``
    # consumer is ``spec_plan._parse_plan_tasks()`` (``spec_plan.py:575``,
    # consumed as ``prompt`` at ``spec_plan.py:589``).
    # The gate is BOUNDED, not a bare prefix: right after ``<W>-<k>`` it
    # additionally requires a separator (``:``, em dash, en dash, ``-``) or end
    # of line. A bare prefix let the generic character class swallow trailing
    # garbage -- ``### W2-0abc`` and ``### W2-0_x`` both yielded a task id
    # that :func:`normalize_task_id` passes through unchanged, i.e. a
    # self-standing phantom id nobody can ever address (the very class of bug
    # W2-9 removes). The bounded gate rejects both, and it is also what stops a
    # plain heading such as ``### File Structure`` or ``### L-1 ...`` from
    # being read as a task block.
    rf"|(?={WAVE_ID_PATTERN}(?:[ \t]*(?::|[—–-])|[ \t]*$)))"
    r"([A-Za-z0-9]+(?:[._-][A-Za-z0-9]+)*)"
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
