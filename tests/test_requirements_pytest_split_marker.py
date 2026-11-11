from pathlib import Path

import pytest

_REQ = Path(__file__).resolve().parent / "requirements.txt"
_env = {"39": {"python_version": "3.9"}, "312": {"python_version": "3.12"}}


def _split_requirements():
    req_mod = pytest.importorskip("packaging.requirements")
    reqs = []
    for raw in _REQ.read_text(encoding="utf-8").splitlines():
        line = raw.split("#", 1)[0].strip()
        if line.startswith("pytest-split"):
            reqs.append(req_mod.Requirement(line))
    return reqs


def _selected(env):
    return [r for r in _split_requirements() if r.marker is None or r.marker.evaluate(env)]


def test_pytest_split_has_two_marker_lines():
    assert len(_split_requirements()) == 2


def test_python39_selects_exactly_the_old_floor():
    ver = pytest.importorskip("packaging.version")
    sel = _selected(_env["39"])
    assert len(sel) == 1
    assert ver.Version("0.8.0") in sel[0].specifier


def test_python312_requires_0_11():
    ver = pytest.importorskip("packaging.version")
    sel = _selected(_env["312"])
    assert len(sel) == 1
    assert ver.Version("0.10.0") not in sel[0].specifier
    assert ver.Version("0.11.0") in sel[0].specifier
