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

from scripts.lib.frontmatter import (
    FRONTMATTER_QUIET_STRIP_FIELDS,
    REFERENCE_STANDARDS_FIELD,
    build_frontmatter,
    parse_frontmatter_text,
    parse_reference_standards,
)
from scripts.lib.log import SyncLog
from scripts.lib.provider_transform import (
    _transform_frontmatter_for_opencode,
    transform_agent_content_for_provider,
)
from scripts.lib.providers import load_providers_config, registered_provider_names

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


def test_documenter_documents_plan_archive_target():
    text = (_REPO_ROOT / "agents" / "1-generic" / "documenter.md").read_text(encoding="utf-8")
    assert "docs/plans/archive" in text
    assert "plan-complete" in text


def test_explorer_documents_spike_mode():
    text = (_REPO_ROOT / "agents" / "1-generic" / "explorer.md").read_text(encoding="utf-8")
    assert "Spike-Modus" in text or "Spike mode" in text
    assert "docs/spikes/" in text
    assert "read-only" in text


def test_reference_standards_field_constant():
    # IC-01: the field name lives in one neutral constant, consumed by the
    # accessor, the quiet-strip set and the consistency check.
    assert REFERENCE_STANDARDS_FIELD == "reference_standards"


def test_parse_reference_standards_reads_raw_list():
    content = (
        "---\n"
        "name: template-code-reviewer\n"
        "reference_standards:\n"
        '  - "Diátaxis"\n'
        '  - "C4 model"\n'
        '  - "arc42"\n'
        "---\n"
        "\n"
        "Body content.\n"
    )
    assert parse_reference_standards(content) == ["Diátaxis", "C4 model", "arc42"]


def test_parse_reference_standards_absent_is_none():
    # Both a frontmatter block without the field and content without any
    # frontmatter yield None -- the field is optional (IC-01).
    assert parse_reference_standards(_sample_content()) is None
    assert parse_reference_standards("no frontmatter here\n") is None


def test_parse_reference_standards_scalar_value_is_returned_raw():
    # The bottom layer does no validation: a scalar comes back as-is (OQ-6).
    content = "---\nname: template-code-reviewer\nreference_standards: arc42\n---\n\nBody.\n"
    assert parse_reference_standards(content) == "arc42"


def test_parse_reference_standards_yaml_error_is_none():
    # A malformed frontmatter must never raise from the accessor.
    content = "---\nname: t\nreference_standards: [unterminated\n---\n\nBody.\n"
    assert parse_reference_standards(content) is None


def _sample_content_with_reference_standards():
    return (
        "---\n"
        "name: template-code-reviewer\n"
        'version: "1.2.2"\n'
        "description: old description\n"
        "prompt_mode: modern\n"
        "reference_standards:\n"
        '  - "arc42"\n'
        "tools:\n"
        "  - Read\n"
        "---\n"
        "\n"
        "Body content.\n"
    )


def test_build_frontmatter_quiet_fields_omitted_from_provenance():
    # AC-07: a quiet field is stripped and stays out of the provenance
    # comment; a loud field (version) is still recorded.
    content = build_frontmatter(
        _sample_content_with_reference_standards(), "code-reviewer", "new description",
        generated_from="1-generic/code-reviewer.md@1.2.2",
        strip_fields=["reference_standards", "version"],
        quiet_fields=FRONTMATTER_QUIET_STRIP_FIELDS,
    )
    fm = content.split("---")[1]
    body = content.split("---", 2)[2]
    assert "reference_standards" not in fm
    assert "reference_standards=" not in body
    assert "version=1.2.2" in body


def test_build_frontmatter_quiet_none_uses_default_set():
    # AC-07: quiet_fields=None applies FRONTMATTER_QUIET_STRIP_FIELDS.
    content = build_frontmatter(
        _sample_content_with_reference_standards(), "code-reviewer", "new description",
        generated_from="1-generic/code-reviewer.md@1.2.2",
        strip_fields=["reference_standards", "version"],
    )
    body = content.split("---", 2)[2]
    assert "reference_standards=" not in body
    assert "version=1.2.2" in body


def test_build_frontmatter_quiet_non_set_falls_back_loudly():
    # AC-07: a non-set (here: list) falls back to the regular loud path without
    # raising -- the quiet field is then named again.
    content = build_frontmatter(
        _sample_content_with_reference_standards(), "code-reviewer", "new description",
        generated_from="1-generic/code-reviewer.md@1.2.2",
        strip_fields=["reference_standards", "version"],
        quiet_fields=["reference_standards"],
    )
    body = content.split("---", 2)[2]
    assert "reference_standards=" in body
    assert "version=1.2.2" in body


def test_opencode_provenance_omits_quiet_fields():
    # AC-07, same matrix for the opencode-native builder.
    content = _transform_frontmatter_for_opencode(
        _sample_content_with_reference_standards(), "code-reviewer", "new description",
        model="", steps="", generated_from="1-generic/code-reviewer.md@1.2.2",
        agent_meta_root=_REPO_ROOT,
        strip_fields=["reference_standards", "version"],
    )
    fm = content.split("---")[1]
    body = content.split("---", 2)[2]
    assert "reference_standards" not in fm
    assert "reference_standards=" not in body
    assert "version=1.2.2" in body

    loud = _transform_frontmatter_for_opencode(
        _sample_content_with_reference_standards(), "code-reviewer", "new description",
        model="", steps="", generated_from="1-generic/code-reviewer.md@1.2.2",
        agent_meta_root=_REPO_ROOT,
        strip_fields=["reference_standards", "version"],
        quiet_fields=["reference_standards"],
    )
    assert "reference_standards=" in loud.split("---", 2)[2]


def test_existing_strip_channel_provenance_is_byte_identical():
    # AC-05: the existing strip channel keeps its exact provenance; the quiet
    # default is a no-op for every field outside FRONTMATTER_QUIET_STRIP_FIELDS.
    quiet_default = build_frontmatter(
        _sample_content(), "code-reviewer", "new description",
        generated_from="1-generic/code-reviewer.md@1.2.2",
        strip_fields=["version", "prompt_mode", "generated-from"],
    )
    explicit_loud = build_frontmatter(
        _sample_content(), "code-reviewer", "new description",
        generated_from="1-generic/code-reviewer.md@1.2.2",
        strip_fields=["version", "prompt_mode", "generated-from"],
        quiet_fields=frozenset(),
    )
    assert quiet_default == explicit_loud
    body = quiet_default.split("---", 2)[2]
    assert "version=1.2.2" in body
    assert "prompt_mode=modern" in body
    assert "generated-from=1-generic/code-reviewer.md@1.2.2" in body


# --- Task 5: end-to-end keep / existing-channel pins -----------------------

def _no_mechanism_providers() -> list[str]:
    _pc = load_providers_config(_REPO_ROOT)
    return [
        p for p in registered_provider_names(_REPO_ROOT)
        if not (((_pc.get(p) or {}).get("agent-transform") or {}).get("frontmatter-mechanism"))
    ]


def _render_for(provider, tmp_path, *, config=None, provider_config=None) -> str:
    return transform_agent_content_for_provider(
        _sample_content_with_reference_standards(), provider, "code-reviewer",
        "code-reviewer", "new description", "1-generic/code-reviewer.md@1.2.2",
        config if config is not None else {}, _REPO_ROOT, tmp_path,
        tmp_path / "agent.out",
        provider_config if provider_config is not None else load_providers_config(_REPO_ROOT),
        SyncLog(),
    )


def test_project_keep_channel_preserves_reference_standards(tmp_path):
    """AC-04: `frontmatter-keep-fields` keeps the field (value intact)."""
    provider = _no_mechanism_providers()[0]
    config = {"provider-options": {provider: {
        "frontmatter-keep-fields": [REFERENCE_STANDARDS_FIELD],
    }}}
    out = _render_for(provider, tmp_path, config=config)
    assert parse_frontmatter_text(out).get(REFERENCE_STANDARDS_FIELD) == ["arc42"]


def test_ai_providers_keep_channel_preserves_reference_standards(tmp_path):
    """AC-04: `frontmatter_keep_fields` (ai-providers channel) keeps it too."""
    pc = load_providers_config(_REPO_ROOT)
    provider = _no_mechanism_providers()[0]
    pc = dict(pc)
    pc[provider] = {**(pc.get(provider) or {}),
                    "frontmatter_keep_fields": [REFERENCE_STANDARDS_FIELD]}
    out = _render_for(provider, tmp_path, provider_config=pc)
    assert parse_frontmatter_text(out).get(REFERENCE_STANDARDS_FIELD) == ["arc42"]


def test_keep_wins_over_conflicting_strip_end_to_end(tmp_path):
    """AC-04: conflicting strip/keep across the two channels → keep wins;
    an unrelated provider stays stripped."""
    pc = load_providers_config(_REPO_ROOT)
    providers = _no_mechanism_providers()
    keep_provider, other_provider = providers[0], providers[1]
    pc = dict(pc)
    pc[keep_provider] = {**(pc.get(keep_provider) or {}),
                         "frontmatter_keep_fields": [REFERENCE_STANDARDS_FIELD]}
    conflicting = {"provider-options": {keep_provider: {
        "frontmatter-strip-fields": [REFERENCE_STANDARDS_FIELD],
    }}}
    kept = _render_for(keep_provider, tmp_path, config=conflicting, provider_config=pc)
    assert parse_frontmatter_text(kept).get(REFERENCE_STANDARDS_FIELD) == ["arc42"]

    other = _render_for(other_provider, tmp_path, config=conflicting, provider_config=pc)
    assert REFERENCE_STANDARDS_FIELD not in other


def test_existing_strip_channel_provenance_unchanged_by_new_default(tmp_path):
    """AC-05: the pre-existing bookkeeping strip channel keeps its
    byte-identical provenance; the new default adds no reference_standards
    token."""
    provider = _no_mechanism_providers()[0]
    config = {"provider-options": {provider: {
        "frontmatter-strip-fields": ["version", "prompt_mode", "generated-from"],
    }}}
    out = _render_for(provider, tmp_path, config=config)
    body = out.split("---", 2)[2]
    assert "version=1.2.2" in body
    assert "prompt_mode=modern" in body
    assert "generated-from=1-generic/code-reviewer.md@1.2.2" in body
    assert "reference_standards=" not in body
    assert REFERENCE_STANDARDS_FIELD not in out
