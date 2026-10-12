"""Docs guardrail: context-related doc corrections and tokenizer measurement doc (Task 0a.10).

Source-assertions pinning corrected claims (study 2026-10-11-context-budget-provider-study.md)
and the structure of the measurement doc. Run:
python3 -m pytest tests/test_context_docs_corrections.py -q
"""
from pathlib import Path
import re

_ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (_ROOT / rel).read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def test_check_help_states_forced_dry_run():
    text = _read("scripts/sync.py")
    assert "use with --dry-run" not in text
    assert "forces dry-run" in _flat(text)


def test_codex_rules_section_not_claiming_loaded_channel():
    text = _read("docs/providers/codex.md")
    flat = _flat(text)
    assert "codex reads a project-root `rules/` directory" not in flat
    assert "starlark" in flat
    assert "nearest-wins" not in flat
    assert "open point (p6)" not in flat


def test_kimi_precedence_is_concatenation():
    flat = _flat(_read("docs/providers/kimi-code.md"))
    assert "nearest-wins" not in flat
    assert "concatenat" in flat


def test_gemini_doc_reflects_native_subagents_and_context_filename():
    text = _read("docs/providers/gemini-cli.md")
    flat = _flat(text)
    assert "kein natives sub-agenten-system" not in flat
    assert "sub-agenten inoffiziell" not in flat
    assert "context.filename" in flat
    assert ".strict()" in text
    assert "von keinem" in flat  # .gemini/rules read by no harness


def test_measurement_doc_has_orchestrator_and_agents_md_rows():
    path = _ROOT / "docs/analysis/2026-10-11-context-tokenizer-measurement.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    rows = [ln for ln in text.splitlines() if ln.startswith("|")]
    assert any("orchestrator" in ln.lower() for ln in rows)
    assert any("AGENTS.md" in ln for ln in rows)
    assert "UNVERIFIED" in text
    assert "measure_tokens.py" in text


def test_measure_tokens_script_exists_and_degrades_without_tokenizer():
    path = _ROOT / "tests/manual/measure_tokens.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "ImportError" in text


def test_changelog_mentions_964_items():
    text = _read("CHANGELOG.md")
    unreleased = text.split("\n## [", 2)[1]
    assert "--context-report" in unreleased
    assert "#964" in unreleased
