"""Regression test for #515: sync.py must never drop user content from the
"Eigene Notizen" section of a managed context file.

The static header above the managed block is regenerated from the template on
every sync. The notes section lives inside that header, so a plain regeneration
deleted everything the user had written there — the one section the template
explicitly promises never to overwrite.

The same promise must hold for AGENTS.md, where the notes section lives in the
FOOTER (below the managed block): that footer is rebuilt from
``AGENTS.project-template.md`` on every sync (``rebuild_footer=True``), so the
user-owned section is in the regeneration path there instead of the header.
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


AGENTS_USER_NOTES = """### Spec-Workflow (reqmd)

`docs/REQUIREMENTS.md` ist die Quelle der Wahrheit.
Neue Anforderungen bekommen dort eine REQ-ID (REQ-xxx).
"""

AGENTS_NOTES_MARKER = "Dieser Bereich wird von `agent-meta` nicht überschrieben!\n"
MANAGED_END_MARKER = "<!-- agent-meta:managed-end -->"


@pytest.fixture
def agents_project(tmp_path):
    """Copy the real AGENTS.md and add user notes to its FOOTER.

    In AGENTS.md the notes section sits below the managed block, and the footer
    template part is regenerated on every sync (``rebuild_footer=True``). The
    user block is inserted before the injected trailing block — everything from
    the first HTML comment below ``managed-end`` — so it lives in exactly the
    region the footer rebuild owns.
    """
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lib.config import build_variables, load_config
    from lib.providers import load_providers_config

    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    variables, _ = build_variables(config, REPO_ROOT)
    provider_config = load_providers_config(REPO_ROOT)

    target = tmp_path / "AGENTS.md"
    shutil.copy(REPO_ROOT / "AGENTS.md", target)

    content = target.read_text(encoding="utf-8")
    assert AGENTS_NOTES_MARKER in content, "fixture source lost its notes marker"
    content = content.replace(
        AGENTS_NOTES_MARKER, AGENTS_NOTES_MARKER + "\n" + AGENTS_USER_NOTES, 1
    )
    # `_split_injected_footer_tail` treats the first HTML comment below the
    # managed block as the start of the injected tail; the notes must sit above
    # it to exercise the footer template part that gets rebuilt.
    footer_start = content.index(MANAGED_END_MARKER) + len(MANAGED_END_MARKER)
    assert content.index(AGENTS_USER_NOTES) > footer_start
    assert content.index(AGENTS_USER_NOTES) < content.index("<!--", footer_start), (
        "fixture must place the user notes in the footer, above the injected tail"
    )
    target.write_text(content, encoding="utf-8")

    def run_sync():
        from lib.context import sync_context_for_provider
        from lib.log import SyncLog

        # Opencode renders AGENTS.md via `_sync_opencode_context`, the same
        # `_regenerate_static_context(..., rebuild_footer=True)` path a real
        # sync.py run takes for the shared AGENTS.md core.
        sync_context_for_provider(
            REPO_ROOT, tmp_path, config, dict(variables), SyncLog(),
            dry_run=False, provider="Opencode", provider_config=provider_config,
        )
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


def test_agents_md_footer_user_notes_survive_sync(agents_project):
    """The notes section lives in the AGENTS.md footer, not the header.

    The footer template part is regenerated on every sync, so everything below
    ``## Eigene Notizen`` must be carried over verbatim — byte-for-byte, not
    merely "some user content is still there".
    """
    content = agents_project()
    assert AGENTS_USER_NOTES in content, (
        "AGENTS.md footer user notes were dropped by the footer rebuild "
        "(_preserve_user_notes only covers the header)"
    )


def test_agents_md_footer_user_notes_survive_repeated_syncs(agents_project):
    agents_project()
    assert AGENTS_USER_NOTES in agents_project()


def test_agents_md_footer_user_notes_are_not_reported_as_drift(agents_project, tmp_path):
    agents_project()
    assert not list(tmp_path.glob("AGENTS.md.sync-backup-*")), (
        "editing the user-owned notes section of the AGENTS.md footer must not be "
        "treated as static-part drift"
    )
