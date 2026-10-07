# Recommended Skills Registry — Anleitung

`config/recommended-skills.yaml` ist eine kuratierte Whitelist von empfohlenen
Skills/Tools für agent-meta-basierte Projekte (issue #680).

---

## Abgrenzung zu `config/skills-registry.yaml`

**Diese beiden Registries sind unabhängige Systeme — nicht verwechseln:**

| | `config/skills-registry.yaml` | `config/recommended-skills.yaml` |
|---|---|---|
| Zweck | Installierte externe Skill-Submodule (Two-Gate: `approved` + `enabled`) | Kuratierte Empfehlungsliste |
| Wirkung | `sync.py` generiert daraus Wrapper-Agenten in `.claude/agents/` und kopiert Dateien nach `.claude/skills/` | Phase 1 (dieses Issue): keine — reine Doku/Referenz |
| Konsument | `scripts/lib/skills.py`, `scripts/lib/agent_sync.py`, `scripts/lib/gitignore.py`, `scripts/admin-server.py`, Admin-UI | Noch keiner (siehe Phase 2 unten) |
| Struktur | `repos:` + `skills:` (pro Skill `approved`, `pinned_commit`) | Flache Liste `recommended-skills:` |

Siehe `docs/guides/features/external-skills.md` für die Installations-Registry.

---

## Schema

```yaml
recommended-skills:
  - name: <skill-name>               # Pflicht
    description: <ein Satz>          # Pflicht
    link: <URL oder Pfad>            # Pflicht, nicht-leer (z.B. relativer Pfad auf ein lokales SKILL.md)
    scope: provider:<providername>   # Pflicht — ODER: agnostic
    tips: <optionaler Freitext>
    recommended-for: [<rolle-oder-usecase>, ...]
```

### `scope` (Pflichtfeld)

- `provider:<name>` — Skill funktioniert nur mit dem Tooling/der Integration eines bestimmten
  Providers (z.B. `provider:claude`). `<name>` muss (kleingeschrieben) auf einen aktiven
  Provider aus `config/ai-providers.yaml` (`providers:`-Keys) verweisen.
- `agnostic` — die Methodik/Disziplin ist portabel und funktioniert mit jedem AI-Provider
  (z.B. Security-Review-Checklisten, Code-Review-Disziplin).

Regex-Validierung: `^(provider:[a-z0-9_-]+|agnostic)$` (siehe
`tests/test_recommended_skills_registry.py`).

### Weitere Felder

- `name`, `description`, `link` — Pflicht, nicht-leer.
- `tips` — optional, Freitext für Hinweise/Caveats. Für noch nicht verifizierte Empfehlungen
  explizit mit `"Speculative: ..."` markieren.
- `recommended-for` — optional, Liste von Rollen oder Use-Cases, für die der Skill relevant ist.

---

## Eintrag hinzufügen

1. Eintrag am Ende der Liste in `config/recommended-skills.yaml` ergänzen.
2. `scope` korrekt setzen (siehe oben) — Pflichtfeld, Test schlägt sonst fehl.
3. Validieren: `python3 -m pytest tests/test_recommended_skills_registry.py -v`
4. Bei Unsicherheit über Nützlichkeit/Aktualität: in `tips` als spekulativ markieren statt
   den Eintrag zu entfernen oder zu erfinden.

Es gibt **keinen Approval-Gate** wie bei `config/skills-registry.yaml` — jede PR, die die
Tests besteht, kann gemerged werden. Kuration erfolgt über Code-Review.

---

## Phase 2 (noch nicht implementiert)

Dieses Issue (#680) deckt nur die Registry + Doku ab (S-Tier-Scope). Eine spätere
Erweiterung könnte `sync.py` dazu befähigen, basierend auf aktiven Rollen/Platform-Presets
automatisch einen "Recommended Skills"-Abschnitt in `CLAUDE.md` zu injizieren
(`recommended-for`-Matching gegen aktive Rollen). Das ist ein eigenes, separates Issue —
siehe Original-Issue #680, Abschnitt "Use Cases" / Acceptance Criteria (optional Punkt).
