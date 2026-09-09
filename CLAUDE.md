# agent-meta

> Projektbeschreibung für Claude-Agenten. Diese Datei ist die **einzige Quelle**
> für projektspezifischen Kontext — Agenten lesen sie, statt eigenen Kontext zu haben.
>
> Generiert von agent-meta v1.0.0 — `2026-09-08`
>
> **Längenempfehlung:** 200–500 Zeilen optimal. Über 500 Zeilen → Detailwissen in
> `docs/ARCHITECTURE.md`, `docs/API.md` o.ä. auslagern und manuell verlinken.
> Agent-spezifisches Wissen → `.claude/3-project/<rolle>-ext.md` (Extension).
>
> **CLAUDE.md Hierarchie (Claude Code lädt in dieser Reihenfolge):**
> 1. `~/.claude/CLAUDE.md` — global, alle Projekte (~50 Zeilen max, persönliche Präferenzen)
> 2. `<projekt>/CLAUDE.md` — diese Datei, projektspezifisch (von agent-meta verwaltet)
> 3. `<ordner>/CLAUDE.md` — optional in Unterordnern (z.B. `src/backend/CLAUDE.md`)

---

## Eigene Notizen

Hier kannst du eigene, projektspezifische Notizen eintragen. Dieser Bereich wird von `agent-meta` nicht überschrieben!

---

## Projekt

**Name:** agent-meta
**Präfix:** am
**Plattform:** Python CLI (sync.py)
**Beschreibung:** Zentrales Meta-Repository für die Standardisierung und Wiederverwendung von Claude-Agenten-Rollen über alle Projekte hinweg.

> Struktur: siehe Verzeichnisstruktur im Repo (`ls`/`find`); deklarativ: `.meta-config/project.yaml` → `variables.PROJECT_STRUCTURE`.

> Runtime & Abhängigkeiten: siehe Projekt-Manifest (`pyproject.toml` / `requirements.txt` / `package.json` / `manifest.json`).

**Entry-Point:** `scripts/sync.py — Haupt-CLI für Agent-Generierung`

**Besondere Patterns:**
- Agent-Templates haben YAML-Frontmatter (name, version, description, tools)
- Platzhalter {{VARIABLE}} werden von sync.py substituiert
- Extensions (.claude/3-project/*-ext.md) werden vom Agenten zur Laufzeit gelesen
- Snippet-Dateien haben eigenes YAML-Frontmatter (snippet, version, language, runtime)


## Code-Konventionen

- Python: PEP 8, snake_case, klare Funktionsnamen
- Keine externen Python-Dependencies außer Stdlib
- Markdown-Dateien: GitHub Flavored Markdown
- YAML Frontmatter in allen Agent-Templates
- Provider-Unterschiede im Syncer-Code über Config-Keys/Capability-Flags ausdrücken, nie über `if provider == "Name"` (siehe `provider-agnostic`-Skill)


## Build & Development

```bash
# Build
python scripts/sync.py

# Tests
python3 scripts/sync.py --validate

# Dev-Stack starten
(kein Dev-Stack)

# Nach Änderungen neu laden
(kein Dev-Stack)
```

## Anforderungs-Kategorien

Kategorien für `docs/REQUIREMENTS.md`:

- Framework-Features (sync.py, neue Agenten-Rollen, Variablen)
- Agenten-Templates (Workflows, Sprach-Sektionen, Versionierung)
- Entwickler-Experience (Howto, Beispiele, Doku)



## Agenten-Konfiguration

<!-- agent-meta:managed-begin -->
<!-- Dieser Block wird von sync.py bei jedem sync automatisch aktualisiert. -->
<!-- Manuelle Änderungen hier werden überschrieben. -->

> **AI ROUTING:** Claude -> CLAUDE.md | Opencode, Gemini -> AGENTS.md

Generiert von agent-meta v1.0.0 — `2026-09-09`
DoD-Preset: **rapid-prototyping** | REQ-Traceability: false | Tests: false | Codebase-Overview: false | Security-Audit: false
> **Einstiegspunkt:** Starte mit dem `orchestrator`-Agenten für alle Entwicklungsaufgaben — Ausnahmen siehe Abschnitt »Orchestrator — Universal Router«.

## Knowledge Engine

Die Knowledge Engine ist aktiviert. Domäne: **internal-docs**.

**Bundle-Pfad:** `knowledge/`
| Pfad | Zweck |
|------|-------|
| `knowledge/schema.md` | Steuerungsdokument — Konventionen, Concept Types, Workflows |
| `knowledge/sources/` | Immutable Raw Sources — LLM liest, modifiziert NIEMALS |
| `knowledge/wiki/` | OKF Knowledge Bundle — LLM-owned, strukturiertes Wiki |
| `knowledge/wiki/index.md` | Content-Katalog aller Wiki-Seiten (OKF §6) |
| `knowledge/wiki/log.md` | Chronologisches Event-Log (OKF §7) |

### Knowledge-Agenten
- **Schema-Owner:** `knowledge-curator` verwaltet `knowledge/schema.md` und Concept-Type-Konventionen

### Knowledge-Workflows
- **Ingest:** Source in `knowledge/sources/` ablegen → `knowledge-ingestor` verarbeitet → Wiki aktualisiert
- **Query:** Frage stellen → `knowledge-querier` durchsucht Index → synthetisiert Antwort
- **Lint:** `knowledge-linter` prüft Wiki-Gesundheit (Widersprüche, Orphans, OKF-Compliance)
- **Migration:** `knowledge-migrator` räumt vorhandene Inhalte auf und migriert ins OKF-Format
- **Gardening:** `knowledge-gardener` pflegt Links, Tags, Typos, Timestamps
<!-- agent-meta:managed-end -->

**Singleton-Regel:** Es existiert genau EIN `orchestrator` pro Session — der vom `main_chat` gespawnte. Worker-Agents dürfen niemals `task(subagent_type="orchestrator", ...)` aufrufen. Verstoß = Deadlock / Routing-Konflikt.

---

## Sprachregeln

<!-- Die globale Rule .claude/rules/language.md (generiert von sync.py) deckt den Kern ab. -->
<!-- Hier nur projektspezifische Abweichungen eintragen — sonst leer lassen. -->

- `README.md` → **Englisch**
- Alle anderen Dokumente → **Deutsch**
- Code-Kommentare, Commit-Messages → **Englisch**
- Kommunikation mit dem Nutzer → **Deutsch**
