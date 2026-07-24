# Knowledge Engine — Phase A Design (Aktivierungsmechanismus & Bundle-Scaffolding)

**Status:** Entwurf zur Freigabe
**Branch:** `feat/knowledge-engine-phase-a`
**Quelle:** `docs/concepts/knowledge-engine-concept.md` (v4, Konzept nicht implementiert)
**Scope-Entscheidung:** Das Gesamtkonzept (7 Agenten, sync.py-Kern, AdminUI, optionale Config-Erweiterungen) ist zu groß für einen Plan. Diese Spec deckt nur **Phase A** ab — die Aktivierungs- und Scaffolding-Grundlage, von der alle weiteren Phasen abhängen.

## Phasenübersicht (Gesamtprojekt)

| Phase | Inhalt | Status |
|-------|--------|--------|
| **A (diese Spec)** | Feature-Flag, Config-Schema, `knowledge.py`, `sync_knowledge_engine()`, Bundle-Scaffolding, `knowledge-schema.template.md` | zu spezifizieren |
| B | 7 `knowledge-*` Agent-Templates + role-defaults.yaml + Routing/CLAUDE.md-Hints | später, eigene Spec |
| C | AdminUI-Integration (`/project/knowledge-engine`) | später, eigene Spec |
| D | Optional: dod-presets.yaml, export.yaml, mcp-registry.yaml Erweiterungen | deferred, nur bei Bedarf |

## Architektur (Phase A)

Folgt exakt dem bestehenden Zero-Overhead-Aktivierungsmuster der `systems-engineering`-Kaskade — kein neues Konzept, sondern Wiederverwendung eines etablierten Patterns:

- **Kein** neues `conditional:`-Feld in `role-defaults.yaml` (das Konzept-Dokument nimmt das fälschlich an — es existiert nicht; `_is_role_enabled()` prüft aktuell nur `role.startswith("se-")` per Präfix-Check ohne Config-Lookup pro Rolle). Phase A erweitert `_is_role_enabled()` in `scripts/lib/agents.py:393` um einen analogen `knowledge-`-Zweig.
- **Config-Block** `knowledge-engine:` in `.meta-config/project.yaml`, analog zu `systems-engineering:` (project.yaml:10-11).
- **Variablen-Injektion** in `build_variables()` (`scripts/lib/config.py`, aktuell ab Zeile ~501 für SE — Knowledge-Engine-Block wird direkt danach ergänzt).
- **Neue Sync-Phase 2.5** `sync_knowledge_engine()` in `scripts/sync.py`, aufgerufen nach Phase 2 (Per-Provider Sync) und vor Phase 3 (Provider Isolation).

## Config-Schema

Neuer Top-Level-Block in `.meta-config/project.yaml`:

```yaml
knowledge-engine:
  enabled: false          # Default OFF — opt-in wie systems-engineering
  domain: research        # enum: research | personal | business | book | internal-docs | custom
  bundle-path: knowledge  # Root-Verzeichnis des Knowledge Bundle
```

**Bewusst reduziert gegenüber Konzept-Dokument:** Phase A implementiert nur `enabled`, `domain`, `bundle-path`. Die im Konzept vorgeschlagenen Unterblöcke `okf{}`, `operations{}`, `migration{}`, `search{}` gehören zu Phase B/D (sie steuern Agenten-Verhalten, das in Phase A noch nicht existiert) und werden hier bewusst **nicht** implementiert, um YAGNI einzuhalten — sie können in Phase B ergänzt werden, wenn die Agenten sie tatsächlich konsumieren.

**JSON-Schema-Ergänzung:** `config/project-config.schema.json` wird um den `knowledge-engine`-Block ergänzt (properties: `enabled` boolean, `domain` enum, `bundle-path` string). Hinweis: `systems-engineering` selbst ist aktuell NICHT im Schema erfasst — Root-Schema hat kein `additionalProperties: false`, das Feld funktioniert also auch unvalidiert. Aus Konsistenzgründen wird `knowledge-engine` trotzdem ins Schema aufgenommen (bessere IDE-Autocomplete, Konvention laut `conventions.md`).

## Komponenten

### 1. `scripts/lib/agents.py::_is_role_enabled()`

```python
def _is_role_enabled(role: str, config: dict) -> bool:
    """Check if a role is enabled based on project config (e.g. systems-engineering flag)."""
    if role.startswith("se-"):
        se_config = config.get("systems-engineering") or {}
        return se_config.get("enabled", True)
    if role.startswith("knowledge-"):
        ke_config = config.get("knowledge-engine") or {}
        return ke_config.get("enabled", False)
    return True
```

Phase A fügt nur den Zweig hinzu — er greift erst in Phase B, sobald `knowledge-*`-Rollen existieren. Kein Verhalten ändert sich für bestehende Projekte, solange `knowledge-engine.enabled` fehlt oder `false` ist.

### 2. `scripts/lib/config.py::build_variables()`

Direkt nach dem bestehenden SE-Block (ab Zeile ~501) ergänzt:

```python
ke_config = config.get("knowledge-engine", {})
variables["KNOWLEDGE_ENGINE_ENABLED"] = "true" if ke_config.get("enabled", False) else "false"
variables["KNOWLEDGE_DOMAIN"] = ke_config.get("domain", "research")
variables["KNOWLEDGE_BUNDLE_PATH"] = ke_config.get("bundle-path", "knowledge")
```

Kein `KNOWLEDGE_SCHEMA_PATH`, `KNOWLEDGE_WIKI_DIR`, `KNOWLEDGE_SOURCES_DIR`, `KNOWLEDGE_CONCEPT_TYPES` in Phase A — diese sind reine Ableitungen (`f"{bundle_path}/wiki"` etc.), die erst gebraucht werden, wenn Agenten (Phase B) oder Templates sie referenzieren. Werden dort direkt aus `KNOWLEDGE_BUNDLE_PATH` abgeleitet statt vorab dupliziert zu werden.

### 3. Neues Modul `scripts/lib/knowledge.py`

Minimal für Phase A — nur was zum Scaffolding gebraucht wird:

```python
DOMAIN_CONCEPT_TYPES = {
    "research": ["paper", "finding", "method", "dataset"],
    "personal": ["person", "event", "place", "memory"],
    "business": ["customer", "deal", "product", "decision"],
    "book": ["character", "location", "theme", "chapter"],
    "custom": ["concept"],
}

def generate_schema(domain: str, bundle_path: str) -> str:
    """Render knowledge-schema.template.md for the given domain."""
    ...

def generate_initial_index() -> str:
    """Render empty index.md skeleton."""
    ...

def generate_initial_log() -> str:
    """Render empty log.md skeleton with header + format documentation."""
    ...
```

Kein `detect_target_repo()` in Phase A (das Konzept sieht das für Migration/Phase D vor — kein Bedarf ohne Migrator-Agent).

### 4. `sync_knowledge_engine()` — neue Phase 2.5 in `scripts/sync.py`

Aufgerufen nach Phase 2, vor Phase 3. Verhalten:

- Wenn `knowledge-engine.enabled` false → **no-op**, keine Dateien angefasst (Zero-Overhead-Garantie).
- Wenn `true` und Bundle-Verzeichnis (`bundle-path`, Default `knowledge/`) noch nicht existiert → Scaffolding anlegen:
  ```
  knowledge/
    schema.md              # generiert aus generate_schema(domain)
    sources/
      assets/.gitkeep
    wiki/
      index.md             # generiert aus generate_initial_index()
      log.md               # generiert aus generate_initial_log()
      concepts/.gitkeep
      entities/.gitkeep
      topics/.gitkeep
      sources/.gitkeep
      queries/.gitkeep
  ```
- Wenn Bundle-Verzeichnis bereits existiert → **nichts überschreiben** (idempotent, respektiert bestehende User-Inhalte). Nur fehlende `.gitkeep`-Marker in leeren Unterordnern ergänzen.
- Domain-Wechsel (z.B. `research` → `personal` nach existierendem Bundle) wird in Phase A **nicht** automatisch migriert — nur `schema.md` würde neu generiert werden müssen, was bestehende Konzepte invalidieren könnte. Stattdessen: Log-Warnung "schema.md nicht automatisch aktualisiert bei Domain-Wechsel — manuell prüfen", kein Auto-Overwrite.

### 5. Template `templates/knowledge-schema.template.md`

Ein einziges generisches Template mit `{{KNOWLEDGE_DOMAIN}}` und `{{KNOWLEDGE_CONCEPT_TYPES}}`-Platzhaltern, gerendert von `generate_schema()`. Kein Bedarf für 5 separate Domain-Templates — die Domain-Unterschiede sind nur die Concept-Type-Liste (siehe `DOMAIN_CONCEPT_TYPES` oben), keine strukturellen Unterschiede im Schema-Format selbst.

## Datenfluss

```
project.yaml (knowledge-engine.enabled: true)
        ↓
sync.py Phase 1 (build_variables) → KNOWLEDGE_ENGINE_ENABLED etc.
        ↓
sync.py Phase 2.5 (sync_knowledge_engine)
        ↓
    existiert knowledge/ bereits?
        nein → Scaffolding anlegen (schema.md, index.md, log.md, Ordnerstruktur)
        ja   → nur fehlende .gitkeep ergänzen, nichts überschreiben
        ↓
knowledge/ Bundle bereit für Phase B (Agenten lesen/schreiben hinein)
```

## Fehlerbehandlung

- `bundle-path` zeigt auf existierende Datei (kein Verzeichnis) → Sync bricht mit klarem Fehler ab, kein Force-Delete.
- Ungültiger `domain`-Wert (nicht in enum) → Schema-Validierung schlägt fehl (Phase 1), Sync stoppt vor Phase 2.5.
- Fehlende Schreibrechte im Zielverzeichnis → Fehler propagieren, kein stiller Fallback.

## Testing

- Unit-Test für `_is_role_enabled("knowledge-x", {"knowledge-engine": {"enabled": True}})` → `True`, und `{}`/`False`-Fälle → `False`.
- Unit-Test für `generate_schema()` pro Domain (5 Fälle) — prüft dass `DOMAIN_CONCEPT_TYPES` korrekt eingesetzt wird.
- Integrationstest: `sync.py --dry-run` mit `knowledge-engine.enabled: true` auf leerem Testprojekt → erwartete Dateiliste ohne tatsächliches Schreiben.
- Integrationstest: zweiter Sync-Lauf auf bereits existierendem Bundle → keine Änderung an `schema.md`/`index.md`/`log.md` (Idempotenz).
- Regressionstest: `knowledge-engine.enabled: false` (oder Block fehlt ganz) → generierte CLAUDE.md/AGENTS.md unverändert gegenüber Stand vor dieser Änderung (Zero-Overhead-Garantie).

## Out of Scope (Phase A)

- Alle 7 `knowledge-*` Agenten-Templates (→ Phase B)
- AdminUI-Integration (→ Phase C)
- `config/knowledge-presets.yaml`, DoD-Presets/Export/MCP-Registry-Erweiterungen (→ Phase D, nur falls später gebraucht)
- Ingest/Query/Lint-Operationen — es gibt in Phase A noch keine Agenten, die das Bundle befüllen; Phase A liefert nur die leere, korrekt strukturierte Grundlage
