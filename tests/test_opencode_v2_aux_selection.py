"""Tests for ``surface-version`` → auxiliary surface values (``cli_file``, ``model-pattern``).

SPEC-OPENCODE-V2-SUPPORT-2026-10-22, plan Task 6 (B.3; AC-B12 resolution,
AC-D7 resolution, AC-T6). ``surface-version`` is *config data* that SELECTS
auxiliary surface values through generic per-surface maps on the registry
entry, applied once in ``load_providers_config`` by
``providers._apply_surface_aux_selection``:

  - ``cli-files: {<surface>: <filename>}``      → flat ``cli_file``
  - ``agent-transform.surface-model-patterns: {<surface>: <regex>}``
                                                → ``agent-transform.model-pattern``

Contract (mirrors ``_apply_surface_format_selection``):

  - the lookup is by VALUE (the ``surface-version`` string as a map key) — no
    provider-name literal, no ``if surface == "v2"`` branch;
  - a provider without the map, without the block, or with a ``surface-version``
    that is not a map key keeps its statically declared value byte-for-byte
    (fail-safe, never raises);
  - the writers still dispatch on the resolved values only and never read
    ``surface-version``.

The C3 keys (``surface-plugin-protocols``/``surface-has-plugins``) are Task 18
and are deliberately NOT part of this module's contract.

Run: python3 -m pytest tests/test_opencode_v2_aux_selection.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.providers import load_providers_config  # noqa: E402

_SURFACE_FORMATS = {"v1": "opencode-json", "v2": "opencode-json-v2"}
_SURFACE_MECHANISMS = {"v1": "opencode-native", "v2": "opencode-native-v2"}
_SURFACE_CLI_FILES = {"v2": "cli.json"}
_SURFACE_MODEL_PATTERNS = {"v2": r"^[^/#\s]+/[^#\s]+(#[A-Za-z0-9._-]+)?$"}


def _write_config(root: Path, providers: dict) -> None:
    """Write a minimal ``config/ai-providers.yaml`` fixture under ``root``."""
    cfg_dir = root / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "ai-providers.yaml").write_text(
        yaml.safe_dump({"providers": providers}, sort_keys=False),
        encoding="utf-8",
    )


def _surface_provider(
    surface: str,
    *,
    cli_files: dict | None = _SURFACE_CLI_FILES,
    model_patterns: dict | None = _SURFACE_MODEL_PATTERNS,
    static: dict | None = None,
) -> dict:
    """A provider entry declaring the auxiliary surface maps for *surface*.

    *static* adds extra keys verbatim (used to prove the fail-safe path keeps
    statically declared ``cli_file`` / ``model-pattern`` values).
    """
    transform: dict = {
        "frontmatter-mechanism": "opencode-native",
        "surface-mechanisms": dict(_SURFACE_MECHANISMS),
    }
    if model_patterns is not None:
        transform["surface-model-patterns"] = dict(model_patterns)
    entry: dict = {
        "surface-version": surface,
        "mcp-config": {
            "committed-file": "opencode.json",
            "format": "opencode-json",
            "surface-formats": dict(_SURFACE_FORMATS),
        },
        "agent-transform": transform,
    }
    if cli_files is not None:
        entry["cli-files"] = dict(cli_files)
    if static:
        for key, value in static.items():
            if key == "model-pattern":
                entry["agent-transform"]["model-pattern"] = value
            else:
                entry[key] = value
    return entry


# --- selection semantics ---------------------------------------------------


def test_v2_resolves_cli_file_and_model_pattern(tmp_path):
    """AC-B12/AC-D7: a v2 surface resolves both auxiliary values from the maps."""
    _write_config(tmp_path, {"Opencode": _surface_provider("v2")})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert cfg["cli_file"] == "cli.json"
    assert cfg["agent-transform"]["model-pattern"] == _SURFACE_MODEL_PATTERNS["v2"]


def test_v1_resolves_neither(tmp_path):
    """The v1 surface is not a key of either map → neither value is injected."""
    _write_config(tmp_path, {"Opencode": _surface_provider("v1")})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert "cli_file" not in cfg
    assert "model-pattern" not in cfg["agent-transform"]


def test_missing_surface_key_keeps_static_value(tmp_path):
    """Fail-safe: an unknown surface key keeps the statically declared values.

    Both shapes are covered — a declared static ``cli_file``/``model-pattern``
    (kept byte-for-byte) and a provider without the maps at all (nothing is
    invented, no raise).
    """
    _write_config(
        tmp_path,
        {
            "Unknown": _surface_provider(
                "v9",
                static={"cli_file": "legacy.json", "model-pattern": "^static$"},
            ),
            "NoMaps": {
                "surface-version": "v2",
                "mcp-config": {"committed-file": "opencode.json", "format": "opencode-json"},
                "agent-transform": {"frontmatter-mechanism": "opencode-native"},
            },
        },
    )
    cfg = load_providers_config(tmp_path)
    assert cfg["Unknown"]["cli_file"] == "legacy.json"
    assert cfg["Unknown"]["agent-transform"]["model-pattern"] == "^static$"
    assert "cli_file" not in cfg["NoMaps"]
    assert "model-pattern" not in cfg["NoMaps"]["agent-transform"]


def test_resolution_is_provider_name_agnostic(tmp_path):
    """A provider name that is not registered resolves identically.

    Proves the resolver keys off the declared data (map + version value),
    never off the literal ``"Opencode"`` name.
    """
    _write_config(
        tmp_path,
        {
            "FutureProvider": _surface_provider("v2"),
            "AnotherFutureProvider": _surface_provider("v1"),
        },
    )
    cfg = load_providers_config(tmp_path)
    assert cfg["FutureProvider"]["cli_file"] == "cli.json"
    assert (
        cfg["FutureProvider"]["agent-transform"]["model-pattern"]
        == _SURFACE_MODEL_PATTERNS["v2"]
    )
    assert "cli_file" not in cfg["AnotherFutureProvider"]
    assert "model-pattern" not in cfg["AnotherFutureProvider"]["agent-transform"]


# --- shipped registry ------------------------------------------------------


def test_real_registry_opencode_v1_default_has_no_cli_file():
    """The committed v1 default stays byte-frozen: no ``cli_file`` is injected.

    Non-vacuity anchor: the registry really declares both maps, so the absence
    on v1 is a *selection* result (v1 is not a key of either map), not a
    missing declaration.
    """
    cfg = load_providers_config(_REPO_ROOT)["Opencode"]
    assert cfg["surface-version"] == "v1"
    assert cfg["cli-files"] == _SURFACE_CLI_FILES
    assert cfg["agent-transform"]["surface-model-patterns"] == _SURFACE_MODEL_PATTERNS
    assert "cli_file" not in cfg
    assert "model-pattern" not in cfg["agent-transform"]


@pytest.mark.parametrize("surface", ["v1", "v2"])
def test_resolved_entry_keeps_surface_formats_and_committed_file(tmp_path, surface):
    """AC-T6: the resolved entry keeps the data ``owns_opencode_surface`` needs.

    ``mcp-config.surface-formats`` (non-empty dict containing a v2 format value)
    and ``mcp-config.committed-file`` must survive the auxiliary resolution —
    for both surfaces.
    """
    _write_config(tmp_path, {"Opencode": _surface_provider(surface)})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert cfg["mcp-config"]["surface-formats"] == _SURFACE_FORMATS
    assert cfg["mcp-config"]["committed-file"] == "opencode.json"
    assert cfg["mcp-config"]["format"] == _SURFACE_FORMATS[surface]
    # And the auxiliary values still follow the same surface selection.
    if surface == "v2":
        assert cfg["cli_file"] == "cli.json"
        assert cfg["agent-transform"]["model-pattern"] == _SURFACE_MODEL_PATTERNS["v2"]
    else:
        assert "cli_file" not in cfg
        assert "model-pattern" not in cfg["agent-transform"]
