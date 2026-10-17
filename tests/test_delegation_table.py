import re
from pathlib import Path

from scripts.lib.config import build_variables, load_config
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
    assert "`developer`" in table


REPO_ROOT = Path(__file__).resolve().parents[1]
_ORCHESTRATOR_TEMPLATE = REPO_ROOT / "agents" / "1-generic" / "orchestrator.md"
_SEPARATOR_RE = re.compile(r"^\s*\|(?:\s*:?-{2,}:?\s*\|)+\s*$")


def _rendered_delegation_table(mode: str) -> str:
    config = {**load_config(REPO_ROOT / ".meta-config" / "project.yaml"),
              "context_file": {"mode": mode}}
    variables, _ = build_variables(config, REPO_ROOT)
    return variables["AGENT_DELEGATION_TABLE"]


def _header_count(text: str) -> int:
    return sum(1 for line in text.splitlines() if _SEPARATOR_RE.match(line))


def test_delegation_table_is_one_dense_table_in_both_modes():
    for mode in ("full", "compact"):
        table = _rendered_delegation_table(mode)
        assert _header_count(table) == 1, f"{mode}: expected exactly one header row"
        assert "\n\n" not in table, f"{mode}: blank line inside the delegation table"


def test_orchestrator_agent_table_renders_a_single_header():
    src = _ORCHESTRATOR_TEMPLATE.read_text(encoding="utf-8")
    block = src.split("**Agent table:**", 1)[1].split(
        "<!-- agent-meta:managed-end -->", 1)[0]
    for mode in ("full", "compact"):
        rendered = block.replace(
            "{{AGENT_DELEGATION_TABLE}}", _rendered_delegation_table(mode))
        assert _header_count(rendered) == 1, f"{mode}: duplicate table header"
        assert "\n\n| `" not in rendered, f"{mode}: blank line between delegation rows"  # developer is a 'required' tier role
