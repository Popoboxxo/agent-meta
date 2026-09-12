"""Consistency checks for the repo-containment ("prison mode") feature.

Two independent checks, mirroring the split established for
``orchestrator.strict`` in :mod:`scripts.lib.consistency.orchestrator_strict`:

* :func:`check_repo_containment_support` -- project-/provider-aware,
  **WARNING-only**. ``hooks/1-generic/repo-containment*.sh`` is the only
  runtime enforcement of ``repo_containment``, and ``scripts/lib/hooks.py``
  only mirrors PreToolUse hooks for providers where
  ``providers.provider_hooks_supported()`` is true (verified
  ``hook_protocol``). On every other active provider the (default-enabled)
  setting is a silent runtime no-op: it exists as a prompt convention plus
  sync-time validation, but nothing gates a write at runtime. This check makes
  that gap visible (spec
  ``docs/concepts/repo-containment-prison-mode.md`` §4.4 / §9.1). The
  effective on/off state is resolved through the real
  :func:`scripts.lib.repo_containment.resolve_effective_repo_containment`
  helper -- the precedence is never re-implemented here.

* :func:`check_repo_containment_templates` -- framework-only,
  **ERROR-only** template drift. It verifies that the framework *source*
  hook wrapper/impl still carry their identifying header/markers and that the
  rule/prompt template references the ``REPO_CONTAINMENT_`` placeholders the
  hook contract is paired with.

Marker-based hook<->rule-template drift is **new** here. The existing
deployed-hook checks (``check_stale_deployed_hooks`` and
``check_hook_enablement_consistency`` in
:mod:`scripts.lib.consistency.hook_drift`) compare *deployed copies* against
the current source and check deployed enablement; they do not inspect the
markers in the framework source templates. This module deliberately does not
duplicate them.

Rule-template gating decision (Sub-Task E): ``rules/1-generic/repo-containment.md``
may not exist yet when this check ships. Emitting an ERROR for a file that is
intentionally not there would be a false positive. The rule-template part of
:func:`check_repo_containment_templates` is therefore **gated on file
existence**: missing -> no finding; present -> it must reference at least one
``REPO_CONTAINMENT_`` placeholder. The check is thus correct both before and
after Sub-Task E lands, and self-activates the moment the template appears.
"""

from __future__ import annotations

import re
from pathlib import Path

from .. import providers as providers_lib
from ..hooks import parse_hook_metadata
from ..repo_containment import resolve_effective_repo_containment
from .report import Finding, Severity

# Framework source templates, relative to the agent-meta root.
HOOK_WRAPPER_RELPATH = "hooks/1-generic/repo-containment.sh"
HOOK_IMPL_RELPATH = "hooks/1-generic/repo-containment-impl.sh"
RULE_TEMPLATE_RELPATH = "rules/1-generic/repo-containment.md"

_EXPECTED_HOOK_NAME = "repo-containment"
_EXPECTED_EVENT = "PreToolUse"
_TRUTHY_VALUES = frozenset({"true", "1", "yes", "on"})
_RULE_PLACEHOLDER_RE = re.compile(r"REPO_CONTAINMENT_[A-Z0-9_]+")


def _read_text(path: Path) -> str | None:
    """Return the file's text, or ``None`` when it cannot be read."""
    try:
        return path.read_text(encoding="utf-8")
    except OSError:
        return None


def _is_truthy(value: object) -> bool:
    """Whether a hook-header value like ``enabled_by_default`` means "on"."""
    return isinstance(value, str) and value.strip().lower() in _TRUTHY_VALUES


def check_repo_containment_support(
    project_root: Path, config: dict, provider_config: dict
) -> list[Finding]:
    """Warn when repo-containment is effectively active for a provider with no
    mirrored PreToolUse hook (``provider_hooks_supported(pc) == false``).

    Containment defaults to enabled, so this warning can fire even when the
    project never wrote a ``repo_containment`` block -- that is the intended
    visibility for the "default ON but only a prompt convention here" gap.
    """
    findings: list[Finding] = []

    active_providers = providers_lib.resolve_providers(config, provider_config)
    for provider in active_providers:
        effective = resolve_effective_repo_containment(config, provider)
        if not effective.enabled:
            continue
        pc = provider_config.get(provider, {})
        if providers_lib.provider_hooks_supported(pc):
            continue
        reason = (
            "has_hooks: false"
            if not pc.get("has_hooks", False)
            else "has_hooks: true but no verified hook_protocol"
        )
        findings.append(Finding(
            Severity.WARNING,
            "repo-containment.no-hook-support",
            ".meta-config/project.yaml",
            f"repo_containment is active for provider '{provider}', but this "
            f"provider has no PreToolUse hook wiring (config/ai-providers.yaml: "
            f"{reason}) -- containment has no runtime effect there and works only "
            f"as a prompt convention.",
            f"Add a repo_containment.provider-overrides entry to scope containment "
            f"to hook-capable providers only, or accept that writes are not gated "
            f"on '{provider}'.",
        ))
    return findings


def _check_wrapper_markers(meta: dict, relpath: str) -> list[Finding]:
    """ERROR findings for missing/incorrect wrapper header markers."""
    findings: list[Finding] = []
    missing: list[str] = []

    if meta.get("hook") != _EXPECTED_HOOK_NAME:
        missing.append(f"# hook: {_EXPECTED_HOOK_NAME}")
    if not str(meta.get("version", "")).strip():
        missing.append("# version: <semver>")
    if meta.get("event") != _EXPECTED_EVENT:
        missing.append(f"# event: {_EXPECTED_EVENT}")
    if not _is_truthy(meta.get("enabled_by_default")):
        missing.append("# enabled_by_default: true")

    if missing:
        findings.append(Finding(
            Severity.ERROR,
            "repo-containment.template-drift",
            relpath,
            "Repo-containment hook wrapper is missing expected header marker(s): "
            + ", ".join(missing) + ".",
            "Restore the marker(s) -- scripts/lib/hooks.py derives hook "
            "registration and default enablement from them.",
        ))
    return findings


def _check_impl_markers(meta: dict, relpath: str) -> list[Finding]:
    """ERROR finding when the impl script has no ``# version:`` marker."""
    if str(meta.get("version", "")).strip():
        return []
    return [Finding(
        Severity.ERROR,
        "repo-containment.template-drift",
        relpath,
        "Repo-containment hook impl is missing its '# version:' marker -- "
        "check_stale_deployed_hooks() reads it to detect deployed drift.",
        "Add a '# version: <semver>' header line and bump it on every logic change.",
    )]


def _check_rule_template(path: Path, relpath: str) -> list[Finding]:
    """ERROR-only placeholder drift for the rule/prompt template.

    Gated on existence: a missing template yields no finding (Sub-Task E may
    not have landed yet). A present template must reference at least one
    ``REPO_CONTAINMENT_`` placeholder so the hook and its prompt counterpart
    stay paired.
    """
    if not path.is_file():
        return []

    content = _read_text(path)
    if content is None:
        return [Finding(
            Severity.ERROR,
            "repo-containment.template-drift",
            relpath,
            "Repo-containment rule template exists but could not be read.",
            "Fix the file permissions/encoding of the rule template.",
        )]

    if _RULE_PLACEHOLDER_RE.search(content):
        return []
    return [Finding(
        Severity.ERROR,
        "repo-containment.template-drift",
        relpath,
        "Repo-containment rule template references no REPO_CONTAINMENT_ "
        "placeholder -- the hook<->template marker contract is broken.",
        "Reference at least one {{REPO_CONTAINMENT_*}} placeholder (e.g. "
        "{{REPO_CONTAINMENT_ENABLED}}) and register it in variables.py.",
    )]


def check_repo_containment_templates(agent_meta_root: Path) -> list[Finding]:
    """ERROR-only framework drift for the repo-containment source templates.

    Validates the hook wrapper/impl header markers and (when it exists) the
    rule template's ``REPO_CONTAINMENT_`` placeholder references. This is the
    marker-based hook<->rule-template check that no existing check covered.
    """
    findings: list[Finding] = []

    wrapper_path = agent_meta_root / HOOK_WRAPPER_RELPATH
    wrapper_content = _read_text(wrapper_path) if wrapper_path.is_file() else None
    if wrapper_content is None:
        findings.append(Finding(
            Severity.ERROR,
            "repo-containment.template-drift",
            HOOK_WRAPPER_RELPATH,
            "Repo-containment hook wrapper is missing or unreadable.",
            "Restore hooks/1-generic/repo-containment.sh (the containment "
            "enforcement entry point).",
        ))
    else:
        findings.extend(_check_wrapper_markers(
            parse_hook_metadata(wrapper_content), HOOK_WRAPPER_RELPATH
        ))

    impl_path = agent_meta_root / HOOK_IMPL_RELPATH
    impl_content = _read_text(impl_path) if impl_path.is_file() else None
    if impl_content is None:
        findings.append(Finding(
            Severity.ERROR,
            "repo-containment.template-drift",
            HOOK_IMPL_RELPATH,
            "Repo-containment hook impl is missing or unreadable.",
            "Restore hooks/1-generic/repo-containment-impl.sh (the containment "
            "logic invoked by the wrapper).",
        ))
    else:
        findings.extend(_check_impl_markers(
            parse_hook_metadata(impl_content), HOOK_IMPL_RELPATH
        ))

    findings.extend(_check_rule_template(
        agent_meta_root / RULE_TEMPLATE_RELPATH, RULE_TEMPLATE_RELPATH
    ))
    return findings
