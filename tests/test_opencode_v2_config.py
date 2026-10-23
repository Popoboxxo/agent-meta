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

Task 8 (B.5) additionally pins the data predicates (``v2_active`` only when
both resolved values match, never raising on missing blocks), the provider/file
ownership criterion (``owns_opencode_surface``, N-M2/AC-B20), the derived state
path, the exact v2 managed key set without ``$schema``/``agents.title.model``
(AC-B3/B10/B11) and the name-based plaintext-secret check (AC-B10/AC-T7).

Run: python3 -m pytest tests/test_opencode_v2_config.py -q
"""
from __future__ import annotations

import copy
import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.dispatch_depth import required_depth_int  # noqa: E402  (path set above)
from lib.isolation import (  # noqa: E402  (path set above)
    _OPENCODE_STATE_FILE,
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
    build_managed_keys,
    find_plaintext_secrets,
    merge_managed_path,
    opencode_state_path,
    owns_opencode_surface,
    project_options,
    v2_active,
)
from lib.providers import (  # noqa: E402  (path set above)
    load_provider_capabilities,
    load_providers_config,
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


# ---------------------------------------------------------------------------
# Task 8 (B.5): activation, provider/file ownership, managed key set, secrets
# ---------------------------------------------------------------------------

_V2_PROVIDER = "Opencode"
_V2_PROJECT_CONFIG = {"provider-options": {_V2_PROVIDER: {"surface-version": "v2"}}}
_PROVIDERS_OBJECT = {
    "opencode-go": {
        "name": "opencode-go",
        "env": ["OC_API_KEY"],
        "settings": {"baseURL": "https://example.invalid/v1"},
    }
}


def _resolved(surface: str = "v1") -> dict:
    """Resolved registry entry for the v1 or v2 surface (real registry data)."""
    project_config = _V2_PROJECT_CONFIG if surface == "v2" else None
    return load_providers_config(_REPO_ROOT, project_config)[_V2_PROVIDER]


def test_v2_active_true_only_with_both_resolved_values():
    """v2 is active only when mechanism AND format are the resolved v2 values."""
    v2 = _resolved("v2")
    assert v2["agent-transform"]["frontmatter-mechanism"] == "opencode-native-v2"
    assert v2["mcp-config"]["format"] == "opencode-json-v2"

    # A single resolved entry and the whole registry are both accepted.
    assert v2_active(v2, _V2_PROVIDER) is True
    assert v2_active({_V2_PROVIDER: v2}, _V2_PROVIDER) is True

    # Only the pair activates — neither value alone is enough.
    wrong_mechanism = copy.deepcopy(v2)
    wrong_mechanism["agent-transform"]["frontmatter-mechanism"] = "opencode-native"
    assert v2_active(wrong_mechanism, _V2_PROVIDER) is False

    wrong_format = copy.deepcopy(v2)
    wrong_format["mcp-config"]["format"] = "opencode-json"
    assert v2_active(wrong_format, _V2_PROVIDER) is False


def test_v2_active_false_for_v1_and_missing_blocks():
    """v1 and malformed/missing blocks are inactive and never raise."""
    v1 = _resolved("v1")
    assert v2_active(v1, _V2_PROVIDER) is False
    assert v2_active({_V2_PROVIDER: v1}, _V2_PROVIDER) is False

    assert v2_active({}, _V2_PROVIDER) is False
    assert v2_active(None, _V2_PROVIDER) is False
    assert v2_active({"mcp-config": {"format": "opencode-json-v2"}}, _V2_PROVIDER) is False
    assert (
        v2_active(
            {"agent-transform": {"frontmatter-mechanism": "opencode-native-v2"}},
            _V2_PROVIDER,
        )
        is False
    )
    assert v2_active({"mcp-config": None, "agent-transform": None}, _V2_PROVIDER) is False


def test_owns_surface_true_for_registry_entry_with_v2_surface_formats_and_committed_file():
    """The real registry entry owns the surface for both resolved surfaces."""
    for surface in ("v1", "v2"):
        pc = _resolved(surface)
        assert owns_opencode_surface(pc, _V2_PROVIDER) is True
        assert owns_opencode_surface({_V2_PROVIDER: pc}, _V2_PROVIDER) is True


def test_owns_surface_false_for_other_formats():
    """A foreign provider (any name) with another MCP format is not an owner."""
    fake = {
        "mcp-config": {
            "committed-file": "fake.json",
            "format": "claude-settings",
            "surface-formats": {"v1": "claude-settings", "v2": "claude-settings"},
        }
    }
    assert owns_opencode_surface(fake, "TotallyFakeProvider") is False
    assert owns_opencode_surface({"TotallyFakeProvider": fake}, "TotallyFakeProvider") is False


def test_owns_surface_false_without_surface_formats():
    """Mammouth-like entry: opencode-json format but no selectable v2 surface."""
    mammouth_like = {
        "mcp-config": {"committed-file": "mammouth.json", "format": "opencode-json"}
    }
    assert owns_opencode_surface(mammouth_like, "Mammouth") is False
    real_mammouth = load_providers_config(_REPO_ROOT)["Mammouth"]
    assert owns_opencode_surface(real_mammouth, "Mammouth") is False


def test_opencode_state_path_derived_from_committed_file(tmp_path):
    """The state path is ``<dir of committed-file>/.opencode/agent-meta-state.json``."""
    pc = _resolved("v2")
    expected = tmp_path / _OPENCODE_STATE_FILE
    assert opencode_state_path(tmp_path, pc) == expected
    # Registry form resolves the surface owner instead of guessing a file.
    assert opencode_state_path(tmp_path, {_V2_PROVIDER: pc}) == expected

    nested = {"mcp-config": {"committed-file": "config/opencode.json"}}
    assert (
        opencode_state_path(tmp_path, nested)
        == tmp_path / "config" / ".opencode" / "agent-meta-state.json"
    )


def test_build_managed_keys_v2_full():
    """Full v2 fixture: exact path/value map, no ``$schema``, no title model."""
    config = {
        "provider-options": {
            _V2_PROVIDER: {
                "experimental-todo": True,
                "providers": copy.deepcopy(_PROVIDERS_OBJECT),
            }
        }
    }
    pc = _resolved("v2")
    assert project_options(config, _V2_PROVIDER) == config["provider-options"][_V2_PROVIDER]

    keys = build_managed_keys(config, _V2_PROVIDER, pc, _REPO_ROOT)

    depth = required_depth_int(
        load_provider_capabilities(_REPO_ROOT).get(_V2_PROVIDER)
    )
    assert keys == {
        "experimental.subagent_depth": depth,
        "experimental.todo": True,
        "providers.opencode-go": _PROVIDERS_OBJECT["opencode-go"],
    }
    assert "$schema" not in keys
    assert "agents.title.model" not in keys
    assert not any(key.startswith("providers.opencode-go.options") for key in keys)
    # Whole registry is accepted as well.
    assert build_managed_keys(config, _V2_PROVIDER, {_V2_PROVIDER: pc}, _REPO_ROOT) == keys


def test_build_managed_keys_without_todo_omits_key():
    """AC-B3: without the option ``experimental.todo`` is not written at all."""
    config = {
        "provider-options": {
            _V2_PROVIDER: {"providers": copy.deepcopy(_PROVIDERS_OBJECT)}
        }
    }
    keys = build_managed_keys(config, _V2_PROVIDER, _resolved("v2"), _REPO_ROOT)
    assert "experimental.todo" not in keys

    # An explicit project depth wins over the capability default.
    explicit = {"provider-options": {_V2_PROVIDER: {"experimental-subagent-depth": 5}}}
    keys = build_managed_keys(explicit, _V2_PROVIDER, _resolved("v2"), _REPO_ROOT)
    assert keys == {"experimental.subagent_depth": 5}


def test_build_managed_keys_empty_when_not_v2():
    """Non-v2 surfaces and non-owner providers manage no keys at all."""
    config = {
        "provider-options": {
            _V2_PROVIDER: {
                "experimental-todo": True,
                "providers": copy.deepcopy(_PROVIDERS_OBJECT),
            }
        }
    }
    assert build_managed_keys(config, _V2_PROVIDER, _resolved("v1"), _REPO_ROOT) == {}

    foreign = {"mcp-config": {"committed-file": "fake.json", "format": "claude-settings"}}
    assert build_managed_keys(config, "TotallyFakeProvider", foreign, _REPO_ROOT) == {}


def test_secret_plaintext_detected():
    """AC-B10/AC-T7: plaintext is detected by key NAME, not by the value."""
    providers_obj = {
        "opencode-go": {"headers": {"X-Api-Key": "EXAMPLE_NOT_A_KEY"}}
    }
    assert find_plaintext_secrets(providers_obj, "providers") == [
        "providers.opencode-go.headers.X-Api-Key"
    ]

    # The value is irrelevant: a different value under a secret-named key is
    # still a finding (the detection is name-based).
    assert find_plaintext_secrets({"x": {"token": "anything"}}, "providers") == [
        "providers.x.token"
    ]
    assert find_plaintext_secrets(
        {"x": {"client_secret": "whatever"}}, "providers"
    ) == ["providers.x.client_secret"]


def test_secret_env_placeholder_ok():
    """``{env:VAR}`` values are valid; malformed placeholders are not."""
    obj = {
        "opencode-go": {
            "env": ["OC_API_KEY"],
            "settings": {"baseURL": "https://example.invalid/v1"},
            "headers": {"X-Api-Key": "{env:OC_API_KEY}"},
        }
    }
    assert find_plaintext_secrets(obj, "providers") == []

    assert find_plaintext_secrets(
        {"x": {"api_key": "{env:1BAD}"}}, "providers"
    ) == ["providers.x.api_key"]
    assert find_plaintext_secrets(
        {"x": {"api_key": "{env:}"}}, "providers"
    ) == ["providers.x.api_key"]


def test_secret_check_walks_nested_oauth():
    """Nested ``oauth`` objects and lists are walked; placeholders are skipped."""
    obj = {
        "x": {
            "oauth": {
                "client_id": "public-id",
                "client_secret": "{env:OC_CLIENT_SECRET}",
                "tokens": [{"access_token": "PLAINTEXT"}],
            }
        }
    }
    assert find_plaintext_secrets(obj, "providers") == [
        "providers.x.oauth.tokens[0].access_token"
    ]
