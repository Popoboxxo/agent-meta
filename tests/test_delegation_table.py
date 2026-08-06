from pathlib import Path

from scripts.lib.delegation_table import get_intent_routing_table


def test_intent_routing_table_includes_pipeline_rows(tmp_path):
    agent_meta_root = Path(".")
    config = {}
    variables = {
        "SE_ENABLED": "false",
        "VALIDATOR_ENABLED": "true",
        "KNOWLEDGE_ENGINE_ENABLED": "false",
        "DEVELOPER_TIERS_ENABLED": "false",
    }
    pipelines = {
        "feature-lifecycle": {
            "signal_keywords": ["Feature implementieren", "Feature bauen", "neues Feature"],
            "stages": [],
        },
        "quick-fix": {
            "signal_keywords": ["Bug fixen"],
            "stages": [],
        },
    }
    table = get_intent_routing_table(agent_meta_root, config, variables, pipelines=pipelines)
    assert "Feature implementieren, Feature bauen, neues Feature" in table
    assert "→ Pipeline: `feature-lifecycle`" in table
    assert "→ Pipeline: `quick-fix`" in table


def test_intent_routing_table_without_pipelines_arg_is_unchanged():
    agent_meta_root = Path(".")
    config = {}
    variables = {
        "SE_ENABLED": "false",
        "VALIDATOR_ENABLED": "true",
        "KNOWLEDGE_ENGINE_ENABLED": "false",
        "DEVELOPER_TIERS_ENABLED": "false",
    }
    # No pipelines= argument at all — must not raise, must not include any
    # "→ Pipeline:" rows (backward compatible with any caller not yet updated).
    table = get_intent_routing_table(agent_meta_root, config, variables)
    assert "→ Pipeline:" not in table
