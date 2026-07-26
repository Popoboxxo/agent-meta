"""GitHub Issues adapter — creates SE requirements as GitHub Issues via gh CLI."""

import json
import re
import subprocess

from .base import SEAdapter

# Default label mapping when none is configured
_DEFAULT_LABELS: dict[str, str] = {
    "l1": "se:l1",
    "l2": "se:l2",
    "l3": "se:l3",
    "leaf": "se:leaf",
}

# Tier detection: req_id prefix patterns
_L1_PATTERN = re.compile(r"REQ-L1[-_]", re.IGNORECASE)
_L2_PATTERN = re.compile(r"REQ-L2[-_]|subsystem", re.IGNORECASE)
_L3_PATTERN = re.compile(r"REQ[-_].*[-_]CP[-_]|REQ-L3[-_]|component", re.IGNORECASE)
_LEAF_PATTERN = re.compile(r"leaf|impl", re.IGNORECASE)


class GitHubIssuesAdapter(SEAdapter):
    """Export SE requirements as GitHub Issues using the ``gh`` CLI.

    Requirements:
    - ``gh`` CLI must be installed and authenticated (``gh auth login``).
    - ``repo`` must be set in config (e.g. "my-org/my-project").

    Raises:
        RuntimeError: If ``gh`` is not available or not authenticated.
    """

    def __init__(self, config: dict) -> None:
        """Initialise the adapter from the ``se-export`` config block.

        Args:
            config: The ``se-export`` section of project.yaml.  Expected keys:
                ``repo`` (required), ``milestone`` (optional),
                ``labels`` (optional dict overriding defaults).
        """
        self._repo: str = config.get("repo", "")
        self._milestone: str | None = config.get("milestone")
        raw_labels: dict = config.get("labels", {})
        self._labels: dict[str, str] = {**_DEFAULT_LABELS, **raw_labels}
        self._dry_run: bool = config.get("dry_run", False)

        self._verify_gh_available()

    # ------------------------------------------------------------------
    # SEAdapter interface
    # ------------------------------------------------------------------

    def create_requirement(
        self,
        req_id: str,
        title: str,
        description: str,
        parent_id: str | None = None,
    ) -> str:
        """Create a GitHub Issue for the requirement.

        The issue body includes the req_id and optional parent reference.

        Args:
            req_id: Internal requirement identifier.
            title: Issue title (will be prefixed with req_id).
            description: Issue body text.
            parent_id: Optional parent issue URL/number for traceability.

        Returns:
            GitHub issue URL (e.g. https://github.com/org/repo/issues/42).

        Raises:
            RuntimeError: On gh CLI failure.
        """
        body_parts = [
            f"**Requirement ID:** `{req_id}`",
        ]
        if parent_id:
            body_parts.append(f"**Parent:** {parent_id}")
        body_parts += ["", description or "(no description provided)"]
        body = "\n".join(body_parts)

        labels = self._resolve_labels(req_id)

        cmd = self._build_create_cmd(title=f"{req_id}: {title}", body=body, labels=labels)

        if self._dry_run:
            return f"[dry-run] would run: {' '.join(cmd)}"

        result = self._run_gh(cmd)
        issue_url = result.stdout.strip()
        if not issue_url:
            raise RuntimeError(
                f"gh issue create succeeded but returned no URL for {req_id}"
            )
        return issue_url

    def link_requirements(
        self,
        source_id: str,
        target_id: str,
        link_type: str,
    ) -> None:
        """Add a traceability comment on the source issue.

        Args:
            source_id: GitHub issue URL of the source.
            target_id: GitHub issue URL of the target.
            link_type: Relationship label (e.g. "refines").
        """
        if self._dry_run:
            return

        source_number = _extract_issue_number(source_id)
        if source_number is None:
            return

        comment = f"**Traceability ({link_type}):** {target_id}"
        cmd = [
            "gh", "issue", "comment", str(source_number),
            "--repo", self._repo,
            "--body", comment,
        ]
        self._run_gh(cmd)

    def update_status(self, req_id: str, status: str) -> None:
        """Update requirement status by adding a label or closing the issue.

        - ``implemented`` / ``verified`` → close the issue.
        - All statuses → add label ``se:status:<status>``.

        Args:
            req_id: GitHub issue URL (as returned by create_requirement).
            status: One of draft | approved | implemented | verified.
        """
        if self._dry_run:
            return

        issue_number = _extract_issue_number(req_id)
        if issue_number is None:
            return

        label = f"se:status:{status}"
        label_cmd = [
            "gh", "issue", "edit", str(issue_number),
            "--repo", self._repo,
            "--add-label", label,
        ]
        try:
            self._run_gh(label_cmd)
        except RuntimeError:
            # Label might not exist; ignore to avoid blocking the export
            pass

        if status in ("implemented", "verified"):
            close_cmd = [
                "gh", "issue", "close", str(issue_number),
                "--repo", self._repo,
            ]
            self._run_gh(close_cmd)

    def export_interface(self, interface: dict) -> str:
        """Create a GitHub Issue for a CQRS interface contract.

        Args:
            interface: Interface dict (from cqrs_interfaces in the schema).

        Returns:
            GitHub issue URL.
        """
        name: str = interface.get("name", "unknown-interface")
        body = f"**Interface Contract:** `{name}`\n\n```json\n{json.dumps(interface, indent=2)}\n```"

        cmd = self._build_create_cmd(
            title=f"[Interface] {name}",
            body=body,
            labels=[self._labels.get("leaf", "se:leaf"), "se:interface"],
        )

        if self._dry_run:
            return f"[dry-run] would run: {' '.join(cmd)}"

        result = self._run_gh(cmd)
        return result.stdout.strip()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _verify_gh_available(self) -> None:
        """Raise RuntimeError if gh CLI is not installed or not authenticated."""
        if self._dry_run:
            return

        try:
            result = subprocess.run(  # noqa: PLW1510
                ["gh", "auth", "status"],
                capture_output=True,
                text=True,
            )
            if result.returncode != 0:
                raise RuntimeError(
                    "gh CLI is not authenticated. Run 'gh auth login' first.\n"
                    f"gh auth status output: {result.stderr.strip()}"
                )
        except FileNotFoundError as exc:
            raise RuntimeError(
                "gh CLI not found. Install it from https://cli.github.com/ "
                "and run 'gh auth login'."
            ) from exc

    def _build_create_cmd(
        self,
        title: str,
        body: str,
        labels: list[str],
    ) -> list[str]:
        """Build the gh issue create command list."""
        cmd = [
            "gh", "issue", "create",
            "--repo", self._repo,
            "--title", title,
            "--body", body,
        ]
        for label in labels:
            if label:
                cmd += ["--label", label]
        if self._milestone:
            cmd += ["--milestone", self._milestone]
        return cmd

    def _resolve_labels(self, req_id: str) -> list[str]:
        """Determine which labels to attach based on req_id naming convention."""
        if _L1_PATTERN.search(req_id):
            base = self._labels.get("l1", "se:l1")
            return [base, "se:system"]
        if _L2_PATTERN.search(req_id):
            base = self._labels.get("l2", "se:l2")
            return [base, "se:subsystem"]
        if _L3_PATTERN.search(req_id):
            base = self._labels.get("l3", "se:l3")
            return [base, "se:component"]
        if _LEAF_PATTERN.search(req_id):
            base = self._labels.get("leaf", "se:leaf")
            return [base, "se:implementable"]
        # Default: treat as L1 when pattern is unclear
        return [self._labels.get("l1", "se:l1")]

    def _run_gh(self, cmd: list[str]) -> subprocess.CompletedProcess:
        """Run a gh CLI command, raising RuntimeError on failure.

        Args:
            cmd: Command token list.

        Returns:
            CompletedProcess instance.

        Raises:
            RuntimeError: If the command exits with a non-zero status.
        """
        result = subprocess.run(cmd, capture_output=True, text=True)  # noqa: PLW1510
        if result.returncode != 0:
            raise RuntimeError(
                f"gh command failed (exit {result.returncode}):\n"
                f"  cmd: {' '.join(cmd)}\n"
                f"  stderr: {result.stderr.strip()}"
            )
        return result


# ------------------------------------------------------------------
# Module-level helpers
# ------------------------------------------------------------------

def _extract_issue_number(issue_url: str) -> int | None:
    """Extract the numeric issue number from a GitHub issue URL or bare number.

    Args:
        issue_url: Full URL (https://github.com/.../issues/42) or plain int string.

    Returns:
        Integer issue number, or None if it cannot be parsed.
    """
    if not issue_url:
        return None
    # Try plain integer
    if issue_url.isdigit():
        return int(issue_url)
    # Try trailing number in URL
    match = re.search(r"/issues/(\d+)$", issue_url)
    if match:
        return int(match.group(1))
    return None
