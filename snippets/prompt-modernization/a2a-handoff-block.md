---
snippet: a2a-handoff-block
version: "1.0.0"
language: typescript
runtime: "agent-meta Modern Mode"
---

**A2A Handoff Contracts (TypeScript):**

```typescript
/** Compact payload for A2A-Handoffs (Feldnamen absichtlich kurz). */
interface IPayload {
  t: string;            // Task-Beschreibung, max. {{A2A_T_SIZE_LIMIT}} Zeichen
  ctx?: string | Record<string, unknown>;  // Kontext
  con?: string[];       // Constraints
  refs?: string[];      // Referenzen (Dateien, Schemas, URLs)
  pri?: 'low' | 'medium' | 'high' | 'critical';
  dep?: string[];       // Abhängigkeiten/Vorbedingungen
}

/** Envelope — Transport-Container für jede Delegation. */
interface IEnvelope {
  protocol_version: '1.0.0';
  handoff_id: string;        // HOFF-YYYYMMDD-NNN
  source_agent: string;
  target_agent: string;
  schema_ref: string;
  payload: IPayload | IPayload[];
  trace_parent?: string | null;
}

/** Standard-Rückgabe aller Worker-Agenten. */
interface IResult {
  status: 'done' | 'partial' | 'failed' | 'escalate';
  result: string;            // 1–2 Sätze
  artifacts?: string[];      // geänderte Dateien
  errors?: string[];
}

/** Erweitertes Rückgabeformat bei Eskalation. */
interface IEscalation extends IResult {
  status: 'escalate' | 'partial';
  escalate_reason: string;
  recommended_tier: 'junior-developer' | 'developer' | 'senior-developer' | string;
  partial_work: string;
  next_steps: string[];
}

/** Batch-Mode für FANOUT — mehrere Tasks an denselben Agententyp. */
interface IBatchPayload {
  batch: true;
  payload: Array<IPayload & { batch_task_id: string }>;
}
```

**Validierungs-Gates (vor Dispatch):**
- `source_agent != target_agent` — Self-Handoff verboten
- `payload.t` ≤ {{A2A_T_SIZE_LIMIT}} Zeichen
- `delegation_depth` ≤ {{A2A_MAX_DEPTH}}
- `payload.t` darf NICHT mit "Du bist..." beginnen

**Schema-Referenz:** `schemas/a2a-handoff.schema.json`, `schemas/handoffs/task-spec.schema.json`
