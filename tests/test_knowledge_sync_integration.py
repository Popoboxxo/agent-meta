"""Integration tests for scripts/sync.py::sync_knowledge_engine() (Phase 2.5)."""
from pathlib import Path
import sys

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.log import SyncLog  # noqa: E402
from lib.io import SyncError  # noqa: E402
import sync as sync_module  # noqa: E402

sync_knowledge_engine = sync_module.sync_knowledge_engine

_AGENT_META_ROOT = _REPO_ROOT


def _config(enabled=True, domain="research", bundle_path="knowledge"):
    return {
        "knowledge-engine": {
            "enabled": enabled,
            "domain": domain,
            "bundle-path": bundle_path,
        }
    }


# ---------------------------------------------------------------------------
# Disabled — zero-overhead regression
# ---------------------------------------------------------------------------

def test_disabled_is_a_complete_noop(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, {}, log, dry_run=False)
    assert not (tmp_path / "knowledge").exists()
    assert not log.actions


def test_disabled_explicitly_is_a_complete_noop(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(enabled=False), log, dry_run=False)
    assert not (tmp_path / "knowledge").exists()
    assert not log.actions


# ---------------------------------------------------------------------------
# Fresh scaffolding
# ---------------------------------------------------------------------------

def test_fresh_bundle_creates_expected_files(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log, dry_run=False)

    bundle = tmp_path / "knowledge"
    assert (bundle / "schema.md").exists()
    assert (bundle / "wiki" / "index.md").exists()
    assert (bundle / "wiki" / "log.md").exists()
    for sub in ["sources/assets", "wiki/concepts", "wiki/entities",
                "wiki/topics", "wiki/sources", "wiki/queries"]:
        assert (bundle / sub / ".gitkeep").exists(), f"missing .gitkeep in {sub}"

    schema_text = (bundle / "schema.md").read_text(encoding="utf-8")
    assert "research" in schema_text
    assert "- paper" in schema_text


def test_fresh_bundle_dry_run_writes_nothing(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log, dry_run=True)
    assert not (tmp_path / "knowledge").exists()


def test_custom_bundle_path_and_domain(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(domain="book", bundle_path="kb"), log, dry_run=False)
    bundle = tmp_path / "kb"
    assert (bundle / "schema.md").exists()
    schema_text = (bundle / "schema.md").read_text(encoding="utf-8")
    assert "book" in schema_text
    assert "- character" in schema_text


# ---------------------------------------------------------------------------
# Idempotency — second run must not overwrite
# ---------------------------------------------------------------------------

def test_second_run_does_not_overwrite_existing_bundle_files(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log, dry_run=False)

    bundle = tmp_path / "knowledge"
    (bundle / "schema.md").write_text("# hand-edited by user\n", encoding="utf-8")
    (bundle / "wiki" / "index.md").write_text("# hand-edited index\n", encoding="utf-8")
    (bundle / "wiki" / "log.md").write_text("# hand-edited log\n", encoding="utf-8")

    log2 = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log2, dry_run=False)

    assert (bundle / "schema.md").read_text(encoding="utf-8") == "# hand-edited by user\n"
    assert (bundle / "wiki" / "index.md").read_text(encoding="utf-8") == "# hand-edited index\n"
    assert (bundle / "wiki" / "log.md").read_text(encoding="utf-8") == "# hand-edited log\n"


def test_second_run_fills_in_missing_gitkeep_only(tmp_path):
    log = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log, dry_run=False)

    bundle = tmp_path / "knowledge"
    (bundle / "wiki" / "concepts" / ".gitkeep").unlink()
    assert not (bundle / "wiki" / "concepts" / ".gitkeep").exists()

    log2 = SyncLog()
    sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log2, dry_run=False)
    assert (bundle / "wiki" / "concepts" / ".gitkeep").exists()


# ---------------------------------------------------------------------------
# Error handling
# ---------------------------------------------------------------------------

def test_bundle_path_is_existing_file_raises_sync_error(tmp_path):
    (tmp_path / "knowledge").write_text("not a directory\n", encoding="utf-8")
    log = SyncLog()
    with pytest.raises(SyncError, match="not a directory"):
        sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(), log, dry_run=False)


def test_invalid_domain_raises_sync_error(tmp_path):
    log = SyncLog()
    with pytest.raises(SyncError, match="Unknown knowledge-engine domain"):
        sync_knowledge_engine(_AGENT_META_ROOT, tmp_path, _config(domain="not-a-real-domain"), log, dry_run=False)
    assert not (tmp_path / "knowledge").exists()
