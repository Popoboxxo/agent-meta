"""Provider-agnostic artifact validators.

Plan Task 1 (SPEC-PROVIDER-AUDIT-OPENCODE-V2-2026-09-30). One pure function per
artifact kind returns :class:`~lib.consistency.report.Finding` objects and never
writes or raises on malformed input.

Provider-agnostic by construction: the artifact **format** is a parameter
(``opencode-json-v2`` vs ``opencode-json``, a frontmatter allow-list, a TOML
document) — no function reads a provider name. This is the single place where a
silent-drop / invalid-artifact class is turned into a signal (design DECISION-3,
§4.3; spec §5).

Reuses ``scripts/lib/consistency/report.py::{Finding, Severity}``.
"""
from __future__ import annotations

import json
import re
from dataclasses import dataclass

try:  # Python >= 3.11 ships tomllib in the stdlib.
    import tomllib
except ModuleNotFoundError:  # pragma: no cover - Python < 3.11 fallback
    import tomli as tomllib

try:
    import yaml as _yaml

    _YAML_AVAILABLE = True
except ImportError:  # pragma: no cover - optional dependency
    _YAML_AVAILABLE = False

from .consistency.report import Finding, Severity
from .frontmatter import split_frontmatter

#: Finding check name. Matches the sync-log line ``artifact-contract: <message>``
#: (spec §5) and the AC-13 ``artifact-contract`` error label.
CHECK = "artifact-contract"

#: Top-level keys that belong to the deprecated v1 Opencode surface only.
_OPENCODE_V1_ONLY_KEYS = ("subagent_depth",)

#: Mechanisms whose artifacts are serialized as TOML, not Markdown frontmatter.
TOML_MECHANISMS = frozenset({"codex-toml"})

#: Frontmatter keys every generated agent artifact MUST carry.
REQUIRED_FIELDS = frozenset({"name", "description"})


@dataclass(frozen=True)
class ArtifactContract:
    """Resolved, provider-agnostic format contract for one provider's artifacts.

    Resolution reads only declared config **values** (``surface-version`` and
    ``agent-transform.{frontmatter-mechanism,allowed-fields,reject-fields}``),
    never a provider name. This is the single source of truth shared by the
    sync-time warning (``agent_sync``) and the consistency check
    (``consistency.artifact_contracts``) so the two cannot diverge.
    """

    mechanism: str
    allowed_fields: set[str] | None
    reject_fields: set[str]
    required_fields: frozenset[str] = REQUIRED_FIELDS


def _artifact_transform(provider_config: dict | None) -> dict:
    """The provider's ``agent-transform`` mapping (empty when absent/malformed)."""
    transform = (provider_config or {}).get("agent-transform")
    return transform if isinstance(transform, dict) else {}


def artifact_v2_surface(provider_config: dict | None) -> bool:
    """Whether the provider declares the v2 silent-drop surface (spec §2.1/§5).

    The allow-list is the v2 guard; the v1 byte shape keeps its unknown keys,
    which the runtime normalizes internally.
    """
    surface = str((provider_config or {}).get("surface-version", "v1"))
    mechanism = str(_artifact_transform(provider_config).get("frontmatter-mechanism", "provider-md"))
    return surface == "v2" or mechanism.endswith("-v2")


def resolve_artifact_contract(provider_config: dict | None) -> ArtifactContract:
    """Resolve one provider's declared artifact contract from config data only.

    The ``allowed-fields`` allow-list is enforced on the v2 surface only (spec
    §2.1/§5); this is the one place that rule is applied, so the sync-time
    warning and the consistency check cannot drift apart.
    """
    transform = _artifact_transform(provider_config)
    mechanism = str(transform.get("frontmatter-mechanism", "provider-md"))
    allowed = transform.get("allowed-fields")
    allowed_fields = (
        set(allowed)
        if isinstance(allowed, list) and allowed and artifact_v2_surface(provider_config)
        else None
    )
    return ArtifactContract(
        mechanism=mechanism,
        allowed_fields=allowed_fields,
        reject_fields=set(transform.get("reject-fields") or []),
    )


def _finding(path: str, message: str, suggestion: str = "") -> Finding:
    return Finding(Severity.ERROR, CHECK, path, message, suggestion)


def validate_toml(text: str, path: str) -> list[Finding]:
    """Parse ``text`` as TOML; a parse failure is a single ERROR Finding.

    An empty document is valid (``tomllib`` yields ``{}``). This closes the
    F1 class where a serialized artifact shipped a singleton block after the
    closing ``\"\"\"`` and a runtime parser rejected it while ``sync.py``
    exited ``0``.
    """
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as exc:
        return [_finding(path, f"invalid TOML: {exc}", "Re-serialize so the document parses.")]
    return []


def validate_frontmatter(
    text: str,
    *,
    allowed_fields: set[str] | None,
    required_fields: set[str],
    reject_fields: set[str],
    path: str,
) -> list[Finding]:
    """Validate a Markdown document's YAML frontmatter against field contracts.

    * ``required_fields`` — every listed key MUST be present.
    * ``allowed_fields`` — when not ``None``, every emitted key MUST be listed.
      ``None`` disables the allow-list (the conservative, no-false-positive
      default; spec §2.1).
    * ``reject_fields`` — every listed key MUST be absent.

    A missing block or malformed YAML yields exactly one ERROR Finding and no
    field-level findings (avoids double-reporting an unparseable document).
    """
    findings: list[Finding] = []

    block, _body = split_frontmatter(text)
    if not block:
        return [_finding(path, "missing YAML frontmatter block")]

    if not _YAML_AVAILABLE:  # pragma: no cover - PyYAML is a runtime dependency
        return [_finding(path, "PyYAML unavailable; cannot validate frontmatter")]

    inner = re.sub(r"^---\n?", "", block)
    inner = re.sub(r"\n?---\s*$", "", inner)
    try:
        parsed = _yaml.safe_load(inner)
    except _yaml.YAMLError as exc:
        return [_finding(path, f"frontmatter is not valid YAML: {exc}")]

    if not isinstance(parsed, dict):
        return [_finding(path, "frontmatter does not parse to a YAML mapping")]

    keys = set(parsed.keys())

    for field in sorted(required_fields - keys):
        findings.append(_finding(path, f"missing required frontmatter field '{field}'"))

    if allowed_fields is not None:
        for field in sorted(keys - set(allowed_fields)):
            findings.append(
                _finding(
                    path,
                    f"frontmatter field '{field}' is not in allowed-fields",
                    "Remove the field or add it to agent-transform.allowed-fields.",
                )
            )

    for field in sorted(keys & set(reject_fields)):
        findings.append(
            _finding(
                path,
                f"frontmatter field '{field}' is rejected (reject-fields)",
                "Remove the field from the emitted frontmatter.",
            )
        )

    return findings


def validate_artifact(text: str, contract: ArtifactContract, path: str) -> list[Finding]:
    """Validate *text* against a resolved *contract*.

    Dispatch is on the declared mechanism only (:data:`TOML_MECHANISMS`), never
    on a provider name. The caller resolves the contract once via
    :func:`resolve_artifact_contract`; this function is the single validation
    entry point for both the sync-time warning and the consistency check.
    """
    if contract.mechanism in TOML_MECHANISMS:
        return validate_toml(text, path)
    return validate_frontmatter(
        text,
        allowed_fields=contract.allowed_fields,
        required_fields=set(contract.required_fields),
        reject_fields=contract.reject_fields,
        path=path,
    )


def validate_json_document(text: str, fmt: str, path: str) -> list[Finding]:
    """Validate a JSON config document against the key shape implied by ``fmt``.

    * ``opencode-json-v2`` — the document MUST carry the nested ``mcp.servers``
      object and MUST NOT carry a flat top-level ``mcp`` server map nor a
      v1-only key (``subagent_depth``).
    * ``opencode-json`` — the document MUST carry the flat top-level ``mcp``
      object (frozen v1 byte shape, AC-21).

    Formats without a declared contract are not guessed (no findings).
    """
    try:
        doc = json.loads(text)
    except json.JSONDecodeError as exc:
        return [_finding(path, f"invalid JSON: {exc}")]

    if not isinstance(doc, dict):
        return [_finding(path, "JSON document root is not an object")]

    if fmt == "opencode-json-v2":
        return _validate_opencode_v2(doc, path)
    if fmt == "opencode-json":
        return _validate_opencode_v1(doc, path)
    return []


def _validate_opencode_v2(doc: dict, path: str) -> list[Finding]:
    findings: list[Finding] = []

    mcp = doc.get("mcp")
    if not isinstance(mcp, dict):
        findings.append(
            _finding(path, "opencode-json-v2 requires the nested 'mcp.servers' object")
        )
    elif "servers" not in mcp:
        findings.append(
            _finding(
                path,
                "opencode-json-v2 'mcp' is a flat v1 server map; expected nested "
                "'mcp.servers'",
            )
        )
    else:
        if not isinstance(mcp["servers"], dict):
            findings.append(
                _finding(path, "opencode-json-v2 'mcp.servers' must be an object")
            )
        # Any sibling of 'servers' is a flat-shape leak (v1 wrote servers here).
        for field in sorted(set(mcp) - {"servers"}):
            findings.append(
                _finding(
                    path,
                    f"opencode-json-v2 'mcp' carries flat key '{field}' next to "
                    "'servers'",
                )
            )

    for field in _OPENCODE_V1_ONLY_KEYS:
        if field in doc:
            findings.append(
                _finding(path, f"opencode-json-v2 must not carry v1-only key '{field}'")
            )

    return findings


def _validate_opencode_v1(doc: dict, path: str) -> list[Finding]:
    if not isinstance(doc.get("mcp"), dict):
        return [_finding(path, "opencode-json requires the flat top-level 'mcp' object")]
    return []
