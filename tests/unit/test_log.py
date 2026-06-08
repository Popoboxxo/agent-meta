"""Tests for scripts.lib.log — SyncLog collection and writing."""

from __future__ import annotations

from pathlib import Path

from scripts.lib.log import SyncLog


class TestSyncLog:
    def test_action_logged(self) -> None:
        log = SyncLog()
        log.action("WRITE", "agent.md", "1-generic/agent.md")
        assert len(log.actions) == 1
        assert "WRITE" in log.actions[0]
        assert "agent.md" in log.actions[0]

    def test_warning_logged_and_printed(self, capsys) -> None:
        log = SyncLog()
        log.warn("Something suspicious")
        assert len(log.warnings) == 1
        assert "Something suspicious" in log.warnings[0]

    def test_skip_logged(self) -> None:
        log = SyncLog()
        log.skip("agent.md", "role not in map")
        assert len(log.skipped) == 1
        assert "SKIP" in log.skipped[0]
        assert "role not in map" in log.skipped[0]

    def test_info_logged(self) -> None:
        log = SyncLog()
        log.info("test", "status message")
        assert len(log.infos) == 1
        assert "test" in log.infos[0]
        assert "status message" in log.infos[0]

    def test_provider_header(self) -> None:
        log = SyncLog()
        log.provider_header("Claude")
        assert len(log.infos) >= 2  # header + separator
        assert "Claude" in log.infos[-2]

    def test_write_output(self, temp_dir: Path) -> None:
        log = SyncLog()
        log.action("WRITE", "test.md", "source/test.md")
        log.warn("test warning")
        log.skip("skip.md", "disabled")

        log_path = temp_dir / "sync.log"
        log.write(log_path, "project.yaml", "0.1.0", "sync", [], dry_run=False)

        assert log_path.exists()
        content = log_path.read_text(encoding="utf-8")
        assert "WRITE" in content
        assert "test warning" in content
        assert "SKIP" in content

    def test_dry_run_does_not_write(self, temp_dir: Path) -> None:
        log = SyncLog()
        log.action("WRITE", "test.md", "source/test.md")

        log_path = temp_dir / "sync.log"
        log.write(log_path, "project.yaml", "0.1.0", "sync", [], dry_run=True)

        assert not log_path.exists()

    def test_empty_log_has_no_warnings_section(self, temp_dir: Path) -> None:
        log = SyncLog()
        log.action("WRITE", "test.md", "source")

        log_path = temp_dir / "sync.log"
        log.write(log_path, "project.yaml", "0.1.0", "sync", [], dry_run=False)

        content = log_path.read_text(encoding="utf-8")
        assert "(none)" in content
