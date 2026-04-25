# Workflow M+N: Scouting & externes Skill-Repo

## M: Claude-Ökosystem scouten
Nur auf explizite Anfrage — NIEMALS automatisch.

```
1. agent-meta-scout → Scouting, Evaluation, Empfehlungs-Bericht
```

## N: Externes Repo als Skill einbinden
Trigger: User teilt Repo-URL, "als Skill einbinden?"

```
1. agent-meta-scout → Repo evaluieren (Qualität, Scope, SKILL.md vorhanden?)

2. Entscheidung:
   ├─ External Skill → agent-meta-manager: --add-skill + aktivieren
   │                 → git: "feat: add external skill <name>"
   ├─ Besser als Rule/Extension → User informieren
   └─ Nicht geeignet → User informieren + ggf. meta-feedback
```

Immer erst evaluieren — nie blind `--add-skill`. Neuer Skill startet mit `approved: false`.
