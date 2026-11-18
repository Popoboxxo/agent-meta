"""Resolve the ``artifact-locations`` matrix for Issue #1186 (T4).

This module is the single resolver for the artifact-location matrix: it merges
project config, YAML presets, schema-level defaults and code fallbacks field by
field, and reports where every value came from. It is a pure library — it never
calls ``sys.exit``, never writes to disk and never branches on a provider name.
Structural hard errors are raised as :class:`ArtifactLocationsError` with a
stable machine-readable ``code`` (the sync-time validator in ``config.py``
translates them into user-facing errors); the semantic validator itself is T5.

Four value sources (Spec §3.3, K3) with source attribution::

    project.yaml artifact-locations.*             -> "project"
    presets.yaml presets.<name>                   -> "preset:<name>"
                 (explicitly selected by project) -> "project-preset:<name>"
    schema "default"                              -> "schema-default"
    DEFAULT_* constants in this module            -> "code-fallback"

``disabled`` (master switch off), ``project-preset:<name>`` (selection
attribution) and ``project-alias:<old-key>`` (per-field alias attribution, D1)
are reported but are *not* additional value sources.
"""
from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Iterable, Optional

import yaml  # PyYAML: documented runtime exception (docs/adr/0001)

# ---------------------------------------------------------------------------
# Source attribution constants (public contract)
# ---------------------------------------------------------------------------
SOURCE_PROJECT = "project"
SOURCE_PRESET_PREFIX = "preset:"
SOURCE_PROJECT_PRESET_PREFIX = "project-preset:"
SOURCE_SCHEMA_DEFAULT = "schema-default"
SOURCE_CODE_FALLBACK = "code-fallback"
SOURCE_DISABLED = "disabled"
SOURCE_PROJECT_ALIAS_PREFIX = "project-alias:"

# Short aliases used by the plan's signature sketch.
SOURCE_PRESET = SOURCE_PRESET_PREFIX
SOURCE_PROJECT_PRESET = SOURCE_PROJECT_PRESET_PREFIX
SOURCE_ALIAS = SOURCE_PROJECT_ALIAS_PREFIX

_REPO_ROOT = Path(__file__).resolve().parents[2]
_PRESET_RELATIVE_PATH = Path("config") / "artifact-locations-presets.yaml"

_SCRATCH_ALIAS_KEY = "repo_containment.tmp-sink.path"
_BACKUP_MARKER = ".sync-backup-"


class ArtifactLocationsError(Exception):
    """A resolver-level error with a stable code and a human-readable message."""

    def __init__(self, code: str, message: str) -> None:
        self.code = code
        self.message = message
        super().__init__(f"{code}: {message}")


# ---------------------------------------------------------------------------
# Framework defaults / registry (code-fallback layer)
# ---------------------------------------------------------------------------
DEFAULT_MODE = "files"
DEFAULT_GIT = "tracked"
DEFAULT_RETENTION = "manual"
DEFAULT_SE_ROOT = "SE"
DEFAULT_SCRATCH_PATH = ".tmp"
DEFAULT_STATE_PATH = ".meta-viz"

#: Closed artifact-kind enum from the schema (20 values).
ALL_KINDS = (
    "code", "concept", "domain", "copyedit", "proofread", "se", "vv",
    "security", "dependency", "a11y", "lifecycle", "prompt", "ai-security",
    "analysis", "triage", "perf", "log", "research", "estimate", "conclusion",
)

#: Closed naming-token canon (Spec §3.2.1, D3).
NAMING_TOKENS = (
    "class", "date", "slug", "kind", "n", "topic", "scope", "nnn", "level",
    "folder",
)
_TOKEN_RE = re.compile(r"\{([^{}]*)\}")

_PERSISTENT_PATH_CLASSES = (
    "specs", "plans", "concepts", "spikes", "reviews", "audits", "analysis",
    "reports", "adr", "traceability", "runbooks",
)
_SE_CLASSES = (
    "se-requirements", "se-architecture", "se-decomposition", "se-interfaces",
    "se-implementation", "se-testplan", "se-validation", "se-verification",
    "se-decisions",
)

#: Naming-token applicability (Spec §3.2.1 table). ``class`` is allowed for
#: every class that carries a naming pattern; the two ephemeral classes and the
#: file-set class have no naming at all.
_TOKEN_APPLICABILITY: dict[str, frozenset[str]] = {
    "class": frozenset(_PERSISTENT_PATH_CLASSES + _SE_CLASSES),
    "date": frozenset(_PERSISTENT_PATH_CLASSES),
    "slug": frozenset(_PERSISTENT_PATH_CLASSES),
    "kind": frozenset({"reviews", "audits", "analysis", "reports"}),
    "n": frozenset({"specs", "plans", "concepts", "spikes", "runbooks"}),
    "topic": frozenset({
        "specs", "plans", "concepts", "spikes", "runbooks", "analysis",
    }),
    "scope": frozenset({"reviews", "reports", "traceability"}),
    "nnn": frozenset({"adr"}),
    "level": frozenset(_SE_CLASSES),
    "folder": frozenset(_SE_CLASSES),
}

#: Fields that have a schema-level default (the ``defaults`` object). Values
#: mirrored here are labelled ``schema-default``; everything else that comes
#: from this module's constants is labelled ``code-fallback``.
SCHEMA_DEFAULT_FIELDS = frozenset({"mode", "git", "naming", "retention"})


@dataclass(frozen=True)
class ClassSpec:
    """Static description of one of the 23 artifact classes."""

    name: str
    form: str  # directory | file-set | ephemeral | state | se
    default_path: str
    naming: Optional[str]
    kinds: tuple[str, ...] = ()
    subdir: str = ""


def _spec(
    name: str,
    form: str,
    default_path: str,
    naming: Optional[str],
    kinds: Iterable[str] = (),
    subdir: str = "",
) -> ClassSpec:
    return ClassSpec(name, form, default_path, naming, tuple(kinds), subdir)


CLASS_REGISTRY: dict[str, ClassSpec] = {
    spec.name: spec
    for spec in (
        _spec("specs", "directory", "docs/specs", "{date}-{slug}.md"),
        _spec("plans", "directory", "docs/plans", "{date}-{slug}.md"),
        _spec("concepts", "directory", "docs/concepts", "{date}-{slug}.md"),
        _spec("spikes", "directory", "docs/spikes", "{date}-issue-{n}-{topic}-spike.md"),
        _spec(
            "reviews", "directory", "docs/reviews", "{kind}-{date}-{slug}.md",
            ("code", "concept", "domain", "copyedit", "proofread", "se"),
        ),
        _spec(
            "audits", "directory", "docs/audits", "{kind}-{date}-{slug}.md",
            ("security", "dependency", "a11y", "lifecycle", "prompt", "ai-security"),
        ),
        _spec(
            "analysis", "directory", "docs/analysis", "{kind}-{date}-{slug}.md",
            ("analysis", "triage", "perf", "log", "research", "estimate", "conclusion"),
        ),
        _spec("reports", "directory", "docs/reports", "{date}-{slug}.md", ("vv",)),
        _spec("adr", "directory", "docs/adr", "ADR-{nnn}_{slug}.md"),
        _spec("traceability", "directory", "docs/traceability", "TRACE_{scope}.md"),
        _spec("runbooks", "directory", "docs/runbooks", "{date}-{slug}.md"),
        _spec("project-docs", "file-set", "", None),
        _spec("scratch", "ephemeral", DEFAULT_SCRATCH_PATH, None),
        _spec("state", "state", DEFAULT_STATE_PATH, None),
        _spec("se-requirements", "se", DEFAULT_SE_ROOT, "L{level}_{folder}_Requirements.md"),
        _spec("se-architecture", "se", DEFAULT_SE_ROOT, "L{level}_{folder}_Architecture.md"),
        _spec("se-decomposition", "se", DEFAULT_SE_ROOT, "L2_architectural_decomposition_iter-N.md"),
        _spec("se-interfaces", "se", DEFAULT_SE_ROOT, "L{level}_{folder}_Interfaces.md"),
        _spec(
            "se-implementation", "se", DEFAULT_SE_ROOT,
            "L{level}_{folder}_Impl.md", subdir="implementation",
        ),
        _spec(
            "se-testplan", "se", DEFAULT_SE_ROOT,
            "L{level}_{folder}_TestPlan.md", subdir="validation",
        ),
        _spec(
            "se-validation", "se", DEFAULT_SE_ROOT,
            "L{level}_{folder}_Validation.md", subdir="validation",
        ),
        _spec(
            "se-verification", "se", DEFAULT_SE_ROOT,
            "L{level}_{folder}_Verification.md", subdir="validation",
        ),
        _spec("se-decisions", "se", DEFAULT_SE_ROOT, "L{level}_{folder}_Decisions.md"),
    )
}


# ---------------------------------------------------------------------------
# Resolved data structures (the three dataclasses of the public contract)
# ---------------------------------------------------------------------------
@dataclass
class ResolvedClass:
    """Effective values for one artifact class plus per-field attribution."""

    name: str
    path: str = ""
    mode: str = DEFAULT_MODE
    git: str = DEFAULT_GIT
    naming: Optional[str] = None
    archive: Optional[str] = None
    retention: str = DEFAULT_RETENTION
    kinds: tuple[str, ...] = ()
    subdir: str = ""
    subdirs: dict[str, str] = field(default_factory=dict)
    event_log: Optional[str] = None
    files: dict[str, str] = field(default_factory=dict)
    source: str = ""
    field_sources: dict[str, str] = field(default_factory=dict)
    fallback_parent: Optional[str] = None


@dataclass
class ResolvedMatrix:
    """Effective artifact-location matrix for one config."""

    classes: dict[str, ResolvedClass] = field(default_factory=dict)
    legacy: tuple[str, ...] = ()
    unmanaged: tuple[str, ...] = ()
    preset: Optional[str] = None
    enabled: bool = True
    strict: bool = False
    source: str = ""


# ---------------------------------------------------------------------------
# Pure validation helpers (validate_* contract; T5 turns them into sync errors)
# ---------------------------------------------------------------------------
def validate_preset(name: str, presets: dict) -> str:
    """Return ``name`` or raise ``artifact-locations.unknown-preset``."""
    if not isinstance(presets, dict) or name not in presets:
        raise ArtifactLocationsError(
            "artifact-locations.unknown-preset", f"unknown preset '{name}'",
        )
    return name


def validate_path(path: Any, class_name: str) -> str:
    """Validate a project-relative class path (no absolute path, no ``..``)."""
    if (
        not isinstance(path, str)
        or not path
        or path.startswith("/")
        or re.match(r"^[A-Za-z]:", path)
        or any(part == ".." for part in path.replace("\\", "/").split("/"))
    ):
        raise ArtifactLocationsError(
            "artifact-locations.path-invalid",
            f"invalid 'artifact-locations.classes.{class_name}.path': "
            "must stay inside the project root",
        )
    return path


def validate_subdir(subdir: Any, class_name: str) -> str:
    """An SE leaf ``subdir`` is a single path segment (or the empty string)."""
    if not isinstance(subdir, str) or "/" in subdir or ".." in subdir:
        raise ArtifactLocationsError(
            "artifact-locations.subdir-invalid",
            f"invalid 'artifact-locations.classes.{class_name}.subdir': "
            "must be a single path segment",
        )
    return subdir


def validate_kind(kind: Any, class_name: str, allowed: Optional[Iterable[str]] = None) -> str:
    """Validate one kind against its class scope (or the global enum)."""
    allowed_set = frozenset(allowed if allowed is not None else CLASS_REGISTRY[class_name].kinds)
    if kind not in allowed_set:
        raise ArtifactLocationsError(
            "artifact-locations.kind-invalid",
            f"invalid 'artifact-locations.classes.{class_name}.kind': "
            f"'{kind}' is not a known artifact kind",
        )
    return kind


def validate_naming(naming: Any, class_name: str) -> str:
    """Validate a naming pattern against the closed token canon (D3)."""
    allowed = " ".join("{" + token + "}" for token in NAMING_TOKENS)
    if not isinstance(naming, str) or not naming:
        raise ArtifactLocationsError(
            "artifact-locations.naming-invalid",
            f"invalid 'artifact-locations.classes.{class_name}.naming': "
            f"empty pattern (allowed: {allowed})",
        )
    if "/" in naming or "\\" in naming or ".." in naming or "<" in naming or ">" in naming:
        raise ArtifactLocationsError(
            "artifact-locations.naming-invalid",
            f"invalid 'artifact-locations.classes.{class_name}.naming': "
            f"no path separator, '..' or <TOKEN> display form (allowed: {allowed})",
        )
    for token in _TOKEN_RE.findall(naming):
        if token not in NAMING_TOKENS:
            raise ArtifactLocationsError(
                "artifact-locations.naming-invalid",
                f"invalid 'artifact-locations.classes.{class_name}.naming': "
                f"unknown token '{{{token}}}' (allowed: {allowed})",
            )
        if class_name not in _TOKEN_APPLICABILITY[token]:
            raise ArtifactLocationsError(
                "artifact-locations.naming-invalid",
                f"invalid 'artifact-locations.classes.{class_name}.naming': "
                f"token '{{{token}}}' is not applicable to class '{class_name}' "
                f"(allowed: {allowed})",
            )
    if not naming.endswith(".md"):
        raise ArtifactLocationsError(
            "artifact-locations.naming-invalid",
            f"invalid 'artifact-locations.classes.{class_name}.naming': "
            f"persistent file classes need a '.md' ending (allowed: {allowed})",
        )
    return naming


# ---------------------------------------------------------------------------
# Preset loading and scratch alias (D1)
# ---------------------------------------------------------------------------
def load_presets(agent_meta_root: Optional[Path]) -> dict[str, dict]:
    """Load ``config/artifact-locations-presets.yaml``; missing file => {}.

    An empty result triggers the ``code-fallback`` layer instead of a silent
    framework default, so callers can always explain where a value came from.
    """
    root = Path(agent_meta_root) if agent_meta_root is not None else _REPO_ROOT
    preset_path = root / _PRESET_RELATIVE_PATH
    if not preset_path.exists():
        return {}
    try:
        payload = yaml.safe_load(preset_path.read_text(encoding="utf-8")) or {}
    except (OSError, yaml.YAMLError):
        return {}
    if not isinstance(payload, dict):
        return {}
    presets = payload.get("presets", {})
    return presets if isinstance(presets, dict) else {}


def resolve_scratch_path(config: dict, classes: dict) -> tuple[str, str]:
    """Resolve the single scratch path and its attribution (D1).

    ``classes.scratch.path`` is the only source. The containment key is a
    migration alias read only while the class is absent; when both are set
    their values must be equal (divergence is a hard error in T5).

    Returns: ``(path, attribution)`` where attribution is ``"project"``,
    ``"project-alias:repo_containment.tmp-sink.path"`` or ``"schema-default"``.
    """
    scratch = (classes or {}).get("scratch", {}) or {}
    class_path = scratch.get("path")
    containment = (config or {}).get("repo_containment", {}) or {}
    tmp_sink = containment.get("tmp-sink", {}) or {}
    alias_path = tmp_sink.get("path")
    alias_source = SOURCE_PROJECT_ALIAS_PREFIX + _SCRATCH_ALIAS_KEY

    if class_path is not None and alias_path is not None and class_path != alias_path:
        raise ArtifactLocationsError(
            "artifact-locations.scratch-sink-divergence",
            f"invalid 'artifact-locations.classes.scratch.path' vs "
            f"'{_SCRATCH_ALIAS_KEY}': values diverge — keep one source "
            "(artifact-locations.classes.scratch.path) and remove the legacy key",
        )
    if class_path is not None:
        validate_path(class_path, "scratch")
        return class_path, SOURCE_PROJECT
    if alias_path is not None:
        validate_path(alias_path, "scratch")
        return alias_path, alias_source
    return DEFAULT_SCRATCH_PATH, SOURCE_SCHEMA_DEFAULT


def validate_scratch_sources(config: dict, classes: dict) -> tuple[str, str]:
    """Validate the single-source invariant (D1) and return the resolved path.

    Divergent values raise ``artifact-locations.scratch-sink-divergence`` even
    when the matrix master switch is off: two write targets for one sink are
    never acceptable (Spec §4.1 structural check).
    """
    return resolve_scratch_path(config, classes)


# ---------------------------------------------------------------------------
# Naming / cell path / SE projection helpers
# ---------------------------------------------------------------------------
def _format_level(level: Any) -> str:
    """Cell directory spelling of a level: ``L3`` (used for the L<n> folder)."""
    if level is None or level == "":
        return ""
    text = str(level)
    return text if text.startswith("L") else f"L{text}"


def _level_token(level: Any) -> str:
    """Naming-token spelling of a level: bare number (the pattern carries ``L``)."""
    if level is None or level == "":
        return ""
    text = str(level)
    return text[1:] if text.startswith("L") else text


def resolve_artifact_naming(
    matrix: Optional[ResolvedMatrix],
    name: str,
    *,
    kind: Optional[str] = None,
    scope: Optional[str] = None,
    **tokens: Any,
) -> str:
    """Resolve a class naming pattern into a concrete file name (D3).

    Unknown or class-inapplicable tokens raise
    ``artifact-locations.naming-invalid``; ``{nnn}`` is zero-padded to three
    digits and ``{level}`` accepts ``3`` or ``L3``.
    """
    if name not in CLASS_REGISTRY:
        raise ArtifactLocationsError(
            "artifact-locations.naming-invalid", f"unknown class '{name}'",
        )
    if matrix is not None and name in matrix.classes:
        pattern = matrix.classes[name].naming
    else:
        pattern = CLASS_REGISTRY[name].naming
    if not pattern:
        raise ArtifactLocationsError(
            "artifact-locations.naming-invalid",
            f"class '{name}' has no naming pattern",
        )
    validate_naming(pattern, name)
    if kind is not None:
        validate_kind(kind, name)

    substitutions = {
        "class": name,
        "date": tokens.get("date", ""),
        "slug": tokens.get("slug", ""),
        "kind": kind if kind is not None else tokens.get("kind", ""),
        "n": str(tokens.get("n", "")),
        "topic": tokens.get("topic", tokens.get("slug", "")),
        "scope": scope if scope is not None else tokens.get("scope", ""),
        "nnn": (
            str(tokens.get("nnn", tokens.get("n"))).zfill(3)
            if tokens.get("nnn", tokens.get("n")) not in (None, "") else ""
        ),
        "level": _level_token(tokens.get("level")),
        "folder": tokens.get("folder", ""),
    }
    for token in _TOKEN_RE.findall(pattern):
        if not substitutions.get(token):
            raise ArtifactLocationsError(
                "artifact-locations.naming-invalid",
                f"missing value for token '{{{token}}}' in class '{name}'",
            )
    return pattern.format(**substitutions)


def resolve_artifact_cell_path(
    name: str,
    level: Any,
    folder: str,
    is_system: bool,
    *,
    matrix: Optional[ResolvedMatrix] = None,
    config: Optional[dict] = None,
    agent_meta_root: Optional[Path] = None,
    project_root: Optional[Path] = None,
) -> str:
    """Compute the write path of one SE cell artifact.

    Layout: ``<class path>/L<n>/<Folder><System|Component>[/<subdir>]/<file>``.
    The cell hierarchy is SE identity model, not configurable; only the root
    path, the leaf subdir and the naming pattern come from the matrix.
    """
    if matrix is None:
        matrix = resolve_artifact_locations(config or {}, agent_meta_root, project_root)
    if name not in matrix.classes:
        raise ArtifactLocationsError(
            "artifact-locations.path-invalid", f"unknown class '{name}'",
        )
    cls = matrix.classes[name]
    suffix = "System" if is_system else "Component"
    segments = [
        cls.path,
        _format_level(level),
        f"{folder}{suffix}",
        cls.subdir,
        resolve_artifact_naming(matrix, name, level=level, folder=folder),
    ]
    return "/".join(segment for segment in segments if segment)


def resolve_se_projection(
    name: str,
    *,
    matrix: Optional[ResolvedMatrix] = None,
    se_root: Optional[str] = None,
) -> str:
    """Derive one of the four SE-global projection paths (D-7).

    The projections follow ``ARTIFACT_SE_ROOT`` exclusively; they are not
    config fields. The ADR leaf is the taxonomy spelling ``ADR`` (Spec §12,
    remaining point 1), the other three leaves are lower-case.
    """
    leaf_key = name[3:] if name.startswith("se-") else name
    if leaf_key not in {"reviews", "reports", "adr", "traceability"}:
        raise ArtifactLocationsError(
            "artifact-locations.path-invalid",
            f"unknown SE projection '{name}'",
        )
    if se_root is None and matrix is not None:
        requirements = matrix.classes.get("se-requirements")
        se_root = requirements.path if requirements is not None else None
    root = se_root or DEFAULT_SE_ROOT
    leaf = "ADR" if leaf_key == "adr" else leaf_key
    return f"{root}/{leaf}"


def artifact_file_stats(names: Iterable[str]) -> tuple[int, Optional[str]]:
    """Count artifact files and return the newest name, ignoring backup siblings.

    ``*.sync-backup-*`` files are tooling artifacts (#1195) and must never
    contribute to counts or to the "newest artifact" reported by T15.
    """
    kept = sorted(name for name in names if _BACKUP_MARKER not in name)
    return len(kept), kept[-1] if kept else None


# Plan's short signature aliases (both names are part of the public contract).
resolve_cell_path = resolve_artifact_cell_path
resolve_naming = resolve_artifact_naming


# ---------------------------------------------------------------------------
# Main resolver
# ---------------------------------------------------------------------------
def _domain_source(field_sources: dict[str, str]) -> str:
    """Pick the highest-priority source for a class (field-wise detail stays intact)."""
    sources = set(field_sources.values())
    if any(
        source == SOURCE_PROJECT or source.startswith(SOURCE_PROJECT_ALIAS_PREFIX)
        for source in sources
    ):
        return SOURCE_PROJECT
    for source in sources:
        if source.startswith(SOURCE_PROJECT_PRESET_PREFIX):
            return source
    for source in sources:
        if source.startswith(SOURCE_PRESET_PREFIX):
            return source
    if SOURCE_SCHEMA_DEFAULT in sources:
        return SOURCE_SCHEMA_DEFAULT
    if SOURCE_CODE_FALLBACK in sources:
        return SOURCE_CODE_FALLBACK
    if SOURCE_DISABLED in sources:
        return SOURCE_DISABLED
    return next(iter(sources), "")


def _base_value(spec: ClassSpec, field_name: str) -> Any:
    """Code-fallback value for one field of one class."""
    if field_name == "path":
        return spec.default_path
    if field_name == "mode":
        return DEFAULT_MODE
    if field_name == "git":
        return "ignored" if spec.form in {"ephemeral", "state"} else DEFAULT_GIT
    if field_name == "naming":
        return spec.naming
    if field_name == "retention":
        return "keep" if spec.form == "state" else DEFAULT_RETENTION
    if field_name == "kinds":
        return spec.kinds
    if field_name == "subdir":
        return spec.subdir
    if field_name == "subdirs":
        if spec.form == "ephemeral":
            return {name: f"{spec.default_path}/{name}" for name in ("logs", "test-output", "drafts")}
        if spec.form == "state":
            return {
                name: f"{spec.default_path}/{name}"
                for name in ("progress", "checkpoints", "handoffs")
            }
        return {}
    if field_name == "event-log":
        return f"{DEFAULT_STATE_PATH}/events.jsonl" if spec.form == "state" else None
    if field_name == "files":
        if spec.name == "project-docs":
            return {
                "architecture": "docs/ARCHITECTURE.md",
                "codebase-overview": "docs/CODEBASE_OVERVIEW.md",
                "requirements": "docs/REQUIREMENTS.md",
                "issue-labels": "docs/issue-labels.md",
            }
        return {}
    if field_name == "archive":
        return None
    return None


def _coerce(field_name: str, value: Any) -> Any:
    if field_name == "kinds":
        return tuple(value or ())
    if field_name in {"subdirs", "files"}:
        return dict(value or {})
    return value


def _additive_list(preset_values: Any, project_values: Any) -> tuple[str, ...]:
    combined: list[str] = []
    for source in (preset_values or (), project_values or ()):
        for entry in source:
            if entry not in combined:
                combined.append(entry)
    return tuple(combined)


def resolve_artifact_locations(
    config: dict,
    agent_meta_root: Optional[Path] = None,
    project_root: Optional[Path] = None,
) -> ResolvedMatrix:
    """Resolve the full artifact-location matrix for one config.

    Pure with respect to ``config`` (never mutated) and total on ``{}``. The
    effective ``source`` of each class is the highest-priority field source;
    ``field_sources`` keeps the per-field detail (Rule 1).
    """
    config = config or {}
    section = config.get("artifact-locations") or {}
    if not isinstance(section, dict):
        section = {}

    enabled = section.get("enabled", True)
    strict = section.get("strict", False)
    preset_name = section.get("preset")
    presets = load_presets(agent_meta_root)
    project_classes = section.get("classes") or {}
    if not isinstance(project_classes, dict):
        project_classes = {}
    project_defaults = section.get("defaults") or {}
    if not isinstance(project_defaults, dict):
        project_defaults = {}
    section_is_empty = not section

    if preset_name is not None:
        validate_preset(preset_name, presets)

    # Framework default preset is always the base; an explicitly selected
    # preset merges on top (presets only restate deviations by design).
    framework = presets.get("default", {}) if presets else {}
    selected = presets.get(preset_name, {}) if preset_name and presets else {}
    framework_classes = framework.get("classes", {}) if isinstance(framework, dict) else {}
    selected_classes = selected.get("classes", {}) if isinstance(selected, dict) else {}

    if presets and section_is_empty:
        # No preset key at all: the framework baseline is the schema-default
        # layer, not a named preset.
        fallback_source = SOURCE_SCHEMA_DEFAULT
    elif presets:
        fallback_source = SOURCE_PRESET_PREFIX + "default"
    else:
        fallback_source = SOURCE_CODE_FALLBACK

    matrix = ResolvedMatrix(
        preset=preset_name,
        enabled=enabled,
        strict=strict,
        source=fallback_source,
    )

    for name, spec in CLASS_REGISTRY.items():
        layers: dict[str, Any] = {}
        sources: dict[str, str] = {}

        for layer, label in (
            (framework_classes, SOURCE_PRESET_PREFIX + "default"),
            (selected_classes, SOURCE_PROJECT_PRESET_PREFIX + str(preset_name)),
        ):
            entry = layer.get(name, {}) or {}
            if not isinstance(entry, dict):
                continue
            for field_name, value in entry.items():
                layers[field_name] = value
                sources[field_name] = label

        project_entry = project_classes.get(name, {}) or {}
        if not isinstance(project_entry, dict):
            project_entry = {}

        field_sources: dict[str, str] = {}
        values: dict[str, Any] = {}
        for field_name in (
            "path", "mode", "git", "naming", "archive", "retention", "kinds",
            "subdir", "subdirs", "event-log", "files",
        ):
            value = _base_value(spec, field_name)
            source = (
                SOURCE_SCHEMA_DEFAULT
                if field_name in SCHEMA_DEFAULT_FIELDS and presets
                else fallback_source
            )

            if field_name in layers:
                value = layers[field_name]
                source = (
                    fallback_source
                    if section_is_empty
                    else sources[field_name]
                )

            # Project defaults are field inheritance inside the project source.
            # They only apply to fields the class form actually declares (e.g.
            # a file-set/ephemeral class has no ``naming`` or ``mode``).
            field_applicable = (
                field_name != "naming" or spec.naming is not None
            ) and (
                field_name != "mode" or spec.form not in {"ephemeral", "state", "file-set"}
            )
            if (
                field_name in project_defaults
                and field_name in SCHEMA_DEFAULT_FIELDS
                and field_applicable
            ):
                value = project_defaults[field_name]
                source = SOURCE_PROJECT

            # Project class entry is the highest-priority layer.
            if field_name in project_entry:
                value = project_entry[field_name]
                source = SOURCE_PROJECT

            value = _coerce(field_name, value)
            if field_name == "path" and value:
                validate_path(value, name)
            if field_name == "subdir" and spec.form == "se":
                validate_subdir(value, name)
            if field_name == "kinds":
                for kind_value in value:
                    validate_kind(kind_value, name, allowed=ALL_KINDS)
            if field_name == "naming" and value:
                validate_naming(value, name)

            values[field_name] = value
            field_sources[field_name] = source

        # D1: single scratch source with alias attribution.
        if name == "scratch":
            scratch_path, scratch_source = resolve_scratch_path(config, project_classes)
            values["path"] = scratch_path
            field_sources["path"] = SOURCE_PROJECT if scratch_source == SOURCE_PROJECT else scratch_source
            alias_in_config = (
                ((config.get("repo_containment") or {}).get("tmp-sink") or {}).get("path")
            )
            if alias_in_config is not None and scratch_source == SOURCE_PROJECT:
                field_sources["path-alias"] = (
                    SOURCE_PROJECT_ALIAS_PREFIX + _SCRATCH_ALIAS_KEY
                )
            if not presets:
                field_sources["path"] = fallback_source
            if section_is_empty:
                field_sources["path"] = SOURCE_SCHEMA_DEFAULT
            if not enabled:
                field_sources["path"] = SOURCE_DISABLED

        # Spec §3.6: state is a projection of progress.* / viz.event_log.
        if name == "state":
            progress = config.get("progress") or {}
            viz = config.get("viz") or {}
            alias_pairs = (
                ("dir", "progress", "progress.dir"),
                ("checkpoint-dir", "checkpoints", "progress.checkpoint-dir"),
                ("handoffs-dir", "handoffs", "progress.handoffs-dir"),
            )
            for config_key, target_key, alias_key in alias_pairs:
                if config_key in progress:
                    subdirs = dict(values["subdirs"])
                    subdirs[target_key] = progress[config_key]
                    values["subdirs"] = subdirs
                    field_sources["subdirs"] = SOURCE_PROJECT_ALIAS_PREFIX + alias_key
            if "event_log" in viz:
                values["event-log"] = viz["event_log"]
                field_sources["event-log"] = SOURCE_PROJECT_ALIAS_PREFIX + "viz.event_log"

        fallback_parent = project_entry.get(
            "fallback-parent", layers.get("fallback-parent"),
        )

        if not enabled:
            # Master switch off: today's paths, nothing redirected (Rule 5).
            for field_name in field_sources:
                field_sources[field_name] = SOURCE_DISABLED

        resolved = ResolvedClass(
            name=name,
            path=values["path"],
            mode=values["mode"],
            git=values["git"],
            naming=values["naming"],
            archive=values["archive"],
            retention=values["retention"],
            kinds=values["kinds"],
            subdir=values["subdir"],
            subdirs=values["subdirs"],
            event_log=values["event-log"],
            files=values["files"],
            source=SOURCE_DISABLED if not enabled else _domain_source(field_sources),
            field_sources=field_sources,
            fallback_parent=fallback_parent,
        )
        matrix.classes[name] = resolved

    # legacy[] and unmanaged[] are read-only, additive framework lists (D-8).
    matrix.legacy = _additive_list(
        framework.get("legacy") if isinstance(framework, dict) else (),
        section.get("legacy"),
    )
    matrix.unmanaged = _additive_list(
        framework.get("unmanaged") if isinstance(framework, dict) else (),
        section.get("unmanaged"),
    )

    return matrix


__all__ = [
    "ALL_KINDS",
    "CLASS_REGISTRY",
    "DEFAULT_SE_ROOT",
    "SOURCE_CODE_FALLBACK",
    "SOURCE_DISABLED",
    "SOURCE_PRESET",
    "SOURCE_PRESET_PREFIX",
    "SOURCE_PROJECT",
    "SOURCE_PROJECT_ALIAS_PREFIX",
    "SOURCE_PROJECT_PRESET",
    "SOURCE_PROJECT_PRESET_PREFIX",
    "SOURCE_SCHEMA_DEFAULT",
    "NAMING_TOKENS",
    "ArtifactLocationsError",
    "ClassSpec",
    "ResolvedClass",
    "ResolvedMatrix",
    "artifact_file_stats",
    "load_presets",
    "resolve_artifact_cell_path",
    "resolve_artifact_locations",
    "resolve_artifact_naming",
    "resolve_cell_path",
    "resolve_naming",
    "resolve_scratch_path",
    "resolve_se_projection",
    "validate_kind",
    "validate_naming",
    "validate_path",
    "validate_preset",
    "validate_scratch_sources",
    "validate_subdir",
]
