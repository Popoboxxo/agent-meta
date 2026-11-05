"""P3 (AC-9 gate part): the A2A rule names the multi-instance limit.

The rule's ``{{else}}`` branch (topology key unset) must stay word-identical
to today's wording — the two ``tests/fixtures/topology-golden`` fixtures prove
the byte identity end-to-end. Only the explicit-topology branch may render the
``{{ORCH_MAX_INSTANCES}}`` limit, and it must render the *effective*,
provider-scoped count (``rules.py::_merged_rule_vars``), not the global one.

Run: python3 -m pytest tests/test_a2a_instance_wording.py -q
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(_REPO_ROOT))

from scripts.lib.rules import _merged_rule_vars  # noqa: E402
from scripts.lib.variables import (  # noqa: E402
    strip_inactive_conditional_blocks,
    substitute,
)

_RULE_SOURCE = _REPO_ROOT / "rules" / "1-generic" / "a2a-delegation-gates.md"

#: The historic ``{{else}}`` wording, pinned verbatim. The source branch must
#: still be exactly this string — an unset topology renders today's bytes.
_HISTORIC_ELSE_BRANCH = (
    "2. **Orchestrator-Singleton:** NUR `main_chat` darf den `orchestrator` "
    "spawnen. Worker{{#if ROLE_ORCHESTRATOR_ACTIVE}} → `orchestrator`{{/if}} "
    "→ HARD REJECT (siehe `singleton-orchestrator-architecture.md`)."
)

_OPEN = "{{#if ORCH_TOPOLOGY_EXPLICIT}}"
_ELSE = "{{else}}"
_CLOSE = "\n{{/if}}"


def _topology_block() -> str:
    """Return the Gate-2 conditional block from the real rule source."""
    text = _RULE_SOURCE.read_text(encoding="utf-8")
    start = text.index(_OPEN)
    end = text.index(_CLOSE, start) + len(_CLOSE)
    return text[start:end]


def _else_branch_source() -> str:
    """Extract the ``{{else}}`` branch, including the nested role conditional."""
    block = _topology_block()
    start = block.index(_ELSE) + len(_ELSE)
    end = block.rindex(_CLOSE)
    return block[start:end]


def _render_gate(variables: dict) -> str:
    rendered = substitute(_topology_block(), variables, "a2a-instance-wording", None)
    return strip_inactive_conditional_blocks(rendered, variables)


def test_unset_topology_renders_word_identical_else_branch():
    """AC-6: an unset topology keeps the historic singleton wording byte-exactly."""
    else_source = _else_branch_source()
    assert else_source.strip("\n") == _HISTORIC_ELSE_BRANCH

    variables = {
        "ORCH_TOPOLOGY_EXPLICIT": "false",
        "ORCH_TOPOLOGY": "",
        "ORCH_MAX_INSTANCES": "1",
        "ROLE_ORCHESTRATOR_ACTIVE": "true",
    }
    rendered = _render_gate(variables)
    expected = strip_inactive_conditional_blocks(
        else_source, {"ROLE_ORCHESTRATOR_ACTIVE": "true"}
    )
    assert rendered.strip("\n") == expected.strip("\n")
    assert "Orchestrator-Singleton" in rendered
    assert "Orchestrator-Topologie" not in rendered
    assert "ORCH_MAX_INSTANCES" not in rendered
    assert "Höchstens" not in rendered


def test_n1_renders_the_singular_limit():
    """Explicit topology with one instance renders the singular count ``1``."""
    rendered = _render_gate({
        "ORCH_TOPOLOGY_EXPLICIT": "true",
        "ORCH_TOPOLOGY": "subagent",
        "ORCH_MAX_INSTANCES": "1",
        "ROLE_ORCHESTRATOR_ACTIVE": "true",
    })
    assert re.search(r"Höchstens\s+1\s+gleichzeitig", rendered), rendered
    assert "Orchestrator-Topologie (subagent)" in rendered
    assert "Genau eine Instanz" not in rendered
    assert "ORCH_MAX_INSTANCES" not in rendered


def test_n_greater_than_one_names_the_limit():
    """Explicit topology with N>1 names ``N`` plus the identity/scope contract."""
    rendered = _render_gate({
        "ORCH_TOPOLOGY_EXPLICIT": "true",
        "ORCH_TOPOLOGY": "hybrid",
        "ORCH_MAX_INSTANCES": "4",
        "ROLE_ORCHESTRATOR_ACTIVE": "true",
    })
    assert re.search(r"Höchstens\s+4\s+gleichzeitig", rendered), rendered
    assert "eindeutiger `orchestrator_id`" in rendered
    assert "disjunktem Scope" in rendered
    assert "HARD ERROR beim Spawn" in rendered
    assert "ORCH_MAX_INSTANCES" not in rendered


def test_merged_rule_vars_resolves_effective_instance_count(tmp_path):
    """``variables=None`` still yields the provider-scoped effective count.

    Claude advertises ``orchestrator_instances.multiple: true``; Continue
    advertises ``false`` and must therefore clamp N=4 back to 1 at render time.
    """
    config = {
        "orchestrator": {
            "topology": "subagent",
            "max-instances": 4,
        }
    }

    claude = _merged_rule_vars(
        _REPO_ROOT, tmp_path, config, "Claude", {}, None
    )
    assert claude["ORCH_MAX_INSTANCES"] == "4"
    assert claude["ORCH_TOPOLOGY_EXPLICIT"] == "true"

    continue_vars = _merged_rule_vars(
        _REPO_ROOT, tmp_path, config, "Continue", {}, None
    )
    assert continue_vars["ORCH_MAX_INSTANCES"] == "1"
