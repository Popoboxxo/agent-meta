# Commit-Konventionen (Conventional Commits)

Gilt für alle Agenten die Commits erstellen oder vorbereiten.

## Format

```
<type>(REQ-xxx): <beschreibung>   ← mit req-traceability
<type>: <beschreibung>            ← ohne req-traceability
```

| Type | Bedeutung | REQ-ID |
|------|-----------|--------|
| `feat` | Neues Feature | Wenn `req-traceability` aktiv |
| `fix` | Bugfix | Wenn `req-traceability` aktiv |
| `refactor` | Refactoring ohne Verhaltensänderung | Wenn `req-traceability` aktiv |
| `test` | Tests hinzufügen/ändern | Wenn `req-traceability` aktiv |
| `chore` | Wartung: Dependencies, Config, Versions-Bumps | **Nie** |
| `docs` | Dokumentation | **Nie** |
| `ci` | CI/CD-Änderungen | **Nie** |

## Regeln

- Beschreibung im **Imperativ**: `add feature`, nicht `added feature`
- Maximal **72 Zeichen** in der ersten Zeile
- Beschreibungssprache: `Englisch`
- Body optional: Was **und warum** geändert wurde

## Beispiele

**Mit req-traceability:**
```
feat(REQ-042): add queue persistence across restarts
fix(REQ-017): prevent duplicate video entries on reconnect
test(REQ-042): add persistence tests
chore: bump version to 1.2.0
docs: update installation instructions
```

**Ohne req-traceability:**
```
feat: add queue persistence across restarts
fix: prevent duplicate video entries on reconnect
chore: bump version to 1.2.0
```
