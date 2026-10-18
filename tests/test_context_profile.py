"""Unit tests for Context-Profile resolution (SPEC-CONTEXT-PROFILES-2026-10-11).

Plan: docs/plans/2026-10-17-context-profiles-phase2-plan.md, Task 2a.1.
Covers IC-02: precedence matrix (explicit > provider-override > profile >
default), ``compact`` implies ``context_file.mode: compact``, the shared-file
rule (any ``full`` sharer ⇒ ``full``), provider variables and the unknown-value
error path.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.context_profile import (
    ResolvedContextProfile,
    context_profile_provider_variables,
    context_profile_variables,
    resolve_context_profile,
    resolve_shared_file_profile,
)


def _config(**extra):
    base = {
        "project": {"name": "t", "prefix": "t", "short": "t"},
        "ai-providers": ["Claude", "Opencode"],
    }
    base.update(extra)
    return base


# --- precedence matrix -------------------------------------------------


def test_default_without_keys_is_full():
    resolved = resolve_context_profile(_config(), "Claude")
    assert resolved.profile == "full"
    assert resolved.context_file_mode == "full"
    assert resolved.rules_preset == "default"
    assert resolved.sources["profile"] == "default"
    assert resolved.sources["context_file_mode"] == "default"
    assert resolved.sources["rules_preset"] == "default"


def test_global_profile_compact_implies_mode_compact():
    resolved = resolve_context_profile(_config(**{"context-profile": "compact"}), "Claude")
    assert resolved.profile == "compact"
    assert resolved.context_file_mode == "compact"
    assert resolved.sources["profile"] == "profile"
    assert resolved.sources["context_file_mode"] == "profile"


def test_explicit_context_file_mode_full_wins_over_profile():
    config = _config(**{"context-profile": "compact", "context_file": {"mode": "full"}})
    resolved = resolve_context_profile(config, "Claude")
    assert resolved.profile == "compact"
    assert resolved.context_file_mode == "full"
    assert resolved.sources["context_file_mode"] == "explicit"


def test_explicit_context_file_mode_compact_wins():
    config = _config(**{"context_file": {"mode": "compact"}})
    resolved = resolve_context_profile(config, "Claude")
    assert resolved.profile == "full"
    assert resolved.context_file_mode == "compact"
    assert resolved.sources["context_file_mode"] == "explicit"


def test_provider_override_beats_global_profile():
    config = _config(
        **{
            "context-profile": "full",
            "provider-overrides": {"Opencode": {"context-profile": "compact"}},
        }
    )
    claude = resolve_context_profile(config, "Claude")
    opencode = resolve_context_profile(config, "Opencode")
    assert claude.profile == "full"
    assert claude.sources["profile"] == "profile"
    assert opencode.profile == "compact"
    assert opencode.sources["profile"] == "provider-override"
    assert opencode.context_file_mode == "compact"
    assert opencode.sources["context_file_mode"] == "provider-override"


def test_provider_override_loses_to_explicit_mode():
    config = _config(
        **{
            "provider-overrides": {"Opencode": {"context-profile": "compact"}},
            "context_file": {"mode": "full"},
        }
    )
    resolved = resolve_context_profile(config, "Opencode")
    assert resolved.profile == "compact"
    assert resolved.context_file_mode == "full"
    assert resolved.sources["context_file_mode"] == "explicit"


def test_provider_override_absent_entry_inherits():
    config = _config(**{"context-profile": "compact", "provider-overrides": {"Opencode": {}}})
    resolved = resolve_context_profile(config, "Claude")
    assert resolved.profile == "compact"
    assert resolved.sources["profile"] == "profile"


def test_unknown_profile_value_raises():
    with pytest.raises(ValueError):
        resolve_context_profile(_config(**{"context-profile": "ultra"}), "Claude")


def test_unknown_provider_override_value_raises():
    config = _config(**{"provider-overrides": {"Opencode": {"context-profile": "ultra"}}})
    with pytest.raises(ValueError):
        resolve_context_profile(config, "Opencode")


def test_invalid_context_file_mode_falls_back_to_profile():
    config = _config(**{"context-profile": "compact", "context_file": {"mode": "garbage"}})
    resolved = resolve_context_profile(config, "Claude")
    assert resolved.context_file_mode == "compact"
    assert resolved.sources["context_file_mode"] == "profile"


def test_rules_preset_source_is_explicit_when_set():
    resolved = resolve_context_profile(_config(**{"rules-preset": "lazy"}), "Claude")
    assert resolved.rules_preset == "lazy"
    assert resolved.sources["rules_preset"] == "explicit"


# --- shared-file rule --------------------------------------------------


def test_shared_file_full_wins():
    profiles = [
        ResolvedContextProfile("A", "compact", "compact", "default", {}),
        ResolvedContextProfile("B", "full", "full", "default", {}),
    ]
    assert resolve_shared_file_profile(profiles) == "full"


def test_shared_file_all_compact():
    profiles = [
        ResolvedContextProfile("A", "compact", "compact", "default", {}),
        ResolvedContextProfile("B", "compact", "compact", "default", {}),
    ]
    assert resolve_shared_file_profile(profiles) == "compact"


def test_shared_file_empty_is_full():
    assert resolve_shared_file_profile([]) == "full"


# --- provider variables -------------------------------------------------


def test_provider_variables_default_full():
    assert context_profile_provider_variables(_config(), "Claude") == {
        "CONTEXT_PROFILE": "full",
        "CONTEXT_PROFILE_COMPACT": "false",
    }


def test_provider_variables_compact_only_for_override_provider():
    config = _config(
        **{"provider-overrides": {"Opencode": {"context-profile": "compact"}}}
    )
    assert context_profile_provider_variables(config, "Opencode") == {
        "CONTEXT_PROFILE": "compact",
        "CONTEXT_PROFILE_COMPACT": "true",
    }
    assert context_profile_provider_variables(config, "Claude") == {
        "CONTEXT_PROFILE": "full",
        "CONTEXT_PROFILE_COMPACT": "false",
    }


def test_shared_wrapper_downgrades_to_full():
    config = _config(
        **{"provider-overrides": {"Opencode": {"context-profile": "compact"}}}
    )
    assert context_profile_variables(config, "Opencode", shared_users=["Claude"]) == {
        "CONTEXT_PROFILE": "full",
        "CONTEXT_PROFILE_COMPACT": "false",
    }


def test_shared_wrapper_keeps_compact_when_all_sharers_compact():
    config = _config(**{"context-profile": "compact"})
    assert context_profile_variables(config, "Opencode", shared_users=["Claude"]) == {
        "CONTEXT_PROFILE": "compact",
        "CONTEXT_PROFILE_COMPACT": "true",
    }
