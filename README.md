Notes

git submodule add <repo-url> .agent-meta
cd .agent-meta && git checkout v0.1.0 && cd ..

cp .agent-meta/agent-meta.config.example.json agent-meta.config.json
# → Werte befüllen

python .agent-meta/scripts/sync.py --init --config agent-meta.config.json
cat sync.log
Das agent-meta.config.json pinnt die Version explizit mit "agent-meta-version": "0.1.0" — reproduzierbar auch auf zukünftigen Rechnern.
