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
