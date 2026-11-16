"""ReqogniLoom active as external plugin AND catalog server => one WARN (#1261).

Run: python -m pytest tests/test_mcp_duplicate_plugin_warning.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.log import SyncLog  # noqa: E402
from lib.mcp_health import check_external_plugin_duplicates  # noqa: E402

REGISTRY = {"reqogniloom": {"external-plugin-id-prefix": "reqogniloom@"},
            "other": {}}
CFGS = {"Claude": {"external_plugins_file": {
    "path": "~/.claude/settings.json", "enabled_key": "enabledPlugins"}}}


def _log():
    return SyncLog()


def _write(home: Path, content: str) -> None:
    f = home / ".claude" / "settings.json"
    f.parent.mkdir(parents=True)
    f.write_text(content, encoding="utf-8")


def _plugins(value) -> str:
    return json.dumps({"enabledPlugins": {"reqogniloom@reqogniloom-marketplace": value}})


def test_warns_once_when_plugin_and_server_active(tmp_path):
    _write(tmp_path, _plugins(True))
    log = _log()
    check_external_plugin_duplicates(REGISTRY, ["reqogniloom", "other"], CFGS, log, tmp_path)
    assert len(log.warnings) == 1
    assert "reqogniloom" in log.warnings[0] and "enabled: false" in log.warnings[0]


def test_no_warn_without_file(tmp_path):
    log = _log()
    check_external_plugin_duplicates(REGISTRY, ["reqogniloom"], CFGS, log, tmp_path)
    assert log.warnings == []


def test_no_warn_when_plugin_false_or_server_inactive(tmp_path):
    _write(tmp_path, _plugins(False))
    log = _log()
    check_external_plugin_duplicates(REGISTRY, ["reqogniloom"], CFGS, log, tmp_path)
    (tmp_path / ".claude" / "settings.json").write_text(_plugins(True), encoding="utf-8")
    check_external_plugin_duplicates(REGISTRY, ["other"], CFGS, log, tmp_path)
    assert log.warnings == []


def test_no_warn_without_provider_flag(tmp_path):
    _write(tmp_path, _plugins(True))
    log = _log()
    check_external_plugin_duplicates(REGISTRY, ["reqogniloom"], {"X": {}}, log, tmp_path)
    assert log.warnings == []


def test_defect_files_never_raise_or_warn(tmp_path):
    for content in ("not json", "[1, 2]", '{"enabledPlugins": []}',
                    '{"enabledPlugins": "x"}'):
        home = tmp_path / str(abs(hash(content)))
        _write(home, content)
        log = _log()
        check_external_plugin_duplicates(REGISTRY, ["reqogniloom"], CFGS, log, home)
        assert log.warnings == []


def test_check_mcp_health_without_provider_cfgs_skips_check(tmp_path):
    import inspect

    from lib.mcp_health import check_mcp_health

    params = inspect.signature(check_mcp_health).parameters
    assert params["provider_cfgs"].default is None


def test_check_external_plugin_duplicates_failure_never_escapes(tmp_path, monkeypatch):
    """IC-5: a raising duplicate check must not abort the health check."""
    import scripts.lib.mcp_health as mh

    def boom(*a, **k):
        raise RuntimeError("boom")

    monkeypatch.setattr(mh, "load_mcp_registry", lambda *a, **k: {"reqogniloom": {}})
    monkeypatch.setattr(mh, "resolve_active_mcp_servers", lambda *a, **k: ["reqogniloom"])
    monkeypatch.setattr(mh, "check_external_plugin_duplicates", boom)
    mh.check_mcp_health(tmp_path, tmp_path, {}, _log(), env={}, provider_cfgs=CFGS)


def test_non_dict_registry_never_raises(tmp_path, monkeypatch):
    import scripts.lib.mcp_health as mh

    monkeypatch.setattr(mh, "load_mcp_registry", lambda *a, **k: [])
    monkeypatch.setattr(mh, "resolve_active_mcp_servers", lambda *a, **k: ["reqogniloom"])
    mh.check_mcp_health(tmp_path, tmp_path, {}, _log(), env={}, provider_cfgs=CFGS, home=tmp_path)


def test_pipeline_passes_only_active_providers(tmp_path, monkeypatch):
    """Wiring: stage 3 hands check_mcp_health the active providers only."""
    import argparse

    import scripts.lib.sync_pipeline as sp

    for name in ("init_settings_json", "init_settings_local_json", "sync_secrets_template"):
        monkeypatch.setattr(sp, name, lambda *a, **k: None)
    seen = {}
    monkeypatch.setattr(sp, "check_mcp_health", lambda *a, **k: seen.update(k))
    config = {"context_file": {"auto_generate": False},
              "provider-deactivation": {"enabled": True, "mode": "selective",
                                        "providers": ["Off"]}}
    provider_config = {"On": {"x": 1}, "Off": {"x": 2}}
    sp._sync_stage_claude_base(
        tmp_path, tmp_path, config, provider_config, ["On", "Off"], {},
        argparse.Namespace(dry_run=True), _log())
    assert seen["provider_cfgs"] == {"On": {"x": 1}}
