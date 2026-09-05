"""Regression test for #638: AGENTS.md is shared by Opencode + Gemini, both via
`context_file: AGENTS.md` (config/ai-providers.yaml). Both render their managed
block through the same `_build_managed_block()`, but several per-provider config
fields (`pending_tasks_file`, `skills_dir`, ...) used to leak the CURRENTLY
rendering provider's own value into the shared block instead of a value that is
identical no matter which shared provider renders it.

Effect: whichever provider ran last in a given sync.py invocation "won" the
managed block content, so a lone `--check`/`--dry-run` run (which renders each
active provider once, in the same fixed order every time) always reported the
first-rendered shared provider's output as "different" from what the
last-rendered provider had actually persisted on disk -- a permanent false
"out of sync" that no `sync.py` run could ever resolve, because both providers'
renders never converge to one shared, stable value.

Fix: `_build_managed_block()` now resolves every provider-specific value used
in the shared block (paths, embedded-rule/tool inclusion) from the UNION of all
providers sharing that `context_file`, not from the single `provider` argument
of the current call -- so the rendered content is byte-identical regardless of
call order.
"""

import shutil
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def loaded_config():
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lib.config import load_config
    from lib.providers import load_providers_config

    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    provider_config = load_providers_config(REPO_ROOT)
    return config, provider_config


# Every provider sharing context_file AGENTS.md (config/ai-providers.yaml).
# Codex/ZCode/KimiCode joined the shared-context group in 2026-09 — the #638
# union logic must cover ALL sharers, not just the two that existed then.
_AGENTS_MD_SHARERS = ("Opencode", "Gemini", "Codex", "ZCode", "KimiCode")


def test_shared_managed_block_identical_regardless_of_provider(loaded_config):
    """All providers sharing AGENTS.md must render byte-identical content."""
    from lib.context import _build_managed_block
    from lib.log import SyncLog

    config, provider_config = loaded_config
    variables = config.get("variables", {})

    rendered = {
        provider: _build_managed_block(
            REPO_ROOT, config, dict(variables), SyncLog(),
            provider=provider, provider_config=provider_config, project_root=REPO_ROOT,
        )
        for provider in _AGENTS_MD_SHARERS
    }
    baseline = rendered[_AGENTS_MD_SHARERS[0]]
    diverged = [p for p, block in rendered.items() if block != baseline]
    assert not diverged, (
        f"AGENTS.md sharers {diverged} render a different managed block than "
        f"{_AGENTS_MD_SHARERS[0]} -- any divergence means a lone sync.py --check "
        f"run will report a permanent, unfixable false 'out of sync' (issue #638)."
    )


def test_repeated_sync_never_reports_pending_agents_md_change(tmp_path, loaded_config):
    """Simulates sync.py --check: sync once, then re-render each shared
    provider independently and confirm neither ever diffs from what is on disk.
    """
    import sys
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lib.context import sync_context_for_provider
    from lib.log import SyncLog

    config, provider_config = loaded_config
    variables = config.get("variables", {})
    project_root = tmp_path
    shutil.copy(REPO_ROOT / "AGENTS.md", project_root / "AGENTS.md")

    def sync_once(provider: str, dry_run: bool) -> SyncLog:
        log = SyncLog()
        sync_context_for_provider(
            REPO_ROOT, project_root, config, variables, log,
            dry_run=dry_run, provider=provider, provider_config=provider_config,
        )
        return log

    # Full convergence sync (all shared providers, real write).
    for provider in _AGENTS_MD_SHARERS:
        sync_once(provider, dry_run=False)
    converged = (project_root / "AGENTS.md").read_text(encoding="utf-8")

    # Now emulate `--check`/`--dry-run`: each shared provider re-renders
    # independently against the already-converged file. Neither may log an
    # AGENTS.md UPDATE action -- that action count is exactly what --check
    # exits non-zero on.
    for provider in _AGENTS_MD_SHARERS:
        log = sync_once(provider, dry_run=True)
        agents_md_updates = [
            a for a in log.actions if "AGENTS.md" in a and "UPDATE" in a
        ]
        assert not agents_md_updates, (
            f"{provider}: dry-run reports AGENTS.md as changed even though no "
            "config changed since the last full sync (issue #638 oscillation)."
        )

    # File on disk must stay byte-identical across the dry-run probes.
    assert (project_root / "AGENTS.md").read_text(encoding="utf-8") == converged
