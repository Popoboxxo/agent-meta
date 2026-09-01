"""Regression tests for scripts/lib/hooks.py::sync_hook_lib() (issue #601).

Deploys hooks/1-generic/lib/*.sh (the shared helper functions individual
hook scripts source, see hooks/1-generic/lib/hook_common.sh) to
<hooks_dir>/lib/ the same way sync_release_gates() deploys release-gates/
scripts: always-copy, .agent-meta-managed-tracked, project-owned files in
lib/ untouched.

Run: python -m pytest tests/test_hook_lib_sync.py -v
"""

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.hooks import sync_hook_lib  # noqa: E402
from lib.log import SyncLog  # noqa: E402


@pytest.fixture
def agent_meta_root(tmp_path):
    root = tmp_path / "agent-meta"
    lib_dir = root / "hooks" / "1-generic" / "lib"
    lib_dir.mkdir(parents=True)
    (lib_dir / "hook_common.sh").write_text(
        "#!/bin/bash\n# lib: hook_common\nfoo() { echo bar; }\n", encoding="utf-8"
    )
    return root


@pytest.fixture
def project_root(tmp_path):
    p = tmp_path / "project"
    p.mkdir()
    return p


def _sync(agent_meta_root, project_root):
    log = SyncLog()
    sync_hook_lib(agent_meta_root, project_root, {"platforms": []}, log, dry_run=False)
    return log


def test_deploys_lib_file_to_hooks_lib_dir(agent_meta_root, project_root):
    _sync(agent_meta_root, project_root)
    deployed = project_root / ".claude" / "hooks" / "lib" / "hook_common.sh"
    assert deployed.exists()
    assert "foo()" in deployed.read_text(encoding="utf-8")


def test_writes_agent_meta_managed_index(agent_meta_root, project_root):
    _sync(agent_meta_root, project_root)
    managed = project_root / ".claude" / "hooks" / "lib" / ".agent-meta-managed"
    assert managed.exists()
    assert managed.read_text(encoding="utf-8").strip() == "hook_common.sh"


def test_removes_stale_lib_file_no_longer_shipped(agent_meta_root, project_root):
    _sync(agent_meta_root, project_root)
    (agent_meta_root / "hooks" / "1-generic" / "lib" / "hook_common.sh").unlink()
    _sync(agent_meta_root, project_root)
    deployed = project_root / ".claude" / "hooks" / "lib" / "hook_common.sh"
    assert not deployed.exists()


def test_never_touches_project_owned_lib_file(agent_meta_root, project_root):
    _sync(agent_meta_root, project_root)
    project_owned = project_root / ".claude" / "hooks" / "lib" / "my-own-helper.sh"
    project_owned.write_text("#!/bin/bash\necho mine\n", encoding="utf-8")

    _sync(agent_meta_root, project_root)
    assert project_owned.exists()
    assert "mine" in project_owned.read_text(encoding="utf-8")


def test_dry_run_makes_no_filesystem_changes(agent_meta_root, project_root):
    log = SyncLog()
    sync_hook_lib(agent_meta_root, project_root, {"platforms": []}, log, dry_run=True)
    deployed = project_root / ".claude" / "hooks" / "lib" / "hook_common.sh"
    assert not deployed.exists()
