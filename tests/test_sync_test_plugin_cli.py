from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import sync  # noqa: E402


def test_arg_parser_accepts_test_plugin():
    parser = sync._build_arg_parser()
    args = parser.parse_args(["--test-plugin", "graphify"])
    assert args.test_plugin == "graphify"


def test_run_test_plugin_reports_status(monkeypatch, capsys):
    monkeypatch.setattr(sync, "run_plugin_test",
                        lambda pid, pdef, secrets=None: {"status": "PASS", "message": "ok", "latency_ms": 5})
    code = sync._run_test_plugin(REPO_ROOT, REPO_ROOT, "graphify")
    out = capsys.readouterr().out
    assert code == 0
    assert "PASS" in out and "graphify" in out


def test_run_test_plugin_unknown_id(capsys):
    code = sync._run_test_plugin(REPO_ROOT, REPO_ROOT, "does-not-exist")
    out = capsys.readouterr().out
    assert code == 1
    assert "not in catalog" in out.lower()
