"""SyncLog — collects sync actions, warnings, skips and infos."""
from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path


class SyncLog:
    """Log collector for sync.py actions, warnings, errors, and info messages."""

    def __init__(self):
        """Initialize an empty sync log with action, warning, error, and info lists."""
        self.actions: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.skipped: list[str] = []
        self.infos: list[str] = []
        self.debugs: list[str] = []
        self._seen_warnings: set[str] = set()
        self.start_time = datetime.now()  # noqa: DTZ005

    def action(self, tag: str, target: str, source: str):
        """Record a sync action with tag, target, and source.

        Args:
            tag: Action type label (e.g., 'SYNC', 'GENERATE').
            target: Target file or resource.
            source: Source file or origin of the action.
        """
        self.actions.append(f"[{tag:<8}]  {target:<50}  ({source})")

    def warn(self, message: str):
        """Record a warning message, deduplicating repeated warnings.

        The same warning is emitted only once to keep the report readable.

        Args:
            message: Warning text to record and print to stderr.
        """
        # The same template is substituted once per provider — emit each
        # distinct warning only once to keep the report readable.
        if message in self._seen_warnings:
            return
        self._seen_warnings.add(message)
        self.warnings.append(f"[WARN]   {message}")
        print(f"  !  {message}", file=sys.stderr)

    def warning(self, message: str):
        """Alias for warn(). Record a warning message."""
        self.warn(message)

    def error(self, target: str, message: str):
        """Record an error for a target with error message.

        Args:
            target: Resource or file that encountered the error.
            message: Error description.
        """
        line = f"[ERROR]  {target:<50}  {message}"
        self.errors.append(line)
        print(f"  X  {target}: {message}", file=sys.stderr)

    def skip(self, target: str, reason: str):
        """Record a skipped action.

        Args:
            target: Resource or file that was skipped.
            reason: Reason for skipping.
        """
        self.skipped.append(f"[SKIP]   {target:<50}  ({reason})")

    def note(self, target: str, reason: str):
        """Record an info-level note about a target.

        Renamed from `info()` (#574): the two-positional-argument signature
        (target, reason) is not a `logging.info(msg, *args)`-style format
        string call, which confused linters into flagging false-positive
        `PLE1205` (too-many-args-for-format-string) findings at every call
        site. `note()` avoids the stdlib-logging naming collision entirely.

        Args:
            target: Resource or operation name.
            reason: Additional information or context.
        """
        self.infos.append(f"[INFO]   {target:<50}  ({reason})")

    def debug(self, target: str, message: str):
        """Record a debug message.

        Args:
            target: Resource or component for debugging.
            message: Debug details.
        """
        self.debugs.append(f"[DEBUG]  {target:<50}  {message}")

    def provider_header(self, provider: str):
        """Add a provider section header to the log.

        Args:
            provider: Provider name to display in the header.
        """
        self.infos.append("")
        self.infos.append(f"[PROVIDER] {provider}")
        self.infos.append(f"{'~' * (len(provider) + 11)}")

    def write(self, log_path: Path, config_path: str, source_version: str,
              mode: str, platforms: list[str], dry_run: bool,
              providers: list[str] | None = None,
              speech_mode: str = "full"):
        """Write the collected log to a file and print to stdout.

        Args:
            log_path: Path where the log file will be written.
            config_path: Path to the project config file.
            source_version: Version of agent-meta being used.
            mode: Sync mode (e.g., 'sync', 'validate').
            platforms: List of target platforms.
            dry_run: Whether this is a dry-run execution.
            providers: Optional list of providers used in sync.
            speech_mode: Speech mode setting for context generation.
        """
        lines = [
            "=" * 60,
            f"agent-meta sync — {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}",
            "=" * 60,
            f"Config:    {config_path}",
            f"Source:    .agent-meta/ (v{source_version})",
            f"Mode:      {'DRY-RUN — ' if dry_run else ''}{mode}",
            f"Platforms: {', '.join(platforms) if platforms else '(none)'}",
            f"Providers: {', '.join(providers) if providers else '(none)'}",
            f"Speech:    {speech_mode}",
            "",
            "ACTIONS",
            "-------",
        ]
        lines += self.actions
        if self.skipped:
            lines += ["", "SKIPPED", "-------"]
            lines += self.skipped
        if self.infos:
            lines += ["", "INFO", "----"]
            lines += self.infos

        if self.debugs:
            lines += ["", "DEBUG", "-----"]
            lines += self.debugs

        if self.errors:
            lines += ["", "ERRORS", "------"]
            lines += self.errors

        if self.warnings:
            lines += ["", "WARNINGS", "--------"]
            lines += self.warnings
        else:
            lines += ["", "WARNINGS", "--------", "(none)"]

        summary = (
            f"{len(self.actions)} action(s)  |  {len(self.skipped)} skipped  |  "
            f"{len(self.warnings)} warning(s)"
        )
        if self.errors:
            summary += f"  |  {len(self.errors)} error(s)"
        lines += [
            "",
            "SUMMARY",
            "-------",
            summary,
            f"Logfile: {log_path}",
        ]

        content = "\n".join(lines) + "\n"
        if not dry_run:
            log_path.write_text(content, encoding="utf-8")
        print()
        print(content)
