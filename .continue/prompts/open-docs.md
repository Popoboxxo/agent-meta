---
description: Open the docs/ folder or a specific analysis document in the terminal
allowed-tools: ["Bash", "Read", "Glob"]
argument-hint: "[analysis | architecture | requirements | <filename>]"
invokable: true
---

Browse or open documentation. $ARGUMENTS

- No argument: List all docs with short descriptions
- `analysis`: List analysis documents in `docs/analysis/`
- `architecture`: Show architecture diagrams
- `requirements`: Open REQUIREMENTS.md
- `<filename>`: Open specific file (fuzzy match)
