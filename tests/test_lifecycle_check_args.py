"""Regression tests for scripts/lifecycle_check.py argument and config parsing.

Issue #475: the script runs inside git hooks, where an unhandled traceback
surfaces as a raw hook failure. Two inputs crashed it:

1. `--project-root` as the last argument -> `args[idx + 1]` IndexError.
2. A mapping- or nested-shaped `ai-providers:` in project.yaml -> the loop
   passed an unhashable dict into `_PROVIDER_PENDING_FILES.get()` -> TypeError.

Both must now fail (or degrade) with a readable message instead.
"""

import subprocess
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPT = _REPO_ROOT / "scripts" / "lifecycle_check.py"

_CONFIG = """\
lifecycle-triggers:
  on-config-change:
  - agent: agent-meta-manager
    task: "Re-run sync.py."
ai-providers:
{providers}
"""


def _run(args, cwd):
    return subprocess.run(
        [sys.executable, str(_SCRIPT), *args],
        capture_output=True, text=True, cwd=str(cwd),
    )


def _project(tmp_path, providers_block):
    meta = tmp_path / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "project.yaml").write_text(
        _CONFIG.format(providers=providers_block), encoding="utf-8"
    )
    return tmp_path


def test_project_root_without_value_exits_cleanly(tmp_path):
    result = _run(["on-config-change", "--project-root"], tmp_path)
    assert result.returncode == 1
    assert "requires a path" in result.stderr
    assert "Traceback" not in result.stderr


def test_nested_provider_entries_do_not_crash(tmp_path):
    # A dict entry is unhashable -- .get() used to raise TypeError.
    root = _project(tmp_path, "- provider: claude\n")
    result = _run(["on-config-change", "--project-root", str(root)], tmp_path)
    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    assert "non-string provider" in result.stderr


def test_mapping_shaped_providers_use_keys(tmp_path):
    root = _project(tmp_path, "  claude:\n    enabled: true\n")
    result = _run(["on-config-change", "--project-root", str(root)], tmp_path)
    assert result.returncode == 0
    assert "Traceback" not in result.stderr
    # 'claude' is not a known provider key -> falls back to .claude/pending-tasks.md
    assert (root / ".claude" / "pending-tasks.md").exists()


def test_scalar_providers_are_rejected_without_traceback(tmp_path):
    root = _project(tmp_path, "42\n")
    result = _run(["on-config-change", "--project-root", str(root)], tmp_path)
    assert result.returncode == 0
    assert "Traceback" not in result.stderr


def test_valid_provider_list_still_writes_pending_tasks(tmp_path):
    root = _project(tmp_path, "- Claude\n")
    result = _run(["on-config-change", "--project-root", str(root)], tmp_path)
    assert result.returncode == 0, result.stderr
    assert (root / ".claude" / "pending-tasks.md").exists()
