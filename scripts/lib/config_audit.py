"""Config audit: detect inconsistencies between project.yaml, role-defaults and templates.

This module provides a read-only audit routine (:func:`audit_config`) plus a
line-based remediation step (:func:`apply_audit`) that disables deprecated roles
in ``.meta-config/project.yaml`` without destroying YAML comments.

Design constraints:
    * No external Python dependencies beyond the stdlib + PyYAML (already used
      project-wide). YAML is only *read* via PyYAML — never re-dumped, since
      ``yaml.dump`` discards comments and reorders keys.
    * :func:`apply_audit` edits the config file line-by-line so hand-written
      comments survive untouched.
    * :func:`apply_audit` is idempotent: lines already carrying the
      ``# AUTO-DISABLED`` marker are skipped on re-runs.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

from .frontmatter import _YAML_AVAILABLE, parse_frontmatter_file
from .roles import load_roles_config

# `_YAML_AVAILABLE` is single-sourced from `.frontmatter` (Issue #571) so the
# fallback-behavior decision is made in exactly one place project-wide. A
# local `import yaml as _yaml` is still needed here for `_read_yaml()`, which
# parses whole project.yaml documents rather than Markdown frontmatter blocks
# (out of scope for the frontmatter-focused canonical module).
try:
    import yaml as _yaml
except ImportError:
    _yaml = None


# Marker written into disabled role lines — also used to detect already-disabled
# lines for idempotency.
_AUTO_DISABLED_MARKER = "# AUTO-DISABLED"

# Matches a YAML list item inside the ``roles:`` block, e.g. ``  - developer``.
# Captures leading indentation (group "indent") and the role name (group "role").
_ROLE_LINE_RE = re.compile(r"^(?P<indent>\s*)-\s+(?P<role>[A-Za-z0-9_-]+)\s*$")

# Matches a `based-on:` frontmatter value, e.g. ``1-generic/developer.md@3.1.1``.
# Captures the generic template stem (group "stem") and the pinned version
# (group "version").
_BASED_ON_RE = re.compile(
    r"^1-generic/(?P<stem>[A-Za-z0-9_-]+)\.md@(?P<version>[\w.\-]+)$"
)

# Leading integer run of a semver-ish string, e.g. "4" from "4.0.1" or
# "3.1.1-beta.2". Non-numeric/missing major segments return None.
_MAJOR_VERSION_RE = re.compile(r"^(\d+)")


@dataclass(frozen=True)
class AuditIssue:
    """A single finding produced by :func:`audit_config`.

    Attributes:
        category: Machine-readable issue class (e.g. ``"deprecated_roles"``).
        severity: One of ``"error"``, ``"warning"`` or ``"info"``.
        role: The role name the issue relates to (empty when not role-scoped).
        message: Short human-readable summary.
        detail: Optional additional context (file path, template name, ...).
    """

    category: str
    severity: str
    role: str
    message: str
    detail: str = ""


@dataclass
class AuditReport:
    """Aggregated result of an audit run.

    Attributes:
        issues: All findings, in discovery order.
    """

    issues: list[AuditIssue] = field(default_factory=list)

    def add(
        self,
        category: str,
        severity: str,
        role: str,
        message: str,
        detail: str = "",
    ) -> None:
        """Append a new :class:`AuditIssue` to the report."""
        self.issues.append(
            AuditIssue(
                category=category,
                severity=severity,
                role=role,
                message=message,
                detail=detail,
            )
        )

    @property
    def has_issues(self) -> bool:
        """True when at least one issue was recorded."""
        return bool(self.issues)

    @property
    def errors(self) -> list[AuditIssue]:
        """All issues with severity ``"error"``."""
        return [i for i in self.issues if i.severity == "error"]

    @property
    def warnings(self) -> list[AuditIssue]:
        """All issues with severity ``"warning"``."""
        return [i for i in self.issues if i.severity == "warning"]

    @property
    def infos(self) -> list[AuditIssue]:
        """All issues with severity ``"info"``."""
        return [i for i in self.issues if i.severity == "info"]

    @property
    def deprecated_roles(self) -> list[str]:
        """Role names flagged as deprecated, de-duplicated, in discovery order."""
        seen: dict[str, None] = {}
        for issue in self.issues:
            if issue.category == "deprecated_roles" and issue.role:
                seen.setdefault(issue.role, None)
        return list(seen.keys())

    def by_category(self, category: str) -> list[AuditIssue]:
        """All issues matching ``category``."""
        return [i for i in self.issues if i.category == category]


def _read_yaml(path: Path) -> dict:
    """Load a YAML file into a dict, returning an empty dict on absence/empty.

    Raises:
        RuntimeError: When PyYAML is unavailable.
    """
    if not _YAML_AVAILABLE:
        raise RuntimeError(
            "PyYAML is required for config audit but is not installed. "
            "Run: pip install pyyaml"
        )
    if not path.exists():
        return {}
    with path.open(encoding="utf-8") as f:
        return _yaml.safe_load(f) or {}


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

    Args:
        agent_meta_root: Repository root containing ``agents/`` and ``config/``.
        project_config_path: Path to ``.meta-config/project.yaml``.

    Returns:
        An :class:`AuditReport` with all discovered issues.
    """
    report = AuditReport()
    config = _read_yaml(project_config_path)

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


def apply_audit(report: AuditReport, project_config_path: Path) -> int:
    """Comment out deprecated role lines in project.yaml (line-based, idempotent).

    Only roles flagged under the ``deprecated_roles`` category are disabled.
    Each matching ``  - <role>`` line is rewritten as::

        # - <role>  # AUTO-DISABLED YYYY-MM-DD: deprecated

    The file is read and written line-by-line so YAML comments are preserved.
    Lines already carrying the ``# AUTO-DISABLED`` marker are skipped, making
    repeated invocations a no-op.

    Args:
        report: The audit report whose deprecated roles should be disabled.
        project_config_path: Path to ``.meta-config/project.yaml``.

    Returns:
        The number of lines that were changed.
    """
    deprecated = set(report.deprecated_roles)
    if not deprecated:
        return 0
    if not project_config_path.exists():
        return 0

    text = project_config_path.read_text(encoding="utf-8")
    # Preserve the original line endings split; keepends=True retains "\n".
    lines = text.splitlines(keepends=True)
    today = date.today().isoformat()  # noqa: DTZ011
    changed = 0

    for index, line in enumerate(lines):
        # Idempotency: never touch lines we already disabled.
        if _AUTO_DISABLED_MARKER in line:
            continue
        # Separate the line body from its trailing newline to rebuild cleanly.
        stripped_newline = ""
        body = line
        if body.endswith("\r\n"):
            stripped_newline = "\r\n"
            body = body[:-2]
        elif body.endswith("\n"):
            stripped_newline = "\n"
            body = body[:-1]

        match = _ROLE_LINE_RE.match(body)
        if not match:
            continue
        if match.group("role") not in deprecated:
            continue

        indent = match.group("indent")
        role = match.group("role")
        lines[index] = (
            f"{indent}# - {role}  "
            f"{_AUTO_DISABLED_MARKER} {today}: deprecated{stripped_newline}"
        )
        changed += 1

    if changed:
        project_config_path.write_text("".join(lines), encoding="utf-8")

    return changed
