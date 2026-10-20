"""Task 12 (2b.3): compact gate-card and compact agent list in the entry file.

Spec ``docs/specs/2026-10-11-context-profiles-spec.md`` IC-06 (AC-24 C3, AC-26
entry-file goals): ``templates/context/agents-managed.md`` swaps
``rules-embedded``/``agents-table`` for the ``gate-card``/``agents-list-compact``
partials behind ``{{#if CONTEXT_PROFILE_COMPACT}}``. The gate-card texts are
extracted verbatim from the source rules — the section names come from
``config/context-anchors.yaml::gate_card_sections`` (IC-12), never a copy.

* ``full`` (or no opt-in): the ``{{else}}`` branch is the unchanged text and the
  render stays byte-identical to the committed managed block (AC-23).
* ``compact`` (opt-in, **UNVERIFIED**): gate-card + one-line agent list; an
  over-hard-cap entry file aborts with ``context.over-hard-cap``.

``compact`` is opt-in and unverified (IC-36): nothing here claims the profile is
verified, validated or recommended. QG-5 freezes the opt-in render as
``tests/fixtures/compact-golden/agents-managed.md``.

Regenerate the golden (only for a justified rebaseline, documented below): render
the ``compact`` profile through ``_render`` and write it to the fixture.

Rebaseline log:
- Release 2.0.0-beta.2 (VERSION bump 2.0.0-beta.1 -> 2.0.0-beta.2): only the
  ``agent-meta v...`` version string in the compact gate-card header changed.
  No substantive render change.
"""
from __future__ import annotations

import difflib
import re
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import build_variables, load_config
from lib.context import _build_managed_block, _update_managed_html_block, build_gate_card
from lib.io import SyncError
from lib.log import SyncLog
from lib.mcp import (
    build_mcp_guardrails_list,
    load_mcp_registry,
    resolve_active_mcp_servers,
)
from lib.providers import (
    load_provider_capabilities,
    load_providers_config,
    runtime_gate_vars,
)

_COMPACT_GOLDEN = (
    _REPO_ROOT / "tests" / "fixtures" / "compact-golden" / "agents-managed.md"
)
_PROVIDER = "Opencode"
_MANAGED_BLOCK_RE = re.compile(
    r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
    re.DOTALL,
)

# Gate-card content mandated by spec 4.2: CRITICAL GATE, Git Delegation,
# Branch-Guard core, commit conventions, language rules, Singleton, MCP denies.
_GATE_CARD_MARKERS = (
    "# CRITICAL GATE",
    "MAIN CHAT darf nicht selbst editieren",
    "Git Delegation",
    "# Branch-Guard",
    "Keine Code-Änderungen direkt auf `main` oder `master`",
    "# Commit-Konventionen",
    "Verwende Conventional Commits (feat, fix, chore).",
    "# Sprachregeln",
    "Singleton",
    "# MCP Hard Prohibitions",
)
_GATE_CARD_SECTIONS = (
    "use-orchestrator#CRITICAL GATE",
    "use-orchestrator#Git Delegation",
    "branch-guard#Branch-Guard",
    "commit-conventions#Commit-Konventionen",
    "language#Sprachregeln",
    "a2a-delegation-gates#Enforced Gates",
    "mcp-guardrails#MCP Hard Prohibitions",
)


@pytest.fixture(scope="module")
def loaded_config():
    return load_config(_REPO_ROOT / ".meta-config" / "project.yaml")


@pytest.fixture(scope="module")
def provider_config():
    return load_providers_config(_REPO_ROOT)


@pytest.fixture(scope="module")
def capabilities():
    return load_provider_capabilities(_REPO_ROOT)


def _variables(provider, provider_config, capabilities, project_root, config):
    pc = provider_config.get(provider, {})
    variables, _warnings = build_variables(config, _REPO_ROOT, project_root)
    variables.update(
        runtime_gate_vars(pc, capabilities.get(provider, {}), config)
    )
    return variables


def _render(profile, project_root, config, provider_config, capabilities):
    """Render the managed block through ``_build_managed_block`` (provider)."""
    cfg = dict(config)
    if profile is not None:
        cfg["context-profile"] = profile
    variables = _variables(_PROVIDER, provider_config, capabilities, project_root, cfg)
    return _build_managed_block(
        _REPO_ROOT, cfg, variables, SyncLog(), provider=_PROVIDER,
        provider_config=provider_config, project_root=project_root,
    )


@pytest.fixture(scope="module")
def rendered(tmp_path_factory, loaded_config, provider_config, capabilities):
    root = tmp_path_factory.mktemp("gate-card-compact")
    return {
        "no_key": _render(None, root / "no-key", loaded_config, provider_config, capabilities),
        "full": _render("full", root / "full", loaded_config, provider_config, capabilities),
        "compact": _render("compact", root / "compact", loaded_config, provider_config, capabilities),
    }


def _diff(expected: str, actual: str, label: str) -> str:
    return "\n".join(
        difflib.unified_diff(
            expected.splitlines(), actual.splitlines(),
            f"golden/{label}", f"now/{label}", lineterm="",
        )
    )


def test_build_gate_card_extracts_verbatim_rule_sections(
    tmp_path, loaded_config, provider_config, capabilities
):
    """``build_gate_card`` yields the mandated gate texts from the source rules."""
    config = dict(loaded_config)
    variables = _variables(
        _PROVIDER, provider_config, capabilities, tmp_path, config
    )
    registry = load_mcp_registry(_REPO_ROOT, config, None)
    variables["MCP_GUARDRAILS_LIST"] = build_mcp_guardrails_list(
        registry,
        resolve_active_mcp_servers(config, _REPO_ROOT, None, registry=registry),
    )

    card = build_gate_card(_REPO_ROOT, config, variables, SyncLog())

    assert isinstance(card, str) and card.strip()
    for marker in _GATE_CARD_MARKERS:
        assert marker in card, f"gate card lost {marker!r}"
    assert "delete_conclusion" in card, "gate card lost the MCP deny list"


def test_gate_card_sections_are_registered_in_the_registry():
    """The section names come from ``gate_card_sections`` (IC-12), not a copy."""
    registry = yaml.safe_load(
        (_REPO_ROOT / "config" / "context-anchors.yaml").read_text(encoding="utf-8")
    )
    sections = registry["gate_card_sections"]
    for spec in _GATE_CARD_SECTIONS:
        assert spec in sections, f"gate_card_sections missing {spec!r}"


@pytest.mark.parametrize(
    "spec", ["use-orchestrator#No Such Section", "no-such-rule#Whatever"]
)
def test_missing_gate_card_section_raises(
    monkeypatch, tmp_path, loaded_config, provider_config, capabilities, spec
):
    """A missing rule or heading aborts the sync instead of a partial card."""
    import lib.context as context

    monkeypatch.setattr(
        context, "_load_gate_card_sections", lambda _root: [spec]
    )
    config = dict(loaded_config)
    variables = _variables(
        _PROVIDER, provider_config, capabilities, tmp_path, config
    )
    with pytest.raises(SyncError, match="context.gate-card"):
        build_gate_card(_REPO_ROOT, config, variables, SyncLog())


_AGENT_LIST_LINE_RE = re.compile(r"^- `[a-z0-9-]+`: ")


def _agents_md_roster_emitted(provider_config, capabilities, config) -> bool:
    """Whether the shared entry file renders the compact roster (capability-driven).

    Mirrors ``_build_managed_block`` exactly: the physical ``AGENTS.md`` renders
    once for every ACTIVE sharer, so the production safe-side resolver decides over
    the sharers' ``roster_in_harness`` flags. Depends only on
    ``config/provider-capabilities.yaml`` and the group membership — never a
    provider literal (keeps the test correct if the group changes, F6).
    """
    from lib.context import _shared_context_users
    from lib.context_profile import resolve_shared_emit_roster

    target = provider_config[_PROVIDER]["context_file"]
    sharers = _shared_context_users(
        _PROVIDER, provider_config, config, target_name=target
    )
    flags = {
        p: (capabilities.get(p) or {}).get("roster_in_harness") is True
        for p in sharers
    }
    return resolve_shared_emit_roster(flags)


def test_compact_entry_swaps_rules_and_table_for_gate_card_and_list(
    rendered, loaded_config, provider_config, capabilities
):
    """``compact`` renders the gate card + a capability-gated one-line agent list."""
    compact = rendered["compact"]
    for marker in _GATE_CARD_MARKERS:
        assert marker in compact, f"compact entry lost {marker!r}"
    assert "| Agent | Core Capabilities |" not in compact, "compact kept the table"
    assert "## Agent Directory" in compact

    lines = compact.splitlines()
    roster_lines = [line for line in lines if _AGENT_LIST_LINE_RE.match(line)]
    if _agents_md_roster_emitted(provider_config, capabilities, loaded_config):
        assert roster_lines, "compact profile must emit the one-line agent list"
        assert len(roster_lines) >= 2, "compact agent list has fewer than two agents"
        start = lines.index(roster_lines[0])
        end = start
        while end + 1 < len(lines) and _AGENT_LIST_LINE_RE.match(lines[end + 1]):
            end += 1
        assert "" not in lines[start:end + 1], "compact agent list contains blank lines"
    else:
        assert not roster_lines, (
            "every ACTIVE AGENTS.md sharer keeps its roster in the harness "
            "(roster_in_harness=true) — the shared compact list must be omitted"
        )


def test_full_and_no_key_render_byte_identical(rendered):
    """No opt-in renders the unchanged ``{{else}}`` branch (AC-23)."""
    assert rendered["no_key"] == rendered["full"]
    committed = (_REPO_ROOT / "AGENTS.md").read_text(encoding="utf-8")
    match = _MANAGED_BLOCK_RE.search(committed)
    assert match, "committed AGENTS.md has no managed block"
    assert rendered["full"].rstrip("\n") == match.group(0).rstrip("\n"), _diff(
        match.group(0).rstrip("\n"), rendered["full"].rstrip("\n"),
        "agents-managed(full)",
    )


def test_compact_render_matches_compact_golden(rendered):
    """QG-5: the opt-in render is frozen as a compact golden."""
    assert _COMPACT_GOLDEN.is_file(), f"compact golden missing: {_COMPACT_GOLDEN} (QG-5)"
    golden = _COMPACT_GOLDEN.read_text(encoding="utf-8")
    assert golden == rendered["compact"], _diff(
        golden, rendered["compact"], "agents-managed(compact)"
    )


def test_compact_entry_over_hard_cap_raises(
    monkeypatch, tmp_path, loaded_config, provider_config, capabilities
):
    """An over-hard-cap compact entry file aborts (never silently written)."""
    import lib.providers as providers

    real = providers.load_provider_capabilities

    def _tiny(root):
        caps = {name: dict(entry or {}) for name, entry in real(root).items()}
        caps.setdefault(_PROVIDER, {})["context_hard_cap_bytes"] = 1
        return caps

    monkeypatch.setattr(providers, "load_provider_capabilities", _tiny)
    config = {**loaded_config, "context-profile": "compact"}
    variables = _variables(
        _PROVIDER, provider_config, capabilities, tmp_path, config
    )
    with pytest.raises(SyncError, match="context.over-hard-cap"):
        _build_managed_block(
            _REPO_ROOT, config, variables, SyncLog(), provider=_PROVIDER,
            provider_config=provider_config, project_root=tmp_path,
        )


_NOTES_COMMENT_RE = re.compile(
    r"<!--\s*\nGeneriert von agent-meta v.*?-->", re.DOTALL
)


def _entry_file_block(
    provider, profile, project_root, loaded_config, provider_config, capabilities
):
    """Render the provider's HTML managed block through the real writer (IC-08).

    ``_update_managed_html_block`` is the single seam that renders
    ``templates/context/claude-managed.md``; the returned text is the managed
    block exactly as it lands in the target file.
    """
    config = dict(loaded_config)
    if profile is not None:
        config["context-profile"] = profile
    variables = _variables(
        provider, provider_config, capabilities, project_root, config
    )
    pc = provider_config[provider]
    target = project_root / pc["context_file"]
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(
        "<!-- agent-meta:managed-begin -->\n<!-- agent-meta:managed-end -->\n",
        encoding="utf-8",
    )
    _update_managed_html_block(
        target, project_root, variables, SyncLog(), dry_run=False,
        agent_meta_root=_REPO_ROOT, provider=provider, pc=pc,
        config=config, provider_config=provider_config,
    )
    match = _MANAGED_BLOCK_RE.search(target.read_text(encoding="utf-8"))
    assert match, f"{provider}: no managed block written"
    return match.group(0)


def test_full_claude_entry_stays_byte_identical(
    tmp_path, loaded_config, provider_config, capabilities
):
    """No opt-in keeps the Claude entry block byte-identical (AC-23, IC-08)."""
    rendered = _entry_file_block(
        "Claude", None, tmp_path, loaded_config, provider_config, capabilities
    )
    committed = (_REPO_ROOT / "CLAUDE.md").read_text(encoding="utf-8")
    match = _MANAGED_BLOCK_RE.search(committed)
    assert match, "committed CLAUDE.md has no managed block"
    assert rendered.rstrip("\n") == match.group(0).rstrip("\n"), _diff(
        match.group(0).rstrip("\n"), rendered.rstrip("\n"), "claude-managed(full)"
    )


def test_compact_claude_notes_become_html_comment(
    tmp_path, loaded_config, provider_config, capabilities
):
    """IC-08 (C6): the Claude entry file hides its notes in an HTML comment."""
    block = _entry_file_block(
        "Claude", "compact", tmp_path, loaded_config, provider_config, capabilities
    )
    assert _NOTES_COMMENT_RE.search(block), (
        "compact Claude notes are not a block HTML comment:\n" + block
    )


def test_compact_foreign_provider_keeps_notes_visible(
    tmp_path, loaded_config, provider_config, capabilities
):
    """IC-08: a reader without ``strips_html_comments`` keeps them visible."""
    block = _entry_file_block(
        "Copilot", "compact", tmp_path, loaded_config, provider_config, capabilities
    )
    assert "Generiert von agent-meta v" in block
    assert _NOTES_COMMENT_RE.search(block) is None, (
        "foreign provider hid its maintainer notes in an HTML comment:\n" + block
    )


def test_compact_shared_entry_file_keeps_notes_visible(
    tmp_path, loaded_config, provider_config, capabilities
):
    """IC-08: a shared context file (more than one reader) keeps them visible."""
    config = {**loaded_config, "context-profile": "compact"}
    config["ai-providers"] = ["Claude", "Copilot"]
    shared = {
        **provider_config,
        "Copilot": {**provider_config["Copilot"], "context_file": "CLAUDE.md"},
    }
    block = _entry_file_block(
        "Claude", "compact", tmp_path, config, shared, capabilities
    )
    assert "Generiert von agent-meta v" in block
    assert _NOTES_COMMENT_RE.search(block) is None, (
        "shared context file hid its maintainer notes in an HTML comment:\n" + block
    )
