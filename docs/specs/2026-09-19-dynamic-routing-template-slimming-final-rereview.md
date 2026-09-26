# Finales Re-Review — Spec `2026-09-19-dynamic-routing-template-slimming.md` (Revision 3)

> Reviewer: `concept-reviewer` · Datum: 2026-09-19
> Reviewed artifact: `docs/specs/2026-09-19-dynamic-routing-template-slimming.md`
> (Revision 3, 876 Zeilen, Status `Entwurf (DRAFT)`)
> Vorgänger: `...-rereview.md` (Rev 2, CHANGES_REQUESTED) · `...-review.md` (Rev 1, CHANGES_REQUESTED)
> Trace-Anker: `spec-id: SPEC-dynamic-routing-template-slimming` · Read-only

## Verdict: CHANGES_REQUESTED

Die beiden MAJOR-Findings der Revision 2 (RVW-17, RVW-18) sind **inhaltlich geschlossen**.
RVW-19, RVW-21, RVW-22, RVW-23 sind adressiert; die RVW-17-Variante (a) und das
RVW-20-Pre-Flight-Gate sind review-seitig tragfähig.

Es verbleibt **ein MAJOR** (RVW-24), das erst durch die zentrale v3-Änderung entsteht
(„`config` ist einzige Gate-Quelle"): die bestehende Zusicherung
`test_routing_tool_definitions.py:89` (`"validator" in enum`) bricht unter der neuen
Semantik, während §6.1 dieselbe Testspanne als „bleibt gültig" führt. Das ist eine
belegbare Traceability-Lücke im Test-Migrationsplan, kein Design-Widerspruch — der Fix
ist mechanisch klein. Aus Review-Sicht ist die Spec daher noch nicht freigabereif; nach
RVW-24 ist sie es.

---

## 1. RVW-17 (MAJOR) — STATUS: GESCHLOSSEN

- §3.1 trennt jetzt sauber: `role_patterns` = Gruppen-Mitgliedschaft (Gating),
  `config_predicate` = Enable-Prädikat. `principal-developer` ∈ `role_patterns` von
  `developer_tiers`, aber **nicht** im Prädikat (`all` junior+senior) — bei
  `default: false` inaktiv, deckungsgleich mit `test_routing_tool_definitions.py:88`.
- §3.2 `is_role_enabled`-Docstring konsistent: „True, wenn `role` über `role_patterns`
  zu einer per `gates` aktivierten Gruppe gehört, sonst True."
- §3.4 stellt `addressability` als **statische, aktivierungsorthogonale**
  Schema-Eigenschaft klar.
- AC A8 ist aktivierungsbewusst: positive Zusage nur bei aktiver Rolle (`intern-developer`
  ohne Gate-Gruppe; `principal-developer` bei aktiver `developer_tiers`), explizite
  Negativ-Klausel für die inaktive Gruppe. Damit ist A8 **unter Default-Config
  widerspruchsfrei und erfüllbar**: unter Default greift die Given-Klausel für
  `principal-developer` nicht, die Negativ-Klausel hält.
- Neuer Komplementär-Test `test_developer_tiers_gate.py` (§6.2) schließt die Lücke bei
  aktiver Gruppe; `test_routing_tool_definitions.py:88` bleibt gültig.
- **Restz-Nit RVW-25:** A8 nennt als alternativen Aktivierungspfad „(bzw. bei
  `principal-developer`-Whitelist)". Das widerspricht §3.1/§3.2: die Projekt-Whitelist
  ist ein **AND**-Filter nach den Gates (`Layer 1 = Gates + Whitelist`), und das
  `developer_tiers`-Prädikat verlangt `all` junior+senior. Eine reine
  `principal-developer`-Whitelist kann die Gruppe **nicht** aktivieren. Erratum streichen
  oder als separaten Override-Mechanismus definieren (dann aber außerhalb dieser Spec).

## 2. RVW-18 (MAJOR) — STATUS: GESCHLOSSEN

- §3.5: `_active_role_names`-Default zurück auf `require_template=False` (Back-Compat,
  kein ValueError); die zwei internen Aufrufer `get_active_agents_data()`
  (`delegation_table.py:81`) und `get_routing_rules()` (`:136`) rufen
  `resolve_active_roles(require_template=True)` explizit auf.
- `template_roles=None` wird bei `require_template=True` **lazy** über
  `resolve_template_roles(agent_meta_root, config)` aufgelöst statt fail-closed (§3.2) —
  der Default-Pfad bleibt funktionsfähig; `get_active_agents_data()` →
  `get_intent_routing_table()` → `INTENT_ROUTING_TABLE` bricht nicht.
- Vollständige Call-Site-Tabelle (7 Zeilen) + 5 Migrationsschritte (§3.5);
  `agents.build_routing_tool_definition`/`..._for_providers` reichen durch;
  `config.build_variables` bindet `unmapped` als `warn_sink`.
- **Konsistenz mit der Routing-Ziel-Menge bestätigt:** Routing-Ziele (Layer 2 aus
  `resolve_active_roles(require_template=True) \ {orchestrator}`) und Hints/Tabelle
  (eigene `collect_sources`-Filter + `resolve_template_roles`) sind deckungsgleich; A3
  ist damit erfüllbar.
- **Restz-Minor RVW-27:** `resolve_template_roles` ist als „collect_sources minus
  `WRAPPER_TEMPLATES`" definiert. `build_agent_hints`/`build_agent_table` filtern
  zusätzlich über `target_filename(role, role_map)` und verwerfen Templates ohne
  ROLE_MAP-Eintrag (`agents.py:159`, `:199-204`; `unmapped`-Liste existiert). Rollen mit
  Template, aber ohne ROLE_MAP-Eintrag würden damit in `target_agents` erscheinen, aber
  aus Hints/Tabelle fallen → A3-Divergenz. „Generierbar" sollte als
  `collect_sources \ WRAPPER_TEMPLATES \ {ohne ROLE_MAP}` definiert werden.

## 3. Kritik der beiden gewählten Varianten

**(a) RVW-17-Variante „Aktivierungs-Vorbedingung statt Semantik-Umbau" — akzeptiert.**
Sie ist der kleinere Eingriff, bleibt mit dem Bestandstest `:88` konsistent, und A8 wird
durch den Komplementär-Test bei aktiver Gruppe vollständig abgedeckt. Kein Semantik-Umbau
der `is_role_enabled`-Regel nötig. Einziger Restz ist das Whitelist-Erratum (RVW-25).

**(b) RVW-20 „Pre-Flight-Gate statt Vorab-Beweis" — akzeptiert.**
Die Spec dokumentiert den konkreten Bestands-Korpus (`se-mode.md:4,11,13,22,41`,
`a2a-protocol.md:4`), die beteiligten Tokens und die erwartete `D-NONROLE`-Exemption und
macht den Guard-Lauf zu einem verpflichtenden Implementierungsschritt (A6 verlangt
0 Verstöße; Treffer → Snippet-Umschreibung, keine Detektoränderung). Da Snippets via
Inlining in generierte Agenten eingehen, würde eine Snippet-Umschreibung ohnehin von B2
erfasst — die Semantik-Absicherung ist also gegeben. Ein Vorab-Beweis ist für die
Freigabe nicht erforderlich; das Gate ist ausreichend konkret.

## 4. RVW-19..23 — STATUS

- **RVW-19 (MINOR):** §3.3 listet die `warn_sink`/`template_roles`-Injektionspunkte für
  alle sechs Builder-Signaturen (`get_routing_rules`, `get_active_agents_data`,
  `get_intent_routing_table`, `build_agent_hints`, `build_agent_table`,
  `build_routing_tool_definition`) auf, inkl. Fallback über `SyncLog`. Adressiert.
- **RVW-20 (MINOR):** §1.8 + A6 als Pre-Flight-Gate. Adressiert.
- **RVW-21 (MINOR):** §3.4 „`orchestrator` ist unabhängig von der Ableitung immer
  `excluded`". Adressiert.
- **RVW-22 (NIT):** §3.7 Schritt 3 + B2a begrenzen Byte-Identität auf übereinstimmende
  Original-Einrückung; Rest → B2b. Adressiert.
- **RVW-23 (NIT):** A3 reduziert auf `config` (+ optionale `template_roles`-Fixture).
  Adressiert.

## 5. 14 ACs — finale Testbarkeit/Eindeutigkeit

| AC | Testbar | Anmerkung |
|---|---|---|
| A1 | ja | Verteilung 81/2/1 (faktisch bestätigt) |
| A2 | ja (mit RVW-26) | Signatur-Schreibweise s.u. |
| A3 | ja (mit RVW-27) | „generierbar" präzisieren |
| A4 | ja | |
| A5 | ja | statisch/aktivierungsorthogonal |
| A6 | ja | Pre-Flight + 0-Verstoß-Assert |
| A7 | ja | |
| A8 | ja | aktivierungsbewusst; RVW-25-Erratum |
| A9 | ja | Prompt-Text + Payload-Assert |
| B1 | ja | 21× → 0× |
| B2 | ja | B2a/B2b, Baseline nach A/vor B |
| B3 | ja | |
| B4 | ja | `--validate`/`--dry-run` existieren |
| B5 | informativ | kein Gate |

Keine Duplikate; kein AC ist nicht-entscheidbar. Anzahl korrekt 14.

## 6. Rest-Findings

### RVW-24 — MAJOR (Traceability / Test-Migration)
- Stelle: §6.1 (Zeile 727) „`tests/test_routing_tool_definitions.py:80-90` … **bleibt
  gültig**" vs. §3.1/§3.2 („`config` ist die **einzige** Gate-Quelle; `variables` keine
  Gate-Quelle mehr").
- Begründung: Testzeile 89 lautet `assert "validator" in enum`; der Aufruf ist
  `get_routing_rules(_AGENT_META_ROOT, {}, dict(_BASE_VARIABLES))` mit
  `VALIDATOR_ENABLED="true"` in `_BASE_VARIABLES` (Testdatei Zeilen 35-40, 81).
  `activation_groups.validator.config_predicate` = `roles_membership any ["validator"]`;
  bei `config = {}` ist `config.get("roles", [])` leer → Gate `false` → `validator` fällt
  aus `target_agents`. Die Aussage „bleibt gültig" ist damit falsch; die Zeile muss
  migriert werden (z.B. `config={"roles": ["validator"]}` oder Anpassung der Assertion).
  Die übrigen Assertions der Spanne (Zeilen 83-88 zu se/knowledge/junior/senior/principal)
  bleiben unter `config={}` gültig — nur Line 89 kippt.
- Wirkung: B4 („vollständige Suite grün") würde ohne diese Migration fehlschlagen, obwohl
  die Spec die Spanne als unverändert ausweist.
- Geforderte Änderung: In §6.1 die Testspanne auf `:80-88` eingrenzen (bleibt gültig) und
  die Validator-Assertion `:89` als zu migrierenden Fall ergänzen (Fixture mit
  `roles: ["validator"]` oder Assertion an die neue Gate-Semantik anpassen). Optional in
  §6.2 einen kleinen `test_validator_gate` als Komplement aufnehmen.

### RVW-25 — NIT (Konsistenz)
- Stelle: AC A8 („bzw. bei `principal-developer`-Whitelist") vs. §3.1/§3.2.
- Geforderte Änderung: Parenthese streichen (Whitelist ist AND-Filter nach den Gates).

### RVW-26 — NIT (Präzision)
- Stelle: AC A2 („`resolve_activation_gates(config)`") vs. §3.2
  (`resolve_activation_gates(agent_meta_root: Path, config: dict)`).
- Geforderte Änderung: Signatur in A2 vollständig schreiben.

### RVW-27 — MINOR (Interface-Definition)
- Stelle: §3.2 `resolve_template_roles` („collect_sources minus `WRAPPER_TEMPLATES`") vs.
  `agents.py:159`/`:199-204` (`target_filename`/`unmapped`).
- Geforderte Änderung: „generierbar" = `collect_sources \ WRAPPER_TEMPLATES \
  {Rollen ohne ROLE_MAP-Eintrag}` definieren, sodass A3 (Routing-Ziele == Hints/Tabelle)
  exakt hält.

### RVW-28 — NIT (Konsistenz)
- Stelle: §3.2 `resolve_active_roles`-Docstring („ValueError nur, wenn
  `require_template=True` UND `agent_meta_root` nicht ermittelbar ist").
- Begründung: `agent_meta_root` ist ein Pflichtparameter ohne Default; der ValueError-Zweig
  ist unerreichbar (und widerspricht der Aussage „kein ValueError im Default-Pfad" nicht,
  ist aber toter Text).
- Geforderte Änderung: Klausel entfernen oder Bedingung konkretisieren.

---

## Freigabe-Einschätzung

- **Aus Review-Sicht noch nicht freigabereif** — es verbleibt das MAJOR RVW-24.
- Nach Behebung von RVW-24 (mechanisch klein, Test-Migrationszeile) sind **alle
  BLOCKER/MAJOR geschlossen**; RVW-25, RVW-26, RVW-27, RVW-28 dürfen als MINOR/NIT
  „vor Plan/Merge adressieren" offen bleiben (RVW-27 sollte idealerweise in §3.2
  einfließen, da es sonst A3-Divergenz-Rauschen erzeugt).
- Die Freigabe selbst erteilt der User (`Status: APPROVED`). Der Review-Status lautet:
  nach RVW-24 freigabereif.
