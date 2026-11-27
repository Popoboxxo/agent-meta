"""REQ-07 (AC-7.1/7.2): commands gate is consistent across both provider configs.

Config-driven: no provider names. ``has_commands`` (ai-providers.yaml) must
match ``commands`` (provider-capabilities.yaml); supporting providers need a
valid ``commands_dir`` and a ``commands_format`` known to
COMMAND_FORMAT_TRANSFORMS.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from scripts.lib.commands import COMMAND_FORMAT_TRANSFORMS
from scripts.lib.providers import (
    load_provider_capabilities,
    load_providers_config,
    provider_commands_supported,
)

ROOT = Path(__file__).resolve().parent.parent


@pytest.fixture(scope="module")
def providers() -> dict:
    return load_providers_config(ROOT)


@pytest.fixture(scope="module")
def capabilities() -> dict:
    return load_provider_capabilities(ROOT)


def _supporting(providers: dict) -> list[str]:
    return sorted(
        name for name, cfg in providers.items() if cfg.get("has_commands")
    )


def _supporting_at_collection() -> list[str]:
    return _supporting(load_providers_config(ROOT))


def test_provider_sets_match(providers: dict, capabilities: dict) -> None:
    assert set(providers) == set(capabilities)


def test_supporting_provider_list_not_empty(providers: dict) -> None:
    assert _supporting(providers), "no provider declares has_commands"


def test_has_commands_matches_capability_all(
    providers: dict, capabilities: dict
) -> None:
    for provider, cfg in providers.items():
        has = cfg.get("has_commands")
        cap = (capabilities.get(provider) or {}).get("commands")
        assert isinstance(has, bool), (
            f"{provider}: has_commands={has!r} is not a bool"
        )
        assert isinstance(cap, bool), (
            f"{provider}: commands={cap!r} is not a bool"
        )
        supported = provider_commands_supported(capabilities[provider])
        assert has == supported, (
            f"{provider}: has_commands={has!r} != commands={supported!r}"
        )


@pytest.mark.parametrize("provider", _supporting_at_collection())
def test_supporting_provider_has_valid_dir_and_format(
    provider: str, providers: dict
) -> None:
    cfg = providers[provider]
    commands_dir = cfg.get("commands_dir")
    assert isinstance(commands_dir, str) and commands_dir.strip(), (
        f"{provider}: commands_dir={commands_dir!r} is not a non-empty str"
    )
    path = Path(commands_dir)
    assert not path.is_absolute(), (
        f"{provider}: commands_dir={commands_dir!r} is absolute"
    )
    assert ".." not in path.parts, (
        f"{provider}: commands_dir={commands_dir!r} contains '..'"
    )
    fmt = cfg.get("commands_format")
    assert fmt in COMMAND_FORMAT_TRANSFORMS, (
        f"{provider}: commands_format={fmt!r} not in "
        f"{sorted(COMMAND_FORMAT_TRANSFORMS)}"
    )
