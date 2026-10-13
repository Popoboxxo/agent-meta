"""Registry validator for config/known-issues.yaml (IC-21, Task 0d.1).

Pure functions, no test code. Validates form, enums, predicate / detector
grammar, the `command` allowlist and the bindings to the capability matrix.
Fail-soft contract for the doctor runner (Task 0d.2): validation never raises
on malformed input; it returns human-readable error strings, which the runner
turns into `doctor.registry-invalid` findings and skips the entry.
Only validation lives here; evaluating predicates / bindings is 0d.2.
"""

import json
import re
from datetime import date
from pathlib import Path

import yaml

_SEVERITIES = {"ERROR", "WARNING", "INFO"}
_VERIFIED = {
    "VERIFIED-RUNTIME", "VERIFIED-SOURCE", "SOURCE-DERIVED", "DOCUMENTED",
    "UNVERIFIED",
}
_EVIDENCE_KINDS = {"runtime", "source", "docs", "third-party"}
_FIX_OWNERS = {"agent-meta-manager", "framework-issue", "project-config"}
_PRED_OPS = {"present", "absent", "eq", "ne", "truthy", "falsy", "in", "gt", "lt"}
_OPS_WITH_VALUE = {"eq", "ne", "in", "gt", "lt"}
_ARTIFACTS = {
    "context_file", "rules_dir", "agents_dir", "skills_dir", "commands_dir",
    "hooks_config_file", "project_config", "sync_log",
}
_DETECTOR_KINDS = {
    "file-size", "regex", "path-exists", "yaml-key", "toml-key", "json-schema",
    "command", "finding-ref", "variable-unreferenced",
}
_FINDING_SOURCES = {
    "context-budget", "active-set", "consistency", "hooks", "sync-log", "doctor",
}
_JSON_SCHEMA_KEYWORDS = {
    "type", "required", "properties", "additionalProperties", "enum",
}
# AC-85: --deactivation-status is deliberately absent; --dry-run is appended by
# the runner, never written in argv.
COMMAND_ALLOWLIST = (
    ("--check",),
    ("--context-report", "--json"),
    ("--cleanup-preview",),
)
FORBIDDEN_ARGV = {"--dry-run", "--deactivation-status"}
_BINDABLE = {"role", "key", "provider"}
_ALWAYS_BOUND = {"provider", "tmp_sink", "agents_dir", "extension_dir", "agent_ext"}
_MESSAGE_ONLY_BOUND = {"reason", "length"}
_PLACEHOLDER = re.compile(r"\{([a-z_]+)\}")


# ---------------------------------------------------------------- key binding

def _walk(node, parts):
    """Yield True if the dotted path (``*`` = any map key) resolves in node."""
    if not parts:
        return True
    head, rest = parts[0], parts[1:]
    if not isinstance(node, dict):
        return False
    if head == "*":
        return any(_walk(v, rest) for v in node.values())
    return head in node and _walk(node[head], rest)


def _key_resolves(path, ctx):
    """Capability-key path resolves in provider-capabilities (IC-09) or, for
    provider contract keys such as agent_ext, in ai-providers.yaml."""
    if not isinstance(path, str) or not path:
        return False
    parts = path.split(".")
    for source in (ctx["caps"], ctx["providers"]):
        if any(_walk(entry, parts) for entry in source.values()):
            return True
    return False


# ------------------------------------------------------------------ validator

def _check_placeholders(text, allowed, where, errors):
    if not isinstance(text, str):
        return
    for name in _PLACEHOLDER.findall(text):
        if name not in allowed:
            errors.append(f"{where}: unbound placeholder {{{name}}}")


def _validate_predicate(pred, ctx, where, errors, bound):
    if not isinstance(pred, dict):
        errors.append(f"{where}: predicate must be a mapping")
        return
    if "active_role_where" in pred:
        crit = pred["active_role_where"]
        if (not isinstance(crit, dict) or len(crit) != 1
                or next(iter(crit)) not in ("tools_without", "tools_with")
                or not isinstance(next(iter(crit.values())), list)):
            errors.append(f"{where}: active_role_where needs tools_without|tools_with list")
        bound.add("role")
        return
    if "active_role" in pred:
        if pred.get("op") not in ("truthy", "falsy"):
            errors.append(f"{where}: active_role op must be truthy|falsy")
        if not isinstance(pred["active_role"], str):
            errors.append(f"{where}: active_role must be a role name")
        return
    if "surface_has_target" in pred:
        _check_placeholders(pred["surface_has_target"], bound | {"key"}, where, errors)
        if pred["surface_has_target"] != "{key}":
            errors.append(f"{where}: surface_has_target must be the {{key}} binding")
        return
    kind = "capability" if "capability" in pred else "config" if "config" in pred else None
    if kind is None:
        errors.append(f"{where}: predicate needs capability|config|active_role|active_role_where")
        return
    path = pred[kind]
    op = pred.get("op")
    if op not in _PRED_OPS:
        errors.append(f"{where}: bad op {op!r}")
    if kind == "capability":
        if not _key_resolves(path, ctx):
            errors.append(f"{where}: capability key {path!r} not found in provider-capabilities/ai-providers")
        if path == "name" or path.startswith("name."):
            errors.append(f"{where}: provider identity predicate (name) is forbidden")
        if "*" in path.split("."):
            bound.add("key")
    else:
        if not isinstance(path, str) or path.split(".")[0] not in ctx["schema_top"]:
            errors.append(f"{where}: config key {path!r} not in project-config schema")
    has_value, has_value_key = "value" in pred, "value_key" in pred
    if op in _OPS_WITH_VALUE:
        if has_value == has_value_key:
            errors.append(f"{where}: op {op} needs exactly one of value|value_key")
    elif has_value or has_value_key:
        errors.append(f"{where}: op {op} takes no value")
    if has_value_key and not _key_resolves(pred["value_key"], ctx):
        errors.append(f"{where}: value_key {pred['value_key']!r} not found in capabilities")
    # Provider identity as a value (display name or registry key) is forbidden.
    candidates = pred["value"] if isinstance(pred.get("value"), list) else [pred.get("value")]
    for cand in candidates:
        if isinstance(cand, str) and cand in ctx["identities"]:
            errors.append(f"{where}: provider identity {cand!r} used as value")
    if "default" in pred and kind != "config":
        errors.append(f"{where}: default is only valid on config predicates")


def _validate_detector(det, ctx, where, errors, bound, nested=False):
    if not isinstance(det, dict):
        errors.append(f"{where}: detector must be a mapping")
        return
    if "any_of" in det:
        subs = det["any_of"]
        if set(det) != {"any_of"} or not isinstance(subs, list) or len(subs) < 2:
            errors.append(f"{where}: any_of must be the only key and hold >= 2 detectors")
            return
        if nested:
            errors.append(f"{where}: any_of must not be nested")
        for i, sub in enumerate(subs):
            _validate_detector(sub, ctx, f"{where}.any_of[{i}]", errors, bound, nested=True)
        return
    kind = det.get("kind")
    if kind not in _DETECTOR_KINDS:
        errors.append(f"{where}: unsupported detector kind {kind!r}")
        return
    keys = set(det) - {"kind"}

    def need(required, optional=()):
        missing = set(required) - keys
        extra = keys - set(required) - set(optional)
        if missing:
            errors.append(f"{where}: {kind} missing {sorted(missing)}")
        if extra:
            errors.append(f"{where}: {kind} unknown fields {sorted(extra)}")

    if kind == "file-size":
        need({"unit", "op"}, {"limit", "limit_key"})
        if det.get("unit") not in ("bytes", "chars", "lines"):
            errors.append(f"{where}: bad unit")
        if det.get("op") not in (">", ">="):
            errors.append(f"{where}: bad file-size op")
        if ("limit" in det) == ("limit_key" in det):
            errors.append(f"{where}: file-size needs exactly one of limit|limit_key")
        if "limit_key" in det and not _key_resolves(det["limit_key"], ctx):
            errors.append(f"{where}: limit_key {det['limit_key']!r} not found")
    elif kind == "regex":
        need({"expect"}, {"pattern", "pattern_from_config", "literal", "default",
                          "line_anchored", "optional_suffix", "allow", "scope",
                          "path", "path_template"})
        if ("pattern" in det) == ("pattern_from_config" in det):
            errors.append(f"{where}: regex needs exactly one of pattern|pattern_from_config")
        if det.get("expect") not in ("match", "no-match"):
            errors.append(f"{where}: bad regex expect")
        if "pattern" in det:
            try:
                re.compile(det["pattern"], re.MULTILINE)
            except re.error as exc:
                errors.append(f"{where}: invalid regex ({exc})")
            for extra in ("literal", "default", "optional_suffix"):
                if extra in det:
                    errors.append(f"{where}: {extra} requires pattern_from_config")
        else:
            if det["pattern_from_config"].split(".")[0] not in ctx["schema_top"]:
                errors.append(f"{where}: pattern_from_config {det['pattern_from_config']!r} not in schema")
            if "literal" in det and det["literal"] is not True:
                errors.append(f"{where}: literal must be true (re.escape semantics)")
        if det.get("scope", "all") not in ("frontmatter", "body", "all"):
            errors.append(f"{where}: bad regex scope")
        _check_placeholders(det.get("path_template"), bound | _ALWAYS_BOUND,
                            f"{where}.path_template", errors)
    elif kind == "path-exists":
        need({"expect"}, {"path", "glob", "path_template", "require_suffix_key",
                          "exclude_glob", "bind", "then"})
        if det.get("expect") not in ("present", "absent"):
            errors.append(f"{where}: bad path-exists expect")
        if sum(k in det for k in ("path", "glob", "path_template")) != 1:
            errors.append(f"{where}: path-exists needs exactly one of path|glob|path_template")
        if "require_suffix_key" in det and not _key_resolves(det["require_suffix_key"], ctx):
            errors.append(f"{where}: require_suffix_key not found")
        local = set(bound)
        if "bind" in det:
            if det["bind"] not in _BINDABLE:
                errors.append(f"{where}: bind must be one of {sorted(_BINDABLE)}")
            local.add(det["bind"])
            bound.add(det["bind"])
        for field in ("path", "glob", "path_template", "exclude_glob"):
            if field in det:
                _check_placeholders(det[field], local | _ALWAYS_BOUND, f"{where}.{field}", errors)
        if "bind" in det and "then" not in det:
            errors.append(f"{where}: bind requires then")
        if "then" in det:
            if "bind" not in det:
                errors.append(f"{where}: then requires bind")
            _validate_detector(det["then"], ctx, f"{where}.then", errors, local, nested=True)
    elif kind in ("yaml-key", "toml-key"):
        optional = {"frontmatter", "value", "value_key"}
        if kind == "yaml-key":
            optional.add("subject")
        need({"key", "op"}, optional)
        if det.get("op") not in _PRED_OPS:
            errors.append(f"{where}: bad op")
        if det.get("op") in _OPS_WITH_VALUE and ("value" in det) == ("value_key" in det):
            errors.append(f"{where}: op {det['op']} needs exactly one of value|value_key")
        if "value_key" in det and not _key_resolves(det["value_key"], ctx):
            errors.append(f"{where}: value_key {det['value_key']!r} not found")
        if det.get("subject") not in (None, "capability"):
            errors.append(f"{where}: subject must be capability")
        if det.get("subject") == "capability" and not _key_resolves(det["key"], ctx):
            errors.append(f"{where}: capability key {det['key']!r} not found")
        if "*" in str(det.get("key", "")).split("."):
            bound.add("key")
    elif kind == "json-schema":
        need(set(), {"schema", "schema_from_key"})
        if ("schema" in det) == ("schema_from_key" in det):
            errors.append(f"{where}: json-schema needs exactly one of schema|schema_from_key")
        if "schema_from_key" in det and not _key_resolves(det["schema_from_key"], ctx):
            errors.append(f"{where}: schema_from_key not found")

        def keywords(node, path):
            if not isinstance(node, dict):
                return
            for kw, sub in node.items():
                if path.endswith(".properties"):
                    keywords(sub, f"{path}.{kw}")  # property name, not keyword
                    continue
                if kw not in _JSON_SCHEMA_KEYWORDS:
                    errors.append(f"{where}: unsupported json-schema keyword {kw!r}")
                elif kw == "properties" and isinstance(sub, dict):
                    keywords(sub, f"{path}.properties")
        keywords(det.get("schema"), "schema")
    elif kind == "command":
        need({"argv", "expect_exit"}, {"timeout_s"})
        argv = det.get("argv")
        if not (isinstance(argv, list) and all(isinstance(a, str) for a in argv)):
            errors.append(f"{where}: argv must be a list of strings")
        else:
            if FORBIDDEN_ARGV & set(argv):
                errors.append(f"{where}: argv contains forbidden flag {sorted(FORBIDDEN_ARGV & set(argv))}")
            if tuple(argv) not in COMMAND_ALLOWLIST:
                errors.append(f"{where}: argv {argv} not in command allowlist")
        if not isinstance(det.get("expect_exit"), int):
            errors.append(f"{where}: expect_exit must be int")
    elif kind == "finding-ref":
        need({"check", "source"}, {"match"})
        if det.get("source") not in _FINDING_SOURCES:
            errors.append(f"{where}: bad finding-ref source {det.get('source')!r}")
        if det.get("source") == "doctor" and not str(det.get("check", "")).startswith("doctor."):
            errors.append(f"{where}: source doctor needs a doctor.* check")
    elif kind == "variable-unreferenced":
        need({"key", "universe"})
        if det.get("key") == "*":
            bound.add("key")
        if det.get("universe") != "all-roles-all-providers":
            errors.append(f"{where}: universe must be all-roles-all-providers")


def _validate_verified_by_capability(spec, ctx, where, errors):
    if not isinstance(spec, dict) or not spec:
        errors.append(f"{where}: must be a non-empty mapping")
        return
    if "derive" in spec:
        m = re.fullmatch(r"surface_verified_state\.([a-z_]+)", str(spec["derive"]))
        if len(spec) != 1 or not m or not _key_resolves(spec["derive"], ctx):
            errors.append(f"{where}: derive must be surface_verified_state.<surface>")
        return
    for cap_key, mapped in spec.items():
        if not _key_resolves(cap_key, ctx):
            errors.append(f"{where}: capability key {cap_key!r} not found")
        values = mapped.values() if isinstance(mapped, dict) else [mapped]
        for state in values:
            if state not in _VERIFIED:
                errors.append(f"{where}: bad verified-state {state!r}")


def validate_entry(entry, ctx):
    errors = []
    eid = entry.get("id", "<no id>") if isinstance(entry, dict) else "<?>"
    where = f"[{eid}]"
    required = {
        "id", "title", "applies_to", "target", "detector", "severity",
        "verified-state", "evidence", "fix-hint", "fix-owner", "introduced-in",
        "fixed-in",
    }
    optional = {"message", "verified-state-by-capability"}
    missing, extra = required - set(entry), set(entry) - required - optional
    if missing:
        errors.append(f"{where}: missing fields {sorted(missing)}")
    if extra:
        errors.append(f"{where}: unknown fields {sorted(extra)}")
    if missing:
        return errors
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", str(entry["id"])):
        errors.append(f"{where}: id must be kebab-case")
    if not isinstance(entry["title"], str) or "\n" in entry["title"].strip():
        errors.append(f"{where}: title must be one line")
    if entry["severity"] not in _SEVERITIES:
        errors.append(f"{where}: bad severity")
    if entry["verified-state"] not in _VERIFIED:
        errors.append(f"{where}: bad verified-state")
    elif entry["verified-state"] == "UNVERIFIED" and entry["severity"] == "ERROR":
        errors.append(f"{where}: UNVERIFIED entries must not declare severity ERROR (ADR-11 cap)")
    if entry["fix-owner"] not in _FIX_OWNERS:
        errors.append(f"{where}: bad fix-owner")
    for field in ("introduced-in", "fixed-in"):
        if entry[field] is not None and not isinstance(entry[field], str):
            errors.append(f"{where}: {field} must be a version string or null")
    ev = entry["evidence"]
    if (not isinstance(ev, dict) or set(ev) != {"kind", "ref", "date"}
            or ev["kind"] not in _EVIDENCE_KINDS or not ev["ref"]):
        errors.append(f"{where}: evidence must be {{kind, ref, date}} with valid kind")
    else:
        try:
            if not isinstance(ev["date"], str):
                raise ValueError("date must be a quoted string")
            date.fromisoformat(ev["date"])
        except ValueError:
            errors.append(f"{where}: evidence date must be YYYY-MM-DD")
    # target
    target = entry["target"]
    if not isinstance(target, dict) or "artifact" not in target:
        errors.append(f"{where}: target.artifact required")
        target = {"artifact": None}
    else:
        extra_t = set(target) - {"artifact", "role", "path"}
        if extra_t:
            errors.append(f"{where}: unknown target fields {sorted(extra_t)}")
        art = target["artifact"]
        if art not in _ARTIFACTS and not _key_resolves(art, {**ctx, "caps": {}}):
            errors.append(f"{where}: target.artifact {art!r} is neither a known artifact nor an ai-providers key")
    # predicates
    bound = set(_ALWAYS_BOUND)
    if not isinstance(entry["applies_to"], list):
        errors.append(f"{where}: applies_to must be a list")
    else:
        for i, pred in enumerate(entry["applies_to"]):
            _validate_predicate(pred, ctx, f"{where}.applies_to[{i}]", errors, bound)
    _validate_detector(entry["detector"], ctx, f"{where}.detector", errors, bound)
    if "verified-state-by-capability" in entry:
        _validate_verified_by_capability(
            entry["verified-state-by-capability"], ctx,
            f"{where}.verified-state-by-capability", errors)
    # bindings (only bound names may appear in templated text)
    for label, text in (
        ("target.role", target.get("role")), ("target.path", target.get("path")),
        ("message", entry.get("message")), ("fix-hint", entry["fix-hint"]),
    ):
        allowed = bound | (_MESSAGE_ONLY_BOUND if label == "message" else set())
        _check_placeholders(text, allowed, f"{where}.{label}", errors)
    return errors


def validate_registry(doc, ctx):
    errors = []
    if not isinstance(doc, dict) or doc.get("registry-version") != 1:
        return ["registry-version must be 1"]
    issues = doc.get("issues")
    if not isinstance(issues, list) or not issues:
        return ["issues must be a non-empty list"]
    if set(doc) - {"registry-version", "issues"}:
        errors.append(f"unknown top-level keys {sorted(set(doc) - {'registry-version', 'issues'})}")
    seen = set()
    for entry in issues:
        eid = entry.get("id") if isinstance(entry, dict) else None
        if eid in seen:
            errors.append(f"duplicate id {eid!r}")
        seen.add(eid)
        errors.extend(validate_entry(entry, ctx) if isinstance(entry, dict) else ["entry not a mapping"])
    return errors

def load_validation_context(agent_meta_root):
    """Load the reference data the validator binds against."""
    root = Path(agent_meta_root)
    caps = yaml.safe_load(
        (root / "config" / "provider-capabilities.yaml").read_text(encoding="utf-8")
    )["capabilities"]
    providers = yaml.safe_load(
        (root / "config" / "ai-providers.yaml").read_text(encoding="utf-8")
    )["providers"]
    schema = json.loads(
        (root / "config" / "project-config.schema.json").read_text(encoding="utf-8")
    )
    return {
        "caps": caps,
        "providers": providers,
        "schema_top": set(schema["properties"]),
        "identities": set(caps) | set(providers),
    }
