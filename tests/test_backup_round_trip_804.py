"""Regression tests for issue #804.

``--backup`` / ``--list-backups`` / ``--restore`` must form a consistent
round-trip:

* a backup created by ``create_backup`` is restorable by the archive *name*
  that ``list_backups`` prints,
* the content that comes back matches what was backed up, and
* an unresolvable archive name/path is a hard error (non-zero exit), never a
  silent ``success: true`` no-op with ``restored: false``.

The #804 root cause: ``restore_backup`` matched zip members against the
provider *key* (``"Claude"``) although the archive stores the provider's root
*directory* (``".claude/"``). No member ever matched, yet ``restored`` was
reported ``True`` when it was set unconditionally.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO_ROOT / "scripts"
sys.path.insert(0, str(_SCRIPTS))

from lib.backup import create_backup, list_backups, restore_backup
from lib.log import SyncLog


def _seed_project(root: Path) -> dict:
    """Create a minimal project with one provider ("Claude")."""
    (root / ".meta-config").mkdir(parents=True, exist_ok=True)
    (root / ".meta-config" / "project.yaml").write_text("roles: []\n", encoding="utf-8")
    agents = root / ".claude" / "agents"
    agents.mkdir(parents=True, exist_ok=True)
    (agents / "developer.md").write_text("ORIGINAL\n", encoding="utf-8")
    return {"Claude": {"agents_dir": ".claude/agents"}}


def _config() -> dict:
    return {"backup": {"dir": ".backup/agent-meta"}}


def _config_with_sink(*, enabled: bool = True, path: str = ".tmp") -> dict:
    """Backup config plus an explicit tmp-sink (AC-09/AC-10)."""
    return {
        "backup": {"dir": ".backup/agent-meta"},
        "repo_containment": {"tmp-sink": {"enabled": enabled, "path": path}},
    }


def _capture_staging(monkeypatch) -> dict:
    """Record the ``TemporaryDirectory(...)`` kwargs used for backup staging."""
    captured: dict = {}
    real_factory = tempfile.TemporaryDirectory

    def recording_factory(*args, **kwargs):
        captured["args"] = args
        captured["dir"] = kwargs.get("dir")
        if kwargs.get("dir") is not None:
            captured["existed_before"] = Path(kwargs["dir"]).is_dir()
        return real_factory(*args, **kwargs)

    monkeypatch.setattr("lib.backup.tempfile.TemporaryDirectory", recording_factory)
    return captured


def test_round_trip_restore_by_name_restores_content(tmp_path):
    """create -> list -> restore-by-name -> content matches."""
    root = tmp_path
    provider_config = _seed_project(root)
    log = SyncLog()

    created = create_backup(
        root, ["Claude"], provider_config, _config(), log,
        label="round-trip", source_version="0.0.0-test",
    )
    assert created["success"] is True

    listing = list_backups(root, _config(), provider_config)
    assert listing["count"] == 1
    name = listing["archives"][0]["name"]
    assert name.endswith(".zip")

    # Mutate the generated file, then restore by the name list_backups shows.
    agent_file = root / ".claude" / "agents" / "developer.md"
    agent_file.write_text("CHANGED\n", encoding="utf-8")

    result = restore_backup(root, name, provider_config, _config(), log)

    assert result["success"] is True
    prov = result["provider_results"]["Claude"]
    assert prov["restored"] is True
    assert prov.get("files_restored", 0) >= 1
    assert agent_file.read_text(encoding="utf-8") == "ORIGINAL\n"
    # The local meta-config belongs to the round-trip as well.
    assert result["config_restored"] is True


def test_round_trip_matches_manifest_directory_not_provider_key(tmp_path):
    """The archive stores `.claude/`, not the provider key `Claude`."""
    root = tmp_path
    provider_config = _seed_project(root)
    log = SyncLog()

    created = create_backup(root, ["Claude"], provider_config, _config(), log,
                            source_version="0.0.0-test")
    archive_name = Path(created["archive"]).name

    agent_file = root / ".claude" / "agents" / "developer.md"
    agent_file.write_text("CHANGED\n", encoding="utf-8")

    result = restore_backup(root, archive_name, provider_config, _config(), log)

    assert result["provider_results"]["Claude"]["restored"] is True
    assert agent_file.read_text(encoding="utf-8") == "ORIGINAL\n"


def test_restore_by_path_form_restores_too(tmp_path):
    root = tmp_path
    provider_config = _seed_project(root)
    log = SyncLog()

    created = create_backup(root, ["Claude"], provider_config, _config(), log,
                            source_version="0.0.0-test")
    archive_path = str(root / created["archive"])

    agent_file = root / ".claude" / "agents" / "developer.md"
    agent_file.write_text("CHANGED\n", encoding="utf-8")

    result = restore_backup(root, archive_path, provider_config, _config(), log)

    assert result["success"] is True
    assert result["provider_results"]["Claude"]["restored"] is True
    assert agent_file.read_text(encoding="utf-8") == "ORIGINAL\n"


def test_restore_unknown_name_is_an_error(tmp_path):
    """An unresolvable name must be an error, not a silent no-op."""
    root = tmp_path
    provider_config = _seed_project(root)
    log = SyncLog()

    result = restore_backup(root, "does-not-exist.zip", provider_config, _config(), log)

    assert result["success"] is False
    assert "does-not-exist.zip" in result["error"]


def test_restore_unknown_name_cli_exits_nonzero(tmp_path):
    """The CLI must not report rc=0 for an unresolvable archive name."""
    root = tmp_path
    (root / ".meta-config").mkdir(parents=True, exist_ok=True)
    (root / ".meta-config" / "project.yaml").write_text("roles: []\n", encoding="utf-8")

    proc = subprocess.run(
        [sys.executable, str(_SCRIPTS / "sync.py"), "--restore", "does-not-exist.zip"],
        cwd=root,
        capture_output=True,
        text=True,
        timeout=120,
        check=False,
    )

    assert proc.returncode != 0, proc.stdout + proc.stderr
    assert "does-not-exist.zip" in (proc.stdout + proc.stderr)


def test_round_trip_restores_local_secrets_file(tmp_path):
    """`.meta-config/secrets.local.yaml` is part of the round-trip when present."""
    root = tmp_path
    provider_config = _seed_project(root)
    secrets = root / ".meta-config" / "secrets.local.yaml"
    secrets.write_text("MCP_EXAMPLE_VALUE: not-a-real-secret\n", encoding="utf-8")
    log = SyncLog()

    created = create_backup(root, ["Claude"], provider_config, _config(), log,
                            source_version="0.0.0-test")
    archive_name = Path(created["archive"]).name

    secrets.unlink()
    result = restore_backup(root, archive_name, provider_config, _config(), log)

    assert result["success"] is True
    assert secrets.read_text(encoding="utf-8") == "MCP_EXAMPLE_VALUE: not-a-real-secret\n"


# ---------------------------------------------------------------------------
# AC-09 -- backup staging lives inside the tmp-sink
# ---------------------------------------------------------------------------

def test_staging_dir_is_inside_tmp_sink(tmp_path, monkeypatch):
    """AC-09: staging is ``<repo>/.tmp/backup-staging``, never the system temp."""
    root = tmp_path
    provider_config = _seed_project(root)
    log = SyncLog()
    captured = _capture_staging(monkeypatch)

    created = create_backup(
        root, ["Claude"], provider_config, _config_with_sink(), log,
        source_version="0.0.0-test",
    )

    assert created["success"] is True
    assert (root / created["archive"]).is_file()

    staging_base = captured.get("dir")
    assert staging_base is not None, "staging must pass dir= to TemporaryDirectory"
    expected = Path(os.path.realpath(root / ".tmp" / "backup-staging"))
    assert Path(staging_base) == expected
    assert captured.get("existed_before") is True
    # AC-09: the system temp dir is not used as the staging base.
    assert Path(os.path.realpath(staging_base)) != Path(os.path.realpath(tempfile.gettempdir()))
    assert not any(
        "backup.staging-system-temp" in warning for warning in log.warnings
    ), log.warnings
