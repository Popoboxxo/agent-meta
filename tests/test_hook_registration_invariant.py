"""Regression tests for issue #808 — generated Claude hooks must not be
silently-dead code.

Invariants under test:

1. Every hook that is meant to run by default (``enabled_by_default: true``,
   not overridden) is registered in the provider's registration artifact and
   its deployed file exists.
2. Every opt-in hook has a working registration path: enabling it via
   ``project.yaml`` registers it.
3. Helper scripts (no ``# hook:`` header) and non-runtime ``Manual`` hooks are
   never registered as standalone hooks.
4. Protocol-scoped scripts (``# hook_protocol:``) are only deployed to
   providers speaking that protocol — e.g. ``antigravity-json-adapter.sh`` is
   not generated for Claude.
5. Every hook script (source and generated) is valid shell (``bash -n``).

Run: python -m pytest tests/test_hook_registration_invariant.py -v
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.hooks import (  # noqa: E402
    NON_RUNTIME_HOOK_EVENTS,
    collect_hook_sources,
    parse_hook_metadata,
    parse_hook_settings_command,
    sync_hooks,
)
from lib.log import SyncLog  # noqa: E402
from lib.providers import load_providers_config  # noqa: E402

_BASH = shutil.which("bash") or "bash"
_CLAUDE_HOOKS_DIR = ".claude/hooks"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("win32", "linux", "darwin"), reason="requires bash"
)


def _sync(project_root: Path, provider: str = "Claude", hooks_cfg: dict | None = None) -> SyncLog:
    log = SyncLog()
    config = {"platforms": [], "hooks": hooks_cfg or {}}
    provider_config = load_providers_config(_REPO_ROOT)
    sync_hooks(
        _REPO_ROOT, project_root, config, log,
        dry_run=False, provider=provider, provider_config=provider_config,
    )
    return log


def _registered_stems(settings_path: Path) -> set[str]:
    """Stems of hooks registered in a Claude settings.json artifact."""
    data = json.loads(settings_path.read_text(encoding="utf-8"))
    stems: set[str] = set()
    for entries in data.get("hooks", {}).values():
        for entry in entries:
            for handler in entry.get("hooks", []):
                filename = parse_hook_settings_command(
                    str(handler.get("command", "")), _CLAUDE_HOOKS_DIR
                )
                if filename:
                    stems.add(Path(filename).stem)
    return stems


def _default_enabled_hooks(provider: str = "Claude") -> set[str]:
    """Source hooks that sync_hooks() is expected to register by default."""
    expected: set[str] = set()
    for source_path, output_name in collect_hook_sources(_REPO_ROOT, []):
        meta = parse_hook_metadata(source_path.read_text(encoding="utf-8"))
        if not meta.get("hook"):
            continue  # helper
        if meta.get("provider") and meta["provider"] != provider:
            continue
        if meta.get("event") in NON_RUNTIME_HOOK_EVENTS:
            continue
        if meta.get("enabled_by_default", "false").lower() == "true":
            expected.add(Path(output_name).stem)
    return expected


def test_default_enabled_hooks_are_registered(tmp_path):
    """Generated-hook invariant: default-enabled hooks ⊆ registered hooks."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    _sync(project_root)

    expected = _default_enabled_hooks()
    assert expected, "sanity: agent-meta must ship at least one default-enabled hook"

    registered = _registered_stems(project_root / ".claude" / "settings.json")
    missing = expected - registered
    assert not missing, f"default-enabled hooks are not registered: {sorted(missing)}"
    for stem in expected:
        assert (project_root / _CLAUDE_HOOKS_DIR / f"{stem}.sh").is_file(), (
            f"registered default-enabled hook '{stem}' has no deployed file"
        )


def test_opt_in_hook_has_a_registration_path(tmp_path):
    """A genuinely opt-in hook is not dead code: enabling it registers it."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    _sync(project_root, hooks_cfg={"lifecycle-check": {"enabled": True}})

    registered = _registered_stems(project_root / ".claude" / "settings.json")
    assert "lifecycle-check" in registered
    settings = json.loads(
        (project_root / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    assert "PostToolUse" in settings["hooks"]


def test_helpers_are_never_registered(tmp_path):
    """Scripts without a `# hook:` header are helpers, not standalone hooks."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    _sync(project_root)

    registered = _registered_stems(project_root / ".claude" / "settings.json")
    for helper in ("orchestrator-guard-impl", "repo-containment-impl", "antigravity-json-adapter"):
        assert helper not in registered, f"helper '{helper}' was registered as a hook"


def test_protocol_scoped_adapter_only_deployed_for_its_protocol(tmp_path):
    """antigravity-json-adapter.sh is not dead code in a Claude project: it is
    simply not generated there (issue #808)."""
    claude_project = tmp_path / "claude"
    claude_project.mkdir()
    _sync(claude_project, provider="Claude")
    assert not (claude_project / _CLAUDE_HOOKS_DIR / "antigravity-json-adapter.sh").exists()

    gemini_project = tmp_path / "gemini"
    gemini_project.mkdir()
    _sync(gemini_project, provider="Gemini")
    assert (gemini_project / ".agents" / "hooks" / "antigravity-json-adapter.sh").exists()


def test_manual_hook_is_never_registered_even_when_enabled(tmp_path):
    """`event: Manual` is not a native runtime event — enabling it must not
    write a 'Manual' bucket into settings.json."""
    project_root = tmp_path / "project"
    project_root.mkdir()

    _sync(project_root, hooks_cfg={"pre-release-check": {"enabled": True}})

    settings = json.loads(
        (project_root / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    hooks = settings.get("hooks", {})
    assert "Manual" not in hooks
    assert "pre-release-check" not in json.dumps(hooks)
    # The dispatcher script is still deployed for the release agent to invoke.
    assert (project_root / _CLAUDE_HOOKS_DIR / "pre-release-check.sh").is_file()


def test_all_hook_scripts_are_valid_shell(tmp_path):
    """Source and generated hook scripts must all pass `bash -n`."""
    source_scripts = sorted((_REPO_ROOT / "hooks").rglob("*.sh"))
    assert source_scripts, "sanity: no hook sources found"

    project_root = tmp_path / "project"
    project_root.mkdir()
    _sync(project_root)
    generated_scripts = sorted((project_root / _CLAUDE_HOOKS_DIR).rglob("*.sh"))
    assert generated_scripts, "sanity: no generated hook scripts found"

    for script in source_scripts + generated_scripts:
        result = subprocess.run(
            [_BASH, "-n", str(script)], capture_output=True, text=True
        )
        assert result.returncode == 0, f"{script}: {result.stderr}"


# --- issue #851: cwd-independent hook command anchoring -----------------------


def _commands(settings: dict) -> list[str]:
    return [
        h["command"]
        for entries in settings.get("hooks", {}).values()
        for entry in entries
        for h in entry.get("hooks", [])
    ]


def test_generated_claude_commands_are_anchored(tmp_path):
    """Registered Claude hook commands are anchored to ${CLAUDE_PROJECT_DIR}
    so they resolve regardless of the session cwd (issue #851)."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _sync(project_root)

    settings = json.loads(
        (project_root / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    commands = _commands(settings)
    assert commands, "sanity: at least one hook must be registered"
    assert all(c.startswith("bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/") for c in commands), commands


def test_parser_recognises_anchored_and_legacy_forms():
    """Inverse parser accepts both the anchored and the legacy relative form,
    and still rejects unrelated commands."""
    assert parse_hook_settings_command(
        "bash ${CLAUDE_PROJECT_DIR}/.claude/hooks/x.sh", _CLAUDE_HOOKS_DIR
    ) == "x.sh"
    assert parse_hook_settings_command(
        "bash .claude/hooks/x.sh", _CLAUDE_HOOKS_DIR
    ) == "x.sh"
    assert parse_hook_settings_command("bash /tmp/x.sh", _CLAUDE_HOOKS_DIR) is None


def test_legacy_relative_entry_is_clean_replaced_not_duplicated(tmp_path):
    """Migration regression (issue #851): a settings.json carrying the legacy
    relative command for a managed hook is recognised as managed and clean-
    replaced by the anchored form — no duplicate entry."""
    project_root = tmp_path / "project"
    project_root.mkdir()
    _sync(project_root)

    settings_path = project_root / ".claude" / "settings.json"
    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    # Simulate a project deployed before the anchor existed.
    for entries in settings["hooks"].values():
        for entry in entries:
            for h in entry["hooks"]:
                h["command"] = h["command"].replace(
                    "bash ${CLAUDE_PROJECT_DIR}/", "bash "
                )
    settings_path.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
    legacy_commands = _commands(settings)
    assert all(c.startswith("bash .claude/hooks/") for c in legacy_commands)

    _sync(project_root)

    settings = json.loads(settings_path.read_text(encoding="utf-8"))
    commands = _commands(settings)
    assert all(c.startswith("bash ${CLAUDE_PROJECT_DIR}/") for c in commands), commands
    assert len(commands) == len(set(commands)), f"duplicate entries: {commands}"
    assert len(commands) == len(legacy_commands)


def test_provider_without_anchor_key_stays_relative(tmp_path):
    """Provider-agnostic (issue #851): a provider config without the anchor key
    keeps the legacy relative command form — no hidden Claude branch."""
    agent_meta_root = tmp_path / "agent-meta"
    generic = agent_meta_root / "hooks" / "1-generic"
    generic.mkdir(parents=True)
    (generic / "anchor-probe.sh").write_text(
        "#!/bin/bash\n# hook: anchor-probe\n# version: 1.0.0\n"
        "# event: PreToolUse\n# enabled_by_default: true\nexit 0\n",
        encoding="utf-8",
    )
    project_root = tmp_path / "project"
    project_root.mkdir()

    log = SyncLog()
    config = {"platforms": [], "hooks": {}}
    provider_config = {
        "TestProv": {
            "hooks_dir": ".testprov/hooks",
            "settings_file": ".testprov/settings.json",
            "hook_protocol": "claude-code-json",
            "has_hooks": True,
        }
    }
    sync_hooks(
        agent_meta_root, project_root, config, log,
        dry_run=False, provider="TestProv", provider_config=provider_config,
    )

    settings = json.loads(
        (project_root / ".testprov" / "settings.json").read_text(encoding="utf-8")
    )
    commands = _commands(settings)
    assert commands == ["bash .testprov/hooks/anchor-probe.sh"], commands
