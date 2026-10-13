"""IC-29 keyword guard (Phase 0 ratchet): routing keywords are language-neutral.

No keyword may contain umlauts (a, o, u with diaeresis, sharp s) or a word from a small German stoplist, unless
it is listed in ``config/routing-language.yaml: keyword_allow`` with a reason.
The allowlist may only shrink (ratchet): stale entries and growth beyond the
Phase-0 baseline fail.
"""
import re
import sys
from pathlib import Path

import yaml

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT))

from scripts.lib.roles import load_roles_config  # noqa: E402

PHASE0_ALLOW_MAX = 18  # may only decrease (AC-68)
_UMLAUT_RE = re.compile("[äöüßÄÖÜ]")
_STOPLIST = frozenset({
    "und", "oder", "der", "die", "das", "mit", "für", "fuer", "nicht", "bitte",
    "ein", "eine", "einen", "zum", "zur", "von", "dem", "den", "des", "auf", "aus",
    "bei", "nach", "wie", "ist", "wird",
})


def _config() -> dict:
    return yaml.safe_load((_ROOT / "config" / "routing-language.yaml").read_text(encoding="utf-8"))


def find_german_keywords(keywords_by_role: dict, allow: set) -> list:
    """Return ``(role, keyword)`` pairs that are German and not allowlisted."""
    hits = []
    for role, keywords in sorted(keywords_by_role.items()):
        for kw in keywords or []:
            words = set(re.findall(r"[^\W\d_]+", str(kw).casefold()))
            german = _UMLAUT_RE.search(str(kw)) or words & _STOPLIST
            if german and str(kw) not in allow:
                hits.append((role, str(kw)))
    return hits


def _real_keywords() -> dict:
    roles = load_roles_config(_ROOT)["roles"]
    return {n: (i.get("routing_patterns") or {}).get("keywords") or [] for n, i in roles.items()}


def test_umlaut_keyword_without_allowlist_is_red():
    assert find_german_keywords({"r": ["Prüfen"]}, set()) == [("r", "Prüfen")]
    assert find_german_keywords({"r": ["Prüfen"]}, {"Prüfen"}) == []


def test_stoplist_word_without_allowlist_is_red():
    assert find_german_keywords({"r": ["Tests und Docs"]}, set()) == [("r", "Tests und Docs")]
    assert find_german_keywords({"r": ["Tests and Docs"]}, set()) == []


def test_real_keywords_are_language_neutral_or_allowlisted():
    allow = {e["keyword"] for e in _config()["keyword_allow"]}
    assert find_german_keywords(_real_keywords(), allow) == []


def test_allowlist_entries_have_reason_and_are_not_stale():
    entries = _config()["keyword_allow"]
    present = {str(k) for kws in _real_keywords().values() for k in kws}
    for e in entries:
        assert str(e.get("reason", "")).strip(), e
        assert e["keyword"] in present, f"stale allowlist entry: {e['keyword']}"
    assert len({e["keyword"] for e in entries}) == len(entries)


def test_allowlist_only_shrinks():
    assert len(_config()["keyword_allow"]) <= PHASE0_ALLOW_MAX
