#!/usr/bin/env python3
"""Export agent-meta roles as a Hermes skill pack (issue #527).

Second export format beside the ``standalone/`` personas
(``scripts/lib/standalone.py``): per-role, ready-to-install skills for the
Hermes Agent framework, plus a machine-readable ``manifest.yaml`` that
carries each role's ABSTRACT cost tier — deliberately WITHOUT any concrete
model IDs. Model resolution (tier -> model) is owned by the consumer
deployment, which can re-map tiers dynamically (budget, usage limits,
provider swaps) without regenerating the pack.

Output layout::

    <output>/
    ├── manifest.yaml              # role -> abstract tier, keywords, contracts
    └── roles/<role>/
        ├── SKILL.md               # Hermes skill frontmatter + usage instructions
        └── references/persona.md  # rendered via render_standalone_agent()

Personas reuse :func:`scripts.lib.standalone.render_standalone_agent`, so they
stay byte-consistent with the ``standalone/`` export (fully resolved, no
``{{PLACEHOLDER}}`` left over, English-only).

Usage (from agent-meta repo root)::

    python3 scripts/hermes_export.py --output /tmp/hermes-skillpack
    python3 scripts/hermes_export.py --output /tmp/pack --roles code-reviewer,explorer
    python3 scripts/hermes_export.py --output /tmp/pack --export-config curation.yaml
    python3 scripts/hermes_export.py --output /tmp/pack --dry-run

Design decisions (issue #527 open questions):

1. Default role set: ALL non-deprecated 1-generic templates — the same skip
   rules as :func:`scripts.lib.standalone.discover_standalone_roles`
   (``_``-prefixed files are reserved resources, ``deprecated: true``
   templates are excluded). A hardcoded curated list would rot as roles are
   added/renamed; consumers filter via ``--roles`` / ``--export-config`` or
   simply ignore manifest entries they do not use.
2. Handoff schemas: the manifest carries contract NAMES (``output_contract``,
   ``input_contracts``) and schema PATHS (``input_schema``, ``output_schema``)
   from ``config/role-defaults.yaml`` — the JSON schemas themselves are NOT
   embedded. Embedding would duplicate a maintained artifact into generated
   output (drift risk); consumers resolve schemas against the agent-meta
   version pinned in ``agent-meta-version``.
3. Naming: ``hermes-skillpack`` (manifest ``format:`` key) and the script
   name stay Hermes-specific per issue #527 — the consumer is the Hermes
   Agent framework. A generic rename can be introduced later as an alias
   without changing the manifest contract.

Tier sources (abstract only):

- Per-role tier: ``config/role-defaults.yaml`` ``roles.<role>.model``
  (abstract tier name), loaded via
  :func:`scripts.lib.roles.load_roles_config`. Legacy Claude aliases
  (``haiku``/``sonnet``/``opus``) are normalized the same way
  ``scripts/lib/roles.py::_resolve_tier_to_model`` does for provider-less
  contexts; ``ultra`` collapses to ``max`` (the export vocabulary caps at
  ``max``).
- ``config/tier-presets.yaml`` (tier -> model matrices) is deliberately NOT
  consulted: resolving tiers to provider model IDs would violate this
  export's no-model-IDs contract. Unknown or empty tier values fall back to
  ``balanced`` with a warning — a raw model ID must never leak into the
  output.

The manifest and skill frontmatter are serialized by a small stdlib emitter
(no PyYAML dependency) so output is byte-stable regardless of the
environment. ``--export-config`` parsing uses PyYAML when available (JSON
configs work without it). The export is additive-only: it never deletes
pre-existing files in the output directory; regenerate into a fresh
directory to get an exact snapshot.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Ensure the repo root is on sys.path so ``scripts.lib`` is importable
# regardless of cwd (same bootstrap pattern as scripts/se-export.py).
_REPO_ROOT = Path(__file__).resolve().parent.parent
if str(_REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(_REPO_ROOT))

try:
    import yaml as _yaml
    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover - exercised only without PyYAML
    _YAML_AVAILABLE = False

from scripts.lib.config import read_version
from scripts.lib.frontmatter import is_deprecated_template, parse_frontmatter_text
from scripts.lib.roles import load_roles_config
from scripts.lib.standalone import discover_standalone_roles, render_standalone_agent

REPO_URL = "https://github.com/Popoboxxo/agent-meta"

MANIFEST_FORMAT = "hermes-skillpack"
MANIFEST_FORMAT_VERSION = "0.1.0"
MANIFEST_NOTE = (
    "Abstract tiers only — NO model IDs. Consumer resolves tier->model locally."
)

# Abstract cost tier vocabulary of the export (issue #527). Deliberately
# narrower than roles.py::_TIER_SEQUENCE: "ultra" collapses to "max".
EXPORT_TIERS = ("nano", "fast", "balanced", "powerful", "max")
DEFAULT_TIER = "balanced"

# Legacy Claude aliases — normalized exactly like roles.py does when no
# provider context is available (roles.py::_resolve_tier_to_model fallback).
_LEGACY_TIER_MAP = {"haiku": "fast", "sonnet": "balanced", "opus": "powerful"}

# Maximum intent keywords folded into a SKILL.md description line (routing
# hint for the consumer's trigger matching; the manifest keeps the full list).
_MAX_SKILL_KEYWORDS = 8


# ---------------------------------------------------------------------------
# Minimal stdlib YAML emitter (deterministic, no PyYAML dependency)
# ---------------------------------------------------------------------------

def _yaml_scalar(value: str) -> str:
    """Return *value* as a double-quoted YAML scalar.

    Always quoting keeps the emitter trivially correct for strings that
    contain colons, dashes, unicode, quotes or newlines, and makes the
    manifest byte-stable across runs.
    """
    escaped = (
        value.replace("\\", "\\\\")
        .replace('"', '\\"')
        .replace("\n", "\\n")
    )
    return f'"{escaped}"'


def _yaml_key(key: str) -> str:
    """Return a mapping key unquoted when it is a safe bare YAML key."""
    if key and key[0].isalnum() and all(ch.isalnum() or ch in "-_." for ch in key):
        return key
    return _yaml_scalar(key)


def _emit_sequence_scalar(item: object) -> str:
    """Render one sequence item scalar (manifest sequences hold scalars only)."""
    if item is None:
        return "null"
    if isinstance(item, bool):
        return "true" if item else "false"
    if isinstance(item, (int, float)):
        return str(item)
    if isinstance(item, (dict, list)):
        raise TypeError(
            "Nested collections inside YAML sequences are not supported by "
            "this emitter (manifest structure guarantees scalar items)."
        )
    return _yaml_scalar(str(item))


def _emit_yaml(data: dict, indent: int = 0) -> str:
    """Serialize a dict structure as block YAML.

    Supports exactly the value types the manifest and skill frontmatter use:
    nested dicts, scalar lists, strings, booleans, numbers, null. Empty
    collections emit flow style (``{}`` / ``[]``) so mappings stay valid YAML.
    """
    pad = "  " * indent
    lines: list[str] = []
    for key, value in data.items():
        k = _yaml_key(str(key))
        if isinstance(value, dict):
            if value:
                lines.append(f"{pad}{k}:")
                lines.append(_emit_yaml(value, indent + 1))
            else:
                lines.append(f"{pad}{k}: {{}}")
        elif isinstance(value, list):
            if value:
                lines.append(f"{pad}{k}:")
                for item in value:
                    lines.append(f"{pad}- {_emit_sequence_scalar(item)}")
            else:
                lines.append(f"{pad}{k}: []")
        elif value is None:
            lines.append(f"{pad}{k}: null")
        elif isinstance(value, bool):
            lines.append(f"{pad}{k}: {'true' if value else 'false'}")
        elif isinstance(value, (int, float)):
            lines.append(f"{pad}{k}: {value}")
        else:
            lines.append(f"{pad}{k}: {_yaml_scalar(str(value))}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Abstract tier resolution (NO model IDs may reach the output)
# ---------------------------------------------------------------------------

def resolve_abstract_tier(model_value: str) -> tuple[str, str | None]:
    """Normalize a role-defaults ``model:`` value to an abstract export tier.

    Returns ``(tier, warning)`` where ``warning`` is ``None`` when the value
    mapped cleanly. Guarantees the returned tier is always a member of
    :data:`EXPORT_TIERS` — anything unresolvable (including a raw model ID)
    falls back to :data:`DEFAULT_TIER` with a warning instead of leaking a
    model ID into the export.
    """
    value = (model_value or "").strip()
    if value in EXPORT_TIERS:
        return value, None
    if value in _LEGACY_TIER_MAP:
        return _LEGACY_TIER_MAP[value], None
    if value == "ultra":
        return "max", (
            "tier 'ultra' collapsed to 'max' (export vocabulary caps at max)"
        )
    if not value:
        return DEFAULT_TIER, (
            "no abstract tier in role-defaults.yaml — defaulting to "
            f"'{DEFAULT_TIER}'"
        )
    return DEFAULT_TIER, (
        f"'{value}' is not an abstract tier (possible model ID) — defaulting "
        f"to '{DEFAULT_TIER}'; model IDs must never appear in this export"
    )


# ---------------------------------------------------------------------------
# Role metadata -> manifest/SKILL payloads
# ---------------------------------------------------------------------------

def _role_description(role: str, entry: dict, agent_meta_root: Path) -> str:
    """Best-effort one-line description for a role.

    Priority: role-defaults ``description`` -> ``short_desc`` -> template
    frontmatter ``description`` (e.g. the provider-expert base template has
    no role-defaults entry by design) -> role name.
    """
    for source in (entry.get("description"), entry.get("short_desc")):
        text = str(source or "").strip()
        if text:
            return text
    template = agent_meta_root / "agents" / "1-generic" / f"{role}.md"
    if template.exists():
        fm = parse_frontmatter_text(template.read_text(encoding="utf-8"))
        text = str(fm.get("description", "") or "").strip()
        if text:
            return text
    return role


def collect_role_meta(
    role: str, agent_meta_root: Path, roles_cfg: dict
) -> tuple[dict, str | None]:
    """Assemble the manifest/skill metadata dict for one role.

    Everything is sourced from ``config/role-defaults.yaml`` (via
    ``load_roles_config``) with template-frontmatter fallbacks — nothing new
    to maintain per-role (issue #527).
    """
    entry = roles_cfg.get("roles", {}).get(role, {})
    if not isinstance(entry, dict):
        entry = {}
    handoff = entry.get("handoff") or {}
    routing = entry.get("routing") or {}
    tier, warning = resolve_abstract_tier(str(entry.get("model", "") or ""))
    meta = {
        "tier": tier,
        "description": _role_description(role, entry, agent_meta_root),
        "keywords": [str(k) for k in (routing.get("intent_keywords") or [])],
        "output_contract": handoff.get("output_contract"),
        "input_contracts": [str(c) for c in (handoff.get("input_contracts") or [])],
        "input_schema": handoff.get("input_schema"),
        "output_schema": handoff.get("output_schema"),
    }
    return meta, warning


def _render_skill_md(role: str, meta: dict, version: str) -> str:
    """Render one role's SKILL.md (Hermes-discoverable frontmatter + usage)."""
    keywords = meta["keywords"][:_MAX_SKILL_KEYWORDS]
    description = str(meta["description"])
    if keywords:
        description = f"{description} Triggers: {', '.join(keywords)}."
    contract = meta["output_contract"]
    contract_suffix = f" (`{contract}`)" if contract else ""

    frontmatter = _emit_yaml(
        {
            "name": f"agent-meta-{role}",
            "description": description,
            "version": version,
            "metadata": {
                "agent-meta": {
                    "role": role,
                    "tier": meta["tier"],
                    "source": f"agents/1-generic/{role}.md",
                }
            },
        }
    )

    trigger_block = ""
    if keywords:
        trigger_block = (
            "Trigger keywords: " + ", ".join(keywords) + ".\n"
        )

    body = (
        f"# agent-meta role: {role}\n"
        "\n"
        f"Generated Hermes skill export from [agent-meta]({REPO_URL}) v{version} "
        "(`scripts/hermes_export.py`, issue #527). The full persona lives in "
        "`references/persona.md` next to this file.\n"
        "\n"
        "## When to use\n"
        "\n"
        f"Delegate a task to this skill when it matches the `{role}` role "
        f"(abstract cost tier: `{meta['tier']}`).\n"
        + trigger_block +
        "\n"
        "## How to use\n"
        "\n"
        "1. Read `references/persona.md` in full and adopt it as your working "
        "role.\n"
        "2. Execute the task according to that persona — its workflow, "
        f"reflection loop and output contract{contract_suffix} are binding.\n"
        "3. Respond structured: `STATUS` / `RESULT` / `ARTIFACTS`; return "
        "artifact paths instead of dumping raw output (result-size "
        "truncation guard).\n"
        "\n"
        "## Consumer-side delegation sketch\n"
        "\n"
        "```python\n"
        "persona = open(\"references/persona.md\", encoding=\"utf-8\").read()\n"
        "delegate_task(\n"
        "    goal=\"<task summary>\",\n"
        f"    context=\"Role: {role} (tier: {meta['tier']}).\\n\\n\" + persona\n"
        "            + \"\\n\\nTASK: <t> | CONTEXT: <ctx> | CONSTRAINTS: <con>\",\n"
        ")\n"
        "```\n"
        "\n"
        "## Tier note\n"
        "\n"
        f"`tier: {meta['tier']}` is an abstract cost tier "
        "(nano | fast | balanced | powerful | max). Map tiers to concrete "
        "models consumer-side per deployment — this skill pack deliberately "
        "contains NO model IDs.\n"
        "\n"
        "---\n"
        f"Source: `agents/1-generic/{role}.md` (agent-meta v{version})\n"
    )
    return f"---\n{frontmatter}\n---\n\n{body}"


def _render_manifest(manifest_roles: dict, version: str) -> str:
    """Render the pack-wide manifest.yaml content (no model IDs, ever)."""
    manifest = {
        "agent-meta-version": version,
        "format": MANIFEST_FORMAT,
        "format-version": MANIFEST_FORMAT_VERSION,
        "note": MANIFEST_NOTE,
        "tier-order": list(EXPORT_TIERS),
        "roles": manifest_roles,
    }
    return _emit_yaml(manifest) + "\n"


# ---------------------------------------------------------------------------
# Export orchestration
# ---------------------------------------------------------------------------

def _skip_reason(agent_meta_root: Path, role: str) -> str:
    """Human-readable reason why a requested role is not exported."""
    source = agent_meta_root / "agents" / "1-generic" / f"{role}.md"
    if not source.exists():
        return "no template in agents/1-generic/"
    if role.startswith("_"):
        return "reserved resource (underscore-prefixed)"
    if is_deprecated_template(source.read_text(encoding="utf-8")):
        return "template is deprecated: true"
    return "not an active 1-generic template"


def _load_export_config(path: Path) -> tuple[list[str], dict[str, str]]:
    """Load an optional curation config: ``roles: [...]``, ``tiers: {...}``.

    YAML configs need PyYAML (clean error when unavailable); JSON configs
    work with the stdlib alone. Returns ``(roles, tier_overrides)``.
    Raises FileNotFoundError / ValueError with a clear message on problems.
    """
    if not path.exists():
        raise FileNotFoundError(f"Export config not found: {path}")
    text = path.read_text(encoding="utf-8")
    suffix = path.suffix.lower()
    data: object
    if suffix == ".json":
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            raise ValueError(f"Invalid JSON in export config {path}: {exc}") from exc
    elif suffix in (".yaml", ".yml"):
        if not _YAML_AVAILABLE:
            raise RuntimeError(
                "--export-config with a YAML file requires PyYAML (not "
                f"installed). Pass a JSON config instead: {path}"
            )
        try:
            data = _yaml.safe_load(text)
        except _yaml.YAMLError as exc:
            raise ValueError(f"Invalid YAML in export config {path}: {exc}") from exc
    else:
        raise ValueError(
            f"Unsupported export-config suffix '{path.suffix}' "
            f"(use .yaml, .yml or .json): {path}"
        )

    if not isinstance(data, dict):
        raise ValueError(
            f"Export config {path}: expected a mapping at the top level, "
            f"got {type(data).__name__}."
        )
    roles = [str(r) for r in (data.get("roles") or [])]
    tiers_raw = data.get("tiers") or {}
    if not isinstance(tiers_raw, dict):
        raise ValueError(
            f"Export config {path}: 'tiers' must be a mapping (role -> tier), "
            f"got {type(tiers_raw).__name__}."
        )
    tiers = {str(r): str(t) for r, t in tiers_raw.items()}
    unknown = sorted(set(data) - {"roles", "tiers"})
    if unknown:
        print(
            f"  !  export config {path.name}: ignoring unknown key(s): "
            f"{', '.join(unknown)} (supported: roles, tiers)",
            file=sys.stderr,
        )
    return roles, tiers


def _validate_tier_overrides(tier_overrides: dict[str, str]) -> None:
    """Reject tier overrides that are not abstract tiers (model-ID leak guard)."""
    invalid = {
        role: value
        for role, value in tier_overrides.items()
        if value not in EXPORT_TIERS
    }
    if invalid:
        details = ", ".join(f"{role}: '{value}'" for role, value in invalid.items())
        raise ValueError(
            "Invalid tier override(s) — only abstract tiers "
            f"({'|'.join(EXPORT_TIERS)}) are allowed, model IDs are forbidden "
            f"in this export: {details}"
        )


def export_skill_pack(
    agent_meta_root: Path,
    output_dir: Path,
    roles: list[str] | None = None,
    tier_overrides: dict[str, str] | None = None,
    dry_run: bool = False,
) -> dict:
    """Export the Hermes skill pack into *output_dir*.

    Args:
        agent_meta_root: agent-meta repository root.
        output_dir: Target directory (created on demand; never cleaned).
        roles: Optional role filter (default: every non-deprecated
            1-generic template, see module docstring decision #1).
        tier_overrides: Optional ``{role: abstract_tier}`` map (validated).
        dry_run: When True, compute everything but write nothing.

    Returns:
        Summary dict with ``written`` (relative paths), ``skipped``
        (``(role, reason)`` tuples), ``warnings``, ``roles`` (manifest role
        map) and the rendered ``manifest`` string.

    Raises:
        ValueError: On invalid tier overrides (non-abstract tier values).
        FileNotFoundError: If agent_meta_root has no agents/1-generic dir.
    """
    generic_dir = agent_meta_root / "agents" / "1-generic"
    if not generic_dir.is_dir():
        raise FileNotFoundError(
            f"Not an agent-meta root (missing {generic_dir}): {agent_meta_root}"
        )
    if output_dir in (agent_meta_root, agent_meta_root / "agents"):
        raise ValueError(
            f"Refusing to export into the source tree: {output_dir}"
        )

    overrides = dict(tier_overrides or {})
    _validate_tier_overrides(overrides)

    available = list(discover_standalone_roles(agent_meta_root))
    skipped: list[tuple[str, str]] = []
    if roles:
        wanted: list[str] = []
        for role in roles:
            if role not in wanted:
                wanted.append(role)
        selected = [role for role in available if role in wanted]
        skipped = [
            (role, _skip_reason(agent_meta_root, role))
            for role in wanted
            if role not in available
        ]
    else:
        selected = available

    version = read_version(agent_meta_root)
    roles_cfg = load_roles_config(agent_meta_root)

    manifest_roles: dict[str, dict] = {}
    written: list[str] = []
    warnings: list[str] = []
    for role in selected:
        meta, warning = collect_role_meta(role, agent_meta_root, roles_cfg)
        if warning:
            warnings.append(f"{role}: {warning}")
        if role in overrides:
            meta["tier"] = overrides[role]

        persona = render_standalone_agent(role, agent_meta_root)
        skill_content = _render_skill_md(role, meta, version)

        rel_skill = f"roles/{role}/SKILL.md"
        rel_persona = f"roles/{role}/references/persona.md"
        manifest_roles[role] = {
            "tier": meta["tier"],
            "description": meta["description"],
            "keywords": meta["keywords"],
            "output_contract": meta["output_contract"],
            "input_contracts": meta["input_contracts"],
            "input_schema": meta["input_schema"],
            "output_schema": meta["output_schema"],
            "skill": rel_skill,
            "persona": rel_persona,
        }
        if not dry_run:
            skill_path = output_dir / "roles" / role / "SKILL.md"
            persona_path = output_dir / "roles" / role / "references" / "persona.md"
            skill_path.parent.mkdir(parents=True, exist_ok=True)
            skill_path.write_text(skill_content, encoding="utf-8")
            persona_path.parent.mkdir(parents=True, exist_ok=True)
            persona_path.write_text(persona, encoding="utf-8")
        written.extend([rel_skill, rel_persona])

    manifest_content = _render_manifest(manifest_roles, version)
    if not dry_run:
        output_dir.mkdir(parents=True, exist_ok=True)
        (output_dir / "manifest.yaml").write_text(manifest_content, encoding="utf-8")
    written.append("manifest.yaml")

    return {
        "written": written,
        "skipped": skipped,
        "warnings": warnings,
        "roles": manifest_roles,
        "manifest": manifest_content,
        "dry_run": dry_run,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def _build_parser() -> argparse.ArgumentParser:
    """Construct the hermes_export CLI argument parser."""
    parser = argparse.ArgumentParser(
        description=(
            "Export agent-meta roles as a Hermes skill pack: per-role "
            "SKILL.md + rendered persona, with abstract cost tiers only "
            "(no model IDs) in the manifest."
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        "--output",
        required=True,
        metavar="DIR",
        help="Output directory for the skill pack (created on demand).",
    )
    parser.add_argument(
        "--root",
        default=None,
        metavar="DIR",
        help=(
            "agent-meta repository root (default: the repo this script "
            "lives in)."
        ),
    )
    parser.add_argument(
        "--roles",
        default="",
        metavar="ROLE[,ROLE...]",
        help=(
            "Comma-separated role filter (default: all non-deprecated "
            "1-generic roles). Overrides export-config 'roles'."
        ),
    )
    parser.add_argument(
        "--export-config",
        dest="export_config",
        default=None,
        metavar="FILE",
        help=(
            "Optional curation config (YAML needs PyYAML, JSON works "
            "without): roles: [...] and tiers: {role: nano|fast|balanced|"
            "powerful|max}."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Compute the export and print what would be written, without writing.",
    )
    return parser


def main() -> int:
    """Entry point for the hermes_export CLI. Returns the process exit code."""
    args = _build_parser().parse_args()

    root = Path(args.root).resolve() if args.root else _REPO_ROOT
    output = Path(args.output).resolve()

    roles: list[str] | None = None
    tier_overrides: dict[str, str] = {}
    try:
        if args.export_config:
            cfg_roles, tier_overrides = _load_export_config(Path(args.export_config))
            roles = cfg_roles or None
        if args.roles:
            cli_roles = [r.strip() for r in args.roles.split(",") if r.strip()]
            if cli_roles:
                roles = cli_roles
        summary = export_skill_pack(
            root,
            output,
            roles=roles,
            tier_overrides=tier_overrides,
            dry_run=args.dry_run,
        )
    except (ValueError, FileNotFoundError, RuntimeError, OSError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    prefix = "[dry-run] would write " if args.dry_run else "wrote "
    for rel_path in summary["written"]:
        print(f"{prefix}{output / rel_path}")
    for role, reason in summary["skipped"]:
        print(f"skipped {role}: {reason}", file=sys.stderr)
    for warning in summary["warnings"]:
        print(f"  !  {warning}", file=sys.stderr)
    mode = " (dry-run)" if args.dry_run else ""
    print(
        f"OK: {len(summary['roles'])} role(s) exported -> {output}{mode}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
