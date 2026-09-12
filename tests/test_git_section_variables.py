"""``git`` repo-settings section -> generated ``GIT_*`` variables (Feature B).

Precedence: explicit ``variables.GIT_*`` > ``git.<field>`` > default. The
``git.branch-prefixes`` map is data-only (Q3): it must not create any
``BRANCH_PREFIX_*`` variable.
"""
from __future__ import annotations

import sys
import textwrap
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

from lib.config import build_variables, load_config  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent


def _load(tmp_path: Path, body: str) -> dict:
    path = tmp_path / "project.yaml"
    path.write_text(
        textwrap.dedent(
            "project:\n  name: t\n  prefix: t\n  short: t\n"
            "ai-providers: [Claude]\n"
        ) + textwrap.dedent(body),
        encoding="utf-8",
    )
    return load_config(path)


def _vars(tmp_path: Path, body: str) -> dict:
    cfg = _load(tmp_path, body)
    variables, _ = build_variables(cfg, _REPO_ROOT, _REPO_ROOT)
    return variables


def test_git_section_sets_main_branch(tmp_path):
    variables = _vars(tmp_path, "git:\n  main-branch: develop\n")
    assert variables["GIT_MAIN_BRANCH"] == "develop"


def test_explicit_variable_wins_over_git_section(tmp_path):
    variables = _vars(
        tmp_path,
        "git:\n  main-branch: develop\n"
        "variables:\n  GIT_MAIN_BRANCH: trunk\n",
    )
    assert variables["GIT_MAIN_BRANCH"] == "trunk"


def test_defaults_without_git_section(tmp_path):
    variables = _vars(tmp_path, "")
    assert variables["GIT_MAIN_BRANCH"] == "main"


def test_remote_url_and_platform_from_git_section(tmp_path):
    variables = _vars(
        tmp_path,
        "git:\n  platform: GitLab\n  remote-url: https://gitlab.com/o/r\n",
    )
    assert variables["GIT_PLATFORM"] == "GitLab"
    assert variables["GIT_REMOTE_URL"] == "https://gitlab.com/o/r"


def test_branch_prefixes_produce_no_variable(tmp_path):
    variables = _vars(
        tmp_path,
        "git:\n  branch-prefixes:\n    feat: 'feature/'\n",
    )
    assert not any(key.startswith("BRANCH_PREFIX") for key in variables)
