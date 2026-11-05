"""Tests for the additive ``additionalDirectories`` writer — issue #1079.

The pytest ``--basetemp`` lives in the platform temp root (usually
``/tmp/<user>/pytest-agent-meta``) because ADR-03 rejects an in-repo basetemp
(the 16-GB incident). That absolute path contains the username and the OS temp
location, so it must never be written into the committed
``.claude/settings.json``. Option C (D20) therefore adds it — additively, never
removing user entries — to the gitignored ``settings.local.json`` through the
data-driven provider key ``settings-allow-dirs-key``.

Run: python3 -m pytest tests/test_settings_dirs.py -q --basetemp=<external>
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402
from lib.settings_dirs import (  # noqa: E402
    basetemp_dirs,
    outside_project_dirs,
    sync_allowed_directories,
)

PC = {"settings_local_file": ".claude/settings.local.json",
      "settings-allow-dirs-key": "permissions.additionalDirectories"}
BASETEMP = "/var/tmp/u/pytest-agent-meta"

_SETTINGS_LOCAL = Path(".claude") / "settings.local.json"
_SETTINGS_COMMITTED = Path(".claude") / "settings.json"


def _read(root: Path) -> dict:
    return json.loads((root / _SETTINGS_LOCAL).read_text(encoding="utf-8"))


def _providers() -> dict:
    return yaml.safe_load(
        (REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8")
    )["providers"]


# ---------------------------------------------------------------------------
# G3 — additive writer
# ---------------------------------------------------------------------------

def test_adds_directory_to_new_local_settings(tmp_path):
    sync_allowed_directories(tmp_path, PC, [BASETEMP], SyncLog(), False)
    assert _read(tmp_path) == {"permissions": {"additionalDirectories": [BASETEMP]}}
    # The committed settings.json is never the write target.
    assert not (tmp_path / _SETTINGS_COMMITTED).exists()


def test_preserves_user_keys_and_existing_entries(tmp_path):
    p = tmp_path / _SETTINGS_LOCAL
    p.parent.mkdir()
    p.write_text(json.dumps({
        "x": 1,
        "permissions": {"allow": ["Bash(ls)"], "additionalDirectories": ["/a"]},
    }), encoding="utf-8")
    sync_allowed_directories(tmp_path, PC, [BASETEMP], SyncLog(), False)
    assert _read(tmp_path) == {
        "x": 1,
        "permissions": {
            "allow": ["Bash(ls)"],
            "additionalDirectories": ["/a", BASETEMP],
        },
    }


def test_idempotent_second_run_no_change(tmp_path):
    sync_allowed_directories(tmp_path, PC, [BASETEMP], SyncLog(), False)
    first = (tmp_path / _SETTINGS_LOCAL).read_bytes()
    sync_allowed_directories(tmp_path, PC, [BASETEMP], SyncLog(), False)
    assert (tmp_path / _SETTINGS_LOCAL).read_bytes() == first


def test_no_capability_no_write(tmp_path):
    sync_allowed_directories(
        tmp_path, {"settings_local_file": ".claude/settings.local.json"},
        [BASETEMP], SyncLog(), False,
    )
    assert not (tmp_path / ".claude").exists()


def test_empty_directories_no_write(tmp_path):
    sync_allowed_directories(tmp_path, PC, [], SyncLog(), False)
    assert not (tmp_path / ".claude").exists()


def test_dry_run_writes_nothing(tmp_path):
    sync_allowed_directories(tmp_path, PC, [BASETEMP], SyncLog(), True)
    assert not (tmp_path / ".claude").exists()


def test_invalid_json_untouched_with_warn(tmp_path):
    p = tmp_path / _SETTINGS_LOCAL
    p.parent.mkdir()
    p.write_text("{not json", encoding="utf-8")
    log = SyncLog()
    sync_allowed_directories(tmp_path, PC, [BASETEMP], log, False)
    assert p.read_text(encoding="utf-8") == "{not json"
    assert len(log.warnings) == 1


def test_outside_project_dirs_filters_inside_paths(tmp_path):
    inside = str(tmp_path / ".tmp" / "pytest")
    assert outside_project_dirs(tmp_path, [inside, BASETEMP]) == [BASETEMP]


# ---------------------------------------------------------------------------
# BLOCKING 1 — the write must stay inside the project (symlinks)
# ---------------------------------------------------------------------------

def test_symlinked_settings_dir_cannot_write_outside_project(tmp_path):
    outside = tmp_path / "outside"
    outside.mkdir()
    project = tmp_path / "project"
    project.mkdir()
    (project / ".claude").symlink_to(outside, target_is_directory=True)

    log = SyncLog()
    status = sync_allowed_directories(project, PC, [BASETEMP], log, False)

    assert status == "warned"
    assert not (outside / "settings.local.json").exists()
    assert len(log.warnings) == 1


def test_symlinked_settings_file_inside_project_is_followed(tmp_path):
    project = tmp_path / "project"
    (project / ".claude").mkdir(parents=True)
    real = project / "real-settings.json"
    real.write_text("{}\n", encoding="utf-8")
    link = project / _SETTINGS_LOCAL
    link.symlink_to(real)

    status = sync_allowed_directories(project, PC, [BASETEMP], SyncLog(), False)

    assert status == "written"
    assert link.is_symlink()
    assert json.loads(real.read_text(encoding="utf-8")) == {
        "permissions": {"additionalDirectories": [BASETEMP]},
    }


def test_symlinked_settings_file_outside_project_is_rejected(tmp_path):
    outside = tmp_path / "outside.json"
    outside.write_text("{}\n", encoding="utf-8")
    project = tmp_path / "project"
    (project / ".claude").mkdir(parents=True)
    (project / _SETTINGS_LOCAL).symlink_to(outside)

    status = sync_allowed_directories(project, PC, [BASETEMP], SyncLog(), False)

    assert status == "warned"
    assert outside.read_text(encoding="utf-8") == "{}\n"


# ---------------------------------------------------------------------------
# BLOCKING 2 — --check must not report an absent gitignored target (#752)
# ---------------------------------------------------------------------------

def _git_repo_with_ignored_settings(root: Path) -> None:
    import subprocess

    subprocess.run(["git", "init", "-q", str(root)], check=True)
    (root / ".gitignore").write_text(
        ".claude/settings.local.json\n", encoding="utf-8",
    )


def test_check_skips_absent_gitignored_target(tmp_path):
    _git_repo_with_ignored_settings(tmp_path)
    log = SyncLog()

    status = sync_allowed_directories(tmp_path, PC, [BASETEMP], log, True)

    assert status == "skipped"
    assert log.actions == []
    assert not (tmp_path / _SETTINGS_LOCAL).exists()


# ---------------------------------------------------------------------------
# ADVISORY 1 — a non-dict intermediate node is never overwritten
# ---------------------------------------------------------------------------

def test_non_dict_intermediate_node_is_preserved(tmp_path):
    p = tmp_path / _SETTINGS_LOCAL
    p.parent.mkdir()
    original = json.dumps({"permissions": "user-string"})
    p.write_text(original, encoding="utf-8")
    log = SyncLog()

    status = sync_allowed_directories(tmp_path, PC, [BASETEMP], log, False)

    assert status == "warned"
    assert p.read_text(encoding="utf-8") == original
    assert len(log.warnings) == 1


# ---------------------------------------------------------------------------
# G4 — provider key, resolved basetemp, gitignored target
# ---------------------------------------------------------------------------

def test_claude_declares_allow_dirs_key_and_others_do_not():
    providers = _providers()
    claude = providers["Claude"]
    assert claude["settings-allow-dirs-key"] == "permissions.additionalDirectories"
    assert claude["settings_local_file"] == ".claude/settings.local.json"
    declared = {
        name: pc["settings-allow-dirs-key"]
        for name, pc in providers.items()
        if name != "Claude" and pc.get("settings-allow-dirs-key")
    }
    # Other providers' allow-dir key formats are unverified — add when documented.
    assert declared == {}


def test_local_settings_target_stays_gitignored():
    claude = _providers()["Claude"]
    assert claude["settings_local_file"] in claude["gitignore_entries"]


def test_basetemp_dirs_for_project_uses_resolved_system_temp(tmp_path):
    out = basetemp_dirs(tmp_path, {})  # framework default: system-temp exception
    assert len(out) == 1
    assert not out[0].startswith(str(tmp_path))


def test_basetemp_dirs_empty_when_sink_used(tmp_path):
    cfg = {
        "repo_containment": {
            "tmp-sink": {
                "system-temp-exception": {"enabled": False, "pytest-basetemp": False},
            },
        },
    }
    assert basetemp_dirs(tmp_path, cfg) == []
