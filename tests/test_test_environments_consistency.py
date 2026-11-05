"""Placeholder registration for the test-environments feature (Task 7).

``TEST_ENVIRONMENT_BLOCK`` and ``TEST_ENVIRONMENTS_SET`` are produced by
``build_test_environment_variables`` and consumed by the six base templates
(Task 8). This module locks the registration touch-points: the builder, the
``build_variables`` wiring, the consistency whitelist, the standalone fallbacks
and the public sync-concept table (AC-ENV-15, Issue #1082).

Run: ``python3 -m pytest tests/test_test_environments_consistency.py``
"""

from __future__ import annotations

import sys
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
REPO_ROOT = Path(__file__).resolve().parents[1]

from lib.config import build_variables, load_config  # noqa: E402
from lib.consistency.placeholders import (  # noqa: E402
    _BUILTIN_VARS,
    _UNREGISTERED_BUILDER_RATCHET,
)
from lib.standalone import (  # noqa: E402
    _CONDITIONAL_FALSE_FLAGS,
    _ORCHESTRATION_FALLBACKS,
)
from lib.test_environments import build_test_environment_variables  # noqa: E402
from lib.variables import strip_inactive_conditional_blocks  # noqa: E402


def test_builder_unconfigured():
    assert build_test_environment_variables({}, None) == {
        "TEST_ENVIRONMENT_BLOCK": "",
        "TEST_ENVIRONMENTS_SET": "false",
    }


def test_builder_configured_uses_platform_fallback(tmp_path):
    (tmp_path / ".claude").mkdir()
    (tmp_path / ".claude" / "platform-config.yaml").write_text(
        "platform:\n  hacs:\n    dev_instance_url: http://dev:8123\n",
        encoding="utf-8",
    )
    v = build_test_environment_variables(
        {"test-environments": {"ha": {"kind": "remote"}}}, tmp_path
    )
    assert v["TEST_ENVIRONMENTS_SET"] == "true"
    assert "http://dev:8123 (from platform.hacs.dev_instance_url)" in v[
        "TEST_ENVIRONMENT_BLOCK"
    ]


def test_build_variables_carries_both_keys():
    cfg = load_config(REPO_ROOT / ".meta-config" / "project.yaml")
    v, _ = build_variables(cfg, REPO_ROOT)
    assert (v["TEST_ENVIRONMENT_BLOCK"], v["TEST_ENVIRONMENTS_SET"]) == ("", "false")
    cfg2 = {**cfg, "test-environments": {"sharkord-local": {"kind": "local"}}}
    v2, _ = build_variables(cfg2, REPO_ROOT)
    assert v2["TEST_ENVIRONMENTS_SET"] == "true"
    assert v2["TEST_ENVIRONMENT_BLOCK"].startswith("## Test environments")


def test_placeholders_registered():
    assert {"TEST_ENVIRONMENT_BLOCK", "TEST_ENVIRONMENTS_SET"} <= _BUILTIN_VARS
    assert not {
        "TEST_ENVIRONMENT_BLOCK",
        "TEST_ENVIRONMENTS_SET",
    } & _UNREGISTERED_BUILDER_RATCHET


def test_standalone_fallbacks():
    assert _CONDITIONAL_FALSE_FLAGS["TEST_ENVIRONMENTS_SET"] == "false"
    assert _ORCHESTRATION_FALLBACKS["TEST_ENVIRONMENT_BLOCK"] == ""


def test_sync_concept_documents_both_placeholders():  # Issue #1082
    text = (REPO_ROOT / "docs/guides/features/sync-concept.md").read_text(
        encoding="utf-8"
    )
    assert "{{%TEST_ENVIRONMENT_BLOCK%}}" in text
    assert "{{%TEST_ENVIRONMENTS_SET%}}" in text
    assert "{{TEST_ENVIRONMENT_BLOCK}}" not in text.replace(
        "{{%TEST_ENVIRONMENT_BLOCK%}}", ""
    )


def test_set_suffix_gate_strips_with_trailing_newline():
    gate = "a\n{{#if TEST_ENVIRONMENTS_SET}}\nX\n{{/if}}\nb\n"
    assert (
        strip_inactive_conditional_blocks(gate, {"TEST_ENVIRONMENTS_SET": "false"})
        == "a\nb\n"
    )
    assert (
        strip_inactive_conditional_blocks(gate, {"TEST_ENVIRONMENTS_SET": "true"})
        == "a\nX\nb\n"
    )
