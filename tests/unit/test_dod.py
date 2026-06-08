"""Tests for scripts.lib.dod — DoD preset loading and resolution."""

from __future__ import annotations

from pathlib import Path

from scripts.lib.dod import load_dod_presets, resolve_dod


class TestLoadDodPresets:
    def test_loads_full_preset(self, agent_meta_root: Path, sample_dod_presets_yaml: Path) -> None:
        presets = load_dod_presets(agent_meta_root)
        assert "full" in presets
        assert presets["full"]["req-traceability"] is True
        assert presets["full"]["tests-required"] is True

    def test_loads_rapid_prototyping(self, agent_meta_root: Path, sample_dod_presets_yaml: Path) -> None:
        presets = load_dod_presets(agent_meta_root)
        assert "rapid-prototyping" in presets
        assert presets["rapid-prototyping"]["req-traceability"] is False
        assert presets["rapid-prototyping"]["tests-required"] is False

    def test_returns_empty_when_no_file(self, temp_dir: Path) -> None:
        presets = load_dod_presets(temp_dir)
        assert presets == {}


class TestResolveDod:
    def test_resolves_preset_values(
        self, agent_meta_root: Path, sample_dod_presets_yaml: Path,
    ) -> None:
        config = {"dod-preset": "full"}
        resolved = resolve_dod(config, agent_meta_root)
        assert resolved["req-traceability"] is True
        assert resolved["tests-required"] is True
        assert resolved["security-audit"] is False

    def test_project_overrides_win(
        self, agent_meta_root: Path, sample_dod_presets_yaml: Path,
    ) -> None:
        config = {
            "dod-preset": "full",
            "dod": {"req-traceability": False, "security-audit": True},
        }
        resolved = resolve_dod(config, agent_meta_root)
        # Override takes precedence
        assert resolved["req-traceability"] is False
        assert resolved["security-audit"] is True
        # Not overridden — from preset
        assert resolved["tests-required"] is True

    def test_unknown_preset_falls_back_to_full(
        self, agent_meta_root: Path, sample_dod_presets_yaml: Path,
    ) -> None:
        config = {"dod-preset": "nonexistent-preset"}
        resolved = resolve_dod(config, agent_meta_root)
        # Falls back to full
        assert resolved["req-traceability"] is True
        assert resolved["tests-required"] is True

    def test_default_preset_when_missing(
        self, agent_meta_root: Path, sample_dod_presets_yaml: Path,
    ) -> None:
        config: dict = {}
        resolved = resolve_dod(config, agent_meta_root)
        assert resolved["req-traceability"] is True
        assert resolved["tests-required"] is True
