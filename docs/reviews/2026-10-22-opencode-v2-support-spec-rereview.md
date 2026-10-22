# Re-Review: SPEC-OPENCODE-V2-SUPPORT-2026-10-22 (Rev. 1.1) und Plan

- **Gegenstand:** `docs/specs/2026-10-22-opencode-v2-support-spec.md` (Rev. 1.1, 523 Zeilen), `docs/plans/2026-10-22-opencode-v2-support-plan.md` (560 Zeilen), beide vollständig gelesen
- **Referenz:** Erst-Review `docs/reviews/2026-10-22-opencode-v2-support-spec-review.md`; Spec A `docs/specs/2026-10-22-opencode-entrypoint-1006-spec.md` (IC-3..IC-7, Nicht-Ziele); Plan A (nur Dateiüberlappung geprüft)
- **Reviewer:** concept-reviewer (Spec-Review-Modus, fokussiert), 2026-10-22
- **Verdikt:** **CHANGES_REQUESTED** — 0 BLOCKER, 3 MAJOR, 11 MINOR, 4 INFO

## 1. Status der Erst-Review-Findings (Spec)

| Finding | Status | Beleg / Rest |
|---|---|---|
| B-1 Gate-Plugin schwächt Gate / v1-Freeze | **behoben** | `surface-has-plugins`/`surface-plugin-protocols` (3.1), statisches `has_plugins: false` (B-D7), `SUPPORTED_PLUGIN_PROTOCOLS` als Vertrag (3.6), Deny bleibt bei `observe` (3.4, AC-C14), AC-C12 um v1-Fall ergänzt. Rest: Rückbau bei `enforce` (N-M1) |
| B-2 v2-Zweig umgeht Spec A | **behoben** | 3.4 normativ: nur Schritt 4 ersetzt, Schritte 1-3 und 5 laufen; `deny_edit`/`edit_allow_paths` in 3.7; AC-C15, AC-C16 |
| M-1 Entscheidung 6 per Default | **behoben** | Abweichung A-6 im Register, OQ-B1 als Freigabe-Gate ohne Default, Alias-Alternative; Plan E3. Nutzerbestätigung steht weiter aus (kein Spec-Mangel) |
| M-2 Phase-B-Keys unbelegt | **behoben** | Q6, C0 vor B, Amendment zu IC-15 Nr. 16 mit Ersatzstrategie, OQ-B11; Plan Task 11 trägt Amendment-Verweis |
| M-3 MCP kein Managed-Merge | **behoben** | Managed-Pfade je Server, State `opencode-v2-mcp`, Rückbau vor frühem Return, `disabled`-Quelle definiert, AC-C17. Rest: m-7, m-10 |
| M-4 Exit-Gate / Phasen | **behoben** | C0 parallel zu A, zwei Verdict-Zeilen, fail-safe, Messbudget statt Zeitbox |
| M-5 Open-world-Permissions | **behoben** | Closed-world-Builder (3.7, B-D8), AC-D1 |
| M-6 Tier-gekoppelter Aufruf | **behoben, neue Lücke** | Tier-unabhängiger Aufruf (3.2, AC-B18). Neue Lücke: Provider-Bindung der Writer (N-M2) |
| M-7 State-Namespace | **behoben** | Vier dict-Namespaces, `_read_state`-Erweiterung, Regel 9, AC-B16 |
| m-1..m-8 | behoben | Entscheidungstabelle (Zeilen 1-4a), Namen/Pfade korrigiert, AC-Zählung 53 stimmt, Baseline AC-T4, Secret-Zusatzregel, Duplikat-Check provider-agnostisch |

Formale Checks: Pflichtsektionen, Trace-Anker, `requires-spec`, `Status: Entwurf` (konsistent, Mid-Line-Erwähnungen matchen `_APPROVED_RE` nicht), keine Treffer für `_PLACEHOLDER_PATTERNS` (`spec_plan.py:88-97`). Plan: `**Spec-ID:**` gesetzt, `Status: Entwurf`, Entry-Gates E1-E4.

## 2. Findings

### MAJOR

**N-M1 (Logik/Konsistenz mit Spec A; Spec 3.4 + Plan Tasks 13, 18): Permissions-Rückbau bei Tier- und Surface-Wechsel ist ungeregelt**
- (a) Tier-Wechsel: Spec 3.4 (:220) verweist für Rückbau bei Tier-Wechsel auf „die Lösung aus Spec A“. Spec A schließt genau das aus (Nicht-Ziel „Keine Rollback-Garantie bei Tier-Wechsel“, OQ-4; IC-7 behält die Bedingung `== "permission"`). AC-C14, zweite Hälfte („Tier `plugin` + `enforce` → Tripel entfernt“), ist so nicht erfüllbar: Plan Task 18 ersetzt die Aufrufbedingung durch `permission_deny_required(...)`. Bei `enforce` ist die Bedingung `False`, `_sync_opencode_runtime_gate` läuft nicht, und niemand entfernt die Tripel. `test_ac_c14_enforce_plugin_removes_triples` bleibt rot.
- (b) v2→v1: Spec 3.4 Rollback nennt „v2 inaktiv“, AC-B7 verlangt einen leeren Namespace `opencode-v2-permissions`. Plan Task 13 verzweigt nur bei `v2_active`, und v1 „schreibt nie `permissions`“. Kein Task baut die v2-Tripel auf v1 zurück. Die Trace-Zeile AC-B7 verweist nur auf Task 9 und 16, nicht auf 13.
- (c) v1→v2: Der v2-Zweig ersetzt Schritt 4 und damit auch den Rückbau der v1-Map (State `runtime-gate-deny`, `isolation.py:467-479`). Die `permission.edit/bash["**"]`-Map bleibt nach der Migration stehen. Das widerspricht AC-C3 („kein `permission.edit/bash` aus dem Gate“) genau im typischen Fall, einem bestehenden v1-strict-Projekt wie diesem Repo.
- Korrektur: Spec 3.4 Schritt 4 surface-übergreifend formulieren. Auf jeder Surface wird zuerst der State des jeweils anderen Formats zurückgebaut, dann das eigene Format geschrieben. Den Permission-Rückbau tier-unabhängig aufrufen (analog M-6) oder die `enforce`-Hälfte von AC-C14 streichen, bis `_baked_plugin_mode` `enforce` liefern kann. Den Verweis „Lösung aus Spec A“ ersetzen. ACs ergänzen: „v1-strict → v2: `permission`-Map-Deny entfernt, `runtime-gate-deny` leer“ und „v2 → v1: Namespace `opencode-v2-permissions` leer“. Plan: Rückbau in Task 13 (bzw. 18) aufnehmen und die Trace-Tabelle für AC-B7 um Task 13 ergänzen.

**N-M2 (Logik/Querwirkung; Spec 3.2, 3.5, 3.8 + Plan Tasks 10, 16, 23): Writer sind nicht an den eigenen Provider gebunden, Rückbau läuft bei anderen Providern**
- Spec 3.2: Aufruf „je aktivem Provider“, No-op nur „ohne `v2_active` UND ohne State“. Die State-Datei ist fest `.opencode/agent-meta-state.json` (`isolation.py:34` `_OPENCODE_STATE_FILE`). In der Claude- oder Gemini-Iteration ist der State also vorhanden, `v2_active(…, "Claude")` ist `False`, damit gilt `T = None`, und Zeile 4 baut die Opencode-Managed-Keys zurück. Die Opencode-Iteration schreibt sie danach neu. Das Ergebnis hängt von der Reihenfolge ab. AC-B8 (Idempotenz) und AC-D5 (andere Provider unverändert) sind gefährdet.
- Plan Task 16: `rollback_opencode_mcp(project_root, log, dry_run)` hat keine Provider- oder Datei-Bindung und wird bei `fmt != "opencode-json-v2"` aufgerufen, also für jeden Nicht-v2-Provider. Plan Task 9 liest fest `opencode.json` statt der aufgelösten `settings_file`.
- Korrektur: In der Spec ein provider-agnostisches Zuständigkeitskriterium festlegen. Beispiel: Der Writer handelt nur für Provider, deren aufgelöste `settings_file`/`mcp-config.committed_file` die verwaltete Datei ist und deren `mcp-config.format` zur Familie `opencode-json*` gehört. Der State-Pfad wird aus Daten abgeleitet, nicht hart verdrahtet. Rückbau nur durch den Provider, dem Datei und State gehören. Signaturen in Task 9/16/23 um die aufgelösten Pfade erweitern. Neues AC: „Projekt mit Opencode v2 + Claude, zweimal synchronisiert → `opencode.json` byte-identisch, keine Rückbau-Aktion aus der Claude-Iteration“.

**N-M3 (Testbarkeit; Plan Task 19): AC-C2 (NO-GO-Fallback) wird nie verifiziert**
- AC-C2 beschreibt den NO-GO-Fall. Der einzige Test (`test_ac_c2_no_go_fallback_documented_in_spike`) liegt in Task 19. Bei NO-GO entfällt Phase C3 komplett, bei GO wird der Test übersprungen. AC-C2 ist damit in keinem Pfad abgedeckt.
- Korrektur: Den AC-C2-Test in Task 3 oder einem eigenen C0-Task verankern, der in beiden Fällen läuft. Bei NO-GO prüft er: v2-Tier `permission`, keine Plugin-Datei, `has_plugins: false`, `runtime_gate: permission` unverändert. Die Trace-Tabelle entsprechend anpassen.

### MINOR

- **m-1 (Plan Task 2 Step 3, Autorenhinweis):** Der erwartete Ausgang ist widersprüchlich: „Exit 0, `5 passed` und `1 skipped`-frei“ und gleichzeitig „darf fehlschlagen“. Fix: Bei `CONFIRMED`+`GO` gilt `6 passed`, Exit 0. Bei `AMEND`/`NO-GO` gilt `5 passed, 1 failed` (`test_verdict_consequences_recorded`), Exit 1 ist erwartet, Task 3 macht den Test grün. Alternative: diesen Test erst in Task 3 anlegen.
- **m-2 (Plan Task 28 Steps 1-2, Autorenhinweis):** Die Rot-Phase ist unklar formuliert („Assert um die Prüfungen erweitern, bevor Task-Inhalt vorhanden wäre ist hier nicht möglich“, „`fail "not implemented"`-freiem Mindestinhalt“). Fix: Task 28 wie Task 29 als Absicherungstest mit Negativprobe deklarieren (z. B. Assert gegen eine v1-Config laufen lassen → Exit ≠ 0) und in die Self-Review-Ausnahmen aufnehmen. Den v2→v1-Rückwechsel im Assert-Skript nur einbauen, wenn `run.sh` einen zweiten Sync unterstützt (U-8), sonst als Python-Test in Task 29.
- **m-3 (Plan Task 1):** `test_each_answer_has_marker_and_source` verlangt je Q-Abschnitt „genau einen“ Marker. Spec Q5/Q6 verlangen aber Marker je Feld bzw. Key. Fix: „mindestens einen“ oder eine Prüfung je Key.
- **m-4 (Plan Task 24 / Parallelität):** Die `Files:`-Liste ist unvollständig: Step 2 ergänzt `tests/test_opencode_v2_surface.py`. Gruppe `c0-g1` (PR C0) widerspricht der Merge-Reihenfolge „PR D (20–33)“. Die Aussage „C0 berührt nur `docs/spikes/…` und die Spec“ ist falsch (Task 1 legt einen Test an, Task 3 ändert den Plan). Die Disjunktheit zu Task 2 bleibt gegeben. Plan A ändert `tests/test_opencode_v2_surface.py` nicht (geprüft). `b-g1` (Tasks 4/5/6) ist disjunkt.
- **m-5 (Plan, Rot-Zahlen):** Task 4 erwartet `7 failed`. Die Ablehnungstests (unbekannter Key, `deepseek`, `depth 0`) sind wegen `additionalProperties: false` schon vor der Änderung grün, realistisch sind ca. 2 failed / 5 passed. Task 13: `test_ac_c15`/`test_ac_c16a` prüfen Spec-A-Verhalten und sind vermutlich bereits grün. Fix: Zahlen korrigieren oder die Tests als Regressionstests kennzeichnen.
- **m-6 (Spec 3.4, Konsistenz mit Spec A IC-4):** Zeile :200 sagt „`_opencode_runtime_gate_entries` unverändert (Spec A IC-4)“, Zeile :216 sagt, der Tier-Check werde um den Modus ergänzt. Das ändert den Spec-A-Vertrag („bleibt UNVERÄNDERT“) und die Semantik von `opencode_runtime_gate_wanted` („tier-`permission` gate“). Fix: Die Modus-Logik nur an der Aufrufstelle (`permission_deny_required`) halten oder die Änderung explizit als Amendment zu Spec A IC-4 führen.
- **m-7 (Spec 3.5 / Plan Task 14):** Quelle für `disabled`/`timeout`/`oauth` ist laut Spec `config/plugin-catalog.yaml`. Die einzige Schemadatei ist `config/project-config.schema.json`, und deren `connection`-Objekte (:1153, :1253) betreffen Projekt-Plugins. Plan Task 14 erweitert nur dieses Schema und lässt den Katalog bewusst unverändert, Katalogwerte bleiben damit unvalidiert. Fix: In der Spec festlegen, welche Quellen gelesen werden (Katalog und/oder Projekt-Connection), und benennen, wie der Katalog validiert wird.
- **m-8 (Spec 3.3 vs. Plan Task 9):** Die Spec verlangt „denselben Prüfer wie `_write_json_config` (`allow_secrets`, `verify_gitignored`)“ plus eine strukturelle Prüfung. Der Plan nutzt nur `find_plaintext_secrets`. Fix: Plan ergänzen oder Spec auf die strukturelle Prüfung reduzieren.
- **m-9 (Gate-Formulierung `VERDICT-FIELDS`):** Plan-Phasentabelle „B: `VERDICT-FIELDS: CONFIRMED`“ und Spec 3.3 („erst starten, wenn Q6 je Key VERIFIED/DOKU liefert“) widersprechen Spec 3.6 („AMEND = Amendment B1 vor B“). Fix: B startet bei `CONFIRMED` oder nach eingearbeitetem Amendment B1. Ein `AMEND`, das nur aus Q5 (MCP) kommt, sollte B nicht blockieren, daher die Folgen getrennt ausweisen.
- **m-10 (Spec Risiken/Nicht-Ziele):** Plan U-6 (lokale `.opencode/mcp.local.json` behält die Ersetzungs-Semantik) und U-7 (v1-MCP-Writer verliert User-Einträge bei aktiven Servern) sind echte Grenzen von Entscheidung 7, stehen aber nur im Plan. Fix: In der Spec als bekannte Grenze aufnehmen.
- **m-11 (Spec Datenfluss :349):** `_apply_surface_aux_selection` listet `has_plugins` nicht, obwohl 3.1 es auflöst.

### INFO

- **i-1:** Spec-A-Symbole (`_opencode_entry_point`, `opencode_runtime_gate_wanted`, `opencode_primary_edit_allow`, `_STATE_DEFAULT_AGENT_KEY`, `deny_edit`) sind korrekt als von Plan A erzeugt ausgewiesen (A-1, E1, Grep-Schritte in Tasks 5, 13, 22). Die Bestandssymbole (`isolation.py:34`, `sync_pipeline.py:1303-1312`, `providers.py:642/653/656`, Schema :1153/:1253) existieren wie referenziert.
- **i-2:** AC-Abdeckung: Alle 53 ACs stehen in der Trace-Tabelle. Echte Lücken nur bei N-M1(b) und N-M3. TDD-Reihenfolge (rot → grün) ist pro Code-Task vorhanden, Ausnahmen sind benannt (außer Task 28, m-2).
- **i-3:** Phasen-/Gate-Logik ist schlüssig: C0 zuerst, B/C/D hängen an Task 3, C3 nur bei GO (Tasks 18/19 mit GO-Bedingung), D hängt nicht an C3 (Task 20 → 17). v1-Freeze und andere Provider sind über AC-C6/C11/D4/D5/D6/T4 abgesichert; offen bleibt die Laufzeit-Querwirkung aus N-M2.
- **i-4:** Plan-State-Kodierung `prior_absent: bool` weicht von Spec A (`prior: None` = fehlte) ab. Das ist vertretbar, weil `null` ein legitimer Wert ist. In Spec 3.2 sollte die Kodierung trotzdem festgeschrieben werden, damit beide Specs eine Form nennen.

## 3. Verdikt

**CHANGES_REQUESTED.** Alle Blocker und Majors des Erst-Reviews sind in der Sache behoben, ohne die Entscheidungen 6-12 neu zu verhandeln. Neu blockierend sind drei Punkte:
- **N-M1:** Rückbau zwischen v1-Map und v2-Liste sowie bei Tier-Wechsel. Die Spec verweist auf eine Spec-A-Lösung, die es nicht gibt, und AC-C14/AC-B7/AC-C3 sind im Plan nicht erfüllbar.
- **N-M2:** Die Writer sind nicht an den eigenen Provider gebunden. Durch die tier-unabhängige Verdrahtung (Fix zu M-6) laufen Rückbauten in fremden Provider-Iterationen.
- **N-M3:** AC-C2 ist im Plan nicht prüfbar.

Alle drei lassen sich ohne Strukturänderung korrigieren. Die Freigabe bleibt zusätzlich an OQ-B1/A-6 (Nutzerbestätigung) gebunden.

**Re-Review-Fokus:** N-M1, N-M2, N-M3, m-1, m-2.
