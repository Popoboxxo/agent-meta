"""Resolver tests for the provider-agnostic frontmatter strip policy.

SPEC-REFERENCE-STANDARDS-2026-09-15 (IC-03), AC-03/AC-04/AC-05/AC-06:

- The global default strips `reference_standards` for every registered provider.
- The project (`provider-options.<P>.*`) and ai-providers (`providers.<P>.*`)
  channels are combined as a union (F-02), not an override.
- `keep` wins over `strip`.
- Malformed values are fail-safe (strip stays active), warn at most once per
  (provider, key) and never raise.

Task 5 extends this module with the provider-parametrised strip/provenance
pins; Task 2 owns the resolver matrix only.

Run: python -m pytest tests/test_reference_standards_strip.py -v
"""
from __future__ import annotations

import logging
from pathlib import Path

import pytest

from scripts.lib.frontmatter import REFERENCE_STANDARDS_FIELD, parse_frontmatter_text
from scripts.lib.log import SyncLog
from scripts.lib.provider_transform import transform_agent_content_for_provider
from scripts.lib.providers import (
    FRONTMATTER_STRIP_DEFAULTS,
    load_providers_config,
    registered_provider_names,
    resolve_frontmatter_strip_fields,
)

try:
    import tomllib
except ModuleNotFoundError:  # Python 3.9/3.10
    tomllib = pytest.importorskip("tomli")

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _registered_providers() -> list[str]:
    return registered_provider_names(_REPO_ROOT)


def _provider_config() -> dict:
    return load_providers_config(_REPO_ROOT)


def _mechanism(provider: str, provider_config: dict) -> str | None:
    spec = (provider_config.get(provider) or {}).get("agent-transform") or {}
    return spec.get("frontmatter-mechanism")


_PC = _provider_config()
_MECHANISM_BY_PROVIDER = {p: _mechanism(p, _PC) for p in _registered_providers()}
_MECHANISM_PROVIDERS = [p for p, m in _MECHANISM_BY_PROVIDER.items() if m]
_NO_MECHANISM_PROVIDERS = [p for p, m in _MECHANISM_BY_PROVIDER.items() if not m]


def _content(*, with_reference_standards: bool = True) -> str:
    rs = (
        "reference_standards:\n"
        '  - "arc42"\n'
        '  - "C4 model"\n'
        if with_reference_standards
        else ""
    )
    return (
        "---\n"
        "name: template-code-reviewer\n"
        'version: "1.2.2"\n'
        "description: old description\n"
        "prompt_mode: modern\n"
        + rs
        + "tools:\n"
        "  - Read\n"
        "---\n"
        "\n"
        "Body content.\n"
    )


def _render(provider, tmp_path, content=None, *, config=None, provider_config=None) -> str:
    return transform_agent_content_for_provider(
        content if content is not None else _content(),
        provider, "code-reviewer", "code-reviewer", "new description",
        "1-generic/code-reviewer.md@1.2.2",
        config if config is not None else {},
        _REPO_ROOT, tmp_path, tmp_path / "agent.out", 
        provider_config if provider_config is not None else _PC,
        SyncLog(),
    )


def test_strip_defaults_contain_reference_standards():
    assert FRONTMATTER_STRIP_DEFAULTS == (REFERENCE_STANDARDS_FIELD,)


@pytest.mark.parametrize("provider", _registered_providers())
def test_resolver_default_contains_field_for_all_registered_providers(provider):
    # AC-03: identical provider-agnostic default for every registered provider.
    result = resolve_frontmatter_strip_fields(provider, {}, {})
    assert REFERENCE_STANDARDS_FIELD in result


def test_resolver_union_of_project_and_ai_providers_channels():
    # AC-05 / F-02: both channels contribute (union), defaults stay in front.
    config = {
        "provider-options": {
            "Claude": {"frontmatter-strip-fields": ["version"]},
        },
    }
    provider_config = {"Claude": {"frontmatter_strip_fields": ["prompt_mode"]}}
    result = resolve_frontmatter_strip_fields("Claude", config, provider_config)
    assert result == [REFERENCE_STANDARDS_FIELD, "version", "prompt_mode"]


def test_resolver_keep_wins_over_strip():
    # AC-04 (resolver side): keep wins via the project channel ...
    project_keep = {
        "provider-options": {
            "Claude": {"frontmatter-keep-fields": [REFERENCE_STANDARDS_FIELD]},
        },
    }
    assert REFERENCE_STANDARDS_FIELD not in resolve_frontmatter_strip_fields(
        "Claude", project_keep, {}
    )
    # ... and identically via the ai-providers channel.
    provider_keep = {
        "Claude": {"frontmatter_keep_fields": [REFERENCE_STANDARDS_FIELD]},
    }
    assert REFERENCE_STANDARDS_FIELD not in resolve_frontmatter_strip_fields(
        "Claude", {}, provider_keep
    )
    # Contradictory channels: keep wins over an explicit strip entry.
    conflicting = {
        "provider-options": {
            "Claude": {"frontmatter-strip-fields": [REFERENCE_STANDARDS_FIELD]},
        },
    }
    assert REFERENCE_STANDARDS_FIELD not in resolve_frontmatter_strip_fields(
        "Claude", conflicting, provider_keep
    )
    # Other providers keep the default strip.
    assert REFERENCE_STANDARDS_FIELD in resolve_frontmatter_strip_fields(
        "Gemini", conflicting, provider_keep
    )


def test_resolver_malformed_values_fail_safe_and_warn_once(caplog):
    caplog.set_level(logging.WARNING)
    # AC-06: a string strip value, a null strip value and a non-list keep value
    # are all ignored; the default strip stays active, no exception is raised.
    config = {
        "provider-options": {
            "Claude": {"frontmatter-strip-fields": "version"},
        },
    }
    provider_config = {
        "Claude": {
            "frontmatter_strip_fields": None,
            "frontmatter_keep_fields": {"version": True},
        },
    }
    result = resolve_frontmatter_strip_fields("Claude", config, provider_config)
    assert REFERENCE_STANDARDS_FIELD in result
    assert "version" not in result

    # Exactly one warning per malformed channel key (the null strip value is
    # treated as absent and adds none), and a second call is deduplicated.
    messages = [r.getMessage() for r in caplog.records if r.levelno == logging.WARNING]
    assert len(messages) == 2, messages
    assert any("frontmatter-strip-fields" in m for m in messages)
    assert any("frontmatter_keep_fields" in m for m in messages)
    caplog.clear()
    resolve_frontmatter_strip_fields("Claude", config, provider_config)
    assert not [r for r in caplog.records if r.levelno == logging.WARNING]

    # Non-dict provider entries and unknown providers never raise and keep the
    # default strip.
    assert REFERENCE_STANDARDS_FIELD in resolve_frontmatter_strip_fields(
        "Claude", {"provider-options": {"Claude": "broken"}}, {"Claude": 7}
    )
    assert REFERENCE_STANDARDS_FIELD in resolve_frontmatter_strip_fields(
        "NotARegisteredProvider", {}, {}
    )
    assert REFERENCE_STANDARDS_FIELD in resolve_frontmatter_strip_fields(
        "Claude", {"provider-options": None}, None
    )


# --- Task 5: provider-matrix regression pins -------------------------------

def test_mechanism_partition_matches_the_documented_8_9_matrix():
    """AC-01/AC-02 context (F-01): exactly two providers use a
    `frontmatter-mechanism`; the other seven patch the frontmatter. The
    mechanism comes from config, not from a provider-name branch."""
    assert len(_MECHANISM_PROVIDERS) == 2, _MECHANISM_PROVIDERS
    assert len(_NO_MECHANISM_PROVIDERS) == 7, _NO_MECHANISM_PROVIDERS
    assert set(_MECHANISM_BY_PROVIDER.values()) - {None} == {"opencode-native", "codex-toml"}


@pytest.mark.parametrize("provider", _NO_MECHANISM_PROVIDERS)
def test_patch_providers_drop_reference_standards_token(provider, tmp_path):
    """AC-01: every provider without a `frontmatter-mechanism` (patch surface)
    drops the field — no YAML key and no provenance token."""
    out = _render(provider, tmp_path)
    assert REFERENCE_STANDARDS_FIELD not in out
    fm = parse_frontmatter_text(out)
    assert REFERENCE_STANDARDS_FIELD not in fm


@pytest.mark.parametrize("provider", _MECHANISM_PROVIDERS)
def test_mechanism_providers_drop_reference_standards_token(provider, tmp_path):
    """AC-02: `opencode-native` parses as YAML without the key; `codex-toml`
    parses with tomllib and carries only the whitelist fields (version /
    generated-from stay header comments)."""
    out = _render(provider, tmp_path)
    assert REFERENCE_STANDARDS_FIELD not in out
    mechanism = _MECHANISM_BY_PROVIDER[provider]

    if mechanism == "opencode-native":
        fm = parse_frontmatter_text(out)
        assert REFERENCE_STANDARDS_FIELD not in fm
        assert fm.get("name") == "code-reviewer"
        return

    assert mechanism == "codex-toml"
    doc = tomllib.loads(out)
    extra = set((( _PC.get(provider) or {}).get("agent-transform") or {}).get("extra-fields") or {})
    allowed = {"name", "description", "model", "developer_instructions"} | extra
    assert set(doc) <= allowed, set(doc) - allowed
    assert doc.get("name") == "code-reviewer"
    assert "description" in doc
    assert "developer_instructions" in doc
    for bookkeeping in ("version", "generated-from", "generated_from", REFERENCE_STANDARDS_FIELD):
        assert bookkeeping not in doc
    assert "# generated-from: 1-generic/code-reviewer.md@1.2.2" in out
    assert "# version: 1.2.2" in out


@pytest.mark.parametrize("provider", _registered_providers())
def test_templates_differing_only_in_reference_standards_are_byte_identical(provider, tmp_path):
    """AC-08: default-strip makes the field invisible for every provider."""
    with_rs = _render(provider, tmp_path, _content(with_reference_standards=True))
    without_rs = _render(provider, tmp_path, _content(with_reference_standards=False))
    assert with_rs == without_rs
