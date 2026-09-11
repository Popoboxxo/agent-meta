"""Regression test for issue #720 part A: nothing currently writes
agent-meta-version back into project.yaml after a successful sync, so the
documented version drifts behind the actually-deployed one."""
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import yaml

from lib.config import config_field_defaults, fill_defaults
from lib.log import SyncLog
from lib.sync_pipeline import sync_version_bookkeeping


def _agent_meta_root_with_version(tmp_path: Path, version: str) -> Path:
    root = tmp_path / "agent-meta"
    root.mkdir()
    (root / "VERSION").write_text(version + "\n", encoding="utf-8")
    return root


def test_stale_version_is_updated_on_disk(tmp_path):
    agent_meta_root = _agent_meta_root_with_version(tmp_path, "1.1.0")
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path = project_root / ".meta-config" / "project.yaml"
    config_path.parent.mkdir(parents=True)
    config_path.write_text(
        "agent-meta-version: '1.0.0'\nproject:\n  name: demo\n  prefix: dm\n  short: demo\n",
        encoding="utf-8",
    )
    config = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    log = SyncLog()

    sync_version_bookkeeping(agent_meta_root, project_root, config_path, config, log, dry_run=False)

    reloaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert reloaded["agent-meta-version"] == "1.1.0"
    assert config["agent-meta-version"] == "1.1.0"
    assert reloaded["project"]["name"] == "demo"  # unrelated keys survive


def test_matching_version_is_a_no_op(tmp_path):
    agent_meta_root = _agent_meta_root_with_version(tmp_path, "1.1.0")
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path = project_root / ".meta-config" / "project.yaml"
    config_path.parent.mkdir(parents=True)
    text = "agent-meta-version: '1.1.0'\nproject:\n  name: demo\n"
    config_path.write_text(text, encoding="utf-8")
    config = {"agent-meta-version": "1.1.0"}
    log = SyncLog()

    sync_version_bookkeeping(agent_meta_root, project_root, config_path, config, log, dry_run=False)

    assert config_path.read_text(encoding="utf-8") == text  # untouched, byte-identical


def test_dry_run_does_not_write(tmp_path):
    agent_meta_root = _agent_meta_root_with_version(tmp_path, "1.1.0")
    project_root = tmp_path / "project"
    project_root.mkdir()
    config_path = project_root / ".meta-config" / "project.yaml"
    config_path.parent.mkdir(parents=True)
    text = "agent-meta-version: '1.0.0'\n"
    config_path.write_text(text, encoding="utf-8")
    config = {"agent-meta-version": "1.0.0"}
    log = SyncLog()

    sync_version_bookkeeping(agent_meta_root, project_root, config_path, config, log, dry_run=True)

    assert config_path.read_text(encoding="utf-8") == text


def _version_file_content(root: Path) -> str:
    """Read the single source of truth — never hardcode a version literal."""
    return (root / "VERSION").read_text(encoding="utf-8").strip()


def test_default_version_comes_from_version_file():
    """Issue #731: the fill-defaults value must equal VERSION, not a literal."""
    repo_root = Path(__file__).resolve().parent.parent
    assert config_field_defaults(repo_root)["agent-meta-version"] == _version_file_content(repo_root)


def test_default_version_derives_from_supplied_root(tmp_path):
    agent_meta_root = _agent_meta_root_with_version(tmp_path, "9.9.9")
    expected = _version_file_content(agent_meta_root)
    assert config_field_defaults(agent_meta_root)["agent-meta-version"] == expected


def test_fill_defaults_writes_version_file_content(tmp_path):
    """The `--fill-defaults` write path must persist exactly VERSION."""
    repo_root = Path(__file__).resolve().parent.parent
    expected = _version_file_content(repo_root)
    config_path = tmp_path / "project.yaml"
    config_path.write_text(
        "project:\n  name: demo\n  prefix: dm\n  short: demo\n"
        "ai-providers:\n  - Claude\n",
        encoding="utf-8",
    )

    fill_defaults(config_path, repo_root, SyncLog(), dry_run=False)

    reloaded = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    assert reloaded["agent-meta-version"] == expected
