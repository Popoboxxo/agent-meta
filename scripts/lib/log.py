"""SyncLog — collects sync actions, warnings, skips and infos."""

import sys
from datetime import datetime
from pathlib import Path


class SyncLog:
    def __init__(self):
        self.actions: list[str] = []
        self.warnings: list[str] = []
        self.errors: list[str] = []
        self.skipped: list[str] = []
        self.infos: list[str] = []
        self.debugs: list[str] = []
        self._seen_warnings: set[str] = set()
        self.start_time = datetime.now()  # noqa: DTZ005

    def action(self, tag: str, target: str, source: str):
        self.actions.append(f"[{tag:<8}]  {target:<50}  ({source})")

    def warn(self, message: str):
        # The same template is substituted once per provider — emit each
        # distinct warning only once to keep the report readable.
        if message in self._seen_warnings:
            return
        self._seen_warnings.add(message)
        self.warnings.append(f"[WARN]   {message}")
        print(f"  !  {message}", file=sys.stderr)

    def error(self, target: str, message: str):
        line = f"[ERROR]  {target:<50}  {message}"
        self.errors.append(line)
        print(f"  X  {target}: {message}", file=sys.stderr)

    def skip(self, target: str, reason: str):
        self.skipped.append(f"[SKIP]   {target:<50}  ({reason})")

    def info(self, target: str, reason: str):
        self.infos.append(f"[INFO]   {target:<50}  ({reason})")

    def debug(self, target: str, message: str):
        self.debugs.append(f"[DEBUG]  {target:<50}  {message}")

    def provider_header(self, provider: str):
        self.infos.append("")
        self.infos.append(f"[PROVIDER] {provider}")
        self.infos.append(f"{'~' * (len(provider) + 11)}")

    def write(self, log_path: Path, config_path: str, source_version: str,
              mode: str, platforms: list[str], dry_run: bool,
              providers: list[str] | None = None,
              speech_mode: str = "full"):
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
