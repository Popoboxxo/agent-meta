"""IC-18 no. 16 / AC-45 / AC-84: expected agent files derive from ActiveSet.

``sync._preview_expected_filenames`` (the expected-file set behind
``--cleanup-preview`` stale detection) must filter by ``ActiveSet.roles``
instead of the raw ``config["roles"]`` allowlist.

Only ``test_expected_files_follow_given_active_set`` fails on the old code; the
two p20 tests pass before and after because ``_should_skip_role`` already applies
the activation gates (they document the contract).
"""
from __future__ import annotations

import dataclasses
import json
import shutil
import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
if str(_REPO_ROOT / "scripts") not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))

import sync  # noqa: E402
from lib.active_set import compute_active_set  # noqa: E402
from lib.agent_sync import _resolve_sync_targets  # noqa: E402
from lib.config import build_variables, load_config  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.providers import load_providers_config  # noqa: E402

_FIXTURES = _REPO_ROOT / "tests" / "fixtures" / "active-set"


def _project(tmp_path: Path, name: str) -> Path:
    (tmp_path / ".meta-config").mkdir()
    dest = tmp_path / ".meta-config" / "project.yaml"
    shutil.copyfile(_FIXTURES / name / ".meta-config" / "project.yaml", dest)
    with dest.open("a", encoding="utf-8") as fh:
        fh.write("project:\n  name: t\n  prefix: t\n")
    return tmp_path


def _expected(project_root: Path, active_set=None) -> set:
    config = load_config(project_root / ".meta-config" / "project.yaml")
    variables, _ = build_variables(config, _REPO_ROOT, project_root)
    provider_config = load_providers_config(_REPO_ROOT, config)
    log = SyncLog()
    pc, role_map, overrides, target_dir = _resolve_sync_targets(
        "Claude", provider_config, _REPO_ROOT, project_root, config, True, log)
    if active_set is None:
        active_set = compute_active_set(config, _REPO_ROOT, project_root)
    return sync._preview_expected_filenames(
        config, variables, "Claude", pc, role_map, overrides, target_dir,
        project_root, _REPO_ROOT, log, active_set)


def test_expected_files_follow_given_active_set(tmp_path):
    # Red before IC-18 no. 16: the raw allowlist ignored the ActiveSet argument.
    root = _project(tmp_path, "p20")
    config = load_config(root / ".meta-config" / "project.yaml")
    full = compute_active_set(config, _REPO_ROOT, root)
    assert "tester.md" in _expected(root, full)
    reduced = dataclasses.replace(full, roles=full.roles - {"tester"})
    assert "tester.md" not in _expected(root, reduced)


def test_gate_dropped_role_not_expected_on_p20(tmp_path):
    # AC-45: developer_tiers gate drops senior-developer in the p20 fixture.
    root = _project(tmp_path, "p20")
    expected = _expected(root)
    assert "senior-developer.md" not in expected
    assert "developer.md" in expected


def test_cleanup_preview_p20_flags_gate_dropped_role_as_stale(tmp_path):
    # End to end: a leftover senior-developer.md is stale, not expected.
    root = _project(tmp_path, "p20")
    sync_py = str(_REPO_ROOT / "scripts" / "sync.py")
    first = subprocess.run([sys.executable, sync_py], cwd=root, capture_output=True, text=True)
    assert first.returncode == 0, first.stderr
    agents = root / ".claude" / "agents"
    shutil.copyfile(agents / "developer.md", agents / "senior-developer.md")
    result = subprocess.run(
        [sys.executable, sync_py, "--cleanup-preview"], cwd=root, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    stale = {Path(e["path"]).name for p in payload["providers"] for e in p["stale"]}
    foreign = {Path(e["path"]).name for p in payload["providers"] for e in p["foreign"]}
    assert "senior-developer.md" in (stale | foreign)
    assert "developer.md" not in stale
