"""One emission predicate decides whether the orchestrator role is written (R1).

SPEC-orchestrator-topology-2026-11-03, P2 (issue #1077), Task 13.

``_should_skip_role`` used to read ``ORCH_MODE_MAIN_CHAT`` from the rendered
variables — a second, independent decision next to the #1090 predicate
``active_set.role_emitted_for_provider``. The skip now goes through that
predicate only:

* global ``orchestrator.mode: main-chat`` -> the role is skipped;
* a provider override ``mode: main-chat`` -> the role is skipped for that
  provider;
* ``topology: subagent`` -> the orchestrator.md is still emitted (as a
  subagent); only the entry point/gate are withheld.

The AST assertions pin the structural half of R1: the module contains no
second ``ORCH_MODE_MAIN_CHAT`` read and exactly one function calls the
predicate.

Run: python3 -m pytest tests/test_orchestrator_topology_skip_role.py -q
"""
from __future__ import annotations

import ast
from pathlib import Path

_REPO_ROOT = Path(__file__).resolve().parent.parent
_AGENT_SYNC = _REPO_ROOT / "scripts" / "lib" / "agent_sync.py"

import sys  # noqa: E402

sys.path.insert(0, str(_REPO_ROOT / "scripts"))

from lib.agent_sync import _should_skip_role  # noqa: E402

_ROLE_MAP = {"orchestrator": "orchestrator", "developer": "developer"}
_PC = {"agent_ext": ".md"}


def _skip(config: dict, provider: str = "Opencode", tmp_path: Path | None = None):
    tmp = tmp_path or Path("/tmp")
    return _should_skip_role(
        role="orchestrator",
        source_path=tmp / "agents" / "1-generic" / "orchestrator.md",
        provider=provider,
        pc=_PC,
        role_map=_ROLE_MAP,
        allowed_roles=None,
        config=config,
        variables={},
        project_root=tmp,
        target_dir=tmp / "agents",
        log=_SilentLog(),
    )


class _SilentLog:
    def skip(self, *args, **kwargs):
        pass

    def warning(self, *args, **kwargs):
        pass


# --- behaviour: the predicate decides --------------------------------------


def test_global_main_chat_skips_the_orchestrator(tmp_path):
    skip, filename = _skip({"orchestrator": {"mode": "main-chat"}}, tmp_path=tmp_path)
    assert (skip, filename) == (True, "orchestrator.md")


def test_provider_override_main_chat_skips_the_orchestrator(tmp_path):
    config = {
        "orchestrator": {
            "mode": "strict",
            "provider-overrides": {"Opencode": {"mode": "main-chat"}},
        }
    }
    skip, filename = _skip(config, tmp_path=tmp_path)
    assert (skip, filename) == (True, "orchestrator.md")


def test_subagent_topology_still_emits_the_orchestrator(tmp_path):
    # Topology changes the POSITION, not whether the file exists: under
    # `subagent` the role is a spawned subagent and must still be written.
    skip, filename = _skip(
        {"orchestrator": {"mode": "strict", "topology": "subagent"}},
        tmp_path=tmp_path,
    )
    assert (skip, filename) == (False, "orchestrator.md")


# --- structure: exactly one decision point ---------------------------------

def _functions_referencing(name: str) -> set:
    tree = ast.parse(_AGENT_SYNC.read_text(encoding="utf-8"))
    callers = set()
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            identifiers = {
                child.id for child in ast.walk(node) if isinstance(child, ast.Name)
            }
            if name in identifiers:
                callers.add(node.name)
    return callers


def test_exactly_one_function_calls_the_emission_predicate():
    assert _functions_referencing("role_emitted_for_provider") == {"_should_skip_role"}


def test_agent_sync_has_no_second_main_chat_read():
    tree = ast.parse(_AGENT_SYNC.read_text(encoding="utf-8"))
    string_constants = {
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant) and isinstance(node.value, str)
    }
    assert "ORCH_MODE_MAIN_CHAT" not in string_constants
