"""IC-29 / AC-69 (`full` part): routing examples follow the project language.

One ``role-defaults.yaml`` fixture (same source for both renders) is rendered
with ``COMMUNICATION_LANGUAGE: Deutsch`` and ``English``; the full JSON routing
artifact shows the language-matching examples, both renders carry identical
canonical keyword sets, and a role whose mapping lacks the project language
falls back to the first variant and logs ``routing.examples-language-fallback``
(INFO). Selection goes exclusively through ``_select_examples`` — including
the ``en``/``de`` aliases and case-insensitive labels (no silent
wrong-language render).
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.agents import (
    build_routing_tool_definition,
    render_routing_tool_definition,
)
from scripts.lib.delegation_table import _select_examples

_FIXTURE = """\
roles:
  mapped-role:
    model: fast
    short_desc: Mapped
    workflow_tier: optional
    routing:
      addressability: keyword
    routing_patterns:
      keywords:
      - Canonical-Kw
      examples:
        Deutsch:
        - "Deutsches Beispiel."
        English:
        - "English example."
  fallback-role:
    model: fast
    short_desc: Fallback
    workflow_tier: optional
    routing:
      addressability: keyword
    routing_patterns:
      keywords:
      - Second-Kw
      examples:
        English:
        - "Only English."
  flat-role:
    model: fast
    short_desc: Flat
    workflow_tier: optional
    routing:
      addressability: keyword
    routing_patterns:
      keywords:
      - Third-Kw
      examples:
      - "Flat example."
"""

_TEMPLATE_ROLES = {"mapped-role", "fallback-role", "flat-role"}


def _fixture_root(tmp_path: Path) -> Path:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "role-defaults.yaml").write_text(_FIXTURE, encoding="utf-8")
    return tmp_path


def _rules_by_agent(root: Path, language: str, info_sink: list | None = None) -> dict:
    definition = build_routing_tool_definition(
        root,
        {},
        {"COMMUNICATION_LANGUAGE": language},
        template_roles=_TEMPLATE_ROLES,
        info_sink=info_sink,
    )
    return {rule["agent"]: rule for rule in definition["routing"]["rules"]}


def test_de_and_en_renders_show_language_matching_examples(tmp_path):
    root = _fixture_root(tmp_path)
    de = _rules_by_agent(root, "Deutsch")
    en = _rules_by_agent(root, "English")
    assert de["mapped-role"]["examples"] == ["Deutsches Beispiel."]
    assert en["mapped-role"]["examples"] == ["English example."]
    assert de["flat-role"]["examples"] == ["Flat example."]
    assert en["flat-role"]["examples"] == ["Flat example."]


def test_rendered_json_carries_language_matching_examples(tmp_path):
    root = _fixture_root(tmp_path)
    definition = build_routing_tool_definition(
        root,
        {},
        {"COMMUNICATION_LANGUAGE": "Deutsch"},
        template_roles=_TEMPLATE_ROLES,
    )
    rendered = render_routing_tool_definition(definition, "json")
    assert '"Deutsches Beispiel."' in rendered
    assert '"English example."' not in rendered
    assert '"Flat example."' in rendered


def test_keyword_sets_are_identical_across_language_renders(tmp_path):
    root = _fixture_root(tmp_path)
    de = _rules_by_agent(root, "Deutsch")
    en = _rules_by_agent(root, "English")
    assert set(de) == set(en)
    for agent in de:
        assert de[agent]["keywords"] == en[agent]["keywords"], agent
    assert de["mapped-role"]["examples"] != en["mapped-role"]["examples"]


def test_role_without_project_language_falls_back_and_logs_info(tmp_path):
    sink: list = []
    root = _fixture_root(tmp_path)
    de = _rules_by_agent(root, "Deutsch", info_sink=sink)
    assert de["fallback-role"]["examples"] == ["Only English."]
    assert len(sink) == 1
    assert "routing.examples-language-fallback" in sink[0]
    assert "fallback-role" in sink[0] and "'Deutsch'" in sink[0]


def test_language_aliases_and_case_select_the_matching_variant(tmp_path):
    examples = {"Deutsch": ["d"], "English": ["e"]}
    assert _select_examples(examples, "de") == ["d"]
    assert _select_examples(examples, "en") == ["e"]
    assert _select_examples(examples, "DEUTSCH") == ["d"]
    assert _select_examples(examples, "English") == ["e"]

    sink: list = []
    root = _fixture_root(tmp_path)
    en = _rules_by_agent(root, "en", info_sink=sink)
    assert en["mapped-role"]["examples"] == ["English example."]
    assert sink == []


def test_unknown_language_falls_back_to_first_variant_with_info(tmp_path):
    examples = {"Deutsch": ["d1", "d2"], "English": ["e"]}
    sink: list = []
    assert _select_examples(examples, "Klingon", role="r1", info_sink=sink) == ["d1", "d2"]
    assert len(sink) == 1 and "r1" in sink[0] and "Klingon" in sink[0]

    sink.clear()
    assert _select_examples(["neutral"], "Klingon", role="r1", info_sink=sink) == ["neutral"]
    assert sink == []
