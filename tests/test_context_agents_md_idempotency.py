"""Regression test for #434: AGENTS.md must be stable (byte-identical) across
repeated sync.py runs with no config change in between.

Root cause: the "agents-managed" context template ends with a trailing
newline after its closing "<!-- agent-meta:managed-end -->" marker, but the
regex used to find the OLD managed block in the existing file never consumes
any whitespace after that marker. Replacing a match that ends exactly at
"-->" with replacement text that ends in "-->\n" inserts one extra blank
line into the untouched footer on every single run, compounding forever.
"""

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def synced_project(tmp_path):
    """A temp copy of this repo's own project pointed at a real AGENTS.md."""
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lib.config import load_config, build_variables
    from lib.providers import load_providers_config
    from lib.context import sync_context_for_provider
    from lib.log import SyncLog

    project_root = tmp_path
    shutil.copy(REPO_ROOT / "AGENTS.md", project_root / "AGENTS.md")

    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    variables, _ = build_variables(config, REPO_ROOT)
    provider_config = load_providers_config(REPO_ROOT)

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
