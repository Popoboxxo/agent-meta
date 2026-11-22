"""E-23 / PR 4.1: lazy routing detail file (E6, AC-R4).

The compact always-on block carries intent flags only; the full fields
(intents, all examples, priority, size_class, contracts) live in a single
on-demand ``routing-details.md`` referenced by exactly one pointer line.
"""
from __future__ import annotations

from scripts.lib.intent_routing import render_routing_detail, routing_detail_pointer


def test_detail_doc_contains_all_deferred_fields():
    rules = [{
        "agent": "developer",
        "intents": ["implement", "fix"],
        "size_class": "M",
        "priority": 2,
        "keywords": ["Bugfix", "Refactoring"],
        "examples": ["Implementiere Feature X.", "Fixe Bug in cache.py."],
        "output_contract": "dev-result-v1",
        "input_contracts": ["task-spec-v1"],
    }]
    doc = render_routing_detail(rules)
    assert "## developer" in doc
    assert "implement, fix" in doc
    assert "| M |" in doc
    assert "p2" in doc
    assert "Implementiere Feature X." in doc
    assert "Fixe Bug in cache.py." in doc
    assert "dev-result-v1" in doc
    assert "task-spec-v1" in doc


def test_detail_pointer_is_single_provider_agnostic_line():
    # The path is derived from the provider's agents_dir (data), never a
    # hardcoded provider name in the template.
    line = routing_detail_pointer("generic/agents")
    assert line.count("\n") == 0
    assert "generic/routing-details.md" in line
    assert "Read" in line
    assert ".claude" not in line
