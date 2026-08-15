"""Regression tests for build_frontmatter()'s provider-aware field stripping.

Background: issue #505 — some providers (e.g. a strict Console Go validation
layer sitting in front of an Opencode-shaped agent schema) reject generated
agent frontmatter outright when it carries agent-meta's own bookkeeping
fields (`version`, `prompt_mode`, `generated-from`) that aren't part of the
provider's own schema. `build_frontmatter()` gained an opt-in `strip_fields`
parameter so a provider can be configured to omit those fields, with their
values preserved in an HTML comment so traceability/version-bump enforcement
(Hard Invariant #2) isn't lost.
"""

from pathlib import Path

from scripts.lib.agents import (
    _transform_frontmatter_for_opencode,
    build_frontmatter,
    transform_agent_content_for_provider,
)
from scripts.lib.log import SyncLog

_REPO_ROOT = Path(__file__).resolve().parents[1]


def _sample_content():
    return (
        "---\n"
        "name: template-code-reviewer\n"
        'version: "1.2.2"\n'
        "description: old description\n"
        "prompt_mode: modern\n"
        "tools:\n"
        "  - Read\n"
        "---\n"
        "\n"
        "Body content.\n"
    )


def test_build_frontmatter_no_strip_fields_keeps_existing_behavior():
    content = build_frontmatter(
        _sample_content(), "code-reviewer", "new description",
        generated_from="1-generic/code-reviewer.md@1.2.2",
    )
    assert "version:" in content
    assert "prompt_mode:" in content
    assert "generated-from: 1-generic/code-reviewer.md@1.2.2" in content
    assert "agent-meta-provenance" not in content


def test_build_frontmatter_strip_fields_removes_listed_keys():
    content = build_frontmatter(
        _sample_content(), "code-reviewer", "new description",
        generated_from="1-generic/code-reviewer.md@1.2.2",
        strip_fields=["version", "prompt_mode", "generated-from"],
    )
    fm = content.split("---")[1]
    assert "version:" not in fm
    assert "prompt_mode:" not in fm
    assert "generated-from:" not in fm
    # name/description must still be updated as normal
    assert "name: code-reviewer" in fm
    assert "description: new description" in fm


def test_build_frontmatter_strip_fields_preserves_provenance_comment():
    content = build_frontmatter(
        _sample_content(), "code-reviewer", "new description",
        generated_from="1-generic/code-reviewer.md@1.2.2",
        strip_fields=["version", "prompt_mode", "generated-from"],
    )
    body = content.split("---", 2)[2]
    assert "agent-meta-provenance" in body
    assert "version=1.2.2" in body
    assert "prompt_mode=modern" in body
    assert "generated-from=1-generic/code-reviewer.md@1.2.2" in body


def test_build_frontmatter_strip_fields_only_mentions_present_fields():
    # The source content has no 'based-on' field -- stripping a field that
    # was never present must not fabricate a bogus provenance entry for it.
    content = build_frontmatter(
        _sample_content(), "code-reviewer", "new description",
        generated_from=None,
        strip_fields=["version", "prompt_mode", "based-on"],
    )
    body = content.split("---", 2)[2]
    assert "based-on=" not in body
    assert "version=1.2.2" in body


def _opencode_sample_content():
    return (
        "---\n"
        "name: template-code-reviewer\n"
        'version: "1.2.2"\n'
        "description: old description\n"
        "prompt_mode: modern\n"
        "tools:\n"
        "  - Read\n"
        "---\n"
        "\n"
        "Body content.\n"
    )


def test_transform_frontmatter_for_opencode_no_strip_fields_keeps_existing_behavior():
    # Regression guard for issue #505: without strip_fields configured
    # (the default for every provider today), the previously-reported
    # fields keep flowing through unchanged -- prompt_mode was never
    # explicitly touched by this function, only implicitly inherited.
    content = _transform_frontmatter_for_opencode(
        _opencode_sample_content(), "code-reviewer", "new description",
        model="", steps="", generated_from="1-generic/code-reviewer.md@1.2.2",
        agent_meta_root=_REPO_ROOT,
    )
    assert "version:" in content
    assert "prompt_mode:" in content
    assert "generated-from:" in content
    assert "agent-meta-provenance" not in content


def test_transform_frontmatter_for_opencode_strip_fields_removes_listed_keys():
    content = _transform_frontmatter_for_opencode(
        _opencode_sample_content(), "code-reviewer", "new description",
        model="", steps="", generated_from="1-generic/code-reviewer.md@1.2.2",
        agent_meta_root=_REPO_ROOT,
        strip_fields=["version", "prompt_mode", "generated-from"],
    )
    fm = content.split("---")[1]
    assert "version:" not in fm
    assert "prompt_mode:" not in fm
    assert "generated-from:" not in fm
    assert "name: code-reviewer" in fm
    assert "mode: subagent" in fm


def test_transform_frontmatter_for_opencode_strip_fields_preserves_provenance():
    content = _transform_frontmatter_for_opencode(
        _opencode_sample_content(), "code-reviewer", "new description",
        model="", steps="", generated_from="1-generic/code-reviewer.md@1.2.2",
        agent_meta_root=_REPO_ROOT,
        strip_fields=["version", "prompt_mode", "generated-from"],
    )
    body = content.split("---", 2)[2]
    assert "agent-meta-provenance" in body
    assert "version=1.2.2" in body
    assert "prompt_mode=modern" in body
    assert "generated-from=1-generic/code-reviewer.md@1.2.2" in body


def test_transform_agent_content_reads_strip_fields_from_project_provider_options(tmp_path):
    # End-to-end regression guard for issue #505: a consumer project must be
    # able to opt into frontmatter stripping for its own Opencode/Console-Go
    # setup via .meta-config/project.yaml's existing `provider-options`
    # block -- the same project-level mechanism Continue's
    # generate-prompts/prompt-mode already use -- without any agent-meta
    # core change per consumer quirk.
    config = {
        "provider-options": {
            "Opencode": {"frontmatter-strip-fields": ["version", "prompt_mode", "generated-from"]},
        },
    }
    content = transform_agent_content_for_provider(
        _opencode_sample_content(), "Opencode", "code-reviewer", "code-reviewer",
        "new description", "1-generic/code-reviewer.md@1.2.2", config,
        _REPO_ROOT, tmp_path, tmp_path / "code-reviewer.md", {}, SyncLog(),
    )
    fm = content.split("---")[1]
    assert "version:" not in fm
    assert "prompt_mode:" not in fm
    assert "generated-from:" not in fm
    assert "agent-meta-provenance" in content


def test_build_frontmatter_strip_fields_empty_list_is_noop():
    content_stripped_empty = build_frontmatter(
        _sample_content(), "code-reviewer", "new description",
        generated_from="1-generic/code-reviewer.md@1.2.2",
        strip_fields=[],
    )
    content_default = build_frontmatter(
        _sample_content(), "code-reviewer", "new description",
        generated_from="1-generic/code-reviewer.md@1.2.2",
    )
    assert content_stripped_empty == content_default
