# Orchestration Dry-Run Engine
# Simulates orchestrator decisions without real agent execution

"""
OrchestratorDryRun — Provider-agnostic orchestration simulation and plan
validator (repurposed per issue #265, spike §2.4).

Usage:
    engine = OrchestratorDryRun(provider="Opencode", config={"max-parallel-agents": 4})
    report = engine.run("Fix Bug A, B, C")
    print(report.to_markdown())

Since issue #265 the engine is a thin SIMULATION wrapper around the
production plan validator ``scripts.lib.orchestration``:

- Parallel capability is looked up from
  ``config/provider-capabilities.yaml`` (``fanout_mechanism``) via
  ``DelegationSyntaxEngine.has_async_fanout`` — no hardcoded provider list
  (this replaces the former provider-agnostic-policy violation).
- The task graph (cycles / deadlocks / duplicate ids) is validated through
  ``orchestration.find_dependency_errors`` BEFORE any dispatch plan is
  generated; a broken graph fails closed to a fully sequential plan.
- The static file-affinity gate (issue #266) runs through the
  ``orchestration.check_plan_file_overlap`` seam; conflicted tasks are
  sequentialized instead of dispatched in parallel.
- Emitted FANOUT batches are re-validated through
  ``orchestration.validate_plan`` (over-commitment, duplicate ids) instead
  of hand-rolled checks.

Real enforcement (calling the checks before an ACTUAL dispatch) stays
harness-side — this engine is the dry-run simulation of that gate.
"""

import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


def _ensure_repo_root_on_path() -> None:
    """Prepend the repo root to sys.path (direct-CLI import fallback)."""
    repo_root = str(Path(__file__).resolve().parents[3])
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)


try:
    from scripts.lib.orchestration import (  # noqa: F401  (validate_plan used below)
        FanoutPlan,
        FanoutTask,
        check_plan_file_overlap,
        find_dependency_errors,
        validate_plan,
    )

    _FILE_AFFINITY_AVAILABLE = True
except ImportError:
    # Direct CLI execution (`python engine.py`) has the script directory —
    # not the repo root — on sys.path. Retry once with the repo root
    # prepended so CLI and pytest runs get identical gating behavior.
    _ensure_repo_root_on_path()
    try:
        from scripts.lib.orchestration import (
            FanoutPlan,
            FanoutTask,
            check_plan_file_overlap,
            find_dependency_errors,
            validate_plan,
        )

        _FILE_AFFINITY_AVAILABLE = True
    except ImportError:
        _FILE_AFFINITY_AVAILABLE = False

# Capability lookup is INDEPENDENT of the analysis seam (issue #265): the
# #266 degradation contract ("module unavailable → no gate, no event") must
# not degrade the fanout capability resolution with it.
try:
    from scripts.lib.delegation_syntax import DelegationSyntaxEngine

    _CAPABILITY_ENGINE_AVAILABLE = True
except ImportError:
    _ensure_repo_root_on_path()
    try:
        from scripts.lib.delegation_syntax import DelegationSyntaxEngine

        _CAPABILITY_ENGINE_AVAILABLE = True
    except ImportError:
        _CAPABILITY_ENGINE_AVAILABLE = False

# Shared DelegationSyntaxEngine (lazy singleton — capability YAML is loaded
# once per process, not once per OrchestratorDryRun instance).
_SYNTAX_ENGINE: "DelegationSyntaxEngine | None" = None


def _shared_syntax_engine() -> "DelegationSyntaxEngine":
    """Return the process-wide capability/syntax engine (lazy init)."""
    global _SYNTAX_ENGINE
    if _SYNTAX_ENGINE is None:
        _SYNTAX_ENGINE = DelegationSyntaxEngine()
    return _SYNTAX_ENGINE


def _fanout_tasks_from_subtasks(subtasks: "list[SubTask]") -> "tuple[FanoutTask, ...]":
    """Map dry-run SubTasks to orchestration plan tasks (validation input)."""
    return tuple(
        FanoutTask(
            task_id=st.name,
            target_agent=st.agent_type,
            prompt=st.description,
            dependencies=tuple(st.dependencies),
        )
        for st in subtasks
    )


@dataclass
class SubTask:
    """A decomposed sub-task."""
    name: str
    agent_type: str
    description: str
    dependencies: list[str] = field(default_factory=list)


@dataclass
class DispatchPlan:
    """Execution plan with FANOUT, PARALLEL_GROUP, or sequential steps."""
    operations: list[dict[str, Any]] = field(default_factory=list)
    
    def to_dict(self) -> dict:
        return {"operations": self.operations}


@dataclass
class SyntaxReport:
    """Validation result for provider-specific syntax."""
    valid: bool
    provider: str
    parallel_supported: bool
    operation: str
    agent_count: int
    errors: list[str] = field(default_factory=list)


@dataclass
class DryRunEvent:
    """A single event in the dry-run timeline."""
    timestamp: str
    type: str
    data: dict[str, Any]


@dataclass
class DryRunReport:
    """Complete dry-run report."""
    intent: str
    subtasks: list[SubTask]
    plan: DispatchPlan
    syntax: SyntaxReport
    provider: str
    events: list[DryRunEvent]
    
    def to_dict(self) -> dict:
        return {
            "intent": self.intent,
            "subtasks": len(self.subtasks),
            "plan": self.plan.to_dict(),
            "syntax": {
                "valid": self.syntax.valid,
                "provider": self.syntax.provider,
                "parallel_supported": self.syntax.parallel_supported,
            },
            "provider": self.provider,
            "events": len(self.events),
        }
    
    def to_markdown(self) -> str:
        lines = [
            "# Orchestration Dry-Run Report",
            "",
            f"**Provider:** {self.provider}",
            f"**Intent:** {self.intent}",
            f"**Sub-Tasks:** {len(self.subtasks)}",
            f"**Parallel:** {self.syntax.parallel_supported}",
            f"**Syntax Valid:** {self.syntax.valid}",
            "",
            "## Sub-Tasks",
            "",
        ]
        for st in self.subtasks:
            deps = f" (depends on: {', '.join(st.dependencies)})" if st.dependencies else ""
            lines.append(f"- `{st.agent_type}`: {st.description}{deps}")
        
        lines.extend(["", "## Events", ""])
        for i, ev in enumerate(self.events, 1):
            lines.append(f"{i}. `{ev.type}` — {json.dumps(ev.data, ensure_ascii=False)[:80]}")
        
        return "\n".join(lines)


class OrchestratorDryRun:
    """Simulates Orchestrator decisions without real agent execution."""

    # Known intents mapping: keyword -> agent
    # Order matters: longer keywords should be checked first to avoid partial matches
    # e.g. "login" should not match "log"
    INTENT_MAP = {  # noqa: RUF012
        # German keywords (longer first)
        "implementieren": "developer",
        "hinzufügen": "developer",
        "analysiere": "ideation",
        "analysieren": "ideation",
        "architektur": "ideation",
        "dokumentation": "documenter",
        "dokumentiere": "documenter",
        "anforderung": "requirements",
        "anforderungen": "requirements",
        "feature": "feature",
        "erstelle": "feature",
        "schreibe": "developer",
        "test": "tester",
        "tests": "tester",
        "validiere": "validator",
        "validieren": "validator",
        "release": "release",
        "feedback": "feedback",
        "upgrade": "agent-meta-manager",
        "meta": "agent-meta-manager",
        "log": "log-analyzer",
        "füge": "developer",
        # English keywords (longer first)
        "implement": "developer",
        "analyze": "ideation",
        "analyse": "ideation",
        "architecture": "ideation",
        "document": "documenter",
        "requirement": "requirements",
        "requirements": "requirements",
        "commit": "git",
        "push": "git",
        "branch": "git",
        "fix": "developer",
        "bug": "developer",
        "design": "ideation",
        "doc": "documenter",
        "sync": "agent-meta-manager",
        "issue": "feedback",
    }

    @classmethod
    def _word_boundary_search(cls, text: str, keyword: str) -> bool:
        """Search for keyword with word boundaries to avoid partial matches."""
        import re
        # Use word boundary regex: \bkeyword\b
        pattern = r'\b' + re.escape(keyword) + r'\b'
        return bool(re.search(pattern, text, re.IGNORECASE))

    def __init__(self, provider: str, config: dict):
        self.provider = provider
        self.config = config
        self.max_parallel = config.get("max-parallel-agents", 4)
        self.events: list[DryRunEvent] = []
        # Issue #265: capability-driven parallel support. Replaces the former
        # hardcoded `provider in ["Claude", "Opencode", "Gemini"]` (a
        # provider-agnostic-policy violation): the FANOUT mechanism comes
        # from config/provider-capabilities.yaml. Unknown providers and the
        # no-capability-engine degradation both fail closed to sequential.
        self._fanout_mechanism: str | None = None
        self._parallel_supported = False
        if _CAPABILITY_ENGINE_AVAILABLE:
            engine = _shared_syntax_engine()
            # Invalid mechanism keys raise (config drift must fail loudly in
            # a dev tool); the post-sync consistency check reports the same
            # drift as a Finding for production syncs.
            self._fanout_mechanism = engine.get_fanout_mechanism(provider)
            self._parallel_supported = engine.has_async_fanout(provider)

    def log_event(self, event_type: str, data: dict):
        """Log an event for Viz-Log integration."""
        from datetime import datetime
        self.events.append(DryRunEvent(
            timestamp=datetime.now().isoformat(),  # noqa: DTZ005
            type=event_type,
            data=data,
        ))

    def classify_intent(self, user_input: str) -> str:
        """Classify user intent and return target agent."""
        user_lower = user_input.lower()
        
        # Check for user override triggers
        override_triggers = [
            "nicht delegieren", "mach das hier", "im hauptchat",
            "kein orchestrator", "ohne orchestrator", "ich will hier arbeiten",
            "delegiere nicht", "not delegate", "do it here", "no orchestrator",
            "without orchestrator", "main chat", "hauptchat",
        ]
        for trigger in override_triggers:
            if trigger in user_lower:
                self.log_event("intent_classified", {"input": user_input, "intent": "USER_OVERRIDE"})
                return "USER_OVERRIDE"
        
        # Check for unknown (very vague input)
        if len(user_input.split()) <= 3 and any(word in user_lower for word in ["ding", "kram", "something", "etwas", "irgendwas"]):
            self.log_event("intent_classified", {"input": user_input, "intent": "UNKNOWN"})
            return "UNKNOWN"
        
        # Map intent: sort keywords by length descending to prefer longer matches
        # e.g. "login" should not match "log", "analysiere" should not match "analyse"
        sorted_keywords = sorted(self.INTENT_MAP.items(), key=lambda x: len(x[0]), reverse=True)
        
        for keyword, agent in sorted_keywords:
            if self._word_boundary_search(user_lower, keyword):
                self.log_event("intent_classified", {"input": user_input, "intent": agent})
                return agent
        
        self.log_event("intent_classified", {"input": user_input, "intent": "UNKNOWN"})
        return "UNKNOWN"

    def decompose_task(self, user_input: str, intent: str) -> list[SubTask]:
        """Decompose multi-tasks into sub-tasks."""
        import re
        
        # Known parallelizable intents: can FANOUT if multiple independent sub-tasks
        parallelizable = ["developer", "tester", "documenter", "ideation"]
        
        if intent in parallelizable:
            # Split by comma or "and" / "und" (English/German)
            # Pattern: comma, or " and " / " und " with word boundaries
            parts = re.split(r',\s*|\bund\b|\band\b', user_input, flags=re.IGNORECASE)
            parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 2]
            
            if len(parts) > 1:
                # Further split by "für" / "for" if present to extract target modules
                # e.g. "Schreib Tests für Modul A, B und C" -> extract A, B, C
                final_parts = []
                for part in parts:
                    # Check if part contains "für" / "for" + list of items
                    for prep in [r'für', r'for']:
                        if re.search(rf'\b{prep}\b', part, re.IGNORECASE):
                            # Split the part after the preposition
                            match = re.search(rf'(.*?)\b{prep}\b\s*(.+)', part, re.IGNORECASE)
                            if match:
                                prefix = match.group(1).strip()
                                items_text = match.group(2).strip()
                                # Try to split items by comma or "and"/"und"
                                items = re.split(r',\s*|\bund\b|\band\b', items_text, flags=re.IGNORECASE)
                                items = [it.strip() for it in items if it.strip() and len(it.strip()) > 0]
                                if len(items) > 1:
                                    for item in items:
                                        final_parts.append(f"{prefix} {item}".strip() if prefix else item)
                                    break
                                    
                    if not final_parts or part not in [fp.split()[-1] if ' ' in fp else fp for fp in final_parts]:
                        final_parts.append(part)
                
                # Remove duplicates while preserving order
                seen = set()
                unique_parts = []
                for p in final_parts:
                    key = p.lower()
                    if key not in seen:
                        seen.add(key)
                        unique_parts.append(p)
                
                if len(unique_parts) > 1:
                    subtasks = []
                    for i, part in enumerate(unique_parts, 1):
                        subtasks.append(SubTask(
                            name=f"task_{i}",
                            agent_type=intent,
                            description=part,
                        ))
                    self.log_event("task_decomposed", {
                        "subtasks": len(subtasks),
                        "decomposition": "FANOUT",
                        "original": user_input,
                    })
                    return subtasks
        
        # Single task
        self.log_event("task_decomposed", {"subtasks": 1, "decomposition": "DIRECT"})
        return [SubTask(name="task_1", agent_type=intent, description=user_input)]

    def _validate_task_graph(self, subtasks: list["SubTask"]) -> list[str]:
        """Cycle / deadlock / duplicate-id validation BEFORE plan generation.

        Delegates to ``orchestration.find_dependency_errors`` (issue #265 —
        the validation logic lives in scripts/lib, no duplicate here). An
        empty result means the graph is dispatchable.
        """
        if not _FILE_AFFINITY_AVAILABLE or len(subtasks) < 2:
            return []
        return find_dependency_errors(_fanout_tasks_from_subtasks(subtasks))

    def _partition_by_file_affinity(
        self, subtasks: list["SubTask"]
    ) -> tuple[list["SubTask"], list["SubTask"]]:
        """Split subtasks by static file-affinity analysis (issue #266).

        Runs the static analysis through the orchestration seam
        (``check_plan_file_overlap``) BEFORE any simulated FANOUT /
        PARALLEL_GROUP emission and returns (safe, conflicted) in original
        input order. Falls back to (all subtasks, []) when the analysis
        module is unavailable — a real dispatch is gated harness-side; this
        is only the dry-run simulation.
        """
        if _FILE_AFFINITY_AVAILABLE and len(subtasks) >= 2:
            overlap = check_plan_file_overlap(
                FanoutPlan(kind="parallel_group", tasks=_fanout_tasks_from_subtasks(subtasks))
            )
            conflicted_ids = {
                task_id
                for task_a, task_b, _files in overlap["conflict"]
                for task_id in (task_a, task_b)
            }
            safe = [st for st in subtasks if st.name not in conflicted_ids]
            conflicted = [st for st in subtasks if st.name in conflicted_ids]
            self.log_event("file_overlap_checked", {
                "safe": overlap["safe"],
                "conflicts": overlap["conflict"],
                "sequentialized": [st.name for st in conflicted],
                "method": "static-analysis",
                "enforcement": "harness-side",
            })
            return safe, conflicted
        return subtasks, []

    def generate_dispatch_plan(self, subtasks: list[SubTask]) -> DispatchPlan:
        """Generate dispatch plan based on sub-tasks and provider capabilities."""
        plan = DispatchPlan()

        # Issue #265: graph validation (cycles / deadlocks / duplicate ids)
        # runs BEFORE any dispatch emission — fail closed to a fully
        # sequential plan instead of dispatching an unresolvable graph.
        graph_errors = self._validate_task_graph(subtasks)
        if graph_errors:
            self.log_event("plan_validation_failed", {"errors": graph_errors})
            for st in subtasks:
                plan.operations.append({
                    "type": "SEQUENTIAL",
                    "agent": st.agent_type,
                    "task": st.description,
                })
            self.log_event("dispatch_plan_generated", plan.to_dict())
            return plan

        if len(subtasks) == 1:
            plan.operations.append({
                "type": "DIRECT",
                "agent": subtasks[0].agent_type,
                "task": subtasks[0].description,
            })
        elif not self._parallel_supported:
            # Sequential fallback for Continue
            for st in subtasks:
                plan.operations.append({
                    "type": "SEQUENTIAL",
                    "agent": st.agent_type,
                    "task": st.description,
                })
        else:
            # Issue #266: static file-affinity gate BEFORE parallel
            # emission — conflicted tasks are sequentialized instead of
            # being dispatched in parallel (race-condition prevention).
            safe_subtasks, conflicted_subtasks = self._partition_by_file_affinity(subtasks)

            parallel_emitted = False
            if len(safe_subtasks) >= 2:
                # Check if all same agent type → FANOUT
                agent_types = {st.agent_type for st in safe_subtasks}
                if len(agent_types) == 1:
                    # FANOUT with batching if needed
                    batches = []
                    current_batch = []
                    for st in safe_subtasks:
                        current_batch.append(st)
                        if len(current_batch) >= self.max_parallel:
                            batches.append(current_batch)
                            current_batch = []
                    if current_batch:
                        batches.append(current_batch)

                    for i, batch in enumerate(batches, 1):
                        plan.operations.append({
                            "type": "FANOUT",
                            "batch": i,
                            "agents": [st.agent_type for st in batch],
                            "tasks": [st.description for st in batch],
                        })
                        if i < len(batches):
                            plan.operations.append({"type": "BARRIER"})
                    parallel_emitted = True
                else:
                    # PARALLEL_GROUP (conflict-free subset only)
                    plan.operations.append({
                        "type": "PARALLEL_GROUP",
                        "agents": [st.agent_type for st in safe_subtasks],
                        "tasks": [st.description for st in safe_subtasks],
                    })
                    parallel_emitted = True
            elif len(safe_subtasks) == 1:
                st = safe_subtasks[0]
                plan.operations.append({
                    "type": "SEQUENTIAL",
                    "agent": st.agent_type,
                    "task": st.description,
                })

            # Sequential section: conflicted tasks never race in parallel.
            if parallel_emitted and conflicted_subtasks:
                plan.operations.append({"type": "BARRIER"})
            for st in conflicted_subtasks:
                plan.operations.append({
                    "type": "SEQUENTIAL",
                    "agent": st.agent_type,
                    "task": st.description,
                })
        
        self.log_event("dispatch_plan_generated", plan.to_dict())
        return plan

    def _batch_fanout_plan(self, op: dict[str, Any]) -> "FanoutPlan":
        """Convert an emitted FANOUT operation into a validation plan (issue #265)."""
        agents = op.get("agents", [])
        tasks = op.get("tasks", [])
        return FanoutPlan(
            kind="fanout",
            tasks=tuple(
                FanoutTask(task_id=f"batch_{index}", target_agent=agent, prompt=task)
                for index, (agent, task) in enumerate(zip(agents, tasks), start=1)
            ),
            max_parallel=self.max_parallel,
        )

    def validate_syntax(self, plan: DispatchPlan) -> SyntaxReport:
        """Validate generated syntax against provider specification.

        Delegates the FANOUT batch checks (over-commitment, duplicate ids,
        graph sanity) to ``orchestration.validate_plan`` (issue #265 — no
        duplicated validation logic in the engine).
        """
        errors = []

        # Capability check (issue #265: capability lookup, no provider-name
        # branch — the mechanism itself is part of the error message).
        if not self._parallel_supported:
            has_parallel = any(op["type"] in ["FANOUT", "PARALLEL_GROUP"] for op in plan.operations)
            if has_parallel:
                errors.append(
                    f"Provider {self.provider} does not support parallel execution "
                    f"(fanout_mechanism={self._fanout_mechanism!r}) — sequential fallback used"
                )

        # FANOUT batch validation via the production plan validator.
        for op in plan.operations:
            if op["type"] == "FANOUT":
                errors.extend(
                    validate_plan(self._batch_fanout_plan(op), max_parallel=self.max_parallel)
                )

        valid = len(errors) == 0

        report = SyntaxReport(
            valid=valid,
            provider=self.provider,
            parallel_supported=self._parallel_supported,
            operation=plan.operations[0]["type"] if plan.operations else "NONE",
            agent_count=sum(len(op.get("agents", [])) for op in plan.operations if "agents" in op),
            errors=errors,
        )

        self.log_event("syntax_validated", {"valid": valid, "errors": errors})
        return report

    def run(self, user_input: str) -> DryRunReport:
        """Execute complete dry-run."""
        intent = self.classify_intent(user_input)
        
        if intent in ["UNKNOWN", "USER_OVERRIDE"]:
            self.log_event("dry_run_complete", {"result": intent})
            return DryRunReport(
                intent=intent,
                subtasks=[],
                plan=DispatchPlan(),
                syntax=SyntaxReport(
                    valid=True,
                    provider=self.provider,
                    parallel_supported=False,
                    operation=intent,
                    agent_count=0,
                ),
                provider=self.provider,
                events=self.events,
            )
        
        subtasks = self.decompose_task(user_input, intent)
        plan = self.generate_dispatch_plan(subtasks)
        syntax = self.validate_syntax(plan)
        
        self.log_event("dry_run_complete", {
            "intent": intent,
            "subtasks": len(subtasks),
            "parallel": syntax.parallel_supported,
        })
        
        return DryRunReport(
            intent=intent,
            subtasks=subtasks,
            plan=plan,
            syntax=syntax,
            provider=self.provider,
            events=self.events,
        )


if __name__ == "__main__":
    # Simple CLI for manual testing
    import sys
    
    provider = sys.argv[1] if len(sys.argv) > 1 else "Opencode"
    user_input = sys.argv[2] if len(sys.argv) > 2 else "Fix Bug A, B, C"
    
    engine = OrchestratorDryRun(provider=provider, config={"max-parallel-agents": 4})
    report = engine.run(user_input)
    
    print(report.to_markdown())
    print("\n" + "=" * 60)
    print("JSON Summary:")
    print(json.dumps(report.to_dict(), indent=2))
