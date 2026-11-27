"""Continue commands sync: stale cleanup and index split (AC-1.2, AC-1.3).

Continue writes role prompts and generic commands into the same directory
(``commands_dir``). Each writer owns its own managed index: role prompts the
default ``.agent-meta-managed``, commands the provider-configured
``commands_managed_index``. The indexes must stay disjoint so removing a
command never deletes a role prompt (and vice versa). All provider values
are read from config/ai-providers.yaml.
"""
from __future__ import annotations

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.active_set import ActiveSet  # noqa: E402
from lib.commands import sync_commands_for_provider  # noqa: E402
from lib.context import sync_prompts_for_continue  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.providers import load_providers_config  # noqa: E402

_PROVIDER = "Continue"
_ROLE_INDEX = ".agent-meta-managed"
_CMD_SRC = "---\ndescription: {n}\nallowed-tools: [\"Agent\"]\n---\n\nRun {n} $ARGUMENTS\n"


def _root(tmp_path: Path, commands: tuple[str, ...]) -> Path:
    root = tmp_path / "am"
    (root / "config").mkdir(parents=True)
    for name in ("ai-providers.yaml", "provider-capabilities.yaml"):
        (root / "config" / name).write_text(
            (REPO_ROOT / "config" / name).read_text(encoding="utf-8"), encoding="utf-8")
    (root / "config" / "role-defaults.yaml").write_text(
        "roles:\n  developer: {}\n", encoding="utf-8")
    agents = root / "agents" / "1-generic"
    agents.mkdir(parents=True)
    (agents / "developer.md").write_text(
        "---\nname: developer\ndescription: \"Dev\"\nversion: 1.0.0\ntools: []\n---\nBody\n",
        encoding="utf-8")
    set_commands(root, commands)
    return root


def set_commands(root: Path, commands: tuple[str, ...]) -> None:
    cdir = root / "commands" / "1-generic"
    cdir.mkdir(parents=True, exist_ok=True)
    for old in cdir.glob("*.md"):
        old.unlink()
    for n in commands:
        (cdir / f"{n}.md").write_text(_CMD_SRC.format(n=n), encoding="utf-8")


def _config() -> dict:
    return {
        "project": {"name": "P"},
        "roles": ["developer"],
        "platforms": [],
        "provider-options": {_PROVIDER: {"generate-prompts": True}},
    }


def _active(config: dict) -> ActiveSet:
    roles = frozenset(config["roles"])
    return ActiveSet(
        roles=roles, routable=roles, known_roles=roles, sources={}, gates={},
        gate_dropped=(), missing_template=(), producers={},
        raw_roles=roles)


def _sync(root: Path, project: Path, *, commands_first: bool = True) -> None:
    config = _config()
    pconf = load_providers_config(REPO_ROOT, config)
    active = _active(config)

    def cmds():
        sync_commands_for_provider(
            root, project, config, SyncLog(), False, _PROVIDER,
            provider_config=pconf, variables={}, active_set=active)

    def prompts():
        sync_prompts_for_continue(
            root, project, config, {}, SyncLog(), False, pconf,
            provider=_PROVIDER, active_set=active)

    for step in ((cmds, prompts) if commands_first else (prompts, cmds)):
        step()


def _paths(project: Path):
    pc = load_providers_config(REPO_ROOT, _config())[_PROVIDER]
    pdir = project / pc["commands_dir"]
    return pdir, pdir / pc["commands_managed_index"], pdir / _ROLE_INDEX


def _lines(path: Path) -> set[str]:
    return set(path.read_text(encoding="utf-8").split())


def test_config_declares_separate_commands_index():
    pc = load_providers_config(REPO_ROOT, _config())[_PROVIDER]
    assert pc["commands_managed_index"] != _ROLE_INDEX


def test_indexes_are_disjoint_after_two_syncs(tmp_path):
    root = _root(tmp_path, ("alpha", "beta"))
    project = tmp_path / "proj"
    for _ in range(2):
        _sync(root, project)
    pdir, cmd_index, role_index = _paths(project)
    assert _lines(cmd_index) == {"alpha.md", "beta.md"}
    assert _lines(role_index) == {"developer.md"}
    assert _lines(cmd_index).isdisjoint(_lines(role_index))
    for name in ("alpha.md", "beta.md", "developer.md"):
        assert (pdir / name).is_file()


def test_removed_command_is_deleted_and_index_updated(tmp_path):
    root = _root(tmp_path, ("alpha", "beta"))
    project = tmp_path / "proj"
    _sync(root, project)
    set_commands(root, ("alpha",))
    _sync(root, project)
    pdir, cmd_index, role_index = _paths(project)
    assert not (pdir / "beta.md").exists()
    assert (pdir / "alpha.md").is_file()
    assert _lines(cmd_index) == {"alpha.md"}
    # role prompt and its index untouched
    assert (pdir / "developer.md").is_file()
    assert _lines(role_index) == {"developer.md"}


def test_removing_all_commands_keeps_role_prompt_in_either_order(tmp_path):
    for first in (True, False):
        base = tmp_path / ("c" if first else "p")
        root = _root(base, ("alpha",))
        project = base / "proj"
        _sync(root, project, commands_first=first)
        set_commands(root, ())
        _sync(root, project, commands_first=first)
        pdir, cmd_index, role_index = _paths(project)
        assert not (pdir / "alpha.md").exists()
        assert (pdir / "developer.md").is_file()
        assert _lines(cmd_index) == set()
        assert _lines(role_index) == {"developer.md"}


def test_role_removal_does_not_delete_commands(tmp_path):
    root = _root(tmp_path, ("alpha",))
    project = tmp_path / "proj"
    _sync(root, project)
    config = _config()
    config["roles"] = []
    pconf = load_providers_config(REPO_ROOT, config)
    sync_prompts_for_continue(
        root, project, config, {}, SyncLog(), False, pconf,
        provider=_PROVIDER, active_set=_active(config))
    pdir, cmd_index, role_index = _paths(project)
    assert not (pdir / "developer.md").exists()
    assert (pdir / "alpha.md").is_file()
    assert _lines(cmd_index) == {"alpha.md"}
    assert _lines(role_index) == set()


def test_unmanaged_file_in_prompts_dir_survives(tmp_path):
    root = _root(tmp_path, ("alpha",))
    project = tmp_path / "proj"
    pdir, _, _ = _paths(project)
    pdir.mkdir(parents=True)
    (pdir / "mine.md").write_text("user prompt\n", encoding="utf-8")
    _sync(root, project)
    set_commands(root, ())
    _sync(root, project)
    assert (pdir / "mine.md").read_text(encoding="utf-8") == "user prompt\n"
