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

from scripts.lib.agent_sync import _build_provider_vars, _git_sentinel_scope_vars
from scripts.lib.config import build_variables
from scripts.lib.log import SyncLog
from scripts.lib.variables import strip_inactive_conditional_blocks, substitute

_REPO_ROOT = Path(__file__).resolve().parent.parent
_GIT_TEMPLATE = _REPO_ROOT / "agents" / "1-generic" / "git.md"

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


# --- Task 2: rendered-template assertions (AC-1 / AC-2) -------------------


def _render_git(pc: dict, *, template: str | None = None) -> str:
    """Render the git agent template with the substitute/strip engine sync.py uses.

    A lightweight render (no full ``sync.py`` run): real project variables plus
    the provider vars from Task 1, then the same ``substitute`` → strip order as
    ``agent_sync._apply_content_pipeline``. Enough to assert the two inline
    provider-injected texts land in the output.
    """
    variables, _warnings = build_variables({}, _REPO_ROOT)
    variables = dict(variables)
    variables.update(_build_provider_vars(
        pc, "Claude", variables, Path(_REPO_ROOT), active_set=frozenset()
    ))
    source = template if template is not None else _GIT_TEMPLATE.read_text(encoding="utf-8")
    text = substitute(source, variables, "git.md", SyncLog())
    return strip_inactive_conditional_blocks(text, variables)


# Genuine PRE-change golden text (git.md before Task 2), taken from plan
# Interface Contracts — deliberately fixed literals, NOT derived from the
# current template. Exact-line equality below therefore fails on a stray '.'
# or any other drift, which the old reconstruction-based test could not catch.
_PRE_CHANGE_BASH_LINE = (
    "- **Bash** — all git/gh commands, "
    "always prefixed with `#agent-meta:agent=git` as the first line (see workflow step 0)"
)
_PRE_CHANGE_PARAGRAPH_END = "and the dispatcher must not forbid it to the git agent.\n"


def _single_line_starting(text: str, prefix: str) -> str:
    matches = [line for line in text.splitlines() if line.startswith(prefix)]
    assert len(matches) == 1, f"expected one line starting {prefix!r}, got {matches}"
    return matches[0]


def test_template_uses_both_placeholders():
    text = _GIT_TEMPLATE.read_text(encoding="utf-8")
    assert "{{GIT_SENTINEL_SCOPE_BLOCK}}" in text
    assert "{{GIT_SENTINEL_BASH_RULE}}" in text


def test_claude_render_has_gh_only_exception_and_tools_wording():
    rendered = _render_git(_pc("hook-agent-id"))

    # AC-1: exception sentence present in the rendered Claude output, with the
    # inline leading space landing right after the sentence-ending period.
    assert "git agent. Exception: for Bash calls that run only `gh`" in rendered
    assert "do NOT add the sentinel line" in rendered
    # AC-1: new <tools> wording for a hook-agent-id provider.
    assert _EXPECTED_BASH_RULE_WITH in rendered
    assert "`gh`-only calls without it" in rendered
    # No placeholder token survives into the rendered agent.
    assert "{{GIT_SENTINEL_SCOPE_BLOCK}}" not in rendered
    assert "{{GIT_SENTINEL_BASH_RULE}}" not in rendered
    # AC-1: the three git example blocks still carry the sentinel as first line.
    sentinel_first = [line for line in rendered.splitlines()
                      if line == "#agent-meta:agent=git"]
    assert len(sentinel_first) == 3


def test_render_without_capability_is_byte_identical_to_pre_change():
    rendered_after = _render_git(_pc())

    # AC-2 (fixed golden, independent of the modified template): the <tools>
    # line must equal the genuine pre-change text EXACTLY — a trailing '.'
    # after `step 0)` makes this fail. The paragraph must end where it did
    # before, with no exception sentence injected for a no-capability provider.
    assert _single_line_starting(
        rendered_after, "- **Bash** — all git/gh commands,"
    ) == _PRE_CHANGE_BASH_LINE
    assert _PRE_CHANGE_PARAGRAPH_END in rendered_after
    assert "Exception: for Bash calls" not in rendered_after

    # AC-2 (full render): compare against a frozen baseline template, not a
    # reconstruction of the modified template. #1335 payload attribution moved
    # git.md 2.2.1 -> 2.2.2 (three GIT_PAYLOAD_ATTRIBUTION blocks) and the guard
    # 1.14.1 -> 1.15.0, changing rendered output. The old git-blob pin
    # (aee986c8: git.md 2.2.0 + no #1329 line) was stale, so the golden is
    # re-pinned to a frozen copy of the intended #1335 baseline template. The
    # render path and this assertion are unchanged; the fixture is frozen so
    # future template drift still fails loudly.
    pre_change = _GOLDEN_BASELINE_TEMPLATE.read_text(encoding="utf-8")
    rendered_pre = _render_git(_pc(), template=pre_change)
    assert rendered_after == rendered_pre


# --- Task 3 / IC-7: variant C renders with ZERO sentinel literals ---------


def _render_c() -> str:
    return _render_git(_pc("hook-agent-id", "hook-role-field"))


def test_variant_c_has_zero_sentinel_literals():
    rendered = _render_c()
    assert "#agent-meta:agent=git" not in rendered
    assert "#agent-meta:agent=" not in rendered


def test_variant_c_step0_paragraph_is_exact_spec_scope_literal():
    rendered = _render_c()
    from tests.test_git_payload_attribution import SCOPE_C

    assert any(line == SCOPE_C for line in rendered.splitlines()), (
        "step-0 paragraph must be exactly _GIT_SENTINEL_SCOPE_WITH_BOTH_CAPS"
    )


def test_variant_c_tools_line_is_exact_spec_bash_rule():
    rendered = _render_c()
    from tests.test_git_payload_attribution import BASH_RULE_C

    assert _single_line_starting(
        rendered, "- **Bash** — all git/gh commands,"
    ) == "- **Bash** — all git/gh commands, " + BASH_RULE_C


def test_variant_c_has_three_git_example_blocks_without_sentinel():
    rendered = _render_c()
    # The three example commands keep their bodies; only the sentinel first
    # line is gone (section 0, state check, post-merge branch listing).
    assert "```bash\ngit status\ngit branch --show-current" in rendered
    assert "```bash\ngit branch --merged {{GIT_MAIN_BRANCH}}" not in rendered
    assert "git branch --merged main" in rendered
    assert rendered.count("\n```bash\n") >= 3
    assert "#agent-meta:agent=git" not in rendered


# --- Golden B byte-identical, Golden C new (IC-9) -------------------------


_GOLDEN_B = _REPO_ROOT / "tests" / "fixtures" / "slimming-golden" / "git.md"
_GOLDEN_C = _REPO_ROOT / "tests" / "fixtures" / "git-payload-attribution" / "git.md"
_GOLDEN_BASELINE_TEMPLATE = (
    _REPO_ROOT / "tests" / "fixtures" / "git-payload-attribution"
    / "git-baseline-template.md"
)


def test_golden_b_still_hunts_sentinel_and_is_untouched():
    golden_b = _GOLDEN_B.read_text(encoding="utf-8")
    # Frozen B golden: 2 prose mentions + 3 example-block sentinels.
    assert golden_b.count("#agent-meta:agent=git") == 5
    assert "Exception: for Bash calls that run only `gh`" in golden_b


def test_golden_c_matches_variant_c_render():
    assert _GOLDEN_C.exists(), "variant C golden fixture is missing"
    assert _GOLDEN_C.read_text(encoding="utf-8") == _render_c()
