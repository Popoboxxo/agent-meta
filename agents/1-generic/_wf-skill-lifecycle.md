# External Skills — Lifecycle

## 7.1 Status anzeigen

```bash
cat .agent-meta/config/skills-registry.yaml
cat .meta-config/project.yaml   # → "external-skills"
```

Statusmatrix: Skill | Approved | Projekt-Status | Repo@commit

## 7.2 Skill aktivieren

Voraussetzung: `approved: true` in skills-registry.yaml.

```
1. Submodule prüfen: ls .agent-meta/external/<repo>/
   → Leer? git submodule update --init --recursive
2. .meta-config/project.yaml: "external-skills": { "skill-name": { "enabled": true } }
3. py .agent-meta/scripts/sync.py --config .meta-config/project.yaml
4. sync.log: Skill unter [WRITE]?
```

Wenn `approved: false` → meta-feedback delegieren (Label: `external-skill`).

## 7.3 Skill deaktivieren

```
1. .meta-config/project.yaml: enabled: false
2. py .agent-meta/scripts/sync.py --config .meta-config/project.yaml
```

## 7.4 Neues Skill-Repo hinzufügen

```
1. Prüfen: SKILL.md vorhanden? Scope klar abgegrenzt?
2. py .agent-meta/scripts/sync.py \
     --add-skill <repo-url> --skill-name <name> --source <path> --role <role>
3. Ergebnis: approved: false — erst prüfen, dann freigeben
```

## 7.5 Repo-Vorschlag vom User

```
Bereits als Submodule? → Ja: aktivieren (7.2) | Nein: ↓
Hochspezialisiert?     → Ja: --add-skill (7.4)
Passt als Rule/Ext?    → User informieren + ggf. meta-feedback
Unklar?                → agent-meta-scout zur Evaluation
```

## 7.6 Submodule aktualisieren

```bash
git submodule update --init --recursive        # nach Clone
cd .agent-meta/external/<repo> && git pull && cd ../..
git add .agent-meta/external/<repo>            # pinned_commit aktualisieren
py .agent-meta/scripts/sync.py --config .meta-config/project.yaml
```

## 7.7 Konsistenz-Check

1. Submodule-Commit == pinned_commit? (`git submodule status .agent-meta`)
2. source + entry Dateien vorhanden?
3. additional_files vorhanden?
4. Orphaned Skills (Repo gelöscht)?
5. SKILL.md nicht registriert?
