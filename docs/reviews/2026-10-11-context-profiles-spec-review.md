# Review: SPEC-CONTEXT-PROFILES-2026-10-11 (Rev. 2.2, DRAFT)

- **Gegenstand:** `docs/specs/2026-10-11-context-profiles-spec.md` (1490 Zeilen, vollständig gelesen)
- **Evidenzbasis:** `docs/analysis/2026-10-11-context-budget-provider-study.md`
- **Reviewer:** concept-reviewer (Spec-Review-Modus), 2026-10-11
- **Verdikt:** **REVISE** (CHANGES_REQUESTED): 6 BLOCKER, 10 WARNUNGEN, 10 HINWEISE
- **Nicht neu verhandelt (entschieden):** Rollen `meta-doctor`/`meta-optimizer` generisch in `agents/1-generic`;
  Q18 Pipeline-Drop + WARN; Q12 geteilte Datei `full` + WARN; D-1 Gate-Card für Kimi-Worker (Phase 3).
  Findings betreffen nur Ausgestaltung, Nachweisbarkeit und Abhängigkeiten dieser Entscheidungen.

## 1. Scope und Methode

- Formale Spec-Checks (Pflichtsektionen, Trace-Anker, Approval-Marker, No-Placeholder).
- Querverweise F-/IC-/AC-/Q-/ADR-/QG-IDs, Phasenplan §9 gegen Abhängigkeiten.
- Stichproben gegen den Code (`scripts/lib/*.py`, `scripts/sync.py`, `config/*.yaml`, Tests, Hooks), siehe §5.
- Threat-Model (4 Fragen) für `meta-doctor`/`--doctor` und `meta-optimizer`/`--apply-config-patch`, siehe §4.

### Formale Spec-Checks

| Check | Ergebnis |
|---|---|
| Pflichtsektionen (Problem/Ziel/Nicht-Ziele §1, Interface Contracts §5, Datenfluss §6, AC §8, Offene Fragen + Risiken §12) | vorhanden |
| Trace-Anker `spec-id: SPEC-CONTEXT-PROFILES-2026-10-11` | vorhanden (Frontmatter, Kopf, Schluss) |
| Approval-Marker | `status: DRAFT` / „Status: Entwurf (DRAFT)": konsistent mit dem Review-Stand |
| No-Placeholder | `<…>` meist als Grammatik-Notation (zulässig); offen sind inhaltliche Platzhalter `name_only_reason: <Text>` (IC-23, IC-26), siehe H-4 |

## 2. Findings

### BLOCKER

**B-1: Optimizer-Beweis L0 gilt nur für das aktuelle Active Set; Inhaltsverlust bei späterer Rollen-/Provider-Aktivierung**
- Fundstelle: IC-24 Algorithmus Schritt 2 (`occurrences == 0` → `no-effect`), IC-25 L0 („alle aktiven Provider"), §4.6, AC-55.
- Begründung: Eine Variable, die nur von Templates inaktiver Rollen oder inaktiver Provider genutzt wird (z. B.
  `TEST_COMMANDS` bei inaktivem `tester`), hat 0 Vorkommen und besteht L0. Nach der Löschung fehlt der Wert,
  sobald die Rolle bzw. der Provider aktiviert wird: Der Inhalt ist verloren, und es bleibt ein unaufgelöster Platzhalter.
  Die 200-B-Schwelle (`dead-variable-content-loss`) deckt nur lange Werte ab. L0 belegt „Render heute gleich",
  aber nicht, dass keine Information verloren geht. Das widerspricht Ziel 8 („verlustfrei").
- Korrektur: `no-effect` nur, wenn die Variable in **keinem** Template der Framework-Menge (alle `known_roles` ×
  alle Provider) referenziert wird. Alternativ L0 zusätzlich auf einem „Universe-Render" beweisen (alle Rollen,
  alle Provider). Kandidaten, die nur im aktuellen Active Set wirkungslos sind, als neue Art `inactive-scope`
  (`deterministic: false`, nur mit `--accept`) führen. QG-11 um einen Fall „Variable nur von inaktiver Rolle
  genutzt ⇒ kein deterministischer Kandidat" ergänzen.

**B-2: Optimizer und das implizite `fill_defaults` widersprechen sich (Kommentarverlust beim nächsten Sync)**
- Fundstelle: IC-24 Schritt 3 („Wert gleich … Schema-Defaults → `no-effect`"), IC-25 („Renders über denselben
  Codepfad wie `--check`"), §4.6 „Verboten: `--fill-defaults`".
- Beleg: Jeder normale Sync ruft `fill_defaults(config_path, …, silent=True)` (`scripts/lib/sync_pipeline.py:152`).
  Fehlt ein strukturelles Top-Level-Feld, wird es ergänzt und die **gesamte** Datei per
  `yaml_dump_preserving_multiline` neu geschrieben (`scripts/lib/config.py:960-969, 1027-1029, 1072-1101`).
  Dabei gehen alle Nutzerkommentare verloren (F-31).
- Begründung: Entfernt der Optimizer einen strukturellen Key mit Default-Wert, fügt der nächste reguläre Sync ihn
  wieder ein und zerstört dabei genau die Kommentare, die der Roundtrip-Guard schützen sollte. Der L0-Render im
  Temp-Projekt füllt denselben Key ebenfalls nach und besteht deshalb trivial.
- Korrektur: Kandidatenraum ausdrücklich auf `variables.*` begrenzen. Keys aus `config_field_defaults()` ∪
  Schema-Top-Level-Defaults (also alles, was `fill_defaults` materialisiert) als Kandidaten ausschließen. Den
  L0-Render mit erzwungenem `dry_run` bzw. ohne Auto-Fill ausführen. Test: Optimizer-Patch anwenden, danach
  regulären Sync ausführen; `project.yaml` muss byte-gleich bleiben.

**B-3: L0 erfasst keine Laufzeit-Leser von `project.yaml`; der Applier vertraut den Hunks aus `proposal.json`**
- Fundstelle: IC-25 L0 („jede Datei byte-gleich" = nur generierte Artefakte), IC-24 `apply_config_patch(…, proposal, …)`,
  `Candidate.hunks`.
- Beleg: Hooks lesen `project.yaml` direkt zur Laufzeit, z. B. `.claude/hooks/repo-containment-impl.sh:170`
  (`CONFIG_FILE=…/project.yaml`), außerdem `orchestrator-guard-impl.sh`, `dod-push-check.sh`, `lib/hook_common.sh`.
- Begründung: (a) Eine Änderung an einem nur zur Laufzeit gelesenen Key (z. B. `repo_containment`, `auto_commit`,
  `admin-ui`) besteht L0, verändert aber sicherheitsrelevantes Verhalten. (b) `proposal.json` liegt beschreibbar
  unter `.tmp/`. Ein manipulierter oder vom LLM editierter Hunk, der Zeilen **einfügt** oder einen nicht gerenderten
  Key ändert, besteht L0.
- Korrektur: Der Applier berechnet die Kandidaten selbst neu (`collect_candidates`) und nimmt aus der Datei nur
  `accept_ids` + `project_yaml_sha256`; Hunks aus der Datei dienen höchstens zum Abgleich. Deterministische Hunks
  dürfen **nur entfernen** (Prüfung: `after_yaml` ist eine Zeilen-Teilfolge von `before_yaml`). Eine Denylist für
  Keys mit Laufzeit-Lesern aus einer Datenquelle (z. B. `config/runtime-config-readers.yaml`) einführen. Testfälle:
  manipulierter Hunk ⇒ Abbruch; Key mit Laufzeit-Leser ⇒ kein Kandidat.

**B-4: Die Read-only-Garantie von `--doctor` ist mit dem beschriebenen Muster nicht erreichbar**
- Fundstelle: IC-21 `command`-Allowlist (`--deactivation-status`), IC-22 („`ctx.read_only = True`, Muster
  `--audit-config`; ruft weder Writer noch `update_roles_enum`"), IC-23 Bash-Allowlist, AC-39.
- Beleg: `_handle_deactivation_status` (`scripts/lib/cli_commands.py:812-825`) setzt **kein** `read_only`. Danach
  läuft der Common-Tail und schreibt `sync.log` außerhalb von Dry-Run (`cli_commands.py:1265-1269`, `log.py:180-181`)
  sowie Env-Skripte (`:1230-1236`). `ctx.read_only` greift erst **nach** `_build_context`. Dieses ruft im Self-Hosting
  `update_roles_enum` (`cli_commands.py:497-498`), also vor jedem Handler. Den einzigen wirksamen Präzedenzfall
  liefert `--cleanup-preview`: Dry-Run erzwingen und stdout umleiten (`scripts/sync.py:683-692`).
- Begründung: Ein `command`-Detektor mit `--deactivation-status` überschreibt `sync.log`. `sync.log` ist zugleich
  Eingabe des Doctors (`finding-ref source: sync-log`), die Befundlage wird also durch die Messung selbst verfälscht.
  AC-39 würde das erst im Test entdecken, das Vertragsmuster in IC-22 ist falsch.
- Korrektur: (1) `--deactivation-status` aus beiden Allowlists streichen oder den Handler auf read-only umstellen
  (eigener Fix). (2) Der `command`-Detektor erzwingt `--dry-run` und hängt es an argv an. (3) IC-22 verweist auf das
  Muster aus `sync.py:683-692` statt auf `--audit-config`. (4) Die Detektor-Reihenfolge festlegen: `sync-log`-Leser
  vor `command`-Detektoren, `sync.log` einmal zu Beginn einlesen. (5) Ein AC-39-Testfall mit einem `command`-Seed
  auf einem Self-Hosting-Fixture.

**B-5: AC-01 ist in Phase 0 nicht erfüllbar, weil `meta-doctor` in Phase 0 liegt**
- Fundstelle: §9 Phase 0 („IC-23 `meta-doctor`", „Verhaltensänderung: keine"), AC-01 („byte-identisch zum Stand
  vor dem Feature"), Q17-Empfehlung „keine Aktivierungsgruppe" (Mehrkosten ≈ 1.2 KB in Projekten ohne Allowlist).
- Begründung: Eine neue Rolle ohne Gate erzeugt in jedem Projekt ohne `roles:` eine neue Agent-Datei und ändert
  Enum, `name_index`, Agent-Tabelle und Roster im Orchestrator. Die Provider-Matrix-Projekte ändern sich also, und
  AC-01 und „keine Verhaltensänderung" widersprechen der Phase-0-Zuordnung.
- Korrektur: Eine Variante wählen und festschreiben (Nutzerentscheidung, siehe §6):
  (a) AC-01 präzisieren: „byte-identisch bis auf die Artefakte der neuen Rollen (explizite Ausnahmeliste) und die
  Golden-Rebaseline im IC-23-PR";
  (b) IC-23 in einen eigenen Phase-0b-PR mit Golden-Rebaseline auslagern;
  (c) Q17 umkehren: Aktivierungsgruppe mit Default aus.

**B-6: Die Registry-Grammatik (IC-21) deckt mehrere Phase-0-Seeds nicht ab; `verified-state` ist nicht providergenau**
- Fundstelle: IC-21 Format + Seed-Tabelle; AC-37/AC-38 (alle Seeds, Positiv/Negativ-Fixtures in Phase 0).
- Begründung, je Seed:
  - `dispatch-depth-missing`: Vergleich `agents.max_depth ≥ required_depth` gegen einen **Capability-Wert**, aber
    `toml-key` kennt nur ein Literal `value` (es fehlt `value_key`).
  - `dead-variable-code-quality-rules`: Regex auf den **Config-Wert**, aber `regex` kennt nur ein festes `pattern`.
  - `read-only-not-enforced`: Das Prädikat „aktive Rolle ohne Write/Edit" ist mit
    `active_role: <role>, op: truthy|falsy` nicht formulierbar.
  - `surface-unverified`: Platzhalter `<s>` über Map-Keys, ohne Wildcard-Semantik.
  - `project-role-not-generated`: `path-exists` mit Iteration über `<role>`, Semantik undefiniert.
  - `schema-validation-skipped`: `finding-ref` auf `doctor.environment`, aber `source` kennt kein `doctor`.
  - `unread-channel`: `verified-state` = „gemischt", kein zulässiger Enum-Wert, der Registry-Test schlägt fehl.
  - `context-hard-cap-truncation` („VERIFIED-RUNTIME (Codex)") gilt per Prädikat auch für ZCode, dessen Cap in der
    Studie nur VERIFIED-SOURCE ist (Studie §4.2). `instruction-soft-cap-chars` mischt Copilot (Audit-Zitat) und
    Antigravity (UNVERIFIED).
- Korrektur: Grammatik erweitern (`value_key`, `pattern_from_config`, Rollen-Prädikat
  `active_role_where: {tools_without: [Write, Edit]}`, Map-Wildcard `*` mit Bindung, `source: doctor`). `verified-state`
  je Provider auflösen, entweder über einen optionalen Block `verified-state-by-capability` oder abgeleitet aus
  `surface_verified_state`. Den Severity-Deckel (ADR-11) je Provider anwenden. Seeds, die nicht formalisierbar sind,
  aus der Phase-0-Pflicht (AC-37) herausnehmen.

### WARNUNGEN

**W-1: Die Active-Set-Konsumentenliste (IC-18) ist unvollständig; der QG-13-Guard wäre in Phase 0 sofort rot**
- Fundstelle: IC-18-Tabelle, IC-19 `active-set.raw-roles-access` (ERROR), QG-13.
- Beleg (Rohzugriffe, die in IC-18 fehlen):
  - `scripts/lib/context.py:2342`: Continue-Prompts filtern gegen die ungegatete Allowlist.
  - `scripts/lib/sync_pipeline.py:1530`: Auto-Commit-Allowlist aus `config.get("roles")`. Das ist sicherheitsrelevant,
    weil eine gate-gedroppte Rolle Commit-Autorität behält.
  - `scripts/sync.py:414`, `scripts/lib/skills.py:424`, `config.py:682, 1681, 2036`.
- Korrektur: Inventar per Code-Grep vervollständigen und je Stelle „Konsument" oder „legitimer Validierer" festlegen
  (z. B. `config_audit.py:276`, `roles.py`). Den Guard als Ratchet mit schrumpfender Registry starten statt ab
  Phase 0 als ERROR. Den Auto-Commit-Konsumenten mit hoher Priorität in die Rangliste §11.1 aufnehmen.

**W-2: Phase 0 ist zu groß für einzelne PRs; die Reihenfolge innerhalb der Phase fehlt**
- Fundstelle: §9 Phase 0 (≈ 17 Arbeitspakete: Eval + Baseline, Tokenizer, `--context-report`, Anker, Budgets,
  IC-10, IC-09, IC-17, IC-19, IC-21 mit 26 Seeds × 2 Fixtures, IC-22, IC-23 + IC-28, IC-13-Erweiterung, IC-29,
  IC-30, IC-32, IC-33).
- Begründung: Phase 1 regelt „je Fix eigener PR", Phase 0 nicht. Es gibt interne Abhängigkeiten:
  - IC-21/IC-22 brauchen IC-10, IC-11 und IC-19.
  - IC-32 `based-on-stale` muss vor dem ersten Template-PR aktiv sein (§9), also vor IC-23.
  - IC-23 braucht IC-28 und IC-27-Contracts (`doctor-findings-v1`). IC-27 ist aber Phase 2 zugeordnet, sodass der
    Handoff an `agent-meta-manager` in Phase 0 `handoff.output-not-consumed` erzeugt.
- Korrektur: Phase 0 in benannte PR-Pakete schneiden, z. B.:
  - 0a: Messung/Report/Budgets
  - 0b: Check-Bibliothek IC-10/IC-19 + IC-17
  - 0c: Template-Guards IC-30/IC-32
  - 0d: Registry + Runner IC-21/IC-22
  - 0e: `meta-doctor` + IC-28 + `doctor-findings-v1`-Consumer (aus IC-27 vorziehen)
  - 0f: Eval-Korpus + Baseline

  Dazu eine DAG-Tabelle; AC-Zuordnung je Paket.

**W-3: Das Eval-Gate (QG-1/AC-25/AC-68/AC-70) ist statistisch nicht prüfbar**
- Fundstelle: QG-1 („≥ full − 1.0 Prozentpunkt je Metrik und je Modellklasse"), AC-02 („innerhalb der dokumentierten Streuung").
- Begründung: Bei einem Korpus von ≈ 500–700 Fällen entspricht 1 pp ≈ 5–7 Fällen. Die Streuung zwischen
  LLM-Läufen liegt typischerweise darüber, das Gate wird damit zufällig grün oder rot. Für Fehlerraten
  (Wrong-Pipeline-Rate) ist „≥ Baseline − 1 pp" die falsche Richtung. Für die Rückfrage-Rate ist keine Richtung
  definiert. AC-68/AC-70 verlangen pro Rollen-Migration einen eigenen Eval-Lauf, das sind viele LLM-Läufe in Phase 1.
- Korrektur: Je Metrik die Richtung festlegen (höher/niedriger besser). Toleranz = max(1 pp, k·σ aus ≥ 3
  Baseline-Läufen) oder ein gepaarter Test (McNemar) auf identischem Korpus. Migrationen batchweise evaluieren
  (ein Lauf je PR, nicht je Rolle).

**W-4: Die Beweisstufen L1/L2 passen nicht zu den Kandidatenarten**
- Fundstelle: IC-25 L1 (`duplicate-value`), L2 (`relocate-*`), IC-24 Diff („entfernt genau die Zeilen des Keys"),
  §11 (`PROJECT_CONTEXT` → Pointer-Satz).
- Begründung:
  - `duplicate-value`: Templates referenzieren beide Keys. Wird einer entfernt, ändert sich der Render und das
    Token-Multiset, L1 ist damit praktisch nie erfüllbar. Ist L1 doch erfüllt, war der Kandidat eigentlich L0.
  - `relocate-*`: Erfordert, den Wert durch einen Pointer-Satz zu **ersetzen**. Das zeilenbasierte Diff-Modell kennt
    nur Entfernen, und §1.3 verbietet Template-Änderungen.
  - Für die Relokationsziele (`<prefix>-<role>-ext.md`, Doku) sind weder Pfadgrenzen noch eine Merge-Regel definiert.
    Ein bestehendes `-ext.md` kann überschrieben werden, das ist Datenverlust.
- Korrektur: Für `duplicate-value` eine Zielsemantik definieren oder die Art bis Phase 3 streichen. Hunk-Typ
  „Wert ersetzen" mit eigenem Beweis aufnehmen. Ziele nur innerhalb des Projekt-Roots außerhalb von
  `.claude/`/Provider-Verzeichnissen zulassen. Bestehende Zieldateien nur anhängen (Managed-Block), nie überschreiben.
  Testfälle dafür in QG-11.

**W-5: Die Severity von `finding-ref` ist undefiniert; der Doctor endet in Phase 0 fast immer mit Exit 1**
- Fundstelle: IC-21 Seeds `dangling-pointer`/`rule-unreachable`/`dangling-role-dispatch` (ERROR), IC-10/IC-19
  (dieselben Checks in Phase 0 WARN), IC-22 Exit-Codes, Q20.
- Begründung: Es ist offen, ob die Registry-Severity oder die Check-Stufe gilt. Mit ERROR liefern praktisch alle
  heutigen Konsumentenprojekte Exit 1 (bekannte Defekte F-06/F-22), was in Hooks/CI blockiert.
- Korrektur: Regel festlegen: effektive Severity = min(Registry-Severity, Check-Stufe der aktuellen Phase,
  Deckel aus ADR-11). AC-41 um einen Severity-Abgleich ergänzen.

**W-6: Phasenabhängigkeit des Seeds `routing-examples-language-fallback`**
- Fundstelle: AC-67 (Phase 0) verlangt den Seed inkl. AC-38-Positiv-Fixture. Die `sync.log`-Zeile
  `routing.examples-language-fallback` entsteht aber erst mit IC-29 „Fallback-Sichtbarkeit", die über AC-69 Phase 1
  zugeordnet ist (heute still, `delegation_table.py:150-157`).
- Korrektur: Den Log-Teil von IC-29 ausdrücklich in Phase 0 aufnehmen oder den Seed nach Phase 1 verschieben.

**W-7: Das Threat-Model für `meta-doctor`/`meta-optimizer` fehlt als eigene Sektion**
- Fundstelle: §4.5, §4.6, IC-23, IC-26, IC-27; Risiken R8/R10 decken das nur teilweise ab.
- Begründung: Die Spec enthält keine Antworten auf die 4 Fragen. Ungeklärt sind insbesondere:
  - Woher wird die Registry geladen? Wenn nur aus `agent_meta_root`, muss ausgeschlossen werden, dass ein
    projektseitiger Overlay- oder Extension-Pfad `command`-Einträge einschleust.
  - Prompt-Injection über Befundtexte: Finding-Messages zitieren Inhalte generierter Dateien.
  - Bash in „read-only" Rollen: `git diff --output=<f>` schreibt Dateien.
  - Wie wird die „Nutzerfreigabe" vor `--apply-config-patch` belegt, wenn der Aufruf über Agenten läuft
    (Agenten-Nachricht ≠ Nutzerzustimmung)?

  Die Analyse dazu steht in §4 dieses Reviews.
- Korrektur: Sektion „§4.7 Threat-Model" mit den 4 Fragen aufnehmen. Ergänzen:
  - Registry ausschließlich aus `agent_meta_root/config/known-issues.yaml`, kein Projekt-Override (Test).
  - Finding-Messages ohne Rohzitate oder mit Längenbegrenzung und gekennzeichnet.
  - Alternative ohne Bash abwägen: `meta-doctor` nur mit Read/Glob/Grep; der Aufrufer führt
    `--doctor --json --out .tmp/doctor/<ts>.json` aus und übergibt die Datei.
  - Freigabe als ausdrückliche Nutzerantwort mit den angenommenen IDs; der Applier protokolliert `accept_ids`
    und den Hash in `.tmp/meta-optimizer/<ts>/applied.json`.

**W-8: Der Roundtrip-Guard zählt Kommentare heuristisch (Fehlalarm bei Block-Scalars)**
- Fundstelle: IC-25 „`lost_comments == expected_comment_loss` (aus den Hunks berechnet)".
- Beleg: `_count_comments` (`scripts/lib/yaml_roundtrip.py:85-116`) zählt jede Zeile mit `#` nach Whitespace, also
  auch Markdown-Überschriften in Block-Scalars (`PROJECT_CONTEXT: |` mit `# …`). `lost_comments` ist eine reine
  Netto-Differenz (`:60-62`).
- Korrektur: `expected_comment_loss` mit **derselben** Funktion auf den entfernten Zeilen berechnen. Zusätzlich die
  Teilfolgen-Prüfung aus B-3 als eigentliches Kriterium verwenden. Testfall: Variable mit Markdown-Block-Scalar entfernen.

**W-9: Umfang und Bündelung der Spec**
- Fundstelle: gesamte Spec (vier Features: Profile, Active-Set, Doctor, Optimizer, dazu Issue-Hygiene §3a).
- Begründung: Freigabe, Rückverfolgung und Plan-Referenzierung sind nur als Ganzes möglich. Ein BLOCKER im
  Optimizer hält das unabhängige Active-Set (Korrektheitsfixes) auf.
- Korrektur: Aufteilen in SPEC-ACTIVE-SET, SPEC-META-DOCTOR, SPEC-META-OPTIMIZER und SPEC-CONTEXT-PROFILES (diese
  Spec), mit gemeinsamem Studienverweis. Alternativ getrennte Approval-Marker je Teil (§4.4/§4.5/§4.6). Nutzerentscheidung.

**W-10: Die Reihenfolge-Regel blockiert den Optimizer unnötig**
- Fundstelle: §9 „Phase 2 beginnt erst, wenn AC-02 erfüllt ist" vs. „Optimizer … unabhängig vom Profil, parallel möglich".
- Korrektur: Das Eval-Gate nur auf IC-01…IC-12 beziehen. IC-24…IC-27 hängen nur an IC-17 (Phase 0).

### HINWEISE

- **H-1: Zeilennummern-Drift (Stichprobe).**
  - Whitelist in `variables.py` steht in **:298** (eine Zeile), nicht in `:298-306` (K-d, IC-03).
  - `claude -a` steht in `ai-providers.yaml:98` (nicht :97).
  - `ctx.read_only` steht in `cli_commands.py:659` (nicht :658).
  - `collect_sources` beginnt bei `frontmatter.py:605` (IC-20 nennt `:638-670`).
  - `SE_BASE_DIR` steht in `config.py:1661` (nicht :1660).

  Vor dem Plan nachziehen, besser Funktionsnamen statt Zeilen verwenden.
- **H-2: Die Pin-Liste in IC-28 Nr. 4 ist nicht sortiert.** Der Test nutzt `sorted(...)`
  (`tests/test_role_addressability_coverage.py:101-106`). Erwartet wird
  `["intern-developer", "meta-doctor", "meta-optimizer", "principal-developer", "template-auditor"]`. Der Docstring
  `:5` („81/2/1") ist veraltet und sollte im selben PR mitkorrigiert werden.
- **H-3: Für `meta-doctor` fehlt der Writer von ARTIFACTS `.tmp/doctor/<ts>.json`.** Die Rolle hat kein Write,
  die CLI kein `--out`. Vorschlag: `--doctor --json --out <path>` (analog `--optimize-config --out`).
- **H-4: Inhaltliche Platzhalter `name_only_reason: <Text>`** (IC-23, IC-26) und `description`/`short_desc` der
  neuen Rollen ausformulieren (No-Placeholder-Regel).
- **H-5: Sentinel-Fan-out bei Konditional-Variablen.** Variablen, die nur in `{{#if X}}` wirken, verlieren durch
  das Sentinel-Wrapping ihre Truthiness und erscheinen mit 0 Vorkommen. L0/Bisektion fängt das ab, aber der
  Fan-out-Report (AC-58) ist für sie falsch. Solche Variablen vom Sentinel-Wrapping ausnehmen und gesondert ausweisen.
- **H-6: `doctor.registry-invalid` ohne `--strict`.** Ein ERROR-Finding führt nach IC-22 zu Exit 1, laut IC-21 wird
  der Eintrag aber nur „übersprungen und gemeldet". Exit-Code eindeutig festlegen.
- **H-7: Widerspruch bei `--context-report`.** IC-11 sagt „schreibt nichts ins Projekt", rendert aber nach `.tmp/`
  im Projekt. Präzisieren: „schreibt nur unter `.tmp/`".
- **H-8: Rev.-2-Evidenz aus unversioniertem Scratch** (`.tmp/ctx-study/dyn/`). AC-43/QG-9 brauchen versionierte
  Fixture-Definitionen (p10-/p20-/pall-artig) unter `tests/fixtures/`. Ihre Konfiguration sollte in der Spec stehen.
- **H-9: QG-2 überzeichnet „Informationserhaltung".** `compact` entfernt §9-Begründungsprosa, Contracts und
  `short_desc`. Belegt wird Erreichbarkeit (Pointer existiert) + Eval, kein Lossless. Formulierung in §1.2 Ziel 2
  anpassen und QG-2 um „entfernte Abschnitte sind über existierende Pointer erreichbar" ergänzen (analog L2).
- **H-10: Unbelegte Annahme zu `_GOLDEN_ROLE_COUNT`.** „Unverändert" (IC-28 Nr. 4) ist unbelegt
  (`tests/test_template_slimming_equivalence.py:84` = 58, Korpus eingefroren). Der Planer prüft, ob der Golden-Test
  neue aktive Rollen gegen den eingefrorenen Korpus abgleicht.

## 3. Positiv bestätigt (Stichprobe gegen Code)

| Behauptung | Beleg |
|---|---|
| Reflection-Override-Leak (F-26) | `scripts/lib/config.py:1817-1821` liest `agent_meta_root/.meta-config/project.yaml`; Default `MAX_ITERATIONS="3"` `:1814` |
| Pipeline-Validierung gegen Rohmenge (F-23) | `config.py:1853-1857` |
| `PROJECT_SPECIFIC_AGENTS` hart `""` (F-25) | `config.py:1712-1714` |
| Builder überschreibt `ORCHESTRATOR_STRICT`/`UNKNOWN_FALLBACK_*` | `config.py:1493, 1580-1587` |
| Lazy-Skill-Writer nur für `has_rules: false` (F-41) | `scripts/lib/rules.py:305` |
| Agent-Name-Suffix (F-13) | `agent_sync.py:892` `Path(filename).stem` |
| Tote Gate-Variablen whitelisted (F-24) | `variables.py:298` |
| Mammouth `settings_file`, Codex `sandbox_mode`, Gemini `commands_dir` | `ai-providers.yaml:534, 668, 147` |
| `_select_examples` | `delegation_table.py:134` |
| `KNOWN_KEYWORD_OVERLAPS` | `tests/test_routing_overlap.py:28` |
| Pins 92 / 88-3-1 | `tests/test_role_addressability_coverage.py:22-23` |
| `hooks.enabled-but-not-registered` existiert | `scripts/lib/consistency/hook_drift.py:184` |
| `analyze_roundtrip`, `order_changed` | `scripts/lib/yaml_roundtrip.py:164-181` |
| `_IDENTITY_FALLBACKS`/`_CONDITIONAL_FALSE_FLAGS`; Szenario-`-x`-Prüfung | `standalone.py:54, 119`; `tests/scenarios/run.sh:76` |
| Provider-Agnostik der Spec | keine `if provider == …`-Logik vorgesehen; Registry verbietet Identitäts-Prädikate; IC-32 leitet Namen aus Daten ab: konform |

## 4. Threat-Model (4 Fragen)

Kein öffentliches Feature (Entwickler-Werkzeug). Vereinfachte Prüfung, aber vollständig, weil der Optimizer
Nutzer-Config schreibt.

### `sync.py --doctor` / `meta-doctor`

1. **Was wird gebaut?** Ein deterministischer Runner über generierte Artefakte, `sync.log`, Hash-Dateien und
   Registry, plus eine LLM-Rolle mit Bash. Er speichert keine Daten außer `.tmp/` und hat keine Auth.
   Eingaben stammen aus Projekt und Framework.
2. **Was kann schiefgehen?**
   - `command`-Detektor startet einen nicht read-only Unterbefehl (`--deactivation-status`: überschreibt `sync.log`
     und Env-Skripte, B-4).
   - Self-Hosting-Schemaschreibzugriff vor dem Handler (B-4).
   - Registry-Einträge aus einer nicht vertrauenswürdigen Quelle (W-7).
   - Prompt-Injection über zitierte Artefaktinhalte in Findings.
   - Bash-Schreibzugriffe der Rolle auf Providern ohne Durchsetzung (F-32).
   - Hängende Subprozesse: `timeout_s` vorhanden, Default-Wert fehlt.
3. **Gegenmaßnahmen (vorhanden):** argv-Allowlist ohne Shell, AC-39-Hash-Snapshot, Severity-Deckel, Fail-soft-Loader.
   **Fehlt:** B-4-Korrekturen, Registry-Quellenbindung, Message-Sanitizing, Default-Timeout, Bash-freie Alternative (W-7).
4. **Konsequenzen:** gering bis mittel. Der Befund wird verfälscht (überschriebenes `sync.log`), unbeabsichtigte
   Dateiänderungen landen im Arbeitsbaum. Kein Sicherheitsbruch nach außen.

### `sync.py --optimize-config` / `--apply-config-patch` / `meta-optimizer`

1. **Was wird gebaut?** Analyse plus ein Applier, der `.meta-config/project.yaml` und Relokationsziele schreibt.
   Die Freigabe läuft über eine Agentenkette (`meta-optimizer` → Nutzer → `agent-meta-manager`).
2. **Was kann schiefgehen?**
   - Inhaltsverlust von Variablen inaktiver Rollen/Provider (B-1).
   - Kommentarverlust durch Re-Fill beim nächsten Sync (B-2).
   - Stille Änderung sicherheitsrelevanter Laufzeit-Keys (`repo_containment`, `auto_commit`) über manipulierte
     Hunks (B-3).
   - Überschreiben bestehender `-ext.md` bzw. Pfade außerhalb des Projekts (W-4).
   - Agenten-Nachricht als vermeintliche Nutzerfreigabe (W-7).
   - Veralteter Vorschlag (durch Hash abgedeckt).
3. **Gegenmaßnahmen (vorhanden):** Hash-Bindung, atomares Schreiben, Roundtrip-Guard, `--accept` für
   nicht-deterministische Kandidaten, Verbot von `--fill-defaults`/`yaml.dump`.
   **Fehlt:**
   - Neuberechnung statt Hunk-Vertrauen und Remove-only-Prüfung (B-3).
   - Universe- bzw. Static-Reference-Prüfung (B-1).
   - Ausschluss der Auto-Fill-Keys (B-2).
   - Pfadgrenzen und Append-only für Ziele (W-4).
   - Protokoll der Freigabe; Backup `project.yaml.bak` im Proposal-Verzeichnis.
4. **Konsequenzen:** mittel bis hoch. Nutzerautorierte Konfiguration und Kommentare gehen verloren,
   Containment- oder Commit-Regeln werden unbemerkt abgeschwächt. Das widerspricht direkt dem Ziel 8 („verlustfrei").

## 5. Verdikt

**REVISE** (CHANGES_REQUESTED). Begründung: B-1…B-3 widerlegen die Verlustfreiheits-Garantie des Optimizers in der
spezifizierten Form. B-4 widerlegt die Read-only-Garantie des Doctors anhand des zitierten Codes. B-5 macht ein
Phase-0-AC unerfüllbar. B-6 lässt Phase-0-ACs ohne definierte Semantik. Profile (§4.1–4.3, IC-01…IC-12) und
Active-Set (§4.4, IC-17…IC-19) sind konzeptionell tragfähig. Sie brauchen nur W-1/W-2 und können nach Aufteilung (W-9)
vorab freigegeben werden.

Für die Freigabe erforderlich: B-1…B-6 behoben. W-1, W-2, W-5, W-7 eingearbeitet oder mit Begründung als Risiko
geführt. H-1/H-2 korrigiert.

## 6. Punkte mit Nutzerentscheidung

1. **B-5 / Q17:** Wie wird `meta-doctor` in Phase 0 eingeführt: (a) AC-01 mit Ausnahmeliste,
   (b) eigener Phase-0b-PR mit Golden-Rebaseline, (c) Aktivierungsgruppe mit Default aus?
2. **B-1:** Wie werden Variablen behandelt, die nur im aktuellen Active Set wirkungslos sind: nie deterministisch
   (`inactive-scope`, nur mit `--accept`) oder ganz ausgeschlossen?
3. **B-2/B-3:** Den Optimizer-Kandidatenraum auf `variables.*` begrenzen (Empfehlung) oder strukturelle Keys mit
   Denylist zulassen?
4. **W-9:** Spec in vier Specs aufteilen oder Teil-Approval je Abschnitt?
5. **W-7:** `meta-doctor`/`meta-optimizer` mit Bash (heutiger Entwurf) oder Bash-frei mit Datei-Handoff?
6. **W-5 / Q20:** Doctor-Exit-Politik in Phase 0 (Severity-Regel für `finding-ref`; `--strict` nur in der agent-meta-CI?).
7. **W-3:** Eval-Toleranzmodell (fixe 1 pp vs. σ-basiert/gepaarter Test) und Batch-Eval statt Eval je Rolle.
8. Weiterhin offen aus der Spec: Q16 (projekt-spezifische Rollen), Q9 (`template-auditor`), Q23
   (`CODE_QUALITY_RULES`), Q33/Q34 (Runtime-Verifikation Gemini-Commands/ZCode-Autoload; nicht blockierend).
