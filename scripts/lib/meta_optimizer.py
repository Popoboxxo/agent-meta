"""Config-optimizer runner and losslessness proof (IC-24/IC-25).

Read-only analysis of ``.meta-config/project.yaml``: it proposes removal
candidates and proves (L0) that removing them keeps every generated artifact of
every active provider byte-identical. All output goes below
``<tmp-sink>/meta-optimizer/<run_id>/`` (``proposal.json``, ``proposal.diff``,
``proof.json``); the project and the framework root are never written to, and the
system temp directory is never used (IC-34, AC-54/75/94).

Candidate search (IC-24): a *sentinel* copy of the config -- every text value
under ``variables:`` wrapped in ``QZ<NAME>QZ...ZQ<NAME>ZQ`` -- is rendered into
``<run>/work/`` through the regular sync codepath, then the substitutions are
counted per provider artifact (``fan_out``). ``occurrences == 0`` means the value
never reaches an artifact of the current active set. The L0 proof renders the
config verbatim and again without the removable keys and compares both trees,
including the render-derived sidecars
``.meta-config/{auto-commit-allowlist,generated-file-hashes,context-hashes}.json``
(AC-55 Rev. 3).

Credential paths (IC-35 ``credentials``: name patterns, explicit keys,
``scan_for_secrets`` when the registry's ``value_scan`` says so) are excluded
completely -- no candidate, no hint, no ``FanOutEntry`` and no value anywhere in
the sink (AC-89); credential source lines inside diff context are replaced by a
deterministic redaction marker. To keep AC-89 watertight, **the render scratch is
removed before the runner returns** (review F1, option (a)): the sentinel render
and both proof renders are deleted, so only ``proposal.json``, ``proposal.diff``
and ``proof.json`` remain below ``<tmp-sink>/meta-optimizer/``. Deleting the
scratch is the minimal change that guarantees no credential byte sequence and no
unredacted config copy survives under the sink, while the renders themselves
still use the real config, so L0 stays honest. Semantic kinds
(``duplicate-value``, ``relocate-*``, ``semantic-merge``) are hints only
(``applicable: false``, no hunk, no proof level) and appear only with
``--include-semantic`` (AC-57/91).

Entry points: :func:`collect_candidates`, :func:`fan_out_counts`,
:func:`prove`, :func:`comparison_file_digests`, :func:`advance_l0`, the CLI
runner :func:`run_optimize_config` and the remove-only applier
:func:`apply_config_patch`.

The applier (IC-24 "Applier", AC-55/56/75/80/89/90/91/94) is the *only* writer:
it reads ``project_yaml_sha256``, the candidate IDs, ``agent_meta_version`` and
``generator_options`` from ``proposal.json``, recomputes the candidates with
:func:`collect_candidates`, reconciles the redacted hunks (a hunk that inserts a
line is not remove-only, a hunk that differs from the recomputed one is a
``hunk-mismatch``) and replaces ``.meta-config/project.yaml`` atomically from a
scratch file below the sink. All-or-nothing: any rejection, a failed proof, a
version/TOCTOU/preview mismatch leaves the config untouched. The backup is
redacted, ``applied.json`` records ``approval_source: "relayed"`` and only key
*names* (AC-89), and every sink artifact is mode ``0600``.
"""
from __future__ import annotations

import copy
import difflib
import hashlib
import json
import os
import re
import shutil
import subprocess
import sys
from collections import Counter
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Literal, Mapping, Optional, Sequence, Tuple

import yaml

from lib.active_set import compute_active_set
from lib.config import build_variables, read_version
from lib.context_report import merge_provider_mappings
from lib.permissions import restrict_owner_only
from lib.providers import (
    load_provider_capabilities,
    load_providers_config,
    resolve_providers,
)
from lib.repo_containment import (
    TmpSinkError,
    resolve_out_path,
    resolve_output_dir,
    resolve_work_dir,
    work_dir_env,
)
from lib.secrets import scan_for_secrets
from lib.variables import strip_inactive_conditional_blocks
from lib.yaml_roundtrip import RoundTripReport, _count_comments, analyze_roundtrip

__all__ = [
    "CandidateKind", "Scope", "Mark", "Candidate", "FanOutEntry",
    "OptimizerProposal", "ProofReport", "ApplyReport", "L0_COMPARISON_FILES",
    "CONTENT_LOSS_THRESHOLD_BYTES", "OPTIMIZER_SUBDIR", "SEMANTIC_KINDS",
    "RegistryError", "credential_paths", "collect_candidates",
    "sentinel_wrapped_names", "fan_out_counts", "prove",
    "comparison_file_digests", "advance_l0", "run_optimize_config",
    "apply_config_patch", "apply_summary",
    "STALE_PROPOSAL_CODE", "VERSION_MISMATCH_CODE", "NOT_REMOVE_ONLY_CODE",
    "PREVIEW_MISMATCH_CODE", "CROSS_DEVICE_CODE", "USAGE_CODE",
    "REJECT_NOT_REPRODUCIBLE", "REJECT_HUNK_MISMATCH", "REJECT_NOT_APPLICABLE",
    "REJECT_CREDENTIAL_KEY", "REJECT_NEEDS_RUNTIME", "APPROVAL_SOURCE_RELAYED",
]

#: Sink subdirectory of the optimizer (IC-34).
OPTIMIZER_SUBDIR = "meta-optimizer"
#: Values longer than this are relocated, not deleted (IC-24 step 2).
CONTENT_LOSS_THRESHOLD_BYTES = 200
#: Stable error codes (IC-24/IC-25).
PROOF_FAILED_CODE = "meta-optimizer.proof-failed"
RENDER_FAILED_CODE = "meta-optimizer.render-failed"
LOSSY_FLAG_CODE = "meta-optimizer.lossy-flag"
OUT_WRITE_FAILED_CODE = "meta-optimizer.out-write-failed"
#: Proof levels (IC-25).
PROOF_LEVELS = ("none", "L0", "L1", "L2", "L3")
#: Hint-only candidate kinds (AC-57/91).
SEMANTIC_KINDS = ("duplicate-value", "relocate-to-ext", "relocate-to-doc", "semantic-merge")
#: Render-derived sidecars that the L0 comparison set must include (AC-55 Rev. 3).
L0_COMPARISON_FILES = (
    ".meta-config/auto-commit-allowlist.json",
    ".meta-config/generated-file-hashes.json",
    ".meta-config/context-hashes.json",
)
#: Run-scoped bookkeeping written by the render but not a generated artifact.
_NON_ARTIFACT_FILES = ("sync.log",)
#: The render's verbatim copy of the input config (not a generated artifact).
_INPUT_CONFIG_COPY = ".meta-config/project.yaml"
#: Scope of what L0 proves (IC-25 Rev. 3, B-1/B-3).
SCOPE_NOTE = (
    "L0 proves byte-equality of the generated artifacts in the CURRENT active set only.",
    "It does not prove the behaviour of runtime readers (IC-35) nor the effect "
    "after a later role/provider activation.",
)
_RUNTIME_READER_WARNING = (
    "A runtime reader consumes this key outside the render; removing it is only "
    "proven for the render, not for the reader."
)
_REACTIVATION_WARNING = (
    "If the role/provider that renders this key is activated later, the value is no "
    "longer available; the placeholder then stays unresolved or falls back to the "
    "framework default."
)
_REDACTION_MARKER = "<redacted credential, {} bytes>"
_REGISTRY_RELPATH = "config/runtime-config-readers.yaml"

#: Applier error codes (IC-24 "Applier"/"Vorschau und Anwendung", Rev. 3.1).
STALE_PROPOSAL_CODE = "meta-optimizer.stale-proposal"
VERSION_MISMATCH_CODE = "meta-optimizer.version-mismatch"
NOT_REMOVE_ONLY_CODE = "meta-optimizer.not-remove-only"
PREVIEW_MISMATCH_CODE = "meta-optimizer.preview-mismatch"
CROSS_DEVICE_CODE = "meta-optimizer.cross-device"
USAGE_CODE = "meta-optimizer.usage"
#: Per-candidate rejection reasons (spec line 1489).
REJECT_NOT_REPRODUCIBLE = "not-reproducible"
REJECT_HUNK_MISMATCH = "hunk-mismatch"
REJECT_NOT_APPLICABLE = "not-applicable"
REJECT_CREDENTIAL_KEY = "credential-key"
REJECT_NEEDS_RUNTIME = "needs-runtime-confirmation"
#: ``applied.json.approval_source``: this spec only ever writes the *relayed*
#: user answer; ``permission-prompt`` is reserved (ADR-17, N-1) and must never
#: appear, so the value is a hard constant rather than a parameter.
APPROVAL_SOURCE_RELAYED = "relayed"
#: Sink artifacts of one applier run (AC-75/AC-90).
PREVIEW_NAME = "preview.json"
APPLIED_NAME = "applied.json"
BACKUP_NAME = "project.yaml.bak"
#: Transient scratch file for the atomic replace, inside the run dir (Rev. 3.3).
_TRANSIENT_CONFIG_NAME = "project.yaml.new"
#: The project config the applier rewrites (IC-24).
_PROJECT_CONFIG_RELPATH = Path(".meta-config") / "project.yaml"
_APPLIER_TOOL = "apply-config-patch"
_REDACTION_RE = re.compile(r"<redacted credential, \d+ bytes>")

#: Test seam (AC-90, TOCTOU): called immediately before the atomic replace, after
#: the config was read back for the hash re-check. Always ``None`` in production.
_TOCTOU_TEST_HOOK: Optional[Callable[[], None]] = None

CandidateKind = Literal[
    "no-effect",                  # removing is byte-identical (builder-overridden, default, unused)
    "dead-variable-content-loss",  # no-effect, but substantial content -> relocate, do not delete
    "duplicate-value",            # same value under two keys
    "relocate-to-ext",            # role-specific content -> <prefix>-<role>-ext.md
    "relocate-to-doc",            # high fan-out -> doc file + pointer
    "semantic-merge",             # content merge
    "inactive-scope",             # only ineffective for inactive roles/providers
    "structural-simplify",        # structural key expressible more compactly (hint only)
    "info-only",                  # hint without a hunk
]
Scope = Literal[
    "variables", "roles", "providers", "auto_commit", "hooks",
    "repo_containment", "orchestrator", "structural-other",
]
Mark = Literal[
    "runtime-reader", "refilled-by-defaults", "inactive-scope",
    "reactivation-loss-warning",
]


@dataclass(frozen=True)
class Candidate:
    """One optimizer candidate (IC-24 Rev. 3 / ADR-18)."""

    id: str
    kind: CandidateKind
    yaml_path: str
    scope: Scope
    marks: Tuple[Mark, ...] = ()
    approval_level: Literal["confirm", "confirm-runtime"] = "confirm"
    warnings: Tuple[str, ...] = ()
    deterministic: bool = False
    applicable: bool = False
    proof_level_required: Literal["none", "L0", "L1", "L2", "L3"] = "none"
    yaml_bytes_saved: int = 0
    injected_bytes_saved_est: int = 0
    rationale: str = ""
    hunks: Tuple[str, ...] = ()


@dataclass(frozen=True)
class FanOutEntry:
    """Per-variable sentinel fan-out (IC-24 step 1, AC-58).

    Conditional variables (spec lines 1445-1449) are never sentinel-wrapped;
    they appear with ``occurrences: null`` (``None``), ``files: null``,
    ``injected_bytes: 0``, zeroed ``per_provider`` and ``conditional: true``.
    """

    variable: str
    value_bytes: int
    occurrences: Optional[int]
    files: Optional[int]
    injected_bytes: int
    per_provider: Mapping[str, int]
    conditional: bool = False


@dataclass(frozen=True)
class OptimizerProposal:
    """The optimizer's read-only proposal (IC-24)."""

    project_yaml_sha256: str
    agent_meta_version: str
    generator_options: Mapping[str, Any]
    candidates: Tuple[Candidate, ...]
    fan_out: Tuple[FanOutEntry, ...]
    diff: str


@dataclass(frozen=True)
class ProofReport:
    """Losslessness proof result (IC-25)."""

    level_reached: Literal["none", "L0", "L1", "L2", "L3"]
    files_compared: int
    byte_equal_files: int
    changed_files: Tuple[str, ...]
    placeholder_sets_equal: bool
    unresolved_placeholders_before: int
    unresolved_placeholders_after: int
    token_multiset_equal: bool
    anchors_ok: bool
    relocation_reachable: Optional[bool]
    roundtrip: RoundTripReport
    expected_comment_loss: int
    ok: bool
    reasons: Tuple[str, ...]
    scope_note: Tuple[str, ...] = SCOPE_NOTE


@dataclass(frozen=True)
class ApplyReport:
    """Outcome of :func:`apply_config_patch` (IC-24 "Applier", AC-80 (d)).

    ``exit_code`` is the process exit code the CLI returns: 0 when every accepted
    candidate was applied (or the preview was written), 1 when anything was
    rejected or a global check failed (then nothing was written), 2 on a usage,
    sink or render error. ``code`` carries the stable error code of the failure
    (``meta-optimizer.*``); ``rejected`` holds ``(id, reason)`` pairs and
    ``applied_ids`` the accepted IDs (for a preview: the ones the preview
    contains, which have not been written yet).
    """

    applied_ids: Tuple[str, ...] = ()
    rejected: Tuple[Tuple[str, str], ...] = ()
    preview_sha256: str = ""
    project_yaml_sha256_before: str = ""
    project_yaml_sha256_after: str = ""
    backup_redacted_keys: Tuple[str, ...] = ()
    log_path: Optional[str] = None
    preview_path: Optional[str] = None
    run_dir: Optional[str] = None
    agent_meta_version: str = ""
    generator_options: Mapping[str, Any] = field(default_factory=dict)
    approval_source: str = APPROVAL_SOURCE_RELAYED
    exit_code: int = 0
    code: str = ""
    errors: Tuple[str, ...] = ()
    dry_run: bool = False


# ---------------------------------------------------------------------------
# Registry / credential helpers (IC-35)
# ---------------------------------------------------------------------------

class RegistryError(RuntimeError):
    """The IC-35 registry could not be loaded -- the optimizer fails closed.

    Silently continuing without the credential patterns would disable the whole
    IC-24/AC-89 exclusion, so a missing or malformed registry is a hard error.
    """

    code = "meta-optimizer.credential-registry-invalid"


def _load_registry(agent_meta_root: Path) -> dict:
    """Load the runtime-config-reader registry or raise :class:`RegistryError`."""
    path = Path(agent_meta_root) / _REGISTRY_RELPATH
    try:
        raw = path.read_text(encoding="utf-8")
        data = yaml.safe_load(raw)
    except (OSError, yaml.YAMLError) as exc:
        raise RegistryError("cannot read {}: {}".format(_REGISTRY_RELPATH, exc)) from exc
    if not isinstance(data, Mapping):
        raise RegistryError("{} is not a mapping".format(_REGISTRY_RELPATH))
    if not isinstance(data.get("credentials"), Mapping):
        raise RegistryError("{} has no credentials block".format(_REGISTRY_RELPATH))
    return dict(data)


def _leaf_paths(node: Any, prefix: str = ""):
    """Yield ``(dotted_path, leaf_value)`` for every non-mapping leaf."""
    if isinstance(node, Mapping):
        for key, value in node.items():
            path = "{}.{}".format(prefix, key) if prefix else str(key)
            yield from _leaf_paths(value, path)
    else:
        yield prefix, node


def _matches_any(path: str, prefixes: Sequence[str]) -> bool:
    return any(path == prefix or path.startswith(prefix + ".") for prefix in prefixes)


def credential_paths(config: Mapping, agent_meta_root: Path) -> frozenset:
    """Return the set of dotted config paths that are credentials (IC-35).

    A path is a credential when one of its segments matches ``name_patterns``
    (case-insensitive, segment-exact), it falls under an explicit ``keys`` entry
    (prefix match) or -- only when the registry's ``value_scan`` declares
    ``secrets`` -- its string value is reported by ``scan_for_secrets``.
    ``max-tokens-overrides`` deliberately does not match.
    """
    registry = _load_registry(Path(agent_meta_root))
    creds = registry.get("credentials") or {}
    patterns = []
    for raw in creds.get("name_patterns") or []:
        try:
            patterns.append(re.compile(str(raw), re.IGNORECASE))
        except re.error:  # pragma: no cover - registry is validated elsewhere
            continue
    keys = [str(entry.get("key")) for entry in (creds.get("keys") or [])
            if isinstance(entry, Mapping) and entry.get("key")]
    scan_values = str(creds.get("value_scan") or "") == "secrets"
    found = set()
    for path, value in _leaf_paths(config):
        if not path:
            continue
        if any(pattern.search(segment) for segment in path.split(".") for pattern in patterns):
            found.add(path)
            continue
        if _matches_any(path, keys):
            found.add(path)
            continue
        if scan_values and isinstance(value, str) and value and scan_for_secrets(value, dict(config)):
            found.add(path)
            continue
    return frozenset(found)


def _runtime_reader_keys(agent_meta_root: Path) -> tuple:
    registry = _load_registry(Path(agent_meta_root))
    return tuple(
        str(entry.get("key")) for entry in (registry.get("readers") or [])
        if isinstance(entry, Mapping) and entry.get("key")
    )


# ---------------------------------------------------------------------------
# Static template references / conditional detection
# ---------------------------------------------------------------------------

_REFERENCE_RE = re.compile(
    r"\{\{#(?:if|unless)\s+([A-Za-z_][A-Za-z0-9_]*)[^\}]*\}\}"
    r"|\{\{([A-Za-z_][A-Za-z0-9_]*)\}\}"
)
_CONDITIONAL_REFERENCE_RE = re.compile(
    r"\{\{#(?:if|unless)\s+([A-Za-z_][A-Za-z0-9_]*)[^\}]*\}\}"
)
_FRAMEWORK_DIRS = ("agents", "rules", "snippets", "templates", "commands")
_REFERENCE_SUFFIXES = (".md", ".yaml", ".yml", ".txt")


def _framework_references(agent_meta_root: Path) -> tuple:
    """Return ``(referenced_names, conditional_names)`` over the IC-21 universe.

    ``referenced_names`` also feeds the universe check (a ``no-effect`` claim
    needs no reference at all or a builder override); ``conditional_names`` are
    the variables used as ``{{#if X}}``/``{{#unless X}}``, which must never be
    sentinel-wrapped (spec lines 1445-1449).
    """
    names = set()
    conditionals = set()
    root = Path(agent_meta_root)
    for directory in _FRAMEWORK_DIRS:
        base = root / directory
        if not base.is_dir():
            continue
        for path in base.rglob("*"):
            if not path.is_file() or path.suffix not in _REFERENCE_SUFFIXES:
                continue
            try:
                text = path.read_text(encoding="utf-8", errors="replace")
            except OSError:  # pragma: no cover - unreadable template
                continue
            for match in _REFERENCE_RE.finditer(text):
                names.add(match.group(1) or match.group(2))
            for match in _CONDITIONAL_REFERENCE_RE.finditer(text):
                conditionals.add(match.group(1))
    return frozenset(names), frozenset(conditionals)


def _is_conditional(name: str, resolved: Mapping,
                    static_conditionals: Mapping = ()) -> bool:
    """True when *name* drives a ``{{#if}}``/``{{#unless}}`` block (never wrapped).

    Two branches, both from the spec (lines 1445-1449): the *static* detection
    over the same template set as the universe check (``{{#if X}}`` /
    ``{{#unless X}}``) and the render's conditional resolver (the whitelist in
    ``variables.py``), probed behaviorally instead of duplicating that list.
    """
    if name in static_conditionals:
        return True
    template = "{{#if %s}}BODY{{/if}}" % name
    active = strip_inactive_conditional_blocks(template, {name: "true"})
    inactive = strip_inactive_conditional_blocks(template, {name: "false"})
    return active == "BODY" and inactive == ""


def _builder_owned_names(names: Sequence[str], config: Mapping, agent_meta_root: Path,
                         project_root: Path, active) -> frozenset:
    """Names the builder sets unconditionally, discarding the user value.

    Probes ``build_variables`` with a unique marker per name: a name whose
    resolved value differs from its marker is overwritten by the builder
    (e.g. ``ORCHESTRATOR_STRICT``, ``UNKNOWN_FALLBACK_*``, ``SE_BASE_DIR``).
    """
    if not names:
        return frozenset()
    probe = copy.deepcopy(dict(config))
    probe_vars = dict(probe.get("variables") or {})
    markers = {name: "AMPROBE{}AMPROBE".format(name) for name in names}
    probe_vars.update(markers)
    probe["variables"] = probe_vars
    try:
        resolved, _ = build_variables(probe, Path(agent_meta_root), Path(project_root),
                                      active_set=active)
    except Exception:  # noqa: BLE001 - probe only; ownership is best-effort
        return frozenset()
    return frozenset(name for name, marker in markers.items() if resolved.get(name) != marker)


# ---------------------------------------------------------------------------
# Sentinel render + fan-out
# ---------------------------------------------------------------------------

def _sentinel_open(name: str) -> str:
    return "QZ{}QZ".format(name)


def _sentinel_close(name: str) -> str:
    return "ZQ{}ZQ".format(name)


def _to_string(value: Any) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def _wrapped_config_text(config: Mapping, names: Sequence[str]) -> str:
    wrapped = copy.deepcopy(dict(config))
    variables = dict(wrapped.get("variables") or {})
    for name in names:
        variables[name] = _sentinel_open(name) + _to_string(variables[name]) + _sentinel_close(name)
    wrapped["variables"] = variables
    return yaml.safe_dump(wrapped, sort_keys=False, allow_unicode=True)


def _iter_render_files(render_root: Path):
    """Yield ``(relative_posix_path, path)`` for every comparable render file.

    Excludes VCS metadata, the rendered config copy and the run log; everything
    else is a generated artifact the L0 proof must find byte-equal.
    """
    render_root = Path(render_root)
    for path in sorted(render_root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(render_root).as_posix()
        if rel.startswith(".git/") or rel in _NON_ARTIFACT_FILES or rel == _INPUT_CONFIG_COPY:
            continue
        yield rel, path


def _norm_rel(value: Any) -> str:
    norm = str(value).replace("\\", "/").strip().strip("/")
    return re.sub(r"^\./", "", norm)


def _provider_root_rels(mapping: Mapping) -> tuple:
    """Registry-declared artifact roots of one provider, as relative paths.

    ``provider_root_dirs`` is the provider tree (agents, rules, hooks, commands,
    skills, settings); the individual dir keys are the fallback for providers
    without that key. The context file is always included.
    """
    rels = []
    for value in (mapping.get("provider_root_dirs") or ()):
        norm = _norm_rel(value)
        if norm:
            rels.append(norm)
    if not rels:
        for key in ("agents_dir", "rules_dir"):
            value = mapping.get(key)
            if value:
                norm = _norm_rel(value)
                if norm:
                    rels.append(norm)
    context_file = mapping.get("context_file")
    if context_file:
        norm = _norm_rel(context_file)
        if norm:
            rels.append(norm)
    return tuple(rels)


def _count_token(path: Path, token: str) -> int:
    try:
        return path.read_bytes().decode("utf-8", errors="replace").count(token)
    except OSError:  # pragma: no cover - unreadable artifact
        return 0


def _sentinel_scan(render_root: Path, providers: Sequence[str], mappings: Mapping,
                   token: str) -> tuple:
    """Count *token* over the whole render; attribute hits per provider root."""
    root_rels = {provider: _provider_root_rels(mappings.get(provider) or {})
                 for provider in providers}
    total = 0
    files = 0
    per_provider: dict = {}
    for rel, path in _iter_render_files(render_root):
        hits = _count_token(path, token)
        if not hits:
            continue
        total += hits
        files += 1
        for provider in providers:
            if any(rel == root or rel.startswith(root + "/") for root in root_rels[provider]):
                per_provider[provider] = per_provider.get(provider, 0) + hits
    return total, files, per_provider


def sentinel_wrapped_names(config: Mapping, agent_meta_root: Path, project_root: Path,
                           active, *, resolved: Optional[Mapping] = None,
                           static_conditionals: Optional[frozenset] = None) -> tuple:
    """Names the sentinel render wraps: text values that are neither conditional
    nor a credential (IC-24 step 1, spec lines 1445-1449)."""
    config = dict(config)
    if resolved is None:
        resolved, _ = build_variables(config, Path(agent_meta_root), Path(project_root),
                                      active_set=active)
    if static_conditionals is None:
        static_conditionals = _framework_references(Path(agent_meta_root))[1]
    credentials = credential_paths(config, Path(agent_meta_root))
    return tuple(
        name for name in sorted(config.get("variables") or {})
        if isinstance((config.get("variables") or {})[name], str)
        and not _is_conditional(name, resolved, static_conditionals)
        and not _matches_any("variables." + name, credentials)
    )


def fan_out_counts(render_root: Path, config: Mapping, agent_meta_root: Path,
                   project_root: Path, active, *, providers: Optional[Sequence[str]] = None,
                   mappings: Optional[Mapping] = None,
                   resolved: Optional[Mapping] = None,
                   static_conditionals: Optional[frozenset] = None) -> tuple:
    """Count sentinel substitutions per text variable over an existing render.

    Returns one dict per text value under ``variables:`` (credentials excluded):
    ``{"variable", "value_bytes", "occurrences", "files", "injected_bytes",
    "per_provider", "conditional"}``. Conditional variables are never wrapped
    (``occurrences: null``, ``files: null``, ``conditional: true``, zeroed
    ``per_provider``) and get no counts.
    """
    render_root = Path(render_root)
    if providers is None or mappings is None:
        provider_config = load_providers_config(Path(agent_meta_root), dict(config))
        providers = resolve_providers(dict(config), provider_config)
        mappings = merge_provider_mappings(
            provider_config, load_provider_capabilities(Path(agent_meta_root)))
    if resolved is None:
        resolved, _ = build_variables(dict(config), Path(agent_meta_root),
                                      Path(project_root), active_set=active)
    if static_conditionals is None:
        static_conditionals = _framework_references(Path(agent_meta_root))[1]
    credentials = credential_paths(config, Path(agent_meta_root))
    entries = []
    for name in sorted((config.get("variables") or {})):
        path = "variables." + name
        value = (config.get("variables") or {})[name]
        if _matches_any(path, credentials):
            continue
        value_bytes = len(_to_string(value).encode("utf-8"))
        if _is_conditional(name, resolved, static_conditionals):
            entries.append({
                "variable": path, "value_bytes": value_bytes, "occurrences": None,
                "files": None, "injected_bytes": 0,
                "per_provider": {provider: 0 for provider in providers},
                "conditional": True,
            })
            continue
        if not isinstance(value, str):
            continue  # only text values can be sentinel-measured
        token = _sentinel_open(name)
        total, files, per_provider = _sentinel_scan(
            render_root, providers, mappings, token)
        entries.append({
            "variable": path, "value_bytes": value_bytes, "occurrences": total,
            "files": files, "injected_bytes": total * value_bytes,
            "per_provider": {key: count * value_bytes
                             for key, count in sorted(per_provider.items())},
            "conditional": False,
        })
    return tuple(entries)


# ---------------------------------------------------------------------------
# Line-based removal + diff
# ---------------------------------------------------------------------------

def _mapping_key_lines(lines: Sequence[str]):
    """Yield ``(dotted_path, index, indent)`` for every mapping key line."""
    stack: list = []
    for index, raw in enumerate(lines):
        line = raw.rstrip("\r\n")
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or stripped.startswith("-"):
            continue
        indent = len(line) - len(line.lstrip(" "))
        match = re.match(r"^([^\s#][^:]*?)\s*:(?:\s|$)", stripped)
        if not match:
            continue
        key = match.group(1).strip()
        while stack and stack[-1][1] >= indent:
            stack.pop()
        dotted = ".".join([entry[0] for entry in stack] + [key])
        yield dotted, index, indent
        stack.append((key, indent))


def _key_spans(lines: Sequence[str], names: Sequence[str]) -> dict:
    """Map each dotted key *name* to its ``(start, end)`` line span."""
    wanted = set(names)
    spans: dict = {}
    for path, index, indent in _mapping_key_lines(lines):
        if path not in wanted:
            continue
        end = index + 1
        while end < len(lines):
            raw = lines[end].rstrip("\r\n")
            if not raw.strip():
                break
            next_indent = len(raw) - len(raw.lstrip(" "))
            if next_indent <= indent:
                break
            end += 1
        spans[path] = (index, end)
    return spans


def _remove_keys(text: str, names: Sequence[str]) -> tuple:
    """Remove the key blocks of *names*; returns ``(new_text, removed_by_name)``."""
    lines = text.splitlines(keepends=True)
    spans = _key_spans(lines, [name for name in names if name])
    removed: dict = {}
    drop: set = set()
    for name, (start, end) in spans.items():
        removed[name] = lines[start:end]
        drop.update(range(start, end))
    new_lines = [line for index, line in enumerate(lines) if index not in drop]
    return "".join(new_lines), removed


def _diff_hunks(before: str, after: str) -> tuple:
    diff_lines = list(difflib.unified_diff(
        before.splitlines(keepends=True), after.splitlines(keepends=True),
        fromfile="a/.meta-config/project.yaml", tofile="b/.meta-config/project.yaml", n=3))
    hunks: list = []
    current: list = []
    for line in diff_lines:
        if line.startswith("@@"):
            if current:
                hunks.append("".join(current))
            current = [line]
        elif current:
            current.append(line)
    if current:
        hunks.append("".join(current))
    return tuple(hunks)


def _redact_hunks(hunks: tuple, credential_lines: Mapping) -> tuple:
    """Replace credential source lines inside diff context with a marker (AC-89)."""
    if not hunks or not credential_lines:
        return hunks
    redacted = []
    for hunk in hunks:
        out_lines = []
        for line in hunk.splitlines(keepends=True):
            prefix = line[:1] if line[:1] in "+- " else ""
            content = line[len(prefix):].rstrip("\r\n")
            marker = credential_lines.get(content)
            if marker is not None:
                out_lines.append("{}{}\n".format(prefix, marker))
            else:
                out_lines.append(line)
        redacted.append("".join(out_lines))
    return tuple(redacted)


def _credential_source_lines(text: str, credentials: Sequence[str], config: Mapping) -> dict:
    """Map exact credential source line text -> redaction marker (AC-89)."""
    lines = text.splitlines()
    markers: dict = {}
    leaves = dict(_leaf_paths(config))
    for path, index, _indent in _mapping_key_lines([line + "\n" for line in lines]):
        if path not in credentials:
            continue
        value_bytes = len(_to_string(leaves.get(path, "")).encode("utf-8"))
        markers[lines[index]] = "{}: {}".format(
            path.split(".")[-1], _REDACTION_MARKER.format(value_bytes))
    return markers


# ---------------------------------------------------------------------------
# Candidate construction
# ---------------------------------------------------------------------------

def _scope_for(path: str) -> str:
    head = path.split(".", 1)[0]
    if path.startswith("variables."):
        return "variables"
    if head == "roles":
        return "roles"
    if head in ("ai-providers", "ai-provider", "default-provider", "providers",
                "provider-overrides", "provider-deactivation", "provider-isolation",
                "model-overrides", "model-inherit-main-chat", "model-source-preference"):
        return "providers"
    if head == "auto_commit":
        return "auto_commit"
    if head == "hooks":
        return "hooks"
    if head == "repo_containment":
        return "repo_containment"
    if head == "orchestrator":
        return "orchestrator"
    return "structural-other"


def _removable_candidate(config_text: str, path: str, kind: str, *, rationale: str,
                         runtime_reader: bool, credential_lines: Mapping,
                         warnings: Tuple[str, ...] = ()) -> Candidate:
    new_text, removed = _remove_keys(config_text, [path])
    removed_lines = removed.get(path, [])
    hunks = _redact_hunks(_diff_hunks(config_text, new_text), credential_lines) if removed_lines else ()
    marks: Tuple = ("runtime-reader",) if runtime_reader else ()
    if kind == "inactive-scope":
        marks = tuple(sorted(set(marks) | {"inactive-scope", "reactivation-loss-warning"}))
    all_warnings = tuple(warnings)
    if runtime_reader:
        all_warnings = all_warnings + (_RUNTIME_READER_WARNING,)
    if kind == "inactive-scope":
        all_warnings = all_warnings + (_REACTIVATION_WARNING,)
    return Candidate(
        id="OPT-{}:{}".format(kind, path),
        kind=kind,
        yaml_path=path,
        scope=_scope_for(path),
        marks=marks,
        approval_level="confirm-runtime" if runtime_reader else "confirm",
        warnings=all_warnings,
        deterministic=(kind == "no-effect" and not marks),
        applicable=True,
        proof_level_required="L0",
        yaml_bytes_saved=sum(len(line.encode("utf-8")) for line in removed_lines),
        rationale=rationale,
        hunks=hunks,
    )


def _hint_candidate(kind: str, path: str, *, rationale: str, warnings: Tuple[str, ...] = ()) -> Candidate:
    return Candidate(
        id="OPT-{}:{}".format(kind, path),
        kind=kind,
        yaml_path=path,
        scope=_scope_for(path),
        marks=(),
        approval_level="confirm",
        warnings=warnings,
        deterministic=False,
        applicable=False,
        proof_level_required="none",
        rationale=rationale,
    )


def _forbid_semantic_kinds(candidates: Sequence[Candidate]) -> list:
    """Drop hint kinds that require ``--include-semantic`` (AC-57/91, review F6).

    Defense in depth: even a future producer of a semantic kind must never leak a
    hint into a run without the flag.
    """
    return [candidate for candidate in candidates if candidate.kind not in SEMANTIC_KINDS]


def _duplicate_hints(raw_vars: Mapping, counts: Mapping, credentials: Sequence[str]) -> list:
    by_value: dict = {}
    for name in sorted(raw_vars):
        path = "variables." + name
        entry = counts.get(path)
        if entry is None or entry["conditional"] or not entry["occurrences"]:
            continue
        if _matches_any(path, credentials):
            continue
        by_value.setdefault(_to_string(raw_vars[name]), []).append(path)
    hints = []
    for paths in by_value.values():
        if len(paths) < 2:
            continue
        for path in paths[1:]:
            hints.append(_hint_candidate(
                "duplicate-value", path,
                rationale="Same value as {} ; deduplicate (hint only, Q36).".format(paths[0])))
    return hints


def collect_candidates(project_root: Path, agent_meta_root: Path, config: Mapping,
                       config_text: str, active, *, work_dir: Optional[Path] = None,
                       providers: Optional[Sequence[str]] = None,
                       mappings: Optional[Mapping] = None,
                       include_semantic: bool = False) -> OptimizerProposal:
    """Collect removal candidates and the fan-out report (IC-24).

    Renders the sentinel config into *work_dir* (default: a fresh
    ``<tmp-sink>/meta-optimizer/<run_id>/work``) and classifies every user
    variable. Credential paths are excluded up front.

    Review N2: when *work_dir* is ``None`` this function allocates the scratch
    itself and therefore **owns** it -- the render holds an unredacted config
    copy, so the scratch (and its now-empty run dir) is removed before returning,
    exactly like :func:`run_optimize_config` does for the dirs it allocates. A
    caller passing *work_dir* keeps ownership of that dir.
    """
    project_root = Path(project_root)
    agent_meta_root = Path(agent_meta_root)
    config = dict(config)
    if providers is None or mappings is None:
        provider_config = load_providers_config(agent_meta_root, config)
        providers = resolve_providers(config, provider_config)
        mappings = merge_provider_mappings(
            provider_config, load_provider_capabilities(agent_meta_root))
    allocated = work_dir is None
    if allocated:
        work_dir = resolve_work_dir(project_root, config, OPTIMIZER_SUBDIR, _run_id())
    work_dir = Path(work_dir)
    try:
        return _classify_candidates(
            project_root, agent_meta_root, config, config_text, active, work_dir,
            providers=providers, mappings=mappings, include_semantic=include_semantic)
    finally:
        if allocated:
            _discard_work_dir(work_dir, work_dir.parent.parent)


def _classify_candidates(project_root: Path, agent_meta_root: Path, config: Mapping,
                         config_text: str, active, work_dir: Path, *,
                         providers: Sequence[str], mappings: Mapping,
                         include_semantic: bool) -> OptimizerProposal:
    """Render, measure and classify; the scratch is owned by the caller."""
    resolved, _ = build_variables(config, agent_meta_root, project_root, active_set=active)
    raw_vars = dict(config.get("variables") or {})
    credentials = credential_paths(config, agent_meta_root)
    runtime_keys = _runtime_reader_keys(agent_meta_root)
    static_refs, static_conditionals = _framework_references(agent_meta_root)
    builder_owned = _builder_owned_names(sorted(raw_vars), config, agent_meta_root,
                                         project_root, active)
    credential_line_map = _credential_source_lines(config_text, sorted(credentials), config)

    wrap_names = sentinel_wrapped_names(
        config, agent_meta_root, project_root, active, resolved=resolved,
        static_conditionals=static_conditionals)
    _render_into(agent_meta_root, _wrapped_config_text(config, wrap_names), work_dir)
    scan = fan_out_counts(
        work_dir, config, agent_meta_root, project_root, active,
        providers=providers, mappings=mappings, resolved=resolved,
        static_conditionals=static_conditionals)
    counts = {entry["variable"]: entry for entry in scan}

    candidates: list = []
    for name in sorted(raw_vars):
        path = "variables." + name
        entry = counts.get(path)
        if entry is None:
            continue
        value_bytes = len(_to_string(raw_vars[name]).encode("utf-8"))
        runtime_reader = _matches_any(path, runtime_keys)
        if entry["conditional"]:
            if name in builder_owned:
                candidates.append(_removable_candidate(
                    config_text, path, "no-effect",
                    rationale="Builder-owned: the resolved value never uses this entry.",
                    runtime_reader=runtime_reader, credential_lines=credential_line_map))
            elif name in static_refs:
                candidates.append(_hint_candidate(
                    "info-only", path,
                    rationale="Conditional variable, not builder-owned; review manually."))
            else:
                candidates.append(_removable_candidate(
                    config_text, path, "no-effect",
                    rationale="Conditional but referenced by no template.",
                    runtime_reader=runtime_reader, credential_lines=credential_line_map))
            continue
        if entry["occurrences"]:
            continue  # effective in the current active set -> nothing removable
        if value_bytes > CONTENT_LOSS_THRESHOLD_BYTES:
            candidates.append(_hint_candidate(
                "dead-variable-content-loss", path,
                rationale=("Unused in every active artifact and longer than {} bytes; "
                           "relocate the content instead of deleting it.").format(
                               CONTENT_LOSS_THRESHOLD_BYTES)))
        elif name in builder_owned or name not in static_refs:
            candidates.append(_removable_candidate(
                config_text, path, "no-effect",
                rationale="Removal is byte-identical for every active artifact (L0).",
                runtime_reader=runtime_reader, credential_lines=credential_line_map))
        else:
            candidates.append(_removable_candidate(
                config_text, path, "inactive-scope",
                rationale=("Only ineffective for the current active set; a template "
                           "reference exists."),
                runtime_reader=runtime_reader, credential_lines=credential_line_map))

    if include_semantic:
        candidates.extend(_duplicate_hints(raw_vars, counts, sorted(credentials)))
    else:
        # Defense in depth (AC-57/91): even a future producer of a semantic kind
        # must never leak a hint into a run without --include-semantic.
        candidates = _forbid_semantic_kinds(candidates)
    candidates.sort(key=lambda candidate: candidate.id)

    fan_entries = tuple(
        FanOutEntry(variable=entry["variable"], value_bytes=entry["value_bytes"],
                    occurrences=entry["occurrences"], files=entry["files"],
                    injected_bytes=entry["injected_bytes"],
                    per_provider=entry["per_provider"],
                    conditional=entry["conditional"])
        for entry in scan
        if entry["conditional"] or entry["occurrences"])

    deterministic_names = [candidate.yaml_path for candidate in candidates
                          if candidate.deterministic]
    if deterministic_names:
        after_text, _ = _remove_keys(config_text, deterministic_names)
        raw_diff = "".join(difflib.unified_diff(
            config_text.splitlines(keepends=True), after_text.splitlines(keepends=True),
            fromfile="a/.meta-config/project.yaml", tofile="b/.meta-config/project.yaml", n=3))
        diff = "".join(_redact_hunks((raw_diff,), credential_line_map))
    else:
        diff = ""

    return OptimizerProposal(
        project_yaml_sha256=hashlib.sha256(config_text.encode("utf-8")).hexdigest(),
        agent_meta_version=_to_string(config.get("agent-meta-version")),
        generator_options={
            "include_semantic": bool(include_semantic),
            "content_loss_threshold_bytes": CONTENT_LOSS_THRESHOLD_BYTES,
        },
        candidates=tuple(candidates),
        fan_out=fan_entries,
        diff=diff,
    )


# ---------------------------------------------------------------------------
# Proof (IC-25)
# ---------------------------------------------------------------------------

def _collect_files(root: Path) -> dict:
    files: dict = {}
    if not root.is_dir():
        return files
    for rel, path in _iter_render_files(root):
        try:
            files[rel] = path.read_bytes()
        except OSError:  # pragma: no cover - unreadable render artifact
            continue
    return files


def _removed_lines(before: str, after: str) -> list:
    out = []
    for line in difflib.unified_diff(before.splitlines(keepends=True),
                                     after.splitlines(keepends=True), n=0):
        if line.startswith("-") and not line.startswith("---"):
            out.append(line[1:])
    return out


_PLACEHOLDER_RE = re.compile(r"\{\{[^{}]*\}\}")
_TOKEN_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_./-]*")


def _placeholder_stats(files: Mapping) -> tuple:
    names = set()
    count = 0
    for data in files.values():
        found = _PLACEHOLDER_RE.findall(data.decode("utf-8", errors="replace"))
        count += len(found)
        names.update(found)
    return names, count


def _token_multiset_equal(before: Mapping, after: Mapping, changed: Sequence[str]) -> bool:
    for rel in changed:
        if rel not in before or rel not in after:
            return False
        left = Counter(_TOKEN_RE.findall(before[rel].decode("utf-8", errors="replace")))
        right = Counter(_TOKEN_RE.findall(after[rel].decode("utf-8", errors="replace")))
        if left != right:
            return False
    return True


def _sha256(path: Path) -> Optional[str]:
    try:
        return hashlib.sha256(path.read_bytes()).hexdigest()
    except OSError:
        return None


def comparison_file_digests(before_render: Path, after_render: Path,
                            comparison_files: Sequence[str] = L0_COMPARISON_FILES) -> tuple:
    """Hash the render-derived sidecars before/after the proof (AC-55 Rev. 3)."""
    before_render = Path(before_render)
    after_render = Path(after_render)
    entries = []
    for rel in comparison_files:
        before_hash = _sha256(before_render / rel)
        after_hash = _sha256(after_render / rel)
        entries.append({
            "path": rel,
            "before_sha256": before_hash,
            "after_sha256": after_hash,
            "equal": before_hash == after_hash,
        })
    return tuple(entries)


def prove(before_render: Path, after_render: Path, before_yaml: str, after_yaml: str,
          level: str, *, relocations: Sequence = (),
          comparison_files: Sequence[str] = L0_COMPARISON_FILES) -> ProofReport:
    """Compare two renders and return a :class:`ProofReport` (IC-25).

    *comparison_files* are always part of the compared set, so a render-derived
    sidecar that a removable candidate would change fails L0.
    """
    before = _collect_files(Path(before_render))
    after = _collect_files(Path(after_render))
    digests = comparison_file_digests(before_render, after_render, comparison_files)
    # A sidecar that vanished from the render (present in neither tree) is a hard
    # failure rather than a silent "equal" (review F8); it is not counted as a
    # compared file either, so it cannot inflate byte_equal_files.
    missing = [entry["path"] for entry in digests
               if entry["before_sha256"] is None or entry["after_sha256"] is None]
    present = {entry["path"] for entry in digests if entry["before_sha256"] or entry["after_sha256"]}
    compared = sorted(set(before) | set(after) | present)
    changed = tuple(sorted(rel for rel in compared if before.get(rel) != after.get(rel)))
    files_compared = len(compared)
    byte_equal_files = files_compared - len(changed)

    roundtrip = analyze_roundtrip(before_yaml, after_yaml)
    expected_comment_loss = _count_comments("".join(_removed_lines(before_yaml, after_yaml)))
    placeholder_names_before, unresolved_before = _placeholder_stats(before)
    placeholder_names_after, unresolved_after = _placeholder_stats(after)
    placeholder_sets_equal = placeholder_names_before == placeholder_names_after
    token_multiset_equal = _token_multiset_equal(before, after, changed)

    reasons: list = []
    for path in missing:
        reasons.append("comparison file missing in the render: {}".format(path))
    if set(before) != set(after):
        file_set_diff = sorted(set(before) ^ set(after))
        reasons.append("file set differs: {}".format(", ".join(file_set_diff[:5])))
    if changed:
        reasons.append("changed files ({}): {}".format(len(changed), ", ".join(changed[:5])))
    if roundtrip.order_changed:
        reasons.append("YAML mapping order changed")
    if roundtrip.lost_comments != expected_comment_loss:
        reasons.append("comment loss {} != expected {}".format(
            roundtrip.lost_comments, expected_comment_loss))
    if level != "L0":
        if not placeholder_sets_equal:
            reasons.append("placeholder sets differ")
        if unresolved_after > unresolved_before:
            reasons.append("unresolved placeholders increased ({} -> {})".format(
                unresolved_before, unresolved_after))
        if not token_multiset_equal:
            reasons.append("token multiset differs")

    # L1's anchor criterion (IC-12) is not consumed by any applicable kind yet;
    # report it as satisfied for L0 and Phase-3 levels alike.
    anchors_ok = True
    ok = bool(level in PROOF_LEVELS and level != "none" and not reasons)
    return ProofReport(
        level_reached=level if ok else "none",
        files_compared=files_compared,
        byte_equal_files=byte_equal_files,
        changed_files=changed,
        placeholder_sets_equal=placeholder_sets_equal,
        unresolved_placeholders_before=unresolved_before,
        unresolved_placeholders_after=unresolved_after,
        token_multiset_equal=token_multiset_equal,
        anchors_ok=anchors_ok,
        relocation_reachable=None,
        roundtrip=roundtrip,
        expected_comment_loss=expected_comment_loss,
        ok=ok,
        reasons=tuple(reasons),
    )


def advance_l0(level: str) -> str:
    """Return the next proof level (``none`` -> ``L0`` -> ... -> ``L3``, capped)."""
    if level not in PROOF_LEVELS:
        return "L0"
    index = PROOF_LEVELS.index(level)
    return PROOF_LEVELS[min(index + 1, len(PROOF_LEVELS) - 1)]


# ---------------------------------------------------------------------------
# Render + CLI runner
# ---------------------------------------------------------------------------

def _run_id() -> str:
    return "{}-{}".format(datetime.now().strftime("%Y%m%d-%H%M%S"), os.getpid())


def _render_into(agent_meta_root: Path, config_text: str, work_dir: Path) -> None:
    """Render *config_text* into *work_dir* via the regular sync codepath."""
    work_dir.mkdir(parents=True, exist_ok=True)
    config_dir = work_dir / ".meta-config"
    config_dir.mkdir(exist_ok=True)
    config_path = config_dir / "project.yaml"
    config_path.write_text(config_text, encoding="utf-8")
    env = work_dir_env(work_dir)
    sync_script = Path(agent_meta_root) / "scripts" / "sync.py"
    subprocess.run(["git", "init", "-q"], cwd=str(work_dir), check=False,
                   capture_output=True, env=env, timeout=60)
    result = subprocess.run(
        [sys.executable, str(sync_script), "--config", str(config_path), "--init"],
        cwd=str(work_dir), env=env, capture_output=True, text=True, timeout=600,
    )
    if result.returncode != 0:
        raise RuntimeError("render failed (rc {}): {}".format(
            result.returncode, (result.stdout + result.stderr)[-800:]))


def _write_json(path: Path, payload: Any) -> None:
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    restrict_owner_only(path)


def _report_dict(report: ProofReport) -> dict:
    return asdict(report)


def _proposal_dict(proposal: OptimizerProposal) -> dict:
    return asdict(proposal)


def _render_summary(proposal: OptimizerProposal, report: ProofReport) -> str:
    lines = [
        "Config optimizer: {} candidate(s) | fan-out {} variable(s) | proof {}".format(
            len(proposal.candidates), len(proposal.fan_out),
            report.level_reached if report.ok else "FAILED"),
    ]
    for candidate in proposal.candidates:
        lines.append("  {:<7} {:<9} {}".format(
            candidate.deterministic and "removable" or "hint",
            candidate.kind, candidate.yaml_path))
    return "\n".join(lines)


def _discard_work_dir(work_dir: Path, artifact_dir: Path) -> bool:
    """Remove a render work dir (and its now-empty run dir) — review F1, option (a).

    The render scratch holds an unredacted copy of ``project.yaml``, so AC-89
    ("no credential byte sequence in any file below the sink") is only watertight
    if the scratch is deleted before the runner returns. The renders themselves
    still use the real config, so the L0 proof stays honest. The artifact
    directory itself is never removed.

    Review N3: the deletion is no longer silent -- a scratch that survived (e.g. a
    permission problem) is reported as a warning, because it would otherwise leak
    a credential copy unnoticed. Returns ``True`` when the scratch is gone.
    """
    work_dir = Path(work_dir)
    artifact_dir = Path(artifact_dir)
    if work_dir == artifact_dir:
        return True
    shutil.rmtree(work_dir, ignore_errors=True)
    if work_dir.parent != artifact_dir:  # never remove the artifact directory
        try:
            work_dir.parent.rmdir()
        except OSError:
            pass
    if work_dir.exists():  # pragma: no cover - filesystem-level failure
        print("warning: render scratch could not be removed: {}".format(work_dir),
              file=sys.stderr)
        return False
    return True


def _discard_empty_dir(path: Path) -> None:
    """Remove *path* when it is empty; never touches a directory with content."""
    try:
        Path(path).rmdir()
    except OSError:
        pass


def run_optimize_config(*, project_root: Path, agent_meta_root: Path, config_path: Path,
                        config: Mapping, active, providers: Optional[Sequence[str]] = None,
                        mappings: Optional[Mapping] = None, as_json: bool = False,
                        include_semantic: bool = False,
                        out: Optional[str] = None,
                        candidates: Optional[Sequence[Candidate]] = None) -> int:
    """Run the read-only optimizer analysis; returns the process exit code.

    Exit 0 on success (also with candidates), 1 when the L0 proof fails
    (``meta-optimizer.proof-failed``, no proposal written), 2 on tmp-sink,
    registry or render errors. Only the artifacts (``proposal.json``,
    ``proposal.diff``, ``proof.json``) stay below ``<tmp-sink>/meta-optimizer/``;
    the render scratch is removed before returning (AC-89, review F1 option (a)).
    ``candidates`` overrides the candidate search (recomputation seam for the
    applier and tests); ``out`` overrides the artifact directory inside the sink.
    """
    project_root = Path(project_root)
    agent_meta_root = Path(agent_meta_root)
    run_id = _run_id()
    try:
        if out:
            run_dir = resolve_out_path(project_root, dict(config), out,
                                       tool="optimize-config")
        else:
            run_dir = resolve_output_dir(project_root, dict(config), OPTIMIZER_SUBDIR) / run_id
        # AC-94: every work dir lies below <sink>/<subdir>/<run_id>/work via
        # resolve_work_dir -- the sentinel render and both proof renders alike.
        work_dir = resolve_work_dir(project_root, dict(config), OPTIMIZER_SUBDIR, run_id)
        proof_before = resolve_work_dir(project_root, dict(config), OPTIMIZER_SUBDIR,
                                        run_id + "-before")
        proof_after = resolve_work_dir(project_root, dict(config), OPTIMIZER_SUBDIR,
                                       run_id + "-after")
    except TmpSinkError as exc:
        print("error: {}: {}".format(exc.code, exc.message), file=sys.stderr)
        return 2
    except OSError as exc:
        print("error: {}: {}".format(OUT_WRITE_FAILED_CODE, exc), file=sys.stderr)
        return 2

    try:
        run_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        print("error: {}: {}".format(OUT_WRITE_FAILED_CODE, exc), file=sys.stderr)
        _discard_work_dir(work_dir, run_dir)
        return 2

    if providers is None or mappings is None:
        provider_config = load_providers_config(agent_meta_root, dict(config))
        providers = resolve_providers(dict(config), provider_config)
        mappings = merge_provider_mappings(
            provider_config, load_provider_capabilities(agent_meta_root))
    config_text = Path(config_path).read_text(encoding="utf-8")

    proposal: Optional[OptimizerProposal] = None
    digests: tuple = ()
    report: Optional[ProofReport] = None
    try:
        if candidates is None:
            proposal = collect_candidates(
                project_root, agent_meta_root, config, config_text, active,
                work_dir=work_dir, providers=providers, mappings=mappings,
                include_semantic=include_semantic)
            removable = [candidate for candidate in proposal.candidates
                         if candidate.deterministic]
        else:
            removable = [candidate for candidate in candidates if candidate.deterministic]

        keys = [candidate.yaml_path for candidate in removable
                if candidate.yaml_path.startswith("variables.")]
        after_text, _ = _remove_keys(config_text, keys)
        _render_into(agent_meta_root, config_text, proof_before)
        _render_into(agent_meta_root, after_text, proof_after)

        report = prove(proof_before, proof_after, config_text, after_text, "L0")
        digests = comparison_file_digests(proof_before, proof_after)
    except RegistryError as exc:
        print("error: {}: {}".format(exc.code, exc), file=sys.stderr)
        return 2
    except (RuntimeError, OSError, subprocess.SubprocessError, yaml.YAMLError, ValueError) as exc:
        print("error: {}: {}".format(RENDER_FAILED_CODE, exc), file=sys.stderr)
        return 2
    finally:
        # AC-89 / review F1 option (a): no render scratch survives -- it holds an
        # unredacted config copy. Runs on every exit path below this point.
        for work in (work_dir, proof_before, proof_after):
            _discard_work_dir(work, run_dir)

    if report is None:  # pragma: no cover - defensive: the try block always sets it
        print("error: {}: no proof report produced".format(OUT_WRITE_FAILED_CODE),
              file=sys.stderr)
        return 2

    # Review N1: this write happens after the scratch was deleted, so it is no
    # longer covered by the render try/except -- an OSError here must surface as
    # the documented Exit 2 instead of a traceback.
    try:
        _write_json(run_dir / "proof.json", {
            "report": _report_dict(report),
            "comparison_files": [dict(entry) for entry in digests],
        })
    except OSError as exc:
        print("error: {}: {}".format(OUT_WRITE_FAILED_CODE, exc), file=sys.stderr)
        return 2
    if not report.ok:
        print("error: {}: {}".format(PROOF_FAILED_CODE, "; ".join(report.reasons)),
              file=sys.stderr)
        return 1

    proof_payload = {
        "level_reached": report.level_reached,
        "ok": report.ok,
        "files_compared": report.files_compared,
        "byte_equal_files": report.byte_equal_files,
    }
    if proposal is None:
        # candidates override (recomputation seam): proof only, no proposal.
        payload = {
            "proof": proof_payload,
            "comparison_files": [dict(entry) for entry in digests],
            "artifacts": {"proof": str(run_dir / "proof.json")},
        }
        if as_json:
            print(json.dumps(payload, indent=2, ensure_ascii=False))
        else:
            print("Config optimizer (recomputation): proof {}".format(report.level_reached))
        return 0

    try:
        _write_json(run_dir / "proposal.json", _proposal_dict(proposal))
        (run_dir / "proposal.diff").write_text(proposal.diff, encoding="utf-8")
        restrict_owner_only(run_dir / "proposal.diff")
    except OSError as exc:  # review N1: documented Exit 2, never a traceback
        print("error: {}: {}".format(OUT_WRITE_FAILED_CODE, exc), file=sys.stderr)
        return 2

    payload = {
        "project_yaml_sha256": proposal.project_yaml_sha256,
        "agent_meta_version": proposal.agent_meta_version,
        "generator_options": dict(proposal.generator_options),
        "candidates": [asdict(candidate) for candidate in proposal.candidates],
        "fan_out": [asdict(entry) for entry in proposal.fan_out],
        "proof": proof_payload,
        "comparison_files": [dict(entry) for entry in digests],
        "artifacts": {
            "proposal": str(run_dir / "proposal.json"),
            "diff": str(run_dir / "proposal.diff"),
            "proof": str(run_dir / "proof.json"),
        },
    }
    if as_json:
        print(json.dumps(payload, indent=2, ensure_ascii=False))
    else:
        print(_render_summary(proposal, report))
    return 0


# ---------------------------------------------------------------------------
# Applier (IC-24 "Applier"; AC-55/56/75/80/89/90/91/94)
# ---------------------------------------------------------------------------

def _is_line_subsequence(before: Sequence[str], after: Sequence[str]) -> bool:
    """True when *after* is a line subsequence of *before* (remove-only)."""
    index = 0
    total = len(before)
    for line in after:
        while index < total and before[index] != line:
            index += 1
        if index >= total:
            return False
        index += 1
    return True


def _hunk_sides(hunk: str) -> Tuple[list, list]:
    """Return ``(before_side, after_side)`` line lists of one unified hunk.

    Header lines are skipped. Redaction markers are dropped from *both* sides:
    the marker stands for a credential context line that exists verbatim on both
    sides, so dropping it keeps the remove-only comparison honest without ever
    touching the value (AC-89).
    """
    before_side: list = []
    after_side: list = []
    for line in hunk.splitlines():
        if line.startswith("@@"):
            continue
        if line.startswith("--- ") or line.startswith("+++ "):
            continue
        prefix = line[:1]
        content = line[1:] if prefix in "+- " else line
        if _REDACTION_RE.search(content):
            continue
        if prefix == "-":
            before_side.append(content)
        elif prefix == "+":
            after_side.append(content)
        else:
            before_side.append(content)
            after_side.append(content)
    return before_side, after_side


def _hunk_is_remove_only(hunk: str) -> bool:
    """True when the hunk only removes lines (its ``+`` side is a subsequence)."""
    before_side, after_side = _hunk_sides(hunk)
    return _is_line_subsequence(before_side, after_side)


def _redacted_config_text(config_text: str, config: Mapping,
                          credentials: Sequence[str]) -> Tuple[str, Tuple[str, ...]]:
    """Return ``(text, key_names)`` with every credential value masked (AC-89).

    The marker is identical to the one used inside diff context, so the backup
    never holds a plaintext credential -- not even below the (gitignored) sink.
    Only key *names* are reported back (``applied.json.backup_redacted_keys``).
    """
    lines = config_text.splitlines()
    if not lines:
        return config_text, ()
    leaves = dict(_leaf_paths(config))
    names: set = set()
    for path, index, indent in _mapping_key_lines([line + "\n" for line in lines]):
        if path not in credentials:
            continue
        key = path.split(".")[-1]
        value_bytes = len(_to_string(leaves.get(path, "")).encode("utf-8"))
        lines[index] = "{}{}: {}".format(
            " " * indent, key, _REDACTION_MARKER.format(value_bytes))
        names.add(key)
    if not names:
        return config_text, ()
    text = "\n".join(lines)
    if config_text.endswith("\n"):
        text += "\n"
    return text, tuple(sorted(names))


def _payload_digest(payload: Mapping) -> str:
    """sha256 over the canonical JSON form of a sink payload (binding digest)."""
    blob = json.dumps(payload, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")
    return hashlib.sha256(blob).hexdigest()


def _binding_digest(payload: Mapping) -> str:
    """Digest over the *binding-relevant* preview fields (AC-90).

    ``preview_sha256`` (the digest itself) and ``proof`` (a report-only extra)
    are excluded, so the digest is identical whether or not the preview carries a
    proof section -- an application can then recompute it from its own body and
    compare it with ``applied.json.preview_sha256``.
    """
    body = {key: value for key, value in payload.items()
            if key not in ("preview_sha256", "proof")}
    return _payload_digest(body)


def _same_device(path_a: Path, path_b: Path) -> bool:
    """True when both paths live on the same device (cross-device guard, Rev. 3.3).

    ``os.replace`` cannot move a file across filesystems, so the applier checks
    before writing anything and aborts with ``meta-optimizer.cross-device``
    instead of leaving a half-written config. An unknown device is treated as
    "same" and left to ``os.replace``.
    """
    try:
        return os.stat(os.fspath(path_a)).st_dev == os.stat(os.fspath(path_b)).st_dev
    except OSError:
        return True


def _applier_run_dir(project_root: Path, config: Mapping, run_id: str) -> Path:
    """``<sink>/meta-optimizer/<run_id>`` (not created), IC-34/Rev. 3.3."""
    work = resolve_work_dir(project_root, config, OPTIMIZER_SUBDIR, run_id,
                            tool=_APPLIER_TOOL)
    return work.parent


def _recompute_candidates(project_root: Path, agent_meta_root: Path, config: Mapping,
                          config_text: str, generator_options: Mapping) -> OptimizerProposal:
    """Recompute the candidates with the proposal's own options (N-7)."""
    active = compute_active_set(dict(config), agent_meta_root, project_root, warn_sink=[])
    return collect_candidates(
        project_root, agent_meta_root, config, config_text, active,
        include_semantic=bool(generator_options.get("include_semantic", False)))


def _preview_body(accept_ids: Sequence[str], accept_runtime_ids: Sequence[str],
                  before_hash: str, version: str, generator_options: Mapping,
                  entries: Sequence[Mapping], rejected: Sequence[Mapping]) -> dict:
    """The deterministic preview/apply payload (IC-24 "Vorschau und Anwendung")."""
    return {
        "accept_ids": list(accept_ids),
        "accept_runtime_ids": list(accept_runtime_ids),
        "project_yaml_sha256": before_hash,
        "agent_meta_version": version,
        "generator_options": dict(generator_options),
        "candidates": [dict(entry) for entry in entries],
        "rejected": [dict(entry) for entry in rejected],
    }


def _preview_entry(candidate: Candidate) -> dict:
    return {
        "id": candidate.id,
        "yaml_path": candidate.yaml_path,
        "kind": candidate.kind,
        "marks": list(candidate.marks),
        "warnings": list(candidate.warnings),
        "hunks": list(candidate.hunks),
    }


def apply_summary(report: ApplyReport) -> str:
    """Human-readable summary of an :class:`ApplyReport` (CLI output)."""
    if report.dry_run:
        head = "Config patch preview: {} accepted, {} rejected".format(
            len(report.applied_ids), len(report.rejected))
    else:
        head = "Config patch applied: {} applied, {} rejected".format(
            len(report.applied_ids), len(report.rejected))
    lines = [head]
    if report.code:
        lines.append("  code: {}".format(report.code))
    for pid, reason in report.rejected:
        lines.append("  rejected: {} ({})".format(pid, reason))
    for error in report.errors:
        lines.append("  error: {}".format(error))
    if report.preview_path:
        lines.append("  preview: {}".format(report.preview_path))
    if report.log_path:
        lines.append("  protocol: {}".format(report.log_path))
    return "\n".join(lines)


def _proposal_candidates(proposal: Mapping) -> Tuple[dict, dict]:
    """Return ``(declared_ids, file_hunks)`` read from ``proposal.json``."""
    declared: set = set()
    hunks: dict = {}
    raw = proposal.get("candidates") or ()
    if isinstance(raw, (list, tuple)):
        for entry in raw:
            if isinstance(entry, Mapping) and entry.get("id"):
                candidate_id = str(entry["id"])
                declared.add(candidate_id)
                hunks[candidate_id] = tuple(str(line) for line in (entry.get("hunks") or ()))
    return declared, hunks


def _check_preview_binding(preview: Mapping, accept_ids: Sequence[str],
                           accept_runtime_ids: Sequence[str], before_hash: str,
                           version: str, stored_sha: str) -> Optional[str]:
    """Return a reason when *preview* does not bind, else ``None`` (AC-90)."""
    if _binding_digest(preview) != stored_sha:
        return "preview.json digest does not match its own preview_sha256"
    if set(str(entry) for entry in (preview.get("accept_ids") or ())) != set(accept_ids):
        return "accepted IDs differ from the preview"
    if set(str(entry) for entry in (preview.get("accept_runtime_ids") or ())) != set(
            accept_runtime_ids):
        return "accepted runtime IDs differ from the preview"
    if _to_string(preview.get("project_yaml_sha256")) != before_hash:
        return "project.yaml hash differs from the preview"
    if _to_string(preview.get("agent_meta_version")) != version:
        return "agent-meta version differs from the preview"
    return None


def _check_preview_hunks(preview: Mapping, accepted: Sequence[Candidate]) -> Optional[str]:
    """Compare the preview's recomputed hunks with the fresh recomputation."""
    entries = {}
    for entry in preview.get("candidates") or ():
        if isinstance(entry, Mapping) and entry.get("id"):
            entries[str(entry["id"])] = entry
    for candidate in accepted:
        entry = entries.get(candidate.id)
        if entry is None:
            return "preview.json has no entry for {}".format(candidate.id)
        if tuple(str(line) for line in (entry.get("hunks") or ())) != candidate.hunks:
            return "recomputed hunk of {} differs from the preview".format(candidate.id)
        if str(entry.get("kind", "")) != candidate.kind:
            return "kind of {} differs from the preview".format(candidate.id)
        if tuple(entry.get("marks") or ()) != candidate.marks:
            return "marks of {} differ from the preview".format(candidate.id)
        if tuple(entry.get("warnings") or ()) != candidate.warnings:
            return "warnings of {} differ from the preview".format(candidate.id)
    return None


def apply_config_patch(project_root: Path, agent_meta_root: Path, proposal_path: Path,
                       accept_ids: Sequence[str], *, accept_runtime_ids: Sequence[str] = (),
                       preview_path: Optional[Path] = None,
                       dry_run: bool) -> ApplyReport:
    """Apply a remove-only config patch (IC-24 "Applier", AC-55/56/80/89/90/91).

    ``proposal.json`` is *only* consulted for ``project_yaml_sha256``, the
    candidate IDs, ``agent_meta_version`` and ``generator_options``: the
    candidates and their hunks are recomputed with :func:`collect_candidates` and
    the file hunks merely have to *match* the recomputed (redacted) ones. Anything
    that does not match -- a non-reproducible ID, a manipulated hunk, a hint, a
    credential key, a missing ``--accept-runtime`` for a ``confirm-runtime``
    candidate, a stale/version-mismatching proposal or a diverging preview --
    is all-or-nothing: the config is never touched. ``dry_run=True`` writes only
    ``<out>/preview.json`` (AC-90).
    """
    project_root = Path(project_root)
    agent_meta_root = Path(agent_meta_root)
    accept_ids = tuple(str(entry) for entry in accept_ids)
    accept_runtime_ids = tuple(str(entry) for entry in accept_runtime_ids)
    dry_run = bool(dry_run)

    if not accept_ids:
        return ApplyReport(dry_run=dry_run, exit_code=2, code=USAGE_CODE,
                           errors=("--accept is mandatory (no implicit application)",))
    if not dry_run and preview_path is None:
        return ApplyReport(dry_run=dry_run, exit_code=2, code=USAGE_CODE,
                           errors=("--preview <preview.json> or --dry-run is mandatory",))

    try:
        proposal = json.loads(Path(proposal_path).read_text(encoding="utf-8"))
    except (OSError, ValueError) as exc:
        return ApplyReport(dry_run=dry_run, exit_code=2, code=USAGE_CODE,
                           errors=("unreadable proposal.json: {}".format(exc),))
    if not isinstance(proposal, Mapping):
        return ApplyReport(dry_run=dry_run, exit_code=2, code=USAGE_CODE,
                           errors=("proposal.json is not a JSON object",))

    declared_ids, file_hunks = _proposal_candidates(proposal)
    generator_options = dict(proposal.get("generator_options") or {})
    declared_version = _to_string(proposal.get("agent_meta_version"))
    declared_hash = _to_string(proposal.get("project_yaml_sha256"))

    running_version = read_version(agent_meta_root)
    if declared_version != running_version:
        return ApplyReport(
            dry_run=dry_run, exit_code=1, code=VERSION_MISMATCH_CODE,
            agent_meta_version=running_version, generator_options=generator_options,
            errors=("proposal targets agent-meta {} but {} is running".format(
                declared_version or "<missing>", running_version),))

    config_path = project_root / _PROJECT_CONFIG_RELPATH
    try:
        config_text = config_path.read_text(encoding="utf-8")
        config = yaml.safe_load(config_text)
    except (OSError, yaml.YAMLError) as exc:
        return ApplyReport(dry_run=dry_run, exit_code=2, code=USAGE_CODE,
                           errors=("cannot read {}: {}".format(_PROJECT_CONFIG_RELPATH, exc),))
    if not isinstance(config, Mapping):
        return ApplyReport(dry_run=dry_run, exit_code=2, code=USAGE_CODE,
                           errors=("{} is not a mapping".format(_PROJECT_CONFIG_RELPATH),))
    config = dict(config)

    before_hash = hashlib.sha256(config_text.encode("utf-8")).hexdigest()
    if before_hash != declared_hash:
        return ApplyReport(dry_run=dry_run, exit_code=1, code=STALE_PROPOSAL_CODE,
                           project_yaml_sha256_before=before_hash,
                           project_yaml_sha256_after=before_hash,
                           agent_meta_version=running_version,
                           generator_options=generator_options,
                           errors=("project.yaml changed since the proposal was written",))

    # AC-90: cheap preview binding checks first, so a mismatching preview never
    # costs a recomputation.
    preview = None
    stored_preview_sha = ""
    if not dry_run:
        try:
            preview = json.loads(Path(preview_path).read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            return ApplyReport(dry_run=dry_run, exit_code=1, code=PREVIEW_MISMATCH_CODE,
                               project_yaml_sha256_before=before_hash,
                               project_yaml_sha256_after=before_hash,
                               errors=("unreadable preview.json: {}".format(exc),))
        if not isinstance(preview, Mapping):
            return ApplyReport(dry_run=dry_run, exit_code=1, code=PREVIEW_MISMATCH_CODE,
                               errors=("preview.json is not a JSON object",))
        preview = dict(preview)
        stored_preview_sha = _to_string(preview.pop("preview_sha256", ""))
        reason = _check_preview_binding(preview, accept_ids, accept_runtime_ids,
                                       before_hash, running_version, stored_preview_sha)
        if reason:
            return ApplyReport(dry_run=dry_run, exit_code=1, code=PREVIEW_MISMATCH_CODE,
                               project_yaml_sha256_before=before_hash,
                               project_yaml_sha256_after=before_hash,
                               preview_path=str(preview_path),
                               agent_meta_version=running_version,
                               generator_options=generator_options, errors=(reason,))

    try:
        recomputed = _recompute_candidates(
            project_root, agent_meta_root, config, config_text, generator_options)
        credentials = credential_paths(config, agent_meta_root)
    except RegistryError as exc:
        return ApplyReport(dry_run=dry_run, exit_code=2, code=exc.code, errors=(str(exc),))
    except (RuntimeError, OSError, subprocess.SubprocessError, yaml.YAMLError, ValueError) as exc:
        return ApplyReport(dry_run=dry_run, exit_code=2, code=RENDER_FAILED_CODE,
                           errors=(str(exc),))

    by_id = {candidate.id: candidate for candidate in recomputed.candidates}
    accepted: list = []
    rejected: list = []
    seen: set = set()
    for candidate_id in accept_ids:
        if candidate_id in seen:
            continue
        seen.add(candidate_id)
        candidate = by_id.get(candidate_id)
        if candidate is None or candidate_id not in declared_ids:
            rejected.append((candidate_id, REJECT_NOT_REPRODUCIBLE))
            continue
        if not candidate.applicable or not candidate.hunks:
            rejected.append((candidate_id, REJECT_NOT_APPLICABLE))
            continue
        if _matches_any(candidate.yaml_path, credentials):
            rejected.append((candidate_id, REJECT_CREDENTIAL_KEY))
            continue
        if (candidate.approval_level == "confirm-runtime"
                and candidate_id not in accept_runtime_ids):
            rejected.append((candidate_id, REJECT_NEEDS_RUNTIME))
            continue
        if candidate_id not in file_hunks:
            rejected.append((candidate_id, REJECT_HUNK_MISMATCH))
            continue
        if not all(_hunk_is_remove_only(hunk) for hunk in file_hunks[candidate_id]):
            # AC-80 (b) / threat model (d): a hunk that inserts a line is a
            # manipulated proposal -> nothing is written at all.
            return ApplyReport(dry_run=dry_run, exit_code=1, code=NOT_REMOVE_ONLY_CODE,
                               rejected=tuple(rejected), project_yaml_sha256_before=before_hash,
                               project_yaml_sha256_after=before_hash,
                               agent_meta_version=running_version,
                               generator_options=generator_options,
                               errors=("proposal hunk of {} inserts a line".format(
                                   candidate_id),))
        if tuple(candidate.hunks) != file_hunks[candidate_id]:
            rejected.append((candidate_id, REJECT_HUNK_MISMATCH))
            continue
        accepted.append(candidate)

    if accepted:
        after_text, _removed = _remove_keys(
            config_text, [candidate.yaml_path for candidate in accepted])
        if not _is_line_subsequence(config_text.splitlines(), after_text.splitlines()):
            return ApplyReport(dry_run=dry_run, exit_code=1, code=NOT_REMOVE_ONLY_CODE,
                               rejected=tuple(rejected), project_yaml_sha256_before=before_hash,
                               project_yaml_sha256_after=before_hash,
                               agent_meta_version=running_version,
                               generator_options=generator_options,
                               errors=("the derived config is not a line subsequence",))
    else:
        after_text = config_text

    if not dry_run and accepted:
        reason = _check_preview_hunks(preview, accepted)
        if reason:
            return ApplyReport(dry_run=dry_run, exit_code=1, code=PREVIEW_MISMATCH_CODE,
                               rejected=tuple(rejected), project_yaml_sha256_before=before_hash,
                               project_yaml_sha256_after=before_hash,
                               preview_path=str(preview_path),
                               agent_meta_version=running_version,
                               generator_options=generator_options, errors=(reason,))

    entries = [_preview_entry(candidate) for candidate in accepted]
    rejected_payload = [{"id": pid, "reason": reason} for pid, reason in rejected]
    body = _preview_body(accept_ids, accept_runtime_ids, before_hash, running_version,
                         recomputed.generator_options, entries, rejected_payload)
    preview_sha256 = _binding_digest(body)

    if rejected and not dry_run:
        # All-or-nothing: nothing at all is written -- no run dir, no protocol.
        return ApplyReport(rejected=tuple(rejected), preview_sha256=preview_sha256,
                           project_yaml_sha256_before=before_hash,
                           project_yaml_sha256_after=before_hash,
                           agent_meta_version=running_version,
                           generator_options=dict(recomputed.generator_options),
                           exit_code=1, dry_run=False)

    return _finish_apply(
        project_root=project_root, agent_meta_root=agent_meta_root, config=config,
        config_path=config_path, config_text=config_text, after_text=after_text,
        accepted=accepted, rejected=rejected, body=body, preview_sha256=preview_sha256,
        before_hash=before_hash, version=running_version, preview_path=preview_path,
        preview=preview, stored_preview_sha=stored_preview_sha, credentials=credentials,
        dry_run=dry_run)


def _finish_apply(*, project_root: Path, agent_meta_root: Path, config: Mapping,
                  config_path: Path, config_text: str, after_text: str,
                  accepted: Sequence[Candidate], rejected: Sequence[Tuple[str, str]],
                  body: Mapping, preview_sha256: str, before_hash: str, version: str,
                  preview_path: Optional[Path], preview: Optional[Mapping],
                  stored_preview_sha: str, credentials: Sequence[str],
                  dry_run: bool) -> ApplyReport:
    """Prove, then preview or write -- the write side of :func:`apply_config_patch`."""
    run_id = _run_id()
    proof_before: Optional[Path] = None
    proof_after: Optional[Path] = None
    try:
        run_dir = _applier_run_dir(project_root, config, run_id)
        if accepted:
            proof_before = resolve_work_dir(project_root, config, OPTIMIZER_SUBDIR,
                                            run_id + "-before", tool=_APPLIER_TOOL)
            proof_after = resolve_work_dir(project_root, config, OPTIMIZER_SUBDIR,
                                           run_id + "-after", tool=_APPLIER_TOOL)
    except TmpSinkError as exc:
        return ApplyReport(rejected=tuple(rejected), exit_code=2, code=exc.code,
                           errors=(exc.message,), dry_run=dry_run,
                           agent_meta_version=version,
                           generator_options=dict(body["generator_options"]))
    except OSError as exc:
        return ApplyReport(rejected=tuple(rejected), exit_code=2,
                           code=OUT_WRITE_FAILED_CODE, errors=(str(exc),), dry_run=dry_run,
                           agent_meta_version=version,
                           generator_options=dict(body["generator_options"]))

    def make(exit_code: int, *, code: str = "", errors: Sequence[str] = (),
             applied_ids: Sequence[str] = (), after: Optional[str] = None,
             preview_out: Optional[str] = None, log_out: Optional[str] = None,
             backup_keys: Sequence[str] = ()) -> ApplyReport:
        return ApplyReport(
            applied_ids=tuple(applied_ids), rejected=tuple(rejected),
            preview_sha256=preview_sha256,
            project_yaml_sha256_before=before_hash,
            project_yaml_sha256_after=after if after is not None else before_hash,
            backup_redacted_keys=tuple(backup_keys),
            log_path=log_out,
            preview_path=preview_out,
            run_dir=str(run_dir) if run_dir.exists() else None,
            agent_meta_version=version,
            generator_options=dict(body["generator_options"]),
            exit_code=exit_code, code=code, errors=tuple(errors), dry_run=dry_run)

    try:
        run_dir.mkdir(parents=True, exist_ok=True)
    except OSError as exc:
        return make(2, code=OUT_WRITE_FAILED_CODE, errors=(str(exc),))

    if not dry_run and not _same_device(run_dir, config_path.parent):
        # Rev. 3.3: os.replace cannot cross a filesystem boundary; abort before
        # anything is written rather than leaving a half-applied config.
        _discard_empty_dir(run_dir)
        return make(1, code=CROSS_DEVICE_CODE,
                    errors=("the tmp-sink is on a different device than .meta-config",))

    proof: Optional[ProofReport] = None
    try:
        if accepted:
            _render_into(agent_meta_root, config_text, proof_before)
            _render_into(agent_meta_root, after_text, proof_after)
            proof = prove(proof_before, proof_after, config_text, after_text, "L0")
    except RegistryError as exc:
        _discard_empty_dir(run_dir)
        return make(2, code=exc.code, errors=(str(exc),))
    except (RuntimeError, OSError, subprocess.SubprocessError, yaml.YAMLError, ValueError) as exc:
        _discard_empty_dir(run_dir)
        return make(2, code=RENDER_FAILED_CODE, errors=(str(exc),))
    finally:
        for work in (proof_before, proof_after):
            if work is not None:
                _discard_work_dir(work, work.parent.parent)

    proof_failed = proof is not None and not proof.ok
    proof_payload = None
    if proof is not None:
        proof_payload = {
            "level_reached": proof.level_reached,
            "ok": proof.ok,
            "files_compared": proof.files_compared,
            "byte_equal_files": proof.byte_equal_files,
            "reasons": list(proof.reasons),
        }

    if dry_run:
        payload = dict(body)
        if proof_payload is not None:
            payload["proof"] = proof_payload
        payload["preview_sha256"] = preview_sha256
        try:
            _write_json(run_dir / PREVIEW_NAME, payload)
        except OSError as exc:
            _discard_empty_dir(run_dir)
            return make(2, code=OUT_WRITE_FAILED_CODE, errors=(str(exc),))
        exit_code = 1 if (rejected or proof_failed) else 0
        codes = []
        if proof_failed:
            codes.extend(proof.reasons)
        return make(exit_code, errors=codes, preview_out=str(run_dir / PREVIEW_NAME),
                    applied_ids=[candidate.id for candidate in accepted])

    if proof_failed:
        # AC-55/IC-25: a proof that does not hold in the applier's own
        # recomputation aborts the whole application, nothing is written.
        _discard_empty_dir(run_dir)
        return make(1, code=PROOF_FAILED_CODE, errors=tuple(proof.reasons))

    # --- the atomic replace (Rev. 3.3) -------------------------------------
    backup_text, backup_keys = _redacted_config_text(
        config_text, config, sorted(credentials))
    transient = run_dir / _TRANSIENT_CONFIG_NAME
    try:
        transient.write_text(after_text, encoding="utf-8")
        restrict_owner_only(transient)
    except OSError as exc:
        _discard_empty_dir(run_dir)
        return make(2, code=OUT_WRITE_FAILED_CODE, errors=(str(exc),))

    if _TOCTOU_TEST_HOOK is not None:
        _TOCTOU_TEST_HOOK()
    try:
        current = config_path.read_text(encoding="utf-8")
    except OSError as exc:  # pragma: no cover - the file was readable above
        transient.unlink(missing_ok=True)
        _discard_empty_dir(run_dir)
        return make(2, code=OUT_WRITE_FAILED_CODE, errors=(str(exc),))
    if hashlib.sha256(current.encode("utf-8")).hexdigest() != before_hash:
        transient.unlink(missing_ok=True)  # N-12: discard the transient file
        _discard_empty_dir(run_dir)
        return make(1, code=STALE_PROPOSAL_CODE,
                    errors=("project.yaml changed between recomputation and replace",))

    try:
        _write_text_mode(backup_text, run_dir / BACKUP_NAME)
        os.replace(os.fspath(transient), os.fspath(config_path))
    except OSError as exc:
        transient.unlink(missing_ok=True)
        return make(2, code=OUT_WRITE_FAILED_CODE, errors=(str(exc),))

    after_hash = hashlib.sha256(after_text.encode("utf-8")).hexdigest()
    applied = {
        "accept_ids": list(body["accept_ids"]),
        "accept_runtime_ids": list(body["accept_runtime_ids"]),
        "rejected": list(body["rejected"]),
        "project_yaml_sha256_before": before_hash,
        "project_yaml_sha256_after": after_hash,
        "preview_sha256": stored_preview_sha or preview_sha256,
        "agent_meta_version": version,
        "generator_options": dict(body["generator_options"]),
        "timestamp": datetime.now().replace(microsecond=0).isoformat(),
        "approval_source": APPROVAL_SOURCE_RELAYED,
        "backup_redacted_keys": list(backup_keys),
    }
    log_path = run_dir / APPLIED_NAME
    try:
        _write_json(log_path, applied)
    except OSError as exc:  # pragma: no cover - pragmatic: the patch is applied
        return make(0, code=OUT_WRITE_FAILED_CODE, errors=(str(exc),),
                    applied_ids=[candidate.id for candidate in accepted], after=after_hash,
                    backup_keys=backup_keys)

    return make(0, applied_ids=[candidate.id for candidate in accepted], after=after_hash,
                log_out=str(log_path), backup_keys=backup_keys)


def _write_text_mode(text: str, path: Path) -> None:
    """Write *text* and restrict it to the owner (sink hardening, AC-89)."""
    path.write_text(text, encoding="utf-8")
    restrict_owner_only(path)
