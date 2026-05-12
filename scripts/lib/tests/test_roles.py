"""Unit tests for scripts/lib/roles.py"""

import pytest
from lib.roles import (
    _resolve_tier_to_model,
    resolve_model,
    resolve_memory,
    resolve_permission_mode,
    resolve_temperature,
    resolve_max_tokens,
    load_roles_config,
    build_role_map,
)


# ---------------------------------------------------------------------------
# _resolve_tier_to_model
# ---------------------------------------------------------------------------

SAMPLE_PROVIDER_CONFIG = {
    "Claude": {
        "model-tiers": {
            "nano": "claude-haiku-4-5",
            "fast": "claude-haiku-4-5",
            "balanced": "claude-sonnet-4-6",
            "powerful": "claude-opus-4-7",
            "max": "claude-opus-4-7",
        },
        "model-aliases": {
            "haiku": "claude-haiku-4-5",
            "sonnet": "claude-sonnet-4-6",
            "opus": "claude-opus-4-7",
        },
    },
    "Gemini": {
        "model-tiers": {
            "nano": "gemini-2.5-flash",
            "fast": "gemini-2.5-flash",
            "balanced": "gemini-2.5-pro",
            "powerful": "gemini-2.5-pro",
            "max": "gemini-2.5-pro",
        },
    },
}


def test_resolve_tier_balanced_claude():
    result = _resolve_tier_to_model("balanced", "Claude", SAMPLE_PROVIDER_CONFIG)
    assert result == "claude-sonnet-4-6"


def test_resolve_tier_fast_claude():
    result = _resolve_tier_to_model("fast", "Claude", SAMPLE_PROVIDER_CONFIG)
    assert result == "claude-haiku-4-5"


def test_resolve_tier_max_claude():
    result = _resolve_tier_to_model("max", "Claude", SAMPLE_PROVIDER_CONFIG)
    assert result == "claude-opus-4-7"


def test_resolve_tier_balanced_gemini():
    result = _resolve_tier_to_model("balanced", "Gemini", SAMPLE_PROVIDER_CONFIG)
    assert result == "gemini-2.5-pro"


def test_resolve_legacy_alias_sonnet():
    result = _resolve_tier_to_model("sonnet", "Claude", SAMPLE_PROVIDER_CONFIG)
    assert result == "claude-sonnet-4-6"


def test_resolve_legacy_alias_haiku():
    result = _resolve_tier_to_model("haiku", "Claude", SAMPLE_PROVIDER_CONFIG)
    assert result == "claude-haiku-4-5"


def test_resolve_legacy_alias_opus():
    result = _resolve_tier_to_model("opus", "Claude", SAMPLE_PROVIDER_CONFIG)
    assert result == "claude-opus-4-7"


def test_resolve_legacy_alias_fallback_for_non_claude():
    # Gemini has no model-aliases — should fall back to tier mapping
    result = _resolve_tier_to_model("sonnet", "Gemini", SAMPLE_PROVIDER_CONFIG)
    assert result == "gemini-2.5-pro"  # sonnet→balanced→gemini-2.5-pro


def test_resolve_full_model_id_passthrough():
    result = _resolve_tier_to_model("claude-sonnet-4-6", "Claude", SAMPLE_PROVIDER_CONFIG)
    assert result == "claude-sonnet-4-6"


def test_resolve_empty_string_returns_empty():
    result = _resolve_tier_to_model("", "Claude", SAMPLE_PROVIDER_CONFIG)
    assert result == ""


def test_resolve_unknown_tier_passthrough():
    result = _resolve_tier_to_model("my-custom-model", "Claude", SAMPLE_PROVIDER_CONFIG)
    assert result == "my-custom-model"


# ---------------------------------------------------------------------------
# resolve_model — precedence
# ---------------------------------------------------------------------------

def test_resolve_model_flat_project_override(agent_meta_root):
    config = {
        "model-overrides": {"developer": "claude-opus-4-7"},
        "project": {"name": "test"},
    }
    result = resolve_model("developer", config, agent_meta_root,
                           provider="Claude", provider_config=SAMPLE_PROVIDER_CONFIG)
    assert result == "claude-opus-4-7"


def test_resolve_model_provider_specific_override_wins(agent_meta_root):
    config = {
        "model-overrides": {
            "developer": "claude-haiku-4-5",
            "Claude": {"developer": "claude-opus-4-7"},
        },
        "project": {"name": "test"},
    }
    result = resolve_model("developer", config, agent_meta_root,
                           provider="Claude", provider_config=SAMPLE_PROVIDER_CONFIG)
    assert result == "claude-opus-4-7"


def test_resolve_model_flat_override_skipped_for_non_claude(agent_meta_root):
    config = {
        "model-overrides": {"developer": "claude-sonnet-4-6"},
        "project": {"name": "test"},
    }
    # For Gemini, the flat Claude override should be skipped — meta default applies
    result = resolve_model("developer", config, agent_meta_root,
                           provider="Gemini", provider_config=SAMPLE_PROVIDER_CONFIG)
    assert result != "claude-sonnet-4-6"


def test_resolve_model_meta_default_from_role_defaults(agent_meta_root):
    config = {"project": {"name": "test"}}
    result = resolve_model("git", config, agent_meta_root,
                           provider="Claude", provider_config=SAMPLE_PROVIDER_CONFIG)
    assert result  # git has model: fast → claude-haiku-4-5


def test_resolve_model_unknown_role_returns_empty(agent_meta_root):
    config = {"project": {"name": "test"}}
    result = resolve_model("nonexistent-role", config, agent_meta_root,
                           provider="Claude", provider_config=SAMPLE_PROVIDER_CONFIG)
    assert result == ""


# ---------------------------------------------------------------------------
# resolve_memory / resolve_permission_mode
# ---------------------------------------------------------------------------

def test_resolve_memory_project_override(agent_meta_root):
    config = {"memory-overrides": {"developer": "local"}, "project": {"name": "t"}}
    assert resolve_memory("developer", config, agent_meta_root) == "local"


def test_resolve_memory_meta_default(agent_meta_root):
    config = {"project": {"name": "t"}}
    # requirements has memory: project in role-defaults.yaml
    result = resolve_memory("requirements", config, agent_meta_root)
    assert result == "project"


def test_resolve_memory_empty_for_no_memory_role(agent_meta_root):
    config = {"project": {"name": "t"}}
    result = resolve_memory("git", config, agent_meta_root)
    assert result == ""


def test_resolve_permission_mode_project_override(agent_meta_root):
    config = {"permission-mode-overrides": {"git": "bypassPermissions"}, "project": {"name": "t"}}
    assert resolve_permission_mode("git", config, agent_meta_root) == "bypassPermissions"


def test_resolve_permission_mode_meta_default_validator(agent_meta_root):
    config = {"project": {"name": "t"}}
    # validator has permission_mode: plan in role-defaults.yaml
    result = resolve_permission_mode("validator", config, agent_meta_root)
    assert result == "plan"


# ---------------------------------------------------------------------------
# resolve_temperature / resolve_max_tokens
# ---------------------------------------------------------------------------

def test_resolve_temperature_meta_default_developer(agent_meta_root):
    config = {"project": {"name": "t"}}
    result = resolve_temperature("developer", config, agent_meta_root)
    assert result == "0.2"


def test_resolve_temperature_project_override(agent_meta_root):
    config = {"temperature-overrides": {"developer": "0.9"}, "project": {"name": "t"}}
    assert resolve_temperature("developer", config, agent_meta_root) == "0.9"


def test_resolve_temperature_empty_for_no_temp_role(agent_meta_root):
    config = {"project": {"name": "t"}}
    result = resolve_temperature("documenter", config, agent_meta_root)
    assert result == ""


def test_resolve_max_tokens_meta_default_developer(agent_meta_root):
    config = {"project": {"name": "t"}}
    result = resolve_max_tokens("developer", config, agent_meta_root)
    assert result == "8192"


def test_resolve_max_tokens_project_override(agent_meta_root):
    config = {"max-tokens-overrides": {"git": "4096"}, "project": {"name": "t"}}
    assert resolve_max_tokens("git", config, agent_meta_root) == "4096"


# ---------------------------------------------------------------------------
# load_roles_config / build_role_map
# ---------------------------------------------------------------------------

def test_load_roles_config_has_required_roles(agent_meta_root):
    cfg = load_roles_config(agent_meta_root)
    roles = cfg["roles"]
    for required in ("developer", "orchestrator", "git", "documenter"):
        assert required in roles, f"Expected '{required}' in roles config"


def test_load_roles_config_no_private_entries(agent_meta_root):
    cfg = load_roles_config(agent_meta_root)
    for key in cfg["roles"]:
        assert not key.startswith("_"), f"Private key '{key}' leaked into roles config"


def test_build_role_map_returns_identity_mapping(agent_meta_root):
    role_map = build_role_map(agent_meta_root)
    assert isinstance(role_map, dict)
    for k, v in role_map.items():
        assert k == v, f"Role map should be identity: {k!r} != {v!r}"
