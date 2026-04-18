# External Skills — Vollständige Anleitung

External Skills sind spezialisierte Agenten aus Drittrepos — hochspezialisiertes Wissen
(z.B. 3D-Druck, CAD, spezifische Plattform-Expertise) das nicht in generische Agenten gehört.

---

## Konzept

```
┌─────────────────────────────────────────────────────────────────────┐
│                        SKILL-ÖKOSYSTEM                              │
│                                                                     │
│   Drittrepo (GitHub)                                                │
│   └── plugins/my-skill/                                             │
│         ├── SKILL.md          ← Skill-Einstiegsdatei               │
│         └── reference.md      ← Zusatzdokumente                    │
│                   │                                                 │
│                   │  git submodule add                              │
│                   ▼                                                 │
│   agent-meta/                                                       │
│   ├── external/my-skills-repo/  ← gepinnter Commit                 │
│   └── config/skills-registry.yaml                                  │
│         ├── repos: { my-skills-repo: { pinned_commit } }           │
│         └── skills: { my-skill: { approved: true/false } }         │
│                   │                                                 │
│                   │  sync.py (Two-Gate-Check)                       │
│                   │  Gate 1: approved: true  (Meta-Freigabe)        │
│                   │  Gate 2: enabled: true   (Projekt-Opt-in)       │
│                   ▼                                                 │
│   Zielprojekt/                                                      │
│   ├── .claude/agents/<role>.md    ← generierter Wrapper-Agent      │
│   └── .claude/skills/my-skill/   ← kopierte Skill-Dateien          │
│         ├── SKILL.md                                                │
│         └── reference.md                                           │
└─────────────────────────────────────────────────────────────────────┘
```

### Zwei-Gate-Prinzip

```
config/skills-registry.yaml          .meta-config/project.yaml
────────────────────────────         ──────────────────────────────
approved: true                  UND  "external-skills": {
  ↑                                    "my-skill": { "enabled": true }
  Meta-Maintainer-Gate                }
  "Skill ist geprüft &                 ↑
   sicher nutzbar"                     Projekt-Gate
                                       "Dieses Projekt will den Skill"
```

**Nur wenn beide Gates `true` → generiert sync.py den Wrapper-Agent.**

---

## Rollen & Verantwortlichkeiten

| Rolle | Aufgabe |
|-------|---------|
| **Skill-Autor** | Erstellt Skill-Repo + SKILL.md, stellt es öffentlich bereit |
| **Meta-Maintainer** | Registriert Skill via `--add-skill`, prüft Qualität, setzt `approved: true` |
| **Projekt-Entwickler** | Aktiviert gewünschte Skills in `.meta-config/project.yaml` |

---

## Lifecycle-Übersicht

```
[Skill-Autor]           [Meta-Maintainer]              [Projekt-Entwickler]
      │                        │                               │
      │  Skill-Repo            │                               │
      │  erstellen ────────────▶                               │
      │                        │  --add-skill ausführen        │
      │                        │  (registriert Submodul        │
      │                        │   + Config-Eintrag)           │
      │                        │                               │
      │                        │  Skill prüfen                 │
      │                        │  approved: true setzen        │
      │                        │  agent-meta pushen            │
      │                        │                               │
      │                        │  ──────────────────────────▶  │
      │                        │  Skill ist verfügbar          │
      │                        │                               │  .meta-config/project.yaml:
      │                        │                               │  "external-skills": {
      │                        │                               │    "my-skill": { "enabled": true }
      │                        │                               │  }
      │                        │                               │
      │                        │                               │  sync.py ausführen
      │                        │                               │  → .claude/agents/my-role.md
      │                        │                               │  → .claude/skills/my-skill/
```

---

## Schritt 1: Verfügbare Skills entdecken

Welche Skills im gebundenen agent-meta verfügbar und freigegeben sind:

```bash
cat .agent-meta/config/skills-registry.yaml
```

Alle Einträge mit `"approved": true` können im Projekt aktiviert werden.

**Als AI-Assistent:** Lies die Datei und zeige dem User eine übersichtliche Liste:
- Skill-Name + Beschreibung
- Repo + gepinnter Commit
- Ob im Projekt bereits aktiviert

---

## Schritt 2: Skill im Projekt aktivieren

In `.meta-config/project.yaml` des Projekts ergänzen:

```json
{
  "external-skills": {
    "home-organization": { "enabled": true },
    "opengrid-openscad": { "enabled": false }
  }
}
```

Dann sync ausführen:

```bash
py .agent-meta/scripts/sync.py 
```

**Ergebnis:**
- `.claude/agents/home-organization-specialist.md` — generierter Wrapper-Agent
- `.claude/skills/home-organization/` — kopierte Skill-Dateien für lazy Read-Zugriff

**Skill-Dateien committen:**

```bash
git add .claude/agents/ .claude/skills/ .meta-config/project.yaml
```

```bash
git commit -m "feat: activate home-organization skill"
```

---

## Schritt 3: Skill deaktivieren

`enabled: false` setzen oder den Eintrag entfernen:

```json
"external-skills": {
  "home-organization": { "enabled": false }
}
```

Beim nächsten sync:
- `[INFO]` im Log: skill not enabled — skipping
- `.claude/agents/<role>.md` wird **gelöscht** (stale cleanup)
- `.claude/skills/<skill-name>/` bleibt erhalten (keine Cleanup-Logik für Skills-Dir)

---

## Für Meta-Maintainer: Neues Skill-Repo registrieren

### Was ist ein valides Skill-Repo?

Ein externes Repo muss mindestens enthalten:

```
my-skills-repo/
  path/to/skill/
    SKILL.md          ← Pflicht: Einstiegsdatei mit Skill-Beschreibung
    reference.md      ← Optional: Zusatzdokumente
```

**Anforderungen an `SKILL.md`:**
- Beschreibt den Skill klar und präzise
- Enthält konkrete Anweisungen/Wissen das der Agent nutzen soll
- Optional: YAML Frontmatter mit `name`, `version`, `description`

### `--add-skill` ausführen

```bash
py .agent-meta/scripts/sync.py \
  --add-skill https://github.com/owner/skill-repo \
  --skill-name my-skill \
  --source path/within/repo \
  --role my-specialist
```

**Parameter:**

| Parameter | Bedeutung | Beispiel |
|-----------|-----------|---------|
| `--add-skill` | GitHub/GitLab URL des Skill-Repos | `https://github.com/racurry/neat-little-package` |
| `--skill-name` | Eindeutiger Bezeichner für den Skill (kebab-case) | `home-organization` |
| `--source` | Pfad zur Skill-Verzeichnis **innerhalb** des Repos | `plugins/spirograph/skills/home-organization` |
| `--role` | Name des generierten Agenten (kebab-case) | `home-organization-specialist` |
| `--entry` | Einstiegsdatei im Skill-Verzeichnis (Standard: `SKILL.md`) | `SKILL.md` |

**Was `--add-skill` tut:**
1. Führt `git submodule add <repo-url> external/<repo-name>` aus
2. Pinnt den aktuellen Commit automatisch in `pinned_commit`
3. Schreibt Eintrag in `config/skills-registry.yaml` mit `approved: false`

**Danach manuell:**

```json
"my-skill": {
  "approved": true,     ← nach Qualitätsprüfung setzen
  ...
  "additional_files": ["reference.md"]   ← Zusatzdokumente ergänzen
}
```

### Qualitätsprüfung vor `approved: true`

Checkliste bevor ein Skill freigegeben wird:

- [ ] `SKILL.md` enthält klare, nutzbare Anweisungen
- [ ] Skill ist auf einen stabilen Commit gepinnt
- [ ] `additional_files` vollständig (alle Referenz-Docs gelistet)
- [ ] `role`-Name ist eindeutig und beschreibend
- [ ] Dry-Run ohne Fehler: `py .agent-meta/scripts/sync.py --dry-run`

---

## Für Meta-Maintainer: Skill auf neuen Commit updaten

```bash
cd .agent-meta/external/neat-little-package
```

```bash
git fetch
```

```bash
git checkout <new-commit-hash>
```

```bash
cd ../../..
```

```bash
git add .agent-meta/external/neat-little-package
```

`pinned_commit` in `config/skills-registry.yaml` manuell aktualisieren:

```json
"neat-little-package": {
  "repo": "https://github.com/racurry/neat-little-package",
  "local_path": "external/neat-little-package",
  "pinned_commit": "<new-commit-hash>"
}
```

```bash
git add .agent-meta/config/skills-registry.yaml
```

```bash
git commit -m "chore: update neat-little-package to <new-commit-hash>"
```

Dann Projekte auf die neue agent-meta Version updaten lassen.

---

## sync.py Log-Ausgaben verstehen

```
[WRITE]  .claude/agents/home-organization-specialist.md   (0-external/home-organization@be411f3)
         ↑ Skill wurde generiert. Commit-Hash zeigt gepinnten Stand.

[COPY]   .claude/skills/home-organization/SKILL.md        (external/neat-little-package/...)
         ↑ Skill-Datei wurde kopiert.

[INFO]   .claude/agents/opengrid-designer.md              (skill 'opengrid-openscad' not approved — skipping)
         ↑ Gate 1 nicht erfüllt: Meta-Maintainer hat noch nicht approved.

[INFO]   .claude/agents/opengrid-designer.md              (skill 'opengrid-openscad' not enabled in .meta-config/project.yaml — skipping)
         ↑ Gate 2 nicht erfüllt: Projekt hat den Skill nicht aktiviert.

[WARN]   external-skills: 'unknown-skill' not found in config/skills-registry.yaml — skipping
         ↑ Projekt referenziert unbekannten Skill → Tippfehler in .meta-config/project.yaml?

[WARN]   external-skills: 'my-skill' is not approved by meta-maintainer — skipping
         ↑ Skill existiert, aber approved: false → Meta-Maintainer muss freigeben.

[WARN]   repo 'neat-little-package': submodule is at abc1234, expected pinned_commit be411f3
         ↑ Submodul-Stand weicht von pinned_commit ab → git checkout <pinned_commit> ausführen.

[DELETE] .claude/agents/old-role.md                       (role removed from config)
         ↑ Deaktivierter Skill wurde aus .claude/agents/ entfernt.
```

---

## Troubleshooting

### Skill wird nicht generiert

1. Prüfe `sync.log` — unter welchem Tag erscheint der Skill? `[INFO]`, `[WARN]` oder gar nicht?
2. `[INFO] not approved` → `approved: true` in `.agent-meta/config/skills-registry.yaml` fehlt
3. `[INFO] not enabled` → `"external-skills": { "skill-name": { "enabled": true } }` in `.meta-config/project.yaml` fehlt
4. `[WARN] not found` → Skill-Name Tippfehler in `.meta-config/project.yaml`
5. `[WARN] submodule not initialized` → `git submodule update --init --recursive` ausführen

### Pinned-Commit-Warning

```
[WARN] repo 'my-repo': submodule is at abc1234, expected pinned_commit be411f3
```

Submodul auf gepinnten Stand zurücksetzen:

```bash
cd .agent-meta/external/my-repo
```

```bash
git checkout be411f3
```

```bash
cd ../../..
```

### Skill-Dateien fehlen nach Sync

Prüfen ob Submodul initialisiert ist:

```bash
ls .agent-meta/external/neat-little-package/
```

Leer → Submodul nicht initialisiert:

```bash
git submodule update --init --recursive
```

---

## Dateistruktur nach Sync

```
Zielprojekt/
├── .meta-config/project.yaml
│     └── "external-skills": { "home-organization": { "enabled": true } }
│
├── .agent-meta/                          ← agent-meta Submodul
│   ├── external/
│   │   └── neat-little-package/          ← Skill-Repo (gepinnter Commit)
│   │       └── plugins/spirograph/skills/
│   │           └── home-organization/
│   │               ├── SKILL.md
│   │               └── cross-system-compatibility.md
│   └── config/skills-registry.yaml
│         ├── repos: { neat-little-package: { pinned_commit: "be411f3..." } }
│         └── skills: { home-organization: { approved: true, repo: "neat-little-package" } }
│
└── .claude/
    ├── agents/
    │   └── home-organization-specialist.md   ← generierter Wrapper-Agent
    └── skills/
        └── home-organization/                ← kopierte Skill-Dateien
            ├── SKILL.md
            └── cross-system-compatibility.md
```

---

## Versionierungs-Strategie

```
agent-meta Version  →  pinned_commit in config/skills-registry.yaml
                               ↓
                    Skill-Stand ist deterministisch:
                    Gleiche agent-meta Version = Gleicher Skill-Stand
                    in allen Projekten die diese Version nutzen.
```

**Skill updaten = agent-meta Release:**
1. Neuen Commit pinnen + `pinned_commit` updaten
2. agent-meta Version bumpen (Patch wenn kein Breaking Change)
3. Projekte upgraden via `git checkout v<new-version>` + sync

---

## Checkliste: Skill erfolgreich eingebunden?

**Meta-Maintainer:**
- [ ] `--add-skill` ausgeführt, Submodul in `external/` vorhanden
- [ ] `pinned_commit` auf stabilem Commit
- [ ] `additional_files` vollständig
- [ ] `approved: true` gesetzt nach Qualitätsprüfung
- [ ] Dry-Run sauber
- [ ] Committed + gepusht

**Projekt-Entwickler:**
- [ ] `"external-skills"` Block in `.meta-config/project.yaml` vorhanden
- [ ] Skill mit `"enabled": true` aktiviert
- [ ] `git submodule update --init --recursive` ausgeführt
- [ ] Sync ausgeführt, `sync.log` ohne Warnings
- [ ] `.claude/agents/<role>.md` vorhanden
- [ ] `.claude/skills/<skill-name>/` vorhanden
- [ ] Committed
