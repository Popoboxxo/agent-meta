"""Managed-merge decision engine for the opencode v2 surface (Phase B, Task 7).

Pins the decision table of ``SPEC-OPENCODE-V2-SUPPORT-2026-10-22`` §3.2 row by
row (1, 2, 3, 3a, 3b, 3c, 4, 4a + idempotency) and the state encoding
``{value, prior, prior_absent}`` that makes a missing prior (``prior_absent:
true``) distinguishable from a legitimate JSON ``null`` prior.

The engine is a pure function over (target, current file value, state entry):
no file I/O, no logging — Task 9 (``sync_opencode_v2_managed_keys``) owns the
I/O layer and renders the returned ``MergeResult``.

Amendment B1 (2026-10-23): no path for a title/small model is managed by this
engine; the table is generic over dotted paths.

Run: python3 -m pytest tests/test_opencode_v2_config.py -q
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.isolation import (  # noqa: E402  (path set above)
    _STATE_V2_CLI,
    _STATE_V2_KEYS,
    _STATE_V2_MCP,
    _STATE_V2_PERMISSIONS,
)
from lib.opencode_v2_config import (  # noqa: E402  (path set above)
    ABSENT,
    STATE_CLI_KEY,
    STATE_KEYS_KEY,
    STATE_MCP_KEY,
    STATE_PERMISSIONS_KEY,
    MergeResult,
    merge_managed_path,
)

_PATH = "experimental.subagent_depth"


def _entry(value, prior=None, prior_absent=True):
    """A state entry in the canonically encoded form of spec §3.2."""
    return {"value": value, "prior": prior, "prior_absent": prior_absent}


def _warning(path=_PATH):
    return f"opencode-v2-managed: {path} user value kept"


def test_row1_write_when_absent_and_unmanaged():
    """Row 1: T, C == ABSENT, P not in S -> write T, record prior == ABSENT.

    Also pins the module contract behind the write: the four state namespaces are
    re-exported from ``isolation`` (Task 5), never re-declared as literals.
    """
    assert STATE_KEYS_KEY == _STATE_V2_KEYS
    assert STATE_PERMISSIONS_KEY == _STATE_V2_PERMISSIONS
    assert STATE_CLI_KEY == _STATE_V2_CLI
    assert STATE_MCP_KEY == _STATE_V2_MCP
    assert len({STATE_KEYS_KEY, STATE_PERMISSIONS_KEY, STATE_CLI_KEY, STATE_MCP_KEY}) == 4

    result = merge_managed_path(_PATH, 3, ABSENT, None)

    assert isinstance(result, MergeResult)
    assert result.action == "write"
    assert result.value == 3
    assert result.state == {"value": 3, "prior": None, "prior_absent": True}
    assert result.warning is None
    # The recorded state must stay JSON-serializable (no sentinel leaks out).
    assert json.loads(json.dumps(result.state)) == result.state


def test_row2_update_when_value_matches_state():
    """Row 2: P in S, C == S.value, C != T -> update to T, prior unchanged."""
    # First write: prior was ABSENT.
    result = merge_managed_path(_PATH, 4, 3, _entry(3))
    assert result.action == "write"
    assert result.value == 4
    assert result.state == {"value": 4, "prior": None, "prior_absent": True}
    assert result.warning is None

    # Second write: a real user prior is preserved across capability changes.
    result = merge_managed_path(_PATH, 5, 4, _entry(4, prior=7, prior_absent=False))
    assert result.action == "write"
    assert result.value == 5
    assert result.state == {"value": 5, "prior": 7, "prior_absent": False}
    assert result.warning is None


def test_row3_user_value_kept_with_warning():
    """Row 3: P not in S, C exists, C != T -> keep the user value, warn."""
    result = merge_managed_path(_PATH, 3, 7, None)

    assert result.action == "keep"
    assert result.value == 7
    assert result.state is None  # no entry: the value is not agent-meta's
    assert result.warning == "opencode-v2-managed: experimental.subagent_depth user value kept"


def test_row3a_equal_user_value_records_prior_and_no_warning():
    """Row 3a: P not in S, C == T -> write nothing, claim ownership with prior == T."""
    result = merge_managed_path("experimental.todo", True, True, None)

    assert result.action == "noop"
    assert result.value is True
    assert result.state == {"value": True, "prior": True, "prior_absent": False}
    assert result.warning is None
    # JSON shape is exactly the one pinned by AC-B17.
    assert json.loads(json.dumps(result.state)) == {
        "value": True,
        "prior": True,
        "prior_absent": False,
    }


def test_row3b_changed_by_user_keeps_and_warns():
    """Row 3b: P in S, C != S.value -> keep the user edit, state unchanged."""
    entry = _entry(3)
    result = merge_managed_path(_PATH, 5, 9, entry)

    assert result.action == "keep"
    assert result.value == 9
    assert result.state == entry  # ownership record survives untouched
    assert result.warning == _warning()


def test_row3c_deleted_by_user_not_rewritten_and_warns():
    """Row 3c (AC-B19): P in S, C == ABSENT -> respect the deletion, keep state."""
    entry = _entry(3)
    result = merge_managed_path(_PATH, 4, ABSENT, entry)

    assert result.action == "keep"
    assert result.value is ABSENT
    assert result.state == entry
    assert result.warning == _warning()


def test_row4_removal_restores_prior_or_deletes():
    """Row 4: T == None, P in S, C == S.value -> restore prior / delete key."""
    # prior was ABSENT -> the key is removed, state entry dropped.
    removed = merge_managed_path(_PATH, None, 3, _entry(3))
    assert removed.action == "remove"
    assert removed.value is ABSENT
    assert removed.state is None
    assert removed.warning is None

    # prior was a user value -> restore it, state entry dropped.
    restored = merge_managed_path(_PATH, None, 3, _entry(3, prior=7, prior_absent=False))
    assert restored.action == "remove"
    assert restored.value == 7
    assert restored.state is None
    assert restored.warning is None


def test_row4a_removal_keeps_user_changed_value_and_drops_state():
    """Row 4a: T == None, P in S, C != S.value -> keep the user value, drop state."""
    result = merge_managed_path(_PATH, None, 9, _entry(3))

    assert result.action == "keep"
    assert result.value == 9
    assert result.state is None  # management ends either way
    assert result.warning == _warning()


def test_idempotent_noop():
    """Idempotency: P in S, C == S.value == T -> no action, state unchanged."""
    entry = _entry(3)
    result = merge_managed_path(_PATH, 3, 3, entry)

    assert result.action == "noop"
    assert result.value == 3
    assert result.state == entry
    assert result.warning is None

    # Row 4/4a with no managed path at all is a no-op as well.
    untouched = merge_managed_path(_PATH, None, 9, None)
    assert untouched.action == "noop"
    assert untouched.value == 9
    assert untouched.state is None
    assert untouched.warning is None


def test_state_encoding_distinguishes_null_prior_from_absent():
    """``prior: null, prior_absent: false`` restores ``null``; ``true`` deletes."""
    null_prior = merge_managed_path(_PATH, None, "x", _entry("x", prior=None, prior_absent=False))
    assert null_prior.action == "remove"
    assert null_prior.value is None
    assert null_prior.value is not ABSENT

    absent_prior = merge_managed_path(_PATH, None, "x", _entry("x", prior=None, prior_absent=True))
    assert absent_prior.action == "remove"
    assert absent_prior.value is ABSENT
    assert absent_prior.value is not None
