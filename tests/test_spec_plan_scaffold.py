"""Sync scaffolds the neutral spec/plan/spike paths when the master switch is
on, and nothing when it is off; the index router picks the file-index
fallback for override/KE-off (R1/D8)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402
from lib.spec_plan_scaffold import resolve_index_mode, scaffold_spec_plan_dirs  # noqa: E402


def _config(enabled, knowledge_engine=True, **sp_extra):
    block = {"enabled": enabled, "paths": {
        "specs": "docs/specs", "plans": "docs/plans", "spikes": "docs/spikes"}}
    block.update(sp_extra)
    return {
        "spec-plan-workflow": block,
        "knowledge-engine": {"enabled": knowledge_engine},
    }


def test_enabled_scaffolds_all_paths(tmp_path):
    log = SyncLog()
    scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, _config(True), log, dry_run=False)
    for sub in ("docs/specs", "docs/plans", "docs/spikes"):
        assert (tmp_path / sub / ".gitkeep").is_file(), f"missing {sub}/.gitkeep"


def test_disabled_scaffolds_nothing(tmp_path):
    log = SyncLog()
    scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, _config(False), log, dry_run=False)
    assert not (tmp_path / "docs" / "specs").exists()


def test_dry_run_scaffolds_nothing(tmp_path):
    log = SyncLog()
    scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, _config(True), log, dry_run=True)
    assert not (tmp_path / "docs" / "specs").exists()


def test_index_mode_defaults_to_knowledge_engine():
    cfg = _config(True, index={"mode": "knowledge-engine", "fallback-index": "docs/INDEX.md"})
    assert resolve_index_mode(cfg) == ("knowledge-engine", "docs/INDEX.md")


def test_override_forces_file_index():
    cfg = _config(True, index={"mode": "knowledge-engine", "fallback-index": "docs/INDEX.md"},
                  **{"external-system-override": {"enabled": True}})
    assert resolve_index_mode(cfg) == ("file-index", "docs/INDEX.md")


def test_ke_off_forces_file_index():
    cfg = _config(True, knowledge_engine=False,
                  index={"mode": "knowledge-engine", "fallback-index": "docs/INDEX.md"})
    assert resolve_index_mode(cfg) == ("file-index", "docs/INDEX.md")


def test_file_index_fallback_written(tmp_path):
    log = SyncLog()
    cfg = _config(True, knowledge_engine=False,
                  index={"mode": "file-index", "fallback-index": "docs/INDEX.md"})
    scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, cfg, log, dry_run=False)
    assert (tmp_path / "docs" / "INDEX.md").is_file()


def test_explicit_off_is_not_overridden():
    cfg = _config(True, knowledge_engine=False,
                  index={"mode": "off", "fallback-index": "docs/INDEX.md"},
                  **{"external-system-override": {"enabled": True}})
    assert resolve_index_mode(cfg) == ("off", "docs/INDEX.md")


def test_off_mode_writes_no_index(tmp_path):
    log = SyncLog()
    cfg = _config(True, knowledge_engine=False,
                  index={"mode": "off", "fallback-index": "docs/INDEX.md"},
                  **{"external-system-override": {"enabled": True}})
    scaffold_spec_plan_dirs(REPO_ROOT, tmp_path, cfg, log, dry_run=False)
    assert not (tmp_path / "docs" / "INDEX.md").exists()
    for sub in ("docs/specs", "docs/plans", "docs/spikes"):
        assert (tmp_path / sub / ".gitkeep").is_file(), f"missing {sub}/.gitkeep"
