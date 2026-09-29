"""warn_sink injection across the ``build_variables()`` builder call sites.

SPEC ``dynamic-routing-template-slimming`` Block A, AC A3 (plan Task 10):
every variable builder that resolves the active role set must receive a real
warning sink, and the collected warnings must surface in the ``unmapped`` list
returned by ``build_variables()`` instead of being silently dropped.
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib import config as config_module

_REPO_ROOT = Path(__file__).resolve().parents[1]

_BUILDER_NAMES = (
    "build_agent_hints",
    "build_agent_table",
    "get_intent_routing_table",
    "build_routing_tool_definitions_for_providers",
    "get_active_agents_data",
)


def _load_project_config() -> dict:
    from scripts.lib.io import _load_yaml_or_json

    data, _ = _load_yaml_or_json(_REPO_ROOT / ".meta-config" / "project.yaml")
    return data or {}


def _install_recorders(monkeypatch) -> list[dict]:
    """Patch every builder with a recording wrapper that delegates for real."""
    recorded: list[dict] = []

    def _record(name: str, real):
        def wrapper(*args, **kwargs):
            sink = kwargs.get("warn_sink")
            recorded.append({"name": name, "warn_sink": sink})
            if isinstance(sink, list):
                sink.append(f"wiring-probe: {name}")
            return real(*args, **kwargs)

        return wrapper

    for name in _BUILDER_NAMES:
        monkeypatch.setattr(config_module, name, _record(name, getattr(config_module, name)))
    return recorded


def _build(monkeypatch):
    recorded = _install_recorders(monkeypatch)
    variables, unmapped = config_module.build_variables(
        _load_project_config(), _REPO_ROOT, _REPO_ROOT
    )
    return recorded, variables, unmapped


def test_every_builder_call_receives_a_list_warn_sink(monkeypatch):
    recorded, _, _ = _build(monkeypatch)
    assert {entry["name"] for entry in recorded} == set(_BUILDER_NAMES)
    for entry in recorded:
        assert isinstance(entry["warn_sink"], list), entry["name"]


def test_injected_warning_surfaces_in_unmapped(monkeypatch):
    recorded, _, unmapped = _build(monkeypatch)
    for name in _BUILDER_NAMES:
        assert f"wiring-probe: {name}" in unmapped


def test_call_sites_never_pass_variables_as_sink(monkeypatch):
    recorded, variables, _ = _build(monkeypatch)
    for entry in recorded:
        assert entry["warn_sink"] is not variables


def test_get_active_agents_data_is_called_exactly_once(monkeypatch):
    """Regression guard for the duplicated ``active_agents`` wiring.

    The pre-fix working tree invoked ``get_active_agents_data()`` twice in
    ``_build_platform_variables()``, which doubled every warning the builder
    appended through the shared ``unmapped`` sink.
    """
    recorded, _, _ = _build(monkeypatch)
    calls = [entry for entry in recorded if entry["name"] == "get_active_agents_data"]
    assert len(calls) == 1


def test_activation_mirrors_are_sourced_from_resolver():
    """AC A2: the display mirror variables track the resolver's groups."""
    from scripts.lib.roles import resolve_activation_gates

    config = _load_project_config()
    variables, _ = config_module.build_variables(config, _REPO_ROOT, _REPO_ROOT)
    gates = resolve_activation_gates(_REPO_ROOT, config)

    for group, variable in (
        ("se", "SE_ENABLED"),
        ("knowledge", "KNOWLEDGE_ENGINE_ENABLED"),
        ("validator", "VALIDATOR_ENABLED"),
        ("developer_tiers", "DEVELOPER_TIERS_ENABLED"),
    ):
        enabled = bool((gates.get(group) or {}).get("enabled", False))
        expected = "true" if enabled else "false"
        assert variables[variable] == expected, variable
