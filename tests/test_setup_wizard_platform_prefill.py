"""Task 7 (platform-project-defaults feature): pure default-selection
helper for the setup wizard's platform prefill (design spec §5) -- NOT the
full interactive wizard (see tests/test_setup_wizard_secrets_prompt.py for
wizard-level coverage of unrelated fields).
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.setup import _platform_prefill


def test_platform_prefill_uses_platform_default_when_available():
    result = _platform_prefill(_REPO_ROOT, ["hacs"], "TEST_COMMANDS", "bun test")
    assert result == "pytest tests/ --cov"


def test_platform_prefill_falls_back_when_no_platforms():
    result = _platform_prefill(_REPO_ROOT, [], "TEST_COMMANDS", "bun test")
    assert result == "bun test"


def test_platform_prefill_falls_back_when_field_not_set_by_platform():
    result = _platform_prefill(_REPO_ROOT, ["hacs"], "DEV_COMMANDS", "bun run build")
    assert result == "bun run build"


def test_platform_prefill_dod_preset():
    result = _platform_prefill(_REPO_ROOT, ["hacs"], "dod-preset", "standard")
    assert result == "standard"
