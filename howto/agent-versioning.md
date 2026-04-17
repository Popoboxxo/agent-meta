# Agent-Versionierung

## Warum?

Jeder generische und plattformspezifische Agent trägt eine eigene `version:`-Nummer
im Frontmatter. Das ermöglicht:

- **Überblick** — Auf einen Blick sehen, welcher Stand in einem Projekt aktiv ist.
- **Ableitungs-Traceability** — Plattform-Agenten dokumentieren explizit, von welcher
  Version des Generic-Agenten sie abgeleitet wurden (`based-on:`).
- **Sync-Transparenz** — Generierte Dateien in `.claude/agents/` tragen `generated-from:`
  mit Quelle + Version, sodass immer klar ist, wann ein Sync fällig ist.

---

## Frontmatter-Felder

### 1-generic Agenten

```yaml
---
name: template-<rolle>
version: "1.2.0"
description: "..."
tools:
  - ...
---
```

| Feld | Pflicht | Bedeutung |
|------|---------|-----------|
| `version` | ✅ | Semantische Version dieses Templates |

### 2-platform Agenten

```yaml
---
name: <plattform>-<rolle>
version: "1.1.0"
based-on: "1-generic/<rolle>.md@1.0.0"
description: "..."
tools:
  - ...
---
```

| Feld | Pflicht | Bedeutung |
|------|---------|-----------|
| `version` | ✅ | Semantische Version dieses Plattform-Agenten |
| `based-on` | ✅ | Quelle + Version des Generic-Agenten, von dem abgeleitet |

### Generierte Agenten in `.claude/agents/`

```yaml
---
name: <rolle>
version: "1.2.0"
based-on: "1-generic/<rolle>.md@1.0.0"   # nur bei Plattform-Agenten
generated-from: "2-platform/<plattform>-<rolle>.md@1.1.0"
description: "Agent für <Projektname>."
tools:
  - ...
---
```

| Feld | Gesetzt durch | Bedeutung |
|------|--------------|-----------|
| `version` | Template (erhalten) | Version des Quell-Templates |
| `based-on` | Template (erhalten) | Generic-Basis (nur bei Plattform-Agenten) |
| `generated-from` | `sync.py` automatisch | Welche Quelldatei + Version diesen Agent erzeugt hat |

> `version` und `based-on` werden von `sync.py` **nicht verändert** — sie kommen
> direkt aus dem Template. `generated-from` wird bei jedem Sync automatisch gesetzt.

---

## Versionierungsregeln

Agenten folgen [Semantic Versioning](https://semver.org/):

| Änderungstyp | Version |
|---|---|
| Neues Pflichtfeld, umbenannte Variable, geändertes Verhalten | **Major** (`X.0.0`) |
| Neue optionale Sektion, neues Feature, erweiterter Scope | **Minor** (`x.Y.0`) |
| Textverbesserung, Klarstellung, Tippfehler | **Patch** (`x.y.Z`) |

**Wichtig:** Die Agenten-Version ist **unabhängig** von der `agent-meta` Repository-Version
(in `VERSION`). Eine neue agent-meta-Version bedeutet nicht automatisch, dass alle
Agenten-Versionen hochgezogen werden — nur geänderte Agenten bekommen eine neue Version.

---

## Wann `based-on` aktualisieren?

Wenn ein Generic-Agent (`1-generic/`) eine neue Version bekommt und ein davon
abhängiger Plattform-Agent (`2-platform/`) inhaltlich angepasst wird:

1. Generic-Agent-Version erhöhen (z.B. `1.0.0` → `1.1.0`)
2. Plattform-Agent inhaltlich anpassen
3. `based-on` im Plattform-Agent auf neue Generic-Version setzen
4. Plattform-Agent-Version erhöhen
5. Projekte neu syncen

Wenn der Plattform-Agent **keine** inhaltlichen Änderungen braucht (Generic-Änderung
ist nicht relevant für die Plattform), kann `based-on` auf der alten Version bleiben —
das ist bewusst und signalisiert: "Wir haben geprüft, keine Anpassung nötig."

---

## Schnellcheck: Ist mein Projekt aktuell?

In einem Zielprojekt in `.claude/agents/<rolle>.md` das Frontmatter prüfen:

```yaml
generated-from: "1-generic/developer.md@1.0.0"
```

Dann in agent-meta `agents/1-generic/developer.md` die aktuelle Version prüfen.
Stimmt sie nicht überein → Sync ausführen:

```bash
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml
```
