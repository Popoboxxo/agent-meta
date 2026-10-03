"""Unit tests for the two generated-artifact consistency checks.

Plan Task 2 (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30), AC-17 (consistency
side) + AC-2.

Covers:

* ``check_artifact_contracts`` — a corrupted generated artifact yields an
  ERROR Finding, a clean tree yields none, and the check is registry-driven
  (no provider name literal in the code under test).
* ``check_model_contracts`` — ``model-format`` prefix + double-application
  (``kimi-code/kimi-code/*``) + ``model-catalog`` containment.
* Registration — both checks run inside ``scripts/consistency-check.py``'s
  ``run_checks`` next to ``check_fanout_backend_contract``.

Run: python3 -m pytest tests/test_consistency_checks.py -q
"""
from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS = _REPO_ROOT / "scripts"
if str(_SCRIPTS) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS))

from lib.consistency.artifact_contracts import check_artifact_contracts
from lib.consistency.model_contracts import check_model_contracts
from lib.consistency.report import Finding, Severity

_ARTIFACT = "artifact-contract"
_MODEL = "model-contract"

# A v2 provider exercises the Opencode-style silent-drop guard (allow-list +
# nested MCP document); the v2 surface is where the allow-list is authoritative
# (spec §5, design §4.3). ProbeToml exercises the TOML serializer contract.
_REGISTRY = """\
providers:
  ProbeV2:
    agents_dir: .probe/agents
    agent_ext: .md
    surface-version: "v2"
    model-format: "kimi-code/{model}"
    model-catalog:
    - kimi-code/good
    agent-transform:
      frontmatter-mechanism: opencode-native-v2
      allowed-fields:
      - name
      - description
      - model
      reject-fields:
      - hint
    mcp-config:
      committed-file: .probe/config.json
      format: opencode-json-v2
  ProbeToml:
    agents_dir: .probetoml/agents
    agent_ext: .toml
    surface-version: "v1"
    model-format: "{model}"
    agent-transform:
      frontmatter-mechanism: codex-toml
      allowed-fields:
      - name
      reject-fields: []
"""


def _probe_root(tmp_path: Path) -> Path:
    root = tmp_path / "repo"
    (root / "config").mkdir(parents=True)
    (root / "config" / "ai-providers.yaml").write_text(_REGISTRY, encoding="utf-8")
    return root


def _write_agent(root: Path, provider_dir: str, name: str, text: str) -> Path:
    d = root / provider_dir
    d.mkdir(parents=True, exist_ok=True)
    path = d / name
    path.write_text(text, encoding="utf-8")
    return path


def _md(name: str, extra: str = "") -> str:
    return (
        "---\n"
        f"name: {name}\n"
        "description: probe agent\n"
        f"{extra}"
        "---\n"
        "Body.\n"
    )


def _by_check(findings: list[Finding], check: str) -> list[Finding]:
    return [f for f in findings if f.check == check]


def _errors(findings: list[Finding]) -> list[Finding]:
    return [f for f in findings if f.severity == Severity.ERROR]


# ---------------------------------------------------------------------------
# check_artifact_contracts
# ---------------------------------------------------------------------------


def test_artifact_clean_fixture_has_no_findings(tmp_path: Path) -> None:
    root = _probe_root(tmp_path)
    _write_agent(root, ".probe/agents", "good.md", _md("good", "model: kimi-code/good\n"))
    (root / ".probe").mkdir(exist_ok=True)
    (root / ".probe" / "config.json").write_text(
        '{"mcp": {"servers": {}}}', encoding="utf-8"
    )

    assert _by_check(check_artifact_contracts(root), _ARTIFACT) == []


def test_artifact_extra_frontmatter_key_is_error(tmp_path: Path) -> None:
    root = _probe_root(tmp_path)
    _write_agent(
        root,
        ".probe/agents",
        "bad.md",
        _md("bad", "model: kimi-code/good\nsurprise: true\n"),
    )

    findings = _by_check(check_artifact_contracts(root), _ARTIFACT)
    errors = _errors(findings)
    assert len(errors) == 1
    assert errors[0].severity == Severity.ERROR
    assert errors[0].file == ".probe/agents/bad.md"
    assert "surprise" in errors[0].message


def test_artifact_reject_field_is_error(tmp_path: Path) -> None:
    root = _probe_root(tmp_path)
    _write_agent(
        root,
        ".probe/agents",
        "rejected.md",
        _md("rejected", "model: kimi-code/good\nhint: forbidden\n"),
    )

    errors = _errors(_by_check(check_artifact_contracts(root), _ARTIFACT))
    rejected = [f for f in errors if "reject-fields" in f.message]
    assert len(rejected) == 1
    assert "hint" in rejected[0].message


def test_artifact_missing_frontmatter_is_error(tmp_path: Path) -> None:
    root = _probe_root(tmp_path)
    _write_agent(root, ".probe/agents", "nofm.md", "no frontmatter here\n")

    errors = _errors(_by_check(check_artifact_contracts(root), _ARTIFACT))
    assert len(errors) == 1
    assert errors[0].file == ".probe/agents/nofm.md"


def test_artifact_malformed_toml_is_error(tmp_path: Path) -> None:
    root = _probe_root(tmp_path)
    _write_agent(root, ".probetoml/agents", "broken.toml", 'name = "x"\n[unterminated\n')

    errors = _errors(_by_check(check_artifact_contracts(root), _ARTIFACT))
    assert len(errors) == 1
    assert errors[0].file == ".probetoml/agents/broken.toml"


def test_artifact_flat_mcp_map_fails_v2_json_contract(tmp_path: Path) -> None:
    root = _probe_root(tmp_path)
    (root / ".probe").mkdir(parents=True)
    (root / ".probe" / "config.json").write_text(
        '{"mcp": {"probe": {"type": "local"}}}', encoding="utf-8"
    )

    errors = _errors(_by_check(check_artifact_contracts(root), _ARTIFACT))
    assert len(errors) == 1
    assert errors[0].file == ".probe/config.json"


def test_artifact_v1_allow_list_is_not_enforced(tmp_path: Path) -> None:
    """The allow-list is the v2 silent-drop guard (spec §5).

    On the v1 surface the runtime normalizes unknown keys, so a declared
    allow-list must not produce findings — otherwise the clean tree would
    fail on the legacy v1 byte shape.
    """
    root = tmp_path / "v1repo"
    (root / "config").mkdir(parents=True)
    (root / "config" / "ai-providers.yaml").write_text(
        "providers:\n"
        "  ProbeV1:\n"
        "    agents_dir: .probe/agents\n"
        "    agent_ext: .md\n"
        "    surface-version: \"v1\"\n"
        "    model-format: \"{model}\"\n"
        "    agent-transform:\n"
        "      frontmatter-mechanism: opencode-native\n"
        "      allowed-fields:\n"
        "      - name\n"
        "      reject-fields: []\n",
        encoding="utf-8",
    )
    _write_agent(root, ".probe/agents", "legacy.md", _md("legacy", "prompt_mode: modern\n"))

    assert _by_check(check_artifact_contracts(root), _ARTIFACT) == []


def test_artifact_missing_registry_is_skipped(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    assert check_artifact_contracts(empty) == []


# ---------------------------------------------------------------------------
# check_model_contracts
# ---------------------------------------------------------------------------


def test_model_clean_fixture_has_no_findings(tmp_path: Path) -> None:
    root = _probe_root(tmp_path)
    _write_agent(root, ".probe/agents", "good.md", _md("good", "model: kimi-code/good\n"))

    assert _by_check(check_model_contracts(root), _MODEL) == []


def test_model_missing_prefix_is_error(tmp_path: Path) -> None:
    root = _probe_root(tmp_path)
    _write_agent(root, ".probe/agents", "bad.md", _md("bad", "model: kimi-k2.6\n"))

    errors = _errors(_by_check(check_model_contracts(root), _MODEL))
    prefix_errors = [f for f in errors if "model-format" in f.message]
    assert len(prefix_errors) == 1
    assert prefix_errors[0].file == ".probe/agents/bad.md"


def test_model_double_prefix_is_error(tmp_path: Path) -> None:
    root = _probe_root(tmp_path)
    _write_agent(
        root, ".probe/agents", "double.md", _md("double", "model: kimi-code/kimi-code/good\n")
    )

    errors = _errors(_by_check(check_model_contracts(root), _MODEL))
    doubled = [f for f in errors if "twice" in f.message]
    assert len(doubled) == 1
    assert doubled[0].file == ".probe/agents/double.md"


def test_model_outside_catalog_is_error(tmp_path: Path) -> None:
    root = _probe_root(tmp_path)
    _write_agent(root, ".probe/agents", "other.md", _md("other", "model: kimi-code/other\n"))

    errors = _errors(_by_check(check_model_contracts(root), _MODEL))
    catalog_errors = [f for f in errors if "model-catalog" in f.message]
    assert len(catalog_errors) == 1
    assert catalog_errors[0].file == ".probe/agents/other.md"


def test_model_toml_artifact_is_scanned(tmp_path: Path) -> None:
    root = _probe_root(tmp_path)
    _write_agent(
        root,
        ".probetoml/agents",
        "agent.toml",
        'name = "agent"\nmodel = "raw-model"\n',
    )

    # ProbeToml model-format is "{model}" (no prefix) and has no catalog, so
    # this is contract-clean; the assertion pins that TOML artifacts are read
    # without crashing and produce no false positive.
    assert _by_check(check_model_contracts(root), _MODEL) == []


def test_model_missing_registry_is_skipped(tmp_path: Path) -> None:
    empty = tmp_path / "empty"
    empty.mkdir()
    assert check_model_contracts(empty) == []


# ---------------------------------------------------------------------------
# real tree + registration
# ---------------------------------------------------------------------------


def test_clean_repo_tree_has_no_contract_errors() -> None:
    assert _errors(check_artifact_contracts(_REPO_ROOT)) == []
    assert _errors(check_model_contracts(_REPO_ROOT)) == []


def _load_consistency_check_module():
    path = _SCRIPTS / "consistency-check.py"
    spec = importlib.util.spec_from_file_location("consistency_check_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_both_checks_registered_in_run_checks(monkeypatch) -> None:
    module = _load_consistency_check_module()

    artifact_sentinel = Finding(
        Severity.ERROR, _ARTIFACT, "sentinel.md", "artifact sentinel"
    )
    model_sentinel = Finding(Severity.ERROR, _MODEL, "sentinel.md", "model sentinel")
    monkeypatch.setattr(module, "check_artifact_contracts", lambda root, _project_config=None: [artifact_sentinel])
    monkeypatch.setattr(module, "check_model_contracts", lambda root, _project_config=None: [model_sentinel])

    findings = module.run_checks(_REPO_ROOT)

    assert artifact_sentinel in findings
    assert model_sentinel in findings
