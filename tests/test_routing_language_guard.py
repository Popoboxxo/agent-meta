"""Routing-language guard for SPEC-ROUTING-LANGUAGE-779-780 (AC1 / AC4).

Locks the frozen canonical-keyword contract for Phase H:

- ``routing_patterns.keywords`` are canonical/language-neutral. The detector
  logic is NOT duplicated here: ``find_german_keywords``, ``_UMLAUT_RE``,
  ``_STOPLIST`` and ``PHASE0_ALLOW_MAX`` are imported from the existing Phase-0
  guard module. The frozen allowlist is the 17 ``keyword`` values from
  ``config/routing-language.yaml: keyword_allow``.
- Language nuance lives only in ``routing_patterns.examples`` as a tagged
  mapping ``{"Deutsch": [...], "English": [...]}``. Every such mapping must
  resolve to a non-empty list for BOTH languages.
- Coverage (roles with non-empty ``routing_patterns.keywords``) must not drop
  below the frozen baseline of 88.

New umlaut/stopword keywords outside the allowlist, allowlist growth, an empty
language variant or a coverage regression make the corresponding test red.
"""
from __future__ import annotations

from pathlib import Path

import yaml

from scripts.lib.delegation_table import _select_examples
from scripts.lib.roles import load_roles_config
from tests.test_routing_keywords_language_neutral import (
    PHASE0_ALLOW_MAX,
    _STOPLIST,
    _UMLAUT_RE,
    find_german_keywords,
)

_AGENT_META_ROOT = Path(__file__).resolve().parents[1]

# Frozen baseline (SPEC S2/D6, re-measured at HEAD e72b1d5f):
# 17 allowlist entries, 88 keyword roles.
_FROZEN_KEYWORD_ROLE_COUNT = 88


def _allow() -> set:
    """The frozen 17 ``keyword`` values from ``config/routing-language.yaml``."""
    config = yaml.safe_load(
        (_AGENT_META_ROOT / "config" / "routing-language.yaml").read_text(
            encoding="utf-8"
        )
    )
    return {entry["keyword"] for entry in config["keyword_allow"]}


def _keywords_by_role() -> dict:
    roles = load_roles_config(_AGENT_META_ROOT)["roles"]
    return {
        name: (info.get("routing_patterns") or {}).get("keywords") or []
        for name, info in roles.items()
    }


def test_keywords_are_canonical() -> None:
    """No keyword outside the frozen allowlist contains German markers.

    Positive direction: real config data is clean. Negative direction: an
    injected umlaut keyword outside the allowlist IS detected, while an
    allowlisted German keyword is tolerated (D-H3 — existing DE keywords stay
    allowed). The allowlist ratchet is frozen: it may only shrink.
    """
    allow = _allow()

    # Shared detector inputs are the frozen ones — no local stoplist duplicate.
    assert _UMLAUT_RE.search("Prüfen")
    assert "und" in _STOPLIST

    injected = "Prüfen"
    assert injected not in allow, "fixture keyword must be outside the freeze"
    assert find_german_keywords({"injected-role": [injected]}, allow) == [
        ("injected-role", injected)
    ]
    assert find_german_keywords(
        {"injected-role": [injected]}, allow | {injected}
    ) == []

    assert find_german_keywords(_keywords_by_role(), allow) == []
    assert len(allow) <= PHASE0_ALLOW_MAX


def test_examples_language_variants_resolve() -> None:
    """Every role with tagged examples resolves both languages non-empty."""
    roles = load_roles_config(_AGENT_META_ROOT)["roles"]
    tagged = {
        name: (info.get("routing_patterns") or {}).get("examples")
        for name, info in roles.items()
    }
    tagged = {
        name: examples
        for name, examples in tagged.items()
        if isinstance(examples, dict)
    }

    for name, examples in tagged.items():
        for language in ("Deutsch", "English"):
            resolved = _select_examples(examples, language)
            assert resolved, f"{name}: no examples resolved for {language}"

    # Non-vacuous guard: the tagged shape itself must resolve both variants.
    fixture = {"Deutsch": ["Deutsches Beispiel."], "English": ["English example."]}
    assert _select_examples(fixture, "Deutsch") == ["Deutsches Beispiel."]
    assert _select_examples(fixture, "English") == ["English example."]


def test_keyword_coverage_unchanged() -> None:
    """At least the frozen 88 roles still carry non-empty keywords."""
    covered = sum(1 for keywords in _keywords_by_role().values() if keywords)
    assert covered >= _FROZEN_KEYWORD_ROLE_COUNT
