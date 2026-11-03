"""Schema validation for the ``auto_commit`` block (issue #1091).

Two layers are covered:

* ``auto_commit_violations`` / ``resolve_auto_commit_config`` (unit): an
  invalid block yields explicit violation messages and the resolver falls
  back to the fail-safe allowlist (``mode: off``, ``eligible_roles: []``).
* ``sync.py`` / ``sync.py --validate`` (subprocess e2e): a schema-invalid
  block fails validation with rc=1 while a normal sync stays rc=0 and writes
  the fail-safe allowlist plus a WARN -- no time-based grace.
"""

import json
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.auto_commit import auto_commit_violations, resolve_auto_commit_config


# --------------------------------------------------------------------------- #
# Unit: violation detection + fail-safe resolver                              #
# --------------------------------------------------------------------------- #


def test_valid_and_absent_blocks_have_no_violations():
    assert auto_commit_violations({}) == []
    assert auto_commit_violations({"auto_commit": None}) == []
    assert auto_commit_violations(
        {"auto_commit": {"mode": "auto", "triggers": ["task-boundary"]}}) == []
    assert auto_commit_violations(
        {"auto_commit": {"mode": "custom", "custom_script": "x.sh"}}) == []


def test_triggers_with_mode_off_is_violation():
    v = auto_commit_violations(
        {"auto_commit": {"mode": "off", "triggers": ["task-boundary"]}})
    assert v == ["auto_commit.triggers is only valid with mode: auto"]


def test_custom_without_script_is_violation():
    msg = "auto_commit.custom_script is required for mode: custom or trigger: custom"
    assert auto_commit_violations({"auto_commit": {"mode": "custom"}}) == [msg]
    assert auto_commit_violations(
        {"auto_commit": {"mode": "auto", "triggers": ["custom"],
                         "custom_script": " "}}) == [msg]


def test_unknown_values_and_keys():
    v = auto_commit_violations(
        {"auto_commit": {"mode": "loose", "triggers": ["nope"], "bogus": 1,
                         "file_count_threshold": 0}})
    assert any("auto_commit.mode" in m for m in v)
    assert any("unknown value" in m and "nope" in m for m in v)
    assert any("bogus" in m for m in v)
    assert any("file_count_threshold" in m for m in v)


def test_resolve_fail_safe_on_violation():
    cfg = {"auto_commit": {"mode": "off", "triggers": ["task-boundary"]}}
    out = resolve_auto_commit_config(cfg, ["developer"], REPO_ROOT)
    assert out["mode"] == "off" and out["eligible_roles"] == [] and out["triggers"] == []


def test_valid_config_unchanged():
    cfg = {"auto_commit": {"mode": "auto", "triggers": ["task-boundary"]}}
    out = resolve_auto_commit_config(cfg, ["developer", "git"], REPO_ROOT)
    assert out["mode"] == "auto" and out["eligible_roles"] == ["developer"]


# --------------------------------------------------------------------------- #
# E2E: --validate rc=1, sync rc=0 + fail-safe allowlist                       #
# --------------------------------------------------------------------------- #


def _project(tmp_path, ac):
    (tmp_path / ".meta-config").mkdir()
    (tmp_path / ".meta-config" / "project.yaml").write_text(
        "project:\n  name: t\n  prefix: t\nai-providers: [Claude]\n"
        "roles: [orchestrator, developer, git]\n" + ac, encoding="utf-8")
    return tmp_path


def _sync(project, *flags):
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync.py"), *flags],
        cwd=project, capture_output=True, text=True)


def test_validate_rc1_on_triggers_with_mode_off(tmp_path):
    p = _project(tmp_path, "auto_commit:\n  mode: 'off'\n  triggers: [task-boundary]\n")
    r = _sync(p, "--validate")
    assert r.returncode == 1 and "triggers is only valid with mode: auto" in (
        r.stdout + r.stderr)


def test_validate_rc1_on_custom_without_script(tmp_path):
    p = _project(tmp_path, "auto_commit:\n  mode: custom\n")
    assert _sync(p, "--validate").returncode == 1


def test_sync_rc0_but_allowlist_fail_safe(tmp_path):
    p = _project(tmp_path, "auto_commit:\n  mode: auto\n  triggers: [custom]\n")
    r = _sync(p)
    assert r.returncode == 0, r.stderr
    data = json.loads(
        (p / ".meta-config" / "auto-commit-allowlist.json").read_text(encoding="utf-8"))
    assert data["mode"] == "off" and data["eligible_roles"] == []
    assert "commit authority disabled" in r.stderr


def test_validate_rc0_on_valid_config(tmp_path):
    p = _project(tmp_path, "auto_commit:\n  mode: auto\n  triggers: [task-boundary]\n")
    assert _sync(p, "--validate").returncode == 0
