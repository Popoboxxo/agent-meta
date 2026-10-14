"""IC-18 no. 8 (Task 1.16, AC-49 part): persona, section 11 fallback and SE prose.

The orchestrator's static prose follows the ActiveSet: the fallback chain names
``meta-feedback`` only when it is active (otherwise ASK), the AI review routing
names ``ai-security-guardian``/``llm-evaluator``/``ai-governance-engineer`` only
when all three are active, the SE-mode prose depends on ``SE_ENABLED``, and the
static prose names only rendered pipelines (closes the PR C known interim:
``concept-driven-dev``/``feature-lifecycle`` were still named after the default
pipeline drop).
"""
from __future__ import annotations

import pytest

from tests.active_set_render import (
    default_config,
    fixture_config,
    section,
    sync_config,
    tiers_on_config,
)

_AI_ROLES = ("ai-security-guardian", "llm-evaluator", "ai-governance-engineer")
_DROPPED_DEFAULT_PIPELINES = ("concept-driven-dev", "feature-lifecycle")


@pytest.fixture(scope="module")
def projects(tmp_path_factory):
    root = tmp_path_factory.mktemp("prose")
    return {
        "p10": sync_config(root / "p10", fixture_config("p10")),
        "default": sync_config(root / "default", default_config()),
        "all": sync_config(root / "all", tiers_on_config()),
    }


def _orchestrator(project) -> str:
    return (project / ".claude" / "agents" / "orchestrator.md").read_text(encoding="utf-8")


def test_p10_without_meta_feedback_asks_the_user(projects):
    text = _orchestrator(projects["p10"])
    assert "meta-feedback" not in text
    fallback = section(text, "## 11. Unknown intent protocol", "## 12. ")
    assert "2. Fallback: ASK — Rückfrage an den Nutzer via `main_chat` → main-chat" in fallback


def test_p10_names_no_inactive_ai_review_role(projects):
    text = _orchestrator(projects["p10"])
    for role in _AI_ROLES + ("effort-estimator", "se-critic"):
        assert role not in text, role
    assert "matching active specialist role of the agent table" in text


def test_default_keeps_meta_feedback_fallback_and_ai_routing(projects):
    text = _orchestrator(projects["default"])
    assert "2. Fallback: ask-user via `main_chat` → meta-feedback → main-chat" in text
    assert "Fallbacks: meta-feedback=" in text
    assert ("Route AI-specific risk patterns to `ai-security-guardian`, output quality to "
            "`llm-evaluator`, and model risk to `ai-governance-engineer`;") in text


@pytest.mark.parametrize("name", ["p10", "default", "all"])
def test_se_prose_only_with_se_enabled(projects, name):
    # SE is a config_flag gate: off in all three projects.
    assert "**SE mode:**" not in _orchestrator(projects[name])


def test_default_static_prose_names_no_dropped_pipeline(projects):
    text = _orchestrator(projects["default"])
    for pipeline in _DROPPED_DEFAULT_PIPELINES:
        assert pipeline not in text, pipeline
    assert "otherwise ad-hoc decomposition along §4 task-size routing" in text


def test_all_roles_keeps_pipeline_prose(projects):
    text = _orchestrator(projects["all"])
    assert "Signal-Keywords → Pipeline `concept-driven-dev` (§2)." in text
    assert "dann `feature-lifecycle` pipeline |" in text
    assert "(z.B. `feature-lifecycle` → Stage `implement`), und KEIN Plan existiert:" in text
