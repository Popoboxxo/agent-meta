---
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: Repository-weite Doku-Konsolidierung agent-meta — Technical Specification
status: APPROVED
approved: 2026-09-26
approved-scope: Ausführung W0–W8; Rev. 0.4 (Commit-/Branch-Normativität) am 2026-09-26 durch den Nutzer bestätigt; A13 und A14 als offene, dokumentierte Abweichungen registriert
revision: 0.4
related:
  - docs/specs/2026-09-25-repository-documentation-consolidation-design.md
  - docs/REQUIREMENTS.md
  - docs/plans/README.md
  - scripts/lib/spec_plan_scaffold.py
---

# Repository-weite Doku-Konsolidierung agent-meta — Technical Specification

> Status: **`APPROVED` (2026-09-26)** — **User-Freigabe liegt vor** (Nutzer, über `main_chat`
> an den `orchestrator`). Dieses Dokument ist eine **Spezifikation**: es definiert Interface
> Contracts, Datenfluss und Acceptance Criteria und enthält **keine Implementierung und
> keinen Plan**. Der Approval-Marker wurde nach dem Review durch `concept-reviewer`
> gesetzt (Approval-Gate, Master-Rule `spec-plan-workflow`).
>
> **Rev. 0.4 ist am 2026-09-26 durch den Nutzer bestätigt** — über den Entscheidungsweg laut
> Plan Rev. 0.4, K1 (`main_chat`). Das Concept-Review von Rev. 0.4 endete zuvor mit
> `VERDICT: BLOCKED` (F-1: neue normative Pflichten ohne erneute User-Freigabe); die
> Bestätigung liegt nun **extern** vor, die Auflösung ist in **§17.7** protokolliert.
> **Offen und bewusst nicht aufgelöst:** die W4/W5/W6-Serialität (**A14**, **§17.8**).
>
> Trace-Anker (aus dem Systemdesign **unverändert** übernommen und vom Plan zu referenzieren):
> `spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25`.
>
> **Verbindliche Eingangsgrundlage:** `docs/specs/2026-09-25-repository-documentation-consolidation-design.md`
> (concept-architect, 2026-09-25, Entscheidungen T-1…T-6, Komponenten C1…C8,
> Checks V1…V9, Wellen W0…W8, Risiken R1…R11, offene Fragen OQ1…OQ6, Downstream-Impacts B1…B6).
> Alle `Datei:Zeile`-Angaben zu `scripts/lib/`, `scripts/`, `config/`, `.meta-config/`,
> `tests/scenarios/`, `knowledge/` und zur Root-Doku wurden am 2026-09-26 gegen den Working
> Tree **re-verifiziert**. Wo diese Spec bewusst vom Design abweicht, steht die Abweichung
> mit Begründung in §13 „Abweichungen vom Design" — stillschweigende Abweichungen gibt es
> nicht.
>
> **Rev. 0.2 (2026-09-26) — Überarbeitung nach Concept-Review (CHANGES_REQUESTED).**
> Eingang: Concept-Review der Rolle `concept-reviewer` vom 2026-09-26 (Verdikt
> **CHANGES_REQUESTED**, 5 kritisch / 8 mittel / 3 niedrig + 5 Aufnahmepunkte; das
> Review-Artefakt selbst ist ein Session-Artefakt und nicht Teil des Repo-Baums — der
> vollständige Findings-Abgleich steht in §17.1). **Alle 16 Findings sind behoben.**
> Sieben Reviewer-Angaben wurden **eigenständig am Repo nachgeprüft**; **drei davon waren
> selbst ungenau und sind korrigiert** (dokumentiert in §17.2). Die Frontmatter blieb
> zu diesem Zeitpunkt `status: Entwurf` — es lag keine User-Freigabe vor.
>
> **Rev. 0.3 (2026-09-26) — Überarbeitung nach Re-Review (CHANGES_REQUESTED, 0 kritisch /
> 2 major / 4 minor / 2 info).** Eingang: Re-Review der Rolle `concept-reviewer` vom
> 2026-09-26 (Verdikt **CHANGES_REQUESTED**, `RESIDUAL_BLOCKERS: Keine`,
> `PLAN_READINESS: Ja`; vollständiger Abgleich in §17.5). **Alle 8 Findings (NEW-1…NEW-8) sind
> behoben**, zusätzlich die **Gegenkorrektur** des Re-Reviewers zu §17.2. **Neu:** `README.md:381`
> als **zweite** F22-Fundstelle (NEW-2) — F22 ist damit eine Zwei-Stellen-Falschzahl wie F3/F14;
> `DOCS_HOOK_SCRIPT_FILES_COUNT == 17` **entfällt** und wird durch
> `DOCS_HOOKS_1GENERIC_COUNT == 9` ersetzt (NEW-1, semantisch an `README.md:696` gebunden);
> Sollwert-Zahl **einheitlich elf** (NEW-4); AC-02 ist **durchsetzbar** formuliert, der
> `xfail`-Snapshot ist als unenforceable entfernt und seine Durchsetzung nach IC-23/AC-36
> **verlagert** (NEW-8). Im selben Codepfad zusätzlich **NF-12** gefunden: `HOOK_EXCLUDED_SUFFIXES`
> schrieb `"_impl.sh"` statt `"-impl.sh"` — die Regel hätte nichts gematcht. Alle übrigen
> Rev.-0.2-Korrekturen (16 Vorreview-Findings, R14–R18, Threat Model, OQ8, OQ6-Reihenfolge)
> sind als behoben **bestätigt** und wurden nicht angefasst. Die Frontmatter blieb
> zu diesem Zeitpunkt `status: Entwurf` — es lag keine User-Freigabe vor.
>
> **Rev. 0.4 (2026-09-26) — Ausführungskorrektur der Branch-/PR-Strategie (offener Punkt OP-1
> der Ausführungs-Records).** Diese Revision korrigiert **drei Normativitätsstellen** und deren
> Folgeverweise: die in Rev. 0.1–0.3 wörtlich „**Verbindlich**" geforderte Strategie „**ein Branch
> pro Welle** (`chore/docs-consolidation-w<N>`), gestapelte PRs" — geführt in der **W0-Zeile von
> §9.2** (OP1-1), im **§9.2-Absatz „PR-/Branch-Kollision"** (OP1-2) und in der **Mitigation von R16**
> (§12.2, OP1-3) — trug die **tatsächlich ausgeführte** Strategie nicht.
> Umgesetzt ist **ein** Wellen-Branch `feat/repository-documentation-consolidation-main` (Basis
> `origin/main`) mit **einem** PR gegen `main`; die Wellen laufen als **sequenzielle Commits** mit
> Wellenkennung im Commit-Titel. Da dieses Dokument sich zur **normativen Quelle** erklärt
> (Kopfzeile „stillschweigende Abweichungen gibt es nicht"; §2.2 „hart — Abweichung gilt als
> Spec-Verstoß"), wäre der eingefrorene Stand eine Verletzung der eigenen Norm — die Korrektur ist
> deshalb **hier** und **sichtbar** erfolgt, nicht in den Ausführungs-Records. **Keine inhaltliche
> Neuerfindung:** unverändert bleiben
> AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20 (R16 **nur** im Lösungsansatz), F1…F25,
> M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9, W0…W8, die Modulaufteilung M1–M4, die Welleninhalte
> und die SSoT-Zielstruktur; **keine** neue Welle, **kein** neues AC/IC/NFA/Risiko, **keine**
> geänderte Architektur. **A13 (neu, rev. 0.4): das Design nennt in seiner W0-Zeile einen
> Branch mit anderem Namen** — `chore/docs-consolidation`
> (`docs/specs/2026-09-25-repository-documentation-consolidation-design.md:265`) gegenüber
> `feat/repository-documentation-consolidation-main` (Basis `origin/main`) hier. Das Design
> verlangt an keiner Stelle gestapelte PRs; die **Zahl** der Branches stimmt, der **Name**
> nicht — das ist eine bewusste Abweichung (**§13 A13**), keine stille. **A14 (neu, rev. 0.4):
> offene Abweichung** — §9.2 führte W4/W5/W6 paarweise parallel, ausgeführt werden sie
> **sequenziell** (**§13 A14**, **§17.8**). §13 umfasst damit **14** Abweichungen
> (A1…A12 unverändert, A13/A14 neu). Volltext, betroffene Stellen und Ausführungsbelege:
> **§17.6**, Freigabe-Auflösung **§17.7**, offener Punkt **§17.8**. Der **formale Abschluss von
> OP-1 in Plan und W0-Records ist ein Folgeschritt** und nicht Teil dieser Revision; das
> **Concept-Review über Rev. 0.4 ist erfolgt** (2026-09-26, `VERDICT: BLOCKED`, F-1) und der
> **Entscheidungsweg `main_chat`** (Plan Rev. 0.4, K1) hat am 2026-09-26 entschieden
> (**§17.7**).
>
> **Freigabevermerk (2026-09-26).** Freigebende Instanz: **Nutzer-Freigabe**, über `main_chat`
> an den `orchestrator` weitergeleitet und hier durch die Rolle `documenter` auf Veranlassung
> des Orchestrators formalisiert. Review-Stand: **Runde 1** (Concept-Review vom 2026-09-26)
> endete mit `CHANGES_REQUESTED` und **5 kritischen Befunden** (K1…K5) → Rev. 0.2 mit
> **16 behobenen** Vorreview-Findings; **Runde 2** (Re-Review vom 2026-09-26) endete mit
> **0 kritischen Befunden**, `RESIDUAL_BLOCKERS: Keine` und `PLAN_READINESS: Ja` → Rev. 0.3
> mit **8 behobenen** Findings (NEW-1…NEW-8) plus der Gegenkorrektur zu §17.2. **Umfang der
> Freigabe:** sie umfasst die **Ausführung der Wellen W0–W8** dieses Vorhabens inklusive der
> in §11.1 weiterhin offenen, mit Owner und Wellen-Blockade versehenen Entscheidungen.
> **Datumsabweichung (dokumentiert):** der Nutzer hat den 2026-09-25 genannt; das ist das
> Datum der **Anfrage**, nicht das der Freigabe. Der Freigabevermerk trägt daher korrekt
> **2026-09-26**.
>
> **Rev. 0.4 — gesonderte Bestätigung (2026-09-26, extern).** Rev. 0.4 ist eine
> **Inhaltsrevision**: Sie führt neue normative Pflichten ein (verbindliche
> Commit-Titel-/Body-Konvention, Branch-Aufbewahrung als Scope-Aussage). Das Concept-Review
> von Rev. 0.4 endete deshalb mit `VERDICT: BLOCKED` (**F-1**) — die Normativität wurde ohne
> erneute User-Freigabe mit derselben Verbindlichkeitstiefe installiert, obwohl §15 `APPROVED`
> nur nach Concept-Review **und** User-Freigabe zulässt. **F-1 ist damit aufgelöst:** Rev. 0.4
> ist am **2026-09-26 durch den Nutzer ausdrücklich bestätigt**, über den Entscheidungsweg
> laut Plan Rev. 0.4, K1 (`main_chat`). **Worauf sich die Bestätigung bezieht:**
>
> - **unverändert:** der Umfang der Ausführungsmechanik **W0–W8** — der Freigabeumfang der
>   Erstfreigabe bleibt unberührt; keine Welle, kein AC/IC/NFA/Risiko wurde verschoben.
> - **neu bestätigt:** die in Rev. 0.4 aufgenommenen **Normativitätsaussagen** — die
>   verbindliche **Commit-Titel-/Body-Konvention** (§9.2 Punkt 2, R16-Mitigation) und die
>   **Branch-Aufbewahrung** als Scope-Aussage (§9.2 Punkt 4, „diese Spec schreibt weder
>   Löschung noch Aufbewahrung eines Branches vor").
> - **Bedingung der Bestätigung:** **A13** (Branch-Namensabweichung) und die
>   **W4/W5/W6-Serialität** (A14) sind als **offene, dokumentierte Abweichungen**
>   registriert — A13 in §13, A14 zusätzlich in **§17.8** mit Status **offen**.
>
> Die zuvor im Dokument selbst ausgerichtete Ausnahme („Inhaltsrevision ohne erneute
> Freigabe") ist damit **entfallen** — sie ist nicht mehr nötig, weil die Freigabe extern
> vorliegt. `status: APPROVED` besteht unverändert; die inhaltliche Revisionshistorie endet
> bei **Rev. 0.4**. (Konvention: `docs/specs/2026-09-13-stale-role-cleanup-design.md:39`,
> `docs/specs/2026-09-15-reference-standards-design.md:67` — beide führen die Freigabe als
> eigene Zeile, **ohne** Revisions-Bump; hier liegt sie zusätzlich als Rev. 0.4 vor.)
>
> **Zusätzlich am 2026-09-26 durch den Nutzer entschieden:** **OQ2**, **OQ6** und **OQ8** (§11.2).
> Alle drei sind damit **geschlossen** und nicht mehr als offene Frage zu führen; §16
> (Selbstreview Rev. 0.3) nennt OQ2/OQ6/OQ8 noch als offen — das ist der historische Rev.-0.3-Stand
> und bleibt als solcher stehen; maßgeblich ist §11.
>
> **Provider-agnostik ist Pflicht.** Kein neuer oder geänderter Codepfad verzweigt über ein
> Provider-Namensliteral. Provider-Unterschiede ausschließlich über Config-Keys /
> Capability-Flags (`config/ai-providers.yaml`, `.meta-config/project.yaml:159-169`).
>
> **Klassifikation (Master-Rule `spec-plan-workflow`):** **XL / Architectural** — die Spec
> berührt vier Modulgrenzen, migriert 4 Doku-Bäume, bricht eine bestehende Policy
> (`knowledge.py:112-114`) und verschiebt öffentliche Pfade. Produktions-Footprint
> (Code): 8 Dateien in `scripts/` + 2 Config-Dateien + 1 Schema-Datei; Doku-/Migrations-
> Footprint: ~65 Dateien (ausschließlich `git mv` + Marker-Regionen).

### Verifikations-Legende

| Marker | Bedeutung |
|---|---|
| **VERIFIED** | am 2026-09-26 im Working Tree gelesen; `Datei:Zeile` genannt |
| **VERIFIED-DESIGN** | aus dem freigegebenen Design übernommen und dort belegt |
| **HYPOTHESIS** | Annahme, vor Implementierung in der jeweiligen Welle zu prüfen |
| **REVIEWER-KORRIGIERT** | Reviewer-Angabe war selbst ungenau; korrigiert, Beleg in §17.2 |

### Revision

| Rev | Datum | Änderung | Autor |
|---|---|---|---|
| 0.1 | 2026-09-26 | Initiale Spezifikation aus `docs/specs/2026-09-25-repository-documentation-consolidation-design.md`; alle `scripts/lib/`-, `config/`-, `.meta-config/`-, `knowledge/`- und Root-Doku-Referenzen re-verifiziert; Modulaufteilung M1–M4; AC-01…AC-35; Trace-Matrix; R1…R13; OQ1…OQ7 | concept-specifier |
| 0.2 | 2026-09-26 | **Review-Überarbeitung (CHANGES_REQUESTED, 16/16 Findings behoben).** **K1** V1-Regel neu spezifiziert (2 Branches, Positiv-/Negativ-Fixture, AC-07/AC-08 ersetzt). **K2** F19 **gestrichen** — Tier-Presets = 5, `README.md:689` ist korrekt (Reviewer bestätigt). **K3** neuer Befund **F22** — DoD-Presets = 7, `README.md:688` ist Drift (Reviewer bestätigt). **K4** F14 erweitert — 8 Pipelines / 7 aktiv, `concept-driven-dev` fehlt in `README.md:479-489` (Reviewer bestätigt). **K5** Absenz-Default = **aus** für Writer **und** Checks (Präzedenz `knowledge.py:127`), `knowledge-engine`-Schreibverbot, Besitzregel für `docs/INDEX.md`; **Anzahl der brechenden Szenarien von 6 auf 3 harte Fehlschläge korrigiert** (§17.2). **M1** Hook-Zählung in zwei benannte Keys getrennt (11 / 17). **M2/M3** Trace-Matrix und W8-ACs repariert. **M4** F6 = vier Orte, Migrationen M-6/M-7 ergänzt, **F23/F24** erfasst. **M5** AC-29 entzirkelt (Stale-Quelle wandert mit der Langfassung). **M6** Restore-Pfad als **IC-24** spezifiziert, AC-35 entsprechend. **M7** R1 auf `docs/INDEX.md` ausgedehnt. **M8** Allowlist-Interaktion **analysiert statt vermutet** (verifiziert: `fnmatch` matcht den Basis-Pfad nicht). **N1–N3** Selbstwidersprüche korrigiert, OQ5/OQ7 als geschlossen markiert, `knowledge-indexer`-Kollision als R19. **Neu:** §12 Threat Model, **R14** (unabhängige Sollwert-Fixture → IC-23 + AC-36/AC-37), **R15** (Schema → M-11), **R16** (PR-/Branch-Kollision), **R17** (Downstream-Asymmetrie), **R18** (Auto-Commit-Interaktion), **R20** (V2-ERROR vs. menschliche Doku-Erstellung), **OQ8** (Index-Regenerierung), **OQ9** (zwei Beispiel-Configs), **§17** (Review-Auflösung + eigene Befunde), AC-01…AC-41, F1…F25 (F19 gestrichen), M-1…M-13, R1…R20, NFA-11, IC-23/IC-24 | concept-specifier |
| 0.3 | 2026-09-26 | **Re-Review-Überarbeitung (CHANGES_REQUESTED, 8/8 Findings + 1 Gegenkorrektur behoben).** **NEW-1** `DOCS_HOOK_SCRIPT_FILES_COUNT == 17` **entfällt** (die 17 zählen `hooks/**`, nicht `hooks/1-generic/`); neu `DOCS_HOOKS_1GENERIC_COUNT == 9` mit der Regel `hooks/1-generic/*.sh` minus `*-impl.sh`, exklusiv für `README.md:696`; `DOCS_HOOKS_COUNT == 11` bleibt unverändert exklusiv für `README.md:501`. **NEW-2** F22 um `README.md:381` erweitert (zweite Falschzahl: Überschrift „6 presets" **und** fehlende `concept-driven`-Zeile). **NEW-3** §1/§1.2-Zählung neu gerechnet: **11** falsche Zahlen (10 in `README.md`, 1 in `ARCHITECTURE.md:3`), `llms.txt:5` ist Prosa, keine Zahl. **NEW-4** Sollwerte einheitlich **elf**. **NEW-5** §9.2-Wellensummen korrigiert (W1: **10**, W3: **14**). **NEW-6** §16-Liste der AC ohne V-Check vervollständigt (**18**). **NEW-7** AC-38-Begründung für `51:32` auf Absenz-Default (IC-13/IC-22) umgestellt. **NEW-8** AC-02 ohne `xfail` Snapshot **durchsetzbar**; Zahlen-Sollwerte liegen ausschließlich in IC-23/AC-36. **Gegenkorrektur** §17.2: **0** Szenarien brechen unter der spezifizierten Abschirmung, **3** in der naiven Variante (nur als Begründung der Abschirmung genannt, kein Arbeitsauftrag — NG-10). **Neu:** NF-9 (Falschzahlenzählung), NF-10 (Sollwertzahl), NF-11 (`README.md:381` als Beleg des Designs), **NF-12** (`HOOK_EXCLUDED_SUFFIXES` schrieb `"_impl.sh"` statt `"-impl.sh"` — hätte `DOCS_HOOKS_COUNT` auf 13 statt 11 laufen lassen; im selben Codepfad wie NEW-1 gefunden und korrigiert) | concept-specifier |
| **0.4** | 2026-09-26 | **Ausführungskorrektur der Branch-/PR-Strategie (offener Punkt OP-1) — drei Normativitätsstellen, keine Design-Änderung, keine inhaltliche Neuerfindung.** **OP1-1** §9.2, **W0-Zeile**: „**ein Branch pro Welle** (`chore/docs-consolidation-w<N>`)" → **ein** Wellen-Branch `feat/repository-documentation-consolidation-main` (Basis `origin/main`) mit **einem** PR gegen `main`; Wellen-Zuordnung über die **Wellenkennung im Commit-Titel**. **OP1-2** §9.2-Absatz „PR-/Branch-Kollision" vollständig neu gefasst (Ein-Branch-/Ein-PR-Regel, Commit-Titel-Konvention inkl. `… W<N> complete` und Task-ID im Commit-Body, Merge-Regel `git mv`-Wellen W4/W5/W6 zuerst, sequenzielle W1→W8, dokumentierter Bestand des überholten Vor-Branches, Rebase gegen `origin/main` vor dem PR-Merge). **OP1-3** **R16-Mitigation** (§12.2): „Ein Branch **pro Welle** …, gestapelte PRs in Reihenfolge" → Reihenfolge- und Merge-Regel statt Branch-Anzahl. **OP1-4** §15 Trace-Anker um den Rev.-0.4-Ausführungskorrektur-Anker ergänzt. **OP1-5** §16 um zwei Abgrenzungszeilen (Rev.-0.4-Grenze, Ownership-Grenze Rev. 0.4) ergänzt. **OP1-6** §17.6 als vollständiger Korrektur- und Beleg-Abschnitt angelegt. **Unverändert:** AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20 (R16 **nur** im Lösungsansatz), F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9, W0…W8, §9.1, §9.2-Welleninhalt und AC-Mengen, §3–§12 im Übrigen. **§13 umfasst 14 Abweichungen** (A1…A12 unverändert; **neu in Rev. 0.4: A13** Branch-Namensabweichung gegen das Design und **A14** offene Abweichung W4/W5/W6-Serialität — das Design verlangt an keiner Stelle gestapelte PRs, die **Zahl** der Branches stimmt, der **Name** nicht). **Freigabe:** Rev. 0.4 am **2026-09-26 durch den Nutzer bestätigt** (Entscheidungsweg laut Plan Rev. 0.4, K1 → `main_chat`) — Auflösung des Review-Blocks `VERDICT: BLOCKED` (F-1) in **§17.7**; die zuvor im Dokument ausgerichtete Ausnahme („Inhaltsrevision ohne erneute Freigabe") ist **entfallen**. **Keine neue ID, keine neue Welle, kein neues Risiko.** Quelle der Korrektur: `docs/plans/2026-09-25-repository-documentation-consolidation.md` (Rev. 0.3, K1/K8/K9, Global Constraints, Task W0-2) und `docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md` §7.1/§7.2. **OP-1 wird in Plan und Records erst durch einen Folgeschritt formal geschlossen**; Concept-Review über Rev. 0.4 **ist erfolgt** (2026-09-26, `VERDICT: BLOCKED`, Befund **F-1**), die **Nutzer-Bestätigung** liegt vor; Auflösung und Wortlaut in **§17.7**, siehe §17.7. | concept-specifier |
| **Freigabe** | **2026-09-26** | **User-Freigabe** (Nutzer, über `main_chat` an den `orchestrator`); formalisiert durch `documenter`. Frontmatter `status:` auf `APPROVED` gesetzt. **Freigabestand:** Concept-Review **Runde 1** (2026-09-26) `CHANGES_REQUESTED`, **5 kritische Befunde** (K1…K5) → Rev. 0.2; Re-Review **Runde 2** (2026-09-26) `CHANGES_REQUESTED` mit **0 kritischen Befunden**, `RESIDUAL_BLOCKERS: Keine`, `PLAN_READINESS: Ja` → Rev. 0.3 mit **8 behobenen** Findings (NEW-1…NEW-8) + Gegenkorrektur. **Umfang:** Freigabe der **Ausführung W0–W8**. **Zusätzlich entschieden (Nutzer, 2026-09-26):** OQ2 (`llms.txt` = **Hybrid**), OQ6 (**tracked**) und OQ8 (Regenerierung über Sync/Validator) → nach §11.2 verschoben. **Keine inhaltliche Änderung** an IC/AC/Risiken — die Freigabe ist eine Statuszeile, kein Revisions-Bump (Konvention: `docs/specs/2026-09-13-stale-role-cleanup-design.md:39`, `docs/specs/2026-09-15-reference-standards-design.md:67`). **Datumsabweichung:** Nutzer nannte 2026-09-25 (Datum der Anfrage); der Freigabevermerk trägt das **Freigabedatum 2026-09-26**. **Nach der Freigabe (rev. 0.4, 2026-09-26):** die Ausführungskorrektur der Branch-/PR-Strategie (§17.6) — **ohne** Änderung an IC/AC/Risiken; die dort zunächst im Dokument ausgerichtete Ausnahme („ohne neue Freigabe") ist **durch die nachfolgende Nutzer-Bestätigung ersetzt**, siehe nächste Zeile | documenter |
| **Freigabe (Rev. 0.4)** | **2026-09-26** | **Nutzer-Bestätigung der Rev. 0.4** (Nutzer, über `main_chat` an den `orchestrator`; Entscheidungsweg laut Plan Rev. 0.4, K1); formalisiert durch `documenter`. **Anlass:** das Concept-Review von Rev. 0.4 endete mit `VERDICT: BLOCKED` (**F-1**) — neue normative Pflichten (verbindliche Commit-Titel-/Body-Konvention, Branch-Aufbewahrung als Scope-Aussage) waren ohne erneute User-Freigabe mit derselben Verbindlichkeitstiefe installiert worden. **Bezug der Bestätigung:** unverändert der Umfang der Ausführungsmechanik **W0–W8**; **neu bestätigt** die in Rev. 0.4 aufgenommenen Normativitätsaussagen. **Bedingung:** **A13** und die **W4/W5/W6-Serialität** (A14) sind als **offene, dokumentierte Abweichungen** registriert (§13, §17.7, §17.8). **Kein** Revisions-Bump — Rev. bleibt 0.4 | documenter |

---

## 1. Problem / messbare Baseline

Die agent-meta-Dokumentation ist an mehreren Stellen gewachsen, ohne dass eine Stelle die
andere ersetzt: eine **fünffache Architektur-Doku**, eine **vierfache Guide-Führung** (Rev. 0.1
nannte drei, M4), **vier Spec/Plan-Bäume** ohne dokumentierte Abgrenzung und **~190
`.md`-Dateien unter `docs/`** (≈ 190, **HYPOTHESIS** — die exakte Zahl wird erst durch
`DOCS_DOCS_FILE_COUNT` belegbar) ohne Index. Gleichzeitig ist jede manuell gepflegte Zahl in
`README.md` nachweislich falsch oder widersprüchlich: **10** Stück (F1, F2, F3 ×2, F4, F14 ×3,
F22 ×2) plus **1** in `ARCHITECTURE.md:3` (F4, zweite Fundstelle) = **11**. Der Zustand ist nicht
„ungenau", er ist **strukturell drift-anfaellig**: es gibt keine Maschine, die eine Zahl in
`README.md` mit der Quelle vergleicht — und in Rev. 0.1 gab es auch keine Maschine, die die
**Formel** hinter der Zahl prüft, weshalb drei falsche Zahlen unentdeckt blieben (§12.3, R14).

> **Rev. 0.3 — Zählung nachgerechnet (NEW-3).** Rev. 0.2 schrieb „10 (F1, F2, F3 ×2, F4, F14 ×3,
> F22) plus 2 in `llms.txt`"; die Aufzählung ergab **9**, und `llms.txt` enthält **keine**
> Zahl. Korrigiert auf **11 = 10 (`README.md`) + 1 (`ARCHITECTURE.md:3`)**, mit den beiden
> Änderungen aus NEW-2 (F22 hat jetzt **zwei** Fundstellen) und der Aufnahme von
> `ARCHITECTURE.md:3` als zweiter F4-Fundstelle. `llms.txt:5` („Claude Code, Gemini/Antigravity,
> Opencode, Continue, GitHub Copilot, Mammouth Code") listet 6 von 9 Providernamen
> (`config/ai-providers.yaml:1` + Blöcke `:2, :98, :172, :249, :316, :369, :434, :493, :545`) —
> das ist eine **inhaltliche** Lücke wie F14s fehlende `concept-driven-dev`-Zeile, über
> **AC-40** behoben, aber **keine** „manuell gepflegte Zahl" und deshalb nicht mitgezählt.
> Beleg und Korrektur in §17.4 (**NF-9**).

### 1.1 Baseline (alle Befunde mit `Datei:Zeile`)

| # | Befund | Beobachteter Wert | Beleg (VERIFIED) |
|---|---|---|---|
| F1 | Agenten-Zahl driftet | `README.md:122` „Agent Roster — **74** Generic Agents"; Ist **80** Rollen-`.md` in `agents/1-generic/` (83 Dateien − 3 `_*`-Helper) | `README.md:122`; Verzeichnislisting `agents/1-generic/` |
| F2 | Provider-Zahl driftet | `README.md:690` „**6** provider configs (Claude, Gemini, Opencode, Continue, Copilot, Mammouth)"; Ist **9** | `README.md:690`; `config/ai-providers.yaml:1` + Provider-Blöcke `:2, :98, :172, :249, :316, :369, :434, :493, :545` |
| F3 | Hook-Zahl **dreifach** widersprüchlich | `README.md:501` „## Hooks (**7** hooks, propagated to all providers)" vs. `README.md:696` „hooks/1-generic/  **5** hook scripts"; Ist **11** deploybare Hooks für `:501` (13 Top-Level-`.sh` — 2 `0-external/` + 11 `1-generic/` — minus 2 `*-impl.sh`) und **9** Hook-Skripte für `:696` (11 Top-Level-`.sh` in `hooks/1-generic/` minus 2 `*-impl.sh`). Die **17** `.sh` unter `hooks/**` (2 + 11 + 1 `lib/hook_common.sh` + 3 `release-gates/`) sind eine **Belegzahl für dieses Befund-Row, kein `DOCS_*`-Faktum** (Rev. 0.3, NEW-1) | `README.md:501`, `README.md:696`; `hooks/**/*.sh`-Listing: `0-external/{graphify-read-guard,graphify-search-guard}.sh`, `1-generic/{antigravity-json-adapter,auto-github-release,lifecycle-check,sync-on-config-change,viz-log,pre-release-check,orchestrator-guard,repo-containment,dod-push-check}.sh`, `1-generic/{orchestrator-guard-impl,repo-containment-impl}.sh`, `1-generic/lib/hook_common.sh`, `1-generic/release-gates/{docker-image-scan,action-pin-validation,artifact-freshness}.sh`; `scripts/lib/hooks.py:95-105` (nicht-rekursives `*.sh`-Glob je Layer: `0-external` `:95-98`, `1-generic` `:101-104`); `scripts/lib/external_tools.py:217-220` („all 0-external hooks are always copied; registration in settings.json stays opt-in per project") |
| F4 | Version driftet — **zwei** Fundstellen (Rev. 0.3) | `README.md:734` „VERSION  # Current version (**v1.0.0**)"; Ist `1.2.0-beta.2`. **Zweite Fundstelle (NEW-3):** `ARCHITECTURE.md:3` „Repo version: **0.92.0** — content last substantively reviewed: 2026-07-20"; dieselbe Zahl ist **zweimal falsch** (auch das Datum predates laut eigenem Kommentar mehrere Releases) | `README.md:734`; `ARCHITECTURE.md:3`; `VERSION:1` (`1.2.0-beta.2`); `.meta-config/project.yaml:1` (`agent-meta-version: 1.2.0-beta.2`). Die `ARCHITECTURE.md`-Deklaration wandert mit M-7 in die Langfassung (§13-A12, AC-29) |
| F5 | **Fünffache** Architektur-Doku | `ARCHITECTURE.md` (84 Zeilen; `:3` „Repo version: **0.92.0**"), `ARCHITECTURE.full.md` (Root), `docs/architecture/` (8 Dateien: `01-layer-model.md` … `07-se-cascade.md` + `prompt-modernization.md`), `knowledge/wiki/concepts/architecture*.md`, `knowledge/sources/ARCHITECTURE.full.md` | `ARCHITECTURE.md:3-4`, `:8-20`; `knowledge/wiki/index.md:24` |
| F6 | **Vierfache** Guide-Führung | `docs/guides/`, `docs/howto/`, `howto/configs/`, `knowledge/wiki/topics/` — **Reviewer-Korrektur M4:** Rev. 0.1 nannte nur drei Orte; `docs/howto/admin-ui-remote-access.md` ist ein vierter, bisher weder in F6 noch in einer Migration erfasst (→ **F23**) | `howto/` enthält **ausschließlich** `configs/`; `howto/configs/` enthält **ausschließlich** `project.yaml.example`; `docs/howto/` enthält **ausschließlich** `admin-ui-remote-access.md`; alle drei VERIFIED per Glob |
| F7 | **Vier** Spec/Plan-Bäume ohne dokumentierte Abgrenzung | `docs/specs/` (22 Einträge inkl. `.gitkeep`), `docs/plans/`, `docs/superpowers/specs/`, `docs/superpowers/plans/` | `docs/specs/`-Listing; `.meta-config/project.yaml:58-63` |
| F8 | `docs/INDEX.md` fehlt, ist aber **bereits spezifizierter Vertrag** | `DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"`; `fallback-index: docs/INDEX.md`; Szenarien 54/55/102 verlangen die Datei | `scripts/lib/spec_plan_scaffold.py:23`; `.meta-config/project.yaml:70`; `tests/scenarios/registry.md:101-102`; `tests/scenarios/asserts/54-spec-plan-external-override.sh:26-27` |
| F9 | Kein generierter Doku-Index | einziger Index-Generator im Repo ist `standalone/README.md` über `render_index()` / `write_standalone_files()` | `scripts/lib/standalone.py:309-369`, `:372-417` |
| F10 | Wiki-Index driftet strukturell | letzter `log.md`-Eintrag 2026-09-03, Specs/Pläne bis 2026-09-19 | `knowledge/wiki/log.md:30` |
| F11 | Wiki-Index deklariert seine Architekturquelle selbst als stale | `status:stale-upstream` | `knowledge/wiki/index.md:24` |
| F12 | `sync_knowledge_engine` regeneriert `index.md`/`log.md` **nie** | Docstring: „never overwrites existing `schema.md`/`wiki/index.md`/`wiki/log.md`" | `scripts/lib/knowledge.py:112-114` |
| F13 | Rollen-Parität: **falsch belegt** (Korrektur, siehe §13-A1) | `se-component-requirements` **ist** in `roles:` enthalten (`project.yaml:148`) und das Template existiert (`agents/1-generic/se-component-requirements.md`). Die Paritätsverletzung entsteht **ausschließlich** aus `systems-engineering.enabled: false` → alle 14 `se-*`-Rollen werden mit `log.skip(..., "systems-engineering is disabled")` übersprungen | `.meta-config/project.yaml:12-13, :148`; `scripts/lib/agent_sync.py:548`; `scripts/lib/roles.py:129` (`resolve_activation_gates`) |
| F14 | Pipeline-Zahl **und** Inhalt driftet | `README.md:479` „## Quality Pipelines (**7** pipelines)" listet 7 Zeilen (`:483-489`). Ist: **8** Pipelines in `config/role-defaults.yaml:2489` (`feature-lifecycle:2490`, `quick-fix:2547`, `bugfix:2572`, `concept-development:2607`, `concept-driven-dev:2633`, `refactor:2706`, `docs-update:2737`, `se-cascade:2755`), davon **7 aktiv** — deaktiviert ist ausschließlich `se-cascade` (`.meta-config/project.yaml:339-342` → `quality-pipelines.overrides.se-cascade.enabled: false`; `role-defaults.yaml:2877` `enabled: false`). **Drei** Fehler in einer Zeile: (a) Zahl 7 statt 8, (b) `concept-driven-dev` fehlt in der Tabelle **ganz**, (c) `se-cascade` steht drin, ist aber deaktiviert. *Reviewer-Korrektur K4: Rev. 0.1 nannte „6 von 7" und stufte die Zahl 7 als korrekt ein — beides falsch.* | `README.md:479-489`; `config/role-defaults.yaml:2489-2877`; `.meta-config/project.yaml:339-342` |
| F15 | **Tote Verweise** | `README.md:721-723` verweist auf `howto/setup/`, `howto/features/` (existieren nicht — `howto/` enthält nur `configs/`); `README.md:724` nennt `CLAUDE.md` als Template-Config (existiert nicht, nur `project.yaml.example`); `docs/REQUIREMENTS.md:21`; `docs/CODEBASE_OVERVIEW.md:33-44` dokumentiert `agents/1-generic/se-orchestrator.md` (existiert nicht — 14 `se-*`-Templates, keines davon `se-orchestrator`) | `README.md:721-724`; `docs/CODEBASE_OVERVIEW.md:33-44` |
| F16 | Zwei parallele ID-Systeme | `REQ-*` (Format-Regel: `docs/REQUIREMENTS.md:4`) vs. `SPEC-<NAME>-<JJJJ-MM-TT>` (z. B. `docs/specs/2026-09-15-reference-standards-design.md:2`) | beide VERIFIED |
| F17 | Generierte Provider-Verzeichnisse sind gitignored, generierte Root-Kontextdateien **nicht** | `.gitignore:13-17` (`.claude/`, `.gemini/`, `.mammouth/`, `.opencode/`, `.serena/`); für `AGENTS.md` / `CLAUDE.md` existiert **kein** Eintrag | `.gitignore:13-17` (gesamte Datei gelesen) |
| F18 | Bestehende Doku-Checks sind auf `docs/api/` begrenzt | `check_sync_cli_docs` (`:9-44`), `check_ui_help_mappings` (`:47-97`), `check_readme_docs_index` (`:100-121`, globbt **nur** `docs/api/*.md`) | `scripts/lib/consistency/docs.py` (vollständig gelesen, 122 Zeilen) |
| ~~**F19**~~ | ~~Tier-Preset-Zahl driftet~~ — **GESTRICHEN in Rev. 0.2 (K2).** `README.md:689` „tier-presets.yaml  **5** tier presets (cheap, normal, advanced, expensive, expensive as hell)" ist **korrekt**: `config/tier-presets.yaml` hat **5** Top-Level-Tiers (`Cheap:1`, `Normal:31`, `Advanced:85`, `Expensive:115`, **`Expensive as Hell:145`**). Rev. 0.1 zählte nur vier und hätte den Wert **4** generiert — eine falsche Korrektur eines richtigen Befunds. Die ID F19 wird **nicht** neu vergeben, um ID-Recycling zu vermeiden; die Nachfolger erhalten F20…F25. | `README.md:689`; `config/tier-presets.yaml:1, :31, :85, :115, :145` |
| **F20** | **Neuer Befund:** `docs/INDEX.md`-Skeleton trägt eine Textmarke, die der Generator erkennen muss | Skeleton-Text enthält die Zeile `File-based index fallback` | `tests/scenarios/asserts/54-spec-plan-external-override.sh:27`; `scripts/lib/spec_plan_scaffold.py:24` |
| **F21** | **Neuer Befund:** Rollen-Parität ist **nicht** durch `roles:` prüfbar, sondern nur gate-bewusst | `roles:` umfasst 59 Einträge (`.meta-config/project.yaml:92-150`), `config/role-defaults.yaml:1` umfasst 84 Rollen — „roles ⊄ generiert" ist ohne Gate-Auswertung ein Dauerfehlalarm | `.meta-config/project.yaml:92-150`; `config/role-defaults.yaml:1-2403`; `scripts/lib/roles.py:129, :256` |
| **F22** | **Neuer Befund (K3, erweitert in Rev. 0.3 / NEW-2):** DoD-Preset-Zahl driftet — an **zwei** Stellen | (a) `README.md:688` „dod-presets.yaml           # **6** DoD presets"; (b) `README.md:381` „## DoD Presets (**6** presets)" mit einer Tabelle, die **6** Zeilen führt und `concept-driven` **nicht** enthält — dieselbe Fehlerklasse wie F14 (fehlende Tabellenzeile). Ist **7**: `config/dod-presets.yaml:12` `presets:` → `full:13`, `standard:30`, `rapid-prototyping:46`, `spec-optional:62`, `spec-driven:79`, `concept-driven:96`, `spec-certified:113`. *Rev. 0.1 führte (a) als „korrekt, nicht zu ändern" — sie ist der Beleg, auf dem das Fehlalarm-Argument in R4 sich stützte, und ist selbst Drift. Rev. 0.2 führte (a) allein und behauptete in NF-4, `README.md:381` existiere nicht — das ist **widerlegt** (§17.4, NF-11).* | `README.md:688`; `README.md:381-390` (Überschrift + 6 Tabellenzeilen `:385-390`); `config/dod-presets.yaml:12-113` |
| **F23** | **Neuer Befund (M4):** vierter Guide-Ort ohne SSoT-Entscheidung | `docs/howto/admin-ui-remote-access.md` existiert, ist in keiner Migration und keiner SSoT-Entscheidung verortet; `howto/`-Root verschwindet (F15), `docs/howto/` bliebe als dritter Guide-Ort ohne Zuordnung stehen | Glob `docs/howto/**` (genau 1 Datei) |
| **F24** | **Neuer Befund (M4):** zwei Beispiel-Configs für denselben Zweck | `docs/guides/project.yaml.example` (**179** Zeilen) und `howto/configs/project.yaml.example` (**340** Zeilen). Nach M-5 liegen **beide** unter `docs/guides/` — eine SSoT-Entscheidung ist nicht getroffen; sie ist eine **inhaltliche** Frage (NG-1) und daher **OQ9** | Dateilängen per Read bestätigt (179 / 340 Zeilen, Endzeilen gelesen) |
| **F25** | **Neuer Befund (R15):** Config-Schema kennt die neuen Keys nicht | `config/project-config.schema.json` (2645 Zeilen) enthält keinen `docs-consolidation`-Block; das Wurzel-Schema ist `additionalProperties: true` (`:2425`) — die Keys würden also **nicht** validiert, aber auch **nicht** per IDE-Autocomplete angeboten. Das Repo nutzt geschlossene Unterobjekte ausdrücklich als Tippfehler-Wächter (Selbstauskunft `:2058`, `:2073`) | `config/project-config.schema.json:2425, :2058, :2073` |

**Korrekt und daher nicht zu ändern** (Beleg, damit V1 keinen Fehlalarm erzeugt):

| Zeile | Aussage | Warum korrekt |
|---|---|---|
| `README.md:689` | „5 tier presets (cheap, normal, advanced, expensive, expensive as hell)" | `config/tier-presets.yaml` hat **5** Top-Level-Tiers (`:1, :31, :85, :115, :145`) — **Reviewer-Korrektur K2**, Rev. 0.1 hatte diese Zeile fälschlich als Drift geführt |
| `README.md:695` | „22 slash-command definitions" | `commands/1-generic/*.md` = **22** Dateien (Glob) |

> **Konsequenz für R4:** Rev. 0.1 stützte sein V1-Fehlalarm-Argument auf `README.md:688`
> („6 DoD presets ist korrekt"). Diese Zeile ist **Drift** (F22), das Argument trägt nicht mehr,
> und R4 wird in §12 entsprechend neu begründet.

### 1.2 Quantifizierter Zielzustand

| Metrik | Ist (2026-09-26) | Ziel nach W8 | Prüfbar durch |
|---|---|---|---|
| manuell gepflegte Zahlen in `README.md` / `llms.txt` / `ARCHITECTURE.md` | **11** = 10 in `README.md` (F1, F2, F3 ×2, F4, F14 ×3, **F22 ×2** — nach NEW-2 mit `README.md:381`) + 1 in `ARCHITECTURE.md:3` (F4). `llms.txt:5` ist eine Prosa-Aufzählung (6 von 9 Providernamen), **keine** Zahl → nicht mitgezählt, inhaltlich über AC-40 behoben | **0** | V1a (Counts), V1b (Versions-Literal) — AC-07/AC-08 |
| Doku-Bäume mit demselben SSoT-Gegenstand | 5 (Architektur), **4** (Guides, korrigiert), 4 (Spec/Plan) | 1 / 1 / 1 (+ archivierte Legacy-Bäume) | V2, V8 |
| `docs/INDEX.md` | existiert nicht | existiert, 100 % generiert, tracked | V2, V4 |
| tote relative interne Links in `docs/**` + `README.md` + `llms.txt` | ≥ 4 (F15) | **0** | V3 |
| Wiki-Seiten ohne `derived-from` bei `type: Architecture` | nicht erhebbar ohne Generator | **0**; alle übrigen Abweichungen nur WARN | V7 |
| `log.md` Alterung | 4 Wochen (F10) | 1 Zeile pro Sync mit Wiki-Änderung | V7 + W7 |
| **unabhängig gepflegte Sollwerte** (Handpflege, nicht aus der Formel abgeleitet) | **0** — kein Gate prüft die Formel gegen eine unabhängige Zahl (R14) | **elf** Werte in `config/doc-facts-expected.yaml` (IC-23), geprüft von einem Test | AC-36 (IC-23) |

---

## 2. Ziel / Nicht-Ziele

### 2.1 Ziel

1. **Jede Zahl in der Einstiegs-Doku ist berechnet, nicht geschrieben.** Eine einzige
   Faktum-Berechnung (`doc_facts.py`) liefert `DOCS_*`-Werte aus den jeweils kanonischen
   Quellen; Rendering und Checks konsumieren dieselbe Quelle — **und** eine zweite,
   unabhängig handgepflegte Datei (`config/doc-facts-expected.yaml`, IC-23) prüft die Formel
   von außen, damit ein systematisch falscher Faktor nicht alle Gates passiert (R14).
2. **Ein kanonischer Doku-Index** (`docs/INDEX.md`, generiert) erfüllt den bereits
   spezifizierten, aber unerfüllten Vertrag aus `spec_plan_scaffold.py:23`.
3. **Verify-by-construction:** die Doku-Checks V1–V9 machen die in §1.1 dokumentierten
   Fehlerklassen *nicht wiederholbar*, statt sie einmal zu korrigieren.
4. **Staleness wird maschinell.** `derived-from` + `derived-at` + Quell-mtime liefern
   `status: stale-source`; das Wiki bleibt ein **abgeleiteter Schatten** mit Herkunftsangabe
   und wird nie ein zweiter Architektur-SSoT.
5. **Migration ohne Inhaltsverlust:** alle Pfadverschiebungen sind `git mv`; keine
   Neuschreibung bestehender Guide- oder Architektur-Inhalte.
6. **Additive, abwesenheits-tolerante Defaults.** Kein Key dieser Initiative verändert
   bestehendes Verhalten, wenn er nicht explizit gesetzt ist — für **Writer und Checks
   gleichermaßen** (Präzedenz `knowledge.py:127-129`).

### 2.2 Nicht-Ziele (hart — Abweichung gilt als Spec-Verstoß)

| # | Nicht-Ziel | Begründung / Beleg |
|---|---|---|
| NG-1 | **Keine inhaltliche Neuschreibung** bestehender Guides, Architektur-Dokumente oder Wiki-Seiten | R9; Migrationswellen sind `git mv` + Marker + Annotationszeilen. Inhaltsarbeit ist eigene REQ. |
| NG-2 | **Keine Mutation an `knowledge/sources/`.** Append-only; nur `knowledge-ingestor` schreibt, `knowledge-curator`/`knowledge-gardener` haben dort kein Schreibrecht | Design §5.1; Policy-Zanker `knowledge/schema.md:44-46` („Removing or renaming an existing type is a structural change and requires user sign-off") |
| NG-3 | **Keine Änderung der Doku-Ownership.** `docs/CODEBASE_OVERVIEW.md` gehört dem `documenter`-Agenten; diese Spec erzeugt dort ausschließlich einen generierten Fakten-Footer und **keinen** Inhalt | `knowledge/wiki/log.md:30` („docs/CODEBASE_OVERVIEW.md bewusst NICHT migriert (HARD CONSTRAINT — gehört documenter-Agent)"); Design R11 |
| NG-4 | **Kein neues `sync.py`-CLI-Flag.** Jedes Flag wäre in `docs/api/cli-reference.md` zu dokumentieren (`consistency/docs.py:9-44` erzwingt das als `Severity.ERROR`) und erzeugte damit selbst Doku-Drift | Design T-5; `scripts/lib/consistency/docs.py:34-42` |
| NG-5 | **Kein Eingriff in generierte Kontextdateien** (`AGENTS.md`, `CLAUDE.md`, Provider-Verzeichnisse) außer dem in M3 beschriebenen, config-seitigen `PROJECT_STRUCTURE`-Korrektur-Edit | Design §7.1; `.gitignore:13-17` |
| NG-6 | **Keine Umbenennung bestehender `SPEC-*`-IDs.** `SPEC-<NAME>-<JJJJ-MM-TT>` bleibt; das Verhältnis zu `REQ-*` wird nur *dokumentiert* (OQ4) | F16; Design OQ4 |
| NG-7 | **Keine Umbenennung/Veröffentlichung von `docs/INDEX.md` in ein anderes Schema** (`docs/README.md` verworfen) | Design T-3; `spec_plan_scaffold.py:23` ist der bestehende Vertrag |
| NG-8 | **Kein Rollen-Paritäts-Fix.** `se-component-requirements` bleibt in `roles:`, die Parität bleibt über den SE-Gate geregelt; V5 wird **gate-bewusst** gebaut, nicht am `roles:`-Listeninhalt | F13/F21-Korrektur, §13-A2; Fix wäre ein Config-Edit und gehört in eigene REQ |
| NG-9 | **Kein Rollout in Consumer-Projekte ohne Opt-in.** `docs-consolidation.enabled` ist **in allen** Projektlayouts per Default `false` — auch in agent-meta selbst wird der Wert **explizit** `true` gesetzt (`.meta-config/project.yaml`, W1). Damit ist die Absenz-Semantik identisch zur Fail-off-Präzedenz `knowledge.py:127` (`ke_config.get("enabled", False)`) und erzeugt **keinen** ungewollten Verhaltenswechsel in den Szenario-Fixtures | Design §3.4 (angepasst, siehe §13-A10); agent-meta ist Submodul in Fremdprojekten (Downstream-Kompatibilität) |
| NG-10 | **Keine Änderung an den Szenarien 50–56.** Sie sind der bestehende Regressionstest für den `docs/INDEX.md`-Vertrag. Diese Spec passt sich **ihnen** an (Absenz-Defaults, Besitzregel, `knowledge-engine`-Schreibverbot) — nicht umgekehrt | `tests/scenarios/registry.md:97-103`; IC-13, IC-15, AC-38 |
| NG-11 | **Kein Platzhalter-Marker in generierten Provider-Dateien.** `DOCS_*`-Platzhalter werden ausschließlich von E3 (`doc_renderer`) aufgelöst, nie von E1/E2 — sonst würden sie in Consumer-Provider-Dateien landen | IC-11, OQ5 (geschlossen, §11) |

### 2.3 Scope-Grenzen gegen Nachbar-Initiativen

- **Track A** (parallel, arbeitet in `tests/`, `tests/fixtures/`, `scripts/lib/`, `config/`):
  W1/W2 werden **nicht** parallel zu Track A gestartet. Vor W1: `git log --oneline -20 -- scripts/lib/`
  prüfen; pro Welle ein Commit pro Datei; vor jedem Merge Rebase gegen den Track-A-Branch
  (Design R3). **Neu (R15/§2.3-A):** Track A committet derzeit in
  `tests/fixtures/slimming-golden/`; die in AC-07/AC-08 spezifizierte V1-Fixture
  (`tests/fixtures/docs_v1_fixtures.md`) darf deshalb **nicht** angelegt werden, bevor der
  Track-A-Branch gemergt ist. Ownership-Konflikt, kein Berechtigungs-Konflikt.
- **Szenario `64-docs-facts-drift.md`**: von **Track A** verfasst, nicht in dieser Initiative
  (Design §4, Ownership-Konflikt). Diese Spec definiert nur das Verhalten, das es prüft
  (AC-15). **Nummerierungskorrektur (Rev. 0.2, §17.1-NF-1):** das Design nennt
  `63-docs-facts-drift.md`, die Nummer **63 ist im Repo bereits vergeben**
  (`registry.md:110` = `63-context-file-modes`, `asserts/63-context-file-modes.sh`,
  `configs/63-context-file-modes.project.yaml`). Korrekt ist **64**.
- **Der AGENTS.md-Bootstrap-Block** (66 hartgelistete Agenten am Repo-Ende) driftet
  ebenfalls, ist aber **bewusst außerhalb** des Scopes (OQ3, Design R10).

---

## 3. Zielstruktur / SSoT-Matrix

### 3.1 Generationsmodi (verbindliche Definition)

| Modus | Definition | Schreibrecht | Drift-Folge |
|---|---|---|---|
| **generiert** | Datei ist 100 % Generator-Output; Handedit ist ein Fehler | Generator | V6 (ERROR) |
| **hybrid** | Handprosa + generierte Marker-Regionen (`agent-meta:docs-*`) | Mensch außerhalb, Generator innerhalb der Marker | V1 (ERROR ab W2-Ende), V6 (ERROR) |
| **handgepflegt** |rein manuell; nur optionaler generierter Fakten-Footer | Mensch | keiner (bewusst) |
| **redirect** | reine Verweis-Seite ohne eigenen Inhalt, zeigt auf das SSoT | Mensch (ein Link) | V3 (ERROR auf toten Link) |
| **archiviert** | historischer Beleg, nicht mehr referenziert | keines | keiner |

### 3.2 SSoT-Matrix: Faktumklasse → kanonische Quelle → Konsumenten → Modus

| Faktumklasse | Kanonische Quelle (SSoT) | Konsumenten | Modus |
|---|---|---|---|
| Version | `VERSION` (gelesen via `read_version()`, `scripts/lib/config.py:1060-1064`) | `README.md`, `llms.txt`, `ARCHITECTURE.md`, `docs/INDEX.md` | generiert (Faktenblock) |
| Agenten-Templates gesamt / SE / non-SE | `agents/1-generic/*.md` mit Frontmatter `name` (80 Dateien, 3 `_*`-Helper ausgeschlossen) | `README.md:122`, `docs/INDEX.md` | generiert |
| Rollen **aktiv** (erzeugte Provider-Dateien) | `roles:` (`.meta-config/project.yaml:92-150`) ∩ Templates ∩ `resolve_activation_gates()` (`scripts/lib/roles.py:129`) | `README.md`, `docs/INDEX.md` | generiert |
| Hooks | `hooks/**/*.sh`, Top-Level-Regel ohne `lib/`, ohne `release-gates/`, **ohne `*-impl.sh`** → **11** deploybare Hooks (`DOCS_HOOKS_COUNT`, global, „propagated to all providers"); für die Verzeichnis-Zeile `README.md:696` ein **eigenes, enger gebundenes** Faktum `DOCS_HOOKS_1GENERIC_COUNT` = `hooks/1-generic/*.sh` ohne `*-impl.sh` → **9** | `README.md:501` → 11 (`DOCS_HOOKS_COUNT`), `README.md:696` → 9 (`DOCS_HOOKS_1GENERIC_COUNT`), `docs/INDEX.md` → `DOCS_HOOKS_BLOCK` | generiert |
| Provider | `config/ai-providers.yaml:1` → 9 Blöcke | `README.md:690`, `llms.txt:5`, `docs/INDEX.md` | generiert |
| Pipelines (mit Enabled-Status) | `config/role-defaults.yaml:2489` (8) ∩ `.meta-config/project.yaml:339-343` → 7 aktiv | `README.md:479-489`, `docs/INDEX.md` | generiert |
| DoD-Presets / Tier-Presets | `config/dod-presets.yaml:12` (7) / `config/tier-presets.yaml:1, :31, :85, :115, :145` (5) | `README.md:381-390` (Überschrift **und** Preset-Tabelle, F22 b) → 7, `README.md:688` (F22 a) → 7, `README.md:689` → 5 | generiert |
| Commands | `commands/1-generic/` | `README.md:695` | generiert |
| Szenarien (**volatil**) | `tests/scenarios/asserts/*.sh` (63 Dateien) | **nur** `docs/INDEX.md`, in einer `docs-volatile`-Sektion **am Dateiende vor dem Footer** und **nicht** im `facts-hash` (R1) | generiert, README/llms ausgeschlossen (R1) |
| Doku-Baum + 1-Zeilen-Beschreibungen | Dateisystem `docs/**/*.md` + Frontmatter `description` | `docs/INDEX.md`, `docs/architecture/INDEX.md` | generiert |
| Doku-Architektur-Langfassung | `docs/architecture/00-overview-full.md` (aus Root via `git mv`) | `ARCHITECTURE.md` (Stub), `llms.txt:24` | handgepflegt |
| Architektur-Detailseiten | `docs/architecture/01…07` | `ARCHITECTURE.md`-Stub, `docs/architecture/INDEX.md` | handgepflegt |
| Architektur-Diagramm-Index | `ARCHITECTURE.md` (Diagramm-Tabelle `:8-20`) | `llms.txt:24`, Root | generierter Stub (T-4) |
| Guides | `docs/guides/` (inkl. M-6 aus `docs/howto/`) | `docs/INDEX.md`, Wiki-Redirects | handgepflegt |
| Beispiel-Configs | `docs/guides/configs/project.yaml.example` (340 Z, aus `howto/configs/`, M-5) **und** `docs/guides/project.yaml.example` (179 Z, bereits vorhanden) — **SSoT zwischen beiden ungeklärt → OQ9**; bis zur Entscheidung bleiben **beide** bestehen (kein Merge, NG-1) | `docs/INDEX.md` | handgepflegt |
| Provider-Referenz | `docs/providers/` (6 von 9 — Lücke als Befund) | `docs/INDEX.md` | handgepflegt |
| CLI-/UI-Referenz | `docs/api/` (7 Dateien) | `README.md` (V4), `llms.txt:17-19` | handgepflegt |
| Specs / Pläne / Spikes | `docs/specs/`, `docs/plans/`, `docs/spikes/` (`.meta-config/project.yaml:58-60`) | `docs/INDEX.md` | handgepflegt / archiviert |
| Spec-Plan-Legacy | `docs/superpowers/{specs,plans}` → `docs/{specs,plans}/archive/superpowers/` | keiner (historisch) | archiviert |
| Doku-Index | `docs/INDEX.md` | alle Doku-Konsumenten | generiert |
| Knowledge-Quellen | `knowledge/sources/` | Wiki (nur lesend) | **unveränderlich** (NG-2) |
| Knowledge-Wiki-Seiten | `knowledge/wiki/{concepts,entities,topics,plans,specs,sources,queries}/` | `knowledge/wiki/index.md` | handgepflegt (LLM) + Pflicht-`derived-from` |
| Knowledge-Index | `knowledge/wiki/index.md` | Knowledge-Agenten | generiert (W7, Flag-gated) |
| Knowledge-Log | `knowledge/wiki/log.md` | Knowledge-Agenten | hybrid (Generator-Append + manuell) |
| `docs/CODEBASE_OVERVIEW.md` | `documenter`-Agent | Nutzer | handgepflegt, **nur** Fakten-Footer (NG-3) |
| Anforderungen | `docs/REQUIREMENTS.md` (`REQ-*`, Format `:4`) | `validator` | handgepflegt |

### 3.3 SSoT-Entscheidung je Bereich (aus Design §1.1, unverändert übernommen)

| Bereich | SSoT | Wird Stub/Redirect | Wird archiviert | Verschwindet |
|---|---|---|---|---|
| Root-Doku | `README.md` (Handprosa) + `DOCS_*`-Faktenblöcke | `ARCHITECTURE.md` → generierter Pointer auf `docs/architecture/INDEX.md` | — | `howto/`-Root (F15) |
| docs-INDEX | `docs/INDEX.md`, 100 % generiert | — | — | kein `docs/README.md` (T-3/T-4) |
| Architektur | `docs/architecture/` (00 + 01–07 + `prompt-modernization.md`) | Root-`ARCHITECTURE.md`; `knowledge/wiki/concepts/architecture*.md` → Verweis-Seiten | `ARCHITECTURE.full.md` → `docs/architecture/00-overview-full.md` | keiner |
| Guides | `docs/guides/` | `knowledge/wiki/topics/*-guide*` → Redirect | `howto/configs/` → `docs/guides/configs/`; `docs/howto/admin-ui-remote-access.md` → `docs/guides/admin-ui-remote-access.md` (M-6) | `howto/`-Root (F15), `docs/howto/`-Root (F23) |
| Specs/Pläne | `docs/specs/`, `docs/plans/`, `docs/spikes/` | — | `docs/superpowers/{specs,plans}` → `docs/{specs,plans}/archive/superpowers/` | `docs/superpowers/` |
| Knowledge-Wiki | **kein SSoT** — abgeleiteter Schatten | alle mit `derived-from` | `knowledge/sources/` bleibt unverändert | keiner |
| Traceability | `docs/REQUIREMENTS.md` (`REQ-*`) | — | `SPEC-*`-Naming bleibt (NG-6) | — |

---

## 4. Modulaufteilung (vier in sich abgeschlossene Module, eine Spec-Datei)

Begründung der Ein-Datei-Entscheidung: die Repo-Konvention verlangt **eine** Spec-Datei pro
`spec-id` mit Frontmatter-`spec-id` (`docs/specs/2026-09-15-reference-standards-design.md:1-8`,
`docs/specs/2026-09-13-stale-role-cleanup-design.md:1-9`) und einen `Trace-Anker`-Block; sie
verlangt **nicht** genau eine Datei für vier Wellen-Gruppen. Das Design empfahl in §11 vier
Wellen-Specs. Diese Spec hält die vier Module als **getrennte, in sich abgeschlossene
Abschnitte mit eigenen ICs, ACs, Wellen und Rollback-Punkten**; eine Aufteilung in vier
Dateien ist eine **Planungsentscheidung** und wird hier **nicht** vorweggenommen
(**OQ7 — geschlossen**, §11).

| Modul | Verantwortung (genau eine) | Dateien (Code) | Wellen | Vorgänger | Rollback |
|---|---|---|---|---|---|
| **M1 — DocFacts + Doku-Checks** | Berechnet `DOCS_*`-Fakten und bewertet Doku-Drift | `scripts/lib/doc_facts.py` (neu), `scripts/lib/consistency/docs.py` (erweitert), `scripts/consistency-check.py` (Registrierung), `scripts/lib/consistency/placeholders.py` (Namespace), `config/doc-facts-expected.yaml` (neu, handgepflegt) | W1, W2 | — | `docs-consolidation.checks.strict: false`; `docs-consolidation.enabled: false` |
| **M2 — Renderer + Indexer + Brücke** | Rendert `docs/INDEX.md` und `DOCS_*`-Blöcke; garantiert Idempotenz, `dry_run`, Fact-Hash | `scripts/lib/doc_renderer.py` (neu), `scripts/lib/doc_index.py` (neu), `scripts/lib/config.py` (Snippet-Bridge), `scripts/lib/sync_pipeline.py` (Stage), `scripts/lib/spec_plan_scaffold.py` (Guard), `scripts/lib/generated_file_drift.py` (Docs-Dateiliste), `snippets/docs/*.md` (neu) | W1, W3, W4 | M1 | `git rm docs/INDEX.md`; Marker entfernen; `docs-consolidation.enabled: false` |
| **M3 — Migration** | Pfadverschiebungen und Marker-Regionen (`git mv`, kein Inhalts-Rewrite) | keine neuen Code-Dateien; `README.md`, `ARCHITECTURE.md`, `.meta-config/project.yaml`, `config/project-config.schema.json`, `docs/**` | W4, W5, W6, W8 | M2 (W3) | je Welle: `git mv` zurück; Config-Key additiv → Zeile entfernen |
| **M4 — Knowledge-Index-Generierung** | Rendert `knowledge/wiki/index.md` deterministisch; hängt `log.md` an | `scripts/lib/knowledge.py` (erweitert), `agents/1-generic/knowledge-indexer.md` (Umschreibung) | W7 | M3 (W5) | `knowledge-engine.okf.index-mode: llm` → Generator stumm; `restore_wiki_index()` (IC-24) |

**Test-Dateien** (von der Implementierung zu erzeugen, kein Produktions-Footprint, aber vom
Plan zu berücksichtigen — Dateinamen sind über die ACs verbindlich festgelegt):
`tests/test_doc_facts.py`, `tests/test_doc_renderer.py`, `tests/test_generated_file_drift_docs.py`,
`tests/test_knowledge_index_gen.py`, `tests/test_docs_consolidation_migration.py`,
`tests/fixtures/docs_v1_fixtures.md` (V1-Fixture, AC-07/AC-08).

**Schichtungs-Invariante (unverändert, Design §2):** M1 ist das stdlib-only-Blatt ohne
Doku-Dateisystem-Wissen; M2 konsumiert M1; M3 ist reiner Datenumzug ohne Code; M4 ist ein
Schwester-Modul zu M2, das M1 **nicht** importiert (kein Zyklus, keine Kopplung).

---

## 5. Interface Contracts

Alle neuen Module sind **stdlib-only** und folgen der Dependency-Invariante
`scripts/lib/variables.py:9-17` (keine Zyklen, neutraler Boden unten). Docstrings, Naming
(snake_case) und `from __future__ import annotations` folgen `scripts/lib/spec_plan_scaffold.py:12`.

### 5.1 Modul M1 — DocFacts

#### IC-01 — `scripts/lib/doc_facts.py` (neu): Faktum-API

```python
# scripts/lib/doc_facts.py
"""Berechnet die DOCS_*-Fakten aus den kanonischen Quellen (SSoT je Faktumklasse).

Neutrales Blatt: kennt keine Doku-Datei, liest keine Handprosa, schreibt nichts.
Alle nicht berechenbaren Faktuen ergeben "" (fail-soft, identisch zum
_load_block_snippet-Vertrag, config.py:1850-1851).
"""
from __future__ import annotations

from pathlib import Path

# Exklusionsregeln Hook-Zaehlung — kodieren die README:501-vs-:696-Widerspruechlichkeit
# strukturell (Design §3.2), nicht per Korrektur. Die beiden Regeln sind KEINE
# Alternativen, sondern gelten fuer verschiedene Fragen (siehe Aufloesung M1).
# ACHTUNG (rev. 0.3, NF-12): die Suffix-Regel muss "-impl.sh" (Bindestrich) lauten, nicht
# "_impl.sh" — die Dateien heissen `orchestrator-guard-impl.sh` / `repo-containment-impl.sh`
# (verifiziert per Glob). Mit "_impl.sh" wuerde die Regel nichts matchen und DOCS_HOOKS_COUNT
# liefe auf 13 statt 11.
HOOK_EXCLUDED_DIRS: frozenset[str] = frozenset({"lib", "release-gates"})
HOOK_EXCLUDED_SUFFIXES: tuple[str, ...] = ("-impl.sh",)
AGENT_HELPER_PREFIX: str = "_"

def compute_doc_facts(
    agent_meta_root: Path,
    config: dict,
    *,
    provider_config: dict | None = None,
    log=None,
) -> dict[str, str]:
    """Return the full DOCS_* fact dict. Never raises on a missing source."""
```

**Fehlerpfade:** `agent_meta_root` existiert nicht → alle Faktuen `""` plus ein
`log.debug`-Eintrag (kein Abbruch). Eine einzelne Quelle ist unlesbar → nur dieses Faktum
`""`. **Kein** `SyncError` — der Generator darf nie einen Sync wegen einer Zahl abbrechen.

**M1-Auflösung (verbindlich, rev. 0.3):** `HOOK_EXCLUDED_DIRS` und `HOOK_EXCLUDED_SUFFIXES` werden
**beide** angewandt — aber auf **zwei verschiedene, je Frage und je Zielstelle benannte**
Faktum-Keys. Damit entfällt die Frage „welche Zahl gilt?" **und** die Frage „welche Zahl gehört an
diese Zeile?":

| Key | Regel | VERIFIED 2026-09-26 | Beantwortet | Einzige Zielstelle |
|---|---|---|---|---|
| `DOCS_HOOKS_COUNT` | `hooks/**/*.sh` **ohne** `lib`, **ohne** `release-gates`, **ohne** `*-impl.sh` | **11** | „Wie viele Hooks werden registriert und an alle Provider propagiert?" — die Frage, die die **Überschrift** `README.md:501` stellt | `README.md:501` |
| `DOCS_HOOKS_1GENERIC_COUNT` | `hooks/1-generic/*.sh` (**nicht-rekursiv**, wie der Collector) **ohne** `*-impl.sh` | **9** | „Wie viele Hook-Skripte liegen in dem Verzeichnis, das diese Zeile **namentlich** nennt?" — die Frage, die die **Tree-Zeile** `README.md:696` stellt | `README.md:696` |

**Warum zwei Keys und nicht einer (rev. 0.3, NEW-1).** Die beiden Zielstellen stellen zwei
verschiedene Fragen, und Rev. 0.2 hat sie mit einem globalen Key beantwortet, der an der zweiten
Stelle **semantisch nicht passt**:

- `README.md:501` liegt in der **Hooks-Sektion** und fragt nach der **Anzahl** der Hooks, die an
  alle Provider propagiert werden — eine Aussage über den **gesamten** `hooks/`-Baum. Hier ist **11**
  richtig: 2 `0-external/` + 11 top-level `1-generic/` − 2 `*-impl.sh`. Die Registrierung dieser
  11 erfolgt durch `sync_hooks()`, das `0-external` (`:95-98`) und `1-generic` (`:101-104`)
  nicht-rekursiv je Layer sammelt und `2-platform`-Overrides darüber legt (`hooks/2-platform/`
  enthält heute nur `.gitkeep`).
- `README.md:696` ist eine **Zeile im Verzeichnisbaum** und nennt den Pfad `hooks/1-generic/`
  selbst. Ihre Zahl kann daher nur eine Eigenschaft **dieses Verzeichnisses** sein. Der
  17er-Wert zählt `hooks/**` und hätte dort eine Zahl über einen anderen Pfad behauptet — genau
  die F19/F22-Fehlerklasse („Zahl steht an einer Stelle, gilt aber für eine andere"). Echte
  `.sh`-Dateien in `hooks/1-generic/` auf Top-Level sind **11**; zwei davon sind
  `*-impl.sh`-Geschwister von `orchestrator-guard.sh` / `repo-containment.sh` (Helper, keine
  Hooks — dieselbe Einstufung wie in `DOCS_HOOKS_COUNT`, konsistent mit
  `consistency/repo_containment.py:22` „hook wrapper/impl"). Also **9**.

**Verbindliche Renderform (keine Auslegungsspielräume):**

- `README.md:501` → `## Hooks ({{DOCS_HOOKS_COUNT}} hooks, propagated to all providers)`
- `README.md:696` → `hooks/1-generic/               # {{DOCS_HOOKS_1GENERIC_COUNT}} hook scripts (+2 *-impl.sh helpers)`
  Der Klammerzuschlag ist **verpflichtend**, weil er den Dateizähler (11) vom Hook-Zähler (9)
  unterscheidet; ohne ihn wäre die Zeile mit `ls hooks/1-generic/*.sh | wc -l` nicht
  reproduzierbar.

**Ausdrücklich gestrichen (rev. 0.3):** `DOCS_HOOK_SCRIPT_FILES_COUNT == 17` aus Rev. 0.2. Die 17
bleiben eine **Belegzahl in §1.1 (F3)** und in §16, sind aber **kein `DOCS_*`-Faktum**: es gibt
keine README-Zeile, die „alle Hook-Skript-Dateien im Repo" behauptet, und ein Faktum ohne
Zielstelle wäre eine zweite, ungeprüfte Zahl in genau der Datei, die diese Spec bereinigen soll.
Ein späteres Bedürfnis nach dieser Zahl (z. B. `docs/INDEX.md`) braucht eine eigene, neu
verifizierte Zielstelle — nicht die Wiederverwendung dieser Zahl.

**Kreuz-Rendering ist verboten:** `DOCS_HOOKS_COUNT` wird **nicht** in `README.md:696` gerendert
und `DOCS_HOOKS_1GENERIC_COUNT` **nicht** in `README.md:501`. Die früher widersprüchliche
Doppelangabe („7" vs. „5") entsteht dann nicht mehr, weil zwei verschiedene Fragen zwei
verschiedene Keys **mit je eigener Zielstelle** bekommen.

#### IC-02 — Faktum-Vertrag (Platzhalter → Quelle → Formel)

Alle Werte sind **Strings**. `volatile: true` markiert Faktuen, die in `README.md` und
`llms.txt` **nicht** gerendert werden dürfen (R1).

| Platzhalter | Quelle (kanonisch) | Berechnungsregel | `volatile` |
|---|---|---|---|
| `DOCS_VERSION` | `VERSION` via `read_version()` (`config.py:1060-1064`) | exakter Dateiinhalt, `strip()` | nein |
| `DOCS_AGENT_TEMPLATES_COUNT` | `agents/1-generic/*.md` | Anzahl Dateien mit Frontmatter-`name`, ohne `_*`-Präfix (VERIFIED heute: 80) | nein |
| `DOCS_AGENTS_SE_COUNT` | dito | Teilmenge mit Namenspräfix `se-` (VERIFIED heute: 14) | nein |
| `DOCS_AGENTS_NONSE_COUNT` | dito | Differenz (VERIFIED heute: 66) | nein |
| `DOCS_AGENTS_ACTIVE_COUNT` | `roles:` (`project.yaml:92-150`) ∩ Templates ∩ `resolve_activation_gates()` (`roles.py:129`) | `len(...)` — **nicht** `len(roles)`, um F13/F21 nicht zu reproduzieren | nein |
| `DOCS_HOOKS_COUNT` | `hooks/**/*.sh` | `HOOK_EXCLUDED_DIRS` **und** `HOOK_EXCLUDED_SUFFIXES` (VERIFIED heute: **11**); renders **ausschließlich** in `README.md:501` | nein |
| `DOCS_HOOKS_1GENERIC_COUNT` | `hooks/1-generic/*.sh` (nicht-rekursiv) | `HOOK_EXCLUDED_SUFFIXES` (VERIFIED heute: **9**); renders **ausschließlich** in `README.md:696` | nein |
| `DOCS_PROVIDER_COUNT` | `config/ai-providers.yaml:1` | `len(data["providers"])` (VERIFIED heute: 9) | nein |
| `DOCS_PIPELINES_COUNT` | `config/role-defaults.yaml:2489` | Top-Level-Keys unter `quality_pipelines:` — **inkl.** disabled (VERIFIED heute: **8**) | nein |
| `DOCS_PIPELINES_ACTIVE_COUNT` | dito ∩ `project.yaml:339-343` | nur `enabled != false` **nach** Merge der `quality-pipelines.overrides` (VERIFIED heute: **7 von 8**) | nein |
| `DOCS_DOD_PRESET_COUNT` | `config/dod-presets.yaml:12` | `len(presets)` (VERIFIED heute: **7**) | nein |
| `DOCS_TIER_PRESET_COUNT` | `config/tier-presets.yaml` | Top-Level-Keys (VERIFIED heute: **5** — Korrektur von Rev. 0.1, das fälschlich 4 behauptete) | nein |
| `DOCS_COMMAND_COUNT` | `commands/1-generic/` | Anzahl `*.md` | nein |
| `DOCS_SCENARIO_COUNT` | `tests/scenarios/asserts/*.sh` (VERIFIED heute: 63) | `len(glob("*.sh"))` — **nicht** `tests/scenarios/*.md` (dort liegt nur `registry.md`) | **ja** |
| `DOCS_DOCS_FILE_COUNT` | `docs/**/*.md` | ohne Pfadsegment `_archive` / `archive` | nein |
| `DOCS_AGENT_ROSTER_BLOCK` | Templates + `config/role-defaults.yaml` | Markdown-Tabelle, eine Zeile je Rolle | nein |
| `DOCS_PIPELINES_BLOCK` | dito | Tabelle **mit** Enabled-Spalte | nein |
| `DOCS_HOOKS_BLOCK` | `hooks/**/*.sh` | Tabelle Hook/Trigger/Pfad | nein |
| `DOCS_PROVIDERS_BLOCK` | `config/ai-providers.yaml` | Tabelle Provider/Verzeichnis/Capabilities | nein |
| `DOCS_TIER_PRESET_BLOCK` | `config/tier-presets.yaml` | Tabelle Tier/Modell (5 Zeilen) | nein |
| `DOCS_DOD_PRESET_BLOCK` | `config/dod-presets.yaml` | Tabelle Preset/Begründung (7 Zeilen) | nein |
| `DOCS_REPO_FACTS_BLOCK` | alle obigen **ohne** volatile | kompakter Faktenblock für `llms.txt` | nein |

**Schlüsselzahl: 23** (17 Skalar + 6 `*_BLOCK`). `DOCS_TIER_PRESET_COUNT` und
`DOCS_DOD_PRESET_COUNT` bleiben **beide** erhalten: F22 (DoD) ist ein Drift-Befund, F19
(Tier) war keiner — die Zahl wird unabhängig vom Befundstatus berechnet, weil ein SSoT-Faktum
nicht davon abhängt, ob die heutige Doku gerade richtig oder falsch ist.

**Nicht im Namespace:** `DOCS_LANGUAGE` und `INTERNAL_DOCS_LANGUAGE` sind **bereits**
existierende Built-ins (`.meta-config/project.yaml:183-184`) und dürfen **nicht** von
`doc_facts.py` belegt oder überschrieben werden. Namensraum-Disziplin: `*_BLOCK` ist belegt
(`QUALITY_PIPELINES_BLOCK`, `config.py:1882`); alle neuen Namen tragen zwingend `DOCS_`-Präfix.

#### IC-03 — `scripts/lib/doc_facts.py` :: Staleness-Resolver (gate-bewusst)

```python
def compute_wiki_staleness(wiki_root: Path, project_root: Path) -> dict[str, str]:
    """Map rel-wiki-page-path -> computed status tag ("" = fresh).

    status:stale-source  iff mtime(derived-from target) > derived-at
    status:age-<n>d      iff floor((now - derived-at).days) == n  (observation, not a status)
    """
```

- `type: Architecture` **ohne** `derived-from` → Ergebnis `"missing-derived-from"`; dieser
  Wert ist die V7-ERROR-Quelle (siehe IC-05).
- `status:stale-upstream` (aktuell manuell gepflegt, `knowledge/wiki/index.md:24`) bleibt als
  historisches Tag **erhalten**, wird aber nicht mehr manuell gepflegt, sondern maschinell
  extrahiert. **Quelle ist `docs/architecture/00-overview-full.md` — NICHT `ARCHITECTURE.md`**:
  `knowledge/wiki/index.md:24` beschreibt die Wiki-Seite `concepts/architecture.md` als
  „Rohkopie von **ARCHITECTURE.full.md**", und `ARCHITECTURE.md:3` („Repo version: **0.92.0**
  — content last substantively reviewed: 2026-07-20") ist lediglich der **Stub**, der auf die
  Langfassung verweist. Nach M-1 wandert der Text in die Langfassung, nach M-2 verschwindet er
  aus dem Stub ⇒ liest man weiter aus dem Stub, ist die Quelle nach W4 **weg** und V7 bekäme
  keinen Träger (das ist der Zirkelschluss aus M5). Deshalb wandert die Extraktionsquelle mit
  (M-7 in IC-17) und AC-29 prüft beide Seiten getrennt.

#### IC-04 — `scripts/lib/doc_facts.py` :: aktive-Rollen-Menge (F13/F21-Korrektur)

```python
def compute_active_roles(
    agent_meta_root: Path, config: dict, provider_config: dict | None = None
) -> set[str]:
    """Rollen, die sync.py in mindestens einem aktiven Provider-Verzeichnis erzeugt.

    = set(config["roles"]) & {template name in agents/1-generic/}
      & {r for r in ... if is_role_enabled(r, resolve_activation_gates(agent_meta_root, config))}
      & {r for r in ... if provider supports agents for at least one active provider}
    """
```

Hintergrund: `se-component-requirements` ist in `roles:` **enthalten**
(`.meta-config/project.yaml:148`) und wird dennoch nicht erzeugt, weil
`systems-engineering.enabled: false` (`project.yaml:12-13`) den Aktivierungs-Gate schließt
(`scripts/lib/agent_sync.py:548`, `scripts/lib/roles.py:129`). Ein Check auf
`roles ⊄ generiert` ohne Gate-Auswertung ist daher ein **Dauerfehlalarm** (F21) — die
Vergleichsmenge muss `compute_active_roles()` sein.

#### IC-05 — `scripts/lib/consistency/docs.py` (erweitert): Checks V1–V9

Bestehende drei Checks bleiben **unverändert** in Signatur und Severity
(`check_sync_cli_docs` `:9`, `check_ui_help_mappings` `:47`, `check_readme_docs_index` `:100`).
Neu kommen neun Checks mit der Signatur `check_*(root: Path, config: dict | None = None) -> list[Finding]`
und `check="docs.<name>"`:

| # | Check | Erkennt | Severity | Gate | Start |
|---|---|---|---|---|---|
| V1 | `check_no_manual_counts` | **zwei Branches, siehe §5.1.1** — V1a Count-Branch, V1b Versions-Branch | F1, F2, F3 ×2, F4, F14 ×3, F22 | ERROR | **W2: WARNING**, nach W3: ERROR |
| V2 | `check_docs_index_completeness` | jede getrackte `docs/**/*.md` (ohne `archive/`, `_archive/`, ohne `docs/INDEX.md` selbst) fehlt in `docs/INDEX.md` | F8, F15, F20 | ERROR | W3 |
| V3 | `check_internal_links` | relative Markdown-Links in `docs/**`, `README.md`, `llms.txt` auf nicht existierende Ziele (ohne `#anchor`-Prüfung, ohne `http(s)://`, ohne `mailto:`) | F15 | ERROR | W2 |
| V4 | `check_readme_docs_index` (**erweitert**) | heute `docs/api/*.md` (`:111`) → generalisiert auf den gesamten `docs/`-Baum; die bisherige Teilmenge bleibt eine echte Teilmenge der neuen Prüfung | F8, F23 | ERROR (unverändert) | W3 |
| V5 | `check_role_generation_parity` | `compute_active_roles()` (IC-04) ⊄ erzeugte Provider-Agent-Dateien | F13, F21 | **ERROR, sobald** `systems-engineering.enabled: true`; sonst WARNING | W2 |
| V6 | `check_docs_facts_fresh` | (a) gerenderter `DOCS_*`-Block ≠ `compute_doc_facts()` **oder** (b) `compute_doc_facts()` ≠ Sollwert aus IC-23 | Handedit-Drift **oder** Formel-Drift | ERROR | W2 |
| V7 | `check_wiki_staleness` | Wiki-Seite mit `derived-from` älter als die Quelle, oder `type: Architecture` ohne `derived-from` | F5, F10, F11 | WARNING | W2 |
| V8 | `check_spec_plan_path_convention` | Spec/Plan außerhalb `docs/{specs,plans,spikes}` bzw. nicht unter `archive/` | F7, F16 | WARNING | W6 |
| V9 | `check_stale_backups` | `*.sync-backup-*` (`.gitignore:22`) in Provider-Verzeichnissen älter als N Tage | 179 Altlasten | WARNING (lokal, gitignored) | W8 |

**V1-Common-Gate (verbindlich, neu):** Jeder der neun Checks ist ein **No-op**, wenn
`docs-consolidation.enabled` nicht `true` ist. Begründung: identische Absenz-Semantik wie der
Generator (IC-22) — sonst feuern die Checks in Consumer-Projekten, deren `docs/` nicht
agent-meta gehört (NFA-04, R17), **und** in allen 63 Szenario-Fixtures, die den Key nicht
setzen (AC-38). Kein „agent-meta-Eigenerkennung\"-Heuristik-Gate.

#### 5.1.1 V1-Erkennungsregel (verbindlich; ersetzt die Rev.-0.1-Regex vollständig)

Die Rev.-0.1-Regex
`^\s*\|?\s*(\d+)\s+(agents?|hooks?|providers?|pipelines?|presets?|configs?|templates?|tiers?|szenarien?)\b`
matchte **keine** der sechs in IC-05 genannten Fundstellen (K1). Sie wird durch **zwei
disjunkte Branches** ersetzt, die an den verifizierten Zitatzeilen kalibriert sind.

**Gemeinsame Suppression (vor beiden Branches):**

1. Zeile liegt **innerhalb** einer `agent-meta:docs-begin`…`agent-meta:docs-end`-Region.
2. Zeile trägt irgendwo einen `agent-meta:docs-exempt`-Marker.
3. Zeile liegt **innerhalb** eines Markdown-Fenced-Code-Blocks (` ``` ` oder `~~~`) der
   geprüften Datei.
4. Datei ist selbst generiert (`docs/INDEX.md`).

**Branch V1a — „gezählte Sache"** (deckt F1, F2, F3 ×2, F14 ×3, F22):

- Ein **Zahl-Token** `\b\d{1,4}\b`, das **nicht** Bestandteil eines `\d+\.\d+`-Tokens ist
  (⇒ `1.0.0` ist keine Zählung).
- Auf **derselben Zeile** steht ein **Nomen aus der Whitelist** (case-insensitive, optionaler
  Plural):
  `agent(s) | hook(s) | provider(s) | pipeline(s) | preset(s) | tier(s) | template(s) |
  config(s) | command(s) | scenario(s) | szenario(sien) | role(s) | skill(s) | rule(s) | test(s)`.
- **Abstandsregel:** höchstens **3 Tokens** zwischen Zahl und Nomen (erlaubt Adjektive wie
  „Generic", „DoD"; verhindert, dass ein Zähler zwei Sätze später greift).
- Der Finding nennt `branch="V1a"`, `file`, `line`, das Zahl-Token und das Nomen.

**Branch V1b — „Versions-Literal"** (deckt F4):

- Ein Semver-artiges Literal `\b\d+\.\d+\.\d+(?:-[0-9A-Za-z.]+)?\b` auf einer Zeile, die
  zusätzlich `version` (case-insensitive) enthält.
- Begründung der Trennung: `VERSION  # Current version (v1.0.0)` enthält **keine** Ganzzahl
  und würde von V1a **nicht** erfasst. V1a pauschal auf Versionszeilen anzuwenden erzeugt
  dagegen Fehlalarme in Changelog, `docs/api/cli-reference.md` und
  `docs/specs/**` (dort stehen Versionsangaben legitim). Der Finding nennt `branch="V1b"`.

**Positiv-Fixture (verbindlich, wörtlich):** `tests/fixtures/docs_v1_fixtures.md` enthält
mindestens diese vier Zeilen, **1:1 aus `README.md`** inklusive `##`-Prefix und
Einrückung — damit ist der Heading-Fall belegt, den Rev. 0.1 nicht abgedeckt hat:

```markdown
## Agent Roster — 74 Generic Agents
## Hooks (7 hooks, propagated to all providers)
  ai-providers.yaml          # 6 provider configs (Claude, Gemini, Opencode, Continue, Copilot, Mammouth)
VERSION                      # Current version (v1.0.0)
```

Erwartung: **4 Findings**, alle `severity=WARNING`, `check="docs.no_manual_counts"`, `file`
= Fixture-Pfad, `line` = 1/2/3/4, `branch` = `V1a` für 1–3 und `V1b` für 4.
Mit `docs-consolidation.checks.strict: true` sind alle vier `Severity.ERROR`.

**Negativ-Fixture (verbindlich, wörtlich):** `tests/fixtures/docs_v1_fixtures.md` enthält
zusätzlich je einen Fall pro Suppression:

```markdown
<!-- agent-meta:docs-begin facts -->
| Agents | 74 |
<!-- agent-meta:docs-end facts -->

## Agent Roster — 74 Generic Agents <!-- agent-meta:docs-exempt: Beispiel -->

```text
## Hooks (7 hooks)
```

- `74` **innerhalb** einer `docs-*-Region` ⇒ kein Finding
- `74` mit `docs-exempt`-Marker ⇒ kein Finding
- `7` **innerhalb** eines Fenced-Code-Blocks ⇒ kein Finding
- eine Zeile `| Agents | 74 |` außerhalb jeder Region **innerhalb der Fixture** ⇒ **1 Finding**
  (Gegenprobe: das Nomen steht hier **vor** der Zahl, die Abstandsregel greift in beide
  Richtungen)

Erwartung Negativ-Teil: **genau 1 Finding** (die Gegenprobe), sonst 0.

**V1-Anti-Pattern (verbindlich, unverändert):** V1a/V1b prüfen **nicht die Zahl**, sondern die
**Abwesenheit einer Marker-Region an dieser Stelle**. Ein Autor muss eine Zahl entweder
generieren lassen oder die Zeile bewusst als
`<!-- agent-meta:docs-exempt: <grund> -->`
markieren. Damit bleibt `README.md:689` („5 tier presets", **korrekt**) exempt-fähig, ohne
Regex-Hexerei. **Kein stilles Durchwinken.**

**Registrierung:** `scripts/consistency-check.py:52-56` (Import-Block `lib.consistency.docs`)
wird um die neun Namen erweitert; der Aufruf erfolgt in der bestehenden `run_checks()`-Liste.
Die bestehende Importform (`from lib.consistency.docs import (...)`, `:52-56`) bleibt
namensgleich. **Exit-Codes** (Modul-Docstring `:23-26`): `0` = keine Errors (Warnings
erlaubt, außer `--strict`), `1` ≥ 1 Error, `2` Skriptfehler — unverändert.

#### IC-06 — `scripts/lib/consistency/placeholders.py` :: Namespace-Registrierung

```python
# scripts/lib/consistency/placeholders.py
_DYNAMIC_PREFIXES: tuple[re.Pattern, ...] = (
    re.compile(r'^PAL_[A-Z0-9_]+$'),
    re.compile(r'^PIPELINE_[A-Z0-9_]+_(BLOCK|PROVIDER_BLOCKS)$'),
    re.compile(r'^DOCS_[A-Z0-9_]+$'),          # NEU — IC-02-Namensraum
)
```

**Korrektur zum Design (siehe §13-A3):** `check_placeholders` erzeugt für unbekannte Namen
`Severity.WARNING` (`:177-182`), **nicht** ERROR. Ein nicht aufgelöstes `{{DOCS_*}}` ist daher
**kein** Fehler-Gate; das Fehler-Gate ist **V6**. Die Spec verlässt sich auf V6, nicht auf
eine (nicht existierende) ERROR-Stufe.

### 5.2 Modul M2 — Renderer, Indexer, Brücke

#### IC-07 — `scripts/lib/doc_renderer.py` (neu): Rendering-API

```python
# scripts/lib/doc_renderer.py
"""Rendert docs/INDEX.md (Volltext) und DOCS_*-Faktenbloecke in Marker-Regionen."""
from __future__ import annotations

DOCS_BLOCK_RE = re.compile(
    r"(<!--\s*agent-meta:docs-begin\s+(?P<region>[a-z0-9-]+)\s*-->)(?P<body>.*?)"
    r"(<!--\s*agent-meta:docs-end\s+(?P=region)\s*-->)",
    re.DOTALL,
)
"""Marker-Paar je Region. Form folgt context.py:36-39 (_MANAGED_BLOCK_RE, re.DOTALL)."""

def render_doc_fact_block(region: str, facts: dict[str, str]) -> str:
    """Body-Text fuer eine Region. Deterministisch, kein Zeitstempel (NFA-02)."""

def render_docs_index(index_model: dict, facts: dict[str, str]) -> str:
    """Volltext docs/INDEX.md inkl. Fakten-Footer (IC-14)."""

def apply_fact_blocks(text: str, facts: dict[str, str], log=None) -> str:
    """Ersetze den Body jeder DOCS_BLOCK_RE-Region. Fehlende Region -> unveraendert."""
```

**Fehlerpfade:** Eine `docs-begin`-Region ohne zugehöriges `docs-end` → `text` bleibt
unverändert **plus** `log.warning("docs", "unbalanced marker region '<region>'")`; kein
Abbruch, kein Halbschreiben. Zwei Regionen gleichen Namens → nur die **erste** wird
ersetzt (`count=1`, Muster `context.py:42-50`), die zweite erzeugt eine Warnung.
**Leere Fact-Werte:** rendert `<!-- agent-meta:docs-empty: <name> -->` anstelle einer
leeren Zeile (kein stilles Leerzeichen-Rauschen im Diff).

#### IC-08 — Marker-Syntax in `README.md` (Hybrid-Modus)

```
<!-- agent-meta:docs-begin facts -->
…generiert…
<!-- agent-meta:docs-end facts -->
```

Erlaubte Regionsnamen: `facts`, `roster`, `pipelines`, `hooks`, `providers`, `version`.
**Eigener Namespace** neben `agent-meta:managed-begin/end` (`context.py:36-38`,
`context.py:1264-1265`, `cli_commands.py:95-96`): `docs-*` ≠ `managed-*` ⇒ keine Kollision.
VERIFIED: `README.md` enthält **keinen** `agent-meta:managed-*`-Marker ⇒ die Doku-Region
kann nicht in eine Kontext-Region hineinlaufen. `.gitignore`-Managed-Block
(`context.py:294-295`) bleibt unverändert, weil `README.md`/`docs/INDEX.md` **keine**
Provider-Dateien sind (§7.1 des Designs).

#### IC-09 — `scripts/lib/doc_index.py` (neu): Docs-Baum-Modell

```python
# scripts/lib/doc_index.py
"""Baut den Doku-Baum + 1-Zeilen-Beschreibungen. Einzige Komponente, die
Doku-Dateisystem-Semantik kennt — darf NICHT nach Doku-Pfaden in doc_facts.py dupliziert werden."""
from __future__ import annotations

EXCLUDED_DIR_SEGMENTS: frozenset[str] = frozenset({"archive", "_archive", "local-Inputs"})
DESCRIPTION_MAX_CHARS: int = 120

def build_index_model(project_root: Path) -> dict:
    """{'root': rel, 'entries': [{'path', 'title', 'description', 'kind', 'depth'}]}"""
```

- `title`: erstes `# `-Heading, sonst Dateiname ohne Endung.
- `description`: Frontmatter-`description`, auf `DESCRIPTION_MAX_CHARS` gekürzt mit `…`;
  **Fallback**: `""` → der Renderer schreibt `—`. Kein erfundener Text.
- `kind`: `architecture|api|providers|guides|specs|plans|spikes|concepts|se-cascade|other`.
- Sortierung: `kind`-Reihenfolge aus §3.2, dann `path` aufsteigend — deterministisch, damit
  der Diff stabil bleibt (NFA-02).
- **Zweimal laufend auf demselben Baum → byte-identisches Ergebnis** (NFA-01).

#### IC-10 — `docs/INDEX.md`-Format (kanonisch, 100 % generiert)

````markdown
# Documentation Index

> Generated by agent-meta `sync.py` (docs-consolidation). Do not edit by hand —
> every region below is regenerated on each sync. Hand prose lives in the pages
> this index links to.

## architecture
- [Layer Model](architecture/01-layer-model.md) — Override-Priorität der 4 Layer …

## guides
- …

<!-- agent-meta:docs-facts:begin -->
| Fact | Value |
|------|-------|
| Version | 1.2.0-beta.2 |
| Agent templates | 80 |
<!-- agent-meta:docs-facts:end -->

## volatile
<!-- agent-meta:docs-volatile:begin -->
| Scenarios | 63 |
<!-- agent-meta:docs-volatile:end -->

<!-- agent-meta:docs-footer -->
facts-hash: <sha256 über den kanonischen **nicht-volatilen** Faktum-Satz, 16 Hex-Zeichen>
generator: doc-indexer/1
<!-- /agent-meta:docs-footer -->
````

**Regeln:** (a) kein Zeitstempel (NFA-02, Muster `standalone.py:365` — dort steht die
Version, kein Datum); (b) `facts-hash` ist `sha256` über `"\\n".join(f"{k}={v}" for k in
sorted(non_volatile_facts))`, gekürzt auf 16 Zeichen — **stabil** gegenüber
Reihenfolge-Änderungen **und** gegenüber Szenario-Zahl-Änderungen (R1); (c) jeder
`docs/**/*.md`-Pfad (ohne `archive/`, `_archive/`) erscheint **genau einmal** als
Link; `docs/INDEX.md` selbst nie; (d) `docs/architecture/INDEX.md` ist eine Teil-Vorschau
auf denselben Baum (Design §1); (e) **Die Volatile-Sektion steht als letzte Sektion vor dem
Footer**, damit ein Szenario-Diff genau **eine** Zeile betrifft und der Review-Diff nicht
über die Datei springt (M7).

#### IC-11 — Snippet-Bridge in `scripts/lib/config.py` (C3, Erweiterung `:1861-1914`)

```python
# scripts/lib/config.py :: _build_snippet_variables  (bestehende Signatur unverändert)
#   _build_snippet_variables(variables: dict, agent_meta_root: Path) -> None
    # ERGÄNZUNG — neues Verzeichnis, kein Neu-Inventar des Mechanismus:
    _docs_snippets_dir = agent_meta_root / "snippets" / "docs"
    for _snippet_name, _var_stem in (
        ("repo-facts", "DOCS_REPO_FACTS"),
        ("agent-roster", "DOCS_AGENT_ROSTER"),
        ("pipelines", "DOCS_PIPELINES"),
        ("hooks", "DOCS_HOOKS"),
        ("providers", "DOCS_PROVIDERS"),
        ("tier-presets", "DOCS_TIER_PRESET"),
    ):
        _snippet_path = _docs_snippets_dir / f"{_snippet_name}.md"
        _var_name = f"{_var_stem}_BLOCK"
        variables[_var_name] = (
            _load_block_snippet(_snippet_path)
            if _snippet_path.exists() else ""
        )
```

- **`_load_block_snippet` wird wiederverwendet, nicht modifiziert** (`config.py:1842-1858`):
  Frontmatter-Strip, CRLF→LF-Normalisierung, `strip("\n")` — der kanonische
  Inlining-Transform bleibt unverändert (§7.1 des Designs).
- Die Ergänzung steht **nach** dem bestehenden `snippets/security/`-Block
  (`config.py:1923-1924`), damit die bestehende Reihenfolge der Orchestrator-/Developer-/
  Security-Snippets unangetastet bleibt.
- Die Resultate werden **vor** dem Rendern durch `doc_renderer.apply_fact_blocks()` mit den
  C1-Werten substituiert; die Substitutions-Engine ist Engine E3 des Designs
  (`substitution.py:83-93`, Keep-Policy `:86-88`), **nicht** E1/E2 — damit sind
  Doku-Platzhalter nie von Provider-Engines auflösbar (OQ5, rückwärtskompatibel).

#### IC-12 — `scripts/sync_pipeline.py` :: Doku-Stage und **Reihenfolge-Pflicht**

Neue Stage-Funktion, Muster identisch zu `_sync_stage_knowledge_and_isolation` (`:922-945`):

```python
def _sync_stage_docs_consolidation(
    agent_meta_root: Path, project_root: Path, config: dict,
    provider_config: dict, args: argparse.Namespace, log: SyncLog,
) -> None:
    """Doku-Index + DOCS_*-Faktenbloecke. Laeuft NACH scaffold_spec_plan_dirs,
    damit der Generator den KE-off-fallback nicht ueberschreibt (IC-15)."""
    try:
        sync_docs_consolidation(
            agent_meta_root, project_root, config, provider_config, log, args.dry_run,
        )
    except SyncError as exc:
        print(f"\n  !!  Docs consolidation aborted: {exc}", file=sys.stderr)
        sys.exit(1)
```

**Verbindliche Aufrufreihenfolge** (Abweichung vom Design, siehe §13-A4):

1. `_sync_stage_generated_file_drift_scan` (`sync_pipeline.py:587-620`) — **vor** jedem
   Writer, damit Handedit-Drift noch sichtbar ist.
2. `_sync_stage_knowledge_and_isolation` (`:922-945`) → darin `sync_knowledge_engine` (`:929`)
   und `scaffold_spec_plan_dirs` (`:935`).
3. **`_sync_stage_docs_consolidation` (neu) — unmittelbar nach `scaffold_spec_plan_dirs`.**
4. `_sync_stage_generated_file_hash_capture` (`:1090-1099`) — fasst den Endzustand ein.
5. `_sync_stage_auto_commit_allowlist` (`:1102`) — bleibt die letzte Stage (`:1106-1109`).

Begründung: `scaffold_spec_plan_dirs` schreibt `docs/INDEX.md` **nur** im `file-index`-Modus
(`spec_plan_scaffold.py:62-68`). Läuft der Generator davor, überschreibt der Scaffold das
Voll-Index mit dem Skeleton (B2). Das ist die stärkere Form von C8.

#### IC-13 — Schreib-, Idempotenz- und `dry_run`-Vertrag

```python
def sync_docs_consolidation(
    agent_meta_root: Path, project_root: Path, config: dict,
    provider_config: dict, log: SyncLog, dry_run: bool,
) -> dict:
    """Return {'written': [...], 'unchanged': [...], 'skipped': [...]}."""
```

| Situation | Verhalten | Muster / Beleg |
|---|---|---|
| `docs-consolidation.enabled` **nicht** `true` — **auch bei kompletter Abwesenheit des Keys** | `log.skip("docs-consolidation", "disabled in project.yaml")`, **kein** Schreibzugriff, **keine** V1–V9-Ausführung | `knowledge.py:127-129` (`ke_config.get("enabled", False)`) — **Fail-off-Präzedenz** |
| `resolve_index_mode(config)[0] == "knowledge-engine"` (KE-Index ist autoritativ) | **kein** `docs/INDEX.md` schreiben; `skipped` + `log.note("docs-consolidation", "knowledge-engine index is authoritative")` | `spec_plan_scaffold.py:40-44`; **Szenario 52** (`asserts/52:44` `[ ! -e "docs/INDEX.md" ]`) |
| `resolve_index_mode(config)[0] == "file-index"` und Ziel ist **nicht** das Scaffold-Skeleton | **kein** `docs/INDEX.md` schreiben; `skipped` + `log.note(..., "file-index fallback owned by scaffold")` | **Szenarien 54/55/56** (`asserts/54:27`, `asserts/55:25` `grep -q 'File-based index fallback'`) |
| `resolve_index_mode(config)[0] == "file-index"` und Ziel **ist** das Scaffold-Skeleton (Präfix-Erkennung) | Voll-Index **einmalig** ersetzen | IC-15, F20, `asserts/54:26-27` |
| Ziel existiert **nicht** (agent-meta selbst, vor W3) | Voll-Index anlegen | IC-10 |
| Zielinhalt == Istinhalt | in `unchanged`, **kein** `write_checked` | `standalone.py:386-389, :404-410` |
| Inhalt weicht ab | `write_checked(...)` + `log.action("UPDATE", rel, "docs consolidation")` | `knowledge.py:158-159` |
| `dry_run=True` | rendert, schreibt **nichts**, meldet `would-update` in `written` | `knowledge.py:153, :158`; `standalone.py:391-393` |
| Consumer ohne `docs/`-Verzeichnis | `skipped` + `log.note`; **kein** `mkdir` in Fremdprojekten | Design §3.4 |
| Faktum nicht berechenbar | Wert `""` → `docs-empty`-Marker (kein Abbruch) | IC-01 |
| Platzhalter-**Name** unbekannt | bleibt wörtlich stehen (`substitution.py:86-87`, Default-Keep) **plus** V6-ERROR | IC-05, IC-07 |
| `docs-consolidation.index-mode: skeleton` | Scaffold-Skeleton bleibt **immer** unangetastet | IC-15, AC-21 |

**Besitzregel (K5-Kern, verbindlich):** Der Generator **besitzt `docs/INDEX.md` nur dann,
wenn er sie selbst erzeugt hat** — d. h. wenn das Ziel vorher nicht existierte, **oder** wenn
es das Scaffold-Skeleton ist. Er überschreibt **nie** eine Datei, die ein anderer Writer
legitim geschrieben hat. Ohne diese Regel hätte die Spec (mit `enabled: true` als
Abwesenheits-Default) in den Szenario-Fixtures — die keinen `docs-consolidation`-Key führen
(`run.sh:46-52` kopiert `tests/scenarios/configs/*.project.yaml` unverändert nach
`$tmp/.meta-config/project.yaml`) — den Scaffold-Skeleton mit dem Voll-Index überschrieben
und die Szenarien 54/55/56 sowie 52 gebrochen (AC-38).

#### IC-14 — Fact-Hash-Footer (Diff-Stabilität)

- Algorithmus: `sha256("\n".join(sorted(f"{k}={facts[k]}" for k in facts
  if k not in volatile_facts)))` → erste 16 Hex-Zeichen. **Volatile Fakten gehen nicht ein**
  (R1/M7: sonst erzeugt jedes neue Szenario zusätzlich einen `facts-hash`-Wechsel, der
  inhaltlich bedeutungslos ist).
- **Kein Zeitstempel, kein absoluter Pfad, keine Host-/User-Information** (Secrets-Regel und
  NFA-02). Muster `standalone.py:362-368` (dort: `Generated from agent-meta v{version}`).
- `generator: doc-indexer/1` ist eine **statische** Versions-Konstante, die nur bei einer
  bewussten Formatänderung von `1` hochgezählt wird — sonst Diff-Stabilität.

#### IC-15 — C8 Scaffold-Guard in `scripts/lib/spec_plan_scaffold.py`

```python
# scripts/lib/spec_plan_scaffold.py
DEFAULT_FALLBACK_INDEX = "docs/INDEX.md"   # :23  — bleibt identisch
_FILE_INDEX_SKELETON = "…"                  # :24  — bleibt identisch
_FILE_INDEX_SKELETON_MARKER = "File-based index fallback"   # NEU

def is_file_index_skeleton(text: str) -> bool:
    """True iff *text* ist der vom Scaffold geschriebene Skeleton (Zeilen-Brk ein-aus)."""
```

Der Generator (IC-10) ruft `is_file_index_skeleton()` **vor** dem Schreiben. Ist das Ziel ein
Skeleton **und** ist `docs-consolidation.index-mode: full` **und** ist
`docs-consolidation.enabled == true` **und** ist `resolve_index_mode() == "file-index"`, wird
es durch das Voll-Index ersetzt (erlaubt, einmalig). In **allen anderen** Fällen bleibt der
Scaffold-Skeleton unangetastet (Consumer-Vertrag, Szenarien 54/55/56). Ist `index-mode:
skeleton`, bleibt der Scaffold-Skeleton **immer** unangetastet. **Nie** der umgekehrte Fall:
der Generator schreibt **nie** einen Skeleton.
Regressionsschutz: Szenarien 54/55/56 (`registry.md:97-103`,
`asserts/54-spec-plan-external-override.sh:26-27`, `asserts/55-spec-plan-ke-off-fallback.sh:24-25`,
`asserts/56-spec-plan-preset-coupling.sh:31`) sowie AC-38.

#### IC-16 — `scripts/lib/generated_file_drift.py` :: Docs-Dateien in die Hash-Baseline

Der Store ist **provider-unabhängig** keybar (`generated_file_drift.py:333`
`relative_to(project_root).as_posix()`), und es existiert bereits ein provider-freier
Präzedenzfall: `PLATFORM_DEFAULTS_RESOLVED_REL` (`:44`) wird in `scan_generated_file_drift`
(`:344-349`, Pseudo-Provider `"platform-defaults"` `:349`) und in
`capture_generated_file_hashes` (`:422-424`) behandelt.

```python
DOCS_GENERATED_RELS: tuple[str, ...] = ("docs/INDEX.md", "docs/architecture/INDEX.md")
DOCS_FACT_BLOCK_HOSTS: tuple[str, ...] = ("README.md", "llms.txt", "ARCHITECTURE.md")
DOCS_MARKER_KEY_SUFFIX = "#docs:"            # Key-Form: <rel-pfad>#docs:<region>
# + jeder Pfad, dessen Inhalt einen <!-- agent-meta:docs-begin ... -->-Marker trägt
```

- **Kein** Eintritt in `_iter_managed_files` (`:240-310`) — das ist provider-scoped und würde
  Doku-Dateien fälschlich einem Provider zuordnen. Stattdessen eine eigene, einmalige
  Ergänzung neben dem `PLATFORM_DEFAULTS_RESOLVED_REL`-Handling (`:344-349`, `:422-424`),
  mit Pseudo-Provider `"docs-consolidation"`.
- **Grenze:** `README.md` enthält **Handprosa plus** generierte Regionen. Ein Diff in der
  Handprosa darf **kein** Drift-Finding sein. Deshalb wird für `DOCS_FACT_BLOCK_HOSTS` nicht
  die ganze Datei gehasht, sondern **nur der extrahierte Marker-Body** (normalisiert:
  `"\n".join(line.rstrip() for line in body.splitlines()).strip()`). Der Store-Key lautet
  dann `README.md#docs:facts` (analog `platform-defaults.resolved.yaml`-Präzedenz, Key ist
  ein String und muss kein Pfad sein).

**M8-Auflösung — analysiert statt vermutet (Rev. 0.2).** Rev. 0.1 führte den `#`-Key als
`HYPOTHESIS` und empfahl, das Key-Design zu ändern. Der Code wurde am Working Tree
**nachgelesen**; das Ergebnis ist spezifizierbar, und die nötige Änderung ist **kleiner** als
ein Key-Design-Wechsel:

| Consumer des Hash-Stores | Verhalten mit `README.md#docs:facts` | Beleg | Konsequenz |
|---|---|---|---|
| `_load_hashes` / `_save_hashes` | Key ist ein beliebiger String, wird als Dict-Schlüssel persistiert | `:51-67` | **kein** Problem |
| `is_allowlisted(rel_path, patterns)` | `fnmatch` matcht gegen den **ganzen** String ⇒ ein Muster `README.md` matcht `README.md#docs:facts` **nicht** | `:82-84` | **Verbindliche Regel:** für Marker-Body-Keys wird gegen den **Basis-Pfad** (Key ohne `#`-Suffix) gematcht. Sonst umgeht ein Allowlist-Eintrag für `README.md` genau die Marker-Keys, die er unterdrücken soll |
| `backup_drifted_files` | `target = project_root / finding["path"]` (`:379`); `read_text` schlägt fehl ⇒ `log.debug` + `continue`: **fail-soft, kein Fehler, aber auch kein Backup** | `:379-386` | **Verbindlich (NFA-05):** der Generator darf eine handeditierte Region **nicht** überschreiben, sondern meldet sie (AC-19) — das ist die *Konsequenz* daraus, dass kein Backup entsteht |
| `_sync_stage_auto_commit_allowlist` | **keine Interaktion.** Die Stage liest `config` + `active_roles` via `resolve_auto_commit_config(config, active_roles, agent_meta_root)` und schreibt `.meta-config/auto-commit-allowlist.json`; sie liest den Drift-Store **nicht** | `sync_pipeline.py:1102-1117` | **Reviewer-Korrektur R18** (§17.2): die befürchtete Interaktion existiert nicht — R18 wird als *analysiert und nicht zutreffend* geführt, mit verifiziertem Beleg |
| `capture_generated_file_hashes` | `hashes[rel_path] = content_hash(...)` je aktivem Provider plus Pseudo-Provider-Ergänzung | `:405-425` | Doku-Keys müssen in **beide** Richtungen (Scan **und** Capture) symmetrisch ergänzt werden, sonst meldet der Scan dauerhaft Drift |

- `drift-allowlist.yaml` (`generated_file_drift.py:37`, `allow-edits`) gilt unverändert auch
  für Doku-Pfade — mit der Basis-Pfad-Regel oben.

### 5.3 Modul M3 — Migration

#### IC-17 — Migrationsoperationen (alle `git mv`, kein Inhalts-Rewrite)

| # | Operation | Quelle | Ziel | Welle | Rollback |
|---|---|---|---|---|---|
| M-1 | `git mv` Langfassung | `ARCHITECTURE.full.md` | `docs/architecture/00-overview-full.md` | W4 | `git mv` zurück |
| M-2 | Stub schreiben | `ARCHITECTURE.md` (84 Z, regeneriert) | `ARCHITECTURE.md` | W4 | `git checkout` |
| M-3 | `git mv` Legacy-Specs | `docs/superpowers/specs/` | `docs/specs/archive/superpowers/` | W6 | `git mv` zurück |
| M-4 | `git mv` Legacy-Pläne | `docs/superpowers/plans/` | `docs/plans/archive/superpowers/` | W6 | `git mv` zurück |
| M-5 | `git mv` Beispiel-Configs | `howto/configs/project.yaml.example` (340 Z) | `docs/guides/configs/project.yaml.example` | W5 | `git mv` zurück |
| M-6 | `git mv` Howto-Guide (**neu, M4**) | `docs/howto/admin-ui-remote-access.md` | `docs/guides/admin-ui-remote-access.md` | W5 | `git mv` zurück; `docs/howto/` danach leer und `git rm` |
| M-7 | Stale-Deklaration wandert mit (**neu, M5**) | `ARCHITECTURE.md:3` | **additive** Stale-Zeile in `docs/architecture/00-overview-full.md`; im Stub **entfällt** sie | W4 | Zeile entfernen; Stub via `git checkout` |
| M-8 | Verweise bereinigen | `README.md:721-724` | Zeilen auf existierende Ziele umgeschrieben bzw. entfernt | W8 | `git checkout` |
| M-9 | `derived-from`-Annotation | `knowledge/wiki/**` | Frontmatter-Zeile ergänzt (**additive** Zeile pro Seite, kein Textumbau) | W5 | Zeile entfernen (additiv revertierbar) |
| M-10 | Wiki-Architektur-Redirects | `knowledge/wiki/concepts/architecture*.md` | Kurzform: eine Zeile „SSoT: `docs/architecture/…`" + `derived-from` | W5 | `git checkout` |
| M-11 | Config-Schema-Block (**neu, R15**) | `config/project-config.schema.json` | **neuer Top-Level-Block** `docs-consolidation` mit den 6 Keys aus IC-22, `additionalProperties: false` | **W1** | `git checkout` |
| M-12 | `PROJECT_STRUCTURE`-Korrektur | `.meta-config/project.yaml:205-221` | Fehlende Wurzel-Einträge ergänzt (`docs/INDEX.md`, `docs/guides/configs/`, `docs/providers/`, `docs/se-cascade/`, `docs/concepts/`) — **Config-Edit**, kein Doku-Edit | W8 | `git checkout` |
| M-13 | `legacy:`-Liste erweitern | `.meta-config/project.yaml:61-63` | **additive zwei Zeilen** (die zwei neuen Archivpfade) | W6 | Zeile entfernen |

**M-11-Begründung und -Korrektur (R15, rev. 0.2):** `scripts/lib/config.py` validiert
`project.yaml` gegen `config/project-config.schema.json` (Präzedenz: `dod-presets.yaml:8`
verweist ebenfalls auf das Schema). Das **Wurzel**-Schema ist permissiv
(`additionalProperties: true`, `:2425`) — die 6 neuen Keys sind also **kein** harter
Blocker, sie würden die Validierung nicht brechen. Sie zu deklarieren ist dennoch
**Repo-Konvention**: das Schema nutzt geschlossene Unterobjekte ausdrücklich als
Tippfehler-Wächter (Selbstauskunft in `:2058` und `:2073`). M-11 ist damit
**Konventions- und Autocomplete-Pflicht, keine Fehlerbehebung** — diese Einordnung korrigiert
die Reviewer-Lesart „geht sonst gar nichts" (siehe §17.2).

**B1-Mitigation verbindlich:** die alten `legacy:`-Einträge (`docs/superpowers/specs`,
`docs/superpowers/plans`, `project.yaml:61-63`) bleiben **ein Release** stehen und erzeugen
eine Deprecation-WARNING im Sync-Log. Release-Notes-Pflicht, Minor-Bump.

**B6-Hinweis:** M-12 verändert `PROJECT_STRUCTURE`, das in **jeder** generierten Kontextdatei
landet (`.meta-config/project.yaml:205-221` → `AGENTS.md`/`CLAUDE.md`). Der managed-block-Mechanismus
(`context.py:36-38`) und die Drift-Detection fangen Handpflege ab; der Layout-Diff ist
**sichtbar** und damit ein Review-Punkt, kein stiller Side-Effect.

#### IC-18 — `ARCHITECTURE.md` als generierter Stub (T-4)

Der Stub enthält: Titel, **generierter** Diagramm-Index (Tabelle aus `docs/architecture/*.md`
+ `docs/concepts/viz-logging-mcp.md` + `docs/concepts/a2a-handoff-protocol.md`, heute
`ARCHITECTURE.md:8-20`), einen Pointer auf `docs/architecture/INDEX.md`, den Link auf
`docs/architecture/00-overview-full.md` und **keine eigenen Inhalte**. `llms.txt:24` verlinkt
weiterhin auf `ARCHITECTURE.md` und bleibt damit gültig (T-4-B, „Löschen bricht Deeplinks").

**Stale-Deklaration (M5, entzirkelt):** `ARCHITECTURE.md:3` („Repo version: **0.92.0** —
content last substantively reviewed: 2026-07-20") ist heute die maschinenlesbare Quelle für
`status:stale-upstream` (`knowledge/wiki/index.md:24`). Nach M-1 liegt dieser Inhalt in
`docs/architecture/00-overview-full.md`, nach M-2 ist er aus dem Stub **weg**. Rev. 0.1
verlangte in AC-29, die Zeile `Repo version:` zu verbieten, **und** berief sich dabei auf
genau diese maschinelle Extraktion — nach W4 ist die Quelle weg, der AC war zirkulär. Auflösung:

- **M-7** verschiebt die Deklaration in die Langfassung (additive Zeile dort, keine im Stub).
- **IC-03** liest die Deklaration aus `docs/architecture/00-overview-full.md` — **nicht** aus
  dem Stub.
- **AC-29** prüft beide Seiten **getrennt**: (a) der Stub enthält generierten Diagramm-Index,
  beide Pointer und keine eigene Architektur-Prose; (b) die Stale-Deklaration steht in der
  Langfassung, nicht im Stub; (c) `compute_wiki_staleness()` liefert für
  `concepts/architecture.md` mit `derived-from: docs/architecture/00-overview-full.md` einen
  auswertbaren Wert. Damit verbietet der AC nichts, dessen Quelle er voraussetzt.

### 5.4 Modul M4 — Knowledge-Index-Generierung

#### IC-19 — `scripts/lib/knowledge.py` (Erweiterung `:103-205`): `index.md`-Generator

**Policy-Bruch, Bedingung (a):** `knowledge.py:112-114` sagt „never overwrites existing
`schema.md`/`wiki/index.md`/`wiki/log.md`". Diese Spec bricht das **nur** für `index.md` und
**nur** unter den Bedingungen des Rollback-Flags. Vor Aktivierung wird
`knowledge/schema.md` (§2 „Usage", `:41-42`) um einen Absatz „`index.md` is generated"
ergänzt — eine **strukturelle** Änderung, die laut `knowledge/schema.md:44-46`
User-Sign-off braucht (**Bedingung für W7**, nicht für diese Spec).

```python
def sync_wiki_index(agent_meta_root: Path, project_root: Path,
                     config: dict, log: SyncLog, dry_run: bool) -> dict:
    """Deterministischer 1:1-Index aus dem Dateisystem. No-op wenn
    knowledge-engine.okf.index-mode != "generated" (Rollback-Flag)."""
```

| Schicht | Ort | Schreibrecht | Ableitung | Pflicht-Frontmatter |
|---|---|---|---|---|
| Quelle | `knowledge/sources/` | nur `knowledge-ingestor`, additiv (NG-2) | keine | `source-of`, `captured-at`, `immutable: true`, optional `supersedes` |
| Wiki-Seite | `knowledge/wiki/{concepts,entities,topics,plans,specs,sources,queries}/` | Knowledge-Agenten (LLM-owned) | `derived-from: <rel-pfad>` + `derived-at: <ISO>` | `type`, `derived-from`, `derived-at`, `status` |
| Index | `knowledge/wiki/index.md` | **Generator (IC-19)** | 1:1 aus dem Dateisystem | — |
| Log | `knowledge/wiki/log.md` | Generator-**Append** + manuell erlaubt | 1 Zeile pro Sync mit Wiki-Änderung | — |

Verzeichnisnamen folgen `knowledge.py:_KNOWLEDGE_GITKEEP_SUBDIRS` (`:87-100`, 14 Einträge inkl.
`wiki/{concepts,entities,topics,sources,queries,plans,specs}`). Sortierung alphabetisch, damit
der Diff minimal bleibt (NFA-02).

#### IC-20 — `knowledge/wiki/log.md`-Append (Bedingung (c))

- Format exakt nach `knowledge/wiki/log.md:13-17`:
  `YYYY-MM-DD HH:MM — <operation> — <summary>`.
- **Genau eine Zeile** pro Sync, in dem sich mindestens eine Wiki-Datei geändert hat; sonst
  **kein** Append (verhindert Log-Churn, NFA-02).
- `operation` ∈ `{index, index/update}` (Vokabular aus `:22, :24, :27`).
- Bestehender Inhalt wird **nie** umsortiert oder gekürzt (append-only, Policy).

#### IC-21 — `agents/1-generic/knowledge-indexer.md` (Bedingung (b))

Umschreibung der Rolle von „schreibe `index.md`" zu „prüfe Generator-Output, melde Drift".
Provider-agnostik: **kein** Claude-Literal, keine Provider-Verzweigung
(`provider-agnostic`-Regel; Guard `tests/test_provider_agnostic_dispatch.py`).
Folgen: alle generierten Provider-Kopien der Rolle werden durch den nächsten Sync neu erzeugt.

**Kollisionsvermerk (N2, rev. 0.2):** dies ist die **einzige** Datei unter `agents/`, die
diese Initiative anfasst, und sie liegt in der von Track A / Rollenpflege berührten Zone
(§2.3). Verbindliche Reihenfolge: W7 startet **erst**, wenn der Rollenpflege-Branch gemergt
ist; IC-21 wird als **letzter** Commit von W7 committet, damit ein Rebase der Rollenpflege
nicht in einem `agents/1-generic/`-Template-Diff landet. Risiko **R19**; Rollback
`git checkout`.

#### IC-22 — Rollback-/Gate-Config

| Key | Ort | **Default bei Abwesenheit** | Default agent-meta (explizit gesetzt) | Wirkung |
|---|---|---|---|---|
| `docs-consolidation.enabled` | `.meta-config/project.yaml` (neu) | **`false`** | `true` (explizit, in W1) | Master-Schalter für **Generator (IC-13) und Checks V1–V9 (IC-05)** |
| `docs-consolidation.index-mode` | dito (neu) | `full` | `full` | `full` = Voll-Index ersetzt **nur** ein Scaffold-Skeleton; `skeleton` = Scaffold-Skeleton bleibt immer |
| `docs-consolidation.checks.strict` | dito (neu) | `false` | `true` (ab W3) | V1 als ERROR vs. WARNING (B4) |
| `docs-consolidation.sources` | dito (neu) | `[]` | `[README.md, llms.txt, ARCHITECTURE.md]` | Liste der hybrid-Dateien; leer = kein Rendering (NG-9) |
| `docs-consolidation.volatile-facts` | dito (neu) | `[DOCS_SCENARIO_COUNT]` | dito | Fakten, die in Hybrid-Dateien unterdrückt und aus dem `facts-hash` ausgeschlossen werden (R1) |
| `knowledge-engine.okf.index-mode` | `.meta-config/project.yaml:18-29` (ergänzt) | `llm` | `llm` für ein Release, danach `generated` | Generator an/aus (T-6, Rollback W7) |

**Selbstwiderspruch aufgelöst (K5, rev. 0.2).** Rev. 0.1 schrieb: „Alle Keys sind **additiv**;
keiner verändert bestehendes Verhalten **bei Abwesenheit** (Schema-Default = Default
agent-meta)" — und setzte zugleich `enabled: true` als Abwesenheits-Default. Beides ist
unvereinbar: `true` **ist** ein Verhaltenswechsel bei Abwesenheit. Die auflösende Regel ist die
**Fail-off-Präzedenz** des Repos: `knowledge.py:127` prüft
`ke_config.get("enabled", False)` — „nicht explizit `true`" heißt „aus", und zwar für den
Knowledge-Engine-Writer (`:127-129`) **und** für dessen Auto-Index-Schalter (`:132`
`okf.get("auto-index", True)` folgt derselben Logik). Genau diese Regelung wird hier für
`docs-consolidation.enabled` übernommen, **für alle sechs Keys** und **für Writer und Checks
gleichermaßen**.

**Konsequenz, die explizit benannt wird (K5):** Die Szenario-Fixtures
`tests/scenarios/configs/*.project.yaml` werden von `tests/scenarios/run.sh:46-52`
unverändert als `$tmp_dir/.meta-config/project.yaml` eingespielt und enthalten **keinen**
`docs-consolidation`-Key (verifiziert am Beispiel `54-spec-plan-external-override.project.yaml`,
34 Zeilen, und `52-spec-plan-enabled.project.yaml`, 32 Zeilen). Mit Fail-off sind Generator
**und** V1–V9 dort vollständig inaktiv. Das ist kein Nebeneffekt, sondern der **vertragliche
Grund**, warum die Szenarien 50/51/52/54/55/56 ohne jede Änderung grün bleiben (NG-10, AC-38).
Ein Szenario, das das Doku-Verhalten prüfen will, muss den Key **explizit** setzen — dafür
ist `64-docs-facts-drift` vorgesehen (§2.3).

**Kein** Key enthält einen Provider-Namen.

### 5.5 Querschnitts-Contracts (rev. 0.2)

#### IC-23 — `config/doc-facts-expected.yaml` + `scripts/lib/doc_facts.py::load_expected_doc_facts` (R14)

**Problemklasse (Korrektheit, nicht Churn).** Die Kette `doc_facts → Renderer → V6` ist ein
**geschlossener Kreis**: V6 vergleicht den gerenderten Block gegen `compute_doc_facts()` —
also gegen dieselbe Formel, die ihn erzeugt hat. Ein **systematisch** falscher Faktor passiert
damit **alle** Gates. Rev. 0.1 hat genau das dreifach bewiesen: F19 (Tier 4 statt 5), F22
(DoD 6 statt 7, Rev. 0.1 als „korrekt" eingestuft) und F14 (6/7 statt 7/8) waren drei
Zählfehler, die **kein** Gate dieser Initiative gefunden hätte. R1 führte das als
„Doku-Diff-Churn"; es ist ein **Korrektheitsrisiko**.

```python
# scripts/lib/doc_facts.py
def load_expected_doc_facts(agent_meta_root: Path, log=None) -> dict[str, str]:
    """Liest config/doc-facts-expected.yaml. {} bei Abwesenheit/Fehler (fail-soft,
    Muster load_yaml_file(..., on_error="default"))."""

def compare_expected_doc_facts(
    computed: dict[str, str], expected: dict[str, str]
) -> list[dict[str, str]]:
    """Return [{'fact', 'computed', 'expected', 'kind'}] mit kind in
    {'mismatch', 'missing-in-expected'}. Deterministisch, nach 'fact' sortiert."""
```

```yaml
# config/doc-facts-expected.yaml   (HANDGEPFLEGT, niemals generiert)
schema-version: 1
verified-at: "2026-09-26"
verified-by: human
DOCS_VERSION: "1.2.0-beta.2"
DOCS_AGENT_TEMPLATES_COUNT: "80"
DOCS_AGENTS_SE_COUNT: "14"
DOCS_PROVIDER_COUNT: "9"
DOCS_HOOKS_COUNT: "11"
DOCS_HOOKS_1GENERIC_COUNT: "9"
DOCS_PIPELINES_COUNT: "8"
DOCS_PIPELINES_ACTIVE_COUNT: "7"
DOCS_DOD_PRESET_COUNT: "7"
DOCS_TIER_PRESET_COUNT: "5"
DOCS_COMMAND_COUNT: "22"
```

**Schlüsselzahl: elf (11).** Rev. 0.2 schrieb an einer Stelle „zwölf" (IC-23-Text, AC-36,
NFA-11, R14) und an anderer „11" (§1.2) — **beides konnte nicht stimmen**, weil die
Yaml-Datei genau **11** Einträge hat. Verbindlich ist **elf** und diese Datei ist der
**einzige** Ort, an dem konkrete Sollzahlen stehen (rev. 0.3, NEW-4/NEW-8: der `xfail`-Snapshot
in AC-02 ist als unenforceable entfernt, damit es nicht zwei Orte für dieselbe Zahl gibt).
Nicht enthalten: `DOCS_AGENTS_NONSE_COUNT` (reine Differenz `SE + NONSE == TEMPLATES`, in AC-02
formelgeprüft), `DOCS_SCENARIO_COUNT` (volatile) und die `*_BLOCK`-Fakten (Text, keine Zahl).

**Vertrag:**

- `compute_doc_facts()` bekommt **keinen** Parameter für die Sollwerte (keine Kopplung, kein
  Zirkel in der anderen Richtung).
- **V6** liest beide Quellen und emittiert zwei Fehlerklassen:
  (a) `kind: "handedit"` — gerenderter Block ≠ `compute_doc_facts()` (bestehender Zweck);
  (b) `kind: "expected-mismatch"` — `compute_doc_facts()` ≠ Sollwert, **obwohl** der
  Render-Output exakt stimmt. `kind: "missing-in-expected"` ist **WARNING**, kein Fehler
  (die Datei darf wachsen).
- **Bekannte, bewusst akzeptierte Kosten:** jede gewollte Änderung einer dieser Zahlen (z. B.
  ein neues Pipeline-Preset) macht V6 rot, bis die Sollwert-Datei im **selben** Commit
  mitgezogen wird. Genau das ist der gewollte Review-Signalweg. Geführt als R14-Restrisiko.
- Die Datei ist **kein** Doku-Output und steht **nicht** unter `docs/`; sie ist eine
  Test-Referenz neben den übrigen Config-Dateien und folgt derselben Schreibdisziplin wie
  `config/dod-presets.yaml` (Prezedenz: `dod-presets.yaml:8` verweist auf das Schema).
- **NG-1 gilt nicht:** die Datei ist neu, es gibt keinen Altinhalt umzuschreiben.

#### IC-24 — `scripts/lib/knowledge.py::restore_wiki_index` (M6, rev. 0.2)

**Problemklasse.** Rev. 0.1 verlangte in AC-35, der Rollback `index-mode: llm` stelle den
Ausgangszustand **byte-identisch** wieder her, spezifizierte aber **nirgends** einen
Restore-Pfad. `index-mode: llm` stellt den **Generator** stumm — die Datei bleibt, was der
Generator geschrieben hat. Es gibt außerdem **keinen** CLI-Restore dafür: `sync.py --backup` /
`--restore` (`cli_commands.py:864`, `:888-900`, `backup.py:376+`) sind
**Provider-Verzeichnis-Zip**-Operationen (`restore_provider_dir`, `deactivation.py:21`,
`:303-353`) und können `knowledge/wiki/index.md` **nicht** wiederherstellen (am Working
Tree verifiziert).

```python
# scripts/lib/knowledge.py
def restore_wiki_index(
    project_root: Path, log: SyncLog, *, dry_run: bool = False
) -> list[str]:
    """Stellt knowledge/wiki/index.md aus der Sicherung des Erstrewrites wieder her.

    Reihenfolge:
      1. jüngste existierende Sibling-Sicherung `index.md.sync-backup-<ts>`
         (Muster backup_drifted_files, generated_file_drift.py:354-402, :388)
         -> dorthin zurueckkopieren;
      2. sonst, wenn `index.md` git-getrackt ist:
         `git -C <project_root> checkout -- knowledge/wiki/index.md`;
      3. sonst: log.error + KEIN Schreibzugriff (fail-closed).
    Gibt die Liste der beruehrten Rel-Pfade zurueck; [] bei No-op.
    """
```

**Vertrag:**

- Aufruf **nur** als manueller Runbook-Schritt in W7 (im Plan als Task mit
  Dry-Run-Substep), **nicht** als Sync-Stage und **ohne** neues CLI-Flag (NG-4).
- `dry_run=True` schreibt nicht, meldet aber die geplanten Zielpfade.
- Fail-closed bei Schritt 3: ein „nichts tun und trotzdem Erfolg melden" wäre Datenverlust
  mit grünem Log.
- Reihenfolge ist vertraglich: Sibling-Backup schlägt Git, weil es den **exakten** Zustand
  unmittelbar vor dem Rewrite sichert, nicht den Commit-Zustand.
- AC-35b/AC-35 in §7 sind entsprechend abgeschwächt und verweisen hierher.

---

## 6. Datenfluss

### (a) Normaler Sync (ohne `--dry-run`, ohne `--check`)

```
project.yaml ──► config.py (load) ──► roles.py::resolve_activation_gates
                                          │
agents/1-generic/ ─┐                       │
config/*.yaml ─────┼──► doc_facts.py ──────┴──► {DOCS_*: str}   (rein, kein Write)
hooks/**/*.sh ─────┘        │
                            ├─► doc_index.py::build_index_model ──► doc_renderer.render_docs_index
                            │                                              │
                            │                                     write_checked("docs/INDEX.md")
                            │                                     (is_file_index_skeleton-Guard IC-15)
                            └─► config.py::_build_snippet_variables ──► DOCS_*_BLOCK (snippets/docs/*.md)
                                            │
   README.md / llms.txt / ARCHITECTURE.md ──► doc_renderer.apply_fact_blocks (DOCS_BLOCK_RE)
                                            │   (fehlende Region → unverändert; keine Handedit-Überschreibung)
                                            └──► write_checked je Datei
Knowledge-Wiki (nur wenn okf.index-mode=generated):
   doc_index.py-Muster ──► knowledge.py::sync_wiki_index ──► knowledge/wiki/index.md
                                                   └──────► knowledge/wiki/log.md (1 Append-Zeile)
Danach: generated_file_drift.capture_generated_file_hashes (inkl. Doku-Pfade, IC-16)
```

### (b) `--check` (Doku-Gate)

```
compute_doc_facts()  vs.  Ist-Inhalt der Marker-Regionen / docs/INDEX.md   → V6 (kind=handedit)
compute_doc_facts()  vs.  config/doc-facts-expected.yaml                  → V6 (kind=expected-mismatch, IC-23)
   → Abweichung: log.warning + Non-Zero-Status (kein Write)
consistency-check.py: V1..V9  →  exit 0 (keine Errors) / 1 (≥1 Error) / 2 (Skriptfehler)
   (V1..V9 sind No-op, solange docs-consolidation.enabled != true — IC-05-Common-Gate)
```

`sync.py:149` `--check` und `sync.py:153` `--validate` dürfen bei **V1, V2, V3, V6** nicht
grün sein. `--validate` ist laut `.meta-config/project.yaml:193` bereits `TEST_COMMAND`.

### (c) `--dry-run`

`sync_docs_consolidation(..., dry_run=True)` rendert vollständig, sammelt die Soll-Inhalte,
schreibt **nichts** (kein `write_checked`, kein `mkdir`, kein `log.md`-Append) und meldet
jeden Write-Kandidaten als `would-update`. Reihenfolge und Marker-Verarbeitung identisch zu (a).

### (d) Migration (W4–W6, W8)

```
git mv (Datei)  ──► docs/INDEX.md neu generieren (erkennt neue Pfade)
                 ──► V2 (Vollständigkeit) und V3 (Link-Integrität) prüfen
                 ──► V8 (Spec/Plan-Pfadkonvention) prüft nach W6
config-Edit (legacy:, PROJECT_STRUCTURE) ──► additiv, ein Release tolerant
```

### (e) Consumer-Projekt (Submodul-Layout)

```
Consumer-Projecten (docs-consolidation.enabled nicht true — Default)
   → log.skip("docs-consolidation", "disabled in project.yaml"); KEIN Schreibzugriff,
     KEIN docs/INDEX.md-Erzeugen, KEIN Snippet-Inlining in Consumer-Kontextdateien.
   → V1..V9: vollständiger No-op. Kein Doku-Check läuft gegen fremde docs/.
   → docs/ sind **nicht** generierte Provider-Artefakte (§7.1 des Designs):
     echter Downstream-Impact beschränkt sich auf B2, B5 (nur bei KE-Nutzung) und B6.
```

---

## 7. Acceptance Criteria

Jedes AC ist nummeriert, beobachtbar (Datei, Befehl, Exit-Code) und mit mindestens einem
Interface Contract und einem Verifikations-Check verknüpft. Testdateinamen sind verbindlich;
`tests/scenarios/`-Artefakte gehören **Track A** (siehe §2.3).

**Testpfad-Konvention innerhalb einer Gruppe:** das erste AC einer Gruppe nennt den vollen
Pfad (`tests/test_doc_facts.py::test_…`); die folgenden ACs derselben Gruppe schreiben nur
noch `::test_…` und meinen dieselbe Datei.

### M1 — DocFacts + Checks

- **AC-01** (IC-01, IC-02) Given ein vollständiges `agent-meta`-Checkout, when
  `compute_doc_facts(agent_meta_root, config, provider_config=provider_config)` läuft, then
  ist das Resultat ein `dict[str, str]` mit **genau** den 23 in IC-02 gelisteten Schlüsseln,
  alle Werte `str`, keine Exceptions, kein Schreibzugriff (Assertion: Verzeichnis-Hash von
  `agent-meta_root` vor/nach identisch). *Test `tests/test_doc_facts.py::test_fact_key_set_exact`.*
- **AC-02** (IC-02) — **rev. 0.3: durchsetzbar formuliert, Snapshot entfernt (NEW-8).** Given der
  Working Tree, when `compute_doc_facts()` läuft, then gilt für **jedes** Skalar-Faktum die
  **Formel**, nicht eine Zahl: `DOCS_AGENTS_SE_COUNT + DOCS_AGENTS_NONSE_COUNT ==
  DOCS_AGENT_TEMPLATES_COUNT`; `DOCS_AGENTS_SE_COUNT` == Anzahl `se-`-Präfix-Templates;
  `DOCS_AGENTS_NONSE_COUNT` == Anzahl der übrigen; `DOCS_PROVIDER_COUNT == len(providers)`;
  `DOCS_HOOKS_COUNT` == `glob(hooks/**/*.sh)` − `{lib/, release-gates/}` − `{*-impl.sh}`;
  `DOCS_HOOKS_1GENERIC_COUNT` == `glob(hooks/1-generic/*.sh)` − `{*-impl.sh}` **und**
  `DOCS_HOOKS_1GENERIC_COUNT <= DOCS_HOOKS_COUNT`;
  `DOCS_PIPELINES_ACTIVE_COUNT == DOCS_PIPELINES_COUNT − disabled overrides` **und**
  `DOCS_PIPELINES_ACTIVE_COUNT <= DOCS_PIPELINES_COUNT`; `DOCS_DOD_PRESET_COUNT ==
  len(dod-presets.yaml presets)`; `DOCS_TIER_PRESET_COUNT` == Top-Level-Keys von
  `tier-presets.yaml`; `DOCS_COMMAND_COUNT == len(glob(commands/1-generic/*.md))`;
  `DOCS_VERSION` == `Path("VERSION").read_text().strip()`. Kein Wert wird gegen eine im Test
  hinterlegte Konstante geprüft. *Test
  `tests/test_doc_facts.py::test_scalar_fact_formulas` (parametrisiert über eine
  Fixture-Konfiguration, **13** Formel-Assertions).*
  **Bewusste Entscheidung (rev. 0.3):** Rev. 0.2 führte zusätzlich einen Stand-Snapshot
  `test_snapshot_counts_2026_09_26` mit **zwölf** Zahlen, der als `xfail` markiert war — ein
  `xfail` ist **nicht durchsetzbar** und hätte einen Fehler nur dokumentiert. Der Snapshot ist
  deshalb **entfernt**; die Durchsetzung der konkreten Zahlen liegt **eindeutig** bei
  `config/doc-facts-expected.yaml` (IC-23) und wird von **AC-36** geprüft. Damit gibt es
  genau **einen** Ort mit Sollzahlen im Repo-Baum und einen **durchsetzbaren** AC dafür.
- **AC-03** (IC-02, IC-14) Given `DOCS_SCENARIO_COUNT` als `volatile`, when
  `apply_fact_blocks()` auf `README.md` oder `llms.txt` angewandt wird, then kommt der Wert
  **nicht** im Output vor. Given zwei Renderings von `docs/INDEX.md`, die sich **nur** in
  `DOCS_SCENARIO_COUNT` unterscheiden, when der `facts-hash` verglichen wird, then sind die
  Hashes **identisch**, und der unterschiedliche Wert steht in der `docs-volatile`-Sektion
  **am Dateiende vor dem Footer** (R1/M7). *Test
  `tests/test_doc_facts.py::test_volatile_fact_absent_from_hybrid_files` +
  `::test_volatile_fact_excluded_from_facts_hash`.*
- **AC-04** (IC-01) Given `config/ai-providers.yaml` fehlt, when `compute_doc_facts()` läuft,
  then ist `DOCS_PROVIDER_COUNT == ""`, alle übrigen Faktuen sind berechnet, und **kein**
  `SyncError` wird geworfen. *Test `tests/test_doc_facts.py::test_missing_source_is_fail_soft`.*
- **AC-05** (IC-04) Given `.meta-config/project.yaml` mit `systems-engineering.enabled: false`
  (Ist-Zustand `:12-13`) und `se-component-requirements` in `roles:` (Ist-Zustand `:148`),
  when `compute_active_roles()` läuft, then ist `se-component-requirements` **nicht** im
  Ergebnis, und `len(result) < len(config["roles"])` ist der einzige zulässige Grund.
  *Test `tests/test_doc_facts.py::test_se_role_excluded_by_gate_not_by_roles_list`.*
- **AC-06** (IC-06) Given ein Agent-Template mit `{{DOCS_PROVIDERS_BLOCK}}` im Body, when
  `consistency-check.py` läuft, then wird **kein** `placeholders.unknown`-Finding erzeugt
  (Prefix `^DOCS_` in `_DYNAMIC_PREFIXES`). *Test
  `tests/test_doc_facts.py::test_docs_prefix_registered_in_placeholders`.*
- **AC-07** (IC-05, §5.1.1, V1a+V1b — **ersetzt die Rev.-0.1-Fassung, K1**) Given die
  Positiv-Fixture `tests/fixtures/docs_v1_fixtures.md` mit genau diesen **vier wörtlichen**
  Zitatzeilen (Zeilennummern 1–4),
  `## Agent Roster — 74 Generic Agents`,
  `## Hooks (7 hooks, propagated to all providers)`,
  `  ai-providers.yaml          # 6 provider configs (Claude, Gemini, Opencode, Continue, Copilot, Mammouth)`,
  `VERSION                      # Current version (v1.0.0)`,
  when `check_no_manual_counts()` läuft, then sind es **genau 4** Findings mit
  `severity=WARNING`, `check="docs.no_manual_counts"`, `file="tests/fixtures/docs_v1_fixtures.md"`,
  `line` = 1/2/3/4, wobei `line` 1/2/3 `branch="V1a"` und `line` 4 `branch="V1b"` tragen.
  Nach Aktivierung von `docs-consolidation.checks.strict: true` sind dieselben vier Befunde
  `Severity.ERROR`. *Test `tests/test_doc_facts.py::test_v1_flags_manual_counts` +
  `::test_v1_four_quote_lines_all_detected`.*
- **AC-08** (IC-05, §5.1.1, V1a+V1b) Given dieselbe Datei mit zusätzlich den drei
  Suppressions-Fällen (Zahl in einer `agent-meta:docs-*-Region`; Zahl mit
  `<!-- agent-meta:docs-exempt: … -->`; Zahl innerhalb eines Fenced-Code-Blocks), when
  `check_no_manual_counts()` läuft, then erzeugt **keiner** dieser drei Fälle ein Finding,
  und die Gegenprobe `| Agents | 74 |` außerhalb jeder Region erzeugt **genau eines**.
  *Test `::test_v1_exempt_and_inside_marker` +
  `::test_v1_noun_before_number_is_detected`.*
- **AC-09** (IC-05, V3) Given `README.md:721-723` unverändert (Links auf `howto/setup/`,
  `howto/features/`, die nicht existieren), when `check_internal_links()` läuft, then ≥ 1
  `Finding(severity=ERROR, check="docs.internal_links")` mit `file="README.md"`. Nach M-8
  (W8) ist derselbe Befund leer. *Test `::test_v3_flags_dead_howto_links`.*
- **AC-10** (IC-05, V7) Given eine Wiki-Seite mit `type: Architecture` **ohne**
  `derived-from`, when `check_wiki_staleness()` läuft, then ≥ 1 Finding
  `check="docs.wiki_staleness"`. Given `derived-from` mit `mtime(Quelle) > derived-at`, then
  das Finding nennt `stale-source`. *Test `::test_v7_missing_and_stale_derived_from`.*
- **AC-11** (IC-05, V5) Given Ist-Zustand F13/F21, when `check_role_generation_parity()` läuft,
  then ist das Finding **WARNING** (nicht ERROR), weil
  `systems-engineering.enabled == false`. Given eine Testkonfiguration mit
  `systems-engineering.enabled: true` und einer `roles:`-Rolle ohne Template, then ist es
  `ERROR`. *Test `::test_v5_severity_depends_on_se_gate`.*
- **AC-12** (IC-05, V2) Given eine getrackte `docs/**/*.md` außerhalb von `archive/`, when
  `check_docs_index_completeness()` läuft und `docs/INDEX.md` fehlt den Pfad, then ≥ 1
  `Finding(severity=ERROR, check="docs.docs_index_completeness")`; `docs/INDEX.md` selbst und
  Pfade unter `archive/` erzeugen **kein** Finding. *Test `::test_v2_missing_page`.*
- **AC-13** (IC-05) Given alle neun Checks, when `consistency-check.py` ohne `--strict` läuft
  und keine Errors vorliegen, then ist `exit 0`; bei genau einem Error `exit 1`. Die
  bestehenden Exit-Code-Dokumentation (`consistency-check.py:23-26`) bleibt gültig.
  *Test `::test_exit_codes_unchanged_with_new_checks`.*

### M2 — Renderer, Indexer, Brücke

- **AC-14** (IC-07, IC-08) Given `README.md` mit **einer** Region
  `<!-- agent-meta:docs-begin facts -->…<!-- agent-meta:docs-end facts -->`,
  when `apply_fact_blocks(text, facts)` läuft, then ist der Body durch den
  `render_doc_fact_block("facts", facts)`-Output ersetzt und Header/Footer **byte-identisch**
  geblieben. *Test `tests/test_doc_renderer.py::test_apply_fact_block_single_region`.*
- **AC-15** (IC-07) Given eine `docs-begin`-Region **ohne** `docs-end`, when
  `apply_fact_blocks()` läuft, then ist der Rückgabewert byte-identisch zum Eingabetext **und**
  genau ein `log.warning` mit `docs` als Channel wurde emittiert. *Test
  `::test_unbalanced_marker_is_noop_with_warning`.*
- **AC-16** (IC-07, IC-08) Given zwei Regionen gleichen Namens, when `apply_fact_blocks()`
  läuft, then ist nur die **erste** ersetzt (Muster `context.py:42-50`) und ein
  `log.warning` nennt die Duplikat-Region. *Test `::test_duplicate_region_first_only`.*
- **AC-17** (IC-09, IC-10) Given ein Fixture mit 5 `.md` unter `docs/` (davon 1 unter
  `archive/`, 1 ohne Frontmatter, 1 ohne `# `-Heading), when `build_index_model()` +
  `render_docs_index()` zweimal laufen, then sind beide Outputs **byte-identisch** (NFA-01)
  und das Ergebnis enthält: die 3 nicht-archivierten Pfade als Links, den `archive/`-Pfad
  **nicht**, für die Frontmatter-lose Datei den Dateinamen als `title` und `—` als
  description, und **keine** erfundene Beschreibung. *Test
  `::test_index_deterministic_and_archive_excluded`.*
- **AC-18** (IC-10, IC-14) Given ein gerendertes `docs/INDEX.md`, when der Footer geprüft
  wird, then enthält er `facts-hash: <16 hex>` und `generator: doc-indexer/1`, und **kein**
  Datum, **keine** Uhrzeit, **keinen** absoluten Pfad, **keinen** Benutzernamen. Ein Regex
  `\d{4}-\d{2}-\d{2}` auf den generierten Footer-Bereich findet **keinen** Treffer.
  *Test `::test_footer_has_no_timestamp`.*
- **AC-19** (IC-16) Given `README.md`, dessen `agent-meta:docs-begin facts`-Region von Hand
  editiert wurde (Handprosa unverändert), when ein Sync mit aktivierter
  Drift-Erkennung läuft, then (a) die **Handprosa** kein Drift-Finding erzeugt,
  (b) ein Drift-Finding mit `provider == "docs-consolidation"` und Pfad
  `README.md#docs:facts` gemeldet wird, (c) `apply_fact_blocks()` die editierte Region
  **nicht** überschreibt, und (d) **keine** Datei namens `README.md#docs:facts` im
  `project_root` entsteht (fail-soft, `generated_file_drift.py:379-386`).
  *Test `tests/test_generated_file_drift_docs.py::test_marker_body_only` +
  `::test_no_backup_for_hash_key`.*
- **AC-20** (IC-13, IC-15) Given ein `docs/INDEX.md` mit exakt dem vom Scaffold geschriebenen
  Inhalt **und** `docs-consolidation.enabled: true` **und** `index-mode: full` **und**
  `resolve_index_mode() == "file-index"`, when `sync_docs_consolidation(..., dry_run=False)`
  läuft, then wird die Datei durch das Voll-Index ersetzt, `log.action("UPDATE",
  "docs/INDEX.md", …)` erscheint **einmalig**, und ein zweiter Lauf meldet `unchanged` mit
  **null** Schreibvorgängen. *Test `tests/test_doc_renderer.py::test_skeleton_replaced_once`.*
- **AC-21** (IC-15, IC-13) Given **dieselbe** Ausgangslage, aber `index-mode: skeleton`,
  when `sync_docs_consolidation()` läuft, then bleibt `docs/INDEX.md` byte-identisch zum
  Scaffold-Skeleton (`is_file_index_skeleton(text) is True`). Given **dieselbe** Ausgangslage,
  aber `resolve_index_mode() == "knowledge-engine"` (KE autoritativ, Szenario 52), when
  `sync_docs_consolidation()` läuft, then wird **kein** `docs/INDEX.md` geschrieben, der
  Eintrag steht in `skipped`, und ein `log.note` nennt den Grund.
  *Test `::test_skeleton_mode_preserves_scaffold` + `::test_ke_authoritative_writes_no_index`.*
- **AC-22** (IC-12) Given die Stage-Reihenfolge, when `sync.py` läuft, then ruft
  `_sync_stage_docs_consolidation` **nach** `scaffold_spec_plan_dirs` (`sync_pipeline.py:935`)
  und **vor** `_sync_stage_generated_file_hash_capture` (`:1090-1099`).
  **Korrektur der Rev.-0.1-Fassung (K5):** bei `knowledge-engine.enabled: true` mit
  `index.mode: knowledge-engine` löst `resolve_index_mode()` (`spec_plan_scaffold.py:40-44`)
  **nicht** zu `file-index` auf — der KE-Index bleibt autoritativ, es wird **kein**
  `docs/INDEX.md` geschrieben. Rev. 0.1 behauptete hier das Gegenteil („gewinnt der
  Voll-Index") und hätte Szenario 52 gebrochen.
  *Test `tests/test_doc_renderer.py::test_stage_order_after_scaffold` +
  `::test_ke_index_stays_authoritative`.*
- **AC-23** (IC-13) Given `dry_run=True`, when `sync_docs_consolidation()` läuft, then sind
  **null** Dateisystem-Schreibvorgänge erfolgt (Hash-Vergleich des `project_root` vor/nach,
  mit Ausnahme der von `sync.py` selbst geschriebenen `sync.log`), `written` listet die
  Write-Kandidaten, und `knowledge/wiki/log.md` ist unverändert. *Test
  `::test_dry_run_no_writes`.*
- **AC-24** (IC-13, IC-22) Given eine `project.yaml` **ohne** `docs-consolidation`-Block
  (der Absenz-Fall, den alle 63 Szenario-Fixtures repräsentieren), when ein normaler Sync
  läuft, then emittiert der Log `skip` mit `docs-consolidation` / `disabled in project.yaml`,
  **keine** Datei unter `docs/` wird angelegt oder verändert, **und** alle neun Checks
  V1–V9 sind No-op (kein Finding aus `consistency-check.py`). Given explizit
  `enabled: false`, then identisches Verhalten. *Test
  `::test_disabled_flag_is_noop` + `::test_absent_block_is_noop`.*
- **AC-25** (IC-11) Given `snippets/docs/repo-facts.md` mit eigenem YAML-Frontmatter und
  `{{DOCS_VERSION}}` im Body, when `_build_snippet_variables()` läuft, then ist
  `variables["DOCS_REPO_FACTS_BLOCK"]` frontmatter-frei, CRLF-normalisiert, ohne führendes/
  abschließendes `\n` (Muster `config.py:1842-1858`), und `QUALITY_PIPELINES_BLOCK` bleibt
  unverändert vorhanden (kein Namensraumkonflikt, `config.py:1882`). *Test
  `tests/test_doc_facts.py::test_docs_snippet_inlining_contract`.*
- **AC-26** (IC-07) Given ein Projekt ohne `docs/`-Verzeichnis und
  `docs-consolidation.enabled: true`, when ein Sync läuft, then wird **kein** Verzeichnis
  angelegt; `skipped` enthält `docs/INDEX.md` und ein `log.note` nennt den Grund. *Test
  `::test_no_docs_dir_is_skipped_not_created`.*
- **AC-27** (IC-07, NFA-02) Given `README.md` mit `DOCS_`-Region und
  `llms.txt` mit `DOCS_PROVIDERS_BLOCK`, when `apply_fact_blocks()` mit identischem
  Faktum-Dict läuft, then sind die Outputs byte-identisch — unabhängig von der
  Python-Dict-Iterationreihenfolge des Aufrufers. *Test `::test_output_independent_of_dict_order`.*
- **AC-36** (IC-23, R14 — **neu**) Given die handgepflegte
  `config/doc-facts-expected.yaml` mit den **elf** Sollwerten, when
  `load_expected_doc_facts()` und `compare_expected_doc_facts()` laufen, then ist die
  Ergebnisliste **leer**. Given eine **manipulierte** Datei (ein Sollwert absichtlich falsch),
  when dieselben Funktionen laufen, then enthält die Liste **genau einen** Eintrag mit
  `kind == "expected-mismatch"` und nennt beide Werte; `compute_doc_facts()` bleibt dabei
  unverändert (die Sollwerte fließen **nicht** in die Berechnung ein). V6 meldet dafür ein
  `Finding(severity=ERROR, check="docs.docs_facts_fresh", kind="expected-mismatch")` **obwohl**
  der gerenderte Block exakt `compute_doc_facts()` entspricht — das ist der Test dafür, dass
  der Kreis `doc_facts → Renderer → V6` gebrochen ist. *Test
  `tests/test_doc_facts_expected.py::test_expected_values_match` +
  `::test_mismatch_is_reported`.*
- **AC-37** (IC-16, M8 — **neu**) Given `.meta-config/drift-allowlist.yaml` mit
  `allow-edits: ["README.md"]`, when `scan_generated_file_drift()` einen Marker-Body-Drift in
  `README.md` auswertet (Store-Key `README.md#docs:facts`), then wird das Finding
  **unterdrückt** — die Allowlist wird gegen den **Basis-Pfad** gematcht, nicht gegen den
  `#`-Key (Beleg: `is_allowlisted` nutzt `fnmatch` auf den ganzen String,
  `generated_file_drift.py:82-84`). Given **denselben** Allowlist-Eintrag und einen Drift in
  der **Handprosa** von `README.md`, then wird die Handprosa **nicht** gehasht und erzeugt
  **kein** Finding. *Test `tests/test_generated_file_drift_docs.py::test_allowlist_matches_base_path`.*
- **AC-38** (IC-13, IC-15, IC-22, NG-10 — **neu, K5-Regressionsgarantie**) Given die
  **unveränderten** Szenario-Fixtures `tests/scenarios/configs/{50,51,52,54,55,56}*.project.yaml`
  (keines enthält einen `docs-consolidation`-Key; `run.sh:46-52` spielt sie 1:1 ein), when
  `tests/scenarios/run.sh` über diese **sechs** Szenarien läuft, then sind **alle sechs grün**,
  und im Einzelnen gilt: `asserts/54:26-27` findet die Datei **und** den Scaffold-Inhalt
  `File-based index fallback`; `asserts/55:24-25` dito; `asserts/56:31` findet die Datei;
  `asserts/50:32` findet die Datei; `asserts/51:32` findet **keine** `docs/INDEX.md`;
  `asserts/52:44` findet **keine** `docs/INDEX.md`. **Tragende Begründung für `51:32`
  (rev. 0.3, NEW-7 — korrigiert):** nicht der Scaffold-Gate, sondern der **Absenz-Default**.
  `configs/51-spec-plan-disabled.project.yaml:1-34` enthält **keinen** `docs-consolidation`-Key;
  `spec-plan-workflow.enabled: false` (`:11-12`) betrifft ausschließlich den **Scaffold**, einen
  anderen Writer, und ist für dieses Assert **nicht** die Begründung. Entscheidend ist:
  `docs-consolidation.enabled` ist bei Abwesenheit **`false`** (IC-22), also endet
  `sync_docs_consolidation()` mit `log.skip` und **ohne jeden Schreibzugriff** (IC-13, Zeile 1) —
  der Generator legt in Szenario 51 weder `docs/INDEX.md` an noch ein `docs/`-Verzeichnis.
  Zwei **nachrangige** Rückfall-Abschirmungen, falls die erste je entfiele: (2) `docs/`
  existiert in 51 nicht (kein Scaffold ⇒ `spec_plan_scaffold.py:49-51` bricht **vor** jedem
  `mkdir` ab) ⇒ IC-13, letzte Zeile („Consumer ohne `docs/`-Verzeichnis → `skipped`, **kein**
  `mkdir`"); (3) `resolve_index_mode()` löst in 51 auf **`file-index`** (KE disabled
  `configs/51-…:7-8` **oder** `external-system-override.enabled: true` `:20-21`,
  `spec_plan_scaffold.py:40-44`) und das Ziel ist **nicht** das Scaffold-Skeleton ⇒ IC-13,
  Zeile 3 („`file-index` und Ziel ist nicht das Scaffold-Skeleton → **kein** Schreiben").
  **Kein** Assert-Skript und **keine** Fixture-Config wird geändert (NG-10). *Test
  `tests/scenarios/run.sh 50 51 52 54 55 56`
  (bestehender Runner, keine neuen Dateien).*

### M3 — Migration

- **AC-28** (IC-17, M-1, M-3, M-4, M-6) Given W4/W5/W6 abgeschlossen, when
  `python3 scripts/sync.py --validate` läuft, then existieren `ARCHITECTURE.full.md`,
  `docs/superpowers/`, `howto/` **und** `docs/howto/` **nicht** mehr, und
  `git log --diff-filter=R --name-only` dieser Wellen zeigt für jede verschobene Datei ein
  **R**ena **+ A**dd-Paar (kein Inhalts-Diff, wenn `git log -M --follow` genutzt wird).
  *Test `tests/test_docs_consolidation_migration.py::test_moves_are_renames`.*
- **AC-29** (IC-18, IC-03, M-7 — **entzirkelt, M5**) Given der neue `ARCHITECTURE.md`-Stub,
  when er gelesen wird, then (a) enthält er einen generierten Diagramm-Index, einen Link auf
  `docs/architecture/INDEX.md` und auf `docs/architecture/00-overview-full.md` und **keine**
  eigene Architektur-Prose; (b) enthält er **keine** Zeile mit `Repo version:` **und**
  `docs/architecture/00-overview-full.md` enthält die Stale-Deklaration
  (`Repo version:` / `last substantively reviewed`); (c) `compute_wiki_staleness()` liefert
  für `knowledge/wiki/concepts/architecture.md` mit `derived-from:
  docs/architecture/00-overview-full.md` einen auswertbaren Wert (kein
  `missing-derived-from`); (d) der Link in `llms.txt:24` bleibt gültig. Der AC verbietet
  **nicht** etwas, dessen Quelle er gleichzeitig voraussetzt — die Quelle wandert mit (M-7).
  *Test `::test_architecture_stub_shape` + `::test_stale_declaration_moved_with_longform`.*
- **AC-30** (IC-17, M-8) Given W8 abgeschlossen, when `check_internal_links()` läuft, then
  sind `README.md`, `llms.txt` und `docs/**` frei von Findings auf **relative interne Links**
  (V3, exit 0). *Test `::test_no_dead_internal_links_after_migration`.*
- **AC-31** (IC-17, M-9, IC-03) Given eine Wiki-Seite in `knowledge/wiki/concepts/` mit
  `type: Architecture`, when die W5-Annotation angewandt ist, then trägt sie
  `derived-from: <existierender Rel-Pfad>` **und** `derived-at: <ISO-8601>`, und der Diff
  dieser Welle ist **ausschließlich** additiv (keine gelöschte Zeile außer der Ersetzung eines
  bestehenden `status:`-Werts). *Test `::test_wiki_annotation_is_additive`.*
- **AC-32** (IC-17, M-13, IC-22) Given `.meta-config/project.yaml`, when die `legacy:`-Liste
  gelesen wird, then enthält sie **vier** Einträge (die zwei alten + die zwei neuen Archivpfade,
  Ist-Stand `:61-63` hat zwei), und ein Sync mit einer der alten Pfade erzeugt eine
  Deprecation-WARNING statt eines Fehlers. *Test `::test_legacy_list_extended_additively`.*
- **AC-39** (IC-17, M-11, R15 — **neu**) Given `config/project-config.schema.json`, when die
  Datei geparst wird, then existiert ein **geschlossener** Top-Level-Block
  `docs-consolidation` (`additionalProperties: false`) mit **genau** den sechs Properties aus
  IC-22, und **keinem** Provider-Namen als Property-Namen. Given eine `project.yaml`, die
  `docs-consolidation.enabled: true` setzt, when die Config geladen wird, then ist die
  Schema-Validierung grün. *Test
  `tests/test_docs_consolidation_migration.py::test_schema_block_present_and_closed`.*
- **AC-40** (IC-02, IC-22 — **neu, schließt die W8-Lücke M3**) Given W8 abgeschlossen, when
  `llms.txt` gelesen wird, then kommt die Providerzahl **nicht** mehr als handgeschriebene
  Zahl im Fließtext vor, sondern ausschließlich aus einem `agent-meta:docs-*-Block`, dessen
  Wert `DOCS_PROVIDER_COUNT` entspricht; dasselbe gilt für `README.md:690` und für
  `docs/INDEX.md`. *Test `::test_provider_count_is_generated_in_readme_llms_index`.*

### M4 — Knowledge-Index-Generierung

- **AC-33** (IC-19, IC-22) Given `knowledge-engine.okf.index-mode: llm`, when ein Sync läuft,
  then ist `knowledge/wiki/index.md` byte-identisch (Generator stumm). Given
  `index-mode: generated`, then wird `index.md` deterministisch neu gerendert, und jede
  Wiki-Seite erscheint **genau einmal**. *Test
  `tests/test_knowledge_index_gen.py::test_index_mode_flag_and_determinism`.*
- **AC-34** (IC-20) Given zwei aufeinanderfolgende Syncs, von denen der erste genau eine
  Wiki-Datei ändert und der zweite keine, when beide laufen, then wird im ersten **eine** Zeile
  im Format `YYYY-MM-DD HH:MM — index/update — <summary>` angehängt und im zweiten **keine**;
  der bestehende Log-Inhalt ist in beiden Fällen unverändert (append-only). *Test
  `::test_log_append_only_on_change`.*
- **AC-35** (IC-19, IC-24, M-6 — **abgeschwächt, M6**) Given `index-mode: generated` und eine
  handgeschriebene `knowledge/wiki/index.md`, when der Generator **das erste Mal** aktiviert
  wird, then existiert **vor** dem ersten Rewrite eine vollständige Sicherung des
  Alt-`index.md` (Sibling `index.md.sync-backup-<YYYYmmdd-HHMMSS>` mit exakt dem Alt-Inhalt,
  Muster `backup_drifted_files`, `generated_file_drift.py:354-402, :388`, dry-run-geeignet).
  **Zurückgezogen** ist die Rev.-0.1-Forderung „der Rollback `index-mode: llm` stellt den
  Ausgangszustand byte-identisch wieder her": `index-mode: llm` stellt den **Generator**
  stumm, nicht die Datei wieder her; es gibt dafür keinen CLI-Pfad
  (`cli_commands.py:864`, `:888-900`, `backup.py:376+` sind Provider-Zip-Operationen).
  Der **Restore-Pfad ist jetzt IC-24 spezifiziert**, nicht behauptet.
  *Test `tests/test_knowledge_index_gen.py::test_first_activation_is_backed_up`.*
- **AC-41** (IC-24, M6 — **neu, ersetzt die Rückforderung aus Rev. 0.1**) Given die
  Sicherung `knowledge/wiki/index.md.sync-backup-<ts>` aus AC-35 und ein durch den
  Generator überschriebenes `index.md`, when `restore_wiki_index(project_root, log)` läuft,
  then ist `knowledge/wiki/index.md` **byte-identisch** mit dem Alt-Inhalt (verglichen über
  `io.content_hash`), und der Rückgabewert nennt genau den berührten Rel-Pfad. Given
  `dry_run=True`, when dieselbe Funktion läuft, then wird **nicht** geschrieben, aber der
  Zielpfad wird gemeldet. Given **weder** Sicherung **noch** Git-Tracking, when dieselbe
  Funktion läuft, then wird **nicht** geschrieben und `log.error` nennt den Grund
  (fail-closed, kein stiller Datenverlust). *Test
  `tests/test_knowledge_index_gen.py::test_restore_from_backup_sibling` +
  `::test_restore_dry_run` + `::test_restore_fails_closed_without_source`.*

---

## 8. Nicht-funktionale Anforderungen

| # | Anforderung | Nachweis |
|---|---|---|
| NFA-01 | **Idempotenz.** Zwei Läufe ohne Eingangsänderung erzeugen **null** Schreibvorgänge und identischen Output. | AC-17, AC-20, AC-33; Muster `standalone.py:386-389, :404-410` |
| NFA-02 | **Diff-Minimalität.** Generierte Dateien enthalten **keinen Zeitstempel, keine absolute Pfadangabe, keine Host-/User-Daten**. Der einzige veränderliche Teil ist der `facts-hash` (Muster) über die **nicht-volatilen** Fakten; Volatile Werte erzeugen genau **eine** Zeilen-Diff am Dateiende (M7). Der Hash bleibt stabil, solange kein nicht-volatiles Faktum kippt; er wechselt nur bei geänderten Faktuen. | AC-18, AC-03, AC-27, AC-34; Muster `standalone.py:362-368` |
| NFA-03 | **Provider-Parität.** Die Doku-Generierung ist **provider-neutral**: identischer `docs/INDEX.md`-, `README.md`- und `llms.txt`-Output unabhängig von der aktiven Provider-Menge. Kein `if provider == …` in M1–M4; Provider-Unterschiede nur über `provider_config`-Capability-Keys. | AC-01, IC-22 (keine Provider-Namen in Config-Keys); Regel `provider-agnostic`, Guard `tests/test_provider_agnostic_dispatch.py` |
| NFA-04 | **Downstream-Kompatibilität.** agent-meta ist ein Git-Submodul. In Consumer-Projekten sind M2 **und alle Checks V1–V9** per Default **aus** (`docs-consolidation.enabled` nicht `true` — Fail-off wie `knowledge.py:127`); M4 berührt `knowledge/` nur bei `index-mode: generated`. | AC-24, AC-26, AC-33, §6(e), IC-22 |
| NFA-05 | **Handedit-Schutz.** Eine von Hand editierte generierte Region wird **nicht** überschrieben, sondern gemeldet. Überschreiben ist explizit kein Ziel (Muster `generated_file_drift.py:591-596`: „skip-overwrite is an explicit non-goal"). Für Marker-Bodies ist das zwingend, weil der `#`-Key **kein** Backup erzeugen kann (IC-16, M8-Tabelle). | AC-19 |
| NFA-06 | **Rollback je Welle.** Jede Welle W1–W8 hat einen benannten, in §4/IC-17 angegebenen Rückrollpunkt, der **keine** andere Welle invalidiert. W7 hat zusätzlich einen **spezifizierten** Restore-Pfad (IC-24) und ist deshalb **isoliert und letzte Welle**. | AC-20, AC-21, AC-32, AC-35, AC-41 |
| NFA-07 | **Stdlib-only.** M1, M2, M4 importieren ausschließlich die Python-Standardbibliothek plus bestehende `scripts/lib`-Module; keine externe Abhängigkeit (Projektregel „Keine externen Python-Dependencies außer Stdlib"). Dependency-Invariante `variables.py:9-17` (keine Zyklen). | AC-01; Modul-Docstrings mit explizitem Importverbot |
| NFA-08 | **Begrenzter Blast Radius.** M3 berührt ausschließlich `docs/`, `knowledge/wiki/`, `README.md`, `ARCHITECTURE.md`, `.meta-config/project.yaml` (additive Config-Zeilen) und `config/project-config.schema.json` (ein geschlossener Block). `agents/`, `hooks/`, `commands/`, `config/*.yaml` und `knowledge/sources/` werden **nicht** inhaltlich angefasst — **eine** Ausnahme ist IC-21 `agents/1-generic/knowledge-indexer.md` in W7 (Rollback `git checkout`, Kollisionsvermerk R19, Reihenfolge in IC-21 verbindlich). | AC-28, AC-31, AC-32, AC-39 |
| NFA-09 | **Beobachtbare Drift.** Jede vom Generator geschriebene Doku-Datei ist über die Hash-Baseline drift-detektierbar (IC-16), inklusive Handprosa-Schutz (nur Marker-Body) und korrekter Allowlist-Wirkung auf den Basis-Pfad. | AC-19, AC-37 |
| NFA-10 | **Keine Secrets.** Generierte Dateien enthalten keine Env-Werte, Tokens oder Secrets. Die einzige Wertquelle ist `VERSION` plus Zählungen/Config-Struktur. | AC-18, IC-02 |
| NFA-11 | **Unabhängige Verifikation der Zahlen (neu, R14).** Die Faktum-Formel wird **nicht** nur von einem Kreis aus Generator und Selbstcheck verifiziert, sondern gegen eine zweite, handgepflegte Quelle (`config/doc-facts-expected.yaml`, IC-23) geprüft. **Elf** Sollwerte, jenseits der Reachability jedes Generators. | AC-36 |

---

## 9. Trace-Matrix

### 9.1 AC → Welle → betroffene Dateien

| AC | Welle | Betroffene Dateien (Code / Config / Doku) | V-Check |
|---|---|---|---|
| AC-01 | W1 | `scripts/lib/doc_facts.py` (neu) | — |
| AC-02 | W1 | `scripts/lib/doc_facts.py`; gelesen: `config/tier-presets.yaml`, `config/dod-presets.yaml`, `config/role-defaults.yaml`, `hooks/1-generic/*.sh`, `hooks/**/*.sh`, `commands/1-generic/`, `VERSION` | — |
| AC-03 | W1 | `scripts/lib/doc_facts.py`, `scripts/lib/doc_renderer.py` | — |
| AC-04 | W1 | `scripts/lib/doc_facts.py` | — |
| AC-05 | W1 | `scripts/lib/doc_facts.py`, `scripts/lib/roles.py:129` (gelesen) | V5 |
| AC-06 | W1 | `scripts/lib/consistency/placeholders.py:128-131` | — |
| AC-25 | W1 | `scripts/lib/config.py:1861-1914`, `snippets/docs/repo-facts.md` (neu) | — |
| AC-39 | W1 | `config/project-config.schema.json` (M-11) | — |
| AC-07 | W2 | `scripts/lib/consistency/docs.py`, `tests/fixtures/docs_v1_fixtures.md` | V1a, V1b |
| AC-08 | W2 | `scripts/lib/consistency/docs.py`, `tests/fixtures/docs_v1_fixtures.md` | V1a, V1b |
| AC-09 | W2 | `scripts/lib/consistency/docs.py`, `README.md:721-723` | V3 |
| AC-10 | W2 | `scripts/lib/consistency/docs.py`, `scripts/lib/doc_facts.py::compute_wiki_staleness` | V7 |
| AC-11 | W2 | `scripts/lib/consistency/docs.py` | V5 |
| AC-13 | W2 | `scripts/consistency-check.py:52-56` | alle |
| AC-36 | W2 | `config/doc-facts-expected.yaml` (neu), `scripts/lib/doc_facts.py::load_expected_doc_facts` | V6 (`expected-mismatch`) |
| AC-12 | W3 | `scripts/lib/consistency/docs.py` | V2 |
| AC-14 | W3 | `scripts/lib/doc_renderer.py`, `README.md` | V6 |
| AC-15 | W3 | `scripts/lib/doc_renderer.py` | V6 |
| AC-16 | W3 | `scripts/lib/doc_renderer.py` | V6 |
| AC-17 | W3 | `scripts/lib/doc_index.py` (neu), `scripts/lib/doc_renderer.py` | V2 |
| AC-18 | W3 | `scripts/lib/doc_renderer.py` (IC-10/IC-14) | — (Determinismus, per Unit-Test) |
| AC-19 | W3 | `scripts/lib/generated_file_drift.py:344-349, :379-386, :405-425` | — (Drift-Store, per Unit-Test) |
| AC-20 | W3 | `scripts/lib/spec_plan_scaffold.py:24, :62-68`, `scripts/lib/doc_renderer.py` | V4 |
| AC-21 | W3 | `scripts/lib/spec_plan_scaffold.py:27-44`, `.meta-config/project.yaml` (neuer Key) | V4 |
| AC-22 | W3 | `scripts/lib/sync_pipeline.py:922-945`, `scripts/lib/spec_plan_scaffold.py:40-44` | — |
| AC-23 | W1 | `scripts/lib/doc_renderer.py`, `scripts/lib/knowledge.py` (später) | — |
| AC-24 | W1 | `.meta-config/project.yaml` (neuer Key `docs-consolidation.enabled`) | — |
| AC-26 | W3 | `scripts/lib/doc_renderer.py` | — |
| AC-27 | W3 | `scripts/lib/doc_renderer.py` | V6 |
| AC-37 | W3 | `scripts/lib/generated_file_drift.py:82-84` | — (Allowlist, per Unit-Test) |
| AC-38 | W3 | `tests/scenarios/configs/{50,51,52,54,55,56}*.project.yaml` (unverändert) | — (bestehender Runner) |
| AC-28 | W4, W5, W6 | `ARCHITECTURE.full.md` → `docs/architecture/00-overview-full.md`; `docs/superpowers/{specs,plans}` → `docs/{specs,plans}/archive/superpowers/`; `howto/`, `docs/howto/` → `docs/guides/` | V8 |
| AC-29 | W4 | `ARCHITECTURE.md`, `docs/architecture/00-overview-full.md` | V3 |
| AC-30 | W8 | `README.md:721-724` (M-8), `docs/REQUIREMENTS.md:21` | V3 |
| AC-31 | W5 | `knowledge/wiki/**` (additive Frontmatter-Zeile) | V7 |
| AC-32 | W6 | `.meta-config/project.yaml:61-63` | V8 |
| AC-40 | W8 | `llms.txt:5`, `README.md:690` (M-12-Umfeld) | V1a, V6 |
| AC-33 | W7 | `scripts/lib/knowledge.py:103-205`, `.meta-config/project.yaml:18-29` | V7 |
| AC-34 | W7 | `scripts/lib/knowledge.py`, `knowledge/wiki/log.md:13-17` | — |
| AC-35 | W7 | `scripts/lib/knowledge.py`, `agents/1-generic/knowledge-indexer.md`, `knowledge/schema.md:41-46` | — |
| AC-41 | W7 | `scripts/lib/knowledge.py::restore_wiki_index` (IC-24) | — |

**V-Check-Spalte, korrigiert (M2).** Rev. 0.1 mappte sachfremde Checks: AC-19 (Marker-Body-Drift)
→ V9 `check_stale_backups` (Backup-Leichen) ist **falsch**, AC-18 (Footer-Determinismus) → V2 und
AC-29 (Stub-Form) → V3/V4 sind **irrelevant**. Neu: AC-19, AC-37, AC-38, AC-34, AC-35, AC-41
sind Invarianten **ohne** Konsistenz-Check (Store-, Szenario- und Restore-Ebene) und werden
per Unit-Test bzw. bestehendem Runner abgesichert — das ist die in §16 geforderte Begründung,
kein Lückenbleiben.

### 9.2 Welle → Modul → AC-Menge → Parallelität

| Welle | Modul | Inhalt | AC | Abhängig von | Parallel mit | Rückrollpunkt |
|---|---|---|---|---|---|---|
| W0 | — | Design-Freeze, Contract-Liste, **ein Wellen-Branch für das gesamte Vorhaben** (`feat/repository-documentation-consolidation-main`, Basis `origin/main`) mit **einem** PR gegen `main`; Wellen-Zuordnung über die **Wellenkennung im Commit-Titel**. **Rev. 0.4 — Ausführungskorrektur 2026-09-26 (OP-1):** ersetzt die Fassung Rev. 0.1–0.3 „**ein Branch pro Welle** (`chore/docs-consolidation-w<N>`), gestapelte PRs"; Einzelheiten und Belege in §17.6, Verbindlichkeitsformulierung im Absatz „PR-/Branch-Strategie" direkt unter dieser Tabelle — Entscheidungs-Records zu OQ2/OQ6/OQ8 — **OQ6/OQ8 entschieden 2026-09-26** (§11.2: `docs/INDEX.md` tracked, **kein** `.gitignore`-Eintrag; Regeneration über Sync/Validator) | — | — | — | — |
| W1 | M1+M2 | C1 DocFacts, C2 DocRenderer, C3 Snippet-Bridge, `config/doc-facts-expected.yaml`; Schema-Block (M-11); **rein additiv**, kein Datei-Diff außer `llms.txt` | AC-01…AC-06, AC-23…AC-25, AC-39 | W0 | W2 (verschiedene Dateien) | revert; kein Datei-Diff |
| W2 | M1 | Checks V1a/V1b, V3, V5, V6 (inkl. Sollwert-Vergleich), V7; **V1 startet WARNING**; V1-Fixture | AC-07…AC-11, AC-13, AC-36 | W1 (V6 braucht C1) | W3 | `docs-consolidation.checks.strict: false` |
| W3 | M2 | `docs/INDEX.md`-Generator + C8 Scaffold-Guard + Besitzregel; volatile-Sektion; Allowlist-Basis-Pfad; **erster echter Datei-Diff**, `docs/INDEX.md` tracked | AC-12, AC-14…AC-22, AC-26, AC-27, AC-37, AC-38 | W1 | W2 (PG-2); **W4 ist Vorgänger, nicht Partner** (rev. 0.4, Folge aus A14) | `git rm docs/INDEX.md`; Scaffold-Skeleton regeneriert |
| W4 | M3 | Architektur-Konsolidierung: `git mv` Langfassung, Root-Stub, Stale-Deklaration wandert mit (M-7) | AC-28 (Teil), AC-29 | W3 | **sequenziell** (PG-3, rev. 0.4) — **nicht** parallel | `git mv` zurück + Stub wiederherstellen |
| W5 | M3 | Guides: `howto/`- und `docs/howto/`-Auflösung (M-5, M-6) + `derived-from`-Annotation (M-9, M-10) | AC-28 (Teil), AC-31 | W1 (C7 braucht C1), W4 (PG-3) | **sequenziell** (PG-3, rev. 0.4) — **nicht** parallel | `git mv` zurück; Annotationen additiv revertierbar |
| W6 | M3 | Spec/Plan-Legacy: `git mv` + `legacy:` additiv erweitern | AC-28 (Teil), AC-32 | W3, W5 (PG-3) | **sequenziell** (PG-3, rev. 0.4) — **nicht** parallel | Config-Key additiv → Zeile entfernen |
| W7 | M4 | `index.md`-Generator (C6), `log.md`-Append, `schema.md`-Update, `knowledge-indexer`-Umschreibung, **Restore-Pfad** (IC-24) | AC-33…AC-35, AC-41 | W5, W3, Rollenpflege-Branch | — (kein Parallel) | `index-mode: llm` → Generator stumm; `restore_wiki_index()` |
| W8 | M1+M3 | `check_stale_backups` (V9), README-Totverweise (M-8), `llms.txt`-/`README.md`-Providerzahl (AC-40), `PROJECT_STRUCTURE`-Korrektur (M-12), ID-Deklaration (OQ4) | AC-30, AC-40 | W2, W3 | — | additiv |

**Jede Welle W1–W8 ist durch mindestens ein AC abgedeckt** (W1: **10**, W2: **7**, W3: **14**,
W4: 2, W5: 2, W6: 2, W7: 4, W8: 2; AC-28 zählt in W4/W5/W6 dreifach). Die Summen sind in Rev. 0.3
**neu gezählt** (NEW-5): Rev. 0.2 nannte W1: 9 und W3: 13 — W1 war AC-39, W3 war AC-38
(eigene AC-Spalte) nicht mitgezählt. **Nachzählung:** W1 = AC-01…AC-06 (6) + AC-23…AC-25 (3) +
AC-39 (1) = 10; W3 = AC-12 (1) + AC-14…AC-22 (9) + AC-26 (1) + AC-27 (1) + AC-37 (1) +
AC-38 (1) = 14. **W0** ist Definitions-Welle ohne AC. **M3-Änderungen:** Rev. 0.1Migrationen sind zu M-1…M-13 **neu** nummeriert
(alphabetische Reihenfolge, keine ID-Recycling); die Zuordnung AC → M-Nummer wurde
entsprechend nachgezogen.

**Ownership-disjunkte Parallelität:** W2 ‖ W3 sind gleichzeitig ausführbar (Dateien:
`scripts/lib/consistency/docs.py` / `docs/INDEX.md` + `scripts/lib/doc_*.py`). **W4/W5/W6 sind
rev. 0.4 als `sequenziell` ausgewiesen** (PG-3, ein Agent, W4 → W5 → W6) — Grund: alle vier
AC **AC-28, AC-29, AC-31, AC-32** verweisen per `::` auf denselben Testdatei-Anker
`tests/test_docs_consolidation_migration.py`; `check_plan_file_overlap` würde den Parallelstart
als Fehler melden, und jede `git mv`-Welle erzeugt R+A-Diffs auf denselben Stammpfaden
(Plan Rev. 0.4, Wellenübersicht/PG-3 und „Warum W2 ‖ W3 parallel ist, W4/W5/W6 aber nicht").
**Diese Angabe ist eine registrierte, offene Abweichung** — sie ist **nicht** in der Design-Quelle
begründet (das Design führt W4/W5/W6 als paarweise parallel, `docs/specs/2026-09-25-repository-documentation-consolidation-design.md:269-271`, zusätzlich `:275` — „W2 ‖ W3 ‖ W5 sind gleichzeitig ausführbar"),
sondern im Plan; Details, Status und Owner: **§13 A14** und **§17.8**. **Konflikt:** W1/W2
berühren `scripts/lib/config.py` bzw. `scripts/lib/consistency/*` — dieselben Dateien, an denen
Track A arbeitet. W1/W2 daher **sequenziell nach Track A**, ein Commit pro Datei, Rebase vor
jedem Merge. Zusätzlich **Fixture-Kollision**: die V1-Fixture `tests/fixtures/docs_v1_fixtures.md`
wird erst **nach** dem Track-A-Merge angelegt (§2.3, R15).

**PR-/Branch-Strategie** (R16, rev. 0.2; **rev. 0.4 — Ausführungskorrektur 2026-09-26, OP-1**): 8
Wellen auf **einem** Branch erzeugen einen ~65-Dateien-PR, der jeden konkurrierenden Doku-PR in
Konfliktdiffs taucht. Ein `git mv`-Welle-Merge macht jeden nachfolgenden Doku-PR konfligiert. Der
**Risiko-Inhalt bleibt unverändert**; verbindlich ist nach Rev. 0.4 die **Reihenfolge- und
Merge-Regel**, nicht die **Branch-Anzahl** — mit derselben Verbindlichkeitstiefe wie die
aufgehobene Fassung, aber mit dem ausgeführten Sachverhalt:

1. **Ein Wellen-Branch, ein PR.** Verbindlich: **ein** Feature-Branch
   `feat/repository-documentation-consolidation-main` (Basis `origin/main`) mit **einem** PR gegen
   `main`. **Kein** `chore/docs-consolidation-w<N>` wird angelegt; die Rev.-0.1- bis
   Rev.-0.3-Vorgabe „ein Branch **pro Welle**, gestapelte PRs in Reihenfolge W1→W8" ist
   **aufgehoben** (Rev. 0.4, §17.6).
2. **Wellen-Zuordnung über die Commits.** Verbindlich: Wellenkennung im Commit-Titel
   `docs(docs-consolidation): W<N> <Zweck>` und ein **Abschluss-Commit** je grüner Welle
   `docs(docs-consolidation): W<N> complete`. Der `W<N>`-**Präfix ist verbindlich** für (a) den
   Wellen-Abschluss-Commit und (b) jeden Commit-Titel, der **Wellen koordiniert** (Wellen-Übergang,
   Reihenfolge-/Merge-Entscheidung, Wellen-Sammelstand). Für **einzelne Datei-Commits innerhalb**
   einer Welle („ein Commit pro Datei", R3) ist der Präfix **optional**; der Titel folgt dann
   `docs(docs-consolidation): <Zweck>` und der **Commit-Body führt zwingend die Task-ID**
   (`Task: W<N>-<k>`). Die Wellenzuordnung ist damit dreifach garantiert: Abschluss-Commit,
   koordinierende Titel, Task-ID im Body.
3. **Merge-Regel.** Die `git mv`-Wellen (**W4/W5/W6**) werden **zuerst** gemergt, weil sie die
   Pfade verschieben und damit jeden folgenden Doku-PR sonst brechen. Die Wellen laufen als
   **sequenzielle** Commits in der Reihenfolge W1→W8; Rebase des Wellen-Branch gegen
   `origin/main` **vor** dem PR-Merge. Damit bleibt der **R16-Intent** — kein Konflikt-Diff in
   konkurrierende Doku-PRs — abgedeckt, ohne die ausgeführte Ein-Branch-Strategie aufzugeben.
4. **Dokumentierter Bestand.** Der überholte Vor-Branch `feat/repository-documentation-consolidation`
   (gemeinsames Präfix, divergente Doppelkopie der Spec-/Plan-Commits, **nicht** in `main`
   gelandet) bleibt auf ausdrückliche Nutzer-Vorgabe („nicht löschen") **erhalten**. Ein
   Post-Merge-Cleanup ist eine **eigene Entscheidung** und **nicht** Teil dieses Vorhabens; diese
   Spec schreibt weder Löschung noch Aufbewahrung eines Branches vor.
5. **Ausführungsnachweis und Belegkette.** `docs/plans/2026-09-25-repository-documentation-consolidation.md`
   (Rev. 0.4, Global Constraints, Task **W0-2**, K1/K8/K9) und
   `docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md` §7.1 (Spec-Abweichung OP-1) und §7.2
   (Commit-Bestand). **Design-Abweichung (rev. 0.4, A13):** das Design nennt in seiner W0-Zeile
   zwar nur *einen* Branch, aber mit ** anderem Namen** — `chore/docs-consolidation`
   (`docs/specs/2026-09-25-repository-documentation-consolidation-design.md:265`); gestapelte PRs
   kommen im Design nicht vor. Der Branch-**Name** ist damit eine bewusste Abweichung (§13 A13).
   §13 umfasst damit **14** Abweichungen (A1…A14).

**Reihenfolge-Begründung:** W1 zuerst (additiv, kein Diff, größte Erkenntnis). W3 vor W4/W6,
weil beide `git mv` sind und ein existierender kanonischer Index die neuen Pfade sofort
sichtbar macht. W7 zuletzt und isoliert, weil es die einzige Welle mit echtem Policy-Bruch,
Datenverlust-Potenzial und `agents/`-Berührung ist.

---

## 10. Nicht-funktionale Akzeptanz (Pipeline-Gate)

- `python3 scripts/sync.py --validate` (= `TEST_COMMAND`, `.meta-config/project.yaml:193`)
  darf bei **V1, V2, V3, V6** nicht grün sein (ab W3; in W2 V1 noch WARNING). **Neu (M7):**
  V6 meldet zusätzlich `kind=expected-mismatch` aus IC-23 — der Test wird bei einer
  unbeabsichtigten Zähländerung rot, auch wenn der Render-Output korrekt ist.
- `python3 scripts/sync.py --dry-run && python3 scripts/sync.py --validate`
  (= `TEST_COMMANDS`, `project.yaml:194`) läuft in jeder Welle grün.
- `python scripts/consistency-check.py --strict` (`:21`) ist ab W3 für `scripts/lib/doc_*.py`
  und `docs/INDEX.md` verpflichtend.
- **Szenarien 50, 51, 52, 54, 55, 56** (`registry.md:97-103`) bleiben nach **jeder** Welle grün —
  sie sind der härteste Regressionstest für B2/IC-15 und für die Absenz-Defaults aus IC-22.
  Verbindlich als **AC-38** verankert; kein Assert-Skript und keine Fixture-Config wird
  angefasst (NG-10).
- Szenario `64-docs-facts-drift.md` (Offset-Drift: Rolle hinzugefügt, Index nicht regeneriert)
  muss `--check` fehlschlagen lassen — **Ownership Track A**, in W2 koordiniert, nicht parallel
  geschrieben. **Nummer 64, nicht 63**: `63` ist bereits `63-context-file-modes`
  (`registry.md:110`, `asserts/63-context-file-modes.sh`,
  `configs/63-context-file-modes.project.yaml`) — eine Kollision, die das Design (§4, Zeile
  207) nicht gesehen hat (§17.1-NF-1).
- **Workflow-Vertrag, neu (OQ8):** V2 ist ab W3 **ERROR**. Legt ein Mensch eine neue
  `docs/**/*.md` an, ist `--validate` **rot**, bis ein Sync mit `docs-consolidation.enabled:
  true` gelaufen ist. Dieser Vertrag ist in W3 im Plan als **expliziter Schritt** zu
  dokumentieren. **Auslöser ist entschieden (Nutzer, 2026-09-26, §11.2 OQ8): der
  deterministische Sync-/Validator-Lauf** — kein Commit-Hook, kein CONTRIBUTING-Hinweis.

---

## 11. Entscheidungsstand (offene Fragen + geschlossene Punkte)

### 11.1 Offen — hier **nicht** entschieden

| # | Frage | Warum nicht entscheidbar | Empfehlung | Owner | Entscheidungsweg | Blockiert |
|---|---|---|---|---|---|---|
| **OQ1** | Sollen `knowledge/wiki/topics/` (43 Guides) vollständig in `docs/guides/` aufgehen, oder bleibt das Wiki als LLM-optimierte Aufbereitung bestehen? | **Produktentscheidung.** Wiki-Seiten sind nicht 1:1 mit Guides (Duplikate *und* Unique); ein Merge verändert den Lesefluss für Knowledge-Agenten. | `docs/guides/` = SSoT; Wiki-Topics behalten nur, was es in `docs/` nicht gibt; Duplikate → Redirect. Umfang erst nach dem C4-Baum-Inventar bezifferbar. | `main_chat` (Eskalation) | Produktentscheidung im Review-Loop; danach Folge-REQ | W5 |
| **OQ3** | `AGENTS.md`-Bootstrap-Block (66 hartgelistete Agenten am Repo-Ende) mitgenerieren? | Der Block liegt in einer generierten Kontextdatei, die in **alle** Submodule-Consumer geht → B6-Risiko. | **Scope-Grenze dieser Initiative** (NG-5). Eigene REQ, da derselbe `DOCS_*`-Mechanismus, anderer Blast Radius. | `requirements` (via `main_chat`) | Eigene REQ nach Abschluss von W8 | nach W8 |
| **OQ4** | ID-System: `REQ-*` vs. `SPEC-<NAME>-<JJJJ-MM-TT>` vereinheitlichen oder als zwei Ebenen definieren? | Betrifft `docs/REQUIREMENTS.md:4` und 4 Spec-Bäume; Umbenennung ist ein Traceability-Bruch für alle offenen Issues. | **Keine Umbenennung** (NG-6). `SPEC-*` = Spec-Pipeline-Artefakt-ID, `REQ-*` = Requirements-Master-ID, mit Einweg-Verweis. Die Deklaration selbst gehört in **W8** (F16) und ist als **AC-40** verankert. | `requirements` + `validator` | Entscheidung vor W8; Ergebnis als deklarativer Abschnitt in `docs/REQUIREMENTS.md` | W8 |
| **OQ9** | Welche der beiden Beispiel-Configs ist SSoT — `docs/guides/project.yaml.example` (179 Z, ab jetzt) oder `docs/guides/configs/project.yaml.example` (340 Z, aus `howto/configs/`)? | **Inhaltsentscheidung.** NG-1 verbietet Neuschreiben; ein Merge wäre Doku-Rewrite. Die Dateien decken unterschiedlich tiefe Abschnitte ab, eine bloße Löschung würde Beispielkonfiguration entfernen. | Beide behalten, die 340-Z-Datei als **vollständige Referenz** kennzeichnen, die 179-Z-Datei als **Kurzfassung** mit Pointer darauf. Zwei Zeilen Zusatz, kein Rewrite. | `technical-writer` + `documenter` | Entscheidung **vor W5**; Ergebnis ist eine `docs/guides/INDEX.md`-Zeile plus ein Pointer in beiden Dateien | **W5** |

**OQ6-Reihenfolgekorrektur (rev. 0.2, §17.1-NF-2):** Rev. 0.1 ließ OQ6 **W3** blockieren. Das
ist zu spät: die Entscheidung „tracked vs. untracked" bestimmt, **ob** `docs/INDEX.md` in
`.gitignore` landet, und `.gitignore` ist bereits in **W1** (M-11-Umfeld) bzw. W3 Welleninhalt
— eine in W3 getroffene `.gitignore`-Entscheidung erzeugt einen zusätzlichen Commit am
falschen Ort. Korrekt: Blockade **W0/W1**, Umsetzung in W3. **Erfüllt:** die Entscheidung
liegt seit 2026-09-26 vor (§11.2, OQ6).

**Nachtrag 2026-09-26 (Statuswechsel, kein Inhaltswechsel):** **OQ2**, **OQ6** und **OQ8** sind
durch **Nutzer-Entscheidung** vom 2026-09-26 **geschlossen** und stehen jetzt in §11.2. Die
verbleibenden offenen Fragen dieser Spec sind damit **OQ1, OQ3, OQ4, OQ9** — jede mit
Owner, Empfehlung, Entscheidungsweg und Wellen-Blockade. §16 (Selbstreview Rev. 0.3) und die
Wellenübersicht §9.2 nennen OQ2/OQ6/OQ8 noch als offen; das ist der **historische Rev.-0.3-Stand**
und bleibt als solcher stehen — maßgeblich für den aktuellen Status ist §11. **Ausnahme nur für
den Rev.-0.3-Stand:** §15 (Trace-Anker) ist dagegen ein **Ist-Zustands-Anker** und führt den
aktuellen Stand (§11.1 offen / §11.2 geschlossen).

### 11.2 Geschlossen — **nicht** mehr als offene Frage führen (N3)

| # | Ursprüngliche Frage | Status | Begründung |
|---|---|---|---|
| **OQ2** | `llms.txt` — **generiert** oder **handgepflegt**? | **GESCHLOSSEN 2026-09-26 — Hybrid: `llms.txt` bleibt handgepflegt, generiert werden ausschließlich `{{DOCS_PROVIDERS_BLOCK}}` und `{{DOCS_REPO_FACTS_BLOCK}}`.** | **Entschieden vom Nutzer** am 2026-09-26, über `main_chat` an den `orchestrator`. **Entspricht der Empfehlung dieser Spec** (Hybrid wie T-2 A) — die Entscheidung **bestätigt** sie, weicht also nicht ab. Handtext-Einleitung und Linkliste (`llms.txt:3-12`, `:17-19`, `:24`) bleiben **handgepflegt**; ein **Vollgenerieren** der Datei ist ausdrücklich **nicht** entschieden. **Folge für `docs-consolidation.sources` (IC-22):** `llms.txt` ist ein Wert der Liste der Hybrid-Dateien — Default bleibt `[README.md, llms.txt, ARCHITECTURE.md]` (IC-22-Tabelle, `volatile-facts`-Regel IC-02 unberührt); die Liste steuert nur, **welche** Dateien zwei Marker-Regionen erhalten, nicht wie viel Prose generiert wird. Genau diese beiden Blöcke sind es, die W3-7 (Plan) in `llms.txt:5` einführt. **Kein neues CLI-Flag** (NG-4), keine neue Doku-Datei, kein Eingriff in den Prosa-Ton. **IC/AC unberührt** (AC-25, AC-40) — betroffen ist ein Modus-Vertrag, kein Code-Vertrag. **W1-Blockade (§11.1) ist damit aufgehoben.** |
| **OQ6** | Soll `docs/INDEX.md` **tracked** sein (git) oder generiert-untracked wie `.claude/`? | **GESCHLOSSEN 2026-09-26 — `docs/INDEX.md` ist versioniert (tracked).** | **Entschieden vom Nutzer** am 2026-09-26, über `main_chat` an den `orchestrator`. Deckt sich mit der Empfehlung dieser Spec (tracked, weil `project.yaml:70` die Datei ohnehin als Fallback-Skeleton *im Repo* schreibt) und mit §3.1 („100 % generiert" unter `docs/`) sowie mit dem Plan (Create `docs/INDEX.md`, W3-6). **Folge:** `docs/INDEX.md` wird **nicht** in `.gitignore` aufgenommen; die `.gitignore`-Entscheidung ist damit gegenstandslos und der Wellenpunkt aus §9.2 (W0) entfällt ersatzlos. Der Vertrag aus `scripts/lib/spec_plan_scaffold.py:23` + `project.yaml:70` bleibt unverändert. **Blockade W0/W1 (§11.1-Hinweis) ist damit aufgehoben.** |
| **OQ8** | **Wer re-generiert `docs/INDEX.md`, wenn ein Mensch eine neue `.md` unter `docs/` anlegt?** V2 ist ab W3 **ERROR** — jede neue Doku-Datei blockiert `--validate` (= `TEST_COMMAND`) bis ein Sync gelaufen ist. | **GESCHLOSSEN 2026-09-26 — Regenerierung läuft deterministisch über Sync/Validator.** | **Entschieden vom Nutzer** am 2026-09-26, über `main_chat` an den `orchestrator`: kein Commit-Hook, sondern der bestehende, ohnehin verpflichtende Sync-/Validator-Lauf (`sync.py` im Default-Sync, `--validate` als `TEST_COMMAND`, `project.yaml:193`). **Kein neuer Hook, kein neuer Vertrag, keine neue Doku-Datei** (`docs/guides/project.yaml.example` bleibt unverändert). **Abweichung von der Empfehlung dieser Spec** (die einen `pre-commit`-Hook vorsah) — die Entscheidung des Nutzers geht vor; die IC/AC bleiben unberührt, da kein Code-, sondern ein Workflow-Vertrag betroffen ist. **V2 bleibt ERROR**, die Vertragsverletzung wird also weiter sichtbar; `W3` bleibt davon abhängig, dass der Sync-Pfad den Index tatsächlich schreibt (C2/C8). |
| **OQ5** | Müssen `DOCS_*`-Platzhalter in **bereits-released** agent-meta-Versionen funktionieren (Submodul-Pinning auf ältere Tags)? | **GESCHLOSSEN: kein Backport.** | IC-11 legt fest, dass Doku-Platzhalter **ausschließlich** von E3 (`doc_renderer`, IC-07) substituiert werden, **nie** von E1/E2 (`variables.py:56`, `builder.py:13`) — den Engines, die in Fremdprojekte deployen. Ein älterer Tag, der keinen `doc_renderer` enthält, kennt die Platzhalter nicht und löst sie nicht auf; ein **neuer** Tag in einem alten Consumer-Projekt löst sie auf, ohne dass der alte Tag etwas zurückportieren muss. NG-11 verankert das als Nicht-Ziel. Widerlegung wäre ein Trigger für eine **neue** REQ, keine offene Frage dieser Spec. |
| **OQ7** | Eine Spec-Datei (aktuell) oder vier Wellen-Specs (Design §11)? | **GESCHLOSSEN: eine Datei, vier Module.** | Repo-Konvention: eine `spec-id` pro Datei (`docs/specs/2026-09-15-reference-standards-design.md:1-8`). Die Aufteilung ist eine **Planungsentscheidung des Planners** (§4), keine Spec-Frage — sie wird im Plan entschieden, nicht in dieser Spec. Rev. 0.1 führte sie unnötig als OQ. |

---

## 12. Risiken (R1…R20) und Threat Model

### 12.1 Design-Risiken R1…R11 (mit Korrekturen aus Rev. 0.2)

| # | Risiko | W. | Mitigation (in dieser Spec verankert) | Owner |
|---|---|---|---|---|
| **R1** | **Doku-Diff-Churn**: jede Rollen-/Hook-Änderung erzeugt einen README-Diff; bei volatilen Zahlen Flattern. **Erweitert (M7):** der Flattern-Pfad ist nicht auf Hybrid-Dateien begrenzt — `DOCS_SCENARIO_COUNT` wird weiterhin in `docs/INDEX.md` gerendert (§3.2), Track A fügt laufend Szenarien hinzu ⇒ Diff in `docs/INDEX.md` **plus** `facts-hash`-Wechsel bei jedem Szenario. | hoch | Footer enthält **nur Fact-Hash, keinen Zeitstempel** (IC-14, NFA-02; Muster `standalone.py:365`). Volatile Fakten werden (a) in Hybrid-Dateien **unterdrückt** (IC-02, `docs-consolidation.volatile-facts`, AC-03), (b) in `docs/INDEX.md` in eine **`docs-volatile`-Sektion am Dateiende vor dem Footer** gerendert — Diff = genau **eine** Zeile, und (c) **nicht** in den `facts-hash` einbezogen, damit der Hash nicht flackert. Verbleibender Restdiff ist eine Zeile pro Szenario und damit im Review sichtbar begründet. | `developer` |
| **R2** | **LLM-Handpflege-Kollision im Wiki**: Knowledge-Agenten schreiben `index.md`, Generator überschreibt → Datenverlust (B5) | hoch | Erstsicherung vor dem ersten Rewrite (AC-35); **spezifizierter** Restore-Pfad (IC-24, AC-41 — Rev. 0.1 behauptete einen ohne Pfad); `index-mode: llm`-Rollback (IC-22); Diff-Review vor Aktivierung; W7 **isoliert und letzte Welle**; ReqogniLoom-Workspace-Export als Zwischenkopie | `knowledge-curator` + `orchestrator` |
| **R3** | **Track-A-Konflikt**: parallele Änderungen in `scripts/lib/`, `config/` **und `tests/fixtures/`** | hoch | W1/W2 sequenziell nach Track A; ein Commit pro Datei; Rebase vor jedem Merge; vor W1 `git log --oneline -20 -- scripts/lib/` prüfen (§2.3). **Ergänzt:** die V1-Fixture `tests/fixtures/docs_v1_fixtures.md` wird erst **nach** dem Track-A-Merge angelegt | `orchestrator` |
| **R4** | **V1-Fehlalarme.** *Neu begründet:* Rev. 0.1 stützte dieses Risiko auf `README.md:688` („6 DoD presets" sei korrekt). Diese Zeile ist **Drift** (F22) — das Argument trägt nicht mehr. Das Risiko bleibt **real**, aber aus einem anderen Grund: die Nomen-Whitelist in V1a ist breit (`test(s)`, `rule(s)`, `skill(s)`), und Fließtext wie „3 tests" in einem Guide würde matchen. | mittel | V1a/V1b prüfen Marker-**Abwesenheit**, nicht die Zahl; `agent-meta:docs-exempt`-Marker (IC-05, §5.1.1); die beiden einzigen **heute** korrekten Handzahlen (`README.md:689` Tier, `README.md:695` Commands) sind **beide** exempt-fähig; Start als **WARNING**, `checks.strict: false` per Default (IC-22); **Positiv- und Negativ-Fixture** verpflichtend (AC-07/AC-08) | `developer` |
| **R5** | Rollen-Parität (F13) | niedrig | V5 ist **gate-bewusst** (IC-04, AC-05, AC-11) und bleibt WARNING, solange `systems-engineering.enabled: false` (`project.yaml:12-13`). Ein etwaiger Fix ist ein **Config-Edit in eigener REQ** (NG-8) | `developer` |
| **R6** | **Link-Check-Fehlalarme** auf externe URLs/Anker | mittel | V3 prüft **nur relative repo-interne Pfade**; `http(s)://`, `mailto:` und `#anchor` werden nicht geprüft; Allowlist-Pattern über den bestehenden `drift-allowlist.yaml`-Mechanismus bzw. `config`-Key (IC-05) | `developer` |
| **R7** | **B2 Doppel-Writer** `docs/INDEX.md` (Generator vs. Scaffold) | hoch | C8 `is_file_index_skeleton()` (IC-15) **plus** verbindliche Stage-Reihenfolge Generator **nach** Scaffold (IC-12) **plus Besitzregel** (IC-13: der Generator überschreibt nur Skeletons und Neuanlagen); `index-mode: skeleton` als zweiter Hebel; Szenarien 50/51/52/54/55/56 als harte Regression (AC-20, AC-21, AC-22, **AC-38**) | `developer` |
| **R8** | **B1 Downstream-Bruch** durch `docs/superpowers`-Verschiebung | mittel | `legacy:`-Liste additiv erweitert (IC-17 M-13), alte Einträge **ein Release** mit Deprecation-WARNING toleriert (AC-32); Release-Notes-Pflicht, Minor-Bump | `release` |
| **R9** | **Scope-Creep**: ~190 `docs/*.md` (**HYPOTHESIS**, exakte Zahl erst über `DOCS_DOCS_FILE_COUNT` belegbar) + 100+ Wiki-Seiten → Migration wird zum Doku-Rewrite | mittel | Wellen sind additiv / `git mv`-only; **keine inhaltliche Neuschreibung** (NG-1); Inhaltsarbeit ist eigene REQ (u. a. OQ9); NFA-08 begrenzt den Blast Radius | `orchestrator` |
| **R10** | `AGENTS.md`-Bootstrap-Block driftet ebenfalls | niedrig | **Bewusst außerhalb des Scopes** (NG-5), als **OQ3** geführt, nicht in den Wellen | `requirements` |
| **R11** | `docs/CODEBASE_OVERVIEW.md` (2245 Z) liegt außerhalb des SSoT-Baums und gehört `documenter` | mittel | **NG-3**: im SSoT-Baum als eigenständiger Entry geführt, **Content-Ownership unangetastet**; Generierung ausschließlich für den Fakten-Footer. Beleg: `knowledge/wiki/log.md:30` („HARD CONSTRAINT — gehört documenter-Agent"); toter Verweis darin (`docs/CODEBASE_OVERVIEW.md:33-44`, `se-orchestrator.md`) wird als **eigenes Folge-Issue** geführt, nicht in dieser Spec korrigiert | `documenter` |

### 12.2 In dieser Spec neu identifizierte Risiken R12…R20

| # | Risiko | W. | Mitigation | Owner |
|---|---|---|---|---|
| **R12** | Der `DOCS_`-Prefix kollidiert semantisch mit den **bereits existierenden** Built-ins `DOCS_LANGUAGE` / `INTERNAL_DOCS_LANGUAGE` (`project.yaml:183-184`) und den `placeholders.py`-Typo-Mappings (`:135-136`) | mittel | IC-02 verbietet explizit die Belegung dieser zwei Namen; `DOCS_`-Namensraum ist auf **Fakten** (`_COUNT`, `_VERSION`, `_BLOCK`) beschränkt; Prefix-Regex `:177` + `_KNOWN_TYPOS` bleiben unangetastet | `developer` |
| **R13** | `PROJECT_STRUCTURE`-Korrektur (M-12) verändert `AGENTS.md`/`CLAUDE.md` in **jedem** Consumer (B6) | niedrig | Additiver Config-Edit; managed-block-Mechanismus (`context.py:36-38`) fängt Handpflege ab; Drift-Detection meldet; als expliziter Review-Punkt in W8 (IC-17) | `developer` + `release` |
| **R14** | **Falsche-Fakt-Kette (Korrektheitsrisiko, nicht Churn).** `doc_facts → Renderer → V6` ist ein **geschlossener Kreis**: V6 vergleicht den Render-Output gegen `compute_doc_facts()`, also gegen dieselbe Formel, die ihn erzeugt hat. Ein **systematisch** falscher Faktor passiert **alle** Gates dieser Initiative. Real belegt: Rev. 0.1 enthielt **drei** solche Zählfehler (F19 4 statt 5, F22 6 statt 7, F14 6/7 statt 7/8) — keiner wäre von V1–V9 gefunden worden. | **hoch** | **IC-23 + AC-36:** unabhängig handgepflegte Sollwert-Datei `config/doc-facts-expected.yaml` (**elf** Werte, rev. 0.3 — die Yaml-Datei hat genau 11 Einträge; Rev. 0.2 nannte an dieser Stelle fälschlich „12"), geprüft von `load_expected_doc_facts()` / `compare_expected_doc_facts()`; V6 meldet `kind=expected-mismatch` als ERROR. **Restrisiko (bewusst akzeptiert):** jede gewollte Zahlenänderung macht den Test rot, bis die Datei im selben Commit mitgezogen wird — das ist der gewollte Review-Signalweg, kein Defekt | `developer` + `validator` |
| **R15** | **Kollision geht über Track A hinaus.** R3 nennt nur `scripts/lib/` und `config/`. Real betroffen sind (a) **sechs** Szenario-Asserts (50/51/52/54/55/56) und (b) `config/project-config.schema.json`, das in Rev. 0.1 **nirgends** als Operation auftauchte. **Korrektur der Einordnung:** das Wurzel-Schema ist `additionalProperties: true` (`:2425`) — die 6 neuen Keys brechen die Validierung **nicht**; fehlend wären Autocomplete und der Tippfehler-Wächter, den das Repo selbst ausdrücklich nutzt (`:2058`, `:2073`). | mittel | (a) Absenz-Defaults fail-off + Besitzregel + `knowledge-engine`-Schreibverbot ⇒ alle sechs Szenarien bleiben unverändert grün (AC-38, NG-10). (b) **M-11** nimmt den Schema-Block als Operation in **W1** auf (IC-17, AC-39). (c) V1-Fixture erst nach Track-A-Merge (§2.3) | `developer` |
| **R16** | **PR-/Branch-Kollision.** 8 Wellen, ~65 Dateien, ein Branch ⇒ ein Groß-PR, der jeden konkurrierenden Doku-PR in Konflikt-Diffs taucht. Ein `git mv`-Welle-Merge macht jeden nachfolgenden Doku-PR konfligiert. **Risiko-Inhalt unverändert.** | mittel | **Rev. 0.4 (Ausführungskorrektur 2026-09-26, OP-1):** die Branch-Anzahl ist **nicht** der Lösungsansatz — abgedeckt wird der R16-Intent über **Reihenfolge- und Merge-Regel**: (1) **ein** Wellen-Branch `feat/repository-documentation-consolidation-main` mit **einem** PR gegen `main`, kein `chore/docs-consolidation-w<N>`; (2) Wellen **sequenziell** W1→W8, Wellenzuordnung über Wellenkennung im Commit-Titel `docs(docs-consolidation): W<N> …` + Abschluss-Commit `… W<N> complete`; (3) `git mv`-Wellen (W4/W5/W6) **zuerst** mergen; (4) ein Commit pro Datei, Task-ID im Commit-Body; (5) Rebase gegen `origin/main` vor dem PR-Merge. Die aufgehobene Forderung „Branch pro Welle, gestapelte PRs" (Rev. 0.1–0.3) und die Begründung der Korrektur stehen in §9.2 (Absatz „PR-/Branch-Strategie") und §17.6 | `orchestrator` + `git` |
| **R17** | **Downstream-Asymmetrie `docs/INDEX.md`.** In Consumer-Projekten bleibt das Scaffold-Skeleton, die V-Checks sind per Default aus. Wäre das nicht so, wäre V2 dort **dauerhaft** rot — eine Asymmetrie, die als „grüner Zustand" erscheint, obwohl nie geprüft wurde. | mittel | **Bewusste, dokumentierte Asymmetrie:** alle neun Checks sind an `docs-consolidation.enabled` gebunden (IC-05-Common-Gate), in Consumer also vollständig inaktiv. Das ist Absicht (NFA-04) und **sichtbar**: V1 meldet nichts, wo gar nicht geprüft wird. Wer Consumer absichtlich prüfen will, setzt den Key explizit. Ein „agent-meta-Eigenerkennung\"-Heuristik-Gate wird **nicht** gebaut (es würde in Fremd-Repos Doku-Claims aufstellen, die niemand gepflegt hat) | `developer` |
| **R18** | **Auto-Commit-Interaktion.** *Analysiert und nicht zutreffend (Rev. 0.2):* die Befürchtung, generierte Doku-Dateien könnten in den Auto-Commit-Pfad geraten, ist **unbegründet**. `_sync_stage_auto_commit_allowlist` (`sync_pipeline.py:1102-1117`) liest `config` + `active_roles` über `resolve_auto_commit_config(config, active_roles, agent_meta_root)` und schreibt `.meta-config/auto-commit-allowlist.json` als **generierte** Ausgabe; der Drift-Store `.meta-config/generated-file-hashes.json` wird dort **nicht** gelesen. Auch der vom Reviewer genannte Pfad `.meta-config/auto-commit-allowlist.json` **existiert im Repo nicht** (Glob: keine Treffer) — es ist ein Sync-Output. | — | keine Mitigation nötig; die Analyse ist in IC-16 (M8-Tabelle) als Beleg verankert, damit die Frage nicht erneut aufgerollt wird | `—` |
| **R19** | **`knowledge-indexer`-Kollision.** IC-21 fasst `agents/1-generic/knowledge-indexer.md` an — eine Datei in der von Track A / Rollenpflege berührten Zone. Ein Rebase der Rollenpflege landet sonst in einem Template-Diff. | niedrig | **Verbindliche Reihenfolge** in IC-21: W7 startet erst nach dem Rollenpflege-Merge; IC-21 ist der **letzte** Commit von W7. Kollisionsvermerk steht dort, nicht nur in einer Klammer (N2) | `orchestrator` |
| **R20** | **V2-ERROR vs. menschliche Doku-Erstellung.** Ab W3 ist V2 ERROR: legt ein Mensch eine neue `docs/**/*.md` an, ist `--validate` (= `TEST_COMMAND`) **rot**, bis ein Sync mit `docs-consolidation.enabled: true` gelaufen ist. Das ist ein **Workflow-Vertrag ohne Owner** und blockiert potenziell jeden Doku-PR. | **hoch** | Als **OQ8** mit Owner (`orchestrator` + `git`), Reihenfolge (Entscheidung vor W3) und Empfehlung (Commit-Hook) aufgenommen; der Vertrag ist in §10 als expliziter W3-Schritt festgehalten. **Nicht** durch Abschwächen von V2 gelöst — V2 ist der Zweck der Initiative. **Stand 2026-09-26:** die Empfehlung (Commit-Hook) ist **nicht** übernommen — der Nutzer hat den deterministischen **Sync-/Validator-Lauf** entschieden (§11.2 OQ8); der Owner- und Reihenfolge-Vertrag bleibt, **V2 bleibt ERROR**, ein neuer Hook wird **nicht** gebaut | `orchestrator` |

### 12.3 Threat Model (vier Fragen)

**1. Was bauen wir?** Einen deterministischen Doku-Fakten- und Index-Generator (4 Module,
8 Dateien in `scripts/`, 1 neue Config-Datei, 1 Schema-Block) plus ~65 Doku-Dateien-Umzüge
und 9 Konsistenz-Checks. Kein Datenspeicher, keine Authentifizierung, keine Autorisierung,
keine Netzwerkzugriffe, keine neuen Abhängigkeiten. Nutzerursprung: **intern**
(agent-meta-Repo) + **Downstream-Submodule** (agent-meta wird als Git-Submodul eingebunden).

**2. Was kann schiefgehen?**

| # | Bedrohung | Real belegt? |
|---|---|---|
| a | **Falscher Fakt wandert in eine getrackte `README.md`/`llms.txt`** und fällt im Review nicht mehr auf, weil er maschinell „aussieht". Ein systematisch falscher Zähler passiert V1–V9 **alle**, weil V6 gegen dieselbe Formel prüft | **ja** — Rev. 0.1 enthielt drei solche Fehler (Tier 4/5, DoD 6/7, Pipelines 6/7 bzw. 7/8) |
| b | **Doppel-Writer** zerstört den `docs/INDEX.md`-Vertrag (Generator überschreibt Scaffold-Skeleton oder umgekehrt) | **ja** — 6 Szenario-Asserts hängen exakt daran (`asserts/50:32`, `:51:32`, `:52:44`, `:54:26-27`, `:55:24-25`, `:56:31`) |
| c | Generator überschreibt LLM-eigenes `knowledge/wiki/index.md` → Datenverlust | **ja** — Policy-Bruch gegen `knowledge.py:112-114` |
| d | Unvollständige Fakten rendern `docs-empty`-Marker in eine **Referenzdatei**, die von Nutzern gelesen wird | möglich — `{{DOCS_*}}` löst in `llms.txt`/`README.md` sichtbar auf |
| e | Ein Allowlist-Eintrag unterdrückt genau die Drift-Findings, die er unterdrücken soll (Basis-Pfad vs. `#`-Key) | **ja, im Code belegt** — `fnmatch` matcht den ganzen String (`generated_file_drift.py:82-84`) |
| f | Neue Doku-Datei blockiert `--validate` und damit den gesamten Dev-Workflow (R20/OQ8) | möglich, Owner unbekannt |

**3. Was tun wir dagegen?**

- **Master-Schalter:** `docs-consolidation.enabled` fail-off, für **Writer und Checks
  gleichermaßen** — schaltet das gesamte Feature ab (IC-13, IC-05, IC-22).
- **Zweiter Hebel:** `index-mode: skeleton` lässt den Scaffold-Skeleton unangetastet (IC-15).
- **Besitzregel:** der Generator überschreibt nur, was er selbst erzeugt hat (IC-13).
- **Unabhängige Zahlenquelle:** `config/doc-facts-expected.yaml` bricht den Kreis
  `doc_facts → Renderer → V6` (IC-23, R14) — das ist die **einzige** Gegenmaßnahme gegen (a).
- **Szenarien als Fremd-Gate:** 50/51/52/54/55/56 sind unveränderbar und schützen (b)
  unabhängig von dieser Spec (AC-38).
- **First-Write-Sicherung + spezifizierter Restore-Pfad** gegen (c) (AC-35, IC-24, AC-41).
- **`docs-empty`-Marker** + Fact-Hash-Footer + `dry_run`-Vertrag gegen (d) (IC-07, IC-14).
- **Allowlist-Basis-Pfad-Regel** + AC-37 gegen (e).
- **Workflow-Vertrag** (OQ8, R20) gegen (f).

**4. Welche Konsequenzen?**
- (a) Nutzer und alle Downstream-Submodule erhalten falsche Zahlen über `README.md` und
  `llms.txt`; die Korrektur ist teuer, weil sie über Submodul-Grenzen propagiert. **Schwer.**
  → R14, IC-23.
- (b) Roter Regressionstest auf `TEST_COMMAND`-Ebene ⇒ **alle** Wellen blockiert. **Schwer.**
  → R7, IC-12/IC-13/IC-15, AC-38.
- (c) Datenverlust im Wiki-Index; Recovery über Sibling-Backup oder Git. **Mittel**, weil
  `knowledge/` git-getrackt ist. → R2, IC-24.
- (e) Drift wird still übersehen — das Gegenteil des Ziels, aber **leise**. **Mittel.**
  → R17-Klassifikation, AC-37.
- (f) Frustration, Workaround über `checks.strict: false`, damit der Gain wieder verloren ist.
  **Mittel.** → R20, OQ8.

**Bewertung:** Alle sechs Bedrohungen sind adressiert, aber **eine** nur unvollständig: (a)
wird ausschließlich durch eine **Handpflege-Datei** gebrochen — ein Fehler in *dieser* Datei
ist wiederum ein Fehler, nur in einer anderen Quelle. Das ist eine echte, benannte
Restgrenze (R14-Restrisiko in IC-23) und kein Versehen: eine dritte, unabhängige Quelle wäre
Over-Engineering für elf stabile Zählwerte.

---

## 13. Abweichungen vom Design (bewusst, begründet)

| # | Design sagt | Diese Spec sagt | Begründung |
|---|---|---|---|
| **A1** | F13: „Rollen-Parität gebrochen: Template existiert, `roles:` **nicht**" (`project.yaml:91-151`) | **Korrigiert:** `se-component-requirements` **ist** in `roles:` (`.meta-config/project.yaml:148`) und das Template existiert. Die Paritätsverletzung entsteht **allein** aus `systems-engineering.enabled: false` (`:12-13`) → `agent_sync.py:548` überspringt alle 14 `se-*`-Rollen | VERIFIED am Working Tree. Die Design-Aussage ist falsch; sie hätte in W8 zu einem wirkungslosen Config-Edit geführt („Einzeiler in `project.yaml roles:`", R5), obwohl die Rolle dort bereits steht |
| **A2** | V5: „`project.yaml roles:` ⊄ generierte Provider-Agent-Dateien" | **Gate-bewusst:** Vergleichsmenge ist `compute_active_roles()` = `roles` ∩ Templates ∩ `resolve_activation_gates()` (IC-04) | `roles:` umfasst 59 Einträge (`:92-150`), `role-defaults.yaml:1` umfasst 84, SE ist deaktiviert → die Design-Formel ist ein **Dauerfehlalarm** (F21) und hätte V2/W2 blockiert. Siehe NG-8 |
| **A3** | §3.4: „unbekannter Platzhalter-Name → bleibt wörtlich + **`--validate` ERROR**" | Unbekannter Name → bleibt wörtlich (`substitution.py:86-87`) + `placeholders.unknown` = **WARNING** (`placeholders.py:177-182`). Das **ERROR**-Gate ist **V6** | VERIFIED: `check_placeholders` kennt nur WARNING. Die Design-Formulierung versprach ein Gate, das im Code nicht existiert. Zusätzlich verlangt IC-06 die Registrierung des `DOCS_`-Prefixes, die das Design nicht nannte |
| **A4** | C8 als alleiniger Schutz gegen den Doppel-Writer (B2) | **C8 plus verbindliche Stage-Reihenfolge**: Generator **nach** `scaffold_spec_plan_dirs` (IC-12) | `scaffold_spec_plan_dirs` schreibt `docs/INDEX.md` nur im `file-index`-Modus (`spec_plan_scaffold.py:62-68`) und läuft in `_sync_stage_knowledge_and_isolation` (`sync_pipeline.py:935`). Läuft der Generator davor, gewinnt der Scaffold. Reihenfolge ist die stärkere, einfachere Garantie; C8 bleibt als zweite Verteidigungslinie |
| **A5** | §3.2: `{{DOCS_SCENARIO_COUNT}}` Quelle = `tests/scenarios/` | Quelle = `tests/scenarios/asserts/*.sh` (63 Dateien); `tests/scenarios/*.md` enthält **nur** `registry.md` | VERIFIED. Mit der Design-Quelle wäre der Wert 1 statt 63 |
| **A6** | §3.2/§0 F3: „Ist 15 `.sh` unter `hooks/**`" | Ist **17** `.sh`; nach der Exklusionsregel (ohne `lib/`, ohne `release-gates/`) **13** | VERIFIED per Glob. Die Designzahl 15 ist falsch; die Exklusionsregel selbst ist korrekt und wird in IC-02 kodiert |
| **A7** | F-Liste endet bei F18 | F19 **gestrichen** (Tier-Presets sind 5, `README.md:689` ist korrekt); ergänzt **F20** (Skeleton-Marke), **F21** (`roles` 59 vs. 84 vs. generiert), **F22** (DoD-Presets 7 vs. `README.md:688` „6"), **F23** (vierter Guide-Ort `docs/howto/`), **F24** (zwei Beispiel-Configs), **F25** (Config-Schema kennt die Keys nicht) | **Korrektur einer eigenen Fehlkorrektur.** Rev. 0.1 führte F19 als Befund und hätte den Wert **4** generiert; `config/tier-presets.yaml` hat nachweislich 5 Tiers (`:1, :31, :85, :115, :145`). F19 ist ersatzlos entfallen (kein ID-Recycling); die übrigen sechs Befunde sind am Working Tree verifiziert. F20 begründet die Marke in IC-15, F21 die Korrektur A2, F22 die Zahl 7 in IC-02, F23 die Migration M-6, F24 die offene Frage OQ9, F25 die Operation M-11 |
| **A8** | Drift über `capture_generated_file_hashes()` „README-Marker-Regionen und `docs/INDEX.md` aufnehmen" | **Nur** `docs/INDEX.md` + `docs/architecture/INDEX.md` als ganze Dateien; Marker-**Hosts** (`README.md`, `llms.txt`, `ARCHITECTURE.md`) nur über den **extrahierten Marker-Body** mit Store-Key `<datei>#docs:<region>` | `README.md` enthält Handprosa (hybrid). Ein Ganzdatei-Hash würde jede Prosa-Änderung als Drift melden — R1-Churn. Für Marker-Bodies gilt NFA-05 (nicht überschreiben), weil `backup_drifted_files` für einen `#`-Key fail-soft **kein** Backup erzeugt (`generated_file_drift.py:379-386`, verifiziert) — und `is_allowlisted` wird deshalb gegen den **Basis-Pfad** gematcht (`:82-84`, verifiziert). Siehe IC-16, AC-19, AC-37 |
| **A9** | §11: vier Wellen-Specs | **Eine** Spec-Datei mit vier abgeschlossenen Modulen (§4) | Auftragsvorgabe; die Repo-Konvention verlangt eine `spec-id` pro Datei, nicht eine Datei pro Welle. Aufteilung ist **Planungsentscheidung** des Planners (§4) — als **OQ7 geschlossen** geführt, nicht offen (§11.2) |
| **A10** | Design nennt keinen `docs-consolidation`-Config-Block | IC-22 definiert **sechs** additive Keys mit **Fail-off**-Defaults (`enabled` = `false` bei Abwesenheit, auch in agent-meta explizit `true`) | **Korrektur der Rev.-0.1-Fassung (K5).** Rev. 0.1 setzte „Schema-Default = Default agent-meta" **und** `enabled: true` als Abwesenheits-Default — unvereinbar, weil `true` selbst ein Verhaltenswechsel bei Abwesenheit ist. Auflösende Präzedenz: `knowledge.py:127` (`ke_config.get("enabled", False)`), fail-off für Writer **und** Checks. Ohne diese Regel hätte die neue Stage 6 Szenarien gebrochen. Zusätzlich: M-11 nimmt `config/project-config.schema.json` als Operation auf (R15) |
| **A11** | V1 gilt als ERROR ab Start | V1 startet **WARNING** in W2, wird nach W3 ERROR — wie im Design §6 W2 vorgesehen; zusätzlich `docs-consolidation.checks.strict` (IC-22) | Konsistent mit Design W2 („V1 startet als WARNING, `--validate` noch nicht blockierend"); als Config-Key operationalisiert, damit B4 für Consumer auflösbar ist |
| **A12** | **Neu (rev. 0.2):** IC-03 las die Stale-Deklaration aus `ARCHITECTURE.md:3` (Design §5.3: „aus `ARCHITECTURE.md:3` maschinell extrahiert") | Quelle ist **`docs/architecture/00-overview-full.md`**; die Deklaration **wandert mit** der Langfassung (M-7) | Der Design-Satz und IC-18/AC-29 waren **zirkulär**: der Stub verliert nach W4 (M-2) alle eigenen Inhalte, also auch `:3` — die Quelle der Extraktion wäre weg. Beleg: `knowledge/wiki/index.md:24` beschreibt `concepts/architecture.md` als „Rohkopie von **ARCHITECTURE.full.md**", nicht von `ARCHITECTURE.md`. IC-03, IC-18 und AC-29 sind konsistent auf die Langfassung umgestellt |
| **A13** | **Neu (rev. 0.4):** Design-W0 nennt den Branch `chore/docs-consolidation` — `docs/specs/2026-09-25-repository-documentation-consolidation-design.md:265`, Spalte „Inhalt" der Tabelle in §6 MIGRATION_ORDER | Verbindlich ist seit Rev. 0.4 der Wellen-Branch **`feat/repository-documentation-consolidation-main`** (Basis `origin/main`) mit **einem** PR gegen `main` (§9.2 W0-Zeile und Absatz „PR-/Branch-Strategie", Punkt 1) | **Nutzer-Vorgabe + Plan-Korrektur K1/K9** (Plan Rev. 0.4, Global Constraints, Task **W0-2**). Die Rev. 0.1–0.3-Fassung „ein Branch **pro Welle** (`chore/docs-consolidation-w<N>`)" war selbst schon eine **Eigenkonstruktion** ohne Design-Deckung — das Design verlangt an keiner Stelle gestapelte PRs und nennt **einen** Branch. Korrektur des Branch-**Namens** gegen die Design-Angabe; der **Umfang** (ein Branch, ein PR) stimmt mit dem Design überein. **Verifiziert am 2026-09-26:** Design-Zeile gelesen, Branch-Name wörtlich `chore/docs-consolidation`. Status: **geschlossen** (Nutzer-Bestätigung Rev. 0.4 vom 2026-09-26, §17.7) |
| **A14** | **Neu (rev. 0.4):** Design §6 führt **W4, W5 und W6 paarweise parallel** — `docs/specs/2026-09-25-repository-documentation-consolidation-design.md:269` (W4: „W5, W6"), `:270` (W5: „W4, W6"), `:271` (W6: „W4, W5"); **zusätzlich** `:275` („Ownership-disjunkte Parallelität: W2 ‖ W3 ‖ W5 sind gleichzeitig ausführbar") — W5 ist danach auch mit **W2/W3** parallel ausgewiesen | §9.2 weist **W4 → W5 → W6 sequenziell** aus (`parallel_group` PG-3, ein Agent) | **Plan-Begründung (PG-3, Plan Rev. 0.4, „Warum W2 ‖ W3 parallel ist, W4/W5/W6 aber nicht"):** die vier AC **AC-28, AC-29, AC-31, AC-32** verweisen **alle** per `::` auf denselben Testdatei-Anker `tests/test_docs_consolidation_migration.py`; parallel ausgeführte Tasks, die dieselbe Datei anlegen oder erweitern, sind nicht ownership-disjunkt — `check_plan_file_overlap` (`scripts/lib/orchestration.py`) würde den Parallelstart als Fehler melden. Zusätzlich erzeugt jede `git mv`-Welle R+A-Diffs auf denselben Stammpfaden. **Diese Abweichung ist vorbestehend und NICHT von Rev. 0.4 erzeugt.** **Status: OFFEN** — vom Nutzer am 2026-09-26 bewusst als *offene, dokumentierte* Abweichung registriert und **hier nicht inhaltlich aufgelöst**. Owner: `orchestrator` → `main_chat`. Volltext, Auflösungsweg und Review-Pflicht: **§17.8** |

**Zählung:** **14** Abweichungen — A1…A12 (rev. 0.1/0.2, unverändert) + **A13** (rev. 0.4,
geschlossen) + **A14** (rev. 0.4, **offen**).

**Übernommen ohne Änderung:** T-1…T-6, die SSoT-Zielstruktur (§1/§1.1 des Designs → §3 hier),
C1–C8 (→ M1–M4 hier), V1–V9 (→ IC-05 hier, mit den Korrekturen A2/A3), W0–W8 (§9.2),
B1–B6 (→ AC-32, IC-17, IC-22, NFA-04, R2/R7/R8), §5.1–§5.4 der Knowledge-Policy (→ IC-19…IC-21).

---

## 14. Out of scope / Folge-Issues

| # | Folge-Issue | Begründung / Owner |
|---|---|---|
| FI-1 | **REQ-IDs für die Traceability-Lücken** (Knowledge Engine, `spec-plan-workflow`, auto-commit, quality-pipelines, hooks, Codex/ZCode/KimiCode) | `docs/REQUIREMENTS.md` kennt heute nur `REQ-CMD-*`, `REQ-GEN-*`, `REQ-PROV-*`, `REQ-SYNC-*`, `REQ-SE-*` (`:9-60`); die genannten Bereiche haben **keine** REQ. Zuweisung ist Aufgabe von `requirements`, **nicht** dieser Spec (kein REQ-ID-Auftrag) |
| FI-2 | `docs/CODEBASE_OVERVIEW.md:33-44` — toter Verweis auf `agents/1-generic/se-orchestrator.md` | **NG-3**: Datei gehört `documenter` (`knowledge/wiki/log.md:30`). Nicht in dieser Initiative editierbar. Owner `documenter` |
| FI-3 | `docs/providers/` deckt 6 von 9 Providern ab (fehlen u. a. eigene Seiten für Claude, Continue, Copilot, Mammouth) | Inhaltliche Doku-Arbeit (NG-1), keine Struktur-Arbeit. Owner `documenter` |
| FI-4 | Inhaltliche Konsolidierung von `knowledge/wiki/topics/` ↔ `docs/guides/` | **OQ1**, Produktentscheidung |
| FI-5 | `AGENTS.md`-Bootstrap-Block (66 hartgelistete Agenten) generieren | **OQ3**, eigener Blast Radius (B6) |
| FI-6 | provider-Referenzseiten für die 3 fehlenden Provider + `README.md:690`-Text auf generierten Block umstellen | Teil von W3/W8, aber **inhaltlich** nach FI-3 |
| FI-7 | `knowledge/sources/docs/guides/` enthält einen alten Guide-Snapshot; die SSoT-Umstellung macht ihn zur reinen Historie | Kein Eingriff (NG-2, append-only). Nur als Doku-Hinweis in `docs/architecture/00-overview-full.md` |
| FI-8 | Rollen-Paritäts-Fix (Config-Edit in `roles:` bzw. SE-Gate) | **NG-8**, eigene REQ |
| FI-9 | `docs/specs/`-Namensschema vereinheitlichen (`SPEC-*`-Naming vs. `REQUIREMENTS.md`) | **OQ4** / **NG-6**, Entscheidung `requirements` + `validator` |
| FI-10 | Abbau der 179 `*.sync-backup-*`-Leichen in `.claude/agents/` | **V9** (W8) meldet nur; das Aufräumen ist eine lokale Aufräumaktion, kein Spec-Gegenstand |

---

## 15. Trace-Anker

```
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
→ Eingang für concept-specifier (Stage "specify" in quality_pipelines.concept-driven-dev)
→ Approval-Gate: Status Entwurf → APPROVED nur durch concept-reviewer nach User-Freigabe
   (Gate durchlaufen: Freigabe 2026-09-26, siehe §Freigabevermerk oben)
→ Plan referenziert: SPEC-DOCS-CONSOLIDATION-2026-09-25
→ Verwandt (unverändert übernommen, keine Supersession):
    docs/REQUIREMENTS.md                        (REQ-*-Master-IDs, Formatregel :4)
    docs/plans/README.md                        (docs/plans/-Konvention, archive/)
    scripts/lib/spec_plan_scaffold.py:23        (docs/INDEX.md-Vertrag)
    docs/specs/2026-09-25-repository-documentation-consolidation-design.md
                                              (verbindliche Design-Grundlage)
    Concept-Review + Re-Review vom 2026-09-26 (Session-Artefakte, nicht committet;
                                              Ausgang in §17.1 und §17.5 protokolliert)
→ Bei Aufteilung (OQ7 geschlossen, §11.2 — Planungsentscheidung des Planners):
    SPEC-DOCS-FACTS-2026-09-25        (M1, W1+W2)
    SPEC-DOCS-INDEX-2026-09-25       (M2, W3+W4)
    SPEC-DOCS-MIGRATION-2026-09-25   (M3, W5+W6+W8)
    SPEC-KNOWLEDGE-INDEX-GEN-2026-09-25 (M4, W7)
→ Rev. 0.4 (2026-09-26) — Ausführungskorrektur der Branch-/PR-Strategie (OP-1), §17.6:
     Ausführung belegt in docs/plans/2026-09-25-repository-documentation-consolidation.md
       (Rev. 0.4, Global Constraints, Task W0-2)
    und docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md §7.1/§7.2
    Geändert: §9.2 (W0-Zeile, Absatz "PR-/Branch-Strategie"), R16-Mitigation, §15/§16/§17.6.
     Unverändert: alle ID-Mengen, §9.1, status APPROVED.
     §13: 14 Abweichungen — A1…A12 unverändert, A13 (Branch-Name) und A14 (W4/W5/W6 seriell,
       offen) in Rev. 0.4 ergänzt.
     Rev. 0.4 am 2026-09-26 durch den Nutzer bestätigt (§17.7); A14 bleibt offen (§17.8).
     Kein neuer spec-id, keine Supersession.
```

**Vollständigkeits-Checkliste (Coverage, keine Selbstbewertung):**

| Pflichtelement | Ort | Status |
|---|---|---|
| Problem / messbare Baseline mit `Datei:Zeile` | §1.1 (F1…F25, davon F19 gestrichen), §1.2 | vorhanden |
| Scope-Grenzen explizit (inkl. `sources/`- und Ownership-Hard-Constraint) | §2.2 NG-1…NG-11, §2.3 | vorhanden |
| Zielstruktur / SSoT-Matrix mit Generationsmodus | §3.1, §3.2, §3.3 | vorhanden |
| DocFacts-Berechnung | IC-01, IC-02, IC-03, IC-04 | vorhanden |
| **Unabhängige Sollwert-Quelle gegen den Kreis `doc_facts → Renderer → V6`** | IC-23, AC-36, R14, NFA-11 | vorhanden |
| Platzhalter-Namespace `DOCS_*` + `DOCS_*_BLOCK` | IC-02, IC-06, IC-11 | vorhanden |
| Synchronisation in die Default-Stage (Muster `sync_knowledge_engine`) | IC-12 (Stage nach `sync_pipeline.py:935`) | vorhanden |
| **Besitzregel für `docs/INDEX.md` (Doppel-Writer)** | IC-13, IC-15, AC-38 | vorhanden |
| `dry_run` / `write_checked` | IC-13, AC-23 | vorhanden |
| Idempotenz-Muster | IC-13, IC-17, NFA-01 | vorhanden |
| Fact-Hash-Footer ohne Zeitstempel, Diff-Stabilität, volatile-Ausnahme | IC-14, NFA-02, AC-03, AC-18 | vorhanden |
| Fallback bei nicht berechenbarem Faktum | IC-01 Fehlerpfade, IC-13, AC-04 | vorhanden |
| **Restore-Pfad für den Policy-Bruch in W7** | IC-24, AC-41 | vorhanden |
| Acceptance Criteria mit V1…V9-Verknüpfung, beobachtbar | §7 (AC-01…AC-41), §9.1 | vorhanden |
| Nicht-funktionale Anforderungen | §8 (NFA-01…NFA-11) | vorhanden |
| Trace-Matrix AC → Wellen → Dateien | §9.1, §9.2 | vorhanden |
| **Threat Model (4 Fragen)** | §12.3 | vorhanden |
| Brücke zu offenen Entscheidungen **und** geschlossenen Punkten | §11.1 (OQ1, OQ3, OQ4, OQ9 — **offen**) / §11.2 (OQ2, OQ5, OQ6, OQ7, OQ8 — **geschlossen**; OQ2/OQ6/OQ8 per Nutzer-Entscheidung vom **2026-09-26**) | vorhanden |
| Risiken R1…R20 mit Mitigation und Owner | §12.1, §12.2 | vorhanden |
| Out of scope / Folge-Issues | §2.2, §14 | vorhanden |
| **Review-Auflösung mit korrigierten Reviewer-Angaben** | §17 | vorhanden |
| Kein `TBD`, kein unbenanntes Placeholder | gesamtes Dokument | geprüft (§16) |
| Jedes AC ≥ 1 Interface Contract | §9.1 Spalte „Betroffene Dateien" + IC-Verweise in §7 | geprüft (§16) |
| Jedes AC ≥ 1 V-Check oder explizit als „—" begründet | §9.1 Spalte „V-Check" + Begründungsabsatz | geprüft (§16) |

---

## 16. Selbstreview (concept-specifier, Rev. 0.3, 2026-09-26)

| Prüfung | Ergebnis |
|---|---|
| **No-Placeholder** | Kein `TBD`, kein `???`, kein `FIXME`, kein leeres Feld. Offene Entscheidungen sind ausschließlich **OQ1, OQ2, OQ3, OQ4, OQ6, OQ8, OQ9** (§11.1) mit Owner, Empfehlung, Entscheidungsweg und Wellen-Blockade; **OQ5** und **OQ7** sind in §11.2 ausdrücklich als **geschlossen** mit Begründung geführt. Jede Interface-Signatur ist vollständig typisiert; jede AC nennt Datei **oder** Befehl **und** Exit-Code/Assertion. |
| **Spec vs. Design** | T-1…T-6, C1–C8, V1–V9, W0–W8, B1–B6, §5.1–§5.4, §1/§1.1 übernommen oder **explizit** begründet abweichend. **14** Abweichungen in §13: 3 Faktualkorrekturen (A1, A5, A6), 3 Gate-Korrekturen (A2, A3, A4), 3 Ergänzungen (A7, A10, A11), 1 Sicherheits-Korrektur (A8), 1 Formatentscheidung (A9), 1 Zirkel-Auflösung (A12), 1 Branch-Namens-Korrektur (A13, rev. 0.4), 1 **offene** Parallelitäts-Abweichung (A14, rev. 0.4, §17.8). Keine stille Abweichung. **Neu gegenüber Rev. 0.1:** A7 enthält die Korrektur der eigenen Fehlkorrektur F19, A10 die Fail-off-Auflösung, A12 die Stale-Quellen-Wanderung. **Neu in Rev. 0.4:** A13 (Design nennt `chore/docs-consolidation`, verbindlich ist `feat/repository-documentation-consolidation-main`) und A14 (W4/W5/W6 seriell statt paarweise parallel — **nicht** aufgelöst, bewusst offen). |
| **IDs** | `spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25` im Frontmatter **und** im Trace-Anker (§15), Format `SPEC-<NAME>-<JJJJ-MM-TT>` konsistent mit `docs/REQUIREMENTS.md:4`-Nachbarn und `docs/specs/2026-09-15-reference-standards-design.md:2`. Kein `REQ-*` vergeben (FI-1, Zuständigkeit `requirements`). **AC-01…AC-41 lückenlos und je genau einmal definiert; §9.1 führt alle 41; §9.2 verteilt sie auf W1–W8, jede Welle mit ≥ 1 AC. IC-01…IC-24 lückenlos. NFA-01…NFA-11 lückenlos. R1…R20 lückenlos. F1…F25 lückenlos, F19 ausdrücklich gestrichen (kein Recycling). V1…V9 lückenlos. W0…W8 lückenlos. OQ1…OQ9, davon OQ5/OQ7 geschlossen. M-1…M-13 lückenlos.** |
| **Querverweise** | Jeder `Datei:Zeile`-Verweis wurde am 2026-09-26 gelesen. **Neu bzw. korrigiert in Rev. 0.2:** `config/tier-presets.yaml:1, :31, :85, :115, :145` (5 Tiers); `config/dod-presets.yaml:12, :13, :30, :46, :62, :79, :96, :113` (7 Presets); `config/role-defaults.yaml:2489, :2490, :2547, :2572, :2607, :2633, :2706, :2737, :2755, :2877` (8 Pipelines, 1 disabled); `.meta-config/project.yaml:339-343` (nur `se-cascade`); `README.md:479-489` (7 Zeilen, `concept-driven-dev` fehlt), `:501`, `:688`, `:689`, `:690`, `:695`, `:696`, `:734`; `hooks/**/*.sh` (17 Dateien, 11 deploybar); `commands/1-generic/*.md` (22); `tests/scenarios/asserts/{50,51,52,54,55,56}*.sh` mit **exakten** Zeilen `:32`, `:44`, `:26-27`, `:24-25`, `:31`; `tests/scenarios/run.sh:46-52`; `tests/scenarios/configs/{51,52,54}*.project.yaml`; `tests/scenarios/registry.md:97-110`; `scripts/lib/spec_plan_scaffold.py:20-24, :27-44, :46-68`; `scripts/lib/knowledge.py:103-114, :116-129, :131-132, :153-169`; `scripts/lib/generated_file_drift.py:35-37, :44, :51-67, :82-84, :240-310, :313-351, :344-349, :354-402, :379-386, :388, :405-425, :422-424, :591-596`; `scripts/lib/consistency/placeholders.py:128-131, :135-136, :148-183, :177-182`; `scripts/lib/sync_pipeline.py:587-620, :922-945, :929, :935, :1090-1099, :1102-1117, :1139`; `scripts/lib/cli_commands.py:72, :864, :888-900, :1139`; `scripts/lib/backup.py:376+`; `scripts/lib/deactivation.py:21, :303-353`; `config/project-config.schema.json:2058, :2073, :2425`; `ARCHITECTURE.md:3, :8-20`; `knowledge/wiki/index.md:24`; `knowledge/wiki/log.md:13-17, :30`; `docs/guides/project.yaml.example` (179 Z), `howto/configs/project.yaml.example` (340 Z), `docs/howto/admin-ui-remote-access.md`. **Neu bzw. korrigiert in Rev. 0.3:** `README.md:381-390` (F22 b — Überschrift + 6 Preset-Zeilen, `concept-driven` fehlt; `config/dod-presets.yaml:96`); `ARCHITECTURE.md:3` (F4, zweite Fundstelle) gegen `VERSION:1`; `hooks/1-generic/*.sh` (**11** Dateien, davon 2 `*-impl.sh` ⇒ **9**) gegen `scripts/lib/hooks.py:95-105` und `scripts/lib/external_tools.py:217-220`; `scripts/lib/spec_plan_scaffold.py:49-51` und `:62-68` für die Abschirmungskette in AC-38; `tests/scenarios/configs/51-spec-plan-disabled.project.yaml:1-34` (kein `docs-consolidation`-Key; `spec-plan-workflow.enabled: false` `:11-12`; `knowledge-engine.enabled: false` `:7-8`; `external-system-override.enabled: true` `:20-21`); `tests/scenarios/asserts/{50:32, 51:29-32, 52:41-44, 54:26-27}` direkt gelesen. `hooks/**/*.sh` = **17** Dateien bleibt eine **Belegzahl der Befund-Zeile F3** und ist **kein** `DOCS_*`-Faktum (NEW-1). **Nicht** verifizierbar und daher als HYPOTHESIS markiert: die exakte Zahl der `docs/**/*.md` (~190, §1) und die Zahl der Knowledge-Agenten im `AGENTS.md`-Bootstrap-Block (66, OQ3, aus dem Design übernommen). |
| **Coverage** | Jedes AC in §7 verweist auf mindestens eine IC; die Zuordnung AC → Welle → Datei → V-Check ist in §9.1 für alle **41** AC gefüllt. AC **ohne** V-Check sind in §9.1 je einzeln begründet; die Liste ist in Rev. 0.3 **vollständig** (NEW-6: Rev. 0.2 ließ AC-06, AC-22 und AC-38 weg) und umfasst **18** AC: **AC-01, AC-02, AC-03, AC-04, AC-06** (Fakten-Invarianten bzw. Key-Set, per Unit-Test in `tests/test_doc_facts.py`), **AC-18, AC-19, AC-22, AC-23, AC-24, AC-25, AC-26** (Determinismus, Drift-Store, Scaffold-Vertrag, Config-/Snippet-Bridge, per Unit-Test), **AC-34, AC-35, AC-37, AC-38, AC-39, AC-41** (Wiki-Restore, Allowlist, Szenario-Runner, Schema-Operation, Restore-Pfad). Die Begründungsklassen: Konfigurations-/Fakten-Invarianten; Determinismus-, Drift-Store-, Szenario- und Restore-Ebene — abgesichert per Unit-Test bzw. bestehendem Runner statt per Consistency-Check. |
| **Modularisierung** | Vier Module M1–M4, jeweils mit eigener Verantwortung, Dateiliste, Wellen, Vorgänger und Rollback (§4). Die Entscheidung „eine Datei" ist in §4 begründet; OQ7 ist als **geschlossen** mit Verweis auf die Planungsentscheidung geführt (§11.2). |
| **Review-Auflösung** | Rev. 0.2: Alle 16 Reviewer-Findings behoben (§17.1), drei Reviewer-Angaben als ungenau nachgewiesen und korrigiert (§17.2 CR-1…CR-6), drei weitere bestätigt (§17.3). **Rev. 0.3: Re-Review** (Concept-Reviewer-Re-Review vom 2026-09-26, CHANGES_REQUESTED, 0 kritisch / 2 major / 4 minor / 2 info) — **alle 8 Findings behoben** (§17.5) plus die **Gegenkorrektur** des Re-Reviewers zu §17.2 CR-1/CR-2. Der Re-Reviewer hat seinerseits **sechs** eigene Angaben (CR-1…CR-6) **zurückgezogen** und die Korrekturen aus Rev. 0.2 ausdrücklich **gestützt**; eine dieser Angaben (die Szenario-Zählung) wurde durch seine eigene Rücknahme **präzisiert**, nicht bestätigt (§17.2, CR-1). |
| **Ownership-Grenze** | Diese Spec-Revision hat **ausschließlich** `docs/specs/2026-09-25-repository-documentation-consolidation.md` geschrieben. Kein Code, keine Config, keine `agents/`-/`knowledge/`-/`tests/fixtures/`-Änderung, kein Commit, kein Push. Der parallele Track A (`tests/fixtures/slimming-golden/`) wurde weder gelesen als Spezifikationsquelle noch verändert. |
| **Rev. 0.4 — Abgrenzung** | Rev. 0.4 korrigiert die Branch-/PR-Normativität auf den ausgeführten Stand: §9.2 W0-Zeile, §9.2-Absatz „PR-/Branch-Strategie", R16-Mitigation sowie die Folgeverweise in §15, §16 und §17.6 (Volltext und Belege in §17.6); zusätzlich §9.2-Spalte „Parallel mit" auf den ausgeführten **sequenziellen** W4/W5/W6-Stand umgestellt und **A13**/**A14** in §13 registriert. **Unverändert:** AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20 (**R16 nur im Lösungsansatz**, nicht im Risiko-Inhalt und nicht in der W-Wahrscheinlichkeit „mittel"), F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9, W0…W8, §9.1, die §9.2-Welleninhalte und AC-Mengen, §3–§12 im Übrigen. **Keine** neue ID, **keine** neue Welle, **kein** neues Risiko, **keine** geänderte Architektur. **§13 umfasst 14 Abweichungen** — **A13** registriert die Branch-Namensabweichung (Design-W0 nennt `chore/docs-consolidation`, `docs/specs/2026-09-25-repository-documentation-consolidation-design.md:265`), **A14** die W4/W5/W6-Serialität und ist **offen** (§17.8). `status: APPROVED` besteht unverändert; Rev. 0.4 ist am **2026-09-26 durch den Nutzer bestätigt** (§17.7) — die zuvor im Dokument ausgerichtete Ausnahme ist entfallen. |
| **Ownership-Grenze (Rev. 0.4)** | Die Rev. 0.4 hat **ausschließlich** `docs/specs/2026-09-25-repository-documentation-consolidation.md` geschrieben. Design und die sechs W0-Records wurden **gelesen, nicht geändert**; die sechs W0-Records bleiben unverändert und führen OP-1 weiterhin offen — der formale Abschluss von OP-1 ist ein **Folgeschritt** (§17.6/§17.7). Der **Plan** `docs/plans/2026-09-25-repository-documentation-consolidation.md` wurde im selben Durchgang **nur in Ankern und Faktenangaben** geändert (K12, Revisions-Bump 0.3 → 0.4, berichtigte Zeilenzahlen, berichtigte OP-1-Aussage im Self-Review) — **kein** Task-, Wellen-, AC-, IC-, NFA- oder Gate-Inhalt. Kein Code, keine Config, kein Commit, kein Push, kein Branch-Wechsel, kein Merge/Rebase/Force. |

---

## 17. Review-Auflösung und Ausführungskorrekturen (Rev. 0.2, Rev. 0.3, Rev. 0.4)

### 17.1 Findings des Concept-Review — alle behoben

| Finding | Severity | Behebung in dieser Rev. | Verifikation |
|---|---|---|---|
| **K1** V1-Regex matcht die Befunde nicht | kritisch | §5.1.1: V1 Regel neu spezifiziert als **zwei disjunkte Branches** — V1a (Zahl + Whitelist-Nomen, ≤ 3 Token Abstand, **beide Richtungen**) und V1b (Semver-Literal + `version`). **Positiv-Fixture mit den 4 wörtlichen Zitatzeilen** und Negativ-Fixture mit 3 Suppressionsfällen + 1 Gegenprobe; AC-07/AC-08 ersetzt. Branch-Name ist Teil des Findings. | **bestätigt.** Alle vier Zeilen erneut gelesen: `README.md:122` (`## Agent Roster — 74 Generic Agents`), `:501` (`## Hooks (7 hooks, …)`), `:690` (`  ai-providers.yaml  # 6 provider configs (…`), `:734` (`VERSION  # Current version (v1.0.0)`). Keine davon matcht die alte Regex (Zahl steht nie am Zeilenanfang). |
| **K2** F19 ist eine falsche Korrektur | kritisch | F19 **gestrichen**, `DOCS_TIER_PRESET_COUNT == 5`, `README.md:689` in „korrekt, nicht zu ändern", §13-A7 korrigiert | **bestätigt.** `config/tier-presets.yaml` hat 5 Top-Level-Keys: `Cheap:1`, `Normal:31`, `Advanced:85`, `Expensive:115`, **`Expensive as Hell:145`**. |
| **K3** DoD-Presets sind 7 | kritisch | Neuer Befund **F22**, `DOCS_DOD_PRESET_COUNT == 7`, Absatz „korrekt" korrigiert, R4 neu begründet | **bestätigt.** `config/dod-presets.yaml:12` `presets:` mit 7 Einträgen: `:13`, `:30`, `:46`, `:62`, `:79`, `:96`, `:113`. |
| **K4** Pipelines: 8 / 7 aktiv, Tabelle unvollständig | kritisch | F14 auf drei Fehler erweitert (Zahl, fehlende Zeile, deaktivierte Zeile), `DOCS_PIPELINES_COUNT == 8`, `DOCS_PIPELINES_ACTIVE_COUNT == 7`, `DOCS_PIPELINES_BLOCK` auf „alle 8" erweitert | **bestätigt.** Alle 8 Pipeline-Keys gelesen; nur `se-cascade` ist `enabled: false` (`:2877`, überschrieben in `project.yaml:339-342`). `README.md:479-489` listet 7 Zeilen ohne `concept-driven-dev`. |
| **K5** Stage bricht bestehende Szenarien | kritisch | **Fail-off-Absenz-Default** (Präzedenz `knowledge.py:127`) für `enabled` **und** für alle V1–V9 (IC-05-Common-Gate); `knowledge-engine`-Schreibverbot; **Besitzregel** in IC-13; `index-mode: skeleton` als echter Hebel; **AC-38** als explizite Regressionsgarantie; NG-10 | **bestätigt, aber in der Zahl korrigiert** — siehe §17.2, CR-1. |
| **M1** Hook-Zählung widersprüchlich | mittel | IC-01-Auflösung: **zwei** Keys mit **getrennt benannten** Regeln **und je genau einer Zielstelle**. **Rev. 0.2-Stand:** `DOCS_HOOKS_COUNT == 11` (ohne `lib`, ohne `release-gates`, ohne `*_impl.sh`) für `README.md:501`, `DOCS_HOOK_SCRIPT_FILES_COUNT == 17` (keine Ausschlussregel) für `README.md:696`. **Rev. 0.3 (NEW-1):** der 17er-Key ist **gestrichen**, weil seine Zahl `hooks/**` zählt und damit an einer Zeile stand, die `hooks/1-generic/` nennt; neu `DOCS_HOOKS_1GENERIC_COUNT == 9` für `README.md:696`. Kreuz-Rendering ist verboten. | **bestätigt, in Rev. 0.3 korrigiert.** 17 `.sh` unter `hooks/**` = 2 `0-external/` + 11 top-level `1-generic/` + 1 `lib/hook_common.sh` + 3 `release-gates/` (Glob). Für `README.md:501` (global, „propagated to all providers"): 17 − 1 − 3 − 2 = **11**. Für `README.md:696` (Verzeichnis-Zeile): 11 top-level `1-generic/` − 2 `*-impl.sh` = **9**. Sammel-Nachweis der Layer-Regel: `hooks.py:95-98` (`0-external`), `:101-104` (`1-generic`), jeweils **nicht-rekursives** `*.sh`-Glob; `external_tools.py:217-220`. |
| **M2** Trace-Matrix inkonsistent | mittel | §9.1: AC-19 → **—** (Drift-Store, begründet), AC-18 → **—** (begründet), AC-29 → **V3**; AC-31 fest auf **W5**; Begründungsabsatz „V-Check-Spalte, korrigiert" ergänzt | **bestätigt** (sachfremde Mappings). |
| **M3** W8-Aktivitäten ohne AC | mittel | **AC-40** (neu) deckt die `llms.txt`-/`README.md`-Providerzahl ab; die **ID-Deklaration (OQ4)** ist über OQ4 mit Owner und Wellen-Blockade in §11.1 verankert und in §9.2 W8 als Inhalt geführt; **AC-30** deckt die README-Totverweise, **AC-39** (neu) die Schema-Operation aus R15, **M-12** die `PROJECT_STRUCTURE`-Korrektur. Jede W8-Aktivität in §9.2 hat damit mindestens ein AC **oder** eine verankerte OQ mit Blockade. | **bestätigt.** Rev. 0.1 führte AC-31 doppelt (W5 und W8) und nannte für W8 zwei Aktivitäten ohne AC. |
| **M4** Guide-Inventar unvollständig | mittel | F6 = **vier** Orte; neue Befunde **F23** (Guide-Sonderpfad) und **F24** (zwei Beispiel-Configs); Migrationen **M-6** (`docs/howto/` → `docs/guides/`) und **M-5** bleibt; SSoT-Entscheidung für beide Beispiel-Configs als **OQ9** (Inhaltsfrage, NG-1) mit Owner | **bestätigt.** `docs/howto/admin-ui-remote-access.md` existiert (Glob, 1 Datei); `docs/guides/project.yaml.example` = **179** Zeilen, `howto/configs/project.yaml.example` = **340** Zeilen (Endzeilen gelesen). |
| **M5** AC-29 zirkulär | mittel | §13-**A12** neu: die Stale-Deklaration **wandert mit** der Langfassung (M-7), IC-03 liest `docs/architecture/00-overview-full.md`, AC-29 prüft beide Seiten getrennt | **bestätigt — und in der Diagnose geschärft.** Die Deklaration in `ARCHITECTURE.md:3` betrifft nicht die Stub-Aussage selbst; `knowledge/wiki/index.md:24` beschreibt `concepts/architecture.md` als „Rohkopie von **ARCHITECTURE.full.md**". |
| **M6** AC-35 übererfüllt | mittel | **IC-24** `restore_wiki_index()` mit Pfad, Reihenfolge und fail-closed; **AC-41** neu; AC-35 auf „Backup existiert" zurückgenommen; NFA-06 aktualisiert | **bestätigt.** `sync.py --backup`/`--restore` (`cli_commands.py:864`, `:888-900`) sind über `backup.py:376+` Provider-Verzeichnis-Zip-Operationen (`deactivation.py:21`, `:303-353`) und können `knowledge/wiki/index.md` nicht wiederherstellen. |
| **M7** R1 nur für Hybrid-Dateien | mittel | R1 erweitert; §3.2 volatile-Zeile auf `docs/INDEX.md` konkretisiert; IC-10 (e) volatile-Sektion am Dateiende; IC-14 schließt volatile aus dem `facts-hash` aus; AC-03 erweitert | **bestätigt.** |
| **M8** `#`-Key als HYPOTHESIS | mittel | **Analysiert statt vermutet:** IC-16-M8-Tabelle listet alle fünf Consumer des Hash-Stores mit Code-Belegen. Verbindliche Regel: Allowlist-Match auf den **Basis-Pfad**; NFA-05 wird zwingend, weil kein Backup entsteht. AC-37 prüft es. | **bestätigt und präzisiert.** `is_allowlisted` = `any(fnmatch.fnmatch(rel_path, p) …)`, `generated_file_drift.py:82-84` — ein Muster `README.md` matcht `README.md#docs:facts` **nicht**. `backup_drifted_files` liest `project_root / finding["path"]` (`:379`) und überspringt fail-soft (`:381-386`). |
| **N1** Selbstwidersprüche | niedrig | Revisionstabelle nennt **AC-01…AC-41**; §15/§16 nennen **OQ1…OQ9** mit OQ5/OQ7 geschlossen. **Rev. 0.3:** die damalige Teilbehauptung „AC-02 sagt „zwölf" und listet zwölf" ist **überholt** — AC-02 ist jetzt rein formelbasiert und enthält **keine** Zahlenliste (NEW-8); die Sollwert-Zahl steht ausschließlich in IC-23 und lautet **elf** (NEW-4) | **bestätigt, in Rev. 0.3 überholt.** |
| **N2** `knowledge-indexer`-Kollision | niedrig | IC-21 trägt jetzt einen eigenen **Kollisionsvermerk** mit verbindlicher Reihenfolge (W7 erst nach Rollenpflege-Merge, IC-21 als letzter Commit); NFA-08 nennt es als **einzige** Ausnahme; **R19** | **bestätigt** (Lag nur im NFA-08-Klammersatz). |
| **N3** OQ5 / OQ7 faktisch entschieden | niedrig | **§11.2** führt beide als **geschlossen** mit Begründung; OQ7 zusätzlich in §4 und §15 | **bestätigt.** |

### 17.2 Korrigierte Reviewer-Angaben (mit Beleg)

> **Rev. 0.3 — Gegenkorrektur des Re-Reviewers zu CR-1/CR-2 (verbindlich).** Der Re-Reviewer
> hat CR-1…CR-6 **zurückgezogen** und die Korrekturen aus Rev. 0.2 **gestützt** — mit **einer**
> Präzisierung: die Formulierung „**3 harte Fehlschläge**" beschreibt die **naive** Variante
> (Generator ohne Abschirmung), **nicht** die spezifizierte. Verbindlich gilt:
> **0 Szenarien brechen unter der in dieser Spec festgelegten Abschirmung** (Fail-off-
> Absenz-Default `docs-consolidation.enabled = false`, IC-13 Zeile 1 / IC-22; KE-Schreibverbot,
> IC-13 Zeile 2; **kein** `mkdir` in Consumer ohne `docs/`, IC-13 letzte Zeile) — so behauptet
> AC-38 zu Recht. **3** ist die Anzahl der Szenarien, die in der **naiven** Variante
> brechen würden, und steht hier **ausschließlich als Begründung der Abschirmung** — es ist
> **kein Arbeitsauftrag**: NG-10 verbietet jede Änderung an `tests/scenarios/`, also darf der
> Planer insbesondere **keine** der drei Zeilen „reparieren".

| # | Reviewer-Angabe | Korrektur | Beleg |
|---|---|---|---|
| **CR-1** | „**6** bestehende Szenarien brechen", darunter `asserts/50:32` und `asserts/56:31` | **0 brechen** unter der spezifizierten Abschirmung; **3** in der naiven Variante. `asserts/50:32` und `asserts/56:31` prüfen nur `[ -f "docs/INDEX.md" ]` — **Existenz**, und die Datei existiert nach dem Scaffold weiter, also bleiben sie **grün**. Ebenso `asserts/54:26` und `asserts/55:24` (Existenz). `asserts/51:32` (`[ ! -e "docs/INDEX.md" ]`) bleibt grün, weil die Fixture **keinen** `docs-consolidation`-Key trägt ⇒ Absenz-Default `enabled = false` ⇒ der Generator führt **keinen** Schreibzugriff aus (IC-13 Zeile 1 / IC-22). `spec-plan-workflow.enabled: false` ist dafür **nicht** die Begründung, sondern betrifft nur den Scaffold (anderer Writer). | `asserts/50:32` `[ -f "docs/INDEX.md" ]`; `asserts/56:31` `[ -f "docs/INDEX.md" ]`; `asserts/51:29-32` prüft `docs/specs|plans|spikes` **nicht** existent, dann `:32 [ ! -e "docs/INDEX.md" ]`; `configs/51-spec-plan-disabled.project.yaml:1-34` (kein `docs-consolidation`-Key), `:11-12` `spec-plan-workflow.enabled: false`, `:7-8` `knowledge-engine.enabled: false`, `:20-21` `external-system-override.enabled: true`; `spec_plan_scaffold.py:49-51` → `log.skip` vor jedem `mkdir` |
| **CR-2** | **Harte** Fehlschläge: `54:27`, `55:25`, `51:32`, `52:44` | In der **naiven** Variante wären es `54:27` (grep `File-based index fallback`), `55:25` (grep dito) und `52:44` (`[ ! -e docs/INDEX.md ]` — KE autoritativ). `51:32` bricht auch naiv **nicht** (s. CR-1). Unter Abschirmung: **0**. Der Spec-Text des Reviews nennt für 56 „Inhaltsprüfung (`:31`)" — `:31` ist jedoch `[ -f ]`, eine reine Existenzprüfung. | `asserts/54:26-27` (`[ -f ]` + `grep -q 'File-based index fallback'`); `asserts/55:24-25` dito; `asserts/52:41-44` Kommentar „no file-index fallback is written" + `[ ! -e "docs/INDEX.md" ]`; `asserts/56:31` `[ -f "docs/INDEX.md" ]` |
| **CR-3** | R18: „Interaktion `_sync_stage_auto_commit_allowlist` mit `auto-commit-allowlist.json` nicht analysiert" | **Nicht zutreffend.** Die Stage liest den Drift-Store nicht; sie schreibt eine **generierte** Ausgabe aus `config` + `active_roles`. Außerdem existiert `.meta-config/auto-commit-allowlist.json` im Repo **nicht** (Glob: 0 Treffer) — es ist ein Sync-Output, kein Input. Risiko als **analysiert und nicht zutreffend** geführt, mit Beleg in IC-16 und R18. | `sync_pipeline.py:1102-1117` (`resolve_auto_commit_config(config, active_roles, agent_meta_root)`, `write_atomic(allowlist_path, …)`); `.meta-config/` hat keine `auto-commit-allowlist.json`; `auto_commit.py:49` beschreibt es als **geschrieben** |
| **CR-4** | R15 impliziert: ohne Schema-Update „geht gar nichts" | **Falsch.** Das Wurzel-Schema ist `additionalProperties: true` (`:2425`) — die 6 Keys brechen die Validierung nicht. Was fehlt, ist Autocomplete und der Tippfehler-Wächter, den das Repo selbst ausdrücklich nutzt. M-11 ist **Konventions-Pflicht**, keine Fehlerbehebung. | `config/project-config.schema.json:2425` `"additionalProperties": true`; Selbstauskunft in `:2058` („Required because spec-plan-workflow is a closed object; additionalProperties:false additionally turns it into a strict typo guard") und `:2073` |
| **CR-5** | M8: Allowlist-/Auto-Commit-Pfad „nicht geprüft" → Key-Design ändern | Nach Prüfung: **kein** Key-Design-Wechsel nötig. `_load_hashes`/`_save_hashes` sind key-agnostisch (`:51-67`); das einzige echte Problem ist der `fnmatch`-Match auf den Gesamtstring (`:82-84`), gelöst durch die Basis-Pfad-Regel. | wie oben |
| **CR-6** | Design/Rev. 0.1: Szenario `63-docs-facts-drift.md` | Nummer **63 ist vergeben** an `63-context-file-modes`. Korrekt: **64**. | `tests/scenarios/registry.md:110`; `asserts/63-context-file-modes.sh`; `configs/63-context-file-modes.project.yaml` |

### 17.3 Geprüfte und **bestätigte** Reviewer-Angaben (DEVIATION_REVIEW A1–A11)

> **Geltungsbereich:** Diese Prüftabelle deckt den **Rev.-0.2-Stand** ab und umfasst die
> §13-Abweichungen **A1…A12**. Die in **Rev. 0.4** hinzugekommenen **A13** und **A14** sind hier
> **nicht** Gegenstand — zu A13 siehe §13/A13 und §17.6, zu A14 siehe §13/A14 und **§17.8**.

| # | Urteil nach eigener Prüfung | Beleg |
|---|---|---|
| **A1** | **trägt** — Design-F Aussage war falsch, die Korrektur ist berechtigt | `project.yaml:148` `se-component-requirements` in `roles:`; `:12-13` `systems-engineering.enabled: false`; `agents/1-generic/se-component-requirements.md` existiert; `agent_sync.py:544-548` `log.skip(rel, "systems-engineering is disabled")` |
| **A2** | **trägt** | `roles:` 59 Einträge (`:92-150`); `role-defaults.yaml:1` 84 Rollen (2-Space-Keys bis `:2403`); Gate-bewusste Vergleichsmenge ist korrekt |
| **A3** | **trägt** | `placeholders.py:128-131` `_DYNAMIC_PREFIXES` (2 Einträge, **kein** `DOCS_`); `:177-182` `Severity.WARNING` |
| **A4** | **trägt inhaltlich, war unvollständig** | `spec_plan_scaffold.py:62-68` schreibt nur bei `mode == "file-index"`; die Regel für `mode == "knowledge-engine"` fehlte → in IC-13 (Zeile „`resolve_index_mode() == knowledge-engine`") und IC-15 ergänzt |
| **A5** | **trägt** | `tests/scenarios/asserts/*.sh` = **63** (gezählt); `tests/scenarios/*.md` enthält nur `registry.md` |
| **A6** | **trägt (Zahlen), Regel war widersprüchlich — Präzisierung in Rev. 0.3 (NEW-1)** | 17 `.sh` unter `hooks/**`, 13 nach `lib/`+`release-gates/`-Ausschluss; IC-01 führte zusätzlich die Suffix-Regel (rev. 0.3: korrekt `-impl.sh`, s. NF-12) → M1 aufgelöst. **Neu:** die 17 sind eine **Belegzahl der F3-Zeile**, kein Faktum; für `README.md:696` gilt der Verzeichnis-Wert **9** (`hooks/1-generic/*.sh` minus 2 `*-impl.sh`) |
| **A7** | **trägt nicht** (F19 falsch) | siehe K2; §13-A7 in Rev. 0.2 korrigiert |
| **A8** | **Begründung trägt, Annahme war ungeprüft** | `generated_file_drift.py:51-67, :82-84, :344-349, :354-402, :405-425` vollständig gelesen; Ergebnis in IC-16 (M8-Tabelle) spezifiziert |
| **A9** | **trägt** | Repo-Konvention `spec-id` pro Datei; Aufteilung als Planungsentscheidung korrekt eskaliert (jetzt OQ7 geschlossen) |
| **A10** | **trägt inhaltlich, Default-Formulierung war der K5-Fehler** | Präzedenz `knowledge.py:127-129` existiert, aber genau deren Fail-**off**-Muster widerspricht „Schema-Default = Default agent-meta" → in IC-22 aufgelöst |
| **A11** | **trägt** | konsistent mit IC-05 (Start WARNING in W2, ERROR ab W3) |

### 17.4 Eigene neue Befunde bei der Überarbeitung (über den Review hinaus)

| # | Befund | Behandlung |
|---|---|---|
| **NF-1** | Das Design (und Rev. 0.1) reserviert Szenario-Nummer **63** für `63-docs-facts-drift` — die ist im Repo bereits belegt | Umbenannt auf **64** (§2.3, §10) |
| **NF-2** | Die Rev.-0.1-Aussage „`README.md:479-489` Pipeline-Tabelle … die *Zahl* 7 stimmt" ist **falsch**; zugleich war die Zahl 7 in `§1.2` als „korrkt" geführt | Korrigiert in F14 und §1.2 |
| **NF-3** | Die Rev.-0.1-Liste „Korrekt und daher nicht zu ändern" enthielt **drei** Einträge, von denen **zwei falsch** waren (`README.md:688` DoD, `README.md:479-489` Pipelines) | Liste auf zwei verifiziert korrekte Zeilen reduziert, beide mit Beleg |
| **NF-4** | ~~Das Design zitiert `README.md:381` als Beleg für die korrekte DoD-Zahl; die Zeile existiert dort nicht (korrekt ist `:688`)~~ — **WIDERLEGT in Rev. 0.3 (NEW-2).** `README.md:381` **existiert**: „## DoD Presets (6 presets)" mit einer 6-zeiligen Tabelle (`:383-390`), der `concept-driven` fehlt. Die Rev.-0.2-Aussage war selbst ein Fehlbefund. | **Als widerlegt markiert und korrigiert:** `README.md:381` ist die **zweite** F22-Fundstelle (Zahl **und** fehlende Zeile) und wird in F22, §3.2 (SSoT-Zielstelle) und §1 mitgezählt. `README.md:688` bleibt die Fundstelle für den Datei-Kommentar. Beleg: `README.md:381-390`; `config/dod-presets.yaml:96` (`concept-driven`) |
| **NF-5** | `DOCS_SCENARIO_COUNT` (63) war in AC-02 gelistet, gehört aber zu den volatilen Fakten und war in der Rev.-0.1-AC-02-Liste die einzige Zahl **ohne** zugehörigen Wert im selben Satz (Aufzählung endete bei `DOCS_SCENARIO_COUNT == 63` ohne Erklärung) | AC-02 auf die **nicht-volatilen** Skalar-Fakten umgestellt; `DOCS_SCENARIO_COUNT` in AC-03 verschoben, wo die Volatilität geprüft wird. **Rev. 0.3:** der in Rev. 0.2 daraus folgende Zahlen-Snapshot (zwölf konkrete Werte als `xfail`) ist **gestrichen** (NEW-8) — AC-02 ist rein **formelbasiert** und damit durchsetzbar; die konkreten Sollzahlen stehen ausschließlich in IC-23 und werden von AC-36 geprüft |
| **NF-6** | Rev. 0.1 zählte in §1.1 „manuell gepflegte Zahlen: 9" und in §1.2 „5 Architektur / 3 Guides" — beides nach Korrektur falsch | §1.2 auf **4** Guides korrigiert; die **Zahlen**-Angabe in Rev. 0.2 war selbst falsch und ist in Rev. 0.3 durch **NF-9** ersetzt |
| **NF-7** | `docs/architecture/` enthält **8** Dateien (`:01-07` + `prompt-modernization.md`), `docs/api/` **7** — beides in §3.2 als Fakt behauptet, aber nirgends belegt | als F5-Beleg belassen (Zeilenangabe `ARCHITECTURE.md:8-20` verweist auf alle), in §16 unter „nicht verifizierbar" nicht aufgeführt, weil über die Diagramm-Tabelle gedeckt |
| **NF-8** | Der parallele Track A committet in `tests/fixtures/`; die von AC-07/AC-08 geforderte Fixture liegt im **selben** Verzeichnis | Als Ownership-Konflikt in §2.3, R3 und R15 geführt; Reihenfolge festgelegt (Fixture erst nach Track-A-Merge) |
| **NF-9** | **Rev. 0.3 (neu):** die Rev.-0.2-Angabe „**10** Stück (F1, F2, F3 ×2, F4, F14 ×3, F22) plus 2 in `llms.txt`" war **doppelt falsch**: die Aufzählung summiert **9** (1+1+2+1+3+1), und `llms.txt` enthält **keine** manuell gepflegte Zahl — `:5` ist Prosa („Claude Code, Gemini/Antigravity, Opencode, Continue, GitHub Copilot, Mammouth Code", 6 von 9 Providernamen). Zusätzlich war `ARCHITECTURE.md:3` als falsche Version **nicht** mitgezählt, obwohl die Zeile der Messzeile in §1/§1.2 (`README.md` / `llms.txt` / `ARCHITECTURE.md`) untersteht | Nachgerechnet und **jede Stelle am Repo belegt**: **11** = 10 in `README.md` (F1 `:122`; F2 `:690`; F3 ×2 `:501`/`:696`; F4 `:734`; F14 ×3; F22 ×2 `:688`/`:381`) + 1 in `ARCHITECTURE.md:3` (F4, zweite Fundstelle, `0.92.0` vs. `VERSION:1` = `1.2.0-beta.2`). `llms.txt:5` als **inhaltliche** Lücke (F2-Analogon, fehlende Providernamen) über **AC-40** adressiert, aber nicht als Zahl gezählt. Korrigiert in §1, §1.1 (F4), §1.2 |
| **NF-10** | **Rev. 0.3 (neu):** die Sollwert-Zahl war uneinheitlich — §1.2 sagte „11", IC-23-Text, AC-36, NFA-11 und R14 sagten „zwölf"/„12", und die Yaml-Datei in IC-23 enthält **11** Einträge | Einheitlich **elf** an allen fünf Stellen; die Yaml-Datei in IC-23 ist der **einzige** Ort mit Sollzahlen. Grund: zwei Orte für dieselbe Zahl sind genau die Fehlerklasse F19/F22 (R14) |
| **NF-11** | **Rev. 0.3 (neu):** die Rev.-0.2-Aussage in NF-4, `README.md:381` existiere nicht, war ein **Fehlbefund** der Spec selbst (siehe oben) | Als **widerlegt** markiert; `README.md:381-390` ist die zweite F22-Fundstelle und wird in F22, §3.2, §1/§1.2 mitgezählt. Lehrpunkt für die Planung: eine Aussage über eine **Nicht-Existenz** braucht denselben Beleg wie eine Existenz-Aussage — hier hätte ein `Read` von `README.md:381` genügt |
| **NF-12** | **Rev. 0.3 (neu, außerhalb der 8 Findings, aber im selben Codepfad wie NEW-1):** IC-01 spezifizierte `HOOK_EXCLUDED_SUFFIXES: tuple[str, ...] = ("_impl.sh",)` — mit **Unterstrich**. Die Dateien heißen `orchestrator-guard-impl.sh` und `repo-containment-impl.sh` (**Bindestrich**, per Glob verifiziert). Die Regel hätte damit **nichts** gematcht und `DOCS_HOOKS_COUNT` liefe auf **13** statt 11 — die eigene Zahl der Spec wäre nicht reproduzierbar, also genau die Fehlerklasse, die V1/IC-23 verhindern sollen | Korrigiert auf `("-impl.sh",)`; die drei Prosa-Stellen (`§3.2`, IC-01-Auflösungstabelle, §17.1-M1) auf `*-impl.sh` vereinheitlicht; Warnkommentar im Code-Block gesetzt |

### 17.5 Re-Review (Rev. 0.3) — Findings NEW-1…NEW-8

Eingang: Re-Review der Rolle `concept-reviewer` vom 2026-09-26 (Session-Artefakt, nicht
committet; der vollständige Findings-Abgleich steht in dieser Tabelle)
(CHANGES_REQUESTED; 0 kritisch / 2 major / 4 minor / 2 info; `RESIDUAL_BLOCKERS: Keine`;
`PLAN_READINESS: Ja`). Der Re-Reviewer bestätigt ausdrücklich die 16 Vorreview-Findings sowie
R14–R18, das Threat Model, OQ8 und die OQ6-Reihenfolge als behoben und zieht seine **eigenen**
sechs Angaben CR-1…CR-6 **zurück**.

| Finding | Sev | Behebung in Rev. 0.3 | Verifikation (jede Stelle am Repo gelesen) |
|---|---|---|---|
| **NEW-1** `DOCS_HOOK_SCRIPT_FILES_COUNT == 17` an `README.md:696` | major | Faktor **gestrichen**; neu `DOCS_HOOKS_1GENERIC_COUNT == 9`, exklusiv für `README.md:696`, mit verbindlicher Renderform inkl. Klammerzuschlag „(+2 `*-impl.sh` helpers)". `DOCS_HOOKS_COUNT == 11` bleibt exklusiv für `README.md:501`. 17 bleibt **Belegzahl** in F3/§16 | `README.md:696` nennt `hooks/1-generic/`; 11 top-level `.sh` dort (Glob), davon 2 `*-impl.sh` ⇒ **9**. `README.md:501` ist die Hooks-**Überschrift** (globale Aussage) ⇒ 17 − 1 `lib/` − 3 `release-gates/` − 2 `*-impl.sh` = **11**. Layer-Regel: `hooks.py:95-98`, `:101-104` (nicht-rekursiv); `external_tools.py:217-220`; `consistency/repo_containment.py:22` („hook wrapper/impl"). **Abweichung vom Reviewer-Vorschlag** (er nannte 11): dokumentiert in §5.1 IC-01 — 11 ist die **Datei**zahl, die Zeile sagt „hook scripts", und die Spec stuft `*-impl.sh` bereits in `DOCS_HOOKS_COUNT` als Nicht-Hooks ein |
| **NEW-2** F22 erfasst nur `README.md:688`; `README.md:381` ist eine zweite Falschzahl; NF-4 widerlegt | major | F22 auf **zwei** Fundstellen erweitert; §3.2-SSoT-Zielstelle auf `README.md:381-390` erweitert; NF-4 als **widerlegt** markiert; Zählung in §1/§1.2 um +1 | `README.md:381` „## DoD Presets (6 presets)", Tabelle `:383-390` mit 6 Zeilen (`full`, `standard`, `rapid-prototyping`, `spec-optional`, `spec-driven`, `spec-certified`); `config/dod-presets.yaml` hat **7** (`:13, :30, :46, :62, :79, :96, :113`) — `concept-driven:96` fehlt in der Tabelle, dieselbe Fehlerklasse wie F14 |
| **NEW-3** §1.2 nennt 10, die Aufzählung ergibt 9 | minor | Neu gerechnet: **11** = 10 (`README.md`) + 1 (`ARCHITECTURE.md:3`); `llms.txt` als Prosa ohne Zahl eingestuft. Beleg und Korrektur in §1, §1.2 und **NF-9** | Aufzählung Rev. 0.2: 1+1+2+1+3+1 = 9 ≠ 10. `ARCHITECTURE.md:3` „Repo version: **0.92.0**" vs. `VERSION:1` = `1.2.0-beta.2`; `llms.txt:5` enthält keine Ziffer |
| **NEW-4** §1.2 sagt 11, IC-23/AC-36/NFA-11/R14 sagen zwölf | minor | Einheitlich **elf** an allen fünf Stellen; Schlüsselzahl-Begründung in IC-23 ergänzt (**NF-10**) | `config/doc-facts-expected.yaml` (IC-23-Block) hat genau **11** Einträge, gezählt |
| **NEW-5** §9.2 nennt W1: 9 / W3: 13, §9.1 nennt 10 / 14 | minor | §9.2 auf **W1: 10, W3: 14** korrigiert, **Nachzählung** beider Wellen als Formel in den Text aufgenommen (AC-39 bzw. AC-38 waren nicht mitgezählt) | W1 = AC-01…AC-06 (6) + AC-23…AC-25 (3) + AC-39 (1) = 10; W3 = AC-12 (1) + AC-14…AC-22 (9) + AC-26 (1) + AC-27 (1) + AC-37 (1) + AC-38 (1) = 14; alle übrigen Wellen unverändert (W2 7, W4 2, W5 2, W6 2, W7 4, W8 2) |
| **NEW-6** §16-Liste der AC ohne V-Check unvollständig | minor | Liste **vollständig** auf **18** AC gebracht, nach Begründungsklassen gruppiert | §9.1 V-Check-Spalte durchgezählt: `—` bei AC-01, AC-02, AC-03, AC-04, AC-06, AC-18, AC-19, AC-22, AC-23, AC-24, AC-25, AC-26, AC-34, AC-35, AC-37, AC-38, AC-39, AC-41 = **18**; Rev. 0.2 nannte 15 (AC-06, AC-22, AC-38 fehlten) |
| **NEW-7** AC-38s Begründung für `51:32` nennt den Scaffold-Gate | info | Umgestellt auf den **Absenz-Default** (`docs-consolidation.enabled` bei Abwesenheit `false` ⇒ `log.skip`, **kein** Schreibzugriff) als tragende Begründung; Scaffold-Abschirmung als **nachrangige** Rückfallebene markiert. Zusatz: die AC referenziert **IC-13/IC-15/IC-22** — ein von der Reviewer-Notiz genanntes „IC-26" existiert in dieser Spec nicht (§16: IC-01…IC-24 lückenlos) | `configs/51-spec-plan-disabled.project.yaml:1-34` enthält **keinen** `docs-consolidation`-Key; `:11-12` `spec-plan-workflow.enabled: false` (betrifft nur den Scaffold), `:7-8` `knowledge-engine.enabled: false`, `:20-21` `external-system-override.enabled: true`; `asserts/51:29-32`; `spec_plan_scaffold.py:49-51` (`log.skip` vor jedem `mkdir`), `:62-68` (Skeleton nur bei `mode == "file-index"`), `:40-44` (`resolve_index_mode`); `IC-13`-Zeilen 1/3 und letzte Zeile |
| **NEW-8** AC-02-Snapshot ist `xfail` und damit nicht durchsetzbar | info | Snapshot **gestrichen**; AC-02 ist jetzt **rein formelbasiert** und durchsetzbar (**13** Formel-Assertions über eine Fixture-Konfiguration). Die Durchsetzung
 der konkreten Sollzahlen liegt **eindeutig** bei IC-23/AC-36; die Entscheidung ist im AC als „bewusste Entscheidung" begründet | `xfail` markiert einen **erwarteten** Fehlschlag: ein fehlerhafter Formel-Faktor wäre darin **invisible**; doppelte Zahlenhaltung (Test + `doc-facts-expected.yaml`) wäre ein zweiter Sollwert-Ort (R14) |
| **Gegenkorrektur** §17.2 „3 harte Fehlschläge" | info | §17.2 sagt jetzt **0 nach Abschirmung, 3 in der naiven Variante** — mit explizitem Hinweis, dass die 3 **kein Arbeitsauftrag** sind (NG-10 verbietet jede Änderung an `tests/scenarios/`) | Absenz-Default `false` (IC-22) ⇒ alle sechs Fixtures ohne `docs-consolidation`-Key ⇒ Generator inaktiv (IC-13 Zeile 1). `asserts/50:32` und `asserts/56:31` sind reine `[ -f ]`-Existenzprüfungen; `asserts/54:26-27` und `asserts/55:24-25` erwarten den Scaffold-Inhalt `File-based index fallback` (Skeleton bleibt unangetastet, IC-15); `asserts/52:41-44` verlangt `knowledge/wiki/index.md` **und** **kein** `docs/INDEX.md` (KE autoritativ). Naive Variante ohne Abschirmung: genau 3 Zeilen wären betroffen |

### 17.6 Rev. 0.4 — Ausführungskorrektur der Branch-/PR-Strategie (offener Punkt **OP-1**)

**Charakter dieser Revision.** Rev. 0.4 ist **keine** Inhalts- oder Design-Erweiterung, sondern die
Korrektur eines **Normativitätswiderspruchs**: Rev. 0.1–0.3 forderten an **drei** Stellen (OP1-1…OP1-3,
siehe Tabelle unten) die Strategie „ein **Branch pro Welle** (`chore/docs-consolidation-w<N>`),
gestapelte PRs" — in der W0-Zeile von §9.2, im §9.2-Absatz „PR-/Branch-Kollision" (dort wörtlich mit
dem Präfix „**Verbindlich**") und in der Mitigation von R16 (§12.2) —,
während die Ausführung einen Wellen-Branch mit einem PR verwendet hat. Da dieses Dokument sich zur
**normativen Quelle** erklärt (Kopfzeile „stillschweigende Abweichungen gibt es nicht"; §2.2 „hart
— Abweichung gilt als Spec-Verstoß"), wäre der unveränderte Stand eine Verletzung der eigenen Norm.
Korrektur deshalb **hier**, nicht in den Records.

**Betroffene Stellen (vollständig, alle geändert am 2026-09-26):**

| # | Stelle | Vorher (Rev. 0.1–0.3) | Nachher (Rev. 0.4) |
|---|---|---|---|
| **OP1-1** | §9.2, **W0-Zeile** (Spalte „Inhalt") | „Design-Freeze, Contract-Liste, **ein Branch pro Welle** (`chore/docs-consolidation-w<N>`), Entscheidungs-Records …" | „… **ein Wellen-Branch für das gesamte Vorhaben** (`feat/repository-documentation-consolidation-main`, Basis `origin/main`) mit **einem** PR gegen `main`; Wellen-Zuordnung über die **Wellenkennung im Commit-Titel**." Ausdrücklicher Rev.-0.4-/OP-1-Vermerk mit Verweis auf den Absatz „PR-/Branch-Strategie" und auf §17.6 |
| **OP1-2** | §9.2, Absatz „PR-/Branch-Kollision" (Rev. 0.1–0.3) | „**Verbindlich:** ein Branch **pro Welle** (`chore/docs-consolidation-w<N>`, in §9.2 Spalte W0 verankert), gestapelte PRs in Reihenfolge W1→W8, `git mv`-Wellen (W4/W5/W6) werden **zuerst** gemergt, weil …" | Neu gefasst als „**PR-/Branch-Strategie** (R16, rev. 0.2; rev. 0.4 …)" mit fünf verbindlichen Punkten: (1) Ein Branch / ein PR, `chore/docs-consolidation-w<N>` **aufgehoben**; (2) Wellen-Zuordnung über Commit-Titel `docs(docs-consolidation): W<N> <Zweck>`, Abschluss-Commit `… W<N> complete`, `W<N>`-Präfix verbindlich für Abschluss- und wellen-koordinierende Titel, **optional** für Datei-Commits (dort Task-ID `Task: W<N>-<k>` im Body), ein Commit pro Datei; (3) Merge-Regel: `git mv`-Wellen W4/W5/W6 **zuerst**, Wellen sequenziell W1→W8, Rebase gegen `origin/main` vor dem PR-Merge; (4) dokumentierter Bestand des überholten Vor-Branches, Post-Merge-Cleanup = eigene Entscheidung; (5) Ausführungsnachweis + Nicht-Design-Abweichung |
| **OP1-3** | §12.2, **R16** (Spalte „Mitigation") | „Ein Branch **pro Welle** (`chore/docs-consolidation-w<N>`, §9.2 W0), gestapelte PRs in Reihenfolge, `git mv`-Wellen **zuerst** mergen, ein Commit pro Datei" | Rev.-0.4-Vermerk: Branch-Anzahl ist **nicht** der Lösungsansatz; fünf Teile Reihenfolge-/Merge-Regel (identisch zu OP1-2, kurz), Verweise auf §9.2 und §17.6. **Risiko-Text und Wahrscheinlichkeit „mittel" unverändert** |
| **OP1-4** | §15, Trace-Anker | ohne Rev.-0.4-Eintrag | Rev.-0.4-Anker ergänzt (Ausführungsbelege, geänderte/unveränderte Stellen, „kein neuer `spec-id`, keine Supersession") |
| **OP1-5** | §16, Selbstreview-Tabelle | 8 Datenzeilen (im Stand `35bb176f` gemessen) | 2 Zeilen ergänzt: „**Rev. 0.4 — Abgrenzung**" und „**Ownership-Grenze (Rev. 0.4)**" ⇒ **10** Datenzeilen; der Kopf der Tabelle trägt weiterhin den Rev.-0.3-Stand (historischer Stand, wie in §11.1/§16 für OQ2/OQ6/OQ8 bereits vermerkt) |
| **OP1-6** | §17 | 17.1–17.5 | 17.6 als vollständiger Korrektur- und Beleg-Abschnitt (dieser Abschnitt) |
| **OP1-7** | Kopfblock, Frontmatter, Revisions-Tabelle, Freigabevermerk | `revision: 0.3`; Revisionshistorie „endet bei Rev. 0.3"; Revisions-Tabelle ohne 0.4 | `revision: 0.4`; Rev.-0.4-Änderungsblock im Kopf; Revisionszeile **0.4** mit Begründung. **Freigabevermerk (Stand nach der Korrektur):** Rev. 0.4 ist am **2026-09-26 durch den Nutzer bestätigt** (Entscheidungsweg laut Plan Rev. 0.4, K1); die zunächst im Dokument ausgerichtete Ausnahme („Inhaltsrevision, aber **keine** erneute Freigabe") ist **entfallen** — Auflösung und Wortlaut in **§17.7**. Frontmatter: `status: APPROVED`, `approved: 2026-09-26`, `approved-scope: …`, `revision: 0.4` |
| **OP1-8** | §13, Abweitungstabelle | A1…A12, Zählung „12 Abweichungen" | **A13** (Branch-Namensabweichung gegen Design:265) und **A14** (W4/W5/W6 seriell statt paarweise parallel, **offen**) ergänzt; Zählung auf **14** angehoben; alle Stellen, die „12 Abweichungen" nannten, nachgezogen (Kopfblock, Revisionszeile 0.4, §9.2 Punkt 5, §15, §16). **Keine** Design-Änderung — das Design bleibt unverändert |

**Unverändert geblieben (ausdrücklich geprüft, kein Widerspruch):**

- **§2.3** (Track A) und **R3**: „pro Welle ein Commit pro Datei; vor jedem Merge Rebase gegen den
  Track-A-Branch" bzw. „Rebase vor jedem Merge". Beide Formulierungen sind **wortgleich aus dem
  Design** übernommen (`docs/specs/2026-09-25-repository-documentation-consolidation-design.md:275`
  bzw. `:368`) und **branch-anzahl-unabhängig**: unter der Ein-Branch-Strategie existiert genau
  **ein** Merge, der Rebase geschieht davor. Keine Änderung — eine Änderung wäre eine
  Design-Abweichung und gehörte in §13.
- **§9.2 Spalte „Rückrollpunkt"** (je Welle): der Plan führt dieselben Punkte
  (`docs/plans/2026-09-25-repository-documentation-consolidation.md`, Wellenübersicht) unverändert
  und **commitweise**; die Wellen-Rückrolle wird durch die Ein-Branch-Strategie **nicht** berührt.
- **§9.2 Spalte „Parallel mit" / „Abhängig von"** für **W4/W5/W6**: war nicht Teil von OP-1 und ist
  in Rev. 0.4 **doch** angefasst worden — die Spalte wurde auf den ausgeführten **sequenziellen**
  Stand umgestellt (PG-3), der Plan führt W4/W5/W6 seit Rev. 0.3 seriell. Grund der
  **Abweichung** (Design :269-271 parallel ↔ Plan PG-3 seriell; `:275` führt W5 zusätzlich als
  gleichzeitig ausführbar mit W2 ‖ W3): gemeinsamer Testdatei-Anker
  AC-28/AC-29/AC-31/AC-32 und `check_plan_file_overlap`. Die Abweichung ist **vorbestehend** und
  wurde **nicht** von Rev. 0.4 erzeugt; sie ist **nicht aufgelöst**, sondern als **A14** in §13 und
  **offener Punkt in §17.8** registriert (Owner `orchestrator` → `main_chat`). Für W1, W2, W3, W7
  und W8 bleiben die Spalten inhaltlich unverändert. *(Ausnahme: die **W3**-Zeile nannte zuvor „W2, W4"; da W4 nach der PG-3-Kette **Vorgänger** von W3 ist, wurde „W4" dort zu „Vorgänger, nicht Partner" präzisiert — dieselbe Korrektur, keine eigene Abweichung.)*
- **§2.2 NG-1…NG-11, §7 (AC-01…AC-41), §8 (NFA-01…NFA-11), §9.1, §3–§8, §10, §11, §12.1/§12.3,
  §13, §14**: keine der 41 AC, 24 IC, 11 NFA, 20 R, 25 F, 13 M, 11 NG, 10 FI, 9 OQ, 9 V, 9 Wellen
  nennt eine Branch-, PR- oder Merge-Anforderung. Beleg: vollständige Suche nach
  `chore/docs-consolidation`, „pro Welle", „gestapelt", „Branch pro", „Merge", „Rebase" — die
  Fundstellen sind oben exhaustiv aufgeführt.

**Verbindlichkeits-Fazit:** Nach Rev. 0.4 ist diese Spec wieder die **normative Quelle** *und*
deckungsgleich mit der Ausführung. Der R16-Schutzziel wird weiterhin verfolgt (Merge-Regel
`git mv`-Wellen zuerst, Reihenfolge W1→W8, ein Commit pro Datei, Sequenzierung über die
Commit-Historie), nur über den ausgeführten statt über den überholten Mechanismus.

**Offener Punkt-Status:** **OP-1 ist mit dieser Revision inhaltlich aufgelöst** (die normative
Quelle stimmt wieder mit der Ausführung überein) und durch die **Nutzer-Bestätigung der Rev. 0.4
vom 2026-09-26** abgesichert (§17.7). **Formal geschlossen** wird er damit **nicht** —
Plan und die sechs W0-Records führen ihn weiterhin als offen und sind in dieser Revision
**nicht** geändert (Files-Ownership). Zum Abschluss nachzuführen (Vorgabe, **nicht** ausgeführt):

| Nachzuführen | Stelle | Was |
|---|---|---|
| `docs/plans/2026-09-25-docs-consolidation-wave0-freeze.md` | Kapitel 7.1 (`:289-302`), Kapitel 10 (OP-1-Tabelle `:417`, Zusammenfassung `:407`), Zeile 25 (Kopf) | OP-1 von „offen" auf „inhaltlich aufgelöst durch Spec Rev. 0.4 (2026-09-26, durch den Nutzer bestätigt — §17.7)"; die Formulierung „Korrektur der Spec (**Rev. 0.4**) **beauftragt, nicht ausgeführt** — sie erfordert ein Concept-Review" (`:417`) **entfällt**; Verweis auf §17.6/§17.7 |
| `docs/plans/2026-09-25-docs-consolidation-track-a-gate.md` | §10, Punkt 5 (`:302`) | dasselbe |
| `docs/plans/2026-09-25-docs-consolidation-oq6.md` | Kopfpunkt 2 (`:24`), OP-1-Hinweis (`:216`) | dasselbe |
| `docs/plans/2026-09-25-repository-documentation-consolidation.md` | K1-Liste im Änderungsblock (`:77`), Global Constraints (`:158`), Self-Review (`:476` und offene Punkte `:1895`), Task **W0-2** (Spezifikationsabweichungs-Box) | OP-1 schließen; die Formulierung „die Korrektur der Spec (Rev. 0.4) ist **beauftragt, aber nicht ausgeführt**" entfällt; Rev.-0.4-Bezug auf `§17.6` + `§17.7` (Nutzer-Bestätigung) umstellen. **In dieser Revision bewusst nicht ausgeführt** — der Plan wurde **nur in Ankern und Faktenangaben** angefasst (K12, Revisions-Bump 0.3 → 0.4, berichtigte Zeilenzahlen, berichtigte OP-1-Aussage im Self-Review; **kein** Task-, Wellen-, AC-, IC-, NFA- oder Gate-Inhalt). Die hier genannten Plan-Zeilenanker (`:77`, `:158`, `:476`, `:1895`) sind durch den Revisions-Bump des Plans **verschoben** und bei der Umsetzung dieses Folge-Schritts neu zu bestimmen |
| `docs/plans/2026-09-25-docs-consolidation-oq1.md` | Kopf (`:42`), Punkt 3 (`:422`) | **keine inhaltliche Änderung nötig** — die Vorrang-Regel („bei Widerspruch gilt die Spec") ist durch Rev. 0.4 wieder stimmig; nur die Datums-/Versionsangabe wäre optional nachzuziehen |
| `docs/plans/2026-09-25-docs-consolidation-oq2.md`, `…-oq8.md` | Kopf (`:38-39` bzw. `:35`) | **keine inhaltliche Änderung nötig**, siehe vorige Zeile |

Ein **Concept-Review** über Rev. 0.4 **ist als erfolgt zu führen** (2026-09-26,
`VERDICT: BLOCKED`, Befund **F-1**); der Entscheidungsweg `main_chat` (Plan Rev. 0.4, K1) hat
am **2026-09-26** entschieden — Auflösung und Wortlaut in **§17.7**. Der Abschluss von **OP-1**
in Plan und Records bleibt ein **Folgeschritt** (siehe Tabelle oben).

---

### 17.7 Nutzerfreigabe der Rev. 0.4 (Behebung von **F-1**)

| Feld | Angabe |
|---|---|
| **Befund** | **F-1** — Concept-Review der Rev. 0.4: `VERDICT: BLOCKED`. Rev. 0.4 führte **neue normative Pflichten** ein (verbindliche Commit-Titel-/Body-Konvention, Branch-Aufbewahrung als Scope-Aussage) und installierte sie „mit derselben Verbindlichkeitstiefe", **ohne erneute User-Freigabe**. Der Freigabevermerk richtete die Ausnahme **im Dokument selbst** aus; §15 lässt `APPROVED` nur nach Concept-Review **und** User-Freigabe zu. |
| **Ursache** | Die Rev. 0.4 war als **Inhaltsrevision** ohne Freigabeschritt entstanden; der Autor hat die Ausnahme selbst erteilt, weil der Freigabeumfang (W0–W8) unverändert blieb. Diese Begründung trug dem Gate nicht Rechnung. |
| **Entscheidung** | Der **Nutzer** hat **Rev. 0.4 am 2026-09-26 ausdrücklich freigegeben** — über den Entscheidungsweg laut Plan Rev. 0.4, K1 (`main_chat`), weitergeleitet an den `orchestrator` und hier durch `documenter` formalisiert. |
| **Bezugsrahmen der Bestätigung** | **unverändert:** der Umfang der Ausführungsmechanik **W0–W8** (keine Welle, kein AC/IC/NFA/Risiko verschoben). **neu bestätigt:** die in Rev. 0.4 aufgenommenen **Normativitätsaussagen** — die verbindliche **Commit-Titel-/Body-Konvention** (§9.2 „PR-/Branch-Strategie", Punkt 2; R16-Mitigation) und die **Branch-Aufbewahrung** als Scope-Aussage (Punkt 4: „diese Spec schreibt weder Löschung noch Aufbewahrung eines Branches vor"). |
| **Bedingung** | **A13** und die **W4/W5/W6-Serialität** (A14) sind als **offene, dokumentierte Abweichungen** zu registrieren — erledigt: A13/A14 in §13, A14 zusätzlich als offener Punkt in **§17.8**. |
| **Ergebnis** | **F-1 aufgelöst.** Die in diesem Dokument ausgerichtete Ausnahme („Inhaltsrevision ohne erneute Freigabe") ist **entfallen** — die Freigabe liegt extern vor. `status: APPROVED` besteht unverändert, **kein** Revisions-Bump: die inhaltliche Revisionshistorie endet bei **Rev. 0.4**. Geändert wurden: Frontmatter (`approved: 2026-09-26`, `approved-scope`), Statuskopf, Revisionszeile **0.4**, Revisionszeile **„Freigabe (Rev. 0.4)"**, §16 (Zeile „Rev. 0.4 — Abgrenzung") und §17.6 (OP1-7). |
| **Nicht betroffen** | AC-01…AC-41, IC-01…IC-24, NFA-01…NFA-11, R1…R20, F1…F25, M-1…M-13, NG-1…NG-11, FI-1…FI-10, OQ1…OQ9, W0…W8 — **keine** inhaltliche Änderung durch die Freigabe. |

---

### 17.8 **Offener Punkt** — W4/W5/W6-Serialität (A14)

> **Status: OFFEN.** Dieser Punkt ist **bewusst nicht aufgelöst.** Er wurde vom Nutzer am
> 2026-09-26 als *offene, dokumentierte Abweichung* registriert; die Inhaltsentscheidung ist
> ausdrücklich der Ausführungsmessung überlassen.

| Feld | Angabe |
|---|---|
| **Sachverhalt** | §9.2 führte **W4, W5, W6** in der Spalte „Parallel mit" als **paarweise parallel** (W4‖W5, W4‖W6, W5‖W6) — das entspricht dem Design (`docs/specs/2026-09-25-repository-documentation-consolidation-design.md:269-271`; `:275` führt W5 zusätzlich als gleichzeitig ausführbar mit W2 ‖ W3). Der Plan Rev. 0.4 führt sie **seriell**: `PG-3 (BEWUSST SERIELL, 1 Agent) W4-1 → … → W6-2` (Wellenübersicht) und in den Task-Köpfen W4-1…W6-2 (`parallel_group: PG-3 (seriell)`). **Ausgeführt wird seriell.** |
| **Registrierung in §9.2** | Die Spalte „Parallel mit" weist für W4/W5/W6 seit Rev. 0.4 **`sequenziell` (PG-3)** aus; die Spalte „Abhängig von" führt die PG-3-Kette mit. Die Angabe bildet damit die **tatsächliche Umsetzung** ab. |
| **Begründung des Plans** | Alle vier AC der drei Wellen — **AC-28, AC-29, AC-31, AC-32** — verweisen per `::` auf denselben Testdatei-Anker `tests/test_docs_consolidation_migration.py`. Tasks, die dieselbe Datei anlegen oder erweitern, sind **nicht ownership-disjunkt**; `check_plan_file_overlap` (`scripts/lib/orchestration.py`) würde den Parallelstart als Fehler melden. Zusätzlich erzeugt jede `git mv`-Welle R+A-Diffs auf denselben Stammpfaden. (Plan Rev. 0.4, Abschnitt „Warum W2 ‖ W3 parallel ist, W4/W5/W6 aber nicht".) |
| **Charakter** | **Echte, vorbestehende Spec-Abweichung** (Plan gegen Spec) — **nicht** von Rev. 0.4 erzeugt und **nicht** Teil der Branch-Korrektur (OP-1). Der Concept-Reviewer hat sie als solche bestätigt. |
| **Abweichungs-ID** | **A14** in §13 (Design ↔ Spec ↔ Plan). |
| **Status** | **OFFEN** |
| **Owner** | `orchestrator` → Eskalation an `main_chat` (Produkt-/Ausführungsentscheidung). |
| **Auflösungsweg** | Eine Auflösung — also die Rückführung der §9.2-Angabe auf „parallel" **oder** eine Änderung der Ausführungsreihenfolge — erfordert eine **eigene Spec-Revision mit Concept-Review**. Der Punkt wird **nicht** nebenläufig in Plan oder Records entschieden. |
| **Zwischendurch geltende Regel** | Bis zur Auflösung gilt die **Ausführung** (seriell, PG-3); die Abweichung ist dokumentiert und nicht stillschweigend. |
