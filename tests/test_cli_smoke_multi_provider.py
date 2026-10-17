"""CLI smoke matrix: every user-facing sync.py mode on a project with ALL providers.

Single-provider tests cannot see regressions that only appear when the full
registry is active or when the framework root differs from ``<project>/.agent-meta``
(e.g. ``--checkpoint`` once resolved a Claude-only registry and crashed for any
other provider). One module-scoped project, modes run in dependency order.

Run: python -m pytest tests/test_cli_smoke_multi_provider.py -v
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SYNC = _REPO_ROOT / "scripts" / "sync.py"
_PROVIDERS = sorted(
    yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
)


@pytest.fixture(scope="module")
def project(tmp_path_factory):
    root = tmp_path_factory.mktemp("cli-smoke")
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
    result = _sync(root, "--init")
    assert result.returncode == 0, result.stdout[-2000:] + result.stderr[-2000:]
    return root


def _sync(root: Path, *args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC), "--config", str(root / ".meta-config" / "project.yaml"), *args],
        cwd=root, capture_output=True, text=True, timeout=300,
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
    ("--update-ext",),
    ("--create-ext", "developer"),
    ("--create-rule", "smokerule"),
    ("--create-hook", "smokehook"),
    ("--create-command", "smokecmd"),
    ("--validate-se",),
    ("--validate-spec-plan",),
    ("--scan-staged",),
])
def test_mode_succeeds(project, mode):
    _ok(project, *mode)


def test_repeat_sync_is_idempotent(project):
    # The create-* modes above add user rules/hooks; the next real sync
    # records them (external-tools drift rule) and must then converge.
    _ok(project)
    _ok(project, "--dry-run", "--check")


def test_checkpoint_with_every_provider(project):
    """--checkpoint must use the running framework's registry, not a guess."""
    _ok(project, "--checkpoint", "--session-id", "smoke1", "--agent", "developer",
        "--task", "T1", "--status", "in_progress", "--description", "d",
        "--summary", "s", "--next-step", "n")
    _ok(project, "--rehydrate")


def test_backup_restore_delete_roundtrip(project):
    _ok(project, "--backup", "--label", "smoke")
    listing = _ok(project, "--list-backups").stdout
    match = re.search(r"([A-Za-z0-9._-]+\.(?:zip|tar\.gz|tgz))", listing)
    assert match, f"no backup archive listed:\n{listing}"
    archive = match.group(1)
    _ok(project, "--restore", archive, "--force")
    _ok(project, "--delete-backup", archive)


def test_deactivate_and_reactivate_provider(project):
    _ok(project, "--deactivate-providers", "Codex")
    assert not (project / ".codex").exists(), "deactivated provider artifacts must be removed"
    _ok(project, "--activate-providers", "Codex")
    assert (project / ".codex").is_dir(), "reactivation must regenerate the provider tree"
