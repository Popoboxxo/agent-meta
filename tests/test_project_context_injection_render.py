"""Render-side tests for project-context injection (issue #1187).

Shared by T4-T10. Each task adds its own section; keep section boundaries so
later tasks can append without disturbing existing tests.
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_ROOT / "scripts"))

from lib.agent_sync import _build_provider_vars  # noqa: E402
from lib.config import _PROJECT_CONTEXT_POINTER_TEXTS  # noqa: E402


# ---------------------------------------------------------------------------
# T4 — provider_vars
# ---------------------------------------------------------------------------


def test_provider_vars_default_injected_true_without_config():
    """No config/scope: conservative default is injected=true + mode=all.

    Backward compatibility for tests/test_orchestrator_name_dispatch.py:56.
    """
    merged = _build_provider_vars(
        {}, "Claude", {"PROJECT_CONTEXT": "P"}, _ROOT, active_set=frozenset()
    )
    assert merged["PROJECT_CONTEXT_INJECTED"] == "true"
    assert merged["PROJECT_CONTEXT_MODE"] == "all"


def test_provider_vars_carry_scope_from_variables():
    """A resolved scope travels through; INJECTED stays true here (T5 decides
    the per-role value)."""
    scope = {
        "mode": "core",
        "whitelist": ["developer"],
        "orchestrator": "inherit",
        "orchestrator_roles": ("orchestrator",),
        "pointer_text": _PROJECT_CONTEXT_POINTER_TEXTS["en"],
        "pointer_language": "en",
        "present": True,
    }
    merged = _build_provider_vars(
        {}, "Claude", {"_PROJECT_CONTEXT_SCOPE": scope}, _ROOT,
        active_set=frozenset(),
    )
    assert merged["PROJECT_CONTEXT_INJECTED"] == "true"
    assert merged["PROJECT_CONTEXT_MODE"] == "core"


def test_provider_vars_carry_formatted_pointer_per_provider():
    """The per-provider context file is substituted into the pointer, and a
    configured German pointer_text stays German (D8)."""
    cases = [
        ("Claude", "CLAUDE.md", None, "Project context"),
        ("Gemini", "AGENTS.md", None, "Project context"),
        ("Opencode", ".continue/rules/project-context.md",
         _PROJECT_CONTEXT_POINTER_TEXTS["de"], "Projektkontext"),
    ]
    for provider, context_file, pointer_text, expected_lead in cases:
        variables = {}
        if pointer_text is not None:
            variables["_PROJECT_CONTEXT_SCOPE"] = {"pointer_text": pointer_text}
        merged = _build_provider_vars(
            {"context_file": context_file}, provider, variables, _ROOT,
            active_set=frozenset(),
        )
        pointer = merged["_PROJECT_CONTEXT_POINTER"]
        assert context_file in pointer
        assert "{context_file}" not in pointer
        assert pointer.startswith(expected_lead)


# ---------------------------------------------------------------------------
# T5 — matrix / apply_scope
# ---------------------------------------------------------------------------


def _t5_impl():
    """Lazy imports: before T5 lands only these tests fail, T4 stays green."""
    from lib.config import project_context_injected_for_role
    from lib.agent_sync import apply_project_context_scope

    return project_context_injected_for_role, apply_project_context_scope


def _pc_scope(mode="all", whitelist=(), orchestrator="inherit",
              orchestrator_roles=("orchestrator",)):
    """Minimal resolved scope (spec §3.1) for matrix/scope tests."""
    return {
        "mode": mode,
        "whitelist": list(whitelist),
        "orchestrator": orchestrator,
        "orchestrator_roles": tuple(orchestrator_roles),
        "pointer_text": _PROJECT_CONTEXT_POINTER_TEXTS["en"],
        "pointer_language": "en",
        "present": True,
    }


# (mode, whitelist, orchestrator, role, expected) — spec §3.1 tables.
_MATRIX_CASES = [
    # all: everyone, except orchestrator roles when exclude wins (D6).
    ("all", (), "inherit", "developer", True),
    ("all", (), "inherit", "orchestrator", True),
    ("all", (), "exclude", "developer", True),
    ("all", (), "exclude", "orchestrator", False),
    # core: nobody, unless include promotes the orchestrator set.
    ("core", (), "inherit", "orchestrator", False),
    ("core", (), "include", "orchestrator", True),
    ("core", (), "include", "developer", False),
    # core+orchestrator: only the orchestrator set; exclude degenerates to core.
    ("core+orchestrator", (), "inherit", "orchestrator", True),
    ("core+orchestrator", (), "inherit", "developer", False),
    ("core+orchestrator", (), "exclude", "orchestrator", False),
    # core+whitelist: only the whitelist; orchestrator set only with include.
    ("core+whitelist", ("developer",), "inherit", "developer", True),
    ("core+whitelist", ("developer",), "inherit", "orchestrator", False),
    ("core+whitelist", ("developer",), "inherit", "planner", False),
    ("core+whitelist", ("developer",), "include", "orchestrator", True),
    ("core+whitelist", ("developer",), "exclude", "orchestrator", False),
    # A whitelisted role that is also a primary-role stays included on inherit.
    ("core+whitelist", ("orchestrator", "developer"), "inherit",
     "orchestrator", True),
]


@pytest.mark.parametrize(
    "mode, whitelist, orchestrator, role, expected",
    _MATRIX_CASES,
    ids=[f"{c[0]}-{c[2]}-{c[3]}" for c in _MATRIX_CASES],
)
def test_injection_matrix(mode, whitelist, orchestrator, role, expected):
    """Pure decision matrix from spec §3.1 (all mode × orchestrator combos)."""
    decision, _ = _t5_impl()
    scope = _pc_scope(mode, whitelist, orchestrator)
    assert decision(scope, role) is expected


def test_injection_matrix_uses_overridden_orchestrator_roles():
    """D5: an override replaces the default set — no silent mixing in."""
    decision, _ = _t5_impl()
    scope = _pc_scope(
        "core+orchestrator", orchestrator_roles=("senior-developer",))
    assert decision(scope, "senior-developer") is True
    assert decision(scope, "orchestrator") is False


def test_injection_matrix_empty_orchestrator_roles():
    """D5: an explicitly empty orchestrator set injects nothing."""
    decision, _ = _t5_impl()
    scope = _pc_scope("core+orchestrator", orchestrator_roles=())
    for role in ("orchestrator", "senior-developer", "developer"):
        assert decision(scope, role) is False


def test_apply_scope_blanks_context_for_excluded_role():
    """Excluded roles lose their paragraph and carry injected=false."""
    _, apply_scope = _t5_impl()
    merged = {"PROJECT_CONTEXT": "PARA", "PROJECT_CONTEXT_INJECTED": "true"}
    result = apply_scope(merged, "developer", _pc_scope("core"))
    assert result is False
    assert merged["PROJECT_CONTEXT"] == ""
    assert merged["PROJECT_CONTEXT_INJECTED"] == "false"


def test_apply_scope_keeps_paragraph_for_included_role():
    """Included roles keep their paragraph and carry injected=true."""
    _, apply_scope = _t5_impl()
    merged = {"PROJECT_CONTEXT": "PARA", "PROJECT_CONTEXT_INJECTED": "false"}
    result = apply_scope(merged, "developer", _pc_scope("all"))
    assert result is True
    assert merged["PROJECT_CONTEXT"] == "PARA"
    assert merged["PROJECT_CONTEXT_INJECTED"] == "true"


def test_apply_scope_does_not_mutate_shared_variables():
    """The caller's variables dict keeps PROJECT_CONTEXT (no role leakage)."""
    _, apply_scope = _t5_impl()
    variables = {"PROJECT_CONTEXT": "PARA", "PROJECT_CONTEXT_INJECTED": "true"}
    merged = dict(variables)
    apply_scope(merged, "developer", _pc_scope("core"))
    assert variables["PROJECT_CONTEXT"] == "PARA"
    assert variables["PROJECT_CONTEXT_INJECTED"] == "true"


# ---------------------------------------------------------------------------
# T6 — pointer
# ---------------------------------------------------------------------------

# The English default is a single source of truth in config.py (D8). Keep this
# copy in the TEST only as the expected value; the renderer must not duplicate
# the sentence (test_pointer_line_text_is_exact).
_T6_EXPECTED_EN = (
    "Project context: read `{context_file}` first — it is the single source "
    "for project-specific facts (embedded here only when "
    "`project-context-injection.mode` includes this role)."
)


def _t6_impl():
    """Lazy imports: T6 helpers stay importable before T6 lands (T4/T5 green)."""
    from lib.agent_sync import insert_project_context_pointer
    from lib.config import resolve_project_context_scope
    from lib.log import SyncLog
    from lib.providers import load_providers_config

    return insert_project_context_pointer, resolve_project_context_scope, SyncLog, load_providers_config


def _t6_scope(section):
    """Resolve a project-context-injection config section into a scope dict."""
    _, resolve_scope, _, load_providers = _t6_impl()
    return resolve_scope(
        {"project-context-injection": section}, _ROOT,
        provider_config=load_providers(_ROOT))


def _t6_pointer_text(scope, provider):
    """Format a provider's pointer exactly as the renderer seam does (T4)."""
    from lib.agent_sync import _build_provider_vars
    from lib.providers import load_providers_config

    pc = dict(load_providers_config(_ROOT)[provider])
    merged = _build_provider_vars(
        pc, provider, {"_PROJECT_CONTEXT_SCOPE": scope}, _ROOT,
        active_set=frozenset())
    return merged["_PROJECT_CONTEXT_POINTER"]


@pytest.fixture(scope="module")
def t6_core_run(tmp_path_factory):
    """One real Claude render in core+whitelist (only ``planner`` injected).

    Covers all three fallback groups plus label cleanup in a single run:
    developer (</context>), intern-developer (</workflow>), mammouth-expert
    (EOF + note), orchestrator (dangling label). German is the configured
    pointer language, so the German default is exercised end-to-end.
    """
    from lib.config import resolve_project_context_scope
    from lib.log import SyncLog
    from lib.providers import load_providers_config
    from lib.agent_sync import sync_agents_for_provider

    provider_config = load_providers_config(_ROOT)
    scope = resolve_project_context_scope(
        {"project-context-injection": {
            "mode": "core+whitelist", "whitelist": ["planner"],
            "pointer-language": "de",
        }},
        _ROOT, provider_config=provider_config)
    config = {"project": {"name": "T6"}, "platforms": []}
    variables = {
        "PROJECT_CONTEXT": "PARA", "COMMUNICATION_LANGUAGE": "Deutsch",
        "_PROJECT_CONTEXT_SCOPE": scope,
    }
    project_root = tmp_path_factory.mktemp("t6-core")
    log = SyncLog()
    sync_agents_for_provider(
        _ROOT, project_root, config, variables, log, dry_run=False,
        provider="Claude", provider_config=provider_config)
    artifacts = {
        path.stem: path.read_text(encoding="utf-8")
        for path in (project_root / ".claude" / "agents").glob("*.md")
    }
    return {
        "artifacts": artifacts,
        "log": log,
        "pointer": scope["pointer_text"].format(context_file="CLAUDE.md"),
    }


def test_pointer_line_text_is_exact():
    """The English default is one line in config.py; no renderer-local copy."""
    insert, _, _, _ = _t6_impl()
    assert insert is not None
    assert _PROJECT_CONTEXT_POINTER_TEXTS["en"] == _T6_EXPECTED_EN
    assert "\n" not in _T6_EXPECTED_EN
    assert "`{context_file}`" in _T6_EXPECTED_EN
    source = (_ROOT / "scripts" / "lib" / "agent_sync.py").read_text(encoding="utf-8")
    assert "it is the single source for" not in source


def test_pointer_german_default_used(t6_core_run):
    """A German scope renders the German default (no English leak, D8)."""
    content = t6_core_run["artifacts"]["developer"]
    assert "Projektkontext: lies zuerst `CLAUDE.md`" in content
    assert "Project context: read" not in content


def test_pointer_text_override_used_verbatim():
    """``pointer-text`` wins verbatim over both language defaults."""
    insert, _, SyncLog, _ = _t6_impl()
    scope = _t6_scope({
        "mode": "core+whitelist", "whitelist": ["planner"],
        "pointer-text": "See `{context_file}` for project facts.",
    })
    pointer = _t6_pointer_text(scope, "Claude")
    assert pointer == "See `CLAUDE.md` for project facts."
    rendered = insert("<context>\nfoo\n</context>\n", pointer, "developer",
                      "developer.md", SyncLog())
    assert "See `CLAUDE.md` for project facts." in rendered.splitlines()
    assert "Project context" not in rendered
    assert "Projektkontext" not in rendered


def test_pointer_uses_resolved_context_file_per_provider():
    """Each provider's pointer names its own resolved ``context_file``."""
    scope = _t6_scope({"mode": "core"})
    expected = {
        "Claude": "CLAUDE.md",
        "Gemini": "AGENTS.md",
        "Opencode": "AGENTS.md",
        "Continue": ".continue/rules/project-context.md",
    }
    for provider, context_file in expected.items():
        pointer = _t6_pointer_text(scope, provider)
        assert f"`{context_file}`" in pointer, (provider, pointer)
        assert "{context_file}" not in pointer


def test_pointer_inserted_at_end_of_context_section(t6_core_run):
    """developer: exactly one pointer line immediately before the last </context>."""
    content = t6_core_run["artifacts"]["developer"]
    lines = content.splitlines()
    pointer = t6_core_run["pointer"]
    at = lines.index(pointer)
    close = max(i for i, line in enumerate(lines) if line.strip() == "</context>")
    assert at < close
    assert content.count(pointer) == 1


def test_pointer_inserted_before_workflow_when_no_context_section(t6_core_run):
    """intern-developer: no <context>, so the pointer goes before </workflow>."""
    content = t6_core_run["artifacts"]["intern-developer"]
    lines = content.splitlines()
    pointer = t6_core_run["pointer"]
    assert "<context>" not in content
    at = lines.index(pointer)
    close = max(i for i, line in enumerate(lines) if line.strip() == "</workflow>")
    assert at < close
    assert content.count(pointer) == 1


def test_pointer_appended_at_eof_with_note(t6_core_run):
    """Neither section: pointer at EOF plus an explicit log note."""
    content = t6_core_run["artifacts"]["mammouth-expert"]
    pointer = t6_core_run["pointer"]
    assert "<context>" not in content and "</workflow>" not in content
    lines = content.splitlines()
    assert lines.index(pointer) >= len(lines) - 3
    notes = " ".join(t6_core_run["log"].infos)
    assert ("no <context>/</workflow> in mammouth-expert.md — "
            "pointer appended at EOF") in notes


def test_dangling_project_context_label_is_removed(t6_core_run):
    """A blanked ``**Project context:**`` label line leaves no empty header."""
    content = t6_core_run["artifacts"]["orchestrator"]
    assert "**Project context:**" not in content


def test_no_pointer_when_injected(t6_core_run):
    """Whitelisted (injected) roles keep their paragraph and get no pointer."""
    pointer = t6_core_run["pointer"]
    planner = t6_core_run["artifacts"]["planner"]
    assert "PARA" in planner
    assert pointer not in planner


def test_exactly_one_pointer_per_excluded_role(t6_core_run):
    """Every excluded role has exactly one pointer; injected roles have none.

    The run covers all three fallback groups (developer, intern-developer,
    mammouth-expert).
    """
    pointer = t6_core_run["pointer"]
    artifacts = t6_core_run["artifacts"]
    assert "<context>" in artifacts["developer"]
    assert "<context>" not in artifacts["intern-developer"]
    assert "</workflow>" in artifacts["intern-developer"]
    assert "<context>" not in artifacts["mammouth-expert"]
    assert "</workflow>" not in artifacts["mammouth-expert"]
    excluded = 0
    for role, content in artifacts.items():
        count = content.count(pointer)
        if role == "planner":
            assert count == 0, role
        else:
            assert count == 1, (role, count)
            excluded += 1
    assert excluded >= 3

