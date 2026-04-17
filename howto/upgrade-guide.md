# Upgrade Guide — agent-meta auf neue Version aktualisieren

---

## Übersicht: Was passiert bei einem Upgrade?

| Datei | Verhalten |
|-------|-----------|
| `.claude/agents/*.md` (aktive Rollen) | Werden **überschrieben** — neue Version aus Meta-Repo |
| `.claude/agents/*.md` (entfernte Rollen) | Werden **gelöscht** — Cleanup bei jedem Sync |
| `CLAUDE.md` — managed block | Wird **automatisch aktualisiert** bei `ai-provider: Claude` |
| `CLAUDE.md` — Rest | Wird **nicht** angefasst |
| `CLAUDE.personal.md` | Wird **nicht** angefasst |
| `.claude/settings.json` | Wird **nicht** angefasst |
| `.gitignore` | Fehlende Einträge werden **ergänzt** |
| `.claude/3-project/*-ext.md` | Werden **nicht** überschrieben — bleiben erhalten |
| `.claude/3-project/*.md` (Override) | Werden **nicht** angefasst |
| `agent-meta.config.yaml` | Wird **nicht** angefasst — manuell prüfen |

**Kernregel:** Alles in `.claude/agents/` wird bei jedem Sync neu generiert.
Rollen die aus `config['roles']` entfernt wurden, werden automatisch gelöscht.
Alles in `.claude/3-project/` ist sicher — wird nie überschrieben.

---

## Standard-Upgrade

```bash
# 1. Submodul auf neue Version ziehen
cd .agent-meta
git fetch
git checkout v0.2.0
cd ..

# 2. agent-meta-version in config aktualisieren
#    Öffne agent-meta.config.yaml und setze:
#    "agent-meta-version": "0.2.0"

# 3. Dry-Run — prüfen was sich ändern würde
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml --dry-run

# 4. Sync ausführen
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml

# 5. sync.log prüfen
cat sync.log

# 6. Neue Warnungen? → Fehlende Variablen in config ergänzen, dann erneut syncen

# 7. Committen
git add .claude/agents/ .agent-meta agent-meta.config.yaml
git commit -m "chore: upgrade agent-meta to v0.2.0"
```

---

## Upgrade mit Breaking Changes (neue Variablen)

Wenn eine neue agent-meta Version neue `{{PLATZHALTER}}` einführt:

1. Dry-Run zeigt `[WARN]` für fehlende Variablen
2. `sync.log` listet alle unerfüllten Platzhalter
3. Neue Variablen in `agent-meta.config.yaml` ergänzen
4. Erneut syncen — Warnungen sollten verschwinden

```bash
# Alle aktuellen Variablen-Namen aus der Config-Vorlage der neuen Version sehen:
cat .agent-meta/howto/agent-meta.config.example.json
```

---

## Upgrade mit Extension-Dateien

Der **managed block** in jeder Extension-Datei enthält auto-generierten Kontext
aus den config-Variablen. Er wird bei jedem `--update-ext` aktualisiert.
Der handgeschriebene Projektbereich darunter bleibt immer erhalten.

```bash
# Nach einem Upgrade: managed blocks aktualisieren
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml --update-ext

# Ergebnis prüfen
cat sync.log
```

Falls eine neue agent-meta Version den `MANAGED_BLOCK_TEMPLATE` in `sync.py` ändert
(neue Variablen, andere Struktur), werden alle Extensions beim nächsten `--update-ext`
automatisch auf das neue Format gebracht.

---

## Upgrade mit Konzept-Änderungen (Major Version)

Bei Major-Version-Upgrades (z.B. v0.x → v1.0) können sich Strukturen ändern:
- Neue Agent-Rollen
- Geänderter Platzhalter-Name
- Neue Pflichtfelder in `agent-meta.config.yaml`

Vorgehen:
1. `CHANGELOG.md` der neuen Version lesen: `cat .agent-meta/CHANGELOG.md`
2. Breaking Changes identifizieren
3. `agent-meta.config.yaml` anpassen
4. Dry-Run ausführen
5. Sync ausführen und `sync.log` prüfen

---

## Rollback

Falls ein Upgrade Probleme verursacht:

```bash
# Submodul auf alte Version zurücksetzen
cd .agent-meta
git checkout v0.1.0
cd ..

# Agenten neu generieren
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml

# Config-Version zurücksetzen
# "agent-meta-version": "0.1.0"
```

---

## Was tun bei Konflikten in Extensions?

Extensions werden nie überschrieben — es gibt keine automatischen Merge-Konflikte.
Wenn eine neue agent-meta Version jedoch die Basis-Logik eines Agenten fundamental ändert
und die Extension darauf aufbaut:

1. Neue Version des Agenten lesen: `cat .claude/agents/developer.md`
2. Eigene Extension prüfen: `cat .claude/3-project/developer-ext.md`
3. Extension bei Bedarf manuell anpassen

**Faustregel:** Extensions referenzieren Verhalten des Agenten nicht direkt —
sie ergänzen ihn mit eigenem Wissen. Dadurch sind Konflikte selten.

---

## Upgrade-Checkliste

- [ ] `CHANGELOG.md` der neuen Version gelesen
- [ ] Submodul auf neue Version gesetzt
- [ ] `agent-meta-version` in config aktualisiert
- [ ] Dry-Run ohne unerwartete Änderungen
- [ ] Sync ausgeführt
- [ ] `sync.log` ohne neue Warnungen
- [ ] Extensions bei Bedarf manuell geprüft
- [ ] Committed

---

## Migration: v0.16.x → v0.17.0

v0.17.0 führt drei neue Systeme ein: **Hooks**, **Rules** und **JSON Schema**.
Alle Änderungen sind rückwärtskompatibel — keine Breaking Changes.

### 1. JSON Schema hinzufügen (empfohlen)

In `agent-meta.config.yaml` oben ergänzen:
```json
{
  "$schema": ".agent-meta/agent-meta.schema.json",
  ...
}
```

Aktiviert IDE-Autovervollständigung und Validierung in VS Code und anderen Editoren.

### 2. Nach dem Upgrade syncen

```bash
cd .agent-meta && git checkout v0.17.0 && cd ..
# agent-meta.config.yaml: "agent-meta-version": "0.17.0"
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml --dry-run
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml
```

Nach dem Sync sind neu vorhanden:
- `.claude/rules/issue-lifecycle.md` — automatisch in alle Agenten geladen
- `.claude/rules/.agent-meta-managed` — Stale-Tracking für verwaltete Rules
- `.claude/hooks/dod-push-check.sh` — DoD-Push-Check (noch inaktiv bis aktiviert)
- `.claude/hooks/.agent-meta-managed` — Stale-Tracking für verwaltete Hooks
- `.claude/settings.local.json` — persönliches Skeleton (gitignored, einmalig angelegt)

### 3. DoD-Push-Check aktivieren (optional)

Falls TEST_COMMAND in der Config gesetzt ist und automatische Push-Blockierung gewünscht:

```json
"hooks": {
  "dod-push-check": { "enabled": true }
}
```

Dann erneut syncen — der Hook wird in `.claude/settings.json` registriert.

Vollständige Dokumentation: `.agent-meta/howto/hooks.md`

### 4. permissionMode-Overrides (optional)

`validator` und `security-auditor` bekommen jetzt automatisch `permissionMode: plan`.
Falls ein anderes Verhalten gewünscht:

```json
"permission-mode-overrides": {
  "validator": "default"
}
```

### 5. Committen

```bash
git add .claude/ agent-meta.config.yaml .agent-meta
git commit -m "chore: upgrade agent-meta to v0.17.0"
```

---

## Migration: v0.20.x → v0.21.0 (Multi-Provider)

v0.21.0 führt Multi-Provider-Support ein: Claude, Gemini und Continue können gleichzeitig
Agenten-Dateien erhalten. Alle Änderungen sind **rückwärtskompatibel** — kein Breaking Change.

### 1. Neues Feld `ai-providers` (Array)

Das neue Array-Feld ersetzt das alte String-Feld:

```json
// Neu (empfohlen)
"ai-providers": ["Claude"]

// Legacy (weiterhin unterstützt — kein Update nötig)
"ai-provider": "Claude"
```

Das String-Feld `ai-provider` wird weiterhin erkannt und verarbeitet.
Ein Upgrade ist optional — wer kein Gemini oder Continue nutzt, muss nichts ändern.

### 2. Weitere Provider hinzufügen (optional)

Um Gemini oder Continue zusätzlich zu aktivieren, `ai-providers` anpassen:

```json
"ai-providers": ["Claude", "Continue"]
```

Beim nächsten Sync legt `sync.py` automatisch die neuen Verzeichnisse an:
- `"Gemini"` → `.gemini/GEMINI.md` + `.gemini/agents/` + `.gemini/settings.json`
- `"Continue"` → `.continue/rules/project-context.md` + `.continue/agents/` + `.continue/config.yaml`

### 3. Sync ausführen

```bash
cd .agent-meta && git checkout v0.21.1-beta && cd ..
# agent-meta.config.yaml: "agent-meta-version": "0.21.1-beta"
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml --dry-run
py .agent-meta/scripts/sync.py --config agent-meta.config.yaml
```

### 4. Committen

```bash
git add .claude/ .gemini/ .continue/ agent-meta.config.yaml .agent-meta
git commit -m "chore: upgrade agent-meta to v0.21.1-beta"
```

> **Vollständige Dokumentation:** [howto/multi-provider.md](multi-provider.md)

---

## Breaking Change: v0.14.4 → `enabled` → `approved` in external-skills.config.yaml

Ab v0.14.4 gilt für External Skills ein **Two-Gate-System**:

- `external-skills.config.yaml`: `enabled` wurde in `approved` umbenannt — Meta-Maintainer-Freigabe
- `agent-meta.config.yaml`: neuer `"external-skills"` Block für projektlokale Aktivierung

**Migration:**

In `external-skills.config.yaml` — alle `"enabled"` umbenennen:
```json
// vorher
"enabled": true

// nachher
"approved": true
```

In `agent-meta.config.yaml` des Projekts — neuen Block ergänzen für jeden gewünschten Skill:
```json
"external-skills": {
  "my-skill": { "enabled": true }
}
```

Ohne diesen Block werden **keine** externen Skills generiert (sicheres Default).
