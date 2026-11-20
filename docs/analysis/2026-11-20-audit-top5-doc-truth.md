---
kind: audit
date: 2026-11-20
title: "DOCUMENTATION-TRUTH Audit — Roadmap PR 0.5 / P32 (Stufe A)"
req: "PR 0.5 / P32 / E-06"
status: done
---

# DOCUMENTATION-TRUTH Audit — Roadmap PR 0.5 / P32 (Stufe A)

> **Zweck:** Read-only Prüfung, ob die dokumentierten Behauptungen der Kern-Dokumente mit
> Code/Konfiguration übereinstimmen („Doku-Wahrheit", Teil von Audit-Top5 Task 4,
> #1245/#1159). Der Bericht ist Grundlage für die Stufe-A-Berichterstattung per PR.
> **Scope:** `README.md`, `AGENTS.md`, `CLAUDE.md`, `docs/INDEX.md`,
> `docs/REQUIREMENTS.md` (nur lesend), `docs/plans/README.md`, `docs/CODEBASE_OVERVIEW.md`.
> **Datenquelle:** direkte Lese-/Glob-/Grep-Zugriffe auf die Arbeitskopie am 2026-11-20;
> Branch `chore/audit-top5-reports` (via `.git/HEAD` verifiziert). Abgleich gegen
> `VERSION`, `.meta-config/project.yaml`, `config/*.yaml`, `scripts/lib/*.py`,
> `.github/workflows/`, sowie echte Verzeichnis-/Dateilisten. Keine externen Quellen.
> **Stand:** 2026-11-20 · **Branch:** `chore/audit-top5-reports` · **Seite 1 von 1.**
> **Einschränkung:** Kein Voll-Testlauf (Gate G1 bewusst ausgesetzt, User-Entscheid vom
> 2026-11-20). Kein `git`-Befehl ausgeführt — der Branch wurde ausschließlich über
> `.git/HEAD` gelesen; die Commit-ID `94a740c5` konnte daher nicht gegen den Ref geprüft
> werden. Befunde sind statische Dokument-/Code-Abgleiche, keine Laufzeit-Validierung.

## Legende

| Marker | Bedeutung |
|---|---|
| **HIGH** | Falsche Behauptung in einem zentralen, extern oder steuernd wirkenden Dokument; direktes Korrektur-Erfordernis. |
| **MEDIUM** | Falsche oder veraltete Behauptung mit realem Irreführungs-/Findbarkeitspotenzial. |
| **LOW** | Unvollständigkeit, veraltetes Datum oder Formulierungsspielraum ohne akuten Schaden. |
| **CONFIRMED FALSE** | Widerspruch durch gelesene Datei/Dateiliste belegt. |
| **NEEDS OWNER DECISION** | Normative/interpretative Differenz; Korrektur erfordert Freigabe des jeweiligen Owners. |

---

## 1. Befunde (priorisiert)

### 1.1 HIGH

**F-01 — `README.md:208` dokumentiert eine unvollständige `rules-preset`-Wertemenge;
der aktive Wert `lazy` fehlt. — CONFIRMED FALSE**
- Behauptung: `| rules-preset | default, minimal, silent | Which rules are active |`.
- Realität: `config/rules-presets.yaml` definiert vier Presets — `default` (Z.51),
  `minimal` (Z.55), `silent` (Z.74), `lazy` (Z.110). `.meta-config/project.yaml:16` setzt
  `rules-preset: lazy`. Das eigene Projekt nutzt also einen Wert, den die externe
  Referenz nicht auflistet.
- Wirkung: Leser`/`Integratoren können `lazy` nicht aus der README ableiten; die Tabelle
  wirkt abschließend („Common top-level keys", Spalte „Values / type").

**F-02 — `docs/CODEBASE_OVERVIEW.md` Knowledge-Engine-Konfigurationsbeispiel ist
falsch (Key-Syntax und Pfad). — CONFIRMED FALSE**
- Behauptung: `bundle_path: docs/knowledge` (Z.1793, Beispielblock), `bundle_init_template`
  (Z.1794) und Baumwurzel `docs/knowledge/` (Z.1822).
- Realität: der Konfigurations-Key ist `bundle-path` (Bindestrich) mit Default `knowledge`
  (`scripts/lib/knowledge.py:136`), gesetzt als `knowledge-engine.bundle-path: knowledge`
  in `.meta-config/project.yaml:22`. `README.md:624` und `CLAUDE.md:82` nennen ebenfalls
  `knowledge/`. Ein `bundle_init_template`-Key existiert in der aktuellen Konfiguration
  nicht.
- Wirkung: Das Kopieren des Beispiels erzeugt eine ungültige/unwirksame Konfiguration;
  ausgerechnet die „code-accurate inventory" ist hier inkorrekt.

**F-03 — `docs/CODEBASE_OVERVIEW.md:3` veralteter Aktualisierungsstand mit mehreren
nachweislich toten Symbol-/Dateireferenzen. — CONFIRMED FALSE**
- Behauptung: „Letzte Aktualisierung: 2026-09-11" (über 2 Monate alt).
- Belege im selben Dokument:
  - `§1.1` beschreibt `agents/1-generic/se-orchestrator.md` („deprecated") samt
    Frontmatter/Version 1.1.0 (Z.33–44). Die Datei existiert nicht
    (`glob **/se-orchestrator.md` → keine Treffer).
  - `§14.2` nennt `scripts/lib/delegation_table.py:generate_intent_routing_table()`
    (Z.1809). Tatsächlich existiert `get_intent_routing_table` (`delegation_table.py:437`,
    importiert in `scripts/lib/config.py:86`); einen `generate_*`-Symbol gibt es nicht.
  - `§14.2` Domain-Tabelle (Z.1799–1805) listet 5 Domains; die aktive und in
    `docs/ui/admin-ui.html:4498,4527` geführte Domain `internal-docs` fehlt
    (`.meta-config/project.yaml:21` setzt `domain: internal-docs`).
- Wirkung: Die Datei ist der zentrale Code-Inventar; veraltete Pfade/Symbole untergraben
  genau den Zweck des Audits („Doku-Wahrheit").

### 1.2 MEDIUM

**F-04 — `docs/INDEX.md:5` veralteter Stand und unvollständiger Fallback-Index. —
CONFIRMED FALSE (Staleness)**
- Behauptung: „Stand: 2026-11-15 — 375 Dateien unter `docs/`, davon 366
  Markdown-Dateien." Das Dokument ist laut Z.3 Fallback-Index für
  `spec-plan-workflow`.
- Realität: `grep` nach `2026-11-16|17|18|19|20` in `docs/INDEX.md` → keine Treffer,
  während die Dateiliste solche Dateien enthält, u.a.
  `docs/plans/2026-11-16-bug-backlog-working-plan.md`,
  `docs/plans/2026-11-17-issue-hygiene-beleg.md`,
  `docs/plans/2026-11-18-1300-speech-mode-embed-channel.md`,
  `docs/plans/2026-11-19-worker-control-capability-plan.md`,
  `docs/specs/2026-11-19-worker-control-capability-spec.md`,
  `docs/specs/2026-11-20-agent-improvement-loop-batch0-spec.md`,
  `docs/specs/2026-11-20-p10-orchestration-checks-spec.md`,
  `docs/reviews/2026-11-20-agent-loop-batch0-spec-review.md`. Der Zählerstand ist
  dadurch zwingend überholt (exakte Neuzählung: siehe F-10).

**F-05 — `docs/INDEX.md:24,28–61` Zählражение `analysis (29)` lässt den
`runbooks`-Bereich aus. — CONFIRMED FALSE**
- Behauptung: 20 Dateien in der `analysis`-Tabelle + 9 in `analysis/evidence` = 29.
- Realität: zusätzlich existiert `docs/analysis/runbooks/antigravity-runtime-probe.md`;
  `grep` nach `runbook` in `docs/INDEX.md` → keine Treffer. Tatsächlich 30 Markdown-Dateien
  unter `docs/analysis/`. Das Unterverzeichnis wird weder gezählt noch erwähnt.

**F-06 — `docs/INDEX.md:421` falsche Dateianzahl für `howto/`. — CONFIRMED FALSE**
- Behauptung: `| howto/ | 1 | Anleitungen |`.
- Realität: `docs/howto/` enthält 2 Markdown-Dateien: `rebaseline.md` und
  `admin-ui-remote-access.md` (letztere wird übrigens von `README.md:588` verlinkt).

**F-07 — `docs/plans/README.md:5–7` beschreibt Archivierung als automatisch, während
die Konfiguration eine Freigabe verlangt. — NEEDS OWNER DECISION**
- Behauptung: abgeschlossene Reports wandern „sobald sie erledigt sind" nach
  `docs/plans/archive/`.
- Realität: `.meta-config/project.yaml:77` setzt `archive.mode: ask`; `Z.76` setzt
  `index.mode: knowledge-engine`. Nach der Rollenregel liegt die Archiv-/Index-Route bei
  `knowledge-ingestor`, während `Z.78` `archive.agent: documenter` konfiguriert.
  Die Doku verschweigt sowohl den `ask`-Gate als auch die Agenten-/Modus-Abhängigkeit.
- Einordnung: interpretativ, da die README eine Konvention und die Config das konkrete
  Verfahren beschreibt; Korrektur durch Owner (Doku/Config) erforderlich.

### 1.3 LOW

**F-08 — `README.md:696` CI-Workflow-Liste unvollständig. — CONFIRMED FALSE
(Unvollständigkeit)**
- Behauptung: „CI workflows: `.github/workflows/validate.yml` …,
  `.github/workflows/orchestration-test.yml` …, and `.github/workflows/release-gate.yml` …".
- Realität: `.github/workflows/` enthält zusätzlich `scorecard.yml`. Die drei genannten
  Angaben selbst stimmen (`validate.yml:86` `SCENARIO_PROFILE: … 'dev' … 'release'`;
  `orchestration-test.yml:210` Python 3.9/3.12).

**F-09 — `README.md:522–523` „full (default, no rule)" bei vorhandener Datei. —
NEEDS OWNER DECISION**
- Behauptung: „One rule file per mode in `speech/`: full (default, no rule), …".
- Realität: `speech/full.md` existiert (Inhalt: „No rule is generated for this mode").
  Die Klammer ist verhaltens-, nicht dateibezogen gemeint; die Formulierung „one rule
  file per mode" ist jedoch wörtlich falsch. 9 Modi ↔ 9 Dateien stimmen ansonsten.

**F-10 — `docs/INDEX.md:5` exakte Zähler nicht nachprüfbar; Neuzählung erforderlich. —
NEEDS OWNER DECISION**
- Die Zahlen 375/366 sind mit Stand 2026-11-15 markiert und durch F-04–F-06 als überholt
  belegt. Eine belastbare aktuelle Gesamtzahl wurde in diesem Read-only-Durchgang nicht
  ermittelt (kein Shell-Zugriff verfügbar). Empfehlung: Zählung im Owner-Durchgang
  erneuern, nicht raten.

**F-11 — `docs/REQUIREMENTS.md:13` REQ-CMD-01 nennt nicht vorhandene Verzeichnisse. —
NEEDS OWNER DECISION (Owner: `requirements`)**
- Behauptung: Vier-Schichten-Modell „mit den Verzeichnissen `commands/0-external/`,
  `commands/1-generic/` und `commands/2-platform/`".
- Realität: `commands/` enthält physisch nur `1-generic/`. `scripts/lib/commands.py:77,89`
  liest `0-external`/`2-platform` als optionale Quellen ein (fehlen → still übersprungen).
  Die REQ ist normativ formuliert; ob die leeren Schichten als „vorhanden" gelten,
  entscheidet der Requirements-Owner. `docs/REQUIREMENTS.md` wurde **nicht** bearbeitet.

**F-12 — Positivbefund (kein Handlungsbedarf, dokumentiert zur Abgrenzung).**
Folgende zentrale Behauptungen wurden geprüft und stimmen überein: `VERSION` =
`2.0.0-beta.9` = Badge/Text in `README.md:3,41` und Generation-Version in
`CLAUDE.md:6,74` / `AGENTS.md:47`; DoD/REQ-Trace/Tests/Codebase-Overview/Security-Audit
in `CLAUDE.md:75` entsprechen `rapid-prototyping` in `config/dod-presets.yaml:56–72`;
Provider-Tabelle (`README.md:234–244`) entspricht `has_hooks`/`context_file`/`agents_dir`
in `config/ai-providers.yaml`; 24 Slash-Commands (`README.md:634`) = 24 Dateien in
`commands/1-generic/`; 7 DoD-Presets (`README.md:456–464`) = `config/dod-presets.yaml`;
3 Conventions-Presets (`README.md:474–480`) = `config/conventions-presets.yaml`;
Plattform-Override-Tabelle (`README.md:288–293`) = 18 Dateien in `agents/2-platform/`;
`docs/INDEX.md:419–428` Verzeichniszahlen `architecture/`, `conclusions/`, `issues/`,
`providers/`, `se-cascade/`, `spikes/`, `ui/` stimmen mit den Dateilisten überein.

---

## 2. Priorisierte Remediation

| Prio | Befund | Maßnahme | Owner (Vorschlag) | Klasse |
|---|---|---|---|---|
| 1 | F-01 | `rules-preset`-Zeile in `README.md:208` um `lazy` ergänzen (Wertemenge aus `config/rules-presets.yaml`). | documenter (README) | CONFIRMED FALSE |
| 2 | F-02 | CODEBASE_OVERVIEW §14 auf `bundle-path`/`knowledge` korrigieren; `bundle_init_template` entfernen oder als nicht existent markieren. | documenter | CONFIRMED FALSE |
| 3 | F-03 | CODEBASE_OVERVIEW Header-Datum erneuern; `se-orchestrator.md`-Eintrag löschen/archivieren; `get_intent_routing_table` korrigieren; `internal-docs` in Domain-Tabelle ergänzen. | documenter | CONFIRMED FALSE |
| 4 | F-04 | `docs/INDEX.md` neu standsetzen: Datum, Gesamtzahlen und alle Dateien ab 2026-11-16 nachtragen. | documenter / knowledge-indexer | CONFIRMED FALSE |
| 5 | F-05, F-06 | `analysis`-Zahl auf 30 korrigieren und `runbooks/`-Sektion ergänzen; `howto/` auf 2 korrigieren. | documenter / knowledge-indexer | CONFIRMED FALSE |
| 6 | F-07 | Archivierungsregel in `docs/plans/README.md` mit `archive.mode: ask` und `index.mode`/`archive.agent` in Einklang bringen. | Owner Doku/Config | NEEDS OWNER DECISION |
| 7 | F-08, F-09 | `scorecard.yml` in README-CI-Liste ergänzen; Formulierung „one rule file per mode" präzisieren. | documenter (README) | teils CONFIRMED, teils DECISION |
| 8 | F-10, F-11 | Exakte Zählung erneuern; REQ-CMD-01 mit `requirements`-Owner klären — **keine** Änderung an `docs/REQUIREMENTS.md` durch dieses Audit. | requirements / documenter | NEEDS OWNER DECISION |

**Reihenfolge-Begründung:** F-01–F-03 betreffen extern bzw. steuernd gelesene Dokumente
mit nachweislich falschen Werten → vor allen Zähl-/Strukturkorrekturen. F-04–F-06 sind
mechanisch, aber der Fallback-Index ist laufzeitrelevant für `spec-plan-workflow`.
F-07–F-11 benötigen Owner-Freigabe bzw. sind kosmetisch.

---

## 3. Confirmation / Abgrenzung

- **Einzige geänderte Datei:** `docs/analysis/2026-11-20-audit-top5-doc-truth.md`
  (dieser Bericht). Keine anderen Docs, keine Config, kein Code, keine Issues, keine
  Worker-Control-/Master-Roadmap-/Batch0-Spec-/Review- oder archivierten Pläne berührt.
- **Kein Voll-Testlauf:** Gate G1 gemäß USER 2026-11-20 ausgesetzt; keine `sync.py`,
  kein `pytest`, keine Validierung ausgeführt.
- **Keine `git`-Aktion:** kein Commit, Push, PR, Tag, Branchwechsel oder Worktree.
- **Keine verbotenen MCP-Tools**, kein Isolation-/Worktree-Flag verwendet.
- **Lesende Ausnahme respektiert:** `docs/REQUIREMENTS.md` und `knowledge/schema.md`
  wurden nicht verändert (F-11 nur als Befund an den Owner).
- **Abdeckung (explizit):** geprüft wurden die in „Scope" genannten Dateien vollständig
  bzw. die in F-01–F-12 zitierten Abschnitte. **Nicht** geprüft: Wiki-Inhalte unter
  `knowledge/wiki/`, Laufzeitverhalten der Provider, Vollständigkeit der
  `superpowers/`-Artefakte (42 laut INDEX, nicht einzeln verifiziert), sowie die
  exakten Gesamtzahlen in F-10.
- **Versionshygiene:** Befunde beziehen sich auf den Arbeitskopie-Stand 2026-11-20,
  VERSION `2.0.0-beta.9`, Branch `chore/audit-top5-reports`. Eine Review-Freigabe liegt
  nicht vor; dieser Bericht ist `STATUS: done` für die Erstellung, nicht abgenommen.

---

STATUS: done
RESULT: DOCUMENTATION-TRUTH-Audit (PR 0.5 / P32, Stufe A) erstellt; 12 Befunde, davon 3 HIGH (README `rules-preset` ohne `lazy`; CODEBASE_OVERVIEW falscher Knowledge-Engine-Key/Pfad und tote Symbol-/Dateireferenzen), 4 MEDIUM (veralteter/unvollständiger `docs/INDEX.md`), 5 LOW/Decision. Kein Voll-Testlauf (G1 ausgesetzt); keine weiteren Dateien geändert. Nächster Schritt: Owner-Freigabe der Remediation-Liste, dann Korrekturen in separatem, freigegebenem PR.
ARTIFACTS: docs/analysis/2026-11-20-audit-top5-doc-truth.md
