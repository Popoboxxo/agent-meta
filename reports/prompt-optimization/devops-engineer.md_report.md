# Prompt Optimization Report: devops-engineer.md

## 1. Executive Summary
Die Analyse des `devops-engineer`-Prompts (v1.1.2) zeigt signifikantes Potenzial zur Token-Reduktion (ca. 40-50% Ersparnis im System-Prompt) und Latenz-Verbesserung. Der aktuelle Prompt nutzt ausgedehnte YAML- und JSON-Beispiele, die als abstrakte Platzhalter dienen, aber eine hohe Token-Last erzeugen. Gemäß den Best Practices für Prompt Compression (Structured Prompting & Relevanz-Filterung) sollten diese durch kompakte Regelwerke oder TypeScript-Interfaces ersetzt werden, ohne dass die Funktionalität beeinträchtigt wird.

## 2. Aktueller Status (Pain Points)
- **Bloated Examples:** Die Sektionen "Pipeline-Grundgerüst" (25 Zeilen YAML) und "Deployment-Manifest" (32 Zeilen YAML) enthalten viel Syntax-Boilerplate ohne zusätzlichen semantischen Wert.
- **Redundante Schemas:** Das "JSON Output Schema" (45 Zeilen) ist extrem granular und spezifisch für Kubernetes, obwohl der Agent plattform-agnostisch arbeiten soll.
- **Regel-Duplikation:** Die Sektion "Branch-Guard" wiederholt globale Framework-Regeln (wie das Anlegen von `feat/`-Branches), die bereits über globale Rules (`AGENTS.md`) injiziert werden.
- **Visuelle vs. Kognitive Dichte:** Tabellen und Checklisten in der Observability-Sektion sind leserlich für Menschen, aber für LLMs als kompakte Key-Value-Listen effizienter zu parsen.

## 3. Actionable Insights & Optimierungsvorschläge

### Vorschlag A: YAML-Codeblöcke in kompakte Constraint-Listen umwandeln
LLMs benötigen keine vollständigen YAML-Skelette, um CI/CD-Pipelines oder Deployments zu generieren. Sie benötigen lediglich die *Constraints* (Bedingungen).

**Vorher (Auszug, 32 Zeilen K8s YAML):**
```yaml
apiVersion: apps/v1
kind: Deployment
...
```

**Nachher (Kompakte Liste):**
```markdown
**Container-Orchestrierung (Constraints):**
- **Resources:** `requests` und `limits` für CPU/Memory sind zwingend.
- **Security:** `runAsNonRoot: true` im SecurityContext.
- **Probes:** `readinessProbe` und `livenessProbe` definieren.
- **Update-Strategie:** `RollingUpdate` (maxUnavailable: 1, maxSurge: 1).
```
*Effekt: ~80% Token-Ersparnis in diesen Sektionen bei exakt gleicher Output-Qualität.*

### Vorschlag B: JSON-Schema durch kompaktes TypeScript-Interface ersetzen
TypeScript-Interfaces erzwingen Struktur mit deutlich weniger Tokens als voluminöse JSON-Beispiele und verhindern "Lost in the Middle"-Effekte. Das verkürzt zudem die "Generation Speed", da der Agent bei Bedarf kompaktere JSONs generiert.

**Nachher (Kompaktes Interface statt 45 Zeilen JSON):**
```typescript
// Output Format: Kompaktes JSON basierend auf diesem Schema
interface InfraReport {
  infra_type: string;
  environment: string;
  components: { name: string, type: string, security_constraints: string[] }[];
  ci_cd_stages: string[];
  observability: { metrics: boolean, logging: boolean, tracing: boolean, alerts: boolean };
  recommendations: string[];
}
```
*Effekt: Plattform-agnostischer, ~70% weniger Tokens im Output-Schema, schnellere Latenz.*

### Vorschlag C: Redundanzen im Branch-Guard und den Don'ts entfernen
Da das `agent-meta` Framework eine globale Branch-Guard-Rule erzwingt, kann diese Sektion im Agenten auf die DevOps-spezifischen Deltas reduziert werden.

**Nachher:**
```markdown
## DevOps-Spezifische Guards & Don'ts
- **IaC-Plan-Review:** Infrastruktur-Änderungen erfordern zwingend Plan-Review (`terraform plan` o.ä.) vor dem Merge.
- **Production-Gates:** Deployments in Prod erfordern manuelle Freigabe.
- **Secrets:** NIEMALS Secrets/Keys im Code/Config. Nutze Secrets-Manager.
- **Security-Scans:** Keine Pipeline ohne Security-Scans, kein Deployment ohne Image-Vulnerability-Scan.
```
*Effekt: Klarere Fokussierung auf die wesentlichen Restriktionen, Vermeidung von Token-Waste durch Doppelungen.*

### Vorschlag D: Pipeline-Phasen linearisieren
Die Pipeline-Struktur kann als linearer Flow dargestellt werden, statt in ein verschachteltes YAML-Objekt gegossen zu werden. Das LLM versteht Sequentialität in Textform sehr gut.

**Nachher:**
```markdown
**Pipeline-Standard-Flow:**
1. `Lint` (Code & Infra)
2. `Test` (Unit/Integration parallel)
3. `Build` (App, Container, Registry-Push)
4. `Security` (Deps, Container, Secrets)
5. `Deploy` (Staging -> Manual Approval -> Production)
6. `Verify` (Health & Integration)
```

## 4. Fazit
Durch die Umsetzung dieser 4 Maßnahmen kann der System-Prompt von `devops-engineer.md` von ca. 280 Zeilen auf unter 150 Zeilen komprimiert werden. Dies senkt den "Reasoning Effort" und die API-Kosten, verringert die Latenz beim Context-Processing und schärft die Persona-Instruktionen gemäß den aktuellen Best-Practices für AI-Agents.
