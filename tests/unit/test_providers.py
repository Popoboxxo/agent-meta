"""Tests for scripts.lib.providers — provider config loading and resolution."""

from __future__ import annotations

from pathlib import Path

from scripts.lib.providers import (
    load_providers_config,
    resolve_providers,
    resolve_provider_options,
)


class TestLoadProvidersConfig:
    def test_loads_claude_config(self, agent_meta_root: Path, sample_providers_yaml: Path) -> None:
        config = load_providers_config(agent_meta_root)
        assert "Claude" in config
        assert config["Claude"]["agents_dir"] == ".claude/agents"
        assert config["Claude"]["has_rules"] is True

    def test_loads_gemini_config(self, agent_meta_root: Path, sample_providers_yaml: Path) -> None:
        config = load_providers_config(agent_meta_root)
        assert "Gemini" in config
        assert config["Gemini"]["context_file"] == "GEMINI.md"

    def test_returns_fallback_when_no_file(self, temp_dir: Path) -> None:
        config = load_providers_config(temp_dir)
        assert "Claude" in config
        assert config["Claude"]["agents_dir"] == ".claude/agents"


class TestResolveProviders:
    def test_resolves_from_multi_provider_list(self) -> None:
        config = {"ai-providers": ["Claude", "Gemini"]}
        provider_config = {
            "Claude": {},
            "Gemini": {},
            "Continue": {},
        }
        providers = resolve_providers(config, provider_config)
        assert providers == ["Claude", "Gemini"]

    def test_resolves_from_legacy_single_provider(self) -> None:
        config = {"ai-provider": "Gemini"}
        provider_config = {"Claude": {}, "Gemini": {}}
        providers = resolve_providers(config, provider_config)
        assert providers == ["Gemini"]

    def test_defaults_to_claude(self) -> None:
        config: dict = {}
        provider_config = {"Claude": {}, "Gemini": {}}
        providers = resolve_providers(config, provider_config)
        assert providers == ["Claude"]

    def test_filters_unknown_providers(self) -> None:
        config = {"ai-providers": ["Claude", "UnknownProvider", "Gemini"]}
        provider_config = {"Claude": {}, "Gemini": {}}
        providers = resolve_providers(config, provider_config)
        assert providers == ["Claude", "Gemini"]

    def test_string_provider_in_multi_field(self) -> None:
        """When ai-providers is a string instead of list."""
        config = {"ai-providers": "Claude"}
        provider_config = {"Claude": {}, "Gemini": {}}
        providers = resolve_providers(config, provider_config)
        assert providers == ["Claude"]


class TestResolveProviderOptions:
    def test_returns_provider_specific_options(self) -> None:
        config = {
            "provider-options": {
                "Continue": {
                    "generate-prompts": True,
                    "prompt-mode": "full",
                }
            }
        }
        opts = resolve_provider_options(config, "Continue")
        assert opts["generate-prompts"] is True
        assert opts["prompt-mode"] == "full"

    def test_returns_empty_for_unknown_provider(self) -> None:
        config: dict = {}
        opts = resolve_provider_options(config, "Claude")
        assert opts == {}
