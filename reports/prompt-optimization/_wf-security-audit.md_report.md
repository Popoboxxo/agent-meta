# Prompt Optimization Report: `_wf-security-audit.md`

## 1. Executive Summary
Basierend auf den OpenAI und Lakera Best Practices sowie den agent-meta Framework-Regeln wurde eine umfassende Analyse des `_wf-security-audit.md` Workflows durchgeführt. Ziel war eine maximale Verschlankung (Token Reduction) und eine Verbesserung der Latenz, ohne die fachliche Tiefe der Security-Audits zu kompromittieren. Durch die Umstellung auf "Structured Prompting", "Chain-of-Symbol" und die Einführung von XML-Delimitern (Handoff-API) kann der Prompt signifikant beschleunigt und robuster gemacht werden.

## 2. Current State Analysis
Der aktuelle Prompt ist funktional, verschwendet jedoch wertvolle Tokens und Context Window Kapazitäten:
- **Token Inefficiency:** Die OWASP Top 10 Tabelle nutzt Markdown-Tabellen-Syntax (`|---|`), was viele Tokens für Formatierungszwecke verbraucht.
- **Verbosity:** Beschreibungen und Aufzählungen in Kategorien (B-E) sind zu prosaisch strukturiert.
- **Workflow-Logik:** Die nummerierte Liste verleitet das LLM zu weitschweifigem Chain-of-Thought (CoT) bei der Ausführung.
- **Output-Vertrag (API):** Das Markdown-Codeblock-Format für den Report ist schwach delimitiert und nutzt einen nicht-standardisierten Platzhalter (`<Projekt>`) anstelle der framework-eigenen Injection-Variablen (`{{PROJECT_NAME}}`).

## 3. Optimization Proposals & Actionable Insights

### 3.1 Structured Prompting & Density (Token Reduction)
**Maßnahme:** Ersetze die Markdown-Tabelle durch eine dichte Key-Value-Liste (YAML-ähnlich). LLMs parsen dies effizienter, ohne Kontext zu verlieren.
*Vorher:* `| A01 | Broken Access Control | Fehlende Autorisierungs-Checks, direkter Objekt-Zugriff |`
*Nachher:* `- A01 AccessControl: missing authz-checks, direct-obj-access`

### 3.2 Category Compression (Relevance Filtering)
**Maßnahme:** Komprimiere die Listen der Kategorien B bis E in dichte, kommagetrennte Arrays. Vermeide unnötige Zeilenumbrüche und Füllwörter.
*Beispiel:* `Deps: CVEs, wildcards (*,^,~), missing/uncommitted lockfile, duplicates`

### 3.3 Chain-of-Symbol (CoS) für den Audit-Workflow
**Maßnahme:** Wandle die Workflow-Liste in eine symbolische Kette (`->`) um. Dies hält den Reasoning-Buffer des Modells klein und forciert eine schnelle, lineare Abarbeitung ohne ausschweifende Erklärungen pro Schritt.
*Vorher:* `1. Scope: Glob auf /, src/...`
*Nachher:* `Workflow: Scope(src/,lib/,config/) -> ScanSecrets(grep) -> Deps(Lockfile+CVE) -> SupplyChain(Docker+CI) -> OWASP -> Crypto(Algorithms+TLS) -> Report`

### 3.4 Handoff Contract als XML-Schema
**Maßnahme:** Definiere das finale Report-Format innerhalb eines `<output_schema>` XML-Tags. Dies stärkt den API-Vertrag zwischen den Agenten (z.B. Security-Auditor und Orchestrator). Tausche zudem `<Projekt>` gegen den nativen Platzhalter `{{PROJECT_NAME}}` aus, der via `sync.py` zur Build-Zeit aufgelöst wird.

---

## 4. Final Streamlined Prompt (Proposal)

*Dieses Template kann direkt das alte `_wf-security-audit.md` ersetzen.*

```markdown
# Security Audit Workflow & Contract

## Audit Categories
OWASP_Top10:
- A01 AccessControl: missing authz-checks, direct-obj-access
- A02 Crypto: MD5/SHA1/DES, plaintext, weak-RNG
- A03 Injection: SQL-concat, shell/template-inj
- A04 Design: missing rate-limit, insecure defaults
- A05 Misconfig: debug-flags, CORS(*), missing sec-headers
- A06 VulnComp: CVEs, EOL-pkgs
- A07 Auth: weak-pw-policy, session-fixation
- A08 Integrity: unsigned pkgs, missing checksums
- A09 Logging: credentials in logs
- A10 SSRF: unvalidated URL-params for ext. requests

Targets:
- Secrets: `sk_, pk_, AKIA, ghp_, xox, Bearer, password=, secret=, api_key=`, hardcoded keys, PEM/DER, committed .env, base64 secrets, comment-credentials
- Deps: CVEs, wildcards (*,^,~), missing/uncommitted lockfile, duplicates
- SupplyChain: unpinned submodules, `curl|bash` in CI/CD, unpinned Docker (`latest`), CDN w/o SRI
- Crypto: MD5, SHA1, DES, 3DES, RC4, ECB, Math.random(), verify=False, rejectUnauthorized:false, RSA<2048, EC<256

## Workflow (Chain-of-Symbol)
`Scope(src/,lib/,config/) -> ScanSecrets(grep) -> Deps(Lockfile+CVE) -> SupplyChain(Docker+CI) -> OWASP -> Crypto(Algorithms+TLS) -> Report`

## Output Schema
Nutze exakt dieses Format für den finalen Report. Ersetze Platzhalter:

<output_schema>
# Security Audit Report — {{PROJECT_NAME}}
**Datum:** [YYYY-MM-DD] | **Status:** CRITICAL / WARN / CLEAN

## Executive Summary
[2-4 Sätze: Gesamtbefund, kritischste Findings, Sofortmaßnahmen]

## Findings
### [CRITICAL|HIGH|MEDIUM|LOW|INFO] — <Titel>
**Cat:** [A-E] | **File:** `path/to/file:line`
**Befund:** `[Snippet]`
**Risiko:** [Angriffsszenario]
**Fix:** [Maßnahme]

## Nicht geprüft
[Was bewusst ausgelassen und warum]

## Nächste Schritte
[Priorisierte Maßnahmen]
</output_schema>

**Severity-Legende:** CRITICAL (vor Deploy), HIGH (aktueller Sprint), MEDIUM (nächster Sprint), LOW (bei Gelegenheit)
```
