"""Unit tests for the context file size guard (issue #540, Phase C2).

check_context_file_size() must emit a WARNING (never an error) when a
sync-generated provider context file exceeds the soft line limit without
acknowledgment, and stay silent:

  - under the limit
  - over the limit WITH context_file.oversize_acknowledged: true

Files without the managed-block marker are hand-written and never reported;
providers sharing one context file (Gemini + Opencode -> AGENTS.md) must be
reported at most once.
"""

import tempfile
from pathlib import Path

from scripts.lib.consistency.report import Severity
from scripts.lib.consistency.context_size import DEFAULT_MAX_LINES, check_context_file_size
from scripts.lib.io import _YAML_AVAILABLE

MANAGED = "<!-- agent-meta:managed-begin -->\n"

# Two providers that share AGENTS.md + one with its own file — mirrors the
# agent-meta self-hosting layout.
PROVIDERS = {
    "Claude": {"context_file": "CLAUDE.md"},
    "Gemini": {"context_file": "AGENTS.md"},
    "Opencode": {"context_file": "AGENTS.md"},
}


def _write(root: Path, rel: str, lines: int, managed: bool = True) -> None:
    """Write a fake generated context file with ``lines`` content lines."""
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    body = "\n".join(f"line {i}" for i in range(lines)) + "\n"
    path.write_text((MANAGED if managed else "") + body, encoding="utf-8")


def test_under_limit_no_warning():
    """A generated file within the limit must not produce any finding."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, "CLAUDE.md", 10)
        findings = check_context_file_size(
            root,
            config={"context_file": {"max_lines": 250}},
            provider_config=PROVIDERS,
        )
        assert findings == []


def test_over_limit_without_ack_warns():
    """Over the limit without acknowledgment -> exactly one WARNING per file."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, "CLAUDE.md", 300)
        _write(root, "AGENTS.md", 400)
        # The guard counts TOTAL file lines (marker line included).
        agents_lines = len((root / "AGENTS.md").read_text(encoding="utf-8").splitlines())
        findings = check_context_file_size(
            root,
            config={"context_file": {}},  # default limit applies
            provider_config=PROVIDERS,
        )
        assert [f.severity for f in findings] == [Severity.WARNING] * 2
        reported = sorted(f.file for f in findings)
        assert reported == ["AGENTS.md", "CLAUDE.md"]
        agents = next(f for f in findings if f.file == "AGENTS.md")
        assert str(agents_lines) in agents.message
        assert str(DEFAULT_MAX_LINES) in agents.message
        assert "oversize_acknowledged" in agents.suggestion


def test_over_limit_with_ack_no_warning():
    """oversize_acknowledged: true must suppress the warning entirely."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, "CLAUDE.md", 300)
        _write(root, "AGENTS.md", 5000)
        findings = check_context_file_size(
            root,
            config={"context_file": {"oversize_acknowledged": True}},
            provider_config=PROVIDERS,
        )
        assert findings == []


def test_custom_max_lines_is_honored():
    """A project-specific max_lines overrides the default threshold."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, "CLAUDE.md", 20)
        under = check_context_file_size(
            root,
            config={"context_file": {"max_lines": 50}},
            provider_config=PROVIDERS,
        )
        assert under == []
        over = check_context_file_size(
            root,
            config={"context_file": {"max_lines": 10}},
            provider_config=PROVIDERS,
        )
        assert len(over) == 1 and over[0].file == "CLAUDE.md"
        assert "(limit: 10)" in over[0].message


def test_handwritten_file_without_marker_is_ignored():
    """Files lacking the managed-block marker are not sync output."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        _write(root, "CLAUDE.md", 300, managed=False)
        findings = check_context_file_size(
            root,
            config={"context_file": {}},
            provider_config=PROVIDERS,
        )
        assert findings == []


def test_missing_files_and_invalid_config_are_tolerated():
    """Absent files and a malformed context_file block must not crash."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        # No files written at all; max_lines of wrong type falls back to default.
        findings = check_context_file_size(
            root,
            config={"context_file": {"max_lines": "not-an-int"}},
            provider_config=PROVIDERS,
        )
        assert findings == []


def test_config_loaded_from_project_yaml():
    """Integration path: config is read from .meta-config/project.yaml."""
    with tempfile.TemporaryDirectory() as tmp:
        root = Path(tmp)
        cfg_dir = root / ".meta-config"
        cfg_dir.mkdir()
        (cfg_dir / "project.yaml").write_text(
            "ai-providers:\n- Claude\ncontext_file:\n"
            "  mode: full\n  max_lines: 5\n  oversize_acknowledged: false\n",
            encoding="utf-8",
        )
        _write(root, "CLAUDE.md", 7)
        if not _YAML_AVAILABLE:
            return  # loader skips YAML configs without PyYAML — nothing to assert
        findings = check_context_file_size(
            root, config=None, provider_config=PROVIDERS,
        )
        assert len(findings) == 1
        assert findings[0].file == "CLAUDE.md"
        assert "(limit: 5)" in findings[0].message
