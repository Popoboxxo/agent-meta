"""Task 0e.4 (IC-28, AC-44/AC-87): the new-role checklist lives in the conventions rule."""
import re
from pathlib import Path

_CONVENTIONS = (
    Path(__file__).resolve().parent.parent
    / "rules" / "2-platform" / "agent-meta-conventions.md"
)
_HEADING = "## Neue-Rolle-Checkliste"

# One keyword per checklist item, in the order of spec IC-28 (Nr. 1-12).
_ORDERED_KEYWORDS = [
    "agents/1-generic/",          # 1 template
    "role-defaults",              # 2 role-defaults entry
    "project-config.schema.json", # 3 schema enum
    "_EXPECTED_TOTAL",            # 4 pinned tests
    "--render-standalone",        # 5 standalone export
    "Szenario",                   # 6 scenario
    "CHANGELOG",                  # 7 changelog
    "cli-reference",              # 8 docs
    ".meta-config/project.yaml",  # 9 self-hosting
    "Aktivierungsgruppe",         # 10 activation group
    "provider",                   # 11 provider-agnostic
    "frontmatter.version-bump",   # 12 version bumps
]


def _section() -> str:
    text = _CONVENTIONS.read_text(encoding="utf-8")
    start = text.index(_HEADING)
    nxt = re.search(r"^## ", text[start + len(_HEADING):], re.MULTILINE)
    return text[start:start + len(_HEADING) + nxt.start()] if nxt else text[start:]


def _items(section: str):
    return re.findall(r"^(\d+)\. (.*)$", section, re.MULTILINE)


def test_section_exists():
    assert _HEADING in _CONVENTIONS.read_text(encoding="utf-8")


def test_exactly_twelve_numbered_items_in_order():
    items = _items(_section().split("### Praxis-Hinweise")[0])
    assert [n for n, _ in items] == [str(i) for i in range(1, 13)]


def test_items_follow_spec_order():
    items = _items(_section().split("### Praxis-Hinweise")[0])
    for (num, body), keyword in zip(items, _ORDERED_KEYWORDS):
        assert keyword in body, f"item {num} lacks keyword {keyword!r}"


def test_central_keywords_present():
    section = _section()
    for kw in (
        "role-defaults", "addressability", "name_only_reason",
        "project-config.schema.json", "standalone", "slimming-golden",
        "hashes.json", "_EXPECTED_TOTAL", "Szenario",
        "gen_role_routing_eval_catalog", "context_budgets", "Praxis-Hinweise",
    ):
        assert kw in section, f"missing keyword {kw!r}"
