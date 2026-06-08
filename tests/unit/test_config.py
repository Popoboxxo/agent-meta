"""Tests for scripts.lib.config — config loading, substitution, conditional blocks."""

from __future__ import annotations

import textwrap
from pathlib import Path
from unittest.mock import patch

import pytest

from scripts.lib.config import (
    find_agent_meta_root,
    load_config,
    read_version,
    substitute,
    strip_inactive_conditional_blocks,
    build_variables,
    fill_defaults,
)
from scripts.lib.log import SyncLog


# ---------------------------------------------------------------------------
# find_agent_meta_root
# ---------------------------------------------------------------------------


class TestFindAgentMetaRoot:
    def test_resolves_from_scripts_sync_py(self) -> None:
        root = find_agent_meta_root(Path("/x/agent-meta/scripts/sync.py"))
        assert root == Path("/x/agent-meta")


# ---------------------------------------------------------------------------
# read_version
# ---------------------------------------------------------------------------


class TestReadVersion:
    def test_reads_existing_version_file(self, agent_meta_root: Path) -> None:
        assert read_version(agent_meta_root) == "0.57.1"

    def test_returns_unknown_when_missing(self, temp_dir: Path) -> None:
        assert read_version(temp_dir) == "unknown"


# ---------------------------------------------------------------------------
# load_config
# ---------------------------------------------------------------------------


class TestLoadConfig:
    def test_loads_yaml_config(self, sample_project_yaml: Path) -> None:
        config = load_config(sample_project_yaml)
        assert config["project"]["name"] == "test-project"
        assert config["dod-preset"] == "rapid-prototyping"

    def test_loads_json_config(self, sample_json_config: Path) -> None:
        config = load_config(sample_json_config)
        assert config["project"]["name"] == "json-test"
        assert config["dod-preset"] == "standard"

    def test_auto_detects_yaml_sibling(self, temp_dir: Path) -> None:
        """When a .json file does not exist but .yaml sibling does, YAML is loaded."""
        yaml_path = temp_dir / "project.yaml"
        yaml_path.write_text("project:\n  name: yaml-wins\nai-provider: Claude\n", encoding="utf-8")

        config = load_config(temp_dir / "project.json")  # .json missing, .yaml exists
        assert config["project"]["name"] == "yaml-wins"

    def test_error_on_missing_config(self, temp_dir: Path) -> None:
        nonexistent = temp_dir / "nope.yaml"
        with pytest.raises(SystemExit):
            load_config(nonexistent)

    def test_loads_json_when_yaml_not_available(self, temp_dir: Path) -> None:
        json_path = temp_dir / "only.json"
        json_path.write_text('{"project": {"name": "only-json"}}', encoding="utf-8")
        config = load_config(json_path)
        assert config["project"]["name"] == "only-json"


# ---------------------------------------------------------------------------
# substitute
# ---------------------------------------------------------------------------


class TestSubstitute:
    def test_replaces_known_variable(self, sample_variables: dict) -> None:
        log = SyncLog()
        result = substitute("Hello {{PROJECT_NAME}}!", sample_variables, "test", log)
        assert result == "Hello TestProject!"

    def test_multiple_variables(self, sample_variables: dict) -> None:
        log = SyncLog()
        template = "Project: {{PROJECT_NAME}} ({{PROJECT_SHORT}}) v{{AGENT_META_VERSION}}"
        result = substitute(template, sample_variables, "test", log)
        assert result == "Project: TestProject (TP) v0.57.1"

    def test_unknown_variable_warns(self, sample_variables: dict) -> None:
        log = SyncLog()
        result = substitute("{{UNKNOWN_VAR}}", sample_variables, "test.md", log)
        # Placeholder remains unchanged
        assert "{{UNKNOWN_VAR}}" in result
        # Warning was logged
        assert len(log.warnings) == 1
        assert "UNKNOWN_VAR" in log.warnings[0]

    def test_escaped_variable_preserved(self, sample_variables: dict) -> None:
        log = SyncLog()
        result = substitute("Use {{%PROJECT_NAME%}} in docs", sample_variables, "test", log)
        # Escaped syntax renders as literal {{PROJECT_NAME}}
        assert result == "Use {{PROJECT_NAME}} in docs"

    def test_escaped_multiple(self, sample_variables: dict) -> None:
        log = SyncLog()
        result = substitute("{{%A%}} and {{%B%}}", sample_variables, "test", log)
        assert result == "{{A}} and {{B}}"

    def test_runtime_placeholders_skipped(self, sample_variables: dict) -> None:
        """PAL_*, agent, task, A2A_ENVELOPE are skipped silently."""
        log = SyncLog()
        result = substitute("{{agent}} {{task}} {{A2A_ENVELOPE}}", sample_variables, "test", log)
        assert result == "{{agent}} {{task}} {{A2A_ENVELOPE}}"
        assert len(log.warnings) == 0

    def test_pal_prefix_skipped(self, sample_variables: dict) -> None:
        log = SyncLog()
        result = substitute("{{PAL_ORCHESTRATOR}}", sample_variables, "test", log)
        assert result == "{{PAL_ORCHESTRATOR}}"
        assert len(log.warnings) == 0

    def test_no_placeholders_returns_unchanged(self, sample_variables: dict) -> None:
        log = SyncLog()
        result = substitute("Plain text without placeholders.", sample_variables, "test", log)
        assert result == "Plain text without placeholders."

    def test_mixed_known_unknown(self, sample_variables: dict) -> None:
        log = SyncLog()
        result = substitute("{{PROJECT_NAME}} + {{BAD_VAR}}", sample_variables, "test", log)
        assert result == "TestProject + {{BAD_VAR}}"
        assert len(log.warnings) == 1


# ---------------------------------------------------------------------------
# strip_inactive_conditional_blocks
# ---------------------------------------------------------------------------


class TestStripInactiveConditionalBlocks:

    def test_if_block_true_kept(self, sample_variables: dict) -> None:
        """Active {{#if VAR}} blocks should keep their content."""
        text = "Start\n{{#if ORCHESTRATOR_ENABLED}}\nOrchestrator is active\n{{/if}}\nEnd"
        result = strip_inactive_conditional_blocks(text, sample_variables)
        assert "Orchestrator is active" in result

    def test_if_block_false_removed(self, sample_variables: dict) -> None:
        """Inactive {{#if VAR}} blocks should be removed entirely."""
        text = "Start\n{{#if DOD_REQ_TRACEABILITY}}\nTraceability\n{{/if}}\nEnd"
        result = strip_inactive_conditional_blocks(text, sample_variables)
        assert "Traceability" not in result
        assert "{{#if" not in result
        assert "{{/if}}" not in result
        assert "Start" in result
        assert "End" in result

    def test_if_else_true_branch(self, sample_variables: dict) -> None:
        """When VAR is true, the true branch wins."""
        text = "{{#if ORCHESTRATOR_ENABLED}}\nACTIVE\n{{else}}\nINACTIVE\n{{/if}}"
        result = strip_inactive_conditional_blocks(text, sample_variables)
        assert "ACTIVE" in result
        assert "INACTIVE" not in result

    def test_if_else_false_branch(self, sample_variables: dict) -> None:
        """When VAR is false, the else branch wins."""
        text = "{{#if DOD_REQ_TRACEABILITY}}\nTRACE_ENABLED\n{{else}}\nTRACE_DISABLED\n{{/if}}"
        result = strip_inactive_conditional_blocks(text, sample_variables)
        assert "TRACE_DISABLED" in result
        assert "TRACE_ENABLED" not in result

    def test_unless_true_var_removes_content(self, sample_variables: dict) -> None:
        """{{#unless VAR}} removes content when VAR is true."""
        text = "Start\n{{#unless ORCHESTRATOR_ENABLED}}\nHidden\n{{/unless}}\nEnd"
        result = strip_inactive_conditional_blocks(text, sample_variables)
        assert "Hidden" not in result
        assert "Start" in result
        assert "End" in result

    def test_unless_false_var_keeps_content(self, sample_variables: dict) -> None:
        """{{#unless VAR}} keeps content when VAR is false."""
        text = "Start\n{{#unless DOD_REQ_TRACEABILITY}}\nNoTrace\n{{/unless}}\nEnd"
        result = strip_inactive_conditional_blocks(text, sample_variables)
        assert "NoTrace" in result

    def test_no_conditionals_unchanged(self) -> None:
        text = "Plain text"
        result = strip_inactive_conditional_blocks(text, {})
        assert result == "Plain text"

    def test_handles_dod_vars(self) -> None:
        """DOD_ vars are in the conditional set."""
        text = "{{#if DOD_SECURITY_AUDIT}}SecAudit{{/if}}"
        vars_ = {"DOD_SECURITY_AUDIT": "false"}
        result = strip_inactive_conditional_blocks(text, vars_)
        assert "SecAudit" not in result

    def test_handles_pipeline_vars(self) -> None:
        """PIPELINE_*_ENABLED vars are in the conditional set."""
        text = "{{#if PIPELINE_BUILD_ENABLED}}Build{{/if}}"
        vars_ = {"PIPELINE_BUILD_ENABLED": "true"}
        result = strip_inactive_conditional_blocks(text, vars_)
        assert "Build" in result


# ---------------------------------------------------------------------------
# build_variables
# ---------------------------------------------------------------------------


class TestBuildVariables:
    def test_builds_basic_variables(
        self, sample_project_yaml: Path, agent_meta_root: Path,
        sample_dod_presets_yaml: Path, sample_providers_yaml: Path,
        sample_role_defaults_yaml: Path,
    ) -> None:
        """build_variables returns a dict with all expected keys."""
        from scripts.lib.config import load_config
        config = load_config(sample_project_yaml)
        variables, warnings = build_variables(config, agent_meta_root)

        assert variables["PROJECT_NAME"] == "test-project"
        assert variables["PROJECT_SHORT"] == "TP"
        assert variables["AGENT_META_VERSION"] == "0.57.1"
        assert variables["DOD_PRESET"] == "rapid-prototyping"
        # Dod expanded
        assert variables["DOD_REQ_TRACEABILITY"] == "false"
        assert variables["DOD_TESTS_REQUIRED"] == "false"
        assert isinstance(variables, dict)


# ---------------------------------------------------------------------------
# fill_defaults
# ---------------------------------------------------------------------------


class TestFillDefaults:
    def test_fills_missing_fields(
        self, temp_dir: Path, agent_meta_root: Path,
    ) -> None:
        """Missing top-level fields get defaults."""
        config_path = temp_dir / "project.yaml"
        config_path.write_text("project:\n  name: fill-test\n", encoding="utf-8")
        log = SyncLog()
        fill_defaults(config_path, agent_meta_root, log, dry_run=False)

        from scripts.lib.config import load_config
        config = load_config(config_path)
        assert config["dod-preset"] == "full"
        assert config["max-parallel-agents"] == 2
        assert config["speech-mode"] == "full"

    def test_dry_run_does_not_write(
        self, temp_dir: Path, agent_meta_root: Path,
    ) -> None:
        """dry_run=True should not modify the file."""
        config_path = temp_dir / "project.yaml"
        original = "project:\n  name: dry-run-test\n"
        config_path.write_text(original, encoding="utf-8")
        log = SyncLog()
        fill_defaults(config_path, agent_meta_root, log, dry_run=True)

        assert config_path.read_text(encoding="utf-8") == original
