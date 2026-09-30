# Review — Spec `2026-09-19-dynamic-routing-template-slimming.md`

> Reviewer: `concept-reviewer` · Datum: 2026-09-19
> Reviewed artifact: `docs/specs/2026-09-19-dynamic-routing-template-slimming.md` (Status DRAFT, 585 Zeilen)
> Trace-Anker (reviewed): `spec-id: SPEC-dynamic-routing-template-slimming`
> Modus: Spec-Review (§7.1) · Read-only

## Verdict: CHANGES_REQUESTED

Die Spec ist strukturell vollständig, methodisch sauber (Ist-Analyse, Contracts, ACs,
Risiken, Threat-Model, Teststrategie, Self-Review) und im Kern tragfähig. Sie ist
**noch nicht freigabefähig**, weil

- ein zentraler Widerspruch die Erfüllbarkeit von AC A3 blockiert (RVW-01),
- mehrere übernommene Ist-Analyse-Aussagen am Repo widerlegbar sind (RVW-02, RVW-03),
- der deklarierte Route-Guard-Schutz durch das Verschieben in Snippets nicht mehr
  trägt (RVW-04),
- drei Interface-Contracts nicht ausimplementierbar sind wie beschrieben
  (RVW-05, RVW-06, RVW-07),
- der zentrale Zielmechanismus (Name-Dispatch) an keiner Stelle erzwungen wird (RVW-09).

Kein Finding ist unbehebbar; keines rechtfertigt `BLOCKED`.

Hinweis Umgebung: Das im Workflow referenzierte Report-Template
`.opencode/snippets/concept-review-report.md` existiert in diesem Checkout nicht
(glob ohne Treffer). Das Review folgt daher dem Vertrag aus dem Rollen-Prompt.

---

## Findings

### BLOCKER

**RVW-01 — `require_template` widersprüchlich zwischen §5.2 und §5.4/AC A3**
- Kategorie: Logik / Konsistenz
- Stelle: §5.2 („`delegation_table._active_role_names` wird ein Wrapper um
  `resolve_active_roles(require_template=False)`") vs. §5.4 (`"target_agents"`-Kommentar
  „aktive Nicht-Orchestrator-Rollen (require_template=True)") vs. AC A3
  („Routing-Ziele exakt `(aktive Rollen ∩ generierbare Rollen) \ {orchestrator}`").
- Begründung: `get_routing_rules()` leitet `target_agents` heute aus `_active_role_names`
  ab (`delegation_table.py:135-138`). Wenn `_active_role_names` per Spec
  `require_template=False` aufruft, kann `target_agents` nicht die in A3 geforderte
  Schnittmenge mit der generierbaren Menge sein — A3 wäre per Konstruktion nicht
  erfüllbar. Dieselbe Funktion speist aber auch `get_active_agents_data()` (Zeilen
  81-94), das nicht zwingend template-gefiltert sein soll; ein pauschales Umschalten
  des Wrappers kippt die Tabelle mit.
- Geforderte Änderung: Call-Sites explizit trennen. Entweder `get_routing_rules()`
  ruft `resolve_active_roles(..., require_template=True)` direkt auf (nicht über den
  `require_template=False`-Wrapper), oder `_active_role_names` erhält einen Parameter.
  §5.2, §5.4 und A3 auf dieselbe Call-Site-Semantik bringen.

### MAJOR

**RVW-02 — Ist-Analyse §1.6 ist faktisch falsch**
- Kategorie: Vollständigkeit / Annahmen
- Stelle: §1.6 „`agents/1-generic/provider-expert.md`, `agents/1-generic/*-reviewer.md`
  haben keinen Eintrag in `config/role-defaults.yaml`."
- Begründung: Alle sechs `*-reviewer.md`-Templates haben sehr wohl Einträge:
  `code-reviewer:` (role-defaults.yaml:1189), `concept-reviewer:` (:1219),
  `frontend-reviewer:` (:2221), `backend-reviewer:` (:2242), `database-reviewer:`
  (:2263), `ui-reviewer:` (:2284) — jeweils mit `routing_patterns`. Nur
  `provider-expert` fehlt (grep ohne Treffer). Die Aussage „Sie können daher weder im
  Routing-Ziel-Enum noch im `name_index` auftauchen; unklar, ob gewollt oder stiller
  Drop" trägt nicht.
- Geforderte Änderung: §1.6 auf `provider-expert` (einziger belegter Fall) reduzieren;
  R7/O4 auf den tatsächlichen Einzelfall zuschneiden. Falls weitere Templates betroffen
  sind, vollständige Liste beilegen.

**RVW-03 — `ANTI_RECURSION_BLOCK` ist nicht 0×, AC B1 beruht auf falscher Zahl**
- Kategorie: Vollständigkeit / Logik
- Stelle: §1.7-Tabelle (`ANTI_RECURSION_BLOCK` … „**0×**"), §5.5 („aktivieren (0 → n
  Referenzen)"), AC B1 („`ANTI_RECURSION_BLOCK` wird mindestens einmal referenziert
  (heute 0×)").
- Begründung: Bereits referenziert in aktiven Templates:
  `agents/1-generic/developer.md:138`, `agents/1-generic/orchestrator.md:298`,
  `agents/1-generic/_reference-agent.md:160`, `agents/2-platform/sharkord-developer.md:85`,
  `agents/2-platform/agent-meta-developer.md:157`. B1 wäre bereits heute erfüllt.
- Geforderte Änderung: Zahl im Ist-Stand korrigieren; B1 auf den echten Slimming-Effekt
  umformulieren (z.B. „die inline duplizierte Anti-Recursion-Prosa ist durch
  `{{ANTI_RECURSION_BLOCK}}` ersetzt; kein Template enthält sie mehr wörtlich").

**RVW-04 — Route-Guard deckt den neuen Ablageort `snippets/` nicht ab**
- Kategorie: Threat-Model / Logik
- Stelle: §2.2.2 + AC A6/B3 („Routing lebt ausschließlich in `config/role-defaults.yaml`"),
  §6.2 F3 („Route-Guard … wird auf Snippets ausgeweitet geprüft (A6/B3)").
- Begründung: Der Guard scannt `_SCOPE_GLOBS = ("agents/1-generic/*.md",
  "rules/1-generic/*.md")` (`tests/test_no_role_routes_in_templates.py:54`) — `snippets/`
  ist nicht im Scope. Darüber hinaus ist „Snippets ausweiten" ein Nicht-Ziel (§3:
  „Detektoren/Ausnahmen bleiben unverändert"). Block B verschiebt genau solche
  wiederkehrenden Blöcke in Snippets; A6/B3 können die Routing-Freiheit des neuen
  Ablageorts damit prinzipiell nicht garantieren. F3 behauptet eine Deckung, die weder
  durch das Nicht-Ziel noch durch die ACs gedeckt ist.
- Geforderte Änderung: Entweder Snippet-Scope in den Guard aufnehmen (inkl. neuem Test)
  und das Nicht-Ziel entsprechend präzisieren („Detektor-Logik unverändert, Scope
  erweitert"), oder explizit zusichern und testen, dass Snippet-Dateien keinerlei
  Routing-Konstrukte enthalten.

**RVW-05 — `_is_role_enabled`-Re-Export ist mit der zugesicherten Signatur nicht baubar**
- Kategorie: Feasibility / Interface
- Stelle: §5.2 („`frontmatter.py::_is_role_enabled(role, config)` wird zum dünnen
  Re-Export … Signatur bleibt kompatibel").
- Begründung: `roles.is_role_enabled(role, config, gates)` benötigt `gates`, die laut
  §5.2 aus `config/role-defaults.yaml::activation_groups` stammen —
  `resolve_activation_gates(agent_meta_root, config)` braucht also `agent_meta_root`.
  `frontmatter._is_role_enabled` (heute `frontmatter.py:467-475`) erhält nur
  `(role, config)`. Ein „dünner Re-Export" ohne Root-Zugriff kann die Defaults nicht
  laden; ohne Defaults wäre das Gate bedeutungslos.
- Geforderte Änderung: Interface festlegen: entweder `agent_meta_root` in die Signatur
  aufnehmen (+ Migrationsplan für Bestandsaufrufer), oder einen prozessweit gecachten
  Default-Resolver benennen, der ohne Root auskommt. Kein „Signatur bleibt kompatibel"
  ohne Mechanismus.

**RVW-06 — A3-Warnungen haben keinen definierten Sink und sind nicht testbar**
- Kategorie: Vollständigkeit / Testbarkeit
- Stelle: AC A3 („jede Abweichung … erzeugt mindestens eine Warnung"), §5.2
  `resolve_active_roles` („Emits warnings for (a) … (b) …").
- Begründung: Der Interface-Contract nennt keinen Warnkanal (Rückgabewert? Logger?
  bestehender `unmapped`-Sink wie in `_build_platform_variables` / `build_agent_table`?).
  Ohne Kanal kann der geforderte Test („mindestens eine Warnung") nicht assertieren.
- Geforderte Änderung: Warn-Sink im Contract festschreiben (z.B. Rückgabe der
  Warnliste oder Anschluss an den bestehenden `unmapped`-Mechanismus) und im neuen
  `test_unified_active_set.py` den Assert dagegen definieren.

**RVW-07 — `config_key: roles` ist als Membership-Prädikat undefiniert**
- Kategorie: Logik / Vollständigkeit
- Stelle: §5.1 `activation_groups.validator` und `.developer_tiers` (`config_key: roles
  # Whitelist-Mitgliedschaft`), AC A2.
- Begründung: Für `validator` lautet die heutige Produktionsregel
  `"validator" in config["roles"]` (`config.py:1601`), für `developer_tiers`
  dagegen konjunktiv `"junior-developer" in roles AND "senior-developer" in roles`
  (`config.py:1605-1607`). Die Spec generalisiert beides zu „Whitelist-Mitgliedschaft",
  ohne die Prädikate zu definieren. `principal-developer ∈ developer_tiers.role_patterns`,
  wird aber in config.py gar nicht als Gate-Kriterium verwendet.
- Geforderte Änderung: Pro Gruppe das exakte Membership-Prädikat spezifizieren
  (Single/Conjunctive) und die Abweichung zur heutigen conj. Regel als bewussten
  Behavior-Change in §3/§6 ausweisen.

**RVW-08 — Byte-Identität als Slimming-Prämisse ist unbelegt und der Inlining-Vertrag fehlt**
- Kategorie: Annahmen / Feasibility
- Stelle: §2.2.3 („Für byte-identische wiederkehrende Blöcke muss der generierte Output
  byte-identisch bleiben (Snippets werden beim Rendern inlined)"), AC B2, §5.5.
- Begründung: Die Spec räumt im Self-Review ein, die Redundanzzahlen (49×/51×) „nicht
  erneut breit verifiziert" übernommen zu haben. Ob überhaupt byte-identische
  Vorkommen existieren (vs. unterschiedlich eingerückte/umgebende Vorkommen), ist damit
  offen. Zudem fehlt der Transformationsvertrag beim Inlining: Snippet-Dateien tragen
  YAML-Frontmatter (§5.5), das beim Rendern entfernt werden muss; Einrückung, führende/
  nachfolgende Leerzeilen und Zeilenenden sind nicht definiert. Bei 51 Einbettungen in
  verschiedener Verschachtelung ist Byte-Gleichheit ohne Normalisierung
  unwahrscheinlich; B2 wäre dann nur über das Diff-Manifest erfüllbar.
  `config.py:2214-2230` (Snippet-Kopierlogik) wurde laut Self-Review ebenfalls nicht
  verifiziert.
- Geforderte Änderung: Vorkommen vorab prüfen und klassifizieren (byte-identisch vs.
  normalisiert); Inlining-Transform (Frontmatter-Strip, Whitespace-/Einrückungsregeln)
  als Contract festschreiben; B2 entsprechend trennen in „byte-identisch" und
  „dokumentiert normalisiert".

**RVW-09 — Der Zielmechanismus „Name→Rolle im Fallback" wird nirgends erzwungen**
- Kategorie: Vollständigkeit / Logik
- Stelle: §2.1.6/§5.6 („Name→Rolle via `name_index`"), AC A4 (prüft nur Datenpräsenz).
- Begründung: `agents/1-generic/orchestrator.md:95` weist den Fallback an, die Route aus
  Keywords/Beispielphrasen/`routing.rules` abzuleiten — `name_index` wird dort nicht
  erwähnt. `{{INTENT_ROUTING_TOOLS}}` wird zwar unabhängig vom Conditional (Zeile 98,
  außerhalb `{{#if ROUTE_INTENT_CALLABLE}}`) eingebettet, also wäre `name_index` im
  Prompt verfügbar; kein AC und kein Interface stellt jedoch sicher, dass der
  Orchestrator ihn für Name-Dispatch nutzt. Damit bleibt das Kernziel „jede aktive Rolle
  adressierbar" daten-, aber nicht verhaltensseitig abgesichert.
- Geforderte Änderung: Prompt-Änderung in `orchestrator.md` (Fallback-Zweig) als
  vertragliche Änderung aufnehmen und eine prüfbare AC ergänzen (z.B. name_only-Rolle
  dispatchbar über `name_index` im nicht-callable Pfad).

### MINOR

**RVW-10 — A1 vs. §5.3: `keyword`-Bedingung widersprüchlich**
- Kategorie: Logik
- Stelle: AC A1 („ jede `keyword`-Rolle hat nicht-leere `routing_patterns.keywords`")
  vs. §5.3 (`keyword`: „erfordert nicht-leere `routing_patterns.keywords` **oder**
  `.examples`").
- Begründung: Zwei unterschiedliche Notwendigkeitsbedingungen für dieselbe Menge.
- Geforderte Änderung: Angleichen (eine der beiden Formulierungen streichen).

**RVW-11 — B2-Baseline-Zeitpunkt ambivalent**
- Kategorie: Logik
- Stelle: AC B2 („byte-identisch zu einer **vor der Änderung** eingefrorenen
  Golden-Baseline") vs. §7.3 („Baseline-Golden-Set **vor Block B** einfrieren").
- Begründung: Block A ändert generierten Output (u.a. `name_index`,
  `openscad-developer`-Patterns). Ein Baseline-Set „vor der Änderung" (vor A) würde
  Block-A-Diffs als B2-Verstöße werten, obwohl sie gewollt sind.
- Geforderte Änderung: In B2 explizit „nach Block A, vor Block B" festschreiben.

**RVW-12 — Approval-/Trace-Marker nicht in kanonischer Form**
- Kategorie: Traceability (§7.1)
- Stelle: Header `> Status: DRAFT` (Zeile 3) und `> Trace-Anker: spec-id: …` (Zeile 6).
- Begründung: Spec-Template (`.opencode/skills/spec-plan-workflow/SKILL.md:71-84`)
  sieht `Status: Entwurf | APPROVED (Datum)` und den Trace-Anker als eigene
  `## Trace-Anker`-Sektion vor. `DRAFT` ist kein kanonischer Marker; der Anker ist
  vorhanden und maschinenlesbar, aber nicht in der Templatestruktur.
- Geforderte Änderung: `Status: Entwurf` verwenden; Trace-Anker als eigene Sektion oder
  die Template-Konvention dokumentiert angleichen.

**RVW-14 — Rolle von `variables` im neuen Resolver undefiniert**
- Kategorie: Annahmen / Logik
- Stelle: §5.2 `resolve_active_roles(agent_meta_root, config, variables, …)` +
  `resolve_activation_gates(agent_meta_root, config)` (ohne `variables`).
- Begründung: Die Gates werden laut Docstring aus `config` aufgelöst; `variables` bleibt
  ohne Aufgabe. Heute ist `variables` die einzige Gate-Quelle (`SE_ENABLED` etc.,
  `delegation_table.py:49-52`). Bleibt die Doppelquelle bestehen, droht genau die
  Divergenz, die Block A beseitigen soll.
- Geforderte Änderung: Klären, ob `variables` überhaupt noch Parameter ist; falls ja,
  Präzedenz (config vs. variables) explizit definieren, sonst entfernen.

**RVW-15 — Ist-Analyse: keine vollständige Rollen-/Adressierbarkeitsliste, kein
expliziter Problem-Abschnitt**
- Kategorie: Vollständigkeit
- Stelle: §1 (Zahlen, aber keine 84er-Rollen-Inventarliste) vs. §7.1-Pflichtsektion
  „Problem / Ziel / Nicht-Ziele".
- Begründung: Die Migration setzt `addressability` für 84 Rollen; die Spec nennt nur
  die 4 Sonderfälle. Die Ableitungsregel (§5.3) deckt das ab, eine prüfbare
  Erwartungstabelle fehlt aber. Ein „Problem"-Kapitel existiert nur implizit
  (`## 1. Ist-Analyse`).
- Geforderte Änderung: Entweder Adressierbarkeits-Mapping-Tabelle (oder Regel-Verweis
  mit Zähl-Erwartung „80 keyword / 3 name_only / 1 excluded") beilegen und den
  Problem-Kern als eigenständigen Absatz voranstellen.

### NIT

**RVW-13 — Doppelte AC / Self-Review-Mapping unvollständig / AC-Anzahl**
- Kategorie: Konsistenz
- Stelle: AC A6 und B3 (identische Route-Guard-Aussage); §9 Self-Review
  („Jede AC ist mindestens einem Contract zugeordnet", Mapping nennt A5, A6, A7, B3, B5,
  B6 nicht).
- Begründung: A6/B3 sind bis auf den Kontext deckungsgleich; die Self-Review-Aussage
  deckt nur 8 der 14 ACs. Der Parent-Auftrag nennt „17 ACs" — die Spec enthält
  tatsächlich **14** (A1–A8, B1–B6).
- Geforderte Änderung: A6/B3 zusammenführen oder scharf trennen; Mapping vervollständigen;
  AC-Zahl im Review-Kontext auf 14 korrigieren.

**RVW-16 — Threat-Model: Daten-/Instruktionsgrenze des `name_index` nicht explizit**
- Kategorie: Threat-Model
- Stelle: §6.2 F2/F3.
- Begründung: `name_index`-Felder (`agent`, `short_desc`, `name_only_reason`) werden in
  den Orchestrator-Prompt eingebettet. Das sind repo-kontrollierte Daten; die Spec sagt
  korrekt, es gebe keine Laufzeit-Nutzereingaben, markiert die Felder aber nicht
  explizit als „nur Daten, nie Instruktion".
- Geforderte Änderung: Ein Satz in F3, dass `name_index` (inkl. Freitext
  `name_only_reason`) reine Datenfläche ist und nie als Routing-/Instruktionsquelle
  interpretiert wird.

---

## Vollständigkeits-Check

| Pflichtelement | Status |
|---|---|
| Ist-Analyse | vorhanden (§1), aber mit belegbaren Fehlern (RVW-02, RVW-03) und ohne vollständige Rollenliste (RVW-15) |
| Zielbild | vorhanden (§2), Block A/B sauber getrennt |
| Nicht-Ziele | vorhanden (§3), inkl. Guardrails (Provider, Worktree, Containment) |
| Acceptance Criteria | vorhanden, 14 statt 17; A3 aktuell nicht erfüllbar (RVW-01), A3-Warnung nicht testbar (RVW-06) |
| Interface Contracts | vorhanden (§5), drei Verträge unvollständig (RVW-05, RVW-06, RVW-07) |
| Datenfluss | vorhanden (§1.4 verifiziert, §5.6 Zielzustand) |
| Risiken | vorhanden (§6.1, R1-R8 mit Mitigation) |
| Threat-Model (4 Fragen) | vorhanden (§6.2 F1-F4), F3 teilweise unbelegt (RVW-04) |
| Teststrategie | vorhanden (§7), neue Tests benannt |
| Offene Entscheidungen | vorhanden (§8, 5) — O1 ist vor `APPROVED` zu schließen |
| Self-Review | vorhanden (§9), überzeichnet zwei Aussagen (RVW-13) |

## Logik-/Konsistenz-Check (Block A vs. B)

- Block A und Block B sind sauber getrennt; der gemeinsame Guard-Bezug (A6/B3) ist
  konsistent gedacht, aber doppelt (RVW-13) und im Snippet-Scope ungedeckt (RVW-04).
- Zentrale Inkonsistenz: `require_template` (RVW-01) — blockiert A3.
- B2 vs. Block A: Zeitpunkt der Golden-Baseline unscharf (RVW-11); Byte-Prämisse
  unbelegt (RVW-08).
- Kein Widerspruch bei Provider-Agnostik: §2/§3/§5 dispatcht durchgängig über
  Capability-/Mechanismus-Keys, kein `if provider ==`.

## Annahmen-Check

Tragende, nicht belegte Annahmen:
1. Byte-Identität / Inlining-Transform beim Slimming (RVW-08) — trägt B2.
2. `name_index` wird im Fallback tatsächlich konsumiert (RVW-09) — trägt das Zielbild
   „jede Rolle adressierbar".
3. `config_key: roles` als generisches Membership-Prädikat (RVW-07) — trägt A2.
4. Re-Export-Kompatibilität ohne Root-Zugriff (RVW-05) — trägt A2/A3-Migration.
5. Redundanzzahlen/Snippet-Kopierlogik unverifiziert (Self-Review, RVW-08).

## Threat-Model-Check (4 Fragen)

F1 (Was bauen wir?), F2 (Was kann schiefgehen?), F3 (Mitigationen?), F4 (Konsequenzen?)
sind vollständig und für ein internes Dev-Tooling-Repo angemessen (kein Produktions-/
Kundenzugriff, keine Laufzeit-Nutzereingaben, kein Secret-Handling). Belastbar **mit
Einschränkung**: F3 behauptet Snippet-Guard-Abdeckung, die durch A6/B3 nicht gedeckt ist
(RVW-04); die Daten-/Instruktionsgrenze des `name_index` ist nicht explizit (RVW-16).

## Route-Guard-/Provider-Agnostik-Check

- Provider-Agnostik: **nicht verletzt**. Keine Provider-Name-Branches; §5.1
  `activation_groups` ist provider-frei; §3 verbietet Capability-Änderungen.
- Route-Guard: Guard-Prinzip (Routing nur in `config/role-defaults.yaml`) bleibt
  nominell gewahrt, aber die Durchsetzung ist für den neuen Ablageort `snippets/`
  lückenhaft (RVW-04). Kein Finding gegen die Formulierung von A6/B3 selbst.

## Bestätigte Punkte (stimmig, kein Finding)

- 84 Rollen in `config/role-defaults.yaml` bestätigt; 4 ohne `routing_patterns`
  (`orchestrator`, `intern-developer`, `principal-developer`, `openscad-developer`)
  stimmen mit `test_roles_without_routing_stay_patternless` (`:67-73`) überein.
- `orchestrator_only: true` genau 3× (`principal-developer`, `bug-feature-analyzer`,
  `knowledge-indexer`).
- Divergenz `_active_role_names` (`delegation_table.py:34-67`) vs. `_is_role_enabled`
  (`frontmatter.py:467-475`) belegt; SE-Default-Widerspruch
  `True` (frontmatter:471) vs. `False` (config.py:1580) belegt.
- `route_intent_tool: false` für alle Provider (`config/provider-capabilities.yaml`);
  Fallback-Conditional in `orchestrator.md:92-96`, `{{INTENT_ROUTING_TOOLS}}` außerhalb
  des Conditionals (Zeile 98) — `name_index` wäre im Prompt verfügbar.
- `_SCOPE_GLOBS` und Detektoren `T-ROUTE-COL`/`T-ROLE-ARROW`/`T-HANDOFF`/`T-NEXT`
  existieren wie referenziert.
- Trace-Anker `spec-id: SPEC-dynamic-routing-template-slimming` gesetzt und
  referenzierbar; `Status` ist klar nicht-approval (kein `APPROVED`).

## Freigabe-Bedingung

`APPROVED` erfordert: Behebung von RVW-01 (Blocker), Auflösung der MAJOR-Findings
RVW-02 bis RVW-09 sowie Schließen von O1 (SE-Default) und O2 (Resolver-Injektion).
RVW-10 bis RVW-16 sind vor `APPROVED` mindestens pragmatisch zu adressieren.
