"""Tests for the config audit module (scripts/lib/config_audit.py).

Covers:
- audit_config: roles_without_template, templates_without_default,
  deprecated_roles, orphaned_pipelines
- apply_audit: line-based commenting, comment preservation, idempotency
"""

from pathlib import Path

import pytest

from scripts.lib.config_audit import (
    AuditIssue,
    AuditReport,
    apply_audit,
    audit_config,
)

# ---------------------------------------------------------------------------
# Fixture: a minimal agent-meta root with templates + role-defaults + config
# ---------------------------------------------------------------------------

def _write(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


def _template(name: str, deprecated: bool = False) -> str:
    dep = "\ndeprecated: true" if deprecated else ""
    return (
        f"---\nname: template-{name}\nversion: \"1.0.0\"\n"
        f"description: \"{name} role.\"{dep}\n---\n\n# {name}\n"
    )


@pytest.fixture()
def meta_root(tmp_path: Path) -> Path:
    """Build a self-contained agent-meta root for auditing."""
    generic = tmp_path / "agents" / "1-generic"
    _write(generic / "developer.md", _template("developer"))
    _write(generic / "git.md", _template("git"))
    _write(generic / "old-role.md", _template("old-role", deprecated=True))
    # Underscore partial — must be ignored by templates_without_default.
    _write(generic / "_wf-shared.md", _template("wf-shared"))
    # Template present but listed in role-defaults below: developer, git.
    _write(
        tmp_path / "config" / "role-defaults.yaml",
        "roles:\n  developer:\n    model: powerful\n  git:\n    model: fast\n"
        "  old-role:\n    model: fast\n",
    )
    return tmp_path


def _config_path(tmp_path: Path, body: str) -> Path:
    path = tmp_path / ".meta-config" / "project.yaml"
    _write(path, body)
    return path


# ---------------------------------------------------------------------------
# audit_config
# ---------------------------------------------------------------------------

def test_roles_without_template(meta_root: Path) -> None:
    cfg = _config_path(
        meta_root,
        "roles:\n  - developer\n  - ghost-role\n",
    )
    report = audit_config(meta_root, cfg)
    missing = report.by_category("roles_without_template")
    assert len(missing) == 1
    assert missing[0].role == "ghost-role"
    assert missing[0].severity == "error"


def test_templates_without_default_ignores_underscore(meta_root: Path) -> None:
    cfg = _config_path(meta_root, "roles:\n  - developer\n")
    report = audit_config(meta_root, cfg)
    flagged = {i.role for i in report.by_category("templates_without_default")}
    # developer, git, old-role have defaults; _wf-shared is underscore → none.
    assert flagged == set()


def test_templates_without_default_detects_missing_entry(meta_root: Path) -> None:
    _write(
        meta_root / "agents" / "1-generic" / "lonely.md",
        _template("lonely"),
    )
    cfg = _config_path(meta_root, "roles:\n  - developer\n")
    report = audit_config(meta_root, cfg)
    flagged = {i.role for i in report.by_category("templates_without_default")}
    assert flagged == {"lonely"}
    assert report.by_category("templates_without_default")[0].severity == "info"


def test_templates_without_default_ignores_known_wrapper_templates(meta_root: Path) -> None:
    # Regression test for audit #415: provider-expert.md is a real template
    # file (unlike the underscore partials) but is intentionally never
    # instantiated as its own role -- it only serves as an `extends:` base
    # for claude-expert/gemini-expert/etc. It must not show up as a false
    # positive on every --audit-config run.
    _write(
        meta_root / "agents" / "1-generic" / "provider-expert.md",
        _template("provider-expert"),
    )
    cfg = _config_path(meta_root, "roles:\n  - developer\n")
    report = audit_config(meta_root, cfg)
    flagged = {i.role for i in report.by_category("templates_without_default")}
    assert "provider-expert" not in flagged


def test_deprecated_roles(meta_root: Path) -> None:
    cfg = _config_path(
        meta_root,
        "roles:\n  - developer\n  - old-role\n",
    )
    report = audit_config(meta_root, cfg)
    deprecated = report.by_category("deprecated_roles")
    assert len(deprecated) == 1
    assert deprecated[0].role == "old-role"
    assert deprecated[0].severity == "warning"
    assert report.deprecated_roles == ["old-role"]


def test_orphaned_pipelines(meta_root: Path) -> None:
    cfg = _config_path(
        meta_root,
        "roles:\n  - developer\n"
        "quality_pipelines:\n"
        "  feature:\n"
        "    stages:\n"
        "      - id: impl\n"
        "        agent: developer\n"
        "      - id: rev\n"
        "        agent: code-reviewer\n",
    )
    report = audit_config(meta_root, cfg)
    orphans = {i.role for i in report.by_category("orphaned_pipelines")}
    assert orphans == {"code-reviewer"}


def test_orphaned_pipelines_loop_refs(meta_root: Path) -> None:
    cfg = _config_path(
        meta_root,
        "roles:\n  - developer\n"
        "quality-pipelines:\n"
        "  overrides:\n"
        "    feature:\n"
        "      stages:\n"
        "        - id: rev\n"
        "          loop:\n"
        "            generator: developer\n"
        "            critic: secret-critic\n",
    )
    report = audit_config(meta_root, cfg)
    orphans = {i.role for i in report.by_category("orphaned_pipelines")}
    assert orphans == {"secret-critic"}


def _write_override(
    tmp_path: Path,
    name: str,
    based_on_role: str,
    based_on_version: str,
) -> None:
    _write(
        tmp_path / "agents" / "2-platform" / f"{name}.md",
        "---\n"
        f"name: {name}\n"
        "version: \"1.0.0\"\n"
        f"description: \"{name} override (test).\"\n"
        f"based-on: \"1-generic/{based_on_role}.md@{based_on_version}\"\n"
        "---\n\n# override\n",
    )


def test_stale_platform_override_detects_major_version_diff(meta_root: Path) -> None:
    # generic developer.md is 1.0.0 per _template() default; bump it to 4.0.1
    # to mirror the real-world issue #560 scenario (override pinned @2.3.0).
    _write(meta_root / "agents" / "1-generic" / "developer.md", _template("developer").replace('"1.0.0"', '"4.0.1"'))
    _write_override(meta_root, "homeassistant-developer", "developer", "2.3.0")
    cfg = _config_path(meta_root, "roles:\n  - developer\n")
    report = audit_config(meta_root, cfg)
    stale = report.by_category("stale_platform_overrides")
    assert len(stale) == 1
    assert stale[0].role == "homeassistant-developer"
    assert stale[0].severity == "warning"
    assert "2 major version(s) behind" in stale[0].message


def test_stale_platform_override_no_false_positive_same_major(meta_root: Path) -> None:
    """A pinned major version equal to the current generic major (patch/minor
    drift only) must not be reported -- only a 1+ major version gap is stale.
    """
    _write(meta_root / "agents" / "1-generic" / "developer.md", _template("developer").replace('"1.0.0"', '"4.0.1"'))
    _write_override(meta_root, "sharkord-developer", "developer", "4.0.0")
    cfg = _config_path(meta_root, "roles:\n  - developer\n")
    report = audit_config(meta_root, cfg)
    assert report.by_category("stale_platform_overrides") == []


def test_stale_platform_override_no_false_positive_matching_version(meta_root: Path) -> None:
    _write_override(meta_root, "agent-meta-developer", "developer", "1.0.0")
    cfg = _config_path(meta_root, "roles:\n  - developer\n")
    report = audit_config(meta_root, cfg)
    assert report.by_category("stale_platform_overrides") == []


def test_stale_platform_override_ignores_missing_generic_base(meta_root: Path) -> None:
    """A based-on reference to a nonexistent generic template is a different
    problem class (handled elsewhere) -- must not crash or be double-reported
    here.
    """
    _write_override(meta_root, "ghost-override", "ghost-role-that-does-not-exist", "1.0.0")
    cfg = _config_path(meta_root, "roles:\n  - developer\n")
    report = audit_config(meta_root, cfg)
    assert report.by_category("stale_platform_overrides") == []


def test_clean_config_has_no_issues(meta_root: Path) -> None:
    cfg = _config_path(meta_root, "roles:\n  - developer\n  - git\n")
    report = audit_config(meta_root, cfg)
    assert report.by_category("roles_without_template") == []
    assert report.by_category("deprecated_roles") == []
    assert report.by_category("orphaned_pipelines") == []


def test_based_on_multi_instance_roles_excluded(meta_root: Path) -> None:
    """Roles produced via ``based-on:`` from a 2-platform override must not
    be reported as ``roles_without_template`` — they share a base template
    (e.g. provider-expert.md) instead of having their own 1-generic file.
    """
    # Base template that serves as the multi-instance source.
    _write(
        meta_root / "agents" / "1-generic" / "provider-expert.md",
        _template("provider-expert"),
    )
    # 2-platform override generates two roles via based-on against the
    # provider-expert base. Frontmatter mirrors the real-world pattern
    # (name: "{{PREFIX}}<role>", based-on: "1-generic/<base>.md@<ver>").
    _write(
        meta_root / "agents" / "2-platform" / "agent-meta-claude-expert.md",
        "---\n"
        "name: \"{{PREFIX}}claude-expert\"\n"
        "version: 1.0.0\n"
        "description: \"Claude expert (test).\"\n"
        "based-on: \"1-generic/provider-expert.md@1.0.0\"\n"
        "---\n\n# claude-expert\n",
    )
    _write(
        meta_root / "agents" / "2-platform" / "agent-meta-gemini-expert.md",
        "---\n"
        "name: \"{{PREFIX}}gemini-expert\"\n"
        "version: 1.0.0\n"
        "description: \"Gemini expert (test).\"\n"
        "based-on: \"1-generic/provider-expert.md@1.0.0\"\n"
        "---\n\n# gemini-expert\n",
    )
    cfg = _config_path(
        meta_root,
        "roles:\n"
        "  - developer\n"
        "  - claude-expert\n"
        "  - gemini-expert\n"
        "  - ghost-role\n",
    )
    report = audit_config(meta_root, cfg)

    # claude-expert / gemini-expert must not show up — they are covered by
    # the provider-expert base via based-on. ghost-role still must.
    missing = {i.role for i in report.by_category("roles_without_template")}
    assert "claude-expert" not in missing
    assert "gemini-expert" not in missing
    assert missing == {"ghost-role"}


def test_unpaired_closing_tag_detected(meta_root: Path) -> None:
    # Copy-paste artifact from issue #567: a trailing `</output>` with no
    # matching `<output>` anywhere in the file.
    _write(
        meta_root / "agents" / "1-generic" / "developer.md",
        _template("developer") + "<persona>\ntext\n</persona>\n</output>\n",
    )
    cfg = _config_path(meta_root, "roles:\n  - developer\n  - git\n")
    report = audit_config(meta_root, cfg)
    unpaired = report.by_category("unpaired_closing_tags")
    assert len(unpaired) == 1
    assert unpaired[0].role == "developer"
    assert unpaired[0].severity == "error"
    assert "</output>" in unpaired[0].message
    assert "<output>" in unpaired[0].message


def test_unpaired_closing_tag_ignores_balanced_tags(meta_root: Path) -> None:
    _write(
        meta_root / "agents" / "1-generic" / "developer.md",
        _template("developer") + "<persona>\ntext\n</persona>\n",
    )
    cfg = _config_path(meta_root, "roles:\n  - developer\n  - git\n")
    report = audit_config(meta_root, cfg)
    assert report.by_category("unpaired_closing_tags") == []


def test_unpaired_closing_tag_ignores_inline_prose_and_placeholders(meta_root: Path) -> None:
    # Inline mentions (`` `<context>` `` mid-sentence) and tag-shaped output
    # placeholders (`<list>` as freeform example content) must never be
    # mistaken for real structural tags -- only a standalone closing line
    # with no standalone opening line anywhere is a genuine finding.
    _write(
        meta_root / "agents" / "1-generic" / "developer.md",
        _template("developer") + (
            "See `<context>` for details.\n"
            "### Affected components\n"
            "<list>\n"
        ),
    )
    cfg = _config_path(meta_root, "roles:\n  - developer\n  - git\n")
    report = audit_config(meta_root, cfg)
    assert report.by_category("unpaired_closing_tags") == []


def test_unpaired_closing_tag_scans_platform_overrides(meta_root: Path) -> None:
    _write(
        meta_root / "agents" / "2-platform" / "acme-developer.md",
        "---\nname: acme-developer\nversion: \"1.0.0\"\n"
        "description: \"ACME developer override.\"\n"
        "based-on: \"1-generic/developer.md@1.0.0\"\n---\n\n"
        "<persona>\ntext\n</persona>\n</output>\n",
    )
    cfg = _config_path(meta_root, "roles:\n  - developer\n  - git\n")
    report = audit_config(meta_root, cfg)
    unpaired = report.by_category("unpaired_closing_tags")
    assert len(unpaired) == 1
    assert unpaired[0].role == "acme-developer"


# ---------------------------------------------------------------------------
# provider_registry_completeness (issue #625)
# ---------------------------------------------------------------------------

def _write_ai_providers(meta_root: Path, provider_names: list[str]) -> None:
    body = "providers:\n" + "".join(f"  {name}: {{}}\n" for name in provider_names)
    _write(meta_root / "config" / "ai-providers.yaml", body)


def _write_lifecycle_check_stub(meta_root: Path, providers: list[str]) -> None:
    """A minimal stand-in for scripts/lifecycle_check.py's pending-tasks map,
    matching the exact construct shape the check's regex targets."""
    entries = "".join(f'    "{p}": ".{p.lower()}/pending-tasks.md",\n' for p in providers)
    _write(
        meta_root / "scripts" / "lifecycle_check.py",
        f"_PROVIDER_PENDING_FILES: dict[str, str] = {{\n{entries}}}\n",
    )


def test_provider_registry_completeness_detects_missing_provider(meta_root: Path) -> None:
    _write_ai_providers(meta_root, ["Claude", "Ghost"])
    _write_lifecycle_check_stub(meta_root, ["Claude"])  # "Ghost" missing
    cfg = _config_path(meta_root, "roles:\n  - developer\n")

    report = audit_config(meta_root, cfg)
    gaps = report.by_category("provider_registry_completeness")

    assert len(gaps) == 1
    assert gaps[0].role == "Ghost"
    assert gaps[0].severity == "warning"
    assert "_PROVIDER_PENDING_FILES" in gaps[0].message


def test_provider_registry_completeness_no_false_positive_when_complete(meta_root: Path) -> None:
    _write_ai_providers(meta_root, ["Claude", "Ghost"])
    _write_lifecycle_check_stub(meta_root, ["Claude", "Ghost"])  # both present
    cfg = _config_path(meta_root, "roles:\n  - developer\n")

    report = audit_config(meta_root, cfg)

    assert report.by_category("provider_registry_completeness") == []


# ---------------------------------------------------------------------------
# apply_audit
# ---------------------------------------------------------------------------

def test_apply_audit_comments_deprecated_role(meta_root: Path) -> None:
    cfg = _config_path(
        meta_root,
        "roles:\n  - developer  # keep me\n  - old-role\n  - git\n",
    )
    report = audit_config(meta_root, cfg)
    changed = apply_audit(report, cfg)
    assert changed == 1
    text = cfg.read_text(encoding="utf-8")
    assert "# - old-role  # AUTO-DISABLED" in text
    # Non-deprecated lines and their comments stay intact.
    assert "  - developer  # keep me\n" in text
    assert "  - git\n" in text


def test_apply_audit_idempotent(meta_root: Path) -> None:
    cfg = _config_path(
        meta_root,
        "roles:\n  - developer\n  - old-role\n",
    )
    report = audit_config(meta_root, cfg)
    first = apply_audit(report, cfg)
    after_first = cfg.read_text(encoding="utf-8")
    # Re-audit against the now-modified file and re-apply.
    report2 = audit_config(meta_root, cfg)
    second = apply_audit(report2, cfg)
    assert first == 1
    assert second == 0
    assert cfg.read_text(encoding="utf-8") == after_first


def test_apply_audit_no_deprecated_is_noop(meta_root: Path) -> None:
    cfg = _config_path(meta_root, "roles:\n  - developer\n  - git\n")
    report = audit_config(meta_root, cfg)
    before = cfg.read_text(encoding="utf-8")
    changed = apply_audit(report, cfg)
    assert changed == 0
    assert cfg.read_text(encoding="utf-8") == before


def test_apply_audit_preserves_unrelated_comments(meta_root: Path) -> None:
    body = (
        "# top comment\nroles:\n"
        "  - developer\n"
        "  - old-role\n"
        "# trailing comment\n"
    )
    cfg = _config_path(meta_root, body)
    report = audit_config(meta_root, cfg)
    apply_audit(report, cfg)
    text = cfg.read_text(encoding="utf-8")
    assert "# top comment\n" in text
    assert "# trailing comment\n" in text


# ---------------------------------------------------------------------------
# dataclass conveniences
# ---------------------------------------------------------------------------

def test_report_severity_properties() -> None:
    report = AuditReport()
    report.add("roles_without_template", "error", "x", "msg")
    report.add("deprecated_roles", "warning", "y", "msg")
    report.add("templates_without_default", "info", "z", "msg")
    assert report.has_issues is True
    assert [i.role for i in report.errors] == ["x"]
    assert [i.role for i in report.warnings] == ["y"]
    assert [i.role for i in report.infos] == ["z"]


def test_audit_issue_is_frozen() -> None:
    issue = AuditIssue("cat", "info", "role", "msg")
    with pytest.raises(Exception):  # noqa: B017
        issue.role = "other"  # type: ignore[misc]
