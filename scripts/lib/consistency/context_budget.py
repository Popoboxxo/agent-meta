"""Context budget and reachability checks (IC-10, SPEC-CONTEXT-PROFILES-2026-10-11).

Pure functions over the files of a synced project -- the sync end, the doctor
and tests call the same functions (ADR-6). Every check has the signature::

    check_<name>(project_root, active_providers, capabilities, active_set)
        -> list[Finding]

``capabilities[provider]`` is the merged provider mapping (ai-providers.yaml
path keys plus provider-capabilities.yaml cap/channel keys, see
``context_report.merge_provider_mappings``). All provider differences are
expressed through those keys (``context_file``, ``rules_dir``, ``skills_dir``,
``rules_read_channels``, ``skills_discovery_dirs``, ``context_*_cap_*``) --
never through provider names.

Severity is centralised: ``SPEC_SEVERITY`` holds the level the spec prescribes
per check, ``PHASE0_SEVERITY`` the level actually emitted today (everything
WARNING, no exit-code change). ``_warn`` reads ``PHASE0_SEVERITY``; promoting a
check to its spec level (e.g. ``over-hard-cap`` and ``marker-in-rule`` from
Phase 1) is a one-line change in that table.

Not part of this module (task 0b.2): ``context.token-report`` (0a report),
``context.declared-surface-empty`` (IC-33) and ``context.legacy-artifact-present``.
Known gap, Phase 1: the Copilot soft cap is per instruction file; it is only
checked here against the entry file.

``active_set`` is part of the shared signature; none of the checks here
depends on the role set (rules and skills are not roles), so it is unused.
"""
from __future__ import annotations

import fnmatch
import re
from pathlib import Path
from typing import Mapping, Optional, Sequence

from .report import Finding, Severity

_ANCHORS_YAML = "config/context-anchors.yaml"
# scripts/lib/consistency/context_budget.py -> framework root (repo or .agent-meta)
_FRAMEWORK_ROOT = Path(__file__).resolve().parents[3]

CHANNEL_NATIVE = "native-rules-dir"
CHANNEL_PATH_SCOPED = "path-scoped"
CHANNEL_SKILLS = "skills"
_FILE_CHANNELS = (CHANNEL_NATIVE, CHANNEL_PATH_SCOPED)

# Level the spec prescribes (IC-10) vs. the level emitted in Phase 0.
SPEC_SEVERITY = {
    "context.over-hard-cap": Severity.ERROR,
    "context.over-soft-cap": Severity.WARNING,
    "context.dangling-pointer": Severity.ERROR,   # WARN in Phase 0, ERROR from Phase 1
    "context.rule-unreachable": Severity.ERROR,   # WARN in Phase 0, ERROR from Phase 1
    "context.unread-channel": Severity.WARNING,
    "context-profile.marker-in-rule": Severity.ERROR,
}
PHASE0_SEVERITY = {check: Severity.WARNING for check in SPEC_SEVERITY}

COMPACT_MARKER = "CONTEXT_PROFILE_COMPACT"
# Row of a lazy-skill table: "| skill-name | description |" below a "| Skill |" header.
_TABLE_HEADER_RE = re.compile(r"^\|\s*Skill\s*\|", re.IGNORECASE)
_TABLE_ROW_RE = re.compile(r"^\|\s*([A-Za-z0-9][A-Za-z0-9_.-]*)\s*\|")
_TABLE_SEPARATOR_RE = re.compile(r"^\|[\s:|-]+\|?\s*$")
_LAZY_POINTER_MARKER = "Übrige Regeln (Lazy-Load)"
_FRONTMATTER_RE = re.compile(r"\A---\r?\n.*?\r?\n---\r?\n", re.DOTALL)


# ---------------------------------------------------------------------------
# helpers
# ---------------------------------------------------------------------------

def _warn(check: str, file: str, message: str, suggestion: str = "") -> Finding:
    return Finding(PHASE0_SEVERITY[check], check, file, message, suggestion)


def _read_text(path: Path) -> Optional[str]:
    try:
        return path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None


def _load_anchor_list(key: str) -> list:
    """Return ``context-anchors.yaml: <key>`` (a list), ``[]`` if absent/malformed."""
    try:
        import yaml
        data = yaml.safe_load((_FRAMEWORK_ROOT / _ANCHORS_YAML).read_text(encoding="utf-8"))
    except Exception:  # missing file, missing PyYAML or parse error -> no exemptions
        return []
    value = data.get(key) if isinstance(data, dict) else None
    return list(value) if isinstance(value, list) else []


def _intentional_unread() -> list:
    """Globs of ``intentional_unread``; entries are ``str`` or ``{glob, reason}``."""
    globs = []
    for entry in _load_anchor_list("intentional_unread"):
        glob = entry.get("glob") if isinstance(entry, dict) else entry
        if isinstance(glob, str) and glob:
            globs.append(glob)
    return globs


def _rel(path: Path, project_root: Path) -> str:
    try:
        return path.relative_to(project_root).as_posix()
    except ValueError:
        return path.as_posix()


def _rule_files(project_root: Path, caps: Mapping) -> list:
    """Generated rule files of a provider (``rules_dir/*.md``), sorted."""
    rules_dir = caps.get("rules_dir")
    if not caps.get("has_rules") or not rules_dir:
        return []
    directory = project_root / rules_dir
    if not directory.is_dir():
        return []
    return sorted(p for p in directory.iterdir() if p.is_file() and p.suffix == ".md")


def _skill_dirs(caps: Mapping) -> list:
    """Directories where a provider discovers skills: ``skills_dir`` + discovery dirs."""
    dirs = []
    own = caps.get("skills_dir")
    if isinstance(own, str) and own:
        dirs.append(own)
    for extra in caps.get("skills_discovery_dirs") or []:
        if isinstance(extra, str) and extra and extra not in dirs:
            dirs.append(extra)
    return dirs


def _has_any_skill(project_root: Path, directory: str) -> bool:
    base = project_root / directory
    return base.is_dir() and any((child / "SKILL.md").is_file() for child in base.iterdir())


def _normalize_heading(line: str) -> str:
    return line.strip().lstrip("#").strip()


def _first_heading(text: str) -> str:
    """First markdown heading line of a rule body (frontmatter stripped), else first line."""
    body = _FRONTMATTER_RE.sub("", text, count=1)
    first_non_empty = ""
    for line in body.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith("#"):
            return stripped
        first_non_empty = first_non_empty or stripped
    return first_non_empty


def _body_probe(text: str) -> str:
    """Second non-empty body line (frontmatter stripped); ``""`` for one-line rules."""
    lines = [ln.strip() for ln in _FRONTMATTER_RE.sub("", text, count=1).splitlines() if ln.strip()]
    return lines[1] if len(lines) > 1 else ""


def _pointer_artifacts(project_root: Path, caps: Mapping) -> list:
    """Generated artifacts that may carry skill pointers: entry file + rule files."""
    artifacts = []
    context_file = caps.get("context_file")
    if context_file:
        artifacts.append(project_root / context_file)
    artifacts.extend(_rule_files(project_root, caps))
    return [p for p in artifacts if p.is_file()]


def _lazy_table_skills(text: str) -> list:
    """Skill names listed in lazy-skill tables (``| Skill | Wann |``) of *text*."""
    skills: list = []
    in_table = False
    for line in text.splitlines():
        if _TABLE_HEADER_RE.match(line):
            in_table = True
            continue
        if not in_table:
            continue
        if _TABLE_SEPARATOR_RE.match(line):
            continue
        row = _TABLE_ROW_RE.match(line)
        if row:
            skills.append(row.group(1))
        else:
            in_table = False
    return skills


def _int_cap(caps: Mapping, key: str) -> Optional[int]:
    value = caps.get(key)
    return value if isinstance(value, int) and not isinstance(value, bool) else None


# ---------------------------------------------------------------------------
# context.over-hard-cap / context.over-soft-cap
# ---------------------------------------------------------------------------

def check_over_hard_cap(
    project_root: Path,
    active_providers: Sequence[str],
    capabilities: Mapping[str, Mapping],
    active_set,
) -> list:
    """``context.over-hard-cap``: entry file >= ``context_hard_cap_bytes`` (WARN in Phase 0; spec: ERROR)."""
    from ..context_report import measure_artifacts

    root = Path(project_root)
    findings = []
    report = measure_artifacts(root, active_providers, capabilities)
    for provider in active_providers:
        stat = (report.get(provider) or {}).get("entry-file")
        if not stat or stat.get("cap_kind") != "hard-bytes":
            continue
        if stat["bytes"] >= stat["cap"]:
            caps = capabilities.get(provider) or {}
            findings.append(_warn(
                "context.over-hard-cap", str(caps.get("context_file", "")),
                f"{provider}: entry file ({stat['bytes']} bytes) exceeds hard cap ({stat['cap']} bytes)",
                "shrink the entry file (profile compact, move content into lazy skills)"))
    return findings


def check_over_soft_cap(
    project_root: Path,
    active_providers: Sequence[str],
    capabilities: Mapping[str, Mapping],
    active_set,
) -> list:
    """``context.over-soft-cap``: entry file above ``context_soft_cap_{bytes,chars,lines}`` (WARN)."""
    from ..context_report import measure_artifacts

    root = Path(project_root)
    findings = []
    report = measure_artifacts(root, active_providers, capabilities)
    for provider in active_providers:
        stat = (report.get(provider) or {}).get("entry-file")
        if not stat:
            continue
        caps = capabilities.get(provider) or {}
        context_file = str(caps.get("context_file", ""))
        measured = {"bytes": stat["bytes"], "lines": stat["lines"]}
        for key, unit in (("context_soft_cap_bytes", "bytes"),
                          ("context_soft_cap_chars", "chars"),
                          ("context_soft_cap_lines", "lines")):
            cap = _int_cap(caps, key)
            if cap is None:
                continue
            if unit == "chars":
                # chars <= bytes: only read the file when bytes already exceed the cap
                if stat["bytes"] <= cap:
                    continue
                text = _read_text(root / context_file)
                value = len(text) if text is not None else stat["bytes"]
            else:
                value = measured[unit]
            if value > cap:
                findings.append(_warn(
                    "context.over-soft-cap", context_file,
                    f"{provider}: entry file has {value} {unit}, soft cap is {cap} {unit}",
                    "shrink the entry file or move reference content into lazy skills"))
    return findings


# ---------------------------------------------------------------------------
# context.dangling-pointer
# ---------------------------------------------------------------------------

def check_dangling_pointer(
    project_root: Path,
    active_providers: Sequence[str],
    capabilities: Mapping[str, Mapping],
    active_set,
) -> list:
    """``context.dangling-pointer``: a skill named in a generated artifact does not exist (WARN; spec: ERROR from Phase 1).

    Two pointer kinds, both resolved against the provider's skill directories
    (``skills_dir`` + ``skills_discovery_dirs``):

    * every skill listed in a lazy-skill table (``| Skill | Wann |``) must have
      ``<dir>/<skill>/SKILL.md`` in one of them;
    * the "Übrige Regeln (Lazy-Load)" pointer promises rule skills; a provider
      whose skill directories hold no ``SKILL.md`` at all breaks that promise.
    """
    root = Path(project_root)
    findings = []
    for provider in active_providers:
        caps = capabilities.get(provider) or {}
        skill_dirs = _skill_dirs(caps)
        where = ", ".join(skill_dirs) if skill_dirs else "(no skills directory declared)"
        seen: set = set()
        lazy_pointer_file = None
        for artifact in _pointer_artifacts(root, caps):
            text = _read_text(artifact)
            if text is None:
                continue
            rel = _rel(artifact, root)
            if _LAZY_POINTER_MARKER in text and lazy_pointer_file is None:
                lazy_pointer_file = rel
            for skill in _lazy_table_skills(text):
                if skill in seen:
                    continue
                seen.add(skill)
                if any((root / d / skill / "SKILL.md").is_file() for d in skill_dirs):
                    continue
                findings.append(_warn(
                    "context.dangling-pointer", rel,
                    f"{provider}: lazy table names skill '{skill}' but <skill>/SKILL.md "
                    f"does not exist in {where}",
                    "generate the skill for this provider or drop the table row"))
        if lazy_pointer_file and not any(_has_any_skill(root, d) for d in skill_dirs):
            findings.append(_warn(
                "context.dangling-pointer", lazy_pointer_file,
                f"{provider}: lazy-load pointer promises rule skills but no SKILL.md exists in {where}",
                "write the lazy rules as skills for this provider or embed them"))
    return findings


# ---------------------------------------------------------------------------
# context.rule-unreachable
# ---------------------------------------------------------------------------

def check_rule_unreachable(
    project_root: Path,
    active_providers: Sequence[str],
    capabilities: Mapping[str, Mapping],
    active_set,
) -> list:
    """``context.rule-unreachable``: reachability invariant (spec 4.3) violated (WARN; spec: ERROR from Phase 1).

    A generated rule file is reachable for a provider when one of these holds:

    * ``rules_read_channels`` contains ``native-rules-dir`` or ``path-scoped``
      (the rules directory itself is read);
    * its heading line is embedded in the provider's entry file (the entry
      file is always loaded);
    * ``rules_read_channels`` contains ``skills`` and
      ``<skill dir>/<rule-stem>/SKILL.md`` exists.
    """
    root = Path(project_root)
    findings = []
    for provider in active_providers:
        caps = capabilities.get(provider) or {}
        channels = caps.get("rules_read_channels") or []
        if any(c in channels for c in _FILE_CHANNELS):
            continue
        context_file = caps.get("context_file")
        entry_text = (_read_text(root / context_file) or "") if context_file else ""
        entry_lines = {_normalize_heading(line) for line in entry_text.splitlines() if line.strip()}
        skill_dirs = _skill_dirs(caps) if CHANNEL_SKILLS in channels else []
        texts = {rule: _read_text(rule) for rule in _rule_files(root, caps)}
        headings = {rule: _normalize_heading(_first_heading(t)) for rule, t in texts.items() if t is not None}
        for rule, text in texts.items():
            if text is None:
                continue
            heading = headings[rule]
            if heading and heading in entry_lines:
                # Rules sharing a heading must not mask each other: only then also
                # require the second body line (embedded text may be re-substituted,
                # so unique headings are trusted on their own).
                shared = list(headings.values()).count(heading) > 1
                if not shared or _body_probe(text) in entry_text:
                    continue
            if any((root / d / rule.stem / "SKILL.md").is_file() for d in skill_dirs):
                continue
            findings.append(_warn(
                "context.rule-unreachable", _rel(rule, root),
                f"{provider}: rule '{rule.stem}' is neither embedded in "
                f"{context_file or 'an entry file'} nor reachable through a read channel "
                f"(rules_read_channels={list(channels)})",
                "embed the rule, route it to a skill the provider discovers, or drop it"))
    return findings


# ---------------------------------------------------------------------------
# context.unread-channel
# ---------------------------------------------------------------------------

def _non_empty_dir(directory: Path) -> bool:
    return directory.is_dir() and any(True for _ in directory.iterdir())


def check_unread_channel(
    project_root: Path,
    active_providers: Sequence[str],
    capabilities: Mapping[str, Mapping],
    active_set,
) -> list:
    """``context.unread-channel``: a generated directory the provider never reads (WARN).

    * ``rules_dir`` with files while ``rules_read_channels`` has neither
      ``native-rules-dir`` nor ``path-scoped``;
    * a non-empty ``skills_dir`` that is not in ``skills_discovery_dirs``.

    Paths matching a glob of ``config/context-anchors.yaml: intentional_unread``
    are exempt.
    """
    root = Path(project_root)
    exempt = _intentional_unread()
    findings = []

    def is_exempt(rel: str) -> bool:
        return any(fnmatch.fnmatch(rel, pattern) for pattern in exempt)

    for provider in active_providers:
        caps = capabilities.get(provider) or {}
        channels = caps.get("rules_read_channels") or []
        rules_dir = caps.get("rules_dir")
        if (caps.get("has_rules") and rules_dir and not any(c in channels for c in _FILE_CHANNELS)
                and _rule_files(root, caps) and not is_exempt(str(rules_dir))):
            findings.append(_warn(
                "context.unread-channel", str(rules_dir),
                f"{provider}: '{rules_dir}' is generated but not read "
                f"(rules_read_channels={list(channels)})",
                "stop generating the directory or add it to intentional_unread with a reason"))
        skills_dir = caps.get("skills_dir")
        discovery = caps.get("skills_discovery_dirs") or []
        if (isinstance(skills_dir, str) and skills_dir and skills_dir not in discovery
                and _non_empty_dir(root / skills_dir) and not is_exempt(skills_dir)):
            findings.append(_warn(
                "context.unread-channel", skills_dir,
                f"{provider}: '{skills_dir}' is generated but not in skills_discovery_dirs {list(discovery)}",
                "fix skills_discovery_dirs or stop generating the directory"))
    return findings


# ---------------------------------------------------------------------------
# context-profile.marker-in-rule
# ---------------------------------------------------------------------------

def check_marker_in_rule(
    project_root: Path,
    active_providers: Sequence[str],
    capabilities: Mapping[str, Mapping],
    active_set,
) -> list:
    """``context-profile.marker-in-rule``: ``CONTEXT_PROFILE_COMPACT`` in a rule file (IC-03; WARN in Phase 0, spec: ERROR).

    Scans rule sources (``<project_root>/rules/**/*.md``) and the generated
    rule directories of the active providers. Native rules must stay
    byte-identical across context profiles, so the marker is not allowed there.
    """
    root = Path(project_root)
    candidates: dict = {}
    source_dir = root / "rules"
    if source_dir.is_dir():
        for path in sorted(source_dir.rglob("*.md")):
            candidates[path] = None
    for provider in active_providers:
        for path in _rule_files(root, capabilities.get(provider) or {}):
            candidates[path] = provider
    findings = []
    for path in sorted(candidates):
        text = _read_text(path)
        if text is not None and COMPACT_MARKER in text:
            findings.append(_warn(
                "context-profile.marker-in-rule", _rel(path, root),
                f"rule file contains the profile marker {COMPACT_MARKER} "
                "(native rules must be identical in every context profile)",
                "move profile-conditional content out of rules (IC-03)"))
    return findings
