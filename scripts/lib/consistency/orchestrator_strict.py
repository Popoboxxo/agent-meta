"""Consistency check: is orchestrator.strict actually enforceable on every active provider?

``orchestrator.strict`` is only as strong as the runtime gate backing it. The
gate tier per provider is resolved by
``providers.provider_runtime_gate_tier(pc, caps)`` (SPEC-OPENCODE-RUNTIME-GATE-
2026-09-13, IC-03) from the machine flags in ``config/ai-providers.yaml``
(``pc``) plus the declared tier in ``config/provider-capabilities.yaml``
(``caps``). The severity is derived from that tier:

``hook`` / ``plugin``
    Runtime-enforced -> no finding.
``permission``
    Partially enforced: the native permission layer blocks Main-Chat writes,
    but delegation provenance is not enforced (a delegated child session is not
    distinguishable from the Main Chat) -> INFO.
``advisory``
    Prompt adherence only, no runtime enforcement -> WARNING by default, ERROR
    when ``orchestrator.require-runtime-gate`` is ``true`` (opt-in, IC-12).

This mirrors the mode-resolution logic in
hooks/1-generic/orchestrator-guard.sh's resolve_mode() so the two stay in
sync -- provider-overrides can legitimately narrow strict mode to a subset
of providers.
"""

from __future__ import annotations

from pathlib import Path

from .. import providers as providers_lib
from ..variables import _resolve_orch_mode
from .report import Finding, Severity

#: Finding id preserved across the tier re-pointing (IC-11). The id names the
#: historic "no hook support" case; it now covers every non-runtime-enforced tier.
_CHECK_ID = "orchestrator-strict.no-hook-support"
#: Announced (not enforced) default flip (D2b). Separate id so the grace notice
#: never masquerades as a no-hook-support finding.
_DEFAULT_FLIP_CHECK_ID = "orchestrator-strict.default-flip-grace"

#: D2b grace window — pure data, version-driven, provider-agnostic.
#:
#: The strict DEFAULT is ``true`` (D1b, one source: ``variables._resolve_orch_mode``).
#: Turning that default into an enforced runtime gate for every existing project
#: is a behaviour change, so it is announced for one minor release: projects that
#: only inherit the default keep the pre-flip behaviour (no runtime gate) and get
#: a warning. From this version on the default is hard. The release that makes it
#: hard only moves this tuple; no provider-specific branch is involved.
_STRICT_DEFAULT_GRACE_UNTIL: tuple[int, int, int] = (2, 1, 0)

_STRICT_DEFAULT_NOTICE = (
    "orchestrator.strict is not configured — agent-meta now defaults to strict. "
    "For one minor release this implicit default does NOT enforce the runtime "
    "gate (behaviour unchanged) and only warns; from {until} the default becomes "
    "hard (edit/shell deny + primary entry point). Set orchestrator.mode: strict "
    "to opt in now, or orchestrator.mode: advisory to keep today's behaviour."
)


def _version_tuple(raw: str) -> tuple[int, int, int]:
    """Lenient ``MAJOR.MINOR.PATCH`` parse; unparsable parts count as ``0``."""
    parts: list[int] = []
    for chunk in str(raw).strip().lstrip("vV").split(".")[:3]:
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return (parts[0], parts[1], parts[2])


def strict_default_grace_active(agent_meta_root: Path | None = None) -> bool:
    """True while the strict-default flip is announced but not runtime-enforced.

    The decision is data: ``<agent_meta_root>/VERSION`` against the window in
    ``_STRICT_DEFAULT_GRACE_UNTIL``.

    A missing or unreadable ``VERSION`` counts as INSIDE the window (M6): the
    public promise is that the implicit strict default is *announced* before it
    hardens, and silently hard-flipping an installation whose version cannot be
    read is exactly the unannounced behaviour-change that promise rules out. The
    hard branch therefore requires a version that proves the window has passed.
    ``OSError`` and ``UnicodeDecodeError`` (a non-UTF-8 VERSION used to abort the
    whole sync) both count as unreadable.

    ``agent_meta_root is None`` stays off: no root means there is no installation
    to read a version from, the caller cannot announce anything either, and the
    frozen Spec-A entries function depends on this default (ADR-4). Every real
    call site passes the framework root (``_opencode_runtime_gate_entries``
    included since M4).
    """
    if agent_meta_root is None:
        return False
    try:
        raw = (Path(agent_meta_root) / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return True
    return _version_tuple(raw) < _STRICT_DEFAULT_GRACE_UNTIL


def _provider_override(orch: dict, provider: str) -> dict:
    """The provider-override mapping for *provider*, or ``{}``."""
    overrides = orch.get("provider-overrides", {}) or {}
    if not isinstance(overrides, dict):
        return {}
    override = overrides.get(provider, {}) or {}
    return override if isinstance(override, dict) else {}


def _strict_is_default_derived(orch: dict, provider: str) -> bool:
    """True when strict is not configured explicitly for *provider*.

    Default-derived means: no ``mode`` on the provider override, no global
    ``mode`` and no legacy ``strict`` key. ``enabled`` alone does not express a
    strict intent (``enabled: false`` resolves to ``main-chat`` anyway).
    """
    if not isinstance(orch, dict):
        return False
    override = _provider_override(orch, provider)
    if override.get("mode") is not None:
        return False
    if orch.get("mode") is not None:
        return False
    return "strict" not in orch


def _resolve_effective_strict(
    orch: dict,
    provider: str,
    agent_meta_root: Path | None = None,
) -> bool:
    """Whether strict is effectively active for *provider*.

    The mode precedence (provider override → global mode → legacy
    ``enabled``/``strict``, default ``strict``) has exactly ONE source:
    :func:`variables._resolve_orch_mode`. This function only adds the D2b grace
    for the implicit default — an explicitly configured strict is always hard.
    """
    if not isinstance(orch, dict):
        return False
    override = _provider_override(orch, provider)
    if _resolve_orch_mode(orch, override, validate=False) != "strict":
        return False
    if _strict_is_default_derived(orch, provider) and strict_default_grace_active(
        agent_meta_root
    ):
        return False
    return True


def strict_default_notice(orch: dict, agent_meta_root: Path | None = None) -> str | None:
    """The D2b grace notice for a project that only inherits the strict default.

    ``None`` once the grace window has passed (the default is then hard) and for
    any project with an explicit ``mode``/``strict`` setting. Provider-agnostic:
    a project-wide statement, emitted once per sync run.
    """
    if not isinstance(orch, dict):
        return None
    if orch.get("mode") is not None or "strict" in orch:
        return None
    if orch.get("enabled") is False:
        return None  # main-chat: the strict default never applies
    if not strict_default_grace_active(agent_meta_root):
        return None
    return _STRICT_DEFAULT_NOTICE.format(
        until=".".join(str(part) for part in _STRICT_DEFAULT_GRACE_UNTIL)
    )


def _require_runtime_gate(orch: dict) -> bool:
    """Defensive read of the opt-in sibling key (IC-12).

    ``orchestrator`` is an open block in the schema, so the value may be
    missing or malformed at runtime. Anything other than an explicit ``True``
    is the backwards-compatible default ``false``.
    """
    if not isinstance(orch, dict):
        return False
    return orch.get("require-runtime-gate", False) is True


def check_orchestrator_strict_hook_support(project_root: Path, config: dict,
                                            provider_config: dict,
                                            agent_meta_root: Path) -> list[Finding]:
    """Report when orchestrator.strict is active but not runtime-enforced.

    ``project_root`` is used for finding paths only; the capability registry is
    loaded from ``agent_meta_root`` (F-12). An unreadable registry degrades to
    the fail-safe ``advisory`` tier via ``load_provider_capabilities`` -- the
    check never raises.
    """
    findings: list[Finding] = []
    orch = config.get("orchestrator", {})

    # D2b grace (data-driven, provider-agnostic): a project that only inherits
    # the strict default is announced -- the runtime gate stays off for one
    # minor release before the default becomes hard.
    notice = strict_default_notice(orch, agent_meta_root)
    if notice:
        findings.append(Finding(
            Severity.WARNING,
            _DEFAULT_FLIP_CHECK_ID,
            ".meta-config/project.yaml",
            notice,
            "Set orchestrator.mode explicitly ('strict' to opt in now, "
            "'advisory' to keep the current behaviour).",
        ))

    if not orch:
        return findings

    capabilities = providers_lib.load_provider_capabilities(agent_meta_root)

    active_providers = providers_lib.resolve_providers(config, provider_config)
    for provider in active_providers:
        if not _resolve_effective_strict(orch, provider, agent_meta_root):
            continue
        pc = provider_config.get(provider, {})
        caps = capabilities.get(provider, {})
        tier = providers_lib.provider_runtime_gate_tier(pc, caps)
        if tier in ("hook", "plugin"):
            continue
        if tier == "permission":
            findings.append(Finding(
                Severity.INFO,
                _CHECK_ID,
                ".meta-config/project.yaml",
                f"orchestrator.strict is active for provider '{provider}', but "
                f"enforcement is only partial (tier 'permission'): the native "
                f"permission layer blocks Main-Chat writes, but delegation "
                f"provenance is not enforced.",
                f"Accept the partial guarantee for '{provider}', or scope strict "
                f"mode to hook/plugin-capable providers via provider-overrides.",
            ))
            continue
        severity = Severity.ERROR if _require_runtime_gate(orch) else Severity.WARNING
        findings.append(Finding(
            severity,
            _CHECK_ID,
            ".meta-config/project.yaml",
            f"orchestrator.strict is active for provider '{provider}', but this "
            f"provider has no runtime enforcement (tier 'advisory') -- the "
            f"setting is prompt-only and has no runtime effect there.",
            f"Add a provider-overrides entry to scope strict mode to providers "
            f"with runtime enforcement (hook/plugin/permission), or set "
            f"orchestrator.require-runtime-gate to true to fail the check.",
        ))
    return findings
