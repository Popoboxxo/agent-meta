"""Tests for scripts/lib/platform.py::resolve_platform_defaults() (Task 2
of the platform-project-defaults feature).

Fixture platform-configs live in tmp_path per test -- NEVER against the
real platform-configs/ directory (that's Task 1, covered separately by
tests/test_platform_defaults_yaml.py).
Spec: docs/superpowers/specs/2026-09-09-platform-project-defaults-design.md
"""
from __future__ import annotations

import sys
from pathlib import Path

import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
_SCRIPTS_DIR = _REPO_ROOT / "scripts"
if str(_SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(_SCRIPTS_DIR))

from lib.platform import resolve_platform_defaults


def _write_defaults(dir_: Path, name: str, content: dict) -> None:
    dir_.mkdir(parents=True, exist_ok=True)
    (dir_ / f"{name}.defaults.yaml").write_text(yaml.dump(content), encoding="utf-8")


def test_single_platform_scalars_pass_through(tmp_path):
    _write_defaults(tmp_path, "hacs", {
        "dod-preset": "standard",
        "variables": {"PLATFORM": "HACS"},
    })
    result = resolve_platform_defaults(["hacs"], tmp_path)
    assert result["dod-preset"] == "standard"
    assert result["conventions-preset"] is None
    assert result["variables"]["PLATFORM"] == "HACS"


def test_two_platforms_same_scalar_key_last_wins(tmp_path):
    _write_defaults(tmp_path, "a", {"variables": {"PLATFORM": "platform-a"}})
    _write_defaults(tmp_path, "b", {"variables": {"PLATFORM": "platform-b"}})
    result = resolve_platform_defaults(["a", "b"], tmp_path)
    assert result["variables"]["PLATFORM"] == "platform-b"


def test_order_sensitivity_swapped_platforms_flip_the_winner(tmp_path):
    _write_defaults(tmp_path, "a", {"variables": {"PLATFORM": "platform-a"}})
    _write_defaults(tmp_path, "b", {"variables": {"PLATFORM": "platform-b"}})
    result = resolve_platform_defaults(["b", "a"], tmp_path)
    assert result["variables"]["PLATFORM"] == "platform-a"


def test_additive_field_set_on_only_one_of_two_platforms(tmp_path):
    _write_defaults(tmp_path, "a", {"variables": {"TEST_COMMANDS+": "cmd-a"}})
    _write_defaults(tmp_path, "b", {"variables": {}})
    result = resolve_platform_defaults(["a", "b"], tmp_path)
    assert result["variables"]["TEST_COMMANDS"] == "cmd-a"


def test_additive_field_set_on_both_platforms_concatenates_in_list_order(tmp_path):
    _write_defaults(tmp_path, "a", {"variables": {"TEST_COMMANDS+": "cmd-a"}})
    _write_defaults(tmp_path, "b", {"variables": {"TEST_COMMANDS+": "cmd-b"}})
    result = resolve_platform_defaults(["a", "b"], tmp_path)
    assert result["variables"]["TEST_COMMANDS"] == "cmd-a && cmd-b"


def test_additive_field_uses_custom_join_char_for_code_conventions(tmp_path):
    _write_defaults(tmp_path, "a", {"variables": {"CODE_CONVENTIONS+": "rule-a"}})
    _write_defaults(tmp_path, "b", {"variables": {"CODE_CONVENTIONS+": "rule-b"}})
    result = resolve_platform_defaults(["a", "b"], tmp_path)
    assert result["variables"]["CODE_CONVENTIONS"] == "rule-a; rule-b"


def test_plain_field_after_additive_field_replaces_it_completely(tmp_path):
    # "<FIELD> ersetzt komplett" (design spec) applies regardless of whether
    # the accumulated value came from a prior scalar OR a prior '+' chain.
    _write_defaults(tmp_path, "a", {"variables": {"TEST_COMMANDS+": "cmd-a"}})
    _write_defaults(tmp_path, "b", {"variables": {"TEST_COMMANDS": "cmd-b"}})
    result = resolve_platform_defaults(["a", "b"], tmp_path)
    assert result["variables"]["TEST_COMMANDS"] == "cmd-b"


def test_unknown_platform_without_defaults_file_does_not_crash(tmp_path):
    result = resolve_platform_defaults(["does-not-exist"], tmp_path)
    assert result == {"dod-preset": None, "conventions-preset": None, "variables": {}}


def test_default_platform_config_dir_resolves_to_real_repo_platform_configs():
    # No platform_config_dir passed -- falls back to <repo_root>/platform-configs.
    result = resolve_platform_defaults(["hacs"])
    assert result["dod-preset"] == "standard"  # from the real Task 1 fixture
