---
plan-id: PLAN-DOCS-CONSOLIDATION-2026-09-25
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: W0-3 — REC-OQ2 — `llms.txt` Hybrid (Ergebnis-Record)
status: done
revision: 0.2
related:
  - docs/plans/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation.md
  - docs/specs/2026-09-25-repository-documentation-consolidation-design.md
  - docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md
  - llms.txt
---

# W0-3 — REC-OQ2 — `llms.txt` Hybrid (Ergebnis-Record)

> Ergebnis-Record der Plan-Task **W0-3** („REC-OQ2 — `llms.txt` Hybrid (Ergebnis-Record,
> entschieden 2026-09-26)"). Plan `PLAN-DOCS-CONSOLIDATION-2026-09-25`, Spec
> `SPEC-DOCS-CONSOLIDATION-2026-09-25` (Rev. 0.3, `status: APPROVED`).
> **Ausführungsinstanz:** `documenter` (Rollen-Ownership dieses Records; die Commit-Leistung
> für W0-3 verbleibt beim `git`-Agenten).
> Stand: Branch `feat/repository-documentation-consolidation-main` @ `95ac76df`,
> Basis `origin/main` = `3c46920a`, PR #839 (Draft).
> **Branch-Bestand (gemessen 2026-09-26):** `git branch --list
> 'feat/repository-documentation-consolidation*'` → **2** Zeilen — der **aktive** Wellen-Branch
> und der **überholte** Branch `feat/repository-documentation-consolidation` (divergente
> Doppelkopie der Spec-/Plan-Commits, nicht in `main`), der auf ausdrückliche **Nutzer-Vorgabe
> („nicht löschen")** erhalten bleibt. Für OQ2 **ohne Wirkung**; Details: W0-2-Record
> Kapitel 7.2, offener Punkt **OP-2** dort §10.
>
> **Nachführung 2026-09-26 (Rev. 0.1 → 0.2):** Ergänzt wurde ausschließlich die
> **Evidenzklassen-Konvention** (global für alle W0-Records) und der **Branch-Bestand** (2
> Branches mit gemeinsamem Präfix, davon 1 aktiv; der überholte bleibt auf Nutzer-Vorgabe
> erhalten). **Die Entscheidung OQ2 (Hybrid), Gewähltes/Verworfenes, alle Konfigurations- und
> Snippet-Folgen und alle Sollwerte bleiben unverändert.**
>
> **Charakter:** Dieser Record **dokumentiert** eine bereits getroffene Entscheidung — er
> trifft sie nicht. Er ist **keine** Kopie und **keine** Revision der Spec; normative Quelle
> bleibt die Spec (Spec §11.2). Bei Widerspruch zwischen diesem Record und der Spec gilt die
> **Spec**.

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
Folgewellen: ein `✅` **ohne** Evidenzklasse ist unvollständig. In diesem Record ist der
Verifikations-Prüfbefehl `nicht gemessen`; alle übrigen Angaben sind Verweise auf Spec, Design
und Dateistand, keine Messwerte.

## Trace-Anker

| Anker | Fundstelle |
|---|---|
| OQ2 — geschlossen, Hybrid | Spec §11.2 (OQ2-Zeile) |
| Empfehlung „Hybrid wie T-2 A" | Design, OQ2-Zeile der Entscheidungstabelle |
| Generationsmodi (hybrid) | Spec §3.1 (Modus-Tabelle) |
| SSoT-Matrix Provider | Spec §3.2 (Zeile „Provider") |
| IC-02 — Faktum-Vertrag, `*_BLOCK` | Spec §5.1 |
| IC-08 — Marker-Syntax (Hybrid-Modus) | Spec §5.2 |
| IC-16 — Drift-Baseline der Marker-Bodies | Spec §5.2 |
| IC-22 — `docs-consolidation.sources` | Spec §5.4 (IC-22-Tabelle) |
| IC-23 — Sollwert-Datei | Spec §5.5 |
| AC-25 — Snippet-Bridge | Spec, Akzeptanzkriterien (M2) |
| AC-40 — Providerzahl generiert | Spec, Akzeptanzkriterien (M3) |
| W1-6 / W3-7 / W8-3 | Plan, Wellen-Kapitel W1 / W3 / W8 |
| Bestandsaufnahme | `llms.txt` (Root, 24 Zeilen) |

## Zweck und Geltungsbereich

Dieser Record schließt **OQ2** ab und macht die Konsequenzen für die Folgewellen
nachvollziehbar. Geltungsbereich ist **ausschließlich** der Generationsmodus der Root-Datei
`llms.txt` innerhalb der Doku-Konsolidierung. Er enthält **keine** Code-, Config- oder
Dateiänderung: `llms.txt` selbst wird erst in **W3-7** (Marker-Regionen) und **W8-3**
(Providerzahl) angefasst, dieser Record nicht.

## 1. Entscheidung

| Feld | Wert |
|---|---|
| **Entscheidung** | **Hybrid** — `llms.txt` bleibt handgepflegt; generiert werden **ausschließlich** `{{DOCS_PROVIDERS_BLOCK}}` und `{{DOCS_REPO_FACTS_BLOCK}}` |
| **Datum** | **2026-09-26** |
| **Entscheider** | Nutzer, über `main_chat` an den `orchestrator`; formalisiert und dokumentiert durch `documenter` |
| **Verhältnis zur Spec** | **bestätigt** die Empfehlung der Spec (Hybrid wie T-2 A, Design-OQ2-Zeile) — die Entscheidung weicht **nicht** ab |
| **Scope** | Modus-Vertrag der Datei `llms.txt`; **kein** Code-Vertrag — IC und AC bleiben unberührt (AC-25, AC-40) |
| **Folge** | `llms.txt` ist ein Wert der Liste der Hybrid-Dateien in `docs-consolidation.sources` (IC-22); Default bleibt `[README.md, llms.txt, ARCHITECTURE.md]` |
| **Nicht entschieden** | ein **Vollgenerieren** der Datei (siehe Kapitel 2) |
| **Aufhebung** | die W1-Blockade aus Spec §11.1 ist mit dieser Entscheidung aufgehoben |

## 2. Gewähltes und verworfene Alternative

### 2.1 Gewählt: Hybrid (zwei generierte Blöcke, Rest Handtext)

Generiert wird **ausschließlich**:

1. `{{DOCS_PROVIDERS_BLOCK}}` — Provider-Tabelle aus `config/ai-providers.yaml` (Spec §5.1).
2. `{{DOCS_REPO_FACTS_BLOCK}}` — kompakter Faktenblock **ohne** volatile Fakten, ausdrücklich
   als „kompakter Faktenblock für `llms.txt`" definiert (Spec §5.1).

Handgepflegt bleiben: **Einleitung**, **Linkliste** und die gesamte übrige **Prosa**
(Spec §3.1, Modus `hybrid`: „Handprosa + generierte Marker-Regionen"; außen Mensch, innen
Generator). Der Marker-Namespace ist `agent-meta:docs-*` und getrennt von
`agent-meta:managed-*` (IC-08).

### 2.2 Verworfen: Vollgenerierung von `llms.txt` (alle Inhalte generiert)

**Diese Variante ist ausdrücklich benannt und nicht gewählt.** Begründung der Verwerfung:

1. **Prosa-Verlust.** `llms.txt` ist bewusst prosaisch für den LLM-Konsum; eine
   Vollgenerierung ersetzt Einleitung und Ton durch Generator-Output (Design, OQ2-Zeile;
   Spec §11.2).
2. **Diff-Churn (R1).** Eine voll generierte Datei wäre Ganzdatei-Output und würde jede
   Prosa-Änderung in einem generierten Diff verschwinden lassen bzw. umgekehrt jeden
   Prosa-Rewrite erzwingen — genau das Risiko, das die Marker-Bodies statt Ganzdatei-Hash
   vermeiden (IC-16, Analyse A8: Marker-Hosts werden nur über den **extrahierten
   Marker-Body** mit Store-Key `<datei>#docs:<region>` in die Hash-Baseline aufgenommen).
3. **Nutzungsverlust.** Die Datei ist ein Einstiegspunkt für Assistenten ohne Clone und
   ohne Pipeline (Abschnitt „For AI assistants just linked to this repo"). Dieser Nutzen ist
   an Text gebunden, den ein Generator nicht kennt.
4. **Kein Bedarf.** Alle driftanfälligen Fakten der Datei werden bereits von den **zwei**
   gewählten Blöcken abgedeckt (Kapitel 3).

Eine spätere Ausweitung des Hybrid-Scopes wäre eine **neue Entscheidung** und braucht
zuerst eine Spec-Revision — sie ergibt sich nicht automatisch aus diesem Record.

## 3. Bestandsaufnahme `llms.txt` (Ist-Stand, 24 Zeilen)

Alle Angaben sind gegen die Datei im Repo gelesen und mit `Datei:Zeile` belegt.

| Beleg | Inhalt | Einstufung |
|---|---|---|
| `llms.txt:1` | `# agent-meta` — Titel | Handtext |
| `llms.txt:3` | Einleitung als Blockquote-Zeile (Meta-Repository, Rollen-Definitionen) | **Handtext, bleibt** |
| `llms.txt:5` | Prosa-Absatz über `sync.py` und die generierten Provider-Zieldateien; **nennt 6 Providernamen**: Claude Code, Gemini/Antigravity, Opencode, Continue, GitHub Copilot, Mammouth Code | **Mischstelle** — einzige Stelle, an der ein generierter Block factisch hingehört |
| `llms.txt:7` | Überschrift `## For AI assistants just linked to this repo` | Handtext |
| `llms.txt:9` | Prosa-Einleitung des Assistenten-Abschnitts | Handtext |
| `llms.txt:11` | Link „Standalone agent index" auf `standalone/README.md` | Handtext (Linkliste) |
| `llms.txt:12` | Anweisung an den Assistenten (Persona übernehmen) | Handtext |
| `llms.txt:14` | Überschrift `## Docs` | Handtext |
| `llms.txt:16-19` | Linkliste: `README.md`, `docs/api/cli-reference.md`, `docs/api/composition-system.md`, `docs/api/admin-ui-reference.md` | **Handtext, bleibt** (Spec §3.2: CLI-/UI-Referenz handgepflegt) |
| `llms.txt:21` | Überschrift `## Optional` | Handtext |
| `llms.txt:23` | Link `CHANGELOG.md` | Handtext |
| `llms.txt:24` | Link `ARCHITECTURE.md` | **Handtext, bleibt** (Spec §3.2: Architektur-Stub-Verweis handgepflegt; der Link muss nach W4 gültig bleiben) |

**Zahlenbestand:** die Datei enthält heute **keine einzige Zahl**, weder eine Version noch
einen Zähler. Es gibt daher **keine** Handzahl, die durch einen generierten Block ersetzt
werden müsste — der generative Eingriff ist rein additiv.

**Erkannte Drift (Proverbenamen, keine Handzahl):** `llms.txt:5` nennt **6** Providernamen,
die kanonische Quelle `config/ai-providers.yaml` enthält **9** Blöcke (Spec §3.2, Zeile
„Provider"; `DOCS_PROVIDER_COUNT` = `len(data["providers"])`, VERIFIED heute 9, Spec §5.1).
Damit ist `llms.txt:5` gegenüber dem Ist-Stand der Provider-Konfiguration unvollständig.
Diese Drift wurde im Audit bewusst **nicht** als Falschzahl gezählt, weil `:5` eine
Prosa-Aufzählung und keine Zahl ist; sie wird inhaltlich über **AC-40** behoben (Spec §1.2,
Kapitel „Falschzahlen"; Spec, AC-40). Genau diese Stelle ist der Zielort des
`{{DOCS_PROVIDERS_BLOCK}}`.

**Platz für die beiden Blöcke:**

- `{{DOCS_PROVIDERS_BLOCK}}` — **Platz vorhanden**: `llms.txt:5` (die Proverbenamen-Aufzählung
  ist der einzige faktische Anker der Datei).
- `{{DOCS_REPO_FACTS_BLOCK}}` — **Platz derzeit nicht vorhanden**: die Datei enthält keine
  Tabelle und keinen Faktenabschnitt. Der Block braucht in W3-7 einen **neu anzulegenden**
  Ankerort (eigene kurze Überschrift oder ein Abschnitt am Dateiende). Das ist eine
  Folgeaufgabe an W3-7, **nicht** an diesen Record — und keine Erweiterung des Hybrid-Scopes.

**Zustand heute:** keine `{{…}}`-Platzhalter, keine `agent-meta:*`-Marker, keine
`DOCS_FACT_BLOCK_HOSTS`-Region (Spec §5.2, `DOCS_FACT_BLOCK_HOSTS` =
`("README.md", "llms.txt", "ARCHITECTURE.md")` — `llms.txt` ist als Marker-Host **vorgesehen**,
aber noch ohne Region). Die interne-Link-Prüfung **V3** erfasst `llms.txt` bereits heute
(Spec §5.1, Check-Tabelle V3).

## 4. Folgen der Entscheidung

| Betroffene Stelle | Folge aus OQ2 |
|---|---|
| **W1-6** (Snippet-Bridge) | Die sechs Snippets in `snippets/docs/` liefern `variables["DOCS_*_BLOCK"]`; für `llms.txt` werden davon **nur** `providers` und `repo-facts` gerendert. **AC-25** (Snippet-Inlining-Vertrag) gilt unverändert für `repo-facts`. |
| **W3-7** (Marker-Regionen) | Führt in `llms.txt` **genau zwei** Regionen ein: `{{DOCS_PROVIDERS_BLOCK}}` an `llms.txt:5` und `{{DOCS_REPO_FACTS_BLOCK}}` an einem neu anzulegenden Ankerort. Prose außerhalb der Regionen bleibt unverändert (NG-1). **Kein** Vollgenerieren der Datei. |
| **W8-3** (Providerzahl) | Löst die Proverbenamen-Drift an `llms.txt:5` und in `README.md:690` zugunsten eines generierten Blocks auf (**AC-40**); der Fließtext darf keine handgeschriebene Providerzahl mehr führen. Test: `test_provider_count_is_generated_in_readme_llms_index`. |
| **IC-22** | `docs-consolidation.sources` bleibt Default `[README.md, llms.txt, ARCHITECTURE.md]`. Die Liste steuert **nur**, welche Dateien zwei Marker-Regionen erhalten — **nicht**, wie viel Prose generiert wird. `docs-consolidation.volatile-facts` bleibt unberührt. |
| **IC-23** | Unberührt: `config/doc-facts-expected.yaml` bleibt die einzige Ort für Sollzahlen und enthält **keine** `*_BLOCK`-Fakten (Text, keine Zahl). Für `llms.txt` ist daraus nur `DOCS_PROVIDER_COUNT` über den `DOCS_PROVIDERS_BLOCK` sichtbar. |
| **AC-25 / AC-40** | Beide bleiben **unverändert** gültig und unverändert gefordert. OQ2 ist ein Modus-Vertrag, kein Code-Vertrag. |
| **NG-1 / R1 / V1 / V6** | NG-1 (kein Inhalts-Rewrite von Altinhalt), R1 (Diff-Churn), V1 (Hybrid-Handzahlen) und V6 (Handedit am generierten Block) gelten für `llms.txt` unverändert; V1/V6 greifen erst, wenn die Regionen existieren. |

**Nicht betroffen:** `docs/INDEX.md` (Modus `generiert`, IC-10), `ARCHITECTURE.md`
(Stub + Linkziel), `README.md` (eigener Hybrid-Scope), Schema `project-config.schema.json`
(AC-39).

## 5. Verifikation

Plan-Verifikation für W0-3: `grep -n 'llms.txt' docs/plans/2026-09-25-docs-consolidation-oq2.md`
→ **Exit 0** mit **mindestens einem Treffer**.

- **Sollwert:** Exit `0`, mindestens ein Treffer. Der Dateiname kommt im Titel, im
  Trace-Anker, in Kapitel 2, in der Bestandsaufnahme (Kapitel 3) und in der Folgentabelle
  vor — der Sollwert ist damit **strukturell erfüllt**.
- **Messung:** **nicht ausgeführt.** Die Datei existierte zum Zeitpunkt des Schreibens
  nicht; der Grep kann erst **nach** dem Schreiben laufen. In dieser Ausführung stand kein
  Shell-Werkzeug zur Verfügung, deshalb wurde **kein** Messwert erhoben und **keiner**
  behauptet. Nachlauf durch die aufrufende Instanz.
- **Evidenzklasse:** `nicht gemessen` (es liegt kein Messwert vor; es wird keiner erfunden).

## 6. Befunde

1. **B-1 — Kein Ankerort für `DOCS_REPO_FACTS_BLOCK`.** `llms.txt` hat heute keinen
   Faktenabschnitt; die Datei enthält keinerlei Zahlen (Kapitel 3). W3-7 muss den Ankerort
   anlegen. Wird er weggelassen, ist der Hybrid-Scope unvollständig umgesetzt (nur ein Block
   statt zwei).
2. **B-2 — Proverbenamen-Drift an `llms.txt:5` (6 von 9).** Sie ist der einzige sachliche
   Mangel der Datei und wird durch `{{DOCS_PROVIDERS_BLOCK}}` in W3-7/W8-3 aufgelöst; sie ist
   **kein** Gegenargument gegen die Hybrid-Entscheidung.
3. **B-3 — Drei Fakten-Keys, die `llms.txt` heute nicht zeigt.** Volatile Fakten dürfen in
   `llms.txt` nicht gerendert werden (IC-02, `DOCS_SCENARIO_COUNT`); `DOCS_HOOKS_COUNT` und
   `DOCS_HOOKS_1GENERIC_COUNT` sind exklusiv für `README.md` vorgesehen. Der
   `DOCS_REPO_FACTS_BLOCK` muss diese Einschränkung spiegeln, sonst kollidiert er mit
   Kreuz-Rendering-Regeln.
4. **B-4 — Linkziel `llms.txt:24` ist wave-übergreifend sensibel.** Nach W4 zeigt der Link
   auf den generierten `ARCHITECTURE.md`-Stub; V3 (interne Links) und AC-28/AC-29 müssen
   grün bleiben. Dieser Record ändert daran nichts, benennt aber die Abhängigkeit.

## 7. Abgrenzung

- **Die Enge des Scopes ist eine Entscheidung, kein Versehen.** „Nur zwei Blöcke" ist
  ausdrücklich gegen die Vollgenerierung gewählt (Kapitel 2.2). Jede weitere generierte
  Region in `llms.txt` wäre eine Scope-Erweiterung und braucht eine neue Entscheidung bzw.
  Spec-Revision.
- **Nicht generiert werden dürfen:** Titel (`llms.txt:1`), Einleitung (`:3`), der
  Assistenten-Abschnitt (`:7-12`), die **gesamte** Linkliste (`:11`, `:16-19`, `:23`, `:24`),
  die Abschnittsüberschriften (`:7`, `:14`, `:21`) sowie jeder erklärende Fließtext. Ein
  Generator-Eingriff außerhalb der zwei benannten Blöcke verstößt gegen NG-1 und gegen
  Kapitel 2.1.
- **Kein CLI-Flag** (NG-4), **keine** neue Doku-Datei, **kein** Eingriff in den Prosa-Ton,
  **keine** Änderung an IC- oder AC-Texten durch diesen Record.
- **Dieser Record ändert keine Datei außer sich selbst.** `llms.txt` bleibt bis W3-7/W8-3
  unverändert; der Plan- und Spec-Text bleiben unverändert; die übrigen W0-Records bleiben
  unverändert.
- **Rollback:** rein dokumentarisch — Entfernen dieser Datei. Kein Code-, Config- oder
  Pipeline-Effekt, keine Rückrollpunkt-Kopplung an eine Welle.
