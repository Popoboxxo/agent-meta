"""#1086 a-e: sync log / hook / MCP label texts."""
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402


def _write_log(log: SyncLog, tmp_path: Path) -> Path:
    path = tmp_path / "s.log"
    log.write(path, "cfg", "1.0", "sync", ["x"], False)
    return path


def test_1086d_warning_not_printed_twice(tmp_path, capsys):
    log = SyncLog()
    log.warn("w-unique-text")
    path = _write_log(log, tmp_path)
    out = capsys.readouterr()
    assert (out.out + out.err).count("w-unique-text") == 1
    assert "WARNINGS: 1 (see above)" in out.out
    assert path.read_text(encoding="utf-8").count("w-unique-text") == 1


def test_1086c_unchanged_separate_from_skipped(tmp_path, capsys):
    log = SyncLog()
    log.note_unchanged("a.sh")
    log.skip("b", "disabled")
    _write_log(log, tmp_path)
    out = capsys.readouterr().out
    assert "1 unchanged  |  1 skipped" in out


def test_1086c_hooks_unchanged_not_skipped(tmp_path):
    from lib.hooks import sync_hooks

    config = {"hooks": {"dod-push-check": {"enabled": True}}}
    for _ in range(2):
        log = SyncLog()
        sync_hooks(_ROOT, tmp_path, config, log, False)
    assert not any("dod-push-check" in line for line in log.skipped)
    assert any("dod-push-check" in line for line in log.unchanged)


def test_1086b_hooks_note_names_provider_config_file(tmp_path):
    from lib.hooks import sync_hooks

    config = {"hooks": {"dod-push-check": {"enabled": True}}}
    pc = {"Gemini": {"has_hooks": True, "hook_protocol": "antigravity-hooks-json", "hooks_dir": ".agents/hooks", "settings_file": ".gemini/settings.json",
                     "hooks_config_file": ".agents/hooks.json"}}
    log = SyncLog()
    sync_hooks(_ROOT, tmp_path, config, log, True, "Gemini", pc)
    notes = [line for line in log.infos if "registered in" in line]
    assert notes, log.infos
    assert all(".agents/hooks.json" in line and "settings.json" not in line for line in notes)


def test_1086a_mcp_label_relative_to_project_root(tmp_path):
    from lib.mcp_provider_config import _config_rel_label

    assert _config_rel_label(tmp_path / ".mcp.json", tmp_path) == ".mcp.json"
    assert _config_rel_label(tmp_path / ".vscode" / "mcp.json", tmp_path) == ".vscode/mcp.json"


def test_1086e_soft_cap_names_shared_context_file(tmp_path):
    from lib.consistency import context_budget as cb

    (tmp_path / "AGENTS.md").write_text("x" * 100, encoding="utf-8")
    caps = {
        "Gemini": {"context_file": "AGENTS.md", "context_soft_cap_chars": 10},
        "Opencode": {"context_file": "AGENTS.md"},
    }
    findings = cb.check_over_soft_cap(tmp_path, ["Gemini", "Opencode"], caps, None)
    assert len(findings) == 1
    assert "shared with: Opencode" in findings[0].message
