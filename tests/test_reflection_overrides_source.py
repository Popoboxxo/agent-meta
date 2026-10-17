"""IC-15 Nr. 17 / AC-51: reflection overrides come from the CONSUMER config.

Before the fix ``_build_pipeline_variables`` called
``load_project_overrides(agent_meta_root/.meta-config/project.yaml)`` — i.e.
agent-meta's OWN tracked config — so a consumer project without a
``reflection-pairs`` block inherited agent-meta's ``MAX_ITERATIONS`` (5) instead
of the framework default (3). These tests pin that the override source is the
``config`` dict handed to ``build_variables``.

Red (before the fix): ``test_consumer_without_overrides_gets_framework_default``
and ``test_consumer_override_wins`` fail — both observe agent-meta's own value.
Green: the consumer config (absent block -> default, present block -> project
value) drives ``MAX_ITERATIONS``.

Run: python -m pytest tests/test_reflection_overrides_source.py -q
"""

from __future__ import annotations

import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.config import build_variables, load_config  # noqa: E402

_AGENT_META_ROOT = _REPO_ROOT
_PROJECT_YAML = _REPO_ROOT / ".meta-config" / "project.yaml"


def _consumer_config() -> dict:
    """The tracked config WITHOUT its own ``reflection-pairs`` block."""
    config = load_config(_PROJECT_YAML)
    config.pop("reflection-pairs", None)
    return config


def test_agent_meta_own_override_differs_from_framework_default():
    """Precondition of the leak: agent-meta's own config overrides the default."""
    owner = load_config(_PROJECT_YAML)
    override = (
        (owner.get("reflection-pairs") or {})
        .get("overrides", {})
        .get("dev-review-loop", {})
        .get("max_iterations")
    )
    assert override is not None
    assert override != 3


def test_consumer_without_overrides_gets_framework_default():
    """AC-51: no ``reflection-pairs`` -> MAX_ITERATIONS is the framework value."""
    variables, _ = build_variables(_consumer_config(), _AGENT_META_ROOT)
    assert variables["REFLECTION_PAIRS_ENABLED"] == "true"
    assert variables["MAX_ITERATIONS"] == "3"


def test_consumer_override_wins():
    """AC-51: an explicit project override is honored."""
    config = _consumer_config()
    config["reflection-pairs"] = {
        "overrides": {"dev-review-loop": {"max_iterations": 9}}
    }
    variables, _ = build_variables(config, _AGENT_META_ROOT)
    assert variables["MAX_ITERATIONS"] == "9"
