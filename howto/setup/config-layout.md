# Config-Layout — Drei Ebenen, klare Zuständigkeiten

agent-meta trennt Konfiguration in drei unabhängige Ebenen.
Jede Ebene hat eine klare Zuständigkeit und einen eigenen Eigentümer.

---

## Übersicht

```
Zielprojekt/
├── .agent-meta/              ← agent-meta Submodul (NICHT anfassen)
│   └── config/               ← Framework-Configs — Eigentümer: agent-meta
│       ├── role-defaults.yaml        Modell, Memory, permissionMode pro Rolle
│       ├── dod-presets.yaml          DoD-Qualitätsprofile (full, standard, rapid-prototyping)
│       ├── ai-providers.yaml         Provider-Einstellungen (Claude, Gemini, Continue)
│       ├── skills-registry.yaml      Externe Skills (approved/pinned)
│       └── project-config.schema.json  JSON Schema für project.yaml
│
├── .meta-config/             ← Projekt-Config — Eigentümer: Dein Projekt ✅
│   └── project.yaml          ← Hier arbeitest du: Rollen, Variablen, Plattform, Provider
│
└── .claude/                  ← Generierter Output — nicht manuell bearbeiten
    ├── agents/               ← Von sync.py generiert
    ├── rules/                ← Von sync.py kopiert
    ├── hooks/                ← Von sync.py kopiert
    ├── platform-config.yaml  ← Plattform-Werte ({{platform.*}}-Overrides)
    └── skills/               ← Kopierte Skill-Dateien
```

---

## Ebene 1: Framework-Configs — `.agent-meta/config/`

**Eigentümer:** agent-meta (Git Submodul)
**Versioniert:** Mit agent-meta zusammen (via `git checkout v<version>`)
**Editierbar:** Nein — wird bei jedem Submodul-Update überschrieben

Diese Dateien definieren das Framework-Verhalten. Sie werden von `sync.py` gelesen
aber **nie** vom Projekt-Entwickler bearbeitet.

| Datei | Inhalt |
|-------|--------|
| `role-defaults.yaml` | Welches Modell, Memory-Scope und permissionMode hat jede Rolle standardmäßig |
| `dod-presets.yaml` | Vordefinierte DoD-Profile: `full`, `standard`, `rapid-prototyping` |
| `ai-providers.yaml` | Welche Provider unterstützt werden, welche Verzeichnisse sie nutzen |
| `skills-registry.yaml` | Externe Skills: Repos, pinned Commits, `approved: true/false` |
| `project-config.schema.json` | JSON Schema für Validierung von `.meta-config/project.yaml` |

**Änderungen** an Framework-Configs → in agent-meta vornehmen → neue Version taggen →
Projekte via `git checkout v<neue-version>` upgraden.

---

## Ebene 2: Projekt-Config — `.meta-config/project.yaml`

**Eigentümer:** Dein Projekt
**Versioniert:** Im Projekt-Repo (committen!)
**Editierbar:** Ja — das ist deine Hauptkonfigurationsdatei

Diese Datei definiert dein Projekt. Sie steuert:
- Welche Agenten-Rollen generiert werden (`roles`)
- Welche Variablen in die Templates injiziert werden (`variables`)
- Welche Provider aktiv sind (`ai-providers`)
- Welche externen Skills aktiviert sind (`external-skills`)
- Welches DoD-Profil gilt (`dod-preset`)

```yaml
# .meta-config/project.yaml
agent-meta-version: 0.25.0
ai-providers:
  - Claude
dod-preset: standard
roles:
  - orchestrator
  - developer
  - git
variables:
  PROJECT_NAME: mein-projekt
  BUILD_COMMAND: bun run build
  # ...
```

**Unabhängig von:**
- Provider-Verzeichnissen (kein `.claude/`, kein `.gemini/` im Pfad)
- Submodul-Verzeichnissen (kein `.agent-meta/` im Pfad)
- Git-Konflikten beim Submodul-Update

---

## Ebene 3: Platform-Config — `.claude/platform-config.yaml`

**Eigentümer:** Dein Projekt
**Versioniert:** Im Projekt-Repo
**Editierbar:** Ja — für plattformspezifische Werte

Nur relevant wenn `platforms: ["homeassistant"]` oder ähnliches in `project.yaml` gesetzt ist.
Überschreibt `{{platform.*}}`-Platzhalter aus den Platform-Defaults.

Siehe [platform-config.md](platform-config.md) für Details.

---

## Migration von alten Config-Pfaden

Ältere Projekte haben `agent-meta.config.yaml` direkt im Projekt-Root.

```bash
py .agent-meta/scripts/migrate-config.py --to-meta-config
```

Das Skript:
1. Erkennt `agent-meta.config.yaml` im Projekt-Root
2. Legt `.meta-config/` an
3. Benennt die Datei um zu `.meta-config/project.yaml`
4. Gibt Hinweise zu weiteren Cleanup-Schritten

---

## Warum diese Trennung?

**Problem vorher:** `agent-meta.config.yaml` lag im Projekt-Root — neben `.agent-meta/` (Submodul) und `.claude/` (Claude-spezifisch). Unklare Zuständigkeit.

**Problem mit `.claude/project.yaml`:** Koppelt die Config an einen konkreten LLM-Provider. Beim Wechsel zu Gemini oder Continue muss der Pfad überall angepasst werden.

**Problem mit `.agent-meta/project.yaml`:** Der Submodul-Ordner gehört dem Framework. Ein `git submodule update` könnte Projekt-Config überschreiben.

**Lösung:** `.meta-config/` ist ein eigenständiges Verzeichnis, das:
- Keinem Provider gehört
- Nicht Teil des Submoduls ist
- Klar signalisiert: "Hier konfigurierst du agent-meta für dieses Projekt"
