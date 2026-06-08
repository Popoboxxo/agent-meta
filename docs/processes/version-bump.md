# Version-Bump Process

> **Ziel:** Zentrale, reproduzierbare Versionserhöhung für agent-meta — alle
> hardcoded Version-Strings in Dokumentation werden automatisch aktualisiert.

## Übersicht

Vor `v0.57.1` wurden Versionen in mehreren Dateien manuell gepflegt
(README.md-Badge, Checkout-Beispiel, Test-Szenarien-Titel, etc.). Das führte
zu Inkonsistenzen (Issue #254). `scripts/bump-version.py` löst das Problem
durch einen zentralen Bump-Mechanismus.

```bash
python scripts/bump-version.py <neue-version>
```

## Was wird aktualisiert

| Artefakt | Beschreibung |
|----------|-------------|
| `VERSION` | Semver-String ohne `v`-Präfix (z.B. `0.58.0`) |
| `README.md` | Badge (`version-X.Y.Z`), Checkout-Beispiel (`vX.Y.Z`) |
| `docs/**/*.md` | Alle Markdown-Dateien unter `docs/` |

**Nicht aktualisiert:**
- `CHANGELOG.md` — dessen Sektionen sind historische Einträge, keine
  Current-Version-Referenzen. Neue Versionen werden manuell hinzugefügt.
- `agents/*/` — Templates tragen ihre eigene Frontmatter-Version (`version:`)
  die unabhängig vom Framework-Release-Zyklus ist.

## Matching-Regeln

`bump-version.py` ersetzt die **aktuelle Version** (aus `VERSION` gelesen)
durch die neue Version. Erkannt werden:

| Format | Beispiel | Erklärung |
|--------|----------|-----------|
| Ohne Präfix | `0.57.1` | Badge-URLs, Plaintext |
| Mit `v`-Präfix | `v0.57.1` | Git-Tags, Checkout-Beispiele |
| Am Satzende | `v0.57.1.` | Wird erkannt (Punkt nach Version erlaubt) |
| In Klammern | `(v0.57.1)` | Wird erkannt |

**Sicherheitsmechanismen:**
- `VERSION`-Datei ist Single-Source-of-Truth — nur was dort steht wird ersetzt
- Kein Partial-Match: `0.57.1` matched **nicht** in `0.57.10`
- `--dry-run` zeigt Diff vor dem Schreiben

## Workflow

### Release-Version-Bump

```bash
# 1. Dry-run — prüfen was geändert würde
python scripts/bump-version.py 0.58.0 --dry-run

# 2. Ausführen
python scripts/bump-version.py 0.58.0

# 3. CHANGELOG.md manuell ergänzen (Header + Änderungen)
#    → [0.58.0] — YYYY-MM-DD

# 4. Review + Commit
git diff
git commit -am "chore: bump version to 0.58.0"
```

### Nur Docs aktualisieren (VERSION unverändert)

```bash
python scripts/bump-version.py 0.58.0 --docs-only
```

Nützlich wenn `VERSION` bereits manuell gesetzt wurde und nur die Docs
nachgezogen werden sollen.

## Neue Doc-Dateien mit Version-Referenz

Wenn eine neue Dokumentationsdatei unter `docs/` die aktuelle Version
referenziert, wird sie beim nächsten `bump-version.py`-Lauf automatisch
aktualisiert. Kein zusätzlicher Konfigurationsschritt nötig.

**Empfohlene Schreibweise:**
```markdown
# My Document — agent-meta v0.57.1
```

Oder im Fließtext:
```markdown
Diese Anleitung gilt für agent-meta v0.57.1.
```

Das `v`-Präfix ist optional — beide Formen werden erkannt.

## Fehlerbehandlung

| Situation | Verhalten |
|-----------|-----------|
| `VERSION` nicht gefunden | Fehler + Exit |
| Aktuelle Version = neue Version | "nothing to do" |
| Keine Docs referenzieren die alte Version | "No documentation files reference version X.Y.Z" |
