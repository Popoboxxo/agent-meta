"""#1086h: optional ``routing.priority`` is only emitted, never resolved (Spec S9)."""
from __future__ import annotations

import copy
from pathlib import Path
from types import SimpleNamespace

from scripts.lib import delegation_table, roles
from scripts.lib.consistency import active_set_refs

_ROOT = Path(".")
_REAL = roles.load_roles_config(_ROOT)


def _roles_with(priorities: dict) -> dict:
    cfg = copy.deepcopy(_REAL)
    for name, prio in priorities.items():
        cfg["roles"][name].setdefault("routing", {})["priority"] = prio
        cfg["roles"][name].setdefault("routing_patterns", {}).setdefault("keywords", []).append("zz-shared")
    return cfg


def _rule(rules: dict, agent: str) -> dict:
    return next(r for r in rules["rules"] if r["agent"] == agent)


def test_rule_dict_carries_int_priority(monkeypatch):
    cfg = _roles_with({"developer": 10, "tester": 0})
    monkeypatch.setattr(delegation_table, "load_roles_config", lambda _root: cfg)
    rules = delegation_table.get_routing_rules(_ROOT, {}, {})
    assert _rule(rules, "developer")["priority"] == 10
    assert _rule(rules, "tester")["priority"] == 0


def test_rule_dict_without_priority_has_no_key(monkeypatch):
    rules = delegation_table.get_routing_rules(_ROOT, {}, {})
    assert all("priority" not in r for r in rules["rules"])


def test_non_int_priority_ignored(monkeypatch):
    cfg = _roles_with({"developer": "x", "tester": True})
    monkeypatch.setattr(delegation_table, "load_roles_config", lambda _root: cfg)
    rules = delegation_table.get_routing_rules(_ROOT, {}, {})
    assert "priority" not in _rule(rules, "developer")
    assert "priority" not in _rule(rules, "tester")


def _overlap(monkeypatch, cfg):
    monkeypatch.setattr(roles, "load_roles_config", lambda _root: cfg)
    aset = SimpleNamespace(routable=frozenset({"developer", "tester"}))
    return [f for f in active_set_refs.check_keyword_overlap(_ROOT, [], {}, aset)
            if "'zz-shared'" in f.message]


def test_overlap_message_names_priority_and_keeps_finding_count(monkeypatch):
    base = _overlap(monkeypatch, _roles_with({"developer": None, "tester": None}))
    with_prio = _overlap(monkeypatch, _roles_with({"developer": 10, "tester": 0}))
    assert len(base) == len(with_prio) == 1
    assert with_prio[0].severity == base[0].severity
    assert with_prio[0].message.endswith("; priority: developer=10, tester=0")
    assert "priority" not in base[0].message
