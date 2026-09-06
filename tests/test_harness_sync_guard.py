"""CLI integration tests for the harness write-isolation guard (issue #547).

Exercises sync.py's real parser + ``_build_context`` with harness activation
via CLI flag and AGENT_META_HARNESS env var, verifying:

- default behavior (no harness anywhere) is 100% unchanged (``ctx.harness`` None),
- a harness whose checkout-root contains the project root activates cleanly,
- a harness whose checkout-root does NOT contain the project root refuses to
  run (fail-closed SystemExit 1) with a remedy in the message,
- the ``--harness`` flag overrides the env var,
- an unknown harness name refuses with the available names listed.
"""
import sys
from pathlib import Path

import pytest

_SCRIPTS_DIR = Path(__file__).resolve().parents[1] / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.cli_commands import _build_context  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from sync import _build_arg_parser  # noqa: E402

REPO_ROOT = _SCRIPTS_DIR.parent


@pytest.fixture(autouse=True)
def _clean_harness_env(monkeypatch):
    """Remove harness env vars so tests are deterministic on any machine."""
    monkeypatch.delenv("AGENT_META_HARNESS", raising=False)
    monkeypatch.delenv("AGENT_META_HARNESS_ROOT", raising=False)


def _tmp_project(tmp_path: Path) -> Path:
    """Create a minimal tmp project (config under .meta-config/)."""
    meta = tmp_path / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "project.yaml").write_text(
        "project:\n  name: harness-guard-test\n", encoding="utf-8"
    )
    return tmp_path


def _parse_args(config_path: Path, extra: list[str] | None = None):
    args = _build_arg_parser().parse_args(
        ["--config", str(config_path)] + (extra or [])
    )
    args.dry_run = True  # never let the context build write anything
    return args


def test_parser_accepts_harness_flag():
    args = _build_arg_parser().parse_args(["--harness", "opencode"])
    assert args.harness == "opencode"
    assert _build_arg_parser().parse_args([]).harness is None


def test_no_harness_active_is_backwards_compatible(tmp_path):
    project = _tmp_project(tmp_path)
    args = _parse_args(project / ".meta-config" / "project.yaml")
    ctx = _build_context(args, REPO_ROOT, SyncLog())
    assert ctx is not None
    assert ctx.harness is None


def test_harness_activates_when_project_inside_checkout(tmp_path, monkeypatch):
    project = _tmp_project(tmp_path / "repos-oc" / "myproject")
    monkeypatch.setenv("AGENT_META_HARNESS", "claude")
    monkeypatch.setenv("AGENT_META_HARNESS_ROOT", str(tmp_path / "repos-oc"))
    args = _parse_args(project / ".meta-config" / "project.yaml")
    ctx = _build_context(args, REPO_ROOT, SyncLog())
    assert ctx is not None
    assert ctx.harness is not None
    assert ctx.harness.name == "claude"
    assert ctx.harness.checkout_root == (tmp_path / "repos-oc").resolve()


def test_harness_cli_flag_overrides_env(tmp_path, monkeypatch):
    project = _tmp_project(tmp_path / "repos" / "myproject")
    monkeypatch.setenv("AGENT_META_HARNESS", "opencode")  # wrong checkout root
    args = _parse_args(
        project / ".meta-config" / "project.yaml", ["--harness", "claude"]
    )
    monkeypatch.setenv("AGENT_META_HARNESS_ROOT", str(tmp_path / "repos"))
    ctx = _build_context(args, REPO_ROOT, SyncLog())
    assert ctx is not None
    assert ctx.harness is not None
    assert ctx.harness.name == "claude"


def test_harness_refuses_outside_checkout(tmp_path, monkeypatch):
    project = _tmp_project(tmp_path)
    monkeypatch.setenv("AGENT_META_HARNESS", "claude")
    # Point the harness checkout somewhere guaranteed not to contain project.
    monkeypatch.setenv("AGENT_META_HARNESS_ROOT", str(tmp_path / "other-checkout"))
    args = _parse_args(project / ".meta-config" / "project.yaml")
    with pytest.raises(SystemExit) as exc_info:
        _build_context(args, REPO_ROOT, SyncLog())
    assert exc_info.value.code == 1


def test_harness_refuses_unknown_name(tmp_path, monkeypatch):
    project = _tmp_project(tmp_path)
    monkeypatch.setenv("AGENT_META_HARNESS", "does-not-exist")
    args = _parse_args(project / ".meta-config" / "project.yaml")
    with pytest.raises(SystemExit) as exc_info:
        _build_context(args, REPO_ROOT, SyncLog())
    assert exc_info.value.code == 1


def test_harness_refusal_message_names_harness_and_remedy(
    tmp_path, monkeypatch, capsys
):
    project = _tmp_project(tmp_path)
    monkeypatch.setenv("AGENT_META_HARNESS", "claude")
    monkeypatch.setenv("AGENT_META_HARNESS_ROOT", str(tmp_path / "other-checkout"))
    args = _parse_args(project / ".meta-config" / "project.yaml")
    with pytest.raises(SystemExit):
        _build_context(args, REPO_ROOT, SyncLog())
    stderr = capsys.readouterr().err
    assert "claude" in stderr
    assert "AGENT_META_HARNESS_ROOT" in stderr
    assert "remedy" in stderr


def test_dry_run_refusal_does_not_write(tmp_path, monkeypatch):
    """The refusal happens in _build_context — before any sync stage runs."""
    project = _tmp_project(tmp_path)
    monkeypatch.setenv("AGENT_META_HARNESS", "claude")
    monkeypatch.setenv("AGENT_META_HARNESS_ROOT", str(tmp_path / "other-checkout"))
    args = _parse_args(project / ".meta-config" / "project.yaml")
    with pytest.raises(SystemExit):
        _build_context(args, REPO_ROOT, SyncLog())
    # Nothing but the config file exists in the project dir.
    existing = {p.name for p in project.rglob("*")}
    assert existing == {".meta-config", "project.yaml"}


def test_self_hosting_repo_inside_sibling_harness_root(monkeypatch):
    """Sanity: with the harness checkout-root pointed at the directory that
    contains this repo (the ~/repos/<repo> convention), the guard passes and
    the harness activates — the agent-meta repo can sync its own checkout."""
    harness_root = REPO_ROOT.parent  # e.g. ~/repos
    monkeypatch.setenv("AGENT_META_HARNESS", "claude")
    monkeypatch.setenv("AGENT_META_HARNESS_ROOT", str(harness_root))
    args = _parse_args(REPO_ROOT / ".meta-config" / "project.yaml")
    ctx = _build_context(args, REPO_ROOT, SyncLog())
    assert ctx is not None
    assert ctx.harness is not None
    assert ctx.harness.name == "claude"
