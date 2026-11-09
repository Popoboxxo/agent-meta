---
status: DRAFT
issue: 1188
issue-url: "https://github.com/Popoboxxo/agent-meta/issues/1188"
spec: docs/specs/2026-11-09-issue-label-taxonomy-spec.md
spec-id: SPEC-issue-label-taxonomy-2026-11-09
class: XL
date: 2026-11-09
branch: feat/1188-issue-label-taxonomy
base-branch: docs/config-wave-plans-1181-1188
base-commit: aaed14c2
trace:
  - SPEC-issue-label-taxonomy-2026-11-09
  - issue-1188
  - issue-1167
  - issue-1141
  - issue-957
  - issue-1168
---

# Deklarative Issue-Label-Taxonomie mit steckbaren Tracker-Adaptern (#1188) — Umsetzungsplan

> Status: **DRAFT** — dieser Plan implementiert nichts, committet nichts und aktiviert
> in `.meta-config/project.yaml` dieses Repos **nichts**.
> **Quelle:** `docs/specs/2026-11-09-issue-label-taxonomy-spec.md` (`Status: DRAFT`,
> Spec-ID `SPEC-issue-label-taxonomy-2026-11-09`, 22 ACs + AC-2b, IC-1…IC-7, D1/D2/D4).
> **Vorbedingung für die Umsetzung:** Die Spec ist heute **nicht freigegeben**. Nach
> Master-Rule `spec-plan-workflow` startet die Implementierung erst mit
> `Status: APPROVED`. Die inhaltlichen Voraussetzungen sind erfüllt: Q1, Q2, Q3, Q4, Q7, Q8 und Q9
> sind am 2026-11-09 entschieden (D9–D15, Abschnitt „Entscheidungsprotokoll (2026-11-09)"). Bis zur
> Freigabe ist dieser Plan die belastbare Vorarbeit, kein Ausführungsauftrag.
>
> **Revision 2 (Review-Einarbeitung 2026-11-09):** RVW-1188-01 (BLOCKER), -02 … -06 (MAJOR) und
> drei WARNs sind eingearbeitet; Auflösungstabelle am Dokumentende („Review-Auflösung
> (2026-11-09)"). Der Plan bleibt `DRAFT`.
> **Revision 3 (Review-Runde 2, 2026-11-09):** RVW2-1188-01 … -04 und die Querschnittsbefunde
> RVW2-X-01/-02 sind eingearbeitet (Prune-Kandidatenformel, beide `project.yaml.example` in T1,
> Golden-Test statt `git diff`, Stufe 3 vs. 5). Die Auflösungstabelle ist entsprechend ergänzt.
> **Revision 4 (Szenario-Konflikte K1–K8, 2026-11-09):** K1, K2, K4 und K6 sind eingearbeitet
> (`unmanaged` statt `project-state`, eine `separator`-Objektform, kein `default`-Feld, `$defs`
> bleibt). K3/K5/K7/K8 betreffen diesen Plan nicht. Auflösungstabelle am Dokumentende.
> **Revision 5 (Nutzer-Entscheidungen D9–D15, 2026-11-09):** Die offenen Punkte Q1, Q2, Q3, Q4,
> Q7, Q8 und Q9 sind entschieden und als **K-12 … K-18** in die Plan-Präzisierungen übernommen
> (Repository-Präzedenzkette, kein Rename in v1, Drift-Baseline für `docs/issue-labels.md`,
> Template-Schalter, `--apply` schreibt / `git` committet, Retry nur bei `429`, Triage-Labels als
> Nicht-Taxonomie). Betroffene Tasks: T1, T9, T13, T15, T16, T17, T18, T21, T25, T30. T30 ist damit
> **kein bedingter Task mehr**; Testdateien 17 → 18, Tasks 29 Pflicht + 1 bedingt → **30 Pflicht**.
> Protokoll: Abschnitt „Entscheidungsprotokoll (2026-11-09)". Der Plan bleibt `DRAFT`.

**Goal:** Eine deklarative Label-Taxonomie (`type` / `area` / `priority`) ersetzt die drei
divergierenden, hartkodierten Label-Tabellen in `feedback`, `meta-feedback` und
`bug-feature-analyzer`; ein siebenstufiger Resolver mit gemeldeter `source` speist alle
Rollen-Templates, `docs/issue-labels.md`, den Consistency-Check und die Admin-UI.
Ein rein datengetriebener Adapter-Registry (`config/issue-adapters.yaml`) projiziert dieselbe
Taxonomie auf GitHub, GitLab, Gitea und — als Beweis der Datengetriebenheit — auf einen
synthetischen vierten Tracker ohne Python-Code. `sync.py --labels` druckt standardmäßig nur
den Diff; erst `--apply` schreibt, `--check` ist ein CI-Gate, `--explain` zeigt pro Achse und
Wert die Herkunft.

**Architecture:** Drei neue Bausteine mit klarer Grenze: `scripts/lib/issue_conventions.py`
(Content + Präzedenz + Achsen-Gate + Projektion + Render der Blöcke/Doku),
`scripts/lib/issue_adapters.py` (Adapter-Registry, Repository-Identität, HTTP-Executor,
Diff/Apply) und `scripts/lib/consistency/issue_labels.py` (sechs Regeln). Die Verdrahtung
bleibt an den bestehenden Nahtstellen: `_build_convention_variables()` in
`scripts/lib/config.py:2673-2734`, der Per-Rollen-Injektionspunkt
`scripts/lib/agent_sync.py:1458-1459`, die Modus-Tabelle `scripts/sync.py:757-787` und die
Writable-Whitelist `scripts/admin-server.py:234-259`. Verhaltens-Verzweigung ausschließlich
über Capability-Flags (`scoped-labels`, `labels`, `issue-forms`/`issue-templates`), nie über
Provider-Namen (`scripts/lib/consistency/provider_literals.py:1-17`).

**Tech Stack:** Python 3 (stdlib only: `urllib.request`, `json`, `re`, `http.server` im Test,
`dataclasses`, `pathlib`), PyYAML (bestehende Runtime-Ausnahme,
`docs/adr/0001-pyyaml-runtime-ausnahme.md`), pytest, Markdown/YAML, Vanilla-JS in
`docs/ui/admin-ui.html`.

**Spec:** docs/specs/2026-11-09-issue-label-taxonomy-spec.md
**Spec-ID:** SPEC-issue-label-taxonomy-2026-11-09
**Issue:** #1188 — `feat(config): declarative issue-label taxonomy with pluggable tracker adapters (type/area/priority)`
**Klasse:** **XL / cross-cutting** · **Datum:** 2026-11-09 · **Basis:** Branch
`docs/config-wave-plans-1181-1188`, HEAD `aaed14c2`, agent-meta `v2.0.0-beta.8`
**Branch für die Umsetzung:** `feat/1188-issue-label-taxonomy` (Branch-Guard: keine
Code-Änderung auf `main`/`master`)
**Größe je Task:** **S** ≤ 1 Datei und ≤ 60 Diff-Zeilen · **M** 2–3 Dateien oder ≤ 250
Diff-Zeilen · **L** > 3 Dateien, neues Modul > 250 Zeilen oder schema-/ui-übergreifend
**Aufwand:** 30 Tasks (**alle Pflicht**), 8 Meilensteine, 18 neue Testdateien,
2 neue Config-Dateien, 1 persistentes Zustands-Manifest, 3 neue Python-Module. Eine belastbare Zahl liefert der
`effort-estimator` (Textverweis; hier bewusst nicht berechnet).

## Voraussetzungen

1. **Spec freigegeben:** `docs/specs/2026-11-09-issue-label-taxonomy-spec.md` trägt
   `Status: APPROVED`. Heute: DRAFT. Ohne Freigabe bleibt dieser Plan DRAFT.
2. **Q1, Q2, Q3, Q4, Q7, Q8, Q9 entschieden (2026-11-09):** D9 (Repository-Präzedenzkette),
   D14 (Retry nur bei `429`), D10 (kein Rename in v1), D11 (`docs/issue-labels.md` in
   `generated-file-hashes.json`), D15 (Triage-Labels als Nicht-Taxonomie), D12
   (`templates.{mode,force}` in IC-1), D13 (`--apply` schreibt, `git` committet). Q1 blockierte
   AC-16 im eigenen Repo (dieses Repo hat **keine** `git:`-Sektion: `.meta-config/project.yaml`
   enthält nur `conventions-preset: default` in `:394`; `git.remote-url` fällt damit auf den
   Schema-Default `""` zurück, `config/project-config.schema.json:1753-1757`) — mit D9 löst
   `repository.*` bzw. `GITHUB_REPOSITORY`/`CI_PROJECT_PATH` das auf. Q9 (Commit-Ownership) ist mit
   D13 beantwortet und blockiert T21 nicht mehr.
3. **Q5 bestätigt** (Spec-Entscheidung: `issue-conventions.platform-overrides.<adapter>`),
   sonst ist Stufe 1 der Präzedenz gegenstandslos.
4. **Keine Aktivierung in diesem Repo:** `.meta-config/project.yaml` bleibt unverändert.
   Nur so bleibt der Golden-Test (AC-9) beweiskräftig, und nur so kollidiert dieser Plan
   nicht mit den Golden-Tests von #1186/#1187/#1181 (Konfliktfläche
   `config/project-config.schema.json`).
5. **Serielle Datei-Disziplin** (Spec §11): `config/project-config.schema.json`,
   `scripts/lib/config.py`, `scripts/lib/consistency/placeholders.py`,
   `scripts/admin-server.py` und `docs/ui/admin-ui.html` sind Ein-Datei-Konfliktflächen.
   Dieser Plan hält sie in getrennten Tasks, damit jede PR genau eine Datei dominiert.
6. **Testkommando:** `python3 -m pytest <pfad> --basetemp="$PYTEST_BASETEMP"`. Kein
   `isolation: "worktree"`, keine Commits durch diesen Plan.

## Zielbild in fünf Sätzen

1. Ein Projekt beschreibt seine Issue-Labels genau einmal — drei Achsen mit Werten, Farben
   und Beschreibungen — und alle Rollen, die Labels vergeben, lesen diese eine Definition.
2. Der Resolver beantwortet für **jeden** Wert und **jede** Projektionsregel die Frage
   „woher kommt dieser Wert?" mit einem `source`-String, und `--explain` druckt ihn.
3. Dieselbe Taxonomie wird pro Plattform nur **projiziert** (Separator je Kardinalität,
   Farbformat, Case, Längen-/Muster-Grenze), nie neu erfunden; ein vierter Tracker ist eine
   YAML-Datei, kein Python-Modul.
4. `sync.py --labels` ist immer gefahrlos (Dry-Run), `--apply` ist idempotent und nicht
   transaktional (Teilfehler mit Tabelle, Exit 1), `--check` ist ein CI-Gate ohne Schreibzugriff.
5. Ohne `issue-conventions.enabled: true` ändert sich **kein Byte** der heutigen Ausgabe —
   die Migration ist additiv und per Entfernen der Sektion vollständig rückrollbar.

## Plan-Präzisierungen (K-1 … K-10)

Diese Punkte sind **Plan-Entscheidungen innerhalb der Spec**, keine Spec-Änderungen. Wo die
Spec zwei Anforderungen spannt, wird die Auflösung hier festgelegt und in der
AC-Traceability (Abschnitt „AC→Task-Traceability") ausgewiesen.

- **K-1 — AC-6 vs. AC-9 (Golden-Bytes je Rolle).** AC-6 verlangt „kein Label-Literal mehr in
  den vier Templates"; AC-9 verlangt für `enabled: false` byte-identische Ausgabe. Beides ist
  nur gleichzeitig erfüllbar, wenn der **Legacy-Text nicht im Template** liegt: die vier
  Templates referenzieren ausschließlich Platzhalter, und der Alt-Text liegt als
  `LEGACY_ROLE_BLOCKS` in `scripts/lib/issue_conventions.py` (framework-intern, pro Rolle).
  Injiziert wird er über einen Per-Rollen-Overlay am bestehenden Punkt
  `scripts/lib/agent_sync.py:1458-1459` (Muster: `_apply_role_auto_commit_overrides`,
  `:92-123`). Löschkriterium: entfällt, sobald `enabled: true` Framework-Default wird — das ist
  **F-5** (Spec §10.2), ein eigenes Issue, kein Teil von #1188. Bis dahin gilt: AC-6 ist als
  „kein Literal **im Template**" erfüllt, die Legacy-Tabelle bleibt in der Ausgabe sichtbar
  (Spec „AC-Interpretationen").
- **K-2 — Eine kanonische Separator-Form (Szenario-Konflikt K2).** Der Separator hat auf **allen
  drei Ebenen** dieselbe Objektform `separator: {single, multi}`: `adapters.<id>.defaults.separator`
  (IC-3), `platform.<adapter>.defaults.separator` (IC-2) und `issue-conventions.defaults.separator`
  (IC-1). Das frühere String-Feld `defaults.label-separator` ist **entfernt**: IC-1 ist
  `additionalProperties: false`, ein String wäre ein Validierungsfehler. Es gibt **keine**
  String→Objekt-Brücke und keinen zweiten Parser; T7 testet ausschließlich die Objektform und die
  Kardinalitäts-Trennung (`single` scoped, `multi` nie scoped — AC-2b).
- **K-3 — `Codeberg` ist ein Alias, kein Adapter.** `git.platform` erlaubt
  `GitHub|GitLab|Gitea|Codeberg` (`config/project-config.schema.json:1742-1752`); die
  Adapter-Datei liefert `aliases: {Codeberg: gitea}` als **Daten**. Kein
  `if platform == "Codeberg"` im Code.
- **K-4 — Repository-Identität ist lazy.** `resolve_issue_conventions()` darf **nie** die
  Repository-Identität auflösen; das passiert ausschließlich im `--labels`-Pfad
  (`issue_adapters.resolve_repository`). Grund: `derive_builder_vars` ruft die Builder mit
  leerem Config-Dict auf (`scripts/lib/consistency/placeholders.py:299-306`); eine frühe
  Identitätsauflösung würde dort einen Fehler erzeugen und `--validate` brechen. Die Auflösung
  folgt der Präzedenzkette aus **K-12**.
- **K-5 — Netzwerk-Zuschnitt (Q6 vorweggenommen).** Regeln 4–6 des Consistency-Checks laufen
  offline in `--validate`; Regeln 1–3 nur in `sync.py --labels [--check]`. `--validate` darf
  `urllib.request.urlopen` **nie** erreichen; Test patcht `urlopen` auf „raise". AC-5 wird
  deshalb als **Kontext-Split** gelesen (ein Modul, sechs IDs, zwei Aufrufkontexte), nicht als
  „sechs Regeln im Offline-Lauf" — Spec §4.7, nachgewiesen in T23/T24.
- **K-6 — Keine Schema-Erfindung (durch D12 überholt, siehe K-15).** Optionale Issue-Templates
  brauchen einen `mode`-Schalter. Bis Revision 4 fehlte er in IC-1 (`additionalProperties: false`),
  deshalb war T30 bedingt. Mit **D12** ist `issue-conventions.templates: {mode, force}` Spec-Vertrag
  (Spec IC-1/§4.9) — T1 legt den Unterabschnitt an, T30 ist ein regulärer Task. Ein explizites
  `renames`-Objekt bleibt **weiterhin außerhalb** dieses Plans: D10 reserviert die `rename`-Zeile,
  aber der Schema-Schlüssel kommt erst mit einer eigenen Spec-Revision.
- **K-7 — Label-Namen sind URL-Segmente (RVW-1188-01).** Der Executor baut jede URL über
  `build_target_url(adapter, identity, op, fields)` und setzt `{name}`, `{id}`, `{owner}`,
  `{repo}`, `{project_id}` **pro Segment** mit `urllib.parse.quote(value, safe="")` ein.
  Projizierte Namen (`type/bug`, `area/core`) bleiben im Soll-Set, im Diff, im Manifest und in
  Meldungen unkodiert. Gitea braucht zusätzlich `ids` (numerische ID) und jeder Adapter
  `pagination`; beides ist **Adapter-Daten**, nicht Code.
- **K-8 — Transport-Härtung (RVW-1188-05).** H-1…H-7 aus Spec §4.12 sind Code: HTTPS-Zwang
  (Loopback-Ausnahme), Host+Scheme projektseitig unveränderlich, relative Pfade, keine
  Redirects, `auth.header` nur mit `{token}`. Der Host stammt für `github`/`gitlab` aus der
  Framework-Konstante und für `gitea` aus `GITEA_URL` (Env) — nie aus `project.yaml`. Kein
  Flag schaltet eine Regel ab.
- **K-9 — Prune über Manifest (RVW-1188-04, RVW2-1188-01).** Löschkandidaten stammen ausschließlich
  aus `.meta-config/issue-labels-state.json` (Spec IC-8) oder `sync.prune-allow`. Der „owned
  prefix" bleibt nur als **Klassifikation** (`info`, `warning`) erhalten und ist **nie**
  Löschgrund. Kandidatenmenge: `(Manifest ∖ desired) ∖ labels(inaktiver Achsen)`. Ohne Manifest
  und ohne `prune-allow`: null Löschkandidaten; `prune-allow` wirkt auch ohne Manifest.
- **K-10 — Eine Präzedenz, AC-14 wörtlich (RVW-1188-02).** Stufe 4 = Framework-Plattform-Default,
  Stufe 5 = Framework-Preset. Die `source`-Literale bleiben stufenfest. T5 testet die Stufe,
  nicht den Namen: `test_level4_framework_platform_source` / `test_level5_framework_preset_source`.
- **K-11 — Kein `default`-Feld in `taxonomyAxis` (Szenario-Konflikt K4).** Ein „zwei Defaults"-
  Fehler ist schema-seitig unerreichbar (`additionalProperties: false`); T4 prüft nur die zwei
  realisierbaren Bedingungen. Die Regel „genau ein `single`-Achsenwert pro Issue" ist eine
  **Laufzeitregel** und wird ausschließlich über AC-7 (`enforcement.single-axis-per-issue`,
  T18 `enforce_single_axis`) getestet — nicht als Schema-Negativtest.

### Entscheidungen D9–D15 als Plan-Präzisierungen (2026-11-09)

- **K-12 — Repository-Identität: Präzedenzkette (D9).** `resolve_repository()` probiert strikt in
  dieser Reihenfolge und nimmt die erste **nicht-leere, parsebare** Quelle:
  `issue-conventions.repository.{owner,repo}`/`project-id` → `git.remote-url` (vier Formen) →
  `GITHUB_REPOSITORY`/`CI_PROJECT_PATH`. Unparsbares wird übersprungen; erst wenn **alle drei**
  fehlen oder unparsbar sind, `IssueConfigError` (Exit 2, kein API-Call). Die Meldung ist **eine**
  Meldung, nennt alle drei Wege und enthält **nie** einen leeren `owner`/`repo`. Reine Datenlogik,
  lazy (K-4), kein Shell-Aufruf (Repo-Containment). Tests: T15.
- **K-13 — Kein Rename in v1 (D10).** Ein neuer Wert erzeugt `create <neu>`; kein
  `update.new_name`-Aufruf. Steht der alte Wert im Manifest, wird er als
  `info: rename-candidate <alt>` gemeldet. Der alte Wert verlässt nur das **Soll-Set**; das
  Tracker-Label bleibt (kein Delete, kein Update). Die `rename`-Zeile bleibt im CLI-Vertrag
  reserviert (Spec IC-5). Test: T17 `test_new_value_creates_and_reports_rename_candidate`.
- **K-14 — `docs/issue-labels.md` ist drift-geprüft (D11).** Registrierung in
  `.meta-config/generated-file-hashes.json` über eine explizite Root-Level-Ausnahme im Muster von
  `PLATFORM_DEFAULTS_RESOLVED_REL` (`scripts/lib/generated_file_drift.py:49`, Scan `:383-393`,
  Capture `:535-537`). Manuelle Edits werden beim Sync überschrieben (`.sync-backup-*`-Sicherung).
  Die Baseline-Datei selbst wird vom Capture-Stage geschrieben, nicht handeditiert. Dieselbe Regel
  gilt in #957 für PR-Templates; die Marker-Regel aus IC-7 bleibt zusätzlich bestehen.
- **K-15 — Template-Schalter (D12).** `issue-conventions.templates: {mode: off|scaffold|manage,
  force: bool}` (offener Default `off`, `force: false`) ist ab jetzt Schema-Vertrag (T1). Semantik:
  `off` = nichts; `scaffold` = nur fehlende Dateien; `manage` = zusätzlich Dateien mit unserem
  Marker; `force: true` = auch Dateien ohne Marker. Erzeugung ausschließlich capability-gesteuert
  (`issue-forms`/`issue-templates`). T30 ist damit **Pflicht-Task**.
- **K-16 — `--apply` schreibt, `git` committet (D13).** Kein `git`-Aufruf, kein Auto-Commit aus
  `_handle_labels`. Die Ergebnis-Tabelle endet mit einer Zeile `wrote .meta-config/issue-labels-state.json`.
  CI-`--apply`-Jobs committen nie. Test: T21 `test_apply_prints_manifest_path_in_result_table`,
  `test_cli_never_invokes_git`.
- **K-17 — Retry nur bei `429` (D14).** Genau ein Retry je Request, nur `429`, Wartezeit aus
  `Retry-After` (Sekunden oder HTTP-Datum), gedeckelt auf 30 s, Default 1 s bei fehlendem/unparsbarem
  Header. `5xx` und Timeouts: kein Retry, Fehler sammeln, weiter, Exit 1 (AC-18). `401`/`403`
  brechen unverändert nach dem ersten Fehlschlag ab (AC-19). `sleep` wird injiziert
  (`UrllibTransport(..., sleep=time.sleep)`), damit Tests nicht warten; kein Backoff, keine
  Retry-Konfiguration in `project.yaml`. Tests: T16/T18.
- **K-18 — Triage-Labels sind Nicht-Taxonomie (D15).** `TRIAGE_LABELS = ("triage", "needs-info")`
  lebt als Framework-Konstante in `scripts/lib/issue_conventions.py`; `render_triage_labels()`
  rendert daraus `{{ISSUE_TRIAGE_LABELS}}`. Kein Projekt-Override, keine vierte Achse (D2), kein
  Soll-Label, kein `prune`-Ziel. Regel 4 des Consistency-Checks nimmt sie von der Literal-Prüfung
  aus; `docs/issue-labels.md` führt sie unter „Nicht Teil der Taxonomie". Tests: T13/T25.

## Global Constraints

- **Additiv:** `issue-conventions.enabled` Default `false`; fehlt die Sektion oder ist sie
  `false`, sind `build_variables()`-Ausgabe, gerenderte Agenten, `GIT_ISSUE_NAMING_BLOCK` und
  `--validate` byte-identisch zu `aaed14c2`.
- **Kein neuer Top-Level-Zwang:** Top-level bleibt `additionalProperties: true`
  (`config/project-config.schema.json:2854`); strikt ist nur die neue Sektion (AC-1). Die
  globale Striktheit ist #1141, nicht #1188.
- **Provider-Agnostik:** Verzweigung ausschließlich über Capability-Flags. In
  `scripts/lib/issue_adapters.py` und `scripts/lib/issue_conventions.py` darf kein
  Provider-Name als Literal im Kontrollfluss stehen; die Namen leben ausschließlich in
  `config/issue-adapters.yaml`. `scripts/lib/consistency/provider_literals.py` bleibt
  unverändert gültig.
- **Secrets:** Ausschließlich `auth.env` (Name der Env-Variable). Kein Token in
  `docs/issue-labels.md`, Rollen-Templates, `sync.log`, Fehlermeldungen, Diff-/Explain-Ausgabe
  oder im Admin-UI-Response (IC-6, AC-8). Zusätzlich gelten die Transport-Regeln H-1…H-7 aus
  Spec §4.12 **immer** (HTTPS-Zwang mit Loopback-Ausnahme, Host-/Scheme-Pinning, relative Pfade,
  keine Redirects, `auth.header` nur mit `{token}`); kein Config-Schlüssel und kein CLI-Flag
  schaltet sie ab.
- **URL-Kodierung:** `{name}`/`{id}` gehen ausschließlich über `build_target_url()` mit
  `quote(value, safe="")` in die URL; projizierte Namen bleiben unkodiert (K-7). Ein Test mit
  `type/bug` **und** `area/core` ist Pflicht.
- **Zustand:** genau eine persistierte Datei, `.meta-config/issue-labels-state.json`
  (Spec IC-8), geschrieben **nur** von `--apply`. Sie ist kein Diff-Cache; ohne sie gibt es
  keine **manifest-basierten** Löschkandidaten (K-9), `sync.prune-allow` wirkt unabhängig
  (IC-5, RVW2-1188-01). Kein Token, nur projizierte Namen + Hash.
- **Commit-Ownership (D13/K-16):** kein Auto-Commit, kein `git`-Aufruf im CLI-Pfad; `--apply`
  druckt die geänderte Datei in der Ergebnis-Tabelle, den Commit macht der `git`-Schritt.
  CI-`--apply`-Jobs committen **nie**.
- **Drift-Baseline (D11/K-14):** `docs/issue-labels.md` (und später die Tracker-Templates) wird in
  `.meta-config/generated-file-hashes.json` registriert; manuelle Edits werden beim Sync
  überschrieben und gemeldet. Die Baseline wird vom Capture-Stage geschrieben, nie handeditiert.
- **Wave-Reihenfolge (verbindlich):** `#1187 → #1186 → #1188 → #1181`, danach `#1141`, die
  Whitelist-Ableitung aus dem Schema zuletzt. Dieser Plan setzt die drei Vorgänger-Issues als
  gemergt voraus (Spec §11); `docs/issue-labels.md` ist `project-docs` (§11.1 der Spec).
- **Szenario-IDs:** `94` = #1181, `95`–`98` = #1187; #1188 belegt **keine** Katalog-ID in
  `tests/scenarios/registry.md` (der End-to-End-Test ist `tests/test_issue_labels_scenario_1188.py`).
- **stdlib only:** keine neue Dependency, `tests/requirements.txt` und `pyproject.toml`
  bleiben unangetastet. `urllib.request` mit `timeout=` wie im Bestand
  (`scripts/admin-server.py:2959-2963`, `:4388-4391`); **genau ein** Retry und nur bei `429` mit
  `Retry-After` (Cap 30 s, Default 1 s, injizierbare `sleep`); `5xx`/Timeouts ohne Retry (K-17, D14).
- **Python-Kompatibilität:** `from __future__ import annotations` bzw. `Optional[...]`; die
  Prüfungen `consistency/python_compat.py` (`--validate`) müssen grün bleiben (kein
  PEP-604 im Laufzeitpfad, keine Backslashes im f-String-Ausdruck).
- **Platzhalter-Registrierung:** Jede neue Builder-Variable **muss** in
  `_BUILTIN_VARS` (`scripts/lib/consistency/placeholders.py:12-139`, Konventionsblock
  `:114-123`) registriert werden. Der Ratchet `_UNREGISTERED_BUILDER_RATCHET` (`:273-284`)
  ist shrink-only und darf nicht erweitert werden — `check_builder_known_set` (`:314`)
  vergleicht die Builder-Ausgabe bei leerem Config-Dict gegen diese Menge.
- **Doku-Kopplung:** Neue `sync.py`-Flags sind Pflicht in `docs/api/cli-reference.md`
  (`scripts/lib/consistency/docs.py:9-44`); neue Admin-UI-Routen brauchen eine
  `<!-- help-id: … -->` in `docs/api/admin-ui-reference.md` (`:47-97`).
- **Commit-Disziplin:** ein Commit pro Task, Englisch, Conventional Commits, ≤ 72 Zeichen
  erste Zeile, Imperativ, **ohne BOM**. Kein Push, kein Tag, kein Merge (Rolle `git`).
- **Sprache:** Plan und Doku Deutsch; Code, Tests, Commit-Messages Englisch.

## File Structure

### Produktion — neu (5), generiert (1), persistiert (1), Plan-Dokument (1)

| Datei | neu/ändern | Zweck | Task |
|---|---|---|---|
| `config/issue-conventions-presets.yaml` | **neu** | Zwei Sektionen: `presets.<name>` (`default`, `minimal`, `conventional`) + `platform.<adapter>`; reine Daten (AC-2) | T2 |
| `config/issue-adapters.yaml` | **neu** | Adapter-Registry `github`/`gitlab`/`gitea` + `aliases` + `separator.single/multi` + `color-format` + `pagination` + `ids` + `capabilities` (AC-2b, AC-3, K-7) | T3 |
| `scripts/lib/issue_conventions.py` | **neu** | 7-Stufen-Resolver, Achsen-Gate, Projektion, Namensgrenzen, Block-/Doku-Renderer, `LEGACY_ROLE_BLOCKS` (K-1) | T2, T4–T9, T19, T25 |
| `scripts/lib/issue_adapters.py` | **neu** | Adapter-Loader, `select_adapter`, Transport-Härtung, `build_target_url`, `resolve_id_map`, `parse_remote_url`, `resolve_repository`, Diff/Apply, Manifest, Single-Axis, Create-Policy | T3, T15–T20 |
| `scripts/lib/consistency/issue_labels.py` | **neu** | Sechs Regeln (4 offline, 2 online) mit eigenen Check-IDs | T23 |
| `docs/issue-labels.md` | **generiert** | Menschliche Doku aus dem Resolver (AC-22), Marker-Kommentar, Ownership-Regel (IC-7), Abschnitt „Nicht Teil der Taxonomie" (D15); Datei-Set `project-docs`; drift-geprüft über `generated-file-hashes.json` (D11) | T25 |
| `.meta-config/issue-labels-state.json` | **persistiert** | Prune-Manifest (Spec IC-8): projizierte Namen + `sha256`, versioniert, nur von `--apply` geschrieben | T17, T21 |
| `docs/plans/2026-11-09-issue-label-taxonomy-plan.md` | **neu** | dieser Plan | — |

### Produktion — ändern (20)

| Datei | neu/ändern | Zweck | Task |
|---|---|---|---|
| `config/project-config.schema.json` | ändern | Sektion `issue-conventions` (`additionalProperties: false`) nach `conventions` (`:703-707`) einfügen; `$defs.taxonomyAxis` neben `$defs` (`:2855`) | T1 |
| `howto/configs/project.yaml.example` | ändern | Neue Sektion `issue-conventions` mit kommentierten Defaults (vollständige Optionsliste); Doku, kein Prüf-Gate, parametrisiert gepinnt | T1 |
| `templates/configs/project.yaml.example` | ändern | Dieselbe Sektion im Starter-Template; beide Beispiele bleiben deckungsgleich (RVW2-1188-02) | T1 |
| `scripts/lib/config.py` | ändern | In `_build_convention_variables()` (`:2673-2734`) Issue-Variablen setzen; `ISSUE_LANGUAGE` (`:2711-2722`) auf den Resolver umstellen, Semantik erhalten | T9 |
| `scripts/lib/agent_sync.py` | ändern | `_apply_role_issue_convention_overrides()` neu, Aufruf neben `:1459` | T10 |
| `scripts/lib/consistency/placeholders.py` | ändern | Neue Variablen in `_BUILTIN_VARS` (`:114-123`) registrieren | T9 |
| `scripts/sync.py` | ändern | Flag `--labels` + Modus-Eintrag in `_MODE_HANDLERS` (`:757-787`); `--apply` (`:482-484`) und `--check` (`:334-338`) wiederverwenden | T21 |
| `scripts/lib/cli_commands.py` | ändern | `_handle_labels(ctx)` neu; Exit 0/1/2; Import in `sync.py:68`-Block | T21 |
| `scripts/consistency-check.py` | ändern | Import (`:42-70`) + Aufruf in `run_checks` (`:224-273`) | T24 |
| `scripts/admin-server.py` | ändern | `issue-conventions` in `PROJECT_WRITABLE_SECTIONS` (`:234-259`); `SUPER_ADMIN_FILES` (`:205-215`); POST-Route `/api/labels/preview` (`:3719-3745`) + Handler | T26, T27 |
| `docs/ui/admin-ui.html` | ändern | Sidebar-Eintrag (`:1644`-Umfeld), `viewProjectIssueLabels`, `router.register` (`:11275`-Umfeld), `routeMap` (`:11370-11415`), Save via `saveProjectSection` (`:5960-5970`) | T26, T27 |
| `agents/1-generic/feedback.md` | ändern | §3-Matrix (`:39-48`) → `{{ISSUE_TAXONOMY_TABLE}}` | T11 |
| `agents/1-generic/meta-feedback.md` | ändern | §4-Label-Liste (`:44-48`) → `{{ISSUE_LABEL_MAP}}` | T12 |
| `agents/1-generic/bug-feature-analyzer.md` | ändern | Label-Schema (`:89`) + Prioritätsmatrix (`:91-97`) → `{{ISSUE_TAXONOMY_TABLE}}` / `{{ISSUE_TRIAGE_LABELS}}` | T13 |
| `agents/1-generic/git.md` | ändern | `{{GIT_ISSUE_NAMING_BLOCK}}` (`:149-151`) → `{{ISSUE_TITLE_FORMAT}}` + `{{ISSUE_CLOSING_KEYWORDS}}` + `{{ISSUE_TAXONOMY_TABLE}}` + `{{ISSUE_LABEL_MAP}}` | T14 |
| `docs/api/cli-reference.md` | ändern | `--labels`, `--apply`, `--check`, `--explain`, `--force`-Wechselwirkung dokumentieren (`:18`, `:27-28`) | T22 |
| `docs/api/admin-ui-reference.md` | ändern | `<!-- help-id: project_instance-issue_labels -->` (Muster `:306`) + Help-IDs der Framework-Sichten | T26, T27 |
| `scripts/lib/generated_file_drift.py` | ändern | Explizite Root-Level-Registrierung von `docs/issue-labels.md` (Muster `PLATFORM_DEFAULTS_RESOLVED_REL`, `:49`, Scan `:383-393`, Capture `:535-537`) — D11 | T25 |
| `.meta-config/generated-file-hashes.json` | ändern (generiert) | Baseline-Eintrag für `docs/issue-labels.md`; wird vom Sync-Capture geschrieben, **nie** handeditiert (D11) | T25 |
| `CHANGELOG.md` | ändern | `[Unreleased]`-Eintrag (Konvention; `crossrefs.changelog-*` prüft nur `agents/`/`commands/`, aber DoD) | T29 |

### Tests — neu (18)

| Datei | Zweck | Task |
|---|---|---|
| `tests/test_issue_conventions_schema.py` | Sektion geschlossen, Defaults, `$defs.taxonomyAxis`, `platform-overrides` geschlossen (RVW-1188-03) | T1 |
| `tests/test_issue_conventions_presets.py` | Zwei-Sektionen-Vertrag, Preset-Inhalte, kein Preset-Name im Code | T2 |
| `tests/test_issue_adapters_registry.py` | Drei Adapter, Capabilities, Alias, `pagination`/`ids` deklariert, Merge ohne Token, synthetischer vierter Adapter, Transport-Härtung beim Load (H-2/H-3/H-6) | T3 |
| `tests/test_issue_conventions_resolver.py` | Sieben Stufen (AC-14-Reihenfolge), `source`, Achsen-Gate, Projektion, Namensgrenzen | T5–T8 |
| `tests/test_issue_conventions_role_blocks.py` | Block-Render, Legacy je Rolle, Platzhalter-Registrierung | T9 |
| `tests/test_issue_conventions_golden.py` | Golden `enabled:false` über alle vier Rollen (AC-9) | T10 |
| `tests/test_issue_adapters_url.py` | Vier URL-Formen, unparsbar, Override, Env-Fallback | T15 |
| `tests/test_issue_adapters_http.py` | Auth-Header, Transport-Injektion, Token-Freiheit, Timeout, **URL-Quoting `type/bug`/`area/core`**, Host-Pinning, Redirect-Abbruch, `{token}`-Pflicht | T16 |
| `tests/test_issue_adapters_diff.py` | create/update/no-op, `prune`-Regel, Rename-Regel, `prune-allow` | T17 |
| `tests/test_issue_labels_state.py` | Manifest-Format, Schreiben nur bei `--apply`, Teilfehler, Fremdlabel im Präfix, fehlendes Manifest | T17 |
| `tests/test_issue_adapters_apply.py` | Teilfehler, 401-Abbruch, Single-Axis, drei Create-Modi, Idempotenz, Gitea-ID-Map | T18–T20 |
| `tests/test_issue_labels_cli.py` | Dry-Run/Apply/Check/Explain, Exitcodes, Nutzungsfehler, Manifest-Persistenz | T21 |
| `tests/test_issue_labels_consistency.py` | Sechs Regel-IDs über beide Kontexte, offline/online-Zuschnitt, still bei `enabled:false` | T23, T24 |
| `tests/test_issue_labels_docs.py` | Generierte Doku, Ownership-Marker, Drift-Registrierung (D11), Nicht-Taxonomie-Abschnitt (D15), kein Token | T25 |
| `tests/test_admin_ui_issue_labels_section.py` | Whitelist, PUT-Roundtrip, Preview-Route, Hilfetext | T26 |
| `tests/test_admin_ui_issue_labels_framework_views.py` | Read-only Framework-Sichten für Presets/Adapter | T27 |
| `tests/test_issue_labels_scenario_1188.py` | Voller Szenarientest mit gemocktem Tracker (Labels mit `/`, Prune, Teilfehler) | T28 |
| `tests/test_issue_labels_templates.py` | `templates.mode` off/scaffold/manage, `force`, Capability-Gating, kein Token (D12) | T30 |

### Tests — bewusst unverändert (1)

| Datei | Zweck | Task |
|---|---|---|
| `tests/test_conventions_migration_invariant.py` | **nicht** ändern (Anker). Der Golden-Test für Issue-Labels liegt in `test_issue_conventions_golden.py`, damit die bestehende Datei konfliktfrei bleibt | — |

### Optionale Tracker-Templates (T30, Pflicht-Task seit D12)

| Datei | Zweck | Task |
|---|---|---|
| `.github/ISSUE_TEMPLATE/<type>.yml` | GitHub Issue Form mit Pre-Labels (`issue-forms`) | T30 |
| `.gitlab/issue_templates/<Type>.md` | GitLab Issue Template (`issue-templates`) | T30 |
| `.gitea/ISSUE_TEMPLATE/<type>.md` | Gitea Issue Template (`issue-templates`) | T30 |

Erzeugt wird ausschließlich bei `issue-conventions.templates.mode != off` und nur für Dateien, die
die Adapter-Capability deckt; `scaffold` fasst bestehende Dateien nie an, `manage` nur
marker-tragende (oder `force: true`).

## pipeline_stages

Dieser Plan ist **noch an keine `plan-driven`-Stage gebunden**: Er ist DRAFT, die Spec ist
DRAFT, und die Wave `docs/config-wave-plans-1181-1188` führt ihn nicht über die
`feature-lifecycle`-Pipeline aus. Beim Übergang `DRAFT → IN PROGRESS` (nach Spec-Freigabe)
wird das Frontmatter ergänzt:

```yaml
pipeline_stages:
  implement: 1   # Stage `implement` (config/role-defaults.yaml:2678-2688) startet bei Task 1
```

Eine Bindung heute wäre eine Falschaussage: `implement` ist eine **einzige** Stage
(`config/role-defaults.yaml:2678-2688`), während dieser Plan 30 Tasks in 8 Meilensteinen
hat; die Task-zu-Agent-Zuordnung passiert über die `Agent:`-Felder der Task-Blöcke.

## Meilensteine

Jeder Meilenstein ist **einzeln grün** (baubar, `--validate` sauber) und hat ein
Zwischentest-Gate. Kein Meilenstein aktiviert die Sektion in `.meta-config/project.yaml`.

| # | Meilenstein | Tasks | Zwischentest-Gate |
|---|---|---|---|
| **M1** | Fundament: Schema, Presets, Adapterdaten, Validator | T1–T4 | `pytest tests/test_issue_conventions_schema.py tests/test_issue_conventions_presets.py tests/test_issue_adapters_registry.py` + `python3 scripts/sync.py --validate` rc 0 |
| **M2** | Resolver: 7 Stufen, `source`, Achsen-Gate, Projektion, Explain | T5–T8 | `pytest tests/test_issue_conventions_resolver.py` grün; `--validate` rc 0 (noch keine Template-Änderung) |
| **M3** | Rollen-Templates + Golden | T9–T14 | `pytest tests/test_issue_conventions_role_blocks.py tests/test_issue_conventions_golden.py` grün; `--validate` rc 0; der Golden-Test aus T10 belegt byte-identische Rollen-Ausgabe bei `enabled:false` — **kein** `git diff`-Gate (nach dem Commit vakuum-grün, RVW2-1188-03) |
| **M4** | Tracker: Identität, Transport-Härtung, URL-Kodierung, IDs, Diff, Manifest, Apply, Modi | T15–T20 | `pytest tests/test_issue_adapters_url.py tests/test_issue_adapters_http.py tests/test_issue_adapters_diff.py tests/test_issue_labels_state.py tests/test_issue_adapters_apply.py` grün, ohne Netzwerk |
| **M5** | CLI `--labels` + Doku-Pflicht | T21–T22 | `pytest tests/test_issue_labels_cli.py`; `--validate` rc 0 (inkl. `docs.cli_reference`); `--help` zeigt `--label` **und** `--labels` |
| **M6** | Consistency-Check | T23–T24 | `pytest tests/test_issue_labels_consistency.py`; `--validate` rc 0 **mit gepatchtem `urlopen`** |
| **M7** | Generierte Doku + Admin-UI | T25–T27 | `pytest tests/test_issue_labels_docs.py tests/test_admin_ui_issue_labels_section.py tests/test_admin_ui_issue_labels_framework_views.py`; `--validate` rc 0 (inkl. `docs.ui_help_mappings`); Preview-Route liefert Explain ohne Token |
| **M8** | Integration, Szenario, Doku-Abschluss, Templates | T28–T30 | `tests/test_issue_labels_scenario_1188.py` und `tests/test_issue_labels_templates.py` grün; volle Suite; `--validate` rc 0; `--validate-spec-plan` nur noch mit dem erwarteten `spec_plan_approval_marker` (Spec-Status) |

## Tasks

> **Legende:** Die Task-IDs sind numerisch (`### Task 5:`), damit der Plan-Validator den
> Abhängigkeitsgraphen parst (`scripts/lib/consistency/spec_plan.py:587-624` normalisiert
> numerische IDs zu `task-<n>`). Die Prosa und die Tabellen in diesem Dokument verweisen
> weiterhin mit `T<n>` auf `### Task <n>` — `T5` = `Task 5`. Jeder Task nennt Rolle,
> Abhängigkeiten, Dateien, Interfaces, Schritte und Commit.

### Task 1: Schema-Sektion `issue-conventions` (IC-1, AC-1)

**Agent:** developer · **Depends on:** — · **Größe:** M
**Files:**
- Modify: `config/project-config.schema.json`
- Modify: `howto/configs/project.yaml.example`
- Modify: `templates/configs/project.yaml.example`
- Create: `tests/test_issue_conventions_schema.py`
**Interfaces:** Produces `properties["issue-conventions"]` und die `$defs` `taxonomyAxis`, `adapterApi`, `adapterIds`, `adapterPagination`, `adapterDefaults` (alle geschlossen); Consumes bestehende `$defs`-Konvention (`config/project-config.schema.json:2855`).

- [ ] Step 1: **Test zuerst** in `tests/test_issue_conventions_schema.py`: `test_section_is_closed` (unbekannter Schlüssel ⇒ Validierungsfehler), `test_taxonomy_axis_is_closed`, `test_defaults_match_ic1` (`enabled:false`, `preset:"default"`, `adapter:"inherit"`, `sync.prune:false`, `sync.prune-allow:[]`, `enforcement.single-axis-per-issue:"error"`, `templates.mode:"off"`, `templates.force:false`), `test_platform_overrides_declared` (Adapter-ID offen), `test_platform_override_value_is_closed` (unbekannter Schlüssel **je Adapter** ⇒ Fehler), `test_platform_override_accepts_transport_keys` (`base-url`, `api`, `ids`, `pagination`, `auth.header`, `defaults` valide; `auth.env`/`auth.token` ⇒ Fehler — RVW-1188-03), `test_create_enum`, `test_repository_subsection_closed_and_documented` (`repository` akzeptiert `owner`/`repo`/`project-id`, kein weiterer Schlüssel — D9), `test_templates_subsection_closed` (nur `mode`/`force`; `mode` ∈ `off|scaffold|manage`; `force` boolean, Default false — D12), `test_examples_contain_closed_section` (parametrisiert über `howto/configs/project.yaml.example` **und** `templates/configs/project.yaml.example`: YAML parsebar, `issue-conventions` ist vorhanden und enthält nur IC-1-Schlüssel inkl. `repository` und `templates` — RVW2-1188-02). Lauf → **rot** (Sektion fehlt in Schema **und** beiden Beispielen).
- [ ] Step 2: Sektion wortgleich zu IC-1 nach `conventions` (`:703-707`), also vor `debug-mode` (`:708`) einfügen; `#/$defs` ergänzen: `taxonomyAxis` (`enabled`, `cardinality`, `color`, `label-case`, `max-length`, `allowed-pattern`, `values`), `adapterApi`, `adapterIds`, `adapterPagination`, `adapterDefaults` — alle mit `additionalProperties: false`, ebenso `platform-overrides.<adapter>` (nur der Adapter-ID-Schlüssel bleibt offen) und `templates` (D12).
- [ ] Step 3: Dieselbe Sektion in **beide** Beispiel-Dateien (`howto/configs/project.yaml.example`, `templates/configs/project.yaml.example`) ergänzen — kommentierte Defaults, gleiche Schlüssel wie IC-1 (inklusive `repository: {owner, repo}` als auskommentiertes Beispiel und `templates: {mode: off, force: false}`), Einfügeposition nach `conventions-preset`/`conventions`. Die Beispiele sind Doku, kein Prüf-Gate; der parametrisierte Test hält sie trotzdem deckungsgleich (RVW2-1188-02).
- [ ] Step 4: `taxonomyAxis`-Defaults dokumentieren (`cardinality`, `label-case:"lower"`, `max-length:50`, `allowed-pattern` leer = keine Prüfung); in der Sektionsbeschreibung vermerken, dass `platform-overrides.<adapter>` der **einzige** Ort für Projekt-Overrides inklusive Transport ist (Spec §4.5/IC-1), dass `repository` die Stufe 0 der Identitäts-Präzedenz ist (D9) und `templates.mode` die drei Stufen aus §4.9 steuert (D12).
- [ ] Step 5: Lauf: `python3 -m pytest tests/test_issue_conventions_schema.py --basetemp="$PYTEST_BASETEMP" -q` → **grün**; `python3 scripts/sync.py --validate` → **rc 0** (Sektion ist additiv).
- [ ] Step 6: Commit `feat: add closed issue-conventions schema section`.

### Task 2: Preset-Datei + Loader (IC-2, AC-2)

**Agent:** developer · **Depends on:** — · **Größe:** M
**Files:**
- Create: `config/issue-conventions-presets.yaml`
- Create: `scripts/lib/issue_conventions.py` (neu; in diesem Task nur der Loader)
- Create: `tests/test_issue_conventions_presets.py`
**Interfaces:** Produces `load_issue_presets(agent_meta_root: Path) -> dict` und `load_platform_defaults(agent_meta_root: Path) -> dict`; Consumes `_load_yaml_or_json` (`scripts/lib/io.py:60`).

- [ ] Step 1: **Test zuerst**: `test_two_sections_only` (`set(data) == {"presets","platform"}`), `test_default_preset_has_three_axes` (type single/area multi disabled/priority single), `test_minimal_is_type_only` (area+priority `enabled:false`, `values:{}`), `test_conventional_has_mapping_only`, `test_platform_separators` (gitlab `{single:"::",multi:"-"}`), `test_platform_section_is_projection_only` (kein `taxonomy`/`mapping` unter `platform` — AC-14-Stufen 4/5 trennen Inhalt von Projektion), `test_no_preset_name_in_python` (grep: `"minimal"`/`"conventional"` kommen in `scripts/lib/issue_conventions.py` nicht als Literal vor).
- [ ] Step 2: YAML exakt nach IC-2 anlegen (Farben/Beschreibungen aus der Spec); `platform.gitlab.defaults.separator.single: "::"`, `platform.github`/`gitea` `"/"`, `color-format` je Plattform.
- [ ] Step 3: Loader implementieren; `_`-Präfix-Keys filtern (Muster `scripts/lib/conventions.py:39-40`).
- [ ] Step 4: Lauf → **grün**; `--validate` rc 0.
- [ ] Step 5: Commit `feat: add declarative issue-conventions presets`.

### Task 3: Adapter-Datei + Registry-Loader (IC-3, AC-2b-Daten, AC-3)

**Agent:** developer · **Depends on:** — · **Größe:** M
**Files:**
- Create: `config/issue-adapters.yaml`
- Create: `scripts/lib/issue_adapters.py` (neu; in diesem Task nur Registry + Härtungs-Load)
- Create: `tests/test_issue_adapters_registry.py`
**Interfaces:** Produces `AdapterConfig` (dataclass mit `auth_env`, `auth_header`, `base_url`, `defaults`, `api`, `ids`, `pagination`, `capabilities`, `aliases`), `load_issue_adapters(agent_meta_root, config) -> dict[str, AdapterConfig]`, `select_adapter(adapters, configured, config) -> AdapterConfig`, `resolved_adapter_dump(adapter) -> dict`; Consumes `_deep_merge` (`scripts/lib/io.py:39`).

- [ ] Step 1: **Test zuerst**: `test_three_adapters_present`, `test_capabilities_sets` (`github` ⊇ `labels`,`issue-labels`,`issue-forms`; `gitlab` ⊇ `scoped-labels`,`issue-templates`; `gitea` ⊇ `issue-templates`), `test_separator_per_cardinality`, `test_codeberg_alias_selects_gitea` (K-3), `test_every_adapter_declares_pagination` (K-7), `test_gitea_declares_ids` (`ids == {op: "list", key: "id"}`; `update`/`delete` pfade enthalten `{id}` — RVW-1188-01), `test_project_override_merges_without_token` (konkret: `issue-conventions.platform-overrides.gitea.base-url` mit gleichem Host, nur Pfad — RVW-1188-03), `test_token_key_rejected` (`auth.token` ⇒ `IssueConfigError`), `test_synthetic_fourth_adapter_from_yaml` (Fixture-Adapter `forgejo-x` nur in YAML, `kind: http`), `test_dump_contains_only_auth_env` (AC-8-Vorstufe), `test_http_base_url_rejected` (H-1), `test_loopback_http_allowed` (H-1-Ausnahme für Tests), `test_host_change_rejected` (H-2: `base-url` mit fremdem Host ⇒ `IssueConfigError`), `test_absolute_path_rejected` (H-3: `path: "https://evil.example/x"`/`"//evil"`/`"../x"`), `test_header_without_token_placeholder_rejected` und `test_header_with_literal_credential_rejected` (H-6).
- [ ] Step 2: YAML nach IC-3 anlegen; `aliases: {Codeberg: gitea}`; `base-url` mit `{GITEA_URL}`-Platzhalter (Env, kein Secret); `pagination` je Adapter; `ids` nur bei `gitea`. Die `capabilities` (`issue-forms`/`issue-templates`) sind zugleich der **einzige** Steuerinput für die Template-Erzeugung in T30 (D12) — kein Provider-Name, keine separate Schalterliste.
- [ ] Step 3: Loader + Merge implementieren: Projekt-Overrides ausschließlich aus `issue-conventions.platform-overrides.<adapter>` (`base-url` nur Pfad, `api.*`, `ids`, `pagination`, `auth.header`, `defaults`); `auth.env` ist pflichtig und **nicht** überschreibbar; `auth.token`/`auth.password` sind harte Fehler; H-1/H-2/H-3/H-6 werden beim Laden geprüft, nicht erst beim Request.
- [ ] Step 4: Lauf → **grün**; `--validate` rc 0.
- [ ] Step 5: Commit `feat: add yaml-driven tracker adapter registry`.

### Task 4: Konfigurations-Validator (AC-12, AC-13)

**Agent:** developer · **Depends on:** 1, 2, 3 · **Größe:** S
**Files:**
- Modify: `scripts/lib/issue_conventions.py`
- Create/Modify: `tests/test_issue_conventions_schema.py`
**Interfaces:** Produces `IssueConfigError(ValueError)` und `validate_issue_conventions(resolved: ResolvedTaxonomy) -> None`; Consumes `ResolvedTaxonomy` (T5-Modell, hier als Stub-Typ eingeführt).

- [ ] Step 1: **Test zuerst**: `test_enabled_axis_with_empty_values_fails` (AC-12), `test_enabled_with_no_active_axis_fails` (AC-12), `test_type_axis_disabled_warns_not_raises` (AC-13, `warnings`-Tupel enthält den Best-Practice-Satz), `test_invalid_allowed_pattern_fails`, `test_multi_axis_with_scoped_separator_is_allowed_but_documented`.
- [ ] Step 2: Validator implementieren; Fehlermeldungen nennen Achse, Pfad und geforderten Zustand (kein nacktes `ValueError`).
- [ ] Step 3: Lauf → **grün**.
- [ ] Step 4: Commit `feat: validate issue taxonomy cardinality and axis toggles`.

### Task 5: Siebenstufiger Resolver mit `source` (AC-14, AC-15)

**Agent:** senior-developer · **Depends on:** 2, 3, 4 · **Größe:** L
**Files:**
- Modify: `scripts/lib/issue_conventions.py`
- Create: `tests/test_issue_conventions_resolver.py`
**Interfaces:** Produces `resolve_issue_conventions(config, agent_meta_root, *, adapter=None) -> ResolvedTaxonomy` mit `SourcedValue(value, source)` je Schlüssel, `Axis.source`, `AxisValue.source`, `Projection.sources`; Consumes `load_issue_presets` (T2), `load_issue_adapters`/`select_adapter` (T3), `git.platform` (`scripts/lib/config.py:1717`).

- [ ] Step 1: **Test zuerst** — Präzedenzmatrix mit je einem Test pro Stufe: `test_level1_project_platform_override_wins`, `test_level2_project_wins`, `test_level3_project_preset_source`, `test_level4_framework_platform_source`, `test_level5_framework_preset_source`, `test_level6_adapter_default_source`, `test_level7_schema_default_source`; dazu `test_ac14_order_platform_beats_preset` (derselbe Schlüssel in `platform.<adapter>` und `presets.default` ⇒ Plattform gewinnt, `source == "framework:platform:<adapter>"`; RVW-1188-02/K-10), `test_project_beats_platform_for_enabled` (AC-15: Framework deaktiviert `area`, Projekt aktiviert ⇒ `enabled is True` **und** beide Quellen in `sources`), `test_platform_default_never_renames` (nicht darstellbarer Wert ⇒ `warning`, kein stilles Umbenennen), `test_source_strings_exact` (die sieben Literale aus §4.3 der Spec, stufenfest).
- [ ] Step 2: Flachmachen der Schlüsselpfade (`taxonomy.<axis>.<key>`, `taxonomy.<axis>.values.<name>.<key>`, `mapping.<k>`, `defaults.*`, Projektionsschlüssel) und generisches `_resolve_key(path) -> SourcedValue` über die sieben Stufen.
- [ ] Step 3: Stufe 3 vs. 5 unterscheiden: explizites Projekt-`preset:` ⇒ `project:preset:<n>` (Stufe 3), sonst Framework-Preset ⇒ `preset:<n>` (Stufe 5). Stufe 4 (`framework:platform:<adapter>`) bleibt unberührt und behält ihren Test (RVW2-1188-04).
- [ ] Step 4: Achsen-Gate **vor** der Projektion anwenden (deaktivierte Achse: keine Werte, keine Projektion, kein Source-Eintrag).
- [ ] Step 5: Lauf → **grün** (≥ 12 Tests).
- [ ] Step 6: Commit `feat: resolve issue taxonomy across seven precedence levels`.

### Task 6: Achsen-Gate und `enabled:false` (AC-9, AC-11)

**Agent:** developer · **Depends on:** 5 · **Größe:** M
**Files:**
- Modify: `scripts/lib/issue_conventions.py`
- Modify: `tests/test_issue_conventions_resolver.py`
**Interfaces:** Produces `ResolvedTaxonomy.enabled: bool` und `active_axes() -> tuple[Axis, ...]`; Consumes T5-Resolver.

- [ ] Step 1: **Test zuerst**: `test_area_disabled_yields_no_labels` (AC-11: keine `area`-Werte, leere Soll-Menge, kein Drift-Kandidat, `type`/`priority` unverändert), `test_disabled_returns_neutral_model` (`enabled is False`, `axes == {}`, `mapping == {}`, keine Projektion), `test_language_still_resolves_when_disabled` (die heutige `ISSUE_LANGUAGE`-Semantik aus `scripts/lib/config.py:2711-2722` bleibt).
- [ ] Step 2: Gate implementieren; bei `enabled:false` **kein** Separator-Resolve und **keine** Repository-Auflösung (K-4).
- [ ] Step 3: Lauf → **grün**.
- [ ] Step 4: Commit `feat: gate inactive issue axes before projection`.

### Task 7: Projektion + Namensgrenzen (AC-2b, AC-20)

**Agent:** senior-developer · **Depends on:** 3, 5 · **Größe:** L
**Files:**
- Modify: `scripts/lib/issue_conventions.py`
- Modify: `tests/test_issue_conventions_resolver.py`
**Interfaces:** Produces `project_label(axis, value, projection) -> str` und `validate_label_name(name, projection) -> None`; Consumes `AdapterConfig.defaults` (T3), `Projection` (T5).

- [ ] Step 1: **Test zuerst**: `test_gitlab_type_uses_double_colon` (`type::bug`), `test_gitlab_area_uses_single_dash` (`area-core`, **nicht** `area::core`; AC-2b), `test_github_uses_slash` (`type/bug`), `test_projected_name_stays_unencoded` (`type/bug` und `area/core` enthalten **kein** `%2F` und kein `%`; die Kodierung passiert erst im Transport — K-7), `test_color_format_per_adapter` (`#d73a4a` für gitlab/gitea, `d73a4a` für github), `test_label_case_lower`, `test_max_length_exceeded_fails_before_http` (51 Zeichen ⇒ `IssueConfigError`, Transport-Callcount 0; AC-20), `test_allowed_pattern_violation_fails` (`^[a-z0-9][a-z0-9/_-]*$`), `test_separator_is_object_form_only` (Projekt-`defaults.separator: {single, multi}` ist gültig; ein String `defaults.separator: "/"` und das entfernte `defaults.label-separator` sind Schema-Fehler — K2), `test_axis_level_override_beats_adapter_default`.
- [ ] Step 2: Projektion implementieren: Separator je `cardinality` (`single`/`multi`), Case-Normalisierung, `color-format`, dann Grenzprüfung (`len`, `re.fullmatch`).
- [ ] Step 3: Grenzprüfung **im Resolve**, nicht im HTTP-Pfad; Fehlertext nennt Achse, Wert, Grenze und den aufgelösten `source`.
- [ ] Step 4: Lauf → **grün**; `--validate` rc 0.
- [ ] Step 5: Commit `feat: project label names per cardinality and adapter limits`.

### Task 8: `--explain`-Modell (AC-14)

**Agent:** developer · **Depends on:** 5 · **Größe:** S
**Files:**
- Modify: `scripts/lib/issue_conventions.py`
- Modify: `tests/test_issue_conventions_resolver.py`
**Interfaces:** Produces `render_explain(resolved) -> list[str]`; Consumes `SourcedValue`/`AxisValue.source`.

- [ ] Step 1: **Test zuerst**: `test_explain_lines` — exakt `type/bug ← preset:default`, `priority/P2 ← preset:default`, `area ← project`, `separator ← adapter:gitlab` (drei Achsen **und** Werte, nicht nur ein Config-Dump), `test_explain_shows_platform_stage_four` (ein Schlüssel aus `platform.gitlab` meldet `framework:platform:gitlab`, nicht `preset:default` — RVW-1188-02), `test_explain_shows_both_sources_for_overruled_platform_default` (AC-15).
- [ ] Step 2: Renderer implementieren, stabil sortiert (Achse, dann Wert).
- [ ] Step 3: Lauf → **grün**.
- [ ] Step 4: Commit `feat: explain resolved issue labels with their source`.

### Task 9: Template-Blöcke + Legacy-Konstanten + Registrierung (AC-6, AC-9)

**Agent:** senior-developer · **Depends on:** 6, 7 · **Größe:** M
**Files:**
- Modify: `scripts/lib/issue_conventions.py`
- Modify: `scripts/lib/config.py`
- Modify: `scripts/lib/consistency/placeholders.py`
- Create: `tests/test_issue_conventions_role_blocks.py`
**Interfaces:** Produces `render_taxonomy_table(resolved)`, `render_label_map(resolved)`, `render_title_format(resolved)`, `render_closing_keywords(resolved)`, `render_triage_labels(resolved)`, `TRIAGE_LABELS: tuple[str, str]` (Framework-Konstante `("triage", "needs-info")`, D15/K-18), `LEGACY_ROLE_BLOCKS: dict[str, dict[str, str]]`; Consumes `_build_convention_variables()` (`scripts/lib/config.py:2673-2734`).

- [ ] Step 1: **Test zuerst**: `test_enabled_table_has_all_axes_and_values`, `test_disabled_block_is_role_legacy` (vier Rollen, vier verschiedene Alt-Texte; K-1), `test_new_vars_registered` (`ISSUE_TAXONOMY_TABLE`, `ISSUE_LABEL_MAP`, `ISSUE_TITLE_FORMAT`, `ISSUE_CLOSING_KEYWORDS`, `ISSUE_TRIAGE_LABELS`, `ISSUE_TAXONOMY_ENABLED` in `_BUILTIN_VARS`), `test_build_variables_with_empty_config_does_not_raise` (K-4), `test_triage_labels_are_a_framework_constant` (`TRIAGE_LABELS == ("triage", "needs-info")`, nicht aus `taxonomy.*`/Projekt-Config ableitbar — D15), `test_triage_labels_are_not_in_desired_set` (`build_desired_labels` enthält weder `triage` noch `needs-info`).
- [ ] Step 2: Sechs Variablen in `_build_convention_variables()` setzen — **immer** (auch bei `enabled:false`), damit `check_placeholders` nie eine unbekannte Variable sieht; Werte im Disabled-Fall = `LEGACY_ROLE_BLOCKS["__default__"]` (neutral).
- [ ] Step 3: `ISSUE_LANGUAGE` auf `resolved.language` umstellen, Fallback `"english"` beibehalten (Semantik aus `:2711-2722` unverändert).
- [ ] Step 4: Registrierung in `_BUILTIN_VARS` (`:114-123`); **nicht** in `_UNREGISTERED_BUILDER_RATCHET` (shrink-only, `:273-284`).
- [ ] Step 5: Lauf: `pytest tests/test_issue_conventions_role_blocks.py` → **grün**; `python3 scripts/sync.py --validate` → **rc 0** (insbesondere `placeholders.builder-known-set`).
- [ ] Step 6: Commit `feat: render issue taxonomy blocks from the resolver`.

### Task 10: Per-Rollen-Legacy-Overlay (AC-6, AC-9)

**Agent:** senior-developer · **Depends on:** 9 · **Größe:** M
**Files:**
- Modify: `scripts/lib/agent_sync.py`
- Create: `tests/test_issue_conventions_golden.py`
**Interfaces:** Produces `_apply_role_issue_convention_overrides(merged_vars, role, resolved_blocks)`; Consumes den Aufrufpunkt `scripts/lib/agent_sync.py:1458-1459` (Muster `_apply_role_auto_commit_overrides`, `:92-123`).

- [ ] Step 1: **Golden-Baseline einfrieren:** vor der Änderung die vier gerenderten Rollen-Dateien aus HEAD `aaed14c2` erzeugen und als Strings in `tests/test_issue_conventions_golden.py` ablegen (nur die betroffenen Abschnitte).
- [ ] Step 2: **Test zuerst**: `test_feedback_block_byte_identical_when_disabled`, `test_meta_feedback_block_byte_identical_when_disabled`, `test_bug_feature_analyzer_block_byte_identical_when_disabled`, `test_git_issue_block_byte_identical_when_disabled`, `test_enabled_blocks_are_role_independent` (bei `enabled:true` erhalten alle vier dieselbe Taxonomie-Tabelle).
- [ ] Step 3: Overlay-Funktion implementieren; Aufruf direkt nach `:1459`. Die Funktion ersetzt die sechs Variablen **nur** für die vier Rollen und **nur** im Disabled-Fall durch `LEGACY_ROLE_BLOCKS[role]`.
- [ ] Step 4: Lauf → **grün**; zusätzlich `pytest tests/test_conventions_migration_invariant.py` → unverändert grün.
- [ ] Step 5: Commit `feat: keep disabled-mode role text byte-identical`.

### Task 11: `feedback.md` auf die Taxonomie umstellen (AC-6)

**Agent:** developer · **Depends on:** 10 · **Größe:** S
**Files:**
- Modify: `agents/1-generic/feedback.md`
- Modify: `tests/test_issue_conventions_role_blocks.py`
**Interfaces:** Consumes `{{ISSUE_TAXONOMY_TABLE}}`; Produces keine neuen Symbole.

- [ ] Step 1: **Test zuerst**: `test_feedback_has_no_label_literal` (Backtick-Literale `` `bug` ``, `` `enhancement` ``, `` `improvement` ``, `` `documentation` ``, `` `security` ``, `` `question` `` kommen im Template **nicht** mehr vor), `test_feedback_uses_taxonomy_table`.
- [ ] Step 2: §3-Matrix (`:39-48`) durch `{{ISSUE_TAXONOMY_TABLE}}` ersetzen; §6-Befehl (`:62-69`) behält `--label "<label>"` (kein Literal).
- [ ] Step 3: Lauf → **grün**; Golden aus T10 bleibt grün.
- [ ] Step 4: Commit `refactor: feed feedback agent labels from the taxonomy`.

### Task 12: `meta-feedback.md` auf die Taxonomie umstellen (AC-6)

**Agent:** developer · **Depends on:** 10 · **Größe:** S
**Files:**
- Modify: `agents/1-generic/meta-feedback.md`
- Modify: `tests/test_issue_conventions_role_blocks.py`
**Interfaces:** Consumes `{{ISSUE_LABEL_MAP}}` und `{{ISSUE_TAXONOMY_TABLE}}`.

- [ ] Step 1: **Test zuerst**: `test_meta_feedback_has_no_label_literal` (Liste `bug`/`enhancement`/`improvement`/`documentation`/`design`/`feature-request` in `:46` verschwindet), `test_meta_feedback_uses_label_map`.
- [ ] Step 2: §4 (`:44-48`) durch die zwei Platzhalter ersetzen; die Severity-Zeile (`:48`) auf `{{ISSUE_TAXONOMY_TABLE}}`-Prioritätswerte verweisen (F-2-Vorbereitung).
- [ ] Step 3: Lauf → **grün**; Golden grün.
- [ ] Step 4: Commit `refactor: feed meta-feedback labels from the taxonomy`.

### Task 13: `bug-feature-analyzer.md` auf die Taxonomie umstellen (AC-6)

**Agent:** developer · **Depends on:** 10 · **Größe:** S
**Files:**
- Modify: `agents/1-generic/bug-feature-analyzer.md`
- Modify: `tests/test_issue_conventions_role_blocks.py`
**Interfaces:** Consumes `{{ISSUE_TAXONOMY_TABLE}}` und `{{ISSUE_TRIAGE_LABELS}}` (Framework-Konstante `TRIAGE_LABELS`, D15).

- [ ] Step 1: **Test zuerst**: `test_bfa_has_no_taxonomy_label_literal` (`` `bug` ``, `` `feature` ``, `` `P0` ``…`` `P3` `` als **Labels**), `test_bfa_keeps_category_words` (die Kategorien `BUG`/`FEATURE`/`USER-ERROR` in `:78-87` bleiben — sie sind Klassifikation, nicht Label), `test_bfa_uses_triage_labels` (`triage`/`needs-info` kommen aus `{{ISSUE_TRIAGE_LABELS}}`, nicht als Literal; D15), `test_bfa_has_no_triage_literal` (die beiden Wörter stehen **nirgends** als Backtick-Literal im Template).
- [ ] Step 2: Label-Schema (`:89`) und Prioritätsmatrix (`:91-97`) ersetzen; Kategorien-Tabelle unangetastet. Die Triage-Zeile referenziert ausschließlich `{{ISSUE_TRIAGE_LABELS}}` und sagt explizit „nicht Teil der Taxonomie" (D15).
- [ ] Step 3: Lauf → **grün**; Golden grün.
- [ ] Step 4: Commit `refactor: feed triage labels from the taxonomy`.

### Task 14: `git.md`-Block aus derselben Auflösung (AC-6, AC-9)

**Agent:** developer · **Depends on:** 10 · **Größe:** M
**Files:**
- Modify: `agents/1-generic/git.md`
- Modify: `tests/test_issue_conventions_role_blocks.py`
**Interfaces:** Consumes `{{ISSUE_TITLE_FORMAT}}`, `{{ISSUE_CLOSING_KEYWORDS}}`, `{{ISSUE_TAXONOMY_TABLE}}`, `{{ISSUE_LABEL_MAP}}`; `GIT_ISSUE_NAMING_BLOCK` bleibt berechnet (Rückwärtskompatibilität), wird aber nicht mehr referenziert.

- [ ] Step 1: **Test zuerst**: `test_git_block_byte_identical_when_disabled` (die drei Zeilen aus `_render_git_issue_naming`, `scripts/lib/conventions.py:288-291`, exakt reproduziert), `test_git_block_uses_projected_names_when_enabled`, `test_git_template_has_no_label_literal`.
- [ ] Step 2: `:149-151` durch die vier Platzhalter ersetzen (Reihenfolge so, dass der Disabled-Fall die heutige Zeilenfolge ergibt).
- [ ] Step 3: Lauf → **grün**; `pytest tests/test_conventions_migration_invariant.py tests/test_variable_builder_active_set.py` → grün (der Rolle-Gate-Fall `:81-89` bleibt unberührt, weil der Block weiter berechnet wird).
- [ ] Step 4: Commit `refactor: render git issue conventions from the taxonomy`.

### Task 15: Repository-Identität: Präzedenzkette aus Config, Git-Remote und CI-Env (AC-16, D9)

**Agent:** senior-developer · **Depends on:** 3 · **Größe:** M
**Files:**
- Modify: `scripts/lib/issue_adapters.py`
- Create: `tests/test_issue_adapters_url.py`
**Interfaces:** Produces `RepositoryIdentity(owner, repo, project_id, host)`, `parse_remote_url(url: str) -> RepositoryIdentity`, `parse_github_repository_env(value: str) -> Optional[RepositoryIdentity]`, `parse_ci_project_path(value: str) -> Optional[RepositoryIdentity]` und `resolve_repository(config, resolved, *, env=None) -> RepositoryIdentity` (**Präzedenz D9**); Consumes `git.remote-url`-Fallback (`scripts/lib/config.py:1718`), `GIT_REMOTE_URL_SET` (`:1747-1763`), `issue-conventions.repository.*` (IC-1), `os.environ`.

- [ ] Step 1: **Test zuerst**: `test_https_url` (`https://github.com/owner/repo.git`), `test_ssh_url` (`git@github.com:owner/repo.git`), `test_suffixless_url`, `test_gitlab_subgroup` (`https://gitlab.com/group/sub/repo` ⇒ `project_id == "group%2Fsub%2Frepo"`), `test_gitea_path_form`, `test_unparsable_raises_with_url_in_message` (AC-16: Meldung enthält die URL und niemals `owner == ""`); **Präzedenzkette (D9):** `test_repository_override_wins_over_remote` (`issue-conventions.repository.owner/repo` gesetzt, `git.remote-url` vorhanden ⇒ Override gewinnt), `test_remote_used_when_no_override`, `test_github_repository_env_fallback` (`git.remote-url` leer, `GITHUB_REPOSITORY=owner/repo` ⇒ Env gewinnt), `test_ci_project_path_fallback_gitlab` (`CI_PROJECT_PATH=group/sub/repo` ⇒ `project_id` URL-encoded), `test_env_without_slash_is_skipped_as_unparsable` (`GITHUB_REPOSITORY=foo` ⇒ wird übersprungen, nicht als `owner=foo`/`repo=""` akzeptiert), `test_all_sources_empty_raises_one_message_naming_three_ways` (Meldung enthält `repository`, `git.remote-url`, `GITHUB_REPOSITORY`/`CI_PROJECT_PATH`), `test_error_never_emits_empty_owner_or_repo` (Assertion auf den kompletten Fehlertext: keine leeren Wertfelder), `test_resolve_repository_never_reads_shell` (`subprocess` wird gepatcht auf `raise`; Repo-Containment).
- [ ] Step 2: Parser implementieren (regex-basiert, vier Formen, `host`-basiert auf `project_id` vs. `owner/repo` entscheiden — **kein** Provider-Name im Kontrollfluss; Alias-Auflösung bleibt Daten, K-3).
- [ ] Step 3: `resolve_repository` implementieren: strikte Präzedenz **repository-Override → `git.remote-url` → CI-Env → `IssueConfigError`** (K-12). Jede Quelle wird nur akzeptiert, wenn sie vollständig parsebar ist; unparsbare Quellen werden zugunsten der nächsten Stufe übersprungen. Lazy (K-4), nie in `build_variables`. Die Fehlermeldung ist **eine** Meldung, nennt alle drei Wege und enthält nie einen leeren `owner`/`repo`.
- [ ] Step 4: Lauf → **grün**.
- [ ] Step 5: Commit `feat: derive tracker repository identity from config, remote and ci env`.

### Task 16: HTTP-Executor, URL-Kodierung, IDs und Auth-Vertrag (AC-8, IC-3, IC-6, §4.12)

**Agent:** senior-developer · **Depends on:** 3, 15 · **Größe:** L
**Files:**
- Modify: `scripts/lib/issue_adapters.py`
- Create: `tests/test_issue_adapters_http.py`
**Interfaces:** Produces `HttpTransport` (Protocol), `UrllibTransport(timeout=15, sleep=time.sleep)`, `retry_delay(retry_after: Optional[str]) -> float` (Sekunden oder HTTP-Datum, Cap 30 s, Default 1 s — D14), `build_headers(adapter, token) -> dict`, `build_target_url(adapter, identity, op, *, fields, id_map=None) -> str`, `resolve_id_map(adapter, identity, transport) -> dict[str, str]`, `iter_pages(adapter, identity, transport) -> list[dict]`, `request(adapter, identity, op, **fields) -> tuple[int, Any]`; Consumes `auth.env`/`auth.header` (T3), `os.environ`, optional `.env` im Projektwurzelverzeichnis.

- [ ] Step 1: **Test zuerst**: `test_header_built_from_template` (`Authorization: Bearer <token>`, `PRIVATE-TOKEN: <token>`), `test_token_from_env_only`, `test_dotenv_read_without_echo`, `test_missing_token_raises_before_request` (keinen stillen anonymen Call), `test_no_token_in_error_message`, `test_no_token_in_resolved_dump`, `test_transport_is_injected` (Fake-Transport, kein Netz), `test_timeout_is_set` (15 s) — **Härtung/Kodierung (RVW-1188-01/-05):** `test_slash_label_is_percent_encoded` (`type/bug` ⇒ `.../labels/type%2Fbug`), `test_nested_slash_label_is_encoded` (`area/core` ⇒ `area%2Fcore`), `test_id_placeholder_uses_numeric_id` (Gitea-Mock: `PATCH /labels/42`, `DELETE /labels/42`, nie `.../type%2Fbug`), `test_id_map_resolved_once_per_run` (Callcount `list` == 1, unabhängig von der Label-Zahl), `test_pagination_reads_all_pages` (Mock liefert 100 + 3 Einträge ⇒ 103), `test_redirect_is_not_followed` (302 auf `https://evil.example` ⇒ Fehler, Auth-Header geht **nicht** an den zweiten Host, Callcount am zweiten Host == 0), `test_auth_header_not_sent_to_foreign_host` (Host-Pinning: Request-URL-Host ≠ `base-url`-Host ⇒ Abbruch vor dem Call) — **Retry-Policy (D14):** `test_429_retried_exactly_once` (zwei `429` hintereinander ⇒ genau 2 Calls, kein dritter), `test_retry_delay_uses_retry_after_seconds`, `test_retry_delay_parses_http_date`, `test_retry_delay_capped_at_30_seconds` (`Retry-After: 3600` ⇒ 30.0), `test_retry_delay_defaults_to_one_second` (Header fehlt/unparsbar), `test_500_is_not_retried`, `test_timeout_is_not_retried`, `test_sleep_is_injected` (`FakeSleep` protokolliert die Wartezeit, Test wartet nie real).
- [ ] Step 2: Transport implementieren; `base-url` expandieren (`{GITEA_URL}`), Pfad über `build_target_url` bauen: jedes `{…}`-Segment mit `quote(value, safe="")` einsetzen, `{id}` aus `id_map` (sonst `IssueConfigError`); Header-Template mit `{token}` substituieren; Body-Template mit `{name}`, `{color}`, `{description}`, `{owner}`, `{repo}`, `{project_id}` (Bodies werden **nicht** URL-kodiert). Retry-Abbildung: nur `429` ⇒ einmal `sleep(retry_delay(header))` und wiederholen; `5xx`/Timeout ⇒ sofort als Fehler zurück (K-17).
- [ ] Step 3: Redirects abschalten (eigener `HTTPRedirectHandler`, der `redirect_request` auf `None` setzt; 3xx wird als Fehler gewertet), Host/Scheme gegen den aufgelösten `base-url` prüfen (H-2/H-5), Maskierung wiederverwenden (`scripts/lib/env.py:130` `_mask`) für jede Log-Zeile.
- [ ] Step 4: Lauf → **grün** (kein `urlopen`-Aufruf im Test).
- [ ] Step 5: Commit `feat: add hardened http executor with url-encoded paths and numeric ids`.

### Task 17: Diff-Engine, Manifest-basiertes `prune`, Rename-Regel (AC-10, IC-5, IC-8)

**Agent:** senior-developer · **Depends on:** 7, 15, 16 · **Größe:** L
**Files:**
- Modify: `scripts/lib/issue_adapters.py`
- Create: `tests/test_issue_adapters_diff.py`
- Create: `tests/test_issue_labels_state.py`
**Interfaces:** Produces `build_desired_labels(resolved) -> dict[str, DesiredLabel]`, `label_diff(desired, actual, projection, *, prune, manifest, prune_allow) -> list[DiffEntry]`, `prune_candidates(actual, desired, manifest, prune_allow) -> tuple[list[DiffEntry], list[Finding]]`, `load_state(project_root) -> State`, `save_state(project_root, state, *, applied_names, adapter_id, repo_key) -> None`, `owned_prefixes(projection) -> tuple[str, ...]` (**nur** Klassifikation, nie Löschgrund); Consumes T7-Projektion, `sync.prune`/`sync.prune-allow` (IC-1).

- [ ] Step 1: **Test zuerst** (`tests/test_issue_adapters_diff.py`): `test_create_update_noop` (drei Zeilen), `test_prune_default_false` (AC-10: Tracker-Label außerhalb der Soll-Menge ⇒ **kein** `delete`), `test_prune_true_manifest_entry_deletes` (Label steht im Manifest eines früheren Laufs ⇒ `delete`), `test_prune_true_prune_allow_deletes` (`sync.prune-allow: [legacy-label]` ⇒ `delete`, ohne Manifest-Eintrag; die Allowlist wirkt auch ohne Manifest — RVW2-1188-01), `test_prune_never_deletes_foreign_label_inside_prefix` (**RVW-1188-04:** `type/needs-design` liegt im Präfix `type/`, steht nicht im Manifest und nicht in `prune-allow` ⇒ **kein** `delete`, nur `info: prune-candidate-unowned`), `test_prune_without_manifest_and_allow_deletes_nothing` (erster Lauf/neuer Klon **und** leere Allowlist ⇒ null Löschkandidaten + `info: prune-needs-manifest`; RVW2-1188-01), `test_prune_allow_does_not_bypass_prune_false` (Allowlist ohne `prune: true` löscht nichts), `test_disabled_axis_labels_never_deleted` (§4.4/IC-5: `area` deaktiviert, `area/core` steht im Manifest ⇒ **kein** Kandidat; Formel `(Manifest ∖ desired) ∖ labels(inaktiver Achsen)`, RVW2-1188-01), `test_candidate_set_is_manifest_minus_desired_minus_inactive` (Manifest mit `type/bug` (desired), `area/core` (inaktive Achse) und `legacy-label` ⇒ genau **ein** Kandidat `legacy-label`), `test_new_value_creates_and_reports_rename_candidate` (**D10:** neuer Wert ⇒ `create <neu>`, alter Wert im Manifest ⇒ `info: rename-candidate <alt>`), `test_no_rename_call_in_v1` (kein `update`-Aufruf mit `new_name`; `update`-Callcount für den alten Wert == 0), `test_old_value_leaves_desired_set_but_stays_in_tracker` (alter Wert fehlt in `desired`, das Tracker-Label bleibt unangetastet), `test_rename_line_is_never_emitted_in_v1` (Ausgabe enthält kein `rename <alt> -> <neu>`; die Zeile bleibt nur Vertrag), `test_check_never_emits_delete`.
- [ ] Step 2: **Test zuerst** (`tests/test_issue_labels_state.py`): `test_state_has_version_and_repo_key` (`version: 1`, `adapters.<id>.<owner/repo>.labels`), `test_state_stores_only_name_and_hash` (kein Token, keine Farbe im Klartext — nur `sha256`), `test_save_state_is_sorted_and_line_per_label` (stabile Schlüsselreihenfolge, ein Label je Zeile → merge-freundlich), `test_partial_apply_adds_only_successful_names` (drei ok, zwei 500 ⇒ nur die drei im Manifest), `test_missing_state_file_yields_empty_state`, `test_state_roundtrip_is_idempotent`.
- [ ] Step 3: Diff implementieren; Soll-Menge aus aktiven Achsen, Ist-Menge aus `list` (T16, paginiert), Manifest aus IC-8. Löschkandidaten über `prune_candidates` (K-9), nicht über den Präfix: `(Manifest ∖ desired) ∖ labels(inaktiver Achsen)`, plus `prune_allow` unabhängig vom Manifest (RVW2-1188-01). Ein nicht mehr gewünschter Wert, der im Manifest steht, erzeugt **ausschließlich** `info: rename-candidate <alt>` — kein `update.new_name`, kein `rename`-Diff-Eintrag (K-13/D10).
- [ ] Step 4: `save_state` implementieren: atomar schreiben (`.tmp`-Datei + `os.replace`), nur aus dem Apply-Pfad (T21) aufrufen; `owned_prefixes` ausschließlich für `info`/`warning`-Klassifikation der Consistency-Regeln 2 verwenden. Kein Commit, kein `git`-Aufruf aus diesem Pfad (D13/K-16) — die Datei wird geschrieben und dem `git`-Schritt übergeben.
- [ ] Step 5: Lauf → **grün**.
- [ ] Step 6: Commit `feat: diff tracker labels against a persisted prune manifest`.

### Task 18: Apply-Engine, Teilfehler, 401-Abbruch, Single-Axis (AC-7, AC-18, AC-19)

**Agent:** senior-developer · **Depends on:** 17 · **Größe:** L
**Files:**
- Modify: `scripts/lib/issue_adapters.py`
- Create: `tests/test_issue_adapters_apply.py`
**Interfaces:** Produces `apply_labels(adapter, identity, diff, *, transport, log) -> ApplyResult` (`entries`, `failed`, `aborted`, `exit_code`), `enforce_single_axis(adapter, labels) -> SingleAxisOutcome` (`allow`/`replace`/`refuse`); Consumes `capabilities` (T3).

- [ ] Step 1: **Test zuerst**: `test_partial_failure_keeps_other_labels` (fünf Labels, dritter Aufruf 500 ⇒ vier angewendet, Tabelle, `exit_code == 1`, **kein** Delete; AC-18), `test_401_aborts_after_first_call` (Callcount == 1, AC-19), `test_403_aborts_like_401`, `test_single_axis_scoped_replaces_second_type` (Adapter mit `scoped-labels` ⇒ genau ein `type::`-Wert im Soll-Set; AC-7), `test_single_axis_unscoped_refuses` (ohne `scoped-labels`, `enforcement.single-axis-per-issue: error` ⇒ `refuse`; AC-7), `test_single_axis_warn_mode_only_warns`, **Retry-Policy (D14/K-17):** `test_no_retry_for_500` (Callcount == 1), `test_no_retry_for_timeout` (Callcount == 1, `failed`-Eintrag), `test_retry_once_on_429_with_retry_after` (genau 2 Calls, dann Erfolg), `test_429_twice_fails_after_single_retry` (Callcount == 2, `failed`, weiter mit dem nächsten Label), `test_retry_still_aborts_on_401_after_retry` (Retry ändert den Auth-Abbruch nicht), `test_result_table_is_stable`.
- [ ] Step 2: Apply implementieren: sequenziell, Fehler sammeln, bei `401`/`403` sofort abbrechen; **kein** Rollback, **kein** Delete-Versuch. Retry-Logik lebt ausschließlich im Transport (T16): `apply_labels` wiederholt **nichts** selbst und zählt nur das Ergebnis; ein nach dem Retry weiterhin fehlgeschlagenes Label landet als `failed` in der Tabelle und führt zu Exit 1.
- [ ] Step 3: Single-Axis-Entscheidung **nur** über `"scoped-labels" in adapter.capabilities`; das Ergebnis fließt in den gerenderten Rollen-Block und in `enforce`.
- [ ] Step 4: Lauf → **grün**.
- [ ] Step 5: Commit `feat: apply label diffs with partial-failure and auth-abort semantics`.

### Task 19: `on-missing-label` in drei Modi (AC-17)

**Agent:** developer · **Depends on:** 5, 18 · **Größe:** S
**Files:**
- Modify: `scripts/lib/issue_adapters.py`
- Modify: `scripts/lib/issue_conventions.py`
- Modify: `tests/test_issue_adapters_apply.py`
**Interfaces:** Produces `creation_policy(mode: str) -> CreatePolicy` (`pre_sync: bool`, `omit_on_missing: bool`, `abort_on_missing: bool`) und `render_creation_policy(resolved) -> str` (wird an `render_label_map` angehängt — **keine** siebte Variable); Consumes `create.on-missing-label` (IC-1).

- [ ] Step 1: **Test zuerst**: `test_policy_warn_and_omit_is_default` (`omit=True`, `abort=False`, `pre_sync=False`, AC-17), `test_policy_create_runs_sync_first` (`pre_sync=True` ⇒ gerenderter Hinweis nennt `sync.py --labels --apply`), `test_policy_fail_aborts`, `test_rendered_block_names_all_three_modes`.
- [ ] Step 2: Policy + Renderer implementieren.
- [ ] Step 3: Lauf → **grün**.
- [ ] Step 4: Commit `feat: add three-mode missing-label policy for issue creation`.

### Task 20: Idempotenz (AC-4)

**Agent:** developer · **Depends on:** 18 · **Größe:** S
**Files:**
- Modify: `tests/test_issue_adapters_apply.py`
**Interfaces:** Consumes T17/T18.

- [ ] Step 1: **Test zuerst**: `test_second_apply_is_all_noop` (Mock-Tracker hält Zustand; zweiter `apply` ⇒ ausschließlich `no-op`, `exit_code == 0`).
- [ ] Step 2: Falls nötig Vergleichsnormalisierung (Farbe case-insensitiv, Beschreibung exakt) — **keine** Sonderfälle pro Adapter.
- [ ] Step 3: Lauf → **grün**.
- [ ] Step 4: Commit `test: pin label sync idempotency`.

### Task 21: CLI `--labels` + Handler + Exitcodes (AC-4, AC-5)

**Agent:** senior-developer · **Depends on:** 5, 8, 17, 18, 19 · **Größe:** L
**Files:**
- Modify: `scripts/sync.py`
- Modify: `scripts/lib/cli_commands.py`
- Create: `tests/test_issue_labels_cli.py`
**Interfaces:** Produces `_handle_labels(ctx: _SyncContext) -> None` und das Flag `--labels`; Consumes `--apply` (`scripts/sync.py:482-484`), `--check` (`:334-338`), `_MODE_HANDLERS` (`:757-787`), `resolve_explain` (T8), `label_diff`/`apply_labels` (T17/T18), `load_state`/`save_state` (T17).

- [ ] Step 1: **Test zuerst**: `test_dry_run_writes_nothing` (AC-4; Fake-Transport zählt nur `list`), `test_apply_creates_labels`, `test_second_run_noop`, `test_check_exits_1_on_drift` (AC-5), `test_check_exits_0_when_clean`, `test_explain_exits_0`, `test_apply_and_check_is_usage_error` (Exit 2, kein HTTP), `test_resolve_error_exits_2_without_http` (AC-20-Kopplung), `test_transport_policy_violation_exits_2_without_http` (H-1/H-2/H-6 ⇒ Resolve-Fehler, Callcount 0), `test_apply_writes_manifest_and_check_does_not` (K-9: `--apply` schreibt `.meta-config/issue-labels-state.json`, `--check` lässt die Datei byte-identisch), **Commit-Ownership (D13/K-16):** `test_apply_prints_manifest_path_in_result_table` (letzte Zeile `wrote .meta-config/issue-labels-state.json`), `test_cli_never_invokes_git` (`subprocess`/`git`-Aufruf gepatcht auf `raise`; der Handler committet nie und ruft kein `git`), `test_help_distinguishes_label_and_labels` (F-3: beide Flags mit eindeutiger Beschreibung), `test_output_lines_are_create_update_noop`.
- [ ] Step 2: Flag mit `help=`-Text anlegen, **nicht** `--label` umbenennen; Modus-Eintrag als **erster** Eintrag nach `audit_config` (`:759`), damit `--labels` nicht in den Default-Sync fällt.
- [ ] Step 3: Handler implementieren: `sys.exit(0|1|2)` explizit; `ctx.read_only = True` für Dry-Run/Check/Explain; keine `env.*`-Scripts, kein `sync.log`-Schreiben im Read-only-Modus (Muster `_handle_audit_config`, `scripts/lib/cli_commands.py:756-788`). Im `--apply`-Pfad nach der Ergebnis-Tabelle `save_state(...)` aufrufen und den geschriebenen Pfad als letzte Tabellenzeile ausgeben (D13/K-16: schreiben + drucken, **nicht** committen, kein `git`-Aufruf). Der normale Sync-Pfad aktualisiert im selben Lauf die Drift-Baseline von `docs/issue-labels.md` über den Capture-Stage (D11/K-14) — kein zweiter, konkurrierender Schreibpfad.
- [ ] Step 4: Import in `scripts/sync.py:68`-Block ergänzen.
- [ ] Step 5: Lauf → **grün**.
- [ ] Step 6: Commit `feat: add sync --labels dry-run, apply, check and explain`.

### Task 22: Doku-Pflicht für die neuen Flags (AC-5, Konvention)

**Agent:** developer · **Depends on:** 21 · **Größe:** S
**Files:**
- Modify: `docs/api/cli-reference.md`
- Modify: `tests/test_issue_labels_cli.py`
**Interfaces:** Consumes `scripts/lib/consistency/docs.py:9-44` (Pflichtprüfung).

- [ ] Step 1: **Test zuerst**: `test_cli_reference_lists_labels_flags` (prüft `--labels`, `--explain` als Backtick-Flags).
- [ ] Step 2: Vier Zeilen in die Flags-Tabelle (`docs/api/cli-reference.md:18-28`-Umfeld) und einen Absatz zur `--label`/`--labels`-Abgrenzung (F-3).
- [ ] Step 3: Lauf: `python3 -m pytest tests/test_issue_labels_cli.py` → **grün**; `python3 scripts/sync.py --validate` → **rc 0** (kein `docs.cli_reference`-Finding).
- [ ] Step 4: Commit `docs: document the label taxonomy cli flags`.

### Task 23: Consistency-Modul `issue-label-taxonomy` (AC-5, AC-9)

**Agent:** senior-developer · **Depends on:** 5, 7, 11, 12, 13, 14 · **Größe:** L
**Files:**
- Create: `scripts/lib/consistency/issue_labels.py`
- Create: `tests/test_issue_labels_consistency.py`
**Interfaces:** Produces `check_issue_labels(root, project_config, *, tracker=None) -> list[Finding]` mit sechs Check-IDs; Consumes `resolve_issue_conventions` (`scripts/lib/issue_conventions.py`), `report.Finding`/`Severity` (`scripts/lib/consistency/report.py`).

- [ ] Step 1: **Test zuerst**, ein Test je Regel: `issue-labels.tracker-missing` (`info`), `issue-labels.tracker-unknown` (`warning`, nur eigener Namespace — Klassifikation über `owned_prefixes`, nicht als Löschgrund), `issue-labels.tracker-metadata-drift` (`warning` mit `source`), `issue-labels.template-literal` (`error`), `issue-labels.role-placeholder-missing` (`error`), `issue-labels.cardinality` (`error`). Dazu `test_silent_when_disabled` (AC-9: keine Findings bei `enabled:false`), `test_offline_rules_never_call_transport` (K-5), `test_online_rules_require_tracker_argument`, `test_all_six_rule_ids_reported_with_tracker` (**AC-5-Nachweis:** mit Tracker liefert dasselbe Modul alle sechs IDs; ohne Tracker genau 4–6).
- [ ] Step 2: Offline-Regeln 4–6 implementieren (Template-Grep auf Backtick-Label-Literale der aktiven Achsen; Platzhalter-Präsenz in den vier Rollen; Kardinalität aus dem Resolver).
- [ ] Step 3: Online-Regeln 1–3 implementieren, `tracker`-Parameter verpflichtend; ohne `tracker` keine Findings (kein Netz).
- [ ] Step 4: Lauf → **grün**.
- [ ] Step 5: Commit `feat: add issue-label-taxonomy consistency check`.

### Task 24: Registrierung + offline/online-Zuschnitt (AC-5, Q6)

**Agent:** developer · **Depends on:** 23 · **Größe:** S
**Files:**
- Modify: `scripts/consistency-check.py`
- Modify: `tests/test_issue_labels_consistency.py`
**Interfaces:** Consumes `run_checks` (`scripts/consistency-check.py:171-274`), Import-Block (`:42-70`).

- [ ] Step 1: **Test zuerst**: `test_run_checks_includes_offline_rules` (IDs 4–6 present), `test_validate_does_not_report_online_ids` (1–3 absent, AC-5-Kontext-Split), `test_labels_check_reports_all_six` (über `_handle_labels` mit Fake-Tracker), `test_validate_never_opens_network` (`urlopen` gepatcht auf `raise` ⇒ `--validate` rc 0; K-5).
- [ ] Step 2: Import + Aufruf **nur** mit `tracker=None` in `run_checks`; die Online-Regeln werden ausschließlich aus `_handle_labels` mit Tracker aufgerufen.
- [ ] Step 3: Lauf → **grün**; `python3 scripts/sync.py --validate` → **rc 0**.
- [ ] Step 4: Commit `feat: wire the label taxonomy check into validate offline`.

### Task 25: Generierte `docs/issue-labels.md` (AC-22, IC-7)

**Agent:** developer · **Depends on:** 5, 7, 9 · **Größe:** M
**Files:**
- Modify: `scripts/lib/issue_conventions.py`
- Modify: `scripts/lib/cli_commands.py` (Schreibpfad im Common Tail)
- Modify: `scripts/lib/generated_file_drift.py` (explizite Root-Level-Registrierung, D11)
- Modify: `.meta-config/generated-file-hashes.json` (Baseline-Eintrag, vom Capture-Stage geschrieben)
- Create: `tests/test_issue_labels_docs.py`
**Interfaces:** Produces `render_issue_labels_doc(resolved, project_name) -> str` und `write_issue_labels_doc(project_root, resolved, *, dry_run, force, log) -> bool`; Consumes `GENERATED_MARKER = "<!-- generated by agent-meta: issue-labels; do not edit -->"`, `PLATFORM_DEFAULTS_RESOLVED_REL`-Muster (`scripts/lib/generated_file_drift.py:49`, Scan `:383-393`, Capture `:535-537`).

- [ ] Step 1: **Test zuerst**: `test_doc_contains_every_active_value` (AC-22: je aktiver Achse jeder Wert mit projiziertem Label-Namen), `test_doc_marks_inactive_axes` (`area` als „deaktiviert", nicht als leer), `test_doc_lists_triage_labels_under_non_taxonomy` (Abschnitt „Nicht Teil der Taxonomie" enthält `triage` und `needs-info` mit Begründung — D15), `test_disabled_writes_nothing`, `test_handwritten_file_is_not_overwritten` (Warnung, kein Write; IC-7), `test_force_overwrites`, `test_marker_required_for_update`, `test_no_token_in_doc` (AC-8), **Drift-Registrierung (D11/K-14):** `test_doc_is_registered_in_generated_file_hashes` (nach dem Sync steht `docs/issue-labels.md` in `.meta-config/generated-file-hashes.json`), `test_manual_edit_is_detected_as_drift` (Datei nach dem Sync ändern ⇒ `scan_generated_file_drift` meldet sie), `test_manual_edit_is_overwritten_with_backup` (nächster Sync stellt den generierten Inhalt wieder her und legt `.sync-backup-*` an).
- [ ] Step 2: Renderer implementieren (Achsen-Tabelle, Mapping-Tabelle, Anwendungsregel, Abschnitt „Nicht Teil der Taxonomie" mit `TRIAGE_LABELS` aus T9/D15, `--explain`-Quellen als Fußnote).
- [ ] Step 3: Schreibpfad in den Common Tail von `_handle_sync` (`scripts/lib/cli_commands.py:1641`ff), nur bei `enabled:true`; `dry_run` schreibt nichts. Danach den Pfad in `scripts/lib/generated_file_drift.py` als Root-Level-Ausnahme registrieren (D11); der Baseline-Eintrag entsteht beim Capture-Stage, nicht durch Handedit.
- [ ] Step 4: Lauf → **grün**; `--validate` rc 0.
- [ ] Step 5: Commit `feat: generate issue label documentation from the resolver`.

### Task 26: Admin-UI-Sektion „Issue labels" (AC-21)

**Agent:** senior-developer · **Depends on:** 1, 5, 8 · **Größe:** L
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `docs/ui/admin-ui.html`
- Modify: `docs/api/admin-ui-reference.md`
- Create: `tests/test_admin_ui_issue_labels_section.py`
**Interfaces:** Produces `PROJECT_WRITABLE_SECTIONS += {"issue-conventions"}` (`scripts/admin-server.py:234-259`), `_route_post_labels_preview` (`/api/labels/preview` in `_POST_EXACT_ROUTES`, `:3719-3745`), `viewProjectIssueLabels` + Route `/project/issue-labels` (`docs/ui/admin-ui.html:11275`-Umfeld, Sidebar `:1644`, `routeMap` `:11370-11415`), Help-ID `project_instance-issue_labels`; Consumes `saveProjectSection` (`:5960-5970`), `render_explain` (T8).

- [ ] Step 1: **Test zuerst**: `test_section_is_writable` (AC-21), `test_put_section_roundtrip` (`PUT /api/config/project/section`), `test_preview_route_returns_explain_and_null_diff` (offline), `test_preview_never_includes_token` (AC-8; auch bei `?online=1`), `test_preview_disabled_returns_flag`, `test_preview_online_requires_pinned_host` (H-2: Preview mit fremdem `base-url`-Host ⇒ 409/`IssueConfigError`, kein Call), `test_help_id_present` (`docs.ui_help_mappings`), `test_route_registered_in_ui` (statischer Grep auf `router.register`/`routeMap`).
- [ ] Step 2: Server: Whitelist-Eintrag; Preview-Handler (read-only, kein Sync, kein Netz ohne explizites `?online=1`); der Online-Zweig nutzt **denselben** Transport wie `--labels` (H-1…H-7, T16) und liefert bei fehlendem Token/ungültigem Host einen Fehlerstatus statt eines anonymen Calls.
- [ ] Step 3: UI-View: Achsenliste mit `enabled`-Schalter, Wert-Tabelle (Name/Farbe/Beschreibung), Mapping-Tabelle, Adapter-Dropdown, Buttons **Save**, **Show diff** (Preview), `--explain`-Ansicht mit `source`.
- [ ] Step 4: Sidebar + `router.register` + `routeMap` + Help-ID in `docs/api/admin-ui-reference.md` (Muster `:306`).
- [ ] Step 5: Lauf → **grün**; `--validate` rc 0.
- [ ] Step 6: Commit `feat: add admin ui pane for the issue label taxonomy`.

### Task 27: Read-only Framework-Sichten für Presets und Adapter

**Agent:** developer · **Depends on:** 2, 3, 26 · **Größe:** S
**Files:**
- Modify: `scripts/admin-server.py`
- Modify: `docs/ui/admin-ui.html`
- Modify: `docs/api/admin-ui-reference.md`
- Create: `tests/test_admin_ui_issue_labels_framework_views.py`
**Interfaces:** Produces `SUPER_ADMIN_FILES["issue-conventions-presets"]` und `["issue-adapters"]` (`scripts/admin-server.py:205-215`), zwei `framework_defaults`-Routen im `routeMap` (`docs/ui/admin-ui.html:11398-11404`-Umfeld) mit Help-IDs; Consumes `_route_get_config` (GET-Präfix `:3696-3701`).

- [ ] Step 1: **Test zuerst**: `test_preset_file_served_readonly`, `test_adapter_file_served_readonly`, `test_adapter_view_never_exposes_token` (nur `auth.env`), `test_framework_help_ids_present`.
- [ ] Step 2: Zwei Einträge in `SUPER_ADMIN_FILES`; zwei schlanke Read-only-Views (Tabellenansicht der Presets bzw. der Adapter-Capabilities), keine Schreibpfade.
- [ ] Step 3: `routeMap` + Help-IDs in `docs/api/admin-ui-reference.md`; die Adapter-Ansicht maskiert `auth.header` vollständig.
- [ ] Step 4: Lauf → **grün**; `--validate` rc 0.
- [ ] Step 5: Commit `feat: expose issue presets and adapters as read-only admin views`.

### Task 28: Voller Szenarientest mit gemocktem Tracker (AC-4, AC-5, AC-10, AC-18, AC-19, AC-22)

**Agent:** tester · **Depends on:** 21, 24, 25, 26, 27 · **Größe:** M
**Files:**
- Create: `tests/test_issue_labels_scenario_1188.py`
**Interfaces:** Consumes alle vorherigen Tasks als **öffentliche** Oberfläche (CLI-Subprozess + HTTP).

> **Szenario-IDs:** #1188 belegt **keine** ID im Katalog `tests/scenarios/registry.md`
> (`94` = #1181, `95`–`98` = #1187). Dieser Task ist ein pytest-Szenario, kein Katalog-Szenario.

- [ ] Step 1: Scratch-Projekt in `.tmp/scenario-labels-1188/` anlegen (idempotent: bei Existenz löschen), mit eigener `.meta-config/project.yaml`, `issue-conventions.enabled: true`, `repository.{owner,repo}` gesetzt (kein `git.remote-url` nötig — genau der D9-Pfad), `taxonomy.area.enabled: true` mit `area.values.core`/`area.values.ui` (erzeugt `area/core`) und `sync.prune: true`, `sync.prune-allow: []`.
- [ ] Step 2: Gemockten Tracker als `http.server` auf `127.0.0.1:0` starten (stdlib, In-Process), Adapter-Fixture mit `base-url: "http://127.0.0.1:<port>/api/v1"` (Loopback-Ausnahme H-1) und `auth.env: SCENARIO_TOKEN` (Dummy-Wert); der Mock hält ein Label `type/needs-design` (Fremdlabel **innerhalb** des Präfix) und antwortet auf `list` paginiert (2 Seiten). **Kein** echtes Netzwerk, kein echtes Token.
- [ ] Step 3: Ablauf erzwingen: `--labels` (Dry-Run ⇒ keine Schreibaufrufe im Mock-Log) → `--labels --apply` (Create **mit** `type/bug` und `area/core`) → `--labels --check` (rc 0) → **Drift** erzeugen (eine Farbe im Mock ändern) → `--check` (rc 1) → **Prune-Fall:** `type/needs-design` steht nicht im Manifest ⇒ bleibt, `info: prune-candidate-unowned`; ein Label aus einem früheren Manifest-Lauf wird gelöscht → **Rename-Fall (D10):** ein neuer Wert erzeugt `create <neu>`, das alte Manifest-Label bleibt im Mock, `info: rename-candidate <alt>`, **kein** `PATCH`-Aufruf mit `new_name` → `--labels --apply`-Wiederholung (idempotent, alles `no-op`).
- [ ] Step 4: Zusatzassertions: Mock-Log zeigt `.../labels/type%2Fbug` und `.../labels/area%2Fcore` (**kodiert**), die CLI-Ausgabe zeigt `type/bug` und `area/core` (**unkodiert**, K-7); `list` wurde je Lauf genau einmal aufgerufen und paginiert; kein Token im gesamten Output/Log/`docs/issue-labels.md`/Manifest; `docs/issue-labels.md` enthält alle aktiven Werte; `.meta-config/issue-labels-state.json` existiert nach `--apply` und ist nach `--check` byte-identisch; Teilfehler-Simulation (Mock antwortet beim dritten Create mit 500) ⇒ Exit 1 + Tabelle; 401-Simulation ⇒ Callcount 1.
- [ ] Step 5: Lauf: `python3 -m pytest tests/test_issue_labels_scenario_1188.py --basetemp="$PYTEST_BASETEMP" -q` → **grün**; danach `.tmp/scenario-labels-1188/` aufräumen.
- [ ] Step 6: Commit `test: add end-to-end label sync scenario with a mock tracker`.

### Task 29: CHANGELOG + Doku-Abschluss (DoD)

**Agent:** documenter · **Depends on:** 28 · **Größe:** S
**Files:**
- Modify: `CHANGELOG.md`
- Modify: `docs/CODEBASE_OVERVIEW.md`
**Interfaces:** Consumes alle Tasks.

- [ ] Step 1: `[Unreleased]`-Eintrag: neue Sektion, neuer CLI-Pfad, neue Config-Dateien, generierte Doku, persistiertes Prune-Manifest (`.meta-config/issue-labels-state.json`), Transport-Härtung (HTTPS/Host-Pinning, keine Redirects) und URL-Kodierung der Label-Pfade.
- [ ] Step 2: Modulabschnitt für `issue_conventions.py`/`issue_adapters.py`/`consistency/issue_labels.py` ergänzen (Muster `### scripts/lib/mcp.py`, `docs/CODEBASE_OVERVIEW.md:1070`).
- [ ] Step 3: Lauf: `python3 scripts/sync.py --validate` → **rc 0**; `git status` zeigt genau die erwarteten Dateien.
- [ ] Step 4: Commit `docs: changelog and module overview for the issue taxonomy`.

### Task 30: Optionale Issue-Templates für drei Plattformen (D12, AC-3/AC-6)

**Agent:** developer · **Depends on:** 1, 9, 26 · **Größe:** M
**Schema:** `issue-conventions.templates: {mode: off|scaffold|manage, force: bool}` ist seit D12
Spec-Vertrag (IC-1) und wird in **T1** angelegt — dieser Task ist deshalb **nicht** bedingt und
erfindet kein Schema (K-15). `renames` bleibt weiterhin außerhalb dieses Plans (K-13).
**Files:**
- Create: `tests/test_issue_labels_templates.py`
- Modify: `scripts/lib/issue_conventions.py` (Generator + Capability-Gating)
- Modify: `scripts/lib/cli_commands.py` (Aufruf im Common Tail, neben T25)
- Modify: `scripts/lib/generated_file_drift.py` (Template-Pfade in die Drift-Baseline, D11)

- [ ] Step 1: **Test zuerst**: `test_off_writes_nothing` (Default `off`), `test_scaffold_creates_missing_only` (vorhandene handgeschriebene Datei bleibt byte-identisch, kein Backup), `test_manage_updates_marker_file`, `test_manage_skips_unmarked_file` (ohne `force`), `test_force_overwrites_unmarked_file`, `test_creates_only_capable_families` (Adapter ohne `issue-forms` ⇒ keine `.github/ISSUE_TEMPLATE`-Datei), `test_no_token_in_templates`, `test_templates_are_registered_in_generated_file_hashes` (D11).
- [ ] Step 2: Generator implementieren, ausschließlich capability-gesteuert (`issue-forms`/`issue-templates`); Dateinamen aus der aktiven `type`-Achse, Inhalt mit `GENERATED_MARKER`.
- [ ] Step 3: Lauf → **grün**; `--validate` rc 0.
- [ ] Step 4: Commit `feat: generate optional issue templates per platform capability`.

## Interfaces & Signaturen

### Schema (IC-1, verbindlich)

- Sektion `issue-conventions`, `additionalProperties: false` auf **allen** Ebenen.
- Schlüssel: `enabled`, `preset`, `adapter`, `defaults{separator{single,multi}, language, title-format, closing-keywords}` (K2: **kein** `label-separator`), `taxonomy{type,area,priority}`, `platform-overrides.<adapter>{taxonomy, mapping, base-url, api, ids, pagination, auth.header, defaults}`, `mapping`, `repository{owner,repo,project-id}`, `templates{mode,force}`, `create{on-missing-label}`, `sync{prune,prune-allow,create-boards}`, `enforcement{unknown-label,missing-type,single-axis-per-issue}`.
- `repository` ist Stufe 0 der Identitäts-Präzedenz (D9/K-12); `templates.mode` ∈ `off|scaffold|manage`, `templates.force` boolean mit Default `false` (D12/K-15).
- `#/$defs/taxonomyAxis` = `{enabled, cardinality, color, label-case, max-length, allowed-pattern, values}`; `values.<name>` = `{color, description}`. **Kein** `default`-Feld (K4); die Zwei-Defaults-Prüfung lebt in AC-7, nicht im Schema.
- Die neuen `$defs` bleiben unter `$defs` (nicht `definitions`), weil das Ist-Schema `draft-07` deklariert und dennoch `$defs` nutzt (`config/project-config.schema.json:2`, `:2855`); `#/$defs/…` löst in beiden Fällen auf (K6).
- Weitere geschlossene `$defs`: `adapterApi` (`list|create|update|delete`), `adapterIds` (`op`, `key`), `adapterPagination` (`param`, `size-param`, `size`), `adapterDefaults` (dieselbe Form wie `adapters.<id>.defaults`).
- `templates` ist ein geschlossener Unterabschnitt mit `mode`/`force` (D12); ein `renames`-Schlüssel existiert **nicht** — D10 reserviert nur die Ausgabezeile (eigene Spec-Revision).

### Adapter-Interface (Daten, IC-3)

```yaml
adapters.<id>:
  kind: http | plugin
  auth: {env: <ENV_NAME>, header: "<Header>: {token}"}   # kein token/password; {token} ist Pflicht
  base-url: string                                        # https (Loopback-Ausnahme)
  aliases: {<platform>: <adapter-id>}                     # optional, Daten
  pagination: {param: <name>, size-param: <name>, size: <int>}   # Pflichtdaten für list
  ids: {op: list, key: id}                                # optional; nötig, wenn api.*.path `{id}` nutzt
  defaults: {separator: {single, multi}, color-format, label-case, max-length, allowed-pattern}
  api: {list, create, update, delete: {method, path, body?}}
  capabilities: [labels, scoped-labels, issue-labels, issue-forms, issue-templates]
```

Python-Gegenstück (`scripts/lib/issue_adapters.py`):

```python
class HttpTransport(Protocol):
    def request(self, method: str, url: str, headers: dict[str, str],
                body: dict | None) -> tuple[int, object]: ...

@dataclass(frozen=True)
class AdapterConfig:
    id: str; kind: str; auth_env: str; auth_header: str; base_url: str
    defaults: dict; api: dict; ids: dict | None; pagination: dict
    capabilities: frozenset[str]; aliases: dict[str, str]

def load_issue_adapters(agent_meta_root: Path, config: dict) -> dict[str, AdapterConfig]
def select_adapter(adapters: dict[str, AdapterConfig], configured: str,
                   config: dict) -> AdapterConfig          # "inherit" -> git.platform + alias
def build_target_url(adapter: AdapterConfig, identity: RepositoryIdentity, op: str, *,
                     fields: dict, id_map: dict[str, str] | None = None) -> str
def resolve_id_map(adapter: AdapterConfig, identity: RepositoryIdentity,
                   transport: HttpTransport) -> dict[str, str]
def iter_pages(adapter: AdapterConfig, identity: RepositoryIdentity,
               transport: HttpTransport) -> list[dict]
def parse_remote_url(url: str) -> RepositoryIdentity
def resolve_repository(config: dict, resolved: ResolvedTaxonomy, *,
                        env: Optional[dict] = None) -> RepositoryIdentity
def retry_delay(retry_after: Optional[str]) -> float   # Cap 30 s, Default 1 s (D14)
def build_desired_labels(resolved: ResolvedTaxonomy) -> dict[str, DesiredLabel]
def label_diff(desired, actual, projection, *, prune: bool,
               manifest: dict[str, str], prune_allow: list[str]) -> list[DiffEntry]
def prune_candidates(actual, desired, manifest, prune_allow) -> tuple[list[DiffEntry], list[Finding]]
def load_state(project_root: Path) -> State
def save_state(project_root: Path, state: State, *, applied_names: list[str],
               adapter_id: str, repo_key: str) -> None
def apply_labels(adapter, identity, diff, *, transport, log) -> ApplyResult
def enforce_single_axis(adapter, labels) -> SingleAxisOutcome
def creation_policy(mode: str) -> CreatePolicy
def resolved_adapter_dump(adapter: AdapterConfig) -> dict   # {"auth": {"env": ...}} — nie mehr
```

### Resolver-Interface (`scripts/lib/issue_conventions.py`)

```python
def resolve_issue_conventions(config: dict, agent_meta_root: Path, *,
                              adapter: str | None = None) -> ResolvedTaxonomy
def validate_issue_conventions(resolved: ResolvedTaxonomy) -> None      # IssueConfigError
def project_label(axis: Axis, value: AxisValue, projection: Projection) -> str
def render_explain(resolved: ResolvedTaxonomy) -> list[str]
def render_taxonomy_table(resolved) -> str
def render_label_map(resolved) -> str
def render_title_format(resolved) -> str
def render_closing_keywords(resolved) -> str
def render_triage_labels(resolved) -> str
def render_creation_policy(resolved) -> str
def render_issue_labels_doc(resolved, project_name: str) -> str
TRIAGE_LABELS: tuple[str, str]                    # ("triage", "needs-info") — Framework-Konstante (D15)
LEGACY_ROLE_BLOCKS: dict[str, dict[str, str]]     # K-1
```

`ResolvedTaxonomy` trägt je Achse und je Wert `source`; `Projection.sources` trägt
`separator-single`, `separator-multi`, `color-format`, `label-case`, `max-length`,
`allowed-pattern`.

### CLI-Vertrag (IC-4)

| Aspekt | Vertrag |
|---|---|
| Flags | `--labels`, `--labels --apply`, `--labels --check`, `--labels --explain`; `--check` + `--explain` erlaubt; `--apply` + `--check` = Nutzungsfehler |
| Default | ohne `--apply` wird **nie** geschrieben (D4) |
| Exit `0` | sauber / Dry-Run / Explain / Apply ohne Fehler |
| Exit `1` | Drift (`--check`) oder Teilfehler (`--apply`) |
| Exit `2` | Resolve-/Config-/Nutzungsfehler; **kein** API-Call |
| Ausgabe | `create <label>` / `update <label>` / `no-op <label>`, Summenzeile, im `--apply`-Fall zusätzlich `wrote .meta-config/issue-labels-state.json`; `rename <alt> -> <neu>` ist **reserviert** und wird in v1 nie erzeugt (D10); `--explain` zeilenweise `<key> ← <source>` |
| Idempotenz | zweiter `--apply` ⇒ nur `no-op`, Exit 0 (AC-4); setzt paginiertes `list` + Name→ID-Map voraus (K-7) |
| Zustand | nur `--apply` schreibt `.meta-config/issue-labels-state.json` (IC-8/K-9); `--labels`, `--check`, `--explain` sind schreibfrei |
| Commit | **kein** Auto-Commit und kein `git`-Aufruf im CLI (D13/K-16); der `git`-Schritt committet, CI-`--apply` nie |
| Transport-Härtung | H-1…H-7 (Spec §4.12) sind **nicht** abschaltbar; Verstoß ⇒ Exit 2 vor dem ersten Call |
| Secret-Freiheit | kein Token in Ausgabe, Logs, Doku, Manifest, Fehlermeldung (AC-8) |

### Auth-Vertrag (IC-6)

- Auth **nur** über `auth.env`; Wert aus `os.environ`, optional aus `.env` im
  Projektwurzelverzeichnis (stdlib-Parser, kein Echo).
- Projekt-Override lebt ausschließlich in `issue-conventions.platform-overrides.<adapter>` und darf
  `base-url` (nur Pfad), `api.*`, `ids`, `pagination`, `auth.header`, `defaults` ändern — **nie**
  `auth.env`/ein Token; `auth.token`/`auth.password` sind `IssueConfigError`. `auth.header` ohne
  `{token}` ist ebenfalls `IssueConfigError` (H-6).
- `resolved_adapter_dump()` liefert ausschließlich `{"auth": {"env": "<NAME>"}}` (AC-8-Test).
- **Nicht konfigurierbar (K-8):** HTTPS-Zwang mit Loopback-Ausnahme, Host-/Scheme-Pinning gegen den
  aufgelösten `base-url`, relative Pfade, keine Redirects, kodierte Pfad-Segmente. Der Gitea-Host
  kommt aus `GITEA_URL`, nie aus `project.yaml`.

## Teststrategie

### Bestehende Tests, die grün bleiben müssen (Regressionsanker)

| Test | Warum |
|---|---|
| `tests/test_conventions_migration_invariant.py:66-89` | Golden der Release-/Changelog-Blöcke und der Rollen-Gate-Fall `GIT_ISSUE_NAMING_BLOCK` |
| `tests/test_conventions_platform_cascade.py:24-57` | Preset-/Plattform-Kaskade bleibt unverändert |
| `tests/test_issue_language.py:30-56` | `ISSUE_LANGUAGE` bleibt unabhängig von `applies_to_roles` |
| `tests/test_variable_builder_active_set.py:77-78` | `GIT_ISSUE_NAMING_BLOCK` bleibt an die `git`-Rolle gegatet |
| `tests/test_admin_server.py:2164-2168` | Whitelist-Vertrag bleibt intakt |
| `tests/scenarios/run.sh` (Katalog) | Szenario-Katalog bleibt grün; `--validate` bleibt offline |

### Neue Testdateien und ihre Achsen

- **Resolver-Matrix:** Achse × Capability × Plattform. Konkret in
  `tests/test_issue_conventions_resolver.py`: `type`/`area`/`priority` ×
  `scoped-labels` an/aus × `github`/`gitlab`/`gitea`/`synthetic`, je mit Separator,
  Farbformat und Namensgrenze. Zusätzlich die 7×7-Präzedenzmatrix.
- **Golden `enabled:false`:** `tests/test_issue_conventions_golden.py` friert die vier
  Rollen-Abschnitte aus `aaed14c2` ein (K-1); der Test schlägt fehl, sobald ein Byte abweicht
  (AC-9).
- **Capability-Pfade (AC-7):** zwei Tests, ein Adapter mit `scoped-labels` (ersetzt), einer
  ohne (verweigert); **kein** Provider-Name im Testcode, nur Capability-Fixtures.
- **Namensgrenzen (AC-20):** Test prüft zusätzlich die Callcount des Fake-Transports == 0.
- **Offline-Zuschnitt (K-5):** Test patcht `urllib.request.urlopen` auf `raise` und ruft
  `run_checks` + `--validate`; grün ist der Beweis, dass kein Netzwerkpfad existiert.
- **Secret-Freiheit (AC-8):** vier Ebenen — `resolved_adapter_dump`, Fehlermeldung, generierte
  Datei/Preview-Response, Manifest (IC-8/3).
- **Transport-Härtung (RVW-1188-05):** drei Pfade in T3/T16 — (a) `http://` auf einen Nicht-Loopback
  Host ⇒ `IssueConfigError`, (b) `base-url`-Host-Wechsel per `platform-overrides` ⇒
  `IssueConfigError`, (c) 302-Antwort ⇒ Fehler ohne zweiten Request und ohne Auth-Header an den
  Zielhost; dazu `auth.header` ohne `{token}` und mit literalem Credential.
- **URL-Kodierung und IDs (RVW-1188-01):** `type/bug`/`area/core` werden kodiert im Pfad
  (`type%2Fbug`), unkodiert in Ausgabe/Manifest; Gitea adressiert mit numerischer ID aus der
  einmalig aufgelösten `list`-Map; `pagination` liest alle Seiten.
- **Prune-Manifest (RVW-1188-04):** `tests/test_issue_labels_state.py` prüft Format, Sortierung,
  Teilfehler-Verhalten und dass ein Fremdlabel **innerhalb** des Präfix (`type/needs-design`) nie
  gelöscht wird.
- **Repository-Präzedenz (D9/K-12):** `tests/test_issue_adapters_url.py` prüft die Kette
  `repository.*` → `git.remote-url` → `GITHUB_REPOSITORY`/`CI_PROJECT_PATH`, das Überspringen
  unparsbarer Quellen und die eine Fehlermeldung, die alle drei Wege nennt und nie einen leeren
  `owner`/`repo` ausgibt.
- **Retry-Policy (D14/K-17):** `tests/test_issue_adapters_http.py` prüft `429`-Retry mit
  `Retry-After` (Sekunden und HTTP-Datum), den 30-s-Cap, den 1-s-Default, „kein Retry bei `5xx` und
  Timeout" und die injizierte `sleep`-Funktion — kein Test wartet real.
- **Kein Rename in v1 (D10/K-13):** `tests/test_issue_adapters_diff.py` prüft, dass ein neuer Wert
  `create <neu>` erzeugt, der alte Wert nur das Soll-Set verlässt, **kein** `update.new_name`-Call
  entsteht und `info: rename-candidate <alt>` erscheint.
- **Template-Schalter (D12/K-15):** `tests/test_issue_labels_templates.py` prüft
  `off`/`scaffold`/`manage`, `force`, Capability-Gating und Token-Freiheit.
- **Drift-Baseline (D11/K-14):** `tests/test_issue_labels_docs.py` prüft Registrierung in
  `.meta-config/generated-file-hashes.json`, Drift-Erkennung nach manuellem Edit und
  Überschreiben mit `.sync-backup-*` beim nächsten Sync.

### Zwischentests je Meilenstein

Siehe Gates in der Meilenstein-Tabelle. Jedes Gate ist **vor** dem nächsten Meilenstein auszuführen; ein rotes
Gate blockiert den nächsten Meilenstein (kein „später fixen").

### Der eine volle Szenarientest (T28)

Genau **ein** End-to-End-Lauf, in `.tmp/scenario-labels-1188/`:

1. Scratch-Projekt + `.meta-config/project.yaml` (`enabled: true`, `repository.*` gesetzt,
   `taxonomy.area.enabled: true` für `area/core`, `sync.prune: true`).
2. Gemockter Tracker (stdlib `http.server`, `127.0.0.1:0` — Loopback-Ausnahme H-1), Adapter-Fixture
   mit paginiertem `list`, Fremdlabel `type/needs-design`, Dummy-Token.
3. `--labels` → **Dry-Run**: Mock-Log enthält nur `list` (paginiert), keinen Schreibaufruf.
4. `--labels --apply` → Create inkl. `type/bug`/`area/core`; Mock sieht `type%2Fbug`/`area%2Fcore`;
   Ergebnistabelle; Manifest geschrieben.
5. `--labels --check` → rc 0 (Manifest bleibt byte-identisch).
6. Drift: eine Farbe im Mock ändern → `--check` → rc 1.
7. Prune: `type/needs-design` bleibt (`info: prune-candidate-unowned`); ein Manifest-Label aus einem
   früheren Lauf wird gelöscht.
8. Rename-Fall gemäß **D10**: `create` für den neuen Wert, altes Label bleibt, `info: rename-candidate`,
   kein `PATCH` mit `new_name`.
9. `--labels --apply` erneut → ausschließlich `no-op`, rc 0.
10. Teilfehler- und 401-Simulation (Mock-Modi) → rc 1 bzw. Callcount 1.
11. Kein Token in irgendeiner Ausgabe, Datei oder im Manifest; `docs/issue-labels.md` vollständig.

Kein echtes Netzwerk, kein echtes Token, kein Zugriff außerhalb von `.tmp/`.

## Migration & Rollback

**Migration (additiv, dreistufig):**

1. **Stufe 0 (dieser Plan):** Code + Config + Tests landen, `enabled: false` überall.
   `build_variables()`-Ausgabe, gerenderte Agenten und `--validate` sind byte-identisch zu
   `aaed14c2`.
2. **Stufe 1 (Opt-in, ein Projekt):** Projekt setzt `issue-conventions.enabled: true` plus
   `taxonomy.area.values`. Erster Lauf ist **immer** `sync.py --labels` (Dry-Run), dann
   `--apply`, dann `--check` im CI.
3. **Stufe 2 (Framework-Default, später):** `enabled`-Default auf `true` heben — erst wenn
   `LEGACY_ROLE_BLOCKS` (K-1) gelöscht werden kann und `docs/issue-labels.md` in allen
   Pilotprojekten stabil ist. Nicht Teil dieses Plans.

**Rollback:**

- **Sofort:** `issue-conventions.enabled: false` setzen (oder die Sektion entfernen) ⇒
  Ausgabe und Rollen-Texte sind wieder die heutigen (K-1-Golden belegt das).
- **Vollständig:** die fünf neuen Produktionsdateien und die Sektion entfernen; keine
  Migration, kein Datenverlust, da der Tracker die einzige Autorität bleibt und nie
  gelöscht wird (`prune: false` Default, IC-5).
- **Manifest:** `.meta-config/issue-labels-state.json` darf jederzeit gelöscht werden — Folge sind
  **null manifest-basierte** Löschkandidaten (IC-5 „prune-needs-manifest"), kein Fehler. Nur
  `sync.prune-allow`-Einträge bleiben unabhängig davon löschbar (RVW2-1188-01). Kein Rollback nötig.
- **Secrets:** Rollback hinterlässt keine Secrets in Artefakten, weil nur `auth.env`
  persistiert wird (IC-6).
- **Kein Rückbau nötig für:** generierte `docs/issue-labels.md` — sie wird bei
  `enabled:false` nicht angefasst und kann manuell gelöscht werden.

## Risiko-Tabelle

| Risiko | Wirkung | Gegenmaßnahme | Restrisiko |
|---|---|---|---|
| **`prune` löscht Fremdlabels im eigenen Präfix** (z. B. `type/needs-design`) | Datenverlust an Menschen-Labels | K-9/IC-5: Löschen nur aus Manifest (IC-8) oder `prune-allow`; Test `test_prune_never_deletes_foreign_label_inside_prefix` | gering |
| **Manifest fehlt/ist nicht versioniert** ⇒ CI blind, Prune wirkungslos | Gate erkennt Drift nicht | IC-8/2 (versioniert), D13 (Commit beim `git`-Schritt, CI committet nie); T21-Test `test_apply_writes_manifest_and_check_does_not` | gering |
| **Label-Namen mit `/` ungeschützt im URL-Pfad** | 404/422, `--apply` nicht idempotent | K-7: `quote(..., safe="")` im Transport, Test mit `type/bug`+`area/core` (T16/T28) | gering |
| **Gitea braucht numerische ID** | jeder Lauf legt neu an, `--check` Dauer-Drift | `ids`-Daten + Name→ID-Map einmal pro Lauf (T16), Test `test_id_placeholder_uses_numeric_id` | gering |
| **Abgeschnittenes `list` (Pagination vergessen)** | Labels gelten als fehlend ⇒ Duplikat-`create` | `pagination` Pflichtdaten (T3), `test_pagination_reads_all_pages` (T16) | gering |
| **Secret-Exfiltration über Projekt-`base-url`/Redirect/literales `auth.header`** | Token-Abfluss an fremden Host | K-8/H-1…H-7, Tests in T3/T16, `--explain`-only-Preview in T26 | gering; Restfall = Operator mit Env- **und** Repo-Kontrolle |
| **Netzwerk in `--validate`** (Regel 1–3 versehentlich registriert) | CI ohne Token schlägt fehl oder hängt; Baseline `EXIT=0` (`.tmp/issue-dump/baseline-validate.txt:27`) bricht | K-5: `run_checks` ruft den Check **nur** mit `tracker=None`; Test patcht `urlopen` auf `raise` (T24) | gering |
| **Rename-Semantik** ohne Tracker-Zustand nicht eindeutig | falsche `rename`-Zeile ⇒ falsches Label angefasst | **D10 (entschieden, K-13):** kein Rename in v1 — `create <neu>` + `info: rename-candidate <alt>`, altes Label bleibt; `rename` nur bei späterer expliziter `renames`-Map (eigene Spec-Revision); Tests in T17 | gering |
| **`--label` vs. `--labels`** | Tippfehler schreibt Backup-Label statt Label-Sync (F-3) | unterschiedliche Help-Texte, Modus-Tabelle **vor** `audit_config` einsortiert, Test `test_help_distinguishes_label_and_labels`; F-3 als eigenes Issue | niedrig |
| **`git.remote-url` fehlt** (dieses Repo: keine `git:`-Sektion, `config/project-config.schema.json:1753-1757` ⇒ `""`) | `--labels` schlägt lokal fehl; CI-Gate blockiert | **D9 (entschieden, K-12):** Präzedenz `repository.*` → `git.remote-url` → `GITHUB_REPOSITORY`/`CI_PROJECT_PATH`; eine Fehlermeldung nennt alle drei Wege, nie leerer `owner`; Tests in T15 | gering |
| **`docs/issue-labels.md` driftet unbemerkt** | Doku widerspricht dem Resolver | **D11 (entschieden, K-14):** Registrierung in `.meta-config/generated-file-hashes.json`; manuelle Edits werden beim Sync überschrieben und gemeldet; Tests in T25 | gering |
| **Interaktives Warten im Test durch `Retry-After`** | hängende/flaky Tests | **D14 (entschieden, K-17):** `sleep` injiziert, Cap 30 s, Default 1 s; Tests prüfen die Wartezeit, warten aber nie real | gering |
| **Auto-Commit aus dem CLI** | ungewollter Commit in CI, unklare Autorität | **D13 (entschieden, K-16):** kein `git`-Aufruf im CLI; `--apply` druckt die Datei, der `git`-Schritt committet; Test `test_cli_never_invokes_git` | gering |
| Golden-Byte-Identität nur über `LEGACY_ROLE_BLOCKS` (K-1) | zwei Quellen für Alt-Text; Drift möglich | Golden-Test (T10) friert die Bytes ein; Löschkriterium dokumentiert (Stufe 2) | niedrig |
| `multi`-Achse + Scoped-Separator (Selbst-Ersetzung) | auf GitLab ersetzt `area::x` das vorherige `area::y` | Separator **pro Kardinalität** (T7), Test `test_gitlab_area_uses_single_dash` (AC-2b) | niedrig |
| Adapter-YAML wird Programmiersprache | Wartbarkeit, `kind: plugin` wird Umweg | keine Bedingungssyntax im Executor, nur Methode/Pfad/Body-Template; Review-Kriterium in T16 | mittel (Disziplin) |
| Schema-Kollision mit #1141/#1186/#1187 | Merge-Konflikt, doppelte Striktheit | eine Sektion pro PR in der Wave-Reihenfolge `#1187 → #1186 → #1188 → #1181`; Top-level bleibt `true`; #1188 liefert die Property, #1141 schaltet **danach** global strikt | mittel |
| Wave-Reihenfolge verletzt (z. B. #1181 vor #1188) | doppelte Bearbeitung derselben Prosa-Region in `git.md`/`agent_sync.py` | Global Constraint „Wave-Reihenfolge"; Spec §11; `docs/issue-labels.md` als `project-docs` in #1186 | niedrig |
| Admin-UI-Whitelist vs. #1186 (Ableitung aus Schema) | zwei Lösungswege an derselben Stelle | T26 fügt **einen** Handeintrag hinzu; die Ableitung aus #1186 läuft als **letzter** Wave-Schritt, danach ist der Eintrag ein No-op | niedrig |
| Token-Leak in Logs/Preview | Sicherheitsvorfall | IC-6, `_mask` (`scripts/lib/env.py:130`), drei AC-8-Ebenen | gering |
| Test-False-Positives bei „kein Label-Literal" | Rot wegen Prosa (`BUG`-Kategorie) | Test greift nur Backtick-Literale der aktiven Achswerte; Kategorien explizit ausgenommen (T13) | gering |
| HTTP-Timeout in CI | hängender Test | Transport injiziert, kein echtes Netz in Unit-Tests; Timeout 15 s nur im Szenarientest gegen `127.0.0.1` | gering |

## AC→Task-Traceability (22 ACs + AC-2b)

| AC | Task(s) | Nachweis | Anmerkung |
|---|---|---|---|
| AC-1 | T1 | `tests/test_issue_conventions_schema.py` | `additionalProperties:false` je Ebene |
| AC-2 | T2 | `tests/test_issue_conventions_presets.py` | Zwei Sektionen, kein Preset-Codepfad |
| AC-2b | T3, T7, T17 | `test_gitlab_area_uses_single_dash`, `test_gitlab_type_uses_double_colon` | Separator je Kardinalität; kein Selbst-Ersetzen im Soll-Set |
| AC-3 | T3 | `test_synthetic_fourth_adapter_from_yaml` | Nur YAML/Fixture, kein Python |
| AC-4 | T16, T17, T18, T20, T21, T28 | `test_dry_run_writes_nothing`, `test_second_run_noop`, `test_id_map_resolved_once_per_run`, `test_apply_prints_manifest_path_in_result_table` | Dry-Run-Default ist strukturell; Idempotenz setzt Pagination + Name→ID-Map voraus (K-7); `--apply` schreibt/druckt, committet nie (D13) |
| AC-5 | T21, T23, T24 | `test_check_exits_1_on_drift`, `test_all_six_rule_ids_reported_with_tracker` | ein Modul, sechs IDs, zwei Kontexte (K-5) |
| AC-6 | T9, T11, T12, T13, T14 | vier `*_has_no_label_literal`-Tests, `test_bfa_has_no_triage_literal` | `git.md` nutzt vier Variablen (K-1), nicht `GIT_ISSUE_NAMING_BLOCK`; Triage-Labels kommen aus `TRIAGE_LABELS` (D15); vollständige Erfüllung erst mit F-5 (`enabled: true`) |
| AC-7 | T18 | `test_single_axis_scoped_replaces_second_type`, `test_single_axis_unscoped_refuses` | beide Capability-Pfade |
| AC-8 | T3, T16, T17, T25, T26, T28 | `test_dump_contains_only_auth_env`, `test_no_token_in_resolved_dump`, `test_preview_never_includes_token`, `test_state_stores_only_name_and_hash` | vier Ebenen: Adapter-Dump, Fehlermeldung/Preview, generierte Doku, Manifest; zusätzlich H-6 (`auth.header` ohne `{token}` ⇒ `IssueConfigError`) |
| AC-9 | T6, T9, T10, T14 | `tests/test_issue_conventions_golden.py` | Byte-Golden über vier Rollen |
| AC-10 | T17, T28 | `test_prune_default_false`, `test_prune_never_deletes_foreign_label_inside_prefix`, `test_prune_without_manifest_and_allow_deletes_nothing`, `test_prune_true_prune_allow_deletes`, `test_candidate_set_is_manifest_minus_desired_minus_inactive`, `test_disabled_axis_labels_never_deleted`, `test_new_value_creates_and_reports_rename_candidate`, `test_no_rename_call_in_v1` | Löschen nur aus Manifest (IC-8) oder `prune-allow`; Präfix ist nur Klassifikation; deaktivierte Achsen löschen nie (K-9); Kandidaten = `(Manifest ∖ desired) ∖ labels(inaktiver Achsen)`; kein Rename in v1 (D10) |
| AC-11 | T6 | `test_area_disabled_yields_no_labels` | Gate **vor** Projektion |
| AC-12 | T4 | `test_enabled_axis_with_empty_values_fails`, `test_enabled_with_no_active_axis_fails` | harter Fehler (Exit 2 im CLI-Pfad) |
| AC-13 | T4 | `test_type_axis_disabled_warns_not_raises` | Warnung mit Best-Practice-Satz |
| AC-14 | T5, T8 | Präzedenzmatrix + `test_explain_lines`, `test_ac14_order_platform_beats_preset` | `source` je Achse **und** Wert; Stufe 4 = Plattform-Default, Stufe 5 = Preset (K-10) |
| AC-15 | T5, T8 | `test_project_beats_platform_for_enabled` | beide Quellen in `--explain` |
| AC-16 | T1, T15 | `tests/test_issue_adapters_url.py` (13 Tests) | vier Formen + unparsbar mit URL; Präzedenz `repository.*` → `git.remote-url` → CI-Env, harter Fehler erst wenn alle drei leer/unparsbar (D9/K-12) |
| AC-17 | T19, T28 | `tests/test_issue_adapters_apply.py`, Szenario | siehe Abschnitt „Nicht abdeckbare bzw. nur teilweise abdeckbare ACs" |
| AC-18 | T16, T18, T28 | `test_partial_failure_keeps_other_labels`, `test_no_retry_for_500`, `test_no_retry_for_timeout` | Tabelle, Exit 1, kein Delete; `5xx`/Timeout ohne Retry, `429` mit genau einem Retry (D14/K-17) |
| AC-19 | T18, T28 | `test_401_aborts_after_first_call`, `test_retry_still_aborts_on_401_after_retry` | Callcount, nicht Meldung; der `429`-Retry ändert den Auth-Abbruch nicht (D14) |
| AC-20 | T7, T21 | `test_max_length_exceeded_fails_before_http` | Callcount 0 |
| AC-21 | T26 | `tests/test_admin_ui_issue_labels_section.py` | Whitelist + PUT + Preview |
| AC-22 | T25, T30 | `tests/test_issue_labels_docs.py`, `tests/test_issue_labels_templates.py` | alle aktiven Werte + Label-Namen; Triage-Abschnitt (D15); Drift-Registrierung in `generated-file-hashes.json` (D11) |

## Backlog-Bugs — Einordnung (gegen die echten Issue-Texte)

| Issue | Einordnung | Tasks in diesem Plan | Begründung |
|---|---|---|---|
| **#1167** — `improvement: unify REQ-ID format across templates and presets and add a format validator` | **unabhängig, aber Datei-nah** — **nicht** in diesem Plan | — (nur Serialisierung) | Der Issue nennt `config/conventions-presets.yaml:34` (REQ-Prefix im Changelog) und `bug-feature-analyzer.md:42,84,134` (ungated REQ-Wording). #1188 ändert dieselben Dateien an **anderen** Stellen (`:50-64` bzw. `:89-97`). Kein inhaltlicher Widerspruch; **nicht parallel** editieren. |
| **#1141** — `bug: project config schema silently accepts unknown top-level keys` | **Nachläufer in der Wave-Reihenfolge** | T1 liefert die Property `issue-conventions`; T1 berührt `additionalProperties` auf Top-Level **nicht** | #1141 verlangt Top-Level `additionalProperties: false` bzw. ein Unknown-Key-Finding (heute `true`, `config/project-config.schema.json:2854`). AC-1 fordert Striktheit **nur für die neue Sektion**. **Reihenfolge (verbindlich):** `#1187 → #1186 → #1188 → #1181 → #1141` — #1141 schaltet global strikt, **nachdem** alle neuen Sektionen als Properties existieren. **Markierung:** #1141 ist der Nachläufer, #1188 der Zulieferer. |
| **#1181** — Commit-Authority je Rolle | **Vorgänger/Nachfolger in derselben Prosa** | T10 (`scripts/lib/agent_sync.py`-Overlay), T14 (`agents/1-generic/git.md`) | #1181 folgt **nach** #1188: beide ändern `agent_sync.py` am selben Injektionspunkt (`:1458-1459`) und dieselbe Region in `git.md`. **Zielmatrix (RVW2-X-01):** `agent_sync.py` → #1187/#1188/#1181 (seriell), `sync_pipeline.py` → #1186/#1181 (hier **kein** #1188-Task), `variables.py`/`standalone.py` → #1187, `tests/scenarios/registry.md` → #1181/#1187/#1186, beide `project.yaml.example` → #1187/#1186/#1188/#1181, `.meta-config/issue-labels-state.json` → #1188 erzeugt / #1186 klassifiziert. Keine inhaltliche Abhängigkeit, nur Datei-Serialisierung (Spec §11). |
| **#957** — `feat: PR-Templates (generic / platform / project override, mit Variablen)` | **Nachbar, gleiche Ausgabefamilie** | T30 (`issue-templates`-Familie); T25 `docs/issue-labels.md` | Der Issue nennt „Issue-Templates als Folge-Request" (Phase 3) — #1188 ist dieser Folge-Request. Beide schreiben unter `.github/` und brauchen dieselbe Ownership-Regel; **D11 entscheidet sie**: Registrierung in `.meta-config/generated-file-hashes.json` (die Datei existiert im Repo, `scripts/lib/generated_file_drift.py:41/53`), Marker-Regel aus IC-7 zusätzlich. Serialisiert wird bei jeder `.github/`-Erzeugung. |
| **#1168** — `fix: git agent writes harness Co-Authored-By …` | **unabhängig, gleiche Datei** | T14 | Funktional orthogonal (Commit-Trailer vs. Issue-Label), aber beide editieren `agents/1-generic/git.md` (dort Commit-Authority-Block, hier `:149-151`). Nur Datei-Serialisierung nötig, keine inhaltliche Abhängigkeit. |

## Neu gemeldete Findings (als separates Issue markiert)

Alle vier Findings stammen aus der Spec (§10.2). Sie werden **nicht** in #1188 mitimplementiert;
die Issue-Nummer wird im Wave-Overview nachgetragen. Hier stehen **keine** erfundenen Nummern.

| ID | Kurzfassung | Beleg | Vorschlag-Titel | Labels (heutiges Vokabular) | Verhältnis zu #1188 |
|---|---|---|---|---|---|
| **F-1** | Der einzige existierende Label-Namespace ist auf **beiden** Zielplattformen falsch: `labels.namespace: "type: {type}"` wird als `type: <type>` gerendert; GitHub erwartet `type/…`, GitLab `::` | `config/conventions-presets.yaml:56` → `scripts/lib/conventions.py:285,290` → `agents/1-generic/git.md:151` | `fix(config): conventions.issues.labels.namespace renders 'type: {type}', which matches neither GitHub nor GitLab label convention` | `bug`, `config`, `P2` | **Minimal-Fix unabhängig möglich** (Default auf `type/{type}`), vollständig erst mit #1188. T14 darf F-1 **nicht** stillschweigend mitlösen — der Namespace kommt aus dem Resolver, nicht aus dem Preset. |
| **F-2** | Die Prioritätsachse hat drei Teildefinitionen und keine kanonische: `meta-feedback.md:48` verweist auf die `bug-feature-analyzer`-Matrix, die Matrix (`:91-97`) bewertet nach Issue-Kategorie, die Taxonomie kennt diese Kategorien nicht | `agents/1-generic/meta-feedback.md:48`; `agents/1-generic/bug-feature-analyzer.md:91-97` | `improvement: carry the triage priority criteria into the label taxonomy (P0-P3 rationale per type)` | `improvement`, `config` | #1188 liefert den **Träger** (`priority.values.<P>.description`, `{{ISSUE_TAXONOMY_TABLE}}`); die inhaltliche Kanonisierung ist F-2. |
| **F-3** | CLI-Namenskollision: `sync.py --label TEXT` (Backup-Label, `scripts/sync.py:456`) und `--labels` unterscheiden sich nur im Plural | `scripts/sync.py:456` vs. neues `--labels` | `chore(cli): disambiguate sync.py --label (backup) and --labels (issue taxonomy)` | `chore`, `config`, `P3` | T21 entschärft nur per Help-Text; die Umbenennung (`--backup-label`) ist F-3. |
| **F-4** | Die Admin-UI editiert `conventions`-Overrides inklusive `issues.*` und verspricht eine Wirkung, die nur für `issues.language` existiert | `docs/ui/admin-ui.html:4156-4323`, Speichern `:4313-4319`; Renderer `scripts/lib/conventions.py:131-132` | `bug(admin-ui): conventions editor exposes inert issues.* fields without a warning or redirect` | `bug`, `config` | T26 fügt ein **neues** Pane hinzu; der Deprecated-Hinweis im alten Pane ist F-4 und wird nicht mitgemacht. |

## Entscheidungsstand (2026-11-09) — Q1…Q9

Alle offenen Punkte sind entschieden; das vollständige Protokoll mit den verbindlichen Texten steht
im Abschnitt „Entscheidungsprotokoll (2026-11-09)". Diese Tabelle hält nur die **Blockadewirkung**
fest.

| ID | Frage | Entscheidung | Blockadewirkung |
|---|---|---|---|
| **Q1** | Repository-Identität, wenn `git.remote-url` leer ist | **D9 / K-12:** `repository.*` → `git.remote-url` → `GITHUB_REPOSITORY`/`CI_PROJECT_PATH`; harter Fehler erst wenn alle drei leer/unparsbar (eine Meldung, alle drei Wege, nie leerer `owner`) | **entblockt T15** und damit M4/M5/M8; das eigene Repo (keine `git:`-Sektion) löst über `repository.*` bzw. die CI-Env auf |
| **Q2** | Retry/Backoff bei `429`/`5xx`/Timeout | **D14 / K-17:** genau ein Retry nur bei `429` mit `Retry-After` (Cap 30 s, Default 1 s, injizierbare `sleep`); `5xx`/Timeout ohne Retry | entblockt T16/T18; deterministisch getestet |
| **Q3** | Rename-Erkennung | **D10 / K-13:** kein Rename in v1; `create <neu>` + `info: rename-candidate <alt>`; `rename` reserviert für spätere `renames`-Map | entblockt T17 und die IC-5-Freigabe; kein Rename-Test mehr erwartet, stattdessen „kein Rename-Call" |
| **Q4** | Ownership/Drift von `docs/issue-labels.md` | **D11 / K-14:** Registrierung in `.meta-config/generated-file-hashes.json`; #957 spiegelt die Regel | entblockt T25; eine Antwort für beide Ausgabefamilien |
| **Q5** (entschieden) | Ort von `platform-overrides` | `issue-conventions.platform-overrides.<adapter>`, geschlossen (IC-1) | keine |
| **Q6** (entschieden) | `--validate` vs. `--labels --check` | Split: Regeln 4–6 offline, 1–3 online (K-5/§4.7) | keine |
| **Q7** | Triage-Labels | **D15 / K-18:** Framework-Konstante `TRIAGE_LABELS`, Abschnitt „Nicht Teil der Taxonomie", keine vierte Achse | entblockt T13; AC-6-Interpretation präzisiert |
| **Q8** | Ort des Template-Schalters | **D12 / K-15:** `issue-conventions.templates.{mode,force}` in IC-1; T30 ist Pflicht-Task | entblockt T1/T30; **kein** bedingter Task mehr |
| **Q9** | Commit des Zustands-Manifests | **D13 / K-16:** `--apply` schreibt und druckt, `git` committet, CI committet nie | entblockt T21; Test `test_cli_never_invokes_git` |

## Kritische Tasks (Reihenfolge für die Umsetzung)

1. **T5** — Präzedenz/Source ist der Kern; ein Fehler hier vergiftet Projektion, Doku, Check und UI.
2. **T7** — Projektion + Namensgrenzen; hier entscheiden sich AC-2b und AC-20 (und ob der
   Apply-Pfad je einen 422 sieht).
3. **T16/T17** — Transport-Härtung, URL-Kodierung, Name→ID-Map und Manifest-Prune; hier
   entscheidet sich, ob `--apply` idempotent ist und ob ein Fremdlabel überlebt.
4. **T10/T14** — Golden-Byte-Identität; ohne sie ist AC-9 nicht belegbar und jede
   Projekt-Migration riskant.
5. **T18** — Teilfehler/401/Single-Axis; die einzige Stelle mit „fremde Systeme werden
   verändert".
6. **T26** — Admin-UI-Schreibpfad; berührt die Whitelist und die 6.000-Zeilen-Single-File-UI.
7. **T23** — sechs Regeln mit unterschiedlichem Severity- und Netzwerkprofil.

## Nicht abdeckbare bzw. nur teilweise abdeckbare ACs

| AC | Einschränkung | Warum |
|---|---|---|
| **AC-17** | Nur die **Policy** und der gerenderte Rollen-Text sind testbar; „creates the issue without the label" ist Rollenverhalten (`feedback`/`meta-feedback`, `gh issue create`), kein CLI-Code | #1188 baut keinen Issue-Ersteller; die Rollen bleiben Prompt-gesteuert |
| **AC-7** (GitLab-Teil) | Getestet auf der **Soll-Menge** und im Mock-Adapter, nicht gegen eine echte GitLab-API | Kein Netzwerk/Token in der Suite |
| **AC-9** (feedback/meta-feedback/bfa) | Byte-Identität nur über `LEGACY_ROLE_BLOCKS` (K-1) erreichbar — eine bewusste Plan-Entscheidung, die AC-6 streng liest (kein Literal im Template) und den Alt-Text framework-intern führt | AC-6 und AC-9 spannen gegenläufig; ohne K-1 wäre eine der beiden ACs verletzt |
| **AC-5** | Die sechs IDs sind **nie** in einem einzigen Lauf sichtbar: offline (4–6) und online (1–3). „consistency-check reports the six rules" wird als „ein Modul, sechs IDs, zwei Kontexte" gelesen und durch `test_all_six_rule_ids_reported_with_tracker` + `test_validate_does_not_report_online_ids` belegt | Netzwerk in `--validate` wäre eine Verhaltensänderung (Q6/K-5) |
| **AC-6** (`git.md`) | `git.md` rendert aus vier Variablen statt aus `GIT_ISSUE_NAMING_BLOCK`; `GIT_ISSUE_NAMING_BLOCK` bleibt berechnet (Rückwärtskompatibilität), aber ungenutzt | Der Block ist eine Zeile zu viel für „no literal", und die vier Variablen sind die einzige Form, die den Disabled-Fall byte-identisch hält |
| **AC-6** (Wirkung) | Die Legacy-Tabelle bleibt in der Default-Ausgabe sichtbar (`enabled: false`); „kein Literal" gilt nur für das Template. Vollständige Erfüllung = Folge-Issue **F-5** (`enabled: true` + `LEGACY_ROLE_BLOCKS` löschen) | AC-6 und AC-9 sind ohne F-5 nicht gleichzeitig erfüllbar (Spec „AC-Interpretationen", RVW-1188-06) |
| **AC-21** („Show diff") | Offline-Teil (Explain + Soll-Menge) ist immer verfügbar; der **Tracker-Diff** braucht einen Token und eine aufgelöste Identität (D9) und ist im Pane als „nicht verfügbar" ausgewiesen, wenn beides fehlt | Sonst würde das Pane bei jedem Öffnen ein Netzwerk-/Auth-Problem zeigen |
| **AC-22** | „Generated" heißt: geschrieben beim Sync, nicht bei `--check`/`--dry-run`; bei `enabled:false` wird die Datei nicht angefasst | IC-7/Repo-Containment |

## Self-Review

- Jeder Task mappt auf **genau eine** Rolle (`developer`, `senior-developer`, `tester`,
  `documenter`); kein Task delegiert weiter.
- Jede Akzeptanz ist beobachtbar: Testname + Assertion, Befehl + erwarteter Exitcode.
- `Files:`/`Interfaces:` sind je Task vollständig; innerhalb einer Parallel-Gruppe
  überlappt keine Datei. Die Ein-Datei-Konfliktflächen
  `config/project-config.schema.json` (T1), `scripts/lib/config.py` (T9) und
  `config/issue-conventions-presets.yaml` (T2) liegen je in genau einem Task;
  `scripts/admin-server.py` und `docs/ui/admin-ui.html` sind zwischen T26 und T27
  **seriell** (T27 nach T26, gleicher Meilenstein, keine Parallel-Gruppe).
- Jede Code-Referenz trägt einen am Branch `docs/config-wave-plans-1181-1188` (`aaed14c2`)
  verifizierten `datei:zeile`-Anker.
- Keine Platzhalter, keine offenen Formulierungen; alle Entscheidungen sind als **D9–D15** im
  Abschnitt „Entscheidungsprotokoll (2026-11-09)" protokolliert und als **K-12 … K-18** in die
  Plan-Präzisierungen übernommen. Offene Fragen gibt es nicht mehr; Q5/Q6 waren bereits entschieden.
- Die drei Review-Kernpunkte sind als eigene Präzisierungen geführt und in **beiden**
  Dokumenten verankert: URL-Kodierung/IDs (K-7), Transport-Härtung (K-8), Manifest-Prune (K-9),
  AC-14-Reihenfolge (K-10).
- Jede Neuinterpretation eines AC steht in der Spec-Tabelle „AC-Interpretationen" und in der
  Plan-Tabelle „Nicht abdeckbare bzw. nur teilweise abdeckbare ACs" — kein AC-Text wurde
  umgeschrieben.
- 18 Testdateien, keine leere Tabellenzelle, keine `<…>`-Auslassung in `Files:`/`Interfaces:`.
- `pipeline_stages` ist bewusst **nicht** gebunden (DRAFT, kein Pipeline-Lauf) und wird beim
  Übergang zu `IN PROGRESS` nachgetragen.
- **Platzhalter-Selbstprüfung:** keine Platzhalter-Marker, keine `<…>`-Auslassungen in
  Pflichtfeldern.
- **Entscheidungs-Abdeckung:** D9 → T15, D10 → T17, D11 → T25/T30, D12 → T1/T30, D13 → T21,
  D14 → T16/T18, D15 → T9/T13/T25; jede Entscheidung hat mindestens einen Task und einen Test.

## Abschlusskriterien dieses Plans

1. Spec `Status: APPROVED`; die inhaltlichen Entscheidungen Q1/Q2/Q3/Q4/Q7/Q8/Q9 liegen vor
   (D9–D15, 2026-11-09).
2. Alle acht Meilenstein-Gates grün, jedes einzeln.
3. `python3 scripts/sync.py --validate` → rc 0, **ohne** Netzwerk.
4. `python3 -m pytest tests --basetemp="$PYTEST_BASETEMP" -q` → grün (volle Suite).
5. `tests/test_issue_labels_scenario_1188.py` grün in `.tmp/scenario-labels-1188/`.
6. `.meta-config/project.yaml` dieses Repos unverändert: `git diff --name-only aaed14c2..HEAD -- .meta-config/project.yaml` ist leer — fester Basis-Commit statt Arbeitsbaum-Diff (RVW2-1188-03).
7. `--validate-spec-plan` meldet **genau ein** ERROR-Finding: `spec_plan_approval_marker`
   (Spec ist DRAFT). Das ist das gewollte Gate und verschwindet mit `Status: APPROVED`.
   Task↔Test-Traceability ist in diesem Repo aus (`rapid-prototyping`,
   `config/dod-presets.yaml:63` `spec-plan-traceability: false`), daher entstehen keine
   weiteren Findings aus den `T<n>`-IDs; der Plan-Graph ist kantenrein
   (`Depends on:` trägt ausschließlich numerische IDs).

---

## Entscheidungsprotokoll (2026-11-09)

Verbindliche Nutzer-Entscheidungen zu den offenen Fragen der Spec. Jede Entscheidung ist in der
Spec (§13) und in diesem Plan eingearbeitet; Abweichungen brauchen eine Spec-Revision.

| D-Nr | Frage | Entscheidung (`DECIDED 2026-11-09`) | Stelle |
|---|---|---|---|
| **D9** | **Q1** — Repository-Identität ohne `git.remote-url` | Präzedenzkette `issue-conventions.repository.{owner,repo}` → `git.remote-url` → CI-Env (`GITHUB_REPOSITORY`, `CI_PROJECT_PATH`); harter Fehler erst, wenn **alle drei** leer/unparsbar sind, mit einer Meldung, die alle drei Wege nennt und **nie** einen leeren `owner` ausgibt. Schema `repository` wird in T1 gepinnt; Parser/Fehlermeldung/Tests in T15 | K-12, T1, T15, Risiken, AC-16-Trace |
| **D10** | **Q3** — Rename | Kein Rename in v1: neuer Wert ⇒ `create <neu>`; altes Label bleibt im Tracker, Meldung `info: rename-candidate <alt>`; kein `update.new_name`, keine `rename`-Ausgabezeile. `rename` bleibt im Vertrag reserviert für eine spätere explizite `renames`-Map (eigene Spec-Revision). Tests: `test_new_value_creates_and_reports_rename_candidate`, `test_no_rename_call_in_v1`, `test_rename_line_is_never_emitted_in_v1` | K-13, T17, Risiken, AC-10-Trace |
| **D11** | **Q4** — Drift-Ownership der generierten Doku | `docs/issue-labels.md` kommt in `.meta-config/generated-file-hashes.json` (Root-Level-Registrierung nach dem Muster `PLATFORM_DEFAULTS_RESOLVED_REL`); manuelle Edits werden beim nächsten Sync überschrieben und gemeldet. Dieselbe Regel spiegelt #957 für PR-Templates. Dieselbe Registrierung gilt für die generierten Tracker-Templates aus T30 | K-14, T25, T30, File Structure, AC-22-Trace |
| **D12** | **Q8** — Ort des Template-Schalters | `issue-conventions.templates: {mode: off\|scaffold\|manage, force: bool}` als geschlossener Unterabschnitt der bestehenden Sektion (Default `off`, `force: false`). `scaffold` = nur fehlende Dateien, `manage` = zusätzlich marker-tragende. **T30 ist Pflicht-Task** (kein bedingter Task, keine Schema-Erfindung) | K-6, K-15, T1, T30, M8 |
| **D13** | **Q9** — Commit des Manifests | `--apply` schreibt und druckt die geänderte Datei in der Ergebnis-Tabelle (`wrote .meta-config/issue-labels-state.json`); **kein** Auto-Commit, **kein** `git`-Aufruf im CLI. Der `git`-Schritt committet; CI-`--apply`-Jobs committen **nie**. Tests: `test_apply_prints_manifest_path_in_result_table`, `test_cli_never_invokes_git` | K-16, T21, CLI-Vertrag, AC-4-Trace |
| **D14** | **Q2** — Retry-Policy | Genau **ein** Retry, nur bei `429`, Wartezeit aus `Retry-After` (Sekunden oder HTTP-Datum), Cap 30 s, Default 1 s, `sleep` injiziert. `5xx`/Timeouts ohne Retry (sammeln, Exit 1); `401`/`403` brechen unverändert nach dem ersten Fehlschlag ab. Kein Backoff, keine Konfiguration in `project.yaml` | K-17, T16, T18, Global Constraints, AC-18/AC-19-Trace |
| **D15** | **Q7** — Triage-Labels | `TRIAGE_LABELS = ("triage", "needs-info")` als Framework-Konstante; `render_triage_labels()` rendert daraus `{{ISSUE_TRIAGE_LABELS}}`. Keine vierte Achse (D2), kein Projekt-Override, kein Soll-Label, kein `prune`-Ziel. `docs/issue-labels.md` führt sie unter „Nicht Teil der Taxonomie"; Regel 4 nimmt sie von der Literal-Prüfung aus | K-18, T9, T13, T25, AC-6-Trace |

**Nicht Teil dieser Entscheidungen:** ein `renames`-Schema-Schlüssel (D10 reserviert nur die
Ausgabezeile) und jede Änderung an `Status: DRAFT`.

---

## Review-Auflösung (2026-11-09)

Alle Review-Befunde zu #1188, mit Änderung und Fundstelle im Plan. Der Plan bleibt `DRAFT`.

| Befund-ID | Änderung | Stelle |
|---|---|---|
| **RVW-1188-01** (BLOCKER) | `{name}`/`{id}` werden in `build_target_url()` pro Segment mit `quote(..., safe="")` kodiert; Gitea bekommt `ids` + Name→ID-Map (einmal pro Lauf); `pagination` ist Pflichtdaten; neue Tests `test_slash_label_is_percent_encoded`, `test_nested_slash_label_is_encoded`, `test_id_placeholder_uses_numeric_id`, `test_pagination_reads_all_pages`; Szenario prüft kodierten Pfad und unkodierte Ausgabe | K-7, **T16** (Größe M → L, Interfaces + 7 neue Tests), T3 (`pagination`/`ids`-Daten), T7 (`test_projected_name_stays_unencoded`), T21, **T28**, „Der eine volle Szenarientest" (Schritte 2–4, 7), Risiken, AC-4-Traceability |
| **RVW-1188-02** (MAJOR) | Stufe 4 = Framework-Plattform-Default, Stufe 5 = Framework-Preset (AC-14 wörtlich); Testnamen getauscht (`test_level4_framework_platform_source` ↔ `test_level5_framework_preset_source`), `test_ac14_order_platform_beats_preset` neu, `test_explain_shows_platform_stage_four` neu | **K-10**, **T5** (Schritt 1), **T8** (Schritt 1), AC-14-Traceability |
| **RVW-1188-03** (MAJOR) | Ein deklarierter Ort für Transport-Overrides: `issue-conventions.platform-overrides.<adapter>.{base-url, api, ids, pagination, auth.header, defaults}`; T1 testet die geschlossene Form, T3 nennt den konkreten Key im Override-Test, `auth.env` nicht überschreibbar | **T1** (`test_platform_override_value_is_closed`, `test_platform_override_accepts_transport_keys`, `$defs`-Liste), **T3** (`test_project_override_merges_without_token` mit konkretem Pfad), Auth-Vertrag, Interfaces |
| **RVW-1188-04** (MAJOR) | `prune` löscht nur aus dem persistierten Manifest (`.meta-config/issue-labels-state.json`) oder `sync.prune-allow`; `owned_prefixes` nur noch Klassifikation; neuer Task-Teil `load_state`/`save_state`; neue Testdatei `tests/test_issue_labels_state.py`; Fremdlabel **innerhalb** des Präfix ist ein eigener Test | **K-9**, **T17** (komplett neu, 6 Schritte, 2 Testdateien), T21 (Manifest-Persistenz), File Structure (+1 Datei, 17 Tests), M4-Gate, Risiken, AC-10-Traceability |
| **RVW-1188-05** (MAJOR) | Transport-Härtung H-1…H-7 als Code: HTTPS-Zwang (Loopback-Ausnahme), Host-/Scheme-Pinning, relative Pfade, keine Redirects, `auth.header` nur mit `{token}`; Tests für alle drei Pfade (http-Schema, Host-Wechsel, Redirect) plus zwei Header-Fälle | **K-8**, Global Constraints („Secrets", „URL-Kodierung"), **T3** (6 neue Load-Tests), **T16** (Interfaces + 2 Härtungs-Tests, Redirect/Auth-Stopp), T26 (Preview nur mit gepinntem Host), Auth-Vertrag, Risiken, „Teststrategie" |
| **RVW-1188-06** (MAJOR, AC-5) | AC-5 als Kontext-Split gepinnt: Offline-Suite meldet 4–6, `--labels --check` meldet 6; ein Modul, sechs IDs; neue Tests `test_all_six_rule_ids_reported_with_tracker`, `test_validate_does_not_report_online_ids`, `test_labels_check_reports_all_six` | **K-5** (erweitert), **T23** (Schritt 1), **T24** (Schritt 1), AC-5-Traceability, „Nicht abdeckbare ACs" (neue AC-5-Zeile) |
| **RVW-1188-06** (MAJOR, AC-6) | AC-6 in zwei Stufen getrennt (Literal im Template vs. Wirkung); Folge-Issue **F-5** benannt; K-1 verweist darauf; Golden-Test bleibt Regressionsanker | **K-1**, „Nicht abdeckbare ACs" (neue AC-6-Zeile), AC-6-Traceability, T10 (Löschkriterium) |
| **WARN `plan:906`** | Leere Tabellenzelle der AC-8-Traceability gefüllt: vier Ebenen inkl. Manifest und H-6, konkrete Testnamen | „AC→Task-Traceability" **AC-8** |
| **WARN `plan:305/320`** | `scripts/lib/issue_conventions.py` (T2) und `scripts/lib/issue_adapters.py` (T3) stehen jetzt als **Create** | **T2** / **T3** unter `Files:` |
| **WARN (Spec §4.10)** | `{{ISSUE_TRIAGE_LABELS}}` und `{{ISSUE_TAXONOMY_ENABLED}}` sind im Spec-Vertrag; T9 listet beide bereits in `_BUILTIN_VARS` (unverändert gültig) | T9 (Schritt 1/4), Spec §4.10 |
| **Querschnitt: Wave-Reihenfolge** | `#1187 → #1186 → #1188 → #1181`, danach `#1141`, Whitelist-Ableitung zuletzt; als Global Constraint und im #1141/#1181-Einordnungsblock | Global Constraints, „Backlog-Bugs — Einordnung" (#1141, #1181 neu), Risiken („Wave-Reihenfolge verletzt") |
| **Querschnitt: Konfliktmatrix** | #1181-Flächen ergänzt: `scripts/lib/sync_pipeline.py`/`agent_sync.py`, `scripts/lib/variables.py`, `scripts/lib/standalone.py`, `tests/scenarios/registry.md`, beide `project.yaml.example` | Global Constraints (Wave-Reihenfolge), „Backlog-Bugs" (#1181-Zeile); vollständige Matrix in Spec §11 |
| **Querschnitt: Szenario-IDs** | `94` = #1181, `95`–`98` = #1187; #1188 belegt **keine** ID (pytest statt Katalog) | Global Constraints, **T28** (Hinweisblock), „Der eine volle Szenarientest" |
| **Querschnitt: `docs/issue-labels.md`** | Als `project-docs`-Datei-Set für #1186 klassifiziert; die Drift-/Ownership-Frage ist **D11** (Registrierung in `generated-file-hashes.json`, #957 spiegelt die Regel) | File Structure (Zeile `docs/issue-labels.md` + `generated_file_drift.py`), Entscheidungsprotokoll D11 |
| **RVW2-1188-01** (MAJOR, Sicherheit/Prune) | Kandidatenmenge ist `(Manifest ∖ desired) ∖ labels(inaktiver Achsen)` statt `desired ∪ (Manifest ∖ aktive Achsen)`; „kein Manifest ⇒ null Kandidaten" gilt nur bei **leerer** `sync.prune-allow` (Allowlist wirkt unabhängig). T17-Tests geschärft: `test_prune_without_manifest_and_allow_deletes_nothing`, `test_prune_true_prune_allow_deletes` (ohne Manifest), `test_candidate_set_is_manifest_minus_desired_minus_inactive`, `test_disabled_axis_labels_never_deleted` (Kandidat statt nur „kein delete") | **T17** (Step 1), AC-10-Traceability, Spec IC-5 |
| **RVW2-1188-02** (MINOR) | Beide `project.yaml.example` sind jetzt Teil von **T1** (`Files:` + neuer Step 3) und werden mit `test_examples_contain_closed_section` parametrisiert gepinnt; File-Structure-Zähler 16 → 18 | **T1** (Files, Step 1, Step 3), File Structure (Produktion — ändern) |
| **RVW2-1188-03** (MINOR, Testgüte) | M3-Gate stützt sich auf den Golden-Test aus T10 statt auf `git diff`; Abschlusskriterium 6 nutzt `git diff --name-only aaed14c2..HEAD -- .meta-config/project.yaml` (fester Basis-Commit, nicht vakuum-grün nach dem Commit) | M3-Gate, „Abschlusskriterien dieses Plans" Nr. 6 |
| **RVW2-1188-04** (MINOR) | Stufen-Nummerierung korrigiert: Projekt-Preset = Stufe 3, Framework-Preset = Stufe 5; Stufe 4 (`framework:platform:<adapter>`) bleibt unverändert | **T5** (Step 3) |
| **RVW2-X-01** (MAJOR, Querschnitt) | Verbindliche Zielmatrix in der #1181-Einordnung nachgezogen (agent_sync.py #1187/#1188/#1181; sync_pipeline.py #1186/#1181; variables.py/standalone.py #1187; registry.md #1181/#1187/#1186; beide Beispiele alle vier; State-Datei #1188/#1186) | „Backlog-Bugs — Einordnung" (#1181-Zeile), Spec §11 |
| **RVW2-X-02** (Querschnitt) | Die Klassifikation der State-Datei ist eine #1186-Pflicht: die State-Datei ist eigene Matrix-Zeile; #1186 führt sie als **`unmanaged[]`** (K1: die frühere `project-state`-Kategorie ist gestrichen) | Spec §11 (Zeile `.meta-config/issue-labels-state.json`), Spec §11.1 |

### Szenario-Konflikte K1–K8 (2026-11-09)

| Befund | Änderung | Stelle |
|---|---|---|
| **K1** (BLOCKER) | State-Datei ist `unmanaged` (Negativ-Deklaration), `project-state` gestrichen; `classes` bleibt 23 | Review-Zeile RVW2-X-02 oben; Spec §11.1 |
| **K2** (MAJOR) | Eine kanonische Objektform `separator: {single, multi}`; `defaults.label-separator` entfernt, kein String-Bridge-Test mehr | **K-2**, **T7** (`test_separator_is_object_form_only`), Interfaces (Schema-Schlüsselliste) |
| **K3** | **Nicht betroffen**: #1188 hat keine `preset`-Wertequelle mit Source-Attribution (sieben Stufen, alle unterscheidbar) | geprüft: K-10, T5 |
| **K4** (MINOR) | Kein `default`-Feld in `taxonomyAxis`; Regel 6 = zwei realisierbare Bedingungen; Zwei-Defaults-Prüfung = AC-7-Laufzeitregel | **K-11**, **T4** (Validator), T18 (`enforce_single_axis`) |
| **K5** | **Nicht betroffen**: keine Grant-Präzedenztabelle im Plan | geprüft: T5 |
| **K6** (NIT) | `$defs` bleibt (Ist-Schema nutzt es unter `draft-07`); explizite Notiz statt `definitions`-Umbenennung | Interfaces (Schema) |
| **K7** | **Nicht betroffen**: durchgehend kebab-case in `issue-conventions` | geprüft: Interfaces |
| **K8** | **Nicht betroffen**: kein bestehender `_KEYS`-Block | geprüft: T1 |

**Nicht geändert (bewusst):** kein neuer Task, keine Umnummerierung (30 Tasks bleiben), keine
AC-Umschreibung; `pipeline_stages` bleibt ungebunden (DRAFT). F-5 ist ein Issue-**Entwurf**; die
im Wave-Kontext als real bestätigten Nummern #1201–#1204 werden nicht zugeordnet, solange die
Titel nicht abgeglichen sind.
