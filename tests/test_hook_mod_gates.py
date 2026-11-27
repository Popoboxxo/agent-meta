"""Direct, CLI and deployment tests for the extracted gate-hook modules.

Issue #1238c2 moves the artifact-freshness parser and the visualization event
logger into flat modules next to ``hook_common.sh``.  The release gate keeps its
pass/fail exit codes and Python-missing self-skip; the logger remains fail-open.
"""
from __future__ import annotations

import ast
import contextlib
import importlib.util
import inspect
import io
import json
import os
import re
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import get_type_hints

import pytest

from tests.timeouts import SCRIPT_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOKS_DIR = _REPO_ROOT / "hooks" / "1-generic"
_LIB_DIR = _HOOKS_DIR / "lib"
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.hook_plugins import sync_hook_lib, sync_release_gates  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_BASH = shutil.which("bash") or "bash"
_MODULES = ("hook_gate_artifact_freshness.py", "hook_gate_viz_log.py")
_INLINE_PY_RX = re.compile(
    r"""<<-?\s*["']?PY(EOF)?["']?|(?:python3?|["']?\$_PY["']?)\s+-(?:\s|c\s)"""
)
_INLINE_PY_ALLOWLIST = {
    "auto-github-release.sh:47": (
        '"$_PY" -c',
        "Outside the #1238 hook-extraction scope; this is the existing thin "
        "bridge that imports lib.auto_github_release.main.",
    ),
    "repo-containment-impl.sh:335": (
        '"$_PY" -c',
        "Trivial one-line os.path.realpath bridge with no control flow; "
        "extracting it would add a module dependency to the security hot path.",
    ),
}


def _load_module(filename: str):
    path = _LIB_DIR / filename
    spec = importlib.util.spec_from_file_location(path.stem, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _call(module, argv, stdin: str = ""):
    stdout, stderr = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(stdout), contextlib.redirect_stderr(stderr):
        rc = module.main(argv, stdin)
    return rc, stdout.getvalue(), stderr.getvalue()


def _clean_env(**extra) -> dict:
    env = {key: value for key, value in os.environ.items()
           if not key.startswith("AGENT_META_")}
    for key in ("CLAUDE_PROJECT_DIR", "AGENT_NAME", "AGENT_PROVIDER",
                "PRE_RELEASE_GATE_ENABLED", "PROJECT_ROOT"):
        env.pop(key, None)
    env.update(extra)
    return env


def _git(repo: Path, *args: str, timestamp: int | None = None) -> None:
    env = dict(os.environ)
    if timestamp is not None:
        date = f"@{timestamp} +0000"
        env["GIT_AUTHOR_DATE"] = date
        env["GIT_COMMITTER_DATE"] = date
    subprocess.run(
        ["git", *args], cwd=str(repo), env=env, capture_output=True, text=True,
        check=True, timeout=SCRIPT_TIMEOUT,
    )


@pytest.fixture
def repo(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    _git(root, "config", "user.email", "test@example.com")
    _git(root, "config", "user.name", "Test")
    return root


def _write_artifact_config(repo: Path, body: str) -> Path:
    meta = repo / ".meta-config"
    meta.mkdir(exist_ok=True)
    path = meta / "generated-artifacts.yaml"
    path.write_text(body, encoding="utf-8")
    return path


def _deploy_hooks(project_root: Path) -> Path:
    project_root.mkdir(parents=True, exist_ok=True)
    provider = "runtime"
    provider_config = {
        provider: {
            "hooks_dir": ".runtime/hooks",
            "has_hooks": True,
            "hook_protocol": "claude-code-json",
        }
    }
    sync_hook_lib(
        _REPO_ROOT, project_root, {"platforms": []}, SyncLog(), dry_run=False,
        provider=provider, provider_config=provider_config,
    )
    sync_release_gates(
        _REPO_ROOT, project_root, {"platforms": []}, SyncLog(), dry_run=False,
        provider=provider, provider_config=provider_config,
        release_gates_resolved={"artifact-freshness": True},
    )
    hooks = project_root / ".runtime" / "hooks"
    shutil.copy2(_HOOKS_DIR / "viz-log.sh", hooks / "viz-log.sh")
    return hooks


@pytest.mark.parametrize("filename", _MODULES)
def test_module_contract_python39_stdlib_and_provider_neutral(filename):
    module = _load_module(filename)
    signature = inspect.signature(module.main)
    assert list(signature.parameters) == ["argv", "stdin"]
    hints = get_type_hints(module.main)
    assert hints["argv"] == list[str]
    assert hints["stdin"] is str
    assert hints["return"] is int

    path = _LIB_DIR / filename
    assert path.parent == _LIB_DIR
    source = path.read_text(encoding="utf-8")
    tree = ast.parse(source, filename=filename, feature_version=(3, 9))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= {
        "__future__", "datetime", "glob", "json", "os", "subprocess", "sys",
    }
    for provider_name in ("Claude", "Gemini", "Codex", "Copilot", "OpenCode"):
        assert provider_name not in source
    assert not re.search(
        r"ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY",
        source,
    )


def test_artifact_freshness_parser_globs_quotes_and_missing_source(
    repo, monkeypatch
):
    (repo / "src").mkdir()
    (repo / "dist").mkdir()
    (repo / "src" / "schema.py").write_text("source", encoding="utf-8")
    (repo / "dist" / "schema.json").write_text("generated", encoding="utf-8")
    config = _write_artifact_config(
        repo,
        "# ignored comment\n"
        "other: ignored\n"
        "artifacts:\n"
        "  - source: \"src/*.py\"\n"
        "    generated: 'dist/schema.json'\n"
        "  - source: missing.txt\n"
        "    generated: missing.json\n",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "artifacts", timestamp=100)
    monkeypatch.chdir(repo)

    result = _call(
        _load_module("hook_gate_artifact_freshness.py"),
        [str(config), "artifact-freshness"],
        "stdin is ignored",
    )
    assert result == (
        0,
        "[SKIP] artifact-freshness: source not found: missing.txt\n"
        "[INFO] artifact-freshness: checked 1 artifact pair(s), all fresh\n",
        "",
    )


def test_artifact_freshness_reports_missing_and_stale_generated(repo, monkeypatch):
    (repo / "source.txt").write_text("v1", encoding="utf-8")
    (repo / "generated.txt").write_text("v1", encoding="utf-8")
    (repo / "missing-source.txt").write_text("v1", encoding="utf-8")
    config = _write_artifact_config(
        repo,
        "artifacts:\n"
        "  - source: source.txt\n"
        "    generated: generated.txt\n"
        "  - source: missing-source.txt\n"
        "    generated: absent.txt\n",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "v1", timestamp=100)
    (repo / "source.txt").write_text("v2", encoding="utf-8")
    _git(repo, "add", "source.txt")
    _git(repo, "commit", "-q", "-m", "v2", timestamp=200)
    monkeypatch.chdir(repo)

    result = _call(
        _load_module("hook_gate_artifact_freshness.py"),
        [str(config), "artifact-freshness"],
        "",
    )
    assert result == (
        1,
        "[FAIL] artifact-freshness: generated.txt is older than its source "
        "source.txt — rebuild required\n"
        "[FAIL] artifact-freshness: absent.txt (from missing-source.txt) — "
        "generated artifact missing\n",
        "",
    )


def test_artifact_freshness_untracked_generated_uses_filesystem_mtime(
    repo, monkeypatch
):
    (repo / "source.txt").write_text("v1", encoding="utf-8")
    config = _write_artifact_config(
        repo,
        "artifacts:\n  - source: source.txt\n    generated: generated.txt\n",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "source", timestamp=100)
    generated = repo / "generated.txt"
    generated.write_text("generated", encoding="utf-8")
    os.utime(generated, (300, 300))
    monkeypatch.chdir(repo)

    assert _call(
        _load_module("hook_gate_artifact_freshness.py"),
        [str(config), "artifact-freshness"], "",
    ) == (
        0,
        "[INFO] artifact-freshness: checked 1 artifact pair(s), all fresh\n",
        "",
    )


def test_artifact_freshness_prefers_git_history_over_filesystem_mtime(
    repo, monkeypatch
):
    (repo / "source.txt").write_text("v1", encoding="utf-8")
    (repo / "generated.txt").write_text("v1", encoding="utf-8")
    config = _write_artifact_config(
        repo,
        "artifacts:\n  - source: source.txt\n    generated: generated.txt\n",
    )
    _git(repo, "add", "-A")
    _git(repo, "commit", "-q", "-m", "v1", timestamp=100)
    os.utime(repo / "source.txt", (999, 999))
    monkeypatch.chdir(repo)

    assert _call(
        _load_module("hook_gate_artifact_freshness.py"),
        [str(config), "artifact-freshness"], "",
    )[0] == 0


def test_viz_log_builds_fixed_event_and_truncates_command(tmp_path, monkeypatch):
    module = _load_module("hook_gate_viz_log.py")

    class FixedDateTime:
        @classmethod
        def now(cls, tz):
            assert tz is timezone.utc
            return datetime(2026, 11, 25, 12, 30, tzinfo=timezone.utc)

    monkeypatch.setattr(module, "datetime", FixedDateTime)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("AGENT_NAME", "tester")
    monkeypatch.setenv("AGENT_PROVIDER", "runtime")
    command = "printf 'ä'; " + "x" * 200

    assert _call(module, [], json.dumps({
        "tool_name": "Bash", "tool_input": {"command": command},
    })) == (0, "", "")
    raw = (tmp_path / ".meta-viz" / "events.jsonl").read_text(encoding="utf-8")
    assert "ä" in raw
    assert json.loads(raw) == {
        "ts": "2026-11-25T12:30:00+00:00",
        "event": "tool_call",
        "agent": "tester",
        "tool": "Bash",
        "provider": "runtime",
        "payload": {"command_preview": command[:120]},
    }


def test_viz_log_appends_and_defaults_missing_fields(tmp_path, monkeypatch):
    module = _load_module("hook_gate_viz_log.py")
    monkeypatch.chdir(tmp_path)
    monkeypatch.delenv("AGENT_NAME", raising=False)
    monkeypatch.delenv("AGENT_PROVIDER", raising=False)

    assert _call(module, [], '{"tool_name":"Read"}') == (0, "", "")
    assert _call(module, [], '{"tool_name":"Bash","tool_input":{}}') == (0, "", "")
    events = [
        json.loads(line)
        for line in (tmp_path / ".meta-viz" / "events.jsonl")
        .read_text(encoding="utf-8").splitlines()
    ]
    assert len(events) == 2
    assert events[0] == {
        "ts": events[0]["ts"], "event": "tool_call", "agent": "system",
        "tool": "Read", "provider": "unknown",
    }
    assert events[1] == {
        "ts": events[1]["ts"], "event": "tool_call", "agent": "system",
        "tool": "Bash", "provider": "unknown",
    }


@pytest.mark.parametrize("payload", ["", "{broken", "null", "[]"])
def test_viz_log_malformed_payload_fails_open(tmp_path, payload):
    assert _call(_load_module("hook_gate_viz_log.py"), [], payload) == (0, "", "")
    assert not (tmp_path / ".meta-viz").exists()


def test_viz_log_cli_reads_stdin_and_exits_zero(tmp_path):
    result = subprocess.run(
        [sys.executable, str(_LIB_DIR / "hook_gate_viz_log.py")],
        input='{"tool_name":"Read","tool_input":{}}',
        capture_output=True, text=True, cwd=str(tmp_path),
        env=_clean_env(AGENT_NAME="tester", AGENT_PROVIDER="runtime"),
        timeout=SCRIPT_TIMEOUT,
    )
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    event = json.loads(
        (tmp_path / ".meta-viz" / "events.jsonl").read_text(encoding="utf-8")
    )
    assert event["agent"] == "tester"
    assert event["provider"] == "runtime"


def test_hooks_without_python_keep_existing_fail_open_behavior(repo, tmp_path):
    minimal_bin = tmp_path / "bin"
    minimal_bin.mkdir()
    dirname = shutil.which("dirname")
    if dirname:
        (minimal_bin / "dirname").symlink_to(dirname)
    _write_artifact_config(
        repo,
        "artifacts:\n  - source: source.txt\n    generated: generated.txt\n",
    )
    env = _clean_env(
        PATH=str(minimal_bin), PROJECT_ROOT=str(repo),
        PRE_RELEASE_GATE_ENABLED="true",
    )

    artifact = subprocess.run(
        [_BASH, str(_HOOKS_DIR / "release-gates" / "artifact-freshness.sh")],
        capture_output=True, text=True, cwd=str(repo), env=env,
        timeout=SCRIPT_TIMEOUT,
    )
    assert artifact.returncode == 0, artifact.stderr
    assert "python3 not available" in artifact.stdout

    viz = subprocess.run(
        [_BASH, str(_HOOKS_DIR / "viz-log.sh")], input='{"tool_name":"Read"}',
        capture_output=True, text=True, cwd=str(repo), env=env,
        timeout=SCRIPT_TIMEOUT,
    )
    assert (viz.returncode, viz.stdout, viz.stderr) == (0, "", "")
    assert not (repo / ".meta-viz").exists()


def test_deployed_artifact_freshness_resolves_sibling_lib_module(tmp_path):
    project = tmp_path / "consumer"
    hooks = _deploy_hooks(project)
    gate = hooks / "release-gates" / "artifact-freshness.sh"
    assert (hooks / "lib" / "hook_gate_artifact_freshness.py").is_file()
    assert not (gate.parent / "hook_gate_artifact_freshness.py").exists()

    _git(project, "init", "-q")
    _git(project, "config", "user.email", "test@example.com")
    _git(project, "config", "user.name", "Test")
    (project / "source.txt").write_text("v1", encoding="utf-8")
    (project / "generated.txt").write_text("v1", encoding="utf-8")
    _write_artifact_config(
        project,
        "artifacts:\n  - source: source.txt\n    generated: generated.txt\n",
    )
    _git(project, "add", "-A")
    _git(project, "commit", "-q", "-m", "v1", timestamp=100)

    result = subprocess.run(
        [_BASH, str(gate)], capture_output=True, text=True, cwd=str(tmp_path),
        env=_clean_env(PROJECT_ROOT=str(project), PRE_RELEASE_GATE_ENABLED="true"),
        timeout=SCRIPT_TIMEOUT,
    )
    assert result.returncode == 0, result.stderr
    assert result.stderr == ""
    assert "[INFO] artifact-freshness: checked 1 artifact pair(s), all fresh" in result.stdout


def test_deployed_viz_log_resolves_sibling_lib_module(tmp_path):
    project = tmp_path / "consumer"
    hooks = _deploy_hooks(project)
    hook = hooks / "viz-log.sh"
    assert (hooks / "lib" / "hook_gate_viz_log.py").is_file()

    result = subprocess.run(
        [_BASH, str(hook)], input='{"tool_name":"Read","tool_input":{}}',
        capture_output=True, text=True, cwd=str(project),
        env=_clean_env(AGENT_NAME="tester", AGENT_PROVIDER="runtime"),
        timeout=SCRIPT_TIMEOUT,
    )
    assert (result.returncode, result.stdout, result.stderr) == (0, "", "")
    event = json.loads(
        (project / ".meta-viz" / "events.jsonl").read_text(encoding="utf-8")
    )
    assert event["tool"] == "Read"
    assert event["agent"] == "tester"


def test_gate_hook_versions_changelogs_and_module_paths():
    artifact = (
        _HOOKS_DIR / "release-gates" / "artifact-freshness.sh"
    ).read_text(encoding="utf-8")
    viz = (_HOOKS_DIR / "viz-log.sh").read_text(encoding="utf-8")
    for source in (artifact, viz):
        assert "# version: 1.2.0" in source
        assert "#1238c2" in source
    assert "$HOOK_LIB_DIR/hook_gate_artifact_freshness.py" in artifact
    assert "$HOOK_LIB_DIR/hook_gate_viz_log.py" in viz

    for source in (artifact, viz):
        for lineno, line in enumerate(source.splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            assert not _INLINE_PY_RX.search(line), f"inline Python at line {lineno}"


def test_inline_py_allowlist():
    found = {}
    sources = sorted(_HOOKS_DIR.glob("*.sh")) + [_LIB_DIR / "hook_common.sh"]
    for path in sources:
        for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            if line.lstrip().startswith("#"):
                continue
            if _INLINE_PY_RX.search(line):
                found[f"{path.name}:{lineno}"] = line.strip()

    assert set(found) == set(_INLINE_PY_ALLOWLIST)
    for location, (fragment, reason) in _INLINE_PY_ALLOWLIST.items():
        assert reason.strip()
        assert fragment in found[location]
