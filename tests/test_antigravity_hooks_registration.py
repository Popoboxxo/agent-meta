"""Tests for the Antigravity (Gemini) hook registration path — issue #674 Phase 3.1.

Covers two layers:

1. scripts/lib/hooks.py::sync_hooks() with hook_protocol antigravity-hooks-json:
   the registration artifact .agents/hooks.json is written in the VERIFIED
   Antigravity schema (hook-name keys, matcher+nested-hooks shape for
   PreToolUse/PostToolUse, flat shape for Stop/PreInvocation/PostInvocation),
   every hook routed through the translating adapter, stale cleanup and
   foreign-entry preservation behave like the Claude settings.json writer,
   and Gemini CLI's .gemini/settings.json is NOT touched.

2. hooks/1-generic/antigravity-json-adapter.sh: translates the verified AGY
   payload (hookEventName/toolCall.{name,args}, camelCase) to the Claude
   contract the generic hook scripts parse, and maps exit 2 + stderr to the
   verified {"decision": "deny", "reason"} AGY output.

Run: python -m pytest tests/test_antigravity_hooks_registration.py -v
"""

import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.hook_plugins import sync_hook_lib  # noqa: E402
from lib.hooks import sync_hooks  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.providers import load_providers_config  # noqa: E402

_ADAPTER_SOURCE = _REPO_ROOT / "hooks" / "1-generic" / "antigravity-json-adapter.sh"

_HOOK_SOURCE = """\
#!/bin/bash
# hook: test-guard
# version: 1.0.0
# event: {event}
# matcher: ""
# description: test guard
# enabled_by_default: true

exit 0
"""


def _gemini_pc() -> dict:
    return load_providers_config(_REPO_ROOT)["Gemini"]


@pytest.fixture
def agent_meta_root(tmp_path):
    root = tmp_path / "agent-meta"
    generic = root / "hooks" / "1-generic"
    generic.mkdir(parents=True)
    (generic / "test-guard.sh").write_text(
        _HOOK_SOURCE.format(event="PreToolUse"), encoding="utf-8"
    )
    shutil.copy(_ADAPTER_SOURCE, generic / _ADAPTER_SOURCE.name)
    lib_dir = generic / "lib"
    lib_dir.mkdir()
    (lib_dir / "hook_common.sh").write_text(
        "#!/bin/bash\n# lib: hook_common\nfoo() { :; }\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def project_root(tmp_path):
    p = tmp_path / "project"
    p.mkdir()
    return p


def _sync(agent_meta_root, project_root, provider="Gemini", log=None):
    log = log or SyncLog()
    config = {"platforms": [], "hooks": {}}
    provider_config = load_providers_config(_REPO_ROOT)
    sync_hooks(agent_meta_root, project_root, config, log, dry_run=False,
               provider=provider, provider_config=provider_config)
    sync_hook_lib(agent_meta_root, project_root, config, log, dry_run=False,
                  provider=provider, provider_config=provider_config)
    return log


def _load_hooks_json(project_root: Path) -> dict:
    return json.loads((project_root / ".agents" / "hooks.json").read_text(encoding="utf-8"))


# ---------------------------------------------------------------------------
# sync_hooks + hooks.json registration writer
# ---------------------------------------------------------------------------

def test_hooks_json_written_in_antigravity_schema(agent_meta_root, project_root):
    _sync(agent_meta_root, project_root)

    hooks_json = _load_hooks_json(project_root)
    entry = hooks_json["test-guard"]["PreToolUse"][0]
    # Matcher is ALWAYS "*": Claude-contract matcher names would never match
    # AGY's native tool names; the scripts gate on the (translated) tool name
    # themselves.
    assert entry["matcher"] == "*"
    handler = entry["hooks"][0]
    assert handler["type"] == "command"
    # Every hook is routed through the translating adapter, path relative to
    # the hooks.json directory.
    assert handler["command"] == "bash ./hooks/antigravity-json-adapter.sh test-guard.sh"


def test_hook_scripts_and_adapter_are_mirrored(agent_meta_root, project_root):
    _sync(agent_meta_root, project_root)
    hooks_dir = project_root / ".agents" / "hooks"
    assert (hooks_dir / "test-guard.sh").exists()
    assert (hooks_dir / _ADAPTER_SOURCE.name).exists()
    assert (hooks_dir / ".agent-meta-managed").exists()
    assert "test-guard.sh" in (hooks_dir / ".agent-meta-managed").read_text(encoding="utf-8")
    # Shared lib deployed next to the hooks (orchestrator-guard sources it
    # fail-closed, issue #595).
    assert (hooks_dir / "lib" / "hook_common.sh").exists()


def test_gemini_cli_settings_file_is_not_touched(agent_meta_root, project_root):
    """The Antigravity registration artifact is .agents/hooks.json — Gemini
    CLI's .gemini/settings.json must stay out of the hook-sync path."""
    _sync(agent_meta_root, project_root)
    assert not (project_root / ".gemini" / "settings.json").exists()


def test_foreign_hook_entries_are_preserved(agent_meta_root, project_root):
    hooks_json_path = project_root / ".agents" / "hooks.json"
    hooks_json_path.parent.mkdir(parents=True)
    hooks_json_path.write_text(json.dumps({
        "user-own-hook": {
            "PreToolUse": [{"matcher": "run_command", "hooks": [
                {"type": "command", "command": "./scripts/mine.sh"}]}],
        },
    }), encoding="utf-8")

    _sync(agent_meta_root, project_root)

    hooks_json = _load_hooks_json(project_root)
    assert "user-own-hook" in hooks_json
    assert "test-guard" in hooks_json


def test_stale_hook_is_removed_from_hooks_json(agent_meta_root, project_root):
    _sync(agent_meta_root, project_root)
    assert "test-guard" in _load_hooks_json(project_root)

    (agent_meta_root / "hooks" / "1-generic" / "test-guard.sh").unlink()
    _sync(agent_meta_root, project_root)

    hooks_json = _load_hooks_json(project_root)
    assert "test-guard" not in hooks_json


def test_sync_is_idempotent(agent_meta_root, project_root):
    first = _sync(agent_meta_root, project_root)
    assert any("registered hooks" in a for a in first.actions)

    second = _sync(agent_meta_root, project_root)
    assert any("hooks registration unchanged" in s for s in second.skipped)


def test_stop_event_uses_flat_handler_shape(agent_meta_root, project_root):
    """Stop/PreInvocation/PostInvocation take a FLAT command list (verified
    schema) — no matcher, no nested hooks array."""
    (agent_meta_root / "hooks" / "1-generic" / "stop-hook.sh").write_text(
        _HOOK_SOURCE.format(event="Stop"), encoding="utf-8"
    )
    _sync(agent_meta_root, project_root)

    hooks_json = _load_hooks_json(project_root)
    stop_handlers = hooks_json["stop-hook"]["Stop"]
    assert stop_handlers == [{
        "type": "command",
        "command": "bash ./hooks/antigravity-json-adapter.sh stop-hook.sh",
    }]


def test_claude_registration_path_unchanged(agent_meta_root, project_root):
    """Dispatch regression guard: the legacy claude-code-json writer still
    registers in .claude/settings.json (settings.json {hooks: ...} shape)."""
    _sync(agent_meta_root, project_root, provider="Claude")

    settings = json.loads(
        (project_root / ".claude" / "settings.json").read_text(encoding="utf-8")
    )
    entry = settings["hooks"]["PreToolUse"][0]
    assert entry["hooks"][0]["command"] == "bash .claude/hooks/test-guard.sh"
    assert not (project_root / ".agents" / "hooks.json").exists()


def test_antigravity_protocol_without_hooks_config_file_warns(tmp_path, project_root):
    """A provider_config with the Antigravity protocol but no hooks_config_file
    must warn + skip registration (config error), not crash or fall back to a
    wrong file."""
    agent_meta_root = tmp_path / "agent-meta"
    generic = agent_meta_root / "hooks" / "1-generic"
    generic.mkdir(parents=True)
    (generic / "test-guard.sh").write_text(
        _HOOK_SOURCE.format(event="PreToolUse"), encoding="utf-8"
    )
    shutil.copy(_ADAPTER_SOURCE, generic / _ADAPTER_SOURCE.name)

    log = SyncLog()
    config = {"platforms": [], "hooks": {}}
    pc = dict(_gemini_pc())
    pc.pop("hooks_config_file")
    sync_hooks(agent_meta_root, project_root, config, log, dry_run=False,
               provider="Gemini", provider_config={"Gemini": pc})

    assert any("hooks_config_file" in w for w in log.warnings)
    assert not (project_root / ".agents" / "hooks.json").exists()


def test_non_object_hooks_json_warns_and_is_left_unchanged(agent_meta_root, project_root):
    """Valid-but-non-object JSON in .agents/hooks.json (e.g. `[]`) must not
    crash the sync or be overwritten — warn + skip, file stays untouched
    (mirrors the _read_existing_json_dict guard in mcp_provider_config.py)."""
    hooks_json_path = project_root / ".agents" / "hooks.json"
    hooks_json_path.parent.mkdir(parents=True)
    hooks_json_path.write_text("[]\n", encoding="utf-8")

    log = _sync(agent_meta_root, project_root)

    assert any("not a JSON object" in w for w in log.warnings)
    assert json.loads(hooks_json_path.read_text(encoding="utf-8")) == []


# ---------------------------------------------------------------------------
# antigravity-json-adapter.sh runtime behavior
# ---------------------------------------------------------------------------

def _adapter_fixture(tmp_path: Path, target_body: str) -> Path:
    """tmp dir with the real adapter + a fake target hook script."""
    d = tmp_path / "agy"
    d.mkdir()
    shutil.copy(_ADAPTER_SOURCE, d / "antigravity-json-adapter.sh")
    (d / "target.sh").write_text(target_body, encoding="utf-8")
    return d


def _run_adapter(fixture_dir: Path, payload: str, target: str = "target.sh",
                 env_out: Path | None = None) -> subprocess.CompletedProcess:
    env = dict(os.environ)
    if env_out is not None:
        env["ADAPTER_TEST_OUT"] = str(env_out)
    return subprocess.run(  # noqa: S603
        ["bash", "antigravity-json-adapter.sh", target],
        input=payload, capture_output=True, text=True, cwd=fixture_dir, env=env,
        timeout=60,
    )


def test_adapter_maps_agy_deny_to_decision_json(tmp_path):
    fixture = _adapter_fixture(tmp_path, '#!/bin/bash\necho "blocked: strict mode" >&2\nexit 2\n')
    payload = json.dumps({
        "hookEventName": "PreToolUse",
        "toolCall": {"name": "run_command", "args": {"CommandLine": "git push"}},
        "stepIdx": 1,
        "workspacePaths": ["/ws"],
    })
    result = _run_adapter(fixture, payload)

    assert result.returncode == 0
    decision = json.loads(result.stdout)
    assert decision["decision"] == "deny"
    assert "blocked: strict mode" in decision["reason"]


def test_adapter_passes_allowed_calls_without_output(tmp_path):
    fixture = _adapter_fixture(tmp_path, '#!/bin/bash\nexit 0\n')
    payload = json.dumps({
        "hookEventName": "PreToolUse",
        "toolCall": {"name": "run_command", "args": {"CommandLine": "ls"}},
        "workspacePaths": ["/ws"],
    })
    result = _run_adapter(fixture, payload)

    assert result.returncode == 0
    # No {"decision": "allow"} — that would auto-allow and bypass AGY's own
    # permission prompts; empty stdout = no hook opinion.
    assert result.stdout == ""


def test_adapter_translates_agy_payload_to_claude_shape(tmp_path):
    out_file = tmp_path / "received.json"
    fixture = _adapter_fixture(
        tmp_path, '#!/bin/bash\ncat > "$ADAPTER_TEST_OUT"\nexit 0\n'
    )
    payload = json.dumps({
        "hookEventName": "PreToolUse",
        "toolCall": {
            "name": "run_command",
            "args": {"CommandLine": "git status", "Cwd": "/ws/sub"},
        },
        "stepIdx": 2,
        "workspacePaths": ["/ws"],
    })
    result = _run_adapter(fixture, payload, env_out=out_file)

    assert result.returncode == 0
    received = json.loads(out_file.read_text(encoding="utf-8"))
    # Claude-contract keys the generic hook scripts parse:
    assert received["hook_event_name"] == "PreToolUse"
    assert received["tool_name"] == "Bash"           # run_command -> Bash
    assert received["tool_input"]["command"] == "git status"  # CommandLine -> command
    assert received["cwd"] == "/ws"                  # workspacePaths[0] -> cwd
    # Original AGY fields kept for forward compatibility:
    assert received["toolCall"]["name"] == "run_command"
    assert received["hookEventName"] == "PreToolUse"


def test_adapter_normalizes_edit_tool_names(tmp_path):
    out_file = tmp_path / "received.json"
    fixture = _adapter_fixture(tmp_path, '#!/bin/bash\ncat > "$ADAPTER_TEST_OUT"\nexit 0\n')
    payload = json.dumps({
        "hookEventName": "PreToolUse",
        "toolCall": {"name": "write_to_file", "args": {"FilePath": "/ws/a.md"}},
        "workspacePaths": ["/ws"],
    })
    _run_adapter(fixture, payload, env_out=out_file)

    received = json.loads(out_file.read_text(encoding="utf-8"))
    assert received["tool_name"] == "Write"


def test_adapter_posttooluse_exit2_emits_no_decision(tmp_path):
    """PostToolUse cannot block — an exit 2 must not emit a deny decision."""
    fixture = _adapter_fixture(tmp_path, '#!/bin/bash\necho "boom" >&2\nexit 2\n')
    payload = json.dumps({
        "hookEventName": "PostToolUse",
        "toolCall": {"name": "run_command", "args": {}},
        "workspacePaths": ["/ws"],
    })
    result = _run_adapter(fixture, payload)

    assert result.returncode == 0
    assert result.stdout == ""


def test_adapter_unparseable_payload_fails_closed_on_pretooluse(tmp_path):
    fixture = _adapter_fixture(tmp_path, '#!/bin/bash\nexit 0\n')
    result = _run_adapter(fixture, "this is not json")

    assert result.returncode == 0
    decision = json.loads(result.stdout)
    assert decision["decision"] == "deny"


def test_adapter_missing_target_fails_open_with_warning(tmp_path):
    fixture = _adapter_fixture(tmp_path, "# unused\n")
    payload = json.dumps({
        "hookEventName": "PreToolUse",
        "toolCall": {"name": "run_command", "args": {}},
        "workspacePaths": ["/ws"],
    })
    result = _run_adapter(fixture, payload, target="does-not-exist.sh")

    assert result.returncode == 0
    assert result.stdout == ""
    assert "not found" in result.stderr


def test_adapter_missing_argument_fails_open_with_warning(tmp_path):
    fixture = _adapter_fixture(tmp_path, "# unused\n")
    payload = json.dumps({
        "hookEventName": "PreToolUse",
        "toolCall": {"name": "run_command", "args": {}},
        "workspacePaths": ["/ws"],
    })
    env = dict(os.environ)
    result = subprocess.run(  # noqa: S603
        ["bash", "antigravity-json-adapter.sh"],
        input=payload, capture_output=True, text=True, cwd=fixture, env=env,
        timeout=60,
    )

    assert result.returncode == 0
    assert result.stdout == ""
    assert "no target hook script argument" in result.stderr
