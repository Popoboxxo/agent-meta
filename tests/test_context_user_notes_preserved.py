"""Regression test for #515: sync.py must never drop user content from the
"Eigene Notizen" section of a managed context file.

The static header above the managed block is regenerated from the template on
every sync. The notes section lives inside that header, so a plain regeneration
deleted everything the user had written there — the one section the template
explicitly promises never to overwrite.
"""

import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]

USER_NOTES = """### Testumfang: wann volle E2E-Suite

Kleine Fixes: gezielte Unit-Tests reichen.
Grosse Changes: volle Suite vor Merge.
"""


@pytest.fixture
def project(tmp_path):
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lib.config import build_variables, load_config

    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    variables, _ = build_variables(config, REPO_ROOT)

    target = tmp_path / "CLAUDE.md"
    shutil.copy(REPO_ROOT / "CLAUDE.md", target)

    content = target.read_text(encoding="utf-8")
    marker = "Dieser Bereich wird von `agent-meta` nicht überschrieben!\n"
    assert marker in content, "fixture source lost its notes marker"
    target.write_text(content.replace(marker, marker + "\n" + USER_NOTES, 1), encoding="utf-8")

    def run_sync():
        from lib.context import sync_claude_md_static
        from lib.log import SyncLog

        sync_claude_md_static(REPO_ROOT, tmp_path, config, variables, SyncLog(), dry_run=False)
        return target.read_text(encoding="utf-8")

    return run_sync


def test_user_notes_survive_sync(project):
    assert USER_NOTES.strip() in project()


def test_user_notes_survive_repeated_syncs(project):
    project()
    assert USER_NOTES.strip() in project()


def test_editing_only_the_notes_is_not_reported_as_drift(project, tmp_path):
    project()
    assert not list(tmp_path.glob("CLAUDE.md.sync-backup-*")), (
        "editing the user-owned notes section must not be treated as static-part drift"
    )
