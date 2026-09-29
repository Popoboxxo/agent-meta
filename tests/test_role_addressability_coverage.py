"""Addressability coverage over the real 84-role config.

SPEC ``dynamic-routing-template-slimming`` AC A1/A5 (Task 4, #779 IT-6):
every role declares ``routing.addressability`` ∈ {keyword, name_only, excluded};
the distribution is exactly ``81 keyword / 2 name_only / 1 excluded``;
``excluded`` is exactly ``orchestrator``; every keyword role has non-empty
``routing_patterns.keywords`` or ``.examples``; every name_only role has a
non-empty ``name_only_reason``.

The derivation helper is intentionally defined *in the test only* (the
production resolver belongs to a later task): it mirrors the spec rule
"patterns present → keyword, else name_only; orchestrator always excluded".
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from scripts.lib.roles import load_roles_config

REPO_ROOT = Path(__file__).resolve().parents[1]
_EXPECTED_TOTAL = 84
_EXPECTED_DISTRIBUTION = {"keyword": 81, "name_only": 2, "excluded": 1}
_VALID = {"keyword", "name_only", "excluded"}


def _roles() -> dict:
    return load_roles_config(REPO_ROOT)["roles"]


def derive_addressability(role_name: str, info: dict) -> str:
    """Spec §3.4 fallback rule (test-local mirror, no production code added).

    ``orchestrator`` is always ``excluded`` regardless of the derivation.
    Otherwise: explicit value wins; without one, non-empty patterns derive
    ``keyword`` and the absence of patterns derives ``name_only``.
    """
    routing = info.get("routing") or {}
    explicit = routing.get("addressability")
    if explicit:
        return explicit
    if role_name == "orchestrator":
        return "excluded"
    patterns = info.get("routing_patterns") or {}
    if patterns.get("keywords") or patterns.get("examples"):
        return "keyword"
    return "name_only"


def test_every_role_declares_a_valid_addressability():
    roles = _roles()
    assert len(roles) == _EXPECTED_TOTAL, f"role count changed: {len(roles)}"
    missing = [name for name, info in roles.items() if "addressability" not in (info.get("routing") or {})]
    assert not missing, f"roles without routing.addressability: {missing}"
    invalid = {
        name: (info.get("routing") or {}).get("addressability")
        for name, info in roles.items()
        if (info.get("routing") or {}).get("addressability") not in _VALID
    }
    assert not invalid, f"invalid addressability values: {invalid}"


def test_addressability_distribution_is_exact():
    roles = _roles()
    distribution = Counter(
        (info.get("routing") or {}).get("addressability") for info in roles.values()
    )
    assert dict(distribution) == _EXPECTED_DISTRIBUTION, (
        f"unexpected distribution: {dict(distribution)}"
    )


def test_excluded_is_exactly_orchestrator():
    roles = _roles()
    excluded = sorted(
        name
        for name, info in roles.items()
        if (info.get("routing") or {}).get("addressability") == "excluded"
    )
    assert excluded == ["orchestrator"], f"excluded set drifted: {excluded}"


def test_keyword_roles_have_non_empty_patterns():
    roles = _roles()
    keyword = [
        name
        for name, info in roles.items()
        if (info.get("routing") or {}).get("addressability") == "keyword"
    ]
    assert len(keyword) == _EXPECTED_DISTRIBUTION["keyword"]
    patternless = []
    for name in keyword:
        patterns = roles[name].get("routing_patterns") or {}
        if not (patterns.get("keywords") or patterns.get("examples")):
            patternless.append(name)
    assert not patternless, f"keyword roles without patterns: {patternless}"


def test_name_only_roles_have_reason():
    roles = _roles()
    name_only = sorted(
        name
        for name, info in roles.items()
        if (info.get("routing") or {}).get("addressability") == "name_only"
    )
    assert name_only == ["intern-developer", "principal-developer"]
    for name in name_only:
        reason = (roles[name].get("routing") or {}).get("name_only_reason")
        assert isinstance(reason, str) and reason.strip(), (
            f"{name}: name_only_reason missing/empty"
        )


def test_openscad_developer_is_keyword_routed_with_real_patterns():
    info = _roles()["openscad-developer"]
    assert (info.get("routing") or {}).get("addressability") == "keyword"
    patterns = info.get("routing_patterns") or {}
    assert patterns.get("keywords") or patterns.get("examples")
    # The new patterns must actually describe the OpenSCAD/3D domain.
    assert any("openscad" in str(k).casefold() or "3d" in str(k).casefold()
               for k in patterns.get("keywords") or [])


def test_derivation_helper_matches_configured_addressability():
    roles = _roles()
    for name, info in roles.items():
        configured = (info.get("routing") or {}).get("addressability")
        assert derive_addressability(name, info) == configured, (
            f"{name}: derivation {derive_addressability(name, info)!r} != "
            f"configured {configured!r}"
        )


def test_derivation_helper_semantics_without_explicit_field():
    # patterns present → keyword
    assert derive_addressability("x", {"routing_patterns": {"keywords": ["k"]}}) == "keyword"
    assert derive_addressability("x", {"routing_patterns": {"examples": ["e"]}}) == "keyword"
    # no patterns → name_only
    assert derive_addressability("x", {}) == "name_only"
    assert derive_addressability("x", {"routing_patterns": {}}) == "name_only"
    # orchestrator is excluded independent of derivation
    assert derive_addressability("orchestrator", {}) == "excluded"
    assert derive_addressability(
        "orchestrator", {"routing_patterns": {"keywords": ["k"]}}
    ) == "excluded"
    # explicit value wins
    assert derive_addressability("x", {"routing": {"addressability": "name_only"}}) == "name_only"
