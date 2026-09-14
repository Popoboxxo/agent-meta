"""Phase-0 `unified` determinism for shared context files.

Covers SPEC-CONTEXT-FILE-MODES-2026-09-13 (AC-01 … AC-04, AC-08, AC-25): a
physical ``context_file`` shared by more than one active provider must render
exactly one deterministic ``GATE_*`` bundle — the **weakest** tier over its
active sharers (``advisory < permission < plugin < hook``) — so the second sharer
write is a byte-identical no-op and ``sync.py --check`` converges.

Run: python -m pytest tests/test_context_file_modes.py -v
"""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import load_config
from lib.context import _build_managed_block
from lib.log import SyncLog
from lib.providers import (
    load_provider_capabilities,
    load_providers_config,
    provider_runtime_gate_tier,
    runtime_gate_vars,
    shared_runtime_gate_vars,
)
from lib.runtime_gate import RUNTIME_GATE_TIER_RANK, weakest_runtime_gate_tier

# The real AGENTS.md sharer set declared in config/ai-providers.yaml.
_AGENTS_MD_SHARERS = ("Opencode", "Gemini", "Codex", "ZCode", "KimiCode")
_ACTIVE_AGENTS_MD_SHARERS = ("Opencode", "Gemini")

_GATE_KEYS = {
    "ENFORCEMENT_TIER",
    "GATE_ENFORCED",
    "GATE_PARTIAL",
    "GATE_ADVISORY",
    "RUNTIME_GATE_PLUGIN_MODE",
}


@pytest.fixture
def loaded_config():
    config = load_config(_REPO_ROOT / ".meta-config" / "project.yaml")
    provider_config = load_providers_config(_REPO_ROOT)
    capabilities = load_provider_capabilities(_REPO_ROOT)
    return config, provider_config, capabilities


def _per_provider_vars(config: dict, pc: dict, caps: dict) -> dict:
    """Mirror sync_pipeline's IC-04 injection for one provider."""
    variables = dict(config.get("variables", {}))
    variables.update(runtime_gate_vars(pc, caps, config))
    return variables


# --- AC-01: weakest-tier vocabulary and fail-safe -------------------------


def test_rank_orders_advisory_permission_plugin_hook():
    """AC-01: RUNTIME_GATE_TIER_RANK is weak -> strong."""
    assert (
        RUNTIME_GATE_TIER_RANK["advisory"]
        < RUNTIME_GATE_TIER_RANK["permission"]
        < RUNTIME_GATE_TIER_RANK["plugin"]
        < RUNTIME_GATE_TIER_RANK["hook"]
    )


@pytest.mark.parametrize(
    "tiers, expected",
    [
        (["hook", "permission"], "permission"),
        (["permission", "hook"], "permission"),
        (["advisory"], "advisory"),
        (["hook", "plugin", "permission", "advisory"], "advisory"),
        ([], "advisory"),
        (None, "advisory"),
        (["unknown", "bogus"], "advisory"),
        (["hook", "unknown"], "hook"),
        (5, "advisory"),
        # CR-06: a bare tier-name string is a single tier, not iterated per char.
        ("hook", "hook"),
        ("advisory", "advisory"),
        ("bogus", "advisory"),
    ],
)
def test_weakest_runtime_gate_tier(tiers, expected):
    """AC-01: fail-safe minimum; empty/None/unknown/non-iterable -> advisory."""
    assert weakest_runtime_gate_tier(tiers) == expected


# --- AC-02: shared-tier resolver ------------------------------------------


def _synthetic_registry():
    provider_config = {
        "PermProvider": {"has_hooks": False},
        "HookProvider": {
            "has_hooks": True,
            "hook_protocol": "claude-code-json",
        },
    }
    capabilities = {
        "PermProvider": {"runtime_gate": "permission"},
        "HookProvider": {"runtime_gate": "hook"},
    }
    return provider_config, capabilities


def test_shared_runtime_gate_vars_returns_weakest_bundle():
    """AC-02: permission + hook sharers resolve to the permission bundle."""
    provider_config, capabilities = _synthetic_registry()
    bundle = shared_runtime_gate_vars(
        ["PermProvider", "HookProvider"], provider_config, capabilities, {}
    )
    assert set(bundle) == _GATE_KEYS
    assert all(isinstance(v, str) for v in bundle.values())
    assert bundle["ENFORCEMENT_TIER"] == "permission"
    assert bundle["GATE_PARTIAL"] == "true"
    assert bundle["GATE_ENFORCED"] == "false"
    assert bundle["GATE_ADVISORY"] == "false"


def test_shared_runtime_gate_vars_failsafe_never_raises():
    """AC-02: missing/non-dict entries degrade to advisory, never KeyError."""
    provider_config, capabilities = _synthetic_registry()
    assert (
        shared_runtime_gate_vars(["Absent"], provider_config, capabilities, {})[
            "ENFORCEMENT_TIER"
        ]
        == "advisory"
    )
    assert (
        shared_runtime_gate_vars(
            ["Absent"], {"Absent": "not-a-mapping"}, capabilities, {}
        )["ENFORCEMENT_TIER"]
        == "advisory"
    )
    # Non-mapping registries / missing capabilities never raise.
    assert (
        shared_runtime_gate_vars(["X"], None, None, None)["ENFORCEMENT_TIER"]
        == "advisory"
    )
    assert (
        shared_runtime_gate_vars([], provider_config, capabilities, {})[
            "ENFORCEMENT_TIER"
        ]
        == "advisory"
    )
    assert (
        shared_runtime_gate_vars(None, provider_config, capabilities, {})[
            "ENFORCEMENT_TIER"
        ]
        == "advisory"
    )
    assert (
        shared_runtime_gate_vars(["Absent"], provider_config, capabilities, {
            "runtime-gate": {"plugin-mode": "bogus"}
        })["RUNTIME_GATE_PLUGIN_MODE"]
        == "observe"
    )


# --- AC-03: shared override makes renders byte-identical ------------------


def test_shared_managed_block_identical_with_gate_vars(loaded_config):
    """AC-03: with the real per-sharer GATE_* vars the renders are identical.

    The render must carry the permission (GATE_PARTIAL) variant — not the hook
    (GATE_ENFORCED) variant — for the shared AGENTS.md group.
    """
    config, provider_config, capabilities = loaded_config
    renders = {}
    for provider in _AGENTS_MD_SHARERS:
        pc = provider_config.get(provider, {})
        variables = _per_provider_vars(config, pc, capabilities.get(provider, {}))
        renders[provider] = _build_managed_block(
            _REPO_ROOT,
            config,
            variables,
            SyncLog(),
            provider=provider,
            provider_config=provider_config,
            project_root=_REPO_ROOT,
        )

    baseline = renders[_AGENTS_MD_SHARERS[0]]
    diverged = [p for p, block in renders.items() if block != baseline]
    assert not diverged, (
        f"AGENTS.md sharers {diverged} render a different managed block than "
        f"{_AGENTS_MD_SHARERS[0]} even with real GATE_* vars injected"
    )
    assert "runtime-partially enforced" in baseline
    assert "NICHT erzwungen" in baseline
    assert "Keine Ausnahmen" not in baseline


# --- AC-04: effective shared tier is the weakest ACTIVE sharer ------------


def test_effective_shared_tier_is_weakest_active_sharer(loaded_config):
    """AC-04: active {Opencode, Gemini} -> permission; inactive advisory do not lower it."""
    config, provider_config, capabilities = loaded_config

    from lib.providers import resolve_providers

    active = set(resolve_providers(config, provider_config))
    assert {"Opencode", "Gemini"} <= active

    shared_users = [
        p for p in _AGENTS_MD_SHARERS
        if provider_config.get(p, {}).get("context_file") == "AGENTS.md"
    ]
    active_shared = [p for p in shared_users if p in active]
    assert set(active_shared) == set(_ACTIVE_AGENTS_MD_SHARERS)
    assert len(active_shared) == 2

    active_bundle = shared_runtime_gate_vars(
        active_shared, provider_config, capabilities, config
    )
    assert active_bundle["ENFORCEMENT_TIER"] == "permission"

    # The configured-but-inactive advisory sharers must NOT lower the tier to
    # advisory (they read the file in this project, so they are not sharers).
    all_bundle = shared_runtime_gate_vars(
        shared_users, provider_config, capabilities, config
    )
    assert all_bundle["ENFORCEMENT_TIER"] == "advisory"
    assert (
        provider_runtime_gate_tier(
            provider_config["Codex"], capabilities.get("Codex", {})
        )
        == "advisory"
    )


# --- AC-08: runtime_gate_vars contract unchanged --------------------------


@pytest.mark.parametrize(
    "pc, capabilities, config, expected",
    [
        (
            {"has_hooks": True, "hook_protocol": "claude-code-json"},
            {},
            {},
            {
                "ENFORCEMENT_TIER": "hook",
                "GATE_ENFORCED": "true",
                "GATE_PARTIAL": "false",
                "GATE_ADVISORY": "false",
                "RUNTIME_GATE_PLUGIN_MODE": "observe",
            },
        ),
        (
            {"has_plugins": True, "plugin_protocol": "opencode-plugin-js"},
            {},
            {},
            {
                "ENFORCEMENT_TIER": "plugin",
                "GATE_ENFORCED": "true",
                "GATE_PARTIAL": "false",
                "GATE_ADVISORY": "false",
                "RUNTIME_GATE_PLUGIN_MODE": "observe",
            },
        ),
        (
            {},
            {"runtime_gate": "permission"},
            {"runtime-gate": {"plugin-mode": "enforce"}},
            {
                "ENFORCEMENT_TIER": "permission",
                "GATE_ENFORCED": "false",
                "GATE_PARTIAL": "true",
                "GATE_ADVISORY": "false",
                "RUNTIME_GATE_PLUGIN_MODE": "enforce",
            },
        ),
        (
            {},
            {},
            None,
            {
                "ENFORCEMENT_TIER": "advisory",
                "GATE_ENFORCED": "false",
                "GATE_PARTIAL": "false",
                "GATE_ADVISORY": "true",
                "RUNTIME_GATE_PLUGIN_MODE": "observe",
            },
        ),
    ],
)
def test_runtime_gate_vars_output_unchanged(pc, capabilities, config, expected):
    """AC-08: the pre-refactor byte output is preserved exactly."""
    assert runtime_gate_vars(pc, capabilities, config) == expected


# --- AC-25: determinism scope — only GATE_* is neutralised ----------------


def test_gate_only_neutralised_orch_mode_still_diverges(loaded_config):
    """AC-25: divergent ORCH_MODE_* still differ (outside the guarantee).

    Only the GATE_* family is neutralised by IC-03; a divergent non-gate
    provider-scoped input (``orchestrator.provider-overrides.<P>.mode``) keeps
    the two renders apart. ``ORCHESTRATOR_INVOCATION_HINT`` is unrendered and
    therefore cannot be a divergence source.
    """
    import copy

    config, provider_config, capabilities = loaded_config

    def _render(provider: str, cfg: dict) -> str:
        pc = provider_config.get(provider, {})
        variables = _per_provider_vars(cfg, pc, capabilities.get(provider, {}))
        return _build_managed_block(
            _REPO_ROOT,
            cfg,
            variables,
            SyncLog(),
            provider=provider,
            provider_config=provider_config,
            project_root=_REPO_ROOT,
        )

    baseline = _render("Opencode", config)
    assert baseline == _render("Gemini", config)

    # Divergent provider-override mode -> renders differ (outside IC-03 scope).
    # The repo default orchestrator mode is ``strict``; give Gemini a divergent
    # ``advisory`` override so the two ORCH_MODE_* flag sets differ.
    divergent = copy.deepcopy(config)
    divergent.setdefault("orchestrator", {}).setdefault(
        "provider-overrides", {}
    ).setdefault("Gemini", {})["mode"] = "advisory"
    assert _render("Opencode", divergent) != _render("Gemini", divergent)

    # ORCHESTRATOR_INVOCATION_HINT differs but is unrendered: no divergence.
    hint_config = copy.deepcopy(config)
    op = copy.deepcopy(provider_config)
    op["Gemini"]["orchestrator_hint"] = "UNIQUE-GEMINI-HINT-SENTINEL"
    op["Opencode"]["orchestrator_hint"] = "UNIQUE-OPENCODE-HINT-SENTINEL"

    def _render_with(op_cfg: dict, provider: str) -> str:
        pc = op_cfg.get(provider, {})
        variables = _per_provider_vars(config, pc, capabilities.get(provider, {}))
        return _build_managed_block(
            _REPO_ROOT, hint_config, variables, SyncLog(),
            provider=provider, provider_config=op_cfg, project_root=_REPO_ROOT,
        )

    assert "UNIQUE-GEMINI-HINT-SENTINEL" not in _render_with(op, "Gemini")
    assert "UNIQUE-OPENCODE-HINT-SENTINEL" not in _render_with(op, "Opencode")
    assert _render_with(op, "Gemini") == _render_with(op, "Opencode")


# ``_build_managed_block`` assigns a few provider-scoped ``local_vars`` beyond
# the gate bundle. Two of them never count as rendered divergence sources:
#
# * ``ORCHESTRATOR_INVOCATION_HINT`` — assigned from ``pc["orchestrator_hint"]``
#   but no rule/template consumes it (N-01), so it cannot make renders differ.
# * ``embedded_rules`` — the pre-rendered rule aggregate whose content diverges
#   *because of* the families below, not as an input of its own.
_DERIVED_DIVERGENCE_KEYS = {"embedded_rules"}
_UNRENDERED_PROVIDER_SCOPED = {"ORCHESTRATOR_INVOCATION_HINT"}


def _provider_scope_family(name: str) -> str:
    """Fold a provider-scoped variable name onto its ``ORCH_MODE``/``REPO_`` family."""
    if name.startswith("ORCH_MODE_"):
        return "ORCH_MODE"
    if name.startswith("REPO_CONTAINMENT_"):
        return "REPO_CONTAINMENT"
    return name


def _provider_scoped_local_var_diff(monkeypatch, loaded_config, cfg) -> set:
    """Keys of ``local_vars`` whose value differs between the two sharers.

    Captures the final ``local_vars`` handed to ``TemplateBuilder.build`` for
    each provider — every provider-scoped input of the shared managed block
    before template resolution. Callers subtract ``_DERIVED_DIVERGENCE_KEYS``
    and ``_UNRENDERED_PROVIDER_SCOPED`` to assert the *rendered* scope.
    """
    from lib.context_templates.builder import TemplateBuilder

    _, provider_config, capabilities = loaded_config

    def _capture(provider: str) -> dict:
        box: dict = {}
        real_build = TemplateBuilder.build

        def _wrap(self, template_name, variables):
            box.clear()
            box.update(variables)
            return real_build(self, template_name, variables)

        with monkeypatch.context() as patch:
            patch.setattr(TemplateBuilder, "build", _wrap)
            variables = _per_provider_vars(
                cfg,
                provider_config.get(provider, {}),
                capabilities.get(provider, {}),
            )
            _build_managed_block(
                _REPO_ROOT,
                cfg,
                variables,
                SyncLog(),
                provider=provider,
                provider_config=provider_config,
                project_root=_REPO_ROOT,
            )
        return box

    opencode = _capture("Opencode")
    gemini = _capture("Gemini")
    keys = set(opencode) | set(gemini)
    return {k for k in keys if opencode.get(k) != gemini.get(k)}


def test_gate_only_neutralised_repo_containment_still_diverges(
    loaded_config, monkeypatch
):
    """AC-25: divergent ``REPO_CONTAINMENT_*`` differs (outside the guarantee).

    IC-03 neutralises the ``GATE_*`` family only. A provider-scoped
    repo-containment override
    (``repo_containment.provider-overrides.<P>.enabled``) is still rendered
    per-provider, so the two shared renders differ — explicitly outside the
    determinism guarantee (R7, OQ-13). Together with
    ``orchestrator.provider-overrides.<P>.mode`` these are the *sole remaining
    rendered* provider-scoped inputs; ``ORCHESTRATOR_INVOCATION_HINT`` is
    assigned but unrendered (N-01).
    """
    import copy

    config, provider_config, capabilities = loaded_config

    def _render(provider: str, cfg: dict, extra_vars: dict | None = None) -> str:
        variables = _per_provider_vars(
            cfg, provider_config.get(provider, {}), capabilities.get(provider, {})
        )
        if extra_vars:
            variables.update(extra_vars)
        return _build_managed_block(
            _REPO_ROOT,
            cfg,
            variables,
            SyncLog(),
            provider=provider,
            provider_config=provider_config,
            project_root=_REPO_ROOT,
        )

    # Baseline: identical provider-scoped config -> byte-identical render.
    assert _render("Opencode", config) == _render("Gemini", config)

    # GATE_* are neutralised: divergent per-provider gate bundles injected via
    # the IC-04 seam cannot make the shared render differ.
    divergent_gate = {
        "Opencode": {
            "ENFORCEMENT_TIER": "hook",
            "GATE_ENFORCED": "true",
            "GATE_PARTIAL": "false",
            "GATE_ADVISORY": "false",
            "RUNTIME_GATE_PLUGIN_MODE": "observe",
        },
        "Gemini": {
            "ENFORCEMENT_TIER": "advisory",
            "GATE_ENFORCED": "false",
            "GATE_PARTIAL": "false",
            "GATE_ADVISORY": "true",
            "RUNTIME_GATE_PLUGIN_MODE": "observe",
        },
    }
    assert (
        _render("Opencode", config, divergent_gate["Opencode"])
        == _render("Gemini", config, divergent_gate["Gemini"])
    )

    # Scope of the guarantee: with GATE_* neutralised, no *rendered*
    # provider-scoped input diverges at baseline. The only per-provider
    # ``local_vars`` difference is the unrendered ORCHESTRATOR_INVOCATION_HINT.
    baseline_rendered = (
        _provider_scoped_local_var_diff(monkeypatch, loaded_config, config)
        - _UNRENDERED_PROVIDER_SCOPED
        - _DERIVED_DIVERGENCE_KEYS
    )
    assert baseline_rendered == set(), (
        "no rendered provider-scoped input may diverge once GATE_* is neutralised"
    )

    # Divergent repo-containment override -> the renders differ (outside scope).
    rc_divergent = copy.deepcopy(config)
    rc_divergent.setdefault("repo_containment", {}).setdefault(
        "provider-overrides", {}
    ).setdefault("Gemini", {})["enabled"] = False
    assert _render("Opencode", rc_divergent) != _render("Gemini", rc_divergent)

    rc_diff = (
        _provider_scoped_local_var_diff(monkeypatch, loaded_config, rc_divergent)
        - _UNRENDERED_PROVIDER_SCOPED
        - _DERIVED_DIVERGENCE_KEYS
    )
    assert rc_diff and all(k.startswith("REPO_CONTAINMENT_") for k in rc_diff)

    # Divergent ORCH mode override -> the renders differ (existing AC-25 case).
    orch_divergent = copy.deepcopy(config)
    orch_divergent.setdefault("orchestrator", {}).setdefault(
        "provider-overrides", {}
    ).setdefault("Gemini", {})["mode"] = "advisory"
    assert _render("Opencode", orch_divergent) != _render("Gemini", orch_divergent)

    orch_diff = (
        _provider_scoped_local_var_diff(monkeypatch, loaded_config, orch_divergent)
        - _UNRENDERED_PROVIDER_SCOPED
        - _DERIVED_DIVERGENCE_KEYS
    )
    assert orch_diff and all(k.startswith("ORCH_MODE_") for k in orch_diff)

    # SOLE remaining rendered provider-scoped inputs: the two divergence
    # sources above are exactly the ORCH_MODE_* and REPO_CONTAINMENT_* families
    # (context.py:1165 / :1170). Nothing else is a rendered provider-scoped
    # input that a config can push apart.
    assert {
        _provider_scope_family(name) for name in (rc_diff | orch_diff)
    } == {"ORCH_MODE", "REPO_CONTAINMENT"}, (
        "ORCH_MODE_* and REPO_CONTAINMENT_* must be the sole remaining rendered "
        "provider-scoped inputs after IC-03 neutralises GATE_*"
    )


# --- AC-05: single render / no double write -------------------------------


def test_single_agents_md_managed_block_write_per_sync_run(tmp_path, loaded_config):
    """AC-05: exactly one UPDATE for AGENTS.md, later active sharers skip.

    A second dry-run pass then reports no pending AGENTS.md change for any
    active sharer — the observable proxy for ``sync.py --check`` convergence
    (the real rc0 check follows after the HITL-approved sync).
    """
    import shutil

    from lib.context import sync_context_for_provider

    config, provider_config, capabilities = loaded_config
    project_root = tmp_path
    shutil.copy(_REPO_ROOT / "AGENTS.md", project_root / "AGENTS.md")

    def _managed_updates(log: SyncLog) -> list:
        return [a for a in log.actions if "AGENTS.md" in a and "managed block" in a]

    def _managed_skips(log: SyncLog) -> list:
        return [
            s for s in log.skipped if "AGENTS.md" in s and "managed block" in s
        ]

    def _sync(provider: str, dry_run: bool) -> SyncLog:
        variables = _per_provider_vars(
            config,
            provider_config.get(provider, {}),
            capabilities.get(provider, {}),
        )
        log = SyncLog()
        sync_context_for_provider(
            _REPO_ROOT, project_root, config, variables, log,
            dry_run=dry_run, provider=provider, provider_config=provider_config,
        )
        return log

    first_run = {p: _sync(p, dry_run=False) for p in _ACTIVE_AGENTS_MD_SHARERS}
    writers = [p for p, log in first_run.items() if _managed_updates(log)]
    assert len(writers) == 1, (
        f"expected exactly one AGENTS.md managed-block write, got {writers}"
    )
    later = [p for p in _ACTIVE_AGENTS_MD_SHARERS if p != writers[0]]
    assert later and all(_managed_skips(first_run[p]) for p in later), (
        "every sharer after the single writer must log a no-op skip"
    )

    for provider in _ACTIVE_AGENTS_MD_SHARERS:
        assert not _managed_updates(_sync(provider, dry_run=True)), (
            f"{provider}: dry-run reports AGENTS.md as changed after convergence"
        )

