---
title: "Knowledge Log"
type: "Guide"
description: "Append-only change log of the knowledge bundle."
timestamp: "2026-07-27"
tags: ["changelog", "log"]
---

# Knowledge Log

> Append-only change log for the knowledge bundle. One entry per ingest/update/query operation.

## Format

```
YYYY-MM-DD HH:MM — <operation> — <summary>
```

## Entries

2026-07-24 00:00 — migrate — 82 Projektdokumente aus agent-meta (docs/, howto/, .claude/rules/, ideation) nach knowledge/wiki/{concepts,entities,topics,sources}/ migriert, OKF-Frontmatter ergänzt.
2026-07-24 00:00 — index — index.md mit vollständigem Content-Katalog (32 Concepts, 7 Entities, 41 Topics, 6 Sources) aufgebaut.
2026-07-25 19:38 — ingest/update — Integration des ReqogniLoom MCP-Servers, Unterstützung für projektspezifische .meta-config/mcp-registry.yaml in mcp.py, sowie Korrektur der Honcho MCP Authentication Headers.
2026-07-27 11:16 — ingest/create — 11 OKF-konforme Konzept- und Architektur-Dokumente zu den 10 Kernprinzipien des agent-meta Frameworks in knowledge/wiki/concepts/ erstellt und in index.md registriert.
2026-07-27 11:16 — ingest — Framework-Prinzipien der agent-meta Architektur (concepts/framework-principles.md) in Knowledge Index & Log aufgenommen.
2026-07-27 11:16 — migrate — 11 Framework-Konzepte aus AGENTS.md, CLAUDE.md und rules/1-generic/ nach knowledge/wiki/concepts/ extrahiert (A2A Gates, Branch-Guard, Commit-Konventionen, DoD, Issue-Lifecycle, Lifecycle-Tasks & Hooks, Language Matrix, Provider-Agnostic Policy, Session Conclusion, Instruction Bleed Risk, Agent Bootstrap Registration) und index.md aktualisiert.
2026-07-27 11:18 — index/update — Deterministische Indexierung aller neu erstellten Framework-Prinzipien und Kernkonzepte in index.md abgeschlossen. Content-Katalog umfasst nun 54 Concepts, 7 Entities, 40 Topics und 6 Sources (107 OKF-Dokumente).
2026-08-10 00:00 — plan — Implementation plan for Issue #456 (Admin UI remote access: bind-host, token auth, host allowlist) created at knowledge/wiki/plans/am-issue-456-remote-admin-auth.md. 8 ordered steps across admin-server.py and project-config.schema.json. Branch: fix/sync-drift-and-external-pin.