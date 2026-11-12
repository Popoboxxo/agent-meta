"""Pin policy of the non-admin-server env helpers (#1189, IC-5a/IC-5b).

K-5: ``tests/test_admin_server.py`` only loads ``admin-server.py``; the other
copies of ``_tmp_sink_env`` (``consistency-check.py``, ``cli_commands.py``,
``run_role_routing_eval.py``) are covered here with the same ``importlib``
loading pattern. ``None``/inherit is only valid for the three D7 states;
anything else raises ``TmpSinkError("tmp-sink.pin-unavailable", ...)``.

Run: python -m pytest tests/test_tmp_sink_pin_policy.py -q
"""

from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.repo_containment import TmpSinkError  # noqa: E402


def _load_script(name: str, filename: str):
    spec = importlib.util.spec_from_file_location(name, REPO_ROOT / "scripts" / filename)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def _project(tmp_path: Path, body: str = "repo_containment:\n  tmp-sink:\n    path: .tmp\n") -> Path:
    root = tmp_path / "proj"
    (root / ".meta-config").mkdir(parents=True)
    (root / ".meta-config" / "project.yaml").write_text(
        "project: {name: t, prefix: t, short: t}\n" + body, encoding="utf-8"
    )
    return root


_BROKEN = 'repo_containment: "x"\n'
_DISABLED = "repo_containment:\n  tmp-sink:\n    enabled: false\n"


def _sink(root: Path) -> str:
    return str(Path(os.path.realpath(root / ".tmp")))


# --- Copy 2: scripts/consistency-check.py --------------------------------

cc = _load_script("consistency_check_policy", "consistency-check.py")


def test_consistency_check_pin_returns_sink_env(tmp_path):
    root = _project(tmp_path)
    env = cc._tmp_sink_env(root)
    assert env["TMPDIR"] == env["TEMP"] == env["TMP"] == _sink(root)


def test_consistency_check_pin_broken_config_raises(tmp_path):
    with pytest.raises(TmpSinkError) as exc:
        cc._tmp_sink_env(_project(tmp_path, _BROKEN))
    assert exc.value.code == "tmp-sink.pin-unavailable"


def test_consistency_check_pin_missing_config_returns_none(tmp_path):
    assert cc._tmp_sink_env(tmp_path) is None


def _raise_pin_error(*_a, **_k):
    raise TmpSinkError("tmp-sink.pin-unavailable", "boom; repair: python scripts/sync.py --validate")


def test_consistency_check_main_pin_error_returns_2(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cc, "run_checks", _raise_pin_error)
    monkeypatch.setattr(sys, "argv", ["consistency-check.py", "--root", str(tmp_path)])
    assert cc.main() == 2
    assert "error: tmp-sink.pin-unavailable:" in capsys.readouterr().err


def test_consistency_check_main_pin_error_json_object(tmp_path, monkeypatch, capsys):
    monkeypatch.setattr(cc, "run_checks", _raise_pin_error)
    monkeypatch.setattr(sys, "argv", ["consistency-check.py", "--json", "--root", str(tmp_path)])
    assert cc.main() == 2
    payload = json.loads(capsys.readouterr().out)
    assert payload["error"] == "tmp-sink.pin-unavailable"
    assert "boom" in payload["detail"]


def test_consistency_check_docstring_drops_never_raises_promise():
    assert "this helper never raises" not in cc._tmp_sink_env.__doc__


# --- Copy 3: scripts/lib/cli_commands.py ---------------------------------

from lib import cli_commands  # noqa: E402


def test_cli_admin_tmp_env_returns_sink_env(tmp_path):
    root = _project(tmp_path)
    env = cli_commands._admin_tmp_env(root)
    assert env["TMPDIR"] == env["TEMP"] == env["TMP"] == _sink(root)


def test_cli_admin_tmp_env_broken_config_raises(tmp_path):
    with pytest.raises(TmpSinkError) as exc:
        cli_commands._admin_tmp_env(_project(tmp_path, _BROKEN))
    assert exc.value.code == "tmp-sink.pin-unavailable"


def test_cli_admin_tmp_env_or_exit_exits_2_on_pin_error(tmp_path, capsys):
    with pytest.raises(SystemExit) as exc:
        cli_commands._admin_tmp_env_or_exit(_project(tmp_path, _BROKEN))
    assert exc.value.code == 2
    assert "error: tmp-sink.pin-unavailable:" in capsys.readouterr().err


def test_cli_admin_tmp_env_or_exit_passes_none_through(tmp_path):
    assert cli_commands._admin_tmp_env_or_exit(_project(tmp_path, _DISABLED)) is None


def test_cli_commands_docstring_drops_never_fails_promise():
    assert "a CLI start never fails because of it" not in cli_commands._admin_tmp_env.__doc__


# --- Copy 4: scripts/run_role_routing_eval.py ----------------------------

sys.path.insert(0, str(REPO_ROOT))
from scripts import run_role_routing_eval as ev  # noqa: E402
from scripts.lib.repo_containment import TmpSinkError as EvalTmpSinkError  # noqa: E402

_CLASS = {"name": "m", "provider": "p", "model_id": "x"}


def _eval_root(monkeypatch, tmp_path: Path, body: str | None = None) -> Path:
    root = _project(tmp_path) if body is None else _project(tmp_path, body)
    monkeypatch.setattr(ev, "_REPO_ROOT", root)
    return root


def test_eval_pin_returns_sink_env(tmp_path, monkeypatch):
    root = _eval_root(monkeypatch, tmp_path)
    env = ev._tmp_sink_env({"PATH": "/bin"})
    assert env["TMPDIR"] == env["TEMP"] == env["TMP"] == _sink(root)


def test_eval_pin_broken_config_raises_pin_unavailable(tmp_path, monkeypatch):
    _eval_root(monkeypatch, tmp_path, _BROKEN)
    with pytest.raises(EvalTmpSinkError) as exc:
        ev._tmp_sink_env({"PATH": "/bin"})
    assert exc.value.code == "tmp-sink.pin-unavailable"


def test_eval_pin_missing_config_returns_base_env_equal(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "_REPO_ROOT", tmp_path)
    base = {"PATH": "/bin", "X": "1"}
    result = ev._tmp_sink_env(base)
    assert result == base and result is not base
    assert set(result) == set(base)


def test_eval_pin_disabled_sink_returns_base_env_equal(tmp_path, monkeypatch):
    _eval_root(monkeypatch, tmp_path, _DISABLED)
    base = {"PATH": "/bin", "X": "1"}
    result = ev._tmp_sink_env(base)
    assert result == base and result is not base
    assert set(result) == set(base)


def test_eval_pin_never_returns_none(tmp_path, monkeypatch):
    monkeypatch.setattr(ev, "_REPO_ROOT", tmp_path)
    assert isinstance(ev._tmp_sink_env(None), dict)


def test_eval_run_class_aborts_before_call_provider(tmp_path, monkeypatch):
    _eval_root(monkeypatch, tmp_path, _BROKEN)
    calls = []
    monkeypatch.setattr(ev, "call_provider", lambda *a, **k: calls.append(1) or "")
    with pytest.raises(EvalTmpSinkError):
        ev.run_class(
            model_class=_CLASS, cases=[{"id": "c", "task": "t"}], repeat=1,
            contract=tmp_path / "c.md", timeout=1.0,
        )
    assert calls == []


def test_eval_main_returns_2_on_pin_error(tmp_path, monkeypatch, capsys):
    _eval_root(monkeypatch, tmp_path, _BROKEN)
    contract = tmp_path / "contract.md"
    contract.write_text("c", encoding="utf-8")
    out_dir = tmp_path / "out"
    monkeypatch.setattr(ev, "load_catalog", lambda _d: ([{"id": "c", "task": "t"}], "h"))
    monkeypatch.setattr(ev, "parse_model_classes", lambda *a, **k: [dict(_CLASS)])
    monkeypatch.setattr(ev, "build_context_report", lambda *a, **k: {})
    monkeypatch.setattr(ev, "estimate_for", lambda **k: {"calls": 1, "models": []})
    monkeypatch.setattr(ev.eval_gate, "format_estimate", lambda e: "estimate")
    monkeypatch.setattr(
        ev.eval_gate, "run_with_approval",
        lambda estimate, approval, runners, *a, **k: [r() for r in runners],
    )
    rc_ = ev.main(["--non-interactive", "--approval", "yes", "--contract", str(contract),
                   "--out-dir", str(out_dir)])
    assert rc_ == 2
    assert "error: tmp-sink.pin-unavailable:" in capsys.readouterr().err
    assert not (out_dir / "baseline").exists()


def test_eval_case_loop_reraises_tmp_sink_error(tmp_path, monkeypatch):
    _eval_root(monkeypatch, tmp_path)

    def boom(*_a, **_k):
        raise EvalTmpSinkError("tmp-sink.pin-unavailable", "x")

    monkeypatch.setattr(ev, "call_provider", boom)
    with pytest.raises(EvalTmpSinkError):
        ev.run_class(
            model_class=_CLASS, cases=[{"id": "c", "task": "t"}], repeat=1,
            contract=tmp_path / "c.md", timeout=1.0,
        )


def test_eval_call_provider_uses_passed_env_and_pins_by_default(tmp_path, monkeypatch):
    root = _eval_root(monkeypatch, tmp_path)
    (tmp_path / "provider-p.sh").write_text("#!/bin/sh\n", encoding="utf-8")
    seen = []

    class _Proc:
        returncode, stdout, stderr = 0, "ok", ""

    monkeypatch.setattr(ev.subprocess, "run", lambda argv, **kw: seen.append(kw["env"]) or _Proc())
    monkeypatch.setattr(ev, "_shell", lambda: "sh")
    args = ("p", "m", "prompt", tmp_path / "c.md", 1.0, tmp_path)
    ev.call_provider(*args, env={"PATH": "/bin", "MARK": "1"})
    assert seen[-1]["MARK"] == "1" and "TMPDIR" not in seen[-1]
    ev.call_provider(*args)
    assert seen[-1]["TMPDIR"] == _sink(root)
