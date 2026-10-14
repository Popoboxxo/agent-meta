"""Doctor runner (IC-22, Task 0d.2): registry-driven diagnosis of an installation.

``run_doctor`` loads ``<agent_meta_root>/config/known-issues.yaml`` (the only
registry source, AC-78), evaluates the predicates per active provider, runs the
detectors (:mod:`lib.doctor_detectors`) and returns a sorted
:class:`DoctorReport`. The runner never writes a file: the sole write target of
the doctor tool set (``--out`` in the tmp-sink) belongs to the CLI (Task 0d.3).

Severity rule (ADR-11, spec IC-22): effective severity = min(registry severity,
level of the referenced check, UNVERIFIED cap per provider). Finding text is a
registry template with bindings; artifact content only appears in ``quoted``
(at most 120 characters) and as ``file[:line]``.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, replace
from pathlib import Path
from typing import Sequence

import yaml

from .active_set import compute_active_set
from .consistency.report import Finding, Severity
from .context_report import merge_provider_mappings
from .deactivation import get_active_providers
from .doctor_detectors import (
    DetectorSkipped, DetectorUnavailable, Hit, detect,
)
from .doctor_formats import QUOTED_MAX, clip
from .doctor_predicates import (
    Env, base_bindings, evaluate_predicates, fixed_in_reached, needs_provider,
    passes_deferred, render, resolve_verified_state,
)
from .doctor_registry import load_validation_context, validate_entry
from .providers import load_provider_capabilities, load_providers_config
from .repo_containment import resolve_effective_repo_containment

REGISTRY_REL = "config/known-issues.yaml"
REGISTRY_VERSION = 1
CHECK_REGISTRY_INVALID = "doctor.registry-invalid"
CHECK_DETECTOR_UNAVAILABLE = "doctor.detector-unavailable"
CHECK_PROVIDER_FILTER = "doctor.provider-filter"
SKIP_FIXED_IN = "fixed-in"
SKIP_PREDICATE = "predicate"
SKIP_UNAVAILABLE = "detector-unavailable"
SKIP_INVALID = "registry-invalid"
_RANK = {Severity.INFO: 0, Severity.WARNING: 1, Severity.ERROR: 2}


@dataclass
class DoctorFinding(Finding):
    """Finding of the doctor; superset of ``consistency.report.Finding``."""

    issue_id: str = ""
    provider: str = ""            # empty = provider-independent
    verified_state: str = ""
    evidence: str = ""
    fix_owner: str = ""
    severity_registry: str = ""   # severity declared by the registry entry
    quoted: str = ""              # artifact excerpt, at most 120 characters
    ref_check: str = ""           # check id behind a finding-ref


@dataclass(frozen=True)
class DoctorReport:
    findings: tuple[DoctorFinding, ...]
    # (issue_id, reason: fixed-in|predicate|detector-unavailable|registry-invalid)
    skipped: tuple[tuple[str, str], ...]
    registry_version: int
    agent_meta_version: str


# ------------------------------------------------------------------- registry

def _runner_finding(check: str, issue_id: str, message: str, suggestion: str,
                    severity: Severity, registry: Severity) -> DoctorFinding:
    return DoctorFinding(
        severity, check, REGISTRY_REL, message, suggestion, issue_id=issue_id,
        verified_state="VERIFIED-SOURCE", fix_owner="framework-issue",
        evidence="source: scripts/lib/doctor.py", severity_registry=registry.value)


def _invalid_finding(issue_id: str, error: str) -> DoctorFinding:
    # WARNING without --strict (spec IC-21 H-6); the registry level ERROR lets the
    # CLI raise it to ERROR / exit 2 for --strict (Task 0d.3).
    subject = f"entry {issue_id!r}" if issue_id else "file"
    return _runner_finding(
        CHECK_REGISTRY_INVALID, issue_id,
        f"known-issues registry {subject} is invalid and was skipped",
        clip(error, 200), Severity.WARNING, Severity.ERROR)


def load_known_issues(agent_meta_root: Path) -> tuple[list[dict], list[DoctorFinding]]:
    """Load and validate the registry; fail-soft, never raises.

    Only ``<agent_meta_root>/config/known-issues.yaml`` is read: no project
    override, no search path, no extension (AC-78). Invalid entries are skipped
    and reported as ``doctor.registry-invalid`` findings.
    """
    root = Path(agent_meta_root)
    try:
        doc = yaml.safe_load((root / REGISTRY_REL).read_text(encoding="utf-8"))
        ctx = load_validation_context(root)
    except (OSError, ValueError, KeyError, TypeError, AttributeError, yaml.YAMLError) as exc:
        return [], [_invalid_finding("", f"registry could not be loaded: {type(exc).__name__}")]
    if (not isinstance(doc, dict) or doc.get("registry-version") != REGISTRY_VERSION
            or not isinstance(doc.get("issues"), list) or not doc["issues"]):
        return [], [_invalid_finding("", "registry-version must be 1 and issues a non-empty list")]
    valid, findings, seen = [], [], set()
    for entry in doc["issues"]:
        eid = entry.get("id") if isinstance(entry, dict) else None
        try:
            errors = validate_entry(entry, ctx) if isinstance(entry, dict) else ["entry not a mapping"]
        except Exception as exc:  # validator must never crash the doctor
            errors = [f"validator failed: {type(exc).__name__}"]
        if eid in seen:
            errors = errors + [f"duplicate id {eid!r}"]
        seen.add(eid)
        if errors:
            findings.append(_invalid_finding(str(eid or ""), errors[0]))
        else:
            valid.append(entry)
    return valid, findings


# ---------------------------------------------------------------------- runner

def _agent_meta_version(agent_meta_root: Path) -> str:
    try:
        return (agent_meta_root / "VERSION").read_text(encoding="utf-8").strip() or "unknown"
    except OSError:
        return "unknown"


def _effective_severity(entry: dict, hit: Hit, state: str) -> tuple:
    registry = Severity(entry["severity"])
    effective = registry if hit.severity is None else min(registry, hit.severity, key=_RANK.get)
    if state == "UNVERIFIED":  # ADR-11 cap, evaluated per provider
        effective = min(effective, Severity.WARNING, key=_RANK.get)
    return registry, effective


def _build_finding(entry: dict, env: Env, hit: Hit, bindings: dict) -> DoctorFinding:
    state = resolve_verified_state(entry, env)
    registry, effective = _effective_severity(entry, hit, state)
    # binding values may stem from artifact names: strip control chars, cap length
    values = {k: clip(v) for k, v in {**env.bindings, **bindings}.items()}
    file = hit.file or render(entry["target"].get("path"), values)
    if hit.line:
        file = f"{file}:{hit.line}"
    ev = entry["evidence"]
    return DoctorFinding(
        effective, "doctor." + entry["id"], file,
        render(entry.get("message") or entry["title"], values),
        render(entry["fix-hint"], values),
        issue_id=entry["id"], provider=hit.provider or env.provider, verified_state=state,
        evidence=f"{ev['kind']}: {ev['ref']} ({ev['date']})",
        fix_owner=entry["fix-owner"], severity_registry=registry.value,
        quoted=clip(hit.quoted, QUOTED_MAX), ref_check=hit.ref_check)


def _unavailable_finding(entry: dict, env: Env, reason: str) -> DoctorFinding:
    return DoctorFinding(
        Severity.INFO, CHECK_DETECTOR_UNAVAILABLE, "",
        f"Detector of known issue {entry['id']!r} is unavailable in this environment",
        clip(reason, 200), issue_id=entry["id"], provider=env.provider,
        verified_state="VERIFIED-SOURCE", fix_owner="project-config",
        evidence="source: scripts/lib/doctor_detectors.py", severity_registry="INFO")


def _filter_finding(name: str, known: bool) -> DoctorFinding:
    why = "is not active in this project" if known else "is not a registered provider"
    return DoctorFinding(
        Severity.INFO, CHECK_PROVIDER_FILTER, "",
        "A requested provider was ignored by the provider filter",
        f"Provider {clip(name, 40)!r} {why}; only active providers are checked.",
        provider=clip(name, 40), verified_state="VERIFIED-SOURCE",
        fix_owner="project-config", evidence="source: scripts/lib/doctor.py",
        severity_registry="INFO")


def _provider_env(base: Env, provider: str) -> Env:
    caps = base.caps_map.get(provider) or {}
    return replace(base, provider=provider, providers=(provider,), caps=caps,
                   bindings=base_bindings(provider, caps, base.bindings["tmp_sink"]))


def _run_entry(entry: dict, base: Env, findings: list, skipped: set) -> None:
    envs = ([_provider_env(base, p) for p in base.providers]
            if needs_provider(entry) else [base])
    applied = False
    for env in envs:
        combos, deferred = evaluate_predicates(entry.get("applies_to"), env)
        for combo in combos:
            applied = True
            sub = replace(env, bindings={**env.bindings, **combo})
            try:
                hits = detect(entry["detector"], sub, entry["target"])
            except DetectorSkipped:
                skipped.add((entry["id"], SKIP_PREDICATE))
                continue
            except DetectorUnavailable as exc:
                skipped.add((entry["id"], SKIP_UNAVAILABLE))
                if exc.notify:
                    findings.append(_unavailable_finding(entry, env, exc.reason))
                continue
            for hit in hits:
                bindings = {**combo, **hit.bindings}
                if passes_deferred(deferred, bindings):
                    findings.append(_build_finding(entry, sub, hit, bindings))
    if not applied:
        skipped.add((entry["id"], SKIP_PREDICATE))


def _sort_key(f: DoctorFinding) -> tuple:
    return (-_RANK[f.severity], f.issue_id, f.provider, f.file, f.check, f.message, f.quoted)


def _dedupe(findings: list) -> list:
    unique = {}
    for f in findings:
        unique.setdefault((f.check, f.issue_id, f.provider, f.file, f.message, f.quoted), f)
    return sorted(unique.values(), key=_sort_key)


def run_doctor(project_root: Path, agent_meta_root: Path, config: dict, *,
               providers: Sequence[str] | None = None) -> DoctorReport:
    """Evaluate the registry against the project installation (read-only).

    Order (spec IC-22): sync.log snapshot, static / ``finding-ref`` detectors,
    then ``command`` detectors. ``providers`` is intersected with the active
    providers of *config* (``None`` = all active providers); a requested name that
    is unknown or not active is ignored and reported as INFO ``doctor.provider-filter``.
    """
    project_root, agent_meta_root = Path(project_root), Path(agent_meta_root)
    config = config if isinstance(config, dict) else {}
    entries, findings = load_known_issues(agent_meta_root)
    skipped = {(f.issue_id, SKIP_INVALID) for f in findings if f.issue_id}
    version = _agent_meta_version(agent_meta_root)

    provider_config = load_providers_config(agent_meta_root, config)
    names = get_active_providers(config, provider_config)
    if providers is not None:
        for name in sorted(set(providers) - set(names)):
            known = name in provider_config
            findings.append(_filter_finding(name, known))
        names = [p for p in names if p in set(providers)]
    caps_map = merge_provider_mappings(
        provider_config, load_provider_capabilities(agent_meta_root))
    effective = resolve_effective_repo_containment(config)
    base = Env(
        project_root=project_root, agent_meta_root=agent_meta_root, config=config,
        active_set=compute_active_set(config, agent_meta_root, project_root, warn_sink=[]),
        caps_map=caps_map, provider_config=provider_config, providers=tuple(names),
        bindings=base_bindings("", {}, effective.tmp_sink_path),
        sink_enabled=effective.tmp_sink_enabled,
        shared={"own_variable_seeds": {
            e["detector"]["key"] for e in entries
            if e["detector"].get("kind") == "variable-unreferenced"
            and e["detector"]["key"] != "*"}})

    ordered = sorted(entries, key=lambda e: e["detector"].get("kind") == "command")
    for entry in ordered:
        if fixed_in_reached(version, entry.get("fixed-in")):
            skipped.add((entry["id"], SKIP_FIXED_IN))
            continue
        _run_entry(entry, base, findings, skipped)

    return DoctorReport(
        findings=tuple(_dedupe(findings)), skipped=tuple(sorted(skipped)),
        registry_version=REGISTRY_VERSION if entries else 0,
        agent_meta_version=version)


# ---------------------------------------------------------------------- output

def report_to_dict(report: DoctorReport) -> dict:
    """JSON-serialisable form (superset of ``print_json_report``, doctor-findings-v1)."""
    findings = [{
        "severity": f.severity.value, "check": f.check, "file": f.file,
        "message": f.message, "suggestion": f.suggestion, "issue_id": f.issue_id,
        "provider": f.provider, "verified_state": f.verified_state,
        "evidence": f.evidence, "fix_owner": f.fix_owner, "quoted": f.quoted,
        "ref_check": f.ref_check, "severity_registry": f.severity_registry,
        "severity_effective": f.severity.value,
    } for f in report.findings]
    count = lambda sev: sum(1 for f in report.findings if f.severity == sev)  # noqa: E731
    return {
        "findings": findings,
        "summary": {
            "total": len(findings), "errors": count(Severity.ERROR),
            "warnings": count(Severity.WARNING), "infos": count(Severity.INFO),
            "registry_version": report.registry_version,
            "agent_meta_version": report.agent_meta_version,
            "skipped": [{"issue_id": i, "reason": r} for i, r in report.skipped],
            "severity": [{
                "issue_id": f["issue_id"], "provider": f["provider"], "file": f["file"],
                "severity_registry": f["severity_registry"],
                "severity_effective": f["severity_effective"],
            } for f in findings],
        },
    }


def print_doctor_json(report: DoctorReport) -> int:
    """Print the deterministic JSON report; exit code 1 if an effective ERROR exists."""
    data = report_to_dict(report)
    print(json.dumps(data, indent=2, ensure_ascii=False, sort_keys=True))
    return 1 if data["summary"]["errors"] else 0
