"""Unit tests for the harness abstraction (scripts/lib/harnesses.py, issue #547).

Covers the config schema parsing (config/harnesses/<name>.yaml), activation
precedence (--harness flag > AGENT_META_HARNESS env), the write-isolation
guard semantics (strict refuse vs. warn) and the shipped harness configs.
"""
import os
from pathlib import Path

import pytest

from scripts.lib.harnesses import (
    DEFAULT_ROOT_ENV,
    HARNESS_ENV_VAR,
    ensure_write_isolation,
    is_within,
    list_harness_names,
    list_harnesses,
    load_harness,
    resolve_active_harness,
)
from scripts.lib.io import SyncError
from scripts.lib.log import SyncLog

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture(autouse=True)
def _clean_harness_env(monkeypatch):
    """Remove harness env vars so tests are deterministic on any machine."""
    monkeypatch.delenv(HARNESS_ENV_VAR, raising=False)
    monkeypatch.delenv(DEFAULT_ROOT_ENV, raising=False)


def _write_harness(tmp_path: Path, name: str, body: str) -> Path:
    hdir = tmp_path / "config" / "harnesses"
    hdir.mkdir(parents=True, exist_ok=True)
    path = hdir / f"{name}.yaml"
    path.write_text(body, encoding="utf-8")
    return tmp_path


VALID = """\
harness:
  name: opencode
  description: "Opencode harness"
  checkout-root: {root}
  branch: agent/opencode
  default-providers:
    - Opencode
"""


# ---------------------------------------------------------------------------
# Schema parsing
# ---------------------------------------------------------------------------

def test_parse_valid_harness(tmp_path):
    root = tmp_path / "repos-oc"
    _write_harness(tmp_path, "opencode", VALID.format(root=root))
    harness = load_harness(tmp_path, "opencode", env={})
    assert harness.name == "opencode"
    assert harness.checkout_root == root.resolve()
    assert harness.branch == "agent/opencode"
    assert harness.default_providers == ("Opencode",)
    assert harness.description == "Opencode harness"
    assert harness.root_env == DEFAULT_ROOT_ENV
    assert harness.source == (tmp_path / "config" / "harnesses" / "opencode.yaml")


def test_parse_defaults_are_minimal(tmp_path):
    _write_harness(tmp_path, "minimal", "harness:\n  name: minimal\n  checkout-root: /somewhere\n")
    harness = load_harness(tmp_path, "minimal", env={})
    assert harness.branch is None
    assert harness.default_providers == ()
    assert harness.description == ""
    assert harness.root_env == DEFAULT_ROOT_ENV


def test_checkout_root_tilde_expansion(tmp_path, monkeypatch):
    monkeypatch.setenv("HOME", str(tmp_path))
    _write_harness(tmp_path, "opencode", VALID.format(root="~/repos-oc"))
    harness = load_harness(tmp_path, "opencode", env={})
    assert harness.checkout_root == (tmp_path / "repos-oc").resolve()


def test_name_must_match_file_stem(tmp_path):
    _write_harness(tmp_path, "opencode", VALID.format(root="/x").replace("opencode", "other"))
    with pytest.raises(SyncError, match="must match the file stem"):
        load_harness(tmp_path, "opencode", env={})


def test_missing_checkout_root_rejected(tmp_path):
    _write_harness(tmp_path, "broken", "harness:\n  name: broken\n")
    with pytest.raises(SyncError, match="checkout-root"):
        load_harness(tmp_path, "broken", env={})


def test_relative_checkout_root_rejected(tmp_path):
    body = VALID.format(root="relative/dir").replace("name: opencode", "name: broken")
    _write_harness(tmp_path, "broken", body)
    with pytest.raises(SyncError, match="absolute path"):
        load_harness(tmp_path, "broken", env={})


def test_missing_harness_block_rejected(tmp_path):
    _write_harness(tmp_path, "broken", "not-harness: true\n")
    with pytest.raises(SyncError, match="harness:"):
        load_harness(tmp_path, "broken", env={})


def test_invalid_default_providers_rejected(tmp_path):
    body = (VALID.format(root="/x") + "  default-providers: 42\n").replace(
        "name: opencode", "name: broken"
    )
    _write_harness(tmp_path, "broken", body)
    with pytest.raises(SyncError, match="default-providers"):
        load_harness(tmp_path, "broken", env={})


# ---------------------------------------------------------------------------
# Root env override
# ---------------------------------------------------------------------------

def test_root_env_overrides_checkout_root(tmp_path, monkeypatch):
    body = VALID.format(root="/from/config").replace(
        "checkout-root: /from/config",
        "checkout-root: /from/config\n  root-env: MY_HARNESS_ROOT",
    )
    _write_harness(tmp_path, "opencode", body)
    monkeypatch.setenv("MY_HARNESS_ROOT", str(tmp_path / "from-env"))
    harness = load_harness(tmp_path, "opencode", env=os.environ)
    assert harness.checkout_root == (tmp_path / "from-env").resolve()
    assert harness.root_env == "MY_HARNESS_ROOT"


def test_root_env_relative_value_rejected(tmp_path, monkeypatch):
    body = VALID.format(root="/from/config").replace(
        "checkout-root: /from/config",
        "checkout-root: /from/config\n  root-env: MY_HARNESS_ROOT",
    )
    _write_harness(tmp_path, "opencode", body)
    monkeypatch.setenv("MY_HARNESS_ROOT", "relative/env/path")
    with pytest.raises(SyncError, match="MY_HARNESS_ROOT"):
        load_harness(tmp_path, "opencode", env=os.environ)


# ---------------------------------------------------------------------------
# Activation precedence
# ---------------------------------------------------------------------------

def test_no_activation_returns_none(tmp_path):
    assert resolve_active_harness(tmp_path, cli_value=None, env={}) is None
    assert resolve_active_harness(tmp_path, cli_value="", env={"AGENT_META_HARNESS": ""}) is None


def test_env_activation(tmp_path):
    _write_harness(tmp_path, "opencode", VALID.format(root="/somewhere"))
    harness = resolve_active_harness(
        tmp_path, cli_value=None, env={"AGENT_META_HARNESS": "opencode"}
    )
    assert harness is not None and harness.name == "opencode"


def test_cli_flag_beats_env(tmp_path):
    _write_harness(tmp_path, "opencode", VALID.format(root="/somewhere"))
    _write_harness(tmp_path, "claude",
                   "harness:\n  name: claude\n  checkout-root: /elsewhere\n")
    harness = resolve_active_harness(
        tmp_path, cli_value="claude", env={"AGENT_META_HARNESS": "opencode"}
    )
    assert harness is not None and harness.name == "claude"


def test_unknown_harness_lists_available(tmp_path):
    _write_harness(tmp_path, "opencode", VALID.format(root="/somewhere"))
    with pytest.raises(SyncError, match="opencode") as exc_info:
        load_harness(tmp_path, "nope", env={})
    # available names are part of the error message
    assert "config/harnesses" in str(exc_info.value)


def test_whitespace_activation_treated_as_unset(tmp_path):
    assert resolve_active_harness(
        tmp_path, cli_value=None, env={"AGENT_META_HARNESS": "   "}
    ) is None


# ---------------------------------------------------------------------------
# Write-isolation guard
# ---------------------------------------------------------------------------

def _mk_harness(tmp_path: Path, root: Path):
    _write_harness(tmp_path, "opencode", VALID.format(root=root))
    return load_harness(tmp_path, "opencode", env={})


def test_is_within_basic(tmp_path):
    inner = tmp_path / "repos" / "proj"
    inner.mkdir(parents=True)
    assert is_within(inner.resolve(), tmp_path.resolve())
    assert is_within(tmp_path.resolve(), tmp_path.resolve())  # equal counts as inside
    assert not is_within(Path("/definitely/elsewhere"), tmp_path.resolve())


def test_guard_allows_target_inside_checkout(tmp_path):
    harness = _mk_harness(tmp_path, tmp_path / "repos-oc")
    project = tmp_path / "repos-oc" / "myproject"
    project.mkdir(parents=True)
    log = SyncLog()
    assert ensure_write_isolation(harness, project, log) is True
    assert not log.warnings


def test_guard_strict_refuses_outside(tmp_path):
    harness = _mk_harness(tmp_path, tmp_path / "repos-oc")
    outside = tmp_path / "repos" / "myproject"
    outside.mkdir(parents=True)
    with pytest.raises(SyncError, match="write isolation violated"):
        ensure_write_isolation(harness, outside, SyncLog())


def test_guard_non_strict_warns_and_allows(tmp_path):
    harness = _mk_harness(tmp_path, tmp_path / "repos-oc")
    outside = tmp_path / "repos" / "myproject"
    outside.mkdir(parents=True)
    log = SyncLog()
    assert ensure_write_isolation(harness, outside, log, strict=False) is False
    assert any("write isolation violated" in w for w in log.warnings)


def test_guard_error_mentions_checkout_and_remedy(tmp_path):
    harness = _mk_harness(tmp_path, tmp_path / "repos-oc")
    outside = tmp_path / "repos" / "myproject"
    outside.mkdir(parents=True)
    with pytest.raises(SyncError) as exc_info:
        ensure_write_isolation(harness, outside, SyncLog(), label="project-root")
    message = str(exc_info.value)
    assert str((tmp_path / "repos-oc").resolve()) in message
    assert "AGENT_META_HARNESS_ROOT" in message
    assert "remedy" in message


def test_guard_flags_nonexistent_checkout_root(tmp_path):
    harness = _mk_harness(tmp_path, tmp_path / "does-not-exist")
    with pytest.raises(SyncError, match="does not exist"):
        ensure_write_isolation(harness, tmp_path, SyncLog())


def test_guard_follows_symlink_escape(tmp_path):
    real_outside = tmp_path / "real-outside"
    real_outside.mkdir()
    harness = _mk_harness(tmp_path, tmp_path / "repos-oc")
    (tmp_path / "repos-oc").mkdir(parents=True)
    link = tmp_path / "repos-oc" / "escape"
    link.symlink_to(real_outside)
    # Resolved target escapes the checkout root even though the raw path
    # (repos-oc/escape/…) lexically sits inside it.
    with pytest.raises(SyncError, match="write isolation violated"):
        ensure_write_isolation(harness, link / "proj", SyncLog())


# ---------------------------------------------------------------------------
# Shipped harness configs (real repo)
# ---------------------------------------------------------------------------

def test_shipped_harness_configs_match_rfc_convention():
    harnesses = list_harnesses(REPO_ROOT, env={})
    assert set(harnesses) == {"claude", "opencode", "third"}
    assert harnesses["claude"].branch == "agent/claude"
    assert harnesses["opencode"].branch == "agent/opencode"
    assert harnesses["third"].branch == "agent/third"
    assert harnesses["claude"].checkout_root == (Path("~/repos").expanduser()).resolve()
    assert harnesses["opencode"].checkout_root == (Path("~/repos-oc").expanduser()).resolve()
    assert harnesses["third"].checkout_root == (Path("~/repos-x").expanduser()).resolve()


def test_list_harness_names_is_pure_listing(tmp_path):
    _write_harness(tmp_path, "opencode", VALID.format(root="/somewhere"))
    (tmp_path / "config" / "harnesses" / "broken.yaml").write_text(
        "harness:\n  name: broken\n", encoding="utf-8"  # invalid: no checkout-root
    )
    # Pure stem listing — does not parse files, works despite the broken one.
    assert list_harness_names(tmp_path) == ["broken", "opencode"]
    # But full listing is fail-closed.
    with pytest.raises(SyncError):
        list_harnesses(tmp_path, env={})
