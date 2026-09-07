"""Pure variable-resolution helpers — no cyclic dependencies.

Scope: turning project config + a variables dict into rendered/derived
values. Three families of pure functions live here so that agents.py,
config.py, context.py and rules.py can import them at module level without
re-introducing the historic agents ↔ config ↔ context import cycle
(Issue #565):

  * Template substitution   — substitute(), strip_inactive_conditional_blocks()
    (substitute() delegates its replacement pass to the shared escape-safe
    core in substitution.py — issue #476)
  * Orchestrator-mode flags  — _resolve_orch_mode(), _orch_mode_flags()

This module depends only on the neutral low-level layer (io, log) and the
stdlib. It must never import agents/config/context/rules or any higher-level
sync module — that invariant is what keeps the dependency graph acyclic.
"""
from __future__ import annotations

import re
import sys

from .io import SyncError
from .log import SyncLog
from .substitution import substitute_placeholders

_VALID_ORCH_MODES = {"strict", "advisory", "main-chat"}

# {{VAR}} placeholder pattern for substitute() — uppercase names only, no
# inner whitespace. Group 1 captures the name (contract of the shared
# substitution core, issue #476).
_VAR_PATTERN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def _resolve_orch_mode(orch_config: dict, provider_override: dict | None = None) -> str:
    """Compute the effective orchestrator mode ('strict'|'advisory'|'main-chat').

    Precedence: provider_override['mode'] > orch_config['mode'] > legacy
    enabled/strict booleans (matching the schema default enabled=true/strict=true
    → 'strict'). provider_override is typically
    orchestrator.provider-overrides.<Provider> from project.yaml; pass None (or a
    dict without 'mode') to fall back to the global orchestrator.mode.
    """
    _mode = None
    if provider_override and provider_override.get("mode") is not None:
        _mode = provider_override.get("mode")
    else:
        _mode = orch_config.get("mode")

    if _mode is not None:
        _normalized_mode = str(_mode).strip().lower()
        if _normalized_mode not in _VALID_ORCH_MODES:
            print(
                f"ERROR: Invalid orchestrator.mode value: {_mode!r}. "
                f"Valid values are: {sorted(_VALID_ORCH_MODES)}. "
                "Hint: use 'main-chat' instead of 'disabled'.",
                file=sys.stderr,
            )
            sys.exit(1)
        return _normalized_mode

    _orch_enabled = orch_config.get("enabled", True)
    _orch_strict = orch_config.get("strict", True)
    if not _orch_enabled:
        return "main-chat"
    elif _orch_strict:
        return "strict"
    else:
        return "advisory"


def _orch_mode_flags(orch_mode: str) -> dict:
    """Return the mutually-exclusive, flat ORCH_MODE_* flags for a resolved mode.

    Exactly one of ORCH_MODE_STRICT/ORCH_MODE_ADVISORY/ORCH_MODE_MAIN_CHAT is
    "true". Used both for the global variables dict and for per-provider
    overrides (see scripts/sync.py per-provider loop).
    """
    _is_main_chat = orch_mode == "main-chat"
    return {
        # ORCH_MODE_DISABLED is a deprecated alias kept for backward compat — it
        # mirrors ORCH_MODE_MAIN_CHAT so legacy templates keep rendering. New
        # templates use ORCH_MODE_MAIN_CHAT.
        "ORCH_MODE_MAIN_CHAT": "true" if _is_main_chat else "false",
        "ORCH_MODE_DISABLED": "true" if _is_main_chat else "false",
        "ORCH_MODE_STRICT": "true" if orch_mode == "strict" else "false",
        "ORCH_MODE_ADVISORY": "true" if orch_mode == "advisory" else "false",
    }



def strip_inactive_conditional_blocks(text: str, variables: dict) -> str:
    """Remove conditional blocks that are inactive in this project.

    Handles:
        {{#if VAR}}...content...{{/if}}
        {{#if VAR}}...content...{{else}}...alt-content...{{/if}}
        {{#unless VAR}}...content...{{/unless}}

    Nested blocks are resolved via repeated passes until no markers remain.

    Uses a guarded non-greedy pattern to prevent cross-block matching
    (e.g. DOD_REQ_TRACEABILITY accidentally matching the ORCHESTRATOR_ENABLED
    block's {{else}} token).
    """
    conditional_vars = {k for k in variables if (k.startswith("DOD_") or k in ("SE_ENABLED", "VALIDATOR_ENABLED", "QUALITY_PIPELINES_ENABLED", "DEVELOPER_TIERS_ENABLED", "EFFORT_ESTIMATOR_ENABLED", "WEB_PROJECT_ENABLED", "KNOWLEDGE_ENGINE_ENABLED")) and k != "DOD_PRESET"}
    conditional_vars.update({k for k in variables if k.startswith("PIPELINE_") and k.endswith("_ENABLED")})
    conditional_vars.update({k for k in variables if k in ("ORCHESTRATOR_ENABLED", "ORCHESTRATOR_STRICT", "DIRECT_DISPATCH_ENABLED", "UNKNOWN_FALLBACK_ASK_USER", "UNKNOWN_FALLBACK_META_FEEDBACK", "UNKNOWN_FALLBACK_MAIN_CHAT", "A2A_PROTOCOL_ENABLED", "ORCHESTRATOR_OUTCOME_CACHING", "CHECKPOINTING_ENABLED", "NATIVE_EXTENSIONS_ENABLED", "NATIVE_EXTENSIONS_WHITELIST_ACTIVE", "ANALYSIS_ENABLED", "FILE_BASED_AGENTS")})
    conditional_vars.update({k for k in variables if k.startswith("ORCH_MODE_")})
    conditional_vars.update({k for k in variables if k.endswith("_SET")})

    if not conditional_vars:
        return text

    # Repeat until stable — handles nested blocks
    max_passes = 10
    for _pass in range(max_passes):
        made_change = False
        for var in conditional_vars:
            var_pattern = re.escape(var)

            # Process simple-if FIRST (before if-else) to prevent
            # cross-block matching: a simple {{#if A}}...{{/if}} should
            # never accidentally capture a downstream {{else}} token.
            #
            # 1. Handle {{#if VAR}}...{{/if}} (simple, no else)
            def replace_if(m: re.Match, _var: str = var) -> str:
                block_content = m.group(1)
                if variables.get(_var, "true") == "false":
                    return ""
                stripped = block_content.strip("\n")
                if m.group(0).endswith("\n"):
                    return stripped + "\n"
                return stripped

            # Guard: prevent simple-if from matching if-else blocks
            # by not crossing {{/if}} or {{else}} boundaries. Also refuse to
            # cross a nested opening marker ({{#if}}/{{#unless}}), so only true
            # innermost blocks match. This makes stripping resolve nested blocks
            # inner-to-outer regardless of the (set-derived) variable iteration
            # order — otherwise output is non-deterministic across processes.
            _simple_body = r"(?:(?!\{\{/if\}\}|\{\{else\}\}|\{\{#if |\{\{#unless ).)*?"
            pattern_if = rf"\{{{{#if {var_pattern}\}}}}\n?({_simple_body})\{{{{/if\}}}}\n?"
            old_text = text
            text = re.sub(pattern_if, replace_if, text, flags=re.DOTALL)
            if text != old_text:
                made_change = True

            # 2. Handle {{#unless VAR}}...{{/unless}}
            def replace_unless(m: re.Match, _var: str = var) -> str:
                block_content = m.group(1)
                is_true = variables.get(_var, "true") == "true"
                if is_true:
                    return ""
                stripped = block_content.strip("\n")
                if m.group(0).endswith("\n") and stripped:
                    return stripped + "\n"
                return stripped

            _unless_body = r"(?:(?!\{\{/unless\}\}|\{\{/if\}\}|\{\{else\}\}|\{\{#if |\{\{#unless ).)*?"
            pattern_unless = rf"\{{{{#unless {var_pattern}\}}}}\n?({_unless_body})\{{{{/unless\}}}}\n?"
            old_text = text
            text = re.sub(pattern_unless, replace_unless, text, flags=re.DOTALL)
            if text != old_text:
                made_change = True

            # 3. Handle {{#if VAR}}...{{else}}...{{/if}} (if-else-endif)
            def replace_if_else(m: re.Match, _var: str = var) -> str:
                true_branch = m.group(1)
                false_branch = m.group(2)
                is_true = variables.get(_var, "true") == "true"
                result = true_branch if is_true else false_branch
                # Preserve trailing newline if original match ended with one
                if m.group(0).endswith("\n"):  # noqa: SIM102
                    if not result.endswith("\n"):
                        result = result + "\n"
                return result

            # Guard: prevent if-else from matching past {{/if}} into
            # other blocks (e.g. DOD simple-if capturing orchestrator's {{else}}).
            # Both branches refuse to cross nested opening markers so if-else
            # blocks also resolve inner-to-outer (order-independent, see above).
            _ife_body = r"(?:(?!\{\{/if\}\}|\{\{else\}\}|\{\{#if |\{\{#unless ).)*?"
            pattern_ife = rf"\{{{{#if {var_pattern}\}}}}\n?({_ife_body})\{{{{else\}}}}\n?({_ife_body})\{{{{/if\}}}}\n?"
            old_text = text
            text = re.sub(pattern_ife, replace_if_else, text, flags=re.DOTALL)
            if text != old_text:
                made_change = True

        if not made_change:
            break

    # Final cleanup: remove any remaining orphaned template markers
    # (e.g. from nested {{#unless A}}{{#unless B}}...{{/unless}}{{/unless}})
    text = re.sub(r'\{\{#if\s+\w+\}\}', '', text)
    text = re.sub(r'\{\{/if\}\}', '', text)
    text = re.sub(r'\{\{else\}\}', '', text)
    text = re.sub(r'\{\{#unless\s+\w+\}\}', '', text)
    text = re.sub(r'\{\{/unless\}\}', '', text)

    return text


def substitute(
    text: str,
    variables: dict,
    source_label: str,
    log: SyncLog,
    strict: bool = False,
) -> str:
    """Replace {{VAR}} occurrences. Warn for missing variables.

    Escape syntax: {{%VAR%}} renders as {{VAR}} without substitution (for literal docs).

    The replacement pass delegates to the shared escape-safe substitution
    core (scripts/lib/substitution.py, issue #476) — function replacement
    keeps values verbatim, never interpreting backslashes or $-group
    references as re.sub replacement escapes (issue #674).

    Args:
        strict: if True, raise SyncError on the first unknown placeholder
            instead of warning and leaving it unsubstituted. Escaped
            placeholders ({{%VAR%}}) and PAL_* placeholders are never
            considered "unknown" — they are exempt in both modes.
            Default False preserves the historic warn-and-continue behavior.
    """
    # First pass: protect escaped literals {{%VAR%}} with unique sentinel
    _SENTINEL = "\x00ESC\x00"
    escaped: list[str] = []

    def stash_escape(m):
        escaped.append(m.group(1))
        return f"{_SENTINEL}{len(escaped) - 1}{_SENTINEL}"

    text = re.sub(r"\{\{%([A-Z0-9_]+)%\}\}", stash_escape, text)

    # Second pass: substitute real {{VAR}} placeholders via the shared
    # escape-safe core (issue #476). PAL_* placeholders are handled by the
    # delegation syntax engine, not by general substitution — exempt them
    # before the variables-dict check.
    def lookup(key: str) -> str | None:
        if key.startswith("PAL_"):
            return None
        if key in variables:
            return str(variables[key])
        return None

    def keep(matched: str, key: str) -> str:
        if key.startswith("PAL_"):
            return matched
        if strict:
            raise SyncError(
                f"Unknown placeholder {{{{{key}}}}} in {source_label} — "
                f"not found in config variables (strict mode)."
            )
        if log:
            log.warn(f"Variable {key} not in config — placeholder remains in: {source_label}")
        return matched

    text = substitute_placeholders(text, _VAR_PATTERN, lookup, keep)

    # Third pass: restore escaped literals as {{VAR}} (no substitution happened)
    for i, name in enumerate(escaped):
        text = text.replace(f"{_SENTINEL}{i}{_SENTINEL}", f"{{{{{name}}}}}")

    return text



