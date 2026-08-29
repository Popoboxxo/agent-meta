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
                       drives on its main path (sync.py:1133-1145, which —
                       unlike validate_test_repo at sync.py:396-403 — passes
                       platform_vars into sync_agents_for_provider/sync_rules,
                       so {{platform.hacs.*}} substitution is exercised):
                       sync_agents_for_provider + sync_rules.

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
  A4. Claude is the only channel:skill provider (skill_channel.PROVIDERS);
      every other provider falls back to a plain rules_dir file.
"""

import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.agents import collect_sources, role_from_platform_file, sync_agents_for_provider
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
            (name, src) for src, name in collect_rule_sources(agent_meta_root, ["hacs"])
        )
        assert "integration-development.md" in sources  # hacs- prefix stripped (rules.py:141)
        assert sources["integration-development.md"].name == "hacs-integration-development.md"

    def test_req534_tier2_collect_rule_sources_negative_without_hacs_platform(self, tmp_path):
        """REQ-534: without platforms:[hacs] the hacs rule is NOT collected (dead weight only)."""
        agent_meta_root = tmp_path / "agent-meta"
        _make_synthetic_agent_meta(agent_meta_root)

        for platforms in ([], ["homeassistant"], ["agent-meta"]):
            names = [name for _, name in collect_rule_sources(agent_meta_root, platforms)]
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
        sources = collect_rule_sources(_REPO_ROOT, ["hacs"])
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
            rules_dir=provider_config["Gemini"].get("rules_dir"), provider="Gemini",
            provider_config=provider_config,
        )
        gemini_rule = project_root / ".gemini" / "rules" / "integration-development.md"
        assert gemini_rule.exists()
        gemini_text = gemini_rule.read_text(encoding="utf-8")
        assert _HACS_OVERRIDES["integration_repo_url"] in gemini_text
        assert "{{platform." not in gemini_text
