"""Active-set reference checks (IC-19, Task 0b.3).

Pure functions over a synced ``project_root``; all share the IC-10 signature
``(project_root, active_providers, capabilities, active_set) -> list[Finding]``.
Phase 1 (Task 1.20, AC-49): ``active-set.dangling-dispatch`` is ERROR; the other
checks stay WARN/INFO. The scan covers per provider the agents, the rules
(``rules_dir``, or the default rules dir for providers with ``has_rules`` but
no ``rules_dir``), the commands (``commands_dir``), the pipeline-details files
and the context file.

Dispatch patterns are derived from ``config/delegation-syntax.yaml`` (per active
provider, nothing hardcoded) plus the shared ``dispatch_phrases`` of
``config/active-set-references.yaml``. When no pattern can be derived for a
provider the check reports ``active-set.dispatch-pattern-missing`` and skips
that provider - never silently.

Heuristic decisions (spec IC-19 names only pipeline formats, dispatch phrases and
dispatch-table rows):
- No generic arrow rule (``-> role``): arrows also appear in boundary lists
  ("Boundary: ... -> role") and fallback flows, which are references, not
  dispatches; those stay ``dangling-mention`` (INFO).
- Table rows count as dispatch only for roles in cells whose column header names
  a routing target (route/agent/role/target/tier/...); prose cells ("When",
  "Notes") of the same row are mentions.
- Pipeline formats with extra slots in the head (``FANOUT({count}, {agent})``)
  are matched with a wildcard for that slot; ``conditional_*`` formats name the
  evaluating agent, not a dispatch target, and are excluded.
"""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .report import Finding, Severity
from ..io import load_yaml_file
from ..pipelines import resolve_pipeline_details_dir
from ..rule_index import read_managed_index
from ..rules import CLAUDE_RULES_DIR

# Default managed-file index name of rules/commands directories (rule_index).
MANAGED_INDEX = ".agent-meta-managed"

CHECK_DANGLING_DISPATCH = "active-set.dangling-dispatch"
CHECK_DANGLING_MENTION = "active-set.dangling-mention"
CHECK_GATE_DROPPED = "active-set.gate-dropped"
CHECK_UNKNOWN_ROLE = "active-set.unknown-role"
CHECK_UNRESOLVED = "active-set.unresolved-placeholder"
CHECK_PATTERN_MISSING = "active-set.dispatch-pattern-missing"
CHECK_KEYWORD_OVERLAP = "routing.keyword-overlap"
CHECK_INVALID_PHRASE = "active-set.invalid-dispatch-phrase"

_AGENT_META_ROOT = Path(__file__).resolve().parents[3]
_PROJECT_CFG = ".meta-config/project.yaml"
_PLACEHOLDER_RE = re.compile(r"\{\{[A-Z][A-Z0-9_]*\}\}")
_ARTICLE = r"(?:(?:an|zu|to)\s+)?(?:(?:den|dem|einen|der|die|das|the)\s+)?"
_FMT_TOKEN_RE = re.compile(r"\{agent\}|\{task\}|\{\w+\}")
_SLOT_RE = re.compile(r"\{\w+\}")
_DISPATCH_HEADER_RE = re.compile(
    r"route|routing|agents?\b|roles?\b|rolle|target|ziel|delegat|dispatch|tier|assign",
    re.IGNORECASE)
_NON_DISPATCH_KEYS = ("conditional",)


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
    return sorted({v for k, v in notation.items()
                   if isinstance(v, str) and "{agent}" in v
                   and not str(k).startswith(_NON_DISPATCH_KEYS)})


def _scan_dirs(cfg: dict, provider: str) -> list:
    """``(dir, managed_index)`` of ``provider``'s generated directories (config keys only).

    ``managed_index`` names the sync's managed-file index in that directory;
    when it exists only the listed files are scanned, so unmanaged user files
    (own commands/rules) never produce findings. ``None`` = scan every file.
    """
    dirs = [(cfg.get("agents_dir"), None)]
    # Providers with native rules but without rules_dir write the default rules dir
    # (same fallback as rules.sync_rules).
    rules_dir = cfg.get("rules_dir") or (CLAUDE_RULES_DIR if cfg.get("has_rules") else None)
    dirs.append((rules_dir, MANAGED_INDEX))
    if cfg.get("has_commands"):
        dirs.append((cfg.get("commands_dir"), cfg.get("commands_managed_index", MANAGED_INDEX)))
    if isinstance(cfg.get("agents_dir"), str):
        dirs.append((resolve_pipeline_details_dir(cfg, provider), None))
    return [(d, idx) for d, idx in dirs if isinstance(d, str)]


def _managed_names(root: Path, index: str):
    """Union of the sync's managed indexes in ``root`` (``index`` plus the
    ``.agent-meta-managed*`` siblings written by MCP/external-tool rules);
    ``None`` when ``root`` has no index at all."""
    indexes = {root / index} | set(root.glob(MANAGED_INDEX + "*"))
    present = [p for p in sorted(indexes) if p.is_file()]
    if not present:
        return None
    names: set = set()
    for path in present:
        names |= read_managed_index(path)
    return names


def _scan_files(project_root: Path, provider: str) -> list:
    cfg = _provider_cfg(provider)
    # Final suffix only: a compound extension (".agent.md") ends in ".md".
    suffixes = {Path("x" + str(ext)).suffix
                for ext in (".md", cfg.get("agent_ext") or ".md", cfg.get("commands_ext") or ".md")}
    files: list = []
    seen: set = set()
    for base, index in _scan_dirs(cfg, provider):
        root = project_root / base
        if not root.is_dir():
            continue
        managed = _managed_names(root, index) if index else None
        for p in sorted(root.rglob("*")):
            if not p.is_file() or p.suffix not in suffixes or p in seen:
                continue
            if managed is not None and p.relative_to(root).as_posix() not in managed:
                continue
            seen.add(p)
            files.append(p)
    ctx = cfg.get("context_file")
    if isinstance(ctx, str) and (project_root / ctx).is_file() and project_root / ctx not in seen:
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
    if not head:
        return None
    # Extra slots in the head ({count}, {index}) match any non-space run.
    head_rx = r"\s*".join(
        r"[^\s,]+" if _SLOT_RE.fullmatch(part) else re.escape(part)
        for part in re.split(r"(\{\w+\})", head.replace(" ", "")) if part)
    suffix = _FMT_TOKEN_RE.split(tail, maxsplit=1)[0].strip()
    # Without a literal suffix the role token must end at a word boundary.
    end = re.escape(suffix) if suffix else r"(?![\w-])"
    return re.compile(r"(?<![\w.])" + head_rx + r"\s*(?P<r>" + alt + ")" + end)


def _phrase_patterns(alt: str) -> tuple:
    """Return ``(patterns, invalid)``; ``invalid`` lists ``(phrase, error)`` pairs."""
    phrases = _refs().get("dispatch_phrases") or {}
    out, invalid = [], []
    for lang in ("en", "de"):
        for phrase in phrases.get(lang) or []:
            try:
                out.append(re.compile(
                    "(?:" + phrase + r")\s*" + _ARTICLE + r"[`@\"']?(?P<r>" + alt
                    + r")(?![\w-])", re.IGNORECASE))
            except re.error as exc:
                invalid.append((str(phrase), str(exc)))
    return out, invalid


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
    dispatch_cols: set = set()
    in_table = False
    for lineno, line in enumerate(lines, 1):
        dispatch = set()
        for pat in dispatch_pats:
            dispatch |= {m.group("r") for m in pat.finditer(line)}
        if line.lstrip().startswith("|"):
            cells = line.strip().strip("|").split("|")
            if not in_table:  # first row of a table = header
                dispatch_cols = {i for i, c in enumerate(cells)
                                 if _DISPATCH_HEADER_RE.search(c)}
                in_table = True
            else:
                for i in dispatch_cols & set(range(len(cells))):
                    dispatch |= {m.group("r") for m in row_token.finditer(cells[i])}
        else:
            in_table = False
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
        phrase_pats, invalid = _phrase_patterns(alt)
        pats += phrase_pats
        if kind == "dispatch":
            findings += [Finding(
                Severity.WARNING, CHECK_INVALID_PHRASE, "config/active-set-references.yaml",
                f"invalid dispatch_phrases regex {phrase!r}: {err}",
                "Fix the regex; the phrase is ignored by the dispatch check")
                for phrase, err in invalid]
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
                        Severity.ERROR, CHECK_DANGLING_DISPATCH, rel,
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


def check_keyword_overlap(project_root: Path, active_providers: Sequence[str],
                          capabilities: Mapping[str, Mapping], active_set) -> list:
    """IC-29 (INFO): keywords shared by >= 2 roles of ``ActiveSet.routable``."""
    from ..roles import load_roles_config

    roles = load_roles_config(_AGENT_META_ROOT).get("roles") or {}
    owners: dict = {}
    for role in sorted(frozenset(active_set.routable)):
        patterns = (roles.get(role) or {}).get("routing_patterns") or {}
        for kw in patterns.get("keywords") or []:
            owners.setdefault(str(kw).strip().casefold(), set()).add(role)
    return [Finding(
        Severity.INFO, CHECK_KEYWORD_OVERLAP, "config/role-defaults.yaml",
        f"keyword '{tok}' is shared by routable roles: {', '.join(sorted(rs))}",
        "Sharpen the keyword or keep it covered by collision eval cases")
        for tok, rs in sorted(owners.items()) if len(rs) >= 2]
