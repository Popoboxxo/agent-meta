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
from lib.log import SyncLog  # noqa: E402
from lib.variables import strip_inactive_conditional_blocks, substitute  # noqa: E402

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Whole-line if/else rather than an inline trailing {{#if}}: the stripper's
# inactive-block removal eats the following newline, which would merge the
# "Main branch" line into the platform line (see
# tests/test_optional_snippets_path_conditional.py).
_LINE = (
    "{{#if GIT_REMOTE_URL_SET}}**Git platform:** {{GIT_PLATFORM}} ({{GIT_REMOTE_URL}})"
    "{{else}}**Git platform:** {{GIT_PLATFORM}}{{/if}}"
)


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


def _render_line(tmp_path: Path, body: str) -> str:
    variables = _vars(tmp_path, body)
    text = strip_inactive_conditional_blocks(_LINE, variables)
    return substitute(text, variables, "git.md", SyncLog())


def test_git_remote_url_set_flag(tmp_path):
    assert _vars(tmp_path, "")["GIT_REMOTE_URL_SET"] == "false"
    assert _vars(tmp_path, "git:\n  remote-url: https://x/y\n")["GIT_REMOTE_URL_SET"] == "true"


def test_git_agent_has_no_empty_parens_without_remote_url(tmp_path):
    assert _render_line(tmp_path, "git:\n  platform: GitLab\n") == "**Git platform:** GitLab"


def test_git_agent_shows_url_when_set(tmp_path):
    out = _render_line(tmp_path, "git:\n  platform: GitHub\n  remote-url: https://github.com/o/r\n")
    assert out == "**Git platform:** GitHub (https://github.com/o/r)"


def test_template_line_is_the_gated_form():
    text = (_REPO_ROOT / "agents" / "1-generic" / "git.md").read_text(encoding="utf-8")
    assert _LINE in text and 'version: "2.1.5"' in text


def test_git_agent_keeps_blank_line_after_platform(tmp_path):
    variables = _vars(tmp_path, "git:\n  platform: GitLab\n")
    text = strip_inactive_conditional_blocks(_LINE + "\n\n**Main branch:** main\n", variables)
    assert substitute(text, variables, "git.md", SyncLog()) == (
        "**Git platform:** GitLab\n\n**Main branch:** main\n"
    )


def test_whitespace_only_remote_url_counts_as_absent(tmp_path):
    """Issue #1093 residual: ``remote-url: '   '`` must not render ``(   )``."""
    variables = _vars(tmp_path, "git:\n  platform: GitLab\n  remote-url: '   '\n")
    assert variables["GIT_REMOTE_URL_SET"] == "false"
    assert _render_line(tmp_path, "git:\n  platform: GitLab\n  remote-url: '   '\n") == (
        "**Git platform:** GitLab"
    )


def test_non_string_remote_url_counts_as_absent(tmp_path):
    """Issue #1093 residual: a YAML list must not render a Python repr.

    The schema warning for a non-string ``git.remote-url`` may still fire;
    only the rendered clause and the derived flag are asserted here.
    """
    body = "git:\n  platform: GitLab\n  remote-url:\n    - a\n    - b\n"
    variables = _vars(tmp_path, body)
    assert variables["GIT_REMOTE_URL_SET"] == "false"
    assert _render_line(tmp_path, body) == "**Git platform:** GitLab"


def test_git_agent_keeps_blank_line_after_remote_url(tmp_path):
    """The active remote-URL branch must also preserve the following blank line."""
    variables = _vars(
        tmp_path,
        "git:\n  platform: GitHub\n  remote-url: https://github.com/o/r\n",
    )
    text = strip_inactive_conditional_blocks(_LINE + "\n\n**Main branch:** main\n", variables)
    assert substitute(text, variables, "git.md", SyncLog()) == (
        "**Git platform:** GitHub (https://github.com/o/r)\n\n**Main branch:** main\n"
    )
