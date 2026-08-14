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


def test_intent_routing_table_drops_per_agent_rows():
    # Phase D (token-efficiency review): individual-agent routing rows are
    # redundant with name+description already in the system prompt — only
    # pipeline rows (and the Tiers summary) belong in this table now.
    agent_meta_root = Path(".")
    config = {}
    variables = {
        "SE_ENABLED": "false",
        "VALIDATOR_ENABLED": "true",
        "KNOWLEDGE_ENGINE_ENABLED": "false",
        "DEVELOPER_TIERS_ENABLED": "false",
    }
    pipelines = {
        "quick-fix": {"signal_keywords": ["Bug fixen"], "stages": []},
    }
    table = get_intent_routing_table(agent_meta_root, config, variables, pipelines=pipelines)
    # A single-agent-only row that used to exist (e.g. developer's own
    # intent_keywords) must not appear as its own table row anymore.
    assert "| `developer` |" not in table
    assert "→ Pipeline: `quick-fix`" in table


def test_intent_routing_table_includes_tiers_summary_line():
    agent_meta_root = Path(".")
    config = {}
    variables = {
        "SE_ENABLED": "false",
        "VALIDATOR_ENABLED": "true",
        "KNOWLEDGE_ENGINE_ENABLED": "false",
        "DEVELOPER_TIERS_ENABLED": "false",
    }
    table = get_intent_routing_table(agent_meta_root, config, variables, pipelines={})
    assert "**Tiers**" in table
    assert "recommended:" in table
    assert "required:" in table
    assert "`developer`" in table  # developer is a 'required' tier role
