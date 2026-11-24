"""Render-side tests for project-context injection (issue #1187).

Shared by T4-T10. Each task adds its own section; keep section boundaries so
later tasks can append without disturbing existing tests.
"""
from __future__ import annotations

import hashlib
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


# ---------------------------------------------------------------------------
# T7 — log
# ---------------------------------------------------------------------------

# Three roles that each carry a ``{{PROJECT_CONTEXT}}`` placeholder in their
# template, so every excluded role contributes a positive paragraph delta.
_T7_ROLES = ("developer", "planner", "bug-feature-analyzer")

# A paragraph deliberately longer than the pointer line so that "chars saved"
# is a positive number (as in a real sync) and the accounting is deterministic.
_T7_PARA = (
    "Project context: this is a deliberately long paragraph used to make the "
    "delta accounting positive and deterministic in the T7 log-line tests. "
    "It stands in for a real project description and is longer than the "
    "pointer line, so 'chars saved' resolves to a positive number."
)


def _t7_impl():
    """Lazy imports for the T7 log seam (T4-T6 stay importable/unchanged)."""
    from lib.agent_sync import sync_agents_for_provider
    from lib.config import resolve_project_context_scope
    from lib.log import SyncLog
    from lib.providers import load_providers_config

    return sync_agents_for_provider, resolve_project_context_scope, SyncLog, load_providers_config


def _t7_run(mode_cfg, tmp_path, dry_run=False, para=None):
    """Run one real Claude sync over the controlled 3-role set; return (scope, log)."""
    sync, resolve_scope, SyncLog, load_providers = _t7_impl()
    provider_config = load_providers(_ROOT)
    scope = resolve_scope(
        {"project-context-injection": dict(mode_cfg)}, _ROOT,
        provider_config=provider_config)
    config = {"project": {"name": "T7"}, "platforms": [], "roles": list(_T7_ROLES)}
    variables = {
        "PROJECT_CONTEXT": para if para is not None else _T7_PARA,
        "COMMUNICATION_LANGUAGE": "English",
        "_PROJECT_CONTEXT_SCOPE": scope,
    }
    log = SyncLog()
    sync(
        _ROOT, tmp_path / "root", config, variables, log, dry_run=dry_run,
        provider="Claude", provider_config=provider_config)
    return scope, log


def _t7_log_line(log):
    """Return the single delta log line (distinct from the EOF-pointer note)."""
    matches = [
        info for info in log.infos
        if "project-context-injection" in info and "mode=" in info
    ]
    assert len(matches) == 1, matches
    return matches[0]


def test_log_line_format_all_mode(tmp_path):
    """All mode logs the exact AC6 format with a zero pointer/savings delta."""
    line = _t7_log_line(_t7_run({"mode": "all"}, tmp_path)[1])
    expected = (
        f"mode=all injected={len(_T7_ROLES)}/{len(_T7_ROLES)} roles, "
        "pointer=0, chars saved=0 (vs mode=all)"
    )
    assert expected in line, line


def test_log_line_counts_pointer_and_savings(tmp_path):
    """Core mode: pointer count = excluded roles; savings = Σpara - Σpointer."""
    scope, log = _t7_run({"mode": "core"}, tmp_path)
    line = _t7_log_line(log)
    pointer = scope["pointer_text"].format(context_file="CLAUDE.md")
    expected_saved = len(_T7_ROLES) * len(_T7_PARA) - len(_T7_ROLES) * len(pointer)
    expected = (
        f"mode=core injected=0/{len(_T7_ROLES)} roles, "
        f"pointer={len(_T7_ROLES)}, chars saved={expected_saved} (vs mode=all)"
    )
    assert expected in line, (line, expected)


def test_log_line_chars_saved_is_zero_for_all(tmp_path):
    """All mode saves exactly 0 — no 'approximate' or signed value."""
    line = _t7_log_line(_t7_run({"mode": "all"}, tmp_path)[1])
    assert "chars saved=0 (vs mode=all)" in line, line
    assert "chars saved=-" not in line, line


def test_log_line_emitted_in_dry_run(tmp_path):
    """--check (dry_run) emits the very same delta line as a real write."""
    _, dry_log = _t7_run({"mode": "core"}, tmp_path / "dry", dry_run=True)
    _, real_log = _t7_run({"mode": "core"}, tmp_path / "real", dry_run=False)
    assert _t7_log_line(dry_log) == _t7_log_line(real_log)


# ---------------------------------------------------------------------------
# T8 — render contracts per mode (AC2, AC3, AC4, AC5)
# ---------------------------------------------------------------------------

# A distinctive marker we inject as PROJECT_CONTEXT; counting it in a rendered
# artifact tells us exactly how many project-context blocks survived.
_T8_PARA = "T8_MARKER_PROJECT_CONTEXT_PARAGRAPH_2026"

# The eight roles named in the plan's T8 contract matrix. Two of them
# (knowledge-curator, knowledge-migrator) sit behind activation groups, which
# _render_run enables explicitly (see below).
_T8_ROLES = (
    "developer", "orchestrator", "ui-ux-designer", "bug-feature-analyzer",
    "knowledge-curator", "knowledge-migrator", "intern-developer",
    "mammouth-expert",
)


def _render_run(config, tmp_path, roles=None, para=_T8_PARA,
                provider="Claude", provider_config=None):
    """Render a controlled role set through the real per-role sync path.

    Pattern from tests/test_template_slimming_equivalence.py:1191-1240:
    ``config`` is passed directly instead of via ``load_config``; variables are
    produced by the real ``build_variables`` (so config -> scope resolution and
    its D6/D8 warnings are exercised), and every role goes through the
    production ``_compose_role_content`` -> ``_apply_content_pipeline`` ->
    ``_finalize_agent_content`` chain inside ``sync_agents_for_provider``.
    That loop also applies the per-role scope (T5) and pointer (T6), which is
    why the full sync function is used rather than rebuilding the pipeline by
    hand.

    ``provider_config`` optionally re-resolves the scope against a fake
    provider registry (to exercise primary-role derivation at render level);
    the actual sync always uses the real registry. Returns a dict exposing the
    artifacts, build warnings, log, resolved scope and the formatted pointer.
    """
    from lib.config import build_variables, resolve_project_context_scope
    from lib.log import SyncLog
    from lib.providers import load_providers_config
    from lib.agent_sync import sync_agents_for_provider

    roles = tuple(roles) if roles is not None else _T8_ROLES
    full = {
        "project": {"name": "T8"},
        "platforms": [],
        "roles": list(roles),
        "variables": {"PROJECT_CONTEXT": para},
        # Enable the two activation groups gating contract roles.
        "knowledge-engine": {"enabled": True},
        "systems-engineering": {"enabled": True},
    }
    full.update(config)  # `config` may override any base key, incl. the section
    # Keep the marker under our control even if a caller replaced `variables`.
    full.setdefault("variables", {})["PROJECT_CONTEXT"] = para

    variables, warnings = build_variables(full, _ROOT, tmp_path)
    if provider_config is not None:
        variables["_PROJECT_CONTEXT_SCOPE"] = resolve_project_context_scope(
            full, _ROOT, provider_config=provider_config,
            communication_language=variables.get("COMMUNICATION_LANGUAGE"),
            warn_sink=warnings,
        )
        variables["PROJECT_CONTEXT_MODE"] = (
            variables["_PROJECT_CONTEXT_SCOPE"]["mode"])

    real_provider_config = load_providers_config(_ROOT)
    log = SyncLog()
    sync_agents_for_provider(
        _ROOT, tmp_path / "project", full, variables, log,
        dry_run=False, provider=provider, provider_config=real_provider_config,
    )
    artifacts = {
        path.stem: path.read_text(encoding="utf-8")
        for path in (tmp_path / "project").rglob("*.md")
        if path.stem in roles
    }
    scope = variables["_PROJECT_CONTEXT_SCOPE"]
    context_file = real_provider_config[provider]["context_file"]
    return {
        "artifacts": artifacts,
        "warnings": warnings,
        "log": log,
        "scope": scope,
        "pointer": scope["pointer_text"].format(context_file=context_file),
    }


def _render(role, config, tmp_path):
    """Return one rendered artifact (plan T8 render-helper signature)."""
    return _render_run(config, tmp_path)["artifacts"][role]


def _pc_warnings(run):
    """Only the once-per-run project-context-injection warnings."""
    return [w for w in run["warnings"] if "project-context-injection." in w]


def test_all_matches_default_absent_key(tmp_path):
    """AC2: an absent section and explicit mode=all render byte-identically."""
    absent = _render_run({}, tmp_path / "absent")["artifacts"]
    explicit = _render_run(
        {"project-context-injection": {"mode": "all"}},
        tmp_path / "explicit",
    )["artifacts"]
    for role in _T8_ROLES:
        assert role in absent and role in explicit, role
        assert absent[role] == explicit[role], role
    # The single-role helper renders the same bytes as the full-run helper.
    assert _render("developer", {}, tmp_path / "helper") == absent["developer"]


def test_core_renders_zero_blocks(tmp_path):
    """AC3: core embeds zero paragraphs and exactly one pointer per role."""
    run = _render_run({"project-context-injection": {"mode": "core"}}, tmp_path)
    for role in _T8_ROLES:
        content = run["artifacts"][role]
        assert content.count(_T8_PARA) == 0, role
        assert content.count(run["pointer"]) == 1, role


def test_core_whitelist_only_whitelisted_roles(tmp_path):
    """AC4: only whitelisted roles keep the block; inherit adds no orchestrator."""
    run = _render_run(
        {"project-context-injection": {
            "mode": "core+whitelist", "whitelist": ["developer"]}},
        tmp_path,
        roles=_T8_ROLES + ("planner",),
    )
    artifacts = run["artifacts"]
    assert artifacts["developer"].count(_T8_PARA) >= 1
    assert run["pointer"] not in artifacts["developer"]
    # `planner` is not whitelisted; `orchestrator` is excluded because inherit
    # is the mode default (it does NOT promote the orchestrator set).
    for role in ("planner", "orchestrator"):
        assert artifacts[role].count(_T8_PARA) == 0, role
        assert artifacts[role].count(run["pointer"]) == 1, role


def test_core_whitelist_include_adds_orchestrator(tmp_path):
    """AC4/AC5: include promotes the orchestrator set; exclude does not."""
    included = _render_run(
        {"project-context-injection": {
            "mode": "core+whitelist", "whitelist": ["developer"],
            "orchestrator": "include"}},
        tmp_path / "include",
    )["artifacts"]
    assert included["developer"].count(_T8_PARA) >= 1
    assert included["orchestrator"].count(_T8_PARA) >= 1

    excluded = _render_run(
        {"project-context-injection": {
            "mode": "core+whitelist", "whitelist": ["developer"],
            "orchestrator": "exclude"}},
        tmp_path / "exclude",
    )["artifacts"]
    assert excluded["developer"].count(_T8_PARA) >= 1
    assert excluded["orchestrator"].count(_T8_PARA) == 0


def test_core_whitelist_unknown_name_fails_render(tmp_path):
    """AC4: an unknown whitelist name aborts the render through build_variables."""
    from lib.io import SyncError

    with pytest.raises(SyncError, match="whitelist-unknown-role") as exc_info:
        _render_run(
            {"project-context-injection": {
                "mode": "core+whitelist", "whitelist": ["developer", "nope"]}},
            tmp_path,
        )
    assert "nope" in str(exc_info.value)


def test_core_orchestrator_only_orchestrator_roles(tmp_path):
    """AC5: core+orchestrator embeds only the orchestrator set.

    A fake provider registry supplies a distinct ``primary-role`` (``planner``)
    so the provider-derived member is verified separately from ``orchestrator``.
    """
    run = _render_run(
        {"project-context-injection": {"mode": "core+orchestrator"}},
        tmp_path,
        roles=_T8_ROLES + ("planner",),
        provider_config={"Claude": {"primary-role": "planner"}},
    )
    scope_roles = run["scope"]["orchestrator_roles"]
    assert "orchestrator" in scope_roles and "planner" in scope_roles
    artifacts = run["artifacts"]
    for role in ("orchestrator", "planner"):
        assert artifacts[role].count(_T8_PARA) >= 1, role
        assert run["pointer"] not in artifacts[role], role
    assert artifacts["developer"].count(_T8_PARA) == 0
    assert artifacts["developer"].count(run["pointer"]) == 1


def test_core_include_moves_orchestrator_in(tmp_path):
    """AC5: core + orchestrator=include behaves like core+orchestrator."""
    run = _render_run(
        {"project-context-injection": {
            "mode": "core", "orchestrator": "include"}},
        tmp_path,
    )
    assert "orchestrator" in run["scope"]["orchestrator_roles"]
    artifacts = run["artifacts"]
    assert artifacts["orchestrator"].count(_T8_PARA) >= 1
    assert run["pointer"] not in artifacts["orchestrator"]
    assert artifacts["developer"].count(_T8_PARA) == 0
    assert artifacts["developer"].count(run["pointer"]) == 1


def test_core_keeps_required_sections_non_empty(tmp_path):
    """AC7 pre-gate: core never drops frontmatter, headings or context bodies."""
    all_run = _render_run({}, tmp_path / "all")
    core_run = _render_run(
        {"project-context-injection": {"mode": "core"}}, tmp_path / "core")
    for role in _T8_ROLES:
        base = all_run["artifacts"][role]
        core = core_run["artifacts"][role]
        assert base.startswith("---") and core.startswith("---"), role
        base_heads = [line for line in base.splitlines() if line.startswith("## ")]
        core_heads = [line for line in core.splitlines() if line.startswith("## ")]
        assert base_heads == core_heads, role
        # The paragraph placeholder is substituted/blanked, never left raw.
        assert "{{PROJECT_CONTEXT}}" not in core, role
        if "<context>" in base:
            body = core.split("<context>", 1)[1].split("</context>", 1)[0]
            assert body.strip(), role
        else:
            # intern-developer / mammouth-expert / knowledge-* have no context
            # section: the pointer fallback must be present instead.
            assert core_run["pointer"] in core, role


def test_all_plus_exclude_only_orchestrator_excluded(tmp_path):
    """AC5/D6: all + exclude excludes only the orchestrator set, with one WARN."""
    run = _render_run(
        {"project-context-injection": {
            "mode": "all", "orchestrator": "exclude"}},
        tmp_path,
    )
    artifacts = run["artifacts"]
    assert artifacts["orchestrator"].count(_T8_PARA) == 0
    assert artifacts["orchestrator"].count(run["pointer"]) == 1
    assert artifacts["developer"].count(_T8_PARA) >= 1
    assert run["pointer"] not in artifacts["developer"]
    warns = _pc_warnings(run)
    assert len(warns) == 1, warns
    assert "exclude-overrides-mode" in warns[0] and "mode=all" in warns[0]


def test_core_orchestrator_with_overridden_roles(tmp_path):
    """AC5/D5: an explicit orchestrator-roles override replaces the default set."""
    run = _render_run(
        {"project-context-injection": {
            "mode": "core+orchestrator",
            "orchestrator-roles": ["senior-developer"]}},
        tmp_path,
        roles=_T8_ROLES + ("senior-developer", "junior-developer"),
    )
    artifacts = run["artifacts"]
    assert artifacts["senior-developer"].count(_T8_PARA) >= 1
    assert artifacts["orchestrator"].count(_T8_PARA) == 0
    assert artifacts["developer"].count(_T8_PARA) == 0


def test_core_orchestrator_with_empty_roles_injects_nothing(tmp_path):
    """AC5/D5: an empty orchestrator set injects nothing and warns once."""
    run = _render_run(
        {"project-context-injection": {
            "mode": "core+orchestrator", "orchestrator-roles": []}},
        tmp_path,
    )
    for role in _T8_ROLES:
        content = run["artifacts"][role]
        assert content.count(_T8_PARA) == 0, role
        assert content.count(run["pointer"]) == 1, role
    warns = _pc_warnings(run)
    assert len(warns) == 1, warns
    assert "empty-orchestrator-set" in warns[0]


def test_pointer_language_de_renders_german_pointer(tmp_path):
    """AC3/D8: German pointer text renders per provider; all mode stays clean."""
    for provider, context_file in (("Claude", "CLAUDE.md"),
                                   ("Gemini", "AGENTS.md")):
        run = _render_run(
            {"project-context-injection": {
                "mode": "core", "pointer-language": "de"}},
            tmp_path / provider,
            provider=provider,
        )
        pointer = run["pointer"]
        assert f"Projektkontext: lies zuerst `{context_file}`" in pointer
        for role in _T8_ROLES:
            content = run["artifacts"][role]
            assert content.count(pointer) == 1, (provider, role)
            assert "Project context: read" not in content, (provider, role)

        all_run = _render_run(
            {"project-context-injection": {
                "mode": "all", "pointer-language": "de"}},
            tmp_path / f"{provider}-all",
            provider=provider,
        )
        for role in _T8_ROLES:
            assert all_run["pointer"] not in all_run["artifacts"][role], role


# ---------------------------------------------------------------------------
# T9 — prose conditionals (D-3)
# ---------------------------------------------------------------------------

# The four roles that carry an in-sentence `{{PROJECT_CONTEXT}}` prose site.
_T9_ROLES = (
    "ui-ux-designer", "bug-feature-analyzer",
    "knowledge-curator", "knowledge-migrator",
)

_T9_TEMPLATES = {
    role: _ROOT / "agents" / "1-generic" / f"{role}.md" for role in _T9_ROLES
}

# Distinctive fragments identifying each of the five prose sites. The mapping
# is role -> tuple of fragments (ui-ux-designer has two prose sites).
_T9_PROSE_FRAGMENTS = {
    "ui-ux-designer": (
        "provides the design vision and context for all UI decisions",
        "No designs without a `",
    ),
    "bug-feature-analyzer": ("Behavior covered by `",),
    "knowledge-curator": ("**Zielrepo-Adaption:** Liest `",),
    "knowledge-migrator": ("1. Lies `",),
}


def _t9_if_body(text):
    """Return the bodies of every `{{#if PROJECT_CONTEXT_INJECTED}}` branch."""
    import re
    return re.findall(
        r"\{\{#if PROJECT_CONTEXT_INJECTED\}\}(.*?)\{\{/if\}\}",
        text,
        flags=re.DOTALL,
    )


def test_no_bare_prose_placeholder_remains():
    """D-3: every non-block `{{PROJECT_CONTEXT}}` sits inside a conditional.

    The four `**Project context:** {{PROJECT_CONTEXT}}` block occurrences are
    renderer-controlled (spec D-4) and stay bare; every other occurrence must
    live inside a `{{#if PROJECT_CONTEXT_INJECTED}}` branch.
    """
    import re
    for role, path in _T9_TEMPLATES.items():
        text = path.read_text(encoding="utf-8")
        total = text.count("{{PROJECT_CONTEXT}}")
        # Two block shapes occur in the corpus: a labelled
        # `**Project context:** {{PROJECT_CONTEXT}}` line and a bare standalone
        # `{{PROJECT_CONTEXT}}` line. Both are renderer-controlled (spec D-4).
        labelled = len(re.findall(
            r"\*\*Project context:\*\* \{\{PROJECT_CONTEXT\}\}", text
        ))
        bare_line = sum(
            1 for line in text.splitlines()
            if line.strip() == "{{PROJECT_CONTEXT}}"
        )
        block = labelled + bare_line
        wrapped = sum(body.count("{{PROJECT_CONTEXT}}")
                      for body in _t9_if_body(text))
        assert total == block + wrapped, (
            f"{role}: {total} occurrences but {block} block + {wrapped} wrapped"
        )
        assert wrapped >= 1, f"{role}: no conditional prose site found"


def test_core_prose_stays_grammatical(tmp_path):
    """D-3: core render shows `CLAUDE.md`, never an empty double-backtick."""
    run = _render_run(
        {"project-context-injection": {"mode": "core"}},
        tmp_path / "t9-core", roles=("ui-ux-designer",),
    )
    art = run["artifacts"]["ui-ux-designer"]
    assert "`CLAUDE.md` provides the design vision" in art
    assert "`` provides the design vision" not in art


def _t9_line_with(lines, fragment):
    matches = [line for line in lines if fragment in line]
    assert len(matches) == 1, (
        f"expected exactly one line for {fragment!r}, got {len(matches)}"
    )
    return matches[0]


def _t9_all_render(tmp_path):
    """Render the four roles with the real project config (default all mode)."""
    from scripts.lib.config import build_variables, load_config
    from scripts.lib.providers import load_providers_config
    from scripts.lib.log import SyncLog
    from scripts.lib.agent_sync import sync_agents_for_provider

    config = load_config(_ROOT / ".meta-config" / "project.yaml")
    variables, _warnings = build_variables(config, _ROOT, tmp_path)
    log = SyncLog()
    sync_agents_for_provider(
        _ROOT, tmp_path / "project", config, variables, log,
        dry_run=False, provider="Claude",
        provider_config=load_providers_config(_ROOT),
    )
    artifacts = {
        path.stem: path.read_text(encoding="utf-8")
        for path in (tmp_path / "project").rglob("*.md")
        if path.stem in _T9_ROLES
    }
    return artifacts, variables


def test_all_prose_matches_golden(tmp_path):
    """AC2: all-mode prose sites stay byte-identical to the frozen goldens."""
    sys.path.insert(0, str(Path(__file__).parent))
    from test_template_slimming_equivalence import _port_golden_meta_tokens

    render, variables = _t9_all_render(tmp_path / "t9-all")
    golden_dir = _ROOT / "tests" / "fixtures" / "slimming-golden"
    for role, fragments in _T9_PROSE_FRAGMENTS.items():
        assert role in render, role
        current = render[role]
        golden = _port_golden_meta_tokens(
            (golden_dir / f"{role}.md").read_text(encoding="utf-8"),
            variables,
        )
        g_lines = golden.splitlines()
        r_lines = current.splitlines()
        for fragment in fragments:
            g_line = _t9_line_with(g_lines, fragment)
            r_line = _t9_line_with(r_lines, fragment)
            assert g_line == r_line, (
                f"{role}: prose line drift for {fragment!r}\n"
                f"golden: {g_line}\nrender: {r_line}"
            )


# ---------------------------------------------------------------------------
# T10 — golden gate (AC2 evidence)
# ---------------------------------------------------------------------------


#: Frozen SHA-256 over the golden corpus: the equivalence gate itself plus
#: every golden fixture, keyed by repo-relative path and raw bytes. AC2 pins
#: this content, not a commit-ancestry range: in squashed rebaseline bundles
#: the legitimate rebaseline lands in the same commit as the change that
#: causes it, so a `base..HEAD` diff cannot distinguish an approved rebaseline
#: from later drift. A content pin keeps the guard meaningful in both layouts.
_GOLDEN_CORPUS_SHA256 = "e59b6889afe66f55aac99d8e7c73588c9fa1f30000c2b46f2ea3bf992c549fc3"


def _golden_corpus_paths():
    return [
        Path("tests/test_template_slimming_equivalence.py"),
        *sorted(Path("tests/fixtures/slimming-golden").rglob("*.md")),
    ]


def _golden_corpus_digest() -> str:
    digest = hashlib.sha256()
    for path in _golden_corpus_paths():
        digest.update(path.as_posix().encode("utf-8"))
        digest.update(b"\0")
        digest.update((_ROOT / path).read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def test_golden_gate_file_untouched_by_this_issue():
    """AC2 evidence: the golden gate and its fixtures match the frozen corpus.

    Any edit to the equivalence test or the golden fixtures — committed or
    only in the working tree — turns this gate red instead of silently
    accepting a rebaseline. Legitimate rebaselines are recorded by advancing
    ``_GOLDEN_CORPUS_SHA256`` in a reviewed change (the historical commit-base
    pins were advanced the same way: ``6eeeff44`` -> ``e22b0ed4`` ->
    ``99be710e`` -> ``47e338cb`` -> ``6fde198b`` -> ``aee986c8`` ->
    ``14efcb23`` -> ``a9f23fc4`` -> ``1adfabb8``; #1335 + T21:
    slimming-golden corpus rebaselined (payload attribution variant C + REQ
    gating); #1344: orchestrator 8.12.5 version pins in five goldens plus the
    equivalence-harness reason log). Unapproved drift still fails loudly.
    """
    actual = _golden_corpus_digest()
    assert actual == _GOLDEN_CORPUS_SHA256, (
        "golden gate drifted — AC2 forbids rebaselining: "
        f"expected {_GOLDEN_CORPUS_SHA256}, got {actual}"
    )

