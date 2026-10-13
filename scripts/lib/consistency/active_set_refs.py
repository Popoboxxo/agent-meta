"""Active-set reference checks (IC-19, Task 0b.3).

Pure functions over a synced ``project_root``; all share the IC-10 signature
``(project_root, active_providers, capabilities, active_set) -> list[Finding]``.
Phase 0: WARN/INFO only.

Dispatch patterns are derived from ``config/delegation-syntax.yaml`` (per active
provider, nothing hardcoded) plus the shared ``dispatch_phrases`` of
``config/active-set-references.yaml``. When no pattern can be derived for a
provider the check reports ``active-set.dispatch-pattern-missing`` and skips
that provider - never silently.
"""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .report import Finding, Severity
from ..io import load_yaml_file

CHECK_DANGLING_DISPATCH = "active-set.dangling-dispatch"
CHECK_DANGLING_MENTION = "active-set.dangling-mention"
CHECK_GATE_DROPPED = "active-set.gate-dropped"
CHECK_UNKNOWN_ROLE = "active-set.unknown-role"
CHECK_UNRESOLVED = "active-set.unresolved-placeholder"
CHECK_PATTERN_MISSING = "active-set.dispatch-pattern-missing"

_AGENT_META_ROOT = Path(__file__).resolve().parents[3]
_PROJECT_CFG = ".meta-config/project.yaml"
_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")
_ARTICLE = r"(?:(?:an|zu|to)\s+)?(?:(?:den|dem|einen|der|die|das|the)\s+)?"
_FMT_TOKEN_RE = re.compile(r"\{agent\}|\{task\}|\{\w+\}")


# --- config / file helpers -------------------------------------------------

def _refs() -> dict:
    return load_yaml_file(_AGENT_META_ROOT / "config" / "active-set-references.yaml") or {}


def _provider_cfg(provider: str) -> dict:
    data = load_yaml_file(_AGENT_META_ROOT / "config" / "ai-providers.yaml") or {}
    return ((data.get("providers") or {}).get(provider)) or {}


def _dispatch_formats(root: Path, provider: str) -> list:
    """Format strings with an ``{agent}`` slot for ``provider`` (empty if none)."""
    data = load_yaml_file(Path(root) / "config" / "delegation-syntax.yaml") or {}
    entry = ((data.get("delegation_syntax") or {}).get(provider)) or {}
    notation = entry.get("pipeline_notation") or {}
    return sorted({v for v in notation.values()
                   if isinstance(v, str) and "{agent}" in v})


def _scan_files(project_root: Path, provider: str) -> list:
    cfg = _provider_cfg(provider)
    ext = str(cfg.get("agent_ext") or ".md")
    files = []
    for key in ("agents_dir", "rules_dir"):
        base = cfg.get(key)
        if isinstance(base, str) and (project_root / base).is_dir():
            files += [p for p in sorted((project_root / base).rglob("*"))
                      if p.is_file() and p.suffix in {".md", ext}]
    ctx = cfg.get("context_file")
    if isinstance(ctx, str) and (project_root / ctx).is_file():
        files.append(project_root / ctx)
    return files


def _read_lines(path: Path) -> list:
    try:
        return path.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError):
        return []


def _rel(path: Path, project_root: Path) -> str:
    return path.relative_to(project_root).as_posix()


def _role_alt(roles) -> str:
    return "|".join(re.escape(r) for r in sorted(roles, key=len, reverse=True))


def _fmt_pattern(fmt: str, alt: str) -> Optional[re.Pattern]:
    head, _, tail = fmt.partition("{agent}")
    head = head.strip()
    if len(head) < 2:
        return None
    suffix = _FMT_TOKEN_RE.split(tail, maxsplit=1)[0].strip()
    # Without a literal suffix the role token must end at a word boundary.
    end = re.escape(suffix) if suffix else r"(?![\w-])"
    return re.compile(re.escape(head) + "(?P<r>" + alt + ")" + end)


def _phrase_patterns(alt: str) -> list:
    phrases = _refs().get("dispatch_phrases") or {}
    out = []
    for lang in ("en", "de"):
        for phrase in phrases.get(lang) or []:
            try:
                out.append(re.compile(
                    "(?:" + phrase + r")\s*" + _ARTICLE + r"[`@\"']?(?P<r>" + alt
                    + r")(?![\w-])", re.IGNORECASE))
            except re.error:
                continue
    # Arrow routes ("... -> `role`") are imperative hand-offs as well.
    out.append(re.compile(r"(?:\u2192|->)\s*[`@\"']?(?P<r>" + alt + r")(?![\w-])"))
    return out


def _dangling_roles(active_set) -> frozenset:
    return frozenset(active_set.known_roles) - frozenset(active_set.roles)


def _dedupe(findings: list) -> list:
    seen, out = set(), []
    for f in findings:
        key = (f.check, f.file, f.message)
        if key not in seen:
            seen.add(key)
            out.append(f)
    return out


def _line_hits(lines: list, dispatch_pats: list, dangling: frozenset) -> list:
    """Per line: (lineno, dispatch_roles, mention_roles)."""
    alt = _role_alt(dangling)
    token = re.compile(r"(?<![\w-])(?P<r>" + alt + r")(?![\w-])")
    row_token = re.compile(r"`(?P<r>" + alt + r")`")
    result = []
    for lineno, line in enumerate(lines, 1):
        dispatch = set()
        for pat in dispatch_pats:
            dispatch |= {m.group("r") for m in pat.finditer(line)}
        if line.lstrip().startswith("|"):
            dispatch |= {m.group("r") for m in row_token.finditer(line)}
        mentions = {m.group("r") for m in token.finditer(line)} - dispatch
        if dispatch or mentions:
            result.append((lineno, dispatch, mentions))
    return result


def _collect(project_root, providers, active_set, kind: str) -> list:
    """Shared scanner for dangling-dispatch (``dispatch``) / -mention (``mention``)."""
    dangling = _dangling_roles(active_set)
    findings = []
    if not dangling:
        return findings
    alt = _role_alt(dangling)
    mention_allow = [str(p) for p in (_refs().get("mention_allow") or [])]
    for provider in providers:
        pats = [p for p in (_fmt_pattern(f, alt)
                            for f in _dispatch_formats(_AGENT_META_ROOT, provider)) if p]
        if not pats:
            findings.append(Finding(
                Severity.WARNING, CHECK_PATTERN_MISSING, "config/delegation-syntax.yaml",
                f"no dispatch pattern derivable for provider '{provider}'; "
                "active-set dispatch/mention checks skipped for it",
                "Add pipeline_notation task_fmt/mention_fmt with an {agent} slot"))
            continue
        pats += _phrase_patterns(alt)
        for path in _scan_files(project_root, provider):
            rel = _rel(path, project_root)
            if kind == "mention" and any(fnmatch.fnmatch(rel, g) for g in mention_allow):
                continue
            per_role: dict = {}
            for lineno, dispatch, mentions in _line_hits(_read_lines(path), pats, dangling):
                for role in (dispatch if kind == "dispatch" else mentions):
                    per_role.setdefault(role, []).append(lineno)
            for role, linenos in sorted(per_role.items()):
                if kind == "dispatch":
                    findings.append(Finding(
                        Severity.WARNING, CHECK_DANGLING_DISPATCH, rel,
                        f"dispatch to inactive role '{role}' ({len(linenos)}x, "
                        f"first line {linenos[0]})",
                        "Activate the role or filter the route for this active set"))
                else:
                    findings.append(Finding(
                        Severity.INFO, CHECK_DANGLING_MENTION, rel,
                        f"mention of inactive role '{role}' ({len(linenos)}x, "
                        f"first line {linenos[0]})"))
    return _dedupe(findings)


# --- public checks (IC-10 signature) ---------------------------------------

def check_dangling_dispatch(project_root: Path, active_providers: Sequence[str],
                            capabilities: Mapping[str, Mapping], active_set) -> list:
    return _collect(Path(project_root), active_providers, active_set, "dispatch")


def check_dangling_mention(project_root: Path, active_providers: Sequence[str],
                           capabilities: Mapping[str, Mapping], active_set) -> list:
    return _collect(Path(project_root), active_providers, active_set, "mention")


def check_gate_dropped(project_root: Path, active_providers: Sequence[str],
                       capabilities: Mapping[str, Mapping], active_set) -> list:
    return [Finding(
        Severity.WARNING, CHECK_GATE_DROPPED, _PROJECT_CFG,
        f"'{d.role}' dropped by group '{d.group}' ({d.reason})",
        "Add the missing roles to the roles allowlist or enable the group")
        for d in active_set.gate_dropped]


def check_unknown_role(project_root: Path, active_providers: Sequence[str],
                       capabilities: Mapping[str, Mapping], active_set) -> list:
    cfg = load_yaml_file(Path(project_root) / _PROJECT_CFG) or {}
    allowlist = cfg.get("roles") if isinstance(cfg, dict) else None
    if not isinstance(allowlist, list):
        return []
    return [Finding(
        Severity.WARNING, CHECK_UNKNOWN_ROLE, _PROJECT_CFG,
        f"allowlist entry '{role}' is not defined in role-defaults",
        "Remove or correct the entry")
        for role in sorted({r for r in allowlist if isinstance(r, str)}
                           - set(active_set.known_roles))]


def check_unresolved_placeholder(project_root: Path, active_providers: Sequence[str],
                                 capabilities: Mapping[str, Mapping], active_set) -> list:
    project_root = Path(project_root)
    allow = {str(p) for p in (_refs().get("placeholder_allow") or [])}
    findings = []
    for provider in active_providers:
        for path in _scan_files(project_root, provider):
            counts: dict = {}
            for line in _read_lines(path):
                for ph in _PLACEHOLDER_RE.findall(line):
                    if ph not in allow:
                        counts[ph] = counts.get(ph, 0) + 1
            for ph, n in sorted(counts.items()):
                findings.append(Finding(
                    Severity.WARNING, CHECK_UNRESOLVED, _rel(path, project_root),
                    f"unresolved placeholder {ph} ({n}x)",
                    "Set the variable in project.yaml or add it to placeholder_allow"))
    return _dedupe(findings)
