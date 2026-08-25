"""Migration-invariant test for the Platform-Level Config Defaults feature.

config/platform-defaults.yaml ships EMPTY (platforms: {}). The invariant
(concept section 8.2c / MAJOR-4 fix) is resolver identity, not byte identity:
with no platform entry, apply_platform_defaults() must be a pure no-op for ANY
project — no project without a populated platform-defaults entry may see a
changed config. This is asserted as real dict equality, not merely "no crash".
"""

import copy
from pathlib import Path

from scripts.lib.platform_defaults import apply_platform_defaults, load_platform_defaults

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_shipped_platform_defaults_file_is_empty():
    # The feature ships with no platform entries — population is a follow-up step.
    assert load_platform_defaults(REPO_ROOT) == {}


def test_apply_is_noop_for_active_platform_when_file_empty():
    # A project with an active platform but no matching platform-defaults entry
    # must get an identical config back.
    config = {
        "platforms": ["hacs"],
        "dod-preset": "rapid-prototyping",
        "roles": ["developer", "tester"],
        "mcp-servers": ["homeassistant"],
    }
    original = copy.deepcopy(config)
    result = apply_platform_defaults(config, REPO_ROOT)
    assert result == original
    # Input must never be mutated in place.
    assert config == original


def test_apply_is_noop_for_empty_platforms():
    config = {"platforms": [], "dod-preset": "full"}
    original = copy.deepcopy(config)
    assert apply_platform_defaults(config, REPO_ROOT) == original


def test_apply_is_noop_when_platforms_key_absent():
    config = {"dod-preset": "standard", "roles": ["git"]}
    original = copy.deepcopy(config)
    assert apply_platform_defaults(config, REPO_ROOT) == original
