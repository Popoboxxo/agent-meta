"""Registry-driven detectors of the doctor runner (IC-21 / IC-22, Task 0d.2).

Table dispatch per detector kind (:data:`DETECTORS`). A detector returns a list
of :class:`Hit` - each hit means "the condition stated by the detector holds"
(an ``any_of`` yields a hit only when no sub-detector hits). Detectors are
strictly read-only: they only read project files; ``command`` runs an
allowlisted ``sync.py`` argv (plus ``--dry-run``) without a shell.
``finding-ref`` imports the IC-10 / IC-19 check functions - there is no second
implementation of those checks here.
"""
from __future__ import annotations

import fnmatch
import importlib
import os
import re
import subprocess
import sys
from dataclasses import dataclass, field, replace
from pathlib import Path
from typing import Optional

import yaml

from .consistency.report import Severity
from .doctor_formats import (
    TomlUnsupported, clip, parse_toml, schema_from_capability_value,
    validate_schema_subset,
)
from .doctor_predicates import (
    MISSING, Env, compare, expected_value, get_path, is_present, iter_paths, render,
)
from .doctor_registry import COMMAND_ALLOWLIST, FORBIDDEN_ARGV
from .frontmatter import parse_frontmatter_text, split_frontmatter
from .repo_containment import TmpSinkError
from .tmp_paths import resolve_tmp_paths

PROJECT_CONFIG_REL = ".meta-config/project.yaml"
RUNTIME_READERS_REL = "config/runtime-config-readers.yaml"
SYNC_LOG_REL = "sync.log"
CAPABILITY_FILE_REL = "config/provider-capabilities.yaml"
CHECK_ENVIRONMENT = "doctor.environment"
CHECK_TMP_SINK = "doctor.tmp-sink-location"
DEFAULT_COMMAND_TIMEOUT_S = 60
_DIR_ARTIFACTS = ("rules_dir", "agents_dir", "skills_dir", "commands_dir")
_TEMPLATE_ROOTS = ("agents", "rules", "templates", "snippets", "commands")
_LOG_LINE = re.compile(r"^\[(INFO|WARN)\]\s+([A-Za-z0-9_.*-]+):?(?:\s|$)")
# check source -> module holding the IC-10 / IC-19 check functions
_CHECK_MODULES = {
    "context-budget": ".consistency.context_budget",
    "active-set": ".consistency.active_set_refs",
}


@dataclass
class Hit:
    file: str = ""
    line: int = 0
    quoted: str = ""
    bindings: dict = field(default_factory=dict)
    severity: Optional[Severity] = None   # raw severity of a referenced check
    ref_check: str = ""
    provider: str = ""   # provider of a per-provider referenced check (else env.provider)


class DetectorUnavailable(Exception):
    """The detector cannot run here (``doctor.detector-unavailable``)."""

    def __init__(self, reason: str, notify: bool = True):
        super().__init__(reason)
        self.reason = reason
        self.notify = notify


class DetectorSkipped(Exception):
    """A required config value is missing: the entry is skipped (``predicate``)."""


# ------------------------------------------------------------------- targets

def _rel(path: Path, root: Path) -> str:
    try:
        return path.relative_to(root).as_posix()
    except ValueError:
        return str(path)


def _files_in(directory: Path, suffix: Optional[str] = None) -> list:
    if not directory.is_dir():
        return []
    return [p for p in sorted(directory.rglob("*"))
            if p.is_file() and (suffix is None or p.name.endswith(suffix))]


def target_files(tgt: dict, env: Env) -> list:
    """Existing artifact files of an entry target (sorted, project-relative base)."""
    root = env.project_root
    path = render(tgt.get("path"), env.bindings)
    if path:
        full = root / path
        return [full] if full.is_file() else _files_in(full)
    art = tgt["artifact"]
    if art == "project_config":
        full = root / PROJECT_CONFIG_REL
        return [full] if full.is_file() else []
    if art == "sync_log":
        full = root / SYNC_LOG_REL
        return [full] if full.is_file() else []
    if art == "hooks_config_file":
        rel = env.caps.get("settings_file") or env.caps.get("hooks_config_file")
    else:
        rel = get_path(env.caps, art, None)
    if not isinstance(rel, str) or not rel:
        return []
    full = root / rel
    if art == "context_file":
        return [full] if full.is_file() else []
    if art in _DIR_ARTIFACTS:
        role = render(tgt.get("role"), env.bindings)
        ext = env.bindings.get("agent_ext") or ".md"
        if art == "agents_dir" and role:
            one = full / (role + ext)
            return [one] if one.is_file() else []
        return _files_in(full, ext if art == "agents_dir" else None)
    return [full] if full.is_file() else _files_in(full)


def _read(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _explicit_files(det: dict, env: Env) -> Optional[list]:
    """Files named by ``path`` / ``path_template`` of a detector, else ``None``."""
    rel = det.get("path") or det.get("path_template")
    if not rel:
        return None
    full = env.project_root / render(rel, env.bindings)
    return [full] if full.is_file() else []


# ---------------------------------------------------------------- file-size

def _measure(path: Path, unit: str, env: Env, tgt: dict) -> Optional[int]:
    from .context_report import count_text_stats, measure_artifacts

    data = path.read_bytes()
    if unit == "chars":
        return len(data.decode("utf-8", errors="replace"))
    stat = None
    if tgt["artifact"] == "context_file" and not tgt.get("path") and env.provider:
        report = env.shared.setdefault("report", {}).get(env.provider)
        if report is None:
            report = measure_artifacts(env.project_root, [env.provider], env.caps_map)
            env.shared["report"][env.provider] = report
        stat = (report.get(env.provider) or {}).get("entry-file")
    if stat is None:
        stat = count_text_stats(data)
    return stat["bytes"] if unit == "bytes" else stat["lines"]


def detect_file_size(det: dict, env: Env, tgt: dict) -> list:
    limit = det["limit"] if "limit" in det else get_path(env.caps, det["limit_key"], None)
    if not isinstance(limit, int) or isinstance(limit, bool):
        return []
    hits = []
    for path in target_files(tgt, env):
        try:
            value = _measure(path, det["unit"], env, tgt)
        except OSError:
            continue
        over = value >= limit if det["op"] == ">=" else value > limit
        if over:
            hits.append(Hit(_rel(path, env.project_root),
                            quoted=f"{value} {det['unit']} {det['op']} {limit}"))
    return hits


# -------------------------------------------------------------------- regex

def _regex_source(det: dict, env: Env) -> str:
    if "pattern" in det:
        return det["pattern"]
    value = get_path(env.config, det["pattern_from_config"], None)
    if not is_present(value):
        value = det.get("default")
    if not is_present(value):
        raise DetectorSkipped(det["pattern_from_config"])
    lines = [ln.strip() for ln in str(value).splitlines() if ln.strip()]
    text = next((ln for ln in lines if len(ln) >= 20), lines[0] if lines else "")
    body = re.escape(text)
    if det.get("optional_suffix"):
        body += "(?:" + re.escape(det["optional_suffix"]) + ")?"
    if det.get("line_anchored"):
        return r"^/?(?:" + body + r")[ \t\r]*$"
    return body


def _scope_text(text: str, scope: str) -> tuple:
    """Return ``(region text, line offset)`` for the regex scope."""
    if scope == "all":
        return text, 0
    block, body = split_frontmatter(text)
    if scope == "frontmatter":
        return block, 0
    return body, block.count("\n")


def detect_regex(det: dict, env: Env, tgt: dict) -> list:
    pattern = re.compile(_regex_source(det, env), re.MULTILINE)
    files = _explicit_files(det, env)
    if files is None:
        files = target_files(tgt, env)
    allow = {str(a) for a in det.get("allow") or []}
    want_match = det["expect"] == "match"
    hits = []
    for path in files:
        text = _read(path)
        if text is None:
            continue
        region, offset = _scope_text(text, det.get("scope", "all"))
        found = [m for m in pattern.finditer(region) if m.group(0) not in allow]
        if bool(found) != want_match:
            continue
        hit = Hit(_rel(path, env.project_root))
        if found:
            start = found[0].start()
            hit.line = region.count("\n", 0, start) + 1 + offset
            begin = region.rfind("\n", 0, start) + 1
            end = region.find("\n", start)
            hit.quoted = clip(region[begin:len(region) if end < 0 else end])
        hits.append(hit)
    return hits


# -------------------------------------------------------------- path-exists

def _glob_matches(det: dict, env: Env, tgt: dict) -> list:
    """Files of the glob; a glob without ``/`` is relative to the target directory."""
    pattern = render(det["glob"], env.bindings)
    base = env.project_root
    if "/" not in pattern:
        art_dir = get_path(env.caps, tgt["artifact"], None)
        if isinstance(art_dir, str) and art_dir:
            base = env.project_root / art_dir
    skip = det.get("exclude_glob")
    return [p for p in sorted(base.glob(pattern))
            if p.is_file() and not (skip and fnmatch.fnmatch(p.name, skip))]


def detect_path_exists(det: dict, env: Env, tgt: dict) -> list:
    want_present = det["expect"] == "present"
    if "glob" not in det:
        full = env.project_root / render(det.get("path") or det["path_template"], env.bindings)
        return [Hit(_rel(full, env.project_root))] if full.exists() == want_present else []
    matches = _glob_matches(det, env, tgt)
    if "require_suffix_key" in det:
        suffix = get_path(env.caps, det["require_suffix_key"], None)
        if not isinstance(suffix, str) or not suffix:
            return []
        return [Hit(_rel(p, env.project_root)) for p in matches if not p.name.endswith(suffix)]
    if "bind" in det:
        hits = []
        for path in matches:
            sub = replace(env, bindings={**env.bindings, det["bind"]: path.stem})
            for hit in detect(det["then"], sub, tgt):
                hit.bindings = {det["bind"]: path.stem, **hit.bindings}
                hits.append(hit)
        return hits
    if want_present:
        return [Hit(_rel(p, env.project_root)) for p in matches]
    return [] if matches else [Hit(render(det["glob"], env.bindings))]


# ------------------------------------------------------- yaml-key / toml-key

def _document_hits(doc, det: dict, env: Env, file: str, expected) -> list:
    hits = []
    for binds, value in iter_paths(doc, det["key"]):
        if compare(det["op"], value, expected):
            hits.append(Hit(file, bindings=binds))
    return hits


def detect_yaml_key(det: dict, env: Env, tgt: dict) -> list:
    expected = expected_value(det, env)
    if det.get("subject") == "capability":
        return _document_hits(env.caps, det, env, CAPABILITY_FILE_REL, expected)
    if det.get("frontmatter"):
        hits = []
        for path in target_files(tgt, env):
            text = _read(path)
            if text is not None:
                doc = parse_frontmatter_text(text)
                hits += _document_hits(doc, det, env, _rel(path, env.project_root), expected)
        return hits
    if tgt["artifact"] == "project_config" and not tgt.get("path"):
        return _document_hits(env.config, det, env, PROJECT_CONFIG_REL, expected)
    hits = []
    for path in target_files(tgt, env):
        try:
            doc = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (OSError, yaml.YAMLError):
            continue
        hits += _document_hits(doc if isinstance(doc, dict) else {}, det, env,
                               _rel(path, env.project_root), expected)
    return hits


def detect_toml_key(det: dict, env: Env, tgt: dict) -> list:
    expected = expected_value(det, env)
    hits = []
    files = target_files(tgt, env)
    if not files:
        raise DetectorUnavailable("target file is missing", notify=False)
    for path in files:
        text = _read(path)
        if text is None:
            continue
        try:
            doc = parse_toml(text)
        except TomlUnsupported as exc:
            raise DetectorUnavailable(f"TOML parser: {exc}") from exc
        value = get_path(doc, det["key"])
        # Interpretation: a missing key under "lt" counts as below the limit.
        if (value is MISSING and det["op"] == "lt") or compare(det["op"], value, expected):
            hits.append(Hit(_rel(path, env.project_root)))
    return hits


# -------------------------------------------------------------- json-schema

def detect_json_schema(det: dict, env: Env, tgt: dict) -> list:
    if "schema" in det:
        schema = det["schema"]
    else:
        try:
            schema = schema_from_capability_value(get_path(env.caps, det["schema_from_key"], None))
        except ValueError as exc:
            raise DetectorUnavailable(str(exc), notify=False) from exc
    hits = []
    for path in target_files(tgt, env):
        text = _read(path)
        if text is None:
            continue
        for error in validate_schema_subset(parse_frontmatter_text(text), schema):
            hits.append(Hit(_rel(path, env.project_root), quoted=clip(error)))
    return hits


# ------------------------------------------------------------------ command

def detect_command(det: dict, env: Env, tgt: dict) -> list:
    argv = list(det["argv"])
    if tuple(argv) not in COMMAND_ALLOWLIST or FORBIDDEN_ARGV & set(argv):
        raise DetectorUnavailable("argv is not on the command allowlist")
    if "--context-report" in argv and not env.sink_enabled:
        raise DetectorUnavailable(
            "writing command needs repo_containment.tmp-sink.enabled: true")
    script = Path(env.agent_meta_root) / "scripts" / "sync.py"
    cmd = [sys.executable, str(script), *argv, "--dry-run"]
    try:
        proc = subprocess.run(
            cmd, cwd=str(env.project_root), shell=False, stdin=subprocess.DEVNULL,
            capture_output=True, encoding="utf-8", errors="replace",
            env={**os.environ, "PYTHONDONTWRITEBYTECODE": "1"},
            timeout=det.get("timeout_s", DEFAULT_COMMAND_TIMEOUT_S))
    except (OSError, ValueError, subprocess.SubprocessError) as exc:
        raise DetectorUnavailable(f"command could not run: {type(exc).__name__}") from exc
    if proc.returncode == det["expect_exit"]:
        return []
    return [Hit(PROJECT_CONFIG_REL, quoted=f"exit {proc.returncode}, expected {det['expect_exit']}")]


# -------------------------------------------------------------- finding-ref

def _sync_log_entries(env: Env) -> list:
    """``(check, message)`` pairs of the sync.log snapshot (read once per run)."""
    if "sync_log" not in env.shared:
        text = _read(env.project_root / SYNC_LOG_REL) or ""
        entries = []
        for line in text.splitlines():
            match = _LOG_LINE.match(line)
            if match:
                severity = Severity.WARNING if match.group(1) == "WARN" else Severity.INFO
                entries.append((match.group(2), line[match.end(2):].strip(" :()"), severity))
        env.shared["sync_log"] = entries
    return env.shared["sync_log"]


def _env_hits(env: Env) -> list:
    import importlib.util

    if importlib.util.find_spec("jsonschema") is not None:
        return []
    return [Hit(PROJECT_CONFIG_REL, quoted="jsonschema not installed",
                severity=Severity.INFO, ref_check=CHECK_ENVIRONMENT)]


def _sink_hits(env: Env) -> list:
    """CHECK_TMP_SINK consumes the central resolver; it never re-reads the path.

    ``resolve_tmp_paths`` raises ``tmp-sink.invalid-path`` with the validator's
    reason text (AC-32), either as ``"'path' is invalid (<reason>); using …"``
    or ``"repo_containment.tmp-sink.path '<rel>': <reason>"``. The doctor
    message renders the bare reason, never the path context. Other resolver
    error codes belong to the validator and must not fire this check.
    """
    try:
        resolve_tmp_paths(env.project_root, env.config)
    except TmpSinkError as exc:
        if exc.code != "tmp-sink.invalid-path":
            return []
        match = re.search(r"\(([^()]*)\); using ", exc.message)
        reason = match.group(1) if match else (exc.message.rpartition(": ")[2] or exc.message)
        return [Hit(PROJECT_CONFIG_REL, quoted=clip(reason), bindings={"reason": reason},
                    severity=Severity.ERROR, ref_check=CHECK_TMP_SINK)]
    return []


_RUNNER_OWNED = {CHECK_ENVIRONMENT: _env_hits, CHECK_TMP_SINK: _sink_hits}


def resolve_check_function(source: str, check: str):
    """Return the IC-10 / IC-19 function behind a check id (convention name), else None."""
    module_name = _CHECK_MODULES.get(source)
    if module_name is None or "." not in check:
        return None
    module = importlib.import_module(module_name, __package__)
    return getattr(module, "check_" + check.split(".", 1)[1].replace("-", "_"), None)


def _scan_checks(source: str, check: str, env: Env) -> list:
    module = importlib.import_module(_CHECK_MODULES[source], __package__)
    func = resolve_check_function(source, check)
    if func is not None and not any(c in check for c in "*?["):
        funcs = [func]
    else:  # glob: run every IC-10 / IC-19 check of the module, the caller filters
        funcs = [getattr(module, n) for n in sorted(dir(module)) if n.startswith("check_")]
    raws = []
    for fn in funcs:
        raws += fn(env.project_root, list(env.providers), env.caps_map, env.active_set)
    return raws


def _raw_findings(det: dict, env: Env) -> list:
    """``(check, file, message, severity, bindings)`` rows of the referenced check."""
    source, check = det["source"], det["check"]
    if source == "doctor":
        fn = _RUNNER_OWNED.get(check)
        if fn is None:
            raise DetectorUnavailable("unknown runner-owned check")
        return [(h.ref_check, h.file, h.quoted, h.severity, h.bindings) for h in fn(env)]
    if source == "sync-log":
        return [(c, SYNC_LOG_REL, msg, sev, {})
                for c, msg, sev in _sync_log_entries(env) if fnmatch.fnmatch(c, check)]
    if source == "hooks":
        from .consistency import hook_drift

        raws = hook_drift.check_hook_enablement_consistency(
            env.project_root, env.agent_meta_root, env.config, env.provider_config)
    elif source in _CHECK_MODULES:
        if resolve_check_function(source, check) is None and not any(c in check for c in "*?["):
            raise DetectorUnavailable("check producer not available yet", notify=False)
        raws = _scan_checks(source, check, env)
    else:
        raise DetectorUnavailable(f"finding source {source!r} is not supported", notify=False)
    return [(r.check, r.file, r.message, r.severity, {}) for r in raws
            if fnmatch.fnmatch(r.check, check)]


def detect_finding_ref(det: dict, env: Env, tgt: dict) -> list:
    pattern = re.compile(det["match"]) if det.get("match") else None
    hits = []
    try:
        rows = _raw_findings(det, env)
    except DetectorUnavailable:
        raise
    except Exception as exc:  # fail-soft: a broken referenced check never crashes the run
        raise DetectorUnavailable(f"referenced check raised {type(exc).__name__}") from exc
    for check, file, message, severity, bindings in rows:
        if pattern and not pattern.search(message):
            continue
        hits.append(Hit(file, quoted=clip(message), bindings=bindings, severity=severity,
                        ref_check=check, provider=_message_provider(det, message, env)))
    return hits


def _message_provider(det: dict, message: str, env: Env) -> str:
    """Provider named by the ``"<provider>: ..."`` prefix of a context-budget message.

    Only a name from the active provider set is accepted (never free text), so
    ``--provider`` filtering and the per-provider ``provider`` field work for
    provider-independent ``finding-ref`` entries.
    """
    if det["source"] != "context-budget":
        return ""
    name = message.split(": ", 1)[0]
    return name if name in env.providers else ""


# ---------------------------------------------------- variable-unreferenced

def _framework_template_text(env: Env) -> str:
    if "templates" not in env.shared:
        parts = []
        for sub in _TEMPLATE_ROOTS:
            base = Path(env.agent_meta_root) / sub
            for path in sorted(base.rglob("*")) if base.is_dir() else []:
                if path.is_file():
                    parts.append(_read(path) or "")
        env.shared["templates"] = "\n".join(parts)
    return env.shared["templates"]


def _runtime_reader_keys(env: Env) -> set:
    """Reader keys from the IC-35 runtime registry (cached on ``env.shared``).

    Fail-soft like the other detectors: a missing/unreadable/malformed registry
    yields an empty set, so the doctor behaves as before and never crashes. Only
    ``agent_meta_root`` is read (source of truth, same as IC-21).
    """
    if "runtime_reader_keys" not in env.shared:
        keys: set = set()
        path = Path(env.agent_meta_root) / RUNTIME_READERS_REL
        try:
            data = yaml.safe_load(path.read_text(encoding="utf-8"))
            for entry in (data or {}).get("readers", []) or []:
                key = entry.get("key") if isinstance(entry, dict) else None
                if isinstance(key, str) and key:
                    keys.add(key)
        except Exception:
            keys = set()
        env.shared["runtime_reader_keys"] = keys
    return env.shared["runtime_reader_keys"]


def _runtime_reader_covers(reader_keys: set, key: str) -> bool:
    """True when a registry reader key covers ``key`` (dotted; prefix for subkeys).

    Both the bare ``<KEY>`` and the ``variables.<KEY>`` form are accepted, so a
    project-config top-level key like ``admin-ui`` counts as consumed just as a
    ``variables.X`` reader covers the variable ``X``.
    """
    for reader_key in reader_keys:
        if reader_key in (key, "variables." + key):
            return True
        if reader_key.startswith(key + ".") or reader_key.startswith("variables." + key + "."):
            return True
    return False


def detect_variable_unreferenced(det: dict, env: Env, tgt: dict) -> list:
    variables = env.config.get("variables")
    if not isinstance(variables, dict):
        return []
    keys = sorted(variables, key=str) if det["key"] == "*" else [det["key"]]
    own_seeds = env.shared.get("own_variable_seeds", set())
    reader_keys = _runtime_reader_keys(env)
    text = _framework_template_text(env)
    hits = []
    for key in keys:
        value = variables.get(key)
        if value is None or (det["key"] == "*" and key in own_seeds):
            continue
        used = re.search(r"\{\{[^}]*\b" + re.escape(str(key)) + r"\b[^}]*\}\}", text)
        if not used and not _runtime_reader_covers(reader_keys, str(key)):
            hits.append(Hit(PROJECT_CONFIG_REL,
                            bindings={"key": str(key), "length": len(str(value))}))
    return hits


# ----------------------------------------------------------------- dispatch

DETECTORS = {
    "file-size": detect_file_size,
    "regex": detect_regex,
    "path-exists": detect_path_exists,
    "yaml-key": detect_yaml_key,
    "toml-key": detect_toml_key,
    "json-schema": detect_json_schema,
    "command": detect_command,
    "finding-ref": detect_finding_ref,
    "variable-unreferenced": detect_variable_unreferenced,
}


def detect(det: dict, env: Env, tgt: dict) -> list:
    """Run one detector (or ``any_of``) and return its hits."""
    if "any_of" in det:
        for sub in det["any_of"]:
            if detect(sub, env, tgt):
                return []
        return [Hit(render(tgt.get("path"), env.bindings))]
    return DETECTORS[det["kind"]](det, env, tgt)
