"""Block-snippet inlining transform (SPEC ``dynamic-routing-template-slimming``).

Covers the canonical transform from SPEC §3.7 / plan Task 10, Block B (B1/B3)
and decision O-D: leading YAML frontmatter is stripped, line endings are
normalised to ``\n`` and the result is reduced with ``strip("\n")``. The three
``snippets/agents/`` block bodies are asserted byte-exactly and
``build_variables()`` must load them deterministically.
"""
from __future__ import annotations

from pathlib import Path

from scripts.lib.config import _load_block_snippet, build_variables

_REPO_ROOT = Path(__file__).resolve().parents[1]
_BLOCK_SNIPPETS_DIR = _REPO_ROOT / "snippets" / "agents"

BACKGROUND_PROCESS_GUARD_BODY = (
    "## Background-Process Guard (issue #506)\n"
    "\n"
    "Wenn du einen Hintergrundprozess startest, MUSST du innerhalb deines "
    "eigenen Turns aktiv auf dessen Completion warten (docker wait, Polling "
    "mit Timeout, synchrones Blockieren). Dein Turn darf NIEMALS mit einem "
    "'waiting'-Platzhalter enden. Es gibt KEINE Reaktivierung nach Turn-Ende "
    "— dein letzter Output ist das Endergebnis."
)

OUTPUT_GUARD_BODY = (
    "<output-guard>\n" + BACKGROUND_PROCESS_GUARD_BODY + "\n</output-guard>"
)

PARSE_INPUT_BODY = (
    "## 1. Parse input\n"
    "A2A envelope present → parse `payload.{t,ctx,con,refs,pri,dep}`. "
    "Otherwise: plain directive from `main_chat`."
)

_BLOCK_KEYS = ("OUTPUT_GUARD_BLOCK", "BACKGROUND_PROCESS_GUARD_BLOCK", "PARSE_INPUT_BLOCK")


def test_missing_file_returns_empty_string(tmp_path):
    assert _load_block_snippet(tmp_path / "does-not-exist.md") == ""


def test_frontmatter_is_stripped(tmp_path):
    path = tmp_path / "block.md"
    path.write_text(
        '---\nsnippet: demo\nversion: "1.0.0"\n---\n\nbody line\n',
        encoding="utf-8",
    )
    result = _load_block_snippet(path)
    assert result == "body line"
    assert not result.startswith("---")
    assert "snippet:" not in result


def test_crlf_input_is_normalised_and_frontmatter_stripped(tmp_path):
    path = tmp_path / "crlf.md"
    path.write_bytes(b"---\r\nsnippet: demo\r\n---\r\nline1\r\nline2\r\n")
    result = _load_block_snippet(path)
    assert result == "line1\nline2"
    assert "\r" not in result


def test_lone_cr_input_is_normalised(tmp_path):
    path = tmp_path / "cr.md"
    path.write_bytes(b"line1\rline2\r")
    result = _load_block_snippet(path)
    assert result == "line1\nline2"
    assert "\r" not in result


def test_trailing_newlines_are_stripped(tmp_path):
    path = tmp_path / "trailing.md"
    path.write_text("body\n\n\n", encoding="utf-8")
    assert _load_block_snippet(path) == "body"


def test_real_background_process_guard_matches_canonical_body():
    assert (
        _load_block_snippet(_BLOCK_SNIPPETS_DIR / "background-process-guard.md")
        == BACKGROUND_PROCESS_GUARD_BODY
    )


def test_real_output_guard_wraps_background_body():
    result = _load_block_snippet(_BLOCK_SNIPPETS_DIR / "output-guard.md")
    assert result == OUTPUT_GUARD_BODY
    assert result == "<output-guard>\n" + BACKGROUND_PROCESS_GUARD_BODY + "\n</output-guard>"


def test_real_parse_input_matches_canonical_body():
    assert (
        _load_block_snippet(_BLOCK_SNIPPETS_DIR / "parse-input.md")
        == PARSE_INPUT_BODY
    )


def test_build_variables_loads_blocks_deterministically():
    first, _ = build_variables({}, _REPO_ROOT)
    second, _ = build_variables({}, _REPO_ROOT)
    for key in _BLOCK_KEYS:
        assert first[key] == second[key]
    assert first["BACKGROUND_PROCESS_GUARD_BLOCK"] == BACKGROUND_PROCESS_GUARD_BODY
    assert first["OUTPUT_GUARD_BLOCK"] == OUTPUT_GUARD_BODY
    assert first["PARSE_INPUT_BLOCK"] == PARSE_INPUT_BODY


# Pre-existing snippet variables loaded by `_build_snippet_variables()`. The new
# agents/ block loader must not touch this legacy path, so each value is pinned
# byte-exactly against a direct read of its source file.
_VERBATIM_ORCHESTRATOR_BLOCKS = (
    ("SE_MODE_BLOCK", "se-mode"),
    ("A2A_PROTOCOL_BLOCK", "a2a-protocol"),
    ("CHECKPOINTING_BLOCK", "checkpointing"),
    ("QUALITY_PIPELINES_BLOCK", "quality-pipelines"),
    ("STATUS_TABLE_BLOCK", "status-table"),
)
_SUBSTITUTED_DEVELOPER_BLOCKS = (
    ("BROWSER_VERIFICATION_BLOCK", "browser-verification"),
    ("LANGUAGE_BEST_PRACTICES_BLOCK", "language-best-practices"),
)


def test_existing_snippet_load_path_is_byte_neutral():
    """Output neutrality: the legacy snippet path stays byte-identical.

    Guards the Task-10 acceptance that wiring the new ``snippets/agents/``
    block variables leaves every pre-existing block (SE / A2A / checkpoint /
    quality-pipelines / status-table / browser-verification / language-best-
    practices / prompt-injection) byte-for-byte unchanged.
    """
    variables, _ = build_variables({}, _REPO_ROOT)

    for var, stem in _VERBATIM_ORCHESTRATOR_BLOCKS:
        expected = (
            _REPO_ROOT / "snippets" / "orchestrator" / f"{stem}.md"
        ).read_text(encoding="utf-8")
        assert variables[var] == expected, var

    for var, stem in _SUBSTITUTED_DEVELOPER_BLOCKS:
        expected = (
            _REPO_ROOT / "snippets" / "developer" / f"{stem}.md"
        ).read_text(encoding="utf-8")
        expected = expected.replace("{{LANGUAGE}}", str(variables.get("LANGUAGE", "")))
        assert variables[var] == expected, var

    pid_expected = (
        _REPO_ROOT / "snippets" / "security" / "prompt-injection-defense.md"
    ).read_text(encoding="utf-8").rstrip("\n")
    assert variables["PROMPT_INJECTION_DEFENSE_BLOCK"] == pid_expected


def test_existing_snippet_blocks_are_deterministic_across_builds():
    """The legacy blocks are stable too — no accidental slurp/ordering drift."""
    legacy_keys = [
        var for var, _ in _VERBATIM_ORCHESTRATOR_BLOCKS
    ] + [
        var for var, _ in _SUBSTITUTED_DEVELOPER_BLOCKS
    ] + ["PROMPT_INJECTION_DEFENSE_BLOCK"]

    first, _ = build_variables({}, _REPO_ROOT)
    second, _ = build_variables({}, _REPO_ROOT)
    for key in legacy_keys:
        assert first[key] == second[key], key
