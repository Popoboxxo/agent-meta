"""Markdown adapter — writes SE requirements as Markdown files to docs/se/."""

import json
from pathlib import Path

from .base import SEAdapter


class MarkdownAdapter(SEAdapter):
    """Write each requirement to a Markdown file under *output_dir*.

    Directory layout::

        <output_dir>/
            index.md          ← Mermaid hierarchy graph + requirement list
            <req_id>.md       ← one file per requirement

    No external calls — pure filesystem operations.
    """

    def __init__(self, output_dir: str = "docs/se") -> None:
        self._output_path = Path(output_dir)
        self._output_path.mkdir(parents=True, exist_ok=True)
        # Track hierarchy for index generation: req_id → (title, parent_id)
        self._registry: dict[str, dict] = {}

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
        """Write a Markdown file for the requirement and record it in the registry.

        Returns:
            Relative file path of the written Markdown file (e.g. docs/se/REQ-L1.md).
        """
        safe_name = _safe_filename(req_id)
        file_path = self._output_path / f"{safe_name}.md"

        lines = [
            f"# {title}",
            "",
            f"**ID:** `{req_id}`",
        ]
        if parent_id:
            lines += [f"**Parent:** `{parent_id}`", ""]
        lines += [
            "",
            "## Description",
            "",
            description or "(no description provided)",
            "",
        ]

        file_path.write_text("\n".join(lines), encoding="utf-8")

        # Record for index
        self._registry[req_id] = {
            "title": title,
            "parent_id": parent_id,
            "file": str(file_path),
        }

        return str(file_path)

    def link_requirements(
        self,
        source_id: str,
        target_id: str,
        link_type: str,
    ) -> None:
        """Append a traceability link to the source requirement's Markdown file.

        Args:
            source_id: File path of the source requirement (as returned by
                       create_requirement).
            target_id: File path of the target requirement.
            link_type: Relationship label (e.g. "refines").
        """
        source_path = Path(source_id)
        if not source_path.exists():
            return

        target_name = Path(target_id).stem if Path(target_id).suffix else target_id
        link_line = f"- **{link_type}** → [{target_name}]({Path(target_id).name})"

        existing = source_path.read_text(encoding="utf-8")
        if "## Traceability" not in existing:
            existing += "\n## Traceability\n\n"
        existing += link_line + "\n"
        source_path.write_text(existing, encoding="utf-8")

    def update_status(self, req_id: str, status: str) -> None:
        """Append or replace a status badge in the requirement's Markdown file.

        Args:
            req_id: File path of the requirement (as returned by create_requirement).
            status: Lifecycle status string.
        """
        req_path = Path(req_id)
        if not req_path.exists():
            return

        existing = req_path.read_text(encoding="utf-8")
        status_line = f"**Status:** `{status}`"

        if "**Status:**" in existing:
            lines = existing.splitlines()
            updated = [
                status_line if line.startswith("**Status:**") else line
                for line in lines
            ]
            req_path.write_text("\n".join(updated), encoding="utf-8")
        else:
            # Insert after the first blank line following the header
            lines = existing.splitlines()
            inserted = False
            result = []
            for line in lines:
                result.append(line)
                if not inserted and line.startswith("**ID:**"):
                    result.append(status_line)
                    inserted = True
            if not inserted:
                result.append(status_line)
            req_path.write_text("\n".join(result), encoding="utf-8")

    def export_interface(self, interface: dict) -> str:
        """Write a CQRS interface contract as a Markdown file.

        Args:
            interface: Interface dict with at minimum a "name" key.

        Returns:
            Relative file path of the written interface Markdown file.
        """
        name: str = interface.get("name", "unknown-interface")
        safe_name = _safe_filename(name)
        file_path = self._output_path / f"iface-{safe_name}.md"

        lines = [
            f"# Interface: {name}",
            "",
            "## Details",
            "",
            "```json",
            json.dumps(interface, indent=2, ensure_ascii=False),
            "```",
            "",
        ]
        file_path.write_text("\n".join(lines), encoding="utf-8")
        return str(file_path)

    # ------------------------------------------------------------------
    # Index generation
    # ------------------------------------------------------------------

    def write_index(self) -> Path:
        """Generate index.md with a Mermaid hierarchy graph.

        Called automatically by export_graph (via the post-export hook).

        Returns:
            Path to the generated index.md.
        """
        index_path = self._output_path / "index.md"

        mermaid_lines = ["```mermaid", "graph TD"]
        link_lines: list[str] = []

        for req_id, meta in self._registry.items():
            safe_id = _mermaid_id(req_id)
            label = meta["title"].replace('"', "'")
            mermaid_lines.append(f'    {safe_id}["{label}"]')
            if meta["parent_id"]:
                # parent_id here is the *external* ID (file path), so we need
                # to find the matching req_id entry by file path.
                parent_req_id = _find_req_by_file(self._registry, meta["parent_id"])
                if parent_req_id:
                    link_lines.append(
                        f"    {_mermaid_id(parent_req_id)} --> {safe_id}"
                    )

        mermaid_lines += link_lines
        mermaid_lines.append("```")

        req_list = ["## Requirements", ""]
        for req_id, meta in self._registry.items():
            file_rel = Path(meta["file"]).name
            req_list.append(f"- [{meta['title']}]({file_rel}) — `{req_id}`")

        content_lines = (
            ["# SE Export Index", "", "## Hierarchy", ""]
            + mermaid_lines
            + [""]
            + req_list
            + [""]
        )
        index_path.write_text("\n".join(content_lines), encoding="utf-8")
        return index_path

    def export_graph(self, graph: dict) -> dict:
        """Export a full SE graph and write index.md afterwards."""
        result = super().export_graph(graph)
        self.write_index()
        return result


# ------------------------------------------------------------------
# Helpers
# ------------------------------------------------------------------

def _safe_filename(name: str) -> str:
    """Convert an arbitrary string to a safe filename stem."""
    return "".join(c if c.isalnum() or c in "-_." else "_" for c in name)


def _mermaid_id(req_id: str) -> str:
    """Convert req_id to a valid Mermaid node identifier."""
    return "".join(c if c.isalnum() else "_" for c in req_id)


def _find_req_by_file(registry: dict, file_path: str) -> str | None:
    """Reverse-lookup: find req_id whose file equals *file_path*."""
    for req_id, meta in registry.items():
        if meta["file"] == file_path:
            return req_id
    return None
