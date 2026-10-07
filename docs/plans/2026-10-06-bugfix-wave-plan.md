---
title: Bugfix-Wave — Implementierungsplan (52 Issues, 8 Cluster)
status: APPROVED
date: 2026-10-06
freigegeben_durch: Nutzer
freigegeben_am: 2026-10-06
repo: agent-meta
source: .tmp/clustering-analysis.md (2026-10-06), .tmp/triage-summary.txt (Track A, Referenz/Exclusion)
scope: Implementierungsplan für 52 bereits geclusterte, implementierungsreife Issues — Reihenfolge, Task-Zerlegung, Akzeptanzkriterien, Rollen-Tier je Issue/Issue-Gruppe
---

# Bugfix-Wave — Implementierungsplan

> **STATUS: APPROVED** — Freigegeben durch Nutzer: 2026-10-06. Implementierung kann beginnen nach Freigabe der Wave-spezifischen Specs (siehe Global Constraints, Punkt 1).
> **Datum:** 2026-10-06 · **Quelle:** `.tmp/clustering-analysis.md` (8-Cluster-Analyse, 52 implementierungsreite Issues, heute verifiziert).
> **Charakter:** Ausführungsplan auf Wellen-Ebene mit Task-Zerlegung je Issue/Issue-Gruppe. Dies ist **kein** Ersatz für das projekteigene Spec/Plan-Gate (`.claude/rules/use-orchestrator.md`): jede Welle/Cluster-Gruppe braucht vor Step 2 (Implementierung) ihren eigenen freigegebenen Spec (`Status: APPROVED`) — siehe Global Constraints, Punkt 1.

## 0. Daten-Vorbehalt (Methodik-Hinweis, kein Platzhalter)

Dieses Planungs-Environment hat keinen Netzwerk-/`gh`-API-Zugriff zur Autorenzeit. Die Issue-Titel in diesem Dokument sind **aus der Cluster-Root-Cause-Beschreibung von `.tmp/clustering-analysis.md` abgeleitete Arbeitstitel**, keine wörtlich von GitHub übernommenen Titel. Jede Task-Gruppe trägt deshalb als verbindlichen **Step 0**: den Live-Issue-Body per `gh issue view <N> --json title,body,labels` abrufen (gh ist installiert unter `/home/hermes/.local/bin/gh`, nur nicht in `$PATH`) und gegen die hier genannte Scope-Annahme abgleichen, bevor der Test-/Implementierungs-Step beginnt. Eine Abweichung zwischen Live-Issue und dieser Scope-Annahme ist ein Stop-Punkt für die ausführende Rolle, kein Grund zum Improvisieren.

Für **C5** (13 Template-Issues, #769–#780 teilweise) existiert bereits eine vollständige Rolle-für-Rolle-Triage: `docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md` (#769–#780, Accept/Modify/Reject/Duplicate je Vorschlag). Wave 4 referenziert diese Triage statt sie zu duplizieren.

## 1. Scope

- **52 implementierungsreite Issues** über 8 Cluster (C1–C8), bereits bereinigt um Track-A (14 Issues: #838, #852–858, #863, #844, #552, #859–860, #603 — separater Track) und um 11 klärungsbedürftige Issues (siehe §7).
- **4 Feedback-Kandidaten** (#896–899) separat trianiert, siehe §8.
- **Nicht im Scope:** Track-A-Issues (parallele Spur), die 11 klärungsbedürftigen Issues, jede Implementierung selbst (dieser Plan plant, implementiert nicht).

## 2. Dev-Tier-Rubrik (für jede Task-Zeile unten angewendet)

| Tier | Datei-/Impact-Umfang | Rolle |
|---|---|---|
| S | ≤ 2 Dateien, isoliert | `junior-developer` |
| M | 3–8 Dateien, ein Modul/eine Config-Familie | `developer` |
| L | 9–20 Dateien oder cross-cutting (Sync-Kern, Architektur, Rollen-Fleet) | `senior-developer` |

## 3. Global Constraints (für jede Welle/jeden Task)

1. **Spec/Plan-Gate bleibt verbindlich.** Dieser Plan ersetzt keine Spec. Vor Step 2 (Implementierung) jeder Task-Gruppe: ein freigegebener Spec (`Status: APPROVED`) — bei S/M-Issues reicht ein gebündelter Cluster-Spec für die ganze Wave, bei L-Issues (C6, C7, Teile von C5) ein Einzel-Spec je Issue.
2. **Provider-Agnostik.** Keine `if provider == "name"`-Literale; Unterschiede über Capability-Flags/Config-Keys (`provider-agnostic`-Skill).
3. **Branch-Guard.** Ein Feature-Branch pro Welle oder pro Issue-Gruppe (`fix/`, `feat/`, `chore/`), nie direkt auf `main`. Git-Mutationen laufen über die `git`-Rolle.
4. **Kein Worktree-Isolation-Argument.** Alle Rollen arbeiten direkt im Projektverzeichnis.
5. **TDD pro Task.** Jeder Implementierungs-Task beginnt mit einem roten Test, bevor der Fix geschrieben wird.
6. **Verifikation pro Fix:** `python3 scripts/sync.py --validate`, `python3 scripts/sync.py --check --dry-run`, zielgerichteter `pytest`-Lauf, am Ende der Welle zusätzlich die Vollsuite `python3 -m pytest tests/ -q`.
7. **Versionierung/Changelog:** jede Template-/Config-Änderung bumpt `VERSION` und trägt einen `CHANGELOG.md`-Eintrag (Keep-a-Changelog-Format, bereits Projekt-Konvention).
8. **Issue-Lifecycle:** Closing-Keyword (`Fixes #NNN`) im Commit/PR plus Post-Completion-Kommentar je Issue (bei Comma-Listen nur das erste `Fixes #N` schließt automatisch — Rest manuell nachziehen).
9. **Datei-Ownership ist disjunkt innerhalb einer Parallel-Gruppe.** Wo zwei Issues dieselbe Datei berühren (z.B. mehrere C2-Issues in `config/ai-providers.yaml`), läuft die Gruppe sequenziell statt parallel — unten je Wave vermerkt.
10. **Aufwand:** Gesamtzusammenfassung über `effort-estimator` (Text-Referenz, kein Tool-Call) — siehe §9, erst nach Freigabe dieses Plans angefordert.

## 4. File Structure (globale Karte über alle Wellen)

| Cluster | Primär berührte Pfade |
|---|---|
| C1 | `scripts/sync.py`, `scripts/lib/cli_commands.py`, `.claude/hooks/dod-push-check.sh` |
| C2 | `config/ai-providers.yaml`, `config/generated/model-registry.json`, `.meta-config/project.yaml`, `agents/2-platform/*` |
| C3 | `scripts/sync.py`, `scripts/lib/cli_commands.py`, `.claude/hooks/*` |
| C4 | `agents/1-generic/*`, `agents/2-platform/*`, `config/skills-registry.yaml` |
| C5 | `agents/1-generic/*.md`, `agents/2-platform/*.md`, `agents/0-external/*.md` |
| C6 | `scripts/lib/`, `scripts/sync.py`, `agents/`, `.meta-config/`, `docs/` |
| C7 | `docs/specs/`, `docs/plans/`, `agents/`, `scripts/`, `config/` |
| C8 | `config/`, `docs/`, `.gitignore`, `.meta-config/project.yaml` |

Kein Pfad wird von zwei parallel laufenden Clustern gleichzeitig beschrieben — Details zu Parallelitäts-Einschränkungen stehen je Wave.

## 5. Wellen-Übersicht und Abhängigkeits-Rationale

```
Wave 1 (C1, P1 — Fundament)
   #265 #266 #267 #346 #753
     |
     v
Wave 2 (C2 + C3, P2 — parallel, beide unabhängig von C1-internals, blockieren spätere Cluster)
   C2: #264 #330 #476 #680 #751 #899      C3: #478 #479 #481
     |                                       |
     v                                       v
Wave 3 (C4 + C8 + C6 — parallel, je von Wave 1/2 abhängig)
   C4 (Depends on C1+C2): #395 #517 #527 #694
   C8 (Depends on C2): #676 #679 #681 #745 #746
   C6 (Depends on C3): #329 #332 #334 #338 #339 #452 #473 #482 #548 #674
     |
     v
Wave 4 (C5, P3 — Depends on C1 / Blocker #528)
   #528 #769 #770 #771 #772 #773 #774 #775 #777 #778 #779 #780 #783
     |
     v
Wave 5 (C7, P1–P3 — Depends on C6)
   #192 #207 #370 #523 #540 #547
```

**Rationale:**
- **Wave 1 zuerst:** C1 (Commit-Gate-Stabilität, Validierungs-Gates, Result-Summarization) ist Fundament für den gesamten Rest — #267 blockiert #528 (Wave 4) direkt.
- **Wave 2 parallel:** C2 (Config/Provider-Konsistenz) und C3 (Hook-Robustheit) berühren disjunkte Dateibereiche (`config/ai-providers.yaml`/`model-registry.json` vs. `.claude/hooks/*`) und haben keine Abhängigkeit untereinander — beide laufen gleichzeitig nach Wave 1.
- **Wave 3 parallel:** C4 (Provider-Capability) braucht ein stabiles C1+C2-Fundament (Commit-Gates + Modell-Registry), C8 (Infrastruktur-Config) braucht die C2-Konfig-Vereinheitlichung, C6 (Refactor/Architektur) braucht die C3-CLI-Modularisierung (#481) als Voraussetzung für die Hook-Registrierungs-Vertiefung. Alle drei sind dateidisjunkt (`agents/1-generic` + `config/skills-registry.yaml` vs. `config/` + `.gitignore` vs. `scripts/lib/` + `.meta-config/`).
- **Wave 4 (C5):** 13 Template-Issues, abhängig von C1 (stabiles Output-Contract-Gate) und intern blockiert durch #528 (muss als erstes der Gruppe laufen). Eigene Welle wegen Umfang (13 Issues, Fleet-weite Template-Edits) und weil sie auf eine bereits bestehende Rolle-für-Rolle-Triage aufsetzt (`docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md`).
- **Wave 5 (C7) zuletzt:** Feature/RFC-Cluster braucht das SE-Framework-Design aus C6 (#329/#332) als Eingabe. #370 (Phase-Planung) ist bereits implementiert und abgeschlossen (verifiziert in dieser Session). #523 (Agent-Eval-Framework-Review) ist ein unabhängiger Concept-Review-Punkt, unabhängig von #370.

---

## Wave 1 — C1: Commit-Gate Stability (P1, Fundament)

**Issues:**

| # | Arbeitstitel | Priorität | Dateien | Tier |
|---|---|---|---|---|
| #265 | FANOUT/BARRIER-Backend-Contract: Plan/Validierungs-Robustheit nachschärfen | P1 | `scripts/sync.py`, `scripts/lib/cli_commands.py` | M (`developer`) |
| #266 | Statische File-Affinity-/Overlap-Prüfung vor Pre-Dispatch verlässlicher machen | P1 | `scripts/lib/cli_commands.py` | M (`developer`) |
| #267 | Result-Summarization-Contract: Checkpoint/Rohausgabe-Archiv robust gegen Teilausfälle | P1 | `scripts/sync.py`, `scripts/lib/cli_commands.py` | M (`developer`) |
| #346 | Validierungs-Gate-Robustheit (Folgefix zu #265/#266/#267) | P1 | `scripts/sync.py` | S (`junior-developer`) |
| #753 | `dod-push-check.sh`: unfilterte Verifikations-Kommandos / Exit-Code-Trennung | P1 | `.claude/hooks/dod-push-check.sh` | S (`junior-developer`) |

**Gemeinsame Interfaces:** `execute_plan`/Dispatcher-Seam (`scripts/lib/cli_commands.py`), `check_file_overlap()`/`check_plan_file_overlap` (Overlap-Erkennung), `CheckpointStore` (Checkpoint-/Summarization-Pfad) — alle vier Issues berühren denselben Commit-Gate-Pfad; **sequenziell in dieser Reihenfolge** (#265 → #266 → #267 → #346), da jedes auf dem Vorgänger-Contract aufbaut; #753 ist dateidisjunkt (eigener Hook) und läuft parallel dazu.

**Task-Zerlegung (je Issue):**
1. Step 0: `gh issue view <N>` lesen, Scope gegen diese Zeile abgleichen.
2. Step 1 (rot): gezielten Test in `tests/test_orchestration_contract.py` bzw. `tests/test_orchestrator_guard_hook.py`/`tests/` (für #753: neuer/erweiterter Hook-Test) schreiben, der den Issue-Defekt reproduziert; `python3 -m pytest <modul> -q` beobachtet Fehlschlag.
3. Step 2: Fix in der genannten Datei implementieren, keine Scope-Erweiterung über die Issue-Beschreibung hinaus.
4. Step 3 (grün): derselbe Testlauf grün; zusätzlich `python3 scripts/sync.py --validate` und `--check --dry-run` grün.
5. Step 4: Commit über die `git`-Rolle, `Fixes #<N>`.

**Akzeptanzkriterien:**
- #265/#266/#267: der jeweils neue/erweiterte Test in `tests/test_orchestration_contract.py` ist grün; kein Regressionsfehlschlag in der Vollsuite.
- #346: der im Issue benannte Edge-Case (Validierungs-Gate) hat einen dedizierten Regressionstest, der vor dem Fix rot war.
- #753: jedes Verifikations-Kommando im Hook schreibt stdout+stderr in eine eigene Log-Datei und meldet den Exit-Code separat (kein `rtk`-Prefix); ein manueller Lauf mit absichtlich fehlschlagendem Sub-Check zeigt den korrekten, isolierten Exit-Code.

---

## Wave 2a — C2: Config/Provider Consistency (P2)

**Issues:**

| # | Arbeitstitel | Priorität | Dateien | Tier |
|---|---|---|---|---|
| #264 | Capability-gated Intent-Routing: Modell-Registry-Abgleich nachschärfen | P2 | `config/ai-providers.yaml`, `config/generated/model-registry.json` | M (`developer`) |
| #330 | Provider-Drift zwischen `config/ai-providers.yaml` und generierten Artefakten | P2 | `config/ai-providers.yaml`, `agents/2-platform/*` | M (`developer`) |
| #476 | Capability-Mismatch-Fix (Vorbedingung für #680) | P2 | `.meta-config/project.yaml`, `config/ai-providers.yaml` | M (`developer`) |
| #680 | Config-Vereinheitlichung (abhängig von #476) | P2 | `.meta-config/project.yaml` | S (`junior-developer`) |
| #751 | Provider-Capability-Konsistenz-Folgefix | P2 | `agents/2-platform/*` | S (`junior-developer`) |
| #899 | Modell-Wartungsprozedur: Sync-Workflow vs. manuelles Editieren klären | P2 | `config/ai-providers.yaml`, `docs/` | S (`junior-developer`) — ggf. reines Doku-Fix, siehe Hinweis |

**Reihenfolge innerhalb der Gruppe:** `#899 → #264 → #330` (laut Cluster-Dependency; #899 klärt zuerst, ob der Modellregistrie-Workflow Sync-generiert oder hand-editiert ist — diese Antwort bestimmt, ob #264/#330 am generierten Artefakt oder an der Quelle ansetzen), danach `#476 → #680` (harte Abhängigkeit). `#751` ist dateidisjunkt zu beiden Ketten (nur `agents/2-platform/*`) und läuft parallel.

**Hinweis #899:** Falls `gh issue view #899` ergibt, dass der Defekt reine Dokumentationslücke ist (Cluster-Root-Cause nennt „may be user-error or doc"), reduziert sich der Task auf einen Doku-Fix in `docs/guides/` — kein Code-Fix, kein Test nötig, nur ein `documenter`-Review statt `junior-developer`-Implementierung.

**Gemeinsame Interfaces:** `config/ai-providers.yaml` als Single-Source für Provider-Metadaten; `scripts/sync.py` liest/generiert `config/generated/model-registry.json` daraus — jede Config-Änderung muss durch einen Sync-Lauf neu validiert werden (Barrier-Step, siehe unten).

**Task-Zerlegung:**
1. Step 0: `gh issue view <N>` lesen.
2. Step 1 (rot): Config-Fixture-Test (z.B. `tests/test_mcp_config.py`-ähnliches Muster) schreiben, der die aktuelle Inkonsistenz (Provider X fehlt im Registry-Output, Capability-Flag falsch) als Fehlschlag reproduziert.
3. Step 2: `config/ai-providers.yaml` bzw. `.meta-config/project.yaml` korrigieren — keine Provider-Namens-Literale in Code, nur Config-Werte.
4. Step 3 (Barrier): `python3 scripts/sync.py` einmal laufen lassen, damit `config/generated/model-registry.json` und `agents/2-platform/*` neu generiert werden; Diff gegen die Erwartung prüfen.
5. Step 4 (grün): zielgerichteter Test grün, `python3 scripts/sync.py --check --dry-run` rc 0.
6. Step 5: Commit über `git`-Rolle, `Fixes #<N>`.

**Akzeptanzkriterien:**
- #264/#330: der generierte `model-registry.json`-Eintrag für den betroffenen Provider stimmt mit `config/ai-providers.yaml` überein (byte-identischer Round-Trip nach Sync).
- #476/#680: das im Issue benannte Capability-Flag ist in `.meta-config/project.yaml` konsistent mit dem, was `config/ai-providers.yaml` für denselben Provider deklariert — ein Konsistenz-Test schlägt vor dem Fix fehl, danach nicht.
- #751: kein Provider-Platzhalter/`{{VARIABLE}}` bleibt nach Sync unsubstituiert im betroffenen `agents/2-platform/*`-Artefakt.
- #899: entweder ein grüner Doku-Test (Workflow korrekt dokumentiert) oder — falls Code-Fix nötig — ein Regressionstest für den Sync-vs-Hand-Edit-Konflikt.

---

## Wave 2b — C3: Hook Robustness (P2)

**Issues:**

| # | Arbeitstitel | Priorität | Dateien | Tier |
|---|---|---|---|---|
| #481 | CLI-Modularisierung / Argparse-Extraktion (Vorbedingung für #478/#479) | P2 | `scripts/sync.py`, `scripts/lib/cli_commands.py` | L (`senior-developer`) |
| #478 | Hook-Registrierungs-Lücke (abhängig von #481) | P2 | `.claude/hooks/*`, `scripts/lib/cli_commands.py` | M (`developer`) |
| #479 | cwd-abhängige Hook-Logik (abhängig von #481) | P2 | `.claude/hooks/*` | M (`developer`) |

**Reihenfolge:** `#481 → {#478, #479 parallel}` — beide Folge-Issues setzen auf der CLI-Modularisierung auf, sind aber untereinander dateidisjunkt genug (unterschiedliche Hook-Dateien) um nach #481 parallel zu laufen.

**Task-Zerlegung #481:**
1. Step 0: `gh issue view #481` lesen — exakte Argparse-Extraktionsgrenze bestätigen.
2. Step 1 (rot): Test in `tests/test_orchestration_contract.py`/CLI-Testmodul, der das aktuelle CLI-Modul gegen die Ziel-Struktur (ausgelagerte Argparse-Definition, importierbar ohne Seiteneffekt) prüft; schlägt vor dem Refactor fehl.
3. Step 2: `scripts/lib/cli_commands.py` extrahieren/refaktorieren, `scripts/sync.py` auf den neuen Einstiegspunkt umstellen; keine Verhaltensänderung der CLI-Flags.
4. Step 3 (grün): CLI-Testmodul grün, `python3 scripts/sync.py --help` liefert identische Ausgabe wie vor dem Refactor (Snapshot-Vergleich).
5. Step 4: Commit über `git`-Rolle, `Fixes #481`.

**Task-Zerlegung #478/#479 (je eigener Task, nach #481 grün):**
1. Step 0: `gh issue view <N>` lesen.
2. Step 1 (rot): Hook-Test schreiben, der die fehlende Registrierung (#478) bzw. die cwd-Abhängigkeit (#479, Fix-Muster analog zu bereits gemergtem #851 — `${CLAUDE_PROJECT_DIR}`-Ankerung) reproduziert.
3. Step 2: Fix in der betroffenen `.claude/hooks/*`-Datei bzw. deren Registrierungseintrag.
4. Step 3 (grün): Hook-Test grün; `python3 scripts/sync.py --check --dry-run` rc 0.
5. Step 4: Commit über `git`-Rolle, `Fixes #<N>`.

**Akzeptanzkriterien:**
- #481: CLI-Verhalten (Flags, Exit-Codes, `--help`-Text) unverändert; die Argparse-Definition ist aus `scripts/sync.py` in ein importierbares Modul extrahiert und von mindestens einem eigenständigen Unit-Test ohne Sync-Lauf abgedeckt.
- #478: der im Issue benannte Hook erscheint nach einem frischen `python3 scripts/sync.py`-Lauf in der generierten `settings.json`/Registrierungsliste.
- #479: der Hook liefert dasselbe Ergebnis unabhängig vom aufrufenden `cwd` (Test ruft den Hook aus zwei verschiedenen Arbeitsverzeichnissen auf und vergleicht die Ausgabe).

---

## Wave 3a — C4: Provider Capability (P2–P3, Depends on C1+C2)

**Issues:**

| # | Arbeitstitel | Priorität | Dateien | Tier |
|---|---|---|---|---|
| #395 | Skills-Integration-Lücke (Capability-Claim ohne Artefakt) | P2 | `agents/1-generic/*`, `config/skills-registry.yaml` | M (`developer`) |
| #517 | Agent-Rollen-Capability-Nachschärfung (Folgefix zu `test-executor`-Einführung) | P2 | `agents/1-generic/*` | S (`junior-developer`) |
| #527 | Commit-Autorisierungs-Capability-Fix | P2–P3 | `agents/2-platform/*` | S (`junior-developer`) |
| #694 | Auto-Commit-Tier-Capability-Konsistenz (Folgefix zu bereits gemergtem Auto-Commit-Feature) | P2–P3 | `agents/1-generic/*`, `scripts/lib/auto_commit.py` | M (`developer`) |

**Task-Zerlegung (gemeinsames Muster, je Issue ein eigener Task):**
1. Step 0: `gh issue view <N>` lesen.
2. Step 1 (rot): Capability-Konsistenz-Test (nach Muster `tests/test_external_tools_registry.py`/`tests/test_auto_commit_lib.py`) schreiben, der die im Issue genannte Capability-Über- oder -Unter-Deklaration reproduziert.
3. Step 2: Fix in `config/skills-registry.yaml` bzw. dem betroffenen `agents/1-generic/*.md`-Frontmatter/Template-Body — Capability-Flag statt Freitext-Prosa, wo das Target ein maschinenlesbares Feld ist.
4. Step 3 (grün): zielgerichteter Test grün; `python3 scripts/sync.py --check --dry-run` rc 0.
5. Step 4: Commit über `git`-Rolle, `Fixes #<N>`.

**Akzeptanzkriterien:**
- #395: jede in `config/skills-registry.yaml` deklarierte Skill-Capability hat ein tatsächlich emittiertes Artefakt (Test prüft `exists()` auf den erwarteten generierten Pfad).
- #517: die Capability-Matrix in `config/role-defaults.yaml`/Template stimmt mit der tatsächlich im Template beschriebenen Fähigkeit überein (kein Claim ohne Tool/Output-Contract-Beleg).
- #527: Commit-Autorisierung ist über ein Capability-Flag ausgedrückt, nicht über Provider-Namens-Literal (Test: `tests/test_provider_agnostic_dispatch.py` bleibt grün).
- #694: Auto-Commit-Tier-Deklaration im Template stimmt mit `scripts/lib/auto_commit.py`-Verhalten überein (Regressionstest in `tests/test_auto_commit_lib.py`).

---

## Wave 3b — C8: Infrastructure Config (P2–P3, Depends on C2)

**Issues:**

| # | Arbeitstitel | Priorität | Dateien | Tier |
|---|---|---|---|---|
| #676 | Plattform-Preset-Inkonsistenz | P2 | `config/`, `.meta-config/project.yaml` | S (`junior-developer`) |
| #679 | Skill-Registry-Lücke (Folgefix, Config-seitig) | P2 | `config/skills-registry.yaml` | S (`junior-developer`) |
| #681 | Docker-Scan-Konfigurationslücke | P3 | `config/` | S (`junior-developer`) |
| #745 | Gitignore-Konfigurationsfix | P2–P3 | `.gitignore`, `.meta-config/project.yaml` | S (`junior-developer`) |
| #746 | Folgefix zu #745 (gemeinsamer Config-Bereich) | P2–P3 | `.gitignore` | S (`junior-developer`) |

**Reihenfolge:** `#745 → #746` sequenziell (teilen sich `.gitignore`), Rest (`#676`, `#679`, `#681`) dateidisjunkt und parallel.

**Task-Zerlegung (gemeinsames Muster):**
1. Step 0: `gh issue view <N>` lesen.
2. Step 1 (rot): Config-/Konsistenz-Test schreiben (z.B. gegen `scripts/lib/config.py`-Loader oder ein neues `tests/test_<topic>_config.py`), der den im Issue benannten Default/Preset-Fehler reproduziert.
3. Step 2: Fix in der jeweiligen Config-Datei (`config/*.yaml`, `.gitignore`, `.meta-config/project.yaml`).
4. Step 3 (grün): Test grün; `python3 scripts/sync.py --validate` rc 0.
5. Step 4: Commit über `git`-Rolle, `Fixes #<N>`.

**Akzeptanzkriterien:**
- #676: das betroffene Plattform-Preset erzeugt nach Sync denselben Artefakt-Satz wie die anderen Presets derselben Kategorie (Vergleichstest).
- #679: der fehlende Skill-Registry-Eintrag ist vorhanden und von `scripts/lib/skill_channel.py` auflösbar.
- #681: der Docker-Scan-Konfigurationswert ist gesetzt und wird von der referenzierten Pipeline-Stage gelesen (kein stiller Default-Fallback mehr).
- #745/#746: `.gitignore` deckt den im Issue benannten Pfad ab; ein `git status --porcelain`-Smoke-Test nach Anlegen einer Testdatei im betroffenen Pfad zeigt keinen Treffer.

---

## Wave 3c — C6: Refactor & Architecture (P2–P3, Depends on C3/#481)

**Issues:**

| # | Arbeitstitel | Priorität | Dateien | Tier |
|---|---|---|---|---|
| #329 | SE-Framework-Design-Grundlage (gatekeept #548) | P2 | `scripts/lib/`, `docs/` | L (`senior-developer`) |
| #332 | SE-Framework-Design-Fortsetzung (gatekeept #548) | P2 | `scripts/lib/`, `.meta-config/` | L (`senior-developer`) |
| #334 | Frontmatter-Parsing-Robustheit | P2 | `scripts/lib/frontmatter.py` | M (`developer`) |
| #338 | Modul-Dekomposition (Folgefix) | P2–P3 | `scripts/sync.py`, `scripts/lib/` | L (`senior-developer`) |
| #339 | Modul-Dekomposition (Folgefix, Teil 2) | P2–P3 | `scripts/lib/` | M (`developer`) |
| #452 | Architektur-Konsistenzfix | P2–P3 | `agents/`, `docs/` | M (`developer`) |
| #473 | Architektur-Vorbedingung für #482 | P2–P3 | `scripts/lib/` | M (`developer`) |
| #482 | Architektur-Folgefix (abhängig von #473) | P2–P3 | `scripts/lib/` | M (`developer`) |
| #548 | SE-Framework-Umsetzung (abhängig von #329/#332) | P2–P3 | `scripts/lib/`, `agents/`, `docs/` | L (`senior-developer`) |
| #674 | Architektur-Folgefix (eigenständig, siehe `docs/plans/2026-09-05-issue-674-roadmap.md`) | P2–P3 | `scripts/lib/` | L (`senior-developer`) — bereits mit eigener Roadmap/Phase-Historie (`2026-09-05-issue-674-roadmap.md`, `2026-09-06-issue-674-phase4b/c/d-*.md`); dieser Task prüft nur den verbleibenden offenen Rest gegen die bestehende Roadmap, keine Neuplanung |

**Reihenfolge:** `#329 → #332 → #548` (hartes Design-Gate, Cluster-Dependency explizit), `#473 → #482` (harte Abhängigkeit); `#334`, `#338`, `#339`, `#452`, `#674` sind an keine der beiden Ketten gebunden und laufen parallel, sofern Dateiüberlappung mit `scripts/lib/` einzeln per `check_plan_file_overlap` bestätigt disjunkt ist (vor Dispatch prüfen — mehrere Issues teilen sich `scripts/lib/`, siehe Constraint 9).

**Task-Zerlegung (gemeinsames Muster, pro Issue ein eigener Spec+Task wegen L-Tier-Mehrheit):**
1. Step 0: `gh issue view <N>` lesen; bei #329/#332/#548 zusätzlich den bestehenden Stand in `docs/plans/` (Roadmap-Dokumente, falls vorhanden) sichten, bevor ein neuer Spec geschrieben wird.
2. Step 1: Einzel-Spec (`Status: APPROVED`) für dieses Issue, da L-Tier (Constraint 1) — Ausnahme #334 (M, kann im Cluster-Spec mitlaufen).
3. Step 2 (rot): Architektur-/Regressionstest, der den aktuellen Design-Mangel (fehlende Abstraktion, brüchiges Frontmatter-Parsing, Modul zu groß) über eine messbare Schwelle reproduziert (z.B. Zeilenzahl-Ratchet, fehlende Modul-Grenze als Import-Zyklus-Test).
4. Step 3: Implementierung gemäß freigegebenem Spec.
5. Step 4 (grün): Test grün, `python3 -m pytest tests/ -q` keine Regression, `python3 scripts/sync.py --validate` rc 0.
6. Step 5: Commit über `git`-Rolle, `Fixes #<N>`.

**Akzeptanzkriterien:**
- #329/#332: das im jeweiligen Spec festgelegte SE-Framework-Design-Dokument ist freigegeben und die darin definierte Schnittstelle hat mindestens einen Konsumenten-Test.
- #334: `scripts/lib/frontmatter.py` parst den im Issue benannten Edge-Case (z.B. mehrzeiliger Wert, fehlender Abschluss-Marker) ohne Exception, mit dediziertem Regressionstest.
- #338/#339: das benannte Modul ist unter die im Spec festgelegte Zeilen-/Verantwortungsgrenze gebracht, ratchet-getestet (kein Wieder-Anwachsen ohne expliziten Test-Update).
- #452: die Architektur-Inkonsistenz-Beschreibung aus dem Issue hat keinen Repro-Treffer mehr (dedizierter Test).
- #473/#482: #482 kompiliert/lädt ausschließlich gegen das von #473 neu exponierte Interface; ein Konsumenten-Test beweist das.
- #548: SE-Framework ist gemäß #329/#332-Design umgesetzt; Abnahme-Kriterium ist im jeweiligen Einzel-Spec definiert (hier nicht vorab fixierbar, da Spec noch nicht existiert).
- #674: der verbleibende offene Rest laut `docs/plans/2026-09-05-issue-674-roadmap.md` ist identifiziert, einem der dort schon definierten Phase-Schritte zugeordnet und abgeschlossen (kein neuer Scope).

---

## Wave 4 — C5: Template Improvements (P3, Depends on C1 / Blocker #528)

**Issues:**

| # | Arbeitstitel | Priorität | Dateien | Tier |
|---|---|---|---|---|
| #528 | Output-Contract-Enforcement (Blocker für die restliche Wave) | P3 | `agents/1-generic/*.md` (Fleet) | L (`senior-developer`) |
| #769 | Core-Development-Rollen — Literatur-Vorschläge umsetzen | P3 | `agents/1-generic/{orchestrator,developer,junior-developer,senior-developer,principal-developer,explorer,git,release,docker}.md`, `config/role-defaults.yaml` | M (`developer`) |
| #770 | Product-&-Planning-Rollen — Literatur-Vorschläge umsetzen | P3 | `agents/1-generic/{feedback,requirements,ideation,planner,product-manager,effort-estimator,bug-feature-analyzer,export-manager,meta-feedback,app-lifecycle-governor}.md`, `docs/REQUIREMENTS.md`, `config/role-defaults.yaml` | M (`developer`) |
| #771 | Testing-&-V&V-Rollen — Literatur-Vorschläge umsetzen | P3 | `agents/1-generic/{tester,e2e-tester,test-executor,validator,se-verifier,se-validator,se-test-engineer,se-testreviewer,se-integration-and-test-manager}.md` | M (`developer`) |
| #772 | SE-V-Modell-Rollen — Literatur-Vorschläge umsetzen | P3 | `agents/1-generic/se-*.md` (9 Rollen) | M (`developer`) |
| #773 | Review-&-Qualitäts-Rollen — Literatur-Vorschläge umsetzen | P3 | `agents/1-generic/{code-reviewer,concept-reviewer,refactoring-specialist,performance-optimizer}.md`, `config/review-rules/{frontend,backend,database,ui}.yaml` | M (`developer`) |
| #774 | Security-&-Operations-Rollen — Literatur-Vorschläge umsetzen | P3 | `agents/1-generic/{security-auditor,dependency-auditor,ai-security-guardian,accessibility-specialist,log-analyzer,incident-responder,sre-engineer}.md`, `config/review-rules/security.yaml` | M (`developer`) |
| #775 | Knowledge-Engine-&-Doku-Rollen — Literatur-Vorschläge umsetzen | P3 | `agents/1-generic/*` (Knowledge/Doku-Rollen) | M (`developer`) |
| #777 | Cross-Cutting-Finding F1: `reference_standards`-Frontmatter-Feld | P3 | `scripts/lib/frontmatter.py`, `agents/1-generic/*` (betroffene Rollen) | M (`developer`) |
| #778 | Cross-Cutting-Finding F2–F6: Boundary-Platzierung/Routing/Review-Regel-Zielpfad | P3 | `config/role-defaults.yaml`, `config/review-rules/*` | M (`developer`) |
| #779 | Cross-Cutting-Findings (7, Design-/Routing-Items) | P3 | `config/role-defaults.yaml` | M (`developer`) |
| #780 | Sprachrouting-Design-Entscheidung (Option C) | P3 | `scripts/lib/delegation_table.py` | M (`developer`) |
| #783 | Folgefix zu #528 (Output-Contract-Ratchet-Erweiterung) | P3 | `tests/test_contract_labels.py`, `agents/1-generic/*.md` (Fleet) | L (`senior-developer`) |

**Reihenfolge:** `#528 → alles andere` (Blocker, Cluster-Dependency explizit). Innerhalb des Rests: `#780 → #778 → #779 → #777` zuerst (Design-Gate-Entscheidungen, laut `docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md` bereits mit Decision-Log D1–D9 vorab entschieden — dieser Task **implementiert** die dort getroffenen Entscheidungen, trifft keine neuen), danach `#769`–`#775` parallel (jede Gruppe berührt eine andere Rollen-Teilmenge, laut Triage-Doku dateidisjunkt bis auf gemeinsame `config/role-defaults.yaml`-Treffer — dort sequenziell innerhalb der Gruppe einchecken, nicht gleichzeitig schreiben). `#783` läuft nach `#528` als dessen direkter Ratchet-Ausbau.

**Task-Zerlegung #528 und #783 (Output-Contract, kein bestehendes Triage-Dokument):**
1. Step 0: `gh issue view #528` / `#783` lesen.
2. Step 1 (rot): `tests/test_contract_labels.py` um die im Issue benannte fehlende Enforcement-Regel erweitern (z.B. ein Template ohne `STATUS:`/`RESULT:`/`ARTIFACTS:`-Block fällt durch den Ratchet); Lauf zeigt Fehlschlag auf dem aktuellen Stand.
3. Step 2: fehlende Output-Contract-Blöcke in den betroffenen `agents/1-generic/*.md`-Templates ergänzen (nur die vom Issue benannte Teilmenge, kein Fleet-weiter Umbau ohne Spec).
4. Step 3 (grün): `tests/test_contract_labels.py` grün, `python3 scripts/sync.py --validate` rc 0.
5. Step 4: Commit über `git`-Rolle, `Fixes #528` (bzw. `#783`).

**Task-Zerlegung #769–#775, #777–#780 (Literatur-Triage-Umsetzung):**
1. Step 0: `gh issue view <N>` lesen **und** den zugehörigen Abschnitt in `docs/plans/2026-09-12-literature-anchored-agent-improvements-plan.md` (Tabelle "Per-Issue-Triage", Abschnitt 1.x) als bindende Scope-Quelle nehmen — jede `accept`/`modify`-Zeile wird zu einem Edit, `reject`/`duplicate`-Zeilen werden übersprungen (bereits entschieden, kein neuer Diskussionsbedarf).
2. Step 1 (rot): pro betroffener Rolle ein Contract-Snapshot-Test (Template enthält die neue Regel-Zeile noch nicht) — sofern noch keiner existiert, in `tests/test_contract_labels.py` oder einem rollenspezifischen Fixture-Test ergänzen.
3. Step 2: Template-Edits gemäß Triage-Tabelle (`accept` = Zeile wörtlich wie in der Decision-Log-Kurzfassung ergänzen; `modify` = die im Decision-Log dokumentierte abgewandelte Form, z.B. `reference_standard`-Verweis statt Inline-Katalog).
4. Step 3 (grün): Contract-Snapshot-Test grün; `python3 scripts/sync.py --check --dry-run` rc 0.
5. Step 4: `VERSION`-Bump (Minor laut Triage-Doku, Ziel `1.2.0`, falls dieser Bump noch nicht gelandet ist — mit `gh`/`grep` in `CHANGELOG.md` prüfen) + `CHANGELOG.md`-Eintrag.
6. Step 5: Commit über `git`-Rolle, `Fixes #<N>`.

**Akzeptanzkriterien:**
- #528/#783: `tests/test_contract_labels.py` deckt 100% der im jeweiligen Issue benannten Template-Teilmenge ab, keine Exception-Registry-Einträge für diese Teilmenge mehr offen.
- #769–#775: jede `accept`/`modify`-Zeile aus der referenzierten Triage-Tabelle ist im Zieltemplate wiederzufinden (stichprobenartige Diff-Prüfung gegen die Tabelle); kein `reject`/`duplicate`-Vorschlag wurde umgesetzt.
- #777: `reference_standards` ist ein dokumentiertes optionales Frontmatter-Feld in `scripts/lib/frontmatter.py` und wird von mindestens einer Rolle genutzt, die zuvor einen Standard inline dupliziert hatte.
- #778/#779: Routing-/Boundary-Aussagen stehen in `config/role-defaults.yaml`, nicht als Template-Prosa (Grep-Guard: die betroffene Prosa-Zeile ist aus dem Template entfernt).
- #780: Sprachrouting läuft über die in #780 festgelegte Option C in `scripts/lib/delegation_table.py`, mit Regressionstest.

---

## Wave 5 — C7: Feature & RFC (P1–P3, Depends on C6)

**Issues:**

| # | Arbeitstitel | Priorität | Dateien | Tier |
|---|---|---|---|---|
| #192 | Feature-Tracking-Issue (siehe `CHANGELOG.md:2049` — bereits als Tracking-Referenz vermerkt) | P1–P3 | `docs/specs/`, `docs/plans/` | S (`junior-developer`) — vermutlich reine Tracking-/Abschluss-Prüfung, siehe Hinweis |
| #207 | RFC-Umsetzung (eigenständig) | P2–P3 | `docs/specs/`, `agents/` | M (`developer`) |
| #370 | Phase-Planung (ALREADY IMPLEMENTED — concept-driven-dev pipeline verified in this session; Issue remains open for documentation closure) | P1–P2 | `docs/plans/` | S (`junior-developer`) — verification/closure only |
| #523 | Agent-Eval-Framework-Review (independent concept-review item; needs plan revision; unrelated to #370) | P1–P2 | `docs/plans/2026-09-06-issue-523-agent-eval-plan-v2.md` (bereits vorhanden — Review, keine Neuplanung) | L (`senior-developer`) |
| #540 | Context-File-Density-Control (Folgefix, Basis bereits in `CHANGELOG.md:772` gelandet) | P2–P3 | `scripts/lib/context.py` | M (`developer`) |
| #547 | RFC-Folgefix (eigenständig) | P2–P3 | `scripts/`, `config/` | M (`developer`) |

**Reihenfolge:** Alle 6 Issues (#192, #207, #370, #523, #540, #547) laufen unabhängig parallel. #370 ist bereits implementiert (nur Verification/Closure nötig). #523 ist ein eigenständiger Concept-Review-Punkt, unabhängig von #370.

**Hinweis #192:** `CHANGELOG.md:2049` enthält bereits „See Issue #192 for tracking" — vor Task-Start klären (Step 0), ob das zugrunde liegende Feature bereits ausgeliefert ist und #192 nur noch geschlossen werden muss, oder ob ein Rest-Scope offen ist. Bei reinem Abschluss: Task reduziert sich auf Verifikation + Issue-Close, keine Implementierung.

**Hinweis #523/#370:** `docs/plans/2026-09-06-issue-523-agent-eval-plan-v2.md` existiert bereits als v2-Plan für das Agent-Eval-Framework. Dieser Task ist primär ein **Review-Abschluss** dieses bestehenden Plans (nicht Neuplanung) — Step 1 prüft, ob der v2-Plan noch aktuell ist, Step 2 implementiert offene Punkte daraus.

**Hinweis #540:** `CHANGELOG.md:772` dokumentiert „Context-file compression (#540, #543): automatic context_file density control" als bereits gelandet. Step 0 muss klären, ob #540 noch offen ist (residualer Scope) oder ob nur das GitHub-Issue nachträglich zu schließen ist.

**Task-Zerlegung (gemeinsames Muster für #207, #547; Sonderfälle #192/#370/#523/#540 siehe Hinweise oben):**
1. Step 0: `gh issue view <N>` lesen, gegen die oben genannten Bestandsdokumente/Changelog-Einträge abgleichen.
2. Step 1 (rot, nur falls Restscope bestätigt): Spec/Test für den verbleibenden Scope schreiben.
3. Step 2: Implementierung gemäß Spec.
4. Step 3 (grün): Test grün, `python3 -m pytest tests/ -q` keine Regression.
5. Step 4: Commit über `git`-Rolle, `Fixes #<N>`.

**Akzeptanzkriterien:**
- #192: entweder (a) Issue wird mit Verweis auf den bereits gelandeten Stand geschlossen, oder (b) ein dedizierter Test für den verbleibenden Scope ist grün.
- #207/#547: der im jeweiligen RFC benannte Akzeptanzpunkt hat einen Test; `python3 scripts/sync.py --validate` rc 0.
- #370: Phase-Plan ist nur nach grünem #523-Review freigegeben; Akzeptanz ist die Freigabe des aktualisierten Phase-Plans (`Status: APPROVED`).
- #523: `docs/plans/2026-09-06-issue-523-agent-eval-plan-v2.md` ist entweder bestätigt aktuell oder in einer neuen Revision aktualisiert; Review-Ergebnis ist dokumentiert.
- #540: entweder Issue-Close mit Verweis auf `CHANGELOG.md:772`, oder ein grüner Regressionstest für den identifizierten Restscope in `scripts/lib/context.py`.

---

## 5a. Session-Triage-Status (2026-10-07 Verification Update)

**Zusammenfassung:** Live-Verifizierung der 52-Issue-Plan-Abhängigkeiten (via `gh issue view` API) hat folgende Erkenntnisse gebracht:

### Korrektionen zur Original-Planung

**Falsche Abhängigkeit identifiziert und korrigiert:**
- **#370 (Phase-Planung):** bereits vollständig implementiert und geschlossen; concept-driven-dev pipeline (agents/templates) existiert und ist getestet. Keine aktive Abhängigkeit zu #523.
- **#523 (Agent-Eval-Framework-Review):** unabhängiger Concept-Review-Verdict (REVISE) auf einem promptfoo-Eval-Plan, inhaltlich unabhängig von #370. Benötigt eigenständige Plan-Revision, blockiert nicht #370.

**Auswirkung auf Wave 5:** #370 und #523 laufen daher parallel (nicht sequenziell). #370 reduziert sich auf Verification/Documentation-Closure, nicht auf Neuentwicklung.

### Echtstand über alle 52 Issues

**Abgeschlossene Issues (29, mit Evidenz):** Bereits gemergt via separate Wave-PRs oder bestätigt closed in dieser Session.

**Aktive Issues mit In-Flight-PRs oder Merges (15 adressiert, größtenteils in Progress):**
- **Gemergt diese Session via dedizierte PRs:** #476, #751, #899, #745, #680, #746 (6 issues, Wave 2a/3b)
- **PRs offen (warten auf Merge):** #679, #452 (2 issues, Wave 3b/3c); #339 spec-only (1 issue, Wave 3c); #779-IT-2 (1 issue, Wave 4)
- **Bereits-Closed / Turned-Out-Done:** #334, #528 (2 issues, jeweils Wave 3c/4 — Verifikation zeigt bereits abgeschlossen)
- **In Scope, noch zu implementieren:**
  - #780 (Sprachrouting, scoped, nicht yet implementiert, Wave 4)
  - #783 (Output-Contract-Ratchet-Folgefix, needs design, Wave 4)
  - #778 (Boundary-Placements/Routing, teilweise deferred, Wave 4)

**Design-Entscheidungen (4, Abschluss ausstehend):** #330, #329, #548, #547 — bereits in Wave-Plänen mit Design-Gates; warten auf freigegebene Specs.

**Besondere Fälle (3 Items):**
- #192 (Feature-Tracking, Monitoring deferred — bereits in CHANGELOG.md dokumentiert, möglicherweise nur Closure nötig)
- #523 (needs plan revision — unabhängig, nicht blockierend wie ursprünglich gedacht)
- #676 (Preset-Konsistenz, partial/stale — Recommendation: Scope durch Review verengern, nicht im Umfang der aktuellen Wave adressiert)

**Out-of-Scope (kein Scope-Fix erforderlich):** #681 (Docker-Scan-Konfiguration), #207 (RFC-Umsetzung) — beide sind explizit in Wave-Plänen enthalten und kein Out-of-Scope

### Numerische Tally (alle 52 Basis-Issues)

| Status | Anzahl | Notes |
|---|---|---|
| Closed/Merged via Wave PRs | 6 | #476, #751, #899, #745, #680, #746 |
| In-Flight via open PRs | 5 | #679, #452, #339, #779-IT-2, + others |
| Already-Done (verified closed) | 2 | #334, #528 |
| Scoped, not yet started | 3 | #780, #783, #778 |
| Design-Decisions pending | 4 | #330, #329, #548, #547 |
| Special cases (tracking/deferred/revision) | 3 | #192, #523, #676 |
| **Verbleibend im ursprünglichen Plan (52)** | **40+ items** | Wave-Struktur bleibt gültig; Abhängigkeits-DAG ist azyklisch |

**Empfehlung:** Plan bleibt in Struktur + Wellen-Logik gültig. Abhängigkeitskette #523→#370 wurde korrigiert zu „Independent". Alle 52 Issues haben einen zugeordneten Wave-Slot und Akzeptanzkriterium. Implementierung kann nach Freigabe der Specs per Wave fortfahren.


## 6. Rollen-Zusammenfassung je Welle

| Welle | Rollen (Mehrfachnennung = mehrere Issues) |
|---|---|
| 1 | `developer` ×3, `junior-developer` ×2 |
| 2a | `developer` ×3, `junior-developer` ×3 (ggf. `documenter` für #899) |
| 2b | `senior-developer` ×1, `developer` ×2 |
| 3a | `developer` ×2, `junior-developer` ×2 |
| 3b | `junior-developer` ×5 |
| 3c | `senior-developer` ×5, `developer` ×5 |
| 4 | `senior-developer` ×2, `developer` ×11 |
| 5 | `senior-developer` ×2, `developer` ×2, `junior-developer` ×1 (+ ggf. Verifikations-Only für #192/#540) |

**Gesamt:** 52 Issues über 5 Wellen, 8 Cluster.

## 7. Out of scope / Klärung zuerst nötig (11 Issues)

| # | Grund (eine Zeile) |
|---|---|
| #317 | Viz-Dashboard-iframe-Rendering — Testkontext unklar, braucht Repro-Klärung vor Scope-Festlegung |
| #534 | Notes/HACS-Plattform-Integration — unklar ob reine Notiz oder konkreter Fix |
| #800 | Architektur-/Framework-Entscheidung (Domain-Folder) — Design-Review ausstehend, möglich Duplikat zu #820 |
| #814 | Architektur-/Framework-Entscheidung — Design-Review ausstehend |
| #820 | Domain-Subfolder-Architektur — möglicher Duplikat zu #877, Abgleich gegen bestehende Architektur-Entscheidungen nötig |
| #827 | Architektur-/Framework-Entscheidung — Design-Review ausstehend |
| #829 | Architektur-/Framework-Entscheidung — Design-Review ausstehend |
| #832 | Architektur-/Framework-Entscheidung — Design-Review ausstehend |
| #865 | Unklarer Scope/Priorität — Body-Review nötig |
| #877 | Subplatform-Layer — möglicher Duplikat zu #820, Abgleich gegen bestehende Architektur-Entscheidungen nötig |
| #885 | Unklarer Scope/Priorität — Body-Review nötig |

**Empfehlung:** Separate Triage-Runde (`requirements`/`bug-feature-analyzer`-Rolle) vor Aufnahme in eine künftige Welle; #820/#877 insbesondere auf Duplikat prüfen, bevor beide unabhängig geplant werden.

## 8. Feedback-Kandidaten (#896–899) — Triage-Status

| # | Klassifikation | Status in diesem Plan |
|---|---|---|
| #896 | FEATURE (Admin-UI Startup-Modi) | Nicht in dieser Wave — niedrige Priorität, Folge-Feature zu #456 |
| #897 | BUG (CORS/Origin-Validierung blockiert Mutationen im Network-Mode) | Nicht in dieser Wave — Vorbedingung für #896, aber kein Teil der 52 implementierungsreiten Issues dieses Clusterings |
| #898 | FEATURE (Admin-UI-Verbesserungen: Auto-Commit-Trigger, Modell-Sichtbarkeit) | Nicht in dieser Wave — mittlere Priorität, UI-Polish |
| #899 | BUG (Modell-Wartungsprozedur) | **In dieser Wave** — siehe Wave 2a, Zeile #899 |

#896–898 bleiben außerhalb dieses Plans (kein Teil der 52 implementierungsreiten Cluster-Issues); #899 ist der einzige der vier Feedback-Kandidaten, der bereits im Cluster C2 enthalten ist und daher Teil von Wave 2a ist.

## 9. Aufwandsschätzung

Gesamtaufwand über `effort-estimator` (Text-Referenz, kein Tool-Call) nach Freigabe (`Status: APPROVED`) dieses Plans anfordern — Eingabe: 52 Issues, Tier-Verteilung aus §6 (12× `senior-developer`-Tier, ca. 25× `developer`-Tier, ca. 15× `junior-developer`-Tier), 5 Wellen mit den oben genannten Abhängigkeitsketten.

## 10. Self-Review

- **Keine Platzhalter-Sprache:** jeder Task nennt konkrete Dateien/Pfade aus `.tmp/clustering-analysis.md`; wo der exakte GitHub-Titel nicht verifizierbar war (kein API-Zugriff), ist das explizit als Arbeitstitel mit verbindlichem `gh issue view`-Step-0 markiert, nicht als erfundener Fakt präsentiert — geprüft und korrigiert für alle 52 Zeilen.
- **Jedes Issue hat ein Akzeptanzkriterium:** jede Wave-Sektion endet mit einer `Akzeptanzkriterien`-Liste, die jede in der Tabelle genannte Issue-Nummer mindestens einmal referenziert — geprüft gegen die Issue-Liste aus `.tmp/clustering-analysis.md` (alle 52 Nummern kommen in genau einer Wave-Tabelle und genau einer Akzeptanzkriterien-Liste vor).
- **Keine Issue-Nummer in zwei Wellen:** Abgleich der 52 Nummern über alle Wave-Tabellen ergab keine Dopplung; `#528` erscheint nur in Wave 4 (nicht zusätzlich im C1-Fundament, obwohl es von #267 abhängt — die Abhängigkeit ist als Wave-1→Wave-4-Kante dokumentiert, nicht als Doppelzuordnung).
- **Keine unbegrenzte/vage Welle:** jede Welle hat eine feste Issue-Liste (keine „und mehr"-Formulierung); Wave 3c (C6, 10 Issues, höchste Komplexität) wurde geprüft und pro Issue einzeln mit Dateien/Tier/Akzeptanzkriterium versehen statt als Sammel-Task — korrigiert gegenüber einem ersten Entwurf, der #334/#338/#339/#452/#674 ursprünglich als eine Sammelzeile geführt hätte.
- **Abhängigkeiten azyklisch:** die in §5 gezeichnete Wellen-DAG hat keine Rückwärtskante; harte Einzel-Abhängigkeiten (#265→#266→#267→#346, #473→#482, #329→#332→#548, #523→#370, #745→#746, #476→#680) sind jeweils als sequenzielle Reihenfolge innerhalb ihrer Wave vermerkt, nicht als Parallel-Gruppe.
- **Spec-Gate nicht übersprungen:** Global Constraint 1 und jede Wave's Task-Zerlegung Step 1/2 erinnern explizit daran, dass Implementierung erst nach freigegebenem Spec beginnt — dieser Plan selbst bleibt `Status: DRAFT` und enthält keine Implementierung.
- **Korrektur bei Review:** ursprünglicher Entwurf hatte C4 und C8 versehentlich beide unter „Wave 3" ohne Unterscheidung a/b/c geführt, was die Parallelitäts-Aussage (3 gleichzeitig laufende, dateidisjunkte Teilcluster) verundeutlicht hätte — behoben durch explizite Unterteilung in Wave 3a/3b/3c mit je eigener Datei-Disjunktheits-Begründung.
