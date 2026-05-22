# STRATEGY: {{PROJECT_NAME}}

> Durable anchor for the Systems Engineering cascade.
> This document defines the system goal, constraints, and scope.
> It is created once at the start of an SE project and updated only when the
> fundamental direction changes.

---

## 1. System Goal

**Primary Objective:**
{{SYSTEM_GOAL}}

**Success Criteria:**
- {{SUCCESS_CRITERION_1}}
- {{SUCCESS_CRITERION_2}}
- {{SUCCESS_CRITERION_3}}

---

## 2. Constraints

### Hard Constraints (non-negotiable)
| ID | Constraint | Impact |
|----|-----------|--------|
| C-001 | {{HARD_CONSTRAINT_1}} | {{IMPACT_1}} |
| C-002 | {{HARD_CONSTRAINT_2}} | {{IMPACT_2}} |

### Soft Constraints (preferable, may be traded)
| ID | Constraint | Priority |
|----|-----------|----------|
| C-003 | {{SOFT_CONSTRAINT_1}} | {{PRIORITY_1}} |
| C-004 | {{SOFT_CONSTRAINT_2}} | {{PRIORITY_2}} |

---

## 3. Stakeholders

| Role | Interest | Influence |
|------|----------|-----------|
| {{STAKEHOLDER_1}} | {{INTEREST_1}} | {{INFLUENCE_1}} |
| {{STAKEHOLDER_2}} | {{INTEREST_2}} | {{INFLUENCE_2}} |
| {{STAKEHOLDER_3}} | {{INTEREST_3}} | {{INFLUENCE_3}} |

---

## 4. Scope

### In-Scope
- {{IN_SCOPE_1}}
- {{IN_SCOPE_2}}

### Out-of-Scope
- {{OUT_OF_SCOPE_1}}
- {{OUT_OF_SCOPE_2}}

### Boundaries
- {{BOUNDARY_1}}
- {{BOUNDARY_2}}

---

## 5. Assumptions

| ID | Assumption | Risk if false |
|----|-----------|---------------|
| A-001 | {{ASSUMPTION_1}} | {{RISK_IF_FALSE_1}} |
| A-002 | {{ASSUMPTION_2}} | {{RISK_IF_FALSE_2}} |

---

## 6. Risks

| ID | Risk | Probability | Impact | Mitigation |
|----|------|------------|--------|-----------|
| R-001 | {{RISK_1}} | {{PROB_1}} | {{IMPACT_RISK_1}} | {{MITIGATION_1}} |
| R-002 | {{RISK_2}} | {{PROB_2}} | {{IMPACT_RISK_2}} | {{MITIGATION_2}} |

---

## 7. SE Cascade Configuration

```yaml
se-cascade:
  max_depth: 5
  max_total_cells: 20
  max_critic_iterations: 3
  max_parallel_cells: 4
  cost_limit_eur: 5.00
```

---

## 8. Traceability

| SE Artifact | Location |
|-------------|----------|
| Requirements | `docs/se/requirements.md` |
| Architecture | `docs/se/architecture.md` |
| Interface Registry | `docs/se/interface-registry.md` |
| Traceability Matrix | `docs/se/traceability-matrix.md` |

---

*Last updated: {{DATE}}*
