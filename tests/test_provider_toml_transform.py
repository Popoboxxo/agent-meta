"""Golden tests for the Codex/ZCode/KimiCode agent transforms (P2).

The three new providers from the 2026-09-04 provider plan differ:

- Codex uses the ``codex-toml`` frontmatter-mechanism: the generated agent
  is a native TOML document (.codex/agents/<name>.toml) with the Markdown
  body as ``developer_instructions`` — built by agent_toml.py on top of
  the generic toml_writer.py.
- ZCode and KimiCode use the DEFAULT transform path (Markdown + YAML
  frontmatter), differing only in their declarative ``agent-transform:``
  blocks (strip-fields, tools handling).

All tests run against the REAL config/ai-providers.yaml,
config/provider-tools.yaml, config/role-defaults.yaml and
config/tier-presets.yaml — no mocking.
"""
from __future__ import annotations

try:
    import tomllib
except ModuleNotFoundError:
    import tomli as tomllib
from pathlib import Path

import yaml

from scripts.lib.frontmatter import target_filename
from scripts.lib.log import SyncLog
from scripts.lib.provider_transform import transform_agent_content_for_provider
from scripts.lib.providers import load_providers_config
from scripts.lib.roles import resolve_model

REPO_ROOT = Path(__file__).resolve().parents[1]

_PROVIDER_CONFIG = load_providers_config(REPO_ROOT)

CODEX_MODEL_BALANCED = "gpt-5.3-codex-spark"
ZCODE_MODEL_BALANCED = "glm-5.3"
ZCODE_MODEL_FAST = "glm-5.3-flash"
KIMICODE_MODEL_BALANCED = "kimi-k2.7-code"


def _sample_agent_content() -> str:
    """Realistic template content: bookkeeping + tools/sampling frontmatter,
    Markdown body with a Claude-specific extension line."""
    return (
        "---\n"
        "name: template-orchestrator\n"
        'version: "0.101.0"\n'
        "description: old description\n"
        "tools:\n"
        "  - Read\n"
        "  - Bash\n"
        "  - Agent\n"
        "  - TodoWrite\n"
        "memory: project\n"
        "temperature: 0.3\n"
        "---\n"
        "\n"
        "# Orchestrator\n\n"
        "Koordiniert alle Entwicklungsaufgaben.\n\n"
        "> **Extension:** Falls `.claude/3-project/orchestrator-ext.md` existiert, lesen.\n"
        "Body-Ende.\n"
    )


def _transform(provider: str, role: str, content: str | None = None,
               description: str = "Einstiegspunkt — koordiniert alle anderen Agenten.") -> tuple[str, SyncLog]:
    """Run the full provider transform for a role against the real config."""
    log = SyncLog()
    out = transform_agent_content_for_provider(
        content or _sample_agent_content(), provider, role, role,
        description, "1-generic/orchestrator.md@0.101.0", {},
        REPO_ROOT, REPO_ROOT,
        REPO_ROOT / ".codex" / "agents" / f"{role}.toml",
        _PROVIDER_CONFIG, log,
    )
    return out, log


# ---------------------------------------------------------------------------
# (a) Codex — codex-toml mechanism
# ---------------------------------------------------------------------------

def test_codex_output_is_valid_toml_with_expected_fields() -> None:
    out, _ = _transform("Codex", "orchestrator")
    assert out.startswith("# agent-meta generated file")
    doc = tomllib.loads(out)
    assert doc["name"] == "orchestrator"
    assert doc["description"] == "Einstiegspunkt — koordiniert alle anderen Agenten."
    assert doc["sandbox_mode"] == "workspace-write"
    # agent-meta bookkeeping lives in comments, not in TOML fields
    assert "version" not in doc
    assert "generated-from" not in doc


def test_codex_body_is_developer_instructions_with_claude_lines_stripped() -> None:
    out, _ = _transform("Codex", "orchestrator")
    doc = tomllib.loads(out)
    assert doc["developer_instructions"] == (
        "# Orchestrator\n\n"
        "Koordiniert alle Entwicklungsaufgaben.\n\n"
        "Body-Ende.\n"
    )
    assert ".claude/3-project" not in doc["developer_instructions"]
    # developer_instructions must be the LAST field: the document ends with
    # its multi-line string and no other assignment follows its opener
    lines = out.splitlines()
    assert lines[-1] == '"""'
    di_idx = lines.index("developer_instructions = \"\"\"")
    name_idx = lines.index("name = \"orchestrator\"")
    assert di_idx > name_idx
    assert not [ln for ln in lines[di_idx + 1:] if ln.endswith("= \"\"\"") or ln.startswith("name = ")]


def test_codex_model_resolved_via_provider_tier_mapping() -> None:
    out, log = _transform("Codex", "orchestrator")
    doc = tomllib.loads(out)
    assert doc["model"] == CODEX_MODEL_BALANCED
    # tools: skip and sampling fields have no place in the Codex TOML schema
    assert "tools" not in doc
    assert "temperature" not in doc
    assert "memory" not in doc
    assert any("model: gpt-5.3-codex-spark" in i for i in log.infos)


def test_codex_provenance_preserved_as_header_comments() -> None:
    out, _ = _transform("Codex", "orchestrator")
    assert "# version: 0.101.0" in out
    assert "# generated-from: 1-generic/orchestrator.md@0.101.0" in out


def test_codex_model_omitted_when_inherit_main_chat_active() -> None:
    log = SyncLog()
    out = transform_agent_content_for_provider(
        _sample_agent_content(), "Codex", "orchestrator", "orchestrator",
        "desc", "1-generic/orchestrator.md@0.101.0",
        {"model-inherit-main-chat": {"Codex": True}},
        REPO_ROOT, REPO_ROOT, REPO_ROOT / ".codex" / "agents" / "orchestrator.toml",
        _PROVIDER_CONFIG, log,
    )
    doc = tomllib.loads(out)
    assert "model" not in doc
    assert doc["developer_instructions"].startswith("# Orchestrator")


def test_codex_filename_ends_with_toml_via_target_filename_ext() -> None:
    role_map = {"orchestrator": "orchestrator"}
    ext = _PROVIDER_CONFIG["Codex"]["agent_ext"]
    assert ext == ".toml"
    assert target_filename("orchestrator", role_map, ext=ext) == "orchestrator.toml"
    # default keeps every existing caller on Markdown output
    assert target_filename("orchestrator", role_map) == "orchestrator.md"


# ---------------------------------------------------------------------------
# (b) ZCode — default path (Markdown + YAML frontmatter)
# ---------------------------------------------------------------------------

def test_zcode_output_stays_markdown_with_injected_model() -> None:
    out, _ = _transform("ZCode", "orchestrator")
    assert out.startswith("---\n")
    fm = out.split("---")[1]
    assert "name: orchestrator" in fm
    assert "model: glm-5.3" in fm


def test_zcode_fast_tier_role_gets_flash_model() -> None:
    out, _ = _transform("ZCode", "junior-developer",
                        description="Triviale Code-Änderungen.")
    fm = out.split("---")[1]
    assert "model: glm-5.3-flash" in fm


def test_zcode_strip_fields_removed_and_tools_untouched() -> None:
    out, _ = _transform("ZCode", "orchestrator")
    fm = out.split("---")[1]
    # strip-fields from the ZCode agent-transform block
    for field in ("memory:", "permissionMode:", "temperature:",
                  "top_p:", "top_k:", "stop_sequences:", "max_output_tokens:"):
        assert field not in fm, f"{field} must be stripped for ZCode"
    # tools: skip — the field stays exactly as generated
    assert "tools:" in fm
    assert "- Read" in fm
    assert "- TodoWrite" in fm


def test_zcode_body_intact_with_claude_lines_stripped() -> None:
    out, _ = _transform("ZCode", "orchestrator")
    assert "Koordiniert alle Entwicklungsaufgaben." in out
    assert "Body-Ende." in out
    assert ".claude/3-project" not in out


# ---------------------------------------------------------------------------
# (c) KimiCode — default path with tools: keep
# ---------------------------------------------------------------------------

def test_kimicode_model_injected_and_strip_fields_applied() -> None:
    out, _ = _transform("KimiCode", "orchestrator")
    assert out.startswith("---\n")
    fm = out.split("---")[1]
    assert "model: kimi-k2.7-code" in fm
    for field in ("memory:", "temperature:", "top_p:", "top_k:",
                  "stop_sequences:", "max_output_tokens:"):
        assert field not in fm, f"{field} must be stripped for KimiCode"


def test_kimicode_tools_kept_and_validated_against_whitelist() -> None:
    out, log = _transform("KimiCode", "orchestrator")
    fm = out.split("---")[1]
    # tools: keep — the field survives (unlike opencode's filter/remove)
    assert "tools:" in fm
    assert "- Read" in fm
    assert "- Agent" in fm
    # validation ran against the real kimicode whitelist: TodoWrite is on
    # the kimicode-silent list → dropped-by-design INFO note
    assert any("TodoWrite" in i and "not supported" in i for i in log.infos)


def test_kimicode_claude_lines_stripped_body_intact() -> None:
    out, _ = _transform("KimiCode", "orchestrator")
    assert ".claude/3-project" not in out
    assert "Koordiniert alle Entwicklungsaufgaben." in out
    assert "Body-Ende." in out


# ---------------------------------------------------------------------------
# (d) Config-drift guards
# ---------------------------------------------------------------------------

def test_codex_registry_exposes_toml_agent_ext() -> None:
    assert _PROVIDER_CONFIG["Codex"]["agent_ext"] == ".toml"


def test_all_three_new_providers_have_agent_transform_block() -> None:
    for provider in ("Codex", "ZCode", "KimiCode"):
        spec = _PROVIDER_CONFIG[provider].get("agent-transform")
        assert isinstance(spec, dict) and spec, (
            f"{provider} is missing its agent-transform block in config/ai-providers.yaml"
        )


def test_only_codex_uses_codex_toml_mechanism() -> None:
    spec = _PROVIDER_CONFIG["Codex"]["agent-transform"]
    assert spec.get("frontmatter-mechanism") == "codex-toml"
    for provider in ("ZCode", "KimiCode"):
        assert "frontmatter-mechanism" not in _PROVIDER_CONFIG[provider]["agent-transform"]


# ---------------------------------------------------------------------------
# Provider tier mapping (Normal preset entries for the new providers)
# ---------------------------------------------------------------------------

def test_provider_tier_mapping_resolves_native_models() -> None:
    """The Normal preset's provider entries mirror each provider's own
    model-tiers table — without them the preset's global tiers (a
    Claude-centric legacy curve) would inject claude-* IDs into
    Codex/ZCode/KimiCode agents."""
    for provider, expected in (
        ("Codex", CODEX_MODEL_BALANCED),
        ("ZCode", ZCODE_MODEL_BALANCED),
        ("KimiCode", KIMICODE_MODEL_BALANCED),
    ):
        resolved = resolve_model("orchestrator", {"tier-preset": "Normal"},
                                 REPO_ROOT, provider=provider,
                                 provider_config=_PROVIDER_CONFIG)
        assert resolved == expected, f"{provider}: got {resolved!r}, want {expected!r}"


def test_normal_preset_has_entries_for_all_three_new_providers() -> None:
    """Config-drift guard: tier-presets.yaml's Normal preset must keep
    provider entries for every provider that ships a model-tiers table."""
    with open(REPO_ROOT / "config" / "tier-presets.yaml", encoding="utf-8") as fh:
        presets = yaml.safe_load(fh)
    providers = presets["Normal"].get("providers", {})
    for provider in ("Codex", "ZCode", "KimiCode"):
        tiers = providers.get(provider, {}).get("tiers", {})
        assert tiers.get("balanced"), (
            f"Normal preset is missing providers.{provider}.tiers.balanced "
            f"(would fall back to the Claude-centric global curve)"
        )


def test_preset_provider_entry_beats_preset_global_tiers() -> None:
    """A preset's provider-specific tiers remain the highest in-preset
    precedence (mechanism the new providers' entries rely on)."""
    config = {
        "tier-presets": {
            "Custom": {
                "tiers": {"balanced": "global-fallback-id"},
                "providers": {"Claude": {"tiers": {"balanced": "preset-provider-id"}}},
            },
        },
        "tier-preset": "Custom",
    }
    resolved = resolve_model("orchestrator", config, REPO_ROOT,
                             provider="Claude", provider_config=_PROVIDER_CONFIG)
    assert resolved == "preset-provider-id"


def test_empty_catalog_still_falls_back_to_preset_global() -> None:
    """Providers without a model-tiers catalog (e.g. Continue) keep the
    historical preset-global fallback — pinned by test_model_inherit too."""
    resolved = resolve_model("orchestrator", {"tier-preset": "Normal"},
                             REPO_ROOT, provider="Continue",
                             provider_config=_PROVIDER_CONFIG)
    assert resolved == "claude-sonnet-5"
