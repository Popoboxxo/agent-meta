"""Provider matrix: one real sync per provider × profile, artifact invariants.

Every provider in config/ai-providers.yaml is synced into a scratch consumer
project (single-provider config) — once per context profile, ``full`` and the
opt-in ``compact`` (Task 18/2c.3, QG-6) — and the generated artifacts are
checked for the invariants that the single-case tests keep missing:

  * sync exits 0
  * every generated agent file is well-formed (TOML via tomllib, Markdown via
    YAML frontmatter)
  * no non-Claude agent file references the Claude-only ``.claude/`` tree
  * no machine-local file the sync creates is left un-ignored by git
    (personal context file, sync.log, generated env scripts)
  * a second ``--dry-run --check`` run reports no pending changes (idempotence)

Multi-provider combinations (QG-6) are covered on top of that: a pair sharing a
context file and a pair spanning two context files.

Parametrized over the live registry, so a newly onboarded provider (and a new
profile) is covered automatically (provider-agnostic: no provider name appears
below).

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
_PROVIDER_CONFIG = yaml.safe_load(
    (_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))["providers"]
_PROVIDERS = sorted(_PROVIDER_CONFIG)
_PROFILES = ("full", "compact")

# Files the sync creates that are machine-local and must never be committable.
_LOCAL_FILE_RE = re.compile(
    r"(\.personal\.md$|(^|/)CLAUDE\.local\.md$|(^|/)sync\.log$|(^|/)env\.(sh|ps1|unset\.sh|unset\.ps1)$|\.sync-backup-)"
)


def _context_file_groups():
    groups = {}
    for provider, pc in _PROVIDER_CONFIG.items():
        groups.setdefault(pc["context_file"], []).append(provider)
    return {name: sorted(members) for name, members in groups.items()}


_CONTEXT_FILE_GROUPS = _context_file_groups()
_SHARED_MEMBERS = max(_CONTEXT_FILE_GROUPS.values(), key=len)
_OTHER_MEMBERS = min(_CONTEXT_FILE_GROUPS.values(), key=len)
# Multi-provider combinations, derived from the registry (no provider literal).
_MULTI_COMBOS = {
    "shared-file": _SHARED_MEMBERS[:2],
    "mixed-files": [_SHARED_MEMBERS[0], _OTHER_MEMBERS[0]],
}


def _run(project: Path, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(_SYNC), "--config", str(project / ".meta-config" / "project.yaml"), *extra],
        cwd=project, capture_output=True, text=True, timeout=300,
    )


def _git(project: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=project, capture_output=True, text=True, check=True
    ).stdout


def _write_and_init(project: Path, providers, profile=None) -> None:
    (project / ".meta-config").mkdir(parents=True, exist_ok=True)
    (project / ".meta-config" / "project.yaml").write_text(
        'agent-meta-version: "2.0.0-beta.1"\n'
        "ai-providers:\n"
        + "".join("- %s\n" % provider for provider in providers)
        + "dod-preset: rapid-prototyping\n"
        + ("context-profile: %s\n" % profile if profile else "")
        + "variables:\n  PROJECT_NAME: matrix\n  PROJECT_PREFIX: mx\n",
        encoding="utf-8",
    )
    subprocess.run(["git", "init", "-q"], cwd=project, check=True)


@pytest.fixture(scope="module",
                params=[(provider, profile) for provider in _PROVIDERS for profile in _PROFILES],
                ids=lambda param: "%s-%s" % (param[0], param[1]))
def synced(request, tmp_path_factory):
    provider, profile = request.param
    project = tmp_path_factory.mktemp("matrix-%s-%s" % (provider, profile))
    _write_and_init(project, [provider], profile)
    result = _run(project, "--init")
    return provider, profile, project, result


@pytest.fixture(scope="module", params=sorted(_MULTI_COMBOS))
def synced_multi(request, tmp_path_factory):
    combo = request.param
    providers = _MULTI_COMBOS[combo]
    project = tmp_path_factory.mktemp("matrix-multi-%s" % combo)
    _write_and_init(project, providers)
    result = _run(project, "--init")
    return combo, providers, project, result


def _generated_files(project: Path):
    for f in project.rglob("*"):
        if f.is_file() and ".git" not in f.relative_to(project).parts:
            yield f


def _assert_well_formed(agents_dir: Path, label: str) -> None:
    assert agents_dir.is_dir(), f"{label}: agents dir {agents_dir} missing"
    files = [f for f in agents_dir.iterdir() if f.is_file() and f.suffix in (".md", ".toml")]
    assert files, f"{label}: no agent files generated"
    for f in files:
        text = f.read_text(encoding="utf-8")
        if f.suffix == ".toml":
            tomllib.loads(text)  # raises -> test fails with the file in the traceback
        elif text.startswith("---"):
            end = text.find("\n---", 3)
            assert end != -1, f"{label}: unterminated frontmatter in {f.name}"
            yaml.safe_load(text[3:end])


def test_sync_succeeds(synced):
    provider, profile, _project, result = synced
    assert result.returncode == 0, (
        f"{provider}/{profile}: sync failed\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}")
    assert "Traceback" not in result.stdout + result.stderr


def test_agent_files_are_well_formed(synced):
    provider, profile, project, _ = synced
    pc = _PROVIDER_CONFIG[provider]
    _assert_well_formed(project / pc["agents_dir"], f"{provider}/{profile}")


def test_no_claude_only_paths_in_foreign_agents(synced):
    provider, profile, project, _ = synced
    pc = _PROVIDER_CONFIG[provider]
    if ".claude" in pc["agents_dir"]:
        pytest.skip("Claude-family provider owns the .claude/ tree")
    agents_dir = project / pc["agents_dir"]
    offenders = [
        f.name for f in agents_dir.iterdir()
        if f.is_file() and ".claude/" in f.read_text(encoding="utf-8")
    ]
    assert not offenders, f"{provider}/{profile}: .claude/ references in {offenders[:5]}"


def test_machine_local_files_are_gitignored(synced):
    provider, profile, project, _ = synced
    untracked = _git(project, "status", "--short", "-uall").splitlines()
    leaked = [
        line[3:] for line in untracked
        if line.startswith("??") and _LOCAL_FILE_RE.search(line[3:])
    ]
    assert not leaked, f"{provider}/{profile}: machine-local files not gitignored: {leaked}"


def test_second_run_is_idempotent(synced):
    provider, profile, project, _ = synced
    result = _run(project, "--dry-run", "--check")
    assert result.returncode == 0, (
        f"{provider}/{profile}: --check reports pending changes after a clean sync\n"
        f"{result.stdout[-2000:]}"
    )


def test_multi_provider_sync_succeeds(synced_multi):
    combo, providers, _project, result = synced_multi
    assert result.returncode == 0, (
        f"{combo} {providers}: sync failed\n{result.stdout[-2000:]}\n{result.stderr[-2000:]}")


def test_multi_provider_agent_files_are_well_formed(synced_multi):
    combo, providers, project, _ = synced_multi
    for provider in providers:
        _assert_well_formed(project / _PROVIDER_CONFIG[provider]["agents_dir"], f"{combo}/{provider}")


def test_multi_provider_second_run_is_idempotent(synced_multi):
    combo, providers, project, _ = synced_multi
    result = _run(project, "--dry-run", "--check")
    assert result.returncode == 0, (
        f"{combo} {providers}: --check reports pending changes after a clean sync\n"
        f"{result.stdout[-2000:]}"
    )


# --- Task 1.24 (AC-11, AC-12): reachability over 9 providers x rules presets ----------

_RULES_PRESETS = ("default", "minimal", "silent", "lazy")


@pytest.fixture(scope="module")
def preset_matrix(tmp_path_factory):
    from tests.active_set_render import preset_config, synced_projects

    configs = {(preset, p): preset_config(p, preset) for preset in _RULES_PRESETS for p in _PROVIDERS}
    names = {key: f"{key[0]}-{key[1]}" for key in configs}
    done = synced_projects(tmp_path_factory, {names[k]: c for k, c in configs.items()})
    return {key: (configs[key], done[names[key]]) for key in configs}


def _context_checks():
    sys.path.insert(0, str(_REPO_ROOT / "scripts"))
    from lib import context_report as cr
    from lib.active_set import compute_active_set
    from lib.consistency import context_budget as cb
    from lib.providers import load_provider_capabilities, load_providers_config

    mappings = cr.merge_provider_mappings(
        load_providers_config(_REPO_ROOT, {}), load_provider_capabilities(_REPO_ROOT))
    return cb, compute_active_set, mappings


def test_dangling_pointer_is_error():
    cb, _compute, _maps = _context_checks()
    from lib.consistency.report import Severity

    assert cb.EMITTED_SEVERITY["context.dangling-pointer"] is Severity.ERROR
    assert cb._warn("context.dangling-pointer", "f", "m").severity is Severity.ERROR


def test_rule_unreachable_is_error():
    # AC-12: the 9x4 matrix reports zero findings (see the test below), so the
    # check now emits its spec level (ERROR) instead of the Phase-0 WARNING.
    cb, _compute, _maps = _context_checks()
    from lib.consistency.report import Severity

    assert cb.EMITTED_SEVERITY["context.rule-unreachable"] is Severity.ERROR
    assert cb._warn("context.rule-unreachable", "f", "m").severity is Severity.ERROR


@pytest.mark.parametrize("preset", _RULES_PRESETS)
@pytest.mark.parametrize("provider", _PROVIDERS)
def test_no_dangling_pointer_and_no_unreachable_rule(preset_matrix, preset, provider):
    cb, compute_active_set, mappings = _context_checks()
    config, project = preset_matrix[(preset, provider)]
    active = compute_active_set(config, _REPO_ROOT, project)
    dangling = cb.check_dangling_pointer(project, [provider], mappings, active)
    assert not dangling, [f"{f.file}: {f.message}" for f in dangling][:5]
    unreachable = [f.file for f in cb.check_rule_unreachable(project, [provider], mappings, active)]
    assert not unreachable, f"{provider}/{preset}: unreachable rules {unreachable}"
