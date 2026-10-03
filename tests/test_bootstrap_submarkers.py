"""Task 10 — Provider-scoped bootstrap sub-markers + legacy migration (TDD).

Spec: docs/specs/2026-09-30-provider-audit-opencode-v2.md §2.4; AC-10, AC-16(a/b/c).
Design: docs/specs/2026-09-30-provider-audit-opencode-v2-design.md §3.5 (DECISION-4, M-6).
Plan: docs/plans/2026-09-30-provider-audit-opencode-v2-plan.md Task 10; OQ-2.

Contracts under test (all provider-agnostic — cleanup iterates the bootstrap
registry, never a ``"Gemini" in active`` literal):

* AC-10  — a Gemini+ZCode project ends with one scoped marker pair per provider
           and both rosters survive in the shared ``AGENTS.md``.
* AC-16a — user notes outside the managed markers survive cleanup/injection.
* AC-16b — an old *scoped* marker of an inactive provider is removed, an active
           one survives.
* AC-16c — the legacy id-less pair is discarded without attribution; a fixture
           carrying only the ZCode-sourced legacy block ends with *both*
           ``:Gemini`` and ``:ZCode`` scoped pairs (M-6).
* OQ-2   — the dead top-level ``agents:`` block leaves the generated
           ``.continue/config.yaml``, the generated header states the auto-load
           is ``cn review``-only, and ``.continue/agents/*.md`` are untouched.

Run: python3 -m pytest tests/test_bootstrap_submarkers.py -q
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.bootstrap import BootstrapEngine  # noqa: E402
from lib.context import (  # noqa: E402
    _cleanup_bootstrap_block,
    _update_continue_config_managed_block,
)
from lib.log import SyncLog  # noqa: E402

LEGACY_BEGIN = "<!-- agent-meta:bootstrap-begin -->"
LEGACY_END = "<!-- agent-meta:bootstrap-end -->"

CONTINUE_DEAD_BEGIN = "# agent-meta:managed-agents-begin"
CONTINUE_DEAD_END = "# agent-meta:managed-agents-end"


def _marker(provider: str, kind: str) -> str:
    return f"<!-- agent-meta:bootstrap-{kind}:{provider} -->"


def _block(text: str, provider: str) -> str:
    begin = _marker(provider, "begin")
    end = _marker(provider, "end")
    start = text.index(begin)
    stop = text.index(end) + len(end)
    return text[start:stop]


def _engine() -> BootstrapEngine:
    return BootstrapEngine(config_dir=REPO_ROOT / "config")


def _provider_config() -> dict:
    # Only the file/context keys resolve_providers needs; the bootstrap marker
    # data lives in config/provider-bootstrap.yaml (the registry under test).
    return {
        "Claude": {"context_file": "CLAUDE.md"},
        "Gemini": {"context_file": "AGENTS.md"},
        "ZCode": {"context_file": "AGENTS.md"},
    }


def _config(active) -> dict:
    return {"ai-providers": list(active)}


def _cleanup(path: Path, active, project_root: Path) -> None:
    _cleanup_bootstrap_block(
        path,
        _config(active),
        _provider_config(),
        SyncLog(),
        dry_run=False,
        project_root=project_root,
        agent_meta_root=REPO_ROOT,
    )


def _gemini_agents_dir(tmp_path: Path) -> Path:
    agents_dir = tmp_path / ".gemini" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "orchestrator.md").write_text("# orchestrator\n", encoding="utf-8")
    (agents_dir / "developer.md").write_text("# developer\n", encoding="utf-8")
    return agents_dir


def _inject(provider: str, agents_dir: Path, project_root: Path) -> dict:
    return _engine().run_bootstrap(
        provider, agents_dir, project_root, context_file="AGENTS.md",
    )


# --------------------------------------------------------------------------- #
# AC-10 — one scoped pair per provider, both rosters survive
# --------------------------------------------------------------------------- #

def test_gemini_and_zcode_emit_one_scoped_pair_each(tmp_path):
    agents_dir = _gemini_agents_dir(tmp_path)
    target = tmp_path / "AGENTS.md"
    target.write_text("# Project\n\nUser intro.\n", encoding="utf-8")

    assert _inject("Gemini", agents_dir, tmp_path)["status"] == "success"
    assert _inject("ZCode", agents_dir, tmp_path)["status"] == "success"

    text = target.read_text(encoding="utf-8")
    assert text.count(_marker("Gemini", "begin")) == 1
    assert text.count(_marker("Gemini", "end")) == 1
    assert text.count(_marker("ZCode", "begin")) == 1
    assert text.count(_marker("ZCode", "end")) == 1
    assert LEGACY_BEGIN not in text
    # Both rosters survive: the second writer must not clobber the first.
    assert "define_subagent" in _block(text, "Gemini")
    assert "Workspace-Level" in _block(text, "ZCode")
    assert "User intro." in text


def test_injection_is_idempotent_per_provider(tmp_path):
    agents_dir = _gemini_agents_dir(tmp_path)
    target = tmp_path / "AGENTS.md"
    target.write_text("# Project\n", encoding="utf-8")

    _inject("Gemini", agents_dir, tmp_path)
    _inject("ZCode", agents_dir, tmp_path)
    first = target.read_text(encoding="utf-8")

    _inject("Gemini", agents_dir, tmp_path)
    _inject("ZCode", agents_dir, tmp_path)
    second = target.read_text(encoding="utf-8")

    assert first == second
    assert second.count(_marker("Gemini", "begin")) == 1
    assert second.count(_marker("ZCode", "begin")) == 1


# --------------------------------------------------------------------------- #
# AC-16b — inactive provider's scoped marker removed, active one survives
# --------------------------------------------------------------------------- #

def test_inactive_provider_scoped_marker_removed_active_survives(tmp_path):
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "# Project\n\n"
        f"{_marker('Gemini', 'begin')}\nGemini roster\n{_marker('Gemini', 'end')}\n\n"
        f"{_marker('ZCode', 'begin')}\nZCode roster\n{_marker('ZCode', 'end')}\n\n"
        "## Eigene Notizen\n\nUser note stays.\n",
        encoding="utf-8",
    )

    _cleanup(target, ["Gemini"], tmp_path)

    text = target.read_text(encoding="utf-8")
    assert _marker("Gemini", "begin") in text
    assert "Gemini roster" in text
    assert _marker("ZCode", "begin") not in text
    assert _marker("ZCode", "end") not in text
    assert "ZCode roster" not in text
    assert "User note stays." in text


# --------------------------------------------------------------------------- #
# AC-16c — legacy id-less pair discarded, rebuilt per provider
# --------------------------------------------------------------------------- #

def test_legacy_unscoped_pair_discarded_then_both_scoped_pairs_written(tmp_path):
    agents_dir = _gemini_agents_dir(tmp_path)
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "# Project\n\n"
        f"{LEGACY_BEGIN}\n"
        "Legacy ZCode-sourced roster — unattributable.\n"
        f"{LEGACY_END}\n\n"
        "## Eigene Notizen\n\nUser note stays.\n",
        encoding="utf-8",
    )

    # Real sync order: context cleanup discards the legacy pair, then the
    # per-provider agents step writes each scoped pair in registry order.
    _cleanup(target, ["Gemini", "ZCode"], tmp_path)
    assert LEGACY_BEGIN not in target.read_text(encoding="utf-8")

    _inject("Gemini", agents_dir, tmp_path)
    _inject("ZCode", agents_dir, tmp_path)

    text = target.read_text(encoding="utf-8")
    assert LEGACY_BEGIN not in text
    assert LEGACY_END not in text
    assert _marker("Gemini", "begin") in text
    assert _marker("ZCode", "begin") in text
    assert "define_subagent" in _block(text, "Gemini")
    assert "User note stays." in text


def test_legacy_pair_removed_even_without_injection(tmp_path):
    """Cleanup alone discards the id-less pair (M-6); nothing inherits it."""
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "# Project\n\n"
        f"{LEGACY_BEGIN}\nLegacy.\n{LEGACY_END}\n\n"
        "## Eigene Notizen\n\nUser note stays.\n",
        encoding="utf-8",
    )

    # No inject provider is active — the id-less pair is still discarded.
    _cleanup(target, ["Claude"], tmp_path)

    text = target.read_text(encoding="utf-8")
    assert LEGACY_BEGIN not in text
    assert LEGACY_END not in text
    assert "Legacy." not in text
    assert "User note stays." in text


# --------------------------------------------------------------------------- #
# AC-16a — repeated cleanup + injection never touches user notes
# --------------------------------------------------------------------------- #

def test_user_notes_survive_cleanup_and_reinjection(tmp_path):
    agents_dir = _gemini_agents_dir(tmp_path)
    target = tmp_path / "AGENTS.md"
    target.write_text(
        "# Project\n\n"
        f"{LEGACY_BEGIN}\nLegacy.\n{LEGACY_END}\n\n"
        "## Eigene Notizen\n\nMy personal notes.\n",
        encoding="utf-8",
    )

    for _ in range(2):
        _cleanup(target, ["Gemini", "ZCode"], tmp_path)
        _inject("Gemini", agents_dir, tmp_path)
        _inject("ZCode", agents_dir, tmp_path)

    text = target.read_text(encoding="utf-8")
    assert "My personal notes." in text
    assert text.count(_marker("Gemini", "begin")) == 1
    assert text.count(_marker("ZCode", "begin")) == 1


# --------------------------------------------------------------------------- #
# OQ-2 — Continue `.continue/config.yaml` is a `cn review`-only surface
# --------------------------------------------------------------------------- #

def test_continue_dead_agents_block_is_removed(tmp_path):
    config_path = tmp_path / ".continue" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text(
        "# Continue configuration\n"
        "name: Example\n"
        "version: 1.0.0\n"
        "\n"
        f"{CONTINUE_DEAD_BEGIN}\n"
        "# Auto-generated by agent-meta sync.py — do not edit manually\n"
        "agents:\n"
        "  - name: developer\n"
        "    prompt: prompts/developer.md\n"
        f"{CONTINUE_DEAD_END}\n",
        encoding="utf-8",
    )
    agents_dir = tmp_path / ".continue" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "developer.md").write_text("# developer\n", encoding="utf-8")

    _engine().run_bootstrap("Continue", agents_dir, tmp_path)

    text = config_path.read_text(encoding="utf-8")
    assert CONTINUE_DEAD_BEGIN not in text
    assert CONTINUE_DEAD_END not in text
    assert "\nagents:" not in text
    assert "prompt: prompts/developer.md" not in text
    # `.continue/agents/*.md` keep being generated for `cn review`.
    assert (agents_dir / "developer.md").exists()


def test_continue_config_unchanged_when_no_dead_block(tmp_path):
    config_path = tmp_path / ".continue" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    original = "name: Example\nversion: 1.0.0\n"
    config_path.write_text(original, encoding="utf-8")
    agents_dir = tmp_path / ".continue" / "agents"
    agents_dir.mkdir(parents=True, exist_ok=True)
    (agents_dir / "developer.md").write_text("# developer\n", encoding="utf-8")

    _engine().run_bootstrap("Continue", agents_dir, tmp_path)

    assert config_path.read_text(encoding="utf-8") == original


def test_continue_header_comment_is_cn_review_only(tmp_path):
    config_path = tmp_path / ".continue" / "config.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)
    config_path.write_text("name: Example\nversion: 1.0.0\n", encoding="utf-8")

    _update_continue_config_managed_block(
        config_path,
        {"AGENT_META_VERSION": "1.2.3", "AGENT_META_DATE": "2026-10-01"},
        SyncLog(),
        dry_run=False,
        project_root=tmp_path,
    )

    text = config_path.read_text(encoding="utf-8")
    agents_line = next(
        line for line in text.splitlines() if line.startswith("# Agents :")
    )
    assert "cn review" in agents_line
    assert "auto-discovered" not in agents_line
    assert "# Rules  : .continue/rules/" in text
