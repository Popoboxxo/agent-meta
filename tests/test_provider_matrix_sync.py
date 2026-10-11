"""Provider matrix: one real sync per registered provider, artifact invariants.

Every provider in config/ai-providers.yaml is synced into a scratch consumer
project (single-provider config) and the generated artifacts are checked for
the invariants that the single-case tests keep missing:

  * sync exits 0
  * every generated agent file is well-formed (TOML via tomllib, Markdown via
    YAML frontmatter)
  * no non-Claude agent file references the Claude-only ``.claude/`` tree
  * no machine-local file the sync creates is left un-ignored by git
    (personal context file, sync.log, generated env scripts)
  * a second ``--dry-run --check`` run reports no pending changes (idempotence)

Parametrized over the live registry, so a newly onboarded provider is covered
automatically (provider-agnostic: no provider name appears below).

Run: python -m pytest tests/test_provider_matrix_sync.py -v
"""

import re
import subprocess
import sys
from pathlib import Path

import pytest
import yaml

try:
    import tomllib
except ModuleNotFoundError:  # Python < 3.11
    import tomli as tomllib

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SYNC = _REPO_ROOT / "scripts" / "sync.py"
_PROVIDERS = sorted(
    yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
)
# Files the sync creates that are machine-local and must never be committable.
_LOCAL_FILE_RE = re.compile(
    r"(\.personal\.md$|(^|/)sync\.log$|(^|/)env\.(sh|ps1|unset\.sh|unset\.ps1)$|\.sync-backup-)"
)


def _run(project: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC), "--config", str(project / ".meta-config" / "project.yaml"), *extra],
        cwd=project, capture_output=True, text=True, timeout=300,
    )


def _git(project: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=project, capture_output=True, text=True, check=True
    ).stdout


@pytest.fixture(scope="module", params=_PROVIDERS)
def synced(request, tmp_path_factory):
    provider = request.param
    project = tmp_path_factory.mktemp(f"matrix-{provider}")
    (project / ".meta-config").mkdir()
    (project / ".meta-config" / "project.yaml").write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        f"ai-providers:\n- {provider}\n"
        "dod-preset: rapid-prototyping\n"
        "variables:\n  PROJECT_NAME: matrix\n  PROJECT_PREFIX: mx\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)
    result = _run(project, "--init")
    return provider, project, result


def _generated_files(project: Path):
    for f in project.rglob("*"):
        if f.is_file() and ".git" not in f.relative_to(project).parts:
            yield f


def test_sync_succeeds(synced):
    provider, _project, result = synced
    assert result.returncode == 0, f"{provider}: sync failed\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}"
    assert "Traceback" not in result.stdout + result.stderr


def test_agent_files_are_well_formed(synced):
    provider, project, _ = synced
    pc = yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"][provider]
    agents_dir = project / pc["agents_dir"]
    assert agents_dir.is_dir(), f"{provider}: agents dir {pc['agents_dir']} missing"
    files = [f for f in agents_dir.iterdir() if f.is_file() and f.suffix in (".md", ".toml")]
    assert files, f"{provider}: no agent files generated"
    for f in files:
        text = f.read_text(encoding="utf-8")
        if f.suffix == ".toml":
            tomllib.loads(text)  # raises -> test fails with the file in the traceback
        elif text.startswith("---"):
            end = text.find("\n---", 3)
            assert end != -1, f"{provider}: unterminated frontmatter in {f.name}"
            yaml.safe_load(text[3:end])


def test_no_claude_only_paths_in_foreign_agents(synced):
    provider, project, _ = synced
    pc = yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"][provider]
    if ".claude" in pc["agents_dir"]:
        pytest.skip("Claude-family provider owns the .claude/ tree")
    agents_dir = project / pc["agents_dir"]
    offenders = [
        f.name for f in agents_dir.iterdir()
        if f.is_file() and ".claude/" in f.read_text(encoding="utf-8")
    ]
    assert not offenders, f"{provider}: .claude/ references in {offenders[:5]}"


def test_machine_local_files_are_gitignored(synced):
    provider, project, _ = synced
    untracked = _git(project, "status", "--short", "-uall").splitlines()
    leaked = [
        line[3:] for line in untracked
        if line.startswith("??") and _LOCAL_FILE_RE.search(line[3:])
    ]
    assert not leaked, f"{provider}: machine-local files not gitignored: {leaked}"


def test_second_run_is_idempotent(synced):
    provider, project, _ = synced
    result = _run(project, "--dry-run", "--check")
    assert result.returncode == 0, (
        f"{provider}: --check reports pending changes after a clean sync\n{result.stdout[-2000:]}"
    )
