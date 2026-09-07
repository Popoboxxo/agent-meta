"""Every active provider's own context_file must be protected from the
`settings` gitignore category, not just Claude's (issue #682 §4 bugfix).

The bug: the old code compared each provider's context_file against the
hardcoded literal "CLAUDE.md" (later against Claude's resolved value) and
only exempted a match -- meaning Gemini's AGENTS.md, Opencode's AGENTS.md,
and Mammouth's MAMMOUTH.md were all still gitignorable under
`settings: true`, defeating the framework's "context file never
ignorable" premise for every provider except Claude. The fix removes the
comparison entirely: a provider's context_file, once present, is simply
never appended to `entries`, for any provider.
"""

import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.gitignore import compute_base_gitignore_entries  # noqa: E402

_PROVIDERS_CONFIG = _REPO_ROOT / "config" / "ai-providers.yaml"


def _load_provider_config() -> dict:
    with _PROVIDERS_CONFIG.open(encoding="utf-8") as f:
        return yaml.safe_load(f)["providers"]


def test_real_config_all_context_files_protected_settings_true():
    # Regression + bugfix: under the real config, settings: true must
    # protect BOTH Claude's and Gemini's context file, not just Claude's.
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        ["Claude", "Gemini"], provider_config, {"settings": True}
    )
    assert "CLAUDE.md" not in entries
    assert "AGENTS.md" not in entries  # was gitignorable before the fix -- now protected


def test_context_file_protection_is_provider_agnostic():
    # Any provider's context_file, whatever its value, is never gitignored --
    # no special-casing of any single provider's literal value.
    provider_config = {
        "Claude": {"context_file": "CLAUDE_CUSTOM.md", "gitignore_entries": []},
        "Gemini": {"context_file": "AGENTS.md"},
        "Mammouth": {"context_file": "MAMMOUTH.md"},
    }
    entries = compute_base_gitignore_entries(
        ["Claude", "Gemini", "Mammouth"], provider_config, {"settings": True}
    )
    assert "CLAUDE_CUSTOM.md" not in entries
    assert "AGENTS.md" not in entries
    assert "MAMMOUTH.md" not in entries


def test_settings_false_still_keeps_all_context_files_out_default():
    provider_config = _load_provider_config()
    entries = compute_base_gitignore_entries(
        ["Claude", "Gemini"], provider_config, {"settings": False}
    )
    assert "CLAUDE.md" not in entries
    assert "AGENTS.md" not in entries
