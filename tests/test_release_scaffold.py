"""Scaffold docs/RELEASE_PROCESS.md from the distribution template when
release.distribution is set; no-op when the release section is absent; a refresh
replaces only the managed block, preserving project additions below (#452)."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402
from lib.release_scaffold import TARGET, scaffold_release_process  # noqa: E402


def _config(**release):
    return {"release": release} if release else {}


_VARIABLES = {"PROJECT_NAME": "MyComponent"}


def test_hacs_distribution_renders_managed_doc(tmp_path):
    log = SyncLog()
    cfg = _config(distribution="hacs",
                  version_file="custom_components/mycomponent/manifest.json")
    scaffold_release_process(REPO_ROOT, tmp_path, cfg, _VARIABLES, log, dry_run=False)

    target = tmp_path / TARGET
    assert target.is_file()
    content = target.read_text(encoding="utf-8")
    assert "<!-- agent-meta:managed-begin -->" in content
    assert "<!-- agent-meta:managed-end -->" in content
    assert "MyComponent" in content
    assert "custom_components/mycomponent/manifest.json" in content
    # No raw placeholder leaked through substitution.
    assert "{{" not in content


def test_no_release_section_is_noop(tmp_path):
    log = SyncLog()
    scaffold_release_process(REPO_ROOT, tmp_path, _config(), _VARIABLES, log, dry_run=False)
    assert not (tmp_path / TARGET).exists()


def test_distribution_without_template_is_noop(tmp_path):
    log = SyncLog()
    cfg = _config(distribution="does-not-exist")
    scaffold_release_process(REPO_ROOT, tmp_path, cfg, _VARIABLES, log, dry_run=False)
    assert not (tmp_path / TARGET).exists()


def test_refresh_preserves_content_below_managed_end(tmp_path):
    log = SyncLog()
    cfg = _config(distribution="hacs", version_file="manifest.json")
    scaffold_release_process(REPO_ROOT, tmp_path, cfg, _VARIABLES, log, dry_run=False)

    target = tmp_path / TARGET
    custom = "\n\n## Projektspezifisch\n\nHand-written note that must survive.\n"
    target.write_text(target.read_text(encoding="utf-8") + custom, encoding="utf-8")

    # Re-run with a changed project name so the managed block actually differs.
    scaffold_release_process(REPO_ROOT, tmp_path, cfg, {"PROJECT_NAME": "Renamed"},
                             log, dry_run=False)
    content = target.read_text(encoding="utf-8")
    assert "Hand-written note that must survive." in content
    assert "Renamed" in content  # managed block refreshed
