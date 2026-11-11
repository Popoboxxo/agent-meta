"""Effective-topology render flags (G2, AC-15/AC-16/AC-21/AC-30).

Issue #1190, plan §5 Tasks 1 and 3.

``_effective_topology_flags`` reports the *resolved* position, not the
declaration:

    ORCH_TOPOLOGY_EFFECTIVE          resolution.effective (never "", never "none")
    ORCH_TOPOLOGY_EFFECTIVE_SOURCE   resolution.source (audit flag)
    ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT source != "derived" (Rev. 2, K-1)
    ORCH_TOPOLOGY_EFFECTIVE_{PRIMARY,SUBAGENT,HYBRID}
                                     exactly one is "true"
    ORCH_TOPOLOGY_INERT              "true" iff mode == "main-chat"

``ORCH_TOPOLOGY_EXPLICIT`` (from the unchanged ``_topology_flags``) keeps
answering "did the user write it?" and must not be conflated with the
effective flags. AC-21 pins the negative invariant: the mode never changes the
resolution.

Task 3 adds the global (provider-LESS) basis in
``config._build_orch_variables``. That dict is explicitly *non-authoritative*:
every provider-scoped render seam overwrites the seven flags via
``_provider_topology_flags`` (T4–T6). The AC-30 ratchet below fails if a render
seam starts reading (or importing) the global basis directly.

Run: python3 -m pytest tests/test_orchestrator_topology_effective_flags.py -q
"""
from __future__ import annotations

import ast
import inspect
import sys
from pathlib import Path

import pytest

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib import config as config_module  # noqa: E402
from scripts.lib.topology import (  # noqa: E402
    VALID_TOPOLOGIES,
    TopologyResolution,
    resolve_topology,
)
from scripts.lib.variables import (  # noqa: E402
    _effective_topology_flags,
    _topology_flags,
)

#: Provider-scoped render seams (plan §5 Tasks 4–6). From T4 onward they MUST
#: call the provider-aware helper; touching the global basis is AC-30 failure.
_RENDER_SEAMS = (
    "rules.py",
    "context.py",
    "agent_sync.py",
    "sync_pipeline.py",
    "agents.py",
    "isolation.py",
    "provider_transform.py",
)

#: The provider-less helper under ratchet — only ``config.py`` may call/import it.
_GLOBAL_BASIS_HELPER = "_effective_topology_flags"

_LIB_ROOT = _REPO_ROOT / "scripts" / "lib"

_POSITION_FLAGS = (
    "ORCH_TOPOLOGY_EFFECTIVE_PRIMARY",
    "ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT",
    "ORCH_TOPOLOGY_EFFECTIVE_HYBRID",
)

_ALL_MODES = ("strict", "advisory", "main-chat")

# (declared, effective, source) — one entry per position, at least one per
# source value, plus a declared-but-degraded case.
_TRIPLES = (
    (None, "primary", "derived"),
    (None, "subagent", "derived"),
    ("primary", "primary", "project"),
    ("subagent", "subagent", "provider-override"),
    ("hybrid", "hybrid", "project"),
    ("primary", "subagent", "project"),
)


def _resolution(declared, effective, source) -> TopologyResolution:
    degraded_from = declared if declared is not None and declared != effective else None
    return TopologyResolution(
        declared=declared,
        effective=effective,
        source=source,
        derived_from="providers.Claude.primary-role" if source == "derived" else None,
        degraded_from=degraded_from,
        degradation_reason=(
            f"degraded from {declared}" if degraded_from is not None else None
        ),
        verification_state="DOCUMENTED",
    )


def test_effective_flags_report_resolution_not_declaration():
    flags = {
        **_topology_flags("", explicit=False, source="derived"),
        **_effective_topology_flags(
            _resolution(None, "primary", "derived"), mode="strict"
        ),
    }

    assert flags["ORCH_TOPOLOGY_EFFECTIVE"] == "primary"
    assert flags["ORCH_TOPOLOGY_EXPLICIT"] == "false"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "true"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "derived"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT"] == "false"


def test_effective_topology_is_never_none():
    for declared, effective, source in _TRIPLES:
        flags = _effective_topology_flags(
            _resolution(declared, effective, source), mode="strict"
        )

        assert flags["ORCH_TOPOLOGY_EFFECTIVE"] in VALID_TOPOLOGIES, (
            declared,
            effective,
            source,
        )
        assert flags["ORCH_TOPOLOGY_EFFECTIVE"] != ""
        assert flags["ORCH_TOPOLOGY_EFFECTIVE"] != "none"


def test_exactly_one_position_flag_is_true():
    for declared, effective, source in _TRIPLES:
        flags = _effective_topology_flags(
            _resolution(declared, effective, source), mode="advisory"
        )

        values = [flags[flag] for flag in _POSITION_FLAGS]
        assert values.count("true") == 1, (declared, effective, source)
        assert all(value in {"true", "false"} for value in values)
        assert flags[f"ORCH_TOPOLOGY_EFFECTIVE_{effective.upper()}"] == "true"


def test_inert_is_true_only_for_main_chat():
    resolution = _resolution(None, "primary", "derived")

    for mode in _ALL_MODES:
        flags = _effective_topology_flags(resolution, mode=mode)
        expected = "true" if mode == "main-chat" else "false"
        assert flags["ORCH_TOPOLOGY_INERT"] == expected, mode


def test_resolve_topology_ignores_mode():
    config = {
        "orchestrator": {"provider-overrides": {"Claude": {"topology": "primary"}}}
    }
    provider_config = {"Claude": {"primary-role": "orchestrator"}}
    capabilities = {
        "topology_support": {"primary": True, "subagent": True, "hybrid": True},
        "topology_degrade": {"primary": None, "subagent": None, "hybrid": None},
        "topology_verified_state": {
            "primary": "DOCUMENTED",
            "subagent": "DOCUMENTED",
            "hybrid": "DOCUMENTED",
        },
    }

    resolutions = [
        resolve_topology(
            config,
            "Claude",
            provider_config=provider_config,
            capabilities=capabilities,
            mode=mode,
            active_set=None,
        )
        for mode in _ALL_MODES
    ]

    assert {resolution.effective for resolution in resolutions} == {"primary"}
    assert {resolution.source for resolution in resolutions} == {"provider-override"}


# --- Task 3: the provider-less (non-authoritative) global basis -------------


def _global_orch_vars(orchestrator_cfg: dict) -> dict:
    """Run the real global builder and return the produced variables dict."""
    variables: dict = {}
    config_module._build_orch_variables(
        variables,
        [],
        {"orchestrator": orchestrator_cfg},
        _REPO_ROOT,
        project_root=_REPO_ROOT,
    )
    return variables


def test_global_block_is_declared_or_failsafe():
    unset = _global_orch_vars({})

    assert unset["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert unset["ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT"] == "false"
    assert unset["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "false"
    assert unset["ORCH_TOPOLOGY_INERT"] == "false"
    assert unset["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "derived"
    # The declaration flags keep their IC-4 meaning and are not rewritten.
    assert unset["ORCH_TOPOLOGY"] == ""
    assert unset["ORCH_TOPOLOGY_EXPLICIT"] == "false"

    declared = _global_orch_vars({"topology": "primary"})

    assert declared["ORCH_TOPOLOGY_EFFECTIVE"] == "primary"
    assert declared["ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT"] == "true"
    assert declared["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "project"
    assert declared["ORCH_TOPOLOGY_EFFECTIVE_PRIMARY"] == "true"
    assert declared["ORCH_TOPOLOGY"] == "primary"
    assert declared["ORCH_TOPOLOGY_EXPLICIT"] == "true"

    # Unknown value fails safe to "subagent" here; the hard enum error stays in
    # _validate_orchestrator_topology.
    bogus = _global_orch_vars({"topology": "bogus"})

    assert bogus["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert bogus["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "true"
    assert bogus["ORCH_TOPOLOGY"] == ""  # _topology_flags fails closed


def test_global_block_honours_main_chat():
    flags = _global_orch_vars({"mode": "main-chat"})

    assert flags["ORCH_MODE_MAIN_CHAT"] == "true"
    assert flags["ORCH_TOPOLOGY_INERT"] == "true"
    # INERT expresses the main-chat case; the position basis is unchanged.
    assert flags["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_SUBAGENT"] == "true"


def test_global_block_is_documented_as_non_authoritative():
    source = inspect.getsource(config_module._build_orch_variables)

    assert "non-authoritative basis" in source, (
        "the global basis block must be documented as non-authoritative "
        "(RVW2-1190-09) so no seam treats it as a provider resolution"
    )

    # The produced values are the fail-safe basis, not a provider resolution:
    # a provider override must never leak into the provider-less dict.
    flags = _global_orch_vars(
        {"provider-overrides": {"Claude": {"topology": "primary"}}}
    )

    assert flags["ORCH_TOPOLOGY_EFFECTIVE"] == "subagent"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT"] == "false"
    assert flags["ORCH_TOPOLOGY_EFFECTIVE_SOURCE"] == "derived"
    assert flags["ORCH_TOPOLOGY"] == ""


def _basis_references(path: Path) -> tuple[list[int], list[int]]:
    """Return (call line numbers, import line numbers) for the global helper."""
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    calls: list[int] = []
    imports: list[int] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            is_basis_call = (
                isinstance(func, ast.Name) and func.id == _GLOBAL_BASIS_HELPER
            ) or (
                isinstance(func, ast.Attribute)
                and func.attr == _GLOBAL_BASIS_HELPER
            )
            if is_basis_call:
                calls.append(node.lineno)
        elif isinstance(node, ast.ImportFrom):
            for alias in node.names:
                if alias.name == _GLOBAL_BASIS_HELPER:
                    imports.append(node.lineno)
    return calls, imports


def test_no_render_seam_reads_the_global_basis():
    """AC-30 ratchet: only config.py may consume the provider-less basis."""
    definition = (_LIB_ROOT / "variables.py").read_text(encoding="utf-8")
    assert f"def {_GLOBAL_BASIS_HELPER}(" in definition, (
        "ratchet target vanished from variables.py — update the ratchet with "
        "the new helper name instead of deleting it"
    )

    callers: dict[str, list[int]] = {}
    importers: dict[str, list[int]] = {}
    for path in sorted(_LIB_ROOT.rglob("*.py")):
        rel = path.relative_to(_LIB_ROOT).as_posix()
        if rel == "variables.py":  # the definition itself
            continue
        calls, imports = _basis_references(path)
        if calls:
            callers[rel] = calls
        if imports:
            importers[rel] = imports

    assert list(callers) == ["config.py"], (
        f"only the global builder may call {_GLOBAL_BASIS_HELPER}; "
        f"render seams must use _provider_topology_flags. Found: {callers}"
    )
    assert list(importers) == ["config.py"], (
        f"only the global builder may import {_GLOBAL_BASIS_HELPER}; "
        f"direct imports bypass the provider override. Found: {importers}"
    )

    # Explicit per-seam pin: a seam must neither call nor import the basis.
    for seam in _RENDER_SEAMS:
        assert seam not in callers, (
            f"render seam {seam} calls the provider-less "
            f"{_GLOBAL_BASIS_HELPER} — use _provider_topology_flags (AC-30)"
        )
        assert seam not in importers, (
            f"render seam {seam} imports the provider-less "
            f"{_GLOBAL_BASIS_HELPER} — use _provider_topology_flags (AC-30)"
        )



# --- Task 21: end-state byte identity (AC-16/AC-27) ------------------------

_TOPOLOGY_GOLDEN = _REPO_ROOT / "tests" / "fixtures" / "topology-golden"
_ORCHESTRATOR_TEMPLATE = _REPO_ROOT / "agents" / "1-generic" / "orchestrator.md"

#: Sentinel for "the project does not write the key" (the derived state).
_UNSET = object()

#: The baseline commit of the plan (§2 M0): the template BEFORE the topology
#: gate was introduced. ``orchestrator.unset-derived-subagent.<provider>.md``
#: freezes that source rendered with the CURRENT renderer.
_BASELINE_TEMPLATE_COMMIT = "aaed14c2"

#: The baseline source is frozen as a committed fixture: ``git show`` exits 128
#: on a shallow CI clone, so the test must never depend on repository history.
_BASELINE_TEMPLATE_FIXTURE = (
    _TOPOLOGY_GOLDEN / f"baseline-{_BASELINE_TEMPLATE_COMMIT}-orchestrator.md"
)

#: Frontmatter lines that legitimately move with a template release. The body
#: (everything after the closing ``---``) must stay byte-identical.
_VOLATILE_FRONTMATTER_KEYS = ("version", "generated-from")


def orchestrator_template_at(commit: str) -> str:
    """Return the orchestrator template frozen for *commit* (baseline source).

    Reads the committed fixture
    ``tests/fixtures/topology-golden/baseline-<commit>-orchestrator.md`` instead
    of ``git show <commit>:agents/1-generic/orchestrator.md`` — a shallow CI
    clone carries no history for the baseline commit.
    """
    fixture = _TOPOLOGY_GOLDEN / f"baseline-{commit}-orchestrator.md"
    assert fixture.is_file(), (
        f"missing committed baseline fixture {fixture.relative_to(_REPO_ROOT).as_posix()} — "
        f"generate it once with `git show "
        f"{_BASELINE_TEMPLATE_COMMIT}:agents/1-generic/orchestrator.md` in a full clone"
    )
    return fixture.read_text(encoding="utf-8")


def _provider_config(provider: str, config: dict):
    from scripts.lib.providers import load_providers_config

    provider_config = load_providers_config(_REPO_ROOT, config)
    if provider not in provider_config:  # pragma: no cover - guard for config edits
        raise AssertionError(f"provider {provider!r} not in ai-providers registry")
    return provider_config


def render_orchestrator(
    provider: str,
    project_root: Path,
    *,
    template_text: str | None = None,
    topology=_UNSET,
    active_set=frozenset(),
) -> str:
    """Render ``agents/1-generic/orchestrator.md`` through the real sync path.

    Mirrors ``sync_agents_for_provider`` for ONE role without writing into the
    repository (everything lands in *project_root*). *topology* overrides the
    project declaration: the ``_UNSET`` sentinel REMOVES the key, which is the
    derived state (all ``ORCH_TOPOLOGY_*`` declaration flags fail closed).

    *template_text* renders arbitrary template bytes through the SAME pipeline
    (used to replay the ``aaed14c2`` baseline with the current renderer);
    ``None`` reads the working-tree template.
    """
    import copy

    from scripts.lib.agent_sync import (
        _apply_content_pipeline,
        _build_provider_vars,
        _finalize_agent_content,
        _parse_frontmatter_yaml,
        _resolve_sync_targets,
        _tools_can_spawn,
    )
    from scripts.lib.config import build_variables, load_config
    from scripts.lib.frontmatter import extract_frontmatter_field
    from scripts.lib.log import SyncLog

    project_root = Path(project_root)
    project_root.mkdir(parents=True, exist_ok=True)

    config = copy.deepcopy(load_config(_REPO_ROOT / ".meta-config" / "project.yaml"))
    orchestrator_cfg = dict(config.get("orchestrator") or {})
    if topology is _UNSET:
        orchestrator_cfg.pop("topology", None)
    else:
        orchestrator_cfg["topology"] = topology
    config["orchestrator"] = orchestrator_cfg

    text = (
        template_text
        if template_text is not None
        else _ORCHESTRATOR_TEMPLATE.read_text(encoding="utf-8")
    )
    lead, _sep, _body = text.partition("\n---")
    assert lead.startswith("---"), "orchestrator template lost its frontmatter"

    variables, _warnings = build_variables(config, _REPO_ROOT, project_root)
    provider_config = _provider_config(provider, config)
    log = SyncLog()
    pc, _role_map, _overrides, target_dir = _resolve_sync_targets(
        provider, provider_config, _REPO_ROOT, project_root, config, True, log
    )
    assert pc is not None, f"{provider} provider config missing"

    source_path = _ORCHESTRATOR_TEMPLATE
    target_path = target_dir / "orchestrator.md"
    can_spawn = _tools_can_spawn(_parse_frontmatter_yaml(text).get("tools"))
    source_version = extract_frontmatter_field(text, "version")
    description = (
        extract_frontmatter_field(text, "description") or "Orchestrator fixture."
    )

    details_dir = f".{provider.lower()}/pipeline-details"
    variables.setdefault("PIPELINE_DETAILS_DIR", details_dir)
    merged = _build_provider_vars(
        pc, provider, variables, _REPO_ROOT, config=config, active_set=active_set
    )
    merged.setdefault("PIPELINE_DETAILS_DIR", details_dir)

    content = _apply_content_pipeline(
        text, config, provider, merged,
        "agents/1-generic/orchestrator.md", None, _REPO_ROOT, log,
    )
    return _finalize_agent_content(
        content, "orchestrator", "orchestrator.md", source_path, provider,
        provider_config, source_version, description, can_spawn, config,
        _REPO_ROOT, project_root, target_path, variables, False, log,
        active_set=active_set,
    )


def _split_frontmatter(text: str) -> tuple[str, str]:
    assert text.startswith("---\n")
    end = text.index("\n---\n", 3)
    return text[4:end], text[end + 5:]


def _frontmatter_delta(expected: str, actual: str) -> list[tuple[str, str]]:
    """Return the ``(expected_line, actual_line)`` pairs of the frontmatter diff."""
    import difflib

    expected_fm, _ = _split_frontmatter(expected)
    actual_fm, _ = _split_frontmatter(actual)
    pairs: list[tuple[str, str]] = []
    for line in difflib.ndiff(expected_fm.splitlines(), actual_fm.splitlines()):
        if line.startswith("- "):
            pairs.append((line[2:], ""))
        elif line.startswith("+ "):
            if pairs and pairs[-1][1] == "":
                pairs[-1] = (pairs[-1][0], line[2:])
            else:
                pairs.append(("", line[2:]))
    return pairs


def _assert_body_identity(baseline: str, current: str) -> None:
    """AC-16/AC-27: only the two version pins may differ, the body never does."""
    _, baseline_body = _split_frontmatter(baseline)
    _, current_body = _split_frontmatter(current)
    assert baseline_body == current_body, (
        "an unset `orchestrator.topology` (derived subagent) changed the "
        "rendered body of the orchestrator — the topology gate must be a "
        "no-op in that state (AC-16/AC-27)"
    )

    delta = _frontmatter_delta(baseline, current)
    assert delta, "expected the two release pins to differ in the frontmatter"
    keys = [line.split(":", 1)[0] for line, _ in delta]
    assert keys == list(_VOLATILE_FRONTMATTER_KEYS), (
        "an unset topology may only move `version` and `generated-from` in the "
        f"frontmatter; unexpected delta: {delta!r}"
    )


_ACTIVE_PROVIDERS = ("Claude", "Opencode", "Gemini")


@pytest.mark.parametrize("provider", _ACTIVE_PROVIDERS)
def test_unset_topology_subagent_render_is_byte_identical(provider, tmp_path):
    """AC-16/AC-27: declaring nothing renders the pre-topology bytes.

    The fixture is the ``aaed14c2`` template replayed through the CURRENT
    renderer (never hand-written). The working-tree template must produce the
    same body for every active provider when the key is missing and the
    provider's ``primary-role`` is absent from the ActiveSet (derived
    ``subagent``).
    """
    golden_path = _TOPOLOGY_GOLDEN / f"orchestrator.unset-derived-subagent.{provider.lower()}.md"
    assert golden_path.is_file(), (
        f"missing frozen baseline {golden_path.name} — regenerate it by replaying "
        f"the committed fixture "
        f"`{_BASELINE_TEMPLATE_FIXTURE.relative_to(_REPO_ROOT).as_posix()}` "
        "through render_orchestrator(provider, ...)"
    )
    baseline = golden_path.read_text(encoding="utf-8")

    current = render_orchestrator(provider, tmp_path / "current")
    _assert_body_identity(baseline, current)

    # The state under test really is "derived subagent": the else branch of
    # both conditionals (neither primary nor explicit) must have rendered.
    _, body = _split_frontmatter(current)
    assert "**Singleton:** Self-spawn" in body, (
        f"{provider}: the unset-key/derived state did not render the legacy "
        "singleton branch — the byte-identity claim would be vacuous"
    )
    assert "**Singleton (session entry):**" not in body
    assert "**Singleton (subagent):**" not in body


def test_frozen_baseline_fixture_replays_the_baseline_template(tmp_path):
    """The fixture really is ``aaed14c2`` + current renderer (no hand edits).

    Replays the committed ``baseline-aaed14c2-orchestrator.md`` fixture through
    the CURRENT renderer and requires byte identity with the frozen
    ``orchestrator.unset-derived-subagent.claude.md`` golden. No repository
    history is read, so the check also runs on a shallow CI clone.
    """
    baseline_source = orchestrator_template_at(_BASELINE_TEMPLATE_COMMIT)
    replayed = render_orchestrator("Claude", tmp_path / "replay", template_text=baseline_source)
    frozen = (
        _TOPOLOGY_GOLDEN / "orchestrator.unset-derived-subagent.claude.md"
    ).read_text(encoding="utf-8")
    assert replayed == frozen, (
        "the frozen baseline fixture drifted from the committed fixture "
        f"`{_BASELINE_TEMPLATE_FIXTURE.relative_to(_REPO_ROOT).as_posix()}` "
        "rendered with the current renderer"
    )


def test_default_effective_is_primary_or_subagent():
    """AC-16: the effective position is always a real position, never empty.

    Covers the provider-less default basis (the repo's own declared config) and
    the provider-scoped resolution for every active provider, with the key
    unset (both derived outcomes) and declared.
    """
    import copy

    from scripts.lib.config import load_config
    from scripts.lib.variables import _provider_topology_flags

    variables, _ = config_module.build_variables(
        load_config(_REPO_ROOT / ".meta-config" / "project.yaml"),
        _REPO_ROOT,
        _REPO_ROOT,
    )
    assert variables["ORCH_TOPOLOGY_EFFECTIVE"] in {"primary", "subagent"}
    assert variables["ORCH_TOPOLOGY_EFFECTIVE"] not in {"", "none", "hybrid"}

    unset = copy.deepcopy(load_config(_REPO_ROOT / ".meta-config" / "project.yaml"))
    orchestrator_cfg = dict(unset.get("orchestrator") or {})
    orchestrator_cfg.pop("topology", None)
    unset["orchestrator"] = orchestrator_cfg

    for provider in _ACTIVE_PROVIDERS:
        for active_set in (frozenset({"orchestrator"}), frozenset()):
            flags = _provider_topology_flags(
                unset, provider, agent_meta_root=_REPO_ROOT,
                mode="strict", active_set=active_set,
            )
            assert flags["ORCH_TOPOLOGY_EFFECTIVE"] in {"primary", "subagent"}, (
                provider, active_set, flags["ORCH_TOPOLOGY_EFFECTIVE"]
            )
            assert flags["ORCH_TOPOLOGY_EFFECTIVE"] not in {"", "none", "hybrid"}
