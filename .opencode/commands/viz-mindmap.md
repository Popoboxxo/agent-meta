---
description: Generate static agent visualization mindmap and interactive HTML graph
allowed-tools: ["Bash"]
argument-hint: "[--open]"
---

Run the visualization generator to create the static agent mindmap:

```bash
# Pass user arguments through ($ARGUMENTS may be empty or contain flags)
FLAGS="$ARGUMENTS"
python .agent-meta/scripts/sync.py --viz-only

# If --open is passed, open the generated HTML graph in the default browser
if echo "$FLAGS" | grep -q -- "--open"; then
    python -c "import webbrowser; webbrowser.open('docs/agent-graph.html')"
fi
```

This generates:
- `docs/agent-mindmap.md` — Mermaid diagram for GitHub/docs
- `docs/agent-graph.html` — Interactive HTML page with dark mode
