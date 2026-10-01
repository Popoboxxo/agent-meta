"""Regression tests for repeated sync.py runs with no config change in between.

Part 1 (issue #434): the "agents-managed" context template ends with a trailing
newline after its closing "<!-- agent-meta:managed-end -->" marker, but the
regex used to find the OLD managed block in the existing file never consumes
any whitespace after that marker. Replacing a match that ends exactly at
"-->" with replacement text that ends in "-->\n" inserts one extra blank
line into the untouched footer on every single run, compounding forever.

Part 2 (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30, Task 11; AC-4): every
provider that renders into the shared ``AGENTS.md`` — now including Mammouth,
which reads ``AGENTS.md`` after the PRE-5/OQ-7 decision — must converge to a
byte-identical managed block from run 1 (shared-render convergence). The
Continue context file joins the same fixpoint invariant: its first run used to
scaffold a rich block that the second run replaced with the steady-state
managed block, so run1 != run2. The first sync now renders the substituted
steady-state block, making run 1 the fixpoint.
"""

import hashlib
import shutil
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

# Every provider whose context_file is AGENTS.md (config/ai-providers.yaml).
_AGENTS_MD_SHARERS = ("Gemini", "Opencode", "Codex", "ZCode", "KimiCode", "Mammouth")


def _load_repo_fixtures():
    from lib.config import build_variables, load_config
    from lib.providers import load_providers_config

    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    variables, _ = build_variables(config, REPO_ROOT)
    provider_config = load_providers_config(REPO_ROOT)
    return config, variables, provider_config


@pytest.fixture
def synced_project(tmp_path):
    """A temp copy of this repo's own project pointed at a real AGENTS.md."""
    from lib.context import sync_context_for_provider
    from lib.log import SyncLog

    project_root = tmp_path
    shutil.copy(REPO_ROOT / "AGENTS.md", project_root / "AGENTS.md")

    config, variables, provider_config = _load_repo_fixtures()

    def run_sync():
        log = SyncLog()
        for provider in ("Gemini", "Opencode"):
            sync_context_for_provider(
                REPO_ROOT, project_root, config, variables, log,
                dry_run=False, provider=provider, provider_config=provider_config,
            )
        return (project_root / "AGENTS.md").read_text(encoding="utf-8")

    return run_sync


def test_agents_md_stable_across_repeated_syncs(synced_project):
    first = synced_project()
    second = synced_project()
    third = synced_project()
    assert first == second == third


def test_agents_md_footer_newline_count_does_not_grow(synced_project):
    import re

    def leading_newlines_after_managed_end(text):
        m = re.search(r"<!--\s*agent-meta:managed-end\s*-->", text)
        i = m.end()
        n = 0
        while text[i + n] == "\n":
            n += 1
        return n

    before = leading_newlines_after_managed_end(synced_project())
    after = leading_newlines_after_managed_end(synced_project())
    assert after == before


@pytest.fixture
def shared_agents_md_project(tmp_path):
    """Sync every AGENTS.md sharer into one temp AGENTS.md.

    Mammouth is now part of the shared-render group (PRE-5/OQ-7): it must
    produce the same managed block as the other sharers, otherwise a lone
    ``--check`` reports a permanent, unfixable false "out of sync".
    """
    from lib.context import sync_context_for_provider
    from lib.log import SyncLog

    project_root = tmp_path
    shutil.copy(REPO_ROOT / "AGENTS.md", project_root / "AGENTS.md")

    config, variables, provider_config = _load_repo_fixtures()

    def run_sync():
        log = SyncLog()
        for provider in _AGENTS_MD_SHARERS:
            sync_context_for_provider(
                REPO_ROOT, project_root, config, variables, log,
                dry_run=False, provider=provider, provider_config=provider_config,
            )
        return (project_root / "AGENTS.md").read_bytes()

    return run_sync


def test_shared_agents_md_converges_with_mammouth(shared_agents_md_project):
    """AC-4: run1 == run2 == run3 for the full shared-render group."""
    first = shared_agents_md_project()
    second = shared_agents_md_project()
    third = shared_agents_md_project()
    assert first == second == third
    assert hashlib.sha256(first).digest() == hashlib.sha256(second).digest()


@pytest.fixture
def continue_project(tmp_path):
    """Run one Continue context sync + convergence pass, return the file bytes."""
    from lib.context import sync_context_for_provider
    from lib.log import SyncLog
    from lib.sync_pipeline import converge_managed_block_context

    project_root = tmp_path
    config, variables, provider_config = _load_repo_fixtures()
    context_file = provider_config["Continue"]["context_file"]

    def run_sync():
        log = SyncLog()
        sync_context_for_provider(
            REPO_ROOT, project_root, config, variables, log,
            dry_run=False, provider="Continue", provider_config=provider_config,
        )
        converge_managed_block_context(
            project_root, context_file, variables, log,
            agent_meta_root=REPO_ROOT,
        )
        return (project_root / context_file).read_bytes()

    return run_sync


def test_continue_context_run1_is_fixpoint(continue_project):
    """AC-4: the first Continue sync is already the run2 fixpoint."""
    first = continue_project()
    second = continue_project()
    third = continue_project()
    assert first == second == third


def test_continue_convergence_preserves_user_content(tmp_path):
    """The run1 convergence only rewrites the managed block, never user text."""
    from lib.context import sync_context_for_provider
    from lib.log import SyncLog
    from lib.sync_pipeline import converge_managed_block_context

    project_root = tmp_path
    config, variables, provider_config = _load_repo_fixtures()
    context_file = provider_config["Continue"]["context_file"]
    log = SyncLog()
    sync_context_for_provider(
        REPO_ROOT, project_root, config, variables, log,
        dry_run=False, provider="Continue", provider_config=provider_config,
    )
    target = project_root / context_file
    user_note = "\n<!-- user note outside the managed block -->\n"
    target.write_text(target.read_text(encoding="utf-8") + user_note, encoding="utf-8")

    converge_managed_block_context(
        project_root, context_file, variables, log, agent_meta_root=REPO_ROOT,
    )

    assert user_note in target.read_text(encoding="utf-8")
