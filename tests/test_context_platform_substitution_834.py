"""Regression tests for issue #834.

``substitute_platform()`` was only wired into the rule/template path
(``rules.py`` / ``agent_sync.py``); the context-file render path
(AGENTS.md, GEMINI.md, …) used the generic ``substitute()`` only, so embedded
platform rules kept their raw ``{{platform.*}}`` placeholders in the generated
context file.

Acceptance criteria (issue #834):
  1. ``substitute_platform()`` is called on the context-render path before write.
  2. The diagnosis distinguishes "key missing in platform-config.yaml" from
     "substitution not applied".
  3. A generated context file contains zero ``{{platform.`` occurrences.

Run:  python -m pytest tests/test_context_platform_substitution_834.py -q
"""

import re
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.config import build_variables, load_config  # noqa: E402
from lib.context import (  # noqa: E402
    _apply_platform_context_substitution,
    sync_context_for_provider,
)
from lib.log import SyncLog  # noqa: E402
from lib.platform import (  # noqa: E402
    load_platform_config,
    substitute_platform,
    warn_unresolved_platform_vars,
)
from lib.providers import load_providers_config  # noqa: E402

_PLATFORM_RE = re.compile(r"\{\{platform\.[^}]+\}\}")

_HACS_OVERRIDES = {
    "integration_repo_url": "https://github.com/acme/ha-acme",
    "reference_repo_url": "https://github.com/home-assistant/core",
    "project_skills": "hacs-integration-development,hacs-integration-review",
    "dev_instance_url": "http://homeassistant.local:8123",
    "custom_components_path": "custom_components",
}


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _write_platform_override(project_root: Path) -> None:
    lines = ["platform:", "  hacs:"]
    for key, value in _HACS_OVERRIDES.items():
        lines.append(f'    {key}: "{value}"')
    _write(project_root / ".claude" / "platform-config.yaml", "\n".join(lines) + "\n")


# ---------------------------------------------------------------------------
# AC 2 — the two diagnoses are distinct and name their real cause.
# ---------------------------------------------------------------------------


def test_missing_key_diagnosis_names_platform_config_file():
    log = SyncLog()
    substitute_platform(
        "x {{platform.hacs.unknown_key}} y",
        {"platform.hacs.known": "v"},
        "ctx/AGENTS.md",
        log,
    )
    assert any(
        "key missing in platform-config.yaml" in w for w in log.warnings
    ), log.warnings


def test_not_applied_diagnosis_is_distinct_from_missing_key():
    log = SyncLog()
    warn_unresolved_platform_vars(
        "repo: {{platform.hacs.integration_repo_url}}",
        {"platform.hacs.integration_repo_url": _HACS_OVERRIDES["integration_repo_url"]},
        "ctx/AGENTS.md",
        log,
    )
    assert any("substitution not applied" in w for w in log.warnings), log.warnings
    # A configured key must NEVER be reported as a configuration gap.
    assert not any("key missing" in w for w in log.warnings), log.warnings


def test_warn_unresolved_reports_missing_key_by_default():
    log = SyncLog()
    warn_unresolved_platform_vars(
        "x {{platform.hacs.absent}} y", {}, "ctx/AGENTS.md", log,
    )
    assert any("key missing in platform-config.yaml" in w for w in log.warnings), log.warnings


def test_warn_unresolved_can_suppress_missing_key():
    """The live path runs substitute_platform first -> no double warning."""
    log = SyncLog()
    warn_unresolved_platform_vars(
        "x {{platform.hacs.absent}} y", {}, "ctx/AGENTS.md", log,
        report_missing=False,
    )
    assert not log.warnings


def test_apply_helper_resolves_and_never_reports_configured_key_as_missing():
    log = SyncLog()
    out = _apply_platform_context_substitution(
        "repo: {{platform.hacs.integration_repo_url}}",
        {"platform.hacs.integration_repo_url": _HACS_OVERRIDES["integration_repo_url"]},
        "ctx/AGENTS.md",
        log,
    )
    assert out == f"repo: {_HACS_OVERRIDES['integration_repo_url']}"
    assert not _PLATFORM_RE.search(out)
    assert not log.warnings


# ---------------------------------------------------------------------------
# AC 1 + AC 3 — end-to-end context render of an embedded platform rule.
# ---------------------------------------------------------------------------


def _load_hacs_config_and_providers():
    """Real repo config with platforms:[hacs] and the embedding `default` preset.

    The repo self-hosts with ``rules-preset: lazy`` (the HACS rule is a lazy
    skill there); a consumer project embedding the rule into AGENTS.md uses the
    default preset, which is exactly the #834 scenario.
    """
    config = load_config(_REPO_ROOT / ".meta-config" / "project.yaml")
    config["platforms"] = ["hacs"]
    config["rules-preset"] = "default"
    provider_config = load_providers_config(_REPO_ROOT)
    variables, _ = build_variables(config, _REPO_ROOT)
    return config, variables, provider_config


@pytest.mark.parametrize("provider", ["Opencode", "Gemini"])
def test_generated_context_file_has_no_raw_platform_placeholders(tmp_path, provider):
    project_root = tmp_path
    _write_platform_override(project_root)

    config, variables, provider_config = _load_hacs_config_and_providers()

    log = SyncLog()
    platform_vars = load_platform_config(_REPO_ROOT, project_root, ["hacs"], log)
    assert platform_vars["platform.hacs.integration_repo_url"]  # config sane

    sync_context_for_provider(
        _REPO_ROOT, project_root, config, variables, log,
        dry_run=False, provider=provider, provider_config=provider_config,
        platform_vars=platform_vars,
    )

    context_file = provider_config[provider]["context_file"]
    text = (project_root / context_file).read_text(encoding="utf-8")

    # AC 3: zero raw placeholders.
    remaining = _PLATFORM_RE.findall(text)
    assert remaining == [], f"raw platform placeholders in {context_file}: {remaining}"

    # AC 1: the configured value actually landed in the embedded rule.
    assert _HACS_OVERRIDES["integration_repo_url"] in text
    assert _HACS_OVERRIDES["dev_instance_url"] in text

    # And no false "configured but not applied" diagnosis was emitted.
    assert not any("substitution not applied" in w for w in log.warnings), log.warnings
