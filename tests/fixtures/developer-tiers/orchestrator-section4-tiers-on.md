## 4. Developer tier selection
| Tier | When |
|------|------|
| `junior-developer` | Solution obvious, ≤2 files |
| `developer` | Standard, clear scope, ≤3 files |
| `senior-developer` | Architecture impact, risk |
| `principal-developer` | Last resort: `senior-developer` has failed 2+ times on the same task and returns `STATUS: escalate` with `RECOMMENDED_TIER: principal-developer` — requires explicit escalation gate (reason + metric per ESCALATE-Card intake, typically `repeated_failure` / `attempts: 2`, plus task summary + failure log), `orchestrator_only`, never called directly by other agents |

**Routing policy (Issue #346):**
1. Unambiguous keyword signals route directly via the `route_intent` routing rules or the derived routing rules (`routing.rules` in the generated tool definition) — no estimator call, no duplicated keyword data here.
2. `effort-estimator` ONLY as tie-breaker when two tiers/roles match equally — never as default routing (latency/cost overhead without value).
3. In doubt → higher tier (below `principal-developer`). Max 1 escalation per task, except the explicit `senior-developer` → `principal-developer` last-resort gate.

**Task-size routing (issue #370):** Für Implementierungs-Tasks — Concept-Agent vorschalten, Developer-Tier nach Größe wählen. Signal-Keywords → Pipeline `concept-driven-dev` (§2). Concept-Agents vorschalten, NICHT selbst analysieren (Router, nicht Worker):

| Task size | Concept agents | Developer tier |
|:---------:|----------------|:--------------:|
| S (≤2 files) | *(skipped — solution obvious)* | `junior-developer` |
| M (3–8 files) | `concept-specifier` (+ review loop) | `developer` |
| L (9–20 files) | `concept-specifier` + `concept-reviewer` | `senior-developer` |
| XL (>20 files) | `concept-architect` + `concept-reviewer` | `principal-developer` |

S: Pipeline überspringen, direkt delegieren. M–XL: erst `concept-driven-dev` (explore → specify → review), dann Implementierung gegen die freigegebene Spec. XL-Implementierung → `principal-developer` NUR mit freigegebener Concept-Basis (Approved Spec/Design); ohne Concept-Basis gilt unverändert der Last-Resort-Eskalations-Gate (reason + metric gemäß ESCALATE-Card intake, plus task summary + failure log, `senior-developer` failed 2+).

**Per-task tier override (A2A, optional):** `payload.tier_override: <tier>` übersteuert die Rolle→Tier-Auflösung nur für genau diesen Dispatch. Guardrails (Rule `a2a-delegation-gates.md`):
- Tier muss im aktiven tier-preset existieren (config/tier-presets.yaml) — sonst Override verwerfen, Fallback auf Rollen-Default.
- Kein Downgrade sicherheitskritischer Rollen (role-defaults.yaml → `tier-override-policy.security-critical-roles`).
- **Audit-Log-Pflicht:** jeden Override-Versuch im Tracker/Checkpoint vermerken: `tier_override=<tier> (applied|rejected: <reason>)`.

**ESCALATE-Card intake (Pflichtfelder):** Gilt für jede ESCALATE-Card, inkl. `senior-developer` → `principal-developer`. Card-Feld `ESCALATE_REASON`/`reason` bzw. `ESCALATE_METRIC`/`metric`. Eine ESCALATE-Card ohne beide Pflichtfelder ist ungültig — kein Tier-Wechsel, strukturierte Nachreichung anfordern:
- `reason` — kategorial: `blast_radius_growth` | `scope_violation` | `repeated_failure` | `security_risk` | `blocked_dependency`
- `metric` — quantifizierbar: z.B. `affected_files > 5` | `subsystems: 3` | `attempts: 2` | `timeout_sec > 600`

**In-role escalation:** Eskalation muss kein Rollenwechsel sein — bei belegtem Blast-Radius-Wachstum (gültige `reason` + `metric`) bleibt die Rolle, der Dispatch steigt per `tier_override` auf `max`. Gültige ESCALATE-Card → straight to `recommended_tier`.

