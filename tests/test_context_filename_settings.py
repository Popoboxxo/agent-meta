"""IC-15 Nr. 8 / AC-18: Gemini CLI context filename settings, no unread ``.gemini/rules``.

Gemini CLI reads ``GEMINI.md`` by default, so the shared core (``AGENTS.md``) is
only read when the provider-native settings file names it: ``context.fileName``
in ``.gemini/settings.json``. The unread ``.gemini/rules`` directory is no longer
written (rules stay embedded in ``AGENTS.md``) and a directory written by an
earlier version is cleaned up through its managed index only.

Everything is driven by config keys (``settings_file`` /
``context_filename_settings_key`` / ``rules_dir`` / ``retired_rules_dirs``) —
never a provider-name branch (``test_no_provider_literal_usage_in_lib``).

Run: python3 -m pytest tests/test_context_filename_settings.py -q
"""
from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.context import _adapter_settings_activation
from lib.providers import load_providers_config
from tests.active_set_render import preset_config, synced_projects


@pytest.fixture(scope="module")
def gemini_project(tmp_path_factory):
    return synced_projects(tmp_path_factory, {"Gemini": preset_config("Gemini")})["Gemini"]


def _sync(project: Path) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "sync.py"), "--config",
         str(project / ".meta-config" / "project.yaml")],
        cwd=project, capture_output=True, text=True, timeout=600)


def test_gemini_settings_name_the_core_context_file(gemini_project):
    """The native settings file names AGENTS.md so Gemini CLI reads it."""
    assert (gemini_project / "AGENTS.md").is_file()
    settings = json.loads(
        (gemini_project / ".gemini" / "settings.json").read_text(encoding="utf-8")
    )
    assert settings["context"]["fileName"] == "AGENTS.md"


def test_gemini_rules_dir_is_not_written(gemini_project):
    """AC-18: the unread ``.gemini/rules`` directory is not written."""
    assert not (gemini_project / ".gemini" / "rules").exists()


def test_gemini_declares_filename_settings_key_without_adapter():
    """Pure data: Gemini opts in via the settings key, not an adapter file."""
    pc = load_providers_config(REPO_ROOT, {})["Gemini"]
    assert pc.get("context_filename_settings_key") == "context.fileName"
    assert pc.get("context_adapter_file") is None
    assert not pc.get("has_rules")
    assert ".gemini/rules" in (pc.get("retired_rules_dirs") or [])


def test_settings_activation_is_config_key_driven():
    """The resolver reads ``settings_file`` + the provider-native dotted key."""
    activation = _adapter_settings_activation({
        "settings_file": ".gemini/settings.json",
        "context_filename_settings_key": "context.fileName",
        "context_file": "AGENTS.md",
    })
    assert activation == {
        "settings_file": ".gemini/settings.json",
        "settings_key": "context.fileName",
        "adapter_file": "AGENTS.md",
    }


def test_settings_activation_requires_settings_file_and_key():
    """A missing ``settings_file``, key or target file degrades to ``None``."""
    assert _adapter_settings_activation({"context_file": "AGENTS.md"}) is None
    assert _adapter_settings_activation({
        "settings_file": ".gemini/settings.json", "context_file": "AGENTS.md",
    }) is None
    assert _adapter_settings_activation({
        "settings_file": ".gemini/settings.json",
        "context_filename_settings_key": "context.fileName",
    }) is None


def test_legacy_gemini_rules_dir_cleanup_keeps_foreign_files(gemini_project, tmp_path):
    """A pre-existing ``.gemini/rules`` is removed through its managed index."""
    project = tmp_path / "legacy-gemini"
    shutil.copytree(gemini_project, project)
    legacy = project / ".gemini" / "rules"
    legacy.mkdir(parents=True, exist_ok=True)
    (legacy / "branch-guard.md").write_text("# rule\n", encoding="utf-8")
    (legacy / "own-rule.md").write_text("# mine\n", encoding="utf-8")
    (legacy / ".agent-meta-managed").write_text("branch-guard.md\n", encoding="utf-8")
    result = _sync(project)
    assert result.returncode == 0, result.stdout[-1500:] + result.stderr[-1500:]
    assert sorted(p.name for p in legacy.iterdir()) == ["own-rule.md"]
