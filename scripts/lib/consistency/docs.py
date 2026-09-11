"""Documentation and UI cross-reference consistency checks."""

import re
from pathlib import Path

from .report import Finding, Severity


def check_sync_cli_docs(root: Path) -> list[Finding]:
    """Check that all argparse arguments in sync.py are documented in cli-reference.md."""
    findings = []
    sync_py = root / "scripts" / "sync.py"
    cli_ref = root / "docs" / "api" / "cli-reference.md"
    
    if not sync_py.exists() or not cli_ref.exists():
        return findings

    # Extract flags from sync.py
    flags = set()
    sync_content = sync_py.read_text(encoding="utf-8")
    for line in sync_content.splitlines():
        if "parser.add_argument(" in line:
            # Match flags like '"--config"' or "'--init'"
            matches = re.findall(r'["\'](--[a-zA-Z0-9-]+)["\']', line)
            flags.update(matches)
            
    # Extract documented flags from cli-reference.md
    ref_content = cli_ref.read_text(encoding="utf-8")
    doc_flags = set()
    for line in ref_content.splitlines():
        matches = re.findall(r'`(--[a-zA-Z0-9-]+)[^`]*`', line)
        doc_flags.update(matches)
        
    for flag in flags:
        if flag not in doc_flags and flag not in ("--help",):
            findings.append(Finding(
                severity=Severity.ERROR,
                check="docs.cli_reference",
                file="docs/api/cli-reference.md",
                message=f"CLI argument '{flag}' is not documented in cli-reference.md",
                suggestion=f"Add an entry for `{flag}` in the appropriate table."
            ))
            
    return findings


def check_ui_help_mappings(root: Path) -> list[Finding]:
    """Check that all routes in admin-ui.html routeMap have a valid help-id in admin-ui-reference.md."""
    findings = []
    admin_ui = root / "docs" / "ui" / "admin-ui.html"
    help_ref = root / "docs" / "api" / "admin-ui-reference.md"
    
    if not admin_ui.exists() or not help_ref.exists():
        return findings
        
    ui_content = admin_ui.read_text(encoding="utf-8")
    ref_content = help_ref.read_text(encoding="utf-8")
    
    # Parse routeMap from admin-ui.html
    route_map_block = re.search(r'const routeMap = \{([^}]+)\};', ui_content)
    if not route_map_block:
        findings.append(Finding(
            severity=Severity.ERROR,
            check="docs.ui_help_mappings",
            file="docs/ui/admin-ui.html",
            message="Could not parse 'routeMap' from admin-ui.html",
            suggestion="Ensure routeMap is a valid JS object literal."
        ))
        return findings
        
    # Extract help IDs expected by UI
    expected_help_ids = set()
    for line in route_map_block.group(1).splitlines():
        line = line.strip()
        if not line or line.startswith("//"): continue
        match = re.search(r'["\']([^"\']+)["\']\s*:\s*["\']([^"\']+)["\']', line)
        if match:
            expected_help_ids.add(match.group(2))
            
    # Extract available help IDs from Markdown
    available_help_ids = set()
    for line in ref_content.splitlines():
        if line.startswith("<!-- help-id: "):
            help_id = line.replace("<!-- help-id: ", "").replace(" -->", "").strip()
            available_help_ids.add(help_id)
            
    for help_id in expected_help_ids:
        if help_id not in available_help_ids:
            findings.append(Finding(
                severity=Severity.ERROR,
                check="docs.ui_help_mappings",
                file="docs/api/admin-ui-reference.md",
                message=f"UI route expects help-id '{help_id}', but it is missing in the documentation.",
                suggestion=f"Add `<!-- help-id: {help_id} -->` to admin-ui-reference.md."
            ))
            
    return findings


_PLAN_SECTION_PATTERNS = [
    re.compile(r'(?im)^#{1,6}\s*(?:Implementation\s+)?Plan\b'),
    re.compile(r'(?im)^#{1,6}\s*Step-by-Step\b'),
    re.compile(r'(?im)^#{1,6}\s*Step\s+\d+\s'),
    re.compile(r'(?m)^\s*pipeline_stages:\s*$'),
]


def check_requirements_no_plan_sections(root: Path) -> list[Finding]:
    """Check that docs/REQUIREMENTS.md carries no implementation-plan chapter.

    Fix for issue #677: REQUIREMENTS.md captures WHAT is needed, never
    HOW/WHEN it gets implemented. Ordered-step / agent-assignment /
    effort-estimate chapters (and the `pipeline_stages:` frontmatter field
    used by plan docs, see agents/1-generic/planner.md) belong to a separate
    document owned by `planner` (plan-<topic>.md or
    knowledge/wiki/plans/<topic>.md) -- see "Boundary to `planner`" in
    agents/1-generic/requirements.md. This was previously only a prose
    convention with nothing enforcing it structurally.
    """
    findings = []
    req_md = root / "docs" / "REQUIREMENTS.md"
    if not req_md.exists():
        return findings

    content = req_md.read_text(encoding="utf-8")
    for pattern in _PLAN_SECTION_PATTERNS:
        match = pattern.search(content)
        if match:
            line_no = content.count("\n", 0, match.start()) + 1
            findings.append(Finding(
                severity=Severity.WARNING,
                check="docs.requirements_no_plan_sections",
                file="docs/REQUIREMENTS.md",
                message=(
                    f"REQUIREMENTS.md:{line_no} looks like an implementation-plan "
                    f"chapter: {match.group(0).strip()!r}"
                ),
                suggestion=(
                    "Move implementation plans to a separate document owned by "
                    "`planner` (plan-<topic>.md or knowledge/wiki/plans/<topic>.md) "
                    "-- see 'Boundary to `planner`' in agents/1-generic/requirements.md."
                ),
            ))
            break  # one finding is enough signal, avoid duplicate noise per file

    return findings


def check_readme_docs_index(root: Path) -> list[Finding]:
    """Check that all markdown files in docs/api/ are linked in README.md."""
    findings = []
    readme = root / "README.md"
    docs_api_dir = root / "docs" / "api"
    
    if not readme.exists() or not docs_api_dir.exists():
        return findings
        
    readme_content = readme.read_text(encoding="utf-8")
    
    for md_file in docs_api_dir.glob("*.md"):
        rel_path = f"docs/api/{md_file.name}"
        if rel_path not in readme_content:
            findings.append(Finding(
                severity=Severity.ERROR,
                check="docs.readme_index",
                file="README.md",
                message=f"File '{rel_path}' is not linked in README.md",
                suggestion=f"Add a link to `[{md_file.stem}]({rel_path})` in the Documentation Index section."
            ))
            
    return findings
