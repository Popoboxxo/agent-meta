---
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: W0-7 — Eskalations-Record OQ1 — Wiki-Topics vs. docs/guides/ (offen)
status: open
revision: 0.2
related:
  - docs/plans/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation-design.md
  - docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md
  - docs/plans/2026-09-25-docs-consolidation-oq2.md
  - docs/plans/2026-09-25-docs-consolidation-oq8.md
---

# W0-7 — Eskalations-Record OQ1: `knowledge/wiki/topics/` vs. `docs/guides/` (offen)

> Eskalations-Record der Plan-Task **W0-7** („DEC-OQ1 — Wiki-Topics vs. `docs/guides/`
> (Produktentscheidung)"), Plan `PLAN-DOCS-CONSOLIDATION-2026-09-25`, Spec
> `SPEC-DOCS-CONSOLIDATION-2026-09-25` (Rev. 0.3, `status: APPROVED`).
> **Ausführende Rolle:** `documenter` (Rollen-Ownership dieses Records; die Commit-Leistung
> für W0-7 verbleibt beim `git`-Agenten).
> Stand: Branch `feat/repository-documentation-consolidation-main`, Basis `origin/main`,
> PR #839 (Draft).
> **Branch-Bestand (gemessen 2026-09-26):** `git branch --list
> 'feat/repository-documentation-consolidation*'` → **2** Zeilen — der **aktive** Wellen-Branch
> und der **überholte** Branch `feat/repository-documentation-consolidation` (divergente
> Doppelkopie der Spec-/Plan-Commits, nicht in `main`), der auf ausdrückliche **Nutzer-Vorgabe
> („nicht löschen")** erhalten bleibt. Für OQ1 **ohne Wirkung** (OQ1 ist eine Inhaltsfrage);
> Details: W0-2-Record Kapitel 7.2, offener Punkt **OP-2** dort §10.
>
> **Nachführung 2026-09-26 (Rev. 0.1 → 0.2):** Korrigiert wurde ausschließlich die
> **Zusammensetzung** der `docs/guides/`-Zählung (Fehlerklasse „error-propagating", Review-Befund
> M1): korrekt sind **32 Dateien = 30 `.md` + 1 `.yml` + 1 `project.yaml.example`**. Die
> Überschneidungspaare (**25**) und die Wiki-Unique-Themen (**15**) sind **unverändert** — beide
> zählen auf der **Wiki-Seite** und sind von der Korrektur nicht betroffen. **Keine** Änderung an
> OQ1, an den Optionen A/B/C, an der Empfehlung oder am Eskalationsinhalt.
>
> **Charakter:** Dieser Record dokumentiert eine **Eskalation**, keine Entscheidung. Er
> enthält **keine** Festlegung dazu, ob `knowledge/wiki/topics/` vollständig in `docs/guides/`
> aufgeht oder als eigenständige LLM-Aufbereitung bestehen bleibt. **OQ1 bleibt offen**
> (Spec §11.1). Die normative Quelle für den Entscheidungsstand bleibt die **Spec**; bei
> Widerspruch zwischen diesem Record und der Spec gilt die **Spec**.

## Konvention: Evidenzklassen (global für alle W0-Records)

Jede Verifikationszeile dieses Records trägt die **Evidenzklasse** — also **wie** der Wert
zustande kam. Ohne diese Angabe ist ein „✅" mehrdeutig, weil es gemessene, abgeleitete und
übernommene Werte gleich erscheinen lässt. Enum (geschlossen, genau vier Werte):

| Evidenzklasse | Bedeutung |
|---|---|
| `gemessen` | Der Wert wurde in diesem Vorhaben durch **Ausführung des Kommandos** ermittelt. |
| `gezählt ohne Shell` | Der Wert wurde mit dateisuchender Prüffunktion (**Muster + Trefferzählung**) ermittelt, ohne Shell — inhaltlich identisch zum Kommando, aber kein Shell-Lauf. |
| `aus Record X übernommen` | Der Wert stammt **unverändert** aus einem anderen Record dieses Vorhabens; die Messung ist dort ausgewiesen. |
| `nicht gemessen` | Es liegt **kein** Wert vor. Er wird **nicht** geschätzt und **nicht** erfunden; die Ausführung bleibt einer benannten Instanz vorbehalten. |

Diese Konvention gilt **global für alle sechs W0-Records** dieses Wellen-Blocks und für alle
Folgewellen: ein `✅` **ohne** Evidenzklasse ist unvollständig. In diesem Record ist **kein**
Wert `gemessen` — alle Bestandszahlen stammen aus Verzeichnis-Listing/Glob
(`gezählt ohne Shell`), und der Verifikations-Prüfbefehl ist ausdrücklich `nicht gemessen`.

## Trace-Anker

| Anker | Fundstelle | Aussage dieses Records |
|---|---|---|
| OQ1 — **offen** | Spec §11.1 (OQ1-Zeile) | Frage, Owner `main_chat`, Blockade W5; dieser Record **ändert** daran nichts |
| Empfehlung der Spec zu OQ1 | Spec §11.1 (Spalte „Empfehlung") | `docs/guides/` = SSoT, Wiki nur Unique, Duplikate → Redirect — **Empfehlung**, nicht Entscheidung |
| F6 — Guide-Führung (vier Orte) | Spec, Befundtabelle F6; Design F6 | `docs/guides/`, `docs/howto/`, `howto/configs/`, `knowledge/wiki/topics/` — die Führungsfrage ist der Gegenstand von OQ1 |
| NG-1 — keine inhaltliche Neuschreibung | Spec §2.2 (Nicht-Ziele) | Migrationswellen sind `git mv` + Marker + Annotationszeilen; Inhaltsarbeit ist eigene REQ |
| NFA-08 — Blast Radius | Spec §8 | begrenzt `docs/`, `knowledge/wiki/`, `README.md`, `ARCHITECTURE.md`; `knowledge/sources/` bleibt unberührt |
| AC-31 — Additivität der Wiki-Annotation | Spec, Akzeptanzkriterien M3; Spec §9.2 (W5) | W5-3 annotiert **additiv** (`derived-from` / `derived-at`), migriert nichts |
| IC-03 / V7 | Spec §5 | Architektur-Redirects und Staleness-Auswertung der annotierten Wiki-Seiten |
| FI-4 — Folge-REQ | Spec, Follow-up-Impacts (FI-4) | „Inhaltliche Konsolidierung von `knowledge/wiki/topics/` ↔ `docs/guides/`" — **OQ1**, Produktentscheidung |
| W5-1 / W5-3 (Abhängigkeit) | Plan, Wellen-Kapitel W5 (jeweils „Depends on") | beide führen **W0-7** als Abhängigkeit; W5-2 folgt transitiv über W5-1 |
| W0-7 (Task-Text) | Plan, Wellen-Kapitel W0, Task W0-7 | Agent `orchestrator` (Eskalation an `main_chat`), Ziel-AK AC-31, kein Code |

## Zweck und Geltungsbereich

Dieser Record erfüllt die **Dokumentationshälfte** von W0-7: Er erhebt den Sachstand, benennt
die Blockade präzise und formuliert die Entscheidungsoptionen so, dass die entscheidende Instanz
ohne weitere Recherche entscheiden kann. Er nimmt **keine** Entscheidung vorweg.

Geltungsbereich ist ausschließlich das Verhältnis von `knowledge/wiki/topics/` zu `docs/guides/`.
Er ändert **keine** Datei in `knowledge/**` oder `docs/guides/` — das ist W5-Arbeit. Ebenfalls
nicht Gegenstand: `knowledge/wiki/concepts/`, `knowledge/wiki/entities/`, `knowledge/sources/`
(NG-2, unverändert) und die Guides-Auflösung `howto/` → `docs/guides/` (W5-2).

## 1. Offener Status

| Feld | Wert |
|---|---|
| **Frage (OQ1)** | Sollen `knowledge/wiki/topics/` vollständig in `docs/guides/` aufgehen, oder bleibt das Wiki als eigenständige LLM-Aufbereitung bestehen und übernimmt nur Unique-Inhalte? |
| **Entscheidungsstand** | **OFFEN** — nicht entschieden, weder in der Spec (§11.1) noch in diesem Record |
| **Datum dieses Records** | **2026-09-26** |
| **Owner** | Produktentscheidung; Spec-Owner ist `main_chat` |
| **Eskalationspfad** | `orchestrator` (Ausführungsinstanz der Task W0-7) → `main_chat` (entscheidende Instanz) |
| **Entscheidungsweg** | Produktentscheidung im Review-Loop; danach Folge-REQ (FI-4) |
| **Blockade** | Abschluss von **W5** (W5-1, W5-3, transitiv W5-2; AC-31) |
| **Von dieser Task getroffene Festlegung** | **keine inhaltliche**; verbindlich ist nur die Scope-Grenze „W5-3 annotiert additiv, migriert nichts" (aus NG-1, unabhängig von OQ1) |

**Warum der Nutzer nicht selbst entschieden hat — und warum hier nicht entschieden wird:**
OQ1 ist eine **Produktentscheidung** über den Umgang mit dem Knowledge-Wiki, nicht eine
technische Frage. Sie beantwortet nicht „wie implementieren wir", sondern „was ist der Wiki
eigentlich wert": Ist das Wiki eine zweite, LLM-gelesene Dokumentation derselben Stoffe, oder
ist es ein eigenständiger, eigener Lesefluss? Diese Frage berührt Arbeitsweise und
Wissenspflege der `knowledge-*`-Agenten und ist damit eine Eigentumsfrage des Projekts, nicht
eine Frage der Doku-Konsolidierung. Der `documenter` erhebt dazu Bestand und Optionen; die
Entscheidung liegt bei `main_chat`/Nutzer. Eine hier getroffene Festlegung würde die in der
Spec dokumentierte Eskalation umgehen.

## 2. Bestandsaufnahme (gezählt am 2026-09-26)

Alle Zahlen dieses Kapitels sind **gezählt**, nicht geschätzt (Verzeichnis-Listing und Glob über
beide Bäume). Belege stehen als `Pfad:Zeile` bzw. als Globsumme. Evidenzklasse für alle Werte
dieses Kapitels: **`gezählt ohne Shell`** (kein Shell-Lauf, kein Kommando mit Exit-Code).

### 2.1 Zählung

| Bestand | Gezählt | Gliederung |
|---|---|---|
| `knowledge/wiki/topics/` | **40 Markdown-Seiten** (Verzeichnis-Listing: 41 Einträge = 40 `.md` + `.gitkeep`) | flach, keine Unterordner |
| `docs/guides/` | **32 Dateien** = **30 `.md`** + **1 `.yml`** + **1 `project.yaml.example`** | 12 Top-Level-Einträge (8 Dateien + 4 Unterordner `ci/`, `features/`, `mcp/`, `setup/`) |
| `knowledge/wiki/index.md` | Katalogeinträge für **alle 40** Topics | OKF §6 Content-Katalog, je Eintrag Titel + Beschreibung + Tags |

**Abweichung zu einer Spec-Zahl (zu klären, nicht zu korrigieren):** Spec §11.1 und Design F6
nennen für `knowledge/wiki/topics/` den Wert **43**. Die Zählung am 2026-09-26 ergibt **40**
Markdown-Seiten. Die Differenz von 3 ist aus dem Repo heraus nicht auflösbar (unterschiedliche
Zählweise denkbar: inkl. Unterordner, inkl. anderer Dateitypen, inkl. eines früheren Stands).
Da der Merge-Umfang von OQ1 aus dieser Zahl abgeleitet würde, ist die **Bezugszahl** Teil der
Eskalation (Kapitel 5). Dieser Record ändert die Spec nicht.

### 2.2 Frontmatter-Befund: alle 40 Topics sind typisierte Ableitungen

Alle 40 Topic-Seiten tragen `type: "Guide"` (Grep über `knowledge/wiki/topics/*.md`, 40 Treffer)
und — belegbar an drei gelesenen Seiten — einen Herkunftsnachweis im Frontmatter:

- `knowledge/wiki/topics/rules.md:2` `type: "Guide"`, `:7` `resource: "../../sources/docs/guides/features/rules.md"`, `:8` `migrated_from: "docs/guides/features/rules.md"`
- `knowledge/wiki/topics/agent-composition.md:2,:7,:8` — gleiche Struktur
- `knowledge/wiki/topics/mcp-setup.md:2,:7,:8` — gleiche Struktur

Ein Grep über `migrated_from:` liefert **40 von 40** Treffern, d. h. **jede** Topic-Seite
deklariert ihr Ursprungsdokument. Verteilung der Ursprungspfade:

| Ursprungsbereich | Anzahl | Topics |
|---|---|---|
| `docs/guides/**` | **27** | der Kern von OQ1 (Kapitel 2.3, 2.6) |
| `docs/se-cascade/**` | **7** | `se-blackbox-to-whitebox`, `se-workflow`, `se-resume-session`, `se-interface-management`, `se-role-boundaries`, `se-mcp-adapters`, `se-cascade-gemini` |
| `docs/providers/**` | **3** | `provider-opencode`, `provider-gemini-cli`, `provider-multi-provider` |
| `docs/analysis/**` | **2** | `274-industry-bestpractices`, `276-architecture-robustness-audit` |
| `docs/ui/specs/**` | **1** | `models-dev-table-redesign` |

### 2.3 Überschneidungen: Wiki-Topics mit Gegenstück unter `docs/guides/` (25 Paare)

Alle 25 Paare sind durch den Namen **und** den `migrated_from:`-Pfad belegt; Wiki-Pfad
einheitlich `knowledge/wiki/topics/<name>.md`.

| # | Wiki-Topic | Gegenstück in `docs/guides/` |
|---|---|---|
| 1 | `external-skills.md` | `docs/guides/features/external-skills.md` |
| 2 | `commands.md` | `docs/guides/features/commands.md` |
| 3 | `platform-config.md` | `docs/guides/features/platform-config.md` |
| 4 | `lifecycle-triggers.md` | `docs/guides/features/lifecycle-triggers.md` |
| 5 | `agent-composition.md` | `docs/guides/features/agent-composition.md` |
| 6 | `agent-isolation.md` | `docs/guides/features/agent-isolation.md` |
| 7 | `sync-concept.md` | `docs/guides/features/sync-concept.md` |
| 8 | `provider-abstraction-layer.md` | `docs/guides/features/provider-abstraction-layer.md` |
| 9 | `rules.md` | `docs/guides/features/rules.md` |
| 10 | `agent-memory.md` | `docs/guides/features/agent-memory.md` |
| 11 | `agent-versioning.md` | `docs/guides/features/agent-versioning.md` |
| 12 | `rules-preset-optimization.md` | `docs/guides/features/rules-preset-optimization.md` |
| 13 | `consistency-check.md` | `docs/guides/features/consistency-check.md` |
| 14 | `agent-delegation-map.md` | `docs/guides/features/agent-delegation-map.md` |
| 15 | `hooks.md` | `docs/guides/features/hooks.md` |
| 16 | `config-layout.md` | `docs/guides/setup/config-layout.md` |
| 17 | `first-steps.md` | `docs/guides/setup/first-steps.md` |
| 18 | `upgrade-guide.md` | `docs/guides/setup/upgrade-guide.md` |
| 19 | `instantiate-project.md` | `docs/guides/setup/instantiate-project.md` |
| 20 | `honcho-setup.md` | `docs/guides/mcp/honcho-setup.md` |
| 21 | `mcp-setup.md` | `docs/guides/mcp-setup.md` |
| 22 | `quality-pipelines.md` | `docs/guides/quality-pipelines.md` |
| 23 | `reflection-loops.md` | `docs/guides/reflection-loops.md` |
| 24 | `test-repo-validation.md` | `docs/guides/test-repo-validation.md` |
| 25 | `sync-check.md` | `docs/guides/ci/sync-check.md` |

### 2.4 Wiki-Themen ohne Gegenstück in `docs/guides/` (15)

| # | Wiki-Topic | Ursprung laut `migrated_from:` | Bemerkung |
|---|---|---|---|
| 1 | `se-blackbox-to-whitebox.md` | `docs/se-cascade/se-blackbox-to-whitebox.md` | Ursprung existiert (`docs/se-cascade/`), liegt aber **außerhalb** von `docs/guides/` |
| 2 | `se-workflow.md` | `docs/se-cascade/se-workflow.md` | dito |
| 3 | `se-resume-session.md` | `docs/se-cascade/se-resume-session.md` | dito |
| 4 | `se-interface-management.md` | `docs/se-cascade/se-interface-management.md` | dito |
| 5 | `se-role-boundaries.md` | `docs/se-cascade/se-role-boundaries.md` | dito |
| 6 | `se-mcp-adapters.md` | `docs/se-cascade/se-mcp-adapters.md` | dito |
| 7 | `se-cascade-gemini.md` | `docs/se-cascade/SE_CASCADE_GEMINI.md` | dito (Dateiname im Ursprung abweichend) |
| 8 | `provider-opencode.md` | `docs/providers/opencode.md` | Gegenstück in `docs/providers/`, **nicht** in `docs/guides/` |
| 9 | `provider-gemini-cli.md` | `docs/providers/gemini-cli.md` | dito |
| 10 | `provider-multi-provider.md` | `docs/providers/multi-provider.md` | dito |
| 11 | `274-industry-bestpractices.md` | `docs/analysis/274-industry-bestpractices.md` | Analysedokument, kein Guide |
| 12 | `276-architecture-robustness-audit.md` | `docs/analysis/276-architecture-robustness-audit.md` | dito |
| 13 | `models-dev-table-redesign.md` | `docs/ui/specs/models-dev-table-redesign.md` | UI-Spec, kein Guide |
| 14 | `reqflow-setup.md` | `docs/guides/mcp/reqflow-setup.md` | **Ursprung existiert nicht mehr** (Glob `docs/**/reqflow*` → 0 Treffer) |
| 15 | `template-gap-analysis.md` | `docs/guides/features/template-gap-analysis.md` | **Ursprung existiert nicht mehr** (Glob `docs/**/template-gap*` → 0 Treffer) |

**Sonderfall 14 und 15:** beide Seiten sind unter `docs/guides/` **geboren**, ihre
Ursprungsdatei ist heute aber nicht im Repo. Sie sind damit die einzigen Topics, deren
„Dublette" **nicht** auflösbar ist — weder durch Redirect noch durch Merge. Sie fallen in
jeder Option (Kapitel 5) gesondert an.

### 2.5 `docs/guides/` ohne Wiki-Gegenstück (5 Markdown-Dateien + 1 `.example` + 1 YAML-Datei)

`docs/guides/context-block-inventory.md`, `docs/guides/cross-harness-dev-isolation.md`,
`docs/guides/mcp-onboarding-checklist.md`, `docs/guides/mcp/reqogniloom-setup.md`,
`docs/guides/mcp/playwright-setup.md`, `docs/guides/project.yaml.example`,
`docs/guides/ci/github-actions-sync-check.yml`.

Das sind **7 Dateien**, davon **5 `.md`** ohne Wiki-Gegenstück und **2 Nicht-Markdown-Dateien**
(`.example` + `.yml`), die nie einen Wiki-Gegenstück haben können. Zur Zählung in Kapitel 2.6:
die 5 Markdown-Dateien sind die „5 ohne Wiki-Seite" der Guide-Bilanz.

Bemerkenswert: `docs/guides/mcp/` enthält `reqogniloom-setup.md` und `playwright-setup.md`, aber
**kein** `reqflow-setup.md` — die parallel im Wiki existierende ReqFlow-Seite (Kapitel 2.4, #14)
hat also einen Guide-Nachbarn mit anderem Produktnamen, keinen echten Gegenpart.

### 2.6 Rechnerische Bilanz

40 Wiki-Themen = **25** mit Gegenstück in `docs/guides/` + **13** mit Ursprung in anderen
`docs/`-Bereichen + **2** mit verwaistem Ursprungspfad.
30 Guide-Markdown = **25** mit Wiki-Seite + **5** ohne. Hinzu kommen 2 **Nicht-Markdown**-Dateien
(`ci/github-actions-sync-check.yml`, `project.yaml.example`) → **32 Dateien** in `docs/guides/`
insgesamt.

Diese Bilanz ist eine **Bestandsaufnahme, keine Empfehlung**. Sie sagt nichts darüber, ob die
25 Paare zusammengeführt werden sollen.

## 3. Stichprobenprüfung (drei Paare)

> **Die folgenden Bewertungen sind Einschätzungen der ausführenden Rolle (`documenter`) und
> ausdrücklich keine Entscheidung.** Sie ersetzen keine Antwort von `main_chat` und begründen
> keine Scope-Festlegung. Sie liefern nur die Faktenbasis, auf der die Optionen in Kapitel 5
> aufsetzen.

### 3.1 `rules` — echte Dublette mit nachgewiesener Veraltung

| Beleg | Befund |
|---|---|
| `knowledge/wiki/topics/rules.md:76` → `:95` | Die Wiki-Seite springt in der Überschriftenliste von `## Naming-Konvention` direkt zu `## Projekt-eigene Rules erstellen`. |
| `docs/guides/features/rules.md:91-116` | Der Guide enthält zusätzlich den Abschnitt `## Skill-Channel (`channel: skill`)` mit Verweis auf `config/rules-presets.yaml` und `scripts/lib/skill_channel.py` (`:93`) — **im Wiki ohne Entsprechung**. |
| `knowledge/wiki/topics/rules.md:161-163` vs. `docs/guides/features/rules.md:183-185` | Der Abschnitt „Verwandte Dokumente" ist in beiden vorhanden, der Wiki-Link auf `CLAUDE.md` ist jedoch pfadangepasst (`../../../CLAUDE.md` statt `../CLAUDE.md`) — eine mechanische Anpassung an die neue Tiefe, kein eigener Inhalt. |
| `knowledge/wiki/topics/rules.md:6` | `timestamp: "2026-07-27"` — Stand der Wiki-Seite. |

**Einschätzung:** echte Dublette, aber ein **veralteter Snapshot**: der Guide ist um einen
Abschnitt weiter, den das Wiki nicht kennt. Das ist kein Zufall, sondern die Kehrseite der
Dublette (Stand vom 2026-07-27, Wiki-Pflege läuft nicht mit).

### 3.2 `agent-composition` — identischer Körper, reine Frontmatter-Aufbereitung

| Beleg | Befund |
|---|---|
| `knowledge/wiki/topics/agent-composition.md:2,:7,:8` | Frontmatter `type: "Guide"`, `resource:`-Verweis auf den unveränderlichen Spiegel, `migrated_from: "docs/guides/features/agent-composition.md"` |
| Überschriftenlisten beider Dateien | **je 11 `##`-Überschriften** in identischer Reihenfolge: Wiki `:18, :30, :48, :59, :98, :165, :195, :208, :255, :279, :307` ↔ Guide `:9, :21, :39, :50, :89, :156, :186, :199, :246, :270, :298` — konstanter Versatz **+9** über die gesamte Datei |
| Dateilängen | Wiki **320** Zeilen, Guide **311** Zeilen — Differenz exakt **+9** (die 9 Frontmatter-Zeilen) |
| `knowledge/wiki/topics/agent-composition.md:12-14` vs. `docs/guides/features/agent-composition.md:3-5` | identischer Einleitungsblock |

**Einschätzung:** **byte-gleicher Körper** mit maschinell ergänztem Frontmatter und angepasstem
`resource`-/`migrated_from`-Verweis. Der Wiki-Beitrag ist hier kein zusätzlicher LLM-Text,
sondern derselbe Stoff plus Herkunftsnachweis. Dies ist das Muster, das den „LLM-Aufbereitung"
Teil von OQ1 berührt: die Aufbereitung besteht (hier) aus Frontmatter + Katalogeintrag.

### 3.3 `mcp-setup` — inhaltliche Dublette mit **Substanzdrift**

| Beleg | Befund |
|---|---|
| `knowledge/wiki/topics/mcp-setup.md:18` | `config/mcp-registry.yaml  ← Globaler Katalog (was gibt es?)` |
| `docs/guides/mcp-setup.md:9` | `config/plugin-catalog.yaml ← Globaler Katalog (was gibt es?)` |
| `knowledge/wiki/topics/mcp-setup.md:2-8` vs. `docs/guides/mcp-setup.md:1-4` | Titel und Einleitungsabsatz identisch; Wiki mit Frontmatter, Guide ohne |
| Dateilängen | Wiki **163** Zeilen, Guide **157** Zeilen |

**Einschätzung:** die beiden Seiten behaupten im Diagrammschnitt **verschiedene Dateinamen** für
denselben Sachverhalt. Die Wiki-Seite nennt einen Pfad, den der aktuelle Guide nicht mehr nennt.
Praktische Folge: ein LLM, das die Wiki-Seite liest, kann einen veralteten Konfigurationspfad
nennen. Das ist ein Sachfehler in der **Duplikat**-Richtung, nicht in der „Wiki als eigener
Stoff"-Richtung.

### 3.4 Was der Katalog als LLM-Aufbereitung tatsächlich liefert

`knowledge/wiki/index.md:75-113` führt **40** Topics mit Titel, gekürzter Beschreibung und
Tags. Das ist der konkrete LLM-lesbare Zusatznutzen des Wiki: nicht eigener Guide-Text,
sondern ein **beschreibender Katalog über denselben Stoff** plus Herkunftsnachweis im
Frontmatter. Ob dieser Zusatznutzen den Duplikat-Aufwand trägt, ist genau die Produktfrage.

## 4. Blockade

| Status | Umfang | Grundlage |
|---|---|---|
| **Blockiert** | **W5-1** (DEC-OQ9) | Plan, W5-1: „Depends on: W4-3, W0-7" |
| **Blockiert** | **W5-3** (M-9/M-10) | Plan, W5-3: „Depends on: W5-2, W0-7" |
| **Blockiert (transitiv)** | **W5-2** (M-5/M-6) | Plan, W5-2: „Depends on: W5-1" |
| **Blockiert** | **Abschluss von W5**, damit **AC-31** und das W5-Gate | Plan, Wellenübersicht: W0-7 „blockiert Abschluss W5 (offen)"; W5-1/W5-3 listen W0-7 als Abhängigkeit |
| **Nicht blockiert** | **W0** (übrige Tasks), **W1**, **W2**, **W3**, **W4**, **W6**, **W7**, **W8** | keine dieser Tasks führt W0-7 als Abhängigkeit; W1–W4 laufen unabhängig, W6–W8 knüpfen an W5-Ergebnisse an, nicht an W0-7 |
| **Nicht blockiert** | die gesamte **Inhaltsarbeit** zu `docs/guides/` und `knowledge/wiki/` | NG-1 verbietet sie ohnehin; OQ1 ist eine Produktfrage, keine Implementierungsfreigabe |

**Wie NG-1 W5-3 auch ohne Entscheidung schützt:** W5-3 ist rein additiv spezifiziert — es
setzt `derived-from: <existierender Rel-Pfad>` und `derived-at: <ISO-8601>` in die Frontmatter
der annotierten Wiki-Seiten und hängt die Architektur-Seiten per Kurzform-Redirect um
(Plan W5-3, Interfaces; Spec IC-17, IC-03). Der Plan-Text, die AC-31 und das W5-Gate lassen
ausschließlich additive Diffs zu; **jede** gelöschte Zeile außer einer `status:`-Ersetzung führt
zum Stopp. Eine Inhaltsmigration — also das eigentliche „Merge"-Ziel von OQ1 — würde gegen
NG-1 und gegen dieses Gate verstoßen und ist daher **ohne** Entscheidung ausgeschlossen. Die
Entscheidung zu OQ1 verschiebt also die **spätere** Scope-Grenze (welche Unique-Inhalte später
wohin wandern, als FI-4), **nicht** die Mechanik der Annotation.

## 5. Eskalationsvorschlag an `main_chat`

**Zu entscheiden ist genau eine Frage:** Wird `knowledge/wiki/topics/` (40 Seiten) zu einer
Duplikatquelle gegenüber `docs/guides/` (32 Dateien, davon 30 Markdown-Guides) mit
Rückverweis-Strategie, oder bleibt das Wiki als eigenständiger LLM-Lesefluss bestehen? Die
Optionen sind vollständig aus der Bestandsaufnahme abgeleitet; jede ist mit W5 und NG-1
vereinbar.

### Option A — `docs/guides/` = SSoT, Wiki-Duplikate → Redirect (Spec-Empfehlung)

Wirkung: die 25 Paare (Kapitel 2.3) werden im Wiki auf ihren Guide verlinkt bzw. als
Kurzform geführt; die 15 Topics ohne Guide-Gegenstück (Kapitel 2.4) bleiben eigenständig;
Anreicherungspunkte für W5-3 sind `derived-from`/`derived-at` (additiv, IC-17) und
`SSoT: docs/guides/…` als Pendant zum Architektur-Redirect (IC-03).

- **Dafür:** genau **eine** Quelle pro Thema; der in Kapitel 3 nachgewiesene Drift
  (`mcp-setup`) verschwindet mit der Dublikatquelle; der Katalog in
  `knowledge/wiki/index.md` bleibt nutzbar, ohne Second-Truth-Pflege.
- **Dagegen:** die 15 Unique-Themen bleiben als „Kopie ohne Master" stehen und brauchen eine
  eigene SSoT-Klärung (FI-4); die 2 verwaisten Topics (`reqflow-setup`,
  `template-gap-analysis`) lösen sich **nicht** auf, weil ihr Guide fehlt; die
  Description-/Tag-Einträge des Wiki-Katalogs müssten beim Redirect-Pfad mitgeführt werden,
  sonst verlieren die `knowledge-*`-Agenten ihren Einstieg; Eingriffe in 25+
  Wiki-Dateien sind ein **inhaltlicher** Schnitt und berühren NG-1, d. h. sie brauchen eine
  eigene REQ.
- **Kosten:** 25 Redirect-/Annotationsentscheidungen, plus Recherche zu 2 verwaisten Topics.

### Option B — Wiki bleibt eigenständige LLM-Aufbereitung, nur Unique wandern

Wirkung: die 25 Paare bleiben als Wiki-Seiten bestehen; SSoT-Regel gilt nur für Inhalte ohne
Guide-Gegenstück; die Pflege-Dopplung wird bewusst in Kauf genommen.

- **Dafür:** der in Kapitel 3.4 belegte LLM-Katalognutzen (Beschreibung + Tags + Herkunftsnachweis)
  bleibt vollständig erhalten; die SE-Kaskade- und Provider-Themen (13 Seiten) behalten ihren
  Platz ohne SSoT-Verhandlung; kein Eingriff in bestehende Wiki-Inhalte → NG-1 bleibt
  unberührt.
- **Dagegen:** die nachgewiesene Drift aus 3.3 bleibt bestehen — das Wiki nennt
  `config/mcp-registry.yaml` statt `config/plugin-catalog.yaml`; Doppelpflege zweier Stellen
  pro Thema; die Prüfung V7/V3 (Staleness) müsste dauerhaft auf beide Bäume laufen, sonst
  wird Drift still; die Spec-Empfehlung wird **verworfen** und muss in Spec §11.1 nachgezogen
  werden (Statuswechsel OQ1 von „offen" nach „geschlossen mit abweichender Empfehlung").

### Option C — Entscheidung auf die Unique-Frage zurückverschieben (Scope-Verkleinerung)

Wirkung: die Frage „alles oder nichts" wird nicht gestellt; entschieden wird nur, ob die
**13** Topics außerhalb von `docs/guides/` eine eigene SSoT brauchen, und die 25 Paare
laufen als **additive** `derived-from`-Annotation ohne Redirect (das ist exakt der
W5-3-Umfang). Ein späterer Umgang mit den 25 Paaren wird als FI-4 geführt.

- **Dafür:** die kleinste entscheidbare Einheit; W5-3 wird nicht über den Tabellenkopf hinaus
  blockiert; der Scope bleibt additiv und NG-1-konform; die 2 verwaisten Topics werden
  zwangsläufig Teil der Entscheidung (kein Origin vorhanden).
- **Dagegen:** der Kernkonflikt von OQ1 (Duplikat vs. eigener Lesefluss) wird nur verschoben,
  nicht gelöst; es entsteht eine **Folgeentscheidung mit erneutem Eskalationsbedarf**; die
  Verwaltung von doppelten Stellen bleibt ungeregelt.

### Empfehlung (ausdrücklich Empfehlung, nicht Entscheidung)

Die **Spec-Empfehlung (Option A)** deckt sich mit dem Befundbild dieses Records: die Stichprobe
zeigt, dass der Wiki-Zusatz im Kern aus Frontmatter und Katalogeintrag besteht und in einem
Fall bereits gedriftet ist. Für die **15** Unique-Themen (Kapitel 2.4) ist die Frage jedoch
offen, ob sie nach `docs/` (z. B. `docs/se-cascade/`, `docs/providers/`) überführt werden
sollten — dafür gibt es in der Spec keine Empfehlung. **Auch diese Empfehlung ist nur ein
Vorschlag an `main_chat`; sie ist keine getroffene Entscheidung und wird in diesem Record
nicht wirksam.**

### Was eine Antwort mindestens enthalten muss

1. Option A, B oder C (oder eine benannte Abweichung davon).
2. Bezugszahl: gilt der Umfang der Migration für **40** Topics (gezählt) oder für die
   **43** der Spec §11.1? Falls 43: welche drei Dateien sind gemeint?
3. Behandlung der 2 Topics mit fehlendem Ursprung (`reqflow-setup`, `template-gap-analysis`).
4. Ob ein Future-Path als **FI-4** (Titel in Kapitel 6) angelegt wird und wer ihn führt.
5. Bestätigung, dass W5-3 **additiv annotiert und nichts migriert** (NG-1) — dies gilt heute
   bereits und ist durch keine Option aufhebbar.

## 6. Folge-REQ (FI-4) — Titel vorgeschlagen, keine ID vergeben

Die inhaltliche Konsolidierung von `knowledge/wiki/topics/` ↔ `docs/guides/` ist als
**FI-4** (Spec, Follow-up-Impacts) geführt und ausdrücklich eine **Produktentscheidung**,
keine Strukturaufgabe dieser Initiative. Vorgeschlagener Arbeitstitel, sobald die Option
gewählt ist:

> **FI-4: Inhaltliche Konsolidierung `knowledge/wiki/topics/` ↔ `docs/guides/` — Unique-Inhalte
> überführen, Duplikate auflösen (SSoT-Entscheidung + Herkunftsannotation)**

Dieser Record **vergibt keine `REQ-*`-ID** — die ID-Deklaration ist selbst Gegenstand von OQ4
und liegt bei `requirements`. Ebenso ändert dieser Record die Spec nicht; die dortige
Empfehlung (Option A) bleibt Empfehlung, bis `main_chat` entscheidet.

## 7. Verifikationsgegenstand

| Gegenstand | Wert | Evidenzklasse |
|---|---|---|
| **Prüfbefehl (aus Plan, Task W0-7)** | `grep -n 'OQ1\|FI-4' docs/plans/2026-09-25-docs-consolidation-oq1.md` | — (Prüfbefehl) |
| **Sollwert** | **0** als Exit-Code (mindestens **ein** Treffer) | — (Sollwert) |
| **Bedeutung des Sollwerts** | Der Record muss OQ1 **und** FI-4 benennen — d. h. die offene Frage und die Folge-REQ-Referenz müssen auffindbar sein. Der Treffer belegt die **Dokumentation** der Eskalation, **nicht** eine Entscheidung und **nicht** eine Migration von Wiki-Inhalten. | — (Interpretation) |
| **Messstatus in diesem Schritt** | **nicht gemessen.** Die Verifikation greift erst nach dem Schreiben und ist dem nachgelagerten Lauf vorbehalten; in diesem Record ist **kein** Messwert eingetragen, weil noch keiner vorliegt. | `nicht gemessen` |
| **Bestandszahlen (Kapitel 2)** | 40 Topics · 32 Guide-Dateien (30 `.md` + 1 `.yml` + 1 `.example`) · 25 Paare · 15 Unique | `gezählt ohne Shell` |
| **Bewusst nicht Gegenstand** | jede Zählung, die eine Datei in `knowledge/wiki/` oder `docs/guides/` verändern würde (W5) | — (Abgrenzung) |

## 8. Abgrenzung

1. **Keine Entscheidung.** Dieser Record trifft **keine** Festlegung zu OQ1. Die Frage bleibt in
   **Spec §11.1** ausdrücklich **offen**; die dortige Empfehlung bleibt Empfehlung.
2. **Keine Migration, keine Annotation.** `knowledge/wiki/**` und `docs/guides/**` sind
   unverändert. W5-1 und W5-3 bleiben die Tasks, die diese Arbeit tun — ausgeführt wird sie
   erst nach Entscheidung.
3. **Keine Spec-Änderung.** Bei Widerspruch zwischen diesem Record und der Spec gilt die Spec.
4. **Eskalationscharakter.** Die Decision-Task-Liste des Plans (Wellen-Übersicht, W0-Zeile
   `W0-7 DEC-OQ1 -----> blockiert Abschluss W5 (offen)`) bildet ab, dass W0-7 eine
   **Entscheidungs-Task** ist und kein Ausführungsschritt. Die Checkboxen der Task stehen
   deshalb bewusst nicht abgehakt: die Entscheidung ist zum Zeitpunkt dieses Records nicht
   erfolgt.
5. **Kein Ersatz für die Entscheidung.** Dieser Record ist die Grundlage, auf der `main_chat`
   entscheidet — nicht deren Ergebnis.
