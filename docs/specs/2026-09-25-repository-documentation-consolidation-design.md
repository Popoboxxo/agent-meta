---
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
title: Repo-weite Doku-Konsolidierung agent-meta — Design
---

# Repo-weite Doku-Konsolidierung agent-meta — Design

> spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
> Rolle: concept-architect · Datum: 2026-09-25 · Klassifikation: XL / Architectural
> Scope: **nur Design**. Keine Repo-Datei außerhalb `.tmp/` wurde angefasst.

---

## 0. Ausgangslage (belegt)

| # | Befund | Beleg |
|---|--------|-------|
| F1 | `README.md` nennt „74 Generic Agents", Ist sind 80 Templates (66 non-SE + 14 SE) | `README.md:122`; `agents/1-generic/` = 83 Einträge = 80 Rollen-`.md` + 3 `_*`-Helper |
| F2 | `README.md` nennt „6 provider configs", Ist 9 | `README.md:690`; `config/ai-providers.yaml` hat 9 Provider-Blöcke (`:2,:98,:172,:249,:316,:369,:434,:493,:545`) |
| F3 | Hook-Anzahl widersprüchlich: „7 hooks" vs. „5 hook scripts" | `README.md:501` vs. `README.md:696`; Ist 15 `.sh` unter `hooks/**` |
| F4 | `README.md:734` sagt `VERSION # Current version (v1.0.0)`, `VERSION` = `1.2.0-beta.2` | `README.md:734`; `.meta-config/project.yaml:1` (`agent-meta-version: 1.2.0-beta.2`) |
| F5 | 5-fache Architektur-Doku | `ARCHITECTURE.md` (84 Z, `:3` nennt Version 0.92.0), `ARCHITECTURE.full.md`, `docs/architecture/01-07`, `knowledge/wiki/concepts/architecture*.md`, `knowledge/sources/ARCHITECTURE.full.md` |
| F6 | 3-fache Guide-Führung | `docs/guides/` (31), `howto/configs/`, `knowledge/wiki/topics/` (43) |
| F7 | 4 Spec/Plan-Bäume ohne dokumentierte Abgrenzung | `docs/specs` (22), `docs/plans` (34), `docs/superpowers/specs` (15), `docs/superpowers/plans` (15) |
| F8 | `docs/INDEX.md` fehlt, ist aber **bereits Vertrag** | `scripts/lib/spec_plan_scaffold.py:23` (`DEFAULT_FALLBACK_INDEX`), `.meta-config/project.yaml:70` (`fallback-index: docs/INDEX.md`), `tests/scenarios/registry.md:101,102` |
| F9 | Kein generierter Doku-Index existiert — der einzige Generator im Repo ist `standalone/README.md` | `scripts/lib/standalone.py:309-369` (`render_index`), `:372-414` (`write_standalone_files`, idempotent + `dry_run`) |
| F10 | Knowledge-Wiki: letzte Log-Zeile 2026-09-03, Specs/Pläne bis 2026-09-19 | `knowledge/wiki/log.md:30` |
| F11 | Wiki-Index deklariert seine eigene Architekturquelle als stale | `knowledge/wiki/index.md:24` (`status:stale-upstream`) |
| F12 | `sync_knowledge_engine` überschreibt `index.md`/`log.md` **nie** | `scripts/lib/knowledge.py:114` |
| F13 | Rollen-Parität gebrochen: Template existiert, `roles:` nicht | `agents/1-generic/se-component-requirements.md`; `.meta-config/project.yaml:91-151`; SE ist aber `enabled: false` (`:12-13`) |
| F14 | `README.md:479-489` listet `se-cascade`, Projekt deaktiviert es | `README.md:489`; `.meta-config/project.yaml:339-342` |
| F15 | Tote Verweise | `README.md:721-724` (`howto/setup/`, `howto/features/` existieren nicht); `docs/REQUIREMENTS.md:21`; `docs/CODEBASE_OVERVIEW.md:33-44` |
| F16 | Zwei parallele ID-Systeme | `docs/REQUIREMENTS.md` (`REQ-*`) vs. Spec/Plan-Naming `SPEC-<NAME>-YYYY-MM-DD` (z. B. `docs/superpowers/plans/2026-09-07-generated-file-drift-detection.md`) |
| F17 | Provider-Verzeichnisse sind gitignored, generierte Root-Kontextdateien sind es **nicht** | `.gitignore:13-17` (`.claude/`, `.gemini/`, `.opencode/`) vs. kein Eintrag für `AGENTS.md`/`CLAUDE.md` |
| F18 | Bestehende Doku-Checks sind auf `docs/api/` begrenzt | `scripts/lib/consistency/docs.py:100-121` (`check_readme_docs_index`), `:9-44` (`check_sync_cli_docs`), `:47-97` (`check_ui_help_mappings`) |

**Unsicherheit (dokumentiert, nicht stillschweigend neu gelesen):** Track A arbeitet parallel in `tests/`, `scripts/lib/`, `config/`. Aussagen F13/F18 und alle `scripts/lib/`-Zeilenangaben sind ein Stand-Snapshot vom 2026-09-25 und können während der Migration drifted sein. Insbesondere betrifft das die in §3.3 genannten Zahlenquellen unter `tests/scenarios/`.

---

## 1. Kanonische Zielstruktur (SSoT pro Bereich)

```
agent-meta/
├── README.md                      ← EINSTIEG. Handtext + <!-- agent-meta:docs-begin/end -->
│                                    FACT-BLÖCKE (generiert). Keine manuellen Zahlen (F1-F4).
├── llms.txt                       ← AI-Einstieg. FACT-BLOCK: {{DOCS_PROVIDERS_BLOCK}}, {{DOCS_REPO_FACTS_BLOCK}}
├── ARCHITECTURE.md                ← GENERIERTER STUB. Nur Diagramm-Index + "→ docs/architecture/"
│                                    (kein eigener Inhalt mehr; F5 gelöst)
├── VERSION                        ← SSoT Version. Nur noch gelesen, nie in Doku dupliziert.
├── CHANGELOG.md                   ← SSoT Release-Historie. ARCHITECTURE.md/llms.txt linken nur drauf.
│
├── docs/
│   ├── INDEX.md                   ← ★ KANONISCHER DOKU-INDEX (generiert, 100 %).
│   │                                 Baum aller Doku-Unterordner + 1-Zeilen-Beschreibung je Seite
│   │                                 + Frontmatter-Zählung. Footer: Fact-Hash + Generator-Version.
│   │                                 Erfüllt den bestehenden Vertrag aus F8.
│   ├── architecture/              ← ★ SSoT ARCHITEKTUR
│   │   ├── 01-layer-model.md … 07-se-cascade.md   (Diagramm-Detailseiten, SSoT je Thema)
│   │   ├── 00-overview-full.md   ← aus ARCHITECTURE.full.md (Root) via git mv. SSoT Langfassung.
│   │   └── INDEX.md              ← generierter Teil-Index (Vorschau auf docs/INDEX.md)
│   ├── api/                       ← ★ SSoT CLI-/UI-Referenz (7 Dateien, unverändert)
│   │   ├── cli-reference.md  admin-ui-reference.md  slash-commands.md
│   │   └── composition-system.md  pal-variables.md  viz-api.md  viz-event-schema.md
│   ├── providers/                 ← ★ SSoT PROVIDER-REFEREN (pro Provider eine Seite, 6 vorhanden)
│   ├── guides/                    ← ★ SSoT GUIDES (31). howto/configs/ wandert hierher als
│   │   │                             guides/configs/ (Beispiel-Configs, kein Guide-Text)
│   │   ├── setup/  features/  mcp/  ci/
│   ├── specs/                     ← ★ SSoT SPECS
│   │   └── archive/superpowers/   ← aus docs/superpowers/specs/ (legacy, project.yaml:62)
│   ├── plans/                     ← ★ SSoT PLÄNE
│   │   └── archive/superpowers/   ← aus docs/superpowers/plans/ (legacy, project.yaml:63)
│   ├── spikes/                    ← ★ SSoT SPIKES (project.yaml:60)
│   ├── concepts/                  ← Design-Entscheidungen (lebend, nicht SSoT für Architektur)
│   ├── conclusions/  analysis/  issues/  testing/  se-cascade/  ui/
│   └── api/, providers/ …         → alle im generierten INDEX.md gelistet
│
└── knowledge/                     ← ABGELEITETER SCHATTEN, kein SSoT (siehe §5)
    ├── schema.md                  ← Steuerdokument, V1 des Bundles
    ├── sources/                   ← ★ IMMUTABLE. Nur additiv. Nie editiert, nie gelöscht.
    └── wiki/
        ├── index.md               ← GENERIERT (Vorschlag, §5.4) — bricht policy aus F12
        ├── log.md                 ← append-only, aber generator-appendiert
        ├── concepts/  entities/  topics/  plans/  specs/  sources/  queries/
            └── Pflicht-Frontmatter: type, derived-from, derived-at
```

### 1.1 SSoT-Entscheidung je Bereich

| Bereich | SSoT | Wird Stub/Redirect | Wird archiviert | Verschwindet |
|---|---|---|---|---|
| **Root-Doku** | `README.md` (Handprosa) + generierte `DOCS_*`-Faktenblöcke | `ARCHITECTURE.md` → generierter Pointer auf `docs/architecture/INDEX.md` | — | `howto/`-Root (F15) |
| **docs-INDEX** | `docs/INDEX.md`, 100 % generiert | — | — | Kein `docs/README.md` (siehe T-4) |
| **Architektur** | `docs/architecture/` (00 + 01–07) | Root-`ARCHITECTURE.md` (84 Z, F5), `knowledge/wiki/concepts/architecture*.md` → reine Verweis-Seiten | `ARCHITECTURE.full.md` → `docs/architecture/00-overview-full.md` (git mv, Root-Stub bleibt für Deeplinks) | keiner |
| **Guides** | `docs/guides/` | `knowledge/wiki/topics/*-guide*` → Redirect auf `docs/guides/` | — | `howto/setup/`, `howto/features/` (existieren nicht, F15 — nur Verweise entfernen) |
| **Specs/Pläne** | `docs/specs/`, `docs/plans/`, `docs/spikes/` (project.yaml:58-60) | — | `docs/superpowers/{specs,plans}/` → `docs/{specs,plans}/archive/superpowers/` | `docs/superpowers/` |
| **Knowledge-Wiki** | **kein SSoT** — abgeleiteter Schatten | alle `derived-from`-Pflicht | `knowledge/sources/ARCHITECTURE.full.md` bleibt **unverändert** (F5, Policy) | keiner in dieser Welle |
| **CLI-/Provider-Referenz** | `docs/api/` + `docs/providers/` | — | — | keiner |
| **Traceability** | `docs/REQUIREMENTS.md` (`REQ-*`) | — | `SPEC-<NAME>-<date>`-Naming wird **beibehalten** (Breaking-Change-Vermeidung) | — |

---

## 2. Komponentenkarte

| Komponente | Datei (neu/geändert) | Verantwortung (genau eine) |
|---|---|---|
| **C1 DocFacts** | `scripts/lib/doc_facts.py` (neu) | Berechnet das Faktum-Dict `{DOCS_*: value}` aus den kanonischen Quellen. Kennt keine Doku-Dateien. |
| **C2 DocRenderer** | `scripts/lib/doc_renderer.py` (neu) | Rendert `docs/INDEX.md` (Volltext) und die `DOCS_*`-Faktenblöcke in Marker-Regionen. Nutzt C1. |
| **C3 Block-Snippet-Bridge** | `scripts/lib/config.py` (`_build_snippet_variables`, `:1861-1914`) | Registriert `DOCS_*_BLOCK`-Variablen aus `snippets/docs/*.md` (C1-Werte eingesetzt). Kein Neu-Inventar. |
| **C4 Docs-Indexer** | `scripts/lib/doc_index.py` (neu) | Baut den Doku-Baum + 1-Zeilen-Beschreibungen (Frontmatter → Fallback Dateiname). Füttert C2. |
| **C5 Doku-Checks** | `scripts/lib/consistency/docs.py` (Erweiterung, `:9-121`) | Verify-by-construction (§4). Registriert 6 neue Checks. |
| **C6 Wiki-Index-Generator** | `scripts/lib/knowledge.py` (Erweiterung, `:103-205`) | Rendert `knowledge/wiki/index.md` deterministisch aus dem Dateisystem; `log.md`-Append. |
| **C7 Staleness-Resolver** | `scripts/lib/doc_facts.py` (Teilmodul) | Berechnet `status:stale-source` aus `derived-from` + `derived-at` + Quell-mtime. |
| **C8 Spec/Plan-Scaffold-Guard** | `scripts/lib/spec_plan_scaffold.py` (`:24,:67`) | Erkennt den vom Scaffold geschriebenen `docs/INDEX.md`-Skeleton und überschreibt ihn nicht (Vertragsbruch sonst, §7 IMPACT-2). |

**Warum nicht ein Component?** C1 (Faktenberechnung) ist rein, testbar, ohne Datei-I/O-Doku-Wissen und wird sowohl von C2 (Index) als auch C3 (README-Blöcke) als auch C5 (Checks) gebraucht. C4 (Index-Baum) ist die einzige Komponente, die Doku-Dateisystem-Semantik kennt und darf nicht in C1. C2 ist die einzige, die Marker-Regionen schreibt. Die Trennung folgt der bestehenden Schichtung in `scripts/lib/` (`config.py` ↔ `context.py` ↔ `agents.py`, siehe `variables.py:9-17` Dependency-Invariante: keine Zyklen, stdlib-only unten).

---

## 3. GENERATED_COUNTS_MECHANISM

### 3.1 Entscheidung: **keine neue Fakten-Datei**

`.meta-config/doc-facts.yaml` wird **verworfen**. Jede Zahl wird zur Sync-Zeit aus der bereits kanonischen Quelle *berechnet*. Begründung: eine Fakten-Datei wäre eine vierte Wahrheit, die selbst driftet — genau das Problem, das gelöst werden soll.

### 3.2 Platzhalter-Syntax und Namensraum

Zwei bestehende Engines, beide `scripts/lib/substitution.py`-basiert (Flucht-Sicherheit, `substitution.py:26-31`):

| Engine | Regex |-Verwendung | Für Doku? |
|---|---|---|
| E1 `variables.substitute()` | `\{\{([A-Z0-9_]+)\}\}` (`variables.py:56`) | Agent-/Rule-/Command-Rendering **in Provider-Dateien** | **nein** — deployt in Fremdprojekte |
| E2 `TemplateBuilder.resolve_variables()` | `\{\{([^…]+)\}\}` (`builder.py:13`) | Kontextdateien (Loops/Conditionals/Partials) | nein |
| **E3 `DocRenderer` (neu)** | `\{\{(DOCS_[A-Z0-9_]+)\}\}` | `README.md`, `llms.txt`, `docs/INDEX.md` | **ja** |

**Namensraum-Disziplin:** Der `*_BLOCK`-Namensraum ist **belegt** — `QUALITY_PIPELINES_BLOCK` stammt bereits aus `snippets/orchestrator/quality-pipelines.md` (`config.py:1882`). Alle Doku-Platzhalter tragen deshalb das Präfix `DOCS_`, Block-Varianten `DOCS_*_BLOCK`. Kollision ist konstruktiv ausgeschlossen.

| Platzhalter | Wert | Quelle (SSoT) |
|---|---|---|
| `{{DOCS_VERSION}}` | `1.2.0-beta.2` | `VERSION` via `read_version()` (`config.py:1060-1064`) |
| `{{DOCS_AGENT_TEMPLATES_COUNT}}` | 80 | `agents/1-generic/*.md` (Frontmatter `name`) |
| `{{DOCS_AGENTS_SE_COUNT}}` / `{{DOCS_AGENTS_NONSE_COUNT}}` | 14 / 66 | Namenspräfix `se-` |
| `{{DOCS_AGENTS_ACTIVE_COUNT}}` | = Anzahl generierter Provider-Agent-Dateien | `.meta-config/project.yaml:91-151` ∩ generierte Dateien |
| `{{DOCS_HOOKS_COUNT}}` | Top-Level-`.sh` (ohne `lib/`, `release-gates/`) | `hooks/**/*.sh` |
| `{{DOCS_PROVIDER_COUNT}}` | 9 | `config/ai-providers.yaml` → `providers:` Keys |
| `{{DOCS_PIPELINES_COUNT}}` | 6 aktiv + 1 disabled | effektive Pipelines inkl. `quality-pipelines.overrides` (project.yaml:339-343) |
| `{{DOCS_SCENARIO_COUNT}}` | n | `tests/scenarios/` — ⚠️ volatile, Track A (F-UNSICHERHEIT) |
| `{{DOCS_DOCS_FILE_COUNT}}` | n | `docs/**/*.md` ohne `_archive`-Pfade |
| `{{DOCS_AGENT_ROSTER_BLOCK}}` | gerenderte Roster-Tabellen | `agents/1-generic/*.md` + `config/role-defaults.yaml` |
| `{{DOCS_PIPELINES_BLOCK}}` | Pipeline-Tabelle **mit Enabled-Status** | `lib/pipelines.py` + project.yaml-Overrides |
| `{{DOCS_HOOKS_BLOCK}}` | Hook-Tabelle | `hooks/**/*.sh` |
| `{{DOCS_PROVIDERS_BLOCK}}` | Provider-Tabelle | `config/ai-providers.yaml` |
| `{{DOCS_REPO_FACTS_BLOCK}}` | kompakter Faktenblock für `llms.txt` | alle obigen |

**Korrektur der Fehlklassifikation (F1/F3/F4/F14):** `README.md:479` „7 pipelines" wird zu „6 aktiv + 1 disabled (se-cascade)". `README.md:501` „7 hooks" und `:696` „5 hook scripts" werden beide zu *einer* generierten Zahl, die die Exklusionsregel explizit kodiert — das eliminates die Widersprüchlichkeit strukturell, nicht per Korrektur.

### 3.3 sync.py-Integration

**Kein neues CLI-Flag.** Begründung: jedes neue Flag muss in `docs/api/cli-reference.md` dokumentiert werden (`consistency/docs.py:9-44` erzwingt das als ERROR) — jedes neue Flag erzeugt also *selbst* Doku-Drift-Potenzial. Stattdessen:

- C2/C3 hängen sich in die **bestehende Default-Sync-Stage** (analog `sync_knowledge_engine`, Phase 2.5 in `sync_pipeline.py`).
- Respektieren `dry_run` und `write_checked` (`knowledge.py:158`) — derselbe Idempotenz- und Log-Kontrakt.
- `--check` (sync.py:149) meldet Abweichung, ohne zu schreiben.
- Wiederverwendung des Idempotenz-Musters aus `standalone.py:387` (`if existing == content: unchanged`), inkl. Stale-File-Entfernung analog `standalone.py:395-400`.

**Optional, nicht empfohlen:** `--render-docs` als Alias zu `--render-standalone` (sync.py:226) für den manuellen Regenerations-Einzelruf. Trade-off T-5.

### 3.4 Fallback-Verhalten

| Situation | Verhalten | Begründung |
|---|---|---|
| Faktum nicht berechenbar (z. B. `config/ai-providers.yaml` fehlt) | **fail-soft → `""`**, exakt wie `_load_block_snippet` (`config.py:1850-1851`) | Konsistenz mit dem etablierten Snippet-Kontrakt |
| Platzhalter-**Name** unbekannt (Tippfehler) | **bleibt wörtlich stehen** (`substitution.py:87`, Default-`keep`) + `--validate` ERROR | Verify-by-construction: ein unaufgelöster `{{DOCS_*}}` *ist* der Drift-Indikator |
| `--dry-run` | rendert, schreibt nicht, loggt `would-update` | Standardvertrag |
| `docs/INDEX.md` existiert als Scaffold-Skeleton (`spec_plan_scaffold.py:24`) | Generator erkennt `_FILE_INDEX_SKELETON`-Präfix und ersetzt ihn **einmalig** durch den Voll-Index; C8 verhindert Overwrite | sonst zerstört der Generator den KE-off-Fallback (IMPACT-2) |
| Consumer-Projekt ohne `docs/`-Verzeichnis | Feature-Flag `docs-consolidation.enabled` (Default `true` in agent-meta, `false` in Consumer via `.agent-meta`/`project.yaml`) | kein ungefragter Schreibvorgang in Fremdprojekten |

### 3.5 Drift-Verhalten

`scripts/lib/generated_file_drift.py` hasht heute nur `.agent-meta-managed`-verzeichnete Dateien (`_managed_names`, `:92`). Design: README-Marker-Regionen und `docs/INDEX.md` werden in `capture_generated_file_hashes()` aufgenommen → Hand-Edit-Drift erzeugt WARNING + `.sync-backup-*` vor dem Overwrite (`generated_file_drift.py:12-15`). Damit greift derselbe Mechanismus, der heute die 179 `*.sync-backup-*`-Leichen in `.claude/agents/` erzeugt hat — diesmal *an der richtigen Stelle*.

**Marker-Syntax in `README.md` (Kompatibilität mit `context.py:36` `_MANAGED_BLOCK_RE` und `.gitignore`-Block bei `context.py:294-295`):**

```
<!-- agent-meta:docs-begin facts -->
…generiert…
<!-- agent-meta:docs-end -->
```

Der Doku-Marker ist ein **eigener** Namespace neben `agent-meta:managed-begin` (`context.py:1264`, `AGENTS.md`), damit die Doku-Region nie mit der Provider-Kontext-Region kollidiert.

---

## 4. VERIFICATION — Verify-by-construction

Erweiterung von `scripts/lib/consistency/docs.py`, registriert in `consistency-check.py:52-56`:

| # | Check | Erkennt | Severity | Gate |
|---|---|---|---|---|
| V1 | `check_no_manual_counts` | Zeilen in `README.md`/`llms.txt`/`ARCHITECTURE.md`, die auf `^\s*\d+\s+(agents?|hooks?|providers?|pipelines?|presets?|configs?|templates?|tiers?)` matchen **außerhalb** eines `agent-meta:docs-*`-Markers | F1-F4, F14 | ERROR (Start: WARNING) |
| V2 | `check_docs_index_completeness` | jede getrackte `docs/**/*.md` (außer `_archive/`, `archive/`) fehlt in `docs/INDEX.md` | F8, toter Verweis | ERROR |
| V3 | `check_internal_links` (neu) | relative Markdown-Links auf nicht existierende Ziele in `docs/**` + `README.md` + `llms.txt` | F15, `docs/REQUIREMENTS.md:21` | ERROR |
| V4 | `check_readme_docs_index` (erweitert von `:100`) | heute nur `docs/api/*.md` → generalisiert auf den gesamten `docs/`-Baum | F8 | ERROR (bestehend) |
| V5 | `check_role_generation_parity` | `project.yaml roles:` ⊄ generierte Provider-Agent-Dateien (fängt `se-component-requirements`, F13) | F13 | WARN solange `systems-engineering.enabled: false` (project.yaml:12-13), sonst ERROR |
| V6 | `check_docs_facts_fresh` | gerenderter `DOCS_*`-Block ≠ C1/C2-Output | Drift nach Hand-Edit | ERROR |
| V7 | `check_wiki_staleness` | Wiki-Seite mit `derived-from` älter als die Quelle, oder ohne `derived-from` bei `type: Architecture` | F5, F10, F11 | WARN |
| V8 | `check_spec_plan_path_convention` | Spec/Plan außerhalb `docs/{specs,plans,spikes}` bzw. nicht in `archive/` | F7, F16 | WARN |
| V9 | `check_stale_backups` | `*.sync-backup-*` in Provider-Verzeichnissen älter als N Tage | 179 Leichen | WARN (lokal, gitignored `.gitignore:22`) |

**Drift-Gate in der Pipeline:** `sync.py --check` (`:149`) und `--validate` (`:153`) dürfen bei V1/V2/V3/V6 nicht grün sein. `--validate` ist laut `project.yaml:193` bereits der TEST_COMMAND.

**Szenario:** `tests/scenarios/63-docs-facts-drift.md` — Offset-Drift (Rolle hinzugefügt, Index nicht regeneriert) muss `--check` fehlschlagen lassen. **Ownership: Track A** (arbeitet in `tests/`), daher in Welle 2 koordiniert, nicht parallel geschrieben.

**Anti-Pattern, das wir vermeiden:** V1 als Regex-Whitelist-Guard kann Fehlalarme erzeugen (z. B. „6 DoD presets" in `README.md:381` ist *korrekt* und soll generiert werden). Deshalb: V1 prüft nicht die Zahl, sondern die **Abwesenheit einer Marker-Region an dieser Stelle** — der Autor muss die Zahl entweder generieren lassen oder die Zeile als bewusste Ausnahme unter `<!-- agent-meta:docs-exempt: reason -->` markieren. Kein stilles Durchwinken, aber auch keine Regex-Hexerei.

---

## 5. KNOWLEDGE_WIKI_POLICY

### 5.1 Unveränderlichkeit von `knowledge/sources/`

- `knowledge/sources/` ist **append-only**. Bestehende Snapshots werden nie editiert, nie gelöscht, nie umformatiert.
- Ein Update erzeugt einen **neuen** Snapshot mit `supersedes: <alter-pfad>` im Frontmatter. Alte Snapshots bleiben als historische Belege stehen.
- Der einzige Schreiber ist `knowledge-ingestor`; `knowledge-curator`/`knowledge-gardener` haben dort kein Schreibrecht (Pflicht-Don't in `knowledge/schema.md:45-46` verankern).
- Begründung: Der Snapshot ist Beweissicherung („was stand am 2026-09-03 in `ARCHITECTURE.full.md`"). Genau diese Beweiskraft macht `status:stale-upstream` (`index.md:24`) wertvoll — wer sie zerstört, verliert die Erklärbarkeit des Drift-Zustands.

### 5.2 Abgrenzung Quellen ↔ Wiki ↔ Index ↔ Log

| Schicht | Ort | Schreibrecht | Ableitung | Pflicht-Frontmatter |
|---|---|---|---|---|
| **Quelle** | `knowledge/sources/` | nur `knowledge-ingestor`, additiv | keine | `source-of`, `captured-at`, `immutable: true`, optional `supersedes` |
| **Wiki-Seite** | `knowledge/wiki/{concepts,entities,topics,…}/` | Knowledge-Agenten (LLM-owned) | **`derived-from: <rel-pfad>` + `derived-at: <ISO>` Pflicht** | `type`, `derived-from`, `derived-at`, `status` |
| **Index** | `knowledge/wiki/index.md` | **Generator (C6)** | 1:1 aus dem Dateisystem | — |
| **Log** | `knowledge/wiki/log.md` | Generator-**Append** + manuell erlaubt | 1 Zeile pro Sync mit Wiki-Änderung | — |

**Regel:** `type: Architecture` ohne `derived-from` ist verboten (V7). Damit kann die Wiki kein zweiter Architektur-SSoT werden (F5) — sie ist ausschließlich Schatten mit Herkunftsangabe.

### 5.3 Staleness-Deklaration

C7 berechnet zwei orthogonal dimensionierte Flags:

1. **`status:stale-source`** — `mtime(derived-from) > derived-at`. Semantik: *die Quelle hat sich seit der Ableitung geändert*. Automatisch, objektiv, billig.
2. **`status:age`** (Beobachtung, kein Status) — Alter der Wiki-Seite in Tagen. `project.yaml:37-44` listet `stale-index` bereits als Lint-Check; wir liefern die Daten dafür.

**Verhältnis zum heutigen Zustand:** Das handgepflegte `status:stale-upstream` (`index.md:24`) ist eine *menschliche* Bewertung („Quelle räumt sich selbst als veraltet ein", `ARCHITECTURE.md:3`). Es bleibt als historisches Tag erhalten, wird aber nicht mehr manuell gepflegt, sondern aus `ARCHITECTURE.md:3` **maschinell extrahiert** (Regex auf `> Repo version:` / „last substantively reviewed"). Der Drift zwischen „ARCHITECTURE.md behauptet 0.92.0" und „VERSION sagt 1.2.0-beta.2" ist damit ein Datenpunkt, kein manueller Pflegeakt.

### 5.4 `index.md` generieren — Policy-Bruch mit Bedingungen

`knowledge.py:114` sagt explizit: *„never overwrites existing `schema.md`/`wiki/index.md`/`wiki/log.md`"*. Ein Generator für `index.md` bricht diese Policy.

**Empfehlung: ja, unter Bedingungen.**
- (a) `schema.md` (`:14-18` des Bundles) wird in derselben Welle um einen Paragraphen „index.md is generated" ergänzt — strukturelle Änderung, braucht Sign-off (schema.md:44-46).
- (b) `knowledge-indexer` (`.claude/skills`/`agents/1-generic/knowledge-indexer.md`) wird umgeschrieben: von „schreibe index.md" zu „prüfe Generator-Output, melde Drift". Provider-agnostik-Policy beachten (kein Claude-Literal).
- (c) `log.md` bekommt vom Generator **eine Zeile pro Sync angehängt**, wenn sich Wiki-Dateien geändert haben → schließt die 4-Wochen-Lücke aus F10 strukturell.
- (d) Rollback-Fenster: Flag `knowledge-engine.okf.index-mode: llm|generated`, Default `llm` für ein Release, Default `generated` danach.

**Verworfene Alternative:** `index.md` LLM-owned lassen und Drift nur melden (V7). Verworfen, weil genau dieser Zustand F10/F11 überhaupt erst erzeugt hat — Verify-only löst Symptome, Generierung löst die Ursache.

---

## 6. MIGRATION_ORDER

| Welle | Inhalt | Abhängig von | Parallelisierbar mit | Rückrollpunkt |
|---|---|---|---|---|
| **W0** | Design-Freeze, Contract-Liste (§7), Branch `chore/docs-consolidation` | — | — | — |
| **W1** | C1 DocFacts + C2 DocRenderer + C4. **Rein additiv**: keine Datei wird verändert, `DOCS_*`-Platzhalter existieren nur im Code. `llms.txt` bekommt den ersten Block. | W0 | W2 (unterschiedliche Dateien) | revert; kein Datei-Diff |
| **W2** | C5 Checks V1–V6 in `consistency/docs.py`. **V1 startet als WARNING** (Bestandsschutz), `--validate` noch nicht blockierend. | W1 (V6 braucht C1) | W3 | Flag `docs-consolidation.checks.strict: false` |
| **W3** | `docs/INDEX.md` Generator + C8 Scaffold-Guard. **Erster echter Datei-Diff.** `docs/INDEX.md` wird tracked. | W1 | W2, W4 | `git rm docs/INDEX.md`; Scaffold-Skeleton regeneriert |
| **W4** | Architektur-Konsolidierung: `git mv ARCHITECTURE.full.md docs/architecture/00-overview-full.md`, Root-Stub, Tabelle ergänzen. | W3 (Index muss das neue Ziel kennen) | W5, W6 | `git mv` zurück + Stub-Datei wiederherstellen |
| **W5** | Guides + `howto/`-Auflösung + `derived-from`-Annotation in `knowledge/wiki/**` (C7). | W1 (C7 braucht C1) | W4, W6 | `git mv` zurück; Annotationen additiv pro Seite revertierbar |
| **W6** | Spec/Plan-legacy: `git mv docs/superpowers/{specs,plans} docs/{specs,plans}/archive/superpowers/`, `project.yaml paths.legacy` erweitern (`:61-63`). | W3 | W4, W5 | Config-Key `legacy` ist additiv → alter Eintrag + neue Zeile; Rückroll = Eintrag entfernen |
| **W7** | Knowledge-Wiki-Policy: `index.md`-Generator (C6), `log.md`-Append, `schema.md`-Update, `knowledge-indexer`-Umschreibung. | W5 (`derived-from` muss stehen), W3 | — (kein Parallel) | `index-mode: llm` im project.yaml → Generator stumm |
| **W8** | Hygiene: `check_stale_backups`, Rollen-Parität `se-component-requirements`, README-Totverweise (F15), `llms.txt`-Providerzahl, ID-System-Klärung `REQ-*` vs `SPEC-*` (F16). | W2, W3 | — | additiv |

**Ownership-disjunkte Parallelität:** W2 ‖ W3 ‖ W5 sind gleichzeitig ausführbar (Dateien: `scripts/lib/consistency/docs.py` / `docs/INDEX.md` + `scripts/lib/doc_*.py` / `docs/guides/` + `knowledge/wiki/**`). **Konflikt:** W1/W2 berühren `scripts/lib/config.py` bzw. `scripts/lib/consistency/*` — **dieselben Dateien, an denen Track A arbeitet.** Deshalb: W1/W2 nicht parallel zu Track A starten, sondern sequenziell danach; pro Welle ein Commit pro Datei, vor jedem Merge Rebase gegen den Track-A-Branch.

**Reihenfolge-Begründung:** W1 vor allem (additiv, kein Diff, größte Erkenntnis). W3 vor W4/W6, weil beide Wellen `git mv` sind und ein existierender kanonischer Index die neuen Pfade sofort sichtbar macht. W7 zuletzt und isoliert, weil es die einzige Welle mit echtem Policy-Bruch und Datenverlust-Potenzial ist (LLM-Handpflege → Generator).

---

## 7. IMPACT — öffentliche Contracts

### 7.1 Berührte Verträge

| Contract | Status | Änderung |
|---|---|---|
| Platzhalter-Namen `{{*_BLOCK}}` | **additiv** | Neue `DOCS_*`-Namespace. Bestehende Namen unverändert; `QUALITY_PIPELINES_BLOCK` (config.py:1882) bleibt ohne Konflikt. |
| Snippet-Inlining-Transform | **unverändert** | `_load_block_snippet` (config.py:1842-1858) wird für `snippets/docs/*.md` wiederverwendet, nicht modifiziert. |
| Generierte Kontextdateien (`AGENTS.md`, `CLAUDE.md`, Provider-Dirs) | **unverändert** | Kein Eingriff. `PROJECT_STRUCTURE` in `project.yaml:205-219` wird inhaltlich korrigiert (Config-Edit, kein Doku-Edit) — dieser Block landet in AGENTS.md, ist also **Medium-Risk für Downstream** (Layout-Änderung sichtbar). |
| sync.py-CLI | **unverändert** | Kein neues Flag (§3.3). `cli-reference.md` (docs/api) bleibt unverändert; `check_sync_cli_docs` (docs.py:9) bleibt grün. |
| Provider-Verzeichnisse (`.claude/` etc.) | **unverändert** | gitignored (`.gitignore:13-17`). Doku-Dateien werden **nicht** in Provider-Verzeichnisse deployed. |
| `.gitignore`-Managed-Block | **unverändert** | `README.md`/`docs/INDEX.md` sind **keine** generierten Provider-Dateien → nicht gitignored, nicht deployed. Der Doku-Marker ist ein eigener Namespace neben `context.py:294-295`. |
| `docs/INDEX.md` | **Vertrag existierte, Datei fehlte** | Jetzt implementiert wie in `spec_plan_scaffold.py:23` + `project.yaml:70` spezifiziert. |

### 7.2 Breaking Changes für Downstream-Projekte

| # | Breaking | Betroffen | Schwere | Mitigation |
|---|---|---|---|---|
| B1 | `docs/superpowers/{specs,plans}` verschwindet → Downstream mit `spec-plan-workflow.paths.legacy` zeigt ins Leere | alle Submodule-Consumer | **mittel** | `project.yaml:61-63` `legacy:`-Liste wird additiv um die neuen Archivpfade ergänzt, alte Einträge 1 Release lang mit Deprecation-WARNING toleriert; Release-Notes-Pflicht; Minor-Bump |
| B2 | `docs/INDEX.md` ist jetzt generiert **und** vom Scaffold geschrieben (`spec_plan_scaffold.py:67`) → Doppel-Writer | Consumer mit `knowledge-engine.enabled: false` (Szenarien 55/56, registry.md:102) | **hoch** | C8 Scaffold-Guard: Generator erkennt den Skeleton-Präfix und überschreibt nicht; `is_unchanged`-Muster aus `standalone.py:387`. Szenario 54/55/56 in der Regression explizit grün halten |
| B3 | `README.md` enthält `<!-- agent-meta:docs-* -->`-Marker → sichtbar für jeden, der die README als LLM-Kontext nutzt (`llms.txt:5` beschreibt genau diesen_USE-CASE) | AI-Consumer | **niedrig** | Marker sind HTML-Kommentare → in Rendered-Markdown unsichtbar; kein Verhaltenswechsel |
| B4 | `check_no_manual_counts` als ERROR blockiert Contributions mit eigenen Zahlen in der README | Consumer-Contributors | **niedrig** | Default `docs-consolidation.checks.strict: false` in Consumer (nur agent-meta selbst strict); Exemption-Marker dokumentiert |
| B5 | `knowledge/wiki/index.md` wird generiert → handgeschriebene Einträge gehen bei Regeneration verloren | KE-Nutzer mit eigenem Wiki | **hoch** | Nur in W7, mit `index-mode: llm`-Rollback-Flag und vorab generiertem Diff-Review; ReqogniLoom-Workspace-Export als Zwischenkopie |
| B6 | `AGENTS.md`-Layout (aus `PROJECT_STRUCTURE`) ändert sich → generierte Kontextdatei in **jedem** Consumer | alle Submodule-Consumer | **niedrig** | managed-block-Mechanismus (`context.py:36`) fängt Handpflege ab; Drift-Detection meldet |

**Entlastung (wichtig):** Die Doku-Konsolidierung betrifft ausschließlich **Repo-interne** Dateien. `docs/`, `README.md`, `ARCHITECTURE.md`, `knowledge/` werden von `sync.py` **nicht** in Consumer-Projekte generiert (anders als `AGENTS.md`/`CLAUDE.md`/Provider-Dirs). Deshalb sind B1–B5 keine Consumer-Breaks im eigentlichen Sinne, sondern Repo-interne Migrationen; **echter** Downstream-Impact ist auf B2, B5 (nur bei KE-Nutzung) und B6 begrenzt.

---

## 8. TRADE_OFFS

### T-1 · Doku-Fakten: berechnen vs. Fakten-Datei vs. manuell

| Option | Begründung für | Begründung gegen |
|---|---|---|
| **A: Berechnen aus kanonischen Quellen (gewählt)** | Kein vierter SSoT; Drift strukturell unmöglich; C1 rein testbar | Mehr Code in C1; volatile Quellen (`tests/scenarios/`) erzeugen Doku-Churn |
| B: `.meta-config/doc-facts.yaml` als Fakten-SSoT | Explizit, reviewbar, kein Code | **Genau das Problem, das wir lösen**: eine gepflegte Datei driftet gegen die Quellen und braucht selbst einen Check |
| C: Zahlen manuell lassen + nur Reviewer-disziplin | Null Code | F1–F4 belegen, dass das bereits 4fach gescheitert ist |

### T-2 · Rendering: Fakten-Blöcke in `README.md` vs. Vollgenerierung vs. neues generiertes File

| Option | Begründung für | Begründung gegen |
|---|---|---|
| **A: Hybrid — Faktenblöcke in `README.md` (Marker), `docs/INDEX.md` vollgeneriert (gewählt)** | Handprosa bleibt editierbar; Zahlen werden trotzdem strukturell erzwungen; `standalone.py` liefert das Idempotenz-Muster; Drift-Detection greift via Hash-Store | Zwei Render-Modi (Block + Volltext) = zwei Codepfade |
| B: README komplett generieren (Template + Facts) | Maximale Driftfreiheit, ein Codepfad | README wird zur Sync-Ausgabe; Autoren können nicht mehr direkt schreiben → hohe Reibung, führt zu `allow-edits`-Allowlist-Auswüchsen (vgl. `.meta-config/drift-allowlist.yaml`, `generated_file_drift.py:37`) |
| C: `README.facts.md` als generiertes Nachbarfile | README bleibt komplett handgepflegt, null Marker | Zwei Zahlen-Quellen im selben Blickfeld → die genaueste Drift-Quelle, die wir bauen könnten |

### T-3 · Doku-Index: `docs/INDEX.md` vs. `docs/README.md` vs. Root-README

| Option | Begründung für | Begründung gegen |
|---|---|---|
| **A: `docs/INDEX.md` (gewählt)** | **Vertrag existiert bereits** (`spec_plan_scaffold.py:23`, `project.yaml:70`, `registry.md:101-102`) — er erfüllt einen spezifizierten, getesteten Fall; Szenarien 54/55/56 bleiben grün | GitHub rendert `INDEX.md` beim Browsen in `docs/` nicht automatisch → Entdeckbarkeit etwas schlechter |
| B: `docs/README.md` als kanonisch | GitHub-nativ, bessere Browsing-UX | Bricht den bestehenden Vertrag; erzwingt Änderung an `spec_plan_scaffold.py` + 3 Registry-Szenarien + project.yaml; **verworfen: unnötiger Breaking Change für kosmetischen UX-Gewinn** |
| C: Root-README als einziger Index | Kein Index-Duplikat | Skaliert nicht (191+ Dateien); README wäre 100 % generiert → T-2 B |

### T-4 · Architektur: Root-`ARCHITECTURE.md` löschen vs. Stub vs. verschieben

| Option | Begründung für | Gegen |
|---|---|---|
| **A: Generierter Stub (gewählt)** | `llms.txt:24` linkt auf `ARCHITECTURE.md`; Löschen bricht Deeplinks; Stub löst F5 (5-fache Doku), weil er keine eigenen Inhalte mehr hat | Pflege des Stubs (trivial: generiert) |
| B: Löschen | Radikalste Konsolidierung | **Bricht `llms.txt:24` und externe Bookmarks** — `llms.txt` ist selbst der AI-Einstiegspunkt |
| C: Unverändert lassen | Kein Diff | F5 bleibt vollständig ungelöst |

### T-5 · sync.py-CLI: neues `--render-docs` vs. integriert

| Option | Begründung für | Gegen |
|---|---|---|
| **A: In den Default-Sync integriert, kein Flag (gewählt)** | Kein CLI-Wachstum → kein `cli-reference.md`-Pflegeaufwand (`docs.py:9-44`); `--dry-run`/`--check` funktionieren automatisch mit | Kein gezielter Einzelaufruf „nur Doku regenerieren" |
| B: `--render-docs` (Symmetrie zu `--render-standalone`, sync.py:226) | Symmetrie, gezielter Aufruf | Jedes Flag = Doku-Pflicht + Doku-Drift-Risiko; `--render-standalone` existiert, weil Standalone *außerhalb* des Normal-Sync liegt — Doku tut das nicht |
| C: Doku-Generierung **nicht** in sync.py, sondern separates `scripts/render-docs.py` | Keine sync.py-Komplexität; unabhängige CI-Stufe | Zwei Build-Eintrittspunkte; `read_version()`/`load_roles_config()`-Reuse über Modulgrenze; --check müsste den externen Runner aufrufen → Doppelpflicht |

### T-6 · Knowledge-Wiki: `index.md` generieren vs. LLM-owned vs. Dual-Write

| Option | Begründung für | Gegen |
|---|---|---|
| **A: Generiert, `index.md`-Flag + Rollback (gewählt)** | F10 (4-Wochen-Lücke) und F11 (handgepflegtes Stale-Tag) sind Ursachen, die nur Generierung beseitigt | Bricht Policy `knowledge.py:114` → B5 |
| B: LLM-owned + Verify-only (V7) | Kein Datenverlust, kein Policy-Bruch | Lässt genau die Drift zu, die wir dokumentiert haben |
| C: Dual-Write (Generator + LLM-Ergänzungen) | Flexibel | Zwei Autoren auf eine Datei → Drift ist wieder programmatisch garantiert; schlechteste Variante |

---

## 9. RISKS

| # | Risiko | W. | Mitigation |
|---|---|---|---|
| R1 | **Doku-Diff-Churn**: jede Rollen-/Hook-Änderung erzeugt einen README-Diff; bei volatilen Zahlen (Szenarien, Track A) Flattern | hoch | Footer enthält **nur einen Fact-Hash, keinen Zeitstempel** (`standalone.py:365` nutzt Version, nicht Zeit — gleiches Muster). Volatile Faktum `{{DOCS_SCENARIO_COUNT}}` wird als „≥N" gerendert oder ganz aus README genommen und nur in `docs/INDEX.md` geführt |
| R2 | **LLM-Handpflege-Kollision im Wiki**: Knowledge-Agenten schreiben `index.md`, Generator überschreibt → Datenverlust (B5) | hoch | Generator-Diff-Review vor Aktivierung; `index-mode: llm`-Rollback; ReqogniLoom-Export als Zwischenkopie; W7 isoliert als letzte Welle |
| R3 | **Track-A-Konflikt**: parallele Änderungen in `scripts/lib/` und `config/` | hoch | W1/W2 sequenziell nach Track A; ein Commit pro Datei; Rebase vor jedem Merge; vor W1 `git log --oneline -20 -- scripts/lib/` prüfen |
| R4 | **V1-Fehlalarme** (`README.md:381` „6 DoD presets" ist korrekt) | mittel | V1 prüft Marker-Abwesenheit, nicht die Zahl; Exemption-Marker `<!-- agent-meta:docs-exempt: reason -->`; Start als WARNING |
| R5 | **Rollen-Parität `se-component-requirements`** (F13) | niedrig | V5 bleibt WARN solange `systems-engineering.enabled: false` (project.yaml:12-13); Fix ist ein Einzeiler in `project.yaml roles:`, gehört aber in W8 und ist ein **Config-Edit**, kein Doku-Edit |
| R6 | **Link-Check-Fehlalarme** auf externe URLs/Anker | mittel | V3 prüft nur relative repo-interne Pfade; Anker-Existenz als separate WARN-Stufe; Allowlist-Pattern in `docs-concepts: []` |
| R7 | **B2 Doppel-Writer** `docs/INDEX.md` (Generator vs. Scaffold) | hoch | C8 in derselben Welle wie W3; Szenarien 54/55/56 als harte Regression |
| R8 | **B1 Downstream-Bruch** durch `docs/superpowers`-Verschiebung | mittel | `legacy:`-Liste additiv erweitern + 1 Release Toleranz; Release-Notes |
| R9 | **Scope-Creep**: 191 `docs/*.md` + 100+ Wiki-Seiten → Migration wird zum Doku-Rewrite | mittel | Wellen sind additiv/git-mv-only; **keine inhaltliche Neuschreibung** in dieser Initiative; Inhaltsarbeit ist eigene REQs |
| R10 | **AGENTS.md-Bootstrap-Block** (66 Rollen hartgelistet am Repo-Ende) driftet ebenfalls | niedrig | **Bewusst außerhalb des Scopes** — als offene Frage OQ3 geführt, nicht in den Wellen |
| R11 | `docs/CODEBASE_OVERVIEW.md` (2245 Z) liegt außerhalb des SSoT-Baums und ist von `documenter` gepflegt (`log.md:30`: „HARD CONSTRAINT — gehört documenter-Agent") | mittel | Im SSoT-Baum als **eigenständiger Entry** geführt, aber Content-Ownership unangetastet; Generierung nur für Fakten-Footer |

---

## 10. OPEN_QUESTIONS

| # | Frage | Warum nicht entscheidbar | Empfehlung / Eskalation |
|---|---|---|---|
| **OQ1** | Sollen `knowledge/wiki/topics/` (43 Guides) vollständig in `docs/guides/` (31) aufgehen, oder bleibt das Wiki als LLM-optimierte Aufbereitung bestehen? | Produktentscheidung: Wiki-Seiten sind nicht 1:1 mit Guides (Duplikate *und* Unique), Merge verändert den Lesefluss für Knowledge-Agenten | **Eskalation an main_chat.** Design-Vorschlag: `docs/guides/` = SSoT, Wiki-Topics behalten nur, was es in `docs/` nicht gibt; Duplikate → Redirect. Umfang erst nach C4-Baum-Inventar bezifferbar |
| **OQ2** | `llms.txt` — generiert oder handgepflegt? | `llms.txt` ist bewusst prosaisch für LLM-Konsum; Vollgenerierung würde den Ton verlieren | Hybrid wie T-2 A: nur `{{DOCS_PROVIDERS_BLOCK}}` + `{{DOCS_REPO_FACTS_BLOCK}}`, Rest Handtext. Entscheidung liegt bei `agent-meta-manager` |
| **OQ3** | `AGENTS.md`-Bootstrap-Block (66 hartgelistete Agenten) mitgenerieren? | Block liegt in einer generierten Kontextdatei, die in **alle** Submodule-Consumer geht → B6-Risiko | **Scope-Grenze dieser Initiative.** Eskalation an `specifier` als eigene REQ, da es denselben `DOCS_*`-Mechanismus nutzen würde, aber einen anderen Blast Radius hat |
| **OQ4** | ID-System: `REQ-*` vs. `SPEC-<NAME>-YYYY-MM-DD` — vereinheitlichen oder als zwei Ebenen definieren? | Betrifft `docs/REQUIREMENTS.md` und 4 Spec-Bäume (F16); Umbenennung ist ein Traceability-Bruch für alle offenen Issues | Empfehlung: **keine Umbenennung.** Definiere `SPEC-*` als Spec-Pipeline-Artefakt-ID und `REQ-*` als Requirements-Master-ID, mit单向-Verweis. Entscheidung an `requirements` + `validator` |
| **OQ5** | Müssen die `DOCS_*`-Platzhalter auch in **bereits-released** agent-meta-Versionen funktionieren (Submodule-Pinning auf ältere Tags)? | Wenn ja, ist ein Backport nötig und `substitution.py` bekommt einen dritten Namespace | Additiv und rückwärtskompatibel — kein Backport nötig, da Doku-Platzhalter nur von C1/C2 aufgelöst werden, nie von Provider-Engines. Bestätigung durch `agent-meta-manager` |
| **OQ6** | Soll `docs/INDEX.md` **tracked** sein (git) oder generiert-untracked wie `.claude/`? | Tracked = im Review sichtbar (gut für Drift-PRs), generiert-untracked = keine Commits | Empfehlung: **tracked**, weil `docs/INDEX.md` laut `project.yaml:70` auch als Fallback-Skeleton *im Repo* geschrieben wird — tracked ist konsistent. Entscheidung an Orchestrator |

---

## 11. Trace-Anker

```
spec-id: SPEC-DOCS-CONSOLIDATION-2026-09-25
→ Eingang für concept-specifier (Stage "specify" in quality_pipelines.concept-driven-dev)
→ Empfohlene Wellen-Specs: SPEC-DOCS-FACTS-2026-09-25 (W1+W2),
                            SPEC-DOCS-INDEX-2026-09-25 (W3),
                            SPEC-DOCS-MIGRATION-2026-09-25 (W4-W6),
                            SPEC-KNOWLEDGE-INDEX-GEN-2026-09-25 (W7)
```
