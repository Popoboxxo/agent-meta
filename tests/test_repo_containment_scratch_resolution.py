"""T24 (D1): the repo-containment hook resolves its scratch sink path from the
artifact-locations matrix instead of reading only the legacy config key.

Precedence (plan §5 T24 / §6.4 D1):

    ARTIFACT_SCRATCH_DIR env
      -> classes[scratch].path from .meta-config/artifact-locations.resolved.json
      -> repo_containment.tmp-sink.path
      -> .tmp

The ``sink_enabled`` switch and the lexical rules (``path_error`` in the hook)
are deliberately unchanged: this is a path-source swap only. The parity suite
(``tests/test_tmp_sink_path_parity.py``) keeps pinning the lexical rules against
``scripts/lib/repo_containment.py::tmp_sink_path_error``.

Run: python -m pytest tests/test_repo_containment_scratch_resolution.py -q
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOK = _REPO_ROOT / "hooks" / "1-generic" / "repo-containment.sh"
_BASH = shutil.which("bash") or "bash"
_TIMEOUT = 30

_MARKER = "REPO_CONTAINMENT"


def _env(extra: dict | None = None) -> dict:
    """Deterministic hook env: no inherited project root, no inherited sink."""
    env = dict(os.environ)
    env.pop("CLAUDE_PROJECT_DIR", None)
    env.pop("ARTIFACT_SCRATCH_DIR", None)
    if extra:
        env.update(extra)
    return env


def _project(root: Path, sink_path: str = ".tmp", sink_enabled: bool = True) -> Path:
    """Create a project root with an explicit legacy tmp-sink configuration."""
    meta = root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "project.yaml").write_text(
        "repo_containment:\n"
        "  enabled: true\n"
        "  tmp-sink:\n"
        f"    enabled: {'true' if sink_enabled else 'false'}\n"
        f'    path: "{sink_path}"\n',
        encoding="utf-8",
    )
    return root


def _resolved(root: Path, scratch_path: str | None = None, *, raw: str | None = None) -> None:
    """Write the resolved matrix data file with an optional scratch class."""
    meta = root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    target = meta / "artifact-locations.resolved.json"
    if raw is not None:
        target.write_text(raw, encoding="utf-8")
        return
    data: dict = {
        "schema_version": "1",
        "preset": "default",
        "enabled": True,
        "strict": False,
        "classes": {},
        "legacy": [],
        "unmanaged": [],
    }
    if scratch_path is not None:
        data["classes"]["scratch"] = {
            "mode": "ephemeral",
            "source": "project",
            "exists": True,
            "kinds": [],
            "subdir": "",
            "field_sources": {"path": "project"},
            "file_count": 0,
            "newest": None,
            "legacy_hits": [],
            "violations": [],
            "path": scratch_path,
        }
    target.write_text(json.dumps(data), encoding="utf-8")


def _run(root: Path, rel_target: str, env: dict | None = None) -> subprocess.CompletedProcess:
    """Invoke the real hook; the payload cwd anchors the repo root."""
    payload = {
        "tool_name": "Write",
        "tool_input": {"file_path": str(root / rel_target)},
        "cwd": str(root),
    }
    return subprocess.run(
        [_BASH, str(_HOOK)],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        cwd=str(root.parent),
        env=env if env is not None else _env(),
        timeout=_TIMEOUT,
    )


def _allowed_line(stderr: str) -> str:
    """The sink advertised on an outside-block message (AC-18 style)."""
    lines = [line for line in stderr.splitlines() if "allowed:" in line]
    assert lines, stderr
    return lines[0]


def test_hook_uses_resolved_scratch_path(tmp_path):
    """The data file is the single source even when project.yaml still says .tmp."""
    root = _project(tmp_path / "project")
    _resolved(root, "alt-sink")

    # The effective sink advertised on a block names the resolved path.
    outside = _run(root, "../outside.py")
    assert outside.returncode == 2, outside.stderr
    assert f"{root}/alt-sink" in outside.stderr
    assert f"under {root}/.tmp" not in _allowed_line(outside.stderr)

    # The resolved sink itself is writable.
    assert _run(root, "alt-sink/x").returncode == 0


def test_hook_falls_back_to_legacy_key_without_datafile(tmp_path):
    """No data file -> legacy key is used, prison stays closed, warning emitted."""
    root = _project(tmp_path / "project", sink_path="legacy-sink")
    # Deliberately no artifact-locations.resolved.json.

    assert _run(root, "legacy-sink/x").returncode == 0

    outside = _run(root, "../outside.py")
    assert outside.returncode == 2  # fails closed: never opens the jail
    assert f"under {root}/legacy-sink" in _allowed_line(outside.stderr)
    assert "artifact-locations.resolved.json" in outside.stderr
    assert "warning" in outside.stderr.lower()


def test_disabled_sink_still_blocks(tmp_path):
    """sink_enabled stays with repo_containment; scratch has no enabled flag."""
    root = _project(tmp_path / "project", sink_path=".tmp", sink_enabled=False)
    _resolved(root, "alt-sink")

    blocked = _run(root, "alt-sink/x")
    assert blocked.returncode == 2
    assert "DISABLED tmp-sink" in blocked.stderr
    # .tmp is no longer the sink, so it is a normal (allowed) in-root path.
    assert _run(root, ".tmp/x").returncode == 0


def test_exported_variable_wins(tmp_path):
    """ARTIFACT_SCRATCH_DIR outranks the resolved matrix and the legacy key."""
    root = _project(tmp_path / "project", sink_path=".tmp")
    _resolved(root, "alt-sink")

    outside = _run(root, "../outside.py", env=_env({"ARTIFACT_SCRATCH_DIR": "env-sink"}))
    assert outside.returncode == 2, outside.stderr
    assert f"under {root}/env-sink" in _allowed_line(outside.stderr)
    assert f"under {root}/alt-sink" not in _allowed_line(outside.stderr)

    assert _run(root, "env-sink/x", env=_env({"ARTIFACT_SCRATCH_DIR": "env-sink"})).returncode == 0


def test_lexical_rules_are_unchanged(tmp_path):
    """Invalid scratch paths from any source fall back to .tmp (never widen)."""
    invalid = ["../x", "/abs/x", ""]
    for index, value in enumerate(invalid):
        root = _project(tmp_path / f"project-{index}", sink_path=".tmp")
        _resolved(root, value)
        outside = _run(root, "../outside.py")
        assert outside.returncode == 2, outside.stderr
        assert f"under {root}/.tmp" in _allowed_line(outside.stderr)

        env_root = _project(tmp_path / f"env-{index}", sink_path=".tmp")
        _resolved(env_root, "alt-sink")
        env_outside = _run(
            env_root, "../outside.py", env=_env({"ARTIFACT_SCRATCH_DIR": value})
        )
        assert env_outside.returncode == 2, env_outside.stderr
        # An unsafe env value is ignored; the next valid source (the data file)
        # is used. The unsafe path must never become an allowed sink.
        assert _allowed_line(env_outside.stderr).strip() == (
            f"allowed:   paths under {env_root} and under {env_root}/alt-sink"
        )


def test_block_message_names_matrix_key(tmp_path):
    """The repair hint names both configuration keys, not only the legacy one."""
    root = _project(tmp_path / "project", sink_path=".tmp", sink_enabled=False)
    _resolved(root, "alt-sink")

    blocked = _run(root, "alt-sink/x")
    assert blocked.returncode == 2
    assert "artifact-locations.classes.scratch.path" in blocked.stderr
    assert "repo_containment.tmp-sink.enabled" in blocked.stderr
