"""CLI gate for ``commit.trailers``: ``sync.py --check-commit-msg FILE`` (#1247).

Covers the exit contract (0 ok/no-op/warn, 1 violation, 2 read error), stdin
(``-``), the read-only/no-tail property and the actual parser+dispatch wiring.
"""
from __future__ import annotations

import argparse
import io
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from lib.cli_commands import _handle_check_commit_msg  # noqa: E402
from lib.log import SyncLog  # noqa: E402

AGENT = "Agent-Meta-Agent: developer"
BOT = "Co-Authored-By: Some Bot <bot@example.com>"
_SYNC = ROOT / "scripts" / "sync.py"


class _Ctx:
    """Minimal stand-in for ``_SyncContext`` (handler reads args/log/config)."""

    def __init__(self, source: str, config: dict) -> None:
        self.args = argparse.Namespace(check_commit_msg=source)
        self.log = SyncLog()
        self.config = config
        self.mode = None
        self.read_only = False


def _invoke(ctx: _Ctx, monkeypatch, stdin_text: str = "") -> int:
    monkeypatch.setattr(sys, "stdin", io.StringIO(stdin_text))
    with pytest.raises(SystemExit) as exc:
        _handle_check_commit_msg(ctx)
    return exc.value.code


def _cfg(trailers):
    return {"commit": {"trailers": trailers}}


def _valid_message() -> str:
    return "fix: thing\n\nSome body\n\n" + AGENT + "\n" + BOT + "\n"


# --- parser / dispatch wiring -------------------------------------------------

def test_parser_registers_flag():
    from sync import _build_arg_parser

    args = _build_arg_parser().parse_args(["--check-commit-msg", "MSG"])
    assert args.check_commit_msg == "MSG"
    assert _build_arg_parser().parse_args([]).check_commit_msg is None


# --- handler exit contract (unit) --------------------------------------------

def test_no_trailers_is_silent_noop_exit0(tmp_path, monkeypatch, capsys):
    """AC1: empty/missing contract -> exit 0, no gate output."""
    msg = tmp_path / "MSG"
    msg.write_text("anything\n", encoding="utf-8")
    for cfg in ({}, {"commit": None}, _cfg([])):
        code = _invoke(_Ctx(str(msg), cfg), monkeypatch)
        assert code == 0
    assert "commit-msg" not in capsys.readouterr().err


def test_all_trailers_verbatim_exit0(tmp_path, monkeypatch, capsys):
    """AC2: every expected trailer exactly once -> exit 0, no output."""
    msg = tmp_path / "MSG"
    msg.write_text(_valid_message(), encoding="utf-8")
    code = _invoke(_Ctx(str(msg), _cfg([AGENT, BOT])), monkeypatch)
    assert code == 0
    assert "commit-msg" not in capsys.readouterr().err


def test_missing_trailer_exit1_with_error(tmp_path, monkeypatch, capsys):
    """AC3: missing token -> [ERROR], exit 1."""
    msg = tmp_path / "MSG"
    msg.write_text("fix: thing\n\nSome body\n\n" + BOT + "\n", encoding="utf-8")
    code = _invoke(_Ctx(str(msg), _cfg([AGENT])), monkeypatch)
    err = capsys.readouterr().err
    assert code == 1
    assert "commit-msg [ERROR]" in err
    assert "commit trailer missing: " + AGENT in err


def test_duplicate_trailer_exit1_with_error(tmp_path, monkeypatch, capsys):
    msg = tmp_path / "MSG"
    msg.write_text("fix: thing\n\n" + AGENT + "\n" + AGENT + "\n", encoding="utf-8")
    code = _invoke(_Ctx(str(msg), _cfg([AGENT])), monkeypatch)
    err = capsys.readouterr().err
    assert code == 1
    assert "commit-msg [ERROR]" in err
    assert "commit trailer duplicated: " + AGENT in err


def test_bom_exit1_with_error(tmp_path, monkeypatch, capsys):
    msg = tmp_path / "MSG"
    msg.write_text("\ufeff" + _valid_message(), encoding="utf-8")
    code = _invoke(_Ctx(str(msg), _cfg([AGENT, BOT])), monkeypatch)
    err = capsys.readouterr().err
    assert code == 1
    assert "commit-msg [ERROR]" in err
    assert "UTF-8 BOM" in err


def test_different_value_exit0_with_warn(tmp_path, monkeypatch, capsys):
    """AC5: same token, different value -> [WARN] hint, exit 0, no [ERROR]."""
    msg = tmp_path / "MSG"
    msg.write_text("fix: thing\n\nAgent-Meta-Agent: wrong-model", encoding="utf-8")
    code = _invoke(_Ctx(str(msg), _cfg([AGENT])), monkeypatch)
    err = capsys.readouterr().err
    assert code == 0
    assert "commit-msg [WARN]" in err
    assert "different value" in err
    assert "brief override" in err
    assert "commit-msg [ERROR]" not in err


def test_invalid_commit_block_exit0_with_validate_hint(tmp_path, monkeypatch, capsys):
    msg = tmp_path / "MSG"
    msg.write_text(_valid_message(), encoding="utf-8")
    code = _invoke(_Ctx(str(msg), {"commit": {"trailers": "bad"}}), monkeypatch)
    err = capsys.readouterr().err
    assert code == 0
    assert "use sync.py --validate" in err


def test_unreadable_file_exit2(tmp_path, monkeypatch, capsys):
    """AC8: missing file -> fail-closed exit 2 via log.error."""
    missing = tmp_path / "does-not-exist"
    ctx = _Ctx(str(missing), _cfg([AGENT]))
    code = _invoke(ctx, monkeypatch)
    err = capsys.readouterr().err
    assert code == 2
    assert "check-commit-msg" in err
    assert str(missing) in err
    assert ctx.log.errors


def test_non_utf8_file_exit2(tmp_path, monkeypatch, capsys):
    msg = tmp_path / "MSG"
    msg.write_bytes(b"fix: thing\n\n\xff\xfe invalid utf-8")
    code = _invoke(_Ctx(str(msg), _cfg([AGENT])), monkeypatch)
    assert code == 2
    assert "check-commit-msg" in capsys.readouterr().err


def test_stdin_source(tmp_path, monkeypatch, capsys):
    """AC9: '-' reads stdin just like a file."""
    code = _invoke(_Ctx("-", _cfg([AGENT])), monkeypatch, _valid_message())
    assert code == 0
    assert "commit-msg" not in capsys.readouterr().err

    code = _invoke(_Ctx("-", _cfg([AGENT])), monkeypatch,
                   "fix: thing\n\nSome body\n\n" + BOT + "\n")
    assert code == 1
    assert "commit trailer missing" in capsys.readouterr().err


# --- end-to-end CLI wiring ----------------------------------------------------

_MINIMAL_CONFIG = (
    "ai-providers: [Claude]\n"
    "dod-preset: rapid-prototyping\n"
    "roles: [developer]\n"
    "project: {name: trailer-gate-test, prefix: tg, short: tgt}\n"
    "variables: {PROJECT_NAME: trailer-gate-test}\n"
)
_TRAILER_BLOCK = 'commit:\n  trailers:\n    - "Agent-Meta-Agent: developer"\n'


def _project(tmp_path: Path) -> Path:
    root = tmp_path / "project"
    meta = root / ".meta-config"
    meta.mkdir(parents=True)
    (meta / "project.yaml").write_text(_MINIMAL_CONFIG + _TRAILER_BLOCK, encoding="utf-8")
    return root


def _sync(root: Path, *flags: str, input: str = None) -> subprocess.CompletedProcess:
    cfg = root / ".meta-config" / "project.yaml"
    return subprocess.run(
        [sys.executable, str(_SYNC), "--config", str(cfg), *flags],
        capture_output=True, text=True, cwd=str(root),
        input=input, encoding="utf-8", errors="replace",
    )


def test_cli_end_to_end_ok_violation_and_no_writes(tmp_path):
    root = _project(tmp_path)
    msg = root / "MSG"
    msg.write_text(_valid_message(), encoding="utf-8")
    before = {p.relative_to(root).as_posix() for p in root.rglob("*")}

    ok = _sync(root, "--check-commit-msg", str(msg))
    assert "Traceback" not in ok.stdout + ok.stderr, ok.stderr
    assert ok.returncode == 0, ok.stderr
    assert "commit-msg" not in ok.stderr
    # Read-only gate: no sync.log / no generated files, no sync tail.
    assert {p.relative_to(root).as_posix() for p in root.rglob("*")} == before

    msg.write_text("fix: thing\n\nSome body\n\n" + BOT + "\n", encoding="utf-8")
    bad = _sync(root, "--check-commit-msg", str(msg))
    assert bad.returncode == 1, bad.stderr
    assert "commit-msg [ERROR]" in bad.stderr
    assert "commit trailer missing" in bad.stderr


def test_cli_end_to_end_stdin(tmp_path):
    root = _project(tmp_path)
    res = _sync(root, "--check-commit-msg", "-", input=_valid_message())
    assert res.returncode == 0, res.stderr
