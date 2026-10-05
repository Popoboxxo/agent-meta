"""Regression lock for the context agent catalog (issue #811 / audit F15).

Audit check F15 compared the generated context catalog against the raw
``roles:`` whitelist in ``.meta-config/project.yaml`` and reported
``se-component-requirements`` as "missing". That is a false positive: the role
is listed in the whitelist but disabled by its ``activation_groups.se`` gate
(``systems-engineering.enabled: false``), so it is *not* an active role.

The binding contract is:

    set(catalog roles) == set(resolve_active_roles(..., require_template=True))

i.e. the catalog is Layer 1 (activation gates + project whitelist) intersected
with the generatable templates (Layer 2). The raw ``roles:`` whitelist is
deliberately broader than the active set; a gated-out whitelist entry must be
absent from the catalog. These tests lock that invariant so a future drift in
the builder (or a re-introduced whitelist-vs-active confusion in an audit) is
caught.
"""
from __future__ import annotations

import re
from pathlib import Path

from scripts.lib.config import build_variables, load_config
from scripts.lib.delegation_table import get_active_agents_data
from scripts.lib.roles import resolve_active_roles

REPO_ROOT = Path(__file__).resolve().parents[1]

_ROW_RE = re.compile(r"^\| `([^`]+)` \|", re.MULTILINE)

# Role whitelisted in this repo's project.yaml but intentionally gated out by
# ``activation_groups.se`` (``systems-engineering.enabled: false``).
_GATED_ROLE = "se-component-requirements"


def _repo_config() -> dict:
    return load_config(REPO_ROOT / ".meta-config" / "project.yaml")


def test_rendered_context_catalog_equals_resolved_active_roles():
    """The rendered catalog is exactly the Layer-2 active set (F15 invariant)."""
    config = _repo_config()
    variables, _ = build_variables(config, REPO_ROOT)

    catalog = _ROW_RE.findall(variables["AGENT_DELEGATION_TABLE"])
    expected = resolve_active_roles(REPO_ROOT, config, require_template=True)

    assert catalog == expected, (
        "context catalog drifted from resolve_active_roles(): "
        f"only-in-catalog={sorted(set(catalog) - set(expected))}, "
        f"missing={sorted(set(expected) - set(catalog))}"
    )
    # The catalog data used to build the table must agree as well.
    assert [entry["name"] for entry in variables["active_agents"]] == expected


def test_gated_whitelist_entry_is_intentionally_absent_from_catalog():
    """A whitelisted-but-gated role must NOT appear in the catalog (issue #811)."""
    config = _repo_config()

    # Preconditions that make this a gated-correctly case, not a builder bug.
    assert _GATED_ROLE in (config.get("roles") or [])
    assert config["systems-engineering"]["enabled"] is False

    catalog = {
        entry["name"] for entry in get_active_agents_data(REPO_ROOT, config, {})
    }
    assert _GATED_ROLE not in catalog
    # And it is excluded by the resolver for the same gate reason.
    assert _GATED_ROLE not in resolve_active_roles(
        REPO_ROOT, config, require_template=True
    )


def test_catalog_follows_activation_gate_semantics():
    """Whitelist entry flips into the catalog only when its gate is enabled."""
    base = _repo_config()
    whitelist = {**base, "roles": [_GATED_ROLE]}

    disabled = {**whitelist, "systems-engineering": {"enabled": False}}
    enabled = {**whitelist, "systems-engineering": {"enabled": True}}

    assert get_active_agents_data(REPO_ROOT, disabled, {}) == []
    assert [entry["name"] for entry in get_active_agents_data(REPO_ROOT, enabled, {})] == [
        _GATED_ROLE
    ]
