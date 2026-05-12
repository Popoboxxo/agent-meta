"""Shared pytest fixtures for scripts/lib tests."""

import sys
from pathlib import Path

import pytest

# Ensure scripts/ is on the path so lib can be imported directly
SCRIPTS_DIR = Path(__file__).resolve().parent.parent.parent
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))

AGENT_META_ROOT = SCRIPTS_DIR.parent


@pytest.fixture
def agent_meta_root():
    return AGENT_META_ROOT


@pytest.fixture
def minimal_config():
    return {
        "project": {"name": "test-project"},
        "ai-providers": ["Claude"],
        "roles": ["developer", "git", "orchestrator"],
    }


@pytest.fixture
def minimal_agent_md():
    return "---\nname: developer\nversion: 1.0.0\ndescription: Test agent\n---\n\n## Body\n\nContent here.\n"
