"""Shared fixtures for agent-meta tests."""

from __future__ import annotations

import json
import tempfile
import textwrap
from pathlib import Path

import pytest


@pytest.fixture
def temp_dir():
    """Create a temporary directory that auto-cleans up after test."""
    with tempfile.TemporaryDirectory() as tmp:
        yield Path(tmp)


@pytest.fixture
def agent_meta_root(temp_dir: Path) -> Path:
    """Create a minimal agent-meta root structure for testing."""
    root = temp_dir / "agent-meta"
    root.mkdir()
    (root / "VERSION").write_text("0.57.1", encoding="utf-8")
    (root / "config").mkdir()
    (root / "agents").mkdir()
    (root / "agents" / "1-generic").mkdir()
    (root / "agents" / "2-platform").mkdir()
    (root / "agents" / "3-project").mkdir()
    (root / "rules").mkdir()
    (root / "rules" / "1-generic").mkdir()
    (root / "rules" / "2-platform").mkdir()
    return root


@pytest.fixture
def sample_dod_presets_yaml(agent_meta_root: Path) -> Path:
    """Write a sample dod-presets.yaml into config/."""
    content = textwrap.dedent("""\
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
    """)
    path = agent_meta_root / "config" / "dod-presets.yaml"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def sample_providers_yaml(agent_meta_root: Path) -> Path:
    """Write a minimal ai-providers.yaml."""
    content = textwrap.dedent("""\
        providers:
          Claude:
            agents_dir: .claude/agents
            agent_ext: .md
            context_file: CLAUDE.md
            has_rules: true
            has_hooks: true
            gitignore_entries:
              - .claude/settings.local.json
          Gemini:
            agents_dir: .gemini/agents
            agent_ext: .md
            context_file: GEMINI.md
            has_rules: true
            has_hooks: false
    """)
    path = agent_meta_root / "config" / "ai-providers.yaml"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def sample_role_defaults_yaml(agent_meta_root: Path) -> Path:
    """Write a minimal role-defaults.yaml."""
    content = textwrap.dedent("""\
        roles:
          orchestrator:
            model: "balanced"
            memory: ""
            description: "Orchestrator"
          developer:
            model: "powerful"
            memory: ""
            description: "Developer"
    """)
    path = agent_meta_root / "config" / "role-defaults.yaml"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def sample_project_yaml(temp_dir: Path) -> Path:
    """Write a minimal project.yaml for testing."""
    content = textwrap.dedent("""\
        project:
          name: "test-project"
          short: "TP"
          prefix: "am"
        dod-preset: "rapid-prototyping"
        ai-provider: "Claude"
    """)
    meta_config = temp_dir / ".meta-config"
    meta_config.mkdir()
    path = meta_config / "project.yaml"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def sample_project_yaml_full(temp_dir: Path) -> Path:
    """Write a project.yaml with all config fields."""
    content = textwrap.dedent("""\
        project:
          name: "full-project"
          short: "FP"
          prefix: ""
        dod-preset: "full"
        max-parallel-agents: 4
        speech-mode: "short"
        ai-provider: "Claude"
        roles:
          - orchestrator
          - developer
          - git
        dod:
          security-audit: true
    """)
    meta_config = temp_dir / ".meta-config"
    meta_config.mkdir()
    path = meta_config / "project.yaml"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def sample_agent_template(agent_meta_root: Path) -> Path:
    """Write a sample agent template into 1-generic/."""
    content = textwrap.dedent("""\
        ---
        name: test-agent
        version: "1.0.0"
        description: "A test agent for {{PROJECT_NAME}}"
        hint: "Use for testing"
        tools: ["Read", "Bash", "Glob"]
        ---

        # {{PROJECT_NAME}} Agent

        ## Context
        Project: {{PROJECT_NAME}} ({{PROJECT_SHORT}})
        Version: {{AGENT_META_VERSION}}
        DoD: {{DOD_PRESET}}

        {{#if DOD_REQ_TRACEABILITY}}
        ## Requirements
        Traceability is enabled
        {{/if}}

        {{#unless DOD_TESTS_REQUIRED}}
        ## Tests
        Tests are NOT required
        {{/unless}}
    """)
    path = agent_meta_root / "agents" / "1-generic" / "test-agent.md"
    path.write_text(content, encoding="utf-8")
    return path


@pytest.fixture
def sample_variables() -> dict:
    """Return a minimal set of variables for substitution tests."""
    return {
        "PROJECT_NAME": "TestProject",
        "PROJECT_SHORT": "TP",
        "AGENT_META_VERSION": "0.57.1",
        "DOD_PRESET": "rapid-prototyping",
        "DOD_REQ_TRACEABILITY": "false",
        "DOD_TESTS_REQUIRED": "false",
        "DOD_CODEBASE_OVERVIEW": "false",
        "DOD_SECURITY_AUDIT": "false",
        "SE_ENABLED": "false",
        "VALIDATOR_ENABLED": "false",
        "MAX_PARALLEL_AGENTS": "2",
        "ORCHESTRATOR_ENABLED": "true",
        "ORCHESTRATOR_STRICT": "true",
        "ORCHESTRATOR_OUTCOME_CACHING": "false",
        "ORCHESTRATOR_CACHE_TTL": "3600",
        "ORCHESTRATOR_CACHE_MAX_ENTRIES": "100",
        "UNKNOWN_FALLBACK_META_FEEDBACK": "true",
        "UNKNOWN_FALLBACK_MAIN_CHAT": "true",
        "UNKNOWN_FALLBACK_ASK_USER": "false",
        "QUALITY_PIPELINES_ENABLED": "false",
        "REFLECTION_PAIRS_ENABLED": "false",
    }


@pytest.fixture
def sample_json_config(temp_dir: Path) -> Path:
    """Write a minimal JSON config file."""
    content = json.dumps({
        "project": {"name": "json-test", "short": "JT", "prefix": ""},
        "dod-preset": "standard",
        "ai-provider": "Claude",
    }, indent=2)
    path = temp_dir / "agent-meta.config.json"
    path.write_text(content, encoding="utf-8")
    return path
