"""Docs guardrail: context-related doc corrections and tokenizer measurement doc (Task 0a.10).

Source-assertions pinning corrected claims (study 2026-10-11-context-budget-provider-study.md)
and the structure of the measurement doc. Run:
python3 -m pytest tests/test_context_docs_corrections.py -q
"""
from pathlib import Path
import importlib.util
import re

_ROOT = Path(__file__).resolve().parents[1]


def _read(rel: str) -> str:
    return (_ROOT / rel).read_text(encoding="utf-8")


def _flat(text: str) -> str:
    return re.sub(r"\s+", " ", text).lower()


def _section(text: str, heading_re: str) -> str:
    """Return the body of the first markdown section whose heading matches."""
    parts = re.split(r"(?m)^(?=#{1,6} )", text)
    for part in parts:
        first = part.splitlines()[0] if part.strip() else ""
        if re.search(heading_re, first, re.IGNORECASE):
            return part
    raise AssertionError("section not found: " + heading_re)


def _sentences(text: str):
    return [_flat(x) for x in re.split(r"(?<=[.;])\s+|\n\s*\n", text) if x.strip()]


def _load_measure_tokens():
    path = _ROOT / "tests/manual/measure_tokens.py"
    spec = importlib.util.spec_from_file_location("measure_tokens", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


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


def test_codex_subdir_agents_md_not_claimed_as_override():
    text = _read("docs/providers/codex.md")
    section = _section(text, r"project context")
    flat = _flat(section)
    assert "concatenation semantics" in flat
    assert "effectively overrides" not in flat
    assert any("closer files appear later" in x and "higher precedence in practice" in x
               for x in _sentences(section))


def test_codex_rules_dir_is_inert_in_codex_section():
    text = _read("docs/providers/codex.md")
    assert any("rules" in x and "starlark" in x for x in _sentences(text))


def test_kimi_precedence_is_concatenation():
    text = _read("docs/providers/kimi-code.md")
    flat = _flat(text)
    assert "nearest-wins" not in flat
    assert any("concatenat" in x and "agents.md" in x for x in _sentences(text))


def test_multi_provider_kimi_agents_md_line_not_nearest_wins_like_codex():
    text = _read("docs/providers/multi-provider.md")
    lines = [ln for ln in text.splitlines() if ln.startswith("- `AGENTS.md`") and "Subdir" in ln]
    assert lines, "Kimi AGENTS.md context line missing"
    flat = _flat(lines[0])
    assert "nearest" not in flat
    assert "konkatenier" in flat


def test_gemini_doc_reflects_native_subagents_and_context_filename():
    text = _read("docs/providers/gemini-cli.md")
    flat = _flat(text)
    assert "kein natives sub-agenten-system" not in flat
    assert "sub-agenten inoffiziell" not in flat
    assert "context.filename" in flat
    assert ".strict()" in text
    assert any("ohne `context.filename`" in x and "agents.md" in x and "ignoriert" in x for x in _sentences(text))
    assert any(".gemini/rules" in x and "von keinem" in x for x in _sentences(text))


def test_measurement_doc_has_orchestrator_and_agents_md_rows():
    path = _ROOT / "docs/analysis/2026-10-11-context-tokenizer-measurement.md"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    rows = [ln for ln in text.splitlines() if ln.startswith("|")]
    assert any("orchestrator" in ln.lower() for ln in rows)
    assert any("AGENTS.md" in ln for ln in rows)
    assert "UNVERIFIED" in text
    assert "measure_tokens.py" in text
    assert "AC-05 OFFEN" in text
    open_section = _section(text, r"offene punkte")
    assert "AC-05" in open_section and "--strict" in open_section
    assert "lazy" in _section(text, r"abweichung|erkl")  # rules gap explained


def test_measure_tokens_script_exists_and_degrades_without_tokenizer():
    path = _ROOT / "tests/manual/measure_tokens.py"
    assert path.is_file()
    text = path.read_text(encoding="utf-8")
    assert "ImportError" in text


def test_measure_tokens_exit_codes_without_tokenizer(tmp_path, monkeypatch, capsys):
    mod = _load_measure_tokens()
    monkeypatch.setattr(mod, "_load_encoder", lambda: None)
    sample = tmp_path / "a.md"
    sample.write_text("hello", encoding="utf-8")
    assert mod.main(["--files", str(sample)]) == 0
    assert mod.main(["--strict", "--files", str(sample)]) == 3
    assert mod.main(["--strict"]) == 3
    assert "--strict" in mod.__doc__ or "strict" in capsys.readouterr().out.lower()


def test_measure_tokens_with_tokenizer_exits_zero(tmp_path, monkeypatch):
    mod = _load_measure_tokens()
    monkeypatch.setattr(mod, "_load_encoder", lambda: (lambda text: max(1, len(text) // 4)))
    sample = tmp_path / "a.md"
    sample.write_text("hello world", encoding="utf-8")
    assert mod.main(["--strict", "--files", str(sample)]) == 0


def test_measure_tokens_help_mentions_strict(capsys):
    mod = _load_measure_tokens()
    try:
        mod.main(["--help"])
    except SystemExit as exc:
        assert exc.code == 0
    assert "--strict" in capsys.readouterr().out


def test_changelog_mentions_964_items():
    text = _read("CHANGELOG.md")
    assert re.search(r"(?m)^## \[Unreleased\]", text)
    unreleased = text.split("\n## [", 2)[1]
    assert unreleased.startswith("Unreleased")
    assert "--context-report" in unreleased
    assert "#964" in unreleased
