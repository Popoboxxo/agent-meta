"""Adapter-capability registry invariant and ``per-provider`` render.

SPEC-CONTEXT-FILE-MODES-2026-09-13:

- AC-12: every provider marked ``context_adapter: true`` (in
  ``config/ai-providers.yaml``) or carrying the ``context-adapter`` capability
  must declare a non-empty ``context_adapter_file`` and an explicit boolean
  ``context_adapter_import_supported``; no two adapters may share a file;
  non-adapter providers carry no adapter keys.
- AC-13: in ``per-provider`` mode direct readers stay on the canonical core and
  only adapter-capable providers get their adapter file.
- AC-14: the Claude adapter's managed block carries no ``GATE_*``.
- AC-15: import/pointer semantics.
- AC-16: the ``per-provider`` render is idempotent.
- AC-17: adapters are recorded in the adapter managed index + context hashes.
- AC-23: the canonical core renders the neutral ``GATE_NEUTRAL`` state in
  ``per-provider`` (directive without a runtime promise, no "if you are X"
  block); ``GATE_NEUTRAL`` is a render state, not a ``RUNTIME_GATE_TIERS``
  value.
- AC-22/AC-26: Codex/Copilot/Continue/Mammouth/Gemini stay direct readers of
  the core (Phase-2 adapters dormant behind their HYPOTHESIS).

Run: python -m pytest tests/test_context_adapters.py -v
"""
from __future__ import annotations

import copy
import json
import re
import shutil
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import load_config
from lib.context import (
    _adapter_reference_line,
    rollback_context_adapters,
    sync_context_adapters_for_provider,
    sync_context_for_provider,
)
from lib.log import SyncLog
from lib.providers import (
    load_provider_capabilities,
    load_providers_config,
    runtime_gate_vars,
)

_ADAPTER_KEYS = (
    "context_adapter",
    "context_adapter_file",
    "context_adapter_import",
    "context_adapter_import_supported",
    "context_adapter_settings",
)

_GATE_KEYS = (
    "ENFORCEMENT_TIER",
    "GATE_ENFORCED",
    "GATE_PARTIAL",
    "GATE_ADVISORY",
    "RUNTIME_GATE_PLUGIN_MODE",
)

_MANAGED_BLOCK_RE = re.compile(
    r"<!--\s*agent-meta:managed-begin\s*-->.*?<!--\s*agent-meta:managed-end\s*-->",
    re.DOTALL,
)
_ADAPTER_INDEX = ".agent-meta-context-adapters-managed"


def _providers() -> dict:
    data = yaml.safe_load(
        (_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8")
    )
    return data.get("providers") or {}


def _is_adapter(pc: dict) -> bool:
    """An adapter provider opts in via the top-level flag or the capability."""
    if pc.get("context_adapter") is True:
        return True
    return "context-adapter" in (pc.get("capabilities") or [])


def _adapter_providers() -> dict:
    return {name: pc for name, pc in _providers().items() if _is_adapter(pc)}


def test_adapter_providers_have_file_and_import_support():
    for name, pc in _adapter_providers().items():
        adapter_file = pc.get("context_adapter_file")
        assert isinstance(adapter_file, str) and adapter_file.strip(), (
            f"Adapter provider '{name}' needs a non-empty context_adapter_file"
        )
        assert isinstance(pc.get("context_adapter_import_supported"), bool), (
            f"Adapter provider '{name}' needs an explicit boolean "
            "context_adapter_import_supported"
        )
        assert isinstance(pc.get("context_adapter_import"), str), (
            f"Adapter provider '{name}' needs a string context_adapter_import "
            "(empty string means pointer line)"
        )


def test_no_two_adapters_share_a_file():
    files: dict = {}
    for name, pc in _adapter_providers().items():
        target = pc.get("context_adapter_file")
        assert target not in files, (
            f"Adapter file '{target}' is declared by both '{files.get(target)}' "
            f"and '{name}' — adapters must be distinct"
        )
        files[target] = name


def test_non_adapter_providers_have_no_adapter_keys():
    """A provider that does not opt in carries no adapter keys.

    Phase 2 exception: an explicitly **disabled** candidate
    (``context_adapter: false``) is a documented dormant registry entry (see
    ``tests/manual/phase2-adapter-hypothesis.md``) and may name its candidate
    file. It is never treated as an adapter.
    """
    for name, pc in _providers().items():
        if _is_adapter(pc):
            continue
        if "context_adapter" in pc:
            assert pc.get("context_adapter") is False, (
                f"Provider '{name}' has a non-boolean context_adapter "
                f"({pc.get('context_adapter')!r}) — use true/false only"
            )
            assert pc.get("context_adapter_settings") is not True, (
                f"Dormant candidate '{name}' must not enable context_adapter_settings"
            )
            continue
        present = [key for key in _ADAPTER_KEYS if key in pc]
        assert not present, (
            f"Non-adapter provider '{name}' declares adapter key(s) {present} — "
            "omit them entirely (direct reader of the core / rules channel)"
        )


def test_claude_is_the_only_phase1_adapter():
    """Phase 1: Claude is the sole adapter — it is the only provider with a
    dedicated context file (``has_dedicated_context_file``)."""
    adapter_names = set(_adapter_providers())
    assert adapter_names == {"Claude"}
    dedicated = {
        name
        for name, pc in _providers().items()
        if pc.get("has_dedicated_context_file") is True
    }
    assert adapter_names == dedicated


# --- Task 5: per-provider core/adapter render + dispatch (AC-13 … AC-17) ----


@pytest.fixture
def loaded_config():
    return (
        load_config(_REPO_ROOT / ".meta-config" / "project.yaml"),
        load_providers_config(_REPO_ROOT),
        load_provider_capabilities(_REPO_ROOT),
    )


def _per_provider_config(config):
    """Deep copy of the loaded config with ``topology: per-provider``."""
    cfg = copy.deepcopy(config)
    block = cfg.get("context_file")
    if not isinstance(block, dict):
        block = {}
        cfg["context_file"] = block
    block["topology"] = "per-provider"
    block.setdefault("core_file", "AGENTS.md")
    return cfg


def _seed(tmp_path, *names):
    for name in names:
        shutil.copy(_REPO_ROOT / name, tmp_path / name)


def _variables(config, pc, caps):
    variables = dict(config.get("variables", {}))
    variables.update(runtime_gate_vars(pc, caps, config))
    return variables


def _sync(project_root, config, provider, pc, caps, provider_config):
    log = SyncLog()
    sync_context_for_provider(
        _REPO_ROOT, project_root, config, _variables(config, pc, caps), log,
        dry_run=False, provider=provider, provider_config=provider_config,
    )
    return log


def _adapter_pc(**overrides):
    pc = {
        "context_file": "CLAUDE.md",
        "context_template": "templates/configs/CLAUDE.project-template.md",
        "has_dedicated_context_file": True,
        "capabilities": ["context-managed-block"],
        "context_adapter": True,
        "context_adapter_file": "CLAUDE.md",
        "context_adapter_import": "@{core}",
        "context_adapter_import_supported": True,
    }
    pc.update(overrides)
    return pc


def _render_synthetic_adapter(tmp_path, config, pc):
    provider = "SyntheticAdapter"
    _seed(tmp_path, pc["context_adapter_file"])
    sync_context_adapters_for_provider(
        _REPO_ROOT, tmp_path, config, _variables(config, pc, {}), SyncLog(),
        dry_run=False, provider=provider, provider_config={provider: pc},
    )
    return (tmp_path / pc["context_adapter_file"]).read_text(encoding="utf-8")


def test_per_provider_direct_readers_stay_on_core(tmp_path, loaded_config):
    """AC-13: direct readers render the canonical core, never an adapter file."""
    config, provider_config, capabilities = loaded_config
    cfg = _per_provider_config(config)
    _seed(tmp_path, "AGENTS.md")

    for provider in ("Opencode", "Gemini"):
        pc = provider_config[provider]
        assert pc.get("context_adapter_file") is None
        _sync(tmp_path, cfg, provider, pc, capabilities.get(provider, {}), provider_config)

    for provider in ("KimiCode", "ZCode"):
        assert provider_config[provider].get("context_adapter_file") is None

    assert (tmp_path / "AGENTS.md").exists()
    assert not (tmp_path / "CLAUDE.md").exists()
    index = tmp_path / _ADAPTER_INDEX
    assert not index.exists() or "CLAUDE.md" not in index.read_text(encoding="utf-8")


def test_claude_adapter_written_to_claude_md(tmp_path, loaded_config):
    """AC-13: the adapter file actually written is Claude's native CLAUDE.md."""
    config, provider_config, capabilities = loaded_config
    cfg = _per_provider_config(config)
    _seed(tmp_path, "CLAUDE.md")
    pc = provider_config["Claude"]

    _sync(tmp_path, cfg, "Claude", pc, capabilities["Claude"], provider_config)

    adapter = tmp_path / pc["context_adapter_file"]
    assert adapter.exists()
    assert "@AGENTS.md" in adapter.read_text(encoding="utf-8")


def test_adapter_import_line_when_supported(tmp_path, loaded_config):
    """AC-15: the supported native import syntax renders ``@AGENTS.md``."""
    config, *_ = loaded_config
    cfg = _per_provider_config(config)
    assert "@AGENTS.md" in _render_synthetic_adapter(tmp_path, cfg, _adapter_pc())


def test_adapter_pointer_line_when_unsupported(tmp_path, loaded_config):
    """AC-15: unsupported import support falls back to a core pointer line."""
    config, *_ = loaded_config
    cfg = _per_provider_config(config)
    pc = _adapter_pc(context_adapter_import_supported=False)
    text = _render_synthetic_adapter(tmp_path, cfg, pc)
    assert "@AGENTS.md" not in text
    assert "AGENTS.md" in text


def test_empty_import_falls_back_to_pointer(tmp_path, loaded_config):
    """AC-15: an empty import syntax never crashes and falls back to pointer."""
    config, *_ = loaded_config
    cfg = _per_provider_config(config)
    pc = _adapter_pc(context_adapter_import="")
    text = _render_synthetic_adapter(tmp_path, cfg, pc)
    assert "@AGENTS.md" not in text
    assert "AGENTS.md" in text
    assert _adapter_reference_line(
        {"context_file": {"core_file": "AGENTS.md"}},
        _adapter_pc(context_adapter_import_supported=False),
    ) == "Read `AGENTS.md` for the shared project context."


def test_claude_managed_block_has_no_gate_vars(tmp_path, loaded_config):
    """AC-14/F-04: the Claude adapter block carries no ``GATE_*`` claim."""
    config, provider_config, capabilities = loaded_config
    cfg = _per_provider_config(config)
    _seed(tmp_path, "CLAUDE.md")
    pc = provider_config["Claude"]

    _sync(tmp_path, cfg, "Claude", pc, capabilities["Claude"], provider_config)

    managed = _MANAGED_BLOCK_RE.search(
        (tmp_path / "CLAUDE.md").read_text(encoding="utf-8")
    )
    assert managed, "the adapter must render a managed block"
    for key in _GATE_KEYS:
        assert key not in managed.group(0), f"{key} leaked into the Claude adapter block"


def test_per_provider_render_idempotent(tmp_path, loaded_config):
    """AC-16: a second ``per-provider`` run is a byte-identical no-op."""
    config, provider_config, capabilities = loaded_config
    cfg = _per_provider_config(config)
    _seed(tmp_path, "CLAUDE.md")
    pc = provider_config["Claude"]

    snapshots = []
    second_log = None
    for index in range(2):
        log = _sync(tmp_path, cfg, "Claude", pc, capabilities["Claude"], provider_config)
        snapshots.append((tmp_path / "CLAUDE.md").read_bytes())
        if index == 1:
            second_log = log

    assert snapshots[0] == snapshots[1]
    rewrites = [a for a in second_log.actions if "CLAUDE.md" in a and "managed block" in a]
    assert not rewrites, f"second run must not rewrite the adapter: {rewrites}"
    assert any("CLAUDE.md" in s and "managed block" in s for s in second_log.skipped)


def test_adapters_recorded_in_index_and_context_hashes(tmp_path, loaded_config):
    """AC-17: the adapter is indexed and gets a context-hash entry."""
    config, provider_config, capabilities = loaded_config
    cfg = _per_provider_config(config)
    _seed(tmp_path, "CLAUDE.md")
    pc = provider_config["Claude"]

    _sync(tmp_path, cfg, "Claude", pc, capabilities["Claude"], provider_config)

    index = (tmp_path / _ADAPTER_INDEX).read_text(encoding="utf-8")
    assert "CLAUDE.md" in index.splitlines()
    hashes = json.loads(
        (tmp_path / ".meta-config" / "context-hashes.json").read_text(encoding="utf-8")
    )["hashes"]
    assert "CLAUDE.md" in hashes


# --- AC-18: rollback to `unified` (Task 6) ---

_ROLLBACK_PROVIDER = "SyntheticAdapter"
_FOREIGN_TEXT = "user-owned, never listed in the adapter index\n"


def _rollback_pc(**overrides):
    """Adapter-capable pc whose unified ``context_file`` is the canonical core.

    Keeps the adapter file distinct from any provider context file so the
    rollback deletion is observable without the unified render re-creating it.
    """
    pc = _adapter_pc(context_file="AGENTS.md", context_adapter_file="ADAPTER.md")
    pc.update(overrides)
    return pc


def _render_adapter_to(tmp_path, config, pc):
    """Render a synthetic adapter file + managed index; returns its path."""
    adapter_file = pc["context_adapter_file"]
    target = tmp_path / adapter_file
    target.write_text(
        "# Adapter\n\n"
        "<!-- agent-meta:managed-begin -->\n"
        "<!-- agent-meta:managed-end -->\n",
        encoding="utf-8",
    )
    sync_context_adapters_for_provider(
        _REPO_ROOT, tmp_path, config, _variables(config, pc, {}), SyncLog(),
        dry_run=False, provider=_ROLLBACK_PROVIDER,
        provider_config={_ROLLBACK_PROVIDER: pc},
    )
    return target


def _to_unified(config):
    cfg = copy.deepcopy(config)
    block = cfg.setdefault("context_file", {})
    block["topology"] = "unified"
    block.setdefault("core_file", "AGENTS.md")
    return cfg


def _rollback(tmp_path, config, provider_config, dry_run=False):
    log = SyncLog()
    backups = rollback_context_adapters(
        tmp_path, config, provider_config, [_ROLLBACK_PROVIDER], log, dry_run,
    )
    return log, backups


def test_rollback_removes_indexed_adapters(tmp_path, loaded_config):
    """AC-18: every index-tracked adapter is removed on ``per-provider`` -> ``unified``."""
    config, *_ = loaded_config
    pc = _rollback_pc()
    provider_config = {_ROLLBACK_PROVIDER: pc}

    adapter = _render_adapter_to(tmp_path, _per_provider_config(config), pc)
    assert adapter.exists()
    index = tmp_path / _ADAPTER_INDEX
    assert "ADAPTER.md" in index.read_text(encoding="utf-8").splitlines()

    log, backups = _rollback(tmp_path, _to_unified(config), provider_config)

    assert not adapter.exists(), "indexed adapter must be removed on rollback"
    assert not index.exists(), "the empty adapter index must not linger"
    assert any("ADAPTER.md" in action for action in log.actions)
    assert list(tmp_path.glob("ADAPTER.md.sync-backup-*")), "cleanup must be backup-first"
    assert backups, "cleanup must report the written backup"


def test_rollback_keeps_foreign_adapter_files(tmp_path, loaded_config):
    """AC-18: a file without an index entry is never touched."""
    config, *_ = loaded_config
    pc = _rollback_pc()
    provider_config = {_ROLLBACK_PROVIDER: pc}
    adapter = _render_adapter_to(tmp_path, _per_provider_config(config), pc)

    foreign = tmp_path / "FOREIGN.md"
    foreign.write_text(_FOREIGN_TEXT, encoding="utf-8")

    _rollback(tmp_path, _to_unified(config), provider_config)

    assert not adapter.exists()
    assert foreign.read_text(encoding="utf-8") == _FOREIGN_TEXT, (
        "a foreign/user file absent from the adapter index must stay byte-identical"
    )


def test_rollback_restores_weakest_tier_core(tmp_path, loaded_config):
    """AC-18: the core again carries the shared weakest-tier (permission) block."""
    config, provider_config, capabilities = loaded_config
    cfg = _to_unified(config)
    shutil.copy(_REPO_ROOT / "AGENTS.md", tmp_path / "AGENTS.md")

    _sync(tmp_path, cfg, "Opencode", provider_config["Opencode"],
          capabilities["Opencode"], provider_config)

    managed = _MANAGED_BLOCK_RE.search(
        (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    )
    assert managed, "the core must carry a managed block after rollback to unified"
    text = managed.group(0)
    assert "runtime-partially enforced" in text
    assert "NICHT erzwungen" in text
    assert "Keine Ausnahmen" not in text


def test_rollback_check_reports_no_pending(tmp_path, loaded_config):
    """AC-18: rollback converges — a read-only second pass reports no pending."""
    config, *_ = loaded_config
    pc = _rollback_pc()
    provider_config = {_ROLLBACK_PROVIDER: pc}
    _render_adapter_to(tmp_path, _per_provider_config(config), pc)
    unified = _to_unified(config)

    _rollback(tmp_path, unified, provider_config)

    log, backups = _rollback(tmp_path, unified, provider_config, dry_run=True)
    assert not log.actions, f"rollback must be idempotent, got {log.actions}"
    assert not backups
    assert not (tmp_path / "ADAPTER.md").exists()
    assert not (tmp_path / _ADAPTER_INDEX).exists()


# ---------------------------------------------------------------------------
# Phase 2 — neutral core render state (AC-23)
# ---------------------------------------------------------------------------

_USE_ORCHESTRATOR = _REPO_ROOT / "rules" / "1-generic" / "use-orchestrator.md"
_A2A_GATES = _REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md"
_NEUTRAL_DIRECTIVE = "MAIN CHAT darf nicht selbst editieren. ALLES -> `orchestrator`."
_GATE_NEUTRAL_HEADING = "# CRITICAL GATE (neutral)"
_PROVIDER_IDENTIFICATION_RE = re.compile(
    r"(?i)\b(if you are|you are|wenn du)\b[^.\n]{0,30}?"
    r"\b(Claude|Gemini|Opencode|Copilot|Codex|Continue|Mammouth|KimiCode|ZCode)\b"
)


def _neutral_flags() -> dict:
    """Render flags for the neutral core state (``per-provider``)."""
    from lib.variables import _orch_mode_flags

    flags = _orch_mode_flags("strict")
    flags.update({
        "ENFORCEMENT_TIER": "permission",
        "GATE_NEUTRAL": "true",
        "GATE_ENFORCED": "false",
        "GATE_PARTIAL": "false",
        "GATE_ADVISORY": "false",
    })
    return flags


def _render_rule(path: Path, flags: dict) -> str:
    from lib.variables import strip_inactive_conditional_blocks, substitute

    text = substitute(path.read_text(encoding="utf-8"), flags, path.name, None)
    return strip_inactive_conditional_blocks(text, flags)


def test_core_carries_neutral_directive(tmp_path, loaded_config):
    """AC-23: the ``per-provider`` core states the directive, no runtime promise."""
    config, provider_config, capabilities = loaded_config
    cfg = _per_provider_config(config)
    _seed(tmp_path, "AGENTS.md")
    pc = provider_config["Opencode"]

    _sync(tmp_path, cfg, "Opencode", pc, capabilities.get("Opencode", {}), provider_config)

    managed = _MANAGED_BLOCK_RE.search(
        (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    )
    assert managed, "the canonical core must carry a managed block"
    block = managed.group(0)
    assert _NEUTRAL_DIRECTIVE in block
    assert _GATE_NEUTRAL_HEADING in block
    # no provider-specific runtime promise / tier wording leaks into the core
    assert "runtime-partially enforced" not in block
    assert "Keine Ausnahmen" not in block
    assert "rein prompt-basiert" not in block
    # the neutral core points at the dedicated channel rule (AC-23)
    assert "siehe `a2a-delegation-gates`" in block


def test_core_neutral_state_is_not_a_runtime_tier():
    """AC-23: ``GATE_NEUTRAL`` is a render state, not a ``RUNTIME_GATE_TIERS`` value."""
    from lib.runtime_gate import RUNTIME_GATE_TIERS

    assert "neutral" not in RUNTIME_GATE_TIERS
    assert "GATE_NEUTRAL" not in RUNTIME_GATE_TIERS
    assert tuple(RUNTIME_GATE_TIERS) == ("hook", "plugin", "permission", "advisory")


def test_a2a_gates_point_at_adapter():
    """AC-23: the neutral core points at "multiple providers, see adapter"."""
    neutral = _render_rule(_A2A_GATES, _neutral_flags())
    assert "multiple providers" in neutral
    assert "Adapter" in neutral
    assert "{{ENFORCEMENT_TIER}}" not in neutral
    assert "Runtime-Enforcement-Tier: `permission`" not in neutral

    tiered_flags = _neutral_flags()
    tiered_flags.update({"GATE_NEUTRAL": "false", "GATE_PARTIAL": "true"})
    tiered = _render_rule(_A2A_GATES, tiered_flags)
    assert "Runtime-Enforcement-Tier: `permission`" in tiered
    assert "multiple providers" not in tiered


def test_no_self_identification_blocks():
    """AC-23/non-goal: no "if you are X" provider self-identification block."""
    sources = sorted((_REPO_ROOT / "rules").rglob("*.md"))
    assert sources, "expected the rule templates"
    for path in sources:
        text = path.read_text(encoding="utf-8")
        assert "{{#if PLATFORM_" not in text, (
            f"{path.relative_to(_REPO_ROOT)} branches on a provider platform flag "
            "(self-identification)"
        )
        assert not _PROVIDER_IDENTIFICATION_RE.search(text), (
            f"{path.relative_to(_REPO_ROOT)} contains a provider self-identification phrase"
        )


# ---------------------------------------------------------------------------
# Phase 2 — remaining adapters stay behind their HYPOTHESIS (AC-22, AC-26)
# ---------------------------------------------------------------------------

_HYPOTHESIS_DOC = _REPO_ROOT / "tests" / "manual" / "phase2-adapter-hypothesis.md"
_PHASE2_PROVIDERS = ("Codex", "Copilot", "Continue", "Mammouth", "Gemini")


def _hypothesis_statuses() -> dict:
    """Parse the provider-matrix rows (``| Provider | Status | ...``) of the doc.

    Only rows whose second cell is a known gate status are considered, so the
    key-reference and metadata tables cannot pollute the map.
    """
    statuses: dict = {}
    for line in _HYPOTHESIS_DOC.read_text(encoding="utf-8").splitlines():
        if not line.startswith("|"):
            continue
        cells = [cell.strip() for cell in line.strip().strip("|").split("|")]
        if len(cells) < 2:
            continue
        name, status = cells[0], cells[1]
        if not name or name == "Provider" or set(name) <= {"-"}:
            continue
        if status == "VERIFIED" or status == "HYPOTHESIS" or status.startswith("FALLBACK"):
            statuses[name] = status
    return statuses


def test_no_adapter_without_verified_hypothesis():
    """AC-22: only providers recorded as ``VERIFIED`` may be active adapters."""
    statuses = _hypothesis_statuses()
    assert statuses, "the hypothesis doc must list the provider matrix"
    verified = {name for name, status in statuses.items() if "VERIFIED" in status}
    assert verified == set(_adapter_providers()), (
        "active adapters must match the VERIFIED rows of "
        "tests/manual/phase2-adapter-hypothesis.md; unverified HYPOTHESIS rows "
        "must stay direct readers"
    )
    for name in _PHASE2_PROVIDERS:
        assert name in statuses, f"{name} missing from the hypothesis matrix"


def test_phase2_providers_default_to_direct_core_reader(tmp_path, loaded_config):
    """AC-22: Codex/Copilot/Continue/Mammouth/Gemini write no adapter by default."""
    config, provider_config, capabilities = loaded_config
    cfg = _per_provider_config(config)
    _seed(tmp_path, "AGENTS.md")

    for provider in _PHASE2_PROVIDERS:
        pc = provider_config[provider]
        assert _is_adapter(pc) is False, f"{provider} must not be an active adapter"
        assert pc.get("context_adapter") is not True
        assert pc.get("context_adapter_settings") is not True

    # A per-provider run keeps them direct readers of the core: no candidate file.
    codex = provider_config["Codex"]
    _sync(tmp_path, cfg, "Codex", codex, capabilities.get("Codex", {}), provider_config)
    assert (tmp_path / "AGENTS.md").read_text(encoding="utf-8")
    assert not (tmp_path / codex["context_adapter_file"]).exists(), (
        "a dormant candidate adapter must never be written"
    )


def test_gemini_context_filename_only_with_settings_flag(loaded_config):
    """AC-26: Gemini's fallback (c) writes no ``context.fileName`` settings key.

    Gemini/Antigravity has no ``context_adapter_settings`` opt-in, so no native
    settings key is written and the shipped settings template carries no
    ``context.fileName`` — the dedicated-file candidate (b) stays deferred.
    """
    _config, provider_config, _capabilities = loaded_config
    gemini = provider_config["Gemini"]
    assert gemini.get("context_adapter_settings") is not True
    assert gemini.get("context_adapter") is not True

    template = (
        _REPO_ROOT / "templates" / "configs" / "GEMINI.settings-template.json"
    ).read_text(encoding="utf-8")
    assert "fileName" not in template, (
        "candidate (b) context.fileName must stay out of the shipped template "
        "until a real-repo verification passes"
    )


def test_settings_write_is_capability_gated(tmp_path, loaded_config):
    """AC-26: a settings activation requires the opt-in **and** a settings file."""
    from lib.context import (
        _adapter_settings_activation,
        _write_adapter_settings_activation,
    )
    from lib.log import SyncLog

    # Off by default / incomplete triples never activate.
    assert _adapter_settings_activation({}) is None
    assert _adapter_settings_activation({"context_adapter_settings": False}) is None
    assert _adapter_settings_activation({
        "context_adapter_settings": True, "context_adapter_file": "A.md",
    }) is None  # no settings_file
    assert _adapter_settings_activation({
        "context_adapter_settings": True, "context_adapter_file": "A.md",
        "settings_file": "s.json",
    }) is None  # no native key name
    activation = _adapter_settings_activation({
        "context_adapter_settings": True, "context_adapter_file": "A.md",
        "settings_file": "s.json", "context_adapter_settings_key": "context.fileName",
    })
    assert activation == {
        "settings_file": "s.json", "settings_key": "context.fileName",
        "adapter_file": "A.md",
    }

    settings = tmp_path / "s.json"
    settings.write_text('{"sibling": true}\n', encoding="utf-8")
    _write_adapter_settings_activation(tmp_path, activation, SyncLog(), dry_run=False)
    document = json.loads(settings.read_text(encoding="utf-8"))
    assert document["context"]["fileName"] == "A.md"
    assert document["sibling"] is True, "sibling settings keys must be preserved"

    # A missing settings file is a warning, never a create-and-guess.
    missing = dict(activation, settings_file="missing.json")
    log = SyncLog()
    _write_adapter_settings_activation(tmp_path, missing, log, dry_run=False)
    assert not (tmp_path / "missing.json").exists()
    assert log.warnings, "a missing settings file must be reported"

