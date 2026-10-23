"""Tests for ``providers.explicit_primary_role`` (IC-1, #1006).

The helper is the single source of truth for the *declared* entry-point role of
a provider: it returns the registry value only when
``provider_config[provider]['primary-role']`` is a non-empty ``str``, and
``None`` otherwise. There is deliberately NO code default (the historic
``'orchestrator'`` default in the mode derivation is retired, see spec
SPEC-OPENCODE-ENTRYPOINT-1006-2026-10-22, IC-1) — a provider that never
declares the key must never be promoted to a primary agent implicitly.

Fail-safe contract under test: the helper never raises. Missing provider,
non-dict entry, non-dict registry, non-str value and empty value all yield
``None``.

Run: python3 -m pytest tests/test_explicit_primary_role.py -q
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.providers import explicit_primary_role, load_providers_config

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_returns_declared_role():
    """A declared, non-empty role is returned verbatim."""
    assert (
        explicit_primary_role({"P": {"primary-role": "orchestrator"}}, "P")
        == "orchestrator"
    )


def test_missing_provider_returns_none():
    """An unregistered provider has no declared role."""
    assert explicit_primary_role({"P": {"primary-role": "orchestrator"}}, "Q") is None


def test_entry_without_key_returns_none():
    """A registered provider without ``primary-role`` gets no code default."""
    assert explicit_primary_role({"P": {"capabilities": []}}, "P") is None


def test_non_dict_entry_returns_none():
    """A malformed (non-mapping) provider entry yields ``None``, never raises."""
    assert explicit_primary_role({"P": "x"}, "P") is None


def test_non_str_or_empty_value_returns_none():
    """Non-str and empty-str values are not a declared role."""
    for value in (5, ["orchestrator"], "", None):
        assert explicit_primary_role({"P": {"primary-role": value}}, "P") is None


def test_non_dict_registry_returns_none():
    """A non-mapping registry yields ``None``, never raises."""
    for registry in (None, []):
        assert explicit_primary_role(registry, "P") is None


def test_real_registry_opencode_explicit_mammouth_none():
    """The real registry: one provider declares the key, another does not.

    Proves the helper reads the shape ``load_providers_config`` actually
    returns and that a provider without the key stays without a role (AC-03,
    AC-04 groundwork).
    """
    registry = load_providers_config(REPO_ROOT)
    assert explicit_primary_role(registry, "Opencode") == "orchestrator"
    assert explicit_primary_role(registry, "Mammouth") is None
