---
pipeline_stages:
  implement: 3
status: DRAFT
date: 2026-11-14
base-commit: origin/main (92d41a90, Phase-D-PR 1 gemergt)
roadmap: docs/superpowers/plans/2026-11-10-backlog-roadmap.md
phase: AUDIT-1 (Querschnitt, kein Roadmap-Issue-Slot)
issues: [1276]
branch: keine (read-only Audit; Berichte via docs-Branch `docs/audit-top5-reports`)
---

# Audit Top-5 Abarbeitung — Ausführungsplan

> Status: DRAFT (2026-11-14) — nur Planung, nichts ausgeführt. Kein Test, kein Sync, kein Issue, kein PR.
> Eingabe: `docs/analysis/2026-11-14-audit-prioritization.md` (Top-5 `:40-48`, Token `:63-65`), Issue #1276 (Folge-Audit, 5 Punkte), Issues #1237–#1276 (40, alle OPEN, nur Titel gelesen außer #1271/#1276).
> **(U)** = unverifiziert.

## Entscheidungsstand 2026-11-15

Quelle: [Master-Roadmap §4](2026-11-15-master-roadmap.md) (Nutzerentscheidungen 2026-11-15). Plan-Status bleibt DRAFT.

- E-06: Audit jetzt in W0; pytest-cov nur temporär; Berichte per PR; G1-Voll-Testlauf erst nach Stufe A + Ja des Nutzers.
- E-27: Kostenpflichtige Läufe nur mit Kosten-Gate (Routing-Eval ja < 1 USD; #969-Baseline erst nach Kostenschätzung + erneutem Ja).
- E-08: Issue-Hygiene erst nach Beleg-Prüfung (Schließen nur mit Beleg-Kommentar), separater späterer Auftrag.
- E-19: Trailer-Formulierung folgt dem konfigurierbaren Contract.

**Goal:** Die fünf priorisierten Audits (Test-Suite, Admin-UI-Sicherheit, Admin-UI-Accessibility, Doku-Wahrheitsgehalt, Knowledge-Engine-Lint) plus Vorbedingung (ReqogniLoom-Toolnamen) so ausführen, dass jeder Befund mit Datei:Zeile belegt ist, als Bericht unter `docs/analysis/` liegt und — nach Dedupe — als Issue mit Lösungsvorschlag im Muster #1237–#1276 vorliegt. Umsetzung der Fixes ist NICHT Teil dieses Plans (geht in einen Bugfix-Batch).
**Architecture:** Jedes Audit = ein Subagent-Lauf mit eigenem Brief, Ausgabe nach .tmp/audit/ (Rohdaten) und `docs/analysis/2026-11-<dd>-audit-<thema>.md` (Bericht); unabhängige Rücklese durch einen zweiten Agenten; Issues erst nach Rücklese. Kosten-Gate vor jedem Lauf, der Rechenzeit verbraucht.
**Tech Stack:** pytest (`-n 2 --dist loadfile`, `tests/README.md:13-19`), `gh` (`/home/hermes/.local/bin/gh`), graphify (`graphify-out/graph.json`, teils stale), Markdown.
**Spec:** keine (Audit, keine Codeänderung; #1276 Lösungsvorschlag ist die Checkliste). Spec/Plan-Gate greift erst für die Fix-Umsetzung im Bugfix-Batch.

## Global Constraints

- Read-only am Code. Schreiben nur: .tmp/**, `docs/analysis/**` (Berichte), GitHub-Issues/-Kommentare.
- Kein `isolation: "worktree"` (`.claude/rules/no-worktree-isolation.md`).
- Verbotene MCP-Tools tabu (`.claude/rules/mcp-guardrails.md`); honcho-/reqogniloom-MCP nicht benutzen. Hinweis: in der Planungssession waren `reqogniloom` (INVALID_CONFIG: `REQOGNILOOM_MCP_URL` fehlt / `url` ungültig) und `honcho` (404) nicht verbunden.
- Keine Closing-Keywords (Closes/Fixes/Resolves) in Commits, PRs, Issue-Kommentaren; Issues nur mit Beleg-Kommentar schließen; Merge macht der Nutzer.
- Commit-Trailer: wörtlich den im Task-Prompt der ausführenden Session vorgegebenen Trailer übernehmen (Auftraggeber nennt ihn »Sonnet 5.5«-Trailer; in der Planungssession lautete der Prompt-Trailer `Claude Fable 5.1` — Abweichung (U), vor Ausführung klären, nie selbst wählen; vgl. Roadmap Entscheidung `:417`).
- `git`-Agent ohne Sentinel-Vorgabe briefen; Worker ohne git-Sentinel führen kein `git init/config/stash` aus (`.claude/rules/use-orchestrator.md`).
- Rechenzeit-Gate: jeder Lauf > 15 min Wall-Clock oder mit CI-Minuten erst nach Kostenschätzung und ausdrücklichem Ja des Nutzers (analog Roadmap Entscheidung 11, `:189`).
- graphify zuerst (`graphify query`), dann gezielte Reads; Volldumps nach .tmp/plans/scratch/ bzw. .tmp/audit/scratch/.

## Platzierung in der Gesamtreihenfolge

- Roadmap-Stand: A, B, C gemergt (#1224, #1225, #1227–#1235), D-PR 1 gemergt (#1236); D-Rest, E, F = Welle 3 offen; G, H = Welle 4; I = Welle 5 (`backlog-roadmap.md:145-156`, `:218-229`).
- Dieser Plan ändert keine Code-Datei → dateidisjunkt zu allen Phasen → **parallel zu Welle 3** ausführbar. Einzige Berührung: `docs/analysis/` (neue Dateien) und Issues.
- Empfohlener Slot: **jetzt, vor Welle 4**, weil (a) Test-Audit die Baseline für #1237/#1246 (Welle-4-Nachbarn) liefert, (b) Doku-Audit vor Phase E (Artefaktorte, #1186) stale Pfade erfasst, die E ohnehin verschiebt — E-Dateien werden im Doku-Audit nur gelistet, nicht bewertet (kein Doppel).
- Ergebnis-Senke: ein neuer Bugfix-Batch (Schritt N). `docs/plans/2026-11-14-bugfix-batch-3-plan.md` **existiert nicht** (geprüft 2026-11-14) → Schritt N legt die Triage-Liste als Vorschlag ab, kein Plan wird ungefragt erzeugt.

### Überschneidungen (nichts doppelt planen)

| Bestehend | Berührung | Regel |
|---|---|---|
| #1276 Folge-Audit | identisch mit diesem Plan | Plan = Abarbeitung von #1276; Punkt (4) Windows-Pfade bleibt bewusst ausgespart (Priorisierung Zeile 15 »nein«), im Abschlusskommentar vermerken |
| `docs/plans/ci-test-improvement-plan.md` (APPROVED 2026-10-29) | CI/Test-Struktur, `refresh-durations`-Job | Audit 1 misst, ändert keine Workflows; Verbesserungen → Issues gegen diesen Plan referenzieren |
| #1240 (Provider-Enumeration in 34 Testdateien), #1246 (TMPDIR-Drift), #1237 (Baseline) | Testlaufzeit/-stabilität | Befunde dort als Kommentar anhängen statt neues Issue |
| #1271, #1272 (viz Stop-PID, SSE-Origin) | Admin-/viz-Sicherheit | in Audit 2 als »bereits offen« markieren; nur neue Flächen (Escaping, CSP, Token-Pfade) werden Issues |
| Phase E (#1186 Artefaktorte), #1180 (C, gemergt) | Doku-Pfade | Audit 4 bewertet keine Artefaktpfade, nur Aussagen über Verhalten/Struktur |
| Phase H (#1161, #1244 Token) | Token-Zahlen in Doku | Audit 4 prüft Token-Aussagen nicht (Phase H misst) |
| #1261/#1264/#1265 (ReqogniLoom) | Schritt 0 | Ergebnis als Kommentar in #1261 (Vorgabe aus #1276) |
| `docs/plans/admin-server-split-backlog.md`, #1273 | Modulgröße | kein Befund dazu in Audit 2/3 |

## File Structure

- Create: .tmp/audit/00-reqogniloom-tool-resolution.md — Schritt-0-Protokoll (Nutzerlauf)
- Create: .tmp/audit/01-test-run/ — pytest-Logs, `--durations`-Ausgabe, `.test_durations` (lokal)
- Create: `docs/analysis/2026-11-<dd>-audit-test-suite.md` — Bericht Audit 1
- Create: `docs/analysis/2026-11-<dd>-audit-admin-ui-security.md` — Bericht Audit 2
- Create: `docs/analysis/2026-11-<dd>-audit-admin-ui-accessibility.md` — Bericht Audit 3
- Create: `docs/analysis/2026-11-<dd>-audit-docs-truth.md` — Bericht Audit 4
- Create: `docs/analysis/2026-11-<dd>-audit-knowledge-lint.md` — Bericht Audit 5 (Linter-nativer Pfad `knowledge/wiki/queries/lint-report-<date>.md` optional, Entscheidung E7)
- Create: .tmp/audit/issue-drafts/<nr-oder-slug>.md — Issue-Entwürfe vor Dedupe
- Create: .tmp/audit/2026-11-<dd>-triage.md — Schritt-N-Konsolidierung
- Modify: keine Code-Datei. `docs/analysis/`-Dateien folgen dem Muster `2026-09-30-provider-audit-*.md`.

## Reihenfolge und Bündelung

```
Schritt 0 (Nutzer, 10k) ─┐
Audit 1 Stufe A (Stichprobe, 25–35k) ──► Gate G1 ──► Audit 1 Stufe B (Voll-Lauf, 35–55k + Stunden)
Audit 2+3 gebündelt (70–100k)  ─┐ parallel zu Audit 1 (andere Dateien)
Audit 5 (15–25k)               ─┘ parallel
Audit 4 (50–70k) nach 1 und 2 (braucht deren Diff-Listen)
Rücklese je Bericht (5–8k je) ──► Issue-Filing ──► Schritt N (15–20k)
```

Gesamt: ~205–295k (Priorisierung `:65`) + Rücklesen ~30k + Schritt N ~15–20k = **~250–345k Token**, ohne Fix-Umsetzung.

---

### Task 0: Vorbedingung — ReqogniLoom-Toolnamen-Auflösung

**Files:** Create .tmp/audit/00-reqogniloom-tool-resolution.md
**Interfaces:** Produces: Liste der tatsächlich registrierten Toolnamen (`mcp__reqogniloom__*` vs. `mcp__plugin_reqogniloom_reqogniloom__*`); Consumes: `.mcp.json`, `.claude/settings*.json`, Plugin-Manifest (nur lesen).
**Agent:** Nutzer selbst (echter Claude-Code-Lauf mit gesetzten Secrets); Dokumentation durch `claude-expert` oder Fable (read-only). Kein Agent ruft MCP auf.
- Ziel: entscheidet #1261/#1264/#1265 (Doppeleinbindung, Allowlist-Abgleich).
- Methodik: Nutzer startet Claude Code mit gültigem `REQOGNILOOM_MCP_URL`/Token, führt `/mcp` aus, kopiert die Server- und Toolliste nach .tmp/audit/00-...md; Agent gleicht gegen `config/`-Katalog und Plugin-Manifest ab (grep, Datei:Zeile).
- Bereits belegbar: in der Planungssession scheiterten beide Einbindungen an Config (`plugin:reqogniloom:reqogniloom` INVALID_CONFIG »Missing REQOGNILOOM_MCP_URL«; `reqogniloom` »'url' is not a valid URL«) — Evidenz für #1261 (inkompatible Env-Namen), als Kommentar nachtragen.
- Abbruch: Nutzer hat keine Zugangsdaten → Schritt 0 wird als »blocked« dokumentiert, Audits 1–5 laufen trotzdem.
- Akzeptanz: Datei enthält Toolnamen-Liste + Abgleichstabelle + Kommentar-Entwurf für #1261 (ohne Closing-Keyword).
- Schätzung: 10k Token, 15 min Nutzerzeit.

### Task 1: Audit 1 — Test-Suite: Lauf, Laufzeit, Flakiness, Abdeckung admin-server/viz

**Files:** Create .tmp/audit/01-test-run/*, `docs/analysis/2026-11-<dd>-audit-test-suite.md`
**Interfaces:** Produces: Durations-Top-50, Skip/Xfail-Inventar, Flake-Liste, Abdeckung `scripts/admin-server.py`/`scripts/viz-*.py`; Consumes: `tests/` (468 Einträge), `tests/README.md`, `.github/workflows/orchestration-test.yml:50-80`, `validate.yml:68-85`.
**Agent:** `test-executor` (Lauf, nur Bash+Read) → `log-analyzer` (Auswertung) → Rücklese `code-reviewer`.
- Ziel/Frage: Wie lange läuft die Suite real, welche Module dominieren, was flaket, was ist dauerhaft geskippt, wie viel von admin-server/viz ist tatsächlich abgedeckt?
- Scope: pytest-Suite, Marker, `subprocess`-Tests (96 Dateien), CI-Shard-Verteilung. Nicht-Scope: Szenario-Suite (`validate.yml` 88 Szenarien, ~46 min seq., `:72-74`) — nur Zählung, kein Lauf; keine Workflow-Änderung; keine Testreparatur.
- Messgrößen: Gesamtdauer, `--durations=50`, Tests/Datei, Skip/Xfail-Gründe (30 Marker lt. Priorisierung `:9`), Wiederholungsstabilität (2 Läufe der Stichprobe), `pytest --cov` nur für `scripts/admin-server.py`, `scripts/viz-*.py` (Vorgabe #1276 Punkt 1; `pytest-cov` ist NICHT in `tests/requirements.txt` → Entscheidung E2).
- Werkzeuge: `PYTHONNOUSERSITE=1 python3 -m pytest -q -n 2 --dist loadfile` (`tests/README.md:14`), `-p no:cacheprovider --basetemp=/var/tmp/hermes/pytest-agent-meta/audit-01` (bestehender Basetemp-Ort, vgl. #1246 TMPDIR-Drift → Sync-Drift nach Lauf mit `git status` prüfen, nicht committen).
- **Abgestufte Variante (Gate G1):**
  - Stufe A (ohne Gate, ~10–15 min): Stichprobe = 16 Dateien `tests/test_admin*`/`tests/test_viz*` + Heavy-Fixture-Slice Shard 1 (5 Dateien, `tests/README.md:139`) + 10 zufällige weitere Dateien (Seed dokumentieren); `--durations=50`, 2 Wiederholungen für Flake-Erkennung.
  - Stufe B1 (Gate, kostenfrei lokal aber Stunden): voller lokaler Lauf `-n 2 --dist loadfile` mit `--store-durations` (pytest-split, `tests/requirements.txt:14-15`); Erwartung aus CI-Kommentar: ~120 min unserialisiert (`orchestration-test.yml:51-53`), lokal mit -n 2 ggf. 1–2 h (U).
  - Stufe B2 (Gate, CI-Minuten): `workflow_dispatch` des Jobs `refresh-durations` (`tests/README.md:141`, lädt `.test_durations` als Artefakt) — kein lokaler Rechner belegt, aber Runner-Minuten; nur falls Repo-Plan Minuten kostet (U, Nutzer weiß es).
  - **Gate-Punkt G1:** nach Stufe A legt der Agent Kostenschätzung vor (Dauer Stufe A × Hochrechnung auf ~6.575 Tests, `ci-test-improvement-plan.md:14`); Stufe B nur nach »Ja« des Nutzers. Empfehlung: B2 falls Minuten frei, sonst B1 nachts.
- Abbruch: Stufe A > 30 min oder > 10 % Fehlschläge → stoppen, Ursache als Befund, kein Stufe-B-Vorschlag ohne Ursachenanalyse.
- Ausgabe: Bericht mit Tabellen (Top-50 Dauer, Skip-Inventar, Flakes, Coverage admin/viz), Issue-Entwürfe: je Cluster (z. B. »Dauerfresser X«, »Flake Y«, »Dauer-Skip Z«) ein Entwurf; Kommentar-Entwürfe für #1240, #1246, #1237 statt Neu-Issue.
- Akzeptanz: Bericht enthält tatsächliche Laufzeit mit Befehl und Exit-Code; jede Zahl mit Logpfad belegt; `git status` nach Lauf dokumentiert (Drift ja/nein).
- Schätzung: Stufe A 25–35k; Stufe B + Auswertung 35–55k; Wall-Clock Stufe B 1–2 h.

### Task 2: Audit 2+3 gebündelt — Admin-/Dashboard-UI Sicherheit und Accessibility

**Files:** Create `docs/analysis/2026-11-<dd>-audit-admin-ui-security.md`, `docs/analysis/2026-11-<dd>-audit-admin-ui-accessibility.md`
**Interfaces:** Produces: Fundliste Sicherheit (Escaping, Auth, CSP, CDN/SRI) und A11y (WCAG 2.1 AA), Phantom-Doku-Korrektur; Consumes: `docs/ui/admin-ui.html` (11.558 Z.), `docs/ui/live-dashboard.html`, `docs/ui/agent-graph.html`, `scripts/viz-report.py`, `scripts/viz-server.py`, `scripts/admin-server.py` (Auth `:1122-1175`, `:3657-3740`).
**Agent:** `code-reviewer` + Skill `security-review` (Teil 2); `accessibility-specialist` (Teil 3); gleicher Dateisatz, zwei Berichte, ein Rücklese-Durchgang (`concept-reviewer` oder zweiter `code-reviewer`).
- Ziel/Frage (2): Werden Event-/Config-Daten vor HTML-Ausgabe escaped? Ist die Token-Auth konsistent (Header, Query-Param-Fallback `:3736`), Origin/Host-Check vollständig (`:1155`, `:3687`)? CSP/SRI vorhanden?
- Ziel/Frage (3): Sind alle interaktiven Elemente tastaturbedienbar und benannt; Kontrast; Fokusführung; Live-Regionen für Statusänderungen?
- Scope: die vier UI-Dateien + Server-Endpunkte, die sie bedienen. Nicht-Scope: #1271 (Stop-PID), #1272 (SSE-Origin) — bereits offen, nur Querverweis; Browser-E2E (kein Playwright-Lauf; Entscheidung E4); Windows-Pfade; Modulsplit #1273.
- Methodik (2): Vollständige Durchsicht aller HTML-Erzeugungsstellen (Stichprobe reicht nicht): `viz-report.py:357` hängt `msg` per f-String ohne Escaping in `<tr>` ein (U: ob `msg` upstream saniert wird); `admin-ui.html` 30× `innerHTML` (Zählung 2026-11-14), 0× `onclick=`, UI über `el(...)`-Helper → prüfen, ob `el()` Textknoten statt HTML setzt; CDN-Loads `viz-report.py:376` (d3 v7) und `:508` (`mermaid@10`, Minor unpinned) ohne SRI; Auth-Pfade in `admin-server.py` gegen `docs/guides/` abgleichen. Werkzeug: grep-Inventar → Datei:Zeile-Tabelle → Bewertung CWE-79/-352/-829.
- Methodik (3): Inventar interaktiver Elemente (`<button` 2×, `role="button"`/`tabindex` 0× im statischen HTML → dynamische Erzeugung per `el("button"…)` zählen); 18 `aria-/role=`-Attribute (Priorisierung `:12`) gegen Element-Inventar; Stichprobe 5 Kern-Flows (Tab-Navigation, Formular speichern, Modal, Tabelle, Statusbanner) per Code-Lesen; Kontrast rechnerisch aus CSS-Variablen. Kein Browserlauf.
- Phantom-Datei: `docs/guides/admin-ui-architecture.md` existiert nicht (geprüft; `ls docs/guides | grep -i admin` leer) → Bericht nennt die tatsächlich existierende Admin-UI-Doku (Suche `docs/` nach »admin-ui«) und schlägt Korrektur in #1276 vor (Kommentar, kein neues Issue).
- Abbruch: Datei-Set > 15k Zeilen über Erwartung oder `el()`-Helper nicht auffindbar → Teilbericht mit expliziter Lücke.
- Ausgabe: zwei Berichte; Issues: Sicherheit je Fläche (Escaping, SRI/CSP, Auth-Fallback) max. 4; A11y gebündelt max. 2 (Pflicht-Fixes AA vs. Nice-to-have), da kein offenes Issue existiert.
- Akzeptanz: jede Sicherheitsaussage mit Datei:Zeile und Angriffsweg; jede A11y-Aussage mit WCAG-Kriterium (z. B. 2.1.1, 4.1.2); Unverifiziertes markiert.
- Schätzung: 70–100k gesamt (2: 40–60k, 3: 30–40k), 0 Rechenzeit.

### Task 3: Audit 5 — Knowledge-Engine-Lint (parallel zu Task 1/2)

**Files:** Create `docs/analysis/2026-11-<dd>-audit-knowledge-lint.md` (+ optional `knowledge/wiki/queries/lint-report-2026-11-<dd>.md`, E7)
**Interfaces:** Produces: Lint-Report nach den 10 Checks (`.claude/agents/knowledge-linter.md:30-44`); Consumes: `knowledge/schema.md`, `knowledge/wiki/` (112 Seiten), `index.md` (181 Z.), `log.md` (33 Z.), `knowledge/sources/`.
**Agent:** `knowledge-linter` (read-only Tools); Rücklese `knowledge-curator` (nur lesen, keine Schema-Änderung).
- Ziel/Frage: Widersprüche, Orphans, kaputte Links, fehlende OKF-Frontmatter, Index-/Log-Staleness (log.md 33 Z. bei 112 Seiten → Verdacht auf Lücke), veraltete Claims gegen Code (Stichprobe 10 Seiten mit Code-Bezug).
- Scope: `knowledge/wiki/**`, `index.md`, `log.md`, `schema.md`. Nicht-Scope: `knowledge/sources/` (immutable, nur als Referenz), Ingest neuer Quellen, Migration (eigener Agent), Phase-C-Integrationsdesign.
- Methodik: alle 10 Checks vollständig (billig: Glob/Grep); Claim-Check als Stichprobe 10 Seiten, Auswahl: höchste Code-Referenzdichte (grep `scripts/`); Metriken: Orphan-Quote, Broken-Link-Zahl, Frontmatter-Vollständigkeit %, Index-Deckung (Seiten in index.md / Seiten gesamt).
- Abbruch: > 50 Broken Links → nur Zählung + Muster, kein Einzelnachweis.
- Ausgabe: Bericht; Issues: max. 2 (»Wiki-Hygiene-Batch« für `knowledge-gardener`, »Index/Log-Staleness-Prozess«); kein Issue je Typo.
- Akzeptanz: Zahlen reproduzierbar (Befehle im Bericht), Severity je Check.
- Schätzung: 15–25k, 0 Rechenzeit.

### Task 4: Audit 4 — Doku-Wahrheitsgehalt (nach Task 1 und 2)

**Files:** Create `docs/analysis/2026-11-<dd>-audit-docs-truth.md`
**Interfaces:** Produces: Diff-Liste »Doku sagt / Code tut« mit Datei:Zeile beidseitig; Consumes: `docs/CODEBASE_OVERVIEW.md` (Stand 2026-09-11, `:3`), `docs/guides/`, `docs/providers/` (U: Ordnername), `.claude/rules/use-lazy-rules.md`, Ergebnisse Task 1 (Testabdeckungs-Aussagen) und Task 2 (Admin-UI-Doku).
**Agent:** `documenter` (Diff-Liste, kein Schreiben in Doku) mit `knowledge-linter`-Muster (Claim-Check); Rücklese `explorer` (Stichprobe 20 % der Diff-Zeilen gegen Code nachmessen).
- Ziel/Frage: Welche Aussagen, die Agenten als Routing-Wahrheit lesen, sind falsch oder stale?
- Scope (Stichprobe, kein Volllauf über 348 Dateien): (a) `CODEBASE_OVERVIEW.md` komplett gegen `scripts/lib/`-Modulliste und Entry-Points; (b) `docs/guides/` alle Dateien mit »admin«, »hook«, »sync« im Namen; (c) Provider-Doku für die 4 Phase-G-Provider nur Existenz der genannten Pfade/Flags (`config/ai-providers.yaml`), keine Verhaltensbewertung (Phase G); (d) `use-lazy-rules.md:17` vs. #1186 (viz-Audit `:183`). Nicht-Scope: Artefaktpfade (Phase E), Token-Zahlen (Phase H), `knowledge/` (Task 3), README.md (extern, Englisch, nur Link-Check).
- Methodik: pro Doku-Aussage ein Prüfbefehl (grep/ls/Read) → Tabelle Aussage | Doku-Zeile | Code-Zeile | Status (wahr/stale/falsch/U). graphify für Modul-Existenz. Stichprobenplan: alle Aussagen in (a)+(d), je Guide die Abschnitte »Architektur«/»Ablauf«, Provider nur Pfade.
- Abbruch: > 40 % der Overview-Aussagen stale → Bericht empfiehlt Regenerierung (`/doc-now`) statt Einzelkorrekturen; Audit endet dort.
- Ausgabe: Bericht + max. 3 Issues (Overview-Regenerierung, Guides-Korrekturbatch, Phantom-Referenzen); #1276 Punkt (2) als Kommentar schließen-vorbereiten (ohne Keyword).
- Akzeptanz: jede Zeile der Diff-Liste beidseitig belegt; Stichprobenauswahl dokumentiert.
- Schätzung: 50–70k.

### Task 5: Qualitätskontrolle — unabhängige Rücklese je Bericht

**Files:** Modify `docs/analysis/2026-11-<dd>-audit-*.md` (Abschnitt »Rücklese«)
**Interfaces:** Produces: Rücklese-Vermerk (bestätigt/korrigiert/entfernt je Befund); Consumes: Berichte Task 1–4.
**Agent:** jeweils anderer Agent als der Autor (Tabelle in den Tasks); nie der Orchestrator selbst.
- Methodik: 100 % der als HIGH markierten Befunde nachmessen (Datei:Zeile öffnen), 20 % Stichprobe der übrigen; Widerspruch → Befund auf (U) setzen oder streichen.
- Akzeptanz: Rücklese-Abschnitt mit Zählung (geprüft/bestätigt/korrigiert), erst danach Issue-Filing.
- Schätzung: 5–8k je Bericht (~30k gesamt).

### Task 6: Issue-Filing mit Dedupe

**Files:** Create .tmp/audit/issue-drafts/*.md; GitHub-Issues (via `feedback`-Agent oder `gh issue create`)
**Interfaces:** Produces: Issues im Muster #1237–#1276; Consumes: Rücklese-geprüfte Berichte.
- Muster (aus #1271): `## Befund` → `## Evidenz` (Datei:Zeile, Tests) → `## Loesungsvorschlag` (Betroffen, Zielzustand, Schritte, Testidee, Aufwand S/M/L, Related) → `## Hinweis` (Verifikationsstand) → `Quelle: Audit 2026-11-<dd> (…), Bericht <Pfad>`; Titel `<type>(<area>): <imperativ>`; Labels wie Bestand (`bug`/`improvement`/`documentation` + `sync`/`hooks`/`config`/`framework`/`viz`).
- Dedupe-Regel: vor jedem Create (1) Titel-Abgleich gegen #1237–#1276 und Phase-D–I-Issue-Listen (`backlog-roadmap.md:150-155`), (2) `gh issue list --search "<2 Schlüsselwörter>" --state all`, (3) Treffer → Kommentar am Bestand mit Bericht-Link statt neues Issue; (4) ein Issue je Befund-Cluster, nie je Zeile; (5) kein Closing-Keyword.
- Akzeptanz: Dedupe-Protokoll je Issue (Suchbegriffe, Treffer) in .tmp/audit/issue-drafts/.
- Schätzung: 10–15k.

### Task N: Konsolidierung und Übergabe an Bugfix-Batch

**Files:** Create .tmp/audit/2026-11-<dd>-triage.md
**Interfaces:** Produces: Triage-Tabelle (Issue | Klasse S/M/L | Phase-Zuordnung | Bugfix-Batch-Kandidat ja/nein); Consumes: alle Issues aus Task 6, `docs/plans/2026-11-14-bugfix-batch-3-plan.md` (nur lesen, **derzeit nicht vorhanden**).
**Agent:** `planner` (read-only) oder Fable.
- Methodik: S-Klasse ohne Spec → Bugfix-Batch-Kandidat; M/L/XL → Spec-Gate (Roadmap §1 `:9`); Zuordnung zu bestehenden Phasen, wenn dateigleich (z. B. Hook-Befunde → D, Provider-Doku → G); Rest → neuer Batch-Vorschlag.
- Falls Batch-3-Plan existiert: Kandidaten als Vorschlagsblock anhängen (nur .tmp/-Kopie, Original nicht editieren); falls nicht: Triage-Datei ist die Übergabe.
- Abschluss #1276: Kommentar mit Checkliste (1)–(5), Status je Punkt, Verweis auf Berichte; Punkt (4) Windows als bewusst offen; Schließen nur durch Nutzer nach Beleg.
- Akzeptanz: jedes neue Issue genau einmal zugeordnet; Summe stimmt mit Task-6-Zählung.
- Schätzung: 15–20k.

## Rollen-/Agenten-Briefe — Skeleton (für jeden Lauf)

```
Rolle: <agent>  | Modus: read-only (Ausnahme: Ausgabedateien unten)
Auftrag: <1 Satz Ziel/Frage aus Task X>
Eingaben: <Dateien mit Zeilenankern>, graphify zuerst (graphify query "...")
Ausgaben: NUR .tmp/audit/<...> und docs/analysis/<datei> — nichts außerhalb des Repos
Verbote: kein git-Mutieren (kein init/config/stash/commit), kein isolation:worktree, kein honcho-/reqogniloom-MCP,
         keine verbotenen MCP-Tools (mcp-guardrails.md), keine Tests/Syncs außer in Task 1 freigegebene Befehle,
         keine Closing-Keywords, keine Issue-Schließung, kein Merge
Belege: jede Aussage Datei:Zeile; Unverifiziertes als (U)
Abbruch: <Kriterium aus Task X> → Teilbericht + Lücke benennen
Rückmeldung: max. 12 Zeilen (Pfad, Zählung, Top-3-Befunde, Lücken)
Commit (nur docs-Branch, nur nach Freigabe, nur git-Agent ohne Sentinel-Vorgabe):
  Trailer wörtlich aus dem Task-Prompt der Session übernehmen — nicht umformulieren.
```

## Entscheidungspunkte für den Nutzer (einzeln)

| # | Frage | Empfehlung |
|---|---|---|
| E1 | Slot: jetzt parallel zu Welle 3 oder erst nach D/E/F? | jetzt (dateidisjunkt, liefert Baseline für Welle 4) |
| E2 | `pytest-cov` temporär installieren (nicht in `tests/requirements.txt`)? | ja, nur in venv der Audit-Session, kein Commit; sonst Coverage-Teil streichen |
| E3 | **Gate G1**: Stufe B des Testlaufs (B1 lokal 1–2 h / B2 CI-`refresh-durations`)? | erst nach Stufe-A-Hochrechnung entscheiden; B2 falls Runner-Minuten frei |
| E4 | A11y zusätzlich mit Playwright (erlaubte Tools) gegen laufenden Admin-Server? | nein in diesem Durchgang (Server-Start = Rechenzeit + Token); Code-Audit zuerst |
| E5 | Audit 2+3 als ein oder zwei Berichte? | zwei Berichte, ein Rücklese-Durchgang |
| E6 | Doku-Audit Stichprobe (a)–(d) oder Vollabgleich 348 Dateien? | Stichprobe; Volllauf nur wenn Stufe > 40 % stale |
| E7 | Knowledge-Lint-Report zusätzlich linter-nativ unter `knowledge/wiki/queries/`? | ja (Linter-Konvention `knowledge-linter.md:45`), Kopie identisch |
| E8 | Berichte via PR auf `docs/audit-top5-reports` oder nur in .tmp/? | PR (ein docs-Branch, Nutzer merged) |
| E9 | Trailer-Wortlaut (»Sonnet 5.5« lt. Auftrag vs. Prompt-Trailer der Planungssession) | vor erstem Commit vom Nutzer bestätigen lassen |
| E10 | Schritt 0 blockiert (keine Zugangsdaten)? | Audits trotzdem starten, #1261 nur mit Config-Fehler-Evidenz kommentieren |

## Abhängigkeiten (Kurz)

- Task 0 unabhängig; Task 1 Stufe A, Task 2, Task 3 parallel startbar; Task 1 Stufe B nach G1; Task 4 nach Task 1 (Stufe A reicht) und Task 2; Task 5 je Bericht; Task 6 nach Task 5; Task N nach Task 6.
- Externe: Nutzer-Ja für G1 (E3) und E2; Zugangsdaten für Task 0.

## Nicht geprüft / Annahmen

- Issue-Bodies #1237–#1275 außer #1271 nicht gelesen (Dedupe per Titel geplant, Volltext-Dedupe erst in Task 6).
- `el()`-Helper in `admin-ui.html` nicht gelesen → Escaping-Verhalten (U).
- `viz-report.py:357` Upstream-Sanitisierung von `msg` nicht geprüft (U).
- Lokale Laufzeit der Suite nie gemessen; CI-Zahlen aus Kommentaren (`orchestration-test.yml:51-53`, `validate.yml:72-74`).
- `docs/providers/` Ordnername nicht verifiziert (U); Phasen-D–I-Pläne nur Header/Goal gelesen.
- graphify-Graph teils stale (Hook-Warnung), nur zur Orientierung.
