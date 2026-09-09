"""Regression tests for the platform-preset cascade fields added to
platform-configs/*.defaults.yaml (Task 1 of the platform-project-defaults
feature). Pure YAML-load-level: verifies shape only, NOT merge semantics
(that's scripts/lib/platform.py::resolve_platform_defaults(), covered by
tests/test_platform_defaults_resolver.py).
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_PLATFORM_CONFIGS_DIR = _REPO_ROOT / "platform-configs"


def _load(name: str) -> dict:
    with (_PLATFORM_CONFIGS_DIR / f"{name}.defaults.yaml").open(encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_hacs_defaults_have_platform_cascade_fields():
    data = _load("hacs")
    assert data["dod-preset"] == "standard"
    assert "conventions-preset" not in data  # deliberate omission, see plan
    assert isinstance(data["variables"], dict)
    assert data["variables"]["PLATFORM"] == "Home Assistant Custom Component"
    assert data["variables"]["RUNTIME"] == "Python 3.13 (HA Core)"
    assert data["variables"]["PROJECT_LANGUAGES"] == "Python"
    assert data["variables"]["TEST_COMMANDS"] == "pytest tests/ --cov"
    assert data["variables"]["CODE_CONVENTIONS+"] == "Python, ruff, mypy --strict"
    # Existing {{platform.hacs.*}} namespace is untouched (no duplication issue here)
    assert data["platform"]["hacs"]["custom_components_path"] == "custom_components"


def test_sharkord_defaults_migrate_service_name_and_host_lan_ip_into_variables():
    data = _load("sharkord")
    assert data["dod-preset"] == "standard"
    assert "conventions-preset" not in data
    assert isinstance(data["variables"], dict)
    assert data["variables"]["PLATFORM"] == "Sharkord Plugin SDK"
    assert data["variables"]["RUNTIME"] == "Bun"
    assert data["variables"]["PROJECT_LANGUAGES"] == "TypeScript"
    assert data["variables"]["SERVICE_NAME"] == "sharkord"
    assert data["variables"]["CONTAINER_NAME"] == "sharkord"
    assert data["variables"]["HOST_LAN_IP"] == "127.0.0.1"
    assert data["variables"]["TEST_COMMANDS+"] == "docker compose run --rm test"
    assert data["variables"]["CODE_CONVENTIONS+"] == "TypeScript, ESLint, Prettier"
    # Old {{platform.sharkord.*}} namespace stays untouched here -- Task 8 removes
    # the now-duplicate service_name/host_lan_ip sub-keys, not this task.
    assert data["platform"]["sharkord"]["service_name"] == "sharkord"
    assert data["platform"]["sharkord"]["host_lan_ip"] == "127.0.0.1"
    assert data["platform"]["sharkord"]["image_tag"] == "v0.0.16"  # untouched by Task 8 either


def test_homeassistant_defaults_have_platform_cascade_fields():
    data = _load("homeassistant")
    assert data["dod-preset"] == "rapid-prototyping"
    assert "conventions-preset" not in data
    assert isinstance(data["variables"], dict)
    assert data["variables"]["PLATFORM"] == "Home Assistant Automation Config"
    assert data["variables"]["RUNTIME"] == "Home Assistant Core (YAML)"
    assert data["variables"]["PROJECT_LANGUAGES"] == "YAML, Jinja2"
    assert data["variables"]["TEST_COMMANDS"] == "hass --script check_config"
