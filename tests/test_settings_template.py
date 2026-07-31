"""Regression test: the Claude settings template ships a non-empty default
permission deny-list for destructive shell operations.

Run: python -m pytest tests/test_settings_template.py -v
"""

import json
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_TEMPLATE = _REPO_ROOT / "templates" / "configs" / "CLAUDE.settings-template.json"

REQUIRED_DENY_PREFIXES = (
    "Bash(rm -rf",
    "Bash(git push --force",
    "Bash(git reset --hard",
)


def test_settings_template_has_default_deny_list():
    data = json.loads(_TEMPLATE.read_text(encoding="utf-8"))
    deny = data["permissions"]["deny"]
    assert isinstance(deny, list) and len(deny) > 0
    for prefix in REQUIRED_DENY_PREFIXES:
        assert any(entry.startswith(prefix) for entry in deny), (
            f"expected a deny entry starting with {prefix!r}, got {deny!r}"
        )


def test_settings_template_is_still_valid_json():
    # Guards against a hand-edit breaking JSON syntax.
    json.loads(_TEMPLATE.read_text(encoding="utf-8"))
