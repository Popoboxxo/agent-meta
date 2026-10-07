"""Scaffold docs/RELEASE_PROCESS.md from a distribution-specific template.

Analogous to ``scaffold_spec_plan_dirs`` in ``lib/spec_plan_scaffold.py``: when
the project declares a ``release.distribution`` in project.yaml, render the
matching ``templates/docs/RELEASE_PROCESS.<distribution>.md`` template and write
it to ``docs/RELEASE_PROCESS.md``.

The rendered body lives inside a managed block (same markers as the extension
files, ``lib/extensions.py``): a refresh replaces only the managed region, so
project-specific additions below the ``managed-end`` marker survive. An absent
``release`` section — or a ``release`` without ``distribution`` — is a no-op.
"""

from __future__ import annotations

from pathlib import Path

from .config import substitute
from .extensions import update_managed_block
from .io import safe_path, write_checked
from .log import SyncLog

TARGET = "docs/RELEASE_PROCESS.md"
_TEMPLATE_DIR = "templates/docs"
_MANAGED_BEGIN = "<!-- agent-meta:managed-begin -->"
_MANAGED_END = "<!-- agent-meta:managed-end -->"
_PROJECT_STUB_TEMPLATE_PATH = "templates/managed-block-project-stub.md"

# Sensible defaults so an unset-but-expected placeholder never leaks a raw
# {{...}} into the generated doc (which would also emit a sync warning).
_RELEASE_VAR_DEFAULTS = {
    "versioning": ("VERSIONING", "semver"),
    "changelog_format": ("CHANGELOG_FORMAT", "keep-a-changelog"),
    "version_file": ("VERSION_FILE", ""),
    "version_field": ("VERSION_FIELD", "version"),
}


def _load_project_stub(agent_meta_root: Path) -> str:
    """Load the never-managed project stub appended below the managed block."""
    template_path = agent_meta_root / _PROJECT_STUB_TEMPLATE_PATH
    if template_path.exists():
        return template_path.read_text(encoding="utf-8")
    return (
        "\n\n---\n\n"
        "## Projektspezifische Erweiterungen\n\n"
        "<!-- This section is NEVER modified by sync.py. -->\n"
        "<!-- Add project-specific knowledge, rules, and patterns here. -->\n"
    )


def _build_release_variables(variables: dict, release: dict) -> dict:
    """Overlay release-specific placeholders onto a copy of the base variables."""
    merged = dict(variables)
    merged["DISTRIBUTION"] = str(release.get("distribution", ""))
    for key, (placeholder, default) in _RELEASE_VAR_DEFAULTS.items():
        merged[placeholder] = str(release.get(key, default))
    return merged


def scaffold_release_process(agent_meta_root: Path, project_root: Path,
                            config: dict, variables: dict, log: SyncLog,
                            dry_run: bool) -> None:
    """Render docs/RELEASE_PROCESS.md from the distribution template (no-op if unset)."""
    release = config.get("release") or {}
    distribution = release.get("distribution")
    if not distribution:
        log.skip("release-process", "no release.distribution configured")
        return

    template_path = agent_meta_root / _TEMPLATE_DIR / f"RELEASE_PROCESS.{distribution}.md"
    if not template_path.exists():
        log.warning(
            f"release.distribution '{distribution}' has no template "
            f"({_TEMPLATE_DIR}/RELEASE_PROCESS.{distribution}.md) — skipping"
        )
        return

    body = substitute(
        template_path.read_text(encoding="utf-8"),
        _build_release_variables(variables, release),
        f"RELEASE_PROCESS.{distribution}.md",
        log,
    )
    managed = f"{_MANAGED_BEGIN}\n{body.rstrip()}\n{_MANAGED_END}"

    target = safe_path(project_root, TARGET)
    if target.exists():
        content = update_managed_block(target.read_text(encoding="utf-8"), managed)
    else:
        content = managed + _load_project_stub(agent_meta_root)

    if write_checked(target, content, log, TARGET, dry_run=dry_run):
        log.action("UPDATE", TARGET, f"release-process ({distribution})")
