"""Tests for scripts.lib.agents — frontmatter, composition, XML wrapping, collect_sources."""

from __future__ import annotations

import textwrap
from pathlib import Path

import pytest

from scripts.lib.agents import (
    extract_frontmatter_field,
    build_frontmatter,
    _split_frontmatter,
    _parse_frontmatter_yaml,
    _find_section_bounds,
    apply_patch,
    wrap_sections_in_xml,
    _make_xml_tag_name,
    collect_sources,
)
from scripts.lib.log import SyncLog


# ---------------------------------------------------------------------------
# _split_frontmatter
# ---------------------------------------------------------------------------


class TestSplitFrontmatter:
    def test_splits_valid_frontmatter(self) -> None:
        content = textwrap.dedent("""\
            ---
            name: test
            version: "1.0"
            ---
            ## Body
            Content here.
        """)
        fm, body = _split_frontmatter(content)
        assert "name: test" in fm
        assert "## Body" in body
        assert "Content here." in body

    def test_no_frontmatter(self) -> None:
        content = "Just a document\nNo frontmatter\n"
        fm, body = _split_frontmatter(content)
        assert fm == ""
        assert body == content

    def test_frontmatter_no_closing(self) -> None:
        content = "---\nname: test\nNo closing"
        fm, body = _split_frontmatter(content)
        assert fm == ""  # no closing --- found


# ---------------------------------------------------------------------------
# _parse_frontmatter_yaml
# ---------------------------------------------------------------------------


class TestParseFrontmatterYaml:
    def test_parses_valid_yaml(self) -> None:
        content = textwrap.dedent("""\
            ---
            name: test-agent
            version: "2.0"
            description: "A test agent"
            tools: [Read, Bash, Glob]
            ---
            Body
        """)
        fm = _parse_frontmatter_yaml(content)
        assert fm["name"] == "test-agent"
        assert fm["version"] == "2.0"
        assert fm["tools"] == ["Read", "Bash", "Glob"]

    def test_no_frontmatter_returns_empty(self) -> None:
        fm = _parse_frontmatter_yaml("No frontmatter")
        assert fm == {}


# ---------------------------------------------------------------------------
# extract_frontmatter_field
# ---------------------------------------------------------------------------


class TestExtractFrontmatterField:
    def test_extracts_name(self) -> None:
        content = "---\nname: test-agent\nversion: \"1.0\"\n---\nBody"
        name = extract_frontmatter_field(content, "name")
        assert name == "test-agent"

    def test_extracts_version(self) -> None:
        content = "---\nname: agent\nversion: \"3.2.1\"\n---\nBody"
        version = extract_frontmatter_field(content, "version")
        assert version == "3.2.1"

    def test_returns_none_for_missing_field(self) -> None:
        content = "---\nname: agent\n---\nBody"
        result = extract_frontmatter_field(content, "description")
        assert result is None

    def test_returns_string_for_list_field(self) -> None:
        """When PyYAML is available, list fields are stringified."""
        content = "---\nname: agent\ntools: [Read, Bash]\n---\nBody"
        result = extract_frontmatter_field(content, "tools")
        # With PyYAML, list returns str(list)
        assert "Read" in result
        assert "Bash" in result


# ---------------------------------------------------------------------------
# build_frontmatter
# ---------------------------------------------------------------------------


class TestBuildFrontmatter:
    def test_replaces_name_and_description(self) -> None:
        content = textwrap.dedent("""\
            ---
            name: old-name
            version: "1.0"
            description: "Old description"
            ---
            Body
        """)
        result = build_frontmatter(content, "new-name", "New description")
        fm = _parse_frontmatter_yaml(result)
        assert fm["name"] == "new-name"
        assert fm["description"] == "New description"
        # Preserved
        assert fm["version"] == "1.0"

    def test_strips_generated_from(self) -> None:
        content = textwrap.dedent("""\
            ---
            name: agent
            description: "desc"
            generated-from: old/path
            ---
            Body
        """)
        result = build_frontmatter(content, "agent", "desc")
        fm = _parse_frontmatter_yaml(result)
        assert "generated-from" not in fm
        assert "generated_from" not in fm


# ---------------------------------------------------------------------------
# _find_section_bounds
# ---------------------------------------------------------------------------


class TestFindSectionBounds:
    def test_finds_section(self) -> None:
        lines = [
            "## Section A\n",
            "Content A\n",
            "## Section B\n",
            "Content B\n",
        ]
        bounds = _find_section_bounds(lines, "## Section A")
        assert bounds is not None
        assert bounds == (0, 2)

    def test_finds_section_at_end(self) -> None:
        lines = [
            "## Only Section\n",
            "Last content\n",
        ]
        bounds = _find_section_bounds(lines, "## Only Section")
        assert bounds == (0, 2)

    def test_returns_none_for_missing(self) -> None:
        lines = ["## Section A\n", "Content\n"]
        bounds = _find_section_bounds(lines, "## Section X")
        assert bounds is None

    def test_respects_section_level(self) -> None:
        """Subsections (###) don't end parent sections."""
        lines = [
            "## Main\n",
            "main content\n",
            "### Sub\n",
            "sub content\n",
            "## Next\n",
            "next content\n",
        ]
        bounds = _find_section_bounds(lines, "## Main")
        assert bounds == (0, 4)  # ends at ## Next


# ---------------------------------------------------------------------------
# apply_patch
# ---------------------------------------------------------------------------


class TestApplyPatch:
    def test_append_operation(self) -> None:
        content = "Header\n\n## Section\nContent\n"
        log = SyncLog()
        result = apply_patch(
            content,
            {"op": "append", "content": "## Appendix\nExtra content\n"},
            log, "test",
        )
        assert "Appendix" in result
        assert result.startswith("Header")

    def test_append_after_operation(self) -> None:
        content = "## Section\nSection content\n\n## Next\nNext content\n"
        log = SyncLog()
        result = apply_patch(
            content,
            {"op": "append-after", "anchor": "## Section", "content": "## Extra\nExtra content\n"},
            log, "test",
        )
        lines = result.splitlines()
        # Find Section, then check Extra comes after it
        sec_idx = next(i for i, l in enumerate(lines) if l.strip() == "## Section")
        ext_idx = next(i for i, l in enumerate(lines) if l.strip() == "## Extra")
        assert ext_idx > sec_idx

    def test_replace_operation(self) -> None:
        content = "## Section\nOld content\n\n## Next\nNext content\n"
        log = SyncLog()
        result = apply_patch(
            content,
            {"op": "replace", "anchor": "## Section", "content": "## Section\nNew content\n"},
            log, "test",
        )
        assert "New content" in result
        assert "Old content" not in result

    def test_delete_operation(self) -> None:
        content = "## ToDelete\nBad content\n\n## Keep\nGood content\n"
        log = SyncLog()
        result = apply_patch(
            content,
            {"op": "delete", "anchor": "## ToDelete"},
            log, "test",
        )
        assert "Bad content" not in result
        assert "Good content" in result

    def test_unknown_op_warns(self) -> None:
        log = SyncLog()
        result = apply_patch("content", {"op": "invalid"}, log, "test")
        assert result == "content"
        assert len(log.warnings) == 1


# ---------------------------------------------------------------------------
# wrap_sections_in_xml
# ---------------------------------------------------------------------------


class TestWrapSectionsInXml:
    def test_wraps_headings_in_xml_tags(self) -> None:
        content = textwrap.dedent("""\
            # Title
            intro text
            ## Section One
            content one
            ## Section Two
            content two
        """)
        result = wrap_sections_in_xml(content)
        assert '<section name="section-one">' in result
        assert '</section>' in result
        assert '<section name="section-two">' in result

    def test_does_not_wrap_h3_headings(self) -> None:
        content = "## Main Section\ncontent\n### Sub Section\nsub content\n"
        result = wrap_sections_in_xml(content)
        assert '<section name="main-section">' in result
        assert '<section name="sub-section">' not in result

    def test_closes_sections(self) -> None:
        content = "## First\nfirst\n## Second\nsecond\n"
        result = wrap_sections_in_xml(content)
        # Count opening and closing tags
        assert result.count('<section') == 2
        assert result.count('</section>') == 2


class TestMakeXmlTagName:
    def test_lowercase_and_hyphens(self) -> None:
        assert _make_xml_tag_name("My Section Name") == "my-section-name"

    def test_removes_special_chars(self) -> None:
        assert _make_xml_tag_name("Hello! World?") == "hello-world"

    def test_collapses_multiple_hyphens(self) -> None:
        """Multiple spaces/hyphens collapse to single hyphen."""
        result = _make_xml_tag_name("A -- B")
        assert result == "a-b"


# ---------------------------------------------------------------------------
# collect_sources
# ---------------------------------------------------------------------------


class TestCollectSources:
    def test_collects_generic_agents(
        self, agent_meta_root: Path, sample_agent_template: Path,
    ) -> None:
        overrides, ext_roles = collect_sources(agent_meta_root, [])
        assert "test-agent" in overrides
        assert overrides["test-agent"].name == "test-agent.md"

    def test_excludes_underscore_files(self, agent_meta_root: Path) -> None:
        """Files starting with _ are skipped."""
        (agent_meta_root / "agents" / "1-generic" / "_internal.md").write_text(
            "---\nname: internal\n---\n", encoding="utf-8",
        )
        overrides, _ = collect_sources(agent_meta_root, [])
        assert "_internal" not in overrides

    def test_empty_generic_dir(self, temp_dir: Path) -> None:
        root = temp_dir / "empty-meta"
        root.mkdir()
        (root / "agents").mkdir()
        (root / "agents" / "1-generic").mkdir()
        (root / "agents" / "2-platform").mkdir()
        overrides, ext_roles = collect_sources(root, [])
        assert overrides == {}
