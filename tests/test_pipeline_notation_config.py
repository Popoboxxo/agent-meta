"""AC-11 (D6/D7/F11): provider pipeline notation is config-backed and registry-driven.

Contract under test (Spec §2.3):
  * every registered provider declares a complete ``pipeline_notation:`` block in
    ``config/delegation-syntax.yaml``;
  * ``pipelines.pipeline_notation(provider, config_dir)`` reads that block and
    fails loud when it is missing (no silent ``opencode``/``task()`` default);
  * the rendered ``task_fmt`` is consistent with the provider's
    ``delegation_syntax.<Provider>.delegate`` phrasing;
  * the provider list comes from the registry
    (``providers.registered_provider_names``), so Copilot is present.
"""
from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from scripts.lib.io import SyncError
from scripts.lib.log import SyncLog
from scripts.lib.pipelines import (
    _PIPELINE_NOTATION_KEYS,
    _generate_pipeline_block,
    _pipeline_notation_declared,
    build_pipeline_variables,
    generate_pipeline_detail_blocks,
    inject_pipeline_blocks,
    pipeline_notation,
    sync_pipeline_detail_files,
)
from scripts.lib.providers import registered_provider_names

REPO_ROOT = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO_ROOT / "config"
SYNTAX_FILE = CONFIG_DIR / "delegation-syntax.yaml"
CONTINUE_TEMPLATE = REPO_ROOT / "templates" / "configs" / "CONTINUE.config-template.yaml"

REGISTERED = registered_provider_names(REPO_ROOT)

# The full key set hardcoded in the former ``_PROVIDER_NOTATION``
# (Spec §2.3 lists exactly these 12 — including parallel_start/parallel_item,
# which ``_generate_pipeline_block()`` reads for ``mode: parallel_group``).
REQUIRED_NOTATION_KEYS = {
    "task_fmt",
    "mention_fmt",
    "loop_start",
    "loop_item",
    "parallel_start",
    "parallel_item",
    "fanout_start",
    "fanout_item",
    "conditional_start",
    "conditional_item",
    "sequential_start",
    "sequential_item",
}

# task_fmt dispatch token / matching delegate token, per provider.
# Claude + Mammouth keep their pre-existing ``background(agent=...)`` notation
# (asserted byte-stable by tests/test_pipelines.py); they are intentionally not
# in this consistency matrix because their legacy notation predates the
# ``delegate`` phrasing alignment.
_DISPATCH_CONSISTENCY = {
    "Opencode": ("task(", "task("),
    "Gemini": ("invoke_subagent(", "invoke_subagent"),
    "Continue": ("@{agent}", "@<ziel-agent>"),
    "Codex": ("spawn_agent(", "spawn_agent"),
    "ZCode": ("Agent(subagent_type=", "Agent(subagent_type="),
    "KimiCode": ("Agent(", "Agent("),
    "Copilot": ("@{agent}", "@<ziel-agent>"),
}


def _syntax() -> dict:
    return yaml.safe_load(SYNTAX_FILE.read_text(encoding="utf-8"))["delegation_syntax"]


# --------------------------------------------------------------------------
# Registry + config completeness
# --------------------------------------------------------------------------


def test_registry_contains_copilot():
    """F11/D7: Copilot is a registered provider and must resolve."""
    assert "Copilot" in REGISTERED


@pytest.mark.parametrize("provider", REGISTERED)
def test_every_registered_provider_has_a_complete_notation_block(provider):
    block = _syntax()[provider].get("pipeline_notation")
    assert isinstance(block, dict), (
        f"delegation_syntax.{provider}.pipeline_notation is missing — "
        "every registered provider needs one (AC-11)"
    )
    assert REQUIRED_NOTATION_KEYS <= set(block), (
        f"{provider}: missing pipeline_notation keys "
        f"{sorted(REQUIRED_NOTATION_KEYS - set(block))}"
    )


@pytest.mark.parametrize("provider", REGISTERED)
def test_pipeline_notation_reads_from_config(provider):
    notation = pipeline_notation(provider, CONFIG_DIR)
    assert set(notation) >= REQUIRED_NOTATION_KEYS
    assert notation == _syntax()[provider]["pipeline_notation"]


def test_pipeline_notation_lookup_is_case_insensitive():
    assert pipeline_notation("opencode", CONFIG_DIR) == pipeline_notation("Opencode", CONFIG_DIR)


def test_pipeline_notation_key_set_constant_matches_config():
    assert _PIPELINE_NOTATION_KEYS == tuple(
        [
            "task_fmt",
            "mention_fmt",
            "loop_start",
            "loop_item",
            "parallel_start",
            "parallel_item",
            "fanout_start",
            "fanout_item",
            "conditional_start",
            "conditional_item",
            "sequential_start",
            "sequential_item",
        ]
    )


# --------------------------------------------------------------------------
# Fail-loud (AC-11: no silent ``task()`` default)
# --------------------------------------------------------------------------


def _write_syntax(tmp_path: Path, syntax: dict) -> Path:
    cfg = tmp_path / "config"
    cfg.mkdir()
    (cfg / "delegation-syntax.yaml").write_text(
        yaml.safe_dump({"delegation_syntax": syntax}), encoding="utf-8"
    )
    return cfg


def test_missing_block_fails_loud(tmp_path):
    cfg = _write_syntax(tmp_path, {"Claude": {"delegate": "x", "pipeline_notation": {}}})
    with pytest.raises(SyncError, match="pipeline_notation"):
        pipeline_notation("Opencode", cfg)


def test_absent_provider_fails_loud(tmp_path):
    cfg = _write_syntax(tmp_path, {"Claude": {"delegate": "x"}})
    with pytest.raises(SyncError, match="pipeline_notation"):
        pipeline_notation("Ghost", cfg)


def test_incomplete_block_fails_loud(tmp_path):
    cfg = _write_syntax(
        tmp_path,
        {"Claude": {"pipeline_notation": {"task_fmt": "x"}}},
    )
    with pytest.raises(SyncError, match="pipeline_notation"):
        pipeline_notation("Claude", cfg)


def test_config_build_pipeline_variables_propagates_missing_block(monkeypatch):
    """AC-11 end-to-end: a ``SyncError`` from ``pipeline_notation`` must escape
    ``config._build_pipeline_variables`` — the broad quality-pipelines handler
    must not downgrade a missing *declared* notation block to an ``unmapped``
    warning (the fail-soft scope that contradicted AC-11)."""
    from scripts.lib import config as config_mod
    from scripts.lib import pipelines as pipelines_mod

    def _boom(provider, config_dir):
        raise SyncError(
            f"delegation-syntax.yaml: provider '{provider}' has no "
            "'pipeline_notation' block (AC-11)."
        )

    monkeypatch.setattr(pipelines_mod, "pipeline_notation", _boom)

    variables: dict = {}
    unmapped: list[str] = []
    with pytest.raises(SyncError, match="pipeline_notation"):
        config_mod._build_pipeline_variables(variables, unmapped, {}, REPO_ROOT, {})
    assert unmapped == [], (
        "the SyncError must propagate, not be recorded as a warning: "
        f"{unmapped}"
    )


# --------------------------------------------------------------------------
# Notation <-> delegate consistency (Spec §2.3, D6)
# --------------------------------------------------------------------------


@pytest.mark.parametrize("provider,tokens", sorted(_DISPATCH_CONSISTENCY.items()))
def test_task_fmt_is_consistent_with_delegate_phrasing(provider, tokens):
    task_token, delegate_token = tokens
    notation = pipeline_notation(provider, CONFIG_DIR)
    assert task_token in notation["task_fmt"], (
        f"{provider}: task_fmt {notation['task_fmt']!r} must use {task_token!r}"
    )
    delegate = _syntax()[provider]["delegate"]
    assert delegate_token in delegate, (
        f"{provider}: delegate phrasing must contain {delegate_token!r}"
    )


# --------------------------------------------------------------------------
# Renderer + registry-driven provider list (D6/D7)
# --------------------------------------------------------------------------


def test_renderer_uses_per_provider_notation_not_opencode_fallback():
    pipeline = {
        "stages": [
            {"id": "x", "agent": "developer", "task": "Fix it", "mode": "sequential"}
        ]
    }
    expected = {
        "Codex": "spawn_agent(",
        "ZCode": "Agent(subagent_type=",
        "KimiCode": "Agent(",
        "Copilot": "@developer",
    }
    for provider, token in expected.items():
        block = _generate_pipeline_block(pipeline, provider)
        assert token in block, f"{provider} rendered {block!r}"
        assert "task(subagent_type=" not in block, (
            f"{provider} still falls back to the Opencode task() notation"
        )


def test_build_pipeline_variables_is_registry_driven():
    pipelines = {
        "p": {
            "stages": [
                {"id": "x", "agent": "developer", "task": "T", "mode": "sequential"}
            ]
        }
    }
    blocks = build_pipeline_variables(pipelines, active_dod={})[
        "PIPELINE_P_PROVIDER_BLOCKS"
    ]
    for provider in REGISTERED:
        assert provider in blocks, f"{provider} missing from provider blocks"
        assert blocks[provider], f"{provider} rendered an empty block"
    assert "task(subagent_type=" not in blocks["Copilot"]
    assert "@developer" in blocks["Copilot"]


# --------------------------------------------------------------------------
# OQ-9 / OQ-2 (Continue surface)
# --------------------------------------------------------------------------


def test_continue_template_roles_enum_excludes_out_of_enum_agent():
    """OQ-9: `agent` is not a valid Continue model role — the starting-point
    template must not ship it (it fails the Continue config schema)."""
    config = yaml.safe_load(CONTINUE_TEMPLATE.read_text(encoding="utf-8"))
    for model in config["models"]:
        assert "agent" not in (model.get("roles") or []), model["name"]


def test_undeclared_provider_is_not_a_notation_provider(tmp_path):
    """A probe/synthetic provider absent from delegation-syntax.yaml is skipped
    (never rendered with an Opencode fallback, never crashes sync)."""
    cfg = _write_syntax(tmp_path, {"Claude": {"pipeline_notation": {}}})
    assert _pipeline_notation_declared("Claude", cfg) is True
    assert _pipeline_notation_declared("GateProbe", cfg) is False


def test_sync_pipeline_detail_files_skips_undeclared_provider(tmp_path):
    pipelines = {
        "p": {"stages": [{"id": "x", "agent": "developer", "task": "T", "mode": "sequential"}]}
    }
    target = tmp_path / "pipeline-details"
    sync_pipeline_detail_files(
        pipelines, "GateProbe", target, tmp_path, {}, SyncLog(), dry_run=False
    )
    assert not target.exists()


def test_continue_bootstrap_sequence_target_is_kept():
    """OQ-2: the Continue `bootstrap_sequence.target` stays (Task 10 removes the
    dead `agents:` block, not this target)."""
    sequence = _syntax()["Continue"]["bootstrap_sequence"]
    assert sequence[0]["target"] == ".continue/config.yaml"


# --------------------------------------------------------------------------
# B1: the render-path guard matches the declared/skip contract
# --------------------------------------------------------------------------

_PROBE_PIPELINES = {
    "p": {
        "stages": [
            {"id": "x", "agent": "developer", "task": "T", "mode": "sequential"}
        ]
    }
}


def test_inject_pipeline_blocks_skips_undeclared_provider():
    """B1 regression: an undeclared/synthetic provider must not reach
    ``pipeline_notation`` on the per-agent render path — it is skipped, exactly
    like ``build_pipeline_variables``/``sync_pipeline_detail_files``."""
    content = "before {{PIPELINE_P_BLOCK}} after {{PIPELINE_DETAIL_BLOCKS}}"
    rendered = inject_pipeline_blocks(content, _PROBE_PIPELINES, "GateProbe", active_dod={})
    assert "{{PIPELINE_P_BLOCK}}" not in rendered
    assert "{{PIPELINE_DETAIL_BLOCKS}}" not in rendered
    # not an error, just an empty block replacement
    assert "before" in rendered and "after" in rendered


def test_generate_pipeline_detail_blocks_skips_undeclared_provider():
    """B1 regression: the aggregate detail renderer must return "" for an
    undeclared provider instead of raising a ``SyncError``."""
    assert generate_pipeline_detail_blocks(_PROBE_PIPELINES, "GateProbe", active_dod={}) == ""


def test_render_paths_still_fail_loud_for_declared_incomplete_provider(
    tmp_path, monkeypatch
):
    """B1 regression: the skip guard covers only *undeclared* providers — a
    declared provider with an incomplete ``pipeline_notation`` block must still
    fail loud on both render paths (AC-11)."""
    from scripts.lib import pipelines as pipelines_mod

    cfg = _write_syntax(
        tmp_path, {"Claude": {"delegate": "x", "pipeline_notation": {}}}
    )
    monkeypatch.setattr(pipelines_mod, "_DEFAULT_CONFIG_DIR", cfg)
    pipelines_mod.pipeline_notation.cache_clear()

    with pytest.raises(SyncError, match="pipeline_notation"):
        pipelines_mod.inject_pipeline_blocks(
            "{{PIPELINE_P_BLOCK}}", _PROBE_PIPELINES, "Claude", active_dod={}
        )
    with pytest.raises(SyncError, match="pipeline_notation"):
        pipelines_mod.generate_pipeline_detail_blocks(
            _PROBE_PIPELINES, "Claude", active_dod={}
        )
