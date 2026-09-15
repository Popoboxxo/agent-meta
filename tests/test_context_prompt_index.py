"""Task 5 (stale-role-cleanup): prompt-index fail-closed migration (IC-08).

Covers:
- AC-23 / IC-08 / OQ-9: an absent prompt index adopts nothing — an unmanaged
  ``orphan.md`` survives instead of being swept by the old fail-open delete —
  while the index is still written.
- AC-23: an empty expected set still yields a 0-byte index after a non-dry
  run.
- AC-23: a present index listing ``stale.md`` makes the stale file deleted and
  the index rewritten.
- AC-24 (context clause): the fail-open guard no longer appears in
  ``scripts/lib/context.py`` and the IC-01 helpers are used instead.

Prompt files carry no agent-meta provenance marker, so the fail-closed
predicate adopt-nothing behaviour is exactly the absent-index case.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.context import sync_prompts_for_continue  # noqa: E402
from lib.log import SyncLog  # noqa: E402


def _make_agent_meta_root(tmp_path: Path) -> Path:
    root = tmp_path / "agent-meta"
    (root / "config").mkdir(parents=True)
    (root / "agents" / "1-generic").mkdir(parents=True)
    (root / "config" / "role-defaults.yaml").write_text(
        "roles:\n  developer: {}\n", encoding="utf-8"
    )
    (root / "agents" / "1-generic" / "developer.md").write_text(
        "---\n"
        "name: developer\n"
        'description: "Developer role"\n'
        "version: 1.0.0\n"
        "tools: []\n"
        "---\n"
        "Body for the developer role.\n",
        encoding="utf-8",
    )
    return root


def _config(roles) -> dict:
    return {
        "project": {"name": "TestProj"},
        "roles": list(roles),
        "platforms": [],
        "provider-options": {"Continue": {"generate-prompts": True}},
    }


def test_absent_prompt_index_adopts_nothing(tmp_path: Path) -> None:
    """AC-23: no index → orphan.md survives; the index is still written."""
    agent_meta_root = _make_agent_meta_root(tmp_path)
    project_root = tmp_path / "project"
    prompts_dir = project_root / ".continue" / "prompts"
    prompts_dir.mkdir(parents=True)
    orphan = prompts_dir / "orphan.md"
    orphan.write_text("user-authored orphan\n", encoding="utf-8")
    index = prompts_dir / ".agent-meta-managed"
    assert not index.exists()

    sync_prompts_for_continue(
        agent_meta_root, project_root, _config(("developer",)), {}, SyncLog(),
        dry_run=False, provider_config={},
    )

    assert orphan.exists(), "fail-open delete removed an unmanaged prompt file"
    assert index.exists(), "index must be written even when nothing is adopted"
    assert index.read_text(encoding="utf-8") == "developer.md\n"
    assert (prompts_dir / "developer.md").exists()


def test_empty_expected_writes_zero_byte_index(tmp_path: Path) -> None:
    """AC-23: expected == set() still produces a 0-byte index (non-dry)."""
    agent_meta_root = _make_agent_meta_root(tmp_path)
    project_root = tmp_path / "project"
    prompts_dir = project_root / ".continue" / "prompts"
    prompts_dir.mkdir(parents=True)
    index = prompts_dir / ".agent-meta-managed"

    sync_prompts_for_continue(
        agent_meta_root, project_root, _config(()), {}, SyncLog(),
        dry_run=False, provider_config={},
    )

    assert index.exists()
    assert index.read_bytes() == b""


def test_present_prompt_index_deletes_stale_and_rewrites(tmp_path: Path) -> None:
    """AC-23: an index-tracked stale prompt is deleted and the index rewritten."""
    agent_meta_root = _make_agent_meta_root(tmp_path)
    project_root = tmp_path / "project"
    prompts_dir = project_root / ".continue" / "prompts"
    prompts_dir.mkdir(parents=True)
    stale = prompts_dir / "stale.md"
    stale.write_text("stale prompt\n", encoding="utf-8")
    index = prompts_dir / ".agent-meta-managed"
    index.write_text("stale.md\n", encoding="utf-8")

    sync_prompts_for_continue(
        agent_meta_root, project_root, _config(("developer",)), {}, SyncLog(),
        dry_run=False, provider_config={},
    )

    assert not stale.exists(), "index-listed stale prompt must be deleted"
    assert index.read_text(encoding="utf-8") == "developer.md\n"


def test_prompt_fail_open_clause_gone() -> None:
    """AC-24: the fail-open guard is gone and the IC-01 helpers are wired in."""
    source = (REPO_ROOT / "scripts" / "lib" / "context.py").read_text(encoding="utf-8")
    assert "not managed_index.exists() or" not in source
    assert "bootstrap_previously_managed" in source
    assert "write_managed_index" in source
