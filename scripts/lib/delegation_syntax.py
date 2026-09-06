"""Provider Abstraction Layer — Delegation Syntax Engine.

Lädt config/delegation-syntax.yaml und substituiert abstrakte
{{PAL_*}} Platzhalter in Templates durch provider-spezifische Syntax.

Usage:
    from scripts.lib.delegation_syntax import DelegationSyntaxEngine

    engine = DelegationSyntaxEngine()
    processed = engine.apply(content, provider="Gemini")
"""
from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any

from .io import load_yaml_file
from .roles import _TIER_SEQUENCE

# Known A2A schemas shipped with agent-meta (relative to repo root).
# These paths are intentionally relative so they remain valid when the repo is
# used as a Git submodule embedded inside another project.
_SCHEMA_PATHS: dict[str, str] = {
    "a2a-handoff": "schemas/a2a-handoff.schema.json",
    "task-spec": "schemas/handoffs/task-spec.schema.json",
}

# Required fields in an A2A envelope (mirrors a2a-handoff.schema.json).
# Maintained here as a fast stdlib-only check — no jsonschema dependency needed.
_A2A_REQUIRED_FIELDS: tuple[str, ...] = (
    "protocol_version",
    "handoff_id",
    "source_agent",
    "target_agent",
    "payload",
    "delegation_depth",
)

# Fallback policy when config/role-defaults.yaml has no tier-override-policy
# block (issue #346): these roles must never be DOWNGRADED via the optional
# payload.tier_override envelope field. Config always wins over this default.
_DEFAULT_SECURITY_CRITICAL_ROLES: frozenset[str] = frozenset(
    {"security-auditor", "code-reviewer"}
)


class DelegationSyntaxEngine:
    """Substitutes abstract delegation placeholders with provider-specific syntax.

    ## Placeholder taxonomy

    This engine handles exclusively **build-time** PAL_* placeholders — they are
    resolved during `sync.py` and replaced with provider-specific syntax strings
    (e.g. native tool-call syntax, YAML text blocks).

    **Runtime placeholders** such as ``<agent-name>`` and ``<task-description>``
    are intentionally NOT handled here.  They are filled in by the LLM at runtime
    when it constructs an actual delegation call.  Using ``{{double-braces}}``
    for these tokens is explicitly avoided: the LLM interprets curly-brace syntax
    as unresolved sync.py placeholders and refuses to delegate (Issue #277 root
    cause).  The angle-bracket convention (``<agent-name>``) signals a
    human-readable slot that the LLM is expected to fill with a concrete value.

    See also: docs/conclusions/conclusions-2026-06-12.md for the historical
    rationale behind this split.

    ## A2A schema integration

    The PAL_HANDOFF placeholder, once substituted, injects provider-specific
    envelope syntax into templates.  The canonical schema for these envelopes is
    ``schemas/a2a-handoff.schema.json`` (repo root).

    Use :meth:`get_schema_ref` to obtain the relative path to a named schema and
    :meth:`validate_envelope` for a lightweight required-fields check that works
    without any third-party dependencies.  Full JSON Schema validation (if
    ``jsonschema`` is installed) is available via :meth:`validate_envelope` as
    well — it degrades gracefully when the library is absent.

    See also: docs/concepts/a2a-handoff-protocol.md for architecture rationale.
    """

    PLACEHOLDERS: dict[str, str] = {  # noqa: RUF012
        "PAL_DELEGATE": "delegate",
        "PAL_FANOUT": "fanout",
        "PAL_PARALLEL_GROUP": "parallel_group",
        "PAL_FALLBACK": "fallback",
        "PAL_TOOL_PREAMBLE": "tool_preamble",
        "PAL_PARALLEL_PATTERN": "parallel_pattern",
        "PAL_HANDOFF": "handoff",
    }

    def __init__(self, config_dir: Path | None = None) -> None:
        if config_dir is None:
            config_dir = Path(__file__).parent.parent.parent / "config"
        self.config_dir = config_dir
        self._syntax_registry: dict[str, Any] | None = None
        self._capabilities_registry: dict[str, Any] | None = None
        self._tier_presets: dict[str, Any] | None = None
        self._role_defaults: dict[str, Any] | None = None

    # ------------------------------------------------------------------
    # Internal registries
    # ------------------------------------------------------------------

    @property
    def syntax_registry(self) -> dict[str, Any]:
        if self._syntax_registry is None:
            # Canonical single-file loader (Issue #479), fail-soft: absent or
            # malformed registry yields {} — same as the former hand-rolled
            # loader (FileNotFoundError/yaml.YAMLError → {}).
            self._syntax_registry = load_yaml_file(
                self.config_dir / "delegation-syntax.yaml",
                on_error="default",
                default={},
            )
        return self._syntax_registry or {}

    @property
    def capabilities_registry(self) -> dict[str, Any]:
        if self._capabilities_registry is None:
            self._capabilities_registry = load_yaml_file(
                self.config_dir / "provider-capabilities.yaml",
                on_error="default",
                default={},
            )
        return self._capabilities_registry or {}

    def get_syntax(self, provider: str) -> dict[str, Any]:
        """Return the delegation syntax map for a provider."""
        return self.syntax_registry.get("delegation_syntax", {}).get(provider, {})

    def get_capabilities(self, provider: str) -> dict[str, Any]:
        """Return capabilities for a provider."""
        return self.capabilities_registry.get("capabilities", {}).get(provider, {})

    @property
    def tier_presets(self) -> dict[str, Any]:
        """Tier preset curves from ``config/tier-presets.yaml`` (fail-soft → ``{}``).

        Same loader pattern as :attr:`syntax_registry` — the file is framework
        config, absent or malformed content yields an empty registry.
        """
        if self._tier_presets is None:
            self._tier_presets = load_yaml_file(
                self.config_dir / "tier-presets.yaml",
                on_error="default",
                default={},
            )
        return self._tier_presets or {}

    @property
    def role_defaults(self) -> dict[str, Any]:
        """Raw ``config/role-defaults.yaml`` content (fail-soft → ``{}``).

        Loads the unfiltered file (unlike ``roles.load_roles_config``, which
        strips everything but ``roles``) because the tier-override policy block
        is a top-level sibling of ``roles``.
        """
        if self._role_defaults is None:
            self._role_defaults = load_yaml_file(
                self.config_dir / "role-defaults.yaml",
                on_error="default",
                default={},
            )
        return self._role_defaults or {}

    # ------------------------------------------------------------------
    # A2A schema helpers
    # ------------------------------------------------------------------

    def get_schema_ref(self, schema_name: str) -> str:
        """Return the relative repo path for a named A2A schema.

        Args:
            schema_name: Key from the internal registry, e.g. ``"a2a-handoff"``
                or ``"task-spec"``.

        Returns:
            Relative path string (e.g. ``"schemas/a2a-handoff.schema.json"``),
            or an empty string when the name is unknown.
        """
        return _SCHEMA_PATHS.get(schema_name, "")

    def validate_envelope(
        self,
        envelope: dict[str, Any],
        schema_name: str = "a2a-handoff",
        agent_meta_root: Path | None = None,
    ) -> list[str]:
        """Validate an A2A envelope dict and return a list of error strings.

        .. note:: **Dormant by design — not a runtime gate.**

           This is a manually-invokable utility, not an enforcement hook. There
           is no interception point for it: the orchestrator dispatches
           subagents through the provider's ``Agent``/``Task`` tool call, not
           through a Python layer, and ``orchestrator-guard.sh`` (the only
           PreToolUse hook running on every tool) can inspect ``Write``,
           ``Edit`` and ``Bash`` only. The gates in
           ``.claude/rules/a2a-delegation-gates.md`` are therefore conventions
           the model follows, not barriers the framework enforces — that rule
           file states this explicitly, and the decision is recorded in
           ``docs/concepts/a2a-handoff-protocol.md``. Do not cite this function
           as evidence that the gates are enforced (issue #460).

        .. note:: **Delegation depth is NOT validated here anymore (issue #346).**

           The former ``max_depth`` range check was removed: platform limits
           (e.g. Claude Code's own subagent depth cap) already enforce a depth
           ceiling, making the local check ritual without gate effect. The
           ``max_depth`` project.yaml configuration
           (``orchestrator.delegation.max_depth``) is documented in
           ``docs/concepts/a2a-handoff-protocol.md`` but no longer plumbed
           through this function. ``delegation_depth`` remains a required
           envelope field for traceability.

        Validation strategy (two tiers):

        1. **Stdlib required-fields check** — always runs, no extra dependencies.
           Verifies that all fields listed in ``_A2A_REQUIRED_FIELDS`` are present,
           rejects self-handoffs (source_agent == target_agent) and performs a
           structural type check on ``payload.tier_override``. The full
           tier_override guardrails (preset bounds, security-critical downgrade
           block, audit record) live in :meth:`resolve_tier_override`.

        2. **Full JSON Schema validation** — runs only when ``jsonschema`` is
           importable *and* the schema file can be resolved.  Gracefully skipped
           when either condition is not met (e.g. lightweight CI environments).

        Args:
            envelope:        The envelope dict to validate.
            schema_name:     Schema key (default ``"a2a-handoff"``).
            agent_meta_root: Repo root path used to locate the schema file.
                             Derived from ``config_dir`` when not provided.

        Returns:
            A list of human-readable error strings.  Empty list means valid.
        """
        errors: list[str] = []

        # Tier 1: required-fields check (stdlib, always runs)
        missing = [f for f in _A2A_REQUIRED_FIELDS if f not in envelope]
        if missing:
            errors.append(f"Missing required fields: {', '.join(missing)}")

        # Tier 1.5: topological hard rejects (Anti-Re-Delegation)
        sa = envelope.get("source_agent")
        ta = envelope.get("target_agent")
        if sa is not None and ta is not None and sa == ta:
            errors.append(
                f"Self-handoff rejected: source_agent ('{sa}') == target_agent ('{ta}'). "
                "Delegation to self is structurally forbidden."
            )

        # Tier 1.6: tier_override structural check (type only — the full
        # guardrails need role/preset context and live in resolve_tier_override).
        payload = envelope.get("payload")
        if isinstance(payload, dict) and "tier_override" in payload:
            tier_override = payload.get("tier_override")
            if not isinstance(tier_override, str) or not tier_override.strip():
                errors.append(
                    "Invalid tier_override: must be a non-empty string tier name, "
                    f"got {type(tier_override).__name__}"
                )

        # Tier 2: full JSON Schema validation (optional, graceful degradation)
        schema_rel = self.get_schema_ref(schema_name)
        if schema_rel:
            if agent_meta_root is None:
                agent_meta_root = self.config_dir.parent
            schema_path = agent_meta_root / schema_rel
            try:
                import jsonschema  # type: ignore[import]
                with open(schema_path, encoding="utf-8") as f:
                    schema = json.load(f)
                validator = jsonschema.Draft7Validator(schema)
                for err in sorted(validator.iter_errors(envelope), key=str):
                    errors.append(str(err.message))
            except ImportError:
                pass  # jsonschema not installed — tier-1 check is sufficient
            except (FileNotFoundError, json.JSONDecodeError):
                pass  # schema file missing/corrupt — skip silently

        return errors

    # ------------------------------------------------------------------
    # Per-task tier override (issue #346)
    # ------------------------------------------------------------------

    def resolve_tier_override(
        self,
        envelope: dict[str, Any],
        role: str | None = None,
        active_preset: str = "Normal",
        provider: str | None = None,
    ) -> dict[str, Any]:
        """Resolve the optional ``payload.tier_override`` A2A envelope field.

        Per-task tier override (issue #346): ``payload.tier_override: <tier>``
        overrides the role→tier resolution (``role-defaults.yaml`` → ``model``)
        for exactly one dispatch. This method enforces the guardrails and
        returns an audit record for every override attempt — accepted or
        rejected (audit-log duty).

        .. note:: **Dormant by design — reference implementation.**

           Like :meth:`validate_envelope`, this is a manually-invokable
           validation utility, not a runtime interception point. The guardrails
           are prompt-enforced via the orchestrator template (tier-selection
           section) and ``.claude/rules/a2a-delegation-gates.md``; this function
           is the testable single source of truth for their semantics.

        Guardrails, evaluated in order:

        1. **Type** — ``tier_override`` must be a non-empty string.
        2. **Known tier** — must be one of the abstract tier names
           (``nano/fast/balanced/powerful/max/ultra``, mirrored from
           ``scripts/lib/roles.py``).
        3. **Preset bounds** — the tier must exist in the active tier preset
           (``config/tier-presets.yaml``): the preset's global ``tiers:`` map,
           or the union with ``providers.<provider>.tiers`` when a provider
           context is given. Unknown preset → rejected.
        4. **No downgrade of security-critical roles** — roles listed in
           ``tier-override-policy.security-critical-roles`` (from
           ``config/role-defaults.yaml``; default: ``security-auditor``,
           ``code-reviewer``) may only be overridden to the same or a higher
           tier. Roles whose ``model`` value is not an abstract tier (e.g. a
           raw model ID) skip the rank comparison — model IDs carry no
           intrinsic ordering.

        Args:
            envelope:      The A2A envelope dict (reads ``payload.tier_override``).
            role:          Role the envelope is dispatched to. Falls back to
                           ``target_agent`` when omitted.
            active_preset: Name of the active tier preset (project.yaml
                           ``tier-preset``, default ``"Normal"``).
            provider:      Optional provider name; widens the preset bounds to
                           the provider-specific tier map when present.

        Returns:
            Dict with keys:

            - ``requested``: the raw override value (``None`` when absent).
            - ``effective``: the applied tier (set only when ``applied``).
            - ``applied``:   ``True`` when the override passes all guardrails.
            - ``errors``:    human-readable guardrail violations (empty when
                             applied or when no override is present).
            - ``audit``:     audit-log entry (``event``, ``target_agent``,
                             ``role``, ``requested``, ``active_preset``,
                             ``decision``, ``reason``) for every present
                             override attempt, or ``None`` when the envelope
                             carries no override.
        """
        payload = envelope.get("payload")
        if not isinstance(payload, dict) or "tier_override" not in payload:
            return {
                "requested": None,
                "effective": None,
                "applied": False,
                "errors": [],
                "audit": None,
            }

        target_agent = envelope.get("target_agent", "")
        role_name = role or (str(target_agent) if target_agent else "")
        audit: dict[str, Any] = {
            "event": "tier_override",
            "target_agent": target_agent,
            "role": role_name,
            "requested": payload.get("tier_override"),
            "active_preset": active_preset,
            "decision": "rejected",
            "reason": "",
        }
        result: dict[str, Any] = {
            "requested": audit["requested"],
            "effective": None,
            "applied": False,
            "errors": [],
            "audit": audit,
        }

        # 1. Type guard
        requested = audit["requested"]
        if not isinstance(requested, str) or not requested.strip():
            result["errors"].append(
                "tier_override must be a non-empty string tier name, "
                f"got {type(requested).__name__}"
            )
            audit["reason"] = "type error: tier_override must be a non-empty string"
            return result
        requested = requested.strip()
        audit["requested"] = requested
        result["requested"] = requested

        # 2. Known tier
        if requested not in _TIER_SEQUENCE:
            result["errors"].append(
                f"Unknown tier '{requested}': must be one of {', '.join(_TIER_SEQUENCE)}"
            )
            audit["reason"] = f"unknown tier '{requested}'"
            return result

        # 3. Preset bounds
        preset = self.tier_presets.get(active_preset)
        if not isinstance(preset, dict) or not preset:
            result["errors"].append(
                f"Active tier-preset '{active_preset}' not found in tier-presets.yaml"
            )
            audit["reason"] = f"preset '{active_preset}' not found"
            return result
        allowed_tiers = set((preset.get("tiers") or {}).keys())
        if provider:
            provider_preset = (preset.get("providers") or {}).get(provider) or {}
            allowed_tiers |= set((provider_preset.get("tiers") or {}).keys())
        if requested not in allowed_tiers:
            scope = f" (provider '{provider}')" if provider else ""
            result["errors"].append(
                f"Tier '{requested}' is not defined in active tier-preset "
                f"'{active_preset}'{scope} — override rejected, "
                "falling back to role default"
            )
            audit["reason"] = (
                f"tier '{requested}' outside active preset '{active_preset}' bounds"
            )
            return result

        # 4. Security-critical downgrade guard (config-driven, issue #346)
        policy = self.role_defaults.get("tier-override-policy")
        policy = policy if isinstance(policy, dict) else {}
        critical_roles = policy.get("security-critical-roles")
        if isinstance(critical_roles, list):
            critical = frozenset(str(r) for r in critical_roles)
        else:
            critical = _DEFAULT_SECURITY_CRITICAL_ROLES
        if role_name in critical:
            role_cfg = (self.role_defaults.get("roles") or {}).get(role_name) or {}
            default_tier = str(role_cfg.get("model") or "")
            if (
                default_tier in _TIER_SEQUENCE
                and _TIER_SEQUENCE.index(requested) < _TIER_SEQUENCE.index(default_tier)
            ):
                result["errors"].append(
                    f"tier_override downgrade rejected: '{role_name}' is "
                    f"security-critical (default tier '{default_tier}'), "
                    f"requested tier '{requested}' is lower"
                )
                audit["reason"] = (
                    f"downgrade blocked for security-critical role '{role_name}'"
                )
                return result

        result["applied"] = True
        result["effective"] = requested
        audit["decision"] = "applied"
        audit["reason"] = "within preset bounds, no tier-policy violation"
        return result

    # ------------------------------------------------------------------
    # Template substitution
    # ------------------------------------------------------------------

    def apply(self, content: str, provider: str, log=None) -> str:
        """Apply provider-specific syntax to abstract placeholders in content.

        1. Evaluates {{#if PAL_*}}...{{/if}} blocks against this provider's
           syntax values ("false"/empty → block removed, anything else → kept).
        2. Replaces {{PAL_*}} placeholders with the native syntax defined
           for the given provider. Removes any remaining PAL placeholders.

        log: optional SyncLog — warns when content references a PAL placeholder
        that has no definition for this provider (likely a config gap).
        """
        syntax = self.get_syntax(provider)

        def eval_conditional(m: re.Match) -> str:
            syntax_key = self.PLACEHOLDERS.get(m.group(1), "")
            value = syntax.get(syntax_key, "")
            active = isinstance(value, str) and value.strip().lower() not in ("", "false")
            if not active:
                return ""
            return m.group(2).strip("\n") + "\n"

        content = re.sub(
            r"\{\{#if (PAL_[A-Z_]+)\}\}\n?(.*?)\{\{/if\}\}\n?",
            eval_conditional, content, flags=re.DOTALL,
        )

        for placeholder, syntax_key in self.PLACEHOLDERS.items():
            pattern = r"\{\{" + re.escape(placeholder) + r"\}\}"
            replacement = syntax.get(syntax_key, "")
            if not isinstance(replacement, str):
                replacement = ""
            if log is not None and not replacement and re.search(pattern, content):
                log.warning(
                    f"PAL: '{placeholder}' has no definition for provider "
                    f"'{provider}' — placeholder removed (check config/delegation-syntax.yaml)"
                )
            content = re.sub(pattern, lambda _m: replacement, content)  # noqa: B023

        # Remove any remaining {{PAL_*}} placeholders (no-ops for this provider)
        leftover = set(re.findall(r"\{\{(PAL_[A-Z_]+)\}\}", content))
        if log is not None:
            for name in sorted(leftover):
                log.warning(
                    f"PAL: unknown placeholder '{{{{{name}}}}}' for provider "
                    f"'{provider}' — removed (not in DelegationSyntaxEngine.PLACEHOLDERS)"
                )
        content = re.sub(r"\{\{PAL_[A-Z_]+\}\}", "", content)

        # Remove PAL_PREFIX: markers (used in templates to mark PAL-dependent sections)
        content = re.sub(r"PAL_PREFIX:\w+\s*\n", "", content)

        return content

    # ------------------------------------------------------------------
    # Provider capability checks
    # ------------------------------------------------------------------

    def needs_bootstrap(self, provider: str) -> bool:
        """Check if provider needs session bootstrap."""
        caps = self.get_capabilities(provider)
        return caps.get("bootstrap_required", False)

    def has_native_subagent_dispatch(self, provider: str) -> bool:
        """Check if provider has native subagent dispatch tools."""
        caps = self.get_capabilities(provider)
        return caps.get("subagent_dispatch", False)

    def has_file_based_agents(self, provider: str) -> bool:
        """Check if provider uses file-based agent discovery."""
        caps = self.get_capabilities(provider)
        return caps.get("file_based_agents", False)
