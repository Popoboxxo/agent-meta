"""Tests for scripts.lib.bootstrap — BootstrapEngine."""

from __future__ import annotations

import textwrap
from pathlib import Path

from scripts.lib.bootstrap import BootstrapEngine


class TestBootstrapEngineInit:
    def test_default_config_dir(self) -> None:
        engine = BootstrapEngine()
        assert engine.config_dir is not None
        assert engine.config_dir.name == "config"

    def test_custom_config_dir(self, temp_dir: Path) -> None:
        engine = BootstrapEngine(config_dir=temp_dir)
        assert engine.config_dir == temp_dir


class TestBootstrapRegistry:
    def test_empty_when_no_config(self, temp_dir: Path) -> None:
        engine = BootstrapEngine(config_dir=temp_dir)
        assert engine.bootstrap_registry == {}

    def test_loads_provider_config(self, temp_dir: Path) -> None:
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        (config_dir / "provider-bootstrap.yaml").write_text(
            textwrap.dedent("""\
                bootstrap:
                  Gemini:
                    mechanism: api-based
                    action: define_subagent
            """),
            encoding="utf-8",
        )
        engine = BootstrapEngine(config_dir=config_dir)
        assert "Gemini" in engine.bootstrap_registry.get("bootstrap", {})


class TestGetBootstrapConfig:
    def test_returns_config_for_provider(self, temp_dir: Path) -> None:
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        (config_dir / "provider-bootstrap.yaml").write_text(
            textwrap.dedent("""\
                bootstrap:
                  Gemini:
                    mechanism: api-based
                    action: define_subagent
            """),
            encoding="utf-8",
        )
        engine = BootstrapEngine(config_dir=config_dir)
        gemini_cfg = engine.get_bootstrap_config("Gemini")
        assert gemini_cfg["mechanism"] == "api-based"

    def test_returns_empty_for_unknown_provider(self, temp_dir: Path) -> None:
        engine = BootstrapEngine(config_dir=temp_dir)
        assert engine.get_bootstrap_config("Unknown") == {}


class TestRunBootstrap:
    def test_none_mechanism_skipped(self, temp_dir: Path) -> None:
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        (config_dir / "provider-bootstrap.yaml").write_text(
            textwrap.dedent("""\
                bootstrap:
                  Claude:
                    mechanism: none
            """),
            encoding="utf-8",
        )
        engine = BootstrapEngine(config_dir=config_dir)
        result = engine.run_bootstrap("Claude", Path("agents"))
        assert result["status"] == "skipped"

    def test_api_based_mechanism(self, temp_dir: Path) -> None:
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        (config_dir / "provider-bootstrap.yaml").write_text(
            textwrap.dedent("""\
                bootstrap:
                  Gemini:
                    mechanism: api-based
            """),
            encoding="utf-8",
        )
        agents_dir = temp_dir / "agents"
        agents_dir.mkdir()
        (agents_dir / "test-agent.md").write_text(
            textwrap.dedent("""\
                ---
                name: test-agent
                description: "Test agent for bootstrapping"
                ---
                ## Content
            """),
            encoding="utf-8",
        )

        engine = BootstrapEngine(config_dir=config_dir)
        result = engine.run_bootstrap("Gemini", agents_dir)
        assert result["status"] == "success"
        assert result["agent_count"] == 1
        assert len(result["instructions"]) == 1

    def test_api_based_empty_agents_dir(self, temp_dir: Path) -> None:
        config_dir = temp_dir / "config"
        config_dir.mkdir()
        (config_dir / "provider-bootstrap.yaml").write_text(
            textwrap.dedent("""\
                bootstrap:
                  Gemini:
                    mechanism: api-based
            """),
            encoding="utf-8",
        )
        agents_dir = temp_dir / "empty_agents"
        agents_dir.mkdir()

        engine = BootstrapEngine(config_dir=config_dir)
        result = engine.run_bootstrap("Gemini", agents_dir)
        assert result["status"] == "success"
        assert result["agent_count"] == 0


class TestExtractDescription:
    def test_extracts_from_frontmatter(self) -> None:
        engine = BootstrapEngine()
        content = textwrap.dedent("""\
            ---
            name: test
            description: "This is a test agent"
            ---
        """)
        desc = engine._extract_description(content)
        assert desc == "This is a test agent"

    def test_fallback_when_no_description(self) -> None:
        engine = BootstrapEngine()
        desc = engine._extract_description("No frontmatter here")
        assert desc == "No description available"


class TestGenerateGeminiBootstrapInstructions:
    def test_generates_instructions(self, temp_dir: Path) -> None:
        agents_dir = temp_dir / "gemini_agents"
        agents_dir.mkdir()
        (agents_dir / "orchestrator.md").write_text("---\nname: orch\n---\n")
        (agents_dir / "developer.md").write_text("---\nname: dev\n---\n")

        engine = BootstrapEngine(config_dir=temp_dir)
        instructions = engine.generate_gemini_bootstrap_instructions(agents_dir)
        assert "Agent Bootstrap" in instructions
        assert "orchestrator.md" in instructions
        assert "developer.md" in instructions
        assert "define_subagent" in instructions

    def test_empty_dir_returns_empty(self, temp_dir: Path) -> None:
        agents_dir = temp_dir / "empty"
        agents_dir.mkdir()

        engine = BootstrapEngine(config_dir=temp_dir)
        instructions = engine.generate_gemini_bootstrap_instructions(agents_dir)
        assert instructions == ""
