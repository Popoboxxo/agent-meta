"""#1335: capability-derived payload-attribution render variables (Task 1).

Variant A (no hook capabilities) and variant B (``hook-agent-id`` only) are
byte-identical to the #1307 contract. Variant C (both capabilities) uses the
exact spec literals and flips ``GIT_PAYLOAD_ATTRIBUTION`` to ``"true"`` —
a pure render derivation, never a new attribution mechanism and no provider
name anywhere in the resolver.

Run: python -m pytest tests/test_git_payload_attribution.py -q
"""
from __future__ import annotations

from pathlib import Path

import scripts.lib.agent_sync as ag
from scripts.lib.agent_sync import _build_provider_vars, _git_sentinel_scope_vars

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Frozen #1307 values (independent of the module under test).
_SCOPE_A = ""
_BASH_RULE_A = (
    "always prefixed with `#agent-meta:agent=git` as the first line "
    "(see workflow step 0)"
)
_SCOPE_B = (
    " Exception: for Bash calls that run only `gh` (no `git` in the call), "
    "do NOT add the sentinel line — it is not needed for `gh`, and the extra "
    "line makes allow rules such as `Bash(gh issue *)` not match. Run such "
    "`gh` calls as their own Bash call; never mix `gh` and `git` in one call. "
    "Every call that runs `git` keeps the sentinel as its first line."
)
_BASH_RULE_B = (
    "`git` calls always prefixed with `#agent-meta:agent=git` as the first "
    "line, `gh`-only calls without it (see workflow step 0)"
)

# Exact spec literals for variant C (SPEC-1335-PAYLOAD-ATTRIBUTION, IC-5).
SCOPE_C = (
    " On providers whose hook payload carries a harness-set agent identity, the `git` role "
    "is taken from that payload — do NOT add a sentinel comment to any Bash call: a "
    "comment-only first line is a separate sub-command and can prevent narrow allow rules "
    "such as `Bash(git status *)` from matching. Destructive-operation, branch and "
    "auto-commit-scope checks still apply."
)
BASH_RULE_C = (
    "`git` and `gh` calls without a sentinel line "
    "(role comes from the hook payload; see workflow step 0)"
)


def _pc(*capabilities: str) -> dict:
    return {"capabilities": list(capabilities)}


BOTH = _pc("hook-agent-id", "hook-role-field")


# --- pure resolver: A/B unchanged, C exact ---------------------------------


def test_variant_a_byte_identical_without_capabilities():
    assert _git_sentinel_scope_vars({}) == {
        "GIT_SENTINEL_SCOPE_BLOCK": _SCOPE_A,
        "GIT_SENTINEL_BASH_RULE": _BASH_RULE_A,
    }


def test_variant_b_byte_identical_with_hook_agent_id_only():
    assert _git_sentinel_scope_vars(_pc("hook-agent-id")) == {
        "GIT_SENTINEL_SCOPE_BLOCK": _SCOPE_B,
        "GIT_SENTINEL_BASH_RULE": _BASH_RULE_B,
    }


def test_variant_c_exact_spec_literals_with_both_capabilities():
    assert _git_sentinel_scope_vars(BOTH) == {
        "GIT_SENTINEL_SCOPE_BLOCK": SCOPE_C,
        "GIT_SENTINEL_BASH_RULE": BASH_RULE_C,
    }


def test_variant_c_reversed_capability_order_is_same():
    assert _git_sentinel_scope_vars(_pc("hook-role-field", "hook-agent-id")) == {
        "GIT_SENTINEL_SCOPE_BLOCK": SCOPE_C,
        "GIT_SENTINEL_BASH_RULE": BASH_RULE_C,
    }


def test_c_literals_live_as_module_constants():
    assert ag._GIT_SENTINEL_SCOPE_WITH_BOTH_CAPS == SCOPE_C
    assert ag._GIT_SENTINEL_BASH_RULE_WITH_BOTH_CAPS == BASH_RULE_C


# --- GIT_PAYLOAD_ATTRIBUTION flag (IC-6) ------------------------------------


def _merged(pc: dict) -> dict:
    return _build_provider_vars(pc, "Claude", {}, _REPO_ROOT, active_set=frozenset())


def test_flag_true_only_with_both_capabilities():
    assert _merged(BOTH)["GIT_PAYLOAD_ATTRIBUTION"] == "true"


def test_flag_false_with_hook_agent_id_only():
    assert _merged(_pc("hook-agent-id"))["GIT_PAYLOAD_ATTRIBUTION"] == "false"


def test_flag_false_with_hook_role_field_only():
    assert _merged(_pc("hook-role-field"))["GIT_PAYLOAD_ATTRIBUTION"] == "false"


def test_flag_false_without_capabilities():
    assert _merged({})["GIT_PAYLOAD_ATTRIBUTION"] == "false"


def test_flag_and_scope_variant_are_consistent():
    merged = _merged(BOTH)
    assert merged["GIT_PAYLOAD_ATTRIBUTION"] == "true"
    assert merged["GIT_SENTINEL_SCOPE_BLOCK"] == SCOPE_C
    assert merged["GIT_SENTINEL_BASH_RULE"] == BASH_RULE_C


# --- registration (IC-8) ----------------------------------------------------


def test_placeholder_is_registered_for_validate():
    from scripts.lib.consistency.placeholders import _BUILTIN_VARS

    assert "GIT_PAYLOAD_ATTRIBUTION" in _BUILTIN_VARS
