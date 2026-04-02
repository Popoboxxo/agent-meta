# Upgrade Guide — agent-meta auf neue Version aktualisieren

---

## Übersicht: Was passiert bei einem Upgrade?

| Datei | Verhalten |
|-------|-----------|
| `.claude/agents/*.md` | Werden **überschrieben** — neue Version aus Meta-Repo |
| `CLAUDE.md` | Wird **nicht** angefasst (außer `--only-variables`) |
| `.claude/3-project/*-ext.md` | Werden **nicht** überschrieben — bleiben erhalten |
| `.claude/3-project/*.md` (Override) | Werden **nicht** angefasst |
| `agent-meta.config.json` | Wird **nicht** angefasst — manuell prüfen |

**Kernregel:** Alles in `.claude/agents/` wird bei jedem Sync neu generiert.
Eigene Anpassungen dort gehen verloren. Alles in `.claude/3-project/` ist sicher.

---

## Standard-Upgrade

```bash
# 1. Submodul auf neue Version ziehen
cd .agent-meta
git fetch
git checkout v0.2.0
cd ..

# 2. agent-meta-version in config aktualisieren
#    Öffne agent-meta.config.json und setze:
#    "agent-meta-version": "0.2.0"

# 3. Dry-Run — prüfen was sich ändern würde
py .agent-meta/scripts/sync.py --config agent-meta.config.json --dry-run

# 4. Sync ausführen
py .agent-meta/scripts/sync.py --config agent-meta.config.json

# 5. sync.log prüfen
cat sync.log

# 6. Neue Warnungen? → Fehlende Variablen in config ergänzen, dann erneut syncen

# 7. Committen
git add .claude/agents/ .agent-meta agent-meta.config.json
git commit -m "chore: upgrade agent-meta to v0.2.0"
```

---

## Upgrade mit Breaking Changes (neue Variablen)

Wenn eine neue agent-meta Version neue `{{PLATZHALTER}}` einführt:

1. Dry-Run zeigt `[WARN]` für fehlende Variablen
2. `sync.log` listet alle unerfüllten Platzhalter
3. Neue Variablen in `agent-meta.config.json` ergänzen
4. Erneut syncen — Warnungen sollten verschwinden

```bash
# Alle aktuellen Variablen-Namen aus der Config-Vorlage der neuen Version sehen:
cat .agent-meta/agent-meta.config.example.json
```

---

## Upgrade mit Extension-Dateien

Extensions (`.claude/3-project/*-ext.md`) werden bei Upgrades **nie überschrieben**.

Falls eine neue agent-meta Version eine verbesserte Vorlage für eine Extension mitbringt:

```bash
# Vorlage aus dem Meta-Repo ansehen:
cat .agent-meta/agents/3-project/developer-ext.md

# Manuell mit eigener Extension abgleichen und bei Bedarf ergänzen:
# .claude/3-project/developer-ext.md
```

---

## Upgrade mit Konzept-Änderungen (Major Version)

Bei Major-Version-Upgrades (z.B. v0.x → v1.0) können sich Strukturen ändern:
- Neue Agent-Rollen
- Geänderter Platzhalter-Name
- Neue Pflichtfelder in `agent-meta.config.json`

Vorgehen:
1. `CHANGELOG.md` der neuen Version lesen: `cat .agent-meta/CHANGELOG.md`
2. Breaking Changes identifizieren
3. `agent-meta.config.json` anpassen
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
py .agent-meta/scripts/sync.py --config agent-meta.config.json

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
