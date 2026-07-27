---
type: "Concept"
title: "Konzept: Provider-Agnostic Policy & Smart Context Regeneration"
description: "Design-Prinzip zur Trennung generischer Agenten-Templates von Anbieterspezifika sowie automatisierte Kontext-Regenerierung mit Drift-Erkennung via context-hashes.json und sync.py --check."
tags: [concept, architecture, multi-provider, status:active]
timestamp: "2026-07-27"
resource: "../../rules/1-generic/provider-agnostic.md"
migrated_from: "rules/1-generic/provider-agnostic.md"
---
# Konzept: Provider-Agnostic Policy & Smart Context Regeneration

> Status: **Umgesetzt — aktiv**  
> Verwandt: [Layer Model](architecture-layer-model.md), [CLI Reference: sync.py](../entities/cli-reference.md)  
> Betroffen: `rules/1-generic/provider-agnostic.md`, `scripts/sync.py`, `.meta-config/context-hashes.json`  

---

## 1. Provider-Agnostic Policy

Das Meta-Repository `agent-meta` unterstützt vielfältige AI-Provider (Claude Code, Gemini/Antigravity, Opencode, Mammouth, Continue, GitHub Copilot).

**Die Provider-Agnostic Policy besagt:**
- Alle Agenten-Templates in `agents/1-generic/` sowie Regeln in `rules/1-generic/` müssen vollkommen anbieterneutral verfasst sein.
- Es dürfen keine spezifischen System-Prompts, Tool-Namen oder LLM-Eigenheiten von Claude, Gemini etc. in generischen Dateien hartcodiert werden.
- Anbieterspezifische Anpassungen gehören ausschließlich in `2-platform/` oder werden zur Build-Zeit via `sync.py` injiziert.

---

## 2. Multi-Provider AI Routing & Context Lifecycle

`sync.py` verwaltet den Lebenszyklus der anbieterspezifischen Einstiegsdokumente:
- `CLAUDE.md` $\rightarrow$ Claude Code Einstiegspunkt
- `AGENTS.md` $\rightarrow$ Opencode & Gemini Einstiegspunkt
- `MAMMOUTH.md` $\rightarrow$ Mammouth Code Einstiegspunkt
- `.continue/config.yaml` $\rightarrow$ Continue-Konfiguration

---

## 3. Smart Context Regeneration & Drift-Erkennung

Um Drift zwischen Konfigurationsdateien (`.meta-config/project.yaml`) und den generierten Provider-Dateien zu verhindern, bietet `sync.py` zwei Mechanismen:

```
                  .meta-config/project.yaml
                             │
                             ▼
                    python scripts/sync.py
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   context-hashes.json               --check Flag (CI Mode)
  (Drift-Erkennung via SHA256)      (Prüft Status ohne zu schreiben,
                                     Exit-Code 1 bei Drift)
```

### `context-hashes.json` (Sidecar-Datei)
- Speichert SHA-256 Hashes aller generierten verwalteten Blöcke.
- Erkennt, ob Entwickler oder LLMs generierte Dateien manuell bearbeitet haben.
- Bei erkanntem Drift legt `sync.py` automatisch ein Backup an (z.B. `.CLAUDE.md.sync-backup-<timestamp>`) und benachrichtigt den Nutzer.

### `--check` Flag (CI-Mode)
Wird im Continuous Integration Server genutzt:
```bash
python scripts/sync.py --check
```
Gibt Exit Code `0` zurück, wenn alle Provider-Dateien aktuell sind, andernfalls Exit Code `1`. Verhindert das Mergen veralteter Kontext-Dateien.