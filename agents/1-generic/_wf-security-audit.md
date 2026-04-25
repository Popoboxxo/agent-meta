# Security Audit — Kategorien & Report-Format

## Audit-Kategorien

### A — OWASP Top 10 (statisch erkennbar)

| ID | Titel | Prüfung |
|----|-------|---------|
| A01 | Broken Access Control | Fehlende Autorisierungs-Checks, direkter Objekt-Zugriff |
| A02 | Cryptographic Failures | MD5/SHA1/DES, Klartext-Speicherung, schlechte RNG |
| A03 | Injection | SQL-Concatenation, Shell-Injection, Template-Injection |
| A04 | Insecure Design | Fehlende Rate-Limiting, unsichere Defaults |
| A05 | Security Misconfiguration | Debug-Flags, offene CORS (`*`), fehlende Security-Header |
| A06 | Vulnerable Components | CVE-bekannte Dependency-Versionen, EOL-Packages |
| A07 | Auth Failures | Schwache Passwort-Policies, Session-Fixation |
| A08 | Software/Data Integrity | Unsigned packages, fehlende Integritätsprüfung |
| A09 | Logging/Monitoring | Credentials in Logs |
| A10 | SSRF | Unvalidierte URL-Parameter für externe Requests |

### B — Secrets & Credentials

Muster: `sk_`, `pk_`, `AKIA`, `ghp_`, `xox`, `Bearer `, `password=`, `secret=`, `api_key=`
- Hardkodierte Keys, private Schlüssel (PEM/DER), `.env`-Dateien committed
- Base64-kodierte Secrets, Credentials in Kommentaren

### C — Dependency-Risiken

- CVE-bekannte Versionen, Wildcard-Ranges (`*`, `^`, `~`)
- Lockfile vorhanden und committed? Doppelte Versionen?

### D — Supply-Chain

- Submodule ohne fixen Commit-Hash
- `curl ... | bash` in CI/CD
- Docker-Images ohne SHA-Pin (`FROM node:latest`)
- CDN-Links ohne SRI

### E — Kryptografie

Schwach: MD5, SHA1, DES, 3DES, RC4, ECB-Modus, `Math.random()`, `random.random()`
- `verify=False`, `rejectUnauthorized: false` — Zertifikats-Validierung deaktiviert
- RSA < 2048 Bit, EC < 256 Bit

---

## Audit-Workflow

```
1. Scope: Glob auf /, src/, lib/, config/, scripts/ + Stack identifizieren
2. Secrets-Scan: Grep auf Muster + .gitignore prüfen
3. Dependencies: Manifest + Lockfile + Wildcards + WebFetch bei konkretem CVE-Verdacht
4. Supply-Chain: .gitmodules + Dockerfiles + CI/CD-Configs
5. OWASP: Injection, SSRF, Path-Traversal, Deserialisierung, Auth
6. Kryptografie: Grep auf schwache Algorithmen + TLS-Configs
7. Report: Findings nach Severity + Datei + Zeile + Empfehlung
```

---

## Report-Format

```markdown
# Security Audit Report — <Projekt>

**Datum:** | **Status:** KRITISCH / WARNUNG / SAUBER

## Executive Summary
[2–4 Sätze: Gesamtbefund, kritischste Findings, Sofortmaßnahmen]

## Findings

### CRITICAL — <Titel>
**Kategorie:** | **Datei:** `src/config.ts:42`
**Befund:** [Code-Snippet]
**Risiko:** [Angriffsszenario]
**Empfehlung:** [Konkrete Maßnahme]

### HIGH / MEDIUM / LOW / INFO — <Titel>
[analog]

## Nicht geprüft
[Was bewusst ausgelassen und warum]

## Nächste Schritte
[Priorisierte Maßnahmen]
```

**Severity:** CRITICAL = vor nächstem Deployment | HIGH = aktueller Sprint | MEDIUM = nächster Sprint | LOW = bei Gelegenheit
