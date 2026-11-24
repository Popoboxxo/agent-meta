"""CLI smoke matrix: every user-facing sync.py mode on a project with ALL providers.

Single-provider tests cannot see regressions that only appear when the full
registry is active or when the framework root differs from ``<project>/.agent-meta``
(e.g. ``--checkpoint`` once resolved a Claude-only registry and crashed for any
other provider). Three module-scoped projects (read-only / scaffold / lifecycle
groups), each with its own all-provider ``--init``, so one failed or slow init
only affects its own group; an init timeout skips the group explicitly.

Run: python -m pytest tests/test_cli_smoke_multi_provider.py -v
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

from tests.timeouts import SLOW_TIMEOUT

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SYNC = _REPO_ROOT / "scripts" / "sync.py"
_PROVIDERS = sorted(
    yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
)


def _make_project(tmp_path_factory, name):
    root = tmp_path_factory.mktemp(name)
    (root / ".meta-config").mkdir()
    (root / ".meta-config" / "project.yaml").write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        "ai-providers: [" + ", ".join(_PROVIDERS) + "]\n"
        "dod-preset: rapid-prototyping\n"
        # Codex silently truncates its AGENTS.md reader at 32 KiB (context hard
        # cap, Task 1.25). The all-provider *full* render is intentionally over
        # that cap (AC-13), so `--init` would abort with `context.over-hard-cap`
        # and mask every CLI mode this matrix exercises. Compact mode — the
        # supported way to fit a large context — keeps the same provider set
        # while staying well below the cap.
        "context_file:\n  mode: compact\n"
        "variables:\n  PROJECT_NAME: smoke\n  PROJECT_PREFIX: sm\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=root, check=True)
    try:
        result = _sync(root, "--init")
    except subprocess.TimeoutExpired:
        pytest.skip(f"{name}: all-provider --init exceeded SLOW_TIMEOUT={SLOW_TIMEOUT}s")
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    return root


@pytest.fixture(scope="module")
def project_readonly(tmp_path_factory):
    return _make_project(tmp_path_factory, "cli-smoke-ro")


@pytest.fixture(scope="module")
def project_scaffold(tmp_path_factory):
    return _make_project(tmp_path_factory, "cli-smoke-scaffold")


@pytest.fixture(scope="module")
def project_lifecycle(tmp_path_factory):
    return _make_project(tmp_path_factory, "cli-smoke-lifecycle")


def _sync(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC), "--config", str(root / ".meta-config" / "project.yaml"), *args],
        cwd=root, capture_output=True, text=True, timeout=SLOW_TIMEOUT,
        encoding="utf-8", errors="replace",
    )


def _ok(root: Path, *args: str) -> subprocess.CompletedProcess:
    result = _sync(root, *args)
    assert "Traceback" not in result.stdout + result.stderr, result.stderr[-2500:]
    assert result.returncode == 0, f"{' '.join(args)} -> rc {result.returncode}\n{result.stdout[-1500:]}\n{result.stderr[-1500:]}"
    return result


@pytest.mark.parametrize("mode", [
    ("--dry-run", "--check"),
    ("--validate",),
    ("--audit-config",),
    ("--cleanup-preview",),
    ("--deactivation-status",),
    ("--list-backups",),
    ("--only-variables",),
    ("--validate-se",),
    ("--validate-spec-plan",),
    ("--scan-staged",),
])
def test_readonly_mode_succeeds(project_readonly, mode):
    _ok(project_readonly, *mode)


@pytest.mark.parametrize("mode", [
    ("--update-ext",),
    ("--create-ext", "developer"),
    ("--create-rule", "smokerule"),
    ("--create-hook", "smokehook"),
    ("--create-command", "smokecmd"),
])
def test_scaffold_mode_succeeds(project_scaffold, mode):
    _ok(project_scaffold, *mode)


def test_repeat_sync_is_idempotent(project_scaffold):
    project = project_scaffold
    # The create-* modes above add user rules/hooks; the next real sync
    # records them (external-tools drift rule) and must then converge.
    _ok(project)
    _ok(project, "--dry-run", "--check")


def test_checkpoint_with_every_provider(project_lifecycle):
    project = project_lifecycle
    """--checkpoint must use the running framework's registry, not a guess."""
    _ok(project, "--checkpoint", "--session-id", "smoke1", "--agent", "developer",
        "--task", "T1", "--status", "in_progress", "--description", "d",
        "--summary", "s", "--next-step", "n")
    _ok(project, "--rehydrate")


def test_backup_restore_delete_roundtrip(project_lifecycle):
    project = project_lifecycle
    _ok(project, "--backup", "--backup-label", "smoke")
    listing = _ok(project, "--list-backups").stdout
    match = re.search(r"([A-Za-z0-9._-]+\.(?:zip|tar\.gz|tgz))", listing)
    assert match, f"no backup archive listed:\n{listing}"
    archive = match.group(1)
    _ok(project, "--restore", archive, "--force")
    _ok(project, "--delete-backup", archive)


def test_deactivate_and_reactivate_provider(project_lifecycle):
    project = project_lifecycle
    _ok(project, "--deactivate-providers", "Codex")
    assert not (project / ".codex").exists(), "deactivated provider artifacts must be removed"
    _ok(project, "--activate-providers", "Codex")
    assert (project / ".codex").is_dir(), "reactivation must regenerate the provider tree"


def test_update_ext_check_reports_drift_without_writing(project_lifecycle):
    """#1269 AC-4: --update-ext --check exits 1 on drift; file stays unchanged."""
    ext = project_lifecycle / ".claude" / "3-project" / "am-developer-ext.md"
    ext.parent.mkdir(parents=True, exist_ok=True)
    ext.write_text("<!-- agent-meta:managed-begin v=deadbeef -->\nhand\n"
                   "<!-- agent-meta:managed-end -->\n", encoding="utf-8")
    before = ext.read_text(encoding="utf-8")
    try:
        result = _sync(project_lifecycle, "--update-ext", "--check")
        assert result.returncode == 1, result.stdout[-800:] + result.stderr[-800:]
        assert ext.read_text(encoding="utf-8") == before
        result = _sync(project_lifecycle, "--update-ext")  # warning + skip, not an error
        assert result.returncode == 0 and ext.read_text(encoding="utf-8") == before
    finally:
        ext.unlink()


@pytest.mark.parametrize("body,strict_rc", [
    ("<!-- agent-meta:managed-begin v=deadbeef -->\nhand\n<!-- agent-meta:managed-end -->\n", 1),
    ("<!-- agent-meta:managed-begin v=deadbeef -->\nno end marker\n", 1),
])
def test_validate_extension_drift_warns_and_strict_fails(project_lifecycle, body, strict_rc):
    """#1269: --validate warns (exit 0), --validate --strict exits 1; no traceback."""
    ext = project_lifecycle / ".claude" / "3-project" / "am-developer-ext.md"
    ext.parent.mkdir(parents=True, exist_ok=True)
    ext.write_text(body, encoding="utf-8")
    try:
        warn = _ok(project_lifecycle, "--validate")
        assert "extension.drift" in warn.stdout + warn.stderr
        strict = _sync(project_lifecycle, "--validate", "--strict")
        assert "Traceback" not in strict.stdout + strict.stderr
        assert strict.returncode == strict_rc
    finally:
        ext.unlink()
