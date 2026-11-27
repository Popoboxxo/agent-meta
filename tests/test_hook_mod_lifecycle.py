"""Direct, CLI, deployment and hook-integration tests for the lifecycle-event
module (MB-2 of docs/plans/systemaudit-umsetzungsplan-2026-11-25.md).

``hooks/1-generic/lifecycle-check.sh`` used to detect git commands with
``grep -qE`` over the raw Bash command string. The detection now lives in
``hooks/1-generic/lib/hook_lifecycle_event.py`` and runs on the shared shell
tokenizer. These tests pin three things:

1. the classifier result per command (real events found, prose/consumers/
   comments/option values not),
2. the unchanged event semantics (release > version bump > merge precedence,
   the ``git describe`` bump heuristic, and "a plain commit raises nothing"),
3. the deployment contract: the module is shipped flat into ``hooks/lib``,
   the hook runs it, and a deployment without it still fails OPEN.
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
from pathlib import Path
from typing import get_type_hints

import pytest

from tests.timeouts import SCRIPT_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parent.parent
_HOOKS_DIR = _REPO_ROOT / "hooks" / "1-generic"
_LIB_DIR = _HOOKS_DIR / "lib"
_HOOK_PATH = _HOOKS_DIR / "lifecycle-check.sh"
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
_MODULE = "hook_lifecycle_event.py"
for _path in (_SCRIPTS_DIR, _LIB_DIR):
    if str(_path) not in sys.path:
        sys.path.insert(0, str(_path))

from lib.hook_plugins import sync_hook_lib  # noqa: E402
from lib.log import SyncLog  # noqa: E402

_BASH = shutil.which("bash") or "bash"

pytestmark = pytest.mark.skipif(
    sys.platform not in ("linux", "darwin"), reason="requires bash"
)

# Every event name the hook accepts (case arm in lifecycle-check.sh).
_EVENTS = {
    "none", "on-release", "on-merge", "on-commit",
    "on-version-bump-patch", "on-version-bump-minor", "on-version-bump-major",
}


def _load_module(filename: str = _MODULE):
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


def _git(*args, cwd: Path):
    return subprocess.run(
        ["git", *args], cwd=str(cwd), capture_output=True, text=True,
        check=True, timeout=SCRIPT_TIMEOUT,
    )


def _tagged_repo(root: Path, tag: str = "v1.0.0") -> Path:
    """A repo whose HEAD~1 carries <tag> (so the bump heuristic sees it)."""
    root.mkdir()
    _git("init", "-q", cwd=root)
    _git("config", "user.email", "test@example.com", cwd=root)
    _git("config", "user.name", "Test", cwd=root)
    (root / "f.txt").write_text("x", encoding="utf-8")
    _git("add", "f.txt", cwd=root)
    _git("commit", "-q", "-m", "init", cwd=root)
    _git("tag", "-a", tag, "-m", tag, cwd=root)
    (root / "f.txt").write_text("y", encoding="utf-8")
    _git("commit", "-q", "-am", "next", cwd=root)
    return root


def _project(root: Path, triggers: dict) -> Path:
    """A project whose lifecycle triggers write .claude/pending-tasks.md."""
    root.mkdir(parents=True, exist_ok=True)
    (root / "agent-meta.config.json").write_text(
        json.dumps({"ai-providers": ["Claude"], "lifecycle-triggers": triggers}),
        encoding="utf-8",
    )
    return root


def _run_hook(hook: Path, cwd: Path, command: str, env=None):
    payload = {
        "tool_name": "Bash",
        "tool_input": {"command": command},
        "tool_result": {"exit_code": 0},
    }
    return subprocess.run(
        [_BASH, str(hook)],
        input=json.dumps(payload),
        capture_output=True, text=True, cwd=str(cwd),
        env=env if env is not None else dict(os.environ),
        timeout=SCRIPT_TIMEOUT,
    )


def _pending(root: Path) -> str:
    path = root / ".claude" / "pending-tasks.md"
    return path.read_text(encoding="utf-8") if path.exists() else ""


# ---------------------------------------------------------------------------
# Module contract
# ---------------------------------------------------------------------------

def test_module_contract_python39_stdlib_and_provider_neutral():
    module = _load_module()
    signature = inspect.signature(module.main)
    assert list(signature.parameters) == ["argv", "stdin"]
    hints = get_type_hints(module.main)
    assert hints["argv"] == list[str]
    assert hints["stdin"] is str
    assert hints["return"] is int

    source = (_LIB_DIR / _MODULE).read_text(encoding="utf-8")
    tree = ast.parse(source, filename=_MODULE, feature_version=(3, 9))
    imports = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports <= {
        "__future__", "os", "re", "shlex", "subprocess", "sys",
        "hook_push_arg_parser", "hook_shell_resolver", "hook_shell_scan",
    }
    for provider_name in ("Claude", "Gemini", "Codex", "Copilot", "OpenCode"):
        assert provider_name not in source
    assert not re.search(
        r"ghp_[A-Za-z0-9]{20,}|AKIA[0-9A-Z]{16}|BEGIN [A-Z ]*PRIVATE KEY",
        source,
    )
    # The shared tokenizer, not a second one: the module imports the three
    # helper functions instead of carrying its own statement splitter.
    assert "def split_shell_statements(" not in source
    assert "def command_start(" not in source
    assert "def walk_push_args(" not in source


# ---------------------------------------------------------------------------
# Per-command classification
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "command,expected",
    [
        # real tag pushes -> on-release
        ("git push origin v1.2.3", "on-release"),
        ("git push origin refs/tags/v1.2.3", "on-release"),
        ("git push --tags", "on-release"),
        ("git push origin --tag", "on-release"),
        ("git push origin v1.2.3:refs/heads/feat", "on-release"),
        ("/usr/bin/git push origin v1.2.3", "on-release"),
        # non-push commands that merely mention the words -> no event
        ("git push origin main", "none"),
        ("git push", "none"),
        ("git commit -m 'feat: x'", "none"),
        ("git status", "none"),
        ("echo \"git push origin v1.2.3\"", "none"),
        ("printf '%s' 'git push --tags'", "none"),
        ("grep -n 'git push' README.md", "none"),
        ("grep -n git push CHANGELOG.md", "none"),
        ("# git push origin v1.2.3", "none"),
        ("man git-push", "none"),
        # merge
        ("git merge feature/x", "on-merge"),
        ("gh pr merge 42 --squash", "on-merge"),
        ("gh pr create --body 'pr merge later'", "none"),
        ("echo 'gh pr merge'", "none"),
    ],
)
def test_detect_command_word_classification(command, expected):
    assert _load_module().detect(command) == expected


@pytest.mark.parametrize(
    "command,expected",
    [
        # wrapper / git global option forms still resolve to the real command
        ("sudo git push origin v1.2.3", "on-release"),
        ("env X=1 git push --tags", "on-release"),
        ("timeout 30 git push origin v9.9.9", "on-release"),
        ("git -C /tmp/repo push origin v1.2.3", "on-release"),
        ("git --no-pager merge feature", "on-merge"),
        ("(git push origin v1.2.3)", "on-release"),
        ("cd sub && git merge feature", "on-merge"),
        # command substitution bodies are statements of their own
        ("echo \"$(git push origin v1.2.3)\"", "on-release"),
        # -o --tags is a push-option VALUE, not the --tags flag
        ("git push -o --tags origin main", "none"),
    ],
)
def test_detect_wrappers_and_quoting(command, expected):
    assert _load_module().detect(command) == expected


def test_detect_precedence_release_beats_merge_and_commit():
    module = _load_module()
    assert module.detect(
        "git merge feature && git push origin v1.2.3"
    ) == "on-release"


def test_detect_unparseable_statement_fails_open():
    # An unbalanced quote is not an executable command; the informational hook
    # must not raise an event (and must not crash) for it.
    assert _load_module().detect("git push origin 'v1.2.3") == "none"


# ---------------------------------------------------------------------------
# Version-bump heuristic (unchanged semantics)
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "version,previous,expected",
    [
        ("2.0.0", "1.9.9", "on-version-bump-major"),
        ("1.3.0", "1.2.9", "on-version-bump-minor"),
        ("1.2.4", "1.2.3", "on-version-bump-patch"),
        ("1.2.3", "", "on-version-bump-patch"),
        # The former shell compared the version parts as STRINGS: "02" != "2".
        ("1.02.3", "1.2.3", "on-version-bump-minor"),
    ],
)
def test_bump_kind_matches_the_former_shell_comparison(version, previous, expected):
    assert _load_module().bump_kind(version, previous) == expected


@pytest.mark.parametrize(
    "command,expected",
    [
        ("git commit -m 'chore: bump version to 2.0.0'", "on-version-bump-major"),
        ('git commit -m "chore: bump to 1.3.0"', "on-version-bump-minor"),
        ("git commit -m 'bump version 1.2.4'", "on-version-bump-patch"),
        ("git commit --message='chore: bump to 1.3.0'", "on-version-bump-minor"),
        ("git commit -m'chore: bump to 1.3.0'", "on-version-bump-minor"),
        ("git commit -am 'chore: bump to 1.3.0'", "on-version-bump-minor"),
        # bump keywords without a version, or a version without bump keywords
        ("git commit -m 'chore: bump'", "none"),
        ("git commit -m 'feat: use 1.3.0'", "none"),
        # a bump message that is only text of another command
        ("echo 'chore: bump version to 2.0.0'", "none"),
    ],
)
def test_commit_bump_message_extraction(tmp_path, monkeypatch, command, expected):
    repo = _tagged_repo(tmp_path / "repo", "v1.2.3")
    monkeypatch.chdir(repo)
    assert _load_module().detect(command) == expected


def test_previous_version_reads_head_parent_tag(tmp_path, monkeypatch):
    module = _load_module()
    repo = _tagged_repo(tmp_path / "repo", "v2.4.1")
    monkeypatch.chdir(repo)
    assert module.previous_version() == "2.4.1"

    empty = tmp_path / "not-a-repo"
    empty.mkdir()
    monkeypatch.chdir(empty)
    assert module.previous_version() == ""  # fail open -> patch


def test_cli_reads_the_command_from_stdin(tmp_path):
    repo = _tagged_repo(tmp_path / "repo", "v1.0.0")
    result = subprocess.run(
        [sys.executable, str(_LIB_DIR / _MODULE)],
        input=b"git push origin v2.0.0\n",
        capture_output=True, cwd=str(repo), timeout=SCRIPT_TIMEOUT,
    )
    assert (result.returncode, result.stdout, result.stderr) == (
        0, b"on-release\n", b""
    )
    assert _call(_load_module(), ["unexpected"], "git push") == (1, "", "")


def test_detect_only_returns_known_event_names():
    module = _load_module()
    for command in (
        "git push origin v1.0.0", "git merge x", "gh pr merge 1",
        "git commit -m 'bump 1.0.0'", "true",
    ):
        assert module.detect(command) in _EVENTS


# ---------------------------------------------------------------------------
# Deployment
# ---------------------------------------------------------------------------

def test_module_deploys_flat_into_the_hook_lib(tmp_path):
    project_root = tmp_path / "project"
    project_root.mkdir()
    provider = "runtime"
    sync_hook_lib(
        _REPO_ROOT,
        project_root,
        {"platforms": []},
        SyncLog(),
        dry_run=False,
        provider=provider,
        provider_config={
            provider: {
                "hooks_dir": ".runtime/hooks",
                "has_hooks": True,
                "hook_protocol": "claude-code-json",
            }
        },
    )
    deployed_lib = project_root / ".runtime" / "hooks" / "lib"
    deployed = deployed_lib / _MODULE
    assert deployed.is_file()
    assert deployed.parent == deployed_lib
    assert _MODULE in (deployed_lib / ".agent-meta-managed").read_text().splitlines()
    for dependency in (
        "hook_shell_scan.py", "hook_shell_resolver.py", "hook_push_arg_parser.py",
    ):
        assert (deployed_lib / dependency).is_file()


def test_hook_uses_the_deployed_module_and_no_raw_command_grep():
    source = _HOOK_PATH.read_text(encoding="utf-8")
    assert "# version: 1.2.0" in source
    assert "v1.2.0" in source
    assert source.count('"$SCRIPT_DIR/lib/' + _MODULE + '"') == 1
    # No regex over the raw command anymore: the former detection used
    # `grep -qE`/`grep -oP` on the command string.
    assert not re.search(r"grep\s+-[a-zA-Z]*[qEoP]", source)
    assert "grep" not in source


# ---------------------------------------------------------------------------
# Hook integration
# ---------------------------------------------------------------------------

def test_hook_writes_the_on_release_task(tmp_path):
    root = _project(tmp_path, {
        "on-release": [{"agent": "release", "task": "release-checklist"}],
        "on-merge": [{"agent": "tester", "task": "merge-task"}],
    })
    result = _run_hook(_HOOK_PATH, root, "git push origin v1.2.3")
    assert result.returncode == 0, result.stderr
    assert "- [ ] **[release]** release-checklist" in _pending(root)


@pytest.mark.parametrize(
    "command,forbidden",
    [
        ('echo "git push origin v1.2.3"', "release-checklist"),
        ("grep -n 'git push' README.md", "release-checklist"),
        ("git commit -m 'chore: bump'", "release-checklist"),
        ("git status", "release-checklist"),
    ],
)
def test_hook_stays_silent_for_prose_and_plain_commands(tmp_path, command, forbidden):
    root = _project(tmp_path, {
        "on-release": [{"agent": "release", "task": "release-checklist"}],
        "on-commit": [{"agent": "tester", "task": "release-checklist"}],
    })
    result = _run_hook(_HOOK_PATH, root, command)
    assert result.returncode == 0, result.stderr
    assert forbidden not in _pending(root)


def test_hook_writes_the_merge_task_and_a_commit_bump_task(tmp_path):
    root = _project(tmp_path, {
        "on-merge": [{"agent": "tester", "task": "merge-task"}],
        "on-version-bump-patch": [{"agent": "documenter", "task": "changelog-task"}],
    })
    merged = _run_hook(_HOOK_PATH, root, "gh pr merge 7 --squash --delete-branch")
    assert merged.returncode == 0, merged.stderr
    assert "- [ ] **[tester]** merge-task" in _pending(root)

    # Not a git repo -> no previous tag -> patch bump (former default).
    bumped = _run_hook(
        _HOOK_PATH, root, "git commit -m 'chore: bump version to 1.2.4'"
    )
    assert bumped.returncode == 0, bumped.stderr
    assert "- [ ] **[documenter]** changelog-task" in _pending(root)


def test_hook_fails_open_without_the_event_module(tmp_path):
    root = _project(tmp_path, {
        "on-release": [{"agent": "release", "task": "release-checklist"}],
    })
    # Mirror the deployed layout (hook + scripts/lifecycle_check.py), but
    # leave the event module out of hooks/lib.
    hooks = root / "hooks"
    lib = hooks / "lib"
    lib.mkdir(parents=True)
    shutil.copy(_HOOK_PATH, hooks / "lifecycle-check.sh")
    for name in ("hook_common.sh", "hook_json_many.py"):
        shutil.copy(_LIB_DIR / name, lib / name)
    scripts = root / "scripts"
    scripts.mkdir()
    shutil.copy(_SCRIPTS_DIR / "lifecycle_check.py", scripts / "lifecycle_check.py")

    result = _run_hook(hooks / "lifecycle-check.sh", root, "git push origin v1.2.3")
    assert result.returncode == 0, result.stderr
    assert _pending(root) == ""
