# Review — Orchestrator `mode` × `topology` (#1190)

> Reviewer: `concept-reviewer` · Datum: 2026-11-09 · Modus: Spec-/Plan-Review (read-only)
> Gegenstand: `docs/specs/2026-11-09-orchestrator-mode-topology-design.md` (862 Zeilen)
> und `docs/plans/2026-11-09-orchestrator-mode-topology-plan.md` (846 Zeilen)
> Branch `docs/1190-orchestrator-topology`, HEAD `aaed14c2`
> Ergebnis: **CHANGES_REQUESTED** — 3 BLOCKER, 9 MAJOR, 6 MINOR, 2 NIT.
> **Review 1 (vor Revision 2) — alle Befunde in Spec/Plan Rev. 2 eingearbeitet.**

## Scope

Geprüft: Beantwortung von Q1–Q5 und der Matrix (4 Surfaces × 6 Kombinationen);
Belastbarkeit von D-Q1…D-Q5 **gegen den Code**; Übersetzung von G1–G9 in
Soll-Verhalten + ACs + Tasks; Ausführbarkeit von T1–T18 (Datei/Test/Verifikation,
Abhängigkeiten, Meilenstein-Gates, Byte-Identität); Teststrategie (Matrix,
Szenarien 100–104, #1182, Registry); Namenskonsistenz Spec↔Plan; Governance
(Convention boundary, `subagent`/`main-chat`-Regression); Scope-Abgrenzung zu
#1077/#1007; Zuordnung der elf Doku-Befunde.

Nicht im Scope: Implementierung, Formulierung, Issue-Kritik, Runtime-Wahrheit
der Provider-Capability-Zellen.

**Verifikationsbasis:** jede tragende Fundstelle wurde in dieser Runde im Repo
gelesen (`datei:zeile`). Die Vorlage der 24-Zellen-Matrix (§12) wurde gegen
`config/provider-capabilities.yaml` und `docs/concepts/runtime-gate-tiers.md`
stichprobenartig geprüft, nicht zellweise neu hergeleitet.

**Einschränkung:** Der Issue-Body #1190 lag nicht vor (`.tmp/issue-dump-1190/`
existiert nicht — siehe RVW-1190-11). Q1–Q5 sind deshalb nur gegen die
Spec-interne Aufgabenstellung prüfbar; die Hypothesen H1–H3 nur gegen die
Spec (RVW-1190-19).

---

## Findings — BLOCKER

### RVW-1190-01 · Dimension: Logik / Belastbarkeit — D-Q5 beruht auf einer falschen Prämisse

**Spec §4-D-Q5 (Z. 315-343), §6.2, AC-12/AC-13; Plan T13 (Z. 444-464).**

Die Entscheidung begründet das INFO damit, dass `direct-dispatch-enabled`
„ausschließlich im `advisory`-Zweig gerendert" werde
(`rules/1-generic/use-orchestrator.md:25-31`). Das ist falsch: derselbe Key
gated `agents/1-generic/orchestrator.md:203-205`
(`{{#if DIRECT_DISPATCH_ENABLED}}{{DIRECT_DISPATCH_SECTION}}{{/if}}`), also die
Sektion „Task decomposition & delegation" des **Orchestrator-Agenten**, und
`config.py:2090-2101` baut `DIRECT_DISPATCH_SECTION` modusunabhängig. Unter
`strict` wird der Orchestrator emittiert (als Session-Einstieg) und die Sektion
gerendert — der Key ist dort **wirksam**, nicht inert. Wirklich inert ist er
unter `mode: main-chat` (Rolle wird nicht emittiert).

Folgen: (a) Der Check feuert in diesem Repo (Key gesetzt, `mode: strict`) auf
einen funktionierenden Key; (b) der gepinnte Text gibt schädlichen Rat
(„Remove the key or switch to `mode: advisory`") — Entfernen ändert die
Agent-Ausgabe, der Wechsel schaltet zusätzlich `strict` ab; (c) AC-12 würde den
Fehlschluss als Test festschreiben.

**Fix:** Prämisse in §4-D-Q5 korrigieren; Bedingung auf
`mode == "main-chat"` ∧ Key präsent umstellen (dort ist der Key nachweislich
wirkungslos, weil Rolle und advisory-Zweig beide entfallen) — oder das Finding
ersatzlos streichen. Gepinnten Text, §6.2, AC-12/AC-13 und T13 entsprechend
ändern. Falls der Check bei `main-chat` bleibt: `--validate` auf diesem Repo
darf dann kein `[INF]` zeigen (Key gesetzt, Modus `strict`).

### RVW-1190-02 · Dimension: Logik / Konsistenz — G1 behauptet provider-agnostisch „es gibt keinen Spawn-Kanal", was für Claude falsch ist

**Spec §5-G1 (Z. 351-375), AC-3, §6.5, §12.4; Plan T7 (Z. 302-327).**

Der neue `primary`-Text behauptet: „Der Orchestrator ist in diesem Projekt der
Session-Einstieg; es gibt keinen Spawn-Kanal. Eine Session, die im Main Chat
läuft, KANN nicht delegieren." Das gilt für OpenCode (`mode: primary` im
Agent-Frontmatter, `.opencode/agents/orchestrator.md:8`; Provider-Zelle
`topology_support.hybrid: false` mit dieser Begründung). Es gilt **nicht** für
Claude: `topology_support.primary: true`
(`config/provider-capabilities.yaml:148`), `main_agent_selectable: true`
(`:144`), kein `mode: primary`-Konzept. Genau deshalb führt dieselbe Spec
`strict × primary` auf Claude als `ALLOWED` mit Hop 0 und `hook`-Tier
(§12.4, Z. 812) — der Main Chat **kann** dort spawnen, und das ist der legale
Kanal für eine Session, die nicht im Orchestrator startet.

Mit AC-3 wird dieser Satz als Teilstring für **jede** effektive `primary`-Position
gepinnt. Auf Claude entsteht damit erneut eine Regel, die den einzigen legalen
Kanal verbietet — exakt der Defekt aus §1.1, den #1190 beheben soll.

**Fix:** Satz von der Capability auf die Position umstellen, z. B. „In diesem
Projekt ist der `orchestrator` der Session-Einstieg (`strict` verlangt das).
Eine Session, die im Main Chat läuft, erfüllt das Gate nicht: sie darf nicht
selbst editieren (`# CRITICAL GATE`) und muss entweder im `orchestrator`
starten oder der Nutzer schaltet `orchestrator.mode: main-chat`." Wenn die
„kein Spawn-Kanal"-Aussage erhalten bleiben soll, muss sie datengetrieben an
eine Capability gebunden werden (z. B. „`primary`-Rolle wird mit
`mode: primary` emittiert") und darf nicht an `EFFECTIVE_PRIMARY` allein hängen.
AC-3, T7-Test und §12.4 (Caveat „Hop 0 nur bei nicht-spawbbarer Entry-Rolle")
mitziehen.

### RVW-1190-03 · Dimension: Ausführbarkeit — T14 adressiert die falsche Funktion; das `TopologyResolution`-Objekt ist dort nicht verfügbar

**Spec §5-G7 (Z. 457-476), AC-22/AC-23; Plan T14 (Z. 466-494), §6.2, §3-File-Map.**

Die Defektstellen (`isolation.py:1826-1830`, `:1457`) sind korrekt benannt. Die
*Ursache* wird aber der falschen Funktion zugeschrieben:

- `:824-862` (Auflösung des `TopologyResolution`) und `:869-872` (Aufruf **mit**
  `topology=`) liegen in `_sync_opencode_runtime_gate` (def `:725`). Dieser Pfad
  übergibt die Topologie **heute schon** — Spec §5-G7 Nr. 1 beschreibt
  bestehendes Verhalten als Fix.
- `:1826-1830` und `:1881-1889` liegen in `reconcile_opencode_surface_gate`
  (def `:1751`). Diese Funktion hat **kein** Topologie-Objekt; ihre Signatur
  (`project_root, config, provider, provider_config, agent_meta_root, log,
  dry_run, *, active_set`) wird von `sync_pipeline.py:1598-1602` und
  `cli_commands.py:344` aufgerufen.

Damit ist T14 in der vorliegenden Form nicht ausführbar: Entweder löst
`reconcile_opencode_surface_gate` die Topologie **selbst** erneut auf (dritter
Auflösungspunkt pro Provider und Lauf — Widerspruch zu R-3 und zur
Global-Constraint „Auflösung je Provider genau einmal pro Lauf"), oder die
Funktion bekommt `topology=` als Keyword und die zwei Aufrufer werden
mitgeändert — beide Dateien fehlen in der File-Structure-Map und in T14s
„Datei"-Zeile.

**Fix:** §5-G7 und T14 auf `reconcile_opencode_surface_gate` umschreiben;
`topology=None` in §6.2 als Signaturerweiterung aufnehmen; `sync_pipeline.py`
und `cli_commands.py` in T14s Datei- und Testliste ergänzen (Durchreichung
statt Neuresolution). AC-23 auf die drei realen Aufrufstellen beziehen
(siehe RVW-1190-16).

---

## Findings — MAJOR

### RVW-1190-04 · Dimension: Konsistenz — AC-21 und T13 widersprechen sich bei der Ablage des INFO-Checks

**Spec §5-G6 (Z. 442-455), AC-21 (Z. 660-662); Plan T13 (Z. 446), §3-File-Map.**

AC-21 fordert: „die drei neuen Checks existieren **ausschließlich** in
`consistency/topology.py`". T13 legt
`orchestrator-strict.direct-dispatch-inert` in
`consistency/orchestrator_strict.py:36-39, :182-250` ab. Der Test aus AC-21
würde gegen die Plan-Umsetzung fehlschlagen; umgekehrt ist die Ablage in
`orchestrator_strict.py` sachlich richtig (Namespace `orchestrator-strict.`,
bestehende Konstante `_DISPATCH…`-Nachbarschaft).

**Fix:** AC-21 auf „zwei Checks in `consistency/topology.py`, einer in
`consistency/orchestrator_strict.py`" präzisieren; §5-G6 „Ort" entsprechend
teilen.

### RVW-1190-05 · Dimension: Logik — Einstiegshinweis (G5/T10/K-4) ist für geteilte Kontextdateien nicht ehrlich

**Spec §5-G5 (Z. 431-440), AC-20; Plan T10 (Z. 376-396), K-4 (Z. 821), T5 (Z. 269-282).**

`AGENTS.md` wird von mehreren Providern nacheinander geschrieben und muss
deshalb **identisch** rendern (Kommentar `context.py:721-722`; Oszillationsschutz
`_shared_context_users`, `:2445-2455`; `EMIT_AGENT_ROSTER`-Muster `:2522-2533`).
K-4 löst das mit „primary-Hinweis iff ∃ Provider mit `effective == 'primary'`".
Das ist deterministisch, aber inhaltlich falsch für die übrigen Leser: in diesem
Repo leitet Opencode `primary` ab, Gemini `subagent`
(`provider-capabilities.yaml:263-264`) — der Render behauptet dann für
Gemini-Sessions „Diese Session startet im `orchestrator`-Agenten". Genau diese
Art von Falschaussage ist der Gegenstand von #1190.

Dasselbe ungelöst: T5 verlangt für den Managed Block „zwei Sharer mit
unterschiedlicher Effektivposition ⇒ **ein** deterministischer Block", ohne zu
sagen, welcher Inhalt gewinnt (safe side? neutral?). G5/AC-20 kennen den
Shared-File-Fall überhaupt nicht.

**Fix:** Geteilte Dateien dürfen keine positionsspezifische Aussage tragen.
Konkret: provider-neutraler Text („Einstiegspunkt: `orchestrator` — ob als
Session-Einstieg oder als Subagent, hängt von `orchestrator.topology` ab; siehe
`use-orchestrator.md`"), oder die „safe side"-Regel explizit definieren (kein
Fall darf mehr behaupten, als für alle Sharer gilt). §5-G5/G2, AC-20 und T10
um den Mixed-Provider-Fall ergänzen (Test: zwei Sharer, unterschiedliche
Effektivposition, Assertion auf den tatsächlich gerenderten Text).

### RVW-1190-06 · Dimension: Ausführbarkeit — die `--check`-Verifikationen von T6–T9 sind in diesem Repo nicht erfüllbar

**Plan T6-T9 (jeweils „Verifikation"), §2 Global Constraints (Z. 60-62), M1/M3/M8.**

`sync --check` bedeutet: „exit 1 if any file would be written/changed"
(`scripts/sync.py:334-338`). Dieses Repo hat kein `topology`, leitet aber
`primary` ab (`primary-role` gesetzt + Rolle im ActiveSet,
`config.py`/`topology.py:135-140`). Sobald T6–T9 aktiv sind, ändern sich
gerenderte Artefakte (Agent-Templates über T8, `a2a-delegation-gates`, der
Singleton-Block, der Einstiegshinweis) → `--check` meldet Drift, bis ein echter
`sync` die Dateien neu schreibt. Kein Task enthält diesen Schritt, und die
File-Structure-Map markiert `AGENTS.md` und `.claude/rules/use-orchestrator.md`
ausdrücklich als „**nicht** editieren — generiert". T7 formuliert das Problem
sogar selbst („die Regel *darf* sich hier ändern"), liefert aber keine
Regeneration.

**Fix:** Pro betroffenem Task (oder als eigener Task vor T18) einen Schritt
„`python3 scripts/sync.py` ausführen, die regenerierten Artefakte prüfen und
committen" aufnehmen; alternativ alle `--check`-Gates gegen einen
Fixture-Consumer (Temp-Test-Repo) formulieren und das ausdrücklich sagen. Bis
dahin sind M1/M3/M8 und T18s Abschluss-Gate nicht einfahrbar.

### RVW-1190-07 · Dimension: Belastbarkeit — T4/T5 lösen die Effektivtopologie ohne den per-Sync-`ActiveSet` auf

**Plan T4 (Z. 249-267), T5 (Z. 269-282), §6.2; Code: `rules.py:281-288`, `context.py:2575-2581`, `topology.py:135-140`.**

`_build_provider_vars` bekommt `active_set` (T6, korrekt). `rules._merged_rule_vars`
und `context._build_managed_block` rufen `resolve_topology` **ohne** `active_set`
auf; `_derive` fällt dann auf die leere Menge zurück und liefert immer
`subagent`. Der Plan lässt den Helfer den ActiveSet „lazy" selbst berechnen —
pro Aufruf. `_merged_rule_vars` wird zweimal pro Provider und Lauf aufgerufen
(`rules.py:519`, `:607`), der Managed Block einmal → bis zu drei zusätzliche
`compute_active_set`-Läufe pro Provider und Sync, und potenziell ein anderer
`effective`-Wert als in der Emission (`provider_transform.py:480-493`,
`agent_sync.py:1427-1430`, die den geteilten Set benutzen). Das ist genau
Risiko P-1/R-3, gegen das der Plan argumentiert.

**Fix:** `active_set` als Pflicht-Keyword von `_provider_topology_flags`
(dokumentiert „same set as emission"), Durchreichung aus
`sync_pipeline._sync_stage_per_provider` bzw. aus den `sync_rules`/
`_sync_managed_block_context`-Aufrufern; AC ergänzen: „Emission und alle drei
Render-Seams benutzen denselben `ActiveSet`" (Test mit zwei Providern und
einem Rolle-nicht-im-Set-Fall).

### RVW-1190-08 · Dimension: Konsistenz — K-1 und K-2 ändern Spec-Contracts, ohne dass die Spec das trägt

**Plan §13 (Z. 818-819); Spec §5-G2 (Z. 390), AC-1 (Z. 568-571).**

- **K-1:** Spec-Formel `ORCH_TOPOLOGY_EFFECTIVE_EXPLICIT := effective != declared
  or source != "derived"` ist bei `declared is None` immer `true` (weil
  `"primary" != None`) — die Plan-Kritik ist sachlich richtig. Aber der Plan
  ersetzt damit einen in §5-G2, §6.3 und AC-17 gepinnten Vertrag durch
  `source != "derived"`, und zwar erst „vor T8" durch eine Bestätigung, die
  niemand geben kann, solange die Spec `DRAFT` ist.
- **K-2:** AC-1 nennt `sync --check` als Kanal; `--check` führt keine
  Consistency-Checks aus (einziger Aufrufer ist
  `scripts/consistency-check.py:264-267`). Der Plan verschiebt den AC auf
  `--validate`/`consistency-check`. Richtig erkannt, aber wieder eine
  AC-Änderung im Plan statt in der Spec.

**Fix:** Spec auf Revision 2 heben: §5-G2-Formel korrigieren, AC-1-Kanal
korrigieren; im Plan K-1/K-2 zu „in Spec Rev. 2 übernommen" degradieren.
Solange beide Punkte offen sind, ist die Spec nicht `APPROVED`-fähig — und der
Plan verweist selbst darauf, dass er erst danach startet.

### RVW-1190-09 · Dimension: Vollständigkeit / Governance — der Plan erfüllt die Pflichtsektionen nicht und hebelt damit den eigenen Approval-Gate aus

**Plan Kopf (Z. 1-33), §2, §3; Code: `consistency/spec_plan.py:31-39`, `:79-87`, `:479-507`.**

`REQUIRED_PLAN_SECTIONS` verlangt `**Goal:**`, `**Architecture:**`,
`**Tech Stack:**`, `**Spec:**`, `## Global Constraints`, `## File Structure`,
`pipeline_stages`. Der Plan hat `pipeline_stages` ✓ und „## 2. Global
Constraints" ✓; es fehlen `**Goal:**`, `**Architecture:**`, `**Tech Stack:**`,
`**Spec:**` und `## File Structure` („## 3. File-Structure-Map" matcht nicht).

Gravierender als die Warnungen: `_check_approval_markers` (`:479-507`) sucht
`**Spec:**`; findet es keins, **überspringt** sie die Prüfung. Der Plan
referenziert die Spec als `> **Spec (verbindlich):**` — der Regex
(`_SPEC_FIELD_RE`, `:79-81`) matcht das nicht. Folge: Der einzige mechanische
Schutz gegen „18 Tasks gegen eine DRAFT-Spec" (ERROR
`spec_plan_approval_marker`) ist deaktiviert — in einem Vorhaben, das Regeln
durchsetzbar machen soll.

**Fix:** Kopf auf die Pflichtfelder umstellen, insbesondere
`**Spec:** docs/specs/2026-11-09-orchestrator-mode-topology-design.md` wörtlich,
plus `**Goal:**`, `**Architecture:**`, `**Tech Stack:**` und `## File Structure`
(Überschrift der Map anpassen). Danach greift der Gate wie beabsichtigt.
Hinweis zusätzlich in §13 aufnehmen: `_classify` (`:318-323`) behandelt
`*-spec.md` als `plan` — die Spec wird also gegen **Plan**-Sektionen geprüft,
und `specs` bleibt leer, sodass die Traceability-Schleife über `specs`
(`:425-439`) für dieses Paar nie läuft. Der §13-Hinweis nennt nur die
Abschnitts-Warnungen, nicht diese Folge.

### RVW-1190-10 · Dimension: Prüfbarkeit — AC-22 nennt einen Kanal, der auf v2 strukturell nicht existieren kann

**Spec §5-G7 (Z. 474-476), AC-22 (Z. 663-667); Plan T14 (Z. 471-483); Code: `consistency/topology.py:94-105`, `:365-382`.**

AC-22 fordert für v2 + `strict` + `subagent` „genau eine
`orchestrator-topology.gate-inactive`-WARN". Der Consistency-Check dieses
Namens ist an Tier `permission` gebunden (`_gate_wanted` → `:103-105`); v2 ist
Tier `plugin`, also entsteht dort **kein Finding**. Was entsteht, ist die
Log-Warnung aus `reconcile_opencode_surface_gate` (`:1881-1889`, Zeile 6). Der
AC vermischt also zwei Kanäle (Finding vs. Sync-Log) — dieselbe Unschärfe, die
der Plan für AC-1 als K-2 benennt, hier aber nicht adressiert. Zusätzlich ist
der neue Warntext nirgends gepinnt, obwohl AC-22 auf sein Vorkommen prüft.

Auf v1 existiert der ID doppelt (Log-Warnung `isolation.py:955-959` **und**
Finding `consistency/topology.py:370-382`) — AC-5 fordert „genau eine".

**Fix:** Kanal explizit benennen („eine Log-Warnung im Sync-Kanal; kein
Consistency-Finding auf v2, weil `_gate_wanted` Tier-`permission`-gebunden
ist"), den Ersatztext als gepinnten Teilstring in §6.4 aufnehmen, und für v1
festlegen, ob Log + Finding als eine oder zwei Meldungen gelten (oder die
Dedup herstellen).

### RVW-1190-11 · Dimension: Prüfbarkeit — zitierte Baseline-Artefakte existieren nicht

**Plan Voraussetzungen 3 (Z. 30-32), M0 (Z. 155), T13-Verifikation (Z. 462-463).**

Zitiert werden `.tmp/issue-dump-1190/baseline-validate.txt:27` (`EXIT=0`) und
`baseline-check.txt:7` (`DRY-RUN — no files will be written`). `.tmp/` existiert
im Repo nicht (kein Treffer, auch nicht versteckt). Zusätzlich widersprechen
sich Voraussetzung 3 („Baseline eingefroren") und M0 („Baseline einfrieren
(keine Änderung)") — der Plan setzt voraus, was er erst erzeugen will.
Ebenfalls unverifiziert: „`94`–`99` für die Config-Welle reserviert" — im Repo
nicht belegbar (Registry listet bis `93`, `registry.md:127-132`).

**Fix:** Dateizitate entfernen und M0 als echten ersten Schritt führen (Baseline
erzeugen, Hashes/EXIT-Codes im Plan dokumentieren, erst dann zitieren). Die
94–99-Reservierung entweder mit Quelle versehen oder als `ISSUE` (nach der
eigenen Legende) markieren — `100`–`104` ist auch ohne Reservierung kollisionsfrei.

### RVW-1190-12 · Dimension: Logik — die dritte G4-Variante ist mit der geplanten Signatur nicht erreichbar; zwei Flags haben keinen Konsumenten

**Spec §5-G2 (Z. 392), §5-G4 (Z. 417-429); Plan T9 (Z. 356-374), §6.2, T1/T2.**

`_singleton_constraint_block(effective: str) -> str` soll drei Varianten
liefern (`primary` / `subagent` / „inert"). `ORCH_TOPOLOGY_EFFECTIVE` ist per
Invariante **nie** leer oder `"none"` (§5-G2) — aus `effective` allein ist die
inert-Variante also nicht ableitbar. `ORCH_TOPOLOGY_INERT` und
`ORCH_TOPOLOGY_EFFECTIVE_SOURCE` werden in T1/T2/AC-15 registriert, aber von
keinem Template und keinem Task konsumiert (T9 nimmt `mode == main-chat`
außerhalb der Signatur an).

**Fix:** Signatur `_singleton_constraint_block(effective: str, *,
inert: bool)` (oder Modus durchreichen) und in T9 explizit als Inert-Quelle
benennen; entweder `ORCH_TOPOLOGY_INERT` dort (und in G5) verdrahten oder aus
dem Flag-Set und AC-15 streichen. `ORCH_TOPOLOGY_EFFECTIVE_SOURCE` als
Doku-/Audit-Flag deklarieren (sonst „totes Flag" mit Registrierungspflicht).

---

## Findings — MINOR

### RVW-1190-13 · Szenario 103 hat keinen Mechanismus

**Plan T17 (Z. 553-574), M8 (Z. 163), §7.5.**

`tests/scenarios/run.sh` kennt kein SKIP: Exit 0 der Assertion = `PASS`
(`run.sh:231`), sonst `FAIL`. Eine Config-Datei, die `run.sh 10` matcht, wird
also ausgeführt. T17 verspricht „4× PASS + 1× SKIP", M8 „5× PASS" — beide
Aussagen sind mit dem Harness unvereinbar, solange 103 wegen #1182 nicht läuft.

**Fix:** Entweder 103 aus dem Match nehmen (Namensschema außerhalb `10*`, im
Katalog als `BLOCKED` geführt) oder die Skip-Konvention in `run.sh` als
expliziten Task aufnehmen; M8 auf das tatsächliche Ergebnis (4 PASS) korrigieren.

### RVW-1190-14 · AC-24 verlangt eine Abdeckung, die kein Task besitzt

**Spec AC-24 (Z. 672-675); Plan §10 (Z. 752), T10.**

AC-24 fordert Abdeckung von „`ROLE_ORCHESTRATOR_ACTIVE` unter `main-chat`".
Kein Task legt diesen Test an; T10 nennt
`tests/test_orchestrator_active_set_prose.py` nur als Regressionslauf
(„0 failed"). Damit ist AC-24 nicht erfüllbar.

**Fix:** Test in T10 (oder T11) benennen und in der AC→Task-Tabelle ergänzen.
Gegenprobe der übrigen AC-24-Elemente ergab vollständige Zuordnung.

### RVW-1190-15 · B-9 stützt sich auf einen Render, der so nicht existiert

**Spec §3.3 letzte Zeile (Z. 120), §9.1 B-9 (Z. 707); Plan T16.**

`.claude/rules/use-orchestrator.md` enthält **kein** „runtime-partially
enforced": Zeile 1 ist `# CRITICAL GATE`, Zeile 2 „… Keine Ausnahmen.", Zeilen
3-4 sind der PARTIAL-Prosatext. Beide gerenderten Fassungen (`AGENTS.md:140-141`
und `.claude/rules/use-orchestrator.md:1-4`) tragen also denselben
Impressiv-Satz — der behauptete Widerspruch „zwei Wortlaute" besteht in dieser
Form nicht. T16s „beide über G1 vereinheitlichen" hat damit kein Ziel.

**Fix:** B-9 auf den tatsächlichen Unterschied umstellen (fehlender Tier-Suffix
bei vorhandenem PARTIAL-Absatz = widersprüchlicher Render innerhalb einer
Datei, was auf einen zweiten GATE_*-Treffer hindeutet) oder den Befund
streichen und die Elf-Liste auf zehn reduzieren.

### RVW-1190-16 · AC-23-Ausnahmen sind unpräzise

**Spec AC-23 (Z. 668-671).** Es gibt drei Aufrufe von `_opencode_entry_point`
(`isolation.py:869`, `:1457`, `:1827`). Die genannten Ausnahmen
(`rollback_only`, `config is None`) beschreiben den **Wert** am Aufruf `:869`,
nicht Aufrufstellen; `:1457`/`:1827` haben mit beiden nichts zu tun. Gelesen
wie geschrieben, erlaubt der AC genau die zwei Stellen, die der Fix ändern muss.

**Fix:** „Alle drei Aufrufstellen übergeben `topology=`; an `:869` darf der Wert
`None` sein, wenn `rollback_only` gilt oder `config is None` ist."

### RVW-1190-17 · Byte-Identität ist für deklarierte `primary`-Consumer nicht abgegrenzt

**Spec AC-27 (Z. 685-686); Plan §8 (Z. 694-697), T8.**

AC-27 fordert Byte-Identität für „ein unverändertes Consumer-Projekt". Ein
Consumer mit deklariertem `topology: primary` ändert aber sehr wohl seine
Agent-Texte (T8: `EFFECTIVE_PRIMARY`-Zweig ersetzt den heutigen expliziten
Zweig). Plan §8 grenzt Byte-Identität nur auf „kein `topology`-Key" ein — die
Spec sagt das nicht.

**Fix:** AC-27 und §8 auf „ohne `topology`-Key" schärfen und deklariertes
`primary` ausdrücklich als beabsichtigte Änderung führen (mit Golden-Fixture
für den neuen Text).

### RVW-1190-18 · Der Remediation-Text von D-Q1 kann in den harten Fehler laufen

**Spec §4-D-Q1 (Z. 183-189), AC-2.** „Declare `orchestrator.topology: subagent`
for this provider": auf Projekt-Scope neben `mode: main-chat` ist genau das ein
ERROR mit rc≠0 (`config.py:557-563`); legal ist nur
`orchestrator.provider-overrides.<P>.topology: subagent`
(`config.py:604-632`).

**Fix:** Im gepinnten Text die Override-Form nennen und den Projekt-Scope-Fall
als unzulässig markieren.

---

## Findings — NIT

### RVW-1190-19 · H1/H2 ohne Spur

**Spec §4-D-Q3 (H3), AC-8, §13.** Q1–Q5 sind explizit entschieden, die Matrix
liegt in 4 × 6 vor. H3 wird zweimal genannt („H3 bestätigt"), H1 und H2
kommen in der Spec nicht vor, und §13 hat keine H→Entscheidung-Zeile. Ohne den
Issue-Body ist die inhaltliche Abdeckung nicht prüfbar; die Spur fehlt aber
sicher.

**Fix:** H-Map in §13 ergänzen (H1/H2/H3 → D-Q/AC, Urteil
bestätigt/widerlegt/offen). Falls H1/H2 durch D-Q1/D-Q4 beantwortet werden, das
explizit sagen.

### RVW-1190-20 · Zahlen und Zitate im Plan

- „alle **8** neuen Namen" in `_BUILTIN_VARS` (T2, Z. 222) vs. „sieben neue
  Flags" (Spec §5-G2, AC-15; Plan §6.1). Es sind sieben.
- T9 zitiert die Injektionsbedingung als `role != "orchestrator" and can_spawn`
  (Z. 366) — tatsächlich `role != "orchestrator" and not
  role.endswith("-iteration") and can_spawn` (`agent_sync.py:985`).
- Der Singleton-Block verweist auf „Gate #5" (`agent_sync.py:981`), die
  a2a-Gates haben aber nur 1–3. Die Byte-Identität konserviert den toten
  Verweis bewusst — im Plan als bewusst übernommen markieren, sonst wirkt es
  wie ein neuer Fehler.
- Der Provider-Fehlertext „cannot run as a subagent" (Spec §1.1, G1) ist im
  Repo nirgends belegt; als `ISSUE` markieren statt als Fakt zu zitieren.

---

## Positiv (was trägt)

- Q1–Q5 sind entschieden, jede mit Kontext/Entscheidung/Alternativen/
  Konsequenzen — die geforderte Form ist eingehalten.
- Die Ableitungs- und Degradationsmechanik ist korrekt gegen den Code belegt
  (`topology.py:135-140`, `:147-183`, `:196-206`; `config.py:435-463`,
  `:538-563`; `provider_transform.py:488-499`, `:529-531`).
- §12 ist eine echte Herleitung mit Evidenz-Index; die Empfehlungen
  kollidieren nicht mit den Capability-Zellen, `hybrid` bleibt degradiert
  (#1077 wird nicht neu aufgerollt), #1007 wird nicht vorweggenommen.
- Die `main-chat`-Diagnose (D-Q1) und die Tier-Ehrlichkeit (D-Q2-Tabelle) sind
  belastbar; `_user_owned_default_agent` bleibt unverändert (AC-21-Negativfall).
- Alle elf Doku-Befunde sind einem Task zugeordnet (B-1…B-11 → T7/T8/T16);
  keine Lücke ohne Task außer RVW-1190-14.
- Die Reihenfolge T1→T18 ist azyklisch; die Meilenstein-Gates sind sinnvoll
  geschnitten (Flags → Parität → Wortlaut → Diagnostik → v2 → Matrix → Doku →
  Szenarien).

---

## Top 5

1. **RVW-1190-01 (BLOCKER)** — D-Q5 ist sachlich falsch: `direct-dispatch-enabled`
   wirkt unter `strict` über `orchestrator.md:203-205`. Der Check würde in
   diesem Repo auf einen funktionierenden Key feuern und zu seiner Entfernung
   raten. Entscheidung neu treffen (Ziel: `main-chat`), sonst streichen.
2. **RVW-1190-03 (BLOCKER)** — T14 ist nicht ausführbar: das
   `TopologyResolution` liegt in `_sync_opencode_runtime_gate`, die Defektstellen
   in `reconcile_opencode_surface_gate`; es fehlen Signaturänderung plus zwei
   Aufrufer-Dateien.
3. **RVW-1190-02 (BLOCKER)** — G1s „kein Spawn-Kanal" ist auf Claude falsch
   (§12.4 wertet dieselbe Zelle als `ALLOWED`) und würde per AC-3 gepinnt.
4. **RVW-1190-06 + RVW-1190-09 (MAJOR)** — Prüfbarkeit: `--check`-Gates sind in
   diesem Repo nicht grün zu bekommen (keine Regenerationsstufe), und der Plan
   erfüllt die Pflichtsektionen nicht, wodurch `spec_plan_approval_marker`
   (DRAFT-Spec + 18 Tasks = ERROR) stillschweigend ausfällt.
5. **RVW-1190-05 + RVW-1190-07 (MAJOR)** — Konsistenz der Render-Seams:
   geteilte Kontextdatei kann keine positionsspezifische Aussage tragen, und
   T4/T5 lösen ohne den per-Sync-`ActiveSet` auf (bis zu drei zusätzliche
   ActiveSet-Läufe pro Provider, Divergenz zur Emission).

---

## Verdikt

**CHANGES_REQUESTED.**

Die Spec beantwortet Q1–Q5 strukturell vollständig und ist methodisch sauber
belegt; der Plan ist task-für-task prüfbar und weitgehend tracebar. Drei
Entscheidungen bzw. Umsetzungsschritte tragen aber nicht: D-Q5 beruht auf einer
widerlegten Code-Annahme, G1 formuliert eine Unausführbarkeit, die auf einer
von der Spec selbst als unterstützt geführten Surface falsch ist, und T14
adressiert eine Funktion, die das benötigte Objekt nicht besitzt. Dazu kommen
zwei Prüfbarkeitsprobleme (Byte-Identität in diesem Repo, Approval-Gate
ausgehebelt) und zwei Konsistenzlücken an den Render-Seams. Nach Korrektur von
RVW-1190-01…-03 und -06…-09 ist das Paar approvbar; die MINOR/NIT-Punkte können
in derselben Überarbeitung mitlaufen.

**Governance:** Der Gate-Text wird in G1 korrekt als Regel (nicht als
Runtime-Versprechen) formuliert, der Tier-Absatz bleibt in beiden Varianten,
`CRITICAL GATE` bleibt als Heading erhalten (#1182-sicher), und `main-chat`
sowie `topology: subagent` werden nicht regressiv verändert — bis auf die
Tatsache, dass die primäre Aussage auf Claude zu stark ist (RVW-1190-02).
