"""Git sentinel scope provider variables (issue #1307, Task 1).

On providers with the ``hook-agent-id`` capability the rendered git agent must
scope its sentinel requirement: pure ``gh`` calls need no sentinel, ``git``
calls keep it. Providers without that capability keep today's text verbatim
(byte-identical output).

This module covers Task 1 only: the pure variable resolver, its merge into
``_build_provider_vars`` and escape-safe substitution of the inline values.
Task 2 adds the rendered-template assertions to this same file.
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.agent_sync import _git_sentinel_scope_vars
from scripts.lib.log import SyncLog
from scripts.lib.variables import substitute

_REPO_ROOT = Path(__file__).resolve().parent.parent

# Exact contract values from the approved plan (Interface Contracts).
_EXPECTED_SCOPE_WITH = (
    " Exception: for Bash calls that run only `gh` (no `git` in the call), "
    "do NOT add the sentinel line — it is not needed for `gh`, and the extra "
    "line makes allow rules such as `Bash(gh issue *)` not match. Run such "
    "`gh` calls as their own Bash call; never mix `gh` and `git` in one call. "
    "Every call that runs `git` keeps the sentinel as its first line."
)
_EXPECTED_SCOPE_WITHOUT = ""
_EXPECTED_BASH_RULE_WITH = (
    "`git` calls always prefixed with `#agent-meta:agent=git` as the first "
    "line, `gh`-only calls without it (see workflow step 0)"
)
_EXPECTED_BASH_RULE_WITHOUT = (
    "always prefixed with `#agent-meta:agent=git` as the first line "
    "(see workflow step 0)"
)


def _pc(*capabilities: str) -> dict:
    return {"capabilities": list(capabilities)}


# --- pure resolver ---------------------------------------------------------


def test_scope_vars_with_hook_agent_id():
    assert _git_sentinel_scope_vars(_pc("hook-agent-id")) == {
        "GIT_SENTINEL_SCOPE_BLOCK": _EXPECTED_SCOPE_WITH,
        "GIT_SENTINEL_BASH_RULE": _EXPECTED_BASH_RULE_WITH,
    }


def test_scope_vars_without_hook_agent_id_keep_legacy_text():
    assert _git_sentinel_scope_vars(_pc("some-other-cap")) == {
        "GIT_SENTINEL_SCOPE_BLOCK": _EXPECTED_SCOPE_WITHOUT,
        "GIT_SENTINEL_BASH_RULE": _EXPECTED_BASH_RULE_WITHOUT,
    }


def test_scope_vars_empty_pc_defaults_to_legacy_text():
    assert _git_sentinel_scope_vars({}) == {
        "GIT_SENTINEL_SCOPE_BLOCK": _EXPECTED_SCOPE_WITHOUT,
        "GIT_SENTINEL_BASH_RULE": _EXPECTED_BASH_RULE_WITHOUT,
    }


# --- merge into _build_provider_vars --------------------------------------


def _merged(pc: dict, tmp_path: Path) -> dict:
    from scripts.lib.agent_sync import _build_provider_vars

    return _build_provider_vars(pc, "Claude", {}, tmp_path, active_set=frozenset())


def test_build_provider_vars_merges_with_hook_agent_id(tmp_path):
    merged = _merged(_pc("hook-agent-id"), tmp_path)
    assert merged["GIT_SENTINEL_SCOPE_BLOCK"] == _EXPECTED_SCOPE_WITH
    assert merged["GIT_SENTINEL_BASH_RULE"] == _EXPECTED_BASH_RULE_WITH


def test_build_provider_vars_merges_without_hook_agent_id(tmp_path):
    merged = _merged(_pc(), tmp_path)
    assert merged["GIT_SENTINEL_SCOPE_BLOCK"] == _EXPECTED_SCOPE_WITHOUT
    assert merged["GIT_SENTINEL_BASH_RULE"] == _EXPECTED_BASH_RULE_WITHOUT


# --- module constants ------------------------------------------------------


def test_texts_live_as_module_constants():
    import scripts.lib.agent_sync as ag

    assert ag._GIT_SENTINEL_SCOPE_WITH_HOOK_AGENT_ID == _EXPECTED_SCOPE_WITH
    assert ag._GIT_SENTINEL_SCOPE_WITHOUT_HOOK_AGENT_ID == _EXPECTED_SCOPE_WITHOUT
    assert ag._GIT_SENTINEL_BASH_RULE_WITH_HOOK_AGENT_ID == _EXPECTED_BASH_RULE_WITH
    assert ag._GIT_SENTINEL_BASH_RULE_WITHOUT_HOOK_AGENT_ID == _EXPECTED_BASH_RULE_WITHOUT


# --- escape-safe substitution (backticks + leading space) -----------------


def test_substitution_preserves_backticks_and_leading_space():
    merged = _merged(_pc("hook-agent-id"), tmp_path=Path(_REPO_ROOT))
    template = (
        "must not forbid it to the git agent.{{GIT_SENTINEL_SCOPE_BLOCK}}\n"
        "- **Bash** — all git/gh commands, {{GIT_SENTINEL_BASH_RULE}}"
    )
    rendered = substitute(template, merged, "git.md", SyncLog())

    # Leading space of the scope value sits inline right after the period.
    assert "git agent. Exception: for Bash calls" in rendered
    # Backticks survive verbatim (no re.sub escape interpretation).
    assert "`gh`" in rendered
    assert "`Bash(gh issue *)`" in rendered
    assert "`#agent-meta:agent=git`" in rendered
    assert rendered.endswith(_EXPECTED_BASH_RULE_WITH)


def test_substitution_without_capability_is_byte_identical():
    merged = _merged(_pc(), tmp_path=Path(_REPO_ROOT))
    template = (
        "must not forbid it to the git agent.{{GIT_SENTINEL_SCOPE_BLOCK}}\n"
        "- **Bash** — all git/gh commands, {{GIT_SENTINEL_BASH_RULE}}"
    )
    rendered = substitute(template, merged, "git.md", SyncLog())

    assert rendered == (
        "must not forbid it to the git agent.\n"
        "- **Bash** — all git/gh commands, " + _EXPECTED_BASH_RULE_WITHOUT
    )
