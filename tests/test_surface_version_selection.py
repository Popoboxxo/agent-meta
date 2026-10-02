"""Tests for ``surface-version`` → ``mcp-config.format`` selection.

SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30, Task-4 addendum (design §3.1,
§3.4, DECISION-7; acceptance AC-5 / scenario 69):

``surface-version`` is *config data* that SELECTS the declared
``mcp-config.format`` through a generic ``mcp-config.surface-formats`` map
(``v1`` → ``opencode-json``, ``v2`` → ``opencode-json-v2``). The selection is
applied once, generically, in ``load_providers_config``:

  - a provider that declares ``mcp-config.surface-formats`` AND whose
    ``surface-version`` is a key of that map gets the mapped format;
  - a provider without the map, or with an unknown ``surface-version``, keeps
    its statically declared ``mcp-config.format`` byte-for-byte;
  - no branch reads a provider name.

The writer (``mcp_provider_config._write_provider_config``) keeps dispatching
on the resolved ``mcp-config.format`` value ONLY and never reads
``surface-version``.

Run: python3 -m pytest tests/test_surface_version_selection.py -q
"""

from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.providers import load_providers_config  # noqa: E402

_SURFACE_FORMATS = {"v1": "opencode-json", "v2": "opencode-json-v2"}


def _write_config(root: Path, providers: dict) -> None:
    """Write a minimal ``config/ai-providers.yaml`` fixture under ``root``."""
    cfg_dir = root / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "ai-providers.yaml").write_text(
        yaml.safe_dump({"providers": providers}, sort_keys=False),
        encoding="utf-8",
    )


def _opencode_like(surface: str, formats: dict | None = _SURFACE_FORMATS) -> dict:
    mcp: dict = {"committed-file": "opencode.json", "format": "opencode-json"}
    if formats is not None:
        mcp["surface-formats"] = dict(formats)
    return {"surface-version": surface, "mcp-config": mcp}


# --- real registry: v1 default stays the flat byte shape -------------------


def test_real_registry_opencode_v1_keeps_flat_format():
    """AC-5: the committed v1 default resolves to the flat ``opencode-json``."""
    cfg = load_providers_config(_REPO_ROOT)["Opencode"]
    assert cfg["surface-version"] == "v1"
    assert cfg["mcp-config"]["format"] == "opencode-json"


def test_real_registry_declares_surface_formats_map():
    """The selection data exists on the Opencode entry (v1 fallback kept)."""
    cfg = load_providers_config(_REPO_ROOT)["Opencode"]
    assert cfg["mcp-config"]["surface-formats"] == _SURFACE_FORMATS


# --- selection semantics ---------------------------------------------------


def test_v1_selects_opencode_json(tmp_path):
    _write_config(tmp_path, {"Opencode": _opencode_like("v1")})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert cfg["mcp-config"]["format"] == "opencode-json"


def test_v2_selects_opencode_json_v2(tmp_path):
    _write_config(tmp_path, {"Opencode": _opencode_like("v2")})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert cfg["mcp-config"]["format"] == "opencode-json-v2"


def test_absent_map_leaves_declared_format_unchanged(tmp_path):
    """A provider without ``surface-formats`` is untouched — even on v2."""
    _write_config(
        tmp_path,
        {"Other": {"surface-version": "v2", "mcp-config": {"format": "kimi-json"}}},
    )
    cfg = load_providers_config(tmp_path)["Other"]
    assert cfg["mcp-config"]["format"] == "kimi-json"


def test_unknown_surface_version_keeps_declared_fallback(tmp_path):
    """An unknown ``surface-version`` is not a key of the map → unchanged."""
    _write_config(tmp_path, {"Opencode": _opencode_like("v3")})
    cfg = load_providers_config(tmp_path)["Opencode"]
    assert cfg["mcp-config"]["format"] == "opencode-json"


def test_selection_is_provider_name_agnostic(tmp_path):
    """A provider name that is not a registered provider still selects.

    Proves the normalizer keys off the declared data (map + version value),
    never off the literal ``"Opencode"`` name.
    """
    _write_config(
        tmp_path,
        {
            "FutureProvider": {
                "surface-version": "v2",
                "mcp-config": {"format": "placeholder", "surface-formats": _SURFACE_FORMATS},
            }
        },
    )
    cfg = load_providers_config(tmp_path)["FutureProvider"]
    assert cfg["mcp-config"]["format"] == "opencode-json-v2"


def test_other_providers_in_same_registry_are_untouched(tmp_path):
    """Normalization is per entry: a mapped provider never affects neighbours."""
    _write_config(
        tmp_path,
        {
            "Mapped": _opencode_like("v2"),
            "Plain": {"surface-version": "v2", "mcp-config": {"format": "codex-toml-mcp"}},
        },
    )
    cfg = load_providers_config(tmp_path)
    assert cfg["Mapped"]["mcp-config"]["format"] == "opencode-json-v2"
    assert cfg["Plain"]["mcp-config"]["format"] == "codex-toml-mcp"


# --- no provider-name branch ----------------------------------------------


def test_normalizer_source_has_no_provider_name_literal():
    """The normalizer must not mention any registered provider name."""
    registered = set(load_providers_config(_REPO_ROOT).keys())
    source = inspect.getsource(load_providers_config)
    # The loader delegates, so include the module-level helper it calls too.
    helper = _find_called_helper(source)
    assert helper is not None, "load_providers_config must delegate the selection"
    offenders = [
        name
        for name in registered
        if f'"{name}"' in helper or f"'{name}'" in helper
    ]
    assert not offenders, (
        f"surface-version selection references provider name(s) {offenders}; "
        "dispatch must stay data-driven"
    )


def _find_called_helper(loader_source: str) -> str | None:
    """Return the source of the first module-level helper called by the loader.

    The helper that performs the selection is the one that reads the
    ``surface-formats`` key, so pick by that marker instead of by name.
    """
    module = sys.modules[load_providers_config.__module__]
    for name, fn in vars(module).items():
        if not inspect.isfunction(fn) or fn.__module__ != module.__name__:
            continue
        if fn is load_providers_config or not name.startswith("_"):
            continue
        if "surface-formats" in inspect.getsource(fn):
            return inspect.getsource(fn)
    return None


def test_helper_is_a_single_generic_pass():
    """Guard: the selection helper iterates values, not provider names."""
    module = sys.modules[load_providers_config.__module__]
    helper = None
    for name, fn in vars(module).items():
        if inspect.isfunction(fn) and "surface-formats" in inspect.getsource(fn):
            if fn is load_providers_config:
                continue
            helper = fn
            break
    assert helper is not None, "no surface-format selection helper found"
    tree = ast.parse(inspect.getsource(helper))
    # No string constant may be compared with ==/!= to select behaviour.
    for node in ast.walk(tree):
        if isinstance(node, ast.Compare):
            for op in node.ops:
                assert not isinstance(op, (ast.Eq, ast.NotEq)), (
                    "selection must be a mapping lookup, not an equality branch"
                )
