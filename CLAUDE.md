# agent-meta

> Projektbeschreibung für Claude-Agenten. Diese Datei ist die **einzige Quelle**
> für projektspezifischen Kontext — Agenten lesen sie, statt eigenen Kontext zu haben.
>
> Generiert von agent-meta v0.100.0 — `2026-08-25`
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

> Tech-Stack, Architektur & Build-Befehle: discoverable via Repo (Manifeste, CI-Configs).

## Code-Konventionen

- Python: PEP 8, snake_case, klare Funktionsnamen
- Keine externen Python-Dependencies außer Stdlib
- Markdown-Dateien: GitHub Flavored Markdown
- YAML Frontmatter in allen Agent-Templates


## Anforderungs-Kategorien

Kategorien für `docs/REQUIREMENTS.md`:

- Framework-Features (sync.py, neue Agenten-Rollen, Variablen)
- Agenten-Templates (Workflows, Sprach-Sektionen, Versionierung)
- Entwickler-Experience (Howto, Beispiele, Doku)



## Agenten-Konfiguration

<!-- agent-meta:managed-begin -->
<!-- Dieser Block wird von sync.py bei jedem sync automatisch aktualisiert. -->
<!-- Manuelle Änderungen hier werden überschrieben. -->

> **AI ROUTING:** Claude -> CLAUDE.md | Opencode, Gemini -> AGENTS.md | Mammouth -> MAMMOUTH.md

Generiert von agent-meta v0.100.0 — `2026-08-25`
DoD-Preset: **rapid-prototyping** | REQ-Traceability: false | Tests: false | Codebase-Overview: false | Security-Audit: false
> **Einstiegspunkt:** Du bist im `main-chat` Modus. Du agierst direkt als Router und Worker (siehe `use-orchestrator.md`).

## Knowledge Engine

Die Knowledge Engine ist aktiviert. Domäne: **personal**.

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
