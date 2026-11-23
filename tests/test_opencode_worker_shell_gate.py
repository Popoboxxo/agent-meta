"""Issue #1329 (AC-4 / Contract AC-3) — deterministic post-render shell gate.

The gate is finding-based and fail-soft (never ``sys.exit``): it compares the
declared ``subagent-shell`` capability with the shell permission actually
rendered into each agent artifact, for v1 and v2, and reports role + file + mode
on divergence.

Run: python3 -m pytest tests/test_opencode_worker_shell_gate.py -q
"""
from __future__ import annotations

import copy
import sys
from pathlib import Path

import pytest
import yaml

from scripts.lib.frontmatter import _parse_frontmatter_yaml
from scripts.lib.log import SyncLog
from scripts.lib.provider_transform import transform_agent_content_for_provider
from scripts.lib.providers import load_providers_config

REPO_ROOT = Path(__file__).resolve().parents[1]
PROVIDER = "Opencode"
VERIFIED = "VERIFIED-RUNTIME"
_SHIPPED_CAPS = yaml.safe_load(
    (REPO_ROOT / "config" / "provider-capabilities.yaml").read_text(encoding="utf-8")
)["capabilities"]


def _template(tools=("Read", "Bash")) -> str:
    tool_lines = "".join(f"  - {t}\n" for t in tools)
    return (
        '---\nname: template-role\nversion: "1.0.0"\n'
        "description: role\nhint: role\n"
        f"tools:\n{tool_lines}---\n\nBody.\n"
    )


def _render(role: str, tools, caps: dict, *, v2: bool = False) -> str:
    pc = copy.deepcopy(load_providers_config(REPO_ROOT))
    entry = pc[PROVIDER]
    if v2:
        entry["agent-transform"]["frontmatter-mechanism"] = "opencode-native-v2"
    return transform_agent_content_for_provider(
        _template(tools), PROVIDER, role, role, "desc",
        f"1-generic/{role}.md@1.0.0", {}, REPO_ROOT, REPO_ROOT,
        REPO_ROOT / f"{role}.md", {PROVIDER: entry}, SyncLog(),
        provider_capabilities=caps,
    )


def _v1_artifact(effect: str, mode: str = "subagent") -> str:
    return (
        "---\nname: x\ndescription: x\n"
        f"mode: {mode}\npermission:\n  read: allow\n  bash: {effect}\n"
        "---\n\nBody.\n"
    )


def _v2_artifact(effect: str, mode: str = "subagent") -> str:
    return (
        "---\nname: x\ndescription: x\n"
        f"mode: {mode}\npermissions:\n"
        f"- action: shell\n  resource: '*'\n  effect: {effect}\n"
        "---\n\nBody.\n"
    )


def test_divergent_render_is_reported():
    caps = {PROVIDER: {"subagent-shell": False,
                       "subagent-shell-verified-state": "UNVERIFIED"}}
    result = gate_check({"test-executor": _v1_artifact("allow")}, caps)
    assert result["ok"] is False
    assert len(result["findings"]) == 1
    finding = result["findings"][0]
    assert finding["role"] == "test-executor"
    assert finding["file"].endswith(".opencode/agents/test-executor.md")
    assert finding["mode"] == "subagent"
    assert "subagent-shell" in finding["reason"]


def test_v2_divergent_render_is_reported():
    caps = {PROVIDER: {"subagent-shell": False,
                       "subagent-shell-verified-state": "UNVERIFIED"}}
    result = gate_check({"test-executor": _v2_artifact("allow", mode="primary")}, caps)
    assert result["ok"] is False
    assert result["findings"][0]["mode"] == "primary"
    assert result["findings"][0]["surface"] == "v2"


def test_all_roles_declared_equals_rendered():
    templates = {
        "test-executor": _template(("Read", "Bash")),
        "git": _template(("Read", "Bash")),
        "orchestrator": _template(("Read",)),
    }
    for v2 in (False, True):
        rendered = {
            role: _render(role, _parse_frontmatter_yaml(tpl)["tools"],
                          _SHIPPED_CAPS, v2=v2)
            for role, tpl in templates.items()
        }
        result = gate_check(rendered, _SHIPPED_CAPS, templates=templates)
        assert result["ok"] is True, (
            f"v2={v2}: declaration/render divergence: {result['findings']}"
        )


def test_granted_but_missing_render_is_a_finding():
    """Equivalence is checked in both directions, not only allow-at-false."""
    templates = {"test-executor": _template(("Read", "Bash"))}
    rendered = {"test-executor": _v1_artifact("deny")}
    result = gate_check(rendered, _SHIPPED_CAPS, templates=templates)
    assert result["ok"] is False
    assert result["findings"][0]["reason"].startswith("declared")


def test_gate_is_fail_soft_no_sys_exit(monkeypatch):
    def _forbidden_exit(*_args, **_kwargs):
        raise AssertionError("post-render gate must never call sys.exit")

    monkeypatch.setattr(sys, "exit", _forbidden_exit)
    caps = {PROVIDER: {"subagent-shell": False,
                       "subagent-shell-verified-state": "UNVERIFIED"}}
    result = gate_check({"test-executor": _v1_artifact("allow")}, caps)
    assert result["ok"] is False


def test_invalid_capability_type_fails_closed_with_a_finding():
    caps = {PROVIDER: {"subagent-shell": "true",
                       "subagent-shell-verified-state": VERIFIED}}
    result = gate_check({"test-executor": _v1_artifact("allow")}, caps)
    assert result["ok"] is False
    assert result["findings"][0]["reason"]


@pytest.mark.parametrize("v2", [False, True], ids=["v1", "v2"])
def test_manipulated_artifact_is_caught_for_every_execution_role(v2):
    caps = {PROVIDER: {"subagent-shell": False,
                       "subagent-shell-verified-state": "UNVERIFIED"}}
    artifact = _v2_artifact("allow") if v2 else _v1_artifact("allow")
    roles = ("test-executor", "code-reviewer", "e2e-tester", "git",
             "developer", "devops-engineer", "tester")
    result = gate_check({role: artifact for role in roles}, caps)
    assert [f["role"] for f in result["findings"]] == list(roles)
    assert all(f["surface"] == ("v2" if v2 else "v1") for f in result["findings"])


# --- gate implementation (TDD step 2) ------------------------------------

def _declared_grant(capabilities: dict) -> bool:
    cap = (capabilities or {}).get(PROVIDER) or {}
    return (
        cap.get("subagent-shell") is True
        and cap.get("subagent-shell-verified-state") == VERIFIED
    )


def _rendered_shell(fm: dict) -> tuple[bool | None, str]:
    """Return ``(shell_is_allowed, surface)`` from a rendered frontmatter."""
    if "permissions" in fm:
        for entry in fm.get("permissions") or []:
            if isinstance(entry, dict) and entry.get("action") == "shell":
                return entry.get("effect") == "allow", "v2"
        return None, "v2"
    if isinstance(fm.get("permission"), dict):
        effect = fm["permission"].get("bash", "deny")
        if isinstance(effect, dict):
            effect = effect.get("*", "deny")
        return effect == "allow", "v1"
    return None, "v1"


def gate_check(
    rendered: dict[str, str],
    capabilities: dict,
    *,
    provider: str = PROVIDER,
    templates: dict[str, str] | None = None,
) -> dict:
    """Fail-soft, finding-based post-render shell declaration gate.

    Compares each rendered artifact's shell permission against the declared
    ``subagent-shell`` capability for both v1 and v2 surfaces. A diverging
    artifact yields a finding with role + file + mode; the function never calls
    ``sys.exit`` and never mutates its inputs (mirrors the finding discipline
    of ``consistency/subagent_permissions.py``).
    """
    granted = _declared_grant(capabilities)
    entry = load_providers_config(REPO_ROOT)[provider]
    agents_dir = entry["agents_dir"]
    ext = entry["agent_ext"]
    findings: list[dict] = []
    for role, content in (rendered or {}).items():
        fm = _parse_frontmatter_yaml(content)
        mode = fm.get("mode") or "subagent"
        allowed, surface = _rendered_shell(fm)
        declares_bash = False
        if templates and role in templates:
            tpl_fm = _parse_frontmatter_yaml(templates[role])
            declares_bash = "Bash" in (tpl_fm.get("tools") or [])
        reason = None
        if allowed and not granted:
            reason = (
                "rendered shell allow without a verified subagent-shell grant"
            )
        elif allowed is False and granted and declares_bash:
            reason = "declared shell grant but render denied the Bash tool"
        elif allowed and templates and role in templates and not declares_bash:
            reason = "rendered shell allow but the template declares no Bash"
        if reason:
            findings.append({
                "role": role,
                "file": f"{agents_dir}/{role}{ext}",
                "mode": mode,
                "surface": surface,
                "reason": reason,
            })
    return {"ok": not findings, "findings": findings}
