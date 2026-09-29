"""DoD preset loading and resolution."""

from __future__ import annotations

import re
import sys
from pathlib import Path

from .io import SyncConfigError, _load_yaml_or_json
from .platform import PLATFORM_CONFIGS_DIR, resolve_platform_defaults, resolve_preset_name

DOD_PRESETS_CONFIG_YAML = "config/dod-presets.yaml"
_DOD_PRESETS_CONFIG_LEGACY = "dod-presets.config.yaml"
_DOD_PRESETS_CONFIG_JSON = "dod-presets.config.json"  # legacy fallback

SPEC_PLAN_GROUPS_CONFIG_YAML = "config/spec-plan-groups.yaml"
SPEC_PLAN_GROUP_ID = "plan-mode"

# Closed enum for the declarative group schema (see config/spec-plan-groups.yaml).
SPEC_PLAN_MECHANISMS = (
    "rule-gate",
    "pipeline-stage-condition",
    "sync-scaffold",
    "template-conditional",
    "validator-noop",
    "knowledge-engine-auto-write",
    "dod-flag",
)

# Closed operand set for the `enabled-when` mini-interpreter. No eval/exec:
# only these operands, `and`/`or` and `==` against a literal are understood.
SPEC_PLAN_WHEN_OPERANDS = (
    "seed",
    "ke.enabled",
    "index.mode",
    "dod.spec-plan-traceability",
)

_KE_WHEN = "seed and ke.enabled and index.mode=='knowledge-engine'"
# Traceability enforcement only kicks in when the workflow is on AND the
# resolved DoD flag is set; the aspect must model exactly that (M3).
_DOD_TRACEABILITY_WHEN = "seed and dod.spec-plan-traceability"

# Fail-safe fallback mirroring config/spec-plan-groups.yaml for agent-meta roots
# that predate the framework config. Kept in sync by
# tests/test_spec_plan_group_consistency.py::test_fallback_group_matches_yaml.
_SPEC_PLAN_FALLBACK_SEED_SOURCES = (
    ("spec-plan-workflow.enabled", "explicit"),
    ("dod.spec-plan-required", "dod"),
)
_SPEC_PLAN_FALLBACK_ASPECTS = (
    ("rules-channel", "seed"),
    ("pipeline-gating", "seed"),
    ("scaffold", "seed"),
    ("template-conditional", "seed"),
    ("consistency-noop", "seed"),
    ("recovery-rehydrate", "seed"),
    ("ke-auto-index", _KE_WHEN),
    ("ke-auto-log", _KE_WHEN),
    ("dod-traceability", _DOD_TRACEABILITY_WHEN),
)


def load_dod_presets(agent_meta_root: Path) -> dict:
    """Load config/dod-presets.yaml with fallback to legacy paths."""
    data, _ = _load_yaml_or_json(
        agent_meta_root / DOD_PRESETS_CONFIG_YAML,
        agent_meta_root / _DOD_PRESETS_CONFIG_LEGACY,
        agent_meta_root / _DOD_PRESETS_CONFIG_JSON,
    )
    if not data:
        return {}
    presets = data.get("presets", {})
    # Strip comment keys (JSON legacy: keys starting with "_")
    return {k: {kk: vv for kk, vv in v.items() if not kk.startswith("_")}
            for k, v in presets.items() if not k.startswith("_")}


def resolve_dod_preset_name(config: dict, agent_meta_root: Path) -> str:
    """Resolve the effective dod-preset NAME (not its resolved field
    values -- see resolve_dod() for that).

    Precedence: project.yaml explicit `dod-preset` > platforms: cascade
    default > "full". Shared by resolve_dod() (which resolves preset
    VALUES from this name) and config.py's DOD_PRESET display variable, so
    both stay consistent -- see this task's plan notes for why a single
    shared function exists instead of duplicating the precedence.

    Precedence itself is the shared platform.resolve_preset_name() (same
    helper resolve_conventions() uses), so an explicit `dod-preset: ""`
    opt-out is honored instead of being swallowed by the old `or` chain.
    """
    platforms = config.get("platforms", [])
    platform_defaults = resolve_platform_defaults(
        platforms, agent_meta_root / PLATFORM_CONFIGS_DIR,
    )
    return resolve_preset_name("dod-preset", config, platform_defaults, "full")


def _fallback_spec_plan_group() -> dict:
    """Built-in Plan-Modus group for roots without config/spec-plan-groups.yaml."""
    return {
        "id": SPEC_PLAN_GROUP_ID,
        "seed": {
            "sources": [
                {"config-path": path, "kind": kind}
                for path, kind in _SPEC_PLAN_FALLBACK_SEED_SOURCES
            ],
            "default": False,
        },
        "aspects": [
            {"id": aspect_id, "enabled-when": enabled_when}
            for aspect_id, enabled_when in _SPEC_PLAN_FALLBACK_ASPECTS
        ],
    }


def _load_spec_plan_group(agent_meta_root: Path) -> dict:
    data, _ = _load_yaml_or_json(agent_meta_root / SPEC_PLAN_GROUPS_CONFIG_YAML)
    groups = data.get("groups") if isinstance(data, dict) else None
    group = groups.get(SPEC_PLAN_GROUP_ID) if isinstance(groups, dict) else None
    if isinstance(group, dict) and isinstance(group.get("aspects"), list):
        return group
    return _fallback_spec_plan_group()


_MISSING = object()


def _lookup_dotted(mapping: dict, dotted_path: str):
    current = mapping
    for key in dotted_path.split("."):
        if not isinstance(current, dict) or key not in current:
            return _MISSING
        current = current[key]
    return current


def _resolve_spec_plan_seed(seed: dict, config: dict, agent_meta_root: Path,
                            dod: dict | None) -> bool:
    for source in seed.get("sources", []):
        kind = source.get("kind")
        config_path = source.get("config-path", "")
        if kind == "explicit":
            value = _lookup_dotted(config, config_path)
            if value is not _MISSING:
                return bool(value)
        elif kind == "dod":
            resolved_dod = dod if dod is not None else resolve_dod(config, agent_meta_root)
            key = config_path.rsplit(".", 1)[-1]
            if key in resolved_dod:
                return bool(resolved_dod[key])
        else:
            raise SyncConfigError(
                f"Unknown seed source kind {kind!r} in spec-plan group config"
            )
    return bool(seed.get("default", False))


_WHEN_TOKEN_RE = re.compile(
    r"\s*(?:(?P<operand>[A-Za-z_][A-Za-z0-9_.-]*)|(?P<literal>'[^']*')|(?P<eq>==))"
)


def _tokenize_enabled_when(expression: str) -> list[str]:
    tokens: list[str] = []
    pos = 0
    while pos < len(expression):
        if expression[pos].isspace():
            pos += 1
            continue
        match = _WHEN_TOKEN_RE.match(expression, pos)
        if not match:
            raise SyncConfigError(f"Illegal token in enabled-when {expression!r}")
        tokens.append(match.group(0).strip())
        pos = match.end()
    if not tokens:
        raise SyncConfigError("Empty enabled-when expression")
    return tokens


class _EnabledWhenParser:
    """Recursive-descent evaluator for the closed `enabled-when` grammar."""

    def __init__(self, tokens: list[str], context: dict) -> None:
        self._tokens = tokens
        self._context = context
        self._pos = 0

    def evaluate(self) -> bool:
        value = self._parse_or()
        if self._pos != len(self._tokens):
            raise SyncConfigError(
                "Trailing tokens in enabled-when expression: "
                + " ".join(self._tokens[self._pos:])
            )
        return bool(value)

    def _peek(self) -> str | None:
        return self._tokens[self._pos] if self._pos < len(self._tokens) else None

    def _parse_or(self):
        value = self._parse_and()
        while self._peek() == "or":
            self._pos += 1
            rhs = self._parse_and()
            value = bool(value) or bool(rhs)
        return value

    def _parse_and(self):
        value = self._parse_comparison()
        while self._peek() == "and":
            self._pos += 1
            rhs = self._parse_comparison()
            value = bool(value) and bool(rhs)
        return value

    def _parse_comparison(self):
        operand = self._parse_operand()
        if self._peek() == "==":
            self._pos += 1
            return operand == self._parse_literal()
        return operand

    def _parse_operand(self):
        token = self._peek()
        if token not in SPEC_PLAN_WHEN_OPERANDS:
            raise SyncConfigError(
                f"Illegal enabled-when operand {token!r}; allowed: "
                + ", ".join(SPEC_PLAN_WHEN_OPERANDS)
            )
        self._pos += 1
        return self._context[token]

    def _parse_literal(self):
        token = self._peek()
        if token is None:
            raise SyncConfigError("Missing literal after '==' in enabled-when")
        self._pos += 1
        if token.startswith("'") and token.endswith("'"):
            return token[1:-1]
        if token == "true":
            return True
        if token == "false":
            return False
        return token


def _evaluate_enabled_when(expression: str, context: dict) -> bool:
    return _EnabledWhenParser(_tokenize_enabled_when(expression), context).evaluate()


def _spec_plan_when_context(config: dict, seed: bool, dod: dict | None = None) -> dict:
    knowledge_engine = config.get("knowledge-engine") or {}
    spec_plan = config.get("spec-plan-workflow") or {}
    index = spec_plan.get("index") if isinstance(spec_plan, dict) else None
    index_mode = (index or {}).get("mode", "knowledge-engine")
    return {
        "seed": bool(seed),
        "ke.enabled": bool(knowledge_engine.get("enabled", False)),
        "index.mode": index_mode,
        "dod.spec-plan-traceability": bool(
            (dod or {}).get("spec-plan-traceability", False)
        ),
    }


def _group_references_dod(group: dict) -> bool:
    """True when any aspect expression consumes a resolved DoD flag."""
    return any(
        "dod." in aspect.get("enabled-when", "")
        for aspect in group.get("aspects", [])
    )


def resolve_spec_plan_bundle(config: dict, agent_meta_root: Path,
                             *, dod: dict | None = None) -> dict[str, bool]:
    """Derive ALL Plan-Modus aspects from ONE seed.

    Seed precedence comes from config/spec-plan-groups.yaml: explicit
    `spec-plan-workflow.enabled` > resolved DoD `spec-plan-required` > False.
    Every aspect is a pure function of the seed and the resolved config; no
    aspect may be set independently. Keys: "enabled" (seed) plus one bool per
    aspect id.

    `dod` is the already-resolved DoD dict. When an aspect consumes a DoD flag
    (e.g. `dod-traceability`) and no resolved dict was passed, it is resolved
    once here (fail-closed). ``resolve_dod`` always passes its own resolved
    dict, so the resolve_dod <-> bundle recursion terminates.
    """
    group = _load_spec_plan_group(agent_meta_root)
    if dod is None and _group_references_dod(group):
        dod = resolve_dod(config, agent_meta_root)
    seed = _resolve_spec_plan_seed(
        group.get("seed", {}), config, agent_meta_root, dod,
    )
    context = _spec_plan_when_context(config, seed, dod)
    bundle: dict[str, bool] = {"enabled": seed}
    for aspect in group.get("aspects", []):
        aspect_id = aspect.get("id")
        if not aspect_id:
            raise SyncConfigError("spec-plan group aspect without an 'id'")
        bundle[aspect_id] = _evaluate_enabled_when(
            aspect.get("enabled-when", "seed"), context,
        )
    return bundle


def resolve_spec_plan_enabled(config: dict, agent_meta_root: Path,
                              *, dod: dict | None = None) -> bool:
    """Single source of truth for the native spec/plan workflow master switch.

    Thin wrapper over resolve_spec_plan_bundle() (signature/semantics
    unchanged): returns the seed `enabled`. Pass `dod=` when the caller
    already holds the resolved DoD dict -- this avoids a second resolve_dod()
    call and the resolve_dod <-> resolve_spec_plan_enabled recursion.
    """
    return resolve_spec_plan_bundle(config, agent_meta_root, dod=dod)["enabled"]


def resolve_dod(config: dict, agent_meta_root: Path) -> dict:
    """Resolve effective DoD values from preset + overrides.

    Precedence (highest to lowest):
    1. Project override:  config["dod"][key]
    2. Preset default:    dod-presets.config.yaml[preset][key]
       (preset itself resolved via resolve_dod_preset_name(): project
       `dod-preset` > platforms: cascade default > "full")
    3. "full" preset:     fallback if preset not found
    """
    presets = load_dod_presets(agent_meta_root)
    preset_name = resolve_dod_preset_name(config, agent_meta_root)

    # Fallback to "full" preset when named preset not found
    if preset_name not in presets:
        if preset_name != "full":
            print(f"  !  Unknown dod-preset '{preset_name}' — falling back to 'full'",
                  file=sys.stderr)
        preset_name = "full"

    preset_values = presets.get(preset_name, {})

    dod_overrides = config.get("dod", {})

    # All known DoD keys — sourced from the full preset as authoritative key set
    full_preset = presets.get("full", {
        "req-traceability": True,
        "tests-required": True,
        "codebase-overview": True,
        "security-audit": False,
        "ai-security-review": False,
        "prompt-governance": False,
        "lifecycle-ownership": False,
        "se-required": "false",
    })

    resolved = {}
    for key, default_val in full_preset.items():
        # "release-gates" is a nested dict, not a flat dod field — it has its
        # own resolver (resolve_release_gates()) and its own project.yaml
        # override axis (top-level `release-gates:`, not `dod:`). Excluded
        # here so resolve_dod()'s contract stays "flat bool/string values only".
        if key == "release-gates":
            continue
        if key in dod_overrides:
            resolved[key] = dod_overrides[key]
        elif key in preset_values:
            resolved[key] = preset_values[key]
        else:
            resolved[key] = default_val

    # Synthetic render key -- MUST pass dod=resolved to avoid recursion
    # (resolve_spec_plan_enabled would otherwise call resolve_dod again).
    resolved["spec-plan-enabled"] = resolve_spec_plan_enabled(
        config, agent_meta_root, dod=resolved,
    )
    return resolved


def resolve_release_gates(config: dict, agent_meta_root: Path) -> dict[str, bool]:
    """Resolve enabled/disabled defaults for release-gate scripts (issue #558).

    Two independent sources merge here — deliberately NOT part of the flat
    `dod` block resolved by resolve_dod():

    1. Preset defaults for the built-in gate names, nested under the active
       DoD preset's `release-gates:` key in config/dod-presets.yaml.
    2. Project overrides: the top-level `release-gates:` key in
       .meta-config/project.yaml — highest precedence. Accepts either
       `{name: {enabled: bool, ...}}` (extra keys ignored here, reserved for
       the gate script itself to read) or a bare `{name: bool}`. Can name
       project-specific gates unknown to any preset.

    Returns a dict of gate-name -> bool for every name known to either
    source. A name absent from both (e.g. a project-authored custom gate
    with no project.yaml entry) is intentionally NOT included — callers
    (scripts/lib/hook_plugins.py::sync_release_gates()) fall back to that gate
    script's own `enabled_by_default` header in that case.
    """
    presets = load_dod_presets(agent_meta_root)
    # Same preset name the rest of the DoD layer sees: honors the platforms:
    # cascade (and an explicit "" opt-out), not just the raw project.yaml key.
    preset_name = resolve_dod_preset_name(config, agent_meta_root)
    if preset_name not in presets:
        preset_name = "full"
    preset_gates = presets.get(preset_name, {}).get("release-gates", {}) or {}

    resolved: dict[str, bool] = {k: bool(v) for k, v in preset_gates.items()}

    project_gates_cfg = config.get("release-gates", {}) or {}
    for name, entry in project_gates_cfg.items():
        if isinstance(entry, dict) and "enabled" in entry:
            resolved[name] = bool(entry["enabled"])
        elif isinstance(entry, bool):
            resolved[name] = entry
    return resolved
