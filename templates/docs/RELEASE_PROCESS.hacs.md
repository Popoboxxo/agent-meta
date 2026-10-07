# Release-Prozess — {{PROJECT_NAME}}

> Generiert von agent-meta aus `templates/docs/RELEASE_PROCESS.{{DISTRIBUTION}}.md`.
> Projektspezifische Ergänzungen gehören UNTER den `managed-end`-Marker.

## 1. Versionierung (Semantic Versioning)

Dieses Projekt folgt [{{VERSIONING}}](https://semver.org/):
`MAJOR.MINOR.PATCH`.

- **MAJOR** — inkompatible Änderungen (Breaking Changes)
- **MINOR** — neue, abwärtskompatible Funktionalität
- **PATCH** — abwärtskompatible Bugfixes

Die autoritative Version steht in `{{VERSION_FILE}}` im Feld `{{VERSION_FIELD}}`:

```json
{
  "{{VERSION_FIELD}}": "1.2.3"
}
```

## 2. Version-Bump — Entscheidungstabelle

Der Bump wird aus den [Conventional Commits](https://www.conventionalcommits.org/)
seit dem letzten Tag abgeleitet:

| Commit-Typ seit letztem Tag | Bump  |
|-----------------------------|-------|
| Commit mit `BREAKING CHANGE` / `!` | MAJOR |
| mindestens ein `feat:`             | MINOR |
| nur `fix:` / `perf:` / sonstige    | PATCH |

Vorgehen:

```bash
# 1. Commits seit letztem Tag auflisten
git log "$(git describe --tags --abbrev=0)"..HEAD --oneline

# 2. Typen analysieren (feat / fix / BREAKING) und Bump bestimmen
# 3. Version in {{VERSION_FILE}} ({{VERSION_FIELD}}) anheben
```

## 3. Changelog ({{CHANGELOG_FORMAT}})

Das Changelog folgt dem Format [{{CHANGELOG_FORMAT}}](https://keepachangelog.com/).
Pflege Einträge unter `[Unreleased]` in `CHANGELOG.md` und verschiebe sie beim
Release unter die neue Versions-Überschrift mit Datum.

Gruppen: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`.

## 4. HACS-Versions-Erkennung (wichtig)

HACS liest die Version aus den **GitHub Releases** und aus `{{VERSION_FILE}}` —
**NICHT** aus `hacs.json`. Daher gilt:

- `{{VERSION_FIELD}}` in `{{VERSION_FILE}}` MUSS dem Git-Tag entsprechen.
- Ein GitHub Release (nicht nur ein Tag) ist erforderlich, damit HACS die
  neue Version anzeigt.
- `hacs.json` steuert nur Metadaten (Name, Domains), nicht die Version.

## 5. Pre-Release-Checkliste

- [ ] Tests grün
- [ ] Linting ohne Fehler
- [ ] `CHANGELOG.md` aktualisiert (`[Unreleased]` → neue Version + Datum)
- [ ] Version in `{{VERSION_FILE}}` (`{{VERSION_FIELD}}`) angehoben
- [ ] Version == geplanter Git-Tag

## 6. Release-Workflow

```bash
# 1. Tag setzen (muss der Version in {{VERSION_FILE}} entsprechen)
git tag -a v1.2.3 -m "Release v1.2.3"

# 2. Tag pushen
git push origin v1.2.3
```

3. **GitHub Release erstellen** (aus dem Tag) mit den Changelog-Einträgen als
   Release Notes — erst damit erkennt HACS die neue Version.
4. **HACS-Sync abwarten:** HACS synchronisiert neue Releases mit Verzögerung
   (typischerweise bis zu ~24 h). Die Version erscheint nicht sofort bei den
   Nutzern.
