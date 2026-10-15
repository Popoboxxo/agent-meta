# Security Paved Roads

Security wird als vorgeprüfte Paved-Road-Blöcke geliefert, nicht als DIY-Aufgabe:
**invisible, consistent, embedded, non-optional** (Netflix Paved Roads / Golden Path).
Ein Block ist ausgereift, sicherheitsgeprüft und wird identisch überall verwendet —
niemand implementiert Security-Logik selbst neu.

## Block-Katalog

| Block | Abdeckt | Eigentümer-Agent |
|-------|---------|------------------|
| `auth-flow` | Authentifizierung (Login, Session, Token) | {{#if ROLE_SECURITY_AUDITOR_ACTIVE}}`security-auditor`{{else}}*(keine aktive Eigentümer-Rolle)*{{/if}} |
| `dependency-check` | SBOM + CVE-Scan der Abhängigkeiten | {{#if ROLE_DEPENDENCY_AUDITOR_ACTIVE}}`dependency-auditor`{{else}}*(keine aktive Eigentümer-Rolle)*{{/if}} |
| `input-validation` | Eingabevalidierung (Schema, Sanitizing) | {{#if ROLE_SECURITY_AUDITOR_ACTIVE}}`security-auditor`{{else}}*(keine aktive Eigentümer-Rolle)*{{/if}} |
| `rate-limiting` | Rate-Limiting / Throttling | {{#if ROLE_DEVOPS_ENGINEER_ACTIVE}}`devops-engineer`{{else}}*(keine aktive Eigentümer-Rolle)*{{/if}} |
| `cors-config` | CORS-Konfiguration | {{#if ROLE_SECURITY_AUDITOR_ACTIVE}}`security-auditor`{{else}}*(keine aktive Eigentümer-Rolle)*{{/if}} |
| `secret-scanning` | Secret-Scan (Leaks in Diffs, Commits, Logs) | {{#if ROLE_SECURITY_AUDITOR_ACTIVE}}`security-auditor`{{else}}*(keine aktive Eigentümer-Rolle)*{{/if}} |

## Enforcement

- **Vor jedem Commit:** Secret-Scan über den Block `secret-scanning` ausführen.
- **Vor jedem Deploy:** `dependency-check` (SBOM + CVE) ausführen.
- **Für neue Features:** den `auth-flow`-Block nutzen statt Auth selbst zu bauen.

DIY-Security ist eine Anti-Pattern: jede Variante erzeugt unbekannte Lücken.
{{#if ROLE_SECURITY_AUDITOR_ACTIVE}}
Abweichungen vom Block-Katalog werden als Review-Befund von `security-auditor`
{{else}}
Abweichungen vom Block-Katalog werden als Review-Befund
{{/if}}
gemeldet, nicht als Eigenbau gerechtfertigt.
