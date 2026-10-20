"""Context-profile verification gate (2a.5, IC-36, AC-86 profile part).

``compact`` ships as an unverified opt-in: the role-routing eval that would
evidence AC-25 (``compact`` >= ``full`` baseline - 1 pp per metric) has not run.
This module answers the single question behind the INFO
``context-profile.unverified``: is there a passing ``compact`` evaluation
against a ``full`` baseline?

Evidence is read only from the agent-meta root
(``tests/routing-llm-eval/roles/{baseline,runs}``) and scored with
``eval_gate.evaluate_gate`` — never re-implemented here. A ``full``/default
profile never triggers the INFO; the INFO disappears as soon as a candidate
``compact`` result passes the gate (2f.3).
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Iterable, List, Literal, Mapping, Optional

from . import eval_gate
from .context_profile import ResolvedContextProfile

EVAL_ROLES_SUBDIR = Path("tests") / "routing-llm-eval" / "roles"
_BASELINE_SUBDIR = "baseline"
_RUNS_SUBDIR = "runs"

GateState = Literal["evidenced", "not-evidenced"]


def _iter_documents(roles_dir: Path) -> Iterable[Mapping]:
    for subdir in (_BASELINE_SUBDIR, _RUNS_SUBDIR):
        directory = roles_dir / subdir
        if not directory.is_dir():
            continue
        for path in sorted(directory.glob("*.json")):
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, ValueError):
                continue
            if isinstance(data, Mapping):
                yield data


def _evidence_status(doc: Mapping) -> Optional[str]:
    evidence = doc.get("evidence")
    if isinstance(evidence, Mapping):
        return evidence.get("status")
    return None


def _as_candidate(doc: Mapping) -> Optional[dict]:
    """Present a result document as an ``eval_gate`` candidate.

    ``model_classes`` values are single numbers per the ``evaluate_gate``
    contract; a baseline-shaped document (lists per metric) is collapsed to the
    mean so both shapes can serve as a candidate.
    """
    classes = doc.get("model_classes")
    if not isinstance(classes, Mapping):
        return None
    collapsed = {}
    for model_class, metrics in classes.items():
        if not isinstance(metrics, Mapping):
            continue
        collapsed[model_class] = {
            metric: (
                round(sum(values) / len(values), 6)
                if isinstance(values, (list, tuple)) and values
                else values
            )
            for metric, values in metrics.items()
        }
    return {
        "status": doc.get("status"),
        "corpus_hash": doc.get("corpus_hash"),
        "model_ids": doc.get("model_ids"),
        "model_classes": collapsed,
    }


def context_profile_gate_state(agent_meta_root: Path) -> GateState:
    """``evidenced`` iff a ``compact`` result passes a ``full`` baseline (AC-25).

    Baselines and candidates must both carry ``evidence.status == "evidenced"``;
    a matching corpus hash / model IDs are enforced by ``evaluate_gate``.
    """
    roles_dir = Path(agent_meta_root) / EVAL_ROLES_SUBDIR
    baselines: List[Mapping] = []
    candidates: List[Mapping] = []
    for doc in _iter_documents(roles_dir):
        if _evidence_status(doc) != "evidenced":
            continue
        if doc.get("profile") == "full":
            baselines.append(doc)
        elif doc.get("profile") == "compact":
            candidates.append(doc)
    for baseline in baselines:
        for candidate in candidates:
            probe = _as_candidate(candidate)
            if probe is None:
                continue
            if eval_gate.evaluate_gate(dict(baseline), probe) == eval_gate.PASSED:
                return "evidenced"
    return "not-evidenced"


def context_profile_info_lines(
    resolved: Iterable[ResolvedContextProfile],
    agent_meta_root: Path,
) -> List[str]:
    """INFO lines (one per ``compact`` provider) while AC-25 is unverified."""
    profiles = list(resolved)
    compact = [profile for profile in profiles if profile.profile == "compact"]
    if not compact:
        return []
    if context_profile_gate_state(agent_meta_root) == "evidenced":
        return []
    return [
        f"context-profile.unverified: {profile.provider} resolves to "
        "profile=compact without a passing 'compact' eval against a 'full' "
        "baseline (AC-25; see tests/routing-llm-eval/roles/)"
        for profile in compact
    ]
