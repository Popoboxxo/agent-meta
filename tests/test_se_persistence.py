"""Test SE-Pipeline persistence: Agent writes output, new run reads and resumes."""
import json
from pathlib import Path

import pytest

from scripts.lib.io import _load_yaml_or_json, _write_yaml

# Project root for schema file access
_AGENT_META_ROOT = Path(__file__).resolve().parent.parent


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def se_state_content():
    """Minimal valid .se-state.yaml fixture."""
    return {
        "project": "test-proj",
        "last_updated": "2026-06-21T14:32:11Z",
        "current_level": "L1",
        "current_node": "Gesamtsystem",
        "last_completed_step": {
            "agent": "se-requirements",
            "iteration": 1,
            "status": "done",
            "output_file": "L1/Gesamtsystem/requirements/L1_Gesamtsystem_Requirements.md",
        },
        "next_expected_step": {
            "agent": "se-critic",
            "input_files": [
                "L1/Gesamtsystem/requirements/L1_Gesamtsystem_Requirements.md",
            ],
        },
        "pending_decisions": [],
        "budget_consumed": {
            "cells": 1,
            "tokens": 3200,
            "estimated_eur": 0.12,
        },
    }


@pytest.fixture
def se_state_file(tmp_path, se_state_content):
    """Write a .se-state.yaml to a temp directory."""
    fpath = tmp_path / ".se-state.yaml"
    _write_yaml(fpath, se_state_content)
    return fpath


# ---------------------------------------------------------------------------
# Test: .se-state.yaml can be written and read round-trip
# ---------------------------------------------------------------------------

def test_se_state_write_and_read_roundtrip(tmp_path, se_state_content):
    """Round-trip: write .se-state.yaml, read it back, verify content."""
    fpath = tmp_path / ".se-state.yaml"
    _write_yaml(fpath, se_state_content)

    assert fpath.exists()

    readback, _used = _load_yaml_or_json(fpath)
    assert readback["project"] == "test-proj"
    assert readback["current_level"] == "L1"
    assert readback["last_completed_step"]["agent"] == "se-requirements"
    assert readback["last_completed_step"]["output_file"] == (
        "L1/Gesamtsystem/requirements/L1_Gesamtsystem_Requirements.md"
    )


# ---------------------------------------------------------------------------
# Test: resume from .se-state.yaml identifies the next expected step
# ---------------------------------------------------------------------------

def test_resume_pointer_next_step(se_state_file):
    """Reading .se-state.yaml reveals the next expected step."""
    state, _used = _load_yaml_or_json(se_state_file)
    next_step = state.get("next_expected_step", {})
    assert next_step["agent"] == "se-critic"
    assert len(next_step["input_files"]) == 1
    assert "L1_Gesamtsystem_Requirements.md" in next_step["input_files"][0]


# ---------------------------------------------------------------------------
# Test: atomic write simulation (write-to-tmp + rename)
# ---------------------------------------------------------------------------

def test_atomic_write_then_rename(tmp_path):
    """Simulate atomic write: write to temp file, then rename to target."""
    target = tmp_path / "requirements" / "L1_Test_Requirements.md"
    target.parent.mkdir(parents=True, exist_ok=True)

    # Write to temp
    tmp_file = tmp_path / ".tmp-write"
    frontmatter = {
        "step": "requirements",
        "agent": "se-requirements",
        "iteration": 1,
        "status": "done",
        "timestamp": "2026-06-21T14:32:11Z",
        "schema_version": "1.0.0",
    }
    content = "---\n" + "\n".join(f"{k}: {v}" for k, v in frontmatter.items()) + "\n---\n\n# Requirements\n"
    tmp_file.write_text(content, encoding="utf-8")

    # Atomic rename
    tmp_file.rename(target)

    assert target.exists()
    assert not tmp_file.exists()  # temp is gone

    read_back = target.read_text(encoding="utf-8")
    assert "step: requirements" in read_back
    assert "agent: se-requirements" in read_back


# ---------------------------------------------------------------------------
# Test: iteration suffix convention
# ---------------------------------------------------------------------------

def test_iteration_suffix_convention():
    """Verify .iter-{N}.md and .final.md naming conventions."""
    base = Path("L1/Gesamtsystem/architecture/L1_Gesamtsystem_Architecture")

    assert (base.parent / (base.name + ".iter-1.md")).name == "L1_Gesamtsystem_Architecture.iter-1.md"
    assert (base.parent / (base.name + ".iter-2.md")).name == "L1_Gesamtsystem_Architecture.iter-2.md"
    assert (base.parent / (base.name + ".final.md")).name == "L1_Gesamtsystem_Architecture.final.md"


# ---------------------------------------------------------------------------
# Test: persistence directory structure
# ---------------------------------------------------------------------------

def test_persistence_directory_structure(tmp_path):
    """Create the full directory structure for an SE project."""
    project_dir = tmp_path / "docs" / "se" / "test-proj"
    subdirs = [
        "L1/Gesamtsystem/requirements",
        "L1/Gesamtsystem/architecture",
        "L1/Gesamtsystem/interfaces",
        "L1/Gesamtsystem/termination",
        "L1/Gesamtsystem/L2/AuthServiceSystem/requirements",
        "L1/Gesamtsystem/L2/AuthServiceSystem/architecture",
        "L1/Gesamtsystem/L2/AuthServiceSystem/implementation",
        "L1/Gesamtsystem/L2/AuthServiceSystem/validation",
    ]
    for d in subdirs:
        (project_dir / d).mkdir(parents=True, exist_ok=True)

    # Create .se-state.yaml
    state_path = project_dir / ".se-state.yaml"
    _write_yaml(state_path, {
        "project": "test-proj",
        "last_updated": "2026-06-21T14:32:11Z",
        "current_level": "L2",
        "current_node": "AuthServiceSystem",
        "last_completed_step": {
            "agent": "se-architect",
            "iteration": 2,
            "status": "approved",
            "output_file": "L1/Gesamtsystem/L2/AuthServiceSystem/architecture/L2_AuthServiceSystem_Architecture.final.md",
        },
        "next_expected_step": {
            "agent": "se-interface-mgr",
            "input_files": [],
        },
        "pending_decisions": [],
        "budget_consumed": {"cells": 3, "tokens": 8500, "estimated_eur": 0.35},
    })

    # Verify state re-read
    state, _used = _load_yaml_or_json(state_path)
    assert state["current_node"] == "AuthServiceSystem"
    assert state["budget_consumed"]["cells"] == 3

    # Verify all directories exist
    for d in subdirs:
        assert (project_dir / d).is_dir(), f"Missing dir: {d}"


# ---------------------------------------------------------------------------
# Test: verify schemas are valid JSON Schema
# ---------------------------------------------------------------------------

def test_se_state_schema_is_valid_json():
    """se-state.schema.json must be valid JSON."""
    schema_path = _AGENT_META_ROOT / "schemas" / "se-state.schema.json"
    assert schema_path.exists(), f"Schema missing: {schema_path}"
    with schema_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert "$schema" in data
    assert "title" in data


def test_se_requirements_schema_is_valid_json():
    """se-requirements.schema.json must be valid JSON."""
    schema_path = _AGENT_META_ROOT / "schemas" / "se-requirements.schema.json"
    assert schema_path.exists(), f"Schema missing: {schema_path}"
    with schema_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    assert data.get("properties", {}).get("requirements") is not None


def test_se_critic_schema_is_valid_json():
    """se-critic.schema.json must be valid JSON."""
    schema_path = _AGENT_META_ROOT / "schemas" / "se-critic.schema.json"
    assert schema_path.exists(), f"Schema missing: {schema_path}"
    with schema_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    checks = data.get("properties", {}).get("checks", {}).get("properties", {})
    assert "role_boundary" in checks
