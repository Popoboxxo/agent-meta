"""REQ-10 hard error: commands support without ``commands_dir`` always fails.

AC-5.1 empty sources, AC-5.2 non-empty sources -> ``SyncError`` ("commands_dir");
AC-5.3 ``commands: false`` -> exactly one INFO "not supported", nothing written.
Provider-agnostic: a synthetic provider name and a synthetic capability config.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.commands import sync_commands_for_provider
from scripts.lib.io import SyncError
from scripts.lib.log import SyncLog

_PROVIDER = "synthetic-provider"


def _fake_root(tmp_path: Path, commands: bool, with_source: bool) -> Path:
    root = tmp_path / "agent-meta"
    (root / "config").mkdir(parents=True)
    flag = "true" if commands else "false"
    (root / "config" / "provider-capabilities.yaml").write_text(
        f"capabilities:\n  {_PROVIDER}:\n    commands: {flag}\n", encoding="utf-8"
    )
    generic = root / "commands" / "1-generic"
    generic.mkdir(parents=True)
    if with_source:
        (generic / "demo.md").write_text("# Demo\n", encoding="utf-8")
    return root


def _run(root: Path, project: Path, log: SyncLog, provider_config: dict) -> None:
    sync_commands_for_provider(
        root, project, {}, log, False, _PROVIDER,
        provider_config=provider_config, variables={},
    )


@pytest.mark.parametrize("with_source", [False, True], ids=["empty-sources", "with-sources"])
@pytest.mark.parametrize("provider_config", [{}, {_PROVIDER: {}}], ids=["no-entry", "no-dir"])
def test_support_without_commands_dir_raises(tmp_path, with_source, provider_config):
    root = _fake_root(tmp_path, commands=True, with_source=with_source)
    project = tmp_path / "project"
    project.mkdir()
    with pytest.raises(SyncError, match="commands_dir"):
        _run(root, project, SyncLog(), provider_config)


def test_unsupported_provider_logs_single_info_and_writes_nothing(tmp_path):
    root = _fake_root(tmp_path, commands=False, with_source=True)
    project = tmp_path / "project"
    project.mkdir()
    log = SyncLog()
    _run(root, project, log, {_PROVIDER: {"commands_dir": "out"}})
    assert len([i for i in log.infos if "not supported" in i]) == 1
    assert len(log.infos) == 1
    assert list(project.iterdir()) == []
