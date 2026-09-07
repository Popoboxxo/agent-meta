"""Audit data shapes shared by config_audit and config_audit_apply (Issue #478).

Leaf module — dataclasses only, no imports beyond the stdlib. Extracted so
the ``config_audit`` ↔ ``config_audit_apply`` pair no longer references each
other for the shared ``AuditReport`` shape: ``config_audit`` re-exports the
apply entry point at top level (backward-compatible API), and
``config_audit_apply`` now imports the report type from this leaf instead of
back-importing from ``config_audit`` (that back-edge existed only under
``TYPE_CHECKING``, but it still made the pair a logical cycle).
"""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class AuditIssue:
    """A single finding produced by :func:`config_audit.audit_config`.

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
