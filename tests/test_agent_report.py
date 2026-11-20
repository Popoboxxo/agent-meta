"""Batch-0 Task 1.1 — per-role x provider measurement CLI tests.

Covers SPEC-AGENT-LOOP-BATCH0-2026-11-20 IC-1..IC-4 / AC-1..4 and the
binding OQ-2/3/4 decisions from the spec review:

* OQ-2: ``session-sum`` is a TOP-LEVEL reserved sibling next to provider keys —
  there is NO ``"providers"`` wrapper in the emitted JSON.
* OQ-3: the session sum aggregates only always-on components
  (``entry-file`` + ``rules`` + ``descriptions``), never the role bodies.
* OQ-4: measurement reads rendered ``.claude/agents/*.md``; the agents_dir
  stays configurable via the function argument.

Run: python3 -m pytest tests/test_agent_report.py -q
"""

from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS = REPO_ROOT / "scripts"
sys.path.insert(0, str(SCRIPTS))

from lib import agent_report  # noqa: E402  (after sys.path insertion)

_spec = importlib.util.spec_from_file_location(
    "measure_context_under_test", SCRIPTS / "measure_context.py")
measure_context = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(measure_context)  # noqa: E402


PROVIDER_A = "p-alpha"
PROVIDER_B = "p-beta"
ROLE_CONTENT = {
    "orchestrator": "# Orchestrator\n\nRole body A.\n" * 4,
    "developer": "# Developer\n\nRole body B.\n" * 3,
}
ALWAYS_ON = {
    "entry-file": {"bytes": 1000, "lines": 10, "tokens_approx": 250},
    "rules": {"bytes": 2000, "lines": 20, "tokens_approx": 500},
    "descriptions": {"bytes": 400, "lines": 4, "tokens_approx": 100},
}


def _seed_agents(tmp_path: Path) -> Path:
    """Create ``<tmp>/.claude/agents/<provider>/<role>.md`` for two providers."""
    agents_dir = tmp_path / ".claude" / "agents"
    for provider in (PROVIDER_A, PROVIDER_B):
        provider_dir = agents_dir / provider
        provider_dir.mkdir(parents=True)
        for role, content in ROLE_CONTENT.items():
            (provider_dir / f"{role}.md").write_text(content, encoding="utf-8")
    return agents_dir


# ---------------------------------------------------------------------------
# IC-1 / AC-1 — measure_agents() shape
# ---------------------------------------------------------------------------

def test_measure_agents_returns_exact_shape(tmp_path):
    agents_dir = _seed_agents(tmp_path)
    report = agent_report.measure_agents(agents_dir, [PROVIDER_A, PROVIDER_B])

    assert set(report) == {PROVIDER_A, PROVIDER_B}
    for provider in (PROVIDER_A, PROVIDER_B):
        assert set(report[provider]) == set(ROLE_CONTENT)
        for role, stat in report[provider].items():
            assert set(stat) == {"bytes", "lines", "tokens_approx"}
            assert all(isinstance(v, int) for v in stat.values())
            assert stat["bytes"] == len(ROLE_CONTENT[role].encode("utf-8"))
            assert stat["tokens_approx"] == stat["bytes"] // 4


# ---------------------------------------------------------------------------
# IC-1b / AC-2 / OQ-3 — session sum = always-on only, NOT + roles
# ---------------------------------------------------------------------------

def test_session_sum_is_always_on_only_not_roles(tmp_path):
    agents_dir = _seed_agents(tmp_path)
    agents = agent_report.measure_agents(agents_dir, [PROVIDER_A])
    # Role bodies are present in the report view but must be ignored.
    view = dict(ALWAYS_ON)
    view.update(agents)
    total = agent_report.session_sum(view, ("entry-file", "rules", "descriptions"))

    assert set(total) == {"bytes", "lines", "tokens_approx"}
    assert total["bytes"] == 1000 + 2000 + 400  # 3400, NOT + role bytes
    assert total["lines"] == 10 + 20 + 4
    assert total["tokens_approx"] == 250 + 500 + 100
    role_bytes = sum(s["bytes"] for s in agents[PROVIDER_A].values())
    assert total["bytes"] != 3400 + role_bytes


# ---------------------------------------------------------------------------
# IC-2/IC-3 / AC-3 / OQ-2 — CLI emits top-level session-sum sibling
# ---------------------------------------------------------------------------

def test_cli_per_agent_json_has_top_level_session_sum_sibling(tmp_path, capsys):
    agents_dir = _seed_agents(tmp_path)
    # Always-on sources for the CLI: entry-file + rules + description lines.
    (tmp_path / "AGENTS.md").write_text("x" * 1000 + "\n" * 9, encoding="utf-8")
    rules_dir = tmp_path / ".claude" / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "rule.md").write_text("y" * 2000 + "\n" * 19, encoding="utf-8")

    rc = measure_context.run_agent_report(agents_dir, True)
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)

    assert "session-sum" in payload
    assert "providers" not in payload  # OQ-2: no wrapper
    assert PROVIDER_A in payload and PROVIDER_B in payload
    assert set(payload[PROVIDER_A]) == set(ROLE_CONTENT)
    assert set(payload["session-sum"]) == {"bytes", "lines", "tokens_approx"}
    assert payload["session-sum"]["bytes"] > 0  # entry + rules + descriptions measured


def test_render_agent_table_has_total_and_session_sum_rows():
    agents = {PROVIDER_A: {"orchestrator": {"bytes": 40, "lines": 4, "tokens_approx": 10}}}
    report = agent_report.build_agent_report(agents, ALWAYS_ON)
    table = agent_report.render_agent_table(report)

    assert "TOTAL" in table
    assert "SESSION-SUM" in table
    assert "Provider" in table and "Role" in table
    assert "3400" in table  # session-sum bytes from always-on only


# ---------------------------------------------------------------------------
# Provider-agnostic (AC-12) — no provider-name literals in the measurement path
# ---------------------------------------------------------------------------

def test_measurement_code_is_provider_agnostic():
    source = Path(agent_report.__file__).read_text(encoding="utf-8").lower()
    # Quoted literals used as provider identifiers are forbidden; path
    # fragments and Python keywords (e.g. ``continue``) are not provider names.
    for literal in ("claude", "gemini", "opencode", "mammouth",
                    "copilot", "antigravity"):
        for token in (f'"{literal}"', f"'{literal}'"):
            assert token not in source, f"provider literal {token} in agent_report.py"
    # Comparing against the reserved session-sum key is allowed; comparing a
    # provider against a quoted name is not.
    for token in ('provider == "', "provider == '"):
        assert token not in source, f"hardcoded provider comparison {token}"
    assert 'provider in ("' not in source
    assert "provider in ('" not in source


# ---------------------------------------------------------------------------
# Error paths — empty providers -> ValueError, missing dir -> FileNotFoundError
# ---------------------------------------------------------------------------

def test_empty_providers_raises_value_error(tmp_path):
    agents_dir = _seed_agents(tmp_path)
    with pytest.raises(ValueError, match="no agent roles found"):
        agent_report.measure_agents(agents_dir, [])


def test_missing_agents_dir_raises_file_not_found(tmp_path):
    with pytest.raises(FileNotFoundError):
        agent_report.measure_agents(tmp_path / "does-not-exist", [PROVIDER_A])


def test_missing_provider_dir_raises_file_not_found(tmp_path):
    agents_dir = _seed_agents(tmp_path)
    with pytest.raises(FileNotFoundError):
        agent_report.measure_agents(agents_dir, ["missing-provider"])


# ---------------------------------------------------------------------------
# IC-2 / AC-4 — argparse flag wiring (canonical form: --per-agent --project P)
# ---------------------------------------------------------------------------

def test_parse_args_per_agent_sets_flag():
    args = measure_context.parse_args(["--per-agent", "--json"])
    assert args.per_agent is True
    assert args.json is True
    assert args.project is None


def test_parse_args_per_agent_together_with_project_is_allowed():
    # AC-4 / IC-2 data flow :112: --per-agent --project P [--json] is canonical.
    args = measure_context.parse_args(
        ["--per-agent", "--project", "somewhere", "--json"])
    assert args.per_agent is True
    assert args.project == "somewhere"
    assert args.json is True


def test_no_per_agent_without_project(tmp_path, capsys):
    # AC-4 (IC-2): --per-agent without --project -> stderr + Exit 2.
    rc = measure_context.main(["--per-agent"])
    assert rc == 2
    assert "requires --project" in capsys.readouterr().err


def test_per_agent_with_project_json(tmp_path, capsys):
    # AC-4 (IC-2/IC-3): canonical form -> Exit 0, JSON roles + session-sum.
    _seed_agents(tmp_path)
    (tmp_path / "AGENTS.md").write_text("x" * 1000 + "\n" * 9, encoding="utf-8")
    rules_dir = tmp_path / ".claude" / "rules"
    rules_dir.mkdir(parents=True)
    (rules_dir / "rule.md").write_text("y" * 2000 + "\n" * 19, encoding="utf-8")

    rc = measure_context.main(
        ["--per-agent", "--project", str(tmp_path), "--json"])
    assert rc == 0
    payload = json.loads(capsys.readouterr().out)
    assert PROVIDER_A in payload and PROVIDER_B in payload
    assert set(payload[PROVIDER_A]) == set(ROLE_CONTENT)
    assert "session-sum" in payload
    assert set(payload["session-sum"]) == {"bytes", "lines", "tokens_approx"}
    assert payload["session-sum"]["bytes"] > 0


def test_non_per_agent_args_unchanged():
    # AC regression: NO-flag behaviour must stay unchanged.
    args = measure_context.parse_args([])
    assert args.target is None
    assert args.project is None
    assert args.json is False
    assert args.per_agent is False
