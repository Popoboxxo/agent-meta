# Prompt-Engineering Report: `_wf-sync-interface.md`

## 1. Ausgangslage & Analyse
Das Dokument `_wf-sync-interface.md` dient als technische Referenz für das `sync.py`-Skript. Es umfasst aktuell 58 Zeilen und nutzt erzählenden Fließtext, simulierte Konsolenausgaben und Markdown-Tabellen.

**Identifizierte Ineffizienzen:**
- **Tabellen-Overhead:** Die Modulstruktur ist als Tabelle definiert. Die Trennzeichen (Pipes `|` und Bindestriche `-`) erzeugen überflüssige Tokens, ohne für das LLM einen semantischen Mehrwert zu bieten. Tabellen sind oft teurer als dichte Listen.
- **Konsolen-Simulation:** Der Abschnitt `sync.log verstehen` ahmt Konsolen-Output nach (inkl. Pfeilen wie `← Agent neu generiert`). Das ist visuell gut für Menschen, aber token-ineffizient für LLMs.
- **Füllwörter & Prosa:** Formulierungen wie "Sucht in dieser Reihenfolge (wenn `--config` weggelassen):" lassen sich prägnanter formulieren (z. B. "Fallback-Reihenfolge").

## 2. Optimierungsvorschläge (nach Prompt-Engineer Best Practices)

- **Structured Prompting & Komprimierung:** Überführung der Markdown-Tabelle in eine dichte Key-Value-Liste. LLMs können "Key: Value"-Muster sehr effizient verarbeiten.
- **Latency & Token Reduction:** Zusammenfassen der Flags in kompaktere Beschreibungen, Reduktion von Whitespace, Entfernen von Füllwörtern.
- **High-Attention Zones:** Wichtige Anweisungen (wie "`sync.py` ist nur Dispatcher..." oder "Warnungen sofort beheben!") wurden nach oben an den Anfang ihrer jeweiligen Blöcke gesetzt, da Modelle am Anfang und Ende des Kontexts am stärksten aufpassen.
- **Gruppierung (Intent Classification):** Die Log-Status-Meldungen und Module wurden logisch gruppiert (z. B. `io`/`log` kombiniert), um Redundanzen aufzulösen.

## 3. Optimierte Version (Vorschlag)

Hier ist die token-optimierte Version, die den Inhalt auf ~25 Zeilen komprimiert, ohne Informationsverlust. Sie ist direkt "Drop-in" fähig:

```markdown
# sync.py — Referenz

## Config-Auto-Detection
Fallback-Reihenfolge (falls `--config` fehlt): `.meta-config/project.yaml` > `agent-meta.config.yaml` (Legacy) > `agent-meta.config.json` (Legacy).

## Flags (`py scripts/sync.py [FLAG]`)
(ohne)                        # Standard-Sync
--init                        # Ersteinrichtung (CLAUDE.md, settings.json, gitignore)
--dry-run                     # Preview der Änderungen
--only-variables              # Nur {{VAR}}-Platzhalter ersetzen
--create-ext <role|all>       # Extension(s) anlegen
--update-ext                  # Managed blocks aktualisieren
--create-rule <thema>         # Projekt-eigene Rule anlegen
--add-skill <url> --skill-name <n> --source <path> --role <r>
--fill-defaults               # Fehlende project.yaml Felder eintragen

## Log-Status (Warnungen sofort beheben!)
- `[WRITE]/[COPY]/[UPDATE]`: Neu generiert, kopiert, managed block aktualisiert.
- `[SKIP]/[DELETE]`: Inaktiv übersprungen, veraltet entfernt.
- `[WARN]/[INFO]`: Fehlende Variablen/Config, Infomeldungen.

## Modulstruktur (`scripts/lib/`)
`sync.py` ist nur Dispatcher. Bei Änderungen zuständiges Modul prüfen:
- **`agents`**: Composition (extends/patches), Frontmatter, sync_agents
- **`config`**: load_config, build_variables, substitute(), fill_defaults
- **`context`**: init_claude_md, sync_context, gitignore
- **`dod`**: load_presets, resolve_dod
- **`extensions`**: create_extension, update_extensions
- **`hooks`/`rules`**: sync/create hooks & rules
- **`io`/`log`**: YAML/JSON-Loader, SyncLog
- **`platform`/`providers`**: Config laden, substitute/resolve
- **`roles`**: load_roles_config, build_role_map, Resolver
- **`skills`**: External Skills (load, check_pinned, sync, add)
```

## Fazit
Durch den Wechsel von Markdown-Tabellen und narrativen Elementen hin zu dichten Listen und komprimierten Beschreibungen wird die Token-Anzahl signifikant verringert. Die Verarbeitungszeit und Latenz des Modells sinkt, ohne dass fachliche Nuancen des `agent-meta` Frameworks verloren gehen.
