"""Runtime-gate plugin generator contract (Phase 1, observe).

Covers the capability-gated plugin generator
(SPEC-OPENCODE-RUNTIME-GATE-2026-09-13, IC-08/IC-15) in its shipped,
**observe-only** form:

- AC-16: a provider with ``has_plugins`` + verified ``plugin_protocol`` gets the
  artifact written and recorded in the ``.agent-meta-managed`` index; without
  the capability no file is written.
- AC-17: flipping ``has_plugins`` off removes the previously managed artifact
  and leaves project-owned files in the plugin directory untouched.
- AC-18: an unknown ``plugin_protocol`` or a missing template warns and writes
  nothing (never silent, never a crash).
- AC-19: the artifact bakes ``MODE=observe``; ``enforce`` stays locked until
  the P6 real-repo verification (plan Task 9).

The plugin never blocks: the generated artifact only annotates via
``tool.execute.before``.

Run: python -m pytest tests/test_runtime_gate_plugins.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.log import SyncLog
from lib.runtime_gate import (
    PLUGIN_STEM,
    PLUGIN_TEMPLATE_BY_PROTOCOL,
    runtime_gate_plugin_relpath,
    sync_runtime_gate_plugins,
)

_PROVIDER = "ProviderX"
_PLUGIN_REL = Path(".opencode/plugins") / f"{PLUGIN_STEM}.js"


def _pc(**overrides) -> dict:
    pc = {
        "has_plugins": True,
        "plugin_dir": ".opencode/plugins",
        "plugin_ext": ".js",
        "plugin_protocol": "opencode-plugin-js",
    }
    pc.update(overrides)
    return pc


def _sync(project_root: Path, pc: dict, *, agent_meta_root: Path = _REPO_ROOT,
          config: dict | None = None, dry_run: bool = False) -> SyncLog:
    log = SyncLog()
    sync_runtime_gate_plugins(
        agent_meta_root, project_root, config or {}, log, dry_run, _PROVIDER,
        {_PROVIDER: pc},
    )
    return log


def test_plugin_written_when_supported(tmp_path: Path) -> None:
    """AC-16: capability + verified protocol -> artifact written + indexed."""
    project_root = tmp_path / "project"
    log = _sync(project_root, _pc())

    target = project_root / _PLUGIN_REL
    assert target.is_file(), log.warnings
    index = (project_root / ".opencode/plugins/.agent-meta-managed").read_text(
        encoding="utf-8"
    )
    assert f"{PLUGIN_STEM}.js" in index
    assert any("COPY" in action for action in log.actions)


def test_no_plugin_written_without_capability(tmp_path: Path) -> None:
    """AC-16/AC-22: no ``has_plugins`` -> no artifact, no plugin dir."""
    project_root = tmp_path / "project"
    log = _sync(project_root, _pc(has_plugins=False))

    assert not (project_root / _PLUGIN_REL).exists()
    assert not (project_root / ".opencode/plugins").exists()
    assert log.actions == []


def test_plugin_rollback_when_has_plugins_false(tmp_path: Path) -> None:
    """AC-17: capability off removes the managed artifact, keeps project files."""
    project_root = tmp_path / "project"
    _sync(project_root, _pc())
    target = project_root / _PLUGIN_REL
    assert target.is_file()

    owned = project_root / ".opencode/plugins/custom-project-plugin.js"
    owned.write_text("// project-owned\n", encoding="utf-8")

    log = _sync(project_root, _pc(has_plugins=False))

    assert not target.exists()
    assert owned.is_file()
    assert owned.read_text(encoding="utf-8") == "// project-owned\n"
    assert not (project_root / ".opencode/plugins/.agent-meta-managed").exists()
    assert any("DELETE" in action for action in log.actions)


def test_unknown_protocol_or_missing_template_warns_without_write(
    tmp_path: Path,
) -> None:
    """AC-18: unknown protocol / missing template -> warn, no write, no crash."""
    project_root = tmp_path / "project"
    log = _sync(project_root, _pc(plugin_protocol="bogus-plugin-js"))

    assert not (project_root / _PLUGIN_REL).exists()
    assert any("unsupported plugin_protocol" in w for w in log.warnings)

    empty_root = tmp_path / "empty-agent-meta"
    empty_root.mkdir()
    project_root_2 = tmp_path / "project-2"
    log_2 = _sync(project_root_2, _pc(), agent_meta_root=empty_root)

    assert not (project_root_2 / _PLUGIN_REL).exists()
    assert any("no template" in w for w in log_2.warnings)


def test_missing_plugin_dir_warns_without_write(tmp_path: Path) -> None:
    """IC-08: ``has_plugins`` without a ``plugin_dir`` warns, never silent."""
    project_root = tmp_path / "project"
    log = _sync(project_root, _pc(plugin_dir=""))

    assert not (project_root / ".opencode/plugins").exists()
    assert any("no plugin_dir" in w for w in log.warnings)


def test_plugin_mode_observe_by_default(tmp_path: Path) -> None:
    """AC-19: the artifact bakes ``MODE=observe`` and never ``enforce``."""
    project_root = tmp_path / "project"
    _sync(project_root, _pc())
    content = (project_root / _PLUGIN_REL).read_text(encoding="utf-8")

    assert 'MODE = "observe"' in content
    assert 'MODE = "enforce"' not in content
    assert "{{" not in content


def test_plugin_mode_stays_observe_until_p6(tmp_path: Path) -> None:
    """AC-19 (P6 lock): a configured ``enforce`` is not baked before Task 9."""
    project_root = tmp_path / "project"
    _sync(project_root, _pc(), config={"runtime-gate": {"plugin-mode": "enforce"}})
    content = (project_root / _PLUGIN_REL).read_text(encoding="utf-8")

    assert 'MODE = "observe"' in content
    assert 'MODE = "enforce"' not in content


def test_agent_allowlist_baked_from_role_registry(tmp_path: Path) -> None:
    """IC-15: the delegated-role allowlist is baked at sync time."""
    project_root = tmp_path / "project"
    _sync(project_root, _pc())
    content = (project_root / _PLUGIN_REL).read_text(encoding="utf-8")

    assert "AGENT_ALLOWLIST = [" in content
    assert '"orchestrator"' in content
    assert "AGENT_ALLOWLIST = {{" not in content


def test_dry_run_writes_nothing(tmp_path: Path) -> None:
    """``dry_run`` detects but never writes the artifact."""
    project_root = tmp_path / "project"
    _sync(project_root, _pc(), dry_run=True)
    assert not (project_root / ".opencode/plugins").exists()


def test_second_sync_is_idempotent(tmp_path: Path) -> None:
    """A second sync leaves identical content and reports ``unchanged``."""
    project_root = tmp_path / "project"
    _sync(project_root, _pc())
    target = project_root / _PLUGIN_REL
    first = target.read_text(encoding="utf-8")

    log = _sync(project_root, _pc())
    assert target.read_text(encoding="utf-8") == first
    assert any("unchanged" in entry for entry in log.skipped)


def test_plugin_relpath_is_config_driven() -> None:
    """IC-08: the relpath derives from config keys only, fail-safe to None."""
    assert runtime_gate_plugin_relpath(_pc()) == (
        f".opencode/plugins/{PLUGIN_STEM}.js"
    )
    assert runtime_gate_plugin_relpath(_pc(has_plugins=False)) is None
    assert runtime_gate_plugin_relpath(_pc(plugin_ext="")) is None
    assert runtime_gate_plugin_relpath(_pc(plugin_dir="")) is None
    assert runtime_gate_plugin_relpath(None) is None
    assert runtime_gate_plugin_relpath({}) is None


def test_template_mapping_targets_existing_observe_template() -> None:
    """IC-08/IC-15: the protocol maps to the shipped observe template."""
    rel = PLUGIN_TEMPLATE_BY_PROTOCOL["opencode-plugin-js"]
    template = _REPO_ROOT / rel
    assert template.is_file()
    text = template.read_text(encoding="utf-8")
    assert "tool.execute.before" in text
    assert 'MODE = "observe"' not in text  # mode is substituted, not hard-coded
    assert 'MODE !== "enforce"' in text
    assert "throw new Error" not in text
