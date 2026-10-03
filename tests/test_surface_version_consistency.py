"""Cross-layer consistency gate for the project-level ``surface-version`` channel.

SPEC-ADMIN-UI-OPENCODE-SURFACE-AMENDMENT-2026-10-03 (plan Task 5, AC-A2/AC-A3,
REV-R2/REV-R5). Trace anchor ``REQ-PROV-01`` (data-driven, no provider-name
branch): the generation path
(``lib.sync_pipeline._sync_stage_config_and_presets``) and the check path
(``lib.agent_sync.collect_artifact_findings`` / the consistency checks) both
resolve the provider registry through the single
``lib.providers.load_providers_config(root, project_config)`` entry point, so a
project that opts into v2 through ``provider-options.<Provider>.surface-version``
cannot be generated as v2 while being validated as v1.

This file is intentionally self-contained: every provider is synthetic and
lives in a scratch ``tmp_path`` framework root, so it neither depends on the
shipped registry's current values nor on external services.

Run: python3 -m pytest tests/test_surface_version_consistency.py -q
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from types import SimpleNamespace

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib import agent_sync, sync_pipeline
from lib.consistency.artifact_contracts import check_artifact_contracts
from lib.consistency.report import Severity
from lib.providers import _surface_version_warnings, load_providers_config

_SURFACE_FORMATS = {"v1": "opencode-json", "v2": "opencode-json-v2"}
_SURFACE_MECHANISMS = {"v1": "opencode-native", "v2": "opencode-native-v2"}


class _NullLog:
    """Minimal ``SyncLog`` stand-in for the stage-2 probe (notes are discarded)."""

    def note(self, *args, **kwargs) -> None:  # noqa: D102, ANN002 - test stub
        pass

    def warn(self, *args, **kwargs) -> None:  # noqa: D102, ANN002 - test stub
        pass


def _write_registry(
    root: Path,
    *,
    formats: dict | None = _SURFACE_FORMATS,
    mechanisms: dict | None = _SURFACE_MECHANISMS,
    version: str = "v1",
) -> None:
    """Write a minimal ``config/ai-providers.yaml`` fixture under ``root``."""
    entry: dict = {
        "agents_dir": ".opencode/agents",
        "agent_ext": ".md",
        "capabilities": ["mcp"],
        "surface-version": version,
        "mcp-config": {"committed-file": "opencode.json", "format": "opencode-json"},
        "agent-transform": {"frontmatter-mechanism": "opencode-native"},
    }
    if formats is not None:
        entry["mcp-config"]["surface-formats"] = dict(formats)
    if mechanisms is not None:
        entry["agent-transform"]["surface-mechanisms"] = dict(mechanisms)
    cfg_dir = root / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "ai-providers.yaml").write_text(
        yaml.safe_dump({"providers": {"Opencode": entry}}, sort_keys=False),
        encoding="utf-8",
    )


def _project(surface: str | None = None) -> dict:
    """A project config with an optional ``provider-options`` v2 opt-in."""
    project: dict = {"ai-providers": ["Opencode"]}
    if surface is not None:
        project["provider-options"] = {"Opencode": {"surface-version": surface}}
    return project


def _dump(obj: dict) -> str:
    """Canonical serialization used for byte-identity comparisons."""
    return json.dumps(obj, sort_keys=True)


def test_generation_and_check_resolve_identical_provider_config(tmp_path, monkeypatch):
    """[AC-A3][REV-R2] The generation and check paths thread the same project config.

    A v2 project must resolve to the v2 shape/mechanism on **both** the
    generation stage and the check gate, and the two resolved ``provider_config``
    mappings must be byte-identical — otherwise generation could emit v2 while
    the check silently validates v1.
    """
    root = tmp_path / "fw"
    root.mkdir()
    _write_registry(root)
    project = _project("v2")
    config_path = tmp_path / ".meta-config" / "project.yaml"
    config_path.parent.mkdir(parents=True, exist_ok=True)

    real = load_providers_config

    # --- generation path: _sync_stage_config_and_presets resolves the registry
    monkeypatch.setattr(sync_pipeline, "fill_defaults", lambda *a, **k: None)
    monkeypatch.setattr(sync_pipeline, "load_config", lambda _path: project)
    monkeypatch.setattr(
        sync_pipeline, "resolve_dod_preset_name", lambda *a, **k: "rapid-prototyping"
    )
    monkeypatch.setattr(sync_pipeline, "resolve_dod", lambda *a, **k: {})
    monkeypatch.setattr(sync_pipeline, "resolve_rules", lambda *a, **k: {})
    monkeypatch.setattr(sync_pipeline, "load_platform_config", lambda *a, **k: None)

    gen_seen: dict = {}

    def gen_spy(root_arg, cfg=None):
        gen_seen["root"] = root_arg
        gen_seen["cfg"] = cfg
        return real(root_arg, cfg)

    monkeypatch.setattr(sync_pipeline, "load_providers_config", gen_spy)

    args = SimpleNamespace(init=False, dry_run=True)
    _, gen_pc, providers, _, _ = sync_pipeline._sync_stage_config_and_presets(
        root, tmp_path, config_path, project, [], args, _NullLog()
    )

    assert providers == ["Opencode"]
    assert gen_seen["cfg"] is project, "generation must pass the project config"
    assert gen_pc["Opencode"]["mcp-config"]["format"] == "opencode-json-v2"
    assert (
        gen_pc["Opencode"]["agent-transform"]["frontmatter-mechanism"]
        == "opencode-native-v2"
    )

    # --- check path: collect_artifact_findings resolves the same registry
    chk_seen: dict = {}

    def chk_spy(root_arg, cfg=None):
        chk_seen["root"] = root_arg
        chk_seen["cfg"] = cfg
        return real(root_arg, cfg)

    monkeypatch.setattr(agent_sync, "load_providers_config", chk_spy)

    agent_sync.collect_artifact_findings(root, tmp_path, project)

    assert chk_seen["cfg"] is project, "check must pass the project config"
    assert chk_seen["root"] == root
    assert _dump(real(root, chk_seen["cfg"])) == _dump(gen_pc), (
        "check-resolved provider_config must equal generation-resolved "
        "provider_config for a v2 project"
    )


def test_unset_project_is_byte_identical_to_registry_default(tmp_path):
    """[AC-A2][AC-A1][D5] v1/unset stays byte-frozen.

    Resolving with no project config, an empty/absent ``provider-options`` block,
    or an explicit ``surface-version: v1`` must all return the exact registry
    default (``opencode-json`` / ``opencode-native``).
    """
    root = tmp_path / "fw"
    root.mkdir()
    _write_registry(root)

    baseline = load_providers_config(root)
    assert baseline["Opencode"]["mcp-config"]["format"] == "opencode-json"
    assert (
        baseline["Opencode"]["agent-transform"]["frontmatter-mechanism"]
        == "opencode-native"
    )

    for project in (
        {},
        {"ai-providers": ["Opencode"]},
        {"provider-options": {"Opencode": {}}},
        _project("v1"),
    ):
        resolved = load_providers_config(root, project)
        assert _dump(resolved) == _dump(baseline), (
            "v1/unset must be byte-identical to the no-project resolution"
        )


def test_non_default_without_formats_warns_in_both_paths(tmp_path):
    """[REV-R5] A v2 opt-in without ``surface-formats`` is a WARNING, not a pass.

    The resolver is fail-safe (keeps the declared shape), so the reject-or-warn
    pair must surface on the check path as a ``Severity.WARNING`` finding instead
    of silently passing.
    """
    root = tmp_path / "fw"
    root.mkdir()
    _write_registry(root, formats=None, mechanisms=None)
    project = _project("v2")

    warnings = _surface_version_warnings(load_providers_config(root, project))
    assert warnings, "a non-default value without surface-formats must warn"
    assert "surface-formats" in warnings[0]

    findings = agent_sync.collect_artifact_findings(root, tmp_path, project)
    warning_findings = [
        finding
        for _, finding in findings
        if finding.severity == Severity.WARNING and "surface-formats" in finding.message
    ]
    assert warning_findings, (
        "the check path must emit a WARNING finding for a non-default "
        "surface-version without surface-formats (REV-R5)"
    )


def test_v1_artifact_under_v2_project_reports_a_finding(tmp_path):
    """[AC-A3] A v1 tree under a v2 project is fail-loud, never a silent rc 0.

    ``check_artifact_contracts`` resolves the same project config as generation;
    a flat v1 ``opencode.json`` therefore fails the v2 key-shape contract, while
    the matching nested-v2 document passes cleanly.
    """
    root = tmp_path / "fw"
    root.mkdir()
    _write_registry(root)
    project = _project("v2")
    committed = root / "opencode.json"

    committed.write_text(
        json.dumps({"mcp": {"playwright": {"command": "npx"}}}), encoding="utf-8"
    )
    mismatch = check_artifact_contracts(root, project)
    assert mismatch, "a v1-shaped artifact under a v2 project must be a finding"
    assert all(finding.severity == Severity.ERROR for finding in mismatch)
    assert any("mcp.servers" in finding.message for finding in mismatch)

    committed.write_text(
        json.dumps({"mcp": {"servers": {}}, "default_agent": "orchestrator"}),
        encoding="utf-8",
    )
    assert check_artifact_contracts(root, project) == []
