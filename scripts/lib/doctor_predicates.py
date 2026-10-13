"""Predicate, binding and verified-state evaluation for the doctor (IC-21, Task 0d.2).

Evaluates the ``applies_to`` grammar of ``config/known-issues.yaml`` against one
provider context (:class:`Env`). Provider differences are expressed only by
capability / config keys, never by provider identity. Pure functions, no writes.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Optional

from .doctor_formats import version_key
from .frontmatter import parse_frontmatter_text

MISSING = object()
UNVERIFIED = "UNVERIFIED"
_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")
# Detector kinds that carry their own provider handling (they receive providers).
_SELF_SCOPED_KINDS = {"finding-ref", "command", "variable-unreferenced"}
_PROVIDER_FREE_ARTIFACTS = {"project_config", "sync_log"}
_CAPABILITY_FIELDS = ("limit_key", "value_key", "require_suffix_key", "schema_from_key")


@dataclass
class Env:
    """Evaluation context of one registry entry for one provider (or all)."""

    project_root: Path
    agent_meta_root: Path
    config: dict
    active_set: Any
    caps_map: dict                  # merged capabilities + ai-providers per provider
    provider_config: dict
    providers: tuple                # providers covered by this env
    provider: str = ""              # "" = provider-independent
    caps: dict = field(default_factory=dict)
    bindings: dict = field(default_factory=dict)
    sink_enabled: bool = True
    shared: dict = field(default_factory=dict)   # run-wide caches (log, templates, ...)


# ------------------------------------------------------------------ key paths

def iter_paths(node, dotted: str):
    """Yield ``(bindings, value)`` for a dotted path; ``*`` iterates map keys.

    Without wildcard exactly one item is yielded (value ``MISSING`` if absent).
    """
    def walk(cur, parts, binds):
        if not parts:
            yield binds, cur
            return
        head, rest = parts[0], parts[1:]
        if head == "*":
            if isinstance(cur, dict):
                for key in sorted(cur, key=str):
                    yield from walk(cur[key], rest, {**binds, "key": str(key)})
            return
        if isinstance(cur, dict) and head in cur:
            yield from walk(cur[head], rest, binds)
        elif "*" not in rest and head != "*":
            yield binds, MISSING

    yield from walk(node, dotted.split("."), {})


def get_path(node, dotted: str, default=MISSING):
    for _, value in iter_paths(node, dotted):
        return default if value is MISSING else value
    return default


def is_present(value) -> bool:
    return value is not MISSING and value is not None and value != "" and value != [] and value != {}


def compare(op: str, actual, expected=None) -> bool:
    """Evaluate the predicate / detector operator grammar."""
    if op == "present":
        return is_present(actual)
    if op == "absent":
        return not is_present(actual)
    value = None if actual is MISSING else actual
    if op == "truthy":
        return bool(value)
    if op == "falsy":
        return not value
    try:
        if op == "eq":
            return value == expected
        if op == "ne":
            return value != expected
        if op == "in":
            return value in expected
        if op == "gt":
            return value is not None and value > expected
        if op == "lt":
            return value is not None and value < expected
    except TypeError:
        return False
    return False


def expected_value(pred: dict, env: Env):
    if "value_key" in pred:
        return get_path(env.caps, pred["value_key"], None)
    return pred.get("value")


# ------------------------------------------------------------------- bindings

def render(template, bindings: dict) -> str:
    """Substitute ``{name}`` bindings; unknown names are left untouched."""
    if not isinstance(template, str):
        return ""
    return _PLACEHOLDER.sub(
        lambda m: str(bindings[m.group(1)]) if m.group(1) in bindings else m.group(0),
        template)


def base_bindings(provider: str, caps: dict, sink_path: str) -> dict:
    return {
        "provider": provider,
        "tmp_sink": sink_path,
        "agents_dir": str(caps.get("agents_dir") or ""),
        "extension_dir": str(caps.get("extension_dir") or ""),
        "agent_ext": str(caps.get("agent_ext") or ".md"),
    }


# ----------------------------------------------------------------- predicates

def _template_tools(agent_meta_root: Path, role: str) -> Optional[list]:
    for path in sorted(Path(agent_meta_root).glob(f"agents/*/{role}.md")):
        try:
            fm = parse_frontmatter_text(path.read_text(encoding="utf-8"))
        except OSError:
            continue
        tools = fm.get("tools", [])
        if isinstance(tools, str):
            tools = [t.strip() for t in tools.split(",")]
        return [str(t) for t in tools] if isinstance(tools, list) else []
    return None


def _roles_where(crit: dict, env: Env) -> list:
    (mode, wanted), = crit.items()
    roles = []
    for role in sorted(env.active_set.roles):
        tools = _template_tools(env.agent_meta_root, role)
        if tools is None:
            continue
        has_any = any(t in tools for t in wanted)
        if (mode == "tools_with" and has_any) or (mode == "tools_without" and not has_any):
            roles.append(role)
    return roles


def _value_predicate(pred: dict, env: Env) -> list:
    """Binding dicts for which a capability / config predicate holds."""
    is_cap = "capability" in pred
    node = env.caps if is_cap else env.config
    expected = expected_value(pred, env)
    out = []
    for binds, value in iter_paths(node, pred["capability" if is_cap else "config"]):
        if value is MISSING and "default" in pred:
            value = pred["default"]
        if compare(pred["op"], value, expected):
            out.append(binds)
    return out


def evaluate_predicates(preds: list, env: Env) -> tuple:
    """Return ``(binding combos, deferred surface filters)``; no combos = not applicable."""
    combos: list = [{}]
    deferred: list = []
    for pred in preds or []:
        if "surface_has_target" in pred:
            deferred.append(pred)
            continue
        if "active_role_where" in pred:
            roles = _roles_where(pred["active_role_where"], env)
            combos = [{**c, "role": r} for c in combos for r in roles]
        elif "active_role" in pred:
            active = pred["active_role"] in env.active_set.roles
            if active != (pred["op"] == "truthy"):
                combos = []
        else:
            matches = _value_predicate(pred, env)
            combos = [{**c, **m} for c in combos for m in matches]
        if not combos:
            return [], deferred
    return combos, deferred


def surface_mapper():
    """``surface_target_key`` of context_budget (surface -> ai-providers target key)."""
    from .consistency.context_budget import surface_target_key

    return surface_target_key


def passes_deferred(deferred: list, bindings: dict) -> bool:
    """``surface_has_target: "{key}"`` filter (mapping source: context_budget)."""
    if not deferred:
        return True
    mapper = surface_mapper()
    key = bindings.get("key")
    return bool(key and mapper(key))


def needs_provider(entry: dict) -> bool:
    """True when the entry must be evaluated once per provider."""
    for pred in entry.get("applies_to") or []:
        if "capability" in pred or "surface_has_target" in pred:
            return True
    detectors = [entry["detector"]]
    while detectors:
        det = detectors.pop()
        detectors.extend(det.get("any_of") or [])
        if "then" in det:
            detectors.append(det["then"])
        if det.get("subject") == "capability" or any(f in det for f in _CAPABILITY_FIELDS):
            return True
        if "any_of" not in det and det.get("kind") not in _SELF_SCOPED_KINDS:
            if entry["target"].get("artifact") not in _PROVIDER_FREE_ARTIFACTS:
                return True
            if any("{" + n + "}" in str(v) for v in det.values()
                   for n in ("agents_dir", "agent_ext", "extension_dir")):
                return True
    return False


# ------------------------------------------------------------- verified state

def resolve_verified_state(entry: dict, env: Env) -> str:
    """Per-provider verified-state (``verified-state-by-capability``).

    ``derive``: the provider's ``surface_verified_state.<surface>``. Capability
    mapping: first key that is present for the provider wins; a scalar maps the
    key to a state, a dict dispatches on the capability value. Fallback is the
    top-level ``verified-state``.
    """
    fallback = entry["verified-state"]
    spec = entry.get("verified-state-by-capability")
    if not spec or not env.provider:
        return fallback
    if "derive" in spec:
        state = get_path(env.caps, spec["derive"], None)
        return state if isinstance(state, str) else fallback
    for key, mapped in spec.items():
        value = get_path(env.caps, key)
        if not is_present(value):
            continue
        if isinstance(mapped, dict):
            for candidate, state in mapped.items():
                if candidate == value or str(candidate) == str(value):
                    return state
            return fallback
        return mapped
    return fallback


def fixed_in_reached(current: str, fixed_in) -> bool:
    return bool(fixed_in) and version_key(current) >= version_key(fixed_in)
