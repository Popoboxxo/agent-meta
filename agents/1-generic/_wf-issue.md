# Workflow L: GitHub Issue bearbeiten

```
0. git          → gh issue list / gh issue view <id>
1. git          → Branch-Guard (fix/<issue> oder feat/<issue>)
2. requirements → REQ-ID zuordnen oder neu vergeben
3. tester       → Reproduzierenden Test schreiben (Bug: Red Phase)
4. developer    → Fix oder Feature implementieren
5. tester       → Tests ausführen, Regression prüfen
6. validator    → DoD-Check
7. documenter   → Doku aktualisieren falls nötig
8. git          → Commit + Push + Issue schließen:
                  gh issue close <id> --comment "Fixed in <commit>"
```

Bug → Schritt 3 zuerst. Feature → wie Workflow A, Ausgangspunkt ist das Issue.
