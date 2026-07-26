"""Tests for the SE export adapter package (scripts/lib/se_export/).

Covers:
- Factory: markdown / github_issues / unknown type
- MarkdownAdapter: creates per-requirement files and index.md with Mermaid
- GitHubIssuesAdapter: correct gh CLI arguments via monkeypatched subprocess.run
"""

import subprocess
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

from scripts.lib.se_export import GitHubIssuesAdapter, MarkdownAdapter, get_adapter

# ---------------------------------------------------------------------------
# Minimal SE graph fixture (conforms to se-decomposition.schema.json)
# ---------------------------------------------------------------------------

@pytest.fixture()
def minimal_graph() -> dict:
    return {
        "feature_id": "REQ-L1-SH-001",
        "stakeholder_requirement": "The system shall do something useful.",
        "l1_system": {
            "blackbox": "Top-level system requirement.",
            "whitebox": ["Subsystem A", "Subsystem B"],
        },
        "l2_subsystems": [
            {
                "subsystem_id": "REQ-L2-SH-001",
                "blackbox": "Subsystem A processes data.",
                "whitebox": ["Component X"],
            },
        ],
        "l3_components": [
            {
                "component_id": "REQ-XY-CP-001",
                "description": "Component X handles input parsing.",
                "refines": "REQ-L2-SH-001",
            },
        ],
        "cqrs_interfaces": {
            "commands": [
                {"name": "ProcessInput", "source": "Client", "target": "ComponentX"},
            ],
            "events": [],
            "queries": [],
        },
    }


# ===========================================================================
# Factory tests
# ===========================================================================

class TestGetAdapter:
    def test_markdown_returns_markdown_adapter(self, tmp_path: Path) -> None:
        config = {"type": "markdown", "output_dir": str(tmp_path)}
        adapter = get_adapter(config)
        assert isinstance(adapter, MarkdownAdapter)

    def test_github_issues_returns_github_adapter(self) -> None:
        config = {
            "type": "github_issues",
            "repo": "test-org/test-repo",
            "dry_run": True,  # prevent real gh auth check
        }
        adapter = get_adapter(config)
        assert isinstance(adapter, GitHubIssuesAdapter)

    def test_unknown_type_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown se-export adapter type"):
            get_adapter({"type": "jira"})

    def test_empty_type_raises_value_error(self) -> None:
        with pytest.raises(ValueError, match="Unknown se-export adapter type"):
            get_adapter({})

    def test_markdown_uses_default_output_dir(self, tmp_path: Path, monkeypatch: Any) -> None:
        # Patch Path.mkdir to avoid actually creating docs/se in the repo
        monkeypatch.chdir(tmp_path)
        adapter = get_adapter({"type": "markdown"})
        assert isinstance(adapter, MarkdownAdapter)


# ===========================================================================
# MarkdownAdapter tests
# ===========================================================================

class TestMarkdownAdapter:
    def test_creates_requirement_file(self, tmp_path: Path) -> None:
        adapter = MarkdownAdapter(output_dir=str(tmp_path))
        ext_id = adapter.create_requirement(
            req_id="REQ-L1-001",
            title="[L1] Top Level",
            description="This is the top-level system requirement.",
        )
        written = Path(ext_id)
        assert written.exists(), f"Expected file at {ext_id}"
        content = written.read_text(encoding="utf-8")
        assert "REQ-L1-001" in content
        assert "Top Level" in content
        assert "top-level system requirement" in content

    def test_creates_file_with_parent_reference(self, tmp_path: Path) -> None:
        adapter = MarkdownAdapter(output_dir=str(tmp_path))
        parent_path = adapter.create_requirement(
            req_id="REQ-L1-001",
            title="Parent",
            description="Parent requirement.",
        )
        child_path = adapter.create_requirement(
            req_id="REQ-L2-001",
            title="Child",
            description="Child requirement.",
            parent_id=parent_path,
        )
        content = Path(child_path).read_text(encoding="utf-8")
        assert "Parent" in content

    def test_write_index_creates_index_md(self, tmp_path: Path) -> None:
        adapter = MarkdownAdapter(output_dir=str(tmp_path))
        adapter.create_requirement("REQ-L1-001", "[L1] Root", "Root desc.")
        adapter.create_requirement("REQ-L2-001", "[L2] Sub", "Sub desc.")
        index_path = adapter.write_index()
        assert index_path.exists()
        content = index_path.read_text(encoding="utf-8")
        assert "```mermaid" in content
        assert "graph TD" in content
        assert "Requirements" in content

    def test_export_graph_produces_files_and_index(
        self, tmp_path: Path, minimal_graph: dict
    ) -> None:
        adapter = MarkdownAdapter(output_dir=str(tmp_path))
        id_map = adapter.export_graph(minimal_graph)

        # index.md must exist
        index_path = tmp_path / "index.md"
        assert index_path.exists(), "index.md was not created"

        index_content = index_path.read_text(encoding="utf-8")
        assert "```mermaid" in index_content
        assert "graph TD" in index_content

        # All req IDs must be in the id_map
        assert "REQ-L1-SH-001" in id_map
        assert "REQ-L2-SH-001" in id_map
        assert "REQ-XY-CP-001" in id_map
        # Interface was exported too
        assert "ProcessInput" in id_map

    def test_export_graph_files_exist(
        self, tmp_path: Path, minimal_graph: dict
    ) -> None:
        adapter = MarkdownAdapter(output_dir=str(tmp_path))
        id_map = adapter.export_graph(minimal_graph)

        for req_id, file_path in id_map.items():
            if req_id == "ProcessInput":
                # Interfaces are stored as iface-*.md
                continue
            assert Path(file_path).exists(), f"Missing file for {req_id}: {file_path}"

    def test_link_requirements_appends_traceability(self, tmp_path: Path) -> None:
        adapter = MarkdownAdapter(output_dir=str(tmp_path))
        src_id = adapter.create_requirement("REQ-A", "Req A", "Source req.")
        tgt_id = adapter.create_requirement("REQ-B", "Req B", "Target req.")
        adapter.link_requirements(src_id, tgt_id, "refines")

        content = Path(src_id).read_text(encoding="utf-8")
        assert "Traceability" in content
        assert "refines" in content

    def test_update_status_writes_status(self, tmp_path: Path) -> None:
        adapter = MarkdownAdapter(output_dir=str(tmp_path))
        req_path = adapter.create_requirement("REQ-STATUS", "Status Test", "Test req.")
        adapter.update_status(req_path, "approved")

        content = Path(req_path).read_text(encoding="utf-8")
        assert "approved" in content

    def test_mermaid_contains_node_labels(
        self, tmp_path: Path, minimal_graph: dict
    ) -> None:
        adapter = MarkdownAdapter(output_dir=str(tmp_path))
        adapter.export_graph(minimal_graph)
        index_content = (tmp_path / "index.md").read_text(encoding="utf-8")
        # At least the L1 node should appear as a Mermaid node
        assert "REQ_L1_SH_001" in index_content or "L1" in index_content


# ===========================================================================
# GitHubIssuesAdapter tests (subprocess.run monkeypatched)
# ===========================================================================

def _make_fake_run(issue_url: str = "https://github.com/test-org/test-repo/issues/42"):
    """Return a fake subprocess.run that returns *issue_url* on stdout."""
    def _fake_run(cmd, **kwargs):
        mock_result = MagicMock(spec=subprocess.CompletedProcess)
        mock_result.returncode = 0
        mock_result.stdout = issue_url + "\n"
        mock_result.stderr = ""
        return mock_result

    return _fake_run


class TestGitHubIssuesAdapter:
    """Tests use dry_run=False but monkeypatch subprocess.run."""

    _CONFIG = {  # noqa: RUF012
        "type": "github_issues",
        "repo": "test-org/test-repo",
        "milestone": "v1.0",
        "labels": {
            "l1": "se:l1",
            "l2": "se:l2",
            "l3": "se:l3",
            "leaf": "se:leaf",
        },
    }

    @pytest.fixture()
    def adapter(self, monkeypatch: Any) -> GitHubIssuesAdapter:
        """Create adapter with subprocess.run patched out entirely."""
        fake_run = _make_fake_run()
        monkeypatch.setattr(subprocess, "run", fake_run)
        return GitHubIssuesAdapter(config=self._CONFIG)

    def test_create_requirement_calls_gh_issue_create(
        self, monkeypatch: Any
    ) -> None:
        captured: list[list[str]] = []

        def _fake_run(cmd, **kwargs):
            captured.append(list(cmd))
            result = MagicMock()
            result.returncode = 0
            result.stdout = "https://github.com/test-org/test-repo/issues/42\n"
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", _fake_run)
        adapter = GitHubIssuesAdapter(config=self._CONFIG)

        ext_id = adapter.create_requirement(
            req_id="REQ-L1-SH-001",
            title="Top Level System",
            description="System must do X.",
        )

        # Find the issue create call (auth status is also captured)
        create_calls = [c for c in captured if "issue" in c and "create" in c]
        assert len(create_calls) == 1, f"Expected 1 create call, got: {create_calls}"

        create_cmd = create_calls[0]
        assert "gh" in create_cmd
        assert "issue" in create_cmd
        assert "create" in create_cmd
        assert "--repo" in create_cmd
        assert "test-org/test-repo" in create_cmd
        assert "--title" in create_cmd
        # ext_id is the returned issue URL
        assert ext_id == "https://github.com/test-org/test-repo/issues/42"

    def test_create_requirement_uses_l1_label_for_l1_req(
        self, monkeypatch: Any
    ) -> None:
        captured: list[list[str]] = []

        def _fake_run(cmd, **kwargs):
            captured.append(list(cmd))
            result = MagicMock()
            result.returncode = 0
            result.stdout = "https://github.com/test-org/test-repo/issues/10\n"
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", _fake_run)
        adapter = GitHubIssuesAdapter(config=self._CONFIG)

        adapter.create_requirement("REQ-L1-SH-001", "L1 Req", "Description.")

        create_cmd = next(
            c for c in captured if "issue" in c and "create" in c
        )
        flat = " ".join(create_cmd)
        assert "se:l1" in flat, f"Expected 'se:l1' label in: {flat}"
        assert "se:system" in flat, f"Expected 'se:system' label in: {flat}"

    def test_create_requirement_uses_l2_label_for_l2_req(
        self, monkeypatch: Any
    ) -> None:
        captured: list[list[str]] = []

        def _fake_run(cmd, **kwargs):
            captured.append(list(cmd))
            result = MagicMock()
            result.returncode = 0
            result.stdout = "https://github.com/test-org/test-repo/issues/11\n"
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", _fake_run)
        adapter = GitHubIssuesAdapter(config=self._CONFIG)

        adapter.create_requirement("REQ-L2-SH-001", "L2 Subsystem", "Subsystem desc.")

        create_cmd = next(
            c for c in captured if "issue" in c and "create" in c
        )
        flat = " ".join(create_cmd)
        assert "se:l2" in flat, f"Expected 'se:l2' label in: {flat}"

    def test_create_requirement_uses_l3_label_for_component(
        self, monkeypatch: Any
    ) -> None:
        captured: list[list[str]] = []

        def _fake_run(cmd, **kwargs):
            captured.append(list(cmd))
            result = MagicMock()
            result.returncode = 0
            result.stdout = "https://github.com/test-org/test-repo/issues/12\n"
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", _fake_run)
        adapter = GitHubIssuesAdapter(config=self._CONFIG)

        adapter.create_requirement("REQ-XY-CP-001", "L3 Component", "Component desc.")

        create_cmd = next(
            c for c in captured if "issue" in c and "create" in c
        )
        flat = " ".join(create_cmd)
        assert "se:l3" in flat, f"Expected 'se:l3' label in: {flat}"

    def test_link_requirements_calls_gh_issue_comment(
        self, monkeypatch: Any
    ) -> None:
        captured: list[list[str]] = []

        def _fake_run(cmd, **kwargs):
            captured.append(list(cmd))
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", _fake_run)
        adapter = GitHubIssuesAdapter(config=self._CONFIG)

        adapter.link_requirements(
            source_id="https://github.com/test-org/test-repo/issues/1",
            target_id="https://github.com/test-org/test-repo/issues/2",
            link_type="refines",
        )

        comment_calls = [c for c in captured if "comment" in c]
        assert len(comment_calls) == 1
        flat = " ".join(comment_calls[0])
        assert "refines" in flat

    def test_update_status_closes_issue_when_implemented(
        self, monkeypatch: Any
    ) -> None:
        captured: list[list[str]] = []

        def _fake_run(cmd, **kwargs):
            captured.append(list(cmd))
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", _fake_run)
        adapter = GitHubIssuesAdapter(config=self._CONFIG)

        adapter.update_status(
            req_id="https://github.com/test-org/test-repo/issues/5",
            status="implemented",
        )

        close_calls = [c for c in captured if "close" in c]
        assert len(close_calls) == 1, f"Expected close call, got: {captured}"

    def test_gh_not_authenticated_raises_runtime_error(
        self, monkeypatch: Any
    ) -> None:
        def _fake_run_auth_fail(cmd, **kwargs):
            result = MagicMock()
            result.returncode = 1
            result.stdout = ""
            result.stderr = "not logged in"
            return result

        monkeypatch.setattr(subprocess, "run", _fake_run_auth_fail)
        with pytest.raises(RuntimeError, match="not authenticated"):
            GitHubIssuesAdapter(config=self._CONFIG)

    def test_gh_not_found_raises_runtime_error(self, monkeypatch: Any) -> None:
        def _fake_run_not_found(cmd, **kwargs):
            raise FileNotFoundError("gh not found")

        monkeypatch.setattr(subprocess, "run", _fake_run_not_found)
        with pytest.raises(RuntimeError, match="gh CLI not found"):
            GitHubIssuesAdapter(config=self._CONFIG)

    def test_dry_run_skips_gh_calls(self, monkeypatch: Any) -> None:
        captured: list[list[str]] = []

        def _fake_run(cmd, **kwargs):
            captured.append(list(cmd))
            result = MagicMock()
            result.returncode = 0
            result.stdout = ""
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", _fake_run)
        config = {**self._CONFIG, "dry_run": True}
        adapter = GitHubIssuesAdapter(config=config)

        ext_id = adapter.create_requirement("REQ-L1-001", "Title", "Desc.")

        # No subprocess calls should have been made at all in dry_run mode
        assert len(captured) == 0, f"Expected no gh calls in dry_run, got: {captured}"
        assert "[dry-run]" in ext_id

    def test_export_interface_calls_gh_issue_create(
        self, monkeypatch: Any
    ) -> None:
        captured: list[list[str]] = []

        def _fake_run(cmd, **kwargs):
            captured.append(list(cmd))
            result = MagicMock()
            result.returncode = 0
            result.stdout = "https://github.com/test-org/test-repo/issues/99\n"
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", _fake_run)
        adapter = GitHubIssuesAdapter(config=self._CONFIG)

        iface = {"name": "ProcessInput", "source": "A", "target": "B"}
        ext_id = adapter.export_interface(iface)

        create_calls = [c for c in captured if "create" in c]
        assert len(create_calls) == 1
        flat = " ".join(create_calls[0])
        assert "se:interface" in flat
        assert ext_id == "https://github.com/test-org/test-repo/issues/99"

    def test_milestone_included_in_create_command(self, monkeypatch: Any) -> None:
        captured: list[list[str]] = []

        def _fake_run(cmd, **kwargs):
            captured.append(list(cmd))
            result = MagicMock()
            result.returncode = 0
            result.stdout = "https://github.com/test-org/test-repo/issues/1\n"
            result.stderr = ""
            return result

        monkeypatch.setattr(subprocess, "run", _fake_run)
        adapter = GitHubIssuesAdapter(config=self._CONFIG)

        adapter.create_requirement("REQ-L1-001", "Title", "Desc.")
        create_cmd = next(c for c in captured if "create" in c)
        flat = " ".join(create_cmd)
        assert "--milestone" in flat
        assert "v1.0" in flat
