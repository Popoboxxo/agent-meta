{{#if A2A_PROTOCOL_ENABLED}}
## A2A Handoff Protocol

**Wann Klartext, wann Envelope:** Normale Delegation (FANOUT/BARRIER/PIPELINE) läuft über das Kommunikationsformat aus Abschnitt 6/7 (`[task] → [agent] (reason)` + Context-Format-Block) — das ist der Normalfall, kein JSON nötig. Ein strukturiertes A2A-Envelope ist **nur** für Routen mit schema-gebundenem Contract Pflicht, d.h. wenn `role-defaults.yaml`'s `handoff.input_schema`/`output_schema` auf eine echte Schema-Datei zeigt (TaskSpec, die 4 Extensions, SE-Kaskade-Schemas). Ein bloßer `output_contract`-Name ohne Schema-Datei ist Dokumentation, kein Envelope-Zwang.

### Kern-Regeln (wenn Envelope Pflicht ist)

- `handoff_id`: `HOFF-YYYYMMDD-NNN` | `schema_ref`: aus Intent-Routing-Tabelle
- `payload.t` (Pflicht): max. **{{A2A_T_SIZE_LIMIT}} Zeichen** — EIN Satz. Überschreitung ist eine dokumentierte Konvention, kein Hard-Gate (Issue #346): Plattform-Limits greifen ohnehin, der Re-Delegation-Check deckt Spec-Dumps ab — siehe Rule `a2a-delegation-gates.md`
- TaskSpec-Felder (`t`, `ctx`, `con`, `pri`, `refs`, `dep`) sind immer kurz — kein Umschalten nötig

### Reference

Full A2A envelope schema: `schemas/a2a-handoff.schema.json`
Delegation syntax per provider: `config/delegation-syntax.yaml`
Pipeline definitions: `config/delegation-syntax.yaml` (pipelines section)

---
{{/if}}
