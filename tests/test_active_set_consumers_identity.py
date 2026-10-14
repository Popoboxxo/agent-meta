"""QG-13 (dynamic) / AC-45: all routing generators consume ONE shared ActiveSet.

Spec ``docs/specs/2026-10-11-context-profiles-spec.md`` IC-17/IC-18 no. 1: per
sync ``compute_active_set`` runs exactly once; ``delegation_table`` (routing
rules, agents data, intent table), ``agents`` (hints, table) and the per-provider
agent loop (``_should_skip_role``) receive that very object (``is`` identity)
instead of recomputing the role set.

The sync is run in-process (``sync.main``) with spies on the compute function
and on every generator entry point; the spies delegate to the real code, so the
sync itself runs unchanged.

Known gap (accepted residual risk, follow-up): ``context.py`` (``build_agent_hints`` ~644/646,
``get_active_agents_data`` ~1717) still calls ``resolve_active_roles`` itself instead of
receiving the shared object; it does not call ``compute_active_set``, so the count above
holds, and the drift risk is low (same resolver).
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import sync  # noqa: E402
import lib.active_set as active_set_mod  # noqa: E402
import lib.agent_sync as agent_sync_mod  # noqa: E402
import lib.agents as agents_mod  # noqa: E402
import lib.cli_commands as cli_commands_mod  # noqa: E402
import lib.config as config_mod  # noqa: E402
import lib.delegation_table as delegation_mod  # noqa: E402

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "active-set"

# (module, attribute) of every generator that must receive the shared object.
_GENERATORS = (
    (delegation_mod, "get_active_agents_data"),
    (delegation_mod, "get_routing_rules"),
    (delegation_mod, "get_intent_routing_table"),
    (agents_mod, "build_agent_hints"),
    (agents_mod, "build_agent_table"),
    (agents_mod, "build_routing_tool_definitions_for_providers"),
    (agent_sync_mod, "_should_skip_role"),
)
# config.py binds some generators by name at import time.
_CONFIG_BOUND = (
    "get_active_agents_data",
    "get_intent_routing_table",
    "build_agent_hints",
    "build_agent_table",
    "build_routing_tool_definitions_for_providers",
)


def _project(tmp_path: Path, fixture: str) -> Path:
    (tmp_path / ".meta-config").mkdir()
    dest = tmp_path / ".meta-config" / "project.yaml"
    shutil.copyfile(_FIXTURES / fixture / ".meta-config" / "project.yaml", dest)
    with dest.open("a", encoding="utf-8") as fh:
        fh.write("project:\n  name: t\n  prefix: t\n")
    subprocess.run(["git", "init", "-q"], cwd=tmp_path, check=True)
    return tmp_path


def _spy(monkeypatch, module, name, calls):
    real = getattr(module, name)

    def wrapper(*args, **kwargs):
        calls.append((name, kwargs.get("active_set")))
        return real(*args, **kwargs)

    monkeypatch.setattr(module, name, wrapper)


@pytest.mark.parametrize("fixture", ["pall", "p10"])
def test_one_active_set_per_sync_shared_by_all_generators(tmp_path, monkeypatch, fixture):
    root = _project(tmp_path, fixture)

    computed = []
    real_compute = active_set_mod.compute_active_set

    def counting_compute(*args, **kwargs):
        result = real_compute(*args, **kwargs)
        computed.append(result)
        return result

    # Every binding of compute_active_set that a sync can reach.
    monkeypatch.setattr(active_set_mod, "compute_active_set", counting_compute)
    monkeypatch.setattr(cli_commands_mod, "compute_active_set", counting_compute)
    monkeypatch.setattr(config_mod, "compute_active_set", counting_compute)

    calls: list = []
    for module, name in _GENERATORS:
        _spy(monkeypatch, module, name, calls)
    for name in _CONFIG_BOUND:
        _spy(monkeypatch, config_mod, name, calls)

    monkeypatch.chdir(root)
    monkeypatch.setattr(
        sys, "argv", ["sync.py", "--config", str(root / ".meta-config" / "project.yaml")])
    try:
        sync.main()
    except SystemExit as exc:
        assert exc.code in (None, 0)

    assert len(computed) == 1, "compute_active_set must run exactly once per sync"
    shared = computed[0]

    seen = {name for name, _ in calls}
    for _, name in _GENERATORS:
        assert name in seen, f"generator {name} was never called (spy not effective)"
    for name, received in calls:
        assert received is shared, f"{name} did not receive the shared ActiveSet object"
