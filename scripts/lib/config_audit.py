"""Config audit: detect inconsistencies between project.yaml, role-defaults and templates.

This module provides a read-only audit routine (:func:`audit_config`). The
matching line-based remediation step (``apply_audit``, disables deprecated
roles in ``.meta-config/project.yaml`` without destroying YAML comments) lives
in :mod:`config_audit_apply` (split out to keep this module under the 600-line
convention) and is re-exported here for backward compatibility.

Design constraints:
    * No external Python dependencies beyond the stdlib + PyYAML (already used
      project-wide). YAML is only *read* via PyYAML — never re-dumped, since
      ``yaml.dump`` discards comments and reorders keys.
"""
from __future__ import annotations

import re
from collections import Counter
from pathlib import Path

from .config_audit_apply import apply_audit  # noqa: F401 -- re-exported, see below
from .config_audit_providers import find_missing_providers
from .config_audit_types import AuditIssue, AuditReport  # noqa: F401 -- re-exported for API compat
from .frontmatter import parse_frontmatter_file
from .io import load_yaml_file
from .providers import load_providers_config
from .roles import load_roles_config


# Matches a `based-on:` frontmatter value, e.g. ``1-generic/developer.md@3.1.1``.
# Captures the generic template stem (group "stem") and the pinned version
# (group "version").
_BASED_ON_RE = re.compile(
    r"^1-generic/(?P<stem>[A-Za-z0-9_-]+)\.md@(?P<version>[\w.\-]+)$"
)

# Leading integer run of a semver-ish string, e.g. "4" from "4.0.1" or
# "3.1.1-beta.2". Non-numeric/missing major segments return None.
_MAJOR_VERSION_RE = re.compile(r"^(\d+)")

# Extracts the content of a `<persona>...</persona>` block (DOTALL so the
# persona's mission statement can span multiple lines).
_PERSONA_BLOCK_RE = re.compile(r"<persona>(.*?)</persona>", re.S)

# Tools that grant write access to the filesystem. A role whose persona
# explicitly declares itself "read-only" must not carry either (issue #575).
_WRITE_TOOLS = frozenset({"Write", "Edit"})

# Matches a line that consists of *nothing but* an XML-ish tag, e.g.
# ``<persona>`` or ``</output_contract>``. Deliberately anchored to the full
# (stripped) line rather than scanning free text -- templates frequently
# mention tag names inline in prose (`` `<context>` ``) or use tag-shaped
# placeholders inside fenced output examples (``<list>``, ``<role>``), and a
# substring scan would misreport those as real structural tags (issue #567).
_STANDALONE_TAG_RE = re.compile(r"^(</?)([A-Za-z][A-Za-z0-9_-]*)>$")


# AuditIssue/AuditReport now live in the config_audit_types leaf module
# (Issue #478) and are re-exported above for API compatibility — tests and
# callers import them from this module.


def _template_path_for_role(agent_meta_root: Path, role: str) -> Path:
    """Return the expected generic template path for a role name."""
    return agent_meta_root / "agents" / "1-generic" / f"{role}.md"


# Generic templates that are intentionally never instantiated as a standalone
# role -- they exist only as an `extends:` base for other, real roles (see
# their referencing 2-platform overrides). Flagging them under
# "templates_without_default" on every --audit-config run is a known false
# positive, not a gap to fix (audit #415).
WRAPPER_TEMPLATES = frozenset({"provider-expert"})


def _is_role_template(path: Path) -> bool:
    """True for generic templates that represent an actual role.

    Underscore-prefixed files (``_skill-wrapper.md``, ``_wf-*.md``) are partials
    or workflow includes, not standalone roles. Files in WRAPPER_TEMPLATES are
    real files but intentionally have no role-defaults entry of their own.
    """
    return (
        path.suffix == ".md"
        and not path.name.startswith("_")
        and path.stem not in WRAPPER_TEMPLATES
    )


def _collect_based_on_roles(agent_meta_root: Path) -> set[str]:
    """Return roles generated via ``based-on`` from a 2-platform override.

    Thin local wrapper that defers to :func:`crossrefs.get_based_on_role_names`
    (DRY — the cross-reference scanner is the single source of truth for the
    ``based-on:`` multi-instance pattern). The import is local because the
    consistency package would otherwise pull in heavier transitive deps that
    config_audit does not need.

    Returns an empty set when the consistency module is unavailable so callers
    can treat the result as "no exclusions" without special-casing imports.
    """
    try:
        from .consistency.crossrefs import get_based_on_role_names
    except ImportError:
        return set()
    return get_based_on_role_names(agent_meta_root)


def _major_version(version: object) -> int | None:
    """Extract the leading major-version integer from a version string.

    Returns None when ``version`` has no parseable leading integer (e.g. an
    empty string or a non-numeric placeholder) so callers can skip comparison
    instead of crashing.
    """
    match = _MAJOR_VERSION_RE.match(str(version).strip())
    return int(match.group(1)) if match else None


def _collect_platform_overrides(agent_meta_root: Path) -> list[Path]:
    """Return all 2-platform override templates (underscore partials excluded)."""
    platform_dir = agent_meta_root / "agents" / "2-platform"
    if not platform_dir.is_dir():
        return []
    return sorted(p for p in platform_dir.glob("*.md") if not p.name.startswith("_"))


def _find_unpaired_closing_tags(path: Path) -> list[str]:
    """Return tag names with a standalone closing line but no matching open.

    Only counts lines that are *exactly* a tag (see :data:`_STANDALONE_TAG_RE`)
    so free-text mentions or placeholder examples never trigger a false
    positive -- only a genuine orphaned closing tag (open count 0, close
    count >= 1) is reported. This is one-directional by design: an unclosed
    *opening* tag (e.g. a template placeholder like ``<list>``) is not this
    check's concern (issue #567).
    """
    opens: Counter = Counter()
    closes: Counter = Counter()
    for line in path.read_text(encoding="utf-8").splitlines():
        match = _STANDALONE_TAG_RE.match(line.strip())
        if not match:
            continue
        slash, name = match.groups()
        if slash == "</":
            closes[name] += 1
        else:
            opens[name] += 1
    return sorted(name for name, count in closes.items() if count > opens.get(name, 0))


def _find_tool_privilege_mismatch(path: Path) -> str | None:
    """Return a mismatch message when a role declares itself read-only but
    carries a write-capable tool (``Write``/``Edit``).

    Scoped to the ``<persona>`` block only (not the whole file) -- "read-only"
    shows up in many templates as a description of an *external* concept
    (e.g. a CLI's read-only mode) rather than a claim about the agent's own
    tool access; only the persona's self-description is authoritative here
    (issue #575, decision: keep `Bash` on `validator`/`code-reviewer` per the
    established "(read-only)" tools-bullet annotation convention -- this
    check targets the stronger Write/Edit signal instead).
    """
    text = path.read_text(encoding="utf-8")
    match = _PERSONA_BLOCK_RE.search(text)
    if not match or not re.search(r"read-only", match.group(1), re.IGNORECASE):
        return None
    tools = parse_frontmatter_file(path).get("tools") or []
    if not isinstance(tools, list):
        return None
    offending = sorted(_WRITE_TOOLS.intersection(tools))
    if not offending:
        return None
    return (
        f"declares itself read-only in <persona> but has write-capable "
        f"tool(s): {', '.join(offending)}"
    )


def _collect_template_files(agent_meta_root: Path) -> list[Path]:
    """Return all agent template Markdown files (1-generic + 2-platform)."""
    files: list[Path] = []
    for subdir in ("1-generic", "2-platform"):
        directory = agent_meta_root / "agents" / subdir
        if directory.is_dir():
            files.extend(sorted(directory.glob("*.md")))
    return files


def _collect_pipeline_role_refs(config: dict) -> set[str]:
    """Return every role referenced by a quality pipeline ``agent:`` field.

    Handles both the project-override shape (``quality-pipelines.overrides``)
    and a fully-specified ``quality_pipelines`` block. Nested ``loop`` and
    ``parallel_group`` agent references are included.
    """
    refs: set[str] = set()

    def _walk(node: object) -> None:
        if isinstance(node, dict):
            agent = node.get("agent")
            if isinstance(agent, str) and agent:
                refs.add(agent)
            for key in ("generator", "critic"):
                val = node.get(key)
                if isinstance(val, str) and val:
                    refs.add(val)
            for value in node.values():
                _walk(value)
        elif isinstance(node, list):
            for item in node:
                _walk(item)

    for key in ("quality_pipelines", "quality-pipelines"):
        block = config.get(key)
        if block:
            _walk(block)
    return refs


def audit_config(agent_meta_root: Path, project_config_path: Path) -> AuditReport:
    """Audit a project config against agent templates and role defaults.

    Detected categories:
        * ``roles_without_template`` (error): a role listed in project.yaml has
          no ``agents/1-generic/<role>.md`` template.
        * ``templates_without_default`` (info): a generic role template has no
          entry in ``config/role-defaults.yaml`` (underscore files ignored).
        * ``deprecated_roles`` (warning): a listed role points to a template
          whose frontmatter has ``deprecated: true``.
        * ``orphaned_pipelines`` (warning): a quality pipeline references a role
          that is not part of the project's ``roles`` list.
        * ``stale_platform_overrides`` (warning): a 2-platform override's
          ``based-on: "1-generic/<role>.md@<version>"`` pin has fallen 1+
          major versions behind the current generic template (issue #560).
        * ``unpaired_closing_tags`` (error): a template has a standalone
          closing tag (e.g. ``</output>``) with no matching opening tag
          anywhere in the file (issue #567).
        * ``tool_privilege_mismatch`` (warning): a role's ``<persona>``
          declares itself read-only but its frontmatter ``tools:`` list
          grants ``Write``/``Edit`` access (issue #575).
        * ``provider_registry_completeness`` (warning): a provider registered
          in ``config/ai-providers.yaml`` is missing from a known
          provider-keyed Python enumeration in ``scripts/`` (issue #625).

    Args:
        agent_meta_root: Repository root containing ``agents/`` and ``config/``.
        project_config_path: Path to ``.meta-config/project.yaml``.

    Returns:
        An :class:`AuditReport` with all discovered issues.
    """
    report = AuditReport()
    # Canonical single-file loader (Issue #479), fail-closed: raises SyncError
    # (with file + location) on malformed YAML / missing PyYAML instead of the
    # former _read_yaml's RuntimeError; missing file still yields {}.
    config = load_yaml_file(project_config_path, on_error="raise", default={})

    project_roles = config.get("roles", [])
    if not isinstance(project_roles, list):
        project_roles = []
    project_roles_set = set(project_roles)

    role_defaults = set(load_roles_config(agent_meta_root)["roles"].keys())
    generic_dir = agent_meta_root / "agents" / "1-generic"

    # Roles produced by a 2-platform override via ``based-on:`` (e.g. the five
    # provider-expert instances). They have no own 1-generic template by design
    # and must not be reported as "roles_without_template".
    based_on_roles = _collect_based_on_roles(agent_meta_root)

    # --- 1. roles_without_template + 3. deprecated_roles -------------------
    for role in project_roles:
        if not isinstance(role, str):
            continue
        template = _template_path_for_role(agent_meta_root, role)
        if not template.exists():
            if role in based_on_roles:
                # Generated via based-on from a 2-platform override — not a
                # missing template.
                continue
            report.add(
                category="roles_without_template",
                severity="error",
                role=role,
                message=f"Role '{role}' has no generic template",
                detail=str(template),
            )
            continue
        frontmatter = parse_frontmatter_file(template)
        if frontmatter.get("deprecated") is True:
            report.add(
                category="deprecated_roles",
                severity="warning",
                role=role,
                message=f"Role '{role}' points to a deprecated template",
                detail=str(template),
            )

    # --- 2. templates_without_default --------------------------------------
    if generic_dir.is_dir():
        for template in sorted(generic_dir.glob("*.md")):
            if not _is_role_template(template):
                continue
            role_name = template.stem
            if role_name not in role_defaults:
                report.add(
                    category="templates_without_default",
                    severity="info",
                    role=role_name,
                    message=(
                        f"Template '{role_name}' has no entry in role-defaults.yaml"
                    ),
                    detail=str(template),
                )

    # --- 4. orphaned_pipelines ---------------------------------------------
    pipeline_refs = _collect_pipeline_role_refs(config)
    for ref in sorted(pipeline_refs):
        if project_roles_set and ref not in project_roles_set:
            report.add(
                category="orphaned_pipelines",
                severity="warning",
                role=ref,
                message=(
                    f"Pipeline references role '{ref}' not in project roles list"
                ),
            )

    # --- 5. stale_platform_overrides ----------------------------------------
    # Full-replacement 2-platform overrides pin the generic template they were
    # copied from via `based-on: "1-generic/<role>.md@<version>"`. Unlike the
    # `extends:`+`patches:` composition style, a full-replacement override does
    # not automatically inherit changes to its generic base — including
    # security-relevant workflow steps added later (issue #560). Flag any
    # override whose pinned major version has fallen 1+ major versions behind
    # the current generic template so the drift becomes visible instead of
    # silently accumulating.
    for override in _collect_platform_overrides(agent_meta_root):
        frontmatter = parse_frontmatter_file(override)
        based_on = frontmatter.get("based-on", "")
        if not isinstance(based_on, str) or not based_on:
            continue
        match = _BASED_ON_RE.match(based_on)
        if not match:
            continue
        generic_stem = match.group("stem")
        pinned_version = match.group("version")

        generic_template = _template_path_for_role(agent_meta_root, generic_stem)
        if not generic_template.exists():
            # Missing base template is a different problem class entirely --
            # not this check's concern.
            continue
        current_version = parse_frontmatter_file(generic_template).get("version")
        if not current_version:
            continue

        pinned_major = _major_version(pinned_version)
        current_major = _major_version(current_version)
        if pinned_major is None or current_major is None:
            continue

        major_diff = current_major - pinned_major
        if major_diff >= 1:
            report.add(
                category="stale_platform_overrides",
                severity="warning",
                role=override.stem,
                message=(
                    f"Override '{override.name}' is based-on "
                    f"{generic_stem}.md@{pinned_version}, but the generic "
                    f"template is now at @{current_version} "
                    f"({major_diff} major version(s) behind)"
                ),
                detail=str(override),
            )

    # --- 6. unpaired_closing_tags -------------------------------------------
    # Copy-paste artifacts (a trailing `</output>` with no `<output>` anywhere
    # in the file) silently ship broken structural markup into every synced
    # project (issue #567). Scoped to 1-generic + 2-platform since those are
    # the only template layers maintained in this repo.
    for template in _collect_template_files(agent_meta_root):
        for tag in _find_unpaired_closing_tags(template):
            report.add(
                category="unpaired_closing_tags",
                severity="error",
                role=template.stem,
                message=(
                    f"Template '{template.name}' has an unpaired closing "
                    f"tag </{tag}> with no matching <{tag}>"
                ),
                detail=str(template),
            )

    # --- 7. tool_privilege_mismatch -----------------------------------------
    # Least-privilege drift: a role whose persona explicitly claims to be
    # read-only must not silently gain Write/Edit access via a copy-pasted
    # tools list (issue #575).
    for template in _collect_template_files(agent_meta_root):
        message = _find_tool_privilege_mismatch(template)
        if message:
            report.add(
                category="tool_privilege_mismatch",
                severity="warning",
                role=template.stem,
                message=f"Template '{template.name}' {message}",
                detail=str(template),
            )

    # --- 8. provider_registry_completeness (issue #625) ---------------------
    # WARN only: a provider can be legitimately excluded from a touchpoint;
    # see config_audit_providers.py for the check itself and its rationale.
    registered_providers = set(load_providers_config(agent_meta_root).keys())
    for touchpoint, provider in find_missing_providers(agent_meta_root, registered_providers):
        report.add(
            category="provider_registry_completeness",
            severity="warning",
            role=provider,
            message=f"Provider '{provider}' is missing from {touchpoint.description}",
            detail=touchpoint.file,
        )

    return report


def format_report(report: AuditReport) -> str:
    """Render an :class:`AuditReport` as a human-readable console block.

    Findings are grouped by category in stable order and prefixed with a short
    severity tag. Empty reports return a single ``ok`` line so callers can print
    the result unconditionally.
    """
    if not report.has_issues:
        return "Config audit: no issues found."

    lines: list[str] = ["Config Audit Report", "=" * 40]

    sections: list[tuple[str, str, str]] = [
        ("deprecated_roles", "Deprecated Roles [auto-fixable with --apply]", "[WARN] "),
        ("roles_without_template", "Roles Without Template", "[ERROR]"),
        ("templates_without_default", "Templates Without Role-Default", "[INFO] "),
        ("orphaned_pipelines", "Orphaned Pipeline References", "[WARN] "),
        ("stale_platform_overrides", "Stale Platform Overrides (based-on drift)", "[WARN] "),
        ("unpaired_closing_tags", "Unpaired Closing Tags", "[ERROR]"),
        ("tool_privilege_mismatch", "Tool-Privilege Mismatches (read-only vs. Write/Edit)", "[WARN] "),
        ("provider_registry_completeness", "Provider Registry Completeness (missing from a known enumeration)", "[WARN] "),
    ]

    for category, title, tag in sections:
        issues = report.by_category(category)
        if not issues:
            continue
        lines.append(f"\n{tag} {title} ({len(issues)}):")
        for issue in issues:
            lines.append(f"  - {issue.role or '-'}: {issue.message}")
            if issue.detail and issue.detail != issue.message:
                lines.append(f"      ({issue.detail})")

    lines.append(f"\nTotal: {len(report.issues)} issue(s) found.")
    return "\n".join(lines)


def report_to_dict(report: AuditReport) -> dict:
    """Return a JSON-serialisable dict grouping all issues by category.

    Intended for the admin-server REST endpoint (``GET /api/config-audit``).
    """
    categories = (
        "deprecated_roles",
        "roles_without_template",
        "templates_without_default",
        "orphaned_pipelines",
        "stale_platform_overrides",
        "unpaired_closing_tags",
        "tool_privilege_mismatch",
        "provider_registry_completeness",
    )
    grouped: dict[str, list[dict]] = {c: [] for c in categories}
    for issue in report.issues:
        grouped.setdefault(issue.category, []).append({
            "category": issue.category,
            "severity": issue.severity,
            "role": issue.role,
            "message": issue.message,
            "detail": issue.detail,
        })
    return {
        "has_issues": report.has_issues,
        "total": len(report.issues),
        "categories": grouped,
    }


# apply_audit() lives in config_audit_apply.py, re-exported via the import above.
