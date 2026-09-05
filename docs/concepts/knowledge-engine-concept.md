# Knowledge Engine für agent-meta — Konzept v4 (Final Deep-Dive)

> **Feature:** `knowledge-engine` — Per Schalter aktivierbares System das Karpathys LLM-Wiki-Pattern und Googles Open Knowledge Format (OKF v0.1) zu 100% implementiert. Liefert 7 spezialisierte Agenten inkl. Migrations-Agent aus und integriert sich vollständig in alle bestehenden Framework-Mechanismen. **Steuerbar über die AdminUI** mit Best-Practice-Voreinstellungen pro Domäne.
>
> **Quellen:**
> - Karpathy LLM-Wiki: https://gist.github.com/karpathy/442a6bf555914893e9891c11519de94f
> - Google OKF v0.1: https://github.com/GoogleCloudPlatform/knowledge-catalog/blob/main/okf/SPEC.md
> - Google Cloud Blog: https://cloud.google.com/blog/products/data-analytics/how-the-open-knowledge-format-can-improve-data-sharing/
>
> **Erstellt:** 2026-07-22 | **Aktualisiert:** 2026-07-24
> **Status:** Implementiert (Phase A-C abgeschlossen, main gemerged). Zwei bewusste Abweichungen vom Konzept:
> - §8 Templates `knowledge-index.template.md`/`knowledge-log.template.md` existieren nicht als Dateien — Inhalt wird stattdessen in `scripts/lib/knowledge.py` (`generate_initial_index()`/`generate_initial_log()`) generiert.
> - §20.6 `config/knowledge-presets.yaml` existiert nicht — Presets liegen inline in `docs/ui/admin-ui.html` als `const PRESETS = {...}`.

---

## Inhaltsverzeichnis

1. [Executive Summary](#1-executive-summary)
2. [Quellenanalyse: Karpathy LLM-Wiki](#2-quellenanalyse-karpathy-llm-wiki)
3. [Quellenanalyse: Google OKF v0.1](#3-quellenanalyse-google-okf-v01)
4. [Fusion: Wie beide Specs zusammenpassen](#4-fusion-wie-beide-specs-zusammenpassen)
5. [Der Schalter: project.yaml Konfiguration](#5-der-schalter-projectyaml-konfiguration)
6. [Aktivierungsmechanismus im Detail](#6-aktivierungsmechanismus-im-detail)
7. [Bundle-Struktur (generiert von sync.py)](#7-bundle-struktur-generiert-von-syncpy)
8. [schema.md — Das Steuerungsdokument](#8-schemamd--das-steuerungsdokument)
9. [Die 7 Agenten — Vollständige Spezifikation](#9-die-7-agenten--vollständige-spezifikation)
10. [Provider-MD Inhalte (CLAUDE.md / AGENTS.md)](#10-provider-md-inhalte-claudemd--agentsmd)
11. [Orchestrator-Template Erweiterung](#11-orchestrator-template-erweiterung)
12. [CODEBASE_OVERVIEW Integration](#12-codebase_overview-integration)
13. [SE-Kaskaden Kompatibilität](#13-se-kaskaden-kompatibilität)
14. [Framework-Kompatibilitätsmatrix (22 Punkte)](#14-framework-kompatibilitätsmatrix-22-punkte)
15. [Sync-Pipeline Integration](#15-sync-pipeline-integration)
16. [Neue Dateien und Modifikationen](#16-neue-dateien-und-modifikationen)
17. [OKF Compliance Matrix](#17-okf-compliance-matrix)
18. [Karpathy Compliance Matrix](#18-karpathy-compliance-matrix)
19. [AdminUI Integration](#19-adminui-integration)
20. [Best-Practice Presets pro Domäne](#20-best-practice-presets-pro-domäne)
21. [Karpathy Compliance Verification (Gegen-Check)](#21-karpathy-compliance-verification-gegen-check)
22. [OKF Compliance Verification (Gegen-Check)](#22-okf-compliance-verification-gegen-check)
23. [Google Referenz-Tooling & Ökosystem](#23-google-referenz-tooling--ökosystem)

---

## 1. Executive Summary

Die Knowledge Engine erweitert agent-meta um ein **optionales, per Schalter aktivierbares Wissensmanagement-System**, das zwei komplementäre Spezifikationen fusioniert:

- **Karpathy LLM-Wiki** definiert den **Workflow**: Wie ein LLM ein persistent compounding Wiki aufbaut, pflegt und nutzt (Ingest → Query → Lint)
- **Google OKF** definiert das **Format**: Wie Knowledge-Dokumente strukturiert werden (YAML-Frontmatter, Bundle-Verzeichnisbaum, index.md, log.md)

Die Engine liefert **7 spezialisierte Agenten** aus, die kleinteilige Arbeiten von der Erstmigration bis zur täglichen Pflege übernehmen. Alle Agenten werden **nur generiert wenn der Schalter aktiv ist** (Zero-Overhead-Garantie, analog SE-Kaskade). Die Engine integriert sich in **alle 22 bestehenden Framework-Mechanismen** (DoD, Quality Pipelines, Reflection Pairs, Hooks, MCP, Viz, Export, Orchestrator-Routing, u.v.m.) und reagiert auf die **Gegebenheiten des Zielrepos** (Sprache, Tech-Stack, vorhandene Docs).

---

## 2. Quellenanalyse: Karpathy LLM-Wiki

### 2.1 Kernidee

Statt RAG (wiederholt ad-hoc aus Rohdaten abrufen) baut das LLM ein **persistentes, wachsendes Wiki** — eine strukturierte, verlinkte Sammlung von Markdown-Dateien zwischen User und Roh-Quellen. Wissen wird **einmal kompiliert und aktuell gehalten**, nicht bei jeder Frage neu abgeleitet.

### 2.2 Drei-Schichten-Architektur

| Schicht | Beschreibung | Owner | Mutability |
|---------|-------------|-------|------------|
| **Raw Sources** | Kuratierte Quelldokumente (Artikel, Papers, Bilder, Daten) | User | Immutable — LLM liest, modifiziert nie |
| **Wiki** | LLM-generierte Markdown-Dateien (Summaries, Entity-Seiten, Topic-Synthesen, Vergleiche) | LLM | LLM-owned — LLM schreibt, User liest |
| **Schema** | Steuerungsdokument (z.B. CLAUDE.md für Claude Code) — Wiki-Struktur, Konventionen, Workflows | User + LLM | Co-evolved — gemeinsam angepasst |

### 2.3 Drei Operationen

**Ingest** — Source → Wiki:
1. Neue Source in Raw Collection ablegen
2. LLM liest Source, diskutiert Key Takeaways mit User
3. LLM schreibt Source Summary, aktualisiert Entity-/Concept-/Topic-Seiten
4. LLM aktualisiert Index, schreibt Log-Eintrag
5. Touch-Radius: typisch 10-15 Wiki-Seiten pro Source

**Query** — Frage → Wiki → Antwort:
1. LLM liest `index.md` zuerst (Content-Katalog)
2. LLM drills into relevante Seiten
3. LLM synthetisiert Antwort mit Citations
4. **File-Back:** Gute Antworten werden als neue Wiki-Seiten abgelegt (Wissen kompoundiert)

**Lint** — Wiki-Gesundheitscheck:
1. Widersprüche zwischen Seiten finden
2. Veraltete Claims identifizieren (neuere Sources widersprechen)
3. Orphan-Seiten (keine Inbound-Links) finden
4. Fehlende Concepts (erwähnt aber nicht existent) identifizieren
5. Datenlücken vorschlagen (Web-Suche könnte füllen)

### 2.4 Spezial-Dateien

**index.md** — Content-orientierter Katalog:
- Jede Wiki-Seite gelistet mit Link, 1-Zeilen-Summary, Metadaten
- Organisiert nach Kategorie
- LLM liest Index zuerst bei Queries → funktioniert als leichtgewichtige Suche

**log.md** — Chronologisches Event-Log:
- Append-only
- Format: `## [YYYY-MM-DD] <operation> | <title>`
- Parseable: `grep "^## \[" log.md | tail -5`

### 2.5 Domänen-Anwendungen (Karpathy)

- **Personal:** Ziele, Gesundheit, Psychologie, Selbstverbesserung
- **Research:** Papers, Artikel, Reports über Wochen/Monate
- **Book:** Kapitel, Figuren, Themen, Handlungsstränge
- **Business:** Slack, Meeting-Transkripte, Kundengespräche, Projektdokumente
- **Competitive Analysis, Due Diligence, Trip-Planung, Kurs-Notizen**

---

## 3. Quellenanalyse: Google OKF v0.1

### 3.1 Kernkonzepte

| Begriff | Definition |
|---------|-----------|
| **Knowledge Bundle** | Selbständige, hierarchische Sammlung von Knowledge-Dokumenten. Die Distributionseinheit. |
| **Concept** | Einzelne Wissenseinheit = 1 Markdown-Datei. Beschreibt Assets (Tabelle, API), abstrakte Ideen (Metrik, Prozess), oder alles dazwischen. |
| **Concept ID** | Dateipfad relativ zum Bundle-Root, ohne `.md`. Z.B. `tables/users.md` → ID: `tables/users` |
| **Frontmatter** | YAML-Block am Dateianfang, begrenzt durch `---` |
| **Body** | Alles nach dem Frontmatter — freier Markdown-Inhalt |
| **Link** | Standard-Markdown-Link zwischen Concepts (Cross-Reference) |
| **Citation** | Link von Concept zu externer Quelle die eine Behauptung stützt |

### 3.2 Bundle-Struktur (OKF §3)

```
path/to/bundle/
├── index.md                      # Optional. Directory Listing.
├── log.md                        # Optional. Chronological history.
├── <concept>.md                  # Concept am Bundle-Root.
└── <subdirectory>/               # Unterverzeichnisse gruppieren Concepts.
    ├── index.md
    ├── <concept>.md
    └── <subdirectory>/
        └── …
```

### 3.3 Reservierte Dateinamen (OKF §3.1)

| Dateiname | Zweck |
|-----------|-------|
| `index.md` | Directory Listing (§6) |
| `log.md` | Update History (§7) |

Alle anderen `.md`-Dateien sind Concept-Dokumente.

### 3.4 Frontmatter-Spezifikation (OKF §4.1)

```yaml
---
type: <Type name>                  # REQUIRED
title: <Display name>              # Recommended
description: <One-line summary>    # Recommended
resource: <Canonical URI>          # Optional
tags: [<tag>, <tag>, …]            # Optional
timestamp: <ISO 8601 datetime>     # Optional
# … producer-defined key/value pairs erlaubt
---
```

**REQUIRED:** `type` — Kurzer String der die Art des Concepts identifiziert. Beispiele: `BigQuery Table`, `API Endpoint`, `Metric`, `Playbook`. Types sind NICHT zentral registriert — Produzenten wählen beschreibende Werte, Konsumenten MÜSSEN unbekannte Types graceful behandeln.

### 3.5 Links & Citations (OKF §5)

- **Links:** Standard-Markdown-Links `[Text](../concepts/related.md)` für Cross-References
- **Citations:** Links zu externen Quellen die Behauptungen im Body stützen

### 3.6 Distribution (OKF §3)

- Git Repository (empfohlen — History, Attribution, Diffs)
- Tarball/ZIP-Archiv
- Unterverzeichnis in größerem Repository

---

## 4. Fusion: Wie beide Specs zusammenpassen

```
┌──────────────────────────────────────────────────────────────┐
│                    KNOWLEDGE ENGINE                          │
│                                                              │
│  ┌─────────────┐   Karpathy definiert    ┌──────────────┐   │
│  │  KARPATHY   │───── Workflow ──────────▶│  OPERATIONEN │   │
│  │  LLM-Wiki   │   (WAS wird getan)      │  Ingest      │   │
│  │             │                         │  Query       │   │
│  │             │                         │  Lint        │   │
│  └─────────────┘                         └──────────────┘   │
│                                                              │
│  ┌─────────────┐   OKF definiert         ┌──────────────┐   │
│  │  GOOGLE     │───── Format ────────────▶│  STRUKTUR    │   │
│  │  OKF v0.1   │   (WIE es aussieht)     │  Frontmatter │   │
│  │             │                         │  Bundle      │   │
│  │             │                         │  index/log   │   │
│  └─────────────┘                         └──────────────┘   │
│                                                              │
│  Mapping:                                                    │
│  Karpathy "Raw Sources" = knowledge/sources/ (immutable)     │
│  Karpathy "Wiki"        = knowledge/wiki/ (OKF Bundle)       │
│  Karpathy "Schema"      = knowledge/schema.md                │
│  Karpathy "index.md"    = OKF §6 index.md                   │
│  Karpathy "log.md"      = OKF §7 log.md                     │
│  Karpathy "Page"        = OKF "Concept" (1 .md Datei)       │
│  Karpathy "Cross-Ref"   = OKF "Link" (Standard-MD-Link)     │
│  Karpathy "Citation"    = OKF "Citation"                     │
└──────────────────────────────────────────────────────────────┘
```

**Kein Konflikt:** Karpathy definiert keine Dateiformat-Regeln, OKF definiert keine Workflow-Regeln. Sie sind **vollständig komplementär**.

---

## 5. Der Schalter: project.yaml Konfiguration

### 5.1 Minimale Aktivierung

```yaml
knowledge-engine:
  enabled: true
```

Das genügt. Alle anderen Werte haben vernünftige Defaults.

### 5.2 Vollständige Konfiguration (alle Optionen)

```yaml
knowledge-engine:
  enabled: true                     # Master-Schalter
  domain: "research"                # research | personal | business | book | internal-docs | custom
  bundle-path: "knowledge"          # Pfad relativ zu project-root
  sources-dir: "sources"            # Unterverzeichnis für Raw Sources
  wiki-dir: "wiki"                  # Unterverzeichnis für OKF Bundle
  schema-language: "auto"           # auto = aus COMMUNICATION_LANGUAGE, oder explizit
  
  okf:                              # OKF-Spec Compliance Optionen
    enforce-frontmatter: true       # Jedes Concept-Doc MUSS type-Feld haben
    allowed-types: []               # Leer = frei wählbar (OKF §4.1)
    auto-index: true                # index.md automatisch nach Ingest aktualisieren
    auto-log: true                  # log.md automatisch nach jeder Operation
    
  operations:                       # Karpathy-Workflow Optionen
    ingest:
      auto-cross-reference: true    # Automatisch Cross-Links pflegen
      auto-index-update: true       # index.md bei jedem Ingest
      batch-mode: false             # true = mehrere Sources, weniger Supervision
    query:
      file-back-results: true       # Gute Antworten als Wiki-Seiten ablegen
    lint:
      schedule: "on-demand"         # on-demand | post-ingest | periodic
      checks:                       # Aktivierte Lint-Checks
        - contradictions            # Widersprüche zwischen Seiten
        - stale-claims              # Veraltete Claims
        - orphan-pages              # Seiten ohne Inbound-Links
        - missing-concepts          # Erwähnt aber nicht existent
        - broken-links              # Kaputte Cross-References
        - data-gaps                 # Lücken die Websearch füllen könnte
        - missing-frontmatter       # OKF §4.1 type-Feld fehlt
        - index-staleness           # OKF §6 index.md nicht aktuell
  
  migration:                        # Migrations-Agent Optionen
    auto-detect-sources: true       # Vorhandene docs/ scannen
    clean-duplicates: true          # Duplikate erkennen und konsolidieren
    preserve-originals: true        # Originale nicht löschen, nur kopieren
  
  search:                           # Such-Integration
    engine: "index-only"            # index-only | mcp-qmd | custom
    mcp-server: ""                  # Falls custom: Server-Name aus mcp-registry
```

### 5.3 JSON Schema Eintrag (`config/project-config.schema.json`)

```json
"knowledge-engine": {
  "type": "object",
  "description": "Knowledge Engine: Aktiviert LLM-Wiki (Karpathy) + OKF (Google) Bundle-Verwaltung. Generiert spezialisierte Knowledge-Agenten und eine OKF-konforme Bundle-Struktur im Zielprojekt.",
  "properties": {
    "enabled": {
      "type": "boolean",
      "description": "Master-Schalter. Wenn false (default), werden keine Knowledge-Agenten generiert und kein Bundle angelegt.",
      "default": false
    },
    "domain": {
      "type": "string",
      "enum": ["research", "personal", "business", "book", "internal-docs", "custom"],
      "description": "Domäne bestimmt vorgeschlagene OKF Concept Types und Schema-Defaults.",
      "default": "research"
    },
    "bundle-path": {
      "type": "string",
      "description": "Wurzelpfad für Knowledge Bundle relativ zum Projekt-Root.",
      "default": "knowledge"
    },
    "sources-dir": {
      "type": "string",
      "description": "Unterverzeichnis für immutable Raw Sources.",
      "default": "sources"
    },
    "wiki-dir": {
      "type": "string",
      "description": "Unterverzeichnis für den OKF Knowledge Bundle (Wiki).",
      "default": "wiki"
    },
    "schema-language": {
      "type": "string",
      "description": "Sprache für schema.md. 'auto' erbt aus COMMUNICATION_LANGUAGE.",
      "default": "auto"
    },
    "okf": {
      "type": "object",
      "properties": {
        "enforce-frontmatter": { "type": "boolean", "default": true },
        "allowed-types": { "type": "array", "items": { "type": "string" }, "default": [] },
        "auto-index": { "type": "boolean", "default": true },
        "auto-log": { "type": "boolean", "default": true }
      }
    },
    "operations": {
      "type": "object",
      "properties": {
        "ingest": {
          "type": "object",
          "properties": {
            "auto-cross-reference": { "type": "boolean", "default": true },
            "auto-index-update": { "type": "boolean", "default": true },
            "batch-mode": { "type": "boolean", "default": false }
          }
        },
        "query": {
          "type": "object",
          "properties": {
            "file-back-results": { "type": "boolean", "default": true }
          }
        },
        "lint": {
          "type": "object",
          "properties": {
            "schedule": { "type": "string", "enum": ["on-demand", "post-ingest", "periodic"], "default": "on-demand" },
            "checks": { "type": "array", "items": { "type": "string" } }
          }
        }
      }
    },
    "migration": {
      "type": "object",
      "properties": {
        "auto-detect-sources": { "type": "boolean", "default": true },
        "clean-duplicates": { "type": "boolean", "default": true },
        "preserve-originals": { "type": "boolean", "default": true }
      }
    },
    "search": {
      "type": "object",
      "properties": {
        "engine": { "type": "string", "enum": ["index-only", "mcp-qmd", "custom"], "default": "index-only" },
        "mcp-server": { "type": "string", "default": "" }
      }
    }
  },
  "required": ["enabled"]
}
```

---

## 6. Aktivierungsmechanismus im Detail

Die Knowledge Engine folgt **exakt dasselbe Activation-Pattern** wie die SE-Kaskade (`systems-engineering.enabled`). Dies garantiert Konsistenz mit dem bestehenden Framework.

### 6.1 `_is_role_enabled()` in `scripts/lib/agents.py`

Aktuelle Funktion (Zeile 375):
```python
def _is_role_enabled(role: str, config: dict) -> bool:
    """Check if a role is enabled based on project config."""
    if role.startswith("se-"):
        se_config = config.get("systems-engineering") or {}
        return se_config.get("enabled", True)
    return True
```

Erweiterung:
```python
def _is_role_enabled(role: str, config: dict) -> bool:
    """Check if a role is enabled based on project config."""
    if role.startswith("se-"):
        se_config = config.get("systems-engineering") or {}
        return se_config.get("enabled", True)
    # NEU: Knowledge-Engine-Rollen
    if role.startswith("knowledge-"):
        ke_config = config.get("knowledge-engine") or {}
        return ke_config.get("enabled", False)  # Default: OFF (opt-in)
    return True
```

**Unterschied zu SE:** Default ist `False` (opt-in), nicht `True`. Kein Projekt bekommt Knowledge-Agenten ohne explizite Aktivierung.

**Wirkung:** `build_agent_hints()` (Zeile 1859) und `build_agent_table()` (Zeile 1922) rufen `_is_role_enabled()` auf (Zeilen 1909, 1941). Wenn `knowledge-engine.enabled: false`, werden alle `knowledge-*` Rollen automatisch aus Agent-Tabellen, Hints und generierten Dateien gefiltert.

### 6.2 `build_variables()` in `scripts/lib/config.py`

Einfügung nach dem SE-Block (nach Zeile 476):

```python
# ---- Knowledge Engine Variables ----
ke_config = config.get("knowledge-engine") or {}
ke_enabled = ke_config.get("enabled", False)
variables["KNOWLEDGE_ENGINE_ENABLED"] = "true" if ke_enabled else "false"

if ke_enabled:
    _bundle_path = ke_config.get("bundle-path", "knowledge")
    _wiki_dir = ke_config.get("wiki-dir", "wiki")
    _sources_dir = ke_config.get("sources-dir", "sources")
    _domain = ke_config.get("domain", "research")
    
    variables["KNOWLEDGE_BUNDLE_PATH"] = _bundle_path
    variables["KNOWLEDGE_WIKI_DIR"] = f"{_bundle_path}/{_wiki_dir}"
    variables["KNOWLEDGE_SOURCES_DIR"] = f"{_bundle_path}/{_sources_dir}"
    variables["KNOWLEDGE_SCHEMA_PATH"] = f"{_bundle_path}/schema.md"
    variables["KNOWLEDGE_DOMAIN"] = _domain
    
    # Domain-spezifische Beschreibung für Schema-Template
    _domain_descriptions = {
        "research": "Forschungs-Wiki: Papers, Studien, Methoden, Findings, Hypothesen, Vergleiche",
        "personal": "Persönliches Wiki: Ziele, Gesundheit, Gewohnheiten, Reflexionen, Erkenntnisse",
        "business": "Business-Wiki: Meetings, Entscheidungen, Metriken, Strategien, Wettbewerb",
        "book": "Buch-Wiki: Kapitel, Figuren, Themen, Handlungsstränge, Settings, Zitate",
        "internal-docs": "Projekt-Doku-Wiki: Architektur, Guides, API-Referenzen, Session-Zusammenfassungen",
        "custom": "Freies Wiki: Konzepte, Entitäten, Themen, Source-Summaries, Query-Ergebnisse",
    }
    variables["KNOWLEDGE_DOMAIN_DESCRIPTION"] = _domain_descriptions.get(_domain, _domain_descriptions["custom"])
    
    # Domain-spezifische OKF Concept Types
    _domain_types = {
        "research": "Paper, Dataset, Method, Finding, Hypothesis, Comparison, Literature Review, Author, Institution",
        "personal": "Goal, Journal Entry, Health Record, Insight, Resource, Habit, Reflection, Book Note",
        "business": "Meeting, Decision, Process, Metric, Customer Insight, Competitor, Strategy, OKR",
        "book": "Chapter, Character, Theme, Plot Thread, Setting, Quote, Timeline Event, Relationship",
        "internal-docs": "Concept, Architecture, API Reference, Guide, Session Conclusion",
        "custom": "Concept, Entity, Topic, Source Summary, Query Result",
    }
    variables["KNOWLEDGE_CONCEPT_TYPES"] = _domain_types.get(_domain, _domain_types["custom"])
```

### 6.3 `strip_inactive_conditional_blocks()`

Die Variable `KNOWLEDGE_ENGINE_ENABLED` wird automatisch über die bestehende Mechanik registriert — `build_variables()` setzt sie als `"true"` oder `"false"`, und der Conditional Stripper evaluiert `{{#if KNOWLEDGE_ENGINE_ENABLED}}...{{/if}}` Blöcke in Agent-Templates entsprechend.

### 6.4 Zero-Overhead-Garantie

Wenn `knowledge-engine.enabled: false` (Default):

| Aspekt | Verhalten |
|--------|-----------|
| `knowledge-*` Agent-Dateien | NICHT generiert (gefiltert durch `_is_role_enabled()`) |
| Knowledge-Engine Block in CLAUDE.md/AGENTS.md | NICHT vorhanden (gefiltert durch `build_agent_hints()`) |
| Knowledge-Variablen in Templates | Gestrippt (`{{#if KNOWLEDGE_ENGINE_ENABLED}}` Blöcke entfernt) |
| `knowledge/` Verzeichnis | NICHT angelegt |
| Token-Last in generierten Agenten | Null Overhead |
| Bootstraps (Gemini `define_subagent`) | Keine Knowledge-Agenten registriert |

---

## 7. Bundle-Struktur (generiert von sync.py)

Wenn `knowledge-engine.enabled: true`, legt `sync_knowledge_engine()` diese Struktur an:

```
<project-root>/
└── knowledge/                          # bundle-path (konfigurierbar)
    ├── schema.md                       # Karpathy Layer 3 — Steuerungsdokument
    ├── sources/                        # Karpathy Layer 1 — Immutable Raw Sources
    │   ├── .gitkeep
    │   └── assets/                     # Bilder, PDFs, Nicht-Markdown-Dateien
    │       └── .gitkeep
    └── wiki/                           # Karpathy Layer 2 + OKF Knowledge Bundle
        ├── index.md                    # OKF §3.1, §6 — Content-Katalog
        ├── log.md                      # OKF §3.1, §7 — Chronologisches Event-Log
        ├── concepts/                   # OKF Concept Documents
        │   └── .gitkeep
        ├── entities/                   # Named Entity Pages (Personen, Systeme, APIs)
        │   └── .gitkeep
        ├── topics/                     # Thematische Synthesen und Überblicke
        │   └── .gitkeep
        ├── sources/                    # Source Summary Pages (1:1 zu raw sources)
        │   └── .gitkeep
        └── queries/                    # Archivierte Query-Ergebnisse (File-Back)
            └── .gitkeep
```

**Warum `wiki/` als OKF-Bundle-Root und nicht direkt `knowledge/`?**
- `knowledge/sources/` enthält immutable Raw Sources — die gehören NICHT in den OKF-Bundle
- `knowledge/schema.md` ist ein Steuerungsdokument — kein OKF-Concept
- Der OKF-Bundle (`wiki/`) enthält NUR Concept-Dokumente + `index.md` + `log.md`
- Saubere Trennung: Karpathy Layer 1 (sources) ≠ Karpathy Layer 2 (wiki = OKF Bundle)

---

## 8. schema.md — Das Steuerungsdokument

### 8.1 Zweck

Die `schema.md` ist Karpathys Layer 3 — das Steuerungsdokument das dem LLM sagt, wie das Wiki strukturiert ist, welche Konventionen gelten, und welche Workflows zu befolgen sind. Es wird von `sync.py` initial generiert und kann dann vom User und den Knowledge-Agenten gemeinsam weiterentwickelt werden.

### 8.2 Template (`templates/knowledge-schema.template.md`)

```markdown
---
type: Schema
title: "{{PROJECT_NAME}} Knowledge Engine Schema"
description: "Steuerungsdokument für die Knowledge Engine — definiert Konventionen, Concept Types und Workflows."
timestamp: {{AGENT_META_DATE}}
---

# Knowledge Engine Schema — {{PROJECT_NAME}}

> Dieses Dokument steuert die Knowledge Engine. Alle Knowledge-Agenten
> lesen es als erstes. User und knowledge-curator evolven es gemeinsam.

## Domäne

{{KNOWLEDGE_DOMAIN_DESCRIPTION}}

## Verzeichnisstruktur

| Pfad | Zweck | Owner |
|------|-------|-------|
| `sources/` | Immutable Raw Sources — NIEMALS modifizieren | User |
| `sources/assets/` | Bilder, PDFs und andere Nicht-Markdown-Dateien | User |
| `wiki/` | OKF-konformer Knowledge Bundle — LLM-owned | Knowledge-Agenten |
| `wiki/concepts/` | Einzelne Wissenseinheiten (OKF Concepts) | knowledge-ingestor |
| `wiki/entities/` | Named Entities (Personen, Systeme, APIs, Orte) | knowledge-ingestor |
| `wiki/topics/` | Thematische Synthesen und Überblicke | knowledge-ingestor |
| `wiki/sources/` | Source Summaries (1:1 zu Raw Sources) | knowledge-ingestor |
| `wiki/queries/` | Archivierte Abfrageergebnisse (File-Back) | knowledge-querier |
| `wiki/index.md` | Content-Katalog aller Wiki-Seiten (OKF §6) | knowledge-indexer |
| `wiki/log.md` | Chronologisches Event-Log (OKF §7) | knowledge-indexer |

## OKF-Konventionen

1. **Frontmatter-Pflicht:** Jede `.md`-Datei in `wiki/` (außer `index.md`, `log.md`) MUSS OKF-konformes YAML-Frontmatter haben:
   ```yaml
   ---
   type: <Type>              # REQUIRED (OKF §4.1)
   title: <Display Name>     # RECOMMENDED
   description: <1-Zeiler>   # RECOMMENDED
   tags: [tag1, tag2]        # OPTIONAL
   timestamp: <ISO 8601>     # OPTIONAL → wird bei Änderung gesetzt
   resource: <URI>           # OPTIONAL → falls Asset-Referenz
   ---
   ```

2. **Concept-ID:** Dateipfad relativ zu `wiki/`, ohne `.md`. Z.B. `concepts/attention.md` → ID: `concepts/attention`

3. **Cross-References:** Standard-Markdown-Links: `[Entity Name](../entities/entity-name.md)`

4. **Citations:** Links zu externen Quellen mit Kontextangabe: `[Quelle](../../sources/paper.pdf) — §3, S.42`

5. **Sprache:** {{COMMUNICATION_LANGUAGE}}

## OKF Concept Types (für dieses Projekt)

Empfohlene Types für die Domäne **{{KNOWLEDGE_DOMAIN}}**:
{{KNOWLEDGE_CONCEPT_TYPES}}

Weitere Types können jederzeit hinzugefügt werden (OKF §4.1: Types sind nicht zentral registriert).

## Workflows

### Ingest (Source verarbeiten)
1. Source in `sources/` ablegen
2. `knowledge-ingestor` liest Source, diskutiert Key Takeaways mit User
3. Source Summary in `wiki/sources/<name>.md` erstellen (OKF-Frontmatter!)
4. Relevante Entity-/Concept-/Topic-Seiten aktualisieren oder neu anlegen
5. Cross-References zwischen allen betroffenen Seiten pflegen
6. `knowledge-indexer` aktualisiert `wiki/index.md` und `wiki/log.md`
7. Touch-Radius: typisch 10-15 Dateien pro Ingest

### Query (Frage beantworten)
1. `knowledge-querier` liest `wiki/index.md` zuerst
2. Drills into relevante Concept-Dokumente
3. Synthetisiert Antwort mit Citations (Quellverweise auf Wiki-Seiten)
4. Bei guten Antworten: File-Back nach `wiki/queries/<name>.md`

### Lint (Wiki-Gesundheitscheck)
1. `knowledge-linter` prüft alle Wiki-Seiten gegen 10 Check-Kategorien
2. Findings als strukturierter Report
3. Auto-fixable Findings → Delegation an `knowledge-gardener`
4. Inhaltliche Findings → Report an User

### Migration (Erstaktivierung)
1. `knowledge-migrator` scannt vorhandene Docs
2. Erstellt Migration-Plan → User-Freigabe
3. Kopiert (nicht verschiebt!) migrierbare Dokumente
4. Konvertiert zu OKF-konformen Wiki-Seiten
5. Generiert initiales `index.md` und `log.md`
```

---

## 9. Die 7 Agenten — Vollständige Spezifikation

### 9.1 Übersicht

| # | Agent | Model-Tier | Memory | Tools | Karpathy-Op | OKF-Aspekt |
|---|-------|------------|--------|-------|-------------|------------|
| 1 | `knowledge-curator` | balanced | project | Read, Write, Agent, TodoWrite | Schema | Bundle mgmt |
| 2 | `knowledge-ingestor` | balanced | project | Read, Write, Edit, Glob, Grep | Ingest | Concept creation |
| 3 | `knowledge-querier` | fast | — | Read, Write, Glob, Grep | Query | Concept traversal |
| 4 | `knowledge-linter` | fast | — | Read, Glob, Grep, TodoWrite | Lint | Frontmatter valid. |
| 5 | `knowledge-indexer` | nano | — | Read, Write, Edit | Index/Log | index.md, log.md |
| 6 | `knowledge-gardener` | nano | — | Read, Write, Edit, Glob | Maintenance | Tags, links |
| 7 | `knowledge-migrator` | balanced | — | Read, Write, Edit, Glob, Grep, Bash | Migration | — |

### 9.2 `knowledge-curator` — Der Dirigent

**Datei:** `agents/1-generic/knowledge-curator.md`

**Template-Frontmatter:**
```yaml
---
name: template-knowledge-curator
version: "1.0.0"
description: "Strategische Knowledge-Engine-Steuerung: Schema-Evolution, Wiki-Strukturierung, Domänen-Anpassung, Ingest-Planung, OKF-Compliance-Sicherung."
hint: "Wiki-Strategie, Schema-Evolution, OKF-Compliance"
tools:
  - Read
  - Write
  - Agent
  - TodoWrite
---
```

**Verhalten im Detail:**

1. **Schema lesen:** Liest `{{KNOWLEDGE_SCHEMA_PATH}}` als ALLERERSTE Aktion — versteht Domäne, Konventionen, aktuelle Concept Types
2. **Ingest planen:** Bei neuen Sources entscheidet der Curator: Einzeln oder Batch? Welche Concept Types sind relevant? Welche bestehenden Seiten müssen aktualisiert werden?
3. **Delegieren:**
   - An `knowledge-ingestor`: Source(s) verarbeiten
   - An `knowledge-linter`: Nach Ingest Konsistenz prüfen
   - An `knowledge-gardener`: Kleinteilige Fixes
   - An `knowledge-indexer`: Wird vom Ingestor direkt delegiert, NICHT vom Curator
4. **Schema evolven:** Gemeinsam mit User anpassen — neue Concept Types hinzufügen, Konventionen verfeinern, Workflows optimieren
5. **OKF-Compliance:** Sicherstellen dass alle neuen Concepts gültige `type`-Felder haben
6. **Zielrepo-Adaption:** Liest `{{PROJECT_CONTEXT}}`, `{{PROJECT_LANGUAGES}}`, `{{PLATFORM}}` — passt Schema-Empfehlungen an den Tech-Stack und die Sprache des Zielprojekts an

**Bedingte Template-Blöcke:**
```markdown
{{#if KNOWLEDGE_ENGINE_ENABLED}}
## Knowledge Engine Kontext
**Domäne:** {{KNOWLEDGE_DOMAIN}}
**Bundle:** `{{KNOWLEDGE_BUNDLE_PATH}}/`
**Schema:** `{{KNOWLEDGE_SCHEMA_PATH}}`
**Wiki:** `{{KNOWLEDGE_WIKI_DIR}}/`
**Sources:** `{{KNOWLEDGE_SOURCES_DIR}}/`

Lies das Schema (`{{KNOWLEDGE_SCHEMA_PATH}}`) ZUERST, bevor du Operationen planst.
{{/if}}
```

**Handoff-Contracts:**
```yaml
# role-defaults.yaml Eintrag
knowledge-curator:
  model: balanced
  memory: project
  workflow_tier: optional
  conditional: knowledge-engine
  description: >-
    Strategische Knowledge-Engine-Steuerung: Schema-Evolution,
    Wiki-Strukturierung, Domänen-Anpassung, Ingest-Planung, OKF-Compliance.
  routing:
    intent_keywords:
      - Knowledge
      - Wiki
      - Wissen
      - Schema
      - Knowledge-Engine
    parallel: false
    orchestrator_only: false
  handoff:
    input_contracts:
      - task-spec-v1
    output_contract: knowledge-spec-v1
```

### 9.3 `knowledge-ingestor` — Der Schreiber

**Datei:** `agents/1-generic/knowledge-ingestor.md`

**Verhalten im Detail — Karpathy "Ingest" Operation:**

**Phase 1: Source lesen**
1. Öffnet die genannte Datei aus `{{KNOWLEDGE_SOURCES_DIR}}/`
2. Identifiziert Source-Typ (Paper, Artikel, Transkript, Code-Doku, etc.)
3. Extrahiert Struktur: Überschriften, Abschnitte, Schlüsselkonzepte

**Phase 2: Diskussion (außer Batch-Mode)**
4. Fasst Key Takeaways zusammen und bespricht sie mit dem User
5. User gibt Richtung vor: Was betonen? Was ignorieren?

**Phase 3: Wiki-Seiten erstellen/aktualisieren**
6. **Source Summary:** `{{KNOWLEDGE_WIKI_DIR}}/sources/<source-name>.md`
   - OKF-Frontmatter: `type: Source Summary`, `title`, `description`, `tags`, `timestamp`
   - Strukturierte Zusammenfassung der Source
   - Quellverweis: `resource: ../../sources/<original-filename>`
7. **Entity Pages:** Identifiziert Named Entities → für jede neue Entity:
   - Prüft ob `{{KNOWLEDGE_WIKI_DIR}}/entities/<entity>.md` existiert
   - Wenn ja: Aktualisiert mit neuen Informationen
   - Wenn nein: Legt neue Entity-Seite an mit `type: Entity`
8. **Concept Pages:** Extrahiert abstrakte Konzepte → analog zu Entities in `concepts/`
9. **Topic Syntheses:** Aktualisiert übergreifende Themen-Seiten in `topics/`
   - Integriert neue Erkenntnisse in bestehende Synthese
   - Vermerkt wo neue Daten alten widersprechen (Karpathy: "noting contradictions")

**Phase 4: Cross-References und Meta**
10. **Cross-References:** Pflegt Standard-Markdown-Links zwischen allen betroffenen Seiten
11. **Citations:** Verlinkt auf die Source: `[Source Name](../../sources/<file>)`
12. **Delegiert an `knowledge-indexer`:** `index.md` + `log.md` Update

**OKF-Pflichten pro Dokument:**
```yaml
---
type: <Entity|Concept|Topic|Source Summary|...>  # REQUIRED (OKF §4.1)
title: "<Display Name>"                           # RECOMMENDED
description: "<One-line summary>"                  # RECOMMENDED
tags: [tag1, tag2]                                 # OPTIONAL
timestamp: "2026-07-22T10:00:00Z"                  # OPTIONAL → wird GESETZT
resource: "<URI>"                                  # OPTIONAL → bei Assets
sources:                                           # KARPATHY EXTENSION
  - "../sources/source-name.md"                    #   Quell-Verweise
---
```

**Touch-Radius:** 10-15 Dateien pro Ingest (Karpathy-Konvention)

**role-defaults.yaml:**
```yaml
knowledge-ingestor:
  model: balanced
  memory: project
  workflow_tier: optional
  conditional: knowledge-engine
  description: >-
    Sources einlesen, Key Information extrahieren, Wiki-Seiten erstellen/
    aktualisieren, Cross-References pflegen. Touch-Radius: ~10-15 Dateien/Ingest.
  routing:
    intent_keywords:
      - Ingest
      - Source verarbeiten
      - einlesen
    parallel: true
    orchestrator_only: false
  handoff:
    input_contracts:
      - task-spec-v1
      - knowledge-spec-v1
    output_contract: knowledge-ingest-v1
    timeout_sec: 300
```

### 9.4 `knowledge-querier` — Der Forscher

**Datei:** `agents/1-generic/knowledge-querier.md`

**Verhalten — Karpathy "Query" Operation:**

1. **Index-First:** Liest `{{KNOWLEDGE_WIKI_DIR}}/index.md` → identifiziert relevante Seiten
2. **Drill-In:** Öffnet gefundene Concept-Dokumente, folgt Cross-References
3. **Synthese:** Generiert Antwort mit Citations (Seitenverweise + Zeilennummern)
4. **File-Back (wenn `file-back-results: true`):** Gute Antworten als neues Concept in `queries/` ablegen
5. **Delegiert an `knowledge-indexer`:** Bei File-Back index.md + log.md Update

**WICHTIG:** Der Querier **schreibt KEINE bestehenden Wiki-Seiten um** — er liest und synthetisiert nur. Neue Erkenntnisse werden als separate Query-Result-Seiten abgelegt. Bestehende Seiten aktualisiert **NUR** der `knowledge-ingestor`.

**role-defaults.yaml:**
```yaml
knowledge-querier:
  model: fast
  memory: ''
  workflow_tier: optional
  conditional: knowledge-engine
  description: >-
    Fragen gegen das Knowledge Wiki beantworten. Index-First-Strategie,
    Drill-in, Synthese mit Citations. File-Back guter Antworten.
  routing:
    intent_keywords:
      - Wiki-Frage
      - Was wissen wir
      - Knowledge Query
      - Recherche im Wiki
    parallel: true
    orchestrator_only: false
  handoff:
    input_contracts:
      - task-spec-v1
    output_contract: dev-result-v1
    timeout_sec: 120
```

### 9.5 `knowledge-linter` — Der Prüfer

**Datei:** `agents/1-generic/knowledge-linter.md`

**10 Lint-Checks (Karpathy + OKF kombiniert):**

| # | Check | Quelle | Severity | Aktion |
|---|-------|--------|----------|--------|
| 1 | **Widersprüche** zwischen Seiten | Karpathy | HIGH | Report mit betroffenen Seiten + Stellen |
| 2 | **Veraltete Claims** (neuere Source widerspricht älterem Eintrag) | Karpathy | HIGH | Markierung + Update-Vorschlag |
| 3 | **Orphan-Seiten** (keine Inbound-Links, nicht im Index) | Karpathy | MEDIUM | Liste + Adoptions-Vorschlag an Gardener |
| 4 | **Fehlende Concepts** (Name erwähnt, keine eigene Seite) | Karpathy | MEDIUM | Stub-Erstellung vorschlagen |
| 5 | **Kaputte Cross-References** (Link-Ziel existiert nicht) | Karpathy+OKF | HIGH | Auto-Fix durch Gardener |
| 6 | **Datenlücken** (Thema erwähnt aber dünn, Websearch könnte helfen) | Karpathy | LOW | Recherche-Vorschlag |
| 7 | **Fehlendes `type`-Frontmatter** (OKF §4.1 REQUIRED) | OKF | CRITICAL | Sofort beheben |
| 8 | **Fehlende recommended Frontmatter** (`title`, `description`) | OKF | LOW | Gardener-Delegation |
| 9 | **`index.md` veraltet** (Wiki-Seiten existieren die nicht im Index stehen) | OKF §6 | MEDIUM | Indexer-Delegation |
| 10 | **`log.md` Inkonsistenzen** (Einträge ohne korrespondierende Seiten) | OKF §7 | LOW | Indexer-Delegation |

**Output:** Strukturierter Lint-Report, optional als `wiki/queries/lint-report-YYYY-MM-DD.md` abgelegt.

**role-defaults.yaml:**
```yaml
knowledge-linter:
  model: fast
  memory: ''
  workflow_tier: optional
  conditional: knowledge-engine
  description: >-
    Wiki-Gesundheitscheck: Widersprüche, Orphans, veraltete Claims,
    kaputte Links, fehlende OKF-Frontmatter, Index-Staleness.
  routing:
    intent_keywords:
      - Wiki-Lint
      - Wiki-Check
      - Knowledge Lint
      - Wiki-Gesundheit
    parallel: true
    orchestrator_only: false
  handoff:
    input_contracts:
      - task-spec-v1
    output_contract: knowledge-lint-v1
```

### 9.6 `knowledge-indexer` — Der Katalogisierer

**Datei:** `agents/1-generic/knowledge-indexer.md`

**`index.md` Pflege (OKF §6 + Karpathy):**
```markdown
---
type: Index
title: "Knowledge Wiki — Inhaltsverzeichnis"
timestamp: 2026-07-22T10:00:00Z
---

# Index

## Entities (7)
| Seite | Beschreibung | Tags | Aktualisiert |
|-------|-------------|------|-------------|
| [Entity A](entities/entity-a.md) | Kurzbeschreibung | `tag1`, `tag2` | 2026-07-22 |

## Concepts (12)
| Seite | Beschreibung | Tags | Aktualisiert |
|-------|-------------|------|-------------|
| [Attention](concepts/attention.md) | Attention-Mechanismus in Transformern | `ml`, `architecture` | 2026-07-21 |

## Topics (4)
| ... |

## Source Summaries (9)
| ... |

## Queries (3)
| ... |
```

**`log.md` Pflege (OKF §7 + Karpathy):**
```markdown
---
type: Log
title: "Knowledge Wiki — Changelog"
---

# Log

## [2026-07-22] ingest | "Deep Learning Paper XYZ"
- Source Summary: `sources/deep-learning-paper-xyz.md`
- Updated: `entities/transformer.md`, `concepts/attention-mechanism.md`, `topics/ml-architectures.md`
- New: `entities/author-name.md`
- Touch-Count: 12 Dateien

## [2026-07-21] query | "Vergleich Transformer vs. RNN"
- Result: `queries/transformer-vs-rnn-vergleich.md`

## [2026-07-21] lint | Wiki Health Check
- Findings: 2 Orphans, 1 fehlender type, 3 kaputte Links
- Auto-Fixed: 3 Links (by knowledge-gardener)
- Open: 2 Orphans, 1 fehlender type

## [2026-07-20] migration | "Initiale Migration von docs/"
- Migriert: 8 Dateien
- Übersprungen: 2 (CODEBASE_OVERVIEW, REQUIREMENTS)
```

**Format-Regeln:**
- `## [YYYY-MM-DD] <operation> | <title>` — konsistentes Prefix
- Operationen: `ingest`, `query`, `lint`, `garden`, `schema-update`, `migration`
- Parseable: `grep "^## \[" wiki/log.md | tail -5`
- Append-only: NIEMALS bestehende Einträge löschen oder ändern

**role-defaults.yaml:**
```yaml
knowledge-indexer:
  model: nano
  memory: ''
  workflow_tier: optional
  conditional: knowledge-engine
  description: >-
    Pflegt index.md (Content-Katalog, OKF §6) und log.md
    (Chronologisches Event-Log, OKF §7) im Knowledge Wiki.
  routing:
    parallel: true
    orchestrator_only: true     # Wird NUR von anderen Knowledge-Agenten delegiert
  handoff:
    input_contracts:
      - knowledge-ingest-v1
    output_contract: dev-result-v1
```

### 9.7 `knowledge-gardener` — Der Gärtner

**Datei:** `agents/1-generic/knowledge-gardener.md`

**Aufgabenmatrix:**

| Task | Beschreibung | Auslöser | Priorität |
|------|-------------|----------|-----------|
| **Link-Reparatur** | Kaputte interne Links fixen, Pfade korrigieren | Linter-Finding #5 | HIGH |
| **Neue Cross-Refs** | Fehlende Verlinkungen zwischen verwandten Seiten | Linter-Finding oder Curator | MEDIUM |
| **Tag-Harmonisierung** | Duplikat-Tags vereinheitlichen (`ML` → `machine-learning`) | Linter/Curator | LOW |
| **Frontmatter-Hygiene** | Fehlende `title`, `description`, `timestamp` ergänzen | Linter-Finding #8 | LOW |
| **Typo-Korrektur** | Rechtschreibung und Grammatik in Wiki-Seiten | Manueller Auftrag | LOW |
| **Format-Konsistenz** | Heading-Hierarchie, Markdown-Stil vereinheitlichen | Manueller Auftrag | LOW |
| **Timestamp-Updates** | `timestamp`-Feld bei Änderungen aktualisieren | Nach jedem Edit | AUTO |
| **Orphan-Adoption** | Verwaiste Seiten in Themen-Hierarchie eingliedern | Linter-Finding #3 | MEDIUM |
| **Stub-Vervollständigung** | Von Linter vorgeschlagene Stub-Seiten mit Inhalt füllen | Linter-Finding #4 | MEDIUM |

**WICHTIG:** Der Gardener verändert **KEINE inhaltliche Substanz** — er pflegt Form, Struktur und Metadaten. Inhaltliche Änderungen macht ausschließlich der `knowledge-ingestor`.

**role-defaults.yaml:**
```yaml
knowledge-gardener:
  model: nano
  memory: ''
  workflow_tier: optional
  conditional: knowledge-engine
  description: >-
    Kleinteilige Wiki-Pflege: Links reparieren, Tags harmonisieren,
    Frontmatter ergänzen, Typos korrigieren, Timestamps aktualisieren.
  routing:
    intent_keywords:
      - Wiki-Pflege
      - Links reparieren
      - Tags aufräumen
      - Wiki aufräumen
    parallel: true
    orchestrator_only: false
  handoff:
    input_contracts:
      - knowledge-lint-v1
      - task-spec-v1
    output_contract: dev-result-v1
```

### 9.8 `knowledge-migrator` — Der Aufräumer

**Datei:** `agents/1-generic/knowledge-migrator.md`

> Der Migrations-Agent löst das Problem der **Erstaktivierung**: Was passiert mit vorhandenen `docs/`, `README.md`, `ARCHITECTURE.md` und anderen Inhalten im Zielrepo?

**Phase 1: Discovery (Read-Only)**

```
1. Lese {{PROJECT_CONTEXT}} — verstehe Projekt, Sprache, Tech-Stack
2. Scanne vorhandene Verzeichnisse:
   a) docs/                   → Architektur-Docs, Guides, API-Docs, ADRs
   b) README.md               → Projekt-Beschreibung
   c) ARCHITECTURE.md          → Architektur-Überblick
   d) docs/conclusions/        → Session-Erkenntnisse
   e) docs/adr/                → Architecture Decision Records
   f) docs/api/                → API-Dokumentation
   g) CHANGELOG.md             → Versionshistorie
   h) *.md im Root             → Potenzielle Sources
3. Markiere GESCHÜTZTE Dateien (NIEMALS migrieren):
   - docs/CODEBASE_OVERVIEW.md   → gehört dem documenter
   - docs/REQUIREMENTS.md        → gehört dem requirements-Agent
   - CLAUDE.md, AGENTS.md        → Provider-Context-Dateien
   - .claude/*, .gemini/*, .opencode/* → Provider-Verzeichnisse
   - VERSION, LICENSE, .gitignore → Infrastruktur-Dateien
4. Erstelle Discovery-Inventar:
   - Migrierbare Dateien mit geschätztem OKF-Type
   - Geschützte Dateien (mit Begründung)
   - Duplikate (gleicher Inhalt in verschiedenen Dateien)
   - Empfohlene Kategorie-Zuordnung (concepts/ vs entities/ vs topics/)
5. Präsentiere User einen Migration-Plan zur EXPLIZITEN Freigabe
```

**Phase 2: Migration (NUR nach User-Freigabe)**

```
Für jedes freigegebene Dokument:

1. KOPIERE (nicht verschiebe!) Original nach knowledge/sources/<name>
   → Originale bleiben wo sie sind (preserve-originals: true)

2. Erstelle OKF-konforme Wiki-Seite:
   a) Bestimme OKF-Type aus Inhalt:
      - README → type: "Project Overview"
      - ARCHITECTURE.md → type: "Architecture"
      - docs/adr/*.md → type: "ADR" (Architecture Decision Record)
      - docs/guides/*.md → type: "Guide"
      - docs/api/*.md → type: "API Reference"
      - docs/conclusions/*.md → type: "Session Conclusion"
      - Fallback: type: "Document"
   
   b) Setze YAML-Frontmatter:
      ---
      type: <abgeleitet>
      title: <aus H1 oder Dateiname>
      description: <erster Absatz oder Zusammenfassung>
      tags: <aus Inhalt extrahiert>
      timestamp: <File-Modification-Date als ISO 8601>
      resource: <relativer Pfad zum Original>
      migrated_from: <originaler Pfad>
      ---
   
   c) Schreibe Datei nach:
      - Architecture → wiki/concepts/architecture.md
      - ADR → wiki/concepts/adr-<name>.md
      - Guide → wiki/topics/<name>.md
      - API Ref → wiki/entities/<api-name>.md
      - Session → wiki/sources/<date>-session.md

3. Pflege Cross-References zwischen migrierten Seiten
```

**Phase 3: Aufräumen**

```
1. Duplikate: Gleicher Inhalt → konsolidieren auf einer Seite
2. Verlinkung: Cross-References zwischen migrierten Seiten erstellen
3. Validierung: OKF-Compliance aller migrierten Seiten prüfen (Linter-Delegation)
4. Index: Initiales index.md generieren (Indexer-Delegation)
5. Log: Migration als erstes log.md Event dokumentieren (Indexer-Delegation)
```

**Schutzregeln (HARD CONSTRAINTS):**

| Datei | Schutz | Begründung |
|-------|--------|-----------|
| `docs/CODEBASE_OVERVIEW.md` | NIEMALS migrieren | Gehört dem `documenter`-Agent |
| `docs/REQUIREMENTS.md` | NIEMALS migrieren | Gehört dem `requirements`-Agent |
| `CLAUDE.md`, `AGENTS.md` | NIEMALS anfassen | Provider-Context (agent-meta managed) |
| `.claude/`, `.gemini/`, `.opencode/` | NIEMALS anfassen | Provider-Verzeichnisse |
| `VERSION`, `LICENSE` | NIEMALS migrieren | Infrastruktur-Dateien |
| `CHANGELOG.md` | NUR als Source KOPIEREN | Originale bleiben |

**role-defaults.yaml:**
```yaml
knowledge-migrator:
  model: balanced
  memory: ''
  workflow_tier: optional
  conditional: knowledge-engine
  description: >-
    Vorhandene Projektinhalte aufräumen und OKF-konform ins Knowledge
    Wiki migrieren. Discovery → Plan → User-Freigabe → Migration → Validierung.
    Schützt documenter- und requirements-eigene Dateien.
  routing:
    intent_keywords:
      - Migrieren
      - Aufräumen
      - Wiki-Migration
      - Docs migrieren
      - Vorhandene Docs ins Wiki
    parallel: false
    orchestrator_only: false
  handoff:
    input_contracts:
      - task-spec-v1
    output_contract: knowledge-migration-v1
    timeout_sec: 600
```

---

## 10. Provider-MD Inhalte (CLAUDE.md / AGENTS.md)

### 10.1 Wie Provider-MDs aktualisiert werden

Provider-Context-Dateien (CLAUDE.md, AGENTS.md) werden **NICHT** durch Template-Conditionals aktualisiert, sondern durch **Python-Code** in `build_agent_hints()` und `build_agent_table()`. Die Logik:

1. `build_agent_hints()` (Zeile 1859 in `agents.py`) iteriert über alle Rollen
2. Für jede Rolle wird `_is_role_enabled(role, config)` aufgerufen (Zeile 1909)
3. Wenn `knowledge-engine.enabled: false`, returniert `_is_role_enabled()` `False` für alle `knowledge-*` Rollen
4. Diese Rollen erscheinen dann **nicht** in der Agent-Tabelle

**Zusätzlich:** Ein Knowledge-Engine-Abschnitt wird in `build_agent_hints()` injiziert — aber NUR wenn aktiviert.

### 10.2 Erweiterung von `build_agent_hints()` in `scripts/lib/agents.py`

Nach der Agent-Tabelle (nach Zeile 1917), vor dem Return:

```python
    # Knowledge Engine hints (only when enabled)
    if variables.get("KNOWLEDGE_ENGINE_ENABLED") == "true":
        bundle = variables.get("KNOWLEDGE_BUNDLE_PATH", "knowledge")
        domain = variables.get("KNOWLEDGE_DOMAIN", "research")
        wiki = variables.get("KNOWLEDGE_WIKI_DIR", f"{bundle}/wiki")
        sources = variables.get("KNOWLEDGE_SOURCES_DIR", f"{bundle}/sources")
        
        lines.append("")
        lines.append("## Knowledge Engine")
        lines.append("")
        lines.append(f"Die Knowledge Engine ist aktiviert. Domäne: **{domain}**.")
        lines.append("")
        lines.append(f"**Bundle-Pfad:** `{bundle}/`")
        lines.append("| Pfad | Zweck |")
        lines.append("|------|-------|")
        lines.append(f"| `{bundle}/schema.md` | Steuerungsdokument — Konventionen, Concept Types, Workflows |")
        lines.append(f"| `{sources}/` | Immutable Raw Sources — LLM liest, modifiziert NIEMALS |")
        lines.append(f"| `{wiki}/` | OKF Knowledge Bundle — LLM-owned, strukturiertes Wiki |")
        lines.append(f"| `{wiki}/index.md` | Content-Katalog aller Wiki-Seiten (OKF §6) |")
        lines.append(f"| `{wiki}/log.md` | Chronologisches Event-Log (OKF §7) |")
        lines.append("")
        lines.append("### Knowledge-Workflows")
        lines.append(f"- **Ingest:** Source in `{sources}/` ablegen → `knowledge-ingestor` verarbeitet → Wiki aktualisiert")
        lines.append("- **Query:** Frage stellen → `knowledge-querier` durchsucht Index → synthetisiert Antwort")
        lines.append("- **Lint:** `knowledge-linter` prüft Wiki-Gesundheit (Widersprüche, Orphans, OKF-Compliance)")
        lines.append("- **Migration:** `knowledge-migrator` räumt vorhandene Inhalte auf und migriert ins OKF-Format")
        lines.append("- **Gardening:** `knowledge-gardener` pflegt Links, Tags, Typos, Timestamps")
```

### 10.3 Gemini Bootstrap-Erweiterung

Der Bootstrap-Block in AGENTS.md wird über `provider-bootstrap.yaml` und die Python-Logik generiert. Knowledge-Agenten werden nur eingefügt wenn aktiviert.

Die bestehende Bootstrap-Generierungslogik iteriert über alle generierten Agent-Dateien in `.gemini/agents/`. Da `_is_role_enabled()` die `knowledge-*` Agenten bei deaktivierter Engine nicht generiert, tauchen sie automatisch auch nicht im Bootstrap auf. **Kein Extra-Code nötig.**

### 10.4 Resultierender CLAUDE.md Managed Block (Beispiel bei aktivierter Engine)

```markdown
<!-- agent-meta:managed-begin -->
<!-- This block is automatically updated by sync.py on every sync. -->
<!-- Manual changes here will be overwritten. -->

> **AI ROUTING:** Claude -> CLAUDE.md | Opencode, Mammouth, Gemini -> AGENTS.md

Generiert von agent-meta v0.82.0 — `2026-07-25`
DoD-Preset: **rapid-prototyping** | REQ-Traceability: false | Tests: false | Codebase-Overview: false | Security-Audit: false

> **Einstiegspunkt:** Startet den `orchestrator`-Agenten für alle Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«.

| Agent | Zuständigkeit |
|-------|--------------|
| `orchestrator` | Einstiegspunkt für ALLE Entwicklungsaufgaben — zerlegt komplexe Tasks und dispatched parallel |
| `developer` | Feature-Implementierung und Bugfixes im Projekt |
| ... (bestehende Agenten) ... |
| `knowledge-curator` | Wiki-Strategie, Schema-Evolution, OKF-Compliance |
| `knowledge-ingestor` | Sources einlesen, Wiki-Seiten erstellen/aktualisieren |
| `knowledge-querier` | Fragen gegen Wiki beantworten, Synthesen archivieren |
| `knowledge-linter` | Wiki-Gesundheit: Widersprüche, Orphans, OKF-Compliance |
| `knowledge-indexer` | index.md und log.md pflegen |
| `knowledge-gardener` | Link-Pflege, Tags, Typos, Frontmatter-Hygiene |
| `knowledge-migrator` | Vorhandene Inhalte aufräumen, OKF-konform migrieren |

## Knowledge Engine

Die Knowledge Engine ist aktiviert. Domäne: **research**.

**Bundle-Pfad:** `knowledge/`
| Pfad | Zweck |
|------|-------|
| `knowledge/schema.md` | Steuerungsdokument — Konventionen, Concept Types, Workflows |
| `knowledge/sources/` | Immutable Raw Sources — LLM liest, modifiziert NIEMALS |
| `knowledge/wiki/` | OKF Knowledge Bundle — LLM-owned, strukturiertes Wiki |
| `knowledge/wiki/index.md` | Content-Katalog aller Wiki-Seiten (OKF §6) |
| `knowledge/wiki/log.md` | Chronologisches Event-Log (OKF §7) |

### Knowledge-Workflows
- **Ingest:** Source in `knowledge/sources/` ablegen → `knowledge-ingestor` verarbeitet → Wiki aktualisiert
- **Query:** Frage stellen → `knowledge-querier` durchsucht Index → synthetisiert Antwort
- **Lint:** `knowledge-linter` prüft Wiki-Gesundheit (Widersprüche, Orphans, OKF-Compliance)
- **Migration:** `knowledge-migrator` räumt vorhandene Inhalte auf und migriert ins OKF-Format
- **Gardening:** `knowledge-gardener` pflegt Links, Tags, Typos, Timestamps

<!-- agent-meta:managed-end -->
```

---

## 11. Orchestrator-Template Erweiterung

Im `agents/1-generic/orchestrator.md` wird ein bedingter Block hinzugefügt, der von `strip_inactive_conditional_blocks()` nur bei aktivierter Engine beibehalten wird:

```markdown
{{#if KNOWLEDGE_ENGINE_ENABLED}}
---

## Knowledge Engine Routing

| Intent | Agent | Beispiel-Trigger |
|--------|-------|-----------------|
| Source einlesen / verarbeiten | `knowledge-curator` → `knowledge-ingestor` | "Verarbeite dieses Paper" |
| Wiki-Frage / Recherche | `knowledge-querier` | "Was wissen wir über X?" |
| Wiki prüfen / Lint | `knowledge-linter` | "Wiki-Healthcheck" |
| Schema anpassen / Wiki-Strategie | `knowledge-curator` | "Neue Concept Types hinzufügen" |
| Kleinteilige Wiki-Fixes | `knowledge-gardener` | "Links im Wiki reparieren" |
| Index aktualisieren | `knowledge-indexer` | Automatisch (nicht direkt delegieren) |
| Vorhandene Docs aufräumen | `knowledge-migrator` | "Migriere docs/ ins Wiki" |

**Ingest-Pipeline (Standard-Flow):**
1. User → Orchestrator: "Verarbeite diese Source"
2. Orchestrator → `knowledge-curator`: Plant Ingest
3. `knowledge-curator` → `knowledge-ingestor`: Verarbeitet Source
4. `knowledge-ingestor` → `knowledge-indexer`: Aktualisiert index.md + log.md
5. Optional: `knowledge-curator` → `knowledge-linter`: Konsistenzprüfung

**Migration-Pipeline (Einmalig bei Erstaktivierung):**
1. User → Orchestrator: "Migriere vorhandene Docs ins Wiki"
2. Orchestrator → `knowledge-migrator`: Discovery → Plan → User-Freigabe → Migration
3. `knowledge-migrator` → `knowledge-indexer`: Initiales index.md + log.md
4. `knowledge-migrator` → `knowledge-linter`: Validierung
{{/if}}
```

---

## 12. CODEBASE_OVERVIEW Integration

Im `agents/1-generic/documenter.md` wird ein bedingter Block hinzugefügt:

```markdown
{{#if KNOWLEDGE_ENGINE_ENABLED}}
## Knowledge Engine Dokumentation

Das Projekt nutzt eine Knowledge Engine (OKF-konform).

| Pfad | Zweck | Dein Auftrag |
|------|-------|-------------|
| `{{KNOWLEDGE_BUNDLE_PATH}}/` | Knowledge Bundle Root | In CODEBASE_OVERVIEW als Verzeichnis listen |
| `{{KNOWLEDGE_WIKI_DIR}}/` | OKF Knowledge Bundle | Verzeichnisstruktur dokumentieren |
| `{{KNOWLEDGE_SOURCES_DIR}}/` | Raw Sources | Nur Existenz erwähnen |
| `{{KNOWLEDGE_SCHEMA_PATH}}` | Steuerungsdokument | NICHT bearbeiten — gehört dem knowledge-curator |

**ABGRENZUNG:**
- Du dokumentierst die Knowledge-Bundle-**STRUKTUR** in CODEBASE_OVERVIEW
- Du schreibst **NICHT** ins Wiki — Wiki-Inhalte verwalten ausschließlich die `knowledge-*` Agenten
- `{{KNOWLEDGE_SCHEMA_PATH}}` ist **NICHT** deine Datei — nur lesen, nie bearbeiten
{{/if}}
```

---

## 13. SE-Kaskaden Kompatibilität

### 13.1 Parallelen im Aktivierungsmuster

| Aspekt | SE-Kaskade | Knowledge Engine |
|--------|-----------|-----------------|
| Config-Key | `systems-engineering.enabled` | `knowledge-engine.enabled` |
| Default | `true` (historisch) | `false` (opt-in) |
| Role-Prefix | `se-*` | `knowledge-*` |
| `_is_role_enabled()` Check | `role.startswith("se-")` | `role.startswith("knowledge-")` |
| Variable | `SE_ENABLED` | `KNOWLEDGE_ENGINE_ENABLED` |
| Zero-Overhead | ✅ | ✅ |
| Agent-Anzahl | 14 Rollen | 7 Rollen |

### 13.2 Synergie wenn beide aktiv

SE und Knowledge Engine sind **unabhängige Features** — keines hängt vom anderen ab. Wenn BEIDE aktiv:

- SE-Decomposition-Output (`SE/L1/.../*.md`) kann als Knowledge-Source in `knowledge/sources/se/` verlinkt werden
- Der `knowledge-migrator` erkennt SE-Output bei Discovery und schlägt Migration vor
- Knowledge Wiki kann SE-Architektur-Entscheidungen als OKF-Concepts dokumentieren
- **Kein Coupling:** Jedes Feature funktioniert unabhängig

### 13.3 Kein SE-Cascade-Equivalent

Die Knowledge Engine implementiert **KEIN Cascade-Modell** (keine rekursive Dekomposition, keine V-Model-Architektur). Die Operationen (Ingest/Query/Lint) sind **flache Workflows**, kein Fractal-Cell-Modell.

---

## 14. Framework-Kompatibilitätsmatrix (22 Punkte)

| # | Framework-Feature | Integration | Aufwand |
|---|-------------------|-------------|---------|
| 1 | **`_is_role_enabled()`** | `knowledge-*` Prefix-Check analog zu `se-*` | 3 Zeilen |
| 2 | **`build_variables()`** | `KNOWLEDGE_ENGINE_ENABLED` + 7 weitere Variables | ~30 Zeilen |
| 3 | **`build_agent_hints()`** | Knowledge Engine Block (Pfade, Workflows) wenn aktiviert | ~25 Zeilen |
| 4 | **`build_agent_table()`** | Automatisch via `_is_role_enabled()` — kein Extra-Code | 0 Zeilen |
| 5 | **`strip_inactive_conditional_blocks()`** | `KNOWLEDGE_ENGINE_ENABLED` automatisch via `build_variables()` | 0 Zeilen |
| 6 | **SE-Kaskade** | Unabhängig, synergetisch wenn beide aktiv | Convention only |
| 7 | **CODEBASE_OVERVIEW** | `{{#if KNOWLEDGE_ENGINE_ENABLED}}` Block in `documenter.md` | Template-Block |
| 8 | **DoD-Presets** | Optional: `knowledge-updated: true/false` in dod-presets.yaml | 6 Zeilen |
| 9 | **Quality Pipelines** | Optional: `knowledge-ingest` Pipeline (Ingest → Lint → Index) | Schema + Config |
| 10 | **Reflection Pairs** | Optional: `ingestor ↔ linter` (Ingest → Lint → Re-Ingest, max 2) | Config-Eintrag |
| 11 | **Hooks** | Optional: `knowledge-post-commit` Hook | Script + Config |
| 12 | **MCP-Registry** | `qmd` als optionaler Search-MCP-Server | Config-Eintrag |
| 13 | **Viz/Event-Tracking** | Knowledge-Ops als Events in `.meta-viz/events.jsonl` | Convention |
| 14 | **Export** | `knowledge-bundle` Export-Target in `export.yaml` | Config-Eintrag |
| 15 | **Orchestrator Routing** | `{{#if KNOWLEDGE_ENGINE_ENABLED}}` Block im Orchestrator | Template-Block |
| 16 | **Direct Dispatch** | `knowledge-querier` direkt dispatched (einfache Frage) | Direct-Dispatch-Table |
| 17 | **Debug Mode** | Automatisch: `[Agent: knowledge-*]` Header | 0 (automatisch) |
| 18 | **Speech Mode** | Automatisch: Rules in allen Provider-Dirs | 0 (automatisch) |
| 19 | **Provider Isolation** | `knowledge/` liegt im Root — alle Provider haben Zugriff | 0 (Standard) |
| 20 | **Memory** | `knowledge-curator` + `knowledge-ingestor`: `memory: project` | role-defaults |
| 21 | **Tier-Presets** | Automatisch: In `Cheap`-Mode heruntergestuft | 0 (automatisch) |
| 22 | **Extensions (3-project)** | Projekte erstellen `<prefix>-knowledge-curator-ext.md` | 0 (Standard) |
| 23 | **Gemini Bootstrap** | Automatisch: `_is_role_enabled()` filtert Nicht-Generierte | 0 (automatisch) |
| 24 | **Gitignore** | Keine Einträge nötig — Bundle ist committed (Git-Wiki) | 0 |
| 25 | **Commands** | Optional: `/ingest`, `/query`, `/lint-wiki` Slash-Commands | 3 Dateien |

---

## 15. Sync-Pipeline Integration

### 15.1 Einordnung in bestehende Pipeline

```
Phase 1: Schema Sync + Config & Variable Resolution
Phase 2: Per-Provider Sync Loop
  ├── sync_context_for_provider
  ├── sync_agents_for_provider    ← knowledge-* Agenten werden hier generiert
  ├── sync_rules & sync_speech_mode
  ├── generate_mcp_artifacts
  ├── sync_hooks & sync_commands
  └── sync_snippets & external_skills
Phase 2.5: ★ sync_knowledge_engine (NEU) ★
Phase 3: Provider Isolation
Phase 4: Skills & Gitignore
Phase 5: Config Audit
Phase 6: Viz & Analysis
```

**Phase 2.5 weil:**
- Braucht aufgelöste Variables (Phase 1 fertig)
- Agent-Dateien müssen generiert sein (Phase 2 fertig)
- Bundle-Struktur muss vor Gitignore-Update existieren (Phase 4)

### 15.2 `sync_knowledge_engine()` — Implementierung

```python
def sync_knowledge_engine(project_root: Path, config: dict, variables: dict, log: SyncLog):
    """Sync Knowledge Engine: Bundle-Struktur + Schema + OKF-Scaffold."""
    ke_config = config.get("knowledge-engine") or {}
    if not ke_config.get("enabled", False):
        log.info("Knowledge Engine: disabled (skipped)")
        return
    
    bundle_path = project_root / ke_config.get("bundle-path", "knowledge")
    wiki_dir = bundle_path / ke_config.get("wiki-dir", "wiki")
    sources_dir = bundle_path / ke_config.get("sources-dir", "sources")
    
    # 1. Bundle-Verzeichnisstruktur sicherstellen
    dirs_to_create = [
        sources_dir,
        sources_dir / "assets",
        wiki_dir,
        wiki_dir / "concepts",
        wiki_dir / "entities",
        wiki_dir / "topics",
        wiki_dir / "sources",
        wiki_dir / "queries",
    ]
    created = []
    for d in dirs_to_create:
        if not d.exists():
            d.mkdir(parents=True, exist_ok=True)
            (d / ".gitkeep").touch(exist_ok=True)
            created.append(str(d.relative_to(project_root)))
    if created:
        log.info(f"Knowledge Engine: Created {len(created)} directories")
    
    # 2. schema.md generieren (NUR wenn nicht existent — User kann es editieren)
    schema_path = bundle_path / "schema.md"
    if not schema_path.exists():
        from .knowledge import generate_schema
        schema_content = generate_schema(ke_config, variables)
        schema_path.write_text(schema_content, encoding="utf-8")
        log.info(f"Knowledge Engine: Generated {schema_path.relative_to(project_root)}")
    
    # 3. index.md Scaffold (NUR wenn nicht existent)
    index_path = wiki_dir / "index.md"
    if not index_path.exists():
        from .knowledge import generate_initial_index
        index_path.write_text(generate_initial_index(variables), encoding="utf-8")
        log.info(f"Knowledge Engine: Generated initial index.md")
    
    # 4. log.md Scaffold (NUR wenn nicht existent)
    log_path = wiki_dir / "log.md"
    if not log_path.exists():
        from .knowledge import generate_initial_log
        log_path.write_text(generate_initial_log(variables), encoding="utf-8")
        log.info(f"Knowledge Engine: Generated initial log.md")
    
    log.info(f"Knowledge Engine: Synced (domain={ke_config.get('domain', 'research')})")
```

### 15.3 Neue lib-Datei: `scripts/lib/knowledge.py`

```python
"""
Knowledge Engine support for agent-meta sync.py.

Handles:
- Bundle directory structure creation
- Schema template generation (domain-adaptive)
- Initial index.md / log.md scaffolding
- Target repo detection for domain adaptation
"""

from datetime import datetime

DOMAIN_CONCEPT_TYPES = {
    "research": ["Paper", "Dataset", "Method", "Finding", "Hypothesis",
                 "Comparison", "Literature Review", "Author", "Institution"],
    "personal": ["Goal", "Journal Entry", "Health Record", "Insight",
                 "Resource", "Habit", "Reflection", "Book Note"],
    "business": ["Meeting", "Decision", "Process", "Metric",
                 "Customer Insight", "Competitor", "Strategy", "OKR"],
    "book":     ["Chapter", "Character", "Theme", "Plot Thread",
                 "Setting", "Quote", "Timeline Event", "Relationship"],
    "internal-docs": ["Concept", "Architecture", "API Reference", "Guide", "Session Conclusion"],
    "custom":   ["Concept", "Entity", "Topic", "Source Summary", "Query Result"],
}

def generate_schema(ke_config: dict, variables: dict) -> str:
    """Generate domain-adaptive schema.md from template."""
    # Template-Substitution mit variables dict
    # ... (Template aus templates/knowledge-schema.template.md laden und substituieren)
    pass

def generate_initial_index(variables: dict) -> str:
    """Generate empty OKF-compliant index.md scaffold."""
    project = variables.get("PROJECT_NAME", "Project")
    now = datetime.now().isoformat()
    return f"""---
type: Index
title: "{project} Knowledge Wiki — Inhaltsverzeichnis"
timestamp: {now}
---

# Index

*Noch keine Einträge. Starte einen Ingest um das Wiki zu füllen.*
"""

def generate_initial_log(variables: dict) -> str:
    """Generate empty OKF-compliant log.md scaffold."""
    now = datetime.now().strftime("%Y-%m-%d")
    return f"""---
type: Log
title: "Knowledge Wiki — Changelog"
---

# Log

## [{now}] init | Knowledge Engine aktiviert
- Bundle-Struktur angelegt
- Schema generiert
- Bereit für ersten Ingest
"""

def detect_target_repo(project_root, config):
    """Analysiert Zielrepo und schlägt Domänen-Adaptionen vor."""
    adaption = {
        "language": config.get("variables", {}).get("COMMUNICATION_LANGUAGE", "Deutsch"),
        "tech_stack": "unknown",
        "migratable_files": [],
        "protected_files": [
            "docs/CODEBASE_OVERVIEW.md",
            "docs/REQUIREMENTS.md",
        ],
    }
    markers = {
        "package.json": "Node.js", "requirements.txt": "Python",
        "Cargo.toml": "Rust", "go.mod": "Go", "pom.xml": "Java/Maven",
    }
    for marker, stack in markers.items():
        if (project_root / marker).exists():
            adaption["tech_stack"] = stack
            break
    return adaption
```

---

## 16. Neue Dateien und Modifikationen

### 16.1 Neue Dateien (11)

| # | Datei | Beschreibung | Größe (geschätzt) |
|---|-------|-------------|-------------------|
| 1 | `scripts/lib/knowledge.py` | Knowledge Engine Sync-Logik | ~150 Zeilen |
| 2 | `agents/1-generic/knowledge-curator.md` | Strategischer Dirigent | ~120 Zeilen |
| 3 | `agents/1-generic/knowledge-ingestor.md` | Source-Verarbeitung + Wiki-Update | ~180 Zeilen |
| 4 | `agents/1-generic/knowledge-querier.md` | Index-First Query + File-Back | ~120 Zeilen |
| 5 | `agents/1-generic/knowledge-linter.md` | 10 Lint-Checks | ~150 Zeilen |
| 6 | `agents/1-generic/knowledge-indexer.md` | index.md + log.md Pflege | ~100 Zeilen |
| 7 | `agents/1-generic/knowledge-gardener.md` | Kleinteilige Pflege | ~100 Zeilen |
| 8 | `agents/1-generic/knowledge-migrator.md` | Aufräum- und Migrations-Agent | ~200 Zeilen |
| 9 | `templates/knowledge-schema.template.md` | Domänen-adaptives Schema-Template | ~80 Zeilen |
| 10 | `templates/knowledge-index.template.md` | Initiales index.md Scaffold | ~20 Zeilen |
| 11 | `templates/knowledge-log.template.md` | Initiales log.md Scaffold | ~15 Zeilen |

### 16.2 Modifizierte Dateien (8)

| # | Datei | Änderung | Zeilen |
|---|-------|----------|--------|
| 1 | `scripts/lib/agents.py` | `_is_role_enabled()` + `knowledge-` Check | +3 |
| 2 | `scripts/lib/agents.py` | `build_agent_hints()` + Knowledge Engine Block | +25 |
| 3 | `scripts/lib/config.py` | `build_variables()` + Knowledge-Variablen | +30 |
| 4 | `scripts/sync.py` | Import `lib.knowledge`, Aufruf `sync_knowledge_engine()` | +5 |
| 5 | `config/role-defaults.yaml` | 7 neue Rollen mit `conditional: knowledge-engine` | +80 |
| 6 | `config/project-config.schema.json` | `knowledge-engine` Objekt-Schema | +60 |
| 7 | `agents/1-generic/orchestrator.md` | `{{#if KNOWLEDGE_ENGINE_ENABLED}}` Routing-Block | +25 |
| 8 | `agents/1-generic/documenter.md` | `{{#if KNOWLEDGE_ENGINE_ENABLED}}` CODEBASE-Block | +15 |

### 16.3 Optionale Erweiterungen (nachgelagert)

| Datei | Änderung |
|-------|----------|
| `config/dod-presets.yaml` | `knowledge-updated` Kriterium |
| `config/export.yaml` | `knowledge-bundle` Export-Target |
| `config/plugin-catalog.yaml` | `qmd` MCP-Server-Eintrag |

---

## 17. OKF Compliance Matrix

| OKF Requirement | Spec § | Implementierung | Agent |
|:----------------|:-------|:----------------|:------|
| Knowledge Bundle = Verzeichnisbaum | §3 | `knowledge/wiki/` von sync.py | sync.py |
| `index.md` für progressive disclosure | §3.1, §6 | Generiert + gepflegt | `knowledge-indexer` |
| `log.md` für Update-History | §3.1, §7 | Generiert + append-only | `knowledge-indexer` |
| Reservierte Dateinamen | §3.1 | In Schema + Ingestor enforced | `knowledge-ingestor` |
| Concept = 1 UTF-8 Markdown | §4 | Template + Konvention | Alle |
| `type` REQUIRED in Frontmatter | §4.1 | Linter CRITICAL, Ingestor setzt | Linter + Ingestor |
| `title` RECOMMENDED | §4.1 | Gardener ergänzt fehlende | Gardener |
| `description` RECOMMENDED | §4.1 | Gardener ergänzt fehlende | Gardener |
| `resource` RECOMMENDED | §4.1 | Ingestor setzt bei Assets, Gardener ergänzt fehlende | Ingestor + Gardener |
| `tags` OPTIONAL | §4.1 | Ingestor setzt, Gardener harmonisiert | Ingestor + Gardener |
| `timestamp` OPTIONAL | §4.1 | Gardener aktualisiert | Gardener |
| Producer-defined key/value pairs | §4.1 | `sources`, `migrated_from` etc. | Alle |
| Concept ID = Pfad ohne .md | §4 | Schema-Konvention | Alle |
| Standard-MD-Links für Cross-Refs | §5 | Ingestor + Gardener pflegen | Ingestor + Gardener |
| Citations = Links zu Quellen | §5 | Ingestor erstellt | Ingestor |
| Unbekannte Types tolerieren | §4.1 | Querier + Linter: graceful | Querier + Linter |
| Git-basierte Distribution | §3 | Bundle = Teil des Git-Repos | Automatisch |

---

## 18. Karpathy Compliance Matrix

| Karpathy Pattern | Implementierung | Agent(en) |
|:-----------------|:----------------|:----------|
| **3 Layers:** Sources, Wiki, Schema | `sources/`, `wiki/`, `schema.md` | sync.py + alle |
| **Ingest:** Source → Wiki (10-15 Seiten) | Ingest-Pipeline | Curator → Ingestor → Indexer |
| **Query:** Index → Drill-in → Synthese | Index-First, Citations | Querier |
| **Lint:** Health-Check (10 Checks) | Lint-Pipeline | Linter → Gardener |
| **index.md:** Content-Katalog | OKF-konform, auto-update | Indexer |
| **log.md:** Append-only Event-Log | Parseable Format | Indexer |
| **File-Back:** Antworten → Wiki-Seiten | `wiki/queries/` | Querier |
| **Cross-References:** automatisch | Standard-MD-Links | Ingestor + Gardener |
| **Schema-Evolution:** User + LLM | `schema.md` editierbar | Curator |
| **Wiki = Git-Repo** | Bundle committed | Automatisch |
| **LLM schreibt, Mensch liest** | Agenten-owned Wiki | Alle knowledge-* |
| **Compounding Knowledge** | Jeder Ingest erweitert Synthese | Ingestor |
| **Obsidian-kompatibel** | Standard-MD + YAML-FM | Alle |
| **CLI-Tools (qmd)** | MCP-Registry optional | qmd (optional) |
| **Widersprüche flaggen** | Lint-Check #1 | Linter |
| **Orphan-Seiten finden** | Lint-Check #3 | Linter |
| **Domänen-Anpassung** | 6 Presets + Zielrepo-Detection | Curator + sync.py |
| **Obsidian Web Clipper** | Source-Import: Markdown-Konvertierung via Clipper → sources/ | User (Tipp in schema.md) |
| **Download Images Locally** | `sources/assets/` für lokale Bilder | Ingestor (referenziert assets) |
| **Marp Slide Decks** | Query-Output als Marp-Markdown möglich | Querier (output-format) |
| **Dataview-kompatibel** | YAML-Frontmatter-Queries via Obsidian Dataview Plugin | Alle (OKF Frontmatter) |
| **Vannevar Bush Memex** | Philosophische Grundlage: Private, curated, associative trails | Konzeptionell |
| **Schema = CLAUDE.md/AGENTS.md** | `schema.md` als dediziertes Steuerungsdokument (analog zu Provider-Context-Dateien) | Curator |
| **"Intentionally abstract"** | Domänen-Presets + Zielrepo-Detection als Konkretisierung | Presets + sync.py |

---

## 19. AdminUI Integration

> Die Knowledge Engine wird über die bestehende AdminUI (`docs/ui/admin-ui.html`) steuerbar.
> Projektspezifisch, mit Best-Practice-Voreinstellungen je Domäne.

### 19.1 Neue Route

| Aspekt | Wert |
|--------|------|
| **Route** | `/project/knowledge-engine` |
| **Sidebar-Gruppe** | Project instance |
| **Icon** | 🧠 |
| **Label** | Knowledge Engine |
| **View-Funktion** | `viewProjectKnowledgeEngine()` |
| **Config-Sektion** | `knowledge-engine` in `project.yaml` |

### 19.2 Server-Änderung (`scripts/admin-server.py`)

In `_write_project_section()` muss `"knowledge-engine"` zur `allowed`-Menge hinzugefügt werden:

```python
allowed = {
    "agent-prompts", "model-overrides", "memory-overrides", "permission-mode-overrides",
    "steps-overrides", "dod", "rules", "roles", "orchestrator", "viz", "admin-ui",
    "provider-tier-overrides", "project", "dod-preset", "rules-preset", "speech-mode",
    "tier-preset", "se-focus", "ai-providers", "platforms", "provider-options",
    "provider-isolation", "environments", "model-source-preference",
    "knowledge-engine",  # ← NEU
}
```

### 19.3 Sidebar-Eintrag (`docs/ui/admin-ui.html`)

In `buildSidebar()` (ca. Zeile 1348), in der Gruppe `"Project instance"`:

```javascript
{ route: "/project/knowledge-engine", label: "Knowledge Engine", icon: "🧠" },
```

### 19.4 Router-Registrierung (`docs/ui/admin-ui.html`)

In `init()` (ca. Zeile 7312):

```javascript
router.register("/project/knowledge-engine", viewProjectKnowledgeEngine);
```

In `helpDocs` `routeMap` (ca. Zeile 7400):

```javascript
"project/knowledge-engine": "project_instance-knowledge_engine",
```

### 19.5 Vollständige View-Funktion `viewProjectKnowledgeEngine()`

```javascript
async function viewProjectKnowledgeEngine() {
  const wrap = el("div");
  wrap.appendChild(el("h1", {}, ["Project — Knowledge Engine"]));
  wrap.appendChild(el("p", { class: "muted" }, [
    "Karpathy LLM-Wiki + Google OKF v0.1 — "
    + "Persistentes Knowledge Wiki mit OKF-konformen Concept-Dokumenten, "
    + "automatischer Index-Pflege und 7 spezialisierten Agenten."
  ]));

  // --- Load project config ---
  const data = await loadProject();
  const ke = (data["knowledge-engine"] && typeof data["knowledge-engine"] === "object")
    ? clone(data["knowledge-engine"])
    : {};

  const status = el("div", { class: "muted" }, ["Loaded from project.yaml."]);
  wrap.appendChild(status);

  // --- Ensure nested objects ---
  if (!ke.okf || typeof ke.okf !== "object") ke.okf = {};
  if (!ke.operations || typeof ke.operations !== "object") ke.operations = {};
  if (!ke.operations.ingest || typeof ke.operations.ingest !== "object") ke.operations.ingest = {};
  if (!ke.operations.query || typeof ke.operations.query !== "object") ke.operations.query = {};
  if (!ke.operations.lint || typeof ke.operations.lint !== "object") ke.operations.lint = {};
  if (!ke.migration || typeof ke.migration !== "object") ke.migration = {};
  if (!ke.search || typeof ke.search !== "object") ke.search = {};

  // --- Best Practice Preset Selector ---
  const presetPanel = el("div", { class: "panel" });
  presetPanel.appendChild(el("h2", {}, ["⚡ Best-Practice Preset"]));
  presetPanel.appendChild(el("p", { class: "muted" }, [
    "Wähle ein Preset um alle Felder mit bewährten Voreinstellungen zu füllen. "
    + "Danach kannst du einzelne Werte anpassen."
  ]));

  const PRESETS = {
    research: {
      domain: "research", "bundle-path": "knowledge", "sources-dir": "sources",
      "wiki-dir": "wiki", "schema-language": "auto",
      okf: { "enforce-frontmatter": true, "allowed-types": [], "auto-index": true, "auto-log": true },
      operations: {
        ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": false },
        query: { "file-back-results": true },
        lint: { schedule: "post-ingest", checks: [
          "contradictions", "stale-claims", "orphan-pages", "missing-concepts",
          "broken-links", "data-gaps", "missing-frontmatter", "index-staleness"
        ]}
      },
      migration: { "auto-detect-sources": true, "clean-duplicates": true, "preserve-originals": true },
      search: { engine: "index-only", "mcp-server": "" }
    },
    personal: {
      domain: "personal", "bundle-path": "knowledge", "sources-dir": "sources",
      "wiki-dir": "wiki", "schema-language": "auto",
      okf: { "enforce-frontmatter": true, "allowed-types": [], "auto-index": true, "auto-log": true },
      operations: {
        ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": false },
        query: { "file-back-results": true },
        lint: { schedule: "on-demand", checks: [
          "orphan-pages", "missing-concepts", "broken-links", "missing-frontmatter"
        ]}
      },
      migration: { "auto-detect-sources": false, "clean-duplicates": false, "preserve-originals": true },
      search: { engine: "index-only", "mcp-server": "" }
    },
    business: {
      domain: "business", "bundle-path": "knowledge", "sources-dir": "sources",
      "wiki-dir": "wiki", "schema-language": "auto",
      okf: { "enforce-frontmatter": true, "allowed-types": [], "auto-index": true, "auto-log": true },
      operations: {
        ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": true },
        query: { "file-back-results": true },
        lint: { schedule: "post-ingest", checks: [
          "contradictions", "stale-claims", "orphan-pages", "missing-concepts",
          "broken-links", "missing-frontmatter", "index-staleness"
        ]}
      },
      migration: { "auto-detect-sources": true, "clean-duplicates": true, "preserve-originals": true },
      search: { engine: "index-only", "mcp-server": "" }
    },
    book: {
      domain: "book", "bundle-path": "knowledge", "sources-dir": "sources",
      "wiki-dir": "wiki", "schema-language": "auto",
      okf: { "enforce-frontmatter": true, "allowed-types": [], "auto-index": true, "auto-log": true },
      operations: {
        ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": false },
        query: { "file-back-results": false },
        lint: { schedule: "on-demand", checks: [
          "orphan-pages", "missing-concepts", "broken-links", "missing-frontmatter"
        ]}
      },
      migration: { "auto-detect-sources": false, "clean-duplicates": false, "preserve-originals": true },
      search: { engine: "index-only", "mcp-server": "" }
    },
    custom: {
      domain: "custom", "bundle-path": "knowledge", "sources-dir": "sources",
      "wiki-dir": "wiki", "schema-language": "auto",
      okf: { "enforce-frontmatter": false, "allowed-types": [], "auto-index": true, "auto-log": true },
      operations: {
        ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": false },
        query: { "file-back-results": true },
        lint: { schedule: "on-demand", checks: ["broken-links", "missing-frontmatter"] }
      },
      migration: { "auto-detect-sources": false, "clean-duplicates": false, "preserve-originals": true },
      search: { engine: "index-only", "mcp-server": "" }
    },
    "internal-docs": {
      domain: "internal-docs", "bundle-path": "knowledge", "sources-dir": "sources",
      "wiki-dir": "wiki", "schema-language": "auto",
      okf: { "enforce-frontmatter": true, "allowed-types": ["Concept", "Architecture", "API Reference", "Guide", "Session Conclusion"], "auto-index": true, "auto-log": true },
      operations: {
        ingest: { "auto-cross-reference": true, "auto-index-update": true, "batch-mode": true },
        query: { "file-back-results": true },
        lint: { schedule: "post-ingest", checks: ["broken-links", "missing-frontmatter", "stale-index", "orphaned-pages", "duplicate-concepts"] }
      },
      migration: { "auto-detect-sources": true, "clean-duplicates": false, "preserve-originals": true },
      search: { engine: "index-only", "mcp-server": "" }
    }
  };

  const presetSelect = el("select");
  ["— Preset wählen —", "research", "personal", "business", "book", "internal-docs", "custom"].forEach(p => {
    const opt = el("option", { value: p === "— Preset wählen —" ? "" : p }, [p]);
    presetSelect.appendChild(opt);
  });
  presetSelect.addEventListener("change", () => {
    const preset = PRESETS[presetSelect.value];
    if (!preset) return;
    // Deep-merge preset into ke
    Object.assign(ke, clone(preset));
    ke.enabled = true;
    // Re-render the page with new values
    router.navigate("/project/knowledge-engine");
  });
  const presetField = el("div", { class: "field" });
  presetField.appendChild(el("label", { class: "field-label" }, ["Domänen-Preset"]));
  presetField.appendChild(presetSelect);
  presetPanel.appendChild(presetField);
  wrap.appendChild(presetPanel);

  // ═══════════════════════════════════════════════════
  // Panel 1: General Settings
  // ═══════════════════════════════════════════════════
  const generalPanel = el("div", { class: "panel" });
  generalPanel.appendChild(el("h2", {}, ["General"]));
  generalPanel.appendChild(checkboxField("enabled", ke.enabled, v => ke.enabled = v));
  generalPanel.appendChild(dropdownField("domain", ke.domain,
    ["research", "personal", "business", "book", "internal-docs", "custom"],
    v => ke.domain = v
  ));
  generalPanel.appendChild(labeledTextField("bundle-path", ke["bundle-path"] ?? "knowledge",
    v => ke["bundle-path"] = v));
  generalPanel.appendChild(labeledTextField("sources-dir", ke["sources-dir"] ?? "sources",
    v => ke["sources-dir"] = v));
  generalPanel.appendChild(labeledTextField("wiki-dir", ke["wiki-dir"] ?? "wiki",
    v => ke["wiki-dir"] = v));
  generalPanel.appendChild(labeledTextField("schema-language", ke["schema-language"] ?? "auto",
    v => ke["schema-language"] = v));
  wrap.appendChild(generalPanel);

  // ═══════════════════════════════════════════════════
  // Panel 2: OKF Compliance Settings
  // ═══════════════════════════════════════════════════
  const okfPanel = el("div", { class: "panel" });
  okfPanel.appendChild(el("h2", {}, ["OKF (Open Knowledge Format)"]));
  okfPanel.appendChild(el("p", { class: "muted" }, [
    "Google OKF v0.1 — Frontmatter-Regeln, Concept-Type-Enforcement, Index-/Log-Automatik."
  ]));
  okfPanel.appendChild(checkboxField("enforce-frontmatter",
    ke.okf["enforce-frontmatter"] ?? true, v => ke.okf["enforce-frontmatter"] = v));
  okfPanel.appendChild(labeledTextField("allowed-types (kommagetrennt)",
    (ke.okf["allowed-types"] || []).join(", "),
    v => ke.okf["allowed-types"] = v ? v.split(",").map(s => s.trim()).filter(Boolean) : []
  ));
  okfPanel.appendChild(checkboxField("auto-index",
    ke.okf["auto-index"] ?? true, v => ke.okf["auto-index"] = v));
  okfPanel.appendChild(checkboxField("auto-log",
    ke.okf["auto-log"] ?? true, v => ke.okf["auto-log"] = v));
  wrap.appendChild(okfPanel);

  // ═══════════════════════════════════════════════════
  // Panel 3: Operations (Karpathy Workflow)
  // ═══════════════════════════════════════════════════
  const opsPanel = el("div", { class: "panel" });
  opsPanel.appendChild(el("h2", {}, ["Operations (Karpathy Workflow)"]));

  opsPanel.appendChild(el("h3", { style: "margin-top:12px;" }, ["Ingest"]));
  opsPanel.appendChild(checkboxField("auto-cross-reference",
    ke.operations.ingest["auto-cross-reference"] ?? true,
    v => ke.operations.ingest["auto-cross-reference"] = v));
  opsPanel.appendChild(checkboxField("auto-index-update",
    ke.operations.ingest["auto-index-update"] ?? true,
    v => ke.operations.ingest["auto-index-update"] = v));
  opsPanel.appendChild(checkboxField("batch-mode",
    ke.operations.ingest["batch-mode"] ?? false,
    v => ke.operations.ingest["batch-mode"] = v));

  opsPanel.appendChild(el("h3", { style: "margin-top:12px;" }, ["Query"]));
  opsPanel.appendChild(checkboxField("file-back-results",
    ke.operations.query["file-back-results"] ?? true,
    v => ke.operations.query["file-back-results"] = v));

  opsPanel.appendChild(el("h3", { style: "margin-top:12px;" }, ["Lint"]));
  opsPanel.appendChild(dropdownField("schedule",
    ke.operations.lint.schedule ?? "on-demand",
    ["on-demand", "post-ingest", "periodic"],
    v => ke.operations.lint.schedule = v
  ));

  // Lint-Checks as individual checkboxes
  const ALL_LINT_CHECKS = [
    "contradictions", "stale-claims", "orphan-pages", "missing-concepts",
    "broken-links", "data-gaps", "missing-frontmatter", "index-staleness"
  ];
  const activeLintChecks = new Set(ke.operations.lint.checks || ALL_LINT_CHECKS);
  opsPanel.appendChild(el("label", { class: "field-label", style: "margin-top:8px;" },
    ["Aktive Lint-Checks:"]));
  ALL_LINT_CHECKS.forEach(check => {
    opsPanel.appendChild(checkboxField(check, activeLintChecks.has(check), v => {
      if (v) activeLintChecks.add(check); else activeLintChecks.delete(check);
      ke.operations.lint.checks = [...activeLintChecks];
    }));
  });

  wrap.appendChild(opsPanel);

  // ═══════════════════════════════════════════════════
  // Panel 4: Migration
  // ═══════════════════════════════════════════════════
  const migPanel = el("div", { class: "panel" });
  migPanel.appendChild(el("h2", {}, ["Migration"]));
  migPanel.appendChild(el("p", { class: "muted" }, [
    "Vorhandene docs/ scannen und OKF-konform ins Wiki migrieren."
  ]));
  migPanel.appendChild(checkboxField("auto-detect-sources",
    ke.migration["auto-detect-sources"] ?? true, v => ke.migration["auto-detect-sources"] = v));
  migPanel.appendChild(checkboxField("clean-duplicates",
    ke.migration["clean-duplicates"] ?? true, v => ke.migration["clean-duplicates"] = v));
  migPanel.appendChild(checkboxField("preserve-originals",
    ke.migration["preserve-originals"] ?? true, v => ke.migration["preserve-originals"] = v));
  wrap.appendChild(migPanel);

  // ═══════════════════════════════════════════════════
  // Panel 5: Search Integration
  // ═══════════════════════════════════════════════════
  const searchPanel = el("div", { class: "panel" });
  searchPanel.appendChild(el("h2", {}, ["Search"]));
  searchPanel.appendChild(dropdownField("engine",
    ke.search.engine ?? "index-only",
    ["index-only", "mcp-qmd", "custom"],
    v => ke.search.engine = v
  ));
  searchPanel.appendChild(labeledTextField("mcp-server",
    ke.search["mcp-server"] ?? "",
    v => ke.search["mcp-server"] = v));
  wrap.appendChild(searchPanel);

  // ═══════════════════════════════════════════════════
  // Save & Dry-Run Buttons
  // ═══════════════════════════════════════════════════
  wrap.appendChild(el("div", { class: "btn-row" }, [
    el("button", { class: "btn btn-primary", onclick: async () => {
      try {
        await saveProjectSection("knowledge-engine", ke, status);
      } catch { /* toast handles error */ }
    }}, ["Save"]),
    el("button", { class: "btn", onclick: () => runDryRun() }, ["Dry-run"]),
  ]));

  return wrap;
}
```

### 19.6 AdminUI Panel-Architektur (5 Panels)

```
┌──────────────────────────────────────────────────────────┐
│  🧠 Project — Knowledge Engine                          │
│  Karpathy LLM-Wiki + Google OKF v0.1                     │
├──────────────────────────────────────────────────────────┤
│                                                          │
│  ⚡ Best-Practice Preset                                 │
│  ┌──────────────────────────────────┐                    │
│  │ Domänen-Preset: [research ▾]    │ ← Füllt alle       │
│  └──────────────────────────────────┘   Felder mit       │
│                                        bewährten Werten  │
│                                                          │
│  General                                                 │
│  ☑ enabled                                               │
│  [domain:     research ▾ ]                               │
│  [bundle-path: knowledge ]                               │
│  [sources-dir: sources   ]                               │
│  [wiki-dir:    wiki      ]                               │
│  [schema-language: auto  ]                               │
│                                                          │
│  OKF (Open Knowledge Format)                             │
│  ☑ enforce-frontmatter                                   │
│  [allowed-types:          ]                              │
│  ☑ auto-index                                            │
│  ☑ auto-log                                              │
│                                                          │
│  Operations (Karpathy Workflow)                          │
│  ▸ Ingest                                                │
│    ☑ auto-cross-reference                                │
│    ☑ auto-index-update                                   │
│    ☐ batch-mode                                          │
│  ▸ Query                                                 │
│    ☑ file-back-results                                   │
│  ▸ Lint                                                  │
│    [schedule: post-ingest ▾]                             │
│    Aktive Lint-Checks:                                   │
│    ☑ contradictions   ☑ stale-claims                     │
│    ☑ orphan-pages     ☑ missing-concepts                 │
│    ☑ broken-links     ☑ data-gaps                        │
│    ☑ missing-frontmatter ☑ index-staleness               │
│                                                          │
│  Migration                                               │
│  ☑ auto-detect-sources                                   │
│  ☑ clean-duplicates                                      │
│  ☑ preserve-originals                                    │
│                                                          │
│  Search                                                  │
│  [engine: index-only ▾]                                  │
│  [mcp-server:          ]                                 │
│                                                          │
│  [  Save  ] [  Dry-run  ]                                │
└──────────────────────────────────────────────────────────┘
```

### 19.7 Dateien für AdminUI-Integration

| # | Datei | Änderung |
|---|-------|---------|
| 1 | `scripts/admin-server.py` | `"knowledge-engine"` in `allowed` Set (1 Zeile) |
| 2 | `docs/ui/admin-ui.html` | Sidebar-Eintrag (1 Zeile) |
| 3 | `docs/ui/admin-ui.html` | Router-Registrierung (1 Zeile) |
| 4 | `docs/ui/admin-ui.html` | Help-Mapping (1 Zeile) |
| 5 | `docs/ui/admin-ui.html` | `viewProjectKnowledgeEngine()` Funktion (~180 Zeilen) |

---

## 20. Best-Practice Presets pro Domäne

> Jedes Preset füllt alle Konfigurationsfelder mit bewährten Werten.
> Der User wählt ein Preset, passt ggf. einzelne Werte an, klickt Save.

### 20.1 Preset: `research` (Empfohlen als Default)

| Feld | Wert | Begründung |
|------|------|------------|
| domain | `research` | Optimiert für Papers, Studien, Vergleiche |
| bundle-path | `knowledge` | Standard |
| sources-dir | `sources` | Immutable Sources |
| wiki-dir | `wiki` | OKF Bundle |
| schema-language | `auto` | Erbt aus COMMUNICATION_LANGUAGE |
| okf.enforce-frontmatter | `true` | Forschung braucht strukturierte Metadaten |
| okf.allowed-types | `[]` (frei) | Flexibel: Paper, Dataset, Method, Finding, etc. |
| okf.auto-index | `true` | Index immer aktuell für Queries |
| okf.auto-log | `true` | Chronologische Nachvollziehbarkeit |
| ingest.auto-cross-reference | `true` | Vernetzung ist Kernwert |
| ingest.auto-index-update | `true` | Sofortige Auffindbarkeit |
| ingest.batch-mode | `false` | Bei Forschung: 1-by-1 Diskussion |
| query.file-back-results | `true` | Synthesen kompoundieren |
| lint.schedule | `post-ingest` | Nach jedem Ingest sofort prüfen |
| lint.checks | **Alle 8** | Maximale Wiki-Gesundheit |
| migration.auto-detect-sources | `true` | Bestehende Docs erkennen |
| migration.clean-duplicates | `true` | Forschungsprojekte haben oft Duplikate |
| migration.preserve-originals | `true` | Sicherheit |
| search.engine | `index-only` | Für <100 Sources ausreichend |

### 20.2 Preset: `personal`

| Unterschied zu `research` | Wert | Begründung |
|--------------------------|------|------------|
| lint.schedule | `on-demand` | Weniger formal |
| lint.checks | 4 (Orphans, Missing, Links, FM) | Keine Widersprüche/Stale-Claims |
| migration.auto-detect-sources | `false` | Persönliches Wiki startet leer |
| migration.clean-duplicates | `false` | Weniger Source-Volumen |

### 20.3 Preset: `business`

| Unterschied zu `research` | Wert | Begründung |
|--------------------------|------|------------|
| ingest.batch-mode | `true` | Meeting-Transkripte, Slack-Threads in Bulk |
| lint.checks | 7 (alle außer data-gaps) | Business: kein Web-Recherche-Vorschlag |

### 20.4 Preset: `book`

| Unterschied zu `research` | Wert | Begründung |
|--------------------------|------|------------|
| query.file-back-results | `false` | Buch-Wiki ist Self-Contained |
| lint.schedule | `on-demand` | Kapitel-by-Kapitel |
| lint.checks | 4 (Orphans, Missing, Links, FM) | Fokus auf Vollständigkeit |
| migration.auto-detect-sources | `false` | Buch kommt sequentiell |

### 20.5 Preset: `custom`

| Unterschied zu `research` | Wert | Begründung |
|--------------------------|------|------------|
| okf.enforce-frontmatter | `false` | Maximale Freiheit |
| lint.schedule | `on-demand` | User entscheidet |
| lint.checks | 2 (Links, FM) | Minimal |
| migration.auto-detect-sources | `false` | Manuell |

### 20.6 Preset: `internal-docs`

| Unterschied zu `research` | Wert | Begründung |
|--------------------------|------|------------|
| okf.allowed-types | `[Concept, Architecture, API Reference, Guide, Session Conclusion]` | Feste Typen statt frei — deckt gängige Software-Projekt-Doku ab |
| lint.schedule | `post-ingest` | Docs driften schnell mit dem Code — früh erkennen |
| lint.checks | 5 (Broken-Links, Missing-FM, Stale-Index, Orphaned-Pages, Duplicate-Concepts) | Fokus auf Doku-Drift, keine Widerspruchs-/Data-Gap-Checks wie bei Research |
| migration.auto-detect-sources | `true` | Kleine Software-Projekte haben fast immer ein bestehendes `docs/`-Verzeichnis |
| migration.clean-duplicates | `false` | Bestehende Docs nicht ungefragt zusammenführen |

### 20.7 Presets in `config/knowledge-presets.yaml`

```yaml
# Knowledge Engine Domain Presets
# Jedes Preset definiert bewährte Voreinstellungen für eine Domäne.
# Der User wählt ein Preset in der AdminUI → alle Felder werden gefüllt.
# Einzelne Werte können danach in project.yaml überschrieben werden.

research:
  label: "Research (Empfohlen)"
  description: "Papers, Studien, Methoden — maximale Vernetzung und Lint"
  concept-types:
    - Paper
    - Dataset
    - Method
    - Finding
    - Hypothesis
    - Comparison
    - Literature Review
    - Author
    - Institution
  lint-schedule: post-ingest
  lint-checks:
    - contradictions
    - stale-claims
    - orphan-pages
    - missing-concepts
    - broken-links
    - data-gaps
    - missing-frontmatter
    - index-staleness
  batch-mode: false
  file-back-results: true
  auto-detect-sources: true
  clean-duplicates: true

personal:
  label: "Personal"
  description: "Ziele, Gesundheit, Reflexionen — leichtgewichtig"
  concept-types:
    - Goal
    - Journal Entry
    - Health Record
    - Insight
    - Resource
    - Habit
    - Reflection
    - Book Note
  lint-schedule: on-demand
  lint-checks:
    - orphan-pages
    - missing-concepts
    - broken-links
    - missing-frontmatter
  batch-mode: false
  file-back-results: true
  auto-detect-sources: false
  clean-duplicates: false

business:
  label: "Business / Team"
  description: "Meetings, Entscheidungen, Metriken — Batch-Ingest"
  concept-types:
    - Meeting
    - Decision
    - Process
    - Metric
    - Customer Insight
    - Competitor
    - Strategy
    - OKR
  lint-schedule: post-ingest
  lint-checks:
    - contradictions
    - stale-claims
    - orphan-pages
    - missing-concepts
    - broken-links
    - missing-frontmatter
    - index-staleness
  batch-mode: true
  file-back-results: true
  auto-detect-sources: true
  clean-duplicates: true

book:
  label: "Book / Reading"
  description: "Kapitel, Figuren, Themen, Handlungsstränge"
  concept-types:
    - Chapter
    - Character
    - Theme
    - Plot Thread
    - Setting
    - Quote
    - Timeline Event
    - Relationship
  lint-schedule: on-demand
  lint-checks:
    - orphan-pages
    - missing-concepts
    - broken-links
    - missing-frontmatter
  batch-mode: false
  file-back-results: false
  auto-detect-sources: false
  clean-duplicates: false

custom:
  label: "Custom (Minimal)"
  description: "Keine Vorgaben — maximale Freiheit"
  concept-types:
    - Concept
    - Entity
    - Topic
    - Source Summary
    - Query Result
  lint-schedule: on-demand
  lint-checks:
    - broken-links
    - missing-frontmatter
  batch-mode: false
  file-back-results: true
  auto-detect-sources: false
  clean-duplicates: false

internal-docs:
  label: "Internal Docs"
  description: "Architektur, Guides, API-Referenzen, Session-Notizen — für kleine Software-Projekte"
  concept-types:
    - Concept
    - Architecture
    - API Reference
    - Guide
    - Session Conclusion
  lint-schedule: post-ingest
  lint-checks:
    - broken-links
    - missing-frontmatter
    - stale-index
    - orphaned-pages
    - duplicate-concepts
  batch-mode: true
  file-back-results: true
  auto-detect-sources: true
  clean-duplicates: false
```

---

## 21. Karpathy Compliance Verification (Gegen-Check)

> Exakter Abgleich gegen https://gist.githubusercontent.com/karpathy/442a6bf555914893e9891c11519de94f/raw

### 21.1 Vollständiger Anforderungs-Abgleich

| # | Karpathy-Zitat (Original) | Status | Implementierung | Anmerkung |
|---|--------------------------|--------|----------------|-----------|
| 1 | "incrementally builds and maintains a persistent wiki" | ✅ | `knowledge/wiki/` — LLM-owned, persistent, Git-committed | |
| 2 | "a structured, interlinked collection of markdown files" | ✅ | OKF Concepts + Standard-MD-Links | |
| 3 | "sits between you and the raw sources" | ✅ | Drei Schichten: `sources/` → `wiki/` → `schema.md` | |
| 4 | "the wiki is a persistent, compounding artifact" | ✅ | Jeder Ingest erweitert bestehende Seiten + neue Seiten | |
| 5 | "You never (or rarely) write the wiki yourself — the LLM writes and maintains all of it" | ✅ | `knowledge-*` Agenten ownen wiki/, User schreibt nie direkt | |
| 6 | "I have the LLM agent open on one side and Obsidian open on the other" | ✅ | Standard-MD + YAML-FM = 100% Obsidian-kompatibel | |
| 7 | "Obsidian is the IDE; the LLM is the programmer; the wiki is the codebase" | ✅ | Agent-owned Wiki, User browst in Obsidian/VS Code | |
| 8 | **"Raw sources"** — curated, immutable | ✅ | `knowledge/sources/` — Agenten lesen, modifizieren nie | |
| 9 | **"The wiki"** — LLM-generated markdown | ✅ | `knowledge/wiki/` — OKF Bundle | |
| 10 | **"The schema"** — "e.g. CLAUDE.md for Claude Code or AGENTS.md for Codex" | ✅ | `knowledge/schema.md` — Steuerungsdokument, analog CLAUDE.md | Schema-Datei ist dediziert, nicht in CLAUDE.md selbst |
| 11 | **Ingest:** "reads the source, discusses key takeaways" | ✅ | `knowledge-ingestor` Phase 2 (außer batch-mode) | |
| 12 | **Ingest:** "writes a summary page, updates the index" | ✅ | Source Summary + Indexer-Delegation | |
| 13 | **Ingest:** "updates relevant entity and concept pages" | ✅ | Entity/Concept/Topic Seiten-Updates | |
| 14 | **Ingest:** "A single source might touch 10-15 wiki pages" | ✅ | Touch-Radius 10-15 als Konvention | |
| 15 | **Ingest:** "batch-ingest many sources at once" | ✅ | `operations.ingest.batch-mode: true` | |
| 16 | **Query:** "searches for relevant pages, reads them, synthesizes" | ✅ | Index-First → Drill-in → Synthese | |
| 17 | **Query:** "good answers can be filed back into the wiki" | ✅ | `wiki/queries/` + `file-back-results: true` | |
| 18 | **Query:** "comparison table, slide deck (Marp), chart (matplotlib), canvas" | ⚡ | Querier kann verschiedene Output-Formate generieren; Marp/matplotlib als Hinweis in Schema | Nicht enforced, als Tipp |
| 19 | **Lint:** "contradictions between pages" | ✅ | Lint-Check #1 | |
| 20 | **Lint:** "stale claims that newer sources have superseded" | ✅ | Lint-Check #2 | |
| 21 | **Lint:** "orphan pages with no inbound links" | ✅ | Lint-Check #3 | |
| 22 | **Lint:** "important concepts mentioned but lacking their own page" | ✅ | Lint-Check #4 | |
| 23 | **Lint:** "missing cross-references" | ✅ | Lint-Check #5 (broken-links) | |
| 24 | **Lint:** "data gaps that could be filled with a web search" | ✅ | Lint-Check #6 (data-gaps) | |
| 25 | **index.md:** "catalog of everything, each page listed with link, one-line summary" | ✅ | OKF §6 + Karpathy-konformes Format | |
| 26 | **index.md:** "Organized by category" | ✅ | Entities, Concepts, Topics, Source Summaries, Queries | |
| 27 | **index.md:** "LLM reads the index first to find relevant pages" | ✅ | Querier: Index-First-Strategie | |
| 28 | **index.md:** "works surprisingly well at moderate scale (~100 sources, ~hundreds of pages)" | ✅ | Default: `search.engine: index-only` | |
| 29 | **log.md:** "append-only record of what happened and when" | ✅ | Indexer: append-only, parseable Format | |
| 30 | **log.md:** "if each entry starts with `## [2026-04-02] ingest \| Article Title`" | ✅ | Exakt dieses Format implementiert | |
| 31 | **log.md:** "`grep \"^## \\[\" log.md \| tail -5`" | ✅ | Parseable durch konsistentes Prefix | |
| 32 | **CLI tools / qmd:** "local search engine, BM25/vector search, CLI + MCP server" | ✅ | `search.engine: mcp-qmd`, MCP-Registry-Eintrag | |
| 33 | **Obsidian Web Clipper:** "converts web articles to markdown" | ✅ | Als Tipp in schema.md dokumentiert | |
| 34 | **Download images locally:** "set Attachment folder path to fixed directory" | ✅ | `sources/assets/` als Asset-Verzeichnis | |
| 35 | **Obsidian graph view:** "best way to see shape of wiki" | ✅ | Standard-MD-Links = Obsidian-Graph funktioniert | |
| 36 | **Marp:** "markdown-based slide deck format" | ⚡ | Als Output-Hint im Querier-Template | |
| 37 | **Dataview:** "runs queries over page frontmatter" | ✅ | OKF YAML-Frontmatter = Dataview-kompatibel | |
| 38 | **"wiki is just a git repo of markdown files"** | ✅ | Bundle = Teil des Git-Repos | |
| 39 | **"This document is intentionally abstract"** | ✅ | 6 Domänen-Presets + Zielrepo-Detection als Konkretisierung | |
| 40 | **Personal/Research/Book/Business/Competitive Analysis** | ✅ | 6 Domänen-Presets (research, personal, business, book, internal-docs, custom) | |

### 21.2 Compliance-Score: **39/40** (97.5%)

Das einzige Item ohne volle Implementierung:
- **#18 (Marp/matplotlib/Canvas Output-Formate):** Als Tipp im Schema dokumentiert, aber nicht enforced. Grund: Karpathy sagt explizit "intentionally abstract" — Output-Formate sind domänenabhängig.

---

## 22. OKF Compliance Verification (Gegen-Check)

> Exakter Abgleich gegen OKF Spec v0.1 Draft + Google Cloud Blog

### 22.1 Vollständiger Anforderungs-Abgleich

| # | OKF Requirement | Spec § | Status | Implementierung |
|---|----------------|--------|--------|----------------|
| 1 | Knowledge Bundle = Verzeichnisbaum | §3 | ✅ | `knowledge/wiki/` von sync.py |
| 2 | Distribution: Git (empfohlen) / Tarball / ZIP / Subdirectory | §3 | ✅ | Git-Repository (empfohlene Variante) |
| 3 | `index.md` reserviert: Directory Listing | §3.1 | ✅ | Generiert + gepflegt durch `knowledge-indexer` |
| 4 | `log.md` reserviert: Update History | §3.1 | ✅ | Generiert + append-only durch `knowledge-indexer` |
| 5 | `index.md` und `log.md` DÜRFEN NICHT als Concept verwendet werden | §3.1 | ✅ | Schema-Konvention + Ingestor-Regel |
| 6 | Concept = 1 UTF-8 encoded Markdown-Datei | §4 | ✅ | Standard in allen Templates |
| 7 | Concept = Frontmatter (YAML) + Body (Markdown) | §4 | ✅ | OKF-konformes Format |
| 8 | Concept ID = Pfad relativ zu Bundle-Root, ohne `.md` | §4 | ✅ | Schema-Konvention |
| 9 | `type` — **REQUIRED** | §4.1 | ✅ | Linter CRITICAL, Ingestor setzt immer |
| 10 | `title` — **RECOMMENDED** | §4.1 | ✅ | Ingestor setzt, Gardener ergänzt fehlende |
| 11 | `description` — **RECOMMENDED** | §4.1 | ✅ | Ingestor setzt, Gardener ergänzt fehlende |
| 12 | `resource` — **RECOMMENDED** (Unique URI for underlying asset) | §4.1 | ✅ | Ingestor setzt bei Assets, Gardener ergänzt | 
| 13 | `tags` — OPTIONAL (Kategorisierung) | §4.1 | ✅ | Ingestor setzt, Gardener harmonisiert |
| 14 | `timestamp` — OPTIONAL (ISO 8601) | §4.1 | ✅ | Gardener aktualisiert bei Änderung |
| 15 | Producer-defined key/value pairs erlaubt | §4.1 | ✅ | `sources`, `migrated_from` etc. |
| 16 | Types sind NICHT zentral registriert | §4.1 | ✅ | `okf.allowed-types: []` = frei wählbar |
| 17 | Consumers MÜSSEN unbekannte Types graceful behandeln | §4.1 | ✅ | Querier + Linter: graceful handling |
| 18 | Cross-References = Standard-Markdown-Links | §5 | ✅ | Ingestor + Gardener pflegen |
| 19 | Citations = Links zu externen Quellen | §5 | ✅ | Ingestor erstellt |
| 20 | Progressive Disclosure via `index.md` | §6 | ✅ | Querier: Index-First-Strategie |
| 21 | `index.md` an jeder Verzeichnisebene möglich | §6 | ✅ | Konzept unterstützt Sub-Indices |

### 22.2 Google Cloud Blog Best Practices

| # | Best Practice | Status | Implementierung |
|---|--------------|--------|----------------|
| 1 | Git-Centric Version Control ("metadata as code") | ✅ | Bundle = committed Git-Verzeichnis |
| 2 | Human-in-the-Loop Curation | ✅ | Ingest-Diskussion (außer batch-mode) |
| 3 | Progressive Disclosure via `index.md` | ✅ | Querier liest Index zuerst |
| 4 | Self-Explanatory Concept Types | ✅ | Domänen-Presets mit klaren Types |
| 5 | Explicit Graph Links (nicht nur Hierarchie) | ✅ | Cross-References durch Ingestor+Gardener |
| 6 | Enrichment Agent Pattern | ✅ | `knowledge-ingestor` = Enrichment Agent |
| 7 | Traversal Agent Pattern | ✅ | `knowledge-querier` = Traversal Agent |
| 8 | Living Wiki Pattern | ✅ | Persistent, compounding Wiki |
| 9 | Model-Agnostic Interoperability | ✅ | OKF = offenes Format, alle LLMs kompatibel |

### 22.3 Compliance-Score: **21/21 Spec + 9/9 Blog = 100%**

---

## 23. Google Referenz-Tooling & Ökosystem

> Google liefert mit OKF v0.1 auch Referenz-Implementierungen.
> Diese können als Inspirationsquelle und Kompatibilitätspartner dienen.

### 23.1 Google-eigenes Tooling

| Tool | Beschreibung | Relevanz für Knowledge Engine |
|------|-------------|-------------------------------|
| **Enrichment Agent** | Python/LLM-Pipeline: Scannt BigQuery, draftet OKF-Concepts, enriched via LLM | Unser `knowledge-ingestor` ist das Äquivalent |
| **Static HTML Visualizer** | Single-file Graph-Visualizer, Zero-Install, Privacy-first | Könnte als optionales Viz-Tool integriert werden |
| **Sample Bundles** | GA4 E-commerce, Stack Overflow, Bitcoin Public Datasets | Test-Bundles für Kompatibilitätstests |
| **Google Cloud Knowledge Catalog** | Cloud-Service der OKF-Bundles ingestiert und an AI-Agents serviert | Enterprise-Integrationspartner |

### 23.2 Kompatibilität mit Google Tooling

Da unsere Knowledge Engine **100% OKF-konforme Bundles** generiert:
- ✅ Google Static HTML Visualizer kann unsere Bundles direkt darstellen
- ✅ Google Enrichment Agent Output kann als Source in unser Wiki importiert werden
- ✅ Google Cloud Knowledge Catalog kann unsere Bundles ingestieren
- ✅ Unsere Bundles können mit Google Sample Bundles gemischt werden

### 23.3 Optionale Integration: Static HTML Visualizer

Könnte als optionaler Download-Link in `schema.md` referenziert werden:
```markdown
## Visualisierung

Nutze den [OKF Static HTML Visualizer](https://github.com/GoogleCloudPlatform/knowledge-catalog/tree/main/okf/viz)
für eine interaktive Graph-Darstellung des Knowledge Bundles.
```
