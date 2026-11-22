---
spec-id: SPEC-model-range-960
title: "model_range — Tier-Range-Routing nach Taskgröße (S/M/L/XL) — Spec (Issue #960, Phase H Task 16)"
status: APPROVED
date: 2026-11-22
approval: "Nutzergo 22.11 — Spezifikation auf Basis des freigegebenen Phasenplans 2026-11-11-phase-h-context-eval.md nachgetragen, keine neue Entscheidung"
issues: "#960"
plan: docs/superpowers/plans/2026-11-11-phase-h-context-eval.md
plan_task: 16
branch: chore/phase-h-bundle
ist_anchor: "87564958 (Re-Messung 2026-11-22; Plan maß bei origin/main 9aa0e0c0)"
klasse: "L — model_range quer durch Config, Schema, Orchestrator"
---

# model_range — Spec (Issue #960, Phase H Task 16)

> Status: APPROVED (Nutzergo 22.11 — Spezifikation auf Basis des freigegebenen Phasenplans 2026-11-11-phase-h-context-eval.md nachgetragen, keine neue Entscheidung)
> Datum: 2026-11-22 | Ist-Anker: Arbeitsstand `chore/phase-h-bundle @ 87564958` (Plan-Anker `origin/main 9aa0e0c0`, Review 2026-11-11) | Plan: `docs/superpowers/plans/2026-11-11-phase-h-context-eval.md` Task 16 (Z. 336-345), Plan-Review Z. 757
> Issue: #960 (Klasse L, Gate Task 16). Diese Spec wurde nachgetragen; die Implementierung entsteht erst in einem Folgeplan (Plan-Task-16-Ziel: "Folgeplan danach").

## Problem / Ziel / Nicht-Ziele

**Problem.** Die Taskgröße S/M/L/XL wird heute im Orchestrator (§4) auf *Developer-Rollen-Tiers* (`junior-developer`/`developer`/`senior-developer`/`principal-developer`) abgebildet, während `scripts/lib/roles.py` pro Rolle genau *einen* Modell-Tier über Presets und Overrides auflöst (`_TIER_SEQUENCE = nano < fast < balanced < powerful < max < ultra`). Es gibt kein `model_range`, das einer Taskgröße einen zulässigen **Modell-Tier-Bereich** (min/max) vorgibt. Issue #960 verlangt diesen Bereich quer durch Config, Schema und Orchestrator.

**Ziel.** Einen implementierbaren, provider-agnostischen Vertrag für ein optionales `model_range` festlegen:
- Abbildung S/M/L/XL → Tier-Klammer (min/max) im bestehenden Tier-Sequenzmodell;
- monotone Abbildung (S ≤ M ≤ L ≤ XL), `min <= max`, Schema-Validierung;
- Vorrang eines expliziten `tier_override` gegenüber einem aus der Klammer abgeleiteten Tier;
- Opt-in / Rückwärtskompatibilität: ohne `model_range` bleibt das Verhalten unverändert.

**Nicht-Ziele.**
- Keine Implementierung — dies ist der Spec-Gate; Code, Config, Hooks, Templates und andere Specs bleiben unberührt.
- Keine Festlegung konkreter Tier-Werte, Zahlenbereiche oder S→Tier-Zuordnungen (der Plan fixiert sie nicht; siehe Offene Fragen).
- Kein Eingriff in `scripts/lib/context.py` (Split #1086i, Phase C) und keine Änderung an Provider-Config-Dateien (`config/ai-providers.yaml`, `config/provider-capabilities.yaml`).
- Keine provider-spezifischen Namens-Branches (nur Config-Keys/Capability-Flags).
- Keine Closing-Keywords in Commit-/PR-Texten; #960 wird in Phase H nicht geschlossen.

## Interface Contracts (Datei:Symbol, Signatur, Fehlerpfade)

Alle Anker gegen den Arbeitsstand `chore/phase-h-bundle @ 87564958` neu gemessen (Plan maß bei `9aa0e0c0`). Python 3.9-kompatibel. **Hinweis:** Der Plan legt die konkreten Tier-Werte/Zahlen bewusst nicht fest; die Contracts beschreiben daher Form und Regeln (Shape), nicht finale Werte.

### IC-1 — `config/role-defaults.yaml`

- Ist: Rollen tragen ein einzelnes `model: <tier>` (z. B. `:415` `documenter: model: fast`, `:443` `security-auditor: model: powerful`). `routing.size_class` existiert an genau 4 Stellen und nur mit Werten S/M: `:424` (documenter, M), `:601` (M), `:646` (S), `:762` (S). Block `tier-override-policy` mit `security-critical-roles` bei `:2604-2613` (Kommentar ab :2604, Key `:2608`). **Kein `model_range`-Feld vorhanden.**
- Soll (Shape): optionales Feld `model_range` — eine Abbildung von Taskgröße (`S`|`M`|`L`|`XL`) auf eine Tier-Klammer `{min: <tier>, max: <tier>}`. Ablageort (pro Rolle vs. zentral) wird im Folgeplan aus den Issue-ACs entschieden — hier nicht erfunden.
- Fehlerpfade: `min`-Tier darf im `_TIER_SEQUENCE`-Rang nicht über `max` liegen (→ Schema/Validator-Fehler, siehe IC-2/IC-3).

### IC-2 — `config/project-config.schema.json`

- Ist: `tier-preset` (Enum + default `Normal`) `:540-551`; `tier-overrides` (role → tier/model-id) `:557-563`; `provider-tier-overrides` `:564-574`; `model-override-all` `:360`, `model-inherit-main-chat` `:368`, `model-overrides` `:376`; `size_class` als `{ "enum": ["S", "M", "L", "XL"] }` `:2621` (innerhalb `...roles.<role>`). **Keine `model_range`-Property vorhanden.**
- Soll (Shape): neue optionale Property `model_range`; `size_class`-Enum bleibt die kanonische Größenmenge `S|M|L|XL`; `min`/`max` sind Tier-Namen aus `_KNOWN_TIERS` (IC-3). Schema (oder schema-gestützter Validator) muss `rank(min) <= rank(max)` erzwingen und nicht-monotone S/M/L/XL-Klammern ablehnen. Das genaue JSON-Schema-Konstrukt (allOf/if-then vs. Python-Validator) wird im Folgeplan festgelegt.
- Fehlerpfade: ungültiger Größen-Schlüssel, ungültiger Tier-Name, `min > max`, nicht-monotone Abbildung → `python3 scripts/sync.py --validate` meldet Fehler.

### IC-3 — `scripts/lib/roles.py`

- Ist (Signaturen, unverändert zitiert):
  - `_KNOWN_TIERS = {"nano","fast","balanced","powerful","max","ultra"}` `:28`; `_TIER_SEQUENCE = ["nano","fast","balanced","powerful","max","ultra"]` `:29`.
  - `load_tier_presets(agent_meta_root: Path) -> dict` `:35`; `_upgrade_tier(tier: str, steps: int) -> str` `:44`; `load_roles_config(agent_meta_root: Path) -> dict` `:53`.
  - `_resolve_tier_to_model(tier_or_alias: str, provider: str, provider_config: dict) -> str` `:293`; `apply_model_format(model: str, provider_config: dict | None, provider: str) -> str` `:328`; `resolve_model(...)` `:351`.
  - `_resolve_model_raw(role: str, project_config: dict, agent_meta_root: Path, provider: str = "Claude", provider_config: dict | None = None, log: Optional[SyncLog] = None) -> str` `:381`; Auflösungsreihenfolge dokumentiert `:391-404`; `tier-overrides` gelesen `:463-468`; Preset-Auflösung `:491-525`; `provider-tier-overrides` `:527-533`.
  - **Keine `model_range`-Referenz vorhanden.**
- Soll (Vertrag, keine neue Signatur erfunden): Die bestehende Tier-Auflösung konsultiert `model_range` nur, wenn kein expliziter Override greift. Rangvergleich erfolgt über `list(_TIER_SEQUENCE).index(tier)`. Reihenfolge der Vorränge bleibt erhalten: `model-override-all` / `model-inherit-main-chat` (`, :414-435`) > `model-overrides` (`:437-453`) > `tier-overrides` (`:463-468`) > `model_range`-Klammer > Rollen-Default (`:455-460`) > Preset/SE-Focus (`:479-525`).
- Fehlerpfade: Tier außerhalb `_KNOWN_TIERS` → wie heute `""`/Pass-through gemäß `_resolve_tier_to_model`; `min > max` → Fehler (IC-2).

### IC-4 — `agents/1-generic/orchestrator.md` §4

- Ist: `## 4. Developer tier selection` `:134`. Task-size-Tabelle (issue #370) `:167-174`: S/M/L/XL → *Developer-Rolle*; Per-task tier override (A2A) `:182-185`: `payload.tier_override: <tier>` mit Guardrails (Preset-Existenz, kein Downgrade sicherheitskritischer Rollen, Audit-Log-Pflicht); Modell-Tier-Linie `:340`: `nano | fast | balanced | powerful | max`. **Kein `model_range`-Text vorhanden.**
- Soll (Shape): §4 beschreibt die `model_range`-Klammer als Ergänzung zur bestehenden Größen-Tabelle; ein gesetzter `payload.tier_override` übersteuert die Klammer (Vorrang wie heute bei `:182-185`). Konkrete S→Tier-Werte werden nicht hier fixiert.
- Fehlerpfade: Tier nicht im aktiven Preset vorhanden → Override verwerfen, Fallback auf Rollen-Default (bestehendes Verhalten `:183`).

### IC-5 — `scripts/lib/sync_pipeline.py`

- Ist: Tier-Bundle-Injektion vor dem Rendern `:1507-1512` (`provider_variables.update(runtime_gate_vars(pc, caps, config))`); Routing-Detail-Datei `:1542-1558` (`render_routing_detail(routing_rules, root=agent_meta_root)`, Kommentar nennt `size_class` `:1544`, registriert in `generated-file-hashes.json` `:1546`); `provider_runtime_gate_tier(pc, caps)` `:1682`. **Keine `model_range`-Referenz vorhanden.**
- Soll (Vertrag): Falls `model_range` in das Routing-Modell aufgenommen wird, fließt es über dieselben bestehenden Pfade (`_ROUTING_MODEL_RULES` → `render_routing_detail`, bzw. `provider_variables`) in Render/Detail-Datei; keine neue Persistenz, kein neuer Schreibpfad. Bei Output-Änderung: Hash-Re-Pin in `generated-file-hashes.json` mit dokumentiertem Grund (Folgeplan).
- Fehlerpfade: keine neuen; bestehende `--check`-Drift-Erkennung bleibt maßgeblich.

### IC-6 — `config/tier-presets.yaml`

- Ist: Presets `Cheap` `:1`, `Normal` `:32`, `Advanced` `:89`, `Expensive` `:119`, `Expensive as Hell` `:149`. Tier-Schlüssel durchgehend `nano, fast, balanced, powerful, max`; `ultra` nur im Preset `Normal` (Claude `:51`, Gemini `:59`, Opencode `:67`). **Kein `model_range`-Feld vorhanden.**
- Soll (Shape): Tier-Klammern referenzieren ausschließlich Tier-Namen, die im aktiven Preset existieren; `ultra` ist nicht in allen Presets vorhanden → Bracketing darf sich nicht auf einen tier-weit-abwesenden Schlüssel verlassen (Auflösung im Folgeplan).
- Fehlerpfade: Klammer mit einem im aktiven Preset fehlenden Tier → resolven gemäß bestehender Preset-Logik (IC-3, `:504-525`), kein harter Abbruch.

## Datenfluss

1. **Input:** Taskgröße `s ∈ {S,M,L,XL}` (Orchestrator §0/§4 Klassifikation), aktive Projekt-Config (`model_range`, `tier-preset`, `tier-overrides`, `model-override-all`, `model-inherit-main-chat`, `provider-tier-overrides`), `config/role-defaults.yaml` (Rollen-`model`, `routing.size_class`), `config/tier-presets.yaml` (Tier-Leiter je Preset/Provider), `config/ai-providers.yaml` (`model-tiers`).
2. **Transformation (Reihenfolge verbindlich):**
   a. Schema-Validierung von `model_range` (gültige Größe, gültige Tiers, `rank(min) <= rank(max)`, Monotonie S≤M≤L≤XL) — IC-2, IC-3.
   b. Explizite Overrides prüfen (`tier_override` zur Laufzeit, `tier-overrides`/`model-override-all` zur Sync-Zeit); wenn gesetzt, gewinnt der Override und `model_range` wird nicht angewendet — IC-3, IC-4.
   c. Ohne Override: Klammer für `s` auswählen, Tier innerhalb `[min, max]` bestimmen (konkrete Auswahlregel → Folgeplan) — IC-1, IC-4, IC-6.
   d. Tier → Modell-ID über die bestehende `roles.py`-Kette (`_resolve_tier_to_model` → Preset/`model-tiers` → `apply_model_format`) — IC-3.
3. **Output:** aufgelöster Modell-Tier je Dispatch; gerenderte Agenten-/Routing-Detail-Dateien; Validierungsfehler bei ungültiger Klammer.
4. **Persistenz:** ausschließlich bestehende Sync-Artefakte (`generated-file-hashes.json`, Routing-Detail-Datei); kein neuer Store, keine neue Datei durch diese Spec.

## Acceptance Criteria (nummeriert, testbar, Given/When/Then)

Die ACs stammen aus Plan-Task-16-Step-2 (Mapping, Klammerung, `tier_override`-Interaktion, Schema `min <= max`, Opt-in-Rückwärtskompatibilität).Der Issue-Text war im Checkout **nicht** verfügbar (siehe Offene Fragen); der exakte AC-Wortlaut und konkrete Werte sind im Folgeplan aus #960 nachzuziehen. Jede AC nennt ihre IC-Zuordnung.

1. **Opt-in / Rückwärtskompatibilität** (→ IC-1..IC-6). Given ein Projekt ohne jeden `model_range`-Schlüssel (Stand `87564958`), When `python3 scripts/sync.py --validate` läuft und ein Sync-Render erfolgt, Then bleibt das Ergebnis byte-identisch zum aktuellen Stand und es treten keine neuen Validierungsfehler auf.
2. **Schema `min <= max`** (→ IC-2, IC-3). Given eine `model_range`-Klammer, bei der für eine Größe der `min`-Tier im `_TIER_SEQUENCE`-Rang über dem `max`-Tier liegt, When die Validierung läuft, Then wird sie mit einem die Größe benennenden Fehler abgelehnt; bei `min == max` wird sie akzeptiert.
3. **Monotone Abbildung** (→ IC-1, IC-2, IC-3). Given die konfigurierten Klammern für S, M, L, XL, When ihre Tier-Ränge verglichen werden, Then gilt `rank(min_S) ≤ rank(min_M) ≤ rank(min_L) ≤ rank(min_XL)` und `rank(max_S) ≤ rank(max_M) ≤ rank(max_L) ≤ rank(max_XL)`. Konkrete Tier-Werte sind hier bewusst nicht festgelegt.
4. **`tier_override`-Vorrang** (→ IC-3, IC-4). Given für eine Rolle ist `payload.tier_override` oder `tier-overrides`/`model-override-all` gesetzt, When die Modellauflösung erfolgt, Then gewinnt der explizite Override gegenüber einem aus `model_range` abgeleiteten Tier; die bestehende Reihenfolge (`:391-404`) bleibt erhalten.
5. **Klammerung** (→ IC-1, IC-4, IC-6). Given eine als `s` klassifizierte Taskgröße und ein aktives `model_range`, When Orchestrator §4 bzw. die Modellauflösung den Tier wählt, Then liegt der gewählte Tier innerhalb der für `s` konfigurierten Klammer (inklusive `min` und `max`) und existiert im aktiven Preset.
6. **Integration / Artefakt-Druck** (→ IC-5, IC-2). Given die Implementierung ist im Folgeplan umgesetzt, When `python3 scripts/sync.py --validate` und die betroffenen Tests laufen, Then gibt es keine neuen Fehler; eine Änderung am gerenderten Output ist ausschließlich mit dokumentiertem Grund in `generated-file-hashes.json` neu gepinnt.

## Offene Fragen + Risiken

- **OQ-1 (nicht entschieden, nicht erfunden):** exakte Abbildung S/M/L/XL → Tier-Stufe. Der Plan fixiert sie nicht; sie ist im Folgeplan aus den Issue-ACs zu bestimmen.
- **OQ-2 (nicht entschieden, nicht erfunden):** konkrete numerische Bereiche / Tier-Tokens für `min` und `max` je Größe. Bewusst offengelassen.
- **OQ-3 (nicht entschieden, nicht erfunden):** Ablageort von `model_range` (pro Rolle in `role-defaults.yaml`, zentral in `project-config.schema.json` oder beides) und das genaue Schema-Konstrukt für `min <= max` (JSON-Schema `if/then` vs. Python-Validator in `config.py`).
- **OQ-4 (nicht entschieden, nicht erfunden):** Bracketing-Verhalten, wenn ein Klammer-Tier im aktiven Preset fehlt (insbesondere `ultra`, nur in `Normal` vorhanden). Auflösung im Folgeplan.
- **OQ-5 (Quellenlücke):** die Issue-Datei #960 lag im Checkout nicht vor (`.tmp/issues/960.md` und `.tmp/issue-dump/issue-960.json` nicht vorhanden; Suche nach `#960` in `.tmp/` ohne Treffer). Die ACs oben sind aus Plan-Task-16-Step-2 abgeleitet; der Issue-AC-Wortlaut ist im Folgeplan aus dem Issue nachzuziehen.
- **Risiko:** Änderungen an `orchestrator.md` §4 und am Routing-Detail können ac01-/Budget-Hashes verschieben → Re-Pin nur mit dokumentiertem Grund (Folgeplan).
- **ADR-Hinweis:** diese Spec trifft keine neue Entscheidung (Nutzergo 22.11: nachgetragen auf Basis des freigegebenen Plans). Design-Entscheidungen zu OQ-1..OQ-4 gehören in den Folgeplan und sind dort als ADR (Kontext/Entscheidung/Konsequenzen) festzuhalten.

### Abdeckungs-Checkliste

- [x] Pflichtabschnitte vorhanden (Problem/Ziel/Nicht-Ziele, Interface Contracts, Datenfluss, ACs, Offene Fragen, Trace-Anker)
- [x] Sechs benannte Dateien mit neu gemessenen Ankern belegt
- [x] Bestätigung: `model_range` in Code/Config/Agents/Schema nicht vorhanden (nur Plan-Docs)
- [x] Keine Signatur erfunden; neue Felder als Shape/Regel beschrieben
- [x] Jede AC testbar und mindestens einem IC zugeordnet
- [x] Keine konkreten Tier-Werte/Zahlen erfunden (als offen markiert)
- [x] Approval-Marker und frontmatter `status: APPROVED` gesetzt

## Trace-Anker: spec-id: SPEC-model-range-960
