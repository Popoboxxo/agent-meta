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

import re
from dataclasses import dataclass, field
from datetime import date
from pathlib import Path

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:
    _YAML_AVAILABLE = False


# Marker written into disabled role lines — also used to detect already-disabled
# lines for idempotency.
_AUTO_DISABLED_MARKER = "# AUTO-DISABLED"

# Matches a YAML list item inside the ``roles:`` block, e.g. ``  - developer``.
# Captures leading indentation (group "indent") and the role name (group "role").
_ROLE_LINE_RE = re.compile(r"^(?P<indent>\s*)-\s+(?P<role>[A-Za-z0-9_-]+)\s*$")


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


def _parse_frontmatter(template_path: Path) -> dict:
    """Parse the YAML frontmatter block of a Markdown agent template.

    The frontmatter is the leading block delimited by ``---`` fences. Returns an
    empty dict when no frontmatter is present or it cannot be parsed.
    """
    try:
        text = template_path.read_text(encoding="utf-8")
    except OSError:
        return {}
    if not text.startswith("---"):
        return {}
    # Split on the closing fence: text == "---\n<yaml>\n---\n<body>"
    parts = text.split("\n---", 1)
    if len(parts) < 2:
        return {}
    block = parts[0]
    if block.startswith("---"):
        block = block[3:]
    if not _YAML_AVAILABLE:
        return {}
    try:
        data = _yaml.safe_load(block)
    except _yaml.YAMLError:
        return {}
    return data if isinstance(data, dict) else {}


def _template_path_for_role(agent_meta_root: Path, role: str) -> Path:
    """Return the expected generic template path for a role name."""
    return agent_meta_root / "agents" / "1-generic" / f"{role}.md"


def _is_role_template(path: Path) -> bool:
    """True for generic templates that represent an actual role.

    Underscore-prefixed files (``_skill-wrapper.md``, ``_wf-*.md``) are partials
    or workflow includes, not standalone roles.
    """
    return path.suffix == ".md" and not path.name.startswith("_")


def _collect_role_defaults(agent_meta_root: Path) -> set[str]:
    """Return the set of role names defined in config/role-defaults.yaml."""
    defaults = _read_yaml(agent_meta_root / "config" / "role-defaults.yaml")
    roles = defaults.get("roles", {})
    if isinstance(roles, dict):
        return set(roles.keys())
    return set()


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

    role_defaults = _collect_role_defaults(agent_meta_root)
    generic_dir = agent_meta_root / "agents" / "1-generic"

    # --- 1. roles_without_template + 3. deprecated_roles -------------------
    for role in project_roles:
        if not isinstance(role, str):
            continue
        template = _template_path_for_role(agent_meta_root, role)
        if not template.exists():
            report.add(
                category="roles_without_template",
                severity="error",
                role=role,
                message=f"Role '{role}' has no generic template",
                detail=str(template),
            )
            continue
        frontmatter = _parse_frontmatter(template)
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
    today = date.today().isoformat()
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
