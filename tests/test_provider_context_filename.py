"""Unit tests for lib.providers.resolve_context_filename (#578).

Regression coverage for the CLAUDE.md -> AGENTS.md fallback that used to be
duplicated inline at two call sites in scripts/sync.py.
"""

import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.providers import resolve_context_filename


def test_non_claude_default_falls_back_to_agents_md():
    assert resolve_context_filename("CLAUDE.md", "Opencode") == "AGENTS.md"


def test_claude_keeps_claude_md():
    assert resolve_context_filename("CLAUDE.md", "Claude") == "CLAUDE.md"


def test_explicit_context_file_is_never_overridden():
    """A provider with an explicit, non-CLAUDE.md context_file is passed through
    unchanged, regardless of provider name."""
    assert resolve_context_filename("GEMINI.md", "Gemini") == "GEMINI.md"
    assert resolve_context_filename("MAMMOUTH.md", "Mammouth") == "MAMMOUTH.md"


def test_empty_and_none_like_values_pass_through():
    assert resolve_context_filename("", "Opencode") == ""
