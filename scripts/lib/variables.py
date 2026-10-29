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
from pathlib import Path

from .io import SyncError
from .log import SyncLog
from .substitution import substitute_placeholders

_VALID_ORCH_MODES = {"strict", "advisory", "main-chat"}

#: The ONE source of the legacy default (D1b). ``config/project-config.schema.json``
#: declares ``orchestrator.mode`` default ``strict``; the legacy ``enabled``/
#: ``strict`` fallback must resolve to exactly the same mode, otherwise the
#: rendered template (``ORCH_MODE_STRICT``) and the runtime gate diverge.
#: ``consistency.orchestrator_strict._resolve_effective_strict`` delegates here.
_ORCH_STRICT_DEFAULT = True

# Subagent-permission policy (Feature A). Neutral, stdlib-only layer so
# config.py/rules.py/standalone.py can share one resolution without
# re-introducing the historic import cycle (Issue #565).
_VALID_SUBAGENT_PERMISSION_MODES: frozenset[str] = frozenset({"strict", "warn", "off"})

#: Conditionals whose *absence* means "inactive". The engine's generic default
#: is the opposite (an absent variable keeps its ``{{#if}}`` block, see
#: ``_conditional_active``), which is correct for opt-out feature flags. A
#: render *state* has to be asked for explicitly instead: ``GATE_NEUTRAL`` is
#: only active when the canonical core is rendered in ``per-provider``
#: topology (SPEC-CONTEXT-FILE-MODES-2026-09-13, AC-23) and must never leak
#: into the shared/``unified`` or provider-native rules render by omission.
# Context-profile flag (IC-03): opt-in, so an absent value must read as
# inactive — otherwise a bare {{#if CONTEXT_PROFILE_COMPACT}} would leak into
# the render path everywhere the provider injection is not applied.
_FALSE_DEFAULT_CONDITIONALS: frozenset[str] = frozenset({
    "GATE_NEUTRAL",
    "CONTEXT_PROFILE_COMPACT",
    "ROSTER_IN_HARNESS",
})

# Only these are safe as {{#if}} conditionals: strip_inactive_conditional_blocks
# treats every value except the literal "false" as active, so a mode STRING
# (SUBAGENT_PERMISSIONS_MODE) must never be used as a conditional.
_BOOLEAN_SUBAGENT_PERMISSION_FLAGS: frozenset[str] = frozenset({
    "SUBAGENT_PERMISSIONS_STRICT",
    "SUBAGENT_PERMISSIONS_WARN",
    "SUBAGENT_PERMISSIONS_OFF",
    "SUBAGENT_PERMISSIONS_ENABLED",
})

# {{VAR}} placeholder pattern for substitute() — uppercase names only, no
# inner whitespace. Group 1 captures the name (contract of the shared
# substitution core, issue #476).
_VAR_PATTERN = re.compile(r"\{\{([A-Z0-9_]+)\}\}")

#: D3(a) grace window — pure data, version-driven, provider-agnostic.
#:
#: A placeholder that is *referenced* in a template but *not defined* (no
#: variable builder, no project `variables:` entry) must fail the sync instead
#: of shipping a literal token (agents) or dropping the line (context files,
#: `context.omit_unresolved_placeholder_lines`). Making that an immediate hard
#: error would break every existing project that carries such a token today, so
#: it is announced for one minor release: until this version the render only
#: warns *and names the future error verbatim*; from this version on it raises
#: `SyncError` (issue #983 / D3(a)). The release that makes it hard only moves
#: this tuple — there is no provider- or role-specific branch anywhere.
_UNRESOLVED_PLACEHOLDER_GRACE_UNTIL: tuple[int, int, int] = (2, 1, 0)


def framework_root() -> Path:
    """The agent-meta checkout root that contains this module (stdlib only).

    ``scripts/lib/variables.py`` → ``parents[2]`` is the checkout root, which is
    the repository root when self-hosting and the ``.agent-meta/`` submodule
    checkout when embedded. Used to read ``VERSION`` for grace windows.
    """
    return Path(__file__).resolve().parents[2]


def _version_tuple(raw: str) -> tuple[int, int, int]:
    """Lenient ``MAJOR.MINOR.PATCH`` parse; unparsable parts count as ``0``."""
    parts: list[int] = []
    for chunk in str(raw).strip().lstrip("vV").split(".")[:3]:
        digits = "".join(ch for ch in chunk if ch.isdigit())
        parts.append(int(digits) if digits else 0)
    while len(parts) < 3:
        parts.append(0)
    return (parts[0], parts[1], parts[2])


def grace_window_active(agent_meta_root: Path | None,
                        until: tuple[int, int, int]) -> bool:
    """True while *until* lies in the future (the announced grace still runs).

    The decision is data: ``<agent_meta_root>/VERSION`` against *until*. A
    missing or unreadable ``VERSION`` counts as INSIDE the window — silently
    hardening an installation whose version cannot be read is exactly the
    unannounced behaviour change a grace window rules out. ``agent_meta_root is
    None`` is ``False`` (no installation, no version, nothing to announce).
    """
    if agent_meta_root is None:
        return False
    try:
        raw = (Path(agent_meta_root) / "VERSION").read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError):
        return True
    return _version_tuple(raw) < tuple(until)


def unresolved_placeholder_grace_active(
    agent_meta_root: Path | None = None,
) -> bool:
    """True while an undefined placeholder warns instead of aborting (D3(a))."""
    root = framework_root() if agent_meta_root is None else Path(agent_meta_root)
    return grace_window_active(root, _UNRESOLVED_PLACEHOLDER_GRACE_UNTIL)


def unknown_placeholder_error_text(key: str, source_label: str) -> str:
    """The ONE error text for an undefined placeholder (announced in the WARN)."""
    return (f"Unknown placeholder {{{{{key}}}}} in {source_label} — "
            f"not found in config variables.")


def unresolved_placeholder_notice(key: str, source_label: str) -> str:
    """The D3(a) grace WARN: states the behaviour AND the future error verbatim."""
    until = ".".join(str(part) for part in _UNRESOLVED_PLACEHOLDER_GRACE_UNTIL)
    error_text = unknown_placeholder_error_text(key, source_label)
    return (
        f"Variable {key} not in config — placeholder remains in: {source_label}. "
        f"D3(a) grace: until {until} this only warns; from {until} it aborts the "
        f"sync with SyncError: \"{error_text}\" "
        f"Add '{key}' under variables: in .meta-config/project.yaml, or fix the "
        f"spelling."
    )


def _placeholder_keep(matched: str, key: str, source_label: str,
                      strict: bool, log: SyncLog | None) -> str:
    """PAL_* pass-through, then hard error / grace WARN / literal keep.

    Shared by both substitution engines (``substitute()`` here and
    ``context_templates.builder.TemplateBuilder.resolve_variables``) so the
    grace decision and the error text cannot drift apart.

    ``substitute()`` only reaches this helper for tokens that survive the
    conditional strip (it probes the stripped text without rewriting its
    output), so a token inside an inactive ``{{#if}}``/``{{#unless}}`` block is
    never evaluated: it cannot warn and cannot abort once the grace window
    closes. The builder engine resolves conditionals before variables for the
    same reason.
    """
    if key.startswith("PAL_"):
        return matched
    if strict or not unresolved_placeholder_grace_active():
        raise SyncError(unknown_placeholder_error_text(key, source_label))
    if log is not None:
        log.warn(unresolved_placeholder_notice(key, source_label))
    return matched


_LINE_LEADING_WS_RE = re.compile(r"^[ \t]*\Z")


def _placeholder_line_indent(match: "re.Match[str]") -> str:
    """Return the indentation of the line the placeholder sits on.

    Returns ``""`` unless the placeholder starts its own line, i.e. unless
    everything between the start of its line and the match is whitespace. An
    inline placeholder inside a sentence (``prefix {{VAR}}``) has no line
    indentation of its own and is never re-indented.
    """
    line_start = match.string.rfind("\n", 0, match.start()) + 1
    prefix = match.string[line_start:match.start()]
    return prefix if _LINE_LEADING_WS_RE.match(prefix) else ""


def _reindent_to_placeholder(match: "re.Match[str]", value: str) -> str:
    """Re-indent the continuation lines of a multi-line value.

    A block value (``{{SOME_BLOCK}}``) whose placeholder is indented at the
    use site — a YAML literal block, a nested list item — must keep that
    indentation on *every* content line, otherwise the first line is indented
    and the rest lands on column 0. Single-line values and column-0
    placeholders are returned unchanged, so this is a no-op for the normal
    (column-0) case.

    Blank lines are exempt: indenting them would emit whitespace-only lines
    that trip ``git diff --check`` and trailing-whitespace hooks in consumer
    projects. A value's own whitespace is never altered — only non-blank
    continuation lines receive the use-site indentation.

    Only continuation lines are touched. The first line is emitted verbatim
    because ``re.sub`` replaces the placeholder text only — the indentation
    that precedes it in the template is still in place for that line.
    """
    if "\n" not in value:
        return value
    indent = _placeholder_line_indent(match)
    if not indent:
        return value
    first, *rest = value.split("\n")
    return "\n".join(
        [first] + [indent + line if line.strip() else line for line in rest]
    )


def _resolve_orch_mode(
    orch_config: dict,
    provider_override: dict | None = None,
    *,
    validate: bool = True,
) -> str:
    """Compute the effective orchestrator mode ('strict'|'advisory'|'main-chat').

    Precedence: provider_override['mode'] > orch_config['mode'] > legacy
    enabled/strict booleans (matching the schema default enabled=true/strict=true
    → 'strict'). provider_override is typically
    orchestrator.provider-overrides.<Provider> from project.yaml; pass None (or a
    dict without 'mode') to fall back to the global orchestrator.mode.

    This is the ONE mode resolver (D1b): ``consistency.orchestrator_strict``
    delegates here instead of keeping a second legacy fallback. ``validate=False``
    keeps the checker's historic fail-soft behaviour for an invalid value (it
    returns the normalized string; callers comparing to ``"strict"`` get
    ``False``) instead of aborting the process.
    """
    _mode = None
    if provider_override and provider_override.get("mode") is not None:
        _mode = provider_override.get("mode")
    else:
        _mode = orch_config.get("mode")

    if _mode is not None:
        _normalized_mode = str(_mode).strip().lower()
        if _normalized_mode not in _VALID_ORCH_MODES:
            if not validate:
                return _normalized_mode
            print(
                f"ERROR: Invalid orchestrator.mode value: {_mode!r}. "
                f"Valid values are: {sorted(_VALID_ORCH_MODES)}. "
                "Hint: use 'main-chat' instead of 'disabled'.",
                file=sys.stderr,
            )
            sys.exit(1)
        return _normalized_mode

    _orch_enabled = orch_config.get("enabled", True)
    _orch_strict = orch_config.get("strict", _ORCH_STRICT_DEFAULT)
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


def _repo_containment_block(enabled: bool, sink_active: bool, tmp_path: str) -> str:
    """Render the effective repo-containment policy text (spec §4.5).

    Mirrors ``A2A_HANDOFF_BLOCK``: a non-empty German policy sentence when
    containment is active, the empty string when it is off. Keeping the text
    derived (rather than hand-written per template) means agent prompts and the
    ``repo-containment`` rule always describe the same effective policy.
    """
    if not enabled:
        return ""
    if sink_active:
        return (
            "Repo-Containment ist AKTIV: Schreibzugriffe sind auf die Projekt-Wurzel "
            f"beschränkt; einziger sanktionierter Ausnahmebereich ist `{tmp_path}/`."
        )
    return (
        "Repo-Containment ist AKTIV: Schreibzugriffe sind strikt auf die "
        "Projekt-Wurzel beschränkt (kein Scratch-Sink aktiv)."
    )


def repo_containment_variables(config: dict, provider: str | None = None) -> dict:
    """Compute the flat ``REPO_CONTAINMENT_*`` variables for a config/provider pair.

    Mirrors ``_orch_mode_flags``: the flag derivation is pure and the actual
    precedence resolution is delegated to the non-exiting resolver
    :func:`scripts.lib.repo_containment.resolve_effective_repo_containment`
    (``provider-override > project > framework default``; spec §2.3) — it is
    never re-implemented here. Pass ``provider=None`` for the project/default
    state (the tmp-sink settings are not provider-scoped).

    Returns:
        REPO_CONTAINMENT_ENABLED: ``"true"``/``"false"`` effective master switch.
        REPO_CONTAINMENT_TMP_SINK_ENABLED: ``"true"`` when the tmp sink is
            enabled. Mirroring the resolver, the tmp-sink settings are resolved
            **independently** of the master switch (the sink is provisioned even
            when containment is off).
        REPO_CONTAINMENT_TMP_PATH: validated project-relative scratch path.
        REPO_CONTAINMENT_BLOCK: rendered policy text when active, else ``""``.
    """
    from .repo_containment import resolve_effective_repo_containment

    effective = resolve_effective_repo_containment(config, provider)
    sink_enabled = bool(effective.tmp_sink_enabled)
    return {
        "REPO_CONTAINMENT_ENABLED": "true" if effective.enabled else "false",
        "REPO_CONTAINMENT_TMP_SINK_ENABLED": "true" if sink_enabled else "false",
        "REPO_CONTAINMENT_TMP_PATH": effective.tmp_sink_path,
        "REPO_CONTAINMENT_BLOCK": _repo_containment_block(
            effective.enabled, sink_enabled, effective.tmp_sink_path
        ),
    }


def normalize_subagent_permission_mode(value: object) -> str | None:
    """Canonicalize a subagent-permission mode value to ``strict``/``warn``/``off``.

    Pure and non-exiting. Returns ``None`` when ``value`` is missing or not one
    of the three canonical strings. Strings are lowercased and stripped; every
    bool normalizes to ``None`` (safe-side: the policy must be opted in with a
    quoted mode name, never inferred from a YAML 1.1 boolean such as an
    unquoted ``off``/``on``).
    """
    if isinstance(value, bool):
        return None
    if not isinstance(value, str):
        return None
    normalized = value.strip().lower()
    if normalized in _VALID_SUBAGENT_PERMISSION_MODES:
        return normalized
    return None


def _resolve_subagent_permissions_mode(
    cfg: dict,
    provider_override: dict | None = None,
) -> str:
    """Effective subagent-permission mode for ``cfg`` + optional override.

    Precedence: ``provider_override['mode']`` > ``cfg['mode']`` > ``"off"``.
    This resolver NEVER calls ``sys.exit`` — an invalid/absent value resolves
    to the safe-side default ``"off"``. All nested access goes through
    ``.get()`` with ``isinstance`` guards (M1); the hard fail lives only in
    ``config._validate_subagent_permissions``.
    """
    mode: object = None
    if isinstance(provider_override, dict) and provider_override.get("mode") is not None:
        mode = provider_override.get("mode")
    elif isinstance(cfg, dict) and cfg.get("mode") is not None:
        mode = cfg.get("mode")

    normalized = normalize_subagent_permission_mode(mode)
    return normalized if normalized is not None else "off"


def _subagent_permission_flags(mode: str) -> dict:
    """Return the flat ``SUBAGENT_PERMISSIONS_*`` flags for a resolved mode.

    Exactly one of STRICT/WARN/OFF is ``"true"``; MODE carries the mode string
    itself. ``SUBAGENT_PERMISSIONS_ENABLED`` is ``"false"`` only for ``off``.
    """
    return {
        "SUBAGENT_PERMISSIONS_MODE": mode,
        "SUBAGENT_PERMISSIONS_STRICT": "true" if mode == "strict" else "false",
        "SUBAGENT_PERMISSIONS_WARN": "true" if mode == "warn" else "false",
        "SUBAGENT_PERMISSIONS_OFF": "true" if mode == "off" else "false",
        "SUBAGENT_PERMISSIONS_ENABLED": "false" if mode == "off" else "true",
    }



def _conditional_active(variables: dict, var: str) -> bool:
    """Whether a ``{{#if VAR}}`` block is active for ``variables``.

    An absent variable keeps its block (historic default: feature flags are
    opt-out) — except for the explicit default-off render states in
    ``_FALSE_DEFAULT_CONDITIONALS``, which only activate when set to
    ``"true"``. This keeps ``GATE_NEUTRAL`` opt-in without touching every
    render path that never mentions it.
    """
    default = "false" if var in _FALSE_DEFAULT_CONDITIONALS else "true"
    return variables.get(var, default) == "true"


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
    conditional_vars.update({k for k in variables if k in ("ORCHESTRATOR_ENABLED", "ORCHESTRATOR_STRICT", "DIRECT_DISPATCH_ENABLED", "UNKNOWN_FALLBACK_ASK_USER", "UNKNOWN_FALLBACK_META_FEEDBACK", "UNKNOWN_FALLBACK_MAIN_CHAT", "A2A_PROTOCOL_ENABLED", "ORCHESTRATOR_OUTCOME_CACHING", "CHECKPOINTING_ENABLED", "NATIVE_EXTENSIONS_ENABLED", "NATIVE_EXTENSIONS_WHITELIST_ACTIVE", "ANALYSIS_ENABLED", "FILE_BASED_AGENTS", "AUTO_COMMIT_ENABLED", "PROGRESS_CHAT_PUSH_ENABLED", "SPEC_PLAN_WORKFLOW_ENABLED", "ROUTE_INTENT_CALLABLE")})
    # IC-05: mutually-exclusive runtime-gate tiers are strippable conditionals.
    conditional_vars.update({"GATE_ENFORCED", "GATE_PARTIAL", "GATE_ADVISORY", "GATE_NEUTRAL"})
    # IC-03: the opt-in context-profile flag. Whitelisted so profile
    # conditionals in agents/context templates resolve; source rules/ must
    # never use it (context-profile.marker-in-rule, ERROR).
    conditional_vars.update({"CONTEXT_PROFILE_COMPACT"})
    # IC-09 / C2: the per-provider ``roster_in_harness`` capability gates the
    # compact agent table (orchestrator template). Default-off: only an explicit
    # "true" omits the roster, so an unwired render keeps the names list.
    conditional_vars.update({"ROSTER_IN_HARNESS"})
    conditional_vars.update({k for k in variables if k.startswith("ORCH_MODE_")})
    conditional_vars.update({k for k in variables if k.startswith("REPO_CONTAINMENT_")})
    conditional_vars.update({k for k in variables if k.startswith("SUBAGENT_PERMISSIONS_")})
    conditional_vars.update({k for k in variables if k.endswith("_SET")})
    # IC-03 / IC-17: per-role activity flags (ROLE_<UPPER_SNAKE>_ACTIVE);
    # built from the ActiveSet by build_variables (IC-18 no. 18)
    conditional_vars.update({k for k in variables if k.startswith("ROLE_") and k.endswith("_ACTIVE")})

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
                if not _conditional_active(variables, _var):
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
                is_true = _conditional_active(variables, _var)
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
                is_true = _conditional_active(variables, _var)
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

    A multi-line value is re-indented to the line indentation of its
    placeholder (``_reindent_to_placeholder``), so a ``{{..._BLOCK}}``
    placeholder nested in a YAML literal block or a list item keeps that
    indentation on every line.

    The replacement pass delegates to the shared escape-safe substitution
    core (scripts/lib/substitution.py, issue #476) — function replacement
    keeps values verbatim, never interpreting backslashes or $-group
    references as re.sub replacement escapes (issue #674).

    Args:
        strict: if True, raise SyncError on the first unknown placeholder
            instead of warning and leaving it unsubstituted. Escaped
            placeholders ({{%VAR%}}) and PAL_* placeholders are never
            considered "unknown" — they are exempt in both modes.
            Default False keeps the announce-then-harden behaviour: while the
            D3(a) grace window runs (``_UNRESOLVED_PLACEHOLDER_GRACE_UNTIL``)
            an undefined placeholder warns and names the future error verbatim;
            once the window has passed the call raises that same SyncError
            (issue #983).

    D3(a) live-output guarantee: a placeholder is only evaluated against the
    text that survives conditional stripping. The liveness probe runs the same
    ``strip_inactive_conditional_blocks`` engine on the input and never
    changes the returned text — order-sensitive callers (``agent_sync`` runs
    the PAL deck engine between substitute and strip, issue #277) keep their
    historic substitute-then-strip behaviour byte-for-byte. A token that
    cannot reach the output (e.g. ``{{PIPELINE_DETAILS_DIR}}`` in the
    ``ORCH_MODE_MAIN_CHAT`` branch of ``use-orchestrator.md`` for a strict-mode
    project) therefore never warns and never aborts, while a token in live
    output still does.
    """
    # First pass: protect escaped literals {{%VAR%}} with unique sentinel
    _SENTINEL = "\x00ESC\x00"
    escaped: list[str] = []

    def stash_escape(m):
        escaped.append(m.group(1))
        return f"{_SENTINEL}{len(escaped) - 1}{_SENTINEL}"

    text = re.sub(r"\{\{%([A-Z0-9_]+)%\}\}", stash_escape, text)

    # Liveness probe for the D3(a) decision (issue #983 follow-up): a token
    # that sits only in an inactive {{#if}}/{{#unless}} block is dropped by the
    # caller's conditional strip and never reaches the output, so it must not
    # warn now / abort once `_UNRESOLVED_PLACEHOLDER_GRACE_UNTIL` passes. The
    # probe is computed lazily (only when an unresolved token triggers `keep`)
    # and never rewrites `text`: order-sensitive callers (agent_sync runs the
    # PAL engine between substitute and strip, issue #277) stay byte-identical.
    _live_text_cache: list[str] = []

    def _survives_conditional_strip(matched: str) -> bool:
        if "{{#if" not in text and "{{#unless" not in text:
            return True
        if not _live_text_cache:
            _live_text_cache.append(
                strip_inactive_conditional_blocks(text, variables))
        return matched in _live_text_cache[0]

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
        if not _survives_conditional_strip(matched):
            return matched
        return _placeholder_keep(matched, key, source_label, strict, log)

    text = substitute_placeholders(
        text, _VAR_PATTERN, lookup, keep, _reindent_to_placeholder
    )

    # Third pass: restore escaped literals as {{VAR}} (no substitution happened)
    for i, name in enumerate(escaped):
        text = text.replace(f"{_SENTINEL}{i}{_SENTINEL}", f"{{{{{name}}}}}")

    return text


# --- AGENT_META_REPO derivation (issue #1037) ------------------------------
# AGENT_META_REPO (owner/repo of the agent-meta upstream) is used by the
# meta-feedback/agent-meta-scout/documenter templates. It used to be reachable
# only through an explicit project.yaml `variables:` entry (the --setup wizard
# writes one), so a hand-written project shipped the literal token (27x per
# 9-provider sync). The slug is derivable — no guesswork, no hardcoded fork
# default: the embedded submodule URL or the checkout's own git remote.

_SLUG_PART_RE = re.compile(r"^[A-Za-z0-9_.-]+$")
_GITMODULE_SECTION_RE = re.compile(r'^\[submodule\s+"([^"]+)"\]$')
_GIT_REMOTE_SECTION_RE = re.compile(r'^\[remote\s+"([^"]+)"\]$')
_GITDIR_POINTER_RE = re.compile(r"^gitdir:\s*(.+)$")


def parse_repo_slug(url: str) -> str:
    """``owner/repo`` from a git URL; ``""`` when no slug can be parsed.

    Handles ``https://host/owner/repo(.git)``, ``ssh://git@host[:port]/owner/
    repo``, the scp-like ``git@host:owner/repo`` and a bare ``owner/repo``.
    """
    raw = str(url or "").strip().rstrip("/")
    if not raw:
        return ""
    if raw.endswith(".git"):
        raw = raw[:-4]
    # scp-like 'git@host:owner/repo' — everything after the FIRST colon is the
    # path. Only when there is no scheme, otherwise the colon belongs to it.
    if "://" not in raw and ":" in raw:
        raw = raw.split(":", 1)[1]
    parts = [part for part in raw.split("/") if part]
    if len(parts) < 2:
        return ""
    owner, repo = parts[-2], parts[-1]
    if not (_SLUG_PART_RE.fullmatch(owner) and _SLUG_PART_RE.fullmatch(repo)):
        return ""
    return f"{owner}/{repo}"


def _ini_sections(text: str) -> dict[str, dict[str, str]]:
    """Minimal INI reader for ``.git/config`` (stdlib only).

    Section names keep their quoting as written (``remote "origin"``) so the
    caller can match the sub-section verbatim; keys are lower-cased.
    """
    sections: dict[str, dict[str, str]] = {}
    current: dict[str, str] | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith(("#", ";")):
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            current = sections.setdefault(stripped[1:-1].strip(), {})
            continue
        if current is not None and "=" in stripped:
            key, _, value = stripped.partition("=")
            current[key.strip().lower()] = value.strip()
    return sections


def _parse_gitmodules(text: str) -> list[tuple[str, str]]:
    """``(path, url)`` pairs of a ``.gitmodules`` body."""
    pairs: list[tuple[str, str]] = []
    current: dict[str, str] | None = None
    for line in text.splitlines():
        stripped = line.strip()
        if _GITMODULE_SECTION_RE.match(stripped):
            if current is not None:
                pairs.append((current.get("path", ""), current.get("url", "")))
            current = {}
            continue
        if stripped.startswith("[") and stripped.endswith("]"):
            if current is not None:
                pairs.append((current.get("path", ""), current.get("url", "")))
            current = None
            continue
        if current is not None and "=" in stripped:
            key, _, value = stripped.partition("=")
            current[key.strip().lower()] = value.strip()
    if current is not None:
        pairs.append((current.get("path", ""), current.get("url", "")))
    return [(path, url) for path, url in pairs if path or url]


def _git_remote_url(checkout_root: Path, remote: str = "origin") -> str:
    """URL of *remote* from the checkout's git config, or ``""``.

    A submodule checkout has a ``.git`` *file* holding a ``gitdir:`` pointer
    into the superproject's ``.git/modules/<name>``; the config that carries
    the submodule's own remote lives there. Unreadable/missing → ``""``.
    """
    marker = Path(checkout_root) / ".git"
    git_dir: Path | None = None
    try:
        if marker.is_dir():
            git_dir = marker
        elif marker.is_file():
            match = _GITDIR_POINTER_RE.match(
                marker.read_text(encoding="utf-8").strip())
            if match:
                pointer = match.group(1).strip()
                git_dir = (Path(checkout_root) / pointer).resolve()
    except (OSError, UnicodeDecodeError):
        return ""
    if git_dir is None:
        return ""
    try:
        config_text = (git_dir / "config").read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return ""
    for section, values in _ini_sections(config_text).items():
        match = _GIT_REMOTE_SECTION_RE.match(f"[{section}]")
        if match and match.group(1) == remote:
            return values.get("url", "")
    return ""


def derive_agent_meta_repo(
    agent_meta_root: Path,
    project_root: Path | None = None,
    rel_path: str = "",
) -> str:
    """Derive the ``owner/repo`` slug of the agent-meta upstream, or ``""``.

    Sources, in order:

    1. ``<project_root>/.gitmodules`` — the submodule whose ``path`` matches
       the embedded checkout (*rel_path*, e.g. ``.agent-meta``), otherwise the
       single submodule whose URL names agent-meta.
    2. the agent-meta checkout's own git remote ``origin`` (self-hosting:
       ``<root>/.git/config``; embedded: the ``gitdir:`` pointer target).

    Returns ``""`` when neither source yields a slug: the caller reports the
    miss instead of emitting a guessed/forked repository. An explicit
    ``variables.AGENT_META_REPO`` entry always wins upstream of this helper.
    """
    want_path = (rel_path or "").strip().strip("/")
    gitmodules = (Path(project_root) / ".gitmodules") if project_root else None
    if gitmodules is not None and gitmodules.is_file():
        try:
            pairs = _parse_gitmodules(gitmodules.read_text(encoding="utf-8"))
        except (OSError, UnicodeDecodeError):
            pairs = []
        if want_path:
            for path, url in pairs:
                if path.strip().strip("/") == want_path:
                    slug = parse_repo_slug(url)
                    if slug:
                        return slug
        named = [parse_repo_slug(url) for _path, url in pairs
                 if "agent-meta" in str(url)]
        named = [slug for slug in named if slug]
        if len(named) == 1:
            return named[0]
    return parse_repo_slug(_git_remote_url(Path(agent_meta_root)))
