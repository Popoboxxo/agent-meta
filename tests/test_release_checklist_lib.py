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


def test_free_text_fields_reject_placeholder_markers():                     # review fix-up
    """The rendered block must never contain ``{{``/``}}`` (placeholder check)."""
    for field in ("task", "verification", "script", "applies-when"):
        item = _item(**{field: "x {{RELEASE_CHECKLIST_BLOCK}} y"})
        if field == "script":
            item["check"] = "script"
        errors = _errs({"items": [item]})
        assert any(
            f"release-checklist.items[0].{field}" in e and "placeholder" in e
            for e in errors
        ), (field, errors)
    # The closing marker alone is rejected as well.
    assert any(
        "placeholder" in e
        for e in _errs({"items": [_item(verification="a }} b")]})
    )
    # Single braces are legitimate free text and stay valid.
    assert not _errs({"items": [_item(task="use {x} here", verification="echo }")]})


def test_validate_exits_with_path(capsys, tmp_path):
    with pytest.raises(SystemExit):
        rc.validate_release_checklist({"release-checklist": {"mode": "loose"}}, tmp_path / "project.yaml")
    assert "release-checklist.mode" in capsys.readouterr().err


def test_load_config_normalizes_unquoted_off(tmp_path):                     # AC-REL-3 end-to-end
    from lib.config import load_config
    p = tmp_path / "project.yaml"
    p.write_text("project: {name: x, prefix: x}\nrelease-checklist:\n  mode: off\n", encoding="utf-8")
    assert load_config(p)["release-checklist"]["mode"] == "off"


# --- Task 2: resolver, renderer, variables ---------------------------------

REQUIRED_PHRASES = (                       # AC-REL-6..9, 11, 21-25 (Template-Text-Asserts)
    "CHECKLIST_MODE", "CHECKLIST_SUMMARY", "not_run", "required_failed", "APPROVAL_REQUEST", "APPROVED:",
    "MODE: check-only", "n/a (nicht ausgeführt)", "Exit 0 = pass", "side-effect free",
    "Step 0", "STATUS: failed", "dod-met", "readme-current", "tests-green", "changelog-updated",
    "version-bumped", "build-created", "git-tag-push", "| phase |",
)


def _res(mode, items=()):
    return rc.resolve_release_checklist({"release-checklist": {"mode": mode, "items": list(items)}})


def test_resolve_defaults():
    r = _res("advisory", [_item()])
    assert r["mode"] == "advisory"
    assert r["items"][0]["check"] == "agent" and r["items"][0]["phase"] == "precondition" and r["items"][0]["required"] is True


def test_resolve_absent_null_empty_is_off():                                # R1
    for cfg in ({}, {"release-checklist": None}, {"release-checklist": {}}):
        assert rc.resolve_release_checklist(cfg) == {"mode": "off", "items": []}
    assert rc.resolve_release_checklist({"release-checklist": {"mode": False}})["mode"] == "off"


def test_resolve_broken_structure_never_raises():                           # R2
    for cfg in ({"release-checklist": "x"}, {"release-checklist": {"items": "x"}},
                {"release-checklist": {"mode": "strict", "items": ["x"]}}, {"release-checklist": {"mode": True}}):
        assert rc.resolve_release_checklist(cfg) == {"mode": "off", "items": []}


def test_render_empty_when_off():
    assert rc.render_release_checklist_block(_res("off", [_item()])) == ""


def test_render_modes_contain_contract():
    for mode in ("advisory", "strict"):
        text = rc.render_release_checklist_block(_res(mode, [_item(id="docker-pushed", phase="step", required=False)]))
        for phrase in REQUIRED_PHRASES: assert phrase in text, (mode, phrase)
        assert "docker-pushed" in text
        assert "non-blocking" not in text and "not blocking" not in text   # AC-REL-22
    assert "Prompt-/Konventions-Boundary" in rc.render_release_checklist_block(_res("strict"))   # AC-REL-7


def test_render_script_item_row():
    text = rc.render_release_checklist_block(_res("strict", [_item(id="sv", check="script", script="python3 scripts/sync.py --validate")]))
    assert "`python3 scripts/sync.py --validate`" in text                   # AC-REL-9


def test_reserved_items_flags_and_template_rowcount():                      # AC-REL-21, b10
    flags = {i: f for i, _, f in rc.RESERVED_DEFAULT_ITEMS}
    assert {i for i, f in flags.items() if f} == {"dod-met", "readme-current"}
    assert {p for _, p, _ in rc.RESERVED_DEFAULT_ITEMS} == {"precondition", "step"}
    tpl = (REPO_ROOT / "agents" / "1-generic" / "release.md").read_text(encoding="utf-8")
    head = tpl.split("## 1. Pre-release checklist", 1)[1].split("{{RELEASE_CUSTOM_CHECKLIST_BLOCK}}", 1)[0]
    rows = [l for l in head.splitlines() if l.startswith("| ") and not l.startswith(("| Check", "|--"))]
    assert len(rows) == len(rc.RESERVED_DEFAULT_ITEMS)


def test_strict_block_na_rules():                                           # AC-REL-8, AC-REL-25
    text = rc.render_release_checklist_block(_res("strict"))
    assert "`reason`" in text and "applies-when" in text
    assert "single line" in text      # einzeilige Begründung


def test_build_variables():
    off = rc.build_release_checklist_variables({})
    assert off == {"RELEASE_CHECKLIST_MODE": "off", "RELEASE_CHECKLIST_ENABLED": "false", "RELEASE_CHECKLIST_BLOCK": ""}
    on = rc.build_release_checklist_variables({"release-checklist": {"mode": "strict"}})
    assert on["RELEASE_CHECKLIST_ENABLED"] == "true" and on["RELEASE_CHECKLIST_BLOCK"]


def test_module_size_limit():                                               # AC-REL-19
    assert len((REPO_ROOT / "scripts" / "lib" / "release_checklist.py").read_text(encoding="utf-8").splitlines()) <= 600
