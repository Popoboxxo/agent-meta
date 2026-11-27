"""Pins for #1086 (a)-(d): sync-output UX consistency."""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.hooks import _update_settings_hooks
from lib.log import SyncLog
from lib.mcp_provider_config import _config_rel_label


def test_config_rel_label_relative_to_project_root(tmp_path):
    # (a) root-level file reads ".mcp.json", not "<checkout>/.mcp.json"
    assert _config_rel_label(tmp_path / ".mcp.json", tmp_path) == ".mcp.json"
    assert _config_rel_label(tmp_path / ".vscode" / "mcp.json", tmp_path) == ".vscode/mcp.json"


def test_config_rel_label_without_root_keeps_parent_dir(tmp_path):
    assert _config_rel_label(tmp_path / ".cursor" / "mcp.json") == ".cursor/mcp.json"


def test_hooks_parse_warning_uses_configured_config_file(tmp_path):
    # (b) label derives from the provider's hooks config path, not "settings.json"
    cfg = tmp_path / ".agents" / "hooks.json"
    cfg.parent.mkdir()
    cfg.write_text("{not json")
    log = SyncLog()
    _update_settings_hooks(tmp_path, set(), {"x.sh"}, [], log, False,
                           settings_path_rel=".agents/hooks.json")
    assert any(".agents/hooks.json could not be parsed" in w for w in log.warnings)
    assert not any("settings.json" in w for w in log.warnings)


def test_skip_and_note_unchanged_are_separate_buckets():
    # (c)
    log = SyncLog()
    log.skip("a", "why")
    log.note_unchanged("b")
    assert len(log.skipped) == 1 and "[SKIP]" in log.skipped[0]
    assert len(log.unchanged) == 1 and "[SAME]" in log.unchanged[0]


def test_warn_deduplicates_identical_messages():
    # (d)
    log = SyncLog()
    log.warn("same")
    log.warn("same")
    log.warn("other")
    assert len(log.warnings) == 2
