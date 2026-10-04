"""Regression for issue #805 (check F11).

Deactivating and reactivating a provider must leave the provider's generated
artifact set identical to a fresh ``sync.py`` result. The original bug: after
``--deactivate-providers Opencode`` + ``--activate-providers Opencode`` the
``.opencode/agents`` tree was gone, because

1. the CLI only regenerated context files (not agents/commands/skills), and
2. reactivation never cleared the deactivation list, and
3. the deactivation backup was written to a different directory/name than the
   one its restore lookup searched.

The tests below run the real CLI in a copied, self-hosting scratch tree with a
minimal project config (single representative provider) so the artifact set is
small and the run is fast. The scratch lives under pytest's ``tmp_path``
(basetemp outside the repo, e.g. ``--basetemp=/tmp/$USER/pytest-805``); the copy
never recurses into ``.tmp`` and never follows symlinks.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parents[1]
_PROVIDER = "Opencode"
_PROVIDER_ROOT = ".opencode"

# Never copied: VCS/meta dirs, the in-repo scratch sinks and the provider
# output itself (regenerated from templates inside the scratch tree).
_COPY_IGNORE = {
    ".git",
    ".tmp",
    ".backup",
    ".playwright-mcp",
    ".agent-meta",
    ".pytest_cache",
    ".venv",
    "external",
    "graphify-out",
    "node_modules",
    "__pycache__",
    _PROVIDER_ROOT,
}


def _copy_repo(dest: Path) -> Path:
    """Copy the repo for a self-hosting run; skip ignores and symlinks.

    A destination inside the copied tree would recurse without bound, so it is
    only allowed when it sits under the ignored ``.tmp`` scratch sink (an
    in-repo basetemp); anything else under the repo must fail loud.
    """
    root = _REPO_ROOT.resolve()
    resolved = dest.resolve()
    if resolved == root or root in resolved.parents:
        rel = resolved.relative_to(root)
        if not rel.parts or rel.parts[0] != ".tmp":
            raise AssertionError(
                f"refusing to copy {root} into {resolved}: destination is inside "
                "the copied source but not under the ignored '.tmp' sink; put "
                "pytest's basetemp outside the repo (e.g. --basetemp=/tmp/$USER)"
            )

    def ignore(dirname: str, names: list[str]) -> set[str]:
        skip: set[str] = set()
        for name in names:
            entry = Path(dirname) / name
            if name in _COPY_IGNORE or name.endswith(".pyc") or entry.is_symlink():
                skip.add(name)
        return skip

    shutil.copytree(_REPO_ROOT, dest, ignore=ignore, symlinks=False)
    return dest


def _write_minimal_project(root: Path) -> None:
    meta = root / ".meta-config"
    meta.mkdir(parents=True, exist_ok=True)
    (meta / "project.yaml").write_text(
        f"ai-providers: [{_PROVIDER}]\n"
        "dod-preset: rapid-prototyping\n"
        "roles: [developer]\n"
        "project: {name: scratch805, prefix: s805, short: scratch805}\n"
        "variables: {PROJECT_NAME: scratch805}\n",
        encoding="utf-8",
    )


def _run_sync(root: Path, *extra_args: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(root / "scripts" / "sync.py"), *extra_args],
        cwd=str(root), capture_output=True, text=True, check=False,
    )


def _artifact_set(root: Path) -> list[str]:
    """Provider artifact set: everything under the provider root + root files.

    Mirrors the audit check (F11): the provider directory tree plus the
    provider-owned repo-root artifacts such as ``opencode.json``.
    """
    artifacts: list[str] = []
    provider_dir = root / _PROVIDER_ROOT
    if provider_dir.exists():
        for entry in sorted(provider_dir.rglob("*")):
            rel = Path(_PROVIDER_ROOT) / entry.relative_to(provider_dir)
            artifacts.append(str(rel) + ("/" if entry.is_dir() else ""))
    for extra in ("opencode.json",):
        if (root / extra).exists():
            artifacts.append(extra)
    return sorted(artifacts)


@pytest.fixture()
def scratch(tmp_path: Path) -> Path:
    root = _copy_repo(tmp_path / "scratch")
    _write_minimal_project(root)
    return root


def test_reactivation_restores_full_artifact_set(scratch: Path) -> None:
    """Pre-deactivate artifact set == post-reactivate artifact set."""
    assert _run_sync(scratch).returncode == 0, "initial sync failed"
    assert (scratch / _PROVIDER_ROOT / "agents").is_dir()

    # A hand-written, non-generated file can only come back via the backup
    # restore path, not via regeneration.
    handwritten = scratch / _PROVIDER_ROOT / "agents" / "handwritten.md"
    handwritten.write_text("# hand written\n", encoding="utf-8")

    before = _artifact_set(scratch)
    assert f"{_PROVIDER_ROOT}/agents/" in before  # sanity: representative set

    deactivate = _run_sync(scratch, "--deactivate-providers", _PROVIDER)
    assert deactivate.returncode == 0, deactivate.stderr
    assert not (scratch / _PROVIDER_ROOT).exists()

    activate = _run_sync(scratch, "--activate-providers", _PROVIDER)
    assert activate.returncode == 0, activate.stderr

    after = _artifact_set(scratch)
    assert after == before, (
        f"artifact set drifted after reactivation\n"
        f"missing: {sorted(set(before) - set(after))}\n"
        f"extra:   {sorted(set(after) - set(before))}"
    )
    assert f"{_PROVIDER_ROOT}/agents/" in after
    assert handwritten.exists(), "restore path did not preserve an untracked file"


def test_reactivation_without_backup_still_regenerates(scratch: Path) -> None:
    """A missing backup must not break reactivation (regeneration covers it)."""
    assert _run_sync(scratch).returncode == 0

    deactivate = _run_sync(scratch, "--deactivate-providers", _PROVIDER)
    assert deactivate.returncode == 0, deactivate.stderr

    shutil.rmtree(scratch / ".backup", ignore_errors=True)

    activate = _run_sync(scratch, "--activate-providers", _PROVIDER)
    assert activate.returncode == 0, activate.stderr
    assert (scratch / _PROVIDER_ROOT / "agents").is_dir()
