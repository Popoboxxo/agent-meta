"""Unit tests for PR 0.3 / P10 (E-05) orchestration checks.

Covers IC-1/IC-2/IC-3 (schema descriptions + config warning dedupe) and IC-4
(depth coherence checker). All tests are unit-level — no ``sync.py`` subprocess.
"""
from __future__ import annotations

import importlib
import io
import json
import sys
from contextlib import redirect_stderr
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

SCHEMA_PATH = ROOT / "config" / "project-config.schema.json"


@pytest.fixture(scope="module")
def schema() -> dict:
    return json.loads(SCHEMA_PATH.read_text(encoding="utf-8"))


# --- IC-1: orchestrator.enabled / strict deprecation labels (AC-1) -----------

def test_orchestrator_enabled_deprecated(schema):
    prop = schema["properties"]["orchestrator"]["properties"]["enabled"]
    assert prop["description"].startswith("DEPRECATED — ")
    assert "orchestrator.mode" in prop["description"]
    assert prop["type"] == "boolean"
    assert prop["default"] is True


def test_orchestrator_strict_deprecated(schema):
    prop = schema["properties"]["orchestrator"]["properties"]["strict"]
    assert prop["description"].startswith("DEPRECATED — ")
    assert "orchestrator.mode" in prop["description"]
    assert prop["type"] == "boolean"
    assert prop["default"] is True


def test_no_deprecated_keyword_on_orchestrator_flags(schema):
    props = schema["properties"]["orchestrator"]["properties"]
    assert "deprecated" not in props["enabled"]
    assert "deprecated" not in props["strict"]


# --- IC-2: knowledge.schema-language inert label (AC-2) ----------------------

def test_schema_language_retained_and_labeled(schema):
    prop = schema["properties"]["knowledge-engine"]["properties"]["schema-language"]
    assert "DEPRECATED" in prop["description"]
    assert "inert" in prop["description"].lower()
    assert prop["type"] == "string"
    assert prop["default"] == "auto"


# --- IC-3: handoff.t-size-limit accepted + warning dedupe (AC-3) -------------

def test_t_size_limit_validates_without_additional_properties_error(tmp_path, schema):
    """AC-3 behavior path: t-size-limit: 250 validates, no duplicate block."""
    cfg = importlib.import_module("lib.config")
    if not cfg._JSONSCHEMA_AVAILABLE:
        pytest.skip("jsonschema not installed — schema validation skipped")

    # F4: fold the property-only schema assertion into the behavior test.
    prop = schema["properties"]["orchestrator"]["properties"]["handoff"]["properties"]["t-size-limit"]
    assert prop["type"] == "integer"
    assert prop["default"] == 300
    assert prop["minimum"] == 1

    config_path = tmp_path / "project.yaml"
    config_path.write_text("", encoding="utf-8")
    config = {"orchestrator": {"handoff": {"t-size-limit": 250}}}

    # The real double-validation call sequence, no private-global poking.
    sink = io.StringIO()
    with redirect_stderr(sink):
        cfg._validate_config(config, config_path)   # exit 0 == no exception
        cfg._validate_config(config, config_path)
    output = sink.getvalue()
    assert "Additional properties are not allowed" not in output
    assert "'t-size-limit' was unexpected" not in output
    # A valid config produces no warnings at all; still "at most once".
    assert output.count("Config validation warnings") <= 1


def test_config_validation_warnings_deduped_by_content(tmp_path):
    """F1 regression: identical warnings dedupe, distinct errors still emit."""
    cfg = importlib.import_module("lib.config")
    if not cfg._JSONSCHEMA_AVAILABLE:
        pytest.skip("jsonschema not installed — schema validation skipped")

    config_path = tmp_path / "project.yaml"
    config_path.write_text("", encoding="utf-8")
    bad_a = {"max-parallel-agents": "not-an-int"}
    bad_b = {"max-parallel-agents": "definitely-not-an-int"}

    sink = io.StringIO()
    with redirect_stderr(sink):
        cfg._validate_config(bad_a, config_path)
        cfg._validate_config(bad_a, config_path)   # duplicate -> suppressed
    output = sink.getvalue()
    assert output.count("Config validation warnings") == 1

    # A different error set in the same process must NOT be suppressed.
    sink2 = io.StringIO()
    with redirect_stderr(sink2):
        cfg._validate_config(bad_b, config_path)
    assert sink2.getvalue().count("Config validation warnings") == 1


# --- IC-4: depth coherence checker (AC-4) ------------------------------------

def _write_capabilities(root: Path, provider: str, required_depth: int) -> None:
    cfg_dir = root / "config"
    cfg_dir.mkdir(parents=True, exist_ok=True)
    (cfg_dir / "provider-capabilities.yaml").write_text(
        f"capabilities:\n  {provider}:\n    required_depth: {required_depth}\n",
        encoding="utf-8",
    )


def test_depth_coherence_emitted_below_required(tmp_path):
    from lib.consistency.depth_coherence import (
        CHECK_EMITTED_BELOW_REQUIRED,
        check_depth_coherence,
    )
    from lib.consistency.report import Severity

    provider = "testprovider"
    _write_capabilities(tmp_path, provider, 2)
    (tmp_path / "emitted.json").write_text(
        json.dumps({"experimental": {"subagent_depth": 1}}), encoding="utf-8"
    )
    config = {
        "ai-providers": [provider],
        "orchestrator": {"delegation": {"max_depth": 10}},
    }
    provider_config = {
        provider: {"mcp-config": {"committed-file": "emitted.json"}},
    }

    findings = check_depth_coherence(tmp_path, config, provider_config)

    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity == Severity.WARNING
    assert finding.check == CHECK_EMITTED_BELOW_REQUIRED
    assert provider in finding.message


def test_depth_coherence_delegation_below_required(tmp_path):
    from lib.consistency.depth_coherence import (
        CHECK_DELEGATION_BELOW_REQUIRED,
        check_depth_coherence,
    )

    provider = "testprovider"
    _write_capabilities(tmp_path, provider, 5)
    config = {
        "ai-providers": [provider],
        "orchestrator": {"delegation": {"max_depth": 2}},
    }
    provider_config = {provider: {}}

    findings = check_depth_coherence(tmp_path, config, provider_config)

    assert [f.check for f in findings] == [CHECK_DELEGATION_BELOW_REQUIRED]


def test_depth_coherence_fail_soft(tmp_path):
    """Defensive fail-soft guard — NOT AC-4 behavioral coverage.

    Malformed inputs must never raise and must never emit a WARNING (which
    would fail ``--strict``); an INFO diagnostic is the only allowed output.
    """
    from lib.consistency.depth_coherence import check_depth_coherence
    from lib.consistency.report import Severity

    # No capabilities file, malformed inputs -> no exception, no WARNING.
    findings = check_depth_coherence(tmp_path, None, "not-a-dict")
    assert not [f for f in findings if f.severity == Severity.WARNING]


def test_depth_coherence_check_error_is_info(tmp_path, monkeypatch):
    """F7: a checker bug is reported as INFO and never raised (fail-soft)."""
    import lib.providers as providers

    from lib.consistency.depth_coherence import check_depth_coherence
    from lib.consistency.report import Severity

    def boom(*args, **kwargs):
        raise RuntimeError("boom")

    monkeypatch.setattr(providers, "load_provider_capabilities", boom)
    findings = check_depth_coherence(tmp_path, {}, {})
    assert len(findings) == 1
    assert findings[0].severity == Severity.INFO
    assert findings[0].check == "depth-coherence.check-error"
    assert "RuntimeError" in findings[0].message


# --- F10: wiring of check_depth_coherence into run_checks ---------------------

def test_depth_coherence_wired_into_run_checks():
    """F10: the consistency-check runner actually registers the checker."""
    import importlib.util
    import inspect

    path = SCRIPTS / "consistency-check.py"
    spec = importlib.util.spec_from_file_location("_consistency_check_p10", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)

    assert callable(module.check_depth_coherence)
    assert "check_depth_coherence(" in inspect.getsource(module.run_checks)
