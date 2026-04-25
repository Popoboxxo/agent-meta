# Workflow H2: agent-meta auf neue Version upgraden

```
1. Version prüfen:
   cat .agent-meta/VERSION
   cat .meta-config/project.yaml  # → "agent-meta-version"

2. CHANGELOG lesen (Breaking Changes?):
   cd .agent-meta && git fetch && git log --oneline HEAD..v<neu> && cd ..
   cat .agent-meta/CHANGELOG.md

3. Submodul ziehen:
   cd .agent-meta && git checkout v<neu> && cd ..

4. agent-meta-version in .meta-config/project.yaml setzen

5. Dry-Run:
   python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --dry-run
   → sync.log: neue Warnungen = fehlende Variablen

6. Fehlende Variablen ergänzen:
   cat .agent-meta/howto/project.yaml.example

7. Sync:
   python .agent-meta/scripts/sync.py --config .meta-config/project.yaml

8. Extensions aktualisieren:
   python .agent-meta/scripts/sync.py --config .meta-config/project.yaml --update-ext

9. git → Commit: "chore: upgrade agent-meta to v<neu>"
   Dateien: .claude/agents/ .claude/3-project/ .agent-meta .meta-config/project.yaml
```
