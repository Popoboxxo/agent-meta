"""Name-only roles stay routable but leave the rendered agent tables.

The eight literature-evidence review roles are ``routing.addressability:
name_only``. A table row for them adds bytes to the hard-capped entry files
without adding a keyword route, so the rendered tables list only
keyword-addressable roles. The routing contract is unchanged: name-only roles
remain in ``target_agents`` and ``routing.name_index`` because they are
reachable by explicit name dispatch.

The excluded set is re-derived here from ``config/role-defaults.yaml``
(explicit ``routing.addressability``, else ``keyword`` when routing patterns
exist, else ``name_only``) — no role name is hardcoded in this test or in the
production filter.
"""
from __future__ import annotations

import re
from pathlib import Path

import yaml

from scripts.lib.config import build_variables, load_config
from scripts.lib.delegation_table import (
    exclude_name_only,
    get_active_agents_data,
    get_routing_rules,
)
from scripts.lib.roles import load_roles_config, resolve_active_roles
from tests.active_set_render import preset_config, synced_project

REPO_ROOT = Path(__file__).resolve().parents[1]
_ROW_RE = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)
_ENTRY_TABLE_HEADER = "| Agent | Core Capabilities |"


def _repo_config() -> dict:
    return load_config(REPO_ROOT / ".meta-config" / "project.yaml")


def _config_derived_name_only() -> set[str]:
    """Re-derive the name-only roles from raw config (independent of the helper)."""
    roles = load_roles_config(REPO_ROOT)["roles"]
    name_only: set[str] = set()
    for role, info in roles.items():
        info = info if isinstance(info, dict) else {}
        routing = info.get("routing") if isinstance(info.get("routing"), dict) else {}
        addressability = routing.get("addressability")
        if addressability == "name_only":
            name_only.add(role)
        elif addressability not in ("keyword", "excluded"):
            patterns = info.get("routing_patterns")
            patterns = patterns if isinstance(patterns, dict) else {}
            if not (patterns.get("keywords") or patterns.get("examples")):
                name_only.add(role)
    return name_only


def _active_name_only(config: dict) -> set[str]:
    active = set(resolve_active_roles(REPO_ROOT, config, require_template=True))
    return _config_derived_name_only() & active


def test_name_only_roles_are_absent_from_the_rendered_agent_table():
    config = _repo_config()
    variables, _ = build_variables(config, REPO_ROOT)
    active = [entry["name"] for entry in variables["active_agents"]]
    name_only = _active_name_only(config)

    assert name_only, "precondition: the repo activates at least one name-only role"
    table_roles = _ROW_RE.findall(variables["AGENT_DELEGATION_TABLE"])
    assert not (set(table_roles) & name_only), sorted(set(table_roles) & name_only)
    # Exact complement: no keyword-addressable role was dropped by accident.
    assert table_roles == [role for role in active if role not in name_only]


def test_name_only_roles_stay_in_routing_targets_and_name_index():
    config = _repo_config()
    name_only = _active_name_only(config)
    routing = get_routing_rules(REPO_ROOT, config, {})

    assert name_only <= set(routing["target_agents"])
    by_name = {entry["agent"]: entry for entry in routing["name_index"]}
    assert name_only <= set(by_name)
    assert {by_name[role]["addressability"] for role in name_only} == {"name_only"}


def test_include_name_only_false_drops_exactly_the_config_derived_set():
    config = _repo_config()
    full = get_active_agents_data(REPO_ROOT, config, {})
    filtered = get_active_agents_data(REPO_ROOT, config, {}, include_name_only=False)

    assert [entry["name"] for entry in filtered] == [
        entry["name"] for entry in full if entry["name"] not in _config_derived_name_only()
    ]
    assert all(entry["addressability"] != "name_only" for entry in filtered)


def test_filter_reads_addressability_from_the_role_config(tmp_path):
    """Flipping one role's config flips its table presence — nothing is hardcoded."""
    meta_root = tmp_path / "meta"
    (meta_root / "config").mkdir(parents=True)
    roles_data = yaml.safe_load(
        (REPO_ROOT / "config" / "role-defaults.yaml").read_text(encoding="utf-8"))
    roles_data["roles"]["developer"]["routing"]["addressability"] = "name_only"
    (meta_root / "config" / "role-defaults.yaml").write_text(
        yaml.safe_dump(roles_data, sort_keys=False, allow_unicode=True), encoding="utf-8")
    load_roles_config.cache_clear()
    try:
        rows = get_active_agents_data(
            meta_root, {}, {}, template_roles={"developer", "tester"},
            include_name_only=False,
        )
    finally:
        load_roles_config.cache_clear()
    assert [entry["name"] for entry in rows] == ["tester"]


def test_rendered_entry_file_directory_omits_name_only_roles(tmp_path_factory):
    """The real sync path (``_build_managed_block``) applies the same filter."""
    project = synced_project(tmp_path_factory, preset_config("Opencode"))
    text = (project / "AGENTS.md").read_text(encoding="utf-8")
    start = text.index(_ENTRY_TABLE_HEADER)
    table = text[start:text.index("\n\n", start)]
    rows = set(_ROW_RE.findall(table))

    name_only = _config_derived_name_only()
    assert name_only, "precondition: the matrix activates name-only roles"
    assert not (rows & name_only), sorted(rows & name_only)
    # Guard against a vacuous pass (empty/renamed table).
    assert {"developer", "tester"} <= rows
