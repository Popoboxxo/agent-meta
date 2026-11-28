"""REQ-01: command layer markers and priority.

Priority: 2-platform > 1-generic > 0-external.

- AC-4.1: layer dirs 0-external/ and 2-platform/ exist with .gitkeep markers
- AC-4.2: platform file p-<name>.md overrides generic/external <name>.md
- AC-4.3: generic overrides external; fallbacks when higher layer is absent
"""
from __future__ import annotations

from pathlib import Path
from typing import Sequence

from scripts.lib.commands import collect_command_sources

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _tree(
    tmp_path: Path,
    ext: Sequence[tuple[str, str]] = (),
    gen: Sequence[tuple[str, str]] = (),
    plat: Sequence[tuple[str, str]] = (),
) -> Path:
    layers = (("0-external", ext), ("1-generic", gen), ("2-platform", plat))
    for layer, files in layers:
        d = tmp_path / "commands" / layer
        d.mkdir(parents=True)
        for name, body in files:
            (d / name).write_text(body, encoding="utf-8")
    return tmp_path


def _as_dict(result):
    return {name: src for src, name in result}


def test_real_root_layer_dirs_exist_and_gitkeep_not_collected():
    assert (_REPO_ROOT / "commands" / "0-external").is_dir()
    assert (_REPO_ROOT / "commands" / "2-platform").is_dir()
    assert (_REPO_ROOT / "commands" / "0-external" / ".gitkeep").is_file()
    assert (_REPO_ROOT / "commands" / "2-platform" / ".gitkeep").is_file()
    result = collect_command_sources(_REPO_ROOT, [])
    assert all(not name.startswith(".") and name.endswith(".md") for _, name in result)
    assert all(src.name != ".gitkeep" for src, _ in result)


def test_generic_overrides_external(tmp_path):
    root = _tree(tmp_path, ext=[("a.md", "ext")], gen=[("a.md", "gen")])
    got = _as_dict(collect_command_sources(root, []))
    assert got["a.md"].parent.name == "1-generic"


def test_platform_overrides_generic_and_external(tmp_path):
    root = _tree(
        tmp_path,
        ext=[("deploy.md", "e")],
        gen=[("deploy.md", "g")],
        plat=[("p-deploy.md", "p")],
    )
    result = collect_command_sources(root, ["p"])
    assert len(result) == 1
    got = _as_dict(result)
    assert list(got) == ["deploy.md"]
    assert got["deploy.md"].name == "p-deploy.md"


def test_fallbacks_when_higher_layer_absent(tmp_path):
    root = _tree(
        tmp_path,
        ext=[("only-ext.md", "e"), ("both.md", "e")],
        gen=[("both.md", "g")],
        plat=[("p-other.md", "p")],
    )
    got = _as_dict(collect_command_sources(root, ["p"]))
    assert got["only-ext.md"].parent.name == "0-external"
    assert got["both.md"].parent.name == "1-generic"
    assert got["other.md"].name == "p-other.md"


def test_unselected_platform_excluded_and_prefix_stripped(tmp_path):
    root = _tree(
        tmp_path,
        gen=[("deploy.md", "g")],
        plat=[("p-deploy.md", "p"), ("q-deploy.md", "q"), ("q-only.md", "q")],
    )
    got = _as_dict(collect_command_sources(root, ["p"]))
    assert got["deploy.md"].name == "p-deploy.md"
    assert "only.md" not in got
    assert "p-deploy.md" not in got
    assert not any(src.name.startswith("q-") for src in got.values())


def test_empty_platforms_ignores_platform_files(tmp_path):
    root = _tree(tmp_path, plat=[("p-a.md", "p")])
    assert collect_command_sources(root, []) == []


def test_missing_layer_dirs_tolerated(tmp_path):
    assert collect_command_sources(tmp_path, ["p"]) == []
