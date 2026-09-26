# Re-Review — Spec `2026-09-19-dynamic-routing-template-slimming.md` (Revision 2)

> Reviewer: `concept-reviewer` · Datum: 2026-09-19
> Reviewed artifact: `docs/specs/2026-09-19-dynamic-routing-template-slimming.md`
> (Revision 2, 770 Zeilen, Status `Entwurf (DRAFT)`)
> Vorgänger-Review: `docs/specs/2026-09-19-dynamic-routing-template-slimming-review.md`
> Trace-Anker: `spec-id: SPEC-dynamic-routing-template-slimming` · Read-only

## Verdict: CHANGES_REQUESTED

Der Blocker RVW-01 ist **tatsächlich** aufgelöst, RVW-02/03 sind inhaltlich belegt
korrigiert, RVW-15 ist zugunsten des Autors entschieden (81/2/1 ist korrekt, mein
80/3/1 war falsch). 14 ACs, vollständiges Mapping, O1/O2 geschlossen.

Es verbleiben **zwei MAJOR** und drei MINOR, die vor `APPROVED` zu schließen sind:
A8 kollidiert mit der `developer_tiers`-Gate-Semantik für `principal-developer`
(RVW-17), und der fail-closed-Default des neuen `_active_role_names` bricht einen
bestehenden Call-Site (`get_active_agents_data` → `INTENT_ROUTING_TABLE`) (RVW-18).
Kein Finding rechtfertigt `BLOCKED`.

---

## Explizite Bestätigungen

### RVW-01 (Blocker) — AUFGELÖST
- §3.5 stellt klar: `get_routing_rules()` ruft
  `resolve_active_roles(..., require_template=True, template_roles=<collect_sources>)`
  **direkt** auf; `_active_role_names` wird parametrisiert (`require_template: bool`).
- AC A3 ist jetzt deckungsgleich formuliert: Routing-Ziele ==
  `resolve_active_roles(require_template=True) \ {orchestrator}`, Hints/Tabelle nutzen
  dieselbe Layer-2-Menge.
- Verifiziert am Code: `_active_role_names` hat genau die zwei Aufrufer
  `delegation_table.py:81` und `:136` — die geforderte Trennung ist damit überhaupt
  herstellbar. Rest siehe RVW-18 (Call-Site-Migration nicht vollständig ausgewiesen),
  der Blocker-Widerspruch selbst ist weg.

### RVW-15 (80/3/1 vs. 81/2/1) — AUTOR HAT RECHT
- Faktisch: `config/role-defaults.yaml` hat **genau 80** `routing_patterns:`-Einträge
  (grep: 80 Treffer). 4 Rollen ohne: `orchestrator`, `intern-developer`,
  `principal-developer`, `openscad-developer`.
- Nach Datenfehler-Fix erhält `openscad-developer` Patterns → **81 keyword**;
  `intern-developer` + `principal-developer` → **2 name_only**; `orchestrator` →
  **1 excluded**. Summe 84. Meine Beispielverteilung „80/3/1" in RVW-15 war
  rechnerisch falsch (sie zählte `openscad-developer` fälschlich zu `name_only`) und
  wird zurückgezogen.

### Weitere bestätigte Fixes
- **RVW-02:** `WRAPPER_TEMPLATES = {"provider-expert"}` (`frontmatter.py:55`),
  `collect_sources`-Ausschluss (`:637`), alle 6 `*-reviewer`-Einträge vorhanden
  (1189/1219/2221/2242/2263/2284) — verifiziert.
- **RVW-03:** 80 `routing_patterns:`; `{{ANTI_RECURSION_BLOCK}}` 5×
  (`developer.md:138`, `orchestrator.md:298`, `_reference-agent.md:160`,
  `sharkord-developer.md:85`, `agent-meta-developer.md:157`); `## Anti-Recursion Guard`
  21× in `agents/` — verifiziert.
- **RVW-04:** Scope-Erweiterung um `snippets/**/*.md` + A6 + neuer Test; Nicht-Ziel
  präzisiert (Detektor-Logik unverändert, Scope erweitert). Rest RVW-20.
- **RVW-05:** 3-Parameter-Signatur + Migrationsliste. Verifiziert: `config.py:645`
  hat `agent_meta_root`; `agents.py:105/178` haben es; `agent_sync.py:487`
  (`_should_skip_role`) hat es selbst **nicht**, der Aufrufer `sync_agents_for_provider`
  (`:1064`) schon — Durchreichen ist trivial. Keine versteckte Global-Abhängigkeit.
- **RVW-06:** `warn_sink`-Contract mit deterministischem Format. Rest RVW-19.
- **RVW-07:** `config_predicate` `mode: any` (validator) / `mode: all`
  (junior+senior) entspricht exakt `config.py:1601` bzw. `:1605-1607` — verifiziert.
- **RVW-08:** B2a/B2b getrennt, Inlining-Transform §3.7. Rest RVW-22.
- **RVW-09:** §3.6 Orchestrator-Fallback-Contract + AC A9. Verifiziert:
  `{{INTENT_ROUTING_TOOLS}}` liegt außerhalb des Conditionals (`orchestrator.md:98`).
- **RVW-10..14, 16, 13:** inhaltlich geschlossen; AC-Zahl 14 korrekt (A1–A9 + B1–B5);
  A6/B3 entdoppelt; Mapping vollständig.

---

## Rest-Findings

### RVW-17 — MAJOR (Logik / Testbarkeit): A8 vs. `developer_tiers`-Gate für `principal-developer`
- Stelle: §3.1 (`developer_tiers.role_patterns: [..., "principal-developer"]`,
  `default: false`; Fußnote „kein Gate-Kriterium, nur Gruppen-Mitgliedschaft"),
  §3.2 `is_role_enabled` („True, wenn `role` zu einer per gates aktivierten Gruppe
  gehört, sonst True"), AC A8 („`name_only`-Rollen sind in `target_agents` und
  `name_index` enthalten").
- Begründung: `principal-developer` ist über `role_patterns` Mitglied der Gruppe
  `developer_tiers`. Bei `default: false` (und ohne `roles`-Whitelist) liefert
  `is_role_enabled("principal-developer")` = `False` → Rolle fällt aus Layer 2 →
  **nicht** in `target_agents`/`name_index`. Genau das tut der Bestandstest heute:
  `tests/test_routing_tool_definitions.py:88` asserted bei
  `DEVELOPER_TIERS_ENABLED="false"` explizit `"principal-developer" not in enum`.
  A8 formuliert ohne Aktivierungs-Vorbedingung und wäre unter Default-Config nicht
  erfüllbar. Die Fußnote in §3.1 („kein Gate-Kriterium") widerspricht der generischen
  `role_patterns`-Gate-Semantik, ohne den Mechanismus zu benennen.
- Geforderte Änderung: Entweder (a) A8 mit Vorbedingung „bei aktiviertem
  `developer_tiers`" formulieren, oder (b) in §3.1/§3.2 explizit festlegen, dass
  `developer_tiers` nur `junior-developer`/`senior-developer` gatet und
  `principal-developer` in `role_patterns` ausschließlich der Adressierbarkeits-/
  Warnzuordnung dient (mit entsprechendem `is_role_enabled`-Sonderfall). (a) ist der
  kleinere Eingriff.

### RVW-18 — MAJOR (Interface / Regression): `_active_role_names`-Default bricht `get_active_agents_data`
- Stelle: §3.5 (`_active_role_names(..., *, require_template: bool = True,
  template_roles: set[str] | None = None)`), §3.2 („`require_template=True` ohne
  `template_roles` → ValueError (fail-closed)").
- Begründung: `_active_role_names` wird an `delegation_table.py:81` von
  `get_active_agents_data()` **ohne** `template_roles` aufgerufen. Mit Default
  `require_template=True` und fail-closed würde dieser Aufruf `ValueError` werfen.
  `get_active_agents_data()` speist `get_intent_routing_table()` (`:206`) →
  `INTENT_ROUTING_TABLE` (`config.py:1962`). Die Spec nennt nur die Trennung für
  `get_routing_rules()`, nicht die Migration der übrigen Call-Sites.
- Geforderte Änderung: In §3.5 explizit auflisten, wer `template_roles` injiziert:
  `get_routing_rules()` (Layer 2), `get_active_agents_data()` (welcher Layer? laut A3
  Layer 2 — dann ebenfalls `template_roles` durchreichen) und ggf.
  `get_intent_routing_table()`. Default-Wahl (`True` vs. `False`) mit den Call-Sites
  konsistent machen.

### RVW-19 — MINOR (Testbarkeit): `warn_sink` nicht in die Builder-Signaturen durchgezeichnet
- Stelle: §3.3 („Caller binden den Sink an den bestehenden `unmapped`-Mechanismus …
  `get_routing_rules` akzeptiert denselben Sink"), §3.5 (Rückgabe-Dict, aber keine
  Signatur mit `warn_sink`).
- Begründung: A3 verlangt den `warn_sink`-Eintrag beim Vergleich von
  `get_routing_rules()`, `build_agent_hints(include_table=True)` und
  `build_agent_table()`. Deren Signaturen werden in §3 nicht um `warn_sink` erweitert;
  ohne Injektionspunkt ist der A3-Test nicht direkt schreibbar.
- Geforderte Änderung: `warn_sink`-Parameter (oder Rückgabe der Warnliste) für
  `get_routing_rules`, `build_agent_hints`, `build_agent_table` im Contract ergänzen.

### RVW-20 — MINOR (Feasibility): bestehender Snippet-Korpus nicht auf Guard-Verträglichkeit geprüft
- Stelle: AC A6 / §1.8 (Scope-Erweiterung auf `snippets/**/*.md`).
- Begründung: Die 13 Bestands-Snippets wurden nicht analysiert. `snippets/orchestrator/
  se-mode.md` enthält `L0→L{{SE_MAX_DEPTH}}`, `continue → neuer System-Cell`,
  `L1: Requirements … ←→ Architecture … → Interface Registry`; `snippets/orchestrator/
  a2a-protocol.md` enthält `[task] → [agent]`. Diese sollten über `D-NONROLE` exempt
  sein (Tokens sind keine Rollen), aber die Spec sichert nicht zu, dass der erweiterte
  Scope sofort 0 Verstöße liefert.
- Geforderte Änderung: Bestands-Snippets einmal gegen die vier Detektoren prüfen und
  das Ergebnis (voraussichtlich clean / ggf. Remediation) in §1.8 oder A6 festhalten.

### RVW-21 — MINOR (Logik): `addressability`-Ableitung kennt `orchestrator` nicht
- Stelle: §3.4 („Fehlt `addressability`: Ableitung (Patterns vorhanden → `keyword`,
  sonst `name_only`)").
- Begründung: Für `orchestrator` (keine Patterns) würde die Ableitung `name_only`
  ergeben, obwohl A1/A5 `excluded` verlangen. Im Migrationsdatensatz wird es explizit
  gesetzt, die Fallback-Regel ist aber unscharf.
- Geforderte Änderung: Satz ergänzen: „`orchestrator` ist unabhängig von der Ableitung
  immer `excluded`."

### RVW-22 — NIT (Logik): Inlining-Einrückung nur für die erste Zeile
- Stelle: §3.7 Schritt 3 („die Einrückung am Verwendungsort liefert das Template").
- Begründung: Bei String-Substitution `{{*_BLOCK}}` → Text wird nur die erste Zeile des
  Blocks an der Template-Einrückung positioniert; Folgzeilen eines mehrzeiligen,
  eingerückten Vorkommens bleiben un-eingerückt. Byte-Identität ist damit auf
  Vorkommen beschränkt, deren Original-Einrückung zur Block-Einrückung passt.
- Geforderte Änderung: Klarstellen, dass B2a nur für Vorkommen gilt, deren
  Original-Einrückung mit der Snippet-Einrückung übereinstimmt (Rest → B2b).

### RVW-23 — NIT (Konsistenz): A3 nennt weiter `variables` als Eingabe
- Stelle: AC A3 („Given beliebige gültige `config`/`variables`").
- Begründung: §3.1/§3.2 haben `variables` als Gate-Quelle entfernt; A3 suggeriert
  weiterhin eine Abhängigkeit.
- Geforderte Änderung: Auf `config` (ggf. `template_roles`-Fixture) reduzieren.

---

## AC-Prüfung (14/14)

| AC | Testbar | Anmerkung |
|---|---|---|
| A1 | ja | Verteilung 81/2/1 faktisch korrekt |
| A2 | ja | `config_predicate` präzise |
| A3 | ja (mit RVW-19) | Warnkanal-Injektion fehlt |
| A4 | ja | |
| A5 | ja | |
| A6 | ja (mit RVW-20) | Bestands-Snippets ungeprüft |
| A7 | ja | |
| A8 | **nein unter Default** | RVW-17: Gate-Vorbedingung fehlt |
| A9 | ja | Prompt + Payload-Assert |
| B1 | ja | 21×→0× verifizierbar |
| B2 | ja | B2a/B2b getrennt; Baseline-Zeitpunkt korrekt (nach A, vor B) |
| B3 | ja | |
| B4 | ja | `--validate`/`--dry-run` existieren |
| B5 | informativ | kein Gate |

Duplikate: keine kritische Redundanz mehr (A6/B3 in v1 war der Duplikat-Kandidat und ist
entdoppelt). A8 ist Teilschnittmenge von A4 (name_only in `name_index`), aber mit
anderer Aussage (kein `rules[]`-Eintrag) — akzeptabel.

## Route-Guard-/Provider-Agnostik-Check

- Provider-Agnostik: nicht verletzt (keine `if provider ==`; Dispatch über
  Capability-Keys; 9 Provider `route_intent_tool: false` verifiziert).
- Route-Guard: Prinzip gewahrt; Scope-Erweiterung um Snippets ist der richtige
  Mechanismus. Feasibility-Rest RVW-20.

## Freigabe-Bedingung

`APPROVED` erfordert die Behebung von RVW-17 und RVW-18 (MAJOR). RVW-19 bis RVW-23
sollen vor `APPROVED` mindestens pragmatisch adressiert werden. RVW-01 ist
nachweislich geschlossen; RVW-15 ist zugunsten der Autoren-Fassung entschieden.
