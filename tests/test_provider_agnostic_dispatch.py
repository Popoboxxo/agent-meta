"""Provider-agnostic dispatch guard (issue #735).

Enforces the repo invariant that provider differences are expressed through
capability flags / config keys, never through literal ``provider == "Name"``
branches in ``scripts/lib/``:

1. AST scan of the touched dispatch modules for equality comparisons against a
   registered provider-name literal (comments/docstrings are ignored by design).
2. Every registered provider carries an explicit ``commands`` boolean in
   ``config/provider-capabilities.yaml`` — no silent else-fallback.
3. ``ai-providers.yaml has_commands`` agrees with the capability flag, and every
   commands-capable provider names a target dir + format.
4. An unsupported provider produces one explicit INFO line (not silence).
"""
from __future__ import annotations

import ast
import sys
from pathlib import Path

import pytest
import yaml

_REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(_REPO_ROOT / "scripts"))

_TOUCHED_MODULES = (
    "commands",
    "roles",
    "rules",
    "sync_pipeline",
    "viz",
    "context",
    "providers",
    "agent_sync",
    # Repo-containment ("prison mode") modules — provider dispatch goes through
    # repo_containment.provider-overrides keyed by registry name, never a
    # literal `provider == "Name"` branch.
    "repo_containment",
    "consistency/repo_containment",
    "subagent_permissions",
    "consistency/subagent_permissions",
)


def _registered_providers() -> list[str]:
    data = yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))
    return sorted((data.get("providers") or {}).keys())


def _provider_capabilities() -> dict:
    data = yaml.safe_load((_REPO_ROOT / "config" / "provider-capabilities.yaml").read_text(encoding="utf-8"))
    return data.get("capabilities") or {}


def _provider_configs() -> dict:
    data = yaml.safe_load((_REPO_ROOT / "config" / "ai-providers.yaml").read_text(encoding="utf-8"))
    return data.get("providers") or {}


def test_no_literal_provider_equality_branches_in_touched_modules():
    """No ``provider == "Claude"``-style branch may remain in the modules
    converted by issue #735. AST-based so comments and docstrings that *mention*
    the anti-pattern do not false-positive."""
    names = set(_registered_providers())
    offenders: list[str] = []
    for module in _TOUCHED_MODULES:
        source = (_REPO_ROOT / "scripts" / "lib" / f"{module}.py").read_text(encoding="utf-8")
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Compare):
                continue
            if not any(isinstance(op, (ast.Eq, ast.NotEq)) for op in node.ops):
                continue
            consts = [
                c.value
                for c in [node.left, *node.comparators]
                if isinstance(c, ast.Constant) and isinstance(c.value, str) and c.value in names
            ]
            if consts:
                offenders.append(f"scripts/lib/{module}.py:{node.lineno}: {consts}")
    assert not offenders, (
        "Literal provider-name equality branch(es) reintroduced — dispatch via "
        "config/ai-providers.yaml capabilities (provider_has_capability) or the "
        "provider-capabilities.yaml registry instead:\n" + "\n".join(offenders)
    )


@pytest.mark.parametrize("provider", _registered_providers())
def test_every_provider_has_explicit_commands_capability(provider):
    caps = _provider_capabilities().get(provider, {})
    assert "commands" in caps, (
        f"Provider '{provider}' has no explicit 'commands' entry in "
        "config/provider-capabilities.yaml — an absent key means the commands "
        "path silently reports unsupported (issue #735)."
    )
    assert isinstance(caps["commands"], bool), (
        f"Provider '{provider}'.commands must be a boolean, got {caps['commands']!r}"
    )


@pytest.mark.parametrize("provider", _registered_providers())
def test_has_commands_flag_matches_capability(provider):
    has_commands = bool(_provider_configs().get(provider, {}).get("has_commands", False))
    capability = bool(_provider_capabilities().get(provider, {}).get("commands", False))
    assert has_commands == capability, (
        f"Provider '{provider}': ai-providers.yaml has_commands={has_commands} "
        f"disagrees with provider-capabilities.yaml commands={capability} — "
        "the two registries must stay in sync (issue #735)."
    )


@pytest.mark.parametrize("provider", _registered_providers())
def test_commands_capable_provider_names_dir_and_format(provider):
    caps = _provider_capabilities().get(provider, {})
    if caps.get("commands") is not True:
        return
    pc = _provider_configs().get(provider, {})
    assert pc.get("commands_dir"), (
        f"Provider '{provider}' declares commands: true but has no commands_dir "
        "in config/ai-providers.yaml — sync would fail loudly (issue #735)."
    )
    assert pc.get("commands_format") in {"markdown", "continue", "toml"}, (
        f"Provider '{provider}' needs an explicit commands_format "
        "(markdown|continue|toml) in config/ai-providers.yaml."
    )


class _LogRecorder:
    def __init__(self):
        self.events = []

    def note(self, label, detail):
        self.events.append(("note", label, detail))

    def action(self, kind, label, detail):
        self.events.append(("action", kind, label, detail))

    def skip(self, label, reason):
        self.events.append(("skip", label, reason))

    def warning(self, msg):
        self.events.append(("warning", msg))


def test_unsupported_provider_logs_explicit_note_instead_of_silence(tmp_path):
    from lib.commands import sync_commands_for_provider

    log = _LogRecorder()
    sync_commands_for_provider(
        _REPO_ROOT, tmp_path, {}, log, dry_run=True,
        provider="Copilot", provider_config=_provider_configs(),
    )
    notes = [e for e in log.events if e[0] == "note" and e[1] == "commands"]
    assert notes, "unsupported provider must emit an explicit commands INFO line"
    assert "not supported" in notes[0][2]


def test_commands_capable_provider_without_dir_fails_loudly(tmp_path):
    from lib.commands import sync_commands_for_provider
    from lib.io import SyncError

    log = _LogRecorder()
    with pytest.raises(SyncError):
        sync_commands_for_provider(
            _REPO_ROOT, tmp_path, {}, log, dry_run=True,
            provider="Opencode", provider_config={"Opencode": {}},
        )
