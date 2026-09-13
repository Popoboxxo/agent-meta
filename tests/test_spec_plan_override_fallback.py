"""external-system-override.enabled=true skips every KE write path and the
file-index fallback takes over (R2b/D8)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.knowledge import sync_knowledge_engine  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.spec_plan_scaffold import scaffold_spec_plan_dirs  # noqa: E402

_KE = {"knowledge-engine": {"enabled": True, "domain": "internal-docs", "bundle-path": "knowledge"}}
_INDEX = {"index": {"mode": "knowledge-engine", "fallback-index": "docs/INDEX.md"}}
_OVERRIDE = {"external-system-override": {"enabled": True, "system": "jira", "note": "external PM"}}


def test_override_skips_all_ke_writes(tmp_path):
    log = SyncLog()
    config = {**_KE, "spec-plan-workflow": {"enabled": True, **_INDEX, **_OVERRIDE}}
    sync_knowledge_engine(REPO_ROOT, tmp_path, config, log, dry_run=False)
    assert not (tmp_path / "knowledge").exists()
    assert any("external-system-override" in entry for entry in log.skipped)


def test_without_override_ke_writes(tmp_path):
    log = SyncLog()
    config = {**_KE, "spec-plan-workflow": {"enabled": True, **_INDEX}}
    sync_knowledge_engine(REPO_ROOT, tmp_path, config, log, dry_run=False)
    assert (tmp_path / "knowledge" / "wiki" / "index.md").exists()


def test_override_end_to_end_uses_file_index_fallback(tmp_path):
    log = SyncLog()
    config = {**_KE, "spec-plan-workflow": {"enabled": True, **_INDEX, **_OVERRIDE}}
    sync_knowledge_engine(REPO_ROOT, tmp_path, config, log, dry_run=False)
    scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, config, log, dry_run=False)
    assert not (tmp_path / "knowledge").exists()
    assert (tmp_path / "docs" / "INDEX.md").is_file()
