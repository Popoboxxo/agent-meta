# Agent Roles

> [Back to Architecture Overview](../../ARCHITECTURE.md)

```mermaid
graph TD
    ORC[orchestrator]
    ORC --> IDE[ideation]
    ORC --> REQ[requirements]
    ORC --> DEV[developer]
    ORC --> TST[tester]
    ORC --> VAL[validator]
    ORC --> DOC[documenter]
    ORC --> GIT[git]
    ORC --> REL[release]
    ORC --> DOK[docker]
    ORC --> MFB[meta-feedback]
    ORC --> AMM[agent-meta-manager]
    ORC --> AMS[agent-meta-scout]
    ORC --> SEC[security-auditor]
    ORC --> EXT[0-external skills]
    ORC --> SE_ORCH[orchestrator (SE-Mode)]
    SE_ORCH --> SE_REQ[se-requirements]
    SE_ORCH --> SE_ARCH[se-architect]
    SE_ARCH --> SE_CRIT[se-critic]
    SE_CRIT --> SE_IFM[se-interface-mgr]
    SE_IFM --> SE_TERM[se-termination]
    SE_TERM -->|continue| SE_ORCH
```

## Rollen-Übersicht

| Agent | Zuständigkeit | Einstieg | Modell |
|-------|--------------|---------|--------|
| `orchestrator` | Einstiegspunkt — koordiniert alle anderen Agenten | Alle Entwicklungsaufgaben | *(voll)* |
| `developer` | Feature-Implementierung und Bugfixes nach REQ-IDs | Implementierungsaufgaben | *(voll)* |
| `junior-developer` | Triviale Fixes (1-2 Dateien, kein Architektur-Impact), eskaliert strukturiert | Kleine Änderungen | haiku |
| `senior-developer` | Komplexe Features, Architektur-Entscheidungen, schwierige Bugs | Architektur-Impact, Cross-Cutting | max |
| `principal-developer` | Ultra-Tier Last-Resort-Eskalation nach wiederholtem senior-developer-Versagen. Mandatiert Root-Cause-Diagnose vor Implementierung | Nur nach Eskalation, `orchestrator_only: true` | ultra |
| `intern-developer` | Easter-Egg/Gag-Agent. Übereifriger, ahnungsloser Intern — read-only, nie für echte Arbeit geroutet | — | nano |
| `tester` | Tests schreiben und ausführen (TDD) | TDD Red/Green Phase | sonnet |
| `validator` | Code gegen REQs prüfen, DoD-Check | Vor Commit/PR | sonnet |
| `requirements` | Anforderungen aufnehmen, REQ-IDs vergeben | Neue Anforderungen | *(voll)* |
| `ideation` | Neue Ideen explorieren, Vision schärfen | Ideen-Phase | *(voll)* |
| `documenter` | Doku pflegen: CODEBASE_OVERVIEW, ARCHITECTURE, README | Nach Implementierung | sonnet |
| `git` | Commits, Branches, Tags, Push/Pull | Git-Operationen | haiku |
| `release` | Versioning, Changelog, Build-Artifact, GitHub Release | Release-Prozess | sonnet |
| `docker` | Docker-Stack bauen, starten, verwalten | Infrastruktur | haiku |
| `meta-feedback` | Verbesserungsvorschläge als GitHub Issues einreichen | Framework-Feedback | haiku |
| `agent-meta-manager` | agent-meta verwalten: Upgrade, Sync, Feedback, projekt-Agenten | Meta-Management | sonnet |
| `agent-meta-scout` | Claude-Ökosystem scouten: neue Skills, Rollen, Rules und Patterns | Ökosystem-Erkundung | sonnet |
| `security-auditor` | Sicherheitsanalyse: OWASP, Secrets, Dependency-Audit | Security-Reviews | sonnet |
| `database-engineer` | DB-Schema-Design, backwards-kompatible Migrationen, Query-Optimierung, Index-Strategie | DB-Änderungen, Migrations, Performance | powerful |
| `incident-responder` | Live-Incident-Koordination, RCA (5-Whys/Fishbone), Severity-Klassifikation, priorisierte Hotfixes | Aktive Incidents, Post-Mortem | powerful |
| `dependency-auditor` | Supply-Chain-Hygiene: SBOM-Analyse, Lizenz-Kompatibilität, Version-Drift, CVE-Checks | Security-Reviews, Release-Vorbereitung | balanced |
| `0-external skills` | Domänenspezifische Agenten aus Drittrepos | Spezialwissen | variiert |
| `orchestrator (SE-Mode)` | Koordiniert 6-stufige rekursive SE-Kaskade | Systems-Engineering | balanced |
| `se-requirements` | Stakeholder-Bedürfnisse → formale L1-Blackbox-REQs | SE-Start | balanced |
| `se-architect` | Black-Box → White-Box (funktionale Dekomposition) | SE-Zerlegung | powerful |
| `se-critic` | Quality Gate: Vollständigkeit, Konsistenz, Testbarkeit | SE-Audit | powerful |
| `se-interface-mgr` | Interface-Verträge + Propagations-Map | SE-Interfaces | balanced |
| `se-termination` | Leaf/Continue-Entscheidung pro Komponente | SE-Abschluss | fast |
