---
name: "Commands Section"
version: 1.0.2
---
## Commands

Slash-Commands werden aus drei Quell-Schichten in das Command-Verzeichnis des Providers synchronisiert. Pfadbasen: `commands/`, `config/` relativ zu agent-meta (im Zielprojekt `.agent-meta/`); Zielordner relativ zum Projekt. Bei gleichem Namen gewinnt die spätere Schicht.

| Schicht (Quelle) | Zweck |
|---|---|
| `commands/0-external/` | Commands aus External Skills |
| `commands/1-generic/` | Generische agent-meta-Commands |
| `commands/2-platform/` | Plattformspezifisch (Präfix `<platform>-` wird gestrippt) |

Für alle Schichten gilt:

- **Ziel:** `commands_dir` des Providers (`config/ai-providers.yaml`).
- **Format:** Format/Endung via `commands_format`/`commands_ext`.
- **Index:** `.agent-meta-managed` je Zielordner (Continue: `.agent-meta-commands-managed`, Key `commands_managed_index`).
- **Stale-Cleanup:** entfernte Commands werden beim Sync gelöscht (nur indexierte Dateien).
- **Gate:** nur Provider mit Capability `commands: true` (`config/provider-capabilities.yaml`) erhalten Commands.
- **Projekteigene Commands:** nicht-indexierte Dateien in jedem `commands_dir` bleiben unangetastet. Bei Namenskollision wird die Projektdatei ohne Backup durch den agent-meta-Command überschrieben. Anlegen (nur Claude): `python3 .agent-meta/scripts/sync.py --create-command <name>`.
