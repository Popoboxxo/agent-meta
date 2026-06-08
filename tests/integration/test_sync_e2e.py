"""Integration tests for sync.py — end-to-end template generation.

Simulates a complete agent-meta sync by setting up fixtures and calling
the sync functions programmatically, then validating generated output.
"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path

import pytest

from scripts.lib.log import SyncLog
from scripts.lib.config import (
    load_config,
    build_variables,
    substitute,
    strip_inactive_conditional_blocks,
)
from scripts.lib.agents import (
    collect_sources,
    sync_agents_for_provider,
)
from scripts.lib.providers import load_providers_config, resolve_providers
from scripts.lib.dod import resolve_dod


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def full_agent_meta_root(temp_dir: Path) -> Path:
    """Build a complete agent-meta directory structure with templates and config."""
    root = temp_dir / "agent-meta"
    root.mkdir()

    # Version
    (root / "VERSION").write_text("0.57.1", encoding="utf-8")

    # Config
    (root / "config").mkdir()
    (root / "config" / "dod-presets.yaml").write_text(
        textwrap.dedent("""\
            presets:
              full:
                req-traceability: true
                tests-required: true
                codebase-overview: true
                security-audit: false
              rapid-prototyping:
                req-traceability: false
                tests-required: false
                codebase-overview: false
                security-audit: false
        """),
        encoding="utf-8",
    )
    (root / "config" / "ai-providers.yaml").write_text(
        textwrap.dedent("""\
            providers:
              Claude:
                agents_dir: .claude/agents
                agent_ext: .md
                context_file: CLAUDE.md
                has_rules: true
                has_hooks: true
                has_commands: false
                has_settings: true
                settings_file: .claude/settings.json
                gitignore_entries:
                  - .claude/settings.local.json
                  - CLAUDE.personal.md
                  - sync.log
                skills_dir: .claude/skills
                snippets_dir: .claude/snippets
                pending_tasks_file: .claude/pending-tasks.md
                extension_dir: .claude/3-project
                model-tiers:
                  nano: claude-haiku
                  fast: claude-haiku
                  balanced: claude-sonnet
                  powerful: claude-opus
                  max: claude-opus
                model-aliases: {}
        """),
        encoding="utf-8",
    )
    (root / "config" / "role-defaults.yaml").write_text(
        textwrap.dedent("""\
            roles:
              orchestrator:
                model: "balanced"
                memory: ""
                workflow_tier: required
                description: "Orchestrator"
              developer:
                model: "powerful"
                memory: ""
                workflow_tier: required
                description: "Developer"
              git:
                model: "fast"
                memory: ""
                workflow_tier: required
                description: "Git operations"
        """),
        encoding="utf-8",
    )

    # Templates
    (root / "agents").mkdir()
    (root / "agents" / "1-generic").mkdir()
    (root / "agents" / "2-platform").mkdir()

    # Orchestrator template
    (root / "agents" / "1-generic" / "orchestrator.md").write_text(
        textwrap.dedent("""\
            ---
            name: orchestrator
            version: "1.0.0"
            description: "Orchestrator for {{PROJECT_NAME}}"
            hint: "Entry point"
            tools: [Read, Bash, Glob, Task]
            ---

            # Orchestrator — {{PROJECT_NAME}}

            ## Project Info
            Version: {{AGENT_META_VERSION}}
            Date: {{AGENT_META_DATE}}

            {{#if DOD_REQ_TRACEABILITY}}
            ## Requirements Traceability
            REQ-IDs are required for this project.
            {{/if}}

            {{#unless DOD_TESTS_REQUIRED}}
            Tests are NOT required in this project.
            {{/unless}}
        """),
        encoding="utf-8",
    )

    # Developer template
    (root / "agents" / "1-generic" / "developer.md").write_text(
        textwrap.dedent("""\
            ---
            name: developer
            version: "1.0.0"
            description: "Developer for {{PROJECT_NAME}}"
            hint: "Use for development tasks"
            tools: [Read, Write, Edit, Bash, Glob, Grep, Task]
            ---

            # Developer — {{PROJECT_NAME}}

            You are the Developer for {{PROJECT_NAME}}.

            ## Context
            Project: {{PROJECT_NAME}} ({{PROJECT_SHORT}})

            ## DoD
            Preset: {{DOD_PRESET}}
            Traceability: {{DOD_REQ_TRACEABILITY}}
            Tests: {{DOD_TESTS_REQUIRED}}
        """),
        encoding="utf-8",
    )

    # Rules
    (root / "rules").mkdir()
    (root / "rules" / "1-generic").mkdir()
    (root / "rules" / "1-generic" / "branch-guard.md").write_text(
        textwrap.dedent("""\
            # Branch-Guard
            Always use feature branches.
        """),
        encoding="utf-8",
    )
    (root / "rules" / "1-generic" / "commit-conventions.md").write_text(
        textwrap.dedent("""\
            # Commit Conventions
            Use conventional commits.
        """),
        encoding="utf-8",
    )
    (root / "rules" / "1-generic" / "dod-criteria.md").write_text(
        textwrap.dedent("""\
            # DoD Criteria
            Check all criteria before completing.
        """),
        encoding="utf-8",
    )

    return root


@pytest.fixture
def full_project_root(temp_dir: Path) -> Path:
    """Create a project root with .meta-config/project.yaml."""
    project = temp_dir / "project"
    project.mkdir()
    (project / ".meta-config").mkdir()
    (project / ".meta-config" / "project.yaml").write_text(
        textwrap.dedent("""\
            project:
              name: "integration-test"
              short: "IT"
              prefix: "am"
            dod-preset: "rapid-prototyping"
            ai-provider: "Claude"
            roles:
              - orchestrator
              - developer
            critical-rules-footer:
              enabled: false
        """),
        encoding="utf-8",
    )
    return project


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestEndToEndSync:
    """Full end-to-end test: config → templates → generated agents."""

    def test_sync_generates_agent_files(
        self, full_agent_meta_root: Path, full_project_root: Path,
    ) -> None:
        """Run sync_agents_for_provider and verify output files exist."""
        config_path = full_project_root / ".meta-config" / "project.yaml"
        config = load_config(config_path)
        log = SyncLog()
        variables, _ = build_variables(config, full_agent_meta_root)
        provider_config = load_providers_config(full_agent_meta_root)

        # Run sync for Claude
        sync_agents_for_provider(
            full_agent_meta_root, full_project_root, config, variables,
            log, dry_run=False, provider="Claude", provider_config=provider_config,
        )

        # Verify generated files
        agents_dir = full_project_root / ".claude" / "agents"
        assert agents_dir.exists()

        orch_file = agents_dir / "orchestrator.md"
        dev_file = agents_dir / "developer.md"

        assert orch_file.exists(), f"Expected {orch_file}"
        assert dev_file.exists(), f"Expected {dev_file}"

    def test_generated_agent_has_substituted_variables(
        self, full_agent_meta_root: Path, full_project_root: Path,
    ) -> None:
        """Generated agents should have variables substituted."""
        config_path = full_project_root / ".meta-config" / "project.yaml"
        config = load_config(config_path)
        log = SyncLog()
        variables, _ = build_variables(config, full_agent_meta_root)
        provider_config = load_providers_config(full_agent_meta_root)

        sync_agents_for_provider(
            full_agent_meta_root, full_project_root, config, variables,
            log, dry_run=False, provider="Claude", provider_config=provider_config,
        )

        dev_file = full_project_root / ".claude" / "agents" / "developer.md"
        content = dev_file.read_text(encoding="utf-8")

        # Variables substituted
        assert "integration-test" in content
        assert "Developer" in content
        # DoD variables
        assert "rapid-prototyping" in content

    def test_conditional_blocks_processed(
        self, full_agent_meta_root: Path, full_project_root: Path,
    ) -> None:
        """Conditional blocks should be processed based on DoD preset."""
        config_path = full_project_root / ".meta-config" / "project.yaml"
        config = load_config(config_path)
        log = SyncLog()
        variables, _ = build_variables(config, full_agent_meta_root)
        provider_config = load_providers_config(full_agent_meta_root)

        sync_agents_for_provider(
            full_agent_meta_root, full_project_root, config, variables,
            log, dry_run=False, provider="Claude", provider_config=provider_config,
        )

        orch_file = full_project_root / ".claude" / "agents" / "orchestrator.md"
        content = orch_file.read_text(encoding="utf-8")

        # rapid-prototyping → DOD_REQ_TRACEABILITY is false → block should be removed
        assert "REQ-IDs are required" not in content
        # rapid-prototyping → DOD_TESTS_REQUIRED is false → unless block shows
        assert "Tests are NOT required" in content

    def test_sync_with_full_preset_shows_traceability(
        self, full_agent_meta_root: Path, full_project_root: Path,
    ) -> None:
        """With 'full' preset, traceability block should be visible."""
        # Override config to use 'full' preset
        config_path = full_project_root / ".meta-config" / "project.yaml"
        config_path.write_text(
            textwrap.dedent("""\
                project:
                  name: "full-test"
                  short: "FT"
                  prefix: ""
                dod-preset: "full"
                ai-provider: "Claude"
                roles:
                  - orchestrator
            """),
            encoding="utf-8",
        )

        config = load_config(config_path)
        log = SyncLog()
        variables, _ = build_variables(config, full_agent_meta_root)
        provider_config = load_providers_config(full_agent_meta_root)

        sync_agents_for_provider(
            full_agent_meta_root, full_project_root, config, variables,
            log, dry_run=False, provider="Claude", provider_config=provider_config,
        )

        orch_file = full_project_root / ".claude" / "agents" / "orchestrator.md"
        content = orch_file.read_text(encoding="utf-8")
        assert "REQ-IDs are required" in content
        assert "Tests are NOT required" not in content

    def test_dry_run_does_not_write_files(
        self, full_agent_meta_root: Path, full_project_root: Path,
    ) -> None:
        """Dry-run should not create agent files."""
        config_path = full_project_root / ".meta-config" / "project.yaml"
        config = load_config(config_path)
        log = SyncLog()
        variables, _ = build_variables(config, full_agent_meta_root)
        provider_config = load_providers_config(full_agent_meta_root)

        sync_agents_for_provider(
            full_agent_meta_root, full_project_root, config, variables,
            log, dry_run=True, provider="Claude", provider_config=provider_config,
        )

        agents_dir = full_project_root / ".claude" / "agents"
        assert not agents_dir.exists() or not list(agents_dir.glob("*.md"))

    def test_respects_role_whitelist(
        self, full_agent_meta_root: Path, full_project_root: Path,
    ) -> None:
        """Only whitelisted roles should be generated."""
        config_path = full_project_root / ".meta-config" / "project.yaml"
        config_path.write_text(
            textwrap.dedent("""\
                project:
                  name: "role-test"
                  short: "RT"
                  prefix: ""
                dod-preset: "rapid-prototyping"
                ai-provider: "Claude"
                roles:
                  - orchestrator
            """),
            encoding="utf-8",
        )

        config = load_config(config_path)
        log = SyncLog()
        variables, _ = build_variables(config, full_agent_meta_root)
        provider_config = load_providers_config(full_agent_meta_root)

        sync_agents_for_provider(
            full_agent_meta_root, full_project_root, config, variables,
            log, dry_run=False, provider="Claude", provider_config=provider_config,
        )

        agents_dir = full_project_root / ".claude" / "agents"
        assert agents_dir.exists()
        assert (agents_dir / "orchestrator.md").exists()
        # developer should NOT exist (not in whitelist)
        assert not (agents_dir / "developer.md").exists()


class TestVariableSubstitutionPipeline:
    """Test the full variable pipeline: build → substitute → strip_conditional."""

    def test_full_pipeline_rapid_prototyping(
        self, full_agent_meta_root: Path, full_project_root: Path,
    ) -> None:
        """End-to-end test of variable pipeline with rapid-prototyping preset."""
        config_path = full_project_root / ".meta-config" / "project.yaml"
        config = load_config(config_path)
        log = SyncLog()
        variables, _ = build_variables(config, full_agent_meta_root)

        template_path = full_agent_meta_root / "agents" / "1-generic" / "orchestrator.md"
        content = template_path.read_text(encoding="utf-8")
        content = substitute(content, variables, "orchestrator.md", log)
        content = strip_inactive_conditional_blocks(content, variables)

        # verify substitutions happened
        assert "integration-test" in content
        # verify conditional blocks processed
        assert "REQ-IDs are required" not in content  # false
        assert "Tests are NOT required" in content  # unless (DOD_TESTS_REQUIRED=false)
        # No leftover markers
        assert "{{#if" not in content
        assert "{{/if}}" not in content
        assert "{{/unless}}" not in content

    def test_full_pipeline_full_preset(
        self, full_agent_meta_root: Path, full_project_root: Path,
    ) -> None:
        """End-to-end test with full preset."""
        config_path = full_project_root / ".meta-config" / "project.yaml"
        config_path.write_text(
            textwrap.dedent("""\
                project:
                  name: "full-project"
                  short: "FP"
                  prefix: ""
                dod-preset: "full"
                ai-provider: "Claude"
                roles:
                  - orchestrator
            """),
            encoding="utf-8",
        )

        config = load_config(config_path)
        log = SyncLog()
        variables, _ = build_variables(config, full_agent_meta_root)

        template_path = full_agent_meta_root / "agents" / "1-generic" / "orchestrator.md"
        content = template_path.read_text(encoding="utf-8")
        content = substitute(content, variables, "orchestrator.md", log)
        content = strip_inactive_conditional_blocks(content, variables)

        assert "REQ-IDs are required" in content  # true
        assert "Tests are NOT required" not in content  # unless (DOD_TESTS_REQUIRED=true)


class TestCollectSources:
    """Integration-level tests for collect_sources."""

    def test_collects_all_generic_agents(
        self, full_agent_meta_root: Path,
    ) -> None:
        overrides, _ = collect_sources(full_agent_meta_root, [])
        assert "orchestrator" in overrides
        assert "developer" in overrides
        # Each override should point to a real file
        for role, path in overrides.items():
            assert path.exists(), f"{role}: {path} not found"


class TestSyncMultiProvider:
    """Test sync across multiple providers."""

    def test_sync_for_claude_and_continue(
        self, full_agent_meta_root: Path, full_project_root: Path,
    ) -> None:
        """Sync to Claude and Continue providers."""
        # Add Continue provider
        providers_yaml = full_agent_meta_root / "config" / "ai-providers.yaml"
        providers_yaml.write_text(
            textwrap.dedent("""\
                providers:
                  Claude:
                    agents_dir: .claude/agents
                    agent_ext: .md
                    context_file: CLAUDE.md
                    has_rules: true
                    has_hooks: true
                    has_commands: false
                    has_settings: true
                    settings_file: .claude/settings.json
                    gitignore_entries: []
                    skills_dir: .claude/skills
                    snippets_dir: .claude/snippets
                    extension_dir: .claude/3-project
                    model-tiers:
                      balanced: claude-sonnet
                    model-aliases: {}
                  Continue:
                    agents_dir: .continue/agents
                    agent_ext: .md
                    context_file: .continue/rules/project-context.md
                    has_rules: true
                    has_hooks: false
                    has_commands: false
                    has_settings: true
                    settings_file: .continue/config.yaml
                    gitignore_entries: []
                    skills_dir: .continue/skills
                    snippets_dir: .continue/snippets
                    extension_dir: .continue/3-project
                    model-tiers: {}
                    model-aliases: {}
            """),
            encoding="utf-8",
        )

        config_path = full_project_root / ".meta-config" / "project.yaml"
        config = load_config(config_path)
        log = SyncLog()
        variables, _ = build_variables(config, full_agent_meta_root)
        provider_config = load_providers_config(full_agent_meta_root)

        # Sync Claude
        sync_agents_for_provider(
            full_agent_meta_root, full_project_root, config, variables,
            log, dry_run=False, provider="Claude", provider_config=provider_config,
        )
        # Sync Continue
        sync_agents_for_provider(
            full_agent_meta_root, full_project_root, config, variables,
            log, dry_run=False, provider="Continue", provider_config=provider_config,
        )

        # Both directories should exist with agent files
        claude_dir = full_project_root / ".claude" / "agents"
        continue_dir = full_project_root / ".continue" / "agents"

        assert claude_dir.exists()
        assert continue_dir.exists()

        for dir_ in (claude_dir, continue_dir):
            agent_files = list(dir_.glob("*.md"))
            assert len(agent_files) >= 2, f"{dir_} has {len(agent_files)} agents"
            # Verify each agent has frontmatter
            for af in agent_files:
                content = af.read_text(encoding="utf-8")
                assert content.startswith("---"), f"{af.name}: missing frontmatter"
