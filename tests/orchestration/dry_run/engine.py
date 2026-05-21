# Orchestration Dry-Run Engine
# Simulates orchestrator decisions without real agent execution

"""
OrchestratorDryRun — Provider-agnostic orchestration simulation.

Usage:
    engine = OrchestratorDryRun(provider="Opencode", config={"max-parallel-agents": 4})
    report = engine.run("Fix Bug A, B, C")
    print(report.to_markdown())
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any
import json


@dataclass
class SubTask:
    """A decomposed sub-task."""
    name: str
    agent_type: str
    description: str
    dependencies: List[str] = field(default_factory=list)


@dataclass
class DispatchPlan:
    """Execution plan with FANOUT, PARALLEL_GROUP, or sequential steps."""
    operations: List[Dict[str, Any]] = field(default_factory=list)
    
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
    errors: List[str] = field(default_factory=list)


@dataclass
class DryRunEvent:
    """A single event in the dry-run timeline."""
    timestamp: str
    type: str
    data: Dict[str, Any]


@dataclass
class DryRunReport:
    """Complete dry-run report."""
    intent: str
    subtasks: List[SubTask]
    plan: DispatchPlan
    syntax: SyntaxReport
    provider: str
    events: List[DryRunEvent]
    
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

    # Known intents mapping
    INTENT_MAP = {
        "fix": "developer",
        "bug": "developer",
        "implement": "developer",
        "feature": "feature",
        "commit": "git",
        "push": "git",
        "branch": "git",
        "analyze": "ideation",
        "analyse": "ideation",
        "design": "ideation",
        "test": "tester",
        "release": "release",
        "document": "documenter",
        "doc": "documenter",
        "meta": "agent-meta-manager",
        "sync": "agent-meta-manager",
        "upgrade": "agent-meta-manager",
        "log": "log-analyzer",
        "feedback": "feedback",
        "issue": "feedback",
    }

    def __init__(self, provider: str, config: dict):
        self.provider = provider
        self.config = config
        self.max_parallel = config.get("max-parallel-agents", 4)
        self.events: List[DryRunEvent] = []
        self._parallel_supported = provider in ["Claude", "Opencode", "Gemini"]

    def log_event(self, event_type: str, data: dict):
        """Log an event for Viz-Log integration."""
        from datetime import datetime
        self.events.append(DryRunEvent(
            timestamp=datetime.now().isoformat(),
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
        ]
        for trigger in override_triggers:
            if trigger in user_lower:
                self.log_event("intent_classified", {"input": user_input, "intent": "USER_OVERRIDE"})
                return "USER_OVERRIDE"
        
        # Check for unknown (very vague input)
        if len(user_input.split()) <= 3 and any(word in user_lower for word in ["ding", "kram", "something", "etwas"]):
            self.log_event("intent_classified", {"input": user_input, "intent": "UNKNOWN"})
            return "UNKNOWN"
        
        # Map intent
        for keyword, agent in self.INTENT_MAP.items():
            if keyword in user_lower:
                self.log_event("intent_classified", {"input": user_input, "intent": agent})
                return agent
        
        self.log_event("intent_classified", {"input": user_input, "intent": "UNKNOWN"})
        return "UNKNOWN"

    def decompose_task(self, user_input: str, intent: str) -> List[SubTask]:
        """Decompose multi-tasks into sub-tasks."""
        # Simple heuristic: if commas or "and" present, might be multi-task
        import re
        
        # Extract items after commas or "and" for known parallel patterns
        if intent in ["developer", "tester", "documenter", "ideation"]:
            # Split by comma or "and" (English/German)
            parts = re.split(r',|und|und', user_input)
            parts = [p.strip() for p in parts if p.strip() and len(p.strip()) > 3]
            
            if len(parts) > 1:
                subtasks = []
                for i, part in enumerate(parts, 1):
                    subtasks.append(SubTask(
                        name=f"task_{i}",
                        agent_type=intent,
                        description=part,
                    ))
                self.log_event("task_decomposed", {"subtasks": len(subtasks), "decomposition": "FANOUT"})
                return subtasks
        
        # Single task
        self.log_event("task_decomposed", {"subtasks": 1, "decomposition": "DIRECT"})
        return [SubTask(name="task_1", agent_type=intent, description=user_input)]

    def generate_dispatch_plan(self, subtasks: List[SubTask]) -> DispatchPlan:
        """Generate dispatch plan based on sub-tasks and provider capabilities."""
        plan = DispatchPlan()
        
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
            # Check if all same agent type → FANOUT
            agent_types = {st.agent_type for st in subtasks}
            if len(agent_types) == 1:
                # FANOUT with batching if needed
                batches = []
                current_batch = []
                for st in subtasks:
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
            else:
                # PARALLEL_GROUP
                plan.operations.append({
                    "type": "PARALLEL_GROUP",
                    "agents": [st.agent_type for st in subtasks],
                    "tasks": [st.description for st in subtasks],
                })
        
        self.log_event("dispatch_plan_generated", plan.to_dict())
        return plan

    def validate_syntax(self, plan: DispatchPlan) -> SyntaxReport:
        """Validate generated syntax against provider specification."""
        errors = []
        
        # Check provider capability
        if not self._parallel_supported:
            has_parallel = any(op["type"] in ["FANOUT", "PARALLEL_GROUP"] for op in plan.operations)
            if has_parallel:
                errors.append(f"Provider {self.provider} does not support parallel execution — sequential fallback used")
        
        # Basic validation
        for op in plan.operations:
            if op["type"] == "FANOUT":
                if self.provider == "Claude":
                    if len(op.get("agents", [])) > self.max_parallel:
                        errors.append(f"FANOUT exceeds MAX_PARALLEL_AGENTS ({self.max_parallel})")
                elif self.provider == "Opencode":
                    if len(op.get("agents", [])) > self.max_parallel:
                        errors.append(f"FANOUT exceeds MAX_PARALLEL_AGENTS ({self.max_parallel})")
        
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
