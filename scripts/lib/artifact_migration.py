"""Legacy alias migration for the artifact-location matrix (Issue #1186, T23/D1).

Once ``artifact-locations`` is the single source, the old path keys become
migration aliases. This module reads them, builds a pure :class:`MigrationPlan`,
renders a ready-to-paste YAML snippet and — only on explicit ``--write`` —
applies the plan to ``project.yaml``.

Write contract:

* comment-preserving: the new ``artifact-locations`` keys are inserted into the
  original text, never re-serialised with :func:`yaml.dump`; the result is
  checked with :func:`lib.yaml_roundtrip.assert_roundtrip_preserved`;
* atomic: :func:`lib.io.write_atomic`;
* idempotent: an alias whose target is already present with the same value is
  skipped, so a second run reports "already migrated" and writes zero bytes;
* refusing: divergent alias/matrix values and ``enabled: false`` are hard
  refusals (the T5 validator remains the authority for divergence).

This is a pure library for planning/rendering — no ``sys.exit``, no provider
branch, no writes except the explicit :func:`apply_migration`.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml  # PyYAML: documented runtime exception (docs/adr/0001)

from lib.artifact_locations import (
    CLASS_REGISTRY,
    ArtifactLocationsError,
    resolve_artifact_locations,
)
from lib.io import write_atomic
from lib.yaml_roundtrip import YamlRoundTripLoss, assert_roundtrip_preserved

_REPO_ROOT = Path(__file__).resolve().parents[2]
_SCRATCH_SOURCE = "repo_containment.tmp-sink.path"
_SE_TARGET = "artifact-locations.classes.se-*.path"
_SE_CLASS_NAMES = tuple(
    name for name, spec in CLASS_REGISTRY.items() if spec.form == "se"
)


class MigrationError(ValueError):
    """A refusal with a stable machine-readable ``code``."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


@dataclass(frozen=True)
class MigrationEntry:
    """One legacy alias → matrix target mapping (pure data)."""

    source_key: str
    target_key: str
    value: str
    reason: str


@dataclass(frozen=True)
class MigrationPlan:
    """The complete, deterministic migration plan."""

    enabled: bool
    entries: tuple[MigrationEntry, ...]

    @property
    def assignments(self) -> list[tuple[tuple[str, ...], str]]:
        """Concrete dotted target paths and their values (SE wildcard expanded)."""
        out: list[tuple[tuple[str, ...], str]] = []
        for entry in self.entries:
            tokens = tuple(entry.target_key.split("."))
            if "se-*" in tokens:
                for name in _SE_CLASS_NAMES:
                    concrete = tuple(name if part == "se-*" else part for part in tokens)
                    out.append((concrete, entry.value))
            else:
                out.append((tokens, entry.value))
        seen: set[tuple[str, ...]] = set()
        unique: list[tuple[tuple[str, ...], str]] = []
        for tokens, value in out:
            if tokens not in seen:
                seen.add(tokens)
                unique.append((tokens, value))
        return unique


@dataclass(frozen=True)
class AppliedReport:
    """Outcome of an ``apply_migration`` call."""

    written: bool
    entries_written: int
    message: str


@dataclass(frozen=True)
class _AliasSpec:
    source_key: str
    target_key: str
    reason: str


#: The six alias groups (D1). ``progress.*`` and ``spec-plan-workflow.paths.*``
#: each cover several concrete source keys; all are handled.
_ALIAS_SPECS: tuple[_AliasSpec, ...] = (
    _AliasSpec(
        "spec-plan-workflow.paths.specs",
        "artifact-locations.classes.specs.path",
        "spec-plan-workflow.paths.* is deprecated; spec/plan paths have one source in the matrix (D1)",
    ),
    _AliasSpec(
        "spec-plan-workflow.paths.plans",
        "artifact-locations.classes.plans.path",
        "spec-plan-workflow.paths.* is deprecated; spec/plan paths have one source in the matrix (D1)",
    ),
    _AliasSpec(
        "spec-plan-workflow.paths.spikes",
        "artifact-locations.classes.spikes.path",
        "spec-plan-workflow.paths.* is deprecated; spec/plan paths have one source in the matrix (D1)",
    ),
    _AliasSpec(
        "se_output.base_dir",
        _SE_TARGET,
        "se_output.base_dir is deprecated; the SE root has a single matrix source (D1)",
    ),
    _AliasSpec(
        _SCRATCH_SOURCE,
        "artifact-locations.classes.scratch.path",
        "tmp-sink.path is a deprecated migration alias; scratch has exactly one source (D1)",
    ),
    _AliasSpec(
        "progress.dir",
        "artifact-locations.classes.state.subdirs.progress",
        "progress.* is deprecated; state subdirs have one source in the matrix (D1)",
    ),
    _AliasSpec(
        "progress.checkpoint-dir",
        "artifact-locations.classes.state.subdirs.checkpoints",
        "progress.* is deprecated; state subdirs have one source in the matrix (D1)",
    ),
    _AliasSpec(
        "progress.handoffs-dir",
        "artifact-locations.classes.state.subdirs.handoffs",
        "progress.* is deprecated; state subdirs have one source in the matrix (D1)",
    ),
    _AliasSpec(
        "viz.event_log",
        "artifact-locations.classes.state.event-log",
        "viz.event_log is deprecated; the state event-log has one source in the matrix (D1)",
    ),
)


# ---------------------------------------------------------------------------
# Pure helpers
# ---------------------------------------------------------------------------
def _get_dotted(data: Any, dotted: str) -> Any:
    """Walk a dotted key path through nested mappings; ``None`` when absent."""
    node = data
    for part in dotted.split("."):
        if not isinstance(node, dict) or part not in node:
            return None
        node = node[part]
    return node


def _explicit_targets(section: dict, target_key: str) -> list[Any]:
    """Values explicitly configured at a target (SE wildcard expanded)."""
    dotted = target_key
    if dotted.startswith("artifact-locations."):
        dotted = dotted[len("artifact-locations."):]
    if "se-*" in dotted.split("."):
        values: list[Any] = []
        for name in _SE_CLASS_NAMES:
            concrete = ".".join(name if part == "se-*" else part for part in dotted.split("."))
            value = _get_dotted(section, concrete)
            if value is not None:
                values.append(value)
        return values
    value = _get_dotted(section, dotted)
    return [value] if value is not None else []


def build_migration_plan(config: dict, matrix: Any = None) -> MigrationPlan:
    """Build the migration plan; never mutate ``config``.

    Raises :class:`MigrationError` when the master switch is off or when an
    alias and its explicit matrix target disagree (D1: no silent double sink).
    """
    config = config or {}
    section = config.get("artifact-locations") or {}
    if not isinstance(section, dict):
        section = {}
    if section.get("enabled", True) is False:
        raise MigrationError(
            "artifact-locations.migration-disabled",
            "artifact-locations is configured with enabled: false: "
            "spec-plan-workflow.paths, se_output.base_dir and "
            "repo_containment.tmp-sink.path remain the sole sources "
            "(Spec §3.3 rule 5); set enabled: true before migrating",
        )

    if matrix is None:
        try:
            matrix = resolve_artifact_locations(config, _REPO_ROOT, None)
        except ArtifactLocationsError as exc:
            # T5 owns the validator; surface the same stable code as a refusal.
            raise MigrationError(exc.code, exc.message) from exc

    entries: list[MigrationEntry] = []
    for spec in _ALIAS_SPECS:
        alias_value = _get_dotted(config, spec.source_key)
        if alias_value is None:
            continue
        explicit = _explicit_targets(section, spec.target_key)
        if any(value != alias_value for value in explicit):
            code = (
                "artifact-locations.scratch-sink-divergence"
                if spec.source_key == _SCRATCH_SOURCE
                else "artifact-locations.migration-divergence"
            )
            raise MigrationError(
                code,
                f"'{spec.source_key}' ({alias_value}) diverges from "
                f"'{spec.target_key}' ({', '.join(str(v) for v in explicit)}); "
                "keep one source — remove the deprecated alias or align the values",
            )
        if explicit and all(value == alias_value for value in explicit):
            continue  # already migrated — idempotent
        entries.append(
            MigrationEntry(spec.source_key, spec.target_key, str(alias_value), spec.reason)
        )
    return MigrationPlan(enabled=True, entries=tuple(entries))


def _assignments_tree(plan: MigrationPlan) -> dict:
    tree: dict = {}
    for tokens, value in plan.assignments:
        node = tree
        for part in tokens[:-1]:
            node = node.setdefault(part, {})
        node[tokens[-1]] = value
    return tree


def render_snippets(plan: MigrationPlan) -> str:
    """Render the read-only preview: per-alias provenance plus a YAML snippet."""
    lines = [
        "# Artifact-location alias migration (Issue #1186, D1) — dry-run preview",
        "# Run 'sync.py --migrate-artifact-aliases --write' to apply (comment-preserving).",
        "",
    ]
    if not plan.entries:
        lines.append("# already migrated: no legacy alias to write")
        return "\n".join(lines)
    for entry in plan.entries:
        lines.append(f"# {entry.source_key} -> {entry.target_key}")
        lines.append(f"#   reason: {entry.reason}")
    lines.append("")
    lines.append(
        yaml.safe_dump(_assignments_tree(plan), sort_keys=False, allow_unicode=True).rstrip("\n")
    )
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Comment-preserving, atomic, idempotent writer
# ---------------------------------------------------------------------------
def _yaml_scalar(value: Any) -> str:
    """Render a scalar as a safe YAML plain/quoted scalar."""
    text = str(value)
    lowered = text.lower()
    special_start = ("-", "?", ":", "#", "[", "]", "{", "}", "&", "*",
                     "!", "|", ">", "@", "`", "%", ",")
    if (
        not text
        or text.strip() != text
        or text[0] in special_start
        or ": " in text
        or " #" in text
        or lowered in {"true", "false", "null", "yes", "no", "on", "off", "~"}
    ):
        return "'" + text.replace("'", "''") + "'"
    return text


def _indent(line: str) -> int:
    return len(line) - len(line.lstrip(" "))


def _key_of(line: str) -> Optional[str]:
    stripped = line.strip()
    if not stripped or stripped.startswith("#") or stripped.startswith("- "):
        return None
    match = re.match(r"^([^:#][^:]*):(?:\s|$)", stripped)
    return match.group(1).strip() if match else None


def _block_end(lines: list[str], start: int, parent_indent: int) -> int:
    """Index of the first line at/above ``parent_indent`` after ``start``."""
    index = start
    while index < len(lines):
        raw = lines[index]
        stripped = raw.strip()
        if not stripped or stripped.startswith("#"):
            index += 1
            continue
        if _indent(raw) <= parent_indent:
            break
        index += 1
    return index


def _ensure_yaml_path(lines: list[str], tokens: tuple[str, ...], value: str) -> None:
    """Insert a missing dotted mapping path into ``lines``, leaving existing lines alone."""
    parent_start = 0
    parent_indent = -1
    for position, key in enumerate(tokens):
        indent = 2 * position
        is_leaf = position == len(tokens) - 1
        end = _block_end(lines, parent_start, parent_indent)
        found: Optional[int] = None
        for index in range(parent_start, end):
            raw = lines[index]
            stripped = raw.strip()
            if not stripped or stripped.startswith("#"):
                continue
            if _indent(raw) == indent and _key_of(raw) == key:
                found = index
                break
        if found is not None:
            if is_leaf:
                return  # already configured — idempotent, never overwrite
            parent_start = found + 1
            parent_indent = indent
            continue
        insert_at = end
        new_line = " " * indent + key + ":" + ((" " + _yaml_scalar(value)) if is_leaf else "")
        if insert_at >= len(lines):
            lines.append(new_line + "\n")
        else:
            lines.insert(insert_at, new_line + "\n")
        if is_leaf:
            return
        parent_start = insert_at + 1
        parent_indent = indent


def _merge_assignments(original: str, assignments: Iterable[tuple[tuple[str, ...], str]]) -> str:
    """Apply assignments textually, preserving every original comment and key order."""
    lines = original.splitlines(keepends=True)
    if lines and not lines[-1].endswith("\n"):
        lines[-1] += "\n"
    for tokens, value in assignments:
        _ensure_yaml_path(lines, tokens, value)
    return "".join(lines)


def apply_migration(project_config_path: Path, plan: MigrationPlan) -> AppliedReport:
    """Apply ``plan`` to ``project.yaml`` atomically, or report "already migrated"."""
    path = Path(project_config_path)
    if not plan.entries:
        return AppliedReport(False, 0, "already migrated: no legacy alias to write")

    original = path.read_text(encoding="utf-8")
    new_text = _merge_assignments(original, plan.assignments)

    # Re-resolve the merged config through the single resolver: structural
    # checks (paths, scratch single-source) run before any disk write.
    try:
        merged = yaml.safe_load(new_text) or {}
        resolve_artifact_locations(merged, _REPO_ROOT, path.parent.parent)
    except (ArtifactLocationsError, yaml.YAMLError) as exc:
        raise MigrationError("artifact-locations.migration-invalid", str(exc)) from exc

    try:
        assert_roundtrip_preserved(original, new_text, context=str(path))
    except YamlRoundTripLoss as exc:
        raise MigrationError("artifact-locations.migration-roundtrip-loss", str(exc)) from exc

    if new_text == original:
        return AppliedReport(False, 0, "already migrated: nothing to change")
    write_atomic(path, new_text)
    return AppliedReport(
        True, len(plan.entries), f"migrated {len(plan.entries)} legacy alias(es)"
    )


__all__ = [
    "AppliedReport",
    "MigrationEntry",
    "MigrationError",
    "MigrationPlan",
    "apply_migration",
    "build_migration_plan",
    "render_snippets",
]
