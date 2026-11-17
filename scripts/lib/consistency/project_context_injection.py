"""Consistency checks for project-context-injection scope (issue #1187, T11).

Four check IDs, all derived from the resolved scope produced by ``lib.config``:

* ``project-context-injection.mode-unknown`` (ERROR) — unknown mode, detected
  without ``jsonschema`` so ``--validate`` stays strict on every runtime.
* ``project-context-injection.whitelist-no-effect`` (WARN) — whitelist set
  outside ``core+whitelist``, or a whitelisted role whose template has no
  ``{{PROJECT_CONTEXT}}`` placeholder.
* ``project-context-injection.orchestrator-role-no-template`` (WARN) — an
  ``orchestrator-roles`` entry whose template has no placeholder (D5).
* ``project-context-injection.pointer-missing`` (WARN) — a role that does not
  embed the project context but whose rendered artifact lacks the resolved
  pointer line (D8: the resolved pointer, never the English literal).

Fail-soft by contract: an absent section or any unexpected error yields no
findings. Resolver-level hard errors (unknown role names, malformed pointer
text) are owned by ``resolve_project_context_scope`` and are not duplicated
here (spec §5.4).
"""
from __future__ import annotations

from pathlib import Path

from .report import Finding, Severity

_SECTION = "project-context-injection"
_PLACEHOLDER = "{{PROJECT_CONTEXT}}"
_TEMPLATE_DIR = "agents/1-generic"
_PROJECT_CONFIG = ".meta-config/project.yaml"

# Framework root that owns the role registry and templates. Resolved from this
# module's location so it is correct both in a self-hosting checkout and when
# the framework is embedded as a downstream ``.agent-meta`` submodule.
_FRAMEWORK_ROOT = Path(__file__).resolve().parents[3]

_CHECK_MODE = f"{_SECTION}.mode-unknown"
_CHECK_WHITELIST = f"{_SECTION}.whitelist-no-effect"
_CHECK_ORCHESTRATOR = f"{_SECTION}.orchestrator-role-no-template"
_CHECK_POINTER = f"{_SECTION}.pointer-missing"


def _load_config(root: Path) -> dict:
    """Load the project config leniently (missing PyYAML/file -> {})."""
    from ..io import _load_yaml_or_json

    config, _ = _load_yaml_or_json(root / _PROJECT_CONFIG)
    return config if isinstance(config, dict) else {}


def _template_rel(role: str) -> str:
    return f"{_TEMPLATE_DIR}/{role}.md"


def _has_placeholder(role: str) -> bool:
    """True when the generic template exists and contains the placeholder.

    A missing/unreadable template is treated as "has placeholder" so the check
    never warns about a file it could not inspect (fail-soft, no false positive).
    """
    path = _FRAMEWORK_ROOT / _TEMPLATE_DIR / f"{role}.md"
    try:
        return _PLACEHOLDER in path.read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return True


def _section_findings(section: dict, mode: str) -> list[Finding]:
    """Warn about ineffective whitelist / orchestrator-role entries."""
    findings: list[Finding] = []
    whitelist = [r for r in (section.get("whitelist") or []) if isinstance(r, str)]
    if whitelist and mode != "core+whitelist":
        findings.append(Finding(
            severity=Severity.WARNING,
            check=_CHECK_WHITELIST,
            file=_PROJECT_CONFIG,
            message=f"whitelist ignored (mode={mode}) — only effective in "
                    "mode=core+whitelist",
            suggestion=f"Set {_SECTION}.mode to core+whitelist or remove the "
                       "whitelist.",
        ))
    for role in whitelist:
        if not _has_placeholder(role):
            rel = _template_rel(role)
            findings.append(Finding(
                severity=Severity.WARNING,
                check=_CHECK_WHITELIST,
                file=rel,
                message=f"whitelist role '{role}' has no {_PLACEHOLDER} "
                        f"placeholder in {rel}; entry has no effect",
            ))
    if "orchestrator-roles" in section:
        for role in section["orchestrator-roles"] or []:
            if isinstance(role, str) and not _has_placeholder(role):
                rel = _template_rel(role)
                findings.append(Finding(
                    severity=Severity.WARNING,
                    check=_CHECK_ORCHESTRATOR,
                    file=rel,
                    message=f"orchestrator role '{role}' has no {_PLACEHOLDER} "
                            f"placeholder in {rel}; entry has no effect",
                ))
    return findings


def _pointer_findings(
    root: Path, config: dict, section: dict, provider_config: dict | None,
) -> list[Finding]:
    """Compare non-injected roles' artifacts against their resolved pointer."""
    from ..config import (
        format_project_context_pointer,
        project_context_injected_for_role,
        resolve_project_context_scope,
    )
    from ..providers import load_providers_config, resolve_providers

    registry = provider_config if provider_config is not None else load_providers_config(
        _FRAMEWORK_ROOT)
    active = resolve_providers(config, registry, tolerate_unknown=True)
    communication_language = (config.get("variables") or {}).get(
        "COMMUNICATION_LANGUAGE")
    scope = resolve_project_context_scope(
        config, _FRAMEWORK_ROOT,
        provider_config=provider_config,
        communication_language=communication_language,
    )

    findings: list[Finding] = []
    seen_paths: set[Path] = set()
    for provider in active:
        pc = registry.get(provider) if isinstance(registry, dict) else None
        if not isinstance(pc, dict):
            continue
        agents_dir, context_file = pc.get("agents_dir"), pc.get("context_file")
        if not isinstance(agents_dir, str) or not agents_dir:
            continue
        if not isinstance(context_file, str) or not context_file:
            continue
        expected = format_project_context_pointer(scope["pointer_text"], context_file)
        directory = root / agents_dir
        if not directory.is_dir():
            continue
        for artifact in sorted(directory.glob("*.md")):
            resolved = artifact.resolve()
            if resolved in seen_paths:
                continue  # shared agents_dir: report each artifact once
            seen_paths.add(resolved)
            role = artifact.stem
            if project_context_injected_for_role(scope, role):
                continue  # embedded context -> no pointer expected
            try:
                content = artifact.read_text(encoding="utf-8")
            except (OSError, UnicodeError):
                continue
            if expected in content:
                continue
            rel = artifact.relative_to(root).as_posix()
            findings.append(Finding(
                severity=Severity.WARNING,
                check=_CHECK_POINTER,
                file=rel,
                message=f"role '{role}' does not embed project context but no "
                        "pointer line was found; expected: "
                        f"{expected}",
                suggestion="Re-run sync so the pointer line is rendered, or "
                           "check the pointer-text/pointer-language config.",
            ))
    return findings


def _check(
    root: Path, config: dict | None, provider_config: dict | None,
) -> list[Finding]:
    from ..config import PROJECT_CONTEXT_MODES

    if config is None:
        config = _load_config(Path(root))
    section = config.get(_SECTION) if isinstance(config, dict) else None
    if not isinstance(section, dict):
        return []  # absent / malformed section -> historic behaviour

    mode = section.get("mode", "all")
    if mode not in PROJECT_CONTEXT_MODES:
        return [Finding(
            severity=Severity.ERROR,
            check=_CHECK_MODE,
            file=_PROJECT_CONFIG,
            message=f"unknown mode {mode!r}; expected one of "
                    f"{', '.join(PROJECT_CONTEXT_MODES)}",
            suggestion=f"Set {_SECTION}.mode to one of "
                       f"{', '.join(PROJECT_CONTEXT_MODES)}.",
        )]

    findings = _section_findings(section, mode)
    findings.extend(_pointer_findings(root, config, section, provider_config))
    return findings


def check_project_context_injection(
    root: Path,
    config: dict | None = None,
    provider_config: dict | None = None,
) -> list[Finding]:
    """Return the four project-context-injection consistency findings.

    ``root`` is the (possibly downstream) project root whose rendered agent
    artifacts are inspected; the role registry and templates always come from
    the framework checkout containing this module. Fail-soft: any unexpected
    error returns an empty list.
    """
    try:
        return _check(Path(root), config, provider_config)
    except Exception:  # noqa: BLE001 - fail-soft by contract (spec §5.4)
        return []
