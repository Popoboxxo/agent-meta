"""Issues #983 / #1037: placeholder resolution, escapes and the D3(a) grace.

Three contracts are pinned here:

1. **D3(a)** — a placeholder that is *referenced* in a template but *not
   defined* (no builder, no project variable) must fail the sync instead of
   leaking a literal token / dropping the line. Because that is a behaviour
   change it runs through a version-driven grace window
   (``variables._UNRESOLVED_PLACEHOLDER_GRACE_UNTIL``, data not a code branch):
   until the window closes the render warns and names the future ``SyncError``
   text verbatim; afterwards the very same text is raised.
2. **#983** — the three placeholders that had no filler are classified
   (``TECH_STACK``: project variable with a builder-derived fallback;
   ``AGENT_RULES`` / ``EXTERNAL_DOCS_LANGUAGE``: reference examples in the
   non-deployable ``_reference-agent.md``, escaped as ``{{%VAR%}}``). The
   unknown-template ratchet is empty.
3. **#1037** — derivable variables have builders: ``project.description``
   seeds ``PROJECT_DESCRIPTION`` and ``AGENT_META_REPO`` is derived from the
   submodule URL or the agent-meta checkout's own git remote.
"""
from __future__ import annotations

from pathlib import Path

import pytest

import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from lib.config import build_variables  # noqa: E402
from lib.consistency import placeholders as _ph  # noqa: E402
from lib.io import SyncError  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.variables import (  # noqa: E402
    _UNRESOLVED_PLACEHOLDER_GRACE_UNTIL,
    derive_agent_meta_repo,
    parse_repo_slug,
    strip_inactive_conditional_blocks,
    substitute,
    unknown_placeholder_error_text,
    unresolved_placeholder_grace_active,
    unresolved_placeholder_notice,
)

REFERENCE_AGENT = ROOT / "agents" / "1-generic" / "_reference-agent.md"


# ---------------------------------------------------------------------------
# D3(a): undefined placeholder → grace WARN, then hard SyncError
# ---------------------------------------------------------------------------

def _render(text: str, variables: dict | None = None) -> tuple[str, SyncLog]:
    log = SyncLog()
    return substitute(text, variables or {}, "probe/template.md", log), log


def test_undefined_placeholder_warns_and_names_the_future_error():
    """Inside the grace window the token stays AND the WARN announces the error."""
    assert unresolved_placeholder_grace_active(ROOT) is True
    rendered, log = _render("line with {{NOT_DEFINED_ANYWHERE}} here")

    # Nothing is silently swallowed: the placeholder is kept, not blanked.
    assert "{{NOT_DEFINED_ANYWHERE}}" in rendered
    warnings = [w for w in log.warnings if "NOT_DEFINED_ANYWHERE" in w]
    assert len(warnings) == 1
    notice = warnings[0]
    # The WARN states the grace deadline and quotes the exact future error text.
    expected_error = unknown_placeholder_error_text(
        "NOT_DEFINED_ANYWHERE", "probe/template.md")
    assert "D3(a) grace" in notice
    assert ".".join(map(str, _UNRESOLVED_PLACEHOLDER_GRACE_UNTIL)) in notice
    assert expected_error in notice
    assert notice.endswith(unresolved_placeholder_notice(
        "NOT_DEFINED_ANYWHERE", "probe/template.md"))


def test_undefined_placeholder_errors_once_the_grace_window_has_passed(monkeypatch):
    """The hard branch is the SAME message the WARN announced — no drift."""
    # Pure data: moving the window into the past flips the behaviour, no code path.
    monkeypatch.setattr(
        "lib.variables._UNRESOLVED_PLACEHOLDER_GRACE_UNTIL", (0, 0, 1))
    assert unresolved_placeholder_grace_active(ROOT) is False

    with pytest.raises(SyncError) as excinfo:
        _render("line with {{NOT_DEFINED_ANYWHERE}} here")
    assert str(excinfo.value) == unknown_placeholder_error_text(
        "NOT_DEFINED_ANYWHERE", "probe/template.md")


def test_defined_placeholder_never_warns_in_either_mode(monkeypatch):
    monkeypatch.setattr(
        "lib.variables._UNRESOLVED_PLACEHOLDER_GRACE_UNTIL", (0, 0, 1))
    rendered, log = _render("x {{KNOWN}} y", {"KNOWN": "ok"})
    assert rendered == "x ok y"
    assert log.warnings == []


def test_escaped_placeholder_is_exempt_in_both_modes(monkeypatch):
    """``{{%VAR%}}`` renders literally, never warns and never aborts — the
    escape is the sanctioned way to ship a literal token."""
    rendered, log = _render("docs: {{%SOME_VAR%}}")
    assert rendered == "docs: {{SOME_VAR}}"
    assert log.warnings == []

    monkeypatch.setattr(
        "lib.variables._UNRESOLVED_PLACEHOLDER_GRACE_UNTIL", (0, 0, 1))
    rendered, _log = _render("docs: {{%SOME_VAR%}}")
    assert rendered == "docs: {{SOME_VAR}}"


def test_grace_window_reads_version_data(tmp_path):
    """Inside/outside is decided by ``<root>/VERSION`` against the window."""
    (tmp_path / "VERSION").write_text("9.9.9\n", encoding="utf-8")
    assert unresolved_placeholder_grace_active(tmp_path) is False
    (tmp_path / "VERSION").write_text("2.0.0-beta.4\n", encoding="utf-8")
    assert unresolved_placeholder_grace_active(tmp_path) is True
    (tmp_path / "VERSION").unlink()
    # Unreadable version = still announced, never a silent hard flip.
    assert unresolved_placeholder_grace_active(tmp_path) is True


# ---------------------------------------------------------------------------
# D3(a) follow-up: a token inside an INACTIVE conditional block never reaches
# the output and therefore must never warn — nor abort once the grace closes.
# Renderers (rules.sync_rules, context embedded rules) substitute BEFORE
# strip_inactive_conditional_blocks, so `substitute()` decides liveness
# against the stripped text without changing its own output.
# ---------------------------------------------------------------------------

USE_ORCHESTRATOR = ROOT / "rules" / "1-generic" / "use-orchestrator.md"


def _strict_rule_vars() -> dict:
    """The render state of `use-orchestrator.md` in a strict-mode project.

    Mirrors the real `build_variables()` keys for the conditional gates the
    template uses, so the nested blocks resolve exactly like a real sync.
    `PIPELINE_DETAILS_DIR` is deliberately absent: it is only injected per
    provider in the sync pipeline, not by the variable builder.
    """
    return {
        "ORCH_MODE_MAIN_CHAT": "false",
        "ORCH_MODE_STRICT": "true",
        "ORCH_MODE_ADVISORY": "false",
        "ORCH_MODE_DISABLED": "false",
        "GATE_ENFORCED": "true",
        "GATE_PARTIAL": "false",
        "GATE_ADVISORY": "false",
        "SPEC_PLAN_WORKFLOW_ENABLED": "false",
        "AUTO_COMMIT_ENABLED": "false",
        "NATIVE_EXTENSIONS_ENABLED": "false",
        "NATIVE_EXTENSIONS_WHITELIST_ACTIVE": "false",
        "ROLE_GIT_ACTIVE": "true",
        "DIRECT_DISPATCH_ENABLED": "false",
        "DIRECT_DISPATCH_SECTION": "",
        "A2A_PROTOCOL_ENABLED": "false",
        "CHECKPOINTING_ENABLED": "false",
    }


def test_placeholder_in_inactive_block_never_warns(monkeypatch):
    """`{{PIPELINE_DETAILS_DIR}}` lives only in the inactive main-chat branch.

    Inside the grace window it used to warn on every sync (seven providers x
    provider-less render paths). The liveness probe keeps it silent.
    """
    log = SyncLog()
    rendered = substitute(
        USE_ORCHESTRATOR.read_text(encoding="utf-8"),
        _strict_rule_vars(), "rules/1-generic/use-orchestrator.md", log)

    assert not [w for w in log.warnings if "PIPELINE_DETAILS_DIR" in w]
    # The caller still strips afterwards; the token cannot reach the output.
    assert "PIPELINE_DETAILS_DIR" not in strip_inactive_conditional_blocks(
        rendered, _strict_rule_vars())


def test_placeholder_in_inactive_block_cannot_abort_after_grace(monkeypatch):
    """At 2.1.0 the render must still succeed: the trap is closed.

    The whole `use-orchestrator.md` is rendered with the grace window moved
    into the past. Before the fix the first undefined token of an inactive
    branch (`{{DIRECT_DISPATCH_SECTION}}`, `{{PIPELINE_DETAILS_DIR}}`, ...)
    aborted the sync.
    """
    monkeypatch.setattr(
        "lib.variables._UNRESOLVED_PLACEHOLDER_GRACE_UNTIL", (0, 0, 1))
    assert unresolved_placeholder_grace_active(ROOT) is False

    log = SyncLog()
    rendered = substitute(
        USE_ORCHESTRATOR.read_text(encoding="utf-8"),
        _strict_rule_vars(), "rules/1-generic/use-orchestrator.md", log)

    assert log.warnings == []
    output = strip_inactive_conditional_blocks(rendered, _strict_rule_vars())
    assert "PIPELINE_DETAILS_DIR" not in output
    assert "Main-Chat Mode" not in output
    assert "CRITICAL GATE" in output


def test_placeholder_in_live_output_still_aborts_after_grace(monkeypatch):
    """The same token DOES abort once it survives the conditional strip.

    Main-chat mode activates the branch, so `{{PIPELINE_DETAILS_DIR}}` is live
    output — all other tokens of the branch are defined to prove the error
    names exactly the token that reaches the user.
    """
    monkeypatch.setattr(
        "lib.variables._UNRESOLVED_PLACEHOLDER_GRACE_UNTIL", (0, 0, 1))
    variables = _strict_rule_vars()
    variables.update({
        "ORCH_MODE_MAIN_CHAT": "true",
        "ORCH_MODE_STRICT": "false",
        "INTENT_ROUTING_TABLE": "| route | agent |",
        "A2A_HANDOFF_BLOCK": "handoff",
        "STATUS_TABLE_BLOCK": "status",
    })

    with pytest.raises(SyncError) as excinfo:
        substitute(
            USE_ORCHESTRATOR.read_text(encoding="utf-8"),
            variables, "rules/1-generic/use-orchestrator.md", SyncLog())

    assert "PIPELINE_DETAILS_DIR" in str(excinfo.value)


def test_liveness_probe_is_per_token_not_per_render(monkeypatch):
    """Mechanism pinned synthetically: inactive silent, active/outside raises."""
    monkeypatch.setattr(
        "lib.variables._UNRESOLVED_PLACEHOLDER_GRACE_UNTIL", (0, 0, 1))
    template = "{{#if GATE_ENFORCED}}on{{else}}{{DEAD_TOKEN}}{{/if}}\n{{LIVE_TOKEN}}"

    # Live token outside any conditional → still a hard error.
    with pytest.raises(SyncError) as excinfo:
        substitute(template, {"GATE_ENFORCED": "true"}, "probe", SyncLog())
    assert "LIVE_TOKEN" in str(excinfo.value)

    # Only the inactive-branch token: silent, kept for the caller's strip.
    out = substitute(
        "{{#if GATE_ENFORCED}}on{{else}}{{DEAD_TOKEN}}{{/if}}",
        {"GATE_ENFORCED": "true"}, "probe", SyncLog())
    assert "{{DEAD_TOKEN}}" in out
    assert strip_inactive_conditional_blocks(
        out, {"GATE_ENFORCED": "true"}) == "on"


# ---------------------------------------------------------------------------
# #983: reference examples render literally, ratchet is empty
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("name", ["TECH_STACK", "AGENT_RULES",
                                  "EXTERNAL_DOCS_LANGUAGE"])
def test_reference_agent_examples_render_literally(name):
    """The didactic examples survive as literal text, not as an unknown token."""
    source = REFERENCE_AGENT.read_text(encoding="utf-8")
    assert f"{{{{%{name}%}}}}" in source, f"{name} is not escaped in the reference"

    rendered, log = _render(source)
    assert f"{{{{{name}}}}}" in rendered
    assert f"{{{{%{name}%}}}}" not in rendered
    assert "{{%" not in rendered
    assert not [w for w in log.warnings if name in w]


def test_unknown_template_ratchet_is_empty_and_repo_is_clean():
    assert _ph._UNKNOWN_TEMPLATE_RATCHET == frozenset()
    assert _ph.check_builder_known_set(ROOT) == []
    for name in ("TECH_STACK", "AGENT_RULES", "EXTERNAL_DOCS_LANGUAGE"):
        findings = [
            f for f in _ph.check_builder_known_set(ROOT) if name in f.message
        ]
        assert findings == []


def test_tech_stack_is_registered_as_a_project_variable():
    """Classification: project variable (sharkord release notes), so it must be
    in the registered set — the fallback from PROJECT_LANGUAGES is covered
    above. It is NOT builder-derived on an empty config."""
    assert "TECH_STACK" in _ph._BUILTIN_VARS
    assert "TECH_STACK" not in _ph._UNKNOWN_TEMPLATE_RATCHET
    empty_config_vars = _ph.derive_builder_vars(ROOT)
    assert "TECH_STACK" not in empty_config_vars


# ---------------------------------------------------------------------------
# #1037: project.description → PROJECT_DESCRIPTION
# ---------------------------------------------------------------------------

def test_project_description_is_seeded_from_the_project_block():
    config = {
        "project": {"name": "demo", "prefix": "dm", "short": "demo",
                    "description": "One-line demo description."},
        "ai-providers": ["Claude"],
        "roles": ["developer"],
    }
    variables, _ = build_variables(config, ROOT)
    assert variables["PROJECT_DESCRIPTION"] == "One-line demo description."
    # PROJECT_GOAL / PROJECT_CONTEXT derive from it as before (issue #733).
    assert variables["PROJECT_GOAL"] == "One-line demo description."
    assert variables["PROJECT_CONTEXT"] == "One-line demo description."


def test_explicit_project_description_variable_wins_over_project_block():
    config = {
        "project": {"name": "demo", "prefix": "dm", "short": "demo",
                    "description": "from project block"},
        "variables": {"PROJECT_DESCRIPTION": "from variables"},
    }
    variables, _ = build_variables(config, ROOT)
    assert variables["PROJECT_DESCRIPTION"] == "from variables"


def test_missing_project_description_is_not_silently_blanked():
    """No project.description → the key stays undefined so D3(a) reports it."""
    variables, _ = build_variables(
        {"project": {"name": "demo", "prefix": "dm", "short": "demo"}}, ROOT)
    assert "PROJECT_DESCRIPTION" not in variables


# ---------------------------------------------------------------------------
# #1037: AGENT_META_REPO derivation
# ---------------------------------------------------------------------------

@pytest.mark.parametrize("url,expected", [
    ("https://github.com/acme/agent-meta.git", "acme/agent-meta"),
    ("git@github.com:acme/agent-meta.git", "acme/agent-meta"),
    ("ssh://git@host:2222/acme/agent-meta", "acme/agent-meta"),
    ("https://gitlab.example.com/group/sub/agent-meta.git", "sub/agent-meta"),
    ("acme/agent-meta", "acme/agent-meta"),
    ("", ""),
    ("git@host:bare-repo", ""),
])
def test_parse_repo_slug(url, expected):
    assert parse_repo_slug(url) == expected


def _embedded_project(tmp_path: Path, url: str) -> tuple[Path, Path]:
    """project_root with an embedded agent_meta checkout + .gitmodules."""
    project_root = tmp_path / "project"
    agent_meta_root = project_root / ".agent-meta"
    agent_meta_root.mkdir(parents=True)
    (project_root / ".gitmodules").write_text(
        '[submodule ".agent-meta"]\n'
        "\tpath = .agent-meta\n"
        f"\turl = {url}\n",
        encoding="utf-8",
    )
    return project_root, agent_meta_root


def test_agent_meta_repo_is_derived_from_the_submodule_url(tmp_path):
    project_root, agent_meta_root = _embedded_project(
        tmp_path, "https://github.com/acme/forked-agent-meta.git")
    variables, _ = build_variables(
        {"project": {"name": "demo", "prefix": "dm", "short": "demo"}},
        agent_meta_root, project_root)
    assert variables["AGENT_META_REPO"] == "acme/forked-agent-meta"


def test_agent_meta_repo_is_derived_from_the_checkout_git_remote(tmp_path):
    """Self-hosting / no .gitmodules: the checkout's own origin is the source."""
    (tmp_path / ".git").mkdir()
    (tmp_path / ".git" / "config").write_text(
        "[core]\n\trepositoryformatversion = 0\n"
        '[remote "origin"]\n\turl = git@github.com:acme/agent-meta.git\n',
        encoding="utf-8",
    )
    assert derive_agent_meta_repo(tmp_path) == "acme/agent-meta"
    variables, _ = build_variables(
        {"project": {"name": "demo", "prefix": "dm", "short": "demo"}},
        tmp_path, tmp_path)
    assert variables["AGENT_META_REPO"] == "acme/agent-meta"


def test_agent_meta_repo_is_derived_through_a_submodule_gitdir_pointer(tmp_path):
    """Embedded checkout: ``.git`` is a file pointing at .git/modules/<name>."""
    modules = tmp_path / "superproject" / ".git" / "modules" / ".agent-meta"
    modules.mkdir(parents=True)
    (modules / "config").write_text(
        '[remote "origin"]\n\turl = https://github.com/acme/agent-meta.git\n',
        encoding="utf-8")
    checkout = tmp_path / "superproject" / ".agent-meta"
    checkout.mkdir()
    (checkout / ".git").write_text(
        "gitdir: ../.git/modules/.agent-meta\n", encoding="utf-8")
    assert derive_agent_meta_repo(checkout) == "acme/agent-meta"


def test_explicit_agent_meta_repo_wins_over_derivation(tmp_path):
    project_root, agent_meta_root = _embedded_project(
        tmp_path, "https://github.com/acme/derived.git")
    variables, _ = build_variables(
        {"project": {"name": "demo", "prefix": "dm", "short": "demo"},
         "variables": {"AGENT_META_REPO": "explicit/repo"}},
        agent_meta_root, project_root)
    assert variables["AGENT_META_REPO"] == "explicit/repo"


def test_underivable_agent_meta_repo_is_reported_not_guessed(tmp_path):
    """D2: a missing key is a WARN — never a hardcoded "assume upstream"."""
    variables, warnings = build_variables(
        {"project": {"name": "demo", "prefix": "dm", "short": "demo"}},
        tmp_path, tmp_path)
    assert "AGENT_META_REPO" not in variables
    assert any(w.startswith("variables.agent-meta-repo-unresolved")
               for w in warnings)


# ---------------------------------------------------------------------------
# #983: TECH_STACK fallback
# ---------------------------------------------------------------------------

def test_tech_stack_falls_back_to_project_languages():
    variables, _ = build_variables(
        {"project": {"name": "demo", "prefix": "dm", "short": "demo"},
         "variables": {"PROJECT_LANGUAGES": "TypeScript, Bun"}}, ROOT)
    assert variables["TECH_STACK"] == "TypeScript, Bun"


def test_explicit_tech_stack_wins():
    variables, _ = build_variables(
        {"project": {"name": "demo", "prefix": "dm", "short": "demo"},
         "variables": {"PROJECT_LANGUAGES": "TypeScript",
                       "TECH_STACK": "TypeScript, Mediasoup"}}, ROOT)
    assert variables["TECH_STACK"] == "TypeScript, Mediasoup"
