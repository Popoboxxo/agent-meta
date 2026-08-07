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

try:
    import yaml
except ImportError:
    yaml = None  # type: ignore[assignment]

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

    # ------------------------------------------------------------------
    # Internal registries
    # ------------------------------------------------------------------

    @property
    def syntax_registry(self) -> dict[str, Any]:
        if self._syntax_registry is None:
            path = self.config_dir / "delegation-syntax.yaml"
            try:
                with open(path, encoding="utf-8") as f:
                    if yaml is not None:
                        self._syntax_registry = yaml.safe_load(f)
                    else:
                        self._syntax_registry = {}
            except (FileNotFoundError, yaml.YAMLError):
                self._syntax_registry = {}
        return self._syntax_registry or {}

    @property
    def capabilities_registry(self) -> dict[str, Any]:
        if self._capabilities_registry is None:
            path = self.config_dir / "provider-capabilities.yaml"
            try:
                with open(path, encoding="utf-8") as f:
                    if yaml is not None:
                        self._capabilities_registry = yaml.safe_load(f)
                    else:
                        self._capabilities_registry = {}
            except (FileNotFoundError, yaml.YAMLError):
                self._capabilities_registry = {}
        return self._capabilities_registry or {}

    def get_syntax(self, provider: str) -> dict[str, Any]:
        """Return the delegation syntax map for a provider."""
        return self.syntax_registry.get("delegation_syntax", {}).get(provider, {})

    def get_capabilities(self, provider: str) -> dict[str, Any]:
        """Return capabilities for a provider."""
        return self.capabilities_registry.get("capabilities", {}).get(provider, {})

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
        max_depth: int = 10,
    ) -> list[str]:
        """Validate an A2A envelope dict and return a list of error strings.

        Validation strategy (two tiers):

        1. **Stdlib required-fields check** — always runs, no extra dependencies.
           Verifies that all fields listed in ``_A2A_REQUIRED_FIELDS`` are present.

        2. **Full JSON Schema validation** — runs only when ``jsonschema`` is
           importable *and* the schema file can be resolved.  Gracefully skipped
           when either condition is not met (e.g. lightweight CI environments).

        Args:
            envelope:        The envelope dict to validate.
            schema_name:     Schema key (default ``"a2a-handoff"``).
            agent_meta_root: Repo root path used to locate the schema file.
                             Derived from ``config_dir`` when not provided.
            max_depth:       Maximum allowed delegation_depth (default 10).
                             Configurable via ``orchestrator.delegation.max_depth``
                             in project.yaml.

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

        dd = envelope.get("delegation_depth")
        if dd is not None:
            if not isinstance(dd, int) or isinstance(dd, bool):
                errors.append(
                    f"Invalid delegation_depth: must be integer 0..{max_depth}, got {type(dd).__name__}"
                )
            elif dd < 0 or dd > max_depth:
                errors.append(f"Delegation depth {dd} out of range: must be 0..{max_depth}")

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
