# Entscheidungstabelle #946 / PR 1.4 — Konfigurations-Hygiene (Entwurf)

> Status: **ENTWURF — dem Nutzer vorzulegen.** Es wurde **nichts gelöscht**, kein
> `.bak` geprunt, kein `.tmp` geleert, kein Branch/Stash entfernt und kein Issue
> (#946, #1263) geschlossen oder kommentiert.
>
> Quellen: Roadmap `docs/plans/2026-11-15-master-roadmap.md` §3.2 PR 1.4, §4 E-11,
> §5 Nr. 2; Settings-Audit A.7 #1–3 (`docs/analysis/2026-11-15-fable-framework-settings-audit.md`);
> Issue #946 (18 Branches, 7 Stashes, `.tmp/cleanup-archive/`); E-09 (`.bak` nicht prunen).

## 1. PR 1.4 — Lösch-/Bereinigungsvorhaben (Freigabe offen)

| # | Betroffene(s) Artefakt | Befund / Ist-Zustand (2026-11-20) | vorgeschlagene Aktion | Freigabe | in diesem PR ausgeführt? |
|---|---|---|---|---|---|
| D-01 | `.continue/` | nicht vorhanden (`ls -d .continue` → kein Treffer) | keine Aktion nötig | entfällt | nein (nichts vorhanden) |
| D-02 | `.meta-config/project.yaml.bak.<ts>` (5 Dateien, gitignored) | vorhanden; eigener Lebenszyklus des meta-optimizers | Entsorgung nur nach Nutzerentscheidung; **nicht** über `--prune-sync-backups` (E-09) | **offen** | **nein** |
| D-03 | `.tmp/` (aktuell ~2,0 GB, u. a. `project.yaml.bak`, `polish/*.bak`, Test-Scratch) | vorhanden, gitignored; Teil davon ist #946-Cleanup-Archiv | gezielte Bereinigung nach Nutzerentscheidung; kein `rm` ohne Freigabe | **offen** | **nein** |
| D-04 | `*.sync-backup-*` (~251 Dateien laut Audit) | `--prune-sync-backups` existiert und ist nicht destruktiv im Sinne von E-09 für `.bak`; Pruning wurde **nicht** ausgeführt | einmaligen Preview (`--dry-run`) und danach Freigabe einholen | **offen** | **nein** |
| D-05 | `se-export:` in `.meta-config/project.yaml` | wird noch von `scripts/se-export.py` und `consistency/se_cascade.py` gelesen; SE aktuell aus | Entfernung = Verhaltensänderung, daher nicht autonom entfernt | **offen** | **nein** |
| D-06 | `test-repo:` in `.meta-config/project.yaml` | wird von `scripts/lib/cli_commands.py` aktiv gelesen; Pfad `../agent-meta-test` existiert nicht | Entfernung würde Test-Repo-Validierung abschalten → Nutzerentscheidung | **offen** | **nein** |
| D-07 | Hook-Teil von #1263 (`hooks/1-generic/lib/hook_common.sh`) | MCP-Namespace `mcp__*__?*` wird weiter pauschal durchgelassen; Deny gilt nur in `.claude/settings.json` | Hook-Deny aus derselben Quelle ergänzen (Issue #1263 Schritt 3) | **offen** (Folgeauftrag) | nein |

Hinweis zu D-02/D-04: E-09 legt fest, dass `project.yaml.bak.*` **nicht** in den
Pruning-Pfad von `--prune-sync-backups` aufgenommen wird. Der aktuelle Code prunt
ausschließlich `*.sync-backup-<timestamp>`; `.bak`-Dateien bleiben unangetastet.

## 2. Issue #946 — Branches und Stashes (Entscheidung durch Nutzer)

Die Liste stammt aus dem Issue-Body (Stand 2026-10-07). Der aktuelle Repository-Stand
(2026-11-20) weicht ab: `git stash list` ist **leer**; von den 18 Branch-Namen sind
lokal noch 15 vorhanden (bereits gemergte bzw. nachgelagerte Resolutionen eingerechnet).
**Alle decisions bleiben explizit offen** — dieses Dokument trifft keine Auswahl.

| # | Branch (aus #946) | Kategorie | dokumentierte Entscheidung | Freigabe |
|---|---|---|---|---|
| B-01 | `feat/issue-batch-677-728` | echte ungemergte Arbeit (PR #742 gemergt, 4 Commits fehlen in main) | offen: weiterführen / PR / archivieren | **offen** |
| B-02 | `fix/sync-check-tracked-only` | lokal, 1 Commit + Stash | offen | **offen** |
| B-03 | `feat/repository-documentation-consolidation` | PR #837 geschlossen, pausiert | offen | **offen** |
| B-04 | `feat/repository-documentation-consolidation-main` | PR #839 geschlossen | offen | **offen** |
| B-05 | `feat/lit-769-core-development` | Inhalt nicht in main | offen | **offen** |
| B-06 | `feat/lit-770` | Inhalt nicht in main | offen | **offen** |
| B-07 | `feat/lit-773` | Inhalt nicht in main | offen | **offen** |
| B-08 | `feat/lit-774` | Inhalt nicht in main | offen | **offen** |
| B-09 | `feat/lit-775` | Inhalt nicht in main | offen | **offen** |
| B-10 | `feat/lit-777` | Inhalt nicht in main | offen | **offen** |
| B-11 | `docs/auto-commit-tiers-spec` | teils in main, Checkbox-Zeilen abweichend | offen | **offen** |
| B-12 | `feat/model-inherit-main-chat` | Guard nicht in main | offen | **offen** |
| B-13 | `docs/integrations-framework-concept` | Inhalt nicht in main | offen | **offen** |
| B-14 | `docs/readme-architecture-overhaul` | Inhalt nicht in main | offen | **offen** |
| B-15 | `feat/integrations-framework` | Inhalt nicht in main | offen | **offen** |
| B-16 | `feat/knowledge-engine-phase-b` | Inhalt nicht in main | offen | **offen** |
| B-17 | `feat/platform-defaults` | Inhalt nicht in main | offen | **offen** |
| B-18 | `fix/bugfix-session-june-2026` | Inhalt nicht in main | offen | **offen** |
| B-19 | `feat/concept-driven-pipeline` | 88 Dateien, 3 % absorbiert, Issue #370 ohne PR geschlossen | offen | **offen** |

| # | Stash (aus #946) | Status 2026-11-20 | Freigabe |
|---|---|---|---|
| S-01 | `docs/838-spec-revision` | `git stash list` leer — vor jeder Löschung ohnehin zu sichern (AK #946) | **offen / gegenstandslos** |
| S-02 | `fix/sync-check-tracked-only` | nicht mehr vorhanden | **offen / gegenstandslos** |
| S-03 | `feat/issue-batch-677-728` | nicht mehr vorhanden | **offen / gegenstandslos** |
| S-04 | `feat/plugin-catalog-unification` | nicht mehr vorhanden | **offen / gegenstandslos** |
| S-05 | `main` (perf cache #656, Untracked-Anteil) | nicht mehr vorhanden | **offen / gegenstandslos** |
| S-06 | `feat/issue-562-…` | nicht mehr vorhanden | **offen / gegenstandslos** |
| S-07 | `fix/admin-ui-remote-token` | nicht mehr vorhanden | **offen / gegenstandslos** |

## 3. Von diesem PR bereits umgesetzt (keine Löschung, keine Nutzerentscheidung nötig)

- `plugins.honcho.enabled: false`, `plugins.reqogniloom.enabled: false` in
  `.meta-config/project.yaml` (E-11). `.mcp.json` wurde per Sync neu gerendert und
  enthält nur noch `playwright`.
- Entfernung toter **Konfigurationsschlüssel** (keine Dateilöschung):
  `knowledge-engine.migration`, leere `provider-options`-Blöcke, die abgeleiteten
  Duplikate `variables.ORCHESTRATOR_STRICT`, `variables.UNKNOWN_FALLBACK_*`,
  `variables.SE_BASE_DIR`. Deren Werte werden von `config.py` aus den
  autoritativen Quellschlüsseln neu abgeleitet (durch Tests belegt).
- #1263 (nicht-destruktiver Teil): `blocked`-Tools aktiver MCP-Server werden als
  `permissions.deny`-Einträge in `.claude/settings.json` gerendert und über einen
  eigenen Managed-State-Namespace zusammengeführt. Hook-Deny (D-07) bleibt offen.
- Rebaseline (H-Klasse + §3.8-Vorbehalt): `.meta-config/generated-file-hashes.json`,
  `AGENTS.md`; der §3.8-Vorbehalt ist eingetreten — das
  `mcp-guardrails.md`-Render ändert sich (Honcho/ReqogniLoom-Zeilen entfallen).
  Deshalb wurde zusätzlich das Rules-Golden
  `tests/fixtures/compact-golden/agents-managed.md` neu verankert und die
  betroffenen Test-Anker (`test_embed_rules_channel.py`, `test_gate_card_compact.py`)
  auf den verbleibenden aktiven Server `playwright` umgestellt.

## 4. Erwartete Nutzerantwort

Für jede Zeile mit **offen**: `freigegeben` (mit ggf. Zeitpunkt/Scope) oder
`abgelehnt`. Erst nach expliziter Freigabe dürfen Lösch-, Prune- oder
Branch-/Stash-Aktionen in einem separaten Auftrag erfolgen.
