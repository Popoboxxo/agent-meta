"""Addressability coverage over the real role config (pinned role count below).

SPEC ``dynamic-routing-template-slimming`` AC A1/A5 (Task 4, #779 IT-6):
every role declares ``routing.addressability`` ∈ {keyword, name_only, excluded};
the distribution is pinned (``_EXPECTED_DISTRIBUTION``);
``excluded`` is exactly ``orchestrator``; every keyword role has non-empty
``routing_patterns.keywords`` or ``.examples``; every name_only role has a
non-empty ``name_only_reason``. IC-29 coverage: every role with language-mapping
``examples`` offers ≥ 1 example per language any mapping of the config uses.

The derivation helper is intentionally defined *in the test only* (the
production resolver belongs to a later task): it mirrors the spec rule
"patterns present → keyword, else name_only; orchestrator always excluded".
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

from scripts.lib.delegation_table import _normalize_language
from scripts.lib.roles import load_roles_config

REPO_ROOT = Path(__file__).resolve().parents[1]
_EXPECTED_TOTAL = 94
_EXPECTED_DISTRIBUTION = {"keyword": 88, "name_only": 5, "excluded": 1}
# Ratchet exceptions for test_name_only_roles_have_no_routing_patterns (IC-28 Nr. 2):
# name_only roles that still carry routing_patterns. Empty since Task 1.35 (Q9);
# new entries are not allowed.
_NAME_ONLY_PATTERN_EXCEPTIONS = frozenset()
_VALID = {"keyword", "name_only", "excluded"}


def _roles() -> dict:
    return load_roles_config(REPO_ROOT)["roles"]


def _mapping_language_gaps(roles: dict) -> dict[str, list[str]]:
    """IC-29 coverage (test-local mirror): role -> mapping languages it lacks.

    Collects every language a list-variant mapping of the config carries
    (normalized, so ``en``/``English`` count as the same language) and reports,
    per role with mapping ``examples``, which of them have no example there.
    An empty list is a missing variant, not coverage: the language key still
    marks the language as used, so the gap is reported (IC-29: ≥ 1 example
    per language).
    """
    mappings = {}
    for name, info in roles.items():
        examples = (info.get("routing_patterns") or {}).get("examples")
        if isinstance(examples, dict):
            mappings[name] = examples

    all_languages: dict[str, str] = {}
    for mapping in mappings.values():
        for key, value in mapping.items():
            if isinstance(value, list):
                all_languages.setdefault(_normalize_language(key), key)

    gaps: dict[str, list[str]] = {}
    for name, mapping in mappings.items():
        # IC-29 requires ≥ 1 example per language: an empty list is a gap,
        # never coverage (the language key still counts as "used" above).
        present = {
            _normalize_language(key)
            for key, value in mapping.items()
            if isinstance(value, list) and value
        }
        missing = sorted(
            label for norm, label in all_languages.items() if norm not in present
        )
        if missing:
            gaps[name] = missing
    return gaps


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


def test_mapping_examples_cover_every_language_used_in_any_mapping():
    """IC-29 mapping coverage: a role with mapping ``examples`` must offer at
    least one example per language any mapping of the config uses (prevents the
    #780 Option-B error "present in EN, missing in DE").

    Vacuous until task 1.46 adds mapping data to ``role-defaults.yaml``; the
    red-ability of the guard is pinned with a synthetic incomplete mapping.
    """
    assert _mapping_language_gaps(_roles()) == {}

    synthetic = {
        "complete": {
            "routing_patterns": {
                "examples": {"Deutsch": ["d"], "English": ["e"]},
            }
        },
        "incomplete": {
            "routing_patterns": {
                "examples": {"English": ["e"]},
            }
        },
        "flat-list": {
            "routing_patterns": {
                "examples": ["neutral for every language"],
            }
        },
    }
    assert _mapping_language_gaps(synthetic) == {"incomplete": ["Deutsch"]}

    empty_variant = {
        "empty-lang": {
            "routing_patterns": {
                "examples": {"Deutsch": [], "English": ["e"]},
            }
        },
    }
    assert _mapping_language_gaps(empty_variant) == {"empty-lang": ["Deutsch"]}


def test_name_only_roles_have_reason():
    roles = _roles()
    name_only = sorted(
        name
        for name, info in roles.items()
        if (info.get("routing") or {}).get("addressability") == "name_only"
    )
    assert name_only == [
        "intern-developer", "meta-doctor", "meta-optimizer",
        "principal-developer", "template-auditor",
    ]
    for name in name_only:
        reason = (roles[name].get("routing") or {}).get("name_only_reason")
        assert isinstance(reason, str) and reason.strip(), (
            f"{name}: name_only_reason missing/empty"
        )


def test_name_only_roles_have_no_routing_patterns():
    """IC-28 Nr. 2: name_only roles carry no routing_patterns/intent_keywords."""
    roles = _roles()
    offenders = []
    for name, info in roles.items():
        routing = info.get("routing") or {}
        if routing.get("addressability") != "name_only":
            continue
        patterns = info.get("routing_patterns") or {}
        if patterns.get("keywords") or patterns.get("examples") or routing.get("intent_keywords"):
            offenders.append(name)
    assert sorted(offenders) == sorted(_NAME_ONLY_PATTERN_EXCEPTIONS), (
        f"name_only roles with routing patterns drifted: {sorted(offenders)} "
        f"(allowed ratchet exceptions: {sorted(_NAME_ONLY_PATTERN_EXCEPTIONS)})"
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
