"""Sync-seam wiring of the runtime-gate tier bundle + A2 dispatch.

Covers the Phase-0 sync wiring (SPEC-OPENCODE-RUNTIME-GATE-2026-09-13):

- IC-04 / F-02: the ``GATE_*`` tier bundle from ``providers.runtime_gate_vars``
  must reach the actual renderer seams (``sync_context_for_provider`` and
  ``sync_rules``) — not just ``agent_sync._build_provider_vars``.
- IC-13 / AC-08 / AC-09: the A2 writer is dispatched from the per-provider
  stage for tier ``permission``, independent of the ``sync_provider_isolation``
  >=2-provider guard, so a single-provider project also gets the deny.
- AC-22: an ``advisory`` provider never gets the deny (and no plugin artifact).
- AC-07: the five new placeholders are registered built-ins.

Run: python -m pytest tests/test_runtime_gate_wiring.py -v
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import scripts.lib.sync_pipeline as sync_pipeline  # noqa: E402
from lib.consistency import placeholders  # noqa: E402
from lib.log import SyncLog  # noqa: E402

PROVIDER = "GateProbe"
_STATE_FILE = Path(".opencode") / "agent-meta-state.json"


def _framework_root(tmp_path: Path, provider: str, tier: str) -> Path:
    """Minimal framework root declaring ``provider`` at the given gate tier."""
    root = tmp_path / "agent-meta"
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "provider-capabilities.yaml").write_text(
        yaml.safe_dump({"capabilities": {provider: {"runtime_gate": tier}}}),
        encoding="utf-8",
    )
    return root


def _provider_config(has_plugins: bool = False) -> dict:
    """Provider entry with only rules enabled (all other sync paths skipped).

    ``has_plugins`` adds the IC-08/IC-14 runtime-gate plugin capability keys so
    the dispatch can be exercised with a fixture, independent of any real
    provider (Opencode still ships ``has_plugins: false``).
    """
    pc = {
        "has_rules": True,
        "rules_dir": ".test/rules",
        "has_hooks": False,
        "has_commands": False,
        "agents_dir": ".test/agents",
    }
    if has_plugins:
        pc.update({
            "has_plugins": True,
            "plugin_dir": ".opencode/plugins",
            "plugin_ext": ".js",
            "plugin_protocol": "opencode-plugin-js",
        })
    return {PROVIDER: pc}


def _run_per_provider(
    tmp_path: Path,
    monkeypatch,
    tier: str,
    config: dict,
    *,
    record_writer: bool = False,
    has_plugins: bool = False,
    agent_meta_root: Path | None = None,
    plugin_calls: list | None = None,
):
    """Drive ``_sync_stage_per_provider`` with every unrelated writer stubbed.

    ``has_plugins`` selects the capability fixture (IC-13). ``agent_meta_root``
    overrides the framework root (the real repo root is needed when the real
    plugin generator must find its template); the default fake root only
    resolves the tier capability. When ``plugin_calls`` is given, the plugin
    writer is replaced by a recorder so the dispatch itself can be asserted.

    Returns ``(captured_rule_vars, writer_calls, project_root)``.
    """
    root = agent_meta_root or _framework_root(tmp_path, PROVIDER, tier)
    project_root = tmp_path / "project"
    project_root.mkdir(parents=True, exist_ok=True)
    provider_config = _provider_config(has_plugins=has_plugins)
    captured: dict = {}
    writer_calls: list = []

    def _rules_spy(agent_meta_root, project_root, config, log, dry_run, **kwargs):
        captured["variables"] = dict(kwargs.get("variables") or {})

    monkeypatch.setattr(sync_pipeline, "sync_rules", _rules_spy)
    monkeypatch.setattr(sync_pipeline, "sync_speech_mode", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_agents_for_provider", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_prompts_for_continue", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_embedded_rule_files", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "generate_mcp_artifacts", lambda *a, **k: [])
    monkeypatch.setattr(sync_pipeline, "generate_external_tool_artifacts", lambda *a, **k: [])
    monkeypatch.setattr(sync_pipeline, "sync_snippets_for_provider", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sync_external_skills_for_provider", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "sweep_orphan_skill_channel_rules", lambda *a, **k: None)

    import lib.external_tools as external_tools_module
    import lib.mcp as mcp_module

    monkeypatch.setattr(mcp_module, "load_mcp_registry", lambda *a, **k: {})
    monkeypatch.setattr(
        external_tools_module, "load_external_tools_registry", lambda *a, **k: {}
    )

    if record_writer:
        monkeypatch.setattr(
            sync_pipeline, "_sync_opencode_runtime_gate",
            lambda *a, **k: writer_calls.append((a, k)),
        )
    if plugin_calls is not None:
        monkeypatch.setattr(
            sync_pipeline, "sync_runtime_gate_plugins",
            lambda *a, **k: plugin_calls.append((a, k)),
        )

    sync_pipeline._sync_stage_per_provider(
        root, project_root, config, provider_config, [PROVIDER], {},
        None, False, False, [], argparse.Namespace(dry_run=False), SyncLog(),
    )
    return captured, writer_calls, project_root


def test_tier_vars_reach_context_render(tmp_path, monkeypatch):
    """IC-04 / F-02: the context seam sees the resolved gate bundle."""
    root = _framework_root(tmp_path, PROVIDER, "permission")
    project_root = tmp_path / "project"
    captured: dict = {}

    def _context_spy(agent_meta_root, project_root, config, variables, log, dry_run,
                     provider, provider_config):
        captured["variables"] = dict(variables)

    monkeypatch.setattr(sync_pipeline, "sync_context_for_provider", _context_spy)

    sync_pipeline._sync_stage_contexts(
        root, project_root, {"orchestrator": {"mode": "strict"}},
        {PROVIDER: {"context_file": "CONTEXT.md"}}, [PROVIDER], {},
        argparse.Namespace(dry_run=False), SyncLog(),
    )

    variables = captured["variables"]
    assert variables["ENFORCEMENT_TIER"] == "permission"
    assert variables["GATE_PARTIAL"] == "true"
    assert variables["GATE_ENFORCED"] == "false"
    assert variables["GATE_ADVISORY"] == "false"
    assert variables["RUNTIME_GATE_PLUGIN_MODE"] == "observe"


def test_tier_vars_reach_rule_render(tmp_path, monkeypatch):
    """IC-04 / F-02: the rules seam sees the resolved gate bundle."""
    captured, _, _ = _run_per_provider(
        tmp_path, monkeypatch, "permission", {"orchestrator": {"mode": "strict"}},
    )
    variables = captured["variables"]
    assert variables["ENFORCEMENT_TIER"] == "permission"
    assert variables["GATE_PARTIAL"] == "true"
    assert variables["GATE_ENFORCED"] == "false"
    assert variables["GATE_ADVISORY"] == "false"
    assert variables["RUNTIME_GATE_PLUGIN_MODE"] == "observe"


def test_strict_sync_writes_mapping_deny(tmp_path, monkeypatch):
    """AC-08: tier permission + strict writes the managed mapping deny."""
    _, _, project_root = _run_per_provider(
        tmp_path, monkeypatch, "permission", {"orchestrator": {"mode": "strict"}},
    )

    data = json.loads((project_root / "opencode.json").read_text(encoding="utf-8"))
    assert data["permission"]["edit"] == {"**": "deny"}
    assert data["permission"]["bash"] == {"**": "deny"}

    state = json.loads((project_root / _STATE_FILE).read_text(encoding="utf-8"))
    assert state["runtime-gate-deny"] == {"**": {"edit": None, "bash": None}}


def test_single_provider_strict_writes_deny(tmp_path, monkeypatch):
    """AC-09: the dispatch is not gated by the isolation >=2-provider guard."""
    providers = [PROVIDER]
    assert len(providers) == 1

    captured, _, project_root = _run_per_provider(
        tmp_path, monkeypatch, "permission", {"orchestrator": {"mode": "strict"}},
    )
    assert captured["variables"]["ENFORCEMENT_TIER"] == "permission"

    data = json.loads((project_root / "opencode.json").read_text(encoding="utf-8"))
    assert data["permission"]["edit"]["**"] == "deny"
    assert data["permission"]["bash"]["**"] == "deny"


def test_advisory_sync_writes_no_deny_and_no_plugin(tmp_path, monkeypatch):
    """AC-22: advisory never dispatches the deny and deploys no plugin."""
    _, writer_calls, project_root = _run_per_provider(
        tmp_path, monkeypatch, "advisory", {"orchestrator": {"mode": "strict"}},
        record_writer=True,
    )

    assert writer_calls == []
    assert not (project_root / "opencode.json").exists()
    assert not (project_root / ".opencode" / "plugins").exists()


def test_plugin_dispatch_noop_without_capability(tmp_path, monkeypatch):
    """IC-13 / AC-16: no ``has_plugins`` -> writer not dispatched, no artifact.

    Proves the dispatch is capability-gated (config-key driven), not merely
    inert: the writer call itself must not happen.
    """
    plugin_calls: list = []
    _, _, project_root = _run_per_provider(
        tmp_path, monkeypatch, "advisory", {}, plugin_calls=plugin_calls,
    )

    assert plugin_calls == []
    assert not (project_root / ".opencode" / "plugins").exists()


def test_plugin_dispatch_fires_with_capability(tmp_path, monkeypatch):
    """IC-13 / AC-16: a ``has_plugins`` fixture dispatches the plugin writer."""
    plugin_calls: list = []
    _run_per_provider(
        tmp_path, monkeypatch, "plugin", {},
        has_plugins=True, agent_meta_root=_REPO_ROOT, plugin_calls=plugin_calls,
    )

    assert len(plugin_calls) == 1
    args, _kwargs = plugin_calls[0]
    assert args[0] == _REPO_ROOT
    assert args[5] == PROVIDER


def test_plugin_artifact_generated_with_capability(tmp_path, monkeypatch):
    """IC-13 / AC-16 / AC-19: the real generator writes the observe artifact."""
    _, _, project_root = _run_per_provider(
        tmp_path, monkeypatch, "plugin", {},
        has_plugins=True, agent_meta_root=_REPO_ROOT,
    )

    artifact = project_root / ".opencode" / "plugins" / "agent-meta-runtime-gate.js"
    assert artifact.is_file()
    content = artifact.read_text(encoding="utf-8")
    assert 'MODE = "observe"' in content
    assert 'MODE = "enforce"' not in content


def test_context_file_modes_paths_untouched_without_capability(tmp_path, monkeypatch):
    """IC-13 (c): the committed context-file-modes paths stay a no-op default.

    With the shipped ``has_plugins: false`` the per-provider stage dispatches no
    plugin writer and writes no plugin artifact, so the committed paths are
    untouched by the new dispatch.
    """
    _, _, project_root = _run_per_provider(tmp_path, monkeypatch, "advisory", {})
    assert not (project_root / ".opencode").exists()


def test_gate_vars_registered_in_builtin_vars():
    """AC-07: the five new placeholders no longer emit 'missing variable'."""
    names = {
        "ENFORCEMENT_TIER", "GATE_ENFORCED", "GATE_PARTIAL", "GATE_ADVISORY",
        "RUNTIME_GATE_PLUGIN_MODE",
    }
    assert names <= set(placeholders._BUILTIN_VARS)

    content = "\n".join("{{%s}}" % name for name in sorted(names))
    findings = placeholders.check_placeholders(Path("probe.md"), content, _REPO_ROOT)
    unknown = [f for f in findings if f.check == "placeholders.unknown"]
    assert unknown == [], [f.message for f in unknown]
