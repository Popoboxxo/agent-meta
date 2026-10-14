"""IC-18 no. 9 (Task 1.17, AC-50): commands with ``requires_roles`` only for active roles.

A command source may declare ``requires_roles: [<role>...]`` in its frontmatter.
It is generated only when ``ActiveSet.all_active(requires_roles)``; a previously
generated command whose role became inactive is removed as a managed file. The
key is a generator directive and never reaches the rendered command (default
render byte-identical). Command bodies may use ``{{#if ROLE_*_ACTIVE}}``.
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest
import yaml

from scripts.lib.active_set import compute_active_set
from scripts.lib.commands import command_required_roles, sync_commands_for_provider
from scripts.lib.consistency.commands import check_command_frontmatter
from scripts.lib.log import SyncLog
from scripts.lib.providers import load_providers_config
from tests.active_set_render import REPO_ROOT, default_config, fixture_config, sync_config

_COMMANDS = REPO_ROOT / "commands" / "1-generic"
# Dispatch commands and the role they delegate to (data lives in the frontmatter).
_EXPECTED = {
    "analyze-logs": ["log-analyzer"],
    "doc-now": ["documenter"],
    "feedback": ["feedback"],
    "report-bug": ["feedback"],
    "upgrade-meta": ["agent-meta-manager"],
}


def _commands_dir(project: Path) -> Path:
    return project / ".claude" / "commands"


@pytest.mark.parametrize("stem,roles", sorted(_EXPECTED.items()))
def test_dispatch_commands_declare_their_role(stem, roles):
    assert command_required_roles((_COMMANDS / f"{stem}.md").read_text(encoding="utf-8")) == roles


@pytest.fixture(scope="module")
def p10(tmp_path_factory):
    return sync_config(tmp_path_factory.mktemp("cmd") / "p10", fixture_config("p10"))


def test_p10_skips_commands_with_inactive_role(p10):
    generated = {p.stem for p in _commands_dir(p10).glob("*.md")}
    # p10 has documenter but none of feedback / log-analyzer / agent-meta-manager.
    assert "doc-now" in generated
    for stem in ("analyze-logs", "feedback", "report-bug", "upgrade-meta"):
        assert stem not in generated, stem


def test_rendered_commands_carry_no_requires_roles(p10):
    for path in _commands_dir(p10).glob("*.md"):
        assert "requires_roles" not in path.read_text(encoding="utf-8"), path.name


def test_p10_add_provider_names_no_inactive_meta_feedback(p10):
    text = (_commands_dir(p10) / "add-provider.md").read_text(encoding="utf-8")
    assert "meta-feedback" not in text
    assert "{{" not in text


def _sync_commands(project: Path, config: dict) -> SyncLog:
    log = SyncLog()
    active = compute_active_set(config, REPO_ROOT, project, warn_sink=[])
    sync_commands_for_provider(
        REPO_ROOT, project, config, log, False, "Claude",
        provider_config=load_providers_config(REPO_ROOT, config),
        variables={}, active_set=active)
    return log


def test_previously_generated_command_is_removed_when_role_turns_inactive(tmp_path):
    full = default_config()
    _sync_commands(tmp_path, full)
    assert (_commands_dir(tmp_path) / "report-bug.md").is_file()
    narrowed = dict(full, roles=["orchestrator", "developer", "documenter", "git"])
    _sync_commands(tmp_path, narrowed)
    assert not (_commands_dir(tmp_path) / "report-bug.md").exists()
    assert (_commands_dir(tmp_path) / "doc-now.md").is_file()
    index = (_commands_dir(tmp_path) / ".agent-meta-managed").read_text(encoding="utf-8")
    assert "report-bug.md" not in index


def test_default_keeps_every_command(tmp_path):
    project = sync_config(tmp_path / "default", default_config())
    generated = {p.stem for p in _commands_dir(project).glob("*.md")}
    assert set(_EXPECTED) <= generated
    text = (_commands_dir(project) / "doc-now.md").read_text(encoding="utf-8")
    source = (_COMMANDS / "doc-now.md").read_text(encoding="utf-8")
    assert text == re.sub(r"^requires_roles:.*\n", "", source, flags=re.M)


def _findings(tmp_path: Path, frontmatter: str):
    path = tmp_path / "commands" / "1-generic" / "x.md"
    path.parent.mkdir(parents=True)
    content = "---\n" + frontmatter + "---\n\nBody $ARGUMENTS\n"
    path.write_text(content, encoding="utf-8")
    return check_command_frontmatter(path, content, REPO_ROOT)


_BASE_FM = 'description: X\nallowed-tools: ["Agent"]\nargument-hint: "[x]"\n'


def test_consistency_accepts_valid_requires_roles(tmp_path):
    findings = _findings(tmp_path, _BASE_FM + "requires_roles: [documenter]\n")
    assert [f.check for f in findings if "requires" in f.check] == []


def test_consistency_flags_unknown_or_malformed_requires_roles(tmp_path):
    unknown = _findings(tmp_path / "a", _BASE_FM + "requires_roles: [no-such-role]\n")
    assert [f.check for f in unknown] == ["commands.requires-roles-invalid"]
    malformed = _findings(tmp_path / "b", _BASE_FM + "requires_roles: documenter\n")
    assert [f.check for f in malformed] == ["commands.requires-roles-invalid"]


def test_requires_roles_data_matches_role_defaults():
    roles = set(yaml.safe_load((REPO_ROOT / "config" / "role-defaults.yaml").read_text(
        encoding="utf-8"))["roles"])
    for path in sorted(_COMMANDS.glob("*.md")):
        assert set(command_required_roles(path.read_text(encoding="utf-8"))) <= roles, path.name
