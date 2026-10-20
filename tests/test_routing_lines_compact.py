"""IC-04 compact routing line format (Task 2b.1, SPEC-CONTEXT-PROFILES-2026-10-11).

Covers ``agents.render_routing_lines`` / ``agents.select_routing_examples`` and
the ``compact`` branch of
``agents.build_routing_tool_definitions_for_providers``:

- line form ``<agent>|<flags>|<kw1>;<kw2>|<example>[/<example>]``,
- flags ``req``/``rec``/``orch-only``/``name-only`` only when non-default, in
  that fixed order; empty flags render as ``||``,
- every keyword is kept (canonical/language-neutral),
- examples are language-selected upstream by ``get_routing_rules`` (via
  ``_select_examples``); the keyword set is identical across languages
  (AC-69 line-format part),
- ``;`` or ``|`` in a keyword raises ``SyncError`` naming role and keyword
  (AC-31),
- pipeline lines ``pipeline:<name>|<signal_keywords>``,
- one ``name-only: <agent> (<reason>); …`` summary line,
- the branch is opt-in: without ``context-profile: compact`` every render stays
  byte-identical (AC-01/AC-35).

Deliberate deviation (C2 precedence, plan Task 2b.1): there is deliberately NO
compact branch for ``PIPELINE_MATCH_TABLE`` — the §2 pipeline table stays
verbatim under ``compact``. The IC-04 "single-source" clause is revisable only
after the 2f eval, so it is intentionally not implemented here (this module only
pins the §3 line form).
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from scripts.lib.agents import (
    ROUTING_TOOL_NAME,
    build_routing_tool_definition,
    build_routing_tool_definitions_for_providers,
    render_routing_lines,
    render_routing_tool_definition,
    select_routing_examples,
)
from scripts.lib.delegation_table import get_routing_rules
from scripts.lib.io import SyncError

_AGENT_META_ROOT = Path(".")

# Same gate set as tests/test_routing_tool_definitions.py: SE cascade, knowledge
# engine and developer tiers off so the expected keyword lines stay stable.
_BASE_VARIABLES: dict = {
    "SE_ENABLED": "false",
    "VALIDATOR_ENABLED": "true",
    "KNOWLEDGE_ENGINE_ENABLED": "false",
    "DEVELOPER_TIERS_ENABLED": "false",
}


def _write_roles(root: Path, body: str) -> None:
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "role-defaults.yaml").write_text(body, encoding="utf-8")


def _name_only_entries(name_index: list[dict]) -> list[dict]:
    return [
        {"agent": entry["agent"], "reason": entry.get("name_only_reason", "")}
        for entry in name_index
        if entry.get("addressability") == "name_only"
    ]


# ---------------------------------------------------------------------------
# select_routing_examples — keyword-redundant examples are dropped
# ---------------------------------------------------------------------------

def test_select_routing_examples_keeps_first_and_drops_keyword_echoes():
    rule = {
        "agent": "developer",
        "keywords": ["Bugfix"],
        "examples": ["Fix den Bugfix jetzt", "Etwas anderes", "noch ein bugfix spaeter"],
    }
    # The first example is always kept, later examples that contain an own
    # keyword (case-insensitive substring) add no routing signal and are dropped.
    assert select_routing_examples(rule) == ["Fix den Bugfix jetzt", "Etwas anderes"]


def test_select_routing_examples_empty_without_examples():
    assert select_routing_examples({"keywords": ["Bugfix"], "examples": []}) == []


# ---------------------------------------------------------------------------
# render_routing_lines — line form, sorting, flags, keywords
# ---------------------------------------------------------------------------

def test_render_routing_lines_sorted_flags_and_keywords():
    rules = [
        {
            "agent": "tester", "tier": "recommended", "orchestrator_only": False,
            "keywords": ["Test", "Verifikation"],
            "examples": ["Schreibe Tests", "Tests gruen"],
        },
        {
            "agent": "developer", "tier": "required", "orchestrator_only": False,
            "keywords": ["Bugfix", "Refactoring"],
            "examples": ["Fix den Bug", "Refactoring bitte"],
        },
    ]
    rendered = render_routing_lines(rules, [], [])
    assert rendered == (
        "developer|req|Bugfix;Refactoring|Fix den Bug\n"
        "tester|rec|Test;Verifikation|Schreibe Tests\n"
    )


def test_render_routing_lines_empty_flags_render_double_pipe():
    rules = [{
        "agent": "optional-role", "tier": "optional", "orchestrator_only": False,
        "keywords": ["Irgendwas"], "examples": [],
    }]
    assert render_routing_lines(rules, [], []) == "optional-role||Irgendwas|\n"


def test_render_routing_lines_flag_order_and_name_only_flag():
    rules = [{
        "agent": "escalation-role", "tier": "required", "orchestrator_only": True,
        "keywords": ["Eskalation"], "examples": ["Eskaliere"],
    }]
    name_only = [{"agent": "escalation-role", "reason": "nur per Name"}]
    lines = render_routing_lines(rules, [], name_only).splitlines()
    # Fixed flag order: req, rec, orch-only, name-only.
    assert lines[0] == "escalation-role|req,orch-only,name-only|Eskalation|Eskaliere"
    assert lines[1] == "name-only: escalation-role (nur per Name)"


def test_render_routing_lines_keeps_all_keywords():
    rules = [{
        "agent": "dev", "tier": "optional", "orchestrator_only": False,
        "keywords": ["Bugfix", "Refactoring", "Implementierung", "Code schreiben"],
        "examples": [],
    }]
    assert render_routing_lines(rules, [], "") == (
        "dev||Bugfix;Refactoring;Implementierung;Code schreiben|\n"
    )


@pytest.mark.parametrize("keyword", ["Bug;fix", "Bug|fix"])
def test_render_routing_lines_keyword_separator_raises_sync_error(keyword):
    rules = [{
        "agent": "dev-role", "tier": "optional", "orchestrator_only": False,
        "keywords": [keyword], "examples": [],
    }]
    with pytest.raises(SyncError) as excinfo:
        render_routing_lines(rules, [], [])
    message = str(excinfo.value)
    assert "dev-role" in message, "the SyncError must name the role"
    assert keyword in message, "the SyncError must name the offending keyword"


def test_render_routing_lines_pipeline_and_name_only_lines():
    pipelines = [
        {"route": "pipeline", "pipeline": "quick-fix", "keywords": ["Bug fixen", "Hotfix"]},
    ]
    name_only = [
        {"agent": "principal-developer", "reason": "last resort"},
        {"agent": "intern-developer", "reason": "trivial"},
    ]
    assert render_routing_lines([], pipelines, name_only) == (
        "pipeline:quick-fix|Bug fixen;Hotfix\n"
        "name-only: intern-developer (trivial); principal-developer (last resort)\n"
    )


def test_render_routing_lines_empty_input_is_empty_string():
    assert render_routing_lines([], [], []) == ""


# ---------------------------------------------------------------------------
# Language-selected examples via get_routing_rules (AC-69 line-format part)
# ---------------------------------------------------------------------------

_DE_EN_ROLES = (
    "roles:\n"
    "  dev-role:\n"
    "    model: fast\n"
    "    workflow_tier: required\n"
    "    routing_patterns:\n"
    "      keywords:\n"
    "      - Canonical-Keyword\n"
    "      examples:\n"
    "        Deutsch:\n"
    "        - Deutsches Beispiel\n"
    "        English:\n"
    "        - English example\n"
)


def test_compact_lines_select_language_but_keep_keywords(tmp_path):
    _write_roles(tmp_path, _DE_EN_ROLES)
    variables = {k: "false" for k in _BASE_VARIABLES}
    template_roles = {"dev-role"}

    def rendered(language: str) -> str:
        data = get_routing_rules(
            tmp_path, {}, variables, template_roles=template_roles, language=language
        )
        return render_routing_lines(data["rules"], data["pipelines"], []).splitlines()[0]

    de = rendered("Deutsch")
    en = rendered("English")
    assert de == "dev-role|req|Canonical-Keyword|Deutsches Beispiel"
    assert en == "dev-role|req|Canonical-Keyword|English example"
    # Keywords stay canonical/language-neutral — identical in both renders.
    assert de.split("|")[2] == en.split("|")[2] == "Canonical-Keyword"


# ---------------------------------------------------------------------------
# compact branch of build_routing_tool_definitions_for_providers
# ---------------------------------------------------------------------------

def test_full_path_without_opt_in_is_byte_identical():
    config = {"roles": ["developer", "tester"]}
    definition = build_routing_tool_definition(_AGENT_META_ROOT, config, dict(_BASE_VARIABLES))
    rendered = build_routing_tool_definitions_for_providers(
        _AGENT_META_ROOT, config, dict(_BASE_VARIABLES), providers=["Claude", "Continue"]
    )
    assert rendered["Claude"] == render_routing_tool_definition(definition, "json")
    assert rendered["Continue"] == render_routing_tool_definition(definition, "yaml_text_block")


def test_compact_opt_in_renders_lines_instead_of_tool_json():
    config = {"roles": ["developer", "tester"], "context-profile": "compact"}
    body = build_routing_tool_definitions_for_providers(
        _AGENT_META_ROOT, config, dict(_BASE_VARIABLES), providers=["Claude"]
    )["Claude"]
    assert not body.lstrip().startswith("{"), "compact must not emit the JSON tool envelope"
    assert '"tool"' not in body, "tool{} is absent while ROUTE_INTENT_CALLABLE=false (AC-31)"
    dev_line = next(line for line in body.splitlines() if line.startswith("developer|"))
    assert dev_line == (
        "developer|req|Bugfix;Refactoring;Implementierung;Code schreiben"
        "|Implementiere das Feature X./Fixe den Bug in cache.py."
    )


def test_compact_not_active_when_route_intent_is_callable(monkeypatch):
    from scripts.lib.delegation_syntax import DelegationSyntaxEngine

    monkeypatch.setattr(
        DelegationSyntaxEngine, "has_route_intent_tool", lambda self, _provider: True
    )
    config = {"roles": ["developer", "tester"], "context-profile": "compact"}
    body = build_routing_tool_definitions_for_providers(
        _AGENT_META_ROOT, config, dict(_BASE_VARIABLES), providers=["Claude"]
    )["Claude"]
    # ROUTE_INTENT_CALLABLE=true keeps the tool{} definition (IC-04).
    assert json.loads(body)["tool"]["name"] == ROUTING_TOOL_NAME


def test_compact_branch_is_scoped_per_provider_override(tmp_path):
    _write_roles(tmp_path, _DE_EN_ROLES)
    config = {
        "provider-overrides": {"Claude": {"context-profile": "compact"}},
    }
    rendered = build_routing_tool_definitions_for_providers(
        tmp_path, config, dict(_BASE_VARIABLES), providers=["Claude", "Continue"],
        template_roles={"dev-role"},
    )
    # Claude is compact → line form; Continue stays full → YAML tool definition.
    assert not rendered["Claude"].lstrip().startswith("{")
    assert rendered["Claude"].split("|")[0] == "dev-role"
    assert "tool:" in rendered["Continue"], "the full YAML render is unchanged"


def test_compact_lines_include_name_only_summary(tmp_path):
    _write_roles(
        tmp_path,
        "roles:\n"
        "  kw-role:\n"
        "    model: fast\n"
        "    workflow_tier: required\n"
        "    routing:\n"
        "      addressability: keyword\n"
        "    routing_patterns:\n"
        "      keywords:\n"
        "      - Keyword-A\n"
        "      examples:\n"
        "      - Beispiel A\n"
        "  named-role:\n"
        "    model: fast\n"
        "    workflow_tier: optional\n"
        "    routing:\n"
        "      addressability: name_only\n"
        "      name_only_reason: Nur per Name erreichbar.\n",
    )
    config = {"context-profile": "compact"}
    body = build_routing_tool_definitions_for_providers(
        tmp_path, config, dict(_BASE_VARIABLES), providers=["Claude"],
        template_roles={"kw-role", "named-role"},
    )["Claude"]
    assert "kw-role|req|Keyword-A|Beispiel A" in body
    assert "name-only: named-role (Nur per Name erreichbar.)" in body
