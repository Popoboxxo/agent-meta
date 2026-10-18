"""Tests for the shared-file context-profile downgrade (2a.6, IC-02/AC-30).

A physical ``AGENTS.md`` shared by several active providers must render one
profile for the whole file. One ``full`` sharer forces ``full`` (ADR-5); a
requested ``compact`` is downgraded with a single WARN
``context-profile.shared-file-downgrade`` per file. A ``provider-overrides.<P>``
entry still only takes effect while P is the sole active sharer.
"""
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.log import SyncLog  # noqa: E402

_AGENTS_MD_SHARERS = ("Opencode", "Gemini", "Codex", "ZCode", "KimiCode", "Mammouth")


@pytest.fixture
def loaded_config():
    from lib.config import load_config
    from lib.providers import load_providers_config

    config = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    provider_config = load_providers_config(REPO_ROOT)
    return config, provider_config


def _config(config, *, active=None):
    config = dict(config)
    selected = list(active) if active is not None else list(_AGENTS_MD_SHARERS)
    config["ai-providers"] = selected
    return config


@pytest.fixture
def captured(monkeypatch):
    """Capture the ``local_vars`` the managed block is built with."""
    import lib.context as context

    captured = {}
    real = context.TemplateBuilder

    class _Recorder:
        def __init__(self, root):
            self._root = root

        def build(self, name, local_vars):
            captured[name] = dict(local_vars)
            return real(self._root).build(name, local_vars)

    monkeypatch.setattr(context, "TemplateBuilder", _Recorder)
    return captured


def _render(config, provider_config, provider, captured, log):
    from lib.context import _build_managed_block

    _build_managed_block(
        REPO_ROOT, config, dict(config.get("variables", {})), log,
        provider=provider, provider_config=provider_config, project_root=REPO_ROOT,
    )
    return captured["agents-managed"]


def test_provider_override_compact_on_shared_file_downgrades(loaded_config, captured):
    config, provider_config = loaded_config
    config = _config(config)
    config["provider-overrides"] = {"Opencode": {"context-profile": "compact"}}

    log = SyncLog()
    for provider in ("Opencode", "Gemini"):
        local_vars = _render(config, provider_config, provider, captured, log)

    assert local_vars["CONTEXT_PROFILE"] == "full"
    assert local_vars["CONTEXT_PROFILE_COMPACT"] == "false"
    downgrades = [w for w in log.warnings if "context-profile.shared-file-downgrade" in w]
    assert len(downgrades) == 1, downgrades
    assert "AGENTS.md" in downgrades[0]
    assert "Opencode" in downgrades[0]


def test_one_full_sharer_forces_downgrade(loaded_config, captured):
    config, provider_config = loaded_config
    config = _config(config)
    config["context-profile"] = "compact"
    config["provider-overrides"] = {"Opencode": {"context-profile": "full"}}

    log = SyncLog()
    local_vars = _render(config, provider_config, "Gemini", captured, log)

    assert local_vars["CONTEXT_PROFILE"] == "full"
    assert local_vars["CONTEXT_PROFILE_COMPACT"] == "false"
    assert len([w for w in log.warnings
                if "context-profile.shared-file-downgrade" in w]) == 1


def test_all_sharers_compact_renders_compact_without_warning(loaded_config, captured):
    config, provider_config = loaded_config
    config = _config(config)
    config["context-profile"] = "compact"

    log = SyncLog()
    local_vars = _render(config, provider_config, "Gemini", captured, log)

    assert local_vars["CONTEXT_PROFILE"] == "compact"
    assert local_vars["CONTEXT_PROFILE_COMPACT"] == "true"
    assert not [w for w in log.warnings
                if "context-profile.shared-file-downgrade" in w]


def test_override_compact_with_sole_active_sharer_keeps_compact(loaded_config, captured):
    config, provider_config = loaded_config
    config = _config(config, active=["Opencode"])
    config["provider-overrides"] = {"Opencode": {"context-profile": "compact"}}

    log = SyncLog()
    local_vars = _render(config, provider_config, "Opencode", captured, log)

    assert local_vars["CONTEXT_PROFILE"] == "compact"
    assert local_vars["CONTEXT_PROFILE_COMPACT"] == "true"
    assert not [w for w in log.warnings
                if "context-profile.shared-file-downgrade" in w]
