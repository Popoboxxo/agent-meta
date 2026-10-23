"""Managed-merge decision engine for the opencode v2 config surface.

Pure functions only: this module decides *what* a managed path should become,
it never touches the filesystem, never logs and never resolves providers. The
I/O layer (reading ``opencode.json`` + the state file, applying the result,
writing) lives in ``sync_opencode_v2_managed_keys`` (Task 9) — keeping the
decision table testable row by row without temp dirs.

The table itself is ``SPEC-OPENCODE-V2-SUPPORT-2026-10-22`` §3.2: for one
managed dotted ``path`` ``P`` with target value ``T`` (``target is None`` =
"no longer managed"), current file value ``C`` (``ABSENT`` = the key does not
exist) and state entry ``S[P]``:

| row | condition | action | state afterwards |
|---|---|---|---|
| 1 | ``T``, ``C == ABSENT``, ``P not in S`` | write | ``value=T``, prior ABSENT |
| 2 | ``T``, ``P in S``, ``C == S.value``, ``C != T`` | write | ``value=T``, prior kept |
| 3 | ``T``, ``P not in S``, ``C`` exists, ``C != T`` | keep + WARN | no entry (user value) |
| 3a | ``T``, ``P not in S``, ``C == T`` | noop | ``value=T``, ``prior=T`` |
| 3b | ``T``, ``P in S``, ``C != S.value`` | keep + WARN | unchanged |
| 3c | ``T``, ``P in S``, ``C == ABSENT`` | keep + WARN | unchanged |
| 4 | ``T == None``, ``P in S``, ``C == S.value`` | remove | entry dropped |
| 4a | ``T == None``, ``P in S``, ``C != S.value`` | keep + WARN | entry dropped |
| — | ``T``, ``P in S``, ``C == S.value == T`` | noop | unchanged |

State encoding (single form of this spec): ``{"value": <json>, "prior":
<json|null>, "prior_absent": <bool>}``. ``prior_absent: true`` means the key
did not exist before the first write — ``prior`` is then ``null`` and carries no
meaning. A legitimate JSON ``null`` prior is ``prior: null`` with
``prior_absent: false`` and is restored as ``null`` by row 4; the two cases must
stay distinguishable because ``null`` is a valid value.

Amendment B1 (2026-10-23): the engine is generic over dotted paths. No
auxiliary title-model path is managed here — the C0 spike could not verify such
a target, so it was dropped from the spec; callers must not assume one exists.
"""
from __future__ import annotations

from dataclasses import dataclass

from . import isolation

# State namespaces (spec §3.2) — re-exported from ``isolation``, which owns the
# state file, so the literals have exactly one source of truth. Each writer
# reads/writes only its own namespace (IC-09, no clobbering).
STATE_KEYS_KEY = isolation._STATE_V2_KEYS
STATE_PERMISSIONS_KEY = isolation._STATE_V2_PERMISSIONS
STATE_CLI_KEY = isolation._STATE_V2_CLI
STATE_MCP_KEY = isolation._STATE_V2_MCP


class _Absent:
    """Sentinel: the JSON key does not exist.

    Distinct from ``None`` on purpose — ``null`` is a legitimate JSON value, so
    "missing" and "present but null" must not collapse into one representation.
    Always compare with ``is``; the sentinel is never serialized.
    """

    __slots__ = ()

    def __repr__(self) -> str:
        return "ABSENT"


ABSENT = _Absent()


@dataclass(frozen=True)
class MergeResult:
    """Decision for one managed path.

    ``action`` is one of ``"write"`` (set the path to ``value``), ``"remove"``
    (delete the path when ``value is ABSENT``, else restore ``value``),
    ``"keep"`` (leave the file alone) or ``"noop"`` (nothing to do at all).
    ``value`` is the value the path should end up with — the target value for
    a write, the restored prior / ``ABSENT`` for a removal, and the observed
    file value for a keep/noop. ``state`` is the new state entry, ``None`` when
    the path is no longer tracked; ``warning`` carries the user-facing warning
    text when a user value was preserved.
    """

    action: str
    value: object
    state: dict | None
    warning: str | None


def _warning(path: str) -> str:
    """The canonical warning text for a preserved user value (spec §3.2)."""
    return f"opencode-v2-managed: {path} user value kept"


def _state_entry(value: object, prior: object, prior_absent: bool) -> dict:
    """Build a state entry in the encoded form (``ABSENT`` never leaks out).

    Passing the ``ABSENT`` sentinel as ``prior`` is accepted and encoded as
    ``prior: null`` + ``prior_absent: true`` — the sentinel itself is never
    stored, so every state entry stays JSON-serializable.
    """
    if prior is ABSENT:
        prior_absent = True
    return {
        "value": value,
        "prior": None if prior_absent else prior,
        "prior_absent": prior_absent,
    }


def _normalise_entry(entry: object) -> dict | None:
    """Normalise a stored state entry, or ``None`` when the path is untracked.

    Missing/foreign state degrades to "untracked" rather than raising. A dict
    without ``prior_absent`` is read with the older ``{value, prior}``
    semantics of spec A (``prior is None`` = key was absent), so a partially
    written entry can never be mistaken for "a null prior existed".
    """
    if not isinstance(entry, dict) or "value" not in entry:
        return None
    prior_absent = entry.get("prior_absent")
    if not isinstance(prior_absent, bool):
        prior_absent = entry.get("prior") is None
    return {
        "value": entry["value"],
        "prior": entry.get("prior"),
        "prior_absent": prior_absent,
    }


def _same(left: object, right: object) -> bool:
    """JSON-value equality that keeps ``true``/``1`` and ``3``/``3.0`` apart.

    Plain ``==`` would equate booleans with numbers (Python semantics), which
    would let a user's ``1`` look like agent-meta's ``true`` and turn a "user
    changed the value" case into a silent overwrite. Recursive so the same
    holds for nested objects such as ``providers.<id>``.
    """
    if left is ABSENT or right is ABSENT:
        return left is right
    if isinstance(left, bool) or isinstance(right, bool):
        return isinstance(left, bool) and isinstance(right, bool) and left is right
    if isinstance(left, dict) and isinstance(right, dict):
        if left.keys() != right.keys():
            return False
        return all(_same(left[key], right[key]) for key in left)
    if isinstance(left, list) and isinstance(right, list):
        return len(left) == len(right) and all(_same(a, b) for a, b in zip(left, right))
    return type(left) is type(right) and left == right


def _merge_removal(path: str, current: object, state: dict | None) -> MergeResult:
    """Rows 4/4a: the path is no longer managed."""
    if state is None:
        return MergeResult(action="noop", value=current, state=None, warning=None)
    if current is ABSENT or not _same(current, state["value"]):
        # 4a — the file no longer holds what agent-meta wrote: the user's
        # decision wins, management just ends (no restore, no overwrite).
        return MergeResult(action="keep", value=current, state=None, warning=_warning(path))
    if state["prior_absent"]:
        # 4 — the key was absent before the first write: delete it again.
        return MergeResult(action="remove", value=ABSENT, state=None, warning=None)
    return MergeResult(action="remove", value=state["prior"], state=None, warning=None)


def merge_managed_path(
    path: str,
    target: object | None,
    current: object,
    entry: dict | None,
) -> MergeResult:
    """Decide the merge for one managed path (spec §3.2 decision table).

    ``path`` is the dotted JSON path, used only for the warning text.
    ``target`` is the value agent-meta wants, or ``None`` when the path is no
    longer managed (removal). ``current`` is the value read from the file, or
    ``ABSENT`` when the key does not exist. ``entry`` is this path's state
    entry, or ``None`` when agent-meta never wrote it.
    """
    state = _normalise_entry(entry)

    if target is None:
        return _merge_removal(path, current, state)

    if state is None:
        if current is ABSENT:
            # Row 1 — nothing there yet: write and remember that it was absent.
            return MergeResult(
                action="write",
                value=target,
                state=_state_entry(target, ABSENT, prior_absent=True),
                warning=None,
            )
        if _same(current, target):
            # Row 3a — the user already has the target value: adopt it without
            # writing, and record it as its own prior so a rollback keeps it.
            return MergeResult(
                action="noop",
                value=current,
                state=_state_entry(target, target, prior_absent=False),
                warning=None,
            )
        # Row 3 — an unmanaged user value differs: never overwrite it.
        return MergeResult(
            action="keep", value=current, state=None, warning=_warning(path)
        )

    if current is ABSENT or not _same(current, state["value"]):
        # Rows 3c/3b — the user deleted or changed our value since the last
        # write. Respect that (no re-write) and keep tracking the deviation.
        return MergeResult(
            action="keep", value=current, state=state, warning=_warning(path)
        )

    if _same(current, target):
        # Idempotency — the file already holds the current target value.
        return MergeResult(action="noop", value=current, state=state, warning=None)

    # Row 2 — the file holds exactly what agent-meta wrote: update it, keeping
    # the original prior so a later rollback still restores the user's value.
    return MergeResult(
        action="write",
        value=target,
        state=_state_entry(target, state["prior"], state["prior_absent"]),
        warning=None,
    )
