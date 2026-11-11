"""Regression tests for the HACS platform preset activation (Issue #534).

Contract source: docs/plans/hacs-platform-preset-audit.md
  - Section 3  — test gap: scripts/lib/platform.py had zero test coverage
  - Section 5  — platform-config loading semantics (defaults path, override
                 file, flatten, skip-silently, required-empty warnings)
  - Section 7.2 — recommended 3-tier test path
  - Section 10 — implementation spec (file paths / keys)

Run:  python -m pytest tests/test_platform_hacs_preset.py -q
Hint: in local environments run with PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 so no
      unrelated pytest plugins (browser/orchestration fixtures) autoload —
      this suite is pure stdlib + pytest + PyYAML.

Tiers (mirroring audit Section 7.2):
  1. Config-Load     — load_platform_config(): defaults file, project
                       overrides, flatten, missing-file "skip silently",
                       required-empty warnings; substitute_platform().
  2. Collection      — collect_rule_sources / collect_command_sources /
                       collect_hook_sources gate hacs-* files on
                       platforms:[hacs] (incl. negative test WITHOUT the
                       platform); role_from_platform_file / collect_sources
                       map hacs-<role>.md → <role>.
  3. Temp-project    — a minimal consumer project (built in pytest tmp_path,
                       zero repo pollution) with platforms:[hacs] is synced
                       via the same lib entry points `python scripts/sync.py`
                       drives on its main path (_handle_sync in
                       lib/cli_commands.py, which — unlike validate_test_repo
                       also in lib/cli_commands.py — passes platform_vars into
                       sync_agents_for_provider/sync_rules,
                       so {{platform.hacs.*}} substitution is exercised):
                       sync_agents_for_provider + sync_rules.

Addendum (Issue #534, Release-Naming-Best-Practice): Tier-2 content-contract
tests pin the release-naming block across the skill source and the
hacs-release / hacs-developer agent anchors (section header, vX.Y.Zb<N>
beta-tag example, anchor presence, example consistency skill ↔ agents).

Encoding of the "temp project + sync.py run" (Tier 3): pytest builds the
consumer project (project config dict with platforms/roles/rules plus
.claude/platform-config.yaml overrides) inside tmp_path and invokes the lib
functions with the exact argument shapes of the sync.py main loop. This is
the audited replacement for a subprocess run (audit Section 7.2, tier 3)
and keeps the test hermetic.

Assumptions baked in from the audit (Section 10) — update here if the
contract changes:
  A1. platform-configs/hacs.defaults.yaml defines exactly five keys:
      custom_components_path (working default "custom_components") plus the
      four required-empty live references integration_repo_url,
      reference_repo_url, project_skills, dev_instance_url (10.1.1).
  A2. rules/2-platform/hacs-integration-development.md has NO frontmatter,
      starts with "# HACS Integration Development", and references all five
      {{platform.hacs.*}} placeholders (10.1.2 / Section 9).
  A3. Output filenames are platform-prefix-STRIPPED: the collected output
      stem is "integration-development" (rules.py:141 strips "<platform>-"),
      so the skill lands at .claude/skills/integration-development/SKILL.md
      and the non-skill-channel fallback at .gemini/rules/
      integration-development.md. The audit's Section 7.2/10.2.4 literal
      paths ".claude/skills/hacs-integration-development/..." are not
      producible by the engine — Section 4.1 documents the stem-keying
      contract (same mechanics that render agent-meta-conventions.md to
      .claude/skills/conventions/SKILL.md), so the rules-presets.yaml entry
      MUST be keyed by the stripped stem. The Tier-2 preset test asserts the
      effective resolution and therefore fails while the preset key is the
      inert literal from 10.2.4.
  A4. Claude is the only channel:skill provider (the "native-skill-channel"
      capability in config/ai-providers.yaml); every other provider falls
      back to a plain rules_dir file.
"""

import __future__
import ast
import asyncio
import builtins
import enum
import logging
import re
import sys
from pathlib import Path
from types import SimpleNamespace
from typing import Optional
from unittest.mock import AsyncMock, MagicMock, call

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.agent_sync import sync_agents_for_provider
from lib.frontmatter import collect_sources, role_from_platform_file
from lib.commands import collect_command_sources
from lib.config import build_variables, load_config
from lib.hooks import collect_hook_sources
from lib.log import SyncLog
from lib.platform import load_platform_config, substitute_platform
from lib.providers import load_providers_config
from lib.rules import collect_rule_sources, resolve_rules, sync_rules


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    """Create parent dirs and write UTF-8 text (same style as other suites)."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _frontmatter_block(text: str) -> str:
    """Return the leading YAML frontmatter block (--- ... ---) or ''. """
    if not text.startswith("---"):
        return ""
    end = text.find("\n---", 3)
    if end == -1:
        return ""
    return text[: end + 4]


# Section 10.1.1 key contract: one working default + four required-empty.
_HACS_DEFAULT_KEYS = ("custom_components_path",)
_HACS_REQUIRED_KEYS = (
    "dev_instance_url",
    "integration_repo_url",
    "reference_repo_url",
    "project_skills",
)

# Project override values used wherever a consumer project is simulated.
_HACS_OVERRIDES = {
    "custom_components_path": "custom_components",
    "dev_instance_url": "http://homeassistant.local:8123",
    "integration_repo_url": "https://github.com/example/ha-cool-integration",
    "reference_repo_url": "https://github.com/home-assistant/core",
    "project_skills": "hacs-integration-development,hacs-integration-review",
}


def _override_yaml(overrides: dict) -> str:
    lines = ["platform:", "  hacs:"]
    for key, value in overrides.items():
        lines.append(f'    {key}: "{value}"')
    return "\n".join(lines) + "\n"


# Files committed with the platform override set (audit Section 2.1).
_HACS_AGENT_FILES = (
    ("hacs-code-reviewer.md", "code-reviewer"),
    ("hacs-developer.md", "developer"),
    ("hacs-devops-engineer.md", "devops-engineer"),
    ("hacs-release.md", "release"),
    ("hacs-tester.md", "tester"),
)

_UNRESOLVED_VAR_RE = re.compile(r"Variable ([A-Z0-9_]+) not in config")
_UPPER_PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def _warned_variables(log: SyncLog) -> set:
    """Variable names substitute() warned about (config.py warn-and-continue)."""
    warned = set()
    for warning in log.warnings:
        match = _UNRESOLVED_VAR_RE.search(warning)
        if match:
            warned.add(match.group(1))
    return warned


def _unexpected_uppercase_residue(text: str, warned: set) -> set:
    """{{UPPERCASE}} placeholders left in output beyond the warned set.

    Mirrors the audit tier-3 acceptance: "no {{UPPERCASE}} residue beyond the
    warn-list". PAL_* placeholders are exempt — substitute() deliberately
    leaves them for the delegation-syntax engine (config.py:1217).
    """
    return {
        name
        for name in _UPPER_PLACEHOLDER_RE.findall(text)
        if name not in warned and not name.startswith("PAL_")
    }


def _make_synthetic_agent_meta(root: Path) -> None:
    """Minimal agent-meta source tree exercising the hacs preset mechanics.

    Mirrors the real structure that matters for the regression:
    role-defaults + composition override with a {{platform.hacs.*}}
    placeholder + a platform rule + rules-presets lazy entry + defaults file.
    """
    _write(
        root / "config" / "role-defaults.yaml",
        "roles:\n  developer:\n    model: \"\"\n",
    )
    _write(
        root / "agents" / "1-generic" / "developer.md",
        "---\n"
        "name: developer\n"
        "version: \"1.0.0\"\n"
        "description: \"Generic developer agent\"\n"
        "prompt_mode: modern\n"
        "---\n"
        "<persona>\n\n"
        "Base persona: implements features and fixes bugs.\n"
        "</persona>\n\n"
        "<context>\n\n"
        "Base context: repository conventions apply.\n"
        "</context>\n",
    )
    _write(
        root / "agents" / "2-platform" / "hacs-developer.md",
        "---\n"
        "name: developer\n"
        "version: \"1.0.0\"\n"
        "description: \"HACS developer agent\"\n"
        "prompt_mode: modern\n"
        "extends: \"1-generic/developer.md\"\n"
        "patches:\n"
        "  - op: append-after\n"
        "    anchor: \"<persona>\"\n"
        "    content: |\n"
        "      HACS platform patch: custom components live under\n"
        "      {{platform.hacs.custom_components_path}}/<domain>/.\n"
        "---\n",
    )
    _write(
        root / "rules" / "2-platform" / "hacs-integration-development.md",
        "# HACS Integration Development\n\n"
        "Live reference: {{platform.hacs.integration_repo_url}}\n\n"
        "Dev instance: {{platform.hacs.dev_instance_url}}\n",
    )
    _write(
        root / "config" / "rules-presets.yaml",
        "presets:\n"
        "  default: {}\n"
        "  lazy:\n"
        "    integration-development:\n"
        "      channel: skill\n"
        "      skill-description: \"Use when developing a HACS custom integration.\"\n",
    )
    _write(
        root / "platform-configs" / "hacs.defaults.yaml",
        "platform:\n"
        "  hacs:\n"
        "    custom_components_path: \"custom_components\"\n"
        "    dev_instance_url: \"\"\n"
        "    integration_repo_url: \"\"\n",
    )


def _make_consumer_project(project_root: Path, overrides: dict) -> None:
    """Minimal consumer project with .claude/platform-config.yaml overrides."""
    project_root.mkdir(parents=True, exist_ok=True)
    if overrides:
        _write(project_root / ".claude" / "platform-config.yaml", _override_yaml(overrides))


def _synthetic_provider_config() -> dict:
    return {
        "Claude": {
            "agents_dir": ".claude/agents",
            "skills_dir": ".claude/skills",
            "rules_dir": ".claude/rules",
            "has_rules": True,
            "capabilities": ["native-skill-channel"],
        },
        "Gemini": {
            "agents_dir": ".gemini/agents",
            "skills_dir": ".gemini/skills",
            "rules_dir": ".gemini/rules",
            "has_rules": True,
        },
    }


# ---------------------------------------------------------------------------
# Tier 1 — Config-Load (scripts/lib/platform.py::load_platform_config)
# ---------------------------------------------------------------------------


class TestTier1PlatformConfigLoad:
    """Audit Section 5 + 7.2 tier 1: platform-config loading semantics."""

    def test_req534_tier1_load_platform_config_loads_hacs_defaults_and_flattens(self, tmp_path):
        """REQ-534: defaults file keys are flattened to platform.hacs.* keys."""
        agent_meta_root = tmp_path / "agent-meta"
        project_root = tmp_path / "project"
        _write(
            agent_meta_root / "platform-configs" / "hacs.defaults.yaml",
            "platform:\n"
            "  hacs:\n"
            "    custom_components_path: \"custom_components\"\n"
            "    paths:\n"
            "      tests: \"custom_components/<domain>/tests\"\n",
        )
        project_root.mkdir()
        log = SyncLog()

        flat = load_platform_config(agent_meta_root, project_root, ["hacs"], log)

        assert flat["platform.hacs.custom_components_path"] == "custom_components"
        # Nested YAML is flattened into dot-notation keys (platform.py:13-27).
        assert flat["platform.hacs.paths.tests"] == "custom_components/<domain>/tests"
        assert log.errors == []

    def test_req534_tier1_project_override_wins_over_defaults(self, tmp_path):
        """REQ-534: .claude/platform-config.yaml overrides the defaults file."""
        agent_meta_root = tmp_path / "agent-meta"
        project_root = tmp_path / "project"
        _make_synthetic_agent_meta(agent_meta_root)
        _make_consumer_project(project_root, {"integration_repo_url": "https://github.com/acme/ha-acme"})

        flat = load_platform_config(agent_meta_root, project_root, ["hacs"], SyncLog())

        assert flat["platform.hacs.integration_repo_url"] == "https://github.com/acme/ha-acme"
        # Defaults still contribute untouched keys.
        assert flat["platform.hacs.custom_components_path"] == "custom_components"

    def test_req534_tier1_missing_defaults_file_skips_silently(self, tmp_path):
        """REQ-534: platform without a defaults file contributes nothing, no warning."""
        agent_meta_root = tmp_path / "agent-meta"
        project_root = tmp_path / "project"
        agent_meta_root.mkdir()
        project_root.mkdir()
        log = SyncLog()

        flat = load_platform_config(agent_meta_root, project_root, ["hacs"], log)

        assert flat == {}
        assert log.warnings == []  # "skip silently" (platform.py:74-76)
        assert log.errors == []

    def test_req534_tier1_required_empty_default_warns_until_overridden(self, tmp_path):
        """REQ-534: empty-string default warns; the warning vanishes once overridden."""
        agent_meta_root = tmp_path / "agent-meta"
        project_root = tmp_path / "project"
        _make_synthetic_agent_meta(agent_meta_root)

        unresolved_log = SyncLog()
        load_platform_config(agent_meta_root, project_root, ["hacs"], unresolved_log)
        required_warnings = [w for w in unresolved_log.warnings if "required field" in w]
        assert any(
            "required field {{platform.hacs.integration_repo_url}} is empty" in w
            for w in required_warnings
        )
        assert any(
            "required field {{platform.hacs.dev_instance_url}} is empty" in w
            for w in required_warnings
        )

        overridden_project = tmp_path / "project-overridden"
        _make_consumer_project(overridden_project, {"integration_repo_url": "https://github.com/acme/ha-acme"})
        resolved_log = SyncLog()
        flat = load_platform_config(agent_meta_root, overridden_project, ["hacs"], resolved_log)
        assert flat["platform.hacs.integration_repo_url"] == "https://github.com/acme/ha-acme"
        assert not any(
            "required field {{platform.hacs.integration_repo_url}}" in w
            for w in resolved_log.warnings
        )

    def test_req534_tier1_substitute_platform_replaces_known_and_keeps_unknown(self, tmp_path):
        """REQ-534: substitute_platform replaces defined keys, warns + keeps unknown, never touches {{UPPERCASE}}."""
        log = SyncLog()
        platform_vars = {"platform.hacs.custom_components_path": "custom_components"}

        text = (
            "Integrations-Repo: {{platform.hacs.custom_components_path}}/<domain>/ — "
            "Projekt: {{PROJECT_NAME}} — Dev-Instanz: {{platform.hacs.unknown_key}}"
        )
        result = substitute_platform(text, platform_vars, "rules/2-platform/hacs-x.md", log)

        assert result.startswith("Integrations-Repo: custom_components/<domain>/ — Projekt: {{PROJECT_NAME}}")
        assert "{{platform.hacs.unknown_key}}" in result  # placeholder remains + warning
        assert any("{{platform.hacs.unknown_key}} not found" in w for w in log.warnings)

    def test_req534_tier1_real_hacs_defaults_yaml_matches_audit_contract(self, tmp_path):
        """REQ-534: shipped platform-configs/hacs.defaults.yaml = Section 10.1.1 contract."""
        defaults_path = _REPO_ROOT / "platform-configs" / "hacs.defaults.yaml"
        assert defaults_path.exists(), "platform-configs/hacs.defaults.yaml is required by audit Section 10.1.1"

        project_root = tmp_path / "consumer"
        project_root.mkdir()
        log = SyncLog()
        flat = load_platform_config(_REPO_ROOT, project_root, ["hacs"], log)

        expected_keys = {
            f"platform.hacs.{key}" for key in _HACS_DEFAULT_KEYS + _HACS_REQUIRED_KEYS
        }
        assert set(flat) == expected_keys  # locked to the shipped 5-key contract
        assert flat["platform.hacs.custom_components_path"] == "custom_components"
        for key in _HACS_REQUIRED_KEYS:
            assert flat[f"platform.hacs.{key}"] == ""

        required_warnings = [w for w in log.warnings if "required field" in w]
        assert len(required_warnings) == len(_HACS_REQUIRED_KEYS)
        for key in _HACS_REQUIRED_KEYS:
            assert any(f"{{platform.hacs.{key}}}" in w for w in required_warnings)


# ---------------------------------------------------------------------------
# Tier 2 — Collection / Role-Mapping gating
# ---------------------------------------------------------------------------


class TestTier2CollectionAndRoleMapping:
    """Audit Section 6 + 7.2 tier 2: hacs-* sources are gated on platforms:[hacs]."""

    def test_req534_tier2_collect_rule_sources_gates_hacs_rule_on_platform(self, tmp_path):
        """REQ-534: the hacs rule is collected (prefix-stripped) only for platforms:[hacs]."""
        agent_meta_root = tmp_path / "agent-meta"
        _make_synthetic_agent_meta(agent_meta_root)

        sources = dict(
            (name, src) for src, name in collect_rule_sources(agent_meta_root, ["hacs"], config={})
        )
        assert "integration-development.md" in sources  # hacs- prefix stripped (rules.py:141)
        assert sources["integration-development.md"].name == "hacs-integration-development.md"

    def test_req534_tier2_collect_rule_sources_negative_without_hacs_platform(self, tmp_path):
        """REQ-534: without platforms:[hacs] the hacs rule is NOT collected (dead weight only)."""
        agent_meta_root = tmp_path / "agent-meta"
        _make_synthetic_agent_meta(agent_meta_root)

        for platforms in ([], ["homeassistant"], ["agent-meta"]):
            names = [name for _, name in collect_rule_sources(agent_meta_root, platforms, config={})]
            assert "integration-development.md" not in names, f"platforms={platforms}"
            assert not any("hacs" in name for name in names), f"platforms={platforms}"

    def test_req534_tier2_collect_command_sources_gates_hacs_commands(self, tmp_path):
        """REQ-534: commands/2-platform/hacs-*.md follow the same platform gating."""
        agent_meta_root = tmp_path / "agent-meta"
        _write(
            agent_meta_root / "commands" / "2-platform" / "hacs-cleanup.md",
            "---\ndescription: HACS cleanup\n---\nBody.\n",
        )

        with_platform = [name for _, name in collect_command_sources(agent_meta_root, ["hacs"])]
        without_platform = [name for _, name in collect_command_sources(agent_meta_root, ["homeassistant"])]

        assert "cleanup.md" in with_platform
        assert without_platform == []

    def test_req534_tier2_collect_hook_sources_gates_hacs_hooks(self, tmp_path):
        """REQ-534: hooks/2-platform/hacs-*.sh follow the same platform gating."""
        agent_meta_root = tmp_path / "agent-meta"
        _write(agent_meta_root / "hooks" / "2-platform" / "hacs-guard.sh", "#!/bin/bash\nexit 0\n")

        with_platform = [name for _, name in collect_hook_sources(agent_meta_root, ["hacs"])]
        without_platform = [name for _, name in collect_hook_sources(agent_meta_root, [])]

        assert "guard.sh" in with_platform
        assert without_platform == []

    @pytest.mark.parametrize(("filename", "expected_role"), _HACS_AGENT_FILES)
    def test_req534_tier2_role_from_platform_file_maps_hacs_roles(self, filename, expected_role):
        """REQ-534: hacs-<role>.md maps to <role> (agents.py:496-501)."""
        assert role_from_platform_file(filename, ["hacs"]) == expected_role

    def test_req534_tier2_role_from_platform_file_negative_matches(self):
        """REQ-534: no role is derived for foreign platforms or unprefixed files."""
        assert role_from_platform_file("hacs-developer.md", ["homeassistant"]) is None
        assert role_from_platform_file("developer.md", ["hacs"]) is None
        assert role_from_platform_file("hacs-developer.md", []) is None

    def test_req534_tier2_real_repo_agent_overrides_map_and_gate(self):
        """REQ-534: the five committed hacs overrides win for platforms:[hacs] only."""
        platform_dir = _REPO_ROOT / "agents" / "2-platform"
        overrides_hacs, _ = collect_sources(_REPO_ROOT, ["hacs"])
        overrides_none, _ = collect_sources(_REPO_ROOT, [])

        for filename, role in _HACS_AGENT_FILES:
            assert (platform_dir / filename).exists(), f"{filename} missing (audit Section 2.1)"
            assert role_from_platform_file(filename, ["hacs"]) == role
            assert overrides_hacs[role] == platform_dir / filename
            # Negative: without the platform the generic template stays in place.
            assert overrides_none[role] != platform_dir / filename
            assert overrides_none[role].parent.name == "1-generic"

    def test_req534_tier2_real_hacs_rule_source_matches_audit_contract(self):
        """REQ-534: shipped rule = Section 10.1.2 (no frontmatter, H1, live-reference placeholders)."""
        rule_path = _REPO_ROOT / "rules" / "2-platform" / "hacs-integration-development.md"
        assert rule_path.exists(), "rules/2-platform/hacs-integration-development.md is required by audit Section 10.1.2"

        content = rule_path.read_text(encoding="utf-8")
        assert not content.startswith("---")  # no frontmatter — skill frontmatter is generated
        assert content.splitlines()[0] == "# HACS Integration Development"
        for key in _HACS_DEFAULT_KEYS + _HACS_REQUIRED_KEYS:
            assert f"{{platform.hacs.{key}}}" in content

    def test_req534_tier2_real_rules_preset_resolves_skill_channel_for_collected_stem(self):
        """REQ-534: rules-presets lazy entry resolves channel:skill for the STRIPPED stem.

        collect_rule_sources strips the platform prefix, and resolve_rules()
        keys options on the output stem (audit Section 4.1). A preset entry
        keyed by the un-stripped literal "hacs-integration-development"
        (audit Section 10.2.4) can never match and is inert — this assertion
        pins the workable contract.
        """
        sources = collect_rule_sources(_REPO_ROOT, ["hacs"], config={})
        stems = {Path(name).stem for _, name in sources}
        assert "integration-development" in stems

        resolved = resolve_rules({"rules-preset": "lazy"}, _REPO_ROOT)
        opts = resolved.get("integration-development")
        assert opts is not None, (
            "config/rules-presets.yaml must key the HACS entry by the stripped output "
            "stem 'integration-development' (the literal 'hacs-integration-development' "
            "key from audit 10.2.4 is inert — see module docstring A3)"
        )
        assert opts.get("channel") == "skill"
        assert (opts.get("skill-description") or "").strip()  # English one-liner per convention


# ---------------------------------------------------------------------------
# Tier 2b — Release-Naming-Best-Practice block (skill source + agent anchors)
# ---------------------------------------------------------------------------

_STABLE_TAG_EXAMPLE = "v1.2.3"
_BETA_TAG_EXAMPLE = "v1.3.0b0"

_HACS_RULE = _REPO_ROOT / "rules" / "2-platform" / "hacs-integration-development.md"
_HACS_RELEASE_AGENT = _REPO_ROOT / "agents" / "2-platform" / "hacs-release.md"
_HACS_DEVELOPER_AGENT = _REPO_ROOT / "agents" / "2-platform" / "hacs-developer.md"


class TestTier2ReleaseNamingBlock:
    """Release-Naming contract across the skill source and the agent anchors.

    The naming block lives in the skill (single source of truth, iron-rule
    style: Regel | Begründung | Fehlerklasse) and is mirrored as compact
    always-on anchors in hacs-release.md (full anchor) and hacs-developer.md
    (one-line tag format in workflow step 6). The literal examples
    v1.2.3 / v1.3.0b0 must stay consistent across all three files.
    """

    def test_req534_tier2_rule_has_release_naming_section_with_six_rules(self):
        """REQ-534: skill carries the Release-Naming section, iron-rule table + sources."""
        content = _HACS_RULE.read_text(encoding="utf-8")
        assert "## Release-Naming-Best-Practice" in content

        section = content.split("## Release-Naming-Best-Practice", 1)[1]
        section = section.split("\n## ", 1)[0]  # cut at the next top-level section

        # Iron-rule table shape: header + 6 data rows (Regel|Begründung|Fehlerklasse).
        assert "| Regel | Begründung | Fehlerklasse bei Verstoß |" in section
        data_rows = [
            line for line in section.splitlines()
            if line.startswith("| ") and "Regel | Begründung" not in line
        ]
        assert len(data_rows) == 6, f"expected 6 naming rules, found {len(data_rows)}"

        # All six rule topics present (tag format, bare semver, beta/pre-release,
        # immutability + promotion, release-notes structure, semver discipline).
        for marker in (
            "vMAJOR.MINOR.PATCH",
            "bare SemVer",
            "vX.Y.Zb<N>",
            "pre-release",
            "nie verschieben, löschen, wiederverwenden",
            "Summary",
            "💥 Breaking changes",
            "Full-Changelog-Link",
            "MAJOR",
            "unique_id",
        ):
            assert marker in section, f"naming section missing marker: {marker}"

        # Research sources documented as URL list inside the section.
        for url in (
            "https://hacs.xyz/docs/publish/start",
            "https://hacs.xyz/docs/use/entities/switch",
            "https://developers.home-assistant.io/docs/versioning",
            "https://semver.org/",
        ):
            assert url in section, f"naming section missing source: {url}"

    def test_req534_tier2_rule_has_tag_examples_in_workflow_step6(self):
        """REQ-534: workflow step 6 (Release-Dreiklang) names stable + beta tag examples."""
        content = _HACS_RULE.read_text(encoding="utf-8")
        assert _STABLE_TAG_EXAMPLE in content
        assert _BETA_TAG_EXAMPLE in content
        # Beta manifest sync example (tag suffix ↔ manifest version).
        assert '"version": "1.3.0b0"' in content

    def test_req534_tier2_release_agent_carries_naming_anchor(self):
        """REQ-534: hacs-release agent carries the always-on Release-Naming anchor."""
        content = _HACS_RELEASE_AGENT.read_text(encoding="utf-8")
        assert "Release-Naming" in content
        assert _STABLE_TAG_EXAMPLE in content
        assert _BETA_TAG_EXAMPLE in content
        assert '"version": "1.3.0b0"' in content
        assert "pre-release" in content.lower()
        assert "nie verschieben, löschen oder wiederverwenden" in content

    def test_req534_tier2_developer_step6_names_tag_format(self):
        """REQ-534: hacs-developer workflow step 6 (Release-Dreiklang) got the tag-format line."""
        content = _HACS_DEVELOPER_AGENT.read_text(encoding="utf-8")
        assert "Release-Dreiklang" in content
        assert _BETA_TAG_EXAMPLE in content

    def test_req534_tier2_beta_tag_example_consistent_across_skill_and_agents(self):
        """REQ-534: the same vX.Y.Zb<N> example (v1.3.0b0) appears in skill AND both agents."""
        texts = {
            "skill": _HACS_RULE.read_text(encoding="utf-8"),
            "hacs-release": _HACS_RELEASE_AGENT.read_text(encoding="utf-8"),
            "hacs-developer": _HACS_DEVELOPER_AGENT.read_text(encoding="utf-8"),
        }
        for name, text in texts.items():
            assert _BETA_TAG_EXAMPLE in text, f"{name} is missing the beta tag example"
            assert re.search(r"v\d+\.\d+\.\d+b\d+", text), f"{name} lacks a vX.Y.Zb<N>-style example"


# ---------------------------------------------------------------------------
# Tier 2c — Entity-registry migration recipe (#1102 await, #1106 A+C)
# ---------------------------------------------------------------------------
#
# Snippet loader: the recipe under "### Entity-Registry-Migration bei
# Umbenennung" is a markdown fence. _migration_recipe_source() extracts it,
# _load_recipe() drops every `from/import homeassistant...` statement (the
# caller supplies those names as stubs in the namespace) and execs the rest.
# PEP 563 is enabled for the exec so HA-only annotation types stay unevaluated.
#
# Contract the recipe must satisfy:
#   - async def async_migrate_entry(hass, entry) -> bool
#   - er.async_migrate_entries(hass, entry.entry_id, <callback>) with the
#     callback as 3rd positional argument; callback(reg_entry) -> dict | None
#   - ir.async_create_issue(..., translation_key=..., is_fixable=..., severity=...)
#   - hass.config_entries.async_update_entry(entry, version=2) exactly once,
#     after the awaited migration
# Namespace names provided by the tests: er, ir, DOMAIN, _LOGGER, HomeAssistant,
# ConfigEntry. Fixture registry: _UID_* / _OLD_EID_* / _NEW_EID_* constants below.

_MIGRATION_SECTION = "### Entity-Registry-Migration bei Umbenennung"
_HACS_CODE_REVIEWER = _REPO_ROOT / "agents" / "2-platform" / "hacs-code-reviewer.md"

_UID_POWER = "health_o_mat_power_old"
_UID_ENERGY = "health_o_mat_energy_old"
_UID_HUMIDITY = "health_o_mat_humidity_old"  # not in the rename map
_OLD_EID_POWER = "sensor.health_o_mat_power_old"
_OLD_EID_ENERGY = "sensor.health_o_mat_energy_old"
_OLD_EID_HUMIDITY = "sensor.health_o_mat_humidity_old"
_NEW_EID_POWER = "sensor.health_o_mat_power"
_NEW_EID_ENERGY = "sensor.health_o_mat_energy"
_USER_RENAMED_EID = "sensor.kitchen_custom_label"

_RECIPE_LOGGER = "custom_components.health_o_mat"
_RENAME_ONLY_KEYS = frozenset({"new_entity_id", "original_name"})


def _migration_recipe_source() -> str:
    """Return the first ```python fence under the migration heading (markdown parse)."""
    text = _HACS_RULE.read_text(encoding="utf-8")
    assert _MIGRATION_SECTION in text, f"heading missing: {_MIGRATION_SECTION}"
    section = text.split(_MIGRATION_SECTION, 1)[1]
    # Cut at the next ## / ### heading; single-# lines are python comments inside the fence.
    section = re.split(r"\n#{2,3} ", section, maxsplit=1)[0]
    fence = re.search(r"^```python\n(.*?)^```[ \t]*$", section, re.S | re.M)
    assert fence, "no ```python fence under the migration heading"
    return fence.group(1)


def _is_ha_import(node: ast.stmt) -> bool:
    """True for homeassistant imports and relative imports (not resolvable in the test)."""
    if isinstance(node, ast.ImportFrom):
        return node.level > 0 or (node.module or "").startswith("homeassistant")
    if isinstance(node, ast.Import):
        return any(alias.name.startswith("homeassistant") for alias in node.names)
    return False


def _load_recipe(namespace: dict) -> None:
    """Exec the recipe into ``namespace`` with homeassistant imports removed."""
    tree = ast.parse(_migration_recipe_source())
    tree.body = [node for node in tree.body if not _is_ha_import(node)]
    code = compile(
        tree,
        "<hacs-rule:entity-registry-migration>",
        "exec",
        flags=__future__.annotations.compiler_flag,
        dont_inherit=True,
    )
    exec(code, namespace)  # trusted repo text, test-only


def _parent_map(tree: ast.AST) -> dict:
    parents = {}
    for node in ast.walk(tree):
        for child in ast.iter_child_nodes(node):
            parents[child] = node
    return parents


def _enclosing_function(node: ast.AST, parents: dict):
    current = parents.get(node)
    while current is not None and not isinstance(current, (ast.FunctionDef, ast.AsyncFunctionDef)):
        current = parents.get(current)
    return current


def _calls_to(tree: ast.AST, attr: str) -> list:
    return [
        node for node in ast.walk(tree)
        if isinstance(node, ast.Call)
        and isinstance(node.func, ast.Attribute)
        and node.func.attr == attr
    ]


def _reg_entry(entity_id: str, unique_id: str, name: str) -> SimpleNamespace:
    """Synthetic RegistryEntry shape (fields HA's registry entry exposes)."""
    return SimpleNamespace(
        entity_id=entity_id,
        unique_id=unique_id,
        name=name,
        original_name=name,
        config_entry_id="entry-1",
        platform="health_o_mat",
        entity_category=None,
        labels=set(),
        aliases=set(),
        area_id=None,
        hidden_by=None,
        disabled_by=None,
    )


def _healthy_entries() -> list:
    return [
        _reg_entry(_OLD_EID_POWER, _UID_POWER, "Power"),
        _reg_entry(_OLD_EID_ENERGY, _UID_ENERGY, "Energy"),
    ]


class _FakeRegistry:
    def __init__(self, entries: list) -> None:
        self.entries = list(entries)

    def async_get(self, entity_id: str):
        return next((e for e in self.entries if e.entity_id == entity_id), None)

    def entity_ids(self) -> set:
        return {e.entity_id for e in self.entries}

    def snapshot(self) -> list:
        return [(e.entity_id, e.original_name, e.unique_id) for e in self.entries]


class _FakeIssueRegistry:
    """Hand-written ``issue_registry`` stand-in with HA's required keyword-only signature.

    A MagicMock would accept a wrong enum member, a missing is_fixable or a None
    translation_key, all of which crash in real HA.
    """

    class IssueSeverity(enum.Enum):
        CRITICAL = "critical"
        ERROR = "error"
        WARNING = "warning"

    def __init__(self) -> None:
        self.issues: dict = {}  # issue_id -> kwargs of the live issue
        self.created: list = []  # issue_id per async_create_issue call

    def async_create_issue(self, hass, domain, issue_id, *, is_fixable, severity,
                           translation_key, translation_placeholders=None, **kw):
        assert isinstance(severity, self.IssueSeverity), f"bad severity {severity!r}"
        assert isinstance(translation_key, str) and translation_key, "translation_key required"
        self.created.append(issue_id)
        self.issues[issue_id] = {"translation_key": translation_key, "domain": domain,
                                 "placeholders": translation_placeholders}

    def async_delete_issue(self, hass, domain, issue_id):
        self.issues.pop(issue_id, None)


def _make_env(entries: list, *, migrate_error: Optional[Exception] = None) -> SimpleNamespace:
    """Stub HA surface. async_migrate_entries drives the callback like HA does.

    HA's async_update_entity raises ValueError when the target id is taken;
    the fake mirrors that. ``returned`` records every dict the callback gave back.
    """
    registry = _FakeRegistry(entries)
    events: list = []   # ordered: ("migrate_done", None) / ("update", kwargs)
    returned: list = [] # (unique_id, dict) for every non-None callback result

    async def _migrate(hass, config_entry_id, callback):
        for reg_entry in list(registry.entries):
            if reg_entry.config_entry_id != config_entry_id:
                continue
            updates = callback(reg_entry)
            if updates is None:
                continue
            returned.append((reg_entry.unique_id, dict(updates)))
            new_id = updates.get("new_entity_id", reg_entry.entity_id)
            if new_id != reg_entry.entity_id and registry.async_get(new_id) is not None:
                raise ValueError(f"Entity id already exists: {new_id}")
            for key, value in updates.items():
                attr = "entity_id" if key == "new_entity_id" else key
                setattr(reg_entry, attr, value)
        events.append(("migrate_done", None))

    er = MagicMock(name="er")
    er.async_migrate_entries = AsyncMock(
        side_effect=migrate_error if migrate_error is not None else _migrate
    )
    er.async_get.return_value = registry
    er.async_entries_for_config_entry.side_effect = (
        lambda reg, cid: [e for e in reg.entries if e.config_entry_id == cid]
    )
    ir = _FakeIssueRegistry()
    hass = MagicMock(name="hass")
    hass.states.async_available.side_effect = lambda eid: eid not in registry.entity_ids()
    hass.config_entries.async_update_entry.side_effect = (
        lambda entry, **kwargs: events.append(("update", kwargs))
    )
    return SimpleNamespace(er=er, ir=ir, hass=hass, registry=registry,
                           events=events, returned=returned)


def _run_recipe(env: SimpleNamespace, *, version: int = 1) -> tuple:
    entry = SimpleNamespace(entry_id="entry-1", version=version)
    namespace = {
        "er": env.er,
        "ir": env.ir,
        "DOMAIN": "health_o_mat",
        "__name__": _RECIPE_LOGGER,  # the recipe's getLogger(__name__) resolves to this
        "_LOGGER": logging.getLogger(_RECIPE_LOGGER),
        "HomeAssistant": object,
        "ConfigEntry": object,
    }
    _load_recipe(namespace)
    # Private loop: asyncio.run() resets the global loop and breaks the HA pytest plugin for later tests.
    loop = asyncio.new_event_loop()
    try:
        result = loop.run_until_complete(namespace["async_migrate_entry"](env.hass, entry))
    finally:
        loop.close()
    return entry, result


def _run_persisted(env: SimpleNamespace, runs: int = 2) -> list:
    """Run the recipe repeatedly; the stored version carries over like in HA."""
    version, results = 1, []
    for _ in range(runs):
        _entry, result = _run_recipe(env, version=version)
        results.append(result)
        for kind, kwargs in env.events:
            if kind == "update" and "version" in kwargs:
                version = kwargs["version"]
    return results


def _warnings(caplog) -> list:
    return [r for r in caplog.records
            if r.levelno == logging.WARNING and r.name == _RECIPE_LOGGER]


class TestTier2EntityMigrationRecipe:
    """Migration recipe contract (#1102: await + single bump; #1106 A+C: safety net).

    Behavioural tests exec the recipe with stub HA objects. The fake
    async_migrate_entries awaits and feeds the callback real-shaped registry
    entries, so a recipe that skips the await never renames anything.
    """

    def test_req534_recipe_awaits_async_migrate_entries_inside_async_def(self):
        """REQ-534: async_migrate_entries call is the operand of an Await in an async def."""
        tree = ast.parse(_migration_recipe_source())
        parents = _parent_map(tree)
        calls = _calls_to(tree, "async_migrate_entries")
        assert len(calls) == 1, f"expected one async_migrate_entries call, found {len(calls)}"
        call_node = calls[0]
        assert isinstance(parents.get(call_node), ast.Await), (
            "async_migrate_entries is called without await: the rename runs after the version bump"
        )
        enclosing = _enclosing_function(call_node, parents)
        assert isinstance(enclosing, ast.AsyncFunctionDef), "await used outside an async def"

    def test_req534_recipe_bumps_version_once_and_only_after_the_await(self):
        """REQ-534: exactly one async_update_entry(..., version=...) call, placed after the await."""
        tree = ast.parse(_migration_recipe_source())
        awaited = [
            node for node in ast.walk(tree)
            if isinstance(node, ast.Await)
            and isinstance(node.value, ast.Call)
            and isinstance(node.value.func, ast.Attribute)
            and node.value.func.attr == "async_migrate_entries"
        ]
        bumps = _calls_to(tree, "async_update_entry")
        assert len(bumps) == 1, f"expected exactly one version bump, found {len(bumps)}"
        assert any(kw.arg == "version" for kw in bumps[0].keywords), "bump lacks version= keyword"
        assert awaited, "no awaited async_migrate_entries to order the version bump against"
        assert bumps[0].lineno > awaited[0].lineno, (
            "version bump is not placed after the awaited async_migrate_entries"
        )

    def test_req534_recipe_happy_path_awaits_then_bumps_version_once(self, caplog):
        """REQ-534: happy path awaits the migration once, then bumps version=2 exactly once."""
        env = _make_env(_healthy_entries())
        entry, result = _run_recipe(env)

        env.er.async_migrate_entries.assert_awaited_once()
        assert result is True
        assert env.registry.async_get(_NEW_EID_POWER) is not None
        assert env.registry.async_get(_NEW_EID_ENERGY) is not None
        assert env.hass.config_entries.async_update_entry.call_args_list == [call(entry, version=2)]
        assert env.events == [("migrate_done", None), ("update", {"version": 2})], (
            f"version bump must follow the completed migration, got {env.events}"
        )

    def test_req534_recipe_collision_skips_entity_warns_creates_issue_no_bump(self, caplog):
        """REQ-534: #1102 — target id already taken -> callback None, warning, repair issue, no bump."""
        caplog.set_level(logging.WARNING)
        entries = _healthy_entries() + [_reg_entry(_NEW_EID_POWER, "unrelated_uid", "Power")]
        env = _make_env(entries)
        _entry, result = _run_recipe(env)

        env.er.async_migrate_entries.assert_awaited_once()
        assert _UID_POWER not in dict(env.returned), "colliding entity must not be renamed"
        assert ("update", {"version": 2}) not in env.events, "version bumped despite collision"
        assert result is False, f"collision must return False, got {result!r}"
        assert _warnings(caplog), "collision produced no warning"
        assert len(env.ir.created) == 1
        assert [i["translation_key"] for i in env.ir.issues.values()] == ["migration_blocked"]
        placeholders = next(iter(env.ir.issues.values()))["placeholders"]
        assert placeholders == {"entities": _NEW_EID_POWER}, "placeholder must carry entity ids"

    def test_req534_recipe_dirty_registry_migrates_rest_warns_and_rerun_is_noop(self, caplog):
        """REQ-534: #1106 — user-renamed entity is skipped with a warning; rest migrates; anchor holds -> bump.

        The mapped entities are power (healthy) and energy (user-renamed); the anchor is
        supported by two OTHER, unmapped entities, so the skip is purely per-entity.
        """
        caplog.set_level(logging.WARNING)
        entries = [
            _reg_entry(_OLD_EID_POWER, _UID_POWER, "Power"),
            _reg_entry(_USER_RENAMED_EID, _UID_ENERGY, "Kitchen Custom"),
            _reg_entry(_OLD_EID_HUMIDITY, _UID_HUMIDITY, "Humidity"),
            _reg_entry("sensor.health_o_mat_other_old", "health_o_mat_other_old", "Other"),
        ]
        env = _make_env(entries)
        result = _run_persisted(env, runs=1)[0]

        assert result is True
        assert env.registry.async_get(_NEW_EID_POWER) is not None, "healthy entity was not migrated"
        assert env.registry.async_get(_USER_RENAMED_EID) is not None, "user-renamed entity was renamed"
        assert _UID_ENERGY not in dict(env.returned)
        assert _warnings(caplog), "user-renamed entity produced no warning"
        assert env.events.count(("update", {"version": 2})) == 1

        before = env.registry.snapshot()
        returned_before = len(env.returned)
        _run_recipe(env, version=2)  # second run starts from the persisted version, like HA
        assert env.events.count(("update", {"version": 2})) == 1, "second run bumped again"
        assert env.registry.snapshot() == before, "second run changed the registry"
        assert len(env.returned) == returned_before, "second run returned further renames"

    def test_req534_recipe_all_mapped_user_renamed_with_anchor_support_bumps(self):
        """REQ-534: #1106 D — every mapped entity user-renamed, anchor held by unmapped others -> bump."""
        env = _make_env([
            _reg_entry("sensor.kitchen_a", _UID_POWER, "A"),
            _reg_entry("sensor.kitchen_b", _UID_ENERGY, "B"),
            _reg_entry(_OLD_EID_HUMIDITY, _UID_HUMIDITY, "Humidity"),
            _reg_entry("sensor.health_o_mat_other_old", "health_o_mat_other_old", "Other"),
        ])
        _entry, result = _run_recipe(env)

        assert result is True
        assert env.returned == []
        assert env.events.count(("update", {"version": 2})) == 1

    def test_req534_recipe_single_entity_unanchored_migrates_warns_bumps_once_no_issue(self, caplog):
        """REQ-534: #1106 A — one entity: rename, ONE anchor warning, bump once, no issue; rerun is a no-op."""
        caplog.set_level(logging.WARNING)
        env = _make_env([_reg_entry(_OLD_EID_POWER, _UID_POWER, "Power")])
        results = _run_persisted(env, runs=2)

        assert results == [True, True]
        assert env.registry.async_get(_NEW_EID_POWER) is not None, "healthy single entity was not migrated"
        assert len(_warnings(caplog)) == 1, "expected exactly one anchor warning (second run is guarded)"
        assert env.events.count(("update", {"version": 2})) == 1, "expected exactly one bump"
        assert env.ir.created == [], "repair issue created although nothing is broken"

    def test_req534_recipe_one_user_renamed_without_other_anchor_support_bumps_once(self, caplog):
        """REQ-534: #1106 A — 2 entities, one user-renamed -> healthy one migrates, one warning pair, bump once."""
        caplog.set_level(logging.WARNING)
        env = _make_env([
            _reg_entry(_OLD_EID_POWER, _UID_POWER, "Power"),
            _reg_entry(_USER_RENAMED_EID, _UID_ENERGY, "Kitchen Custom"),
        ])
        results = _run_persisted(env, runs=2)

        assert results == [True, True]
        assert env.registry.async_get(_NEW_EID_POWER) is not None, "healthy entity was not migrated"
        assert env.registry.async_get(_USER_RENAMED_EID) is not None
        warnings = " | ".join(r.getMessage() for r in _warnings(caplog))
        assert "user-renamed" in warnings and "Anchor" in warnings
        assert env.events.count(("update", {"version": 2})) == 1
        assert env.ir.created == []

    def test_req534_recipe_error_path_warns_creates_repair_issue_no_bump(self, caplog):
        """REQ-534: #1106 C — ValueError from the registry -> warning + repair issue, version kept."""
        caplog.set_level(logging.WARNING)
        env = _make_env(_healthy_entries(), migrate_error=ValueError("entity id already exists"))
        try:
            _entry, result = _run_recipe(env)
        except ValueError as exc:
            pytest.fail(f"migration raised {exc!r}; expected warning + repair issue instead")

        assert result is False
        assert _warnings(caplog), "registry error produced no warning"
        assert len(env.ir.created) == 1
        assert [i["translation_key"] for i in env.ir.issues.values()] == ["migration_blocked"]
        assert ("update", {"version": 2}) not in env.events, "version bumped after failed migration"
        placeholders = next(iter(env.ir.issues.values()))["placeholders"]
        assert "already exists" not in placeholders["entities"], "error text leaked into entities placeholder"
        assert _NEW_EID_POWER in placeholders["entities"]

    def test_req534_recipe_callback_returns_only_rename_fields(self, caplog):
        """REQ-534: callback returns only new_entity_id/original_name; registry metadata is preserved."""
        env = _make_env(_healthy_entries())
        _run_recipe(env)

        returned = dict(env.returned)
        assert {_UID_POWER, _UID_ENERGY} <= set(returned), "recipe returned no rename for mapped entities"
        for uid, updates in returned.items():
            assert "new_entity_id" in updates, f"{uid}: no new_entity_id in callback result"
            assert set(updates) <= _RENAME_ONLY_KEYS, f"{uid}: unexpected keys {set(updates) - _RENAME_ONLY_KEYS}"

    def test_req534_recipe_version_guard_skips_when_already_v2(self):
        """REQ-534: entry.version >= 2 -> no migration, no bump, True."""
        env = _make_env(_healthy_entries())
        _entry, result = _run_recipe(env, version=2)

        assert result is True
        env.er.async_migrate_entries.assert_not_awaited()
        env.hass.config_entries.async_update_entry.assert_not_called()

    def test_req534_recipe_collision_resolved_then_rerun_converges(self):
        """REQ-534: collision -> False; blocker removed; rerun -> True, one bump, no second issue."""
        blocker = _reg_entry(_NEW_EID_POWER, "unrelated_uid", "Power")
        env = _make_env(_healthy_entries() + [blocker])
        _entry, first = _run_recipe(env)
        assert first is False
        env.registry.entries.remove(blocker)  # user resolves the collision

        _entry, second = _run_recipe(env)
        assert second is True
        assert env.registry.async_get(_NEW_EID_POWER).unique_id == _UID_POWER
        assert env.events.count(("update", {"version": 2})) == 1
        assert len(env.ir.created) == 1, "clean rerun created another issue"

    def test_req534_recipe_success_after_failure_deletes_repair_issue(self):
        """REQ-534: a resolved collision clears the stale repair issue."""
        blocker = _reg_entry(_NEW_EID_POWER, "unrelated_uid", "Power")
        env = _make_env(_healthy_entries() + [blocker])
        _run_recipe(env)
        assert len(env.ir.issues) == 1, "collision did not create a repair issue"
        env.registry.entries.remove(blocker)

        _entry, result = _run_recipe(env)
        assert result is True
        assert env.ir.issues == {}, "repair issue survived the successful migration"

    def test_req534_recipe_snippet_binds_every_definition_time_name(self):
        """REQ-534: annotations/decorators/defaults only use names the snippet imports or defines."""
        tree = ast.parse(_migration_recipe_source())
        bound = set(dir(builtins))
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                bound |= {(a.asname or a.name).split(".")[0] for a in node.names}
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                bound.add(node.name)
            elif isinstance(node, (ast.Assign, ast.AnnAssign)):
                targets = node.targets if isinstance(node, ast.Assign) else [node.target]
                bound |= {n.id for t in targets for n in ast.walk(t) if isinstance(n, ast.Name)}
        used: set = set()
        for fn in ast.walk(tree):
            if not isinstance(fn, (ast.FunctionDef, ast.AsyncFunctionDef)):
                continue
            a = fn.args
            exprs = [*fn.decorator_list, *a.defaults, *(d for d in a.kw_defaults if d), fn.returns,
                     *(x.annotation for x in [*a.posonlyargs, *a.args, *a.kwonlyargs] if x.annotation)]
            used |= {n.id for e in exprs if e for n in ast.walk(e) if isinstance(n, ast.Name)}
        assert not used - bound, f"snippet uses unimported names: {sorted(used - bound)}"

    def test_req534_reviewer_f4_requires_await_for_migration(self):
        """REQ-534: reviewer F4 names the missing await as a fail predicate."""
        text = _HACS_CODE_REVIEWER.read_text(encoding="utf-8")
        f4 = [line for line in text.splitlines() if "**F4**" in line]
        assert len(f4) == 1, f"expected exactly one F4 line, found {len(f4)}"
        assert "await er.async_migrate_entries" in f4[0], "F4 does not require await er.async_migrate_entries"
        assert "MagicMock" in f4[0], "F4 does not fail a MagicMock-mocked migration"


# ---------------------------------------------------------------------------
# Tier 3 — Temp-project sync (the regression the task asks for)
# ---------------------------------------------------------------------------


class TestTier3TempProjectSync:
    """Audit Section 7.2 tier 3: sync a minimal consumer project in tmp_path."""

    def test_req534_tier3_synthetic_sync_composes_agent_and_substitutes_placeholders(self, tmp_path):
        """REQ-534: hacs override composes onto the base agent; {{platform.hacs.*}} fully substituted."""
        agent_meta_root = tmp_path / "agent-meta"
        project_root = tmp_path / "consumer"
        _make_synthetic_agent_meta(agent_meta_root)
        _write(
            project_root / ".claude" / "platform-config.yaml",
            "platform:\n  hacs:\n    custom_components_path: \"custom_components_live\"\n",
        )
        log = SyncLog()
        platform_vars = load_platform_config(agent_meta_root, project_root, ["hacs"], log)

        config = {"platforms": ["hacs"], "project": {"name": "hacs-regression"}}
        sync_agents_for_provider(
            agent_meta_root, project_root, config, {"PROJECT_NAME": "hacs-regression"},
            log, dry_run=False, provider="Claude",
            provider_config=_synthetic_provider_config(), platform_vars=platform_vars,
        )

        agent_path = project_root / ".claude" / "agents" / "developer.md"
        assert agent_path.exists()
        text = agent_path.read_text(encoding="utf-8")
        # Composition applied: base AND platform patch both present.
        assert "Base persona: implements features and fixes bugs." in text
        assert "HACS platform patch" in text
        # Composition metadata stripped from the output frontmatter (agents.py:910-911).
        frontmatter = _frontmatter_block(text)
        assert frontmatter
        assert "extends" not in frontmatter
        assert "patches" not in frontmatter
        # Placeholder substitution: no raw {{ at all, substituted value present.
        assert "{{" not in text
        assert "custom_components_live" in text

    def test_req534_tier3_synthetic_sync_routes_hacs_rule_to_skill_md(self, tmp_path):
        """REQ-534: Claude renders the hacs rule as SKILL.md with generated frontmatter.

        Substituted key → value inline; a defined-but-unoverridden required
        key is substituted to an EMPTY string and warns (platform.py:89-94
        warns at load time; substitute_platform replaces the key because it IS
        in platform_vars). Only keys absent from platform_vars entirely keep
        their literal placeholder — pinned in the Tier-1 substitute test.
        """
        agent_meta_root = tmp_path / "agent-meta"
        project_root = tmp_path / "consumer"
        _make_synthetic_agent_meta(agent_meta_root)
        # Only integration_repo_url is overridden — dev_instance_url stays required-empty.
        _write(
            project_root / ".claude" / "platform-config.yaml",
            "platform:\n"
            "  hacs:\n"
            "    integration_repo_url: \"https://github.com/example/ha-cool-integration\"\n",
        )
        log = SyncLog()
        platform_vars = load_platform_config(agent_meta_root, project_root, ["hacs"], log)

        config = {
            "platforms": ["hacs"],
            "project": {"name": "hacs-regression"},
            "rules-preset": "lazy",
        }
        sync_rules(
            agent_meta_root, project_root, config, log, dry_run=False,
            platform_vars=platform_vars, variables={}, provider="Claude",
            provider_config=_synthetic_provider_config(),
            active_set=frozenset(),
        )

        skill_path = project_root / ".claude" / "skills" / "integration-development" / "SKILL.md"
        rule_path = project_root / ".claude" / "rules" / "integration-development.md"
        assert skill_path.exists()
        assert not rule_path.exists()  # channel: skill replaces the plain rules_dir file
        skill_text = skill_path.read_text(encoding="utf-8")
        # Generated frontmatter (skill_channel.py:79-83): name + quoted description.
        assert skill_text.startswith("---\nname: integration-development\ndescription: \"Use when developing a HACS custom integration.\"\n")
        # Substituted override value present, no platform residue.
        assert "https://github.com/example/ha-cool-integration" in skill_text
        assert "{{platform.hacs.integration_repo_url}}" not in skill_text
        # Required-empty, unoverridden: warn at load time + substituted to "".
        assert "{{platform.hacs.dev_instance_url}}" not in skill_text
        assert "Dev instance: \n" in skill_text
        assert any("required field {{platform.hacs.dev_instance_url}} is empty" in w for w in log.warnings)

    def test_req534_tier3_synthetic_sync_without_platform_negates_hacs_output(self, tmp_path):
        """REQ-534: negative — a project without platforms:[hacs] gets no HACS artifacts."""
        agent_meta_root = tmp_path / "agent-meta"
        project_root = tmp_path / "consumer"
        _make_synthetic_agent_meta(agent_meta_root)
        project_root.mkdir(parents=True)
        log = SyncLog()
        platform_vars = load_platform_config(agent_meta_root, project_root, [], log)
        assert platform_vars == {}

        config = {"platforms": [], "project": {"name": "plain-consumer"}}
        sync_agents_for_provider(
            agent_meta_root, project_root, config, {"PROJECT_NAME": "plain-consumer"},
            log, dry_run=False, provider="Claude",
            provider_config=_synthetic_provider_config(), platform_vars=platform_vars,
        )
        sync_rules(
            agent_meta_root, project_root, config, log, dry_run=False,
            platform_vars=platform_vars, variables={}, provider="Claude",
            provider_config=_synthetic_provider_config(),
            active_set=frozenset(),
        )

        agent_text = (project_root / ".claude" / "agents" / "developer.md").read_text(encoding="utf-8")
        assert "HACS platform patch" not in agent_text  # generic developer only
        assert not (project_root / ".claude" / "skills" / "integration-development").exists()
        assert not (project_root / ".claude" / "rules" / "integration-development.md").exists()

    def test_req534_tier3_real_repo_temp_project_sync_generates_hacs_agents_and_skill(self, tmp_path):
        """REQ-534: full regression — real repo sources → temp consumer project.

        Mirrors the sync.py main-path call shape (sync.py:1133-1145) including
        platform_vars. Asserts: the five hacs-gated agents are generated, the
        developer agent carries the HACS persona/workflow sections without
        composition metadata, platform placeholders are substituted
        (override values present, zero {{platform. residue), the hacs rule is
        routed to the Claude skill channel, and non-skill-channel providers
        (Gemini) fall back to a plain rules_dir file.
        """
        project_root = tmp_path / "hacs-consumer"
        _make_consumer_project(project_root, _HACS_OVERRIDES)

        config = load_config(_REPO_ROOT / ".meta-config" / "project.yaml")
        config["platforms"] = ["hacs"]
        config["project"] = {"name": "hacs-regression-consumer", "prefix": "hrc", "short": "HRC"}
        config["roles"] = [role for _, role in _HACS_AGENT_FILES]
        # Project-level override pins the channel decision independent of the
        # rules-presets.yaml key spelling (that contract is Tier-2's job).
        config["rules"] = {
            "integration-development": {
                "channel": "skill",
                "skill-description": "Use when developing a HACS custom integration.",
            },
        }

        log = SyncLog()
        variables, _pre_warnings = build_variables(config, _REPO_ROOT, project_root)
        platform_vars = load_platform_config(_REPO_ROOT, project_root, ["hacs"], log)
        provider_config = load_providers_config(_REPO_ROOT)
        claude_pc = provider_config["Claude"]

        sync_agents_for_provider(
            _REPO_ROOT, project_root, config, variables, log, dry_run=False,
            provider="Claude", provider_config=provider_config,
            platform_vars=platform_vars,
        )
        sync_rules(
            _REPO_ROOT, project_root, config, log, dry_run=False,
            platform_vars=platform_vars, variables=variables,
            rules_dir=claude_pc.get("rules_dir"), provider="Claude",
            provider_config=provider_config,
            active_set=frozenset(),
        )

        agents_dir = project_root / ".claude" / "agents"
        generated = {p.name for p in agents_dir.glob("*.md")}
        assert generated == {role + ".md" for _, role in _HACS_AGENT_FILES}

        developer_text = (agents_dir / "developer.md").read_text(encoding="utf-8")
        # Composition applied (markers from the shipped hacs-developer.md patches).
        assert "Eiserne Regeln" in developer_text
        assert "HACS 7-Schritte-Workflow" in developer_text
        frontmatter = _frontmatter_block(developer_text)
        assert frontmatter
        assert "extends" not in frontmatter
        assert "patches" not in frontmatter
        # Platform substitution: override values in, zero residue out.
        assert _HACS_OVERRIDES["integration_repo_url"] in developer_text
        assert _HACS_OVERRIDES["dev_instance_url"] in developer_text
        assert "{{platform." not in developer_text

        skill_path = project_root / ".claude" / "skills" / "integration-development" / "SKILL.md"
        assert skill_path.exists()
        assert not (project_root / ".claude" / "rules" / "integration-development.md").exists()
        skill_text = skill_path.read_text(encoding="utf-8")
        assert skill_text.startswith("---\nname: integration-development\ndescription: \"")
        assert _HACS_OVERRIDES["integration_repo_url"] in skill_text
        assert "{{platform." not in skill_text

        # No {{UPPERCASE}} residue beyond variables substitute() warned about.
        warned = _warned_variables(log)
        for text in (developer_text, skill_text):
            residue = _unexpected_uppercase_residue(text, warned)
            assert not residue, f"unresolved placeholders: {sorted(residue)}"

        # All required keys were overridden — the sync must not warn about them.
        assert not any("required field" in w for w in log.warnings)
        assert log.errors == []

        # Non-skill-channel provider fallback: plain, prefix-stripped rule file.
        sync_rules(
            _REPO_ROOT, project_root, config, SyncLog(), dry_run=False,
            platform_vars=platform_vars, variables=variables,
            rules_dir=".gemini/rules", provider="Gemini",
            provider_config=provider_config,
            active_set=frozenset(),
        )
        gemini_rule = project_root / ".gemini" / "rules" / "integration-development.md"
        assert gemini_rule.exists()
        gemini_text = gemini_rule.read_text(encoding="utf-8")
        assert _HACS_OVERRIDES["integration_repo_url"] in gemini_text
        assert "{{platform." not in gemini_text
