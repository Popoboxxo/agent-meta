{{#if A2A_PROTOCOL_ENABLED}}
## A2A Handoff Protocol

**Jede Delegation MUSS als strukturiertes A2A-Envelope erfolgen.**

### Kern-Regeln

- `handoff_id`: `HOFF-YYYYMMDD-NNN` | `schema_ref`: aus Intent-Routing-Tabelle
- `payload.t` (Pflicht): max. **{{A2A_T_SIZE_LIMIT}} Zeichen** — EIN Satz. Überschreitung → kein Dispatch
- Compact Mode (`t`, `ctx`, `con`, `pri`, `refs`, `dep`) reduziert Token-Overhead bei FANOUT

### Reference

Full A2A envelope schema: `schemas/a2a-handoff.schema.json`
Delegation syntax per provider: `config/delegation-syntax.yaml`
Pipeline definitions: `config/delegation-syntax.yaml` (pipelines section)

---
{{/if}}
