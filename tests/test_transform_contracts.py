"""Task 6 — transform format contracts (AC-6, AC-13, AC-12/D3, OQ-6, OQ-4).

The transform layer consumes the Task-4 config keys and is dispatched purely on
declared config **values** — there is no ``if provider == "…"`` branch:

* ``tools-format: map`` emits ``tools:`` as a YAML object, never a list
  (AC-6, Mammouth). ``keep``/``filter``/``skip``/``remove`` keep their declared
  semantics.
* ``tool-name-map`` translates Claude tool names to a provider vocabulary
  (Antigravity G-2); an unknown source name passes through unchanged.
* ``allowed-fields`` / ``reject-fields`` feed the Task-1 validators, so a
  transform output that violates the contract yields ``Finding``s (AC-13).
* ``frontmatter-mechanism: opencode-native-v2`` emits the ``primary-role``
  entry as ``mode: primary`` (from the ``primary-role`` data key, OQ-4).
* ``model-literal: inherit`` emits the literal verbatim with no injected tier
  ID (OQ-6).
* the ``model-inherit-fallback`` (``provider_transform.py:290-296``) resolves a
  known tier/role-default through the provider's ``model-tiers`` and applies
  ``model-format`` exactly once; an unresolvable fallback emits **no**
  ``model:`` field — it never leaks a raw tier token (AC-12/D3).

Run: python3 -m pytest tests/test_transform_contracts.py -q
"""
from __future__ import annotations

import copy
from pathlib import Path

import pytest
import yaml

from scripts.lib.artifact_validate import (
    resolve_artifact_contract,
    validate_artifact,
)
from scripts.lib.consistency.report import Severity
from scripts.lib.log import SyncLog
from scripts.lib.provider_transform import transform_agent_content_for_provider
from scripts.lib.providers import load_providers_config

REPO_ROOT = Path(__file__).resolve().parents[1]

_PROVIDER_CONFIG = load_providers_config(REPO_ROOT)


def _sample_agent_content() -> str:
    """Template-shaped content: tools list + a Claude-only extension line."""
    return (
        "---\n"
        "name: template-orchestrator\n"
        'version: "0.101.0"\n'
        "description: old description\n"
        "prompt_mode: modern\n"
        "tools:\n"
        "  - Read\n"
        "  - Bash\n"
        "  - Grep\n"
        "  - Write\n"
        "memory: project\n"
        "temperature: 0.3\n"
        "---\n"
        "\n"
        "Koordiniert alle Entwicklungsaufgaben.\n"
        "> **Extension:** Falls `.claude/3-project/orchestrator-ext.md` existiert, lesen.\n"
        "Body-Ende.\n"
    )


def _transform(
    provider: str,
    role: str = "orchestrator",
    content: str | None = None,
    project_config: dict | None = None,
    provider_config: dict | None = None,
) -> tuple[str, SyncLog]:
    """Run the full provider transform against the real config (or a copy)."""
    config = provider_config if provider_config is not None else _PROVIDER_CONFIG
    log = SyncLog()
    ext = config[provider].get("agent_ext", ".md")
    out = transform_agent_content_for_provider(
        content or _sample_agent_content(),
        provider,
        role,
        role,
        "desc",
        "1-generic/orchestrator.md@0.101.0",
        project_config or {},
        REPO_ROOT,
        REPO_ROOT,
        REPO_ROOT / config[provider]["agents_dir"] / f"{role}{ext}",
        config,
        log,
    )
    return out, log


def _frontmatter(text: str) -> dict:
    """Parse the leading YAML frontmatter block into a dict."""
    block = text.split("---", 2)[1]
    parsed = yaml.safe_load(block)
    assert isinstance(parsed, dict)
    return parsed


def _errors(findings: list) -> list:
    return [f for f in findings if f.severity == Severity.ERROR]


# ---------------------------------------------------------------------------
# AC-6 — tools-format: map (Mammouth)
# ---------------------------------------------------------------------------


def test_mammouth_tools_are_a_yaml_object_not_a_list() -> None:
    """AC-6: a Mammouth ``tools:`` list aborts loading the whole directory, so
    ``tools-format: map`` must emit ``{<name>: true}``."""
    out, _ = _transform("Mammouth")
    tools = _frontmatter(out)["tools"]

    assert isinstance(tools, dict), f"tools must be an object, got {type(tools)!r}"
    assert tools == {"Read": True, "Bash": True, "Grep": True, "Write": True}
    assert not isinstance(tools, list)


def test_tools_format_map_is_data_driven_not_mammouth_specific() -> None:
    """The object form follows from the config value, not the provider name.

    A synthetic provider that declares ``tools-format: map`` gets the same
    shape; the config value is the only selector.
    """
    config = copy.deepcopy(_PROVIDER_CONFIG)
    config["ZCode"]["agent-transform"]["tools-format"] = "map"
    out, _ = _transform("ZCode", provider_config=config)
    assert isinstance(_frontmatter(out)["tools"], dict)


def test_tools_format_filter_replaces_list_with_validated_subset() -> None:
    """Gemini keeps ``tools-format: filter``: the list survives, filtered."""
    out, _ = _transform("Gemini")
    tools = _frontmatter(out)["tools"]
    assert isinstance(tools, list)


def test_tools_format_remove_drops_the_field() -> None:
    """Continue declares ``tools-format: remove``: the field disappears."""
    out, _ = _transform("Continue")
    assert "tools" not in _frontmatter(out)


def test_tools_format_keep_preserves_the_list() -> None:
    """An explicit ``tools-format: keep`` fixture preserves the raw list."""
    config = copy.deepcopy(_PROVIDER_CONFIG)
    config["ZCode"]["agent-transform"]["tools-format"] = "keep"
    out, _ = _transform("ZCode", provider_config=config)
    tools = _frontmatter(out)["tools"]
    assert isinstance(tools, list)
    assert "Read" in tools


def test_tools_format_keep_preserves_out_of_whitelist_tools() -> None:
    """BLOCKING regression: ``keep`` must never drop whitelist-filtered tools.

    With ``tools-format: keep`` the declared list survives verbatim — an
    out-of-whitelist token (``SendMessage``, absent from ZCode's whitelist)
    MUST remain; validation only warns. ``tool-name-map`` is still applied to
    the original list. This is the behaviour ``filter`` intentionally does not
    have (it replaces the list with the whitelisted subset).
    """
    config = copy.deepcopy(_PROVIDER_CONFIG)
    transform = config["ZCode"]["agent-transform"]
    transform["tools-format"] = "keep"
    transform["tool-name-map"] = {"Read": "read_file"}

    content = _sample_agent_content().replace("  - Write\n", "  - Write\n  - SendMessage\n")
    out, log = _transform("ZCode", content=content, provider_config=config)
    tools = _frontmatter(out)["tools"]

    assert isinstance(tools, list)
    assert "SendMessage" in tools, "an out-of-whitelist tool must survive keep"
    assert "read_file" in tools, "tool-name-map must still apply under keep"
    assert "Read" not in tools, "the mapped source token must be translated"
    assert "Write" in tools, "in-whitelist tokens are untouched"
    assert log.warnings, "keep must still validate and warn"


def test_tools_format_filter_drops_out_of_whitelist_tools() -> None:
    """Contrast fixture: ``filter`` replaces the list with the whitelist subset,
    so the same out-of-whitelist token must be dropped."""
    config = copy.deepcopy(_PROVIDER_CONFIG)
    config["ZCode"]["agent-transform"]["tools-format"] = "filter"

    content = _sample_agent_content().replace("  - Write\n", "  - Write\n  - SendMessage\n")
    out, _ = _transform("ZCode", content=content, provider_config=config)
    tools = _frontmatter(out)["tools"]

    assert "SendMessage" not in tools, "filter must drop out-of-whitelist tools"
    assert "Read" in tools


def test_tools_format_skip_leaves_tools_untouched() -> None:
    """Codex ``tools-format: skip`` + ``codex-toml`` leaves no frontmatter list
    and must not raise; the mechanism handles the body only."""
    out, _ = _transform("Codex")
    assert "developer_instructions" in out


# ---------------------------------------------------------------------------
# tool-name-map — Antigravity G-2 vocabulary is data
# ---------------------------------------------------------------------------


def test_tool_name_map_applies_antigravity_g2_vocabulary() -> None:
    """Antigravity maps ``Read``→``view_file`` etc. from ``tool-name-map``."""
    out, _ = _transform("Gemini")
    tools = _frontmatter(out)["tools"]

    assert isinstance(tools, list)
    assert "view_file" in tools
    assert "run_command" in tools
    assert "grep_search" in tools
    assert "replace_file_content" in tools
    for original in ("Read", "Bash", "Grep", "Write"):
        assert original not in tools, f"{original} must be translated by tool-name-map"


def test_tool_name_map_unknown_source_passes_through_unchanged() -> None:
    """An unmapped source name is emitted verbatim (vocabulary is partial)."""
    content = _sample_agent_content().replace("  - Write\n", "  - Write\n  - Glob\n")
    out, _ = _transform("Gemini", content=content)
    tools = _frontmatter(out)["tools"]
    assert "Glob" in tools, "an unmapped source tool must pass through unchanged"


def test_tool_name_map_is_data_driven() -> None:
    """A different provider declaring a map gets it applied — no name branch."""
    config = copy.deepcopy(_PROVIDER_CONFIG)
    config["ZCode"]["agent-transform"]["tool-name-map"] = {"Read": "read_file"}
    config["ZCode"]["agent-transform"]["tools-format"] = "filter"
    out, _ = _transform("ZCode", provider_config=config)
    tools = _frontmatter(out)["tools"]
    assert "read_file" in tools
    assert "Read" not in tools


# ---------------------------------------------------------------------------
# AC-13 — allowed-fields / reject-fields feed the Task-1 validators
# ---------------------------------------------------------------------------


def test_reject_fields_violation_yields_a_finding() -> None:
    """A transform output carrying a rejected field is flagged by the validator.

    ``allowed-fields``/``reject-fields`` are consumed by the Task-1 validator
    (``resolve_artifact_contract`` + ``validate_artifact``); the transform must
    hand it a document whose violation is observable as an ERROR Finding.
    """
    config = copy.deepcopy(_PROVIDER_CONFIG)
    config["Gemini"]["agent-transform"]["reject-fields"] = ["version"]

    out, _ = _transform("Gemini", provider_config=config)
    contract = resolve_artifact_contract(config["Gemini"])
    assert contract.reject_fields == {"version"}

    findings = validate_artifact(out, contract, ".gemini/agents/orchestrator.md")
    errors = _errors(findings)
    assert any("version" in f.message for f in errors), errors


def test_allowed_fields_violation_yields_a_finding_on_v2_surface() -> None:
    """AC-13: a key outside ``allowed-fields`` yields an ERROR on the v2 surface."""
    config = copy.deepcopy(_PROVIDER_CONFIG)
    transform = config["Opencode"]["agent-transform"]
    transform["frontmatter-mechanism"] = "opencode-native-v2"
    transform["allowed-fields"] = ["name", "description"]

    out, _ = _transform("Opencode", provider_config=config)
    contract = resolve_artifact_contract(config["Opencode"])
    assert contract.allowed_fields == {"name", "description"}

    findings = validate_artifact(out, contract, ".opencode/agents/orchestrator.md")
    errors = _errors(findings)
    assert errors, "a key outside the narrow allow-list must yield a finding"
    assert all(f.check == "artifact-contract" for f in errors)


def test_opencode_v2_emitted_frontmatter_passes_shipped_allow_list() -> None:
    """Task-18 regression guard: the real Opencode v2 output must validate clean.

    Both surfaces emit ``prompt_mode`` verbatim (Opencode declares no
    ``strip-fields``), and Opencode preserves unknown frontmatter keys in its
    ``options`` bucket rather than dropping them. The shipped
    ``agent-transform.allowed-fields`` must therefore contain every key the
    transform actually emits — a v2 project must pass ``--validate``.
    """
    config = copy.deepcopy(_PROVIDER_CONFIG)
    transform = config["Opencode"]["agent-transform"]
    transform["frontmatter-mechanism"] = "opencode-native-v2"

    out, _ = _transform("Opencode", provider_config=config)
    emitted = set(_frontmatter(out))
    # Only asserted on the shipped data: this reproduces the Task-18 defect.
    assert "prompt_mode" in emitted, "the Opencode transform emits prompt_mode"

    contract = resolve_artifact_contract(config["Opencode"])
    assert contract.allowed_fields is not None, "v2 surface enforces the allow-list"
    violations = sorted(emitted - contract.allowed_fields)
    assert not violations, f"emitted keys outside allowed-fields: {violations}"

    findings = validate_artifact(out, contract, ".opencode/agents/orchestrator.md")
    assert _errors(findings) == [], _errors(findings)


def test_reject_fields_contract_is_resolved_from_config() -> None:
    """The resolved contract mirrors the declared ``reject-fields`` value."""
    config = copy.deepcopy(_PROVIDER_CONFIG)
    config["Gemini"]["agent-transform"]["reject-fields"] = ["memory"]
    contract = resolve_artifact_contract(config["Gemini"])
    assert contract.reject_fields == {"memory"}


# ---------------------------------------------------------------------------
# OQ-4 — opencode-native-v2 emits the primary-role entry as mode: primary
# ---------------------------------------------------------------------------


def _opencode_v2_config(primary_role: str = "orchestrator") -> dict:
    config = copy.deepcopy(_PROVIDER_CONFIG)
    config["Opencode"]["surface-version"] = "v2"
    config["Opencode"]["agent-transform"]["frontmatter-mechanism"] = "opencode-native-v2"
    config["Opencode"]["primary-role"] = primary_role
    return config


def test_opencode_native_v2_emits_primary_role_mode_primary() -> None:
    """OQ-4: the ``primary-role`` agent is emitted as ``mode: primary``."""
    config = _opencode_v2_config()
    out, _ = _transform("Opencode", role="orchestrator", provider_config=config)
    fm = _frontmatter(out)
    assert fm["mode"] == "primary"


def test_opencode_native_v2_non_primary_roles_stay_subagent() -> None:
    """All other agents remain ``mode: subagent``."""
    config = _opencode_v2_config()
    out, _ = _transform("Opencode", role="developer", provider_config=config)
    fm = _frontmatter(out)
    assert fm["mode"] == "subagent"


def test_opencode_native_v2_primary_role_comes_from_data_key() -> None:
    """The primary role is the declared ``primary-role`` value, not a name."""
    config = _opencode_v2_config(primary_role="developer")
    out, _ = _transform("Opencode", role="developer", provider_config=config)
    assert _frontmatter(out)["mode"] == "primary"
    out, _ = _transform("Opencode", role="orchestrator", provider_config=config)
    assert _frontmatter(out)["mode"] == "subagent"


def test_opencode_native_v1_stays_subagent() -> None:
    """The v1 ``opencode-native`` mechanism is unchanged (no primary entry)."""
    out, _ = _transform("Opencode", role="orchestrator")
    assert _frontmatter(out)["mode"] == "subagent"


# ---------------------------------------------------------------------------
# OQ-6 — model-literal: inherit
# ---------------------------------------------------------------------------


def test_model_literal_inherit_is_emitted_verbatim() -> None:
    """OQ-6: Antigravity declares ``model-literal: inherit`` — the emitted
    ``model`` is the literal, never an injected tier ID."""
    mine = _PROVIDER_CONFIG["Gemini"].get("model-literal")
    assert mine == "inherit", "fixture sanity: Antigravity model-literal must be inherit"

    out, _ = _transform("Gemini")
    model = _frontmatter(out)["model"]
    assert model == "inherit"
    assert "gemini" not in str(model)


def test_model_literal_is_data_driven() -> None:
    """A different literal value is emitted verbatim for any provider."""
    config = copy.deepcopy(_PROVIDER_CONFIG)
    config["ZCode"]["model-literal"] = "inherit"
    out, _ = _transform("ZCode", provider_config=config)
    assert _frontmatter(out)["model"] == "inherit"


# ---------------------------------------------------------------------------
# AC-12/D3 — model-inherit-fallback never leaks a raw tier token
# ---------------------------------------------------------------------------


def test_continue_fallback_with_unresolvable_tier_emits_no_model() -> None:
    """AC-12/D3: Continue has no ``model-tiers`` catalog, so the override-all
    ``balanced`` cannot resolve — the fallback must emit **no** ``model:`` field
    instead of the raw tier token (reproduces the reported defect)."""
    out, _ = _transform(
        "Continue",
        project_config={"model-override-all": {"Continue": "balanced"}},
    )
    fm = _frontmatter(out)
    assert "model" not in fm, f"raw tier token leaked: {fm.get('model')!r}"
    assert "balanced" not in yaml.safe_dump(fm)


def test_continue_fallback_resolves_role_default_through_model_tiers() -> None:
    """When the role-default is a known tier *and* the provider declares a
    ``model-tiers`` entry, the fallback resolves through it (never raw).

    ``powerful`` is a known tier the registry cannot resolve (override-all
    yields ``""``); the orchestrator role-default is ``balanced``, which the
    registry *can* resolve — the fallback must route through it.
    """
    config = copy.deepcopy(_PROVIDER_CONFIG)
    config["Continue"]["model-tiers"] = {"balanced": "continue-balanced-id"}
    out, _ = _transform(
        "Continue",
        role="orchestrator",
        project_config={"model-override-all": {"Continue": "powerful"}},
        provider_config=config,
    )
    assert _frontmatter(out).get("model") == "continue-balanced-id"


def test_fallback_applies_model_format_exactly_once() -> None:
    """The fallback honours ``model-format`` but never doubles the prefix."""
    config = copy.deepcopy(_PROVIDER_CONFIG)
    config["Continue"]["model-tiers"] = {"balanced": "kimi-k2.6"}
    config["Continue"]["model-format"] = "kimi-code/{model}"
    out, _ = _transform(
        "Continue",
        role="orchestrator",
        project_config={"model-override-all": {"Continue": "powerful"}},
        provider_config=config,
    )
    assert _frontmatter(out).get("model") == "kimi-code/kimi-k2.6"


@pytest.mark.parametrize(
    "provider, role",
    [("Continue", "orchestrator"), ("Continue", "developer"), ("Continue", "senior-developer")],
)
def test_fallback_never_emits_a_raw_tier_token(provider: str, role: str) -> None:
    """Sweep the fallback path for a provider with no catalog: no raw token."""
    out, _ = _transform(
        provider,
        role=role,
        project_config={"model-override-all": {provider: "balanced"}},
    )
    model = _frontmatter(out).get("model")
    assert model in (None, ""), f"{provider}/{role}: raw tier leaked: {model!r}"
