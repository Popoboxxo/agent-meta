# Knowledge Engine — Phase B Design (7 Agenten + Routing)

**Status:** Entwurf zur Freigabe
**Branch:** `feat/knowledge-engine-phase-b`
**Quelle:** `docs/concepts/knowledge-engine-concept.md` (v4), §9-11; korrigiert gegenüber Phase-A-Erkenntnissen
**Vorgänger:** `docs/superpowers/specs/2026-07-23-knowledge-engine-phase-a-design.md` (Aktivierungsmechanismus + Bundle-Scaffolding, gemerged)
**Scope-Entscheidung:** Ein Plan für alle 7 Agenten (User-Entscheidung "One plan GO!").

## Phasenübersicht (Gesamtprojekt)

| Phase | Inhalt | Status |
|-------|--------|--------|
| A | Feature-Flag, Config-Schema, `knowledge.py`, `sync_knowledge_engine()`, Bundle-Scaffolding | gemerged |
| **B (diese Spec)** | 7 `knowledge-*` Agent-Templates + role-defaults.yaml + Routing-Integration + Provider-MD-Hints | zu spezifizieren |
| C | AdminUI-Integration (`/project/knowledge-engine`) | später, eigene Spec |
| D | Optional: dod-presets.yaml, export.yaml, mcp-registry.yaml Erweiterungen | deferred, nur bei Bedarf |

## Korrektur gegenüber Konzept-Dokument

Das Konzept-Dokument nimmt in §9 pro Rolle ein `conditional: knowledge-engine`-Feld in `role-defaults.yaml` an. **Dieses Feld existiert im Framework nicht** (dieselbe Korrektur wurde bereits in der Phase-A-Spec für `se-*` festgehalten). Gating läuft ausschließlich über `_is_role_enabled()`'s Präfix-Check (`role.startswith("knowledge-")`), der in Phase A bereits implementiert ist. Alle `role-defaults.yaml`-Einträge in dieser Spec lassen `conditional:` konsequent weg.

**Zweite Korrektur:** §11 des Konzepts schlägt einen statischen `{{#if KNOWLEDGE_ENGINE_ENABLED}}`-Block im `orchestrator.md`-Template für die Routing-Tabelle vor. Das ist unnötig — die tatsächliche Routing-Tabelle in `use-orchestrator.md` wird bereits automatisch aus `config/role-defaults.yaml` generiert (`scripts/lib/delegation_table.py::generate_intent_routing_table()` und `generate_agent_delegation_table()`), analog zum SE-Gating dort (`se_enabled = variables.get("SE_ENABLED", ...)`, dann `role_name.startswith("se-")`-Skip). Phase B erweitert diese zwei Funktionen um einen analogen `knowledge_enabled`-Skip für `role_name.startswith("knowledge-")` — kein Template-Block nötig.

## Architektur

Sieben neue Agent-Templates unter `agents/1-generic/`, gated durch die bestehende `_is_role_enabled()`-Prüfung (Zero-Overhead wenn `knowledge-engine.enabled` fehlt/false). Kein neuer Sync-Schritt, kein neues Config-Schema — Phase B ist reine Template- und Routing-Erweiterung, die auf den in Phase A bereits injizierten `KNOWLEDGE_*`-Variablen und der Bundle-Struktur aufbaut.

**Neue abgeleitete Variablen** (ergänzt in `scripts/lib/config.py`, direkt nach dem bestehenden Phase-A-Block bei Zeile 518, da erst jetzt Templates existieren, die sie konsumieren):

```python
variables["KNOWLEDGE_SCHEMA_PATH"] = f"{variables['KNOWLEDGE_BUNDLE_PATH']}/schema.md"
variables["KNOWLEDGE_WIKI_DIR"] = f"{variables['KNOWLEDGE_BUNDLE_PATH']}/wiki"
variables["KNOWLEDGE_SOURCES_DIR"] = f"{variables['KNOWLEDGE_BUNDLE_PATH']}/sources"
```

## Die 7 Agenten

| # | Agent | Tier | Memory | orchestrator_only | Karpathy-Op |
|---|-------|------|--------|--------------------|--------------|
| 1 | `knowledge-curator` | balanced | project | false | Schema/Planung |
| 2 | `knowledge-ingestor` | balanced | project | false | Ingest |
| 3 | `knowledge-querier` | fast | — | false | Query |
| 4 | `knowledge-linter` | fast | — | false | Lint |
| 5 | `knowledge-indexer` | nano | — | **true** | Index/Log |
| 6 | `knowledge-gardener` | nano | — | false | Maintenance |
| 7 | `knowledge-migrator` | balanced | — | false | Migration |

Vollständige Verhaltensbeschreibungen, OKF-Frontmatter-Pflichten, Touch-Radius-Konventionen und die exakten `role-defaults.yaml`-Blöcke (bereinigt um `conditional:`) stehen in `docs/concepts/knowledge-engine-concept.md` §9.2-9.8 — Quelle der Wahrheit für die Implementierungspläne, mit der o.g. Korrektur angewendet.

**Handoff-Contracts (neu):** `knowledge-spec-v1` (curator→ingestor), `knowledge-ingest-v1` (ingestor→indexer), `knowledge-lint-v1` (linter→gardener/ingestor), `knowledge-migration-v1` (migrator, terminal). Alle `input_contracts` sind entweder `task-spec-v1` (Runtime-Contract, von der Handoff-Validierung ausgenommen) oder werden von einer der 7 Rollen selbst produziert — keine `handoff.input-no-producer`-Warnung zu erwarten. Kein `target_roles`-Feld nötig (das Konzept sieht es nicht vor; ohne es wird auch keine `output-not-consumed`-Warnung ausgelöst).

**`knowledge-migrator` HARD CONSTRAINTS** (verbatim aus §9.8, sicherheitsrelevant): niemals `docs/CODEBASE_OVERVIEW.md`, `docs/REQUIREMENTS.md`, `CLAUDE.md`/`AGENTS.md`, `.claude/`/`.gemini/`/`.opencode/`, `VERSION`, `LICENSE` migrieren oder anfassen. `CHANGELOG.md` darf nur als Source kopiert werden (Original bleibt). Migration kopiert immer, verschiebt nie. Phase 2 (tatsächliche Migration) startet nur nach expliziter User-Freigabe des Phase-1-Discovery-Plans.

## Routing-Integration

1. **`config/role-defaults.yaml`:** 7 neue Rollen-Einträge (Struktur wie oben, ohne `conditional:`).
2. **`scripts/lib/delegation_table.py`:** In `generate_agent_delegation_table()` und `generate_intent_routing_table()` je eine Zeile ergänzt:
   ```python
   knowledge_enabled = variables.get("KNOWLEDGE_ENGINE_ENABLED", "false") == "true"
   ...
   if role_name.startswith("knowledge-") and not knowledge_enabled:
       continue
   ```
   (Analog zum bestehenden `se_enabled`/`role_name.startswith("se-")`-Skip in beiden Funktionen.)
3. **`_PARALLEL_LABELS`** (`delegation_table.py`): 7 neue Einträge, abgeleitet aus dem `routing.parallel`-Feld jeder Rolle (z.B. `"knowledge-ingestor": "✅ (Multi-Sources)"`, `"knowledge-indexer": "❌ (zentral)"`).
4. **`build_agent_hints()`** (`scripts/lib/agents.py`, nach der bestehenden Tabellen-Schleife, vor `return`): zusätzlicher Block mit Bundle-Pfaden und den 5 Knowledge-Workflows (Ingest/Query/Lint/Migration/Gardening), nur gerendert wenn `variables.get("KNOWLEDGE_ENGINE_ENABLED") == "true"` — Inhalt wie in Konzept §10.2 spezifiziert.
5. **`agents/1-generic/documenter.md`:** bedingter Block (`{{#if KNOWLEDGE_ENGINE_ENABLED}}...{{/if}}`) wie in Konzept §12 — dokumentiert nur die Bundle-**Struktur** in CODEBASE_OVERVIEW, keine Wiki-Inhalte; `{{KNOWLEDGE_SCHEMA_PATH}}` ausdrücklich als "nicht deine Datei" markiert.

## Datenfluss

```
Ingest-Pipeline:
  User → knowledge-curator (plant) → knowledge-ingestor (schreibt Wiki-Seiten)
       → knowledge-indexer (index.md + log.md) → optional knowledge-linter (Konsistenz)

Query-Pipeline:
  User → knowledge-querier (index-first, read-only, Synthese mit Citations)
       → optional File-Back als neue Concept-Seite → knowledge-indexer

Lint-Pipeline:
  knowledge-linter (10 Checks) → Findings → knowledge-gardener (mechanisch)
       oder knowledge-ingestor (inhaltlich) je nach Finding-Typ

Migration-Pipeline (einmalig):
  User → knowledge-migrator Phase 1 (Discovery, read-only) → User-Freigabe
       → Phase 2 (Copy + OKF-Frontmatter) → Phase 3 (Cleanup)
       → knowledge-indexer (initiales index.md/log.md) → knowledge-linter (Validierung)
```

## Fehlerbehandlung

- Alle 7 Templates werden nur generiert wenn `knowledge-engine.enabled: true` — bei `false`/fehlend identisches generiertes Ergebnis wie vor Phase B (Zero-Overhead, wie Phase A).
- `knowledge-indexer` ist `orchestrator_only: true` — erscheint in der Routing-Tabelle (wie die bestehenden `orchestrator_only`-Rollen `principal-developer` etc.), aber ohne `intent_keywords`, sodass die Beschreibung als einziger Hinweis dient (Konvention: nicht direkt vom User ansprechbar, nur Delegationsziel anderer Knowledge-Agenten).
- `knowledge-migrator` bricht Phase 2 ab (kein Schreiben) wenn Phase 1 keine explizite User-Freigabe erhalten hat — kein automatischer Fortschritt.
- `knowledge-gardener` und `knowledge-ingestor` haben strikt getrennte Schreibrechte-Konventionen (Form vs. Inhalt) — als Verhaltensregel in beiden Templates dokumentiert, nicht technisch erzwungen (Konvention, kein Tool-Gate).

## Testing

- Template-Rendering-Test pro Agent (7x): Frontmatter valide, `{{KNOWLEDGE_*}}`-Platzhalter korrekt substituiert wenn aktiviert, Agent-Datei wird NICHT generiert wenn deaktiviert.
- `role-defaults.yaml`-Schema-Validierungstest für die 7 neuen Einträge (`python scripts/sync.py --dry-run --validate`).
- Handoff-Contract-Test: `check_handoff_contracts()` liefert keine neuen Findings für die 7 Rollen (input/output-Paare bereits konsistent, s.o.).
- Routing-Tabellen-Test: `generate_intent_routing_table()`/`generate_agent_delegation_table()` mit `KNOWLEDGE_ENGINE_ENABLED=false` → keine `knowledge-*`-Zeilen; mit `=true` → alle 7 Zeilen vorhanden.
- Regressionstest: bestehende SE-Zeilen und Standard-Rollen unverändert bei `KNOWLEDGE_ENGINE_ENABLED=false` (Zero-Overhead-Garantie, gleiches Muster wie Phase A).
- Integrationstest: vollständiger `sync.py`-Lauf mit `knowledge-engine.enabled: true` auf agent-meta selbst (Self-Hosting-Test wie bereits in Phase A begonnen) — prüft dass CLAUDE.md den Knowledge-Engine-Block und alle 7 Agenten in der Tabelle enthält.

## Out of Scope (Phase B)

- AdminUI-Integration (→ Phase C)
- `config/knowledge-presets.yaml`, DoD-Presets/Export/MCP-Registry-Erweiterungen (→ Phase D)
- Tatsächliche Erstmigration von agent-meta's eigenen `docs/` (Ausführung des `knowledge-migrator`-Agenten selbst ist ein späterer, separater User-Auftrag — Phase B liefert nur das Template)
