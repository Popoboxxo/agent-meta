"""Registration tests for the release-checklist placeholders.

Covers the five registration touch-points of the feature: the variable
builder wiring in ``config.py``, the conditional whitelist in
``variables.py``, the known-placeholder set, the standalone fallbacks and
the ``sync-concept`` documentation table.
"""

import copy
import sys
from pathlib import Path

import pytest

REPO_ROOT = Path(__file__).resolve().parents[1]


@pytest.fixture
def base_config():
    sys.path.insert(0, str(REPO_ROOT / "scripts"))
    from lib.config import load_config

    return load_config(REPO_ROOT / ".meta-config" / "project.yaml")


def _build(config):
    from lib.config import build_variables

    variables, _ = build_variables(config, REPO_ROOT)
    return variables


def test_build_variables_default_and_enabled(base_config):
    off = _build(base_config)
    assert off["RELEASE_CHECKLIST_ENABLED"] == "false"
    assert off["RELEASE_CHECKLIST_BLOCK"] == ""
    cfg = copy.deepcopy(base_config)
    cfg["release-checklist"] = {"mode": "advisory"}
    on = _build(cfg)
    assert on["RELEASE_CHECKLIST_ENABLED"] == "true"
    assert "CHECKLIST_MODE" in on["RELEASE_CHECKLIST_BLOCK"]


def test_whitelist_strips_inactive_block():
    from lib.variables import strip_inactive_conditional_blocks as strip

    src = "a\n{{#if RELEASE_CHECKLIST_ENABLED}}\nX\n{{/if}}\nb\n"
    assert strip(src, {"RELEASE_CHECKLIST_ENABLED": "false"}) == "a\nb\n"
    assert strip(src, {"RELEASE_CHECKLIST_ENABLED": "true"}) == "a\nX\nb\n"


def test_placeholders_known_and_builder_check_clean():
    from lib.consistency.placeholders import check_builder_known_set

    assert [
        f for f in check_builder_known_set(REPO_ROOT) if "RELEASE_CHECKLIST" in f.message
    ] == []


def test_standalone_fallbacks():
    from lib.standalone import _CONDITIONAL_FALSE_FLAGS, _ORCHESTRATION_FALLBACKS

    assert _CONDITIONAL_FALSE_FLAGS["RELEASE_CHECKLIST_ENABLED"] == "false"
    assert _ORCHESTRATION_FALLBACKS["RELEASE_CHECKLIST_BLOCK"] == ""


def test_sync_concept_documents_placeholders():
    doc = (REPO_ROOT / "docs/guides/features/sync-concept.md").read_text(encoding="utf-8")
    for name in (
        "RELEASE_CHECKLIST_MODE",
        "RELEASE_CHECKLIST_ENABLED",
        "RELEASE_CHECKLIST_BLOCK",
    ):
        assert name in doc
    assert "{{RELEASE_CHECKLIST_BLOCK}}" not in doc
    assert "{{%RELEASE_CHECKLIST_BLOCK%}}" in doc
