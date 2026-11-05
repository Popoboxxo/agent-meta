"""Regression tests for the OpenCode entry-point / emitted-role invariant.

Issue #1090 (D16): agent-meta must never point ``default_agent`` at a role
this sync did not generate for the provider. In ``orchestrator.mode:
main-chat`` (or legacy ``enabled: false``) the orchestrator agent is not
emitted, so the entry point must stay absent — the session would otherwise
die on an unknown agent.

Three properties are pinned here:

* not-emitted → no entry point is written,
* a dangling USER value survives untouched (only a
  ``opencode.default-agent.dangling`` warning, D16 "user value wins"),
* the valid (strict) case is byte-identical to the pre-fix behaviour.

Run: python3 -m pytest tests/test_opencode_main_chat_entry_point.py -v
"""
from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import isolation
from lib.active_set import role_emitted_for_provider
from lib.context import apply_settings_surface_shape
from lib.log import SyncLog

AS = SimpleNamespace(
    roles=frozenset({"orchestrator", "developer"}),
    known_roles=frozenset({"orchestrator", "developer", "tester"}),
)
PC = {"Opencode": {"primary-role": "orchestrator"}}
MAIN = {"orchestrator": {"mode": "main-chat"}}
STRICT = {"orchestrator": {"mode": "strict"}}


def test_role_emitted_matrix():
    assert role_emitted_for_provider("orchestrator", AS, STRICT, "Opencode") is True
    assert role_emitted_for_provider("orchestrator", AS, MAIN, "Opencode") is False
    assert role_emitted_for_provider("developer", AS, MAIN, "Opencode") is True
    assert role_emitted_for_provider("tester", AS, STRICT, "Opencode") is False
    assert role_emitted_for_provider("orchestrator", None, STRICT, "Opencode") is True


def test_provider_override_only_for_that_provider():
    cfg = {
        "orchestrator": {
            "mode": "strict",
            "provider-overrides": {"Opencode": {"mode": "main-chat"}},
        }
    }
    assert role_emitted_for_provider("orchestrator", AS, cfg, "Opencode") is False
    assert role_emitted_for_provider("orchestrator", AS, cfg, "Gemini") is True


def test_legacy_enabled_false_equals_main_chat():
    assert (
        role_emitted_for_provider(
            "orchestrator", AS, {"orchestrator": {"enabled": False}}, "Opencode"
        )
        is False
    )


def test_entry_point_none_in_main_chat_and_compat_without_config():
    assert isolation._opencode_entry_point("Opencode", PC, AS, MAIN) is None
    assert isolation._opencode_entry_point("Opencode", PC, AS, STRICT) == "orchestrator"
    assert isolation._opencode_entry_point("Opencode", PC, AS) == "orchestrator"


def _run_gate(tmp_path, config, initial="{}\n"):
    (tmp_path / "opencode.json").write_text(initial, encoding="utf-8")
    log = SyncLog()
    isolation._sync_opencode_runtime_gate(
        tmp_path, config, "Opencode", PC, REPO_ROOT, log, False, AS
    )
    return json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8")), log


def test_main_chat_writes_no_default_agent_v1(tmp_path):
    doc, _ = _run_gate(tmp_path, MAIN)
    assert "default_agent" not in doc


def test_strict_unchanged_writes_default_agent(tmp_path):
    doc, _ = _run_gate(tmp_path, STRICT)
    assert doc["default_agent"] == "orchestrator"


# --- E2: v2 init surface + dangling user value -----------------------------


def test_init_shape_omits_default_agent_when_not_emitted():
    pc = {"mcp-config": {"format": "opencode-json-v2"}, "primary-role": "orchestrator"}
    assert (
        "default_agent"
        not in json.loads(
            apply_settings_surface_shape("{}\n", pc, emit_default_agent=False)
        )
    )
    assert (
        json.loads(apply_settings_surface_shape("{}\n", pc))["default_agent"]
        == "orchestrator"
    )


def test_dangling_user_default_agent_warns_not_deleted(tmp_path):
    doc, log = _run_gate(tmp_path, MAIN, initial='{"default_agent": "orchestrator"}\n')
    assert doc["default_agent"] == "orchestrator"
    assert any("opencode.default-agent.dangling" in w for w in log.warnings)


def test_foreign_default_agent_is_not_flagged(tmp_path):
    doc, log = _run_gate(tmp_path, MAIN, initial='{"default_agent": "build"}\n')
    assert doc["default_agent"] == "build" and not log.warnings


def test_managed_default_agent_removed_after_switch_to_main_chat(tmp_path):
    doc, _ = _run_gate(tmp_path, STRICT)
    assert doc["default_agent"] == "orchestrator"
    log = SyncLog()
    isolation._sync_opencode_runtime_gate(
        tmp_path, MAIN, "Opencode", PC, REPO_ROOT, log, False, AS
    )
    assert (
        "default_agent"
        not in json.loads((tmp_path / "opencode.json").read_text(encoding="utf-8"))
    )


@pytest.mark.parametrize("cfg", [MAIN, STRICT])
def test_invariant_default_agent_is_emitted_or_absent(tmp_path, cfg):
    doc, _ = _run_gate(tmp_path, cfg)
    value = doc.get("default_agent")
    assert value is None or role_emitted_for_provider(value, AS, cfg, "Opencode")
