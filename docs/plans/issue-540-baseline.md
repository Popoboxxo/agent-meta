# Issue #540 — Context-Baseline (Phase A2)

> Vor-Komprimierung-Messung als Referenz für Phase D2 (Vorher/Nachher-Report).
> Gemessen mit `python3 scripts/measure_context.py` (Tokens approximiert als Bytes/4).

## Messung

| Metadatum | Wert |
|---|---|
| Datum | 2026-08-25 |
| Commit | `1538c887541a59122b22ccfc11dbbaa88882d512` (`feat/context-compression`) |
| Skript | `scripts/measure_context.py` |

| Datei | Zeilen | Bytes | Tokens (~) |
|---|---:|---:|---:|
| CLAUDE.md | 151 | 5437 | 1359 |
| AGENTS.md | 1082 | 44004 | 11001 |
| MAMMOUTH.md | 173 | 10378 | 2594 |
| **TOTAL** | **1406** | **59819** | **14954** |

Nicht vorhandene Provider-Contextfiles (`.continue/rules/project-context.md`, `.github/copilot/COPILOT.md`) werden vom Skript übersprungen. GEMINI.md existiert in diesem Repo nicht — Gemini teilt sich AGENTS.md.

## AGENTS.md Sektions-Gliederung (Ist)

Zeilenbereiche zum Vergleich nach Phase B (Details und Klassifizierung: `docs/guides/context-block-inventory.md`):

| Bereich | Zeilen | Quelle | Kategorie |
|---|---|---|---|
| Z1–79 Projekt-Overviews | ~79 | `templates/context/partials/project-metadata.md` | OVERVIEW/METADATEN |
| Z81–87 Managed-Header (ROUTING/ENTRY/Version) | ~7 | `templates/context/partials/header.md` | METADATEN |
| Z90–239 Embedded Rules (14 Generic-Rules) | ~150 | `rules/1-generic/*.md` via `rules-embedded.md` | INSTRUKTION |
| Z240–397 Platform-Rules (Schichten, Conventions, Provider-Agnostic) | ~158 | `rules/2-platform/agent-meta-*.md` | gemischt (siehe Inventory) |
| Z398–513 sync.py Interface | ~116 | `rules/2-platform/agent-meta-sync-interface.md` | OVERVIEW |
| Z514–730 MCP-Sektionen (4 Server) | ~217 | generiert aus `config/mcp-registry.yaml` (`scripts/lib/mcp.py`) | INSTRUKTION + OVERVIEW + METADATEN |
| Z731–758 External Tool graphify | ~28 | generiert aus `config/external-tools-registry.yaml` | INSTRUKTION + METADATEN |
| Z760–871 Agent Directory (53 Einträge) | ~112 | `agents-location.md` + `agents-table.md` | OVERVIEW |
| Z873–894 Knowledge Engine | ~22 | `knowledge-engine-hints.md` | METADATEN/OVERVIEW |
| Z902–1025 Bootstrap-Block (Gemini) | ~124 | `scripts/lib/bootstrap.py` (`generate_gemini_bootstrap_instructions`) | OVERVIEW (Kern-Instruktion erhalten) |
| Z1028–1082 RTK/graphify-Fremdinjektionen | ~55 | Drittanbieter-Installer (nicht sync.py) | außerhalb Scope |

## Plan-Soll (Referenz)

| Metrik | Ist | Soll |
|---|---:|---|
| AGENTS.md Zeilen | 1082 | <200 inkl. B6; <400 Zwischenziel ohne B6 |
| Token-Last pro Run (AGENTS.md) | ~11k | <2k |
