"""Hard sync-validator ``config._validate_subagent_permissions`` (Feature A).

Covers AC-A6/A7/A9: enum/provider hard-fails, the strict role obligation over
the REAL override chain (B2) and the safe no-op for ``warn``/``off``/null.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib import config as config_mod  # noqa: E402
from lib.config import load_config  # noqa: E402


def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content), encoding="utf-8")


def _make_fixture(root: Path, *, developer_tools: bool = True,
                  claude_expert_tools: bool = True,
                  claude_expert_extends: bool = False) -> None:
    """Minimal framework fixture: 1-generic base + 2-platform-only override."""
    dev_tools = "tools: [Read, Write]" if developer_tools else "tools: []"
    expert_tools = "tools: [Read]" if claude_expert_tools else "tools: []"

    _write(root / "agents/1-generic/developer.md", f"""\
        ---
        name: developer
        {dev_tools}
        ---
        # developer
        """)
    _write(root / "agents/1-generic/orchestrator.md", """\
        ---
        name: orchestrator
        tools: [Read, Task]
        ---
        # orchestrator
        """)

    # The 2-platform file is built line-by-line: an extends-override does NOT
    # redeclare tools (it inherits them), a plain override declares its own.
    expert_lines = ["---", "name: claude-expert"]
    if claude_expert_extends:
        expert_lines.append("extends: agents/1-generic/provider-expert-base.md")
    else:
        expert_lines.append(expert_tools)
    expert_lines += ["---", "# claude-expert", ""]
    path = root / "agents/2-platform/agent-meta-claude-expert.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(expert_lines), encoding="utf-8")

    if claude_expert_extends:
        _write(root / "agents/1-generic/provider-expert-base.md", """\
            ---
            name: provider-expert
            tools: [Read, WebFetch]
            ---
            # base
            """)

    _write(root / "config/role-defaults.yaml", """\
        roles:
          developer: {}
          claude-expert: {}
          orchestrator: {}
        """)


def _strict_config(**overrides) -> dict:
    cfg = {
        "platforms": ["agent-meta"],
        "ai-providers": ["Claude"],
        "roles": ["developer", "claude-expert", "orchestrator"],
        "subagent_permissions": {"mode": "strict"},
    }
    cfg.update(overrides)
    return cfg


def _validate(cfg: dict, tmp_path: Path) -> None:
    config_mod._validate_subagent_permissions(cfg, tmp_path / "project.yaml")


def test_unknown_provider_key_exits(tmp_path):
    cfg = _strict_config(subagent_permissions={
        "mode": "off",
        "provider-overrides": {"Claud": {"mode": "warn"}},
    })
    with pytest.raises(SystemExit) as exc:
        _validate(cfg, tmp_path)
    assert exc.value.code == 1


def test_invalid_global_enum_exits(tmp_path):
    with pytest.raises(SystemExit):
        _validate({"subagent_permissions": {"mode": "sometimes"}}, tmp_path)


def test_invalid_provider_override_enum_exits(tmp_path):
    with pytest.raises(SystemExit):
        _validate(
            {"subagent_permissions": {"provider-overrides": {"Claude": {"mode": "sometimes"}}}},
            tmp_path,
        )


def test_warn_mode_does_not_exit(tmp_path, monkeypatch):
    monkeypatch.setattr(config_mod, "_framework_root", lambda: tmp_path)
    _validate({"subagent_permissions": {"mode": "warn"}}, tmp_path)


def test_strict_missing_tools_exits_with_role_and_source(tmp_path, monkeypatch, capsys):
    _make_fixture(tmp_path, claude_expert_tools=False)
    monkeypatch.setattr(config_mod, "_framework_root", lambda: tmp_path)
    with pytest.raises(SystemExit) as exc:
        _validate(_strict_config(), tmp_path)
    assert exc.value.code == 1
    err = capsys.readouterr().err
    assert "claude-expert" in err
    assert "agents/2-platform/agent-meta-claude-expert.md" in err


def test_strict_all_roles_declare_tools_does_not_exit(tmp_path, monkeypatch):
    _make_fixture(tmp_path, claude_expert_tools=True)
    monkeypatch.setattr(config_mod, "_framework_root", lambda: tmp_path)
    _validate(_strict_config(), tmp_path)


def test_strict_2platform_override_inherits_tools_via_extends(tmp_path, monkeypatch):
    # B2: 2-platform override without its own tools: composes the base list.
    _make_fixture(tmp_path, claude_expert_tools=False, claude_expert_extends=True)
    monkeypatch.setattr(config_mod, "_framework_root", lambda: tmp_path)
    _validate(_strict_config(), tmp_path)


def test_strict_2platform_override_without_extends_or_tools_exits(tmp_path, monkeypatch):
    _make_fixture(tmp_path, claude_expert_tools=False, claude_expert_extends=False)
    monkeypatch.setattr(config_mod, "_framework_root", lambda: tmp_path)
    with pytest.raises(SystemExit):
        _validate(_strict_config(), tmp_path)


def test_strict_orchestrator_main_chat_is_out_of_scope(tmp_path, monkeypatch):
    # E13: orchestrator is skipped when the global orchestrator mode is main-chat.
    _make_fixture(tmp_path)
    # Drop the orchestrator tools declaration to prove the skip, not the tools.
    _write(tmp_path / "agents/1-generic/orchestrator.md", """\
        ---
        name: orchestrator
        tools: []
        ---
        # orchestrator
        """)
    monkeypatch.setattr(config_mod, "_framework_root", lambda: tmp_path)
    cfg = _strict_config(orchestrator={"mode": "main-chat"})
    _validate(cfg, tmp_path)


def test_null_block_load_config_no_exit(tmp_path):
    path = tmp_path / "project.yaml"
    path.write_text(
        "project:\n  name: t\n  prefix: t\n  short: t\n"
        "ai-providers: [Claude]\n"
        "subagent_permissions:\n",
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg["subagent_permissions"] == {}


def test_load_config_normalizes_bool_modes(tmp_path):
    path = tmp_path / "project.yaml"
    path.write_text(
        "project:\n  name: t\n  prefix: t\n  short: t\n"
        "ai-providers: [Claude]\n"
        "subagent_permissions:\n"
        "  mode: off\n"
        "  provider-overrides:\n"
        "    Claude:\n"
        "      mode: on\n",
        encoding="utf-8",
    )
    cfg = load_config(path)
    assert cfg["subagent_permissions"]["mode"] == "off"
    assert cfg["subagent_permissions"]["provider-overrides"]["Claude"]["mode"] == "off"
