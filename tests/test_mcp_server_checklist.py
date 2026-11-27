"""T34 / #1274: checklist test for every server in the unified plugin catalog.

``config/plugin-catalog.yaml`` is the SSOT: every registered server must be
complete, routed through the ``lazy`` preset as a Skill, actually rendered by
sync, covered by the always-on guardrail (when it has blocked tools) and pass
the #1262 URL/secret validation.

The catalog holds two server kinds with different generated stems:

* ``kind: mcp-server`` -> ``<skills_dir>/mcp-<server>/SKILL.md``
* ``kind: cli-tool``   -> ``<skills_dir>/tool-<name>/SKILL.md``

The test discovers both from the catalog instead of hardcoding a server list,
so a new registry entry fails with its own name until it is fully wired.

Run: python3 -m pytest tests/test_mcp_server_checklist.py -q
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

import pytest
import yaml

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lib.config import load_config  # noqa: E402
from lib.external_tools import generate_external_tool_artifacts  # noqa: E402
from lib.log import SyncLog  # noqa: E402
from lib.mcp import generate_mcp_artifacts  # noqa: E402
from lib.mcp_health import SEVERITY_ERROR, validate_mcp_health  # noqa: E402
from lib.providers import load_providers_config  # noqa: E402
from lib.registry_query import (  # noqa: E402
    build_mcp_guardrails_list,
    load_plugin_catalog,
)

CATALOG = load_plugin_catalog(REPO_ROOT)
SERVER_NAMES = sorted(CATALOG)
MCP_SERVERS = [name for name in SERVER_NAMES if CATALOG[name].get("kind") == "mcp-server"]
PROVIDER = "Claude"
SKILL_DESCRIPTION_LINK = "config/plugin-catalog.yaml"
PLACEHOLDER_RE = re.compile(r"\{\{([A-Z0-9_]+)\}\}")


def _stem_for(name: str, entry: dict) -> str:
    """Return the generated rule stem for one catalog server."""
    kind = (entry or {}).get("kind")
    if kind == "mcp-server":
        return f"mcp-{name}"
    if kind == "cli-tool":
        return f"tool-{name}"
    raise AssertionError(
        f"server '{name}': unsupported catalog kind {kind!r} — expected "
        "'mcp-server' or 'cli-tool'"
    )


def _skill_stem(name: str) -> str:
    return _stem_for(name, CATALOG.get(name, {}))


def _entry_problems(name: str, entry: dict) -> list[str]:
    """Structural completeness problems for one catalog entry."""
    if not isinstance(entry, dict):
        return [f"server '{name}': catalog entry is not a mapping"]

    problems: list[str] = []
    kind = entry.get("kind")
    if kind not in ("mcp-server", "cli-tool"):
        problems.append(
            f"server '{name}': unsupported kind {kind!r} "
            "(expected 'mcp-server' or 'cli-tool')"
        )
        return problems

    for key in ("description", "category", "origin-type"):
        if not str(entry.get(key) or "").strip():
            problems.append(f"server '{name}': catalog field '{key}' is missing")

    if kind == "mcp-server":
        if not isinstance(entry.get("tools"), dict):
            problems.append(f"server '{name}': catalog field 'tools' is missing")
        connection = entry.get("connection")
        if not isinstance(connection, dict) or connection.get("type") not in (
            "sse",
            "stdio",
        ):
            problems.append(
                f"server '{name}': catalog field 'connection.type' must be "
                "'sse' or 'stdio'"
            )
        else:
            declared = set(entry.get("secrets") or [])
            referenced = set(PLACEHOLDER_RE.findall(yaml.safe_dump(connection)))
            undeclared = sorted(referenced - declared)
            if undeclared:
                problems.append(
                    f"server '{name}': connection placeholders not declared "
                    f"under 'secrets': {', '.join(undeclared)}"
                )
    elif not (
        entry.get("binary") or entry.get("rule-content") or entry.get("hooks")
    ):
        problems.append(
            f"server '{name}': cli-tool entry needs 'binary', 'rule-content' "
            "or 'hooks'"
        )

    return problems


def _preset_problems(name: str, presets: dict, entry: dict) -> list[str]:
    """Problems with the lazy-preset Skill routing for one server."""
    stem = _stem_for(name, entry)
    lazy = presets.get("lazy") or {}
    opts = lazy.get(stem)
    if not isinstance(opts, dict):
        return [f"server '{name}': lazy preset entry '{stem}' is missing"]

    problems: list[str] = []
    if opts.get("channel") != "skill":
        problems.append(
            f"server '{name}': lazy preset entry '{stem}' must set "
            "'channel: skill'"
        )
    description = str(opts.get("skill-description") or "").strip()
    if not description:
        problems.append(
            f"server '{name}': lazy preset entry '{stem}' has no "
            "'skill-description'"
        )
    else:
        if not description.lower().startswith("use when"):
            problems.append(
                f"server '{name}': skill-description must start with 'Use when'"
            )
        if SKILL_DESCRIPTION_LINK not in description:
            problems.append(
                f"server '{name}': skill-description must link to "
                f"'{SKILL_DESCRIPTION_LINK}'"
            )
    return problems


def _missing_skills(catalog: dict, skills_dir: Path) -> list[str]:
    """Return one problem per catalog server without a generated SKILL.md."""
    missing: list[str] = []
    for name in sorted(catalog):
        kind = catalog[name].get("kind")
        if kind == "mcp-server":
            stem = f"mcp-{name}"
        elif kind == "cli-tool":
            stem = f"tool-{name}"
        else:
            missing.append(
                f"server '{name}': unsupported catalog kind {kind!r}"
            )
            continue
        if not (skills_dir / stem / "SKILL.md").is_file():
            missing.append(
                f"server '{name}': generated skill missing at {stem}/SKILL.md"
            )
    return missing


def _table_stems() -> set[str]:
    """Skill stems listed in the hand-authored lazy-rules pointer table."""
    text = (REPO_ROOT / "rules/1-generic/use-lazy-rules.md").read_text(
        encoding="utf-8"
    )
    return set(re.findall(r"^\|\s*(mcp-[a-z0-9-]+|tool-[a-z0-9-]+)\s*\|", text, re.M))


@pytest.fixture(scope="module")
def rendered_project(tmp_path_factory) -> Path:
    """Sync all catalog servers into a throwaway project (no ignored repo files)."""
    project_root = tmp_path_factory.mktemp("mcp-server-checklist")
    config = dict(load_config(REPO_ROOT / ".meta-config" / "project.yaml"))
    config["rules-preset"] = "lazy"
    config["plugins"] = {name: {"enabled": True} for name in CATALOG}

    provider_config = load_providers_config(REPO_ROOT)
    log = SyncLog()
    generate_mcp_artifacts(
        REPO_ROOT, project_root, config, provider_config, log,
        dry_run=False, provider=PROVIDER,
    )
    generate_external_tool_artifacts(
        REPO_ROOT, project_root, config, provider_config, log,
        dry_run=False, provider=PROVIDER,
    )
    assert log.errors == [], log.errors
    return project_root


# --- catalog completeness ---------------------------------------------------


@pytest.mark.parametrize("server", SERVER_NAMES)
def test_catalog_entry_is_complete(server):
    problems = _entry_problems(server, CATALOG[server])
    assert not problems, "\n".join(problems)


# --- lazy-rule routing (preset + pointer table) -----------------------------


@pytest.mark.parametrize("server", SERVER_NAMES)
def test_server_is_routed_through_lazy_skill_preset(server):
    presets = yaml.safe_load(
        (REPO_ROOT / "config" / "rules-presets.yaml").read_text(encoding="utf-8")
    )["presets"]
    problems = _preset_problems(server, presets, CATALOG[server])
    assert not problems, "\n".join(problems)


@pytest.mark.parametrize("server", SERVER_NAMES)
def test_server_appears_in_lazy_rules_pointer_table(server):
    stem = _skill_stem(server)
    assert stem in _table_stems(), (
        f"server '{server}': '{stem}' is missing from "
        "rules/1-generic/use-lazy-rules.md"
    )


# --- generated skills (render into a temp project) --------------------------


def test_every_registry_server_has_a_generated_skill(rendered_project):
    skills_dir = rendered_project / load_providers_config(REPO_ROOT)[PROVIDER][
        "skills_dir"
    ]
    missing = _missing_skills(CATALOG, skills_dir)
    assert not missing, "\n".join(missing)


@pytest.mark.parametrize("server", SERVER_NAMES)
def test_generated_skill_has_expected_frontmatter(rendered_project, server):
    skills_dir = rendered_project / load_providers_config(REPO_ROOT)[PROVIDER][
        "skills_dir"
    ]
    stem = _skill_stem(server)
    skill = skills_dir / stem / "SKILL.md"
    assert skill.is_file(), f"server '{server}': {stem}/SKILL.md missing"

    text = skill.read_text(encoding="utf-8")
    assert text.startswith("---\n"), f"server '{server}': frontmatter missing"
    frontmatter = yaml.safe_load(text.split("---", 2)[1]) or {}
    assert frontmatter.get("name") == stem
    description = str(frontmatter.get("description") or "")
    assert description.lower().startswith("use when"), description
    assert SKILL_DESCRIPTION_LINK in description, description


# --- guardrail + #1262 validation ------------------------------------------


@pytest.mark.parametrize("server", MCP_SERVERS)
def test_blocked_tools_reach_the_guardrail_list(server):
    blocked = CATALOG[server].get("tools", {}).get("blocked", [])
    if not blocked:
        pytest.skip(f"server '{server}' declares no blocked tools")

    guardrails = build_mcp_guardrails_list(CATALOG, [server])
    assert f"- **{server}:**" in guardrails
    for tool in blocked:
        assert f"`{tool}`" in guardrails, f"server '{server}': {tool} missing"


@pytest.mark.parametrize("server", SERVER_NAMES)
def test_catalog_entry_passes_1262_validation(server, tmp_path):
    findings = validate_mcp_health(
        REPO_ROOT, tmp_path, {}, env={}, registry=CATALOG, active=[server],
    )
    errors = [finding for finding in findings if finding[1] == SEVERITY_ERROR]
    assert not errors, errors


# --- AC-1: a new server without wiring fails with its name -----------------


def test_new_server_without_generated_skill_names_the_server(tmp_path):
    catalog = dict(CATALOG)
    catalog["brand-new-server"] = {
        **CATALOG["playwright"],
        "description": "new server without a lazy rule",
    }

    skills_dir = tmp_path / "skills"
    for name in CATALOG:
        stem = _skill_stem(name)
        (skills_dir / stem).mkdir(parents=True)
        (skills_dir / stem / "SKILL.md").write_text(
            "---\nname: stub\n---\n", encoding="utf-8"
        )

    missing = _missing_skills(catalog, skills_dir)
    assert missing == [
        "server 'brand-new-server': generated skill missing at "
        "mcp-brand-new-server/SKILL.md"
    ]


def test_new_server_without_lazy_preset_names_the_server():
    presets = yaml.safe_load(
        (REPO_ROOT / "config" / "rules-presets.yaml").read_text(encoding="utf-8")
    )["presets"]
    catalog = dict(CATALOG)
    catalog["brand-new-server"] = dict(CATALOG["playwright"])

    problems = _preset_problems("brand-new-server", presets, catalog["brand-new-server"])
    assert problems == [
        "server 'brand-new-server': lazy preset entry 'mcp-brand-new-server' is missing"
    ]
