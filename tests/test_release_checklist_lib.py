"""Tests for the release-checklist normalizer and validator (Task 1)."""

import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib import release_checklist as rc


def _item(**kw):
    return {"id": "a-1", "task": "t", "verification": "v", **kw}


def _errs(block):
    return rc.collect_release_checklist_errors({"release-checklist": block})


def test_normalize_false_only():
    cfg = {"release-checklist": {"mode": False}}
    rc.normalize_release_checklist_mode(cfg)
    assert cfg["release-checklist"]["mode"] == "off"
    cfg = {"release-checklist": {"mode": True}}
    rc.normalize_release_checklist_mode(cfg)
    assert cfg["release-checklist"]["mode"] is True
    assert any("quote the value" in e for e in _errs({"mode": True}))      # AC-REL-3


def test_invalid_mode_names_path():                                         # AC-REL-2
    assert any("release-checklist.mode" in e for e in _errs({"mode": "loose"}))


def test_duplicate_and_reserved_ids():                                      # AC-REL-4
    assert _errs({"items": [_item(), _item()]})
    assert _errs({"items": [_item(id="tests-green")]})


def test_script_check_rules():                                              # AC-REL-5
    assert _errs({"items": [_item(check="script")]})
    assert _errs({"items": [_item(check="agent", script="x")]})
    assert _errs({"items": [_item(check="script", script="a\nb")]})
    assert not _errs({"items": [_item(check="script", script="python3 -V")]})


def test_unknown_keys_and_phase():                                          # AC-REL-5, AC-REL-21
    assert _errs({"bogus": 1})
    assert _errs({"items": [_item(bogus=1)]})
    assert _errs({"items": [_item(phase="later")]})
    assert not _errs({"items": [_item(phase="step", required=False, **{"applies-when": "x"})]})


def test_null_and_empty_block_are_absent():                                 # R1
    for cfg in ({}, {"release-checklist": None}, {"release-checklist": {}},
                {"release-checklist": {"items": []}}):
        assert rc.collect_release_checklist_errors(cfg) == []


def test_non_list_items_and_non_mapping_item():                             # R2
    assert any("release-checklist.items" in e for e in _errs({"items": "x"}))
    assert any("release-checklist.items[0]" in e for e in _errs({"items": ["x"]}))


def test_script_whitespace_only_and_cr():                                   # R3
    assert _errs({"items": [_item(check="script", script="   ")]})
    assert _errs({"items": [_item(check="script", script="a\rb")]})


def test_item_field_types_are_hard_errors():                                # R4
    for bad in (_item(id="Foo"), _item(id="a_b"), _item(id=123), _item(required="yes"),
                _item(task=""), _item(verification=None)):
        assert _errs({"items": [bad]}), bad
    assert _errs({"items": [{"id": "x", "verification": "v"}]})            # task missing


def test_validate_exits_with_path(capsys, tmp_path):
    with pytest.raises(SystemExit):
        rc.validate_release_checklist({"release-checklist": {"mode": "loose"}}, tmp_path / "project.yaml")
    assert "release-checklist.mode" in capsys.readouterr().err


def test_load_config_normalizes_unquoted_off(tmp_path):                     # AC-REL-3 end-to-end
    from lib.config import load_config
    p = tmp_path / "project.yaml"
    p.write_text("project: {name: x, prefix: x}\nrelease-checklist:\n  mode: off\n", encoding="utf-8")
    assert load_config(p)["release-checklist"]["mode"] == "off"
