# Submodule-Schutzkonzept

Regeln für den Umgang mit dem `.agent-meta`-Submodul und `.gitmodules`:

- **Keine direkten Änderungen in `.agent-meta/`:** Dateien in `.agent-meta/` dürfen in Konsumenten-Repositories niemals direkt editiert oder committet werden.
- **Keine Mutation von `.gitmodules` / Git Staging:** `.gitmodules` darf nicht automatisch modifiziert werden und Submodule dürfen nicht automatisch via `git add` gestaged werden.
- **Kein Source-Code-Scaffolding in Konsumenten-Projekten:** In Konsumenten-Projekten wird kein Anwendungscode generiert/gerüstet; verwaltet werden ausschließlich `.meta-config/project.yaml` und die Managed Blocks.
- **Framework-Änderungen nur im agent-meta Repo:** Änderungen am agent-meta Framework müssen auf Feature-Branches im agent-meta Repository selbst durchgeführt werden.
