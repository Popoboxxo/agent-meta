"""Unit tests for the #1323 config-vs-allow-list consistency check.

The check is INFO-only and non-destructive: it compares the tool names declared
in the provider-capability config against the case literals of
``hook_known_tool_name`` in ``hooks/1-generic/lib/hook_common.sh``. It is a
config<->allow-list comparison, never a live harness feed, and never imports a
documentation snapshot from ``tests/``.
"""
import sys
from pathlib import Path
from types import SimpleNamespace

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.cli_commands import _doctor_exit_code  # noqa: E402
from lib.consistency.hook_known_tool_names import (  # noqa: E402
    check_unknown_tool_names,
    load_expected_tool_names,
    parse_known_tool_names,
)
from lib.consistency.report import Finding, Severity, print_report  # noqa: E402
from lib.doctor_detectors import _raw_findings  # noqa: E402
from lib.doctor_predicates import Env  # noqa: E402

HOOK_LIB_REL = Path("hooks/1-generic/lib/hook_common.sh")
CHECK_ID = "hooks.unknown-tool-name"

_HOOK_LIB = """\
#!/bin/bash
# hook_known_tool_name -- synthetic allow-list for the unit tests.
hook_known_tool_name() {
  case "$1" in
    mcp__?*__?*) return 0 ;;
    KnownTool|OtherTool|SendMessage) return 0 ;;
  esac
  return 1
}
"""

_CAPS = """\
capabilities:
  Claude:
    native_agent_tools: ["KnownTool", "othertool"]
    worker_control_tools: ["SendMessage"]
"""

_TOOLS = """\
claude:
  - KnownTool
  - OtherTool
  - mcp__*
claude-silent:
  - HiddenTool
opencode_deny_critical:
  - DeniedTool
opencode_primary_edit_allow:
  - EditOnlyPath
terminal_tool:
  Claude: SomeTerminal
"""


def _setup(tmp_path, *, hook=_HOOK_LIB, caps=_CAPS, tools=_TOOLS):
    """Create a tiny framework root with the two config data sources."""
    root = tmp_path / "agent-meta"
    (root / HOOK_LIB_REL.parent).mkdir(parents=True, exist_ok=True)
    (root / HOOK_LIB_REL).write_text(hook, encoding="utf-8")
    (root / "config").mkdir(parents=True, exist_ok=True)
    (root / "config" / "provider-capabilities.yaml").write_text(caps, encoding="utf-8")
    (root / "config" / "provider-tools.yaml").write_text(tools, encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()
    return project, root


def _with_caps(tmp_path, caps):
    return _setup(tmp_path, caps=caps)


# --- parse_known_tool_names --------------------------------------------------

def test_parse_known_tool_names_extracts_case_literals_only():
    names = parse_known_tool_names(_HOOK_LIB)

    assert names == {"KnownTool", "OtherTool", "SendMessage"}
    assert "mcp__?*__?*" not in names          # wildcard is not a literal
    assert "EnterWorktree" not in names        # comment-only mention


def test_parse_known_tool_names_stops_at_indented_esac():
    # Regression (#1323 review): the shipped hook closes its case with an
    # indented ``  esac``. A later ``return 0 ;;`` arm must not be folded in.
    source = """\
hook_known_tool_name() {
  case "$1" in
    KnownTool|OtherTool|SendMessage) return 0 ;;
  esac
  return 1
}

decoy_hook() {
  case "$1" in
    DecoyTool) return 0 ;;
  esac
}
"""
    names = parse_known_tool_names(source)

    assert names == {"KnownTool", "OtherTool", "SendMessage"}
    assert "DecoyTool" not in names  # trailing arm after the function's esac


def test_parse_known_tool_names_is_fail_soft_without_function():
    assert parse_known_tool_names("# no hook function here\n") == frozenset()
    assert parse_known_tool_names("") == frozenset()


# --- load_expected_tool_names (config data source, not tests snapshot) -------

def test_load_expected_tool_names_reads_config_and_filters_meta_keys(tmp_path):
    _, root = _setup(tmp_path)

    expected = load_expected_tool_names(root)

    assert expected == frozenset({"knowntool", "othertool", "sendmessage"})
    assert "hiddentool" not in expected        # claude-silent excluded
    assert "deniedtool" not in expected        # opencode_deny_critical excluded
    assert "editonlypath" not in expected      # opencode_primary_edit_allow excluded
    assert "someterminal" not in expected      # terminal_tool excluded
    assert not any(n.startswith("mcp__") for n in expected)


# --- AC-1 / AC-2: unknown tool -> INFO finding, rc 0, non-destructive --------

def test_clean_config_has_no_deltas(tmp_path):
    project, root = _setup(tmp_path)

    assert check_unknown_tool_names(project, root, {}, {}) == []


def test_unknown_tool_is_one_info_finding_and_never_blocks(tmp_path):
    project, root = _with_caps(
        tmp_path,
        _CAPS.replace('["KnownTool", "othertool"]', '["KnownTool", "othertool", "FutureTool"]'),
    )

    findings = check_unknown_tool_names(project, root, {}, {})

    assert len(findings) == 1
    finding = findings[0]
    assert finding.severity == Severity.INFO
    assert finding.check == CHECK_ID
    assert finding.file == "hooks/1-generic/lib/hook_common.sh"
    assert "FutureTool" in finding.message
    assert "hook_known_tool_name" in finding.suggestion
    # Non-destructive: no source/config file was modified.
    assert (project.parent / "agent-meta" / HOOK_LIB_REL).read_text(encoding="utf-8") == _HOOK_LIB
    # print_report derives rc from ERROR only -- INFO stays at 0.
    assert print_report(findings, project, changed_only=False) == 0


# --- AC-3: doctor --strict stays at rc 0 ------------------------------------

def test_doctor_strict_does_not_escalate_info_finding(tmp_path):
    project, root = _with_caps(
        tmp_path,
        _CAPS.replace('["KnownTool", "othertool"]', '["KnownTool", "othertool", "FutureTool"]'),
    )
    findings = check_unknown_tool_names(project, root, {}, {})

    assert _doctor_exit_code(SimpleNamespace(findings=findings), strict=True) == 0
    assert _doctor_exit_code(SimpleNamespace(findings=findings), strict=False) == 0


# --- AC-4: config<->allow-list deltas, direction-specific INFO --------------

def test_deltas_are_direction_specific_info_findings(tmp_path):
    hook = _HOOK_LIB.replace("KnownTool|OtherTool|SendMessage",
                             "KnownTool|OtherTool|SendMessage|AllowedOnly")
    caps = _CAPS.replace('["KnownTool", "othertool"]',
                         '["KnownTool", "othertool", "AliasTool"]')
    project, root = _setup(tmp_path, hook=hook, caps=caps)

    findings = check_unknown_tool_names(project, root, {}, {})

    assert len(findings) == 2
    assert all(f.severity == Severity.INFO and f.check == CHECK_ID for f in findings)
    expected_only = [f for f in findings if "AliasTool" in f.message]
    known_only = [f for f in findings if "AllowedOnly" in f.message]
    assert len(expected_only) == 1 and len(known_only) == 1
    assert "provider capability config" in expected_only[0].message
    assert "not declared in the provider" in known_only[0].message
    assert "hook_known_tool_name" in expected_only[0].suggestion
    assert "hook_known_tool_name" in known_only[0].suggestion


def test_real_repo_uses_config_source_and_reports_aliases_and_handback():
    project = REPO_ROOT / ".tmp"

    findings = check_unknown_tool_names(project, REPO_ROOT, {}, {})

    assert findings, "the shipped config has documented config<->allow-list deltas"
    assert all(f.severity == Severity.INFO and f.check == CHECK_ID for f in findings)
    assert all(f.file == "hooks/1-generic/lib/hook_common.sh" for f in findings)
    by_name = {f.message: f for f in findings}
    messages = "\n".join(by_name)
    # Config aliases (expected-only) and SubagentHandback (known-only) are deltas.
    assert any("define_subagent" in m for m in by_name)
    assert any("AgentSwarm" in m for m in by_name)
    assert any("SubagentHandback" in m for m in by_name)
    # Deliberately excluded names never become findings.
    assert "EnterWorktree" not in messages and "ExitWorktree" not in messages
    assert "mcp__" not in messages
    assert print_report(findings, project, changed_only=False) == 0


# --- fail-soft ---------------------------------------------------------------

def test_missing_hook_source_is_fail_soft(tmp_path):
    root = tmp_path / "agent-meta"
    (root / "config").mkdir(parents=True)
    (root / "config" / "provider-capabilities.yaml").write_text(_CAPS, encoding="utf-8")
    (root / "config" / "provider-tools.yaml").write_text(_TOOLS, encoding="utf-8")
    project = tmp_path / "project"
    project.mkdir()

    assert check_unknown_tool_names(project, root, {}, {}) == []


# --- doctor wiring -----------------------------------------------------------

def test_doctor_hooks_branch_dispatches_the_new_check(tmp_path):
    project, root = _with_caps(
        tmp_path,
        _CAPS.replace('["KnownTool", "othertool"]', '["KnownTool", "othertool", "FutureTool"]'),
    )
    env = Env(project_root=project, agent_meta_root=root, config={}, active_set=None,
              caps_map={}, provider_config={}, providers=())

    rows = _raw_findings({"source": "hooks", "check": CHECK_ID}, env)

    assert len(rows) == 1
    assert rows[0][0] == CHECK_ID
    assert rows[0][3] == Severity.INFO
