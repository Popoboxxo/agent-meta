# Literature-Anchored Role Enrichment — O'Reilly "Cybersecurity Month 2026"

## STATUS

- **Date:** 2026-10-04
- **HEAD:** `43ca7e1d` (`main`)
- **VERSION:** 1.0.0
- **Mode:** Plan — keine Implementierung. Dieses Dokument ist die einzige Änderung dieses PRs:
  keine Rollen-Templates, Configs, Skripte oder Generator-Läufe.
- **Quelle:** Humble Bundle „Cybersecurity Month 2026 by O'Reilly" — 20 Items, davon **19 Bände**
  übernommen (1 Dublette ausgesondert). Import 2026-10-04, Calibre-IDs 714–732,
  indexiert in den lokalen Literatur-Index (8.289 Chunks).
- **Evidenz-Basis:** Semantische Suche über den Literatur-Index, **24 Queries über 12 bestehende
  Rollen + 1 Rollen-Kandidat**, ausgewertet auf **Abschnitts-Ebene** der Quellbände.
- **Abgrenzung:** Unabhängig von PR #840 (`feat/ai-agent-roles-literature-2026`). Dort wurden 4
  KI-Agenten-Rollen aus einer 50-Bücher-Analyse ergänzt; hier geht es um Security-Belege aus einem
  anderen Korpus für **andere** Rollen. Keine gemeinsamen Dateien, keine Reihenfolge-Abhängigkeit.
- **Empfehlung:** **4 Rollen primär** (`log-analyzer`, `dependency-auditor`, `devops-engineer`,
  `concept-architect`), **6 Rollen sekundär**, **1 Rollen-Kandidat** (`security-engineer`).
- **Ziel-VERSION (bei Umsetzung):** 1.2.0 (Minor — Belege in bestehenden optionalen Feldern,
  keine neuen Pflichtfelder).

---

## 1. Anlass

Das Framework deckt Security heute nur in **Spezialrollen** ab (`dependency-auditor`,
`incident-responder`, `se-verifier`, `log-analyzer`). Mit dem O'Reilly-Korpus stehen 19
Security-Bände auf aktuellem Stand (2023–2025) bereit, die mehrere Rollen mit **prüfbaren
Belegen** stützen können — im etablierten Muster dieses Repos: eine konkrete Regel im
Rollenkörper, belegt durch `(Autor, ch. N)` bzw. einen Abschnittsverweis.

Dieser Plan beantwortet **welche Inhalte welcher Rolle zugeordnet werden können** — als
Entscheidungsvorlage, nicht als fertige Formulierung.

## 2. Methode

1. **Quelle erschlossen:** 19 EPUBs geladen, Metadaten gegengeprüft (20/20 sauber), in Calibre
   übernommen (Katalog 617 → 636), in den Literatur-Index geschrieben (19/19, `EXIT 0`).
2. **Query-Set:** pro Rolle zwei englische Queries auf die *Fähigkeit* (nicht auf das Buch),
   z. B. `log-analyzer` → „log correlation and detection engineering for security events".
   24 Queries über 13 Rollen.
3. **Auswertung:** Alle Queries in einem Batch-Lauf gegen den Index (jeder Shard einmal geöffnet),
   Top-12-Treffer je Query. Treffer auf **Abschnitts-Ebene** der Bücher, mit Cosine-Score.
4. **Treffer, die aus dem neuen Korpus stammen, wurden markiert** und gegen die im Index bereits
   vorhandenen Bände derselben Domäne verglichen.

**Belastbarkeit:** Die Scores sind Ähnlichkeitsmaße, keine inhaltliche Prüfung. Ein Abschnitts-Titel
kann ein Kandidat sein, ohne die Behauptung bereits zu tragen. Die Belege sind daher als
**Fundstellen** zu lesen, die im Implementierungs-PR am Volltext zu verifizieren sind — nicht als
bereits geprüfte Aussage.

**Reproduzierbarkeit:** Query-Set und Rohtreffer liegen als Artefakte vor
(`agent_queries_security2026.json`, `lit_hits_security2026.json`, `analyze_security_hits.py`).

## 3. Befund: Rollen mit Belegpotenzial

Legende: **★** = Beleg aus dem neuen Korpus. Score = Cosine-Ähnlichkeit.
„Neu/Treffer" = Anzahl neuer Belege an der Gesamtzahl der Top-Treffer der Rolle.

### 3.1 `log-analyzer` — dichtestes Feld (5 von 12)

| Beleg (★ = neu) | Abschnitt | Score |
|---|---|---|
| ★ Security as Code | Metrics | 0.722 |
| ★ Practical Cloud Security | Searching and Correlation | 0.720 |
| Digital Forensics and Incident Response | Log file searching | 0.691 |
| ★ Defensive Security Handbook | Security Information and Event Management | 0.690 |
| ★ Kubernetes Security and Observability | Implementing Observability for Kubernetes | 0.680 |
| Digital Forensics and Incident Response | Filtered log review | 0.670 |

**Ist-Zustand der Rolle:** Frequency-Clustering, RFC-5424-Severity, Log-Qualität,
Baseline-vs-Anomalie, Korrelation mit Traces und Metriken.
**Lücke:** Die Rolle ist ein **allgemeiner Applikations-Log-Analysator**. Es fehlt die
Security-Dimension: SIEM-Denken, Korrelationsregeln, Unterscheidung Audit-Log vs.
Anwendungs-Log, Erkennung von Log-Manipulation.
**Vorschlag:** Eine Regelergänzung zur **Security-Signifikanz** von Log-Ereignissen, belegt über
Defensive Security Handbook (SIEM) und Practical Cloud Security (Correlation).

### 3.2 `dependency-auditor` — präziseste Einzeltreffer (4 von 11)

| Beleg (★ = neu) | Abschnitt | Score |
|---|---|---|
| ★ Identity Security for Software Development | SBOMs | 0.775 |
| ★ Software Supply Chain Security | Transparency of a device | 0.772 |
| The Embedded Linux Security Handbook | Technical requirements | 0.745 |
| ★ Zero Trust Networks | Trusting Builds | 0.669 |

**Ist-Zustand der Rolle:** SBOM-Formate (CycloneDX/SPDX, ISO/IEC 5962), transitive Closure,
Provenance (Registry/Maintainer), OSV-/NVD-Verifikation, Lizenzmatrix, Risikokategorien.
**Lücke:** Alle Belege adressieren **Build-Integrität** — Signierung, Attestierung, Vertrauen in
den Build selbst. Die Rolle prüft, *was* eingebunden ist, aber nicht, *woraus* es gebaut wurde.
**Vorschlag:** Eine Regel zur **Build-Provenance** (Signaturen/Attestierung) neben der bisherigen
Artefakt-Inventarisierung.

### 3.3 `devops-engineer` — breiteste Lücke (5 von 11)

| Beleg (★ = neu) | Abschnitt | Score |
|---|---|---|
| ★ Kubernetes Security and Observability | Choice of Operating System | 0.733 |
| ★ Identity Security for Software Development | Best Practices for Kubernetes Security | 0.728 |
| ★ Security as Code | Infrastructure as Code | 0.714 |
| ★ Intelligent Continuous Security | Dynamic Application Security Testing | 0.702 |
| ★ Security Architecture for Hybrid Cloud | A Distributed Version Control System | 0.702 |

**Ist-Zustand der Rolle:** CI/CD-Pipelines, IaC, Containerisierung, Observability; Security
im Kern als ein Punkt („keine Secrets im Code").
**Lücke:** Cluster-Härtung, RBAC, Network Policy, Admission Control, DAST in der Pipeline,
Secure-Defaults für Managed Services. Der Security-Anteil der Rolle ist der dünnste aller
untersuchten Rollen.
**Vorschlag:** Ein eigener Security-Abschnitt für **Cluster- und Pipeline-Härtung**.

### 3.4 `concept-architect` — direkt anschlussfähig (5 von 12)

| Beleg (★ = neu) | Abschnitt | Score |
|---|---|---|
| ★ Security Architecture for Hybrid Cloud | Security Architecture for Hybrid Cloud | 0.763 |
| ★ Zero Trust Networks | Evaluation of input sources by the trust algorithm | 0.755 |
| ★ Web Application Security | Zero Trust Design Pattern | 0.719 |

**Ist-Zustand der Rolle:** Komponentenzerlegung, Schnittstellen, Trade-offs, Qualitätsattribute
(Fowler-Schule).
**Lücke:** Die **Trust-Boundary-Betrachtung** fehlt vollständig — wo verläuft die
Vertrauensgrenze, welche Angriffsfläche entsteht durch eine Komponente, welche Daten dürfen
Grenzen queren.
**Vorschlag:** Trust Boundaries als **Pflichtbestandteil der Komponentenzerlegung**.

### 3.5 `code-reviewer` (7 von 12 — höchste Neu-Quote, niedrigere Scores)

| Beleg (★ = neu) | Abschnitt | Score |
|---|---|---|
| ★ Software Supply Chain Security | Secure Development Lifecycle Control 04 | 0.695 |
| ★ Web Application Security | Search Engines | 0.675 |
| ★ Practical Cloud Security | Warning | 0.663 |
| ★ Security Architecture for Hybrid Cloud | Integration testing | 0.655 |

**Ist-Zustand der Rolle:** Blast-Radius-Analyse, SOLID/DRY, Signal-Disziplin, Review-Qualität.
**Lücke:** Schwachstellen-Klassen und Secure-Coding-Muster fehlen als Review-Kriterium.
**Hinweis:** Die vergleichsweise niedrigen Scores und teils unspezifischen Abschnitts-Titel
(„Search Engines", „Warning") machen diese Zuordnung **am schwächsten belegt** — im Plan daher
sekundär geführt. Anschluss besteht bereits über `config/review-rules/security.yaml`
(SEC-01…SEC-06 mit OWASP-/CWE-`standard_ref`); dort wäre eine Review-Regel der natürliche Ort,
nicht im Template.

### 3.6 `api-specialist` (4 von 10)

| Beleg (★ = neu) | Abschnitt | Score |
|---|---|---|
| ★ Web Application Security | Query Parameter Tampering | 0.704 |
| ★ Software Supply Chain Security | Securing APIs | 0.695 |
| ★ Learning Serverless Security | No authentication and authorization mechanisms | 0.652 |

**Ist-Zustand der Rolle:** OpenAPI/Contract-First, Schnittstellenspezifikation, Versionierung.
**Lücke:** Angriffsklassen auf die *eigene* Schnittstelle — Parameter-Manipulation,
Authn/Authz-Lücken, Rate-Limiting.
**Vorschlag:** Ein Prüfschritt „Angriffsfläche der spezifizierten Schnittstelle".

### 3.7 `app-lifecycle-governor` (4 von 13)

| Beleg (★ = neu) | Abschnitt | Score |
|---|---|---|
| ★ Building a Cyber Risk Management Program | Risk-Based Strategy and Execution | 0.655 |
| ★ Software Supply Chain Security | ISO 31000:2018 Risk Management standard | 0.609 |
| ★ Defensive Security Handbook | Asset Management and Documentation | 0.584 |

**Ist-Zustand der Rolle:** Ownership, SLA, Data-Classification, Deprecation, Orphan-Erkennung,
Tech-Debt-Index.
**Lücke:** Der Risiko-Index ist qualitativ. **ISO 31000** und risikobasierte Priorisierung
geben ihm eine Methodik.
**Vorschlag:** Risikobewertung an eine Norm binden statt frei zu schätzen.

### 3.8 Weitere Rollen mit Belegen (sekundär)

| Rolle | Neu/Treffer | Stärkster Beleg | Score |
|---|---|---|---|
| `sre-engineer` | 3/7 | ★ Intelligent Continuous Security · ARO-Plattform | 0.678 |
| `validator` | 5/14 | ★ Building a Cyber Risk Mgmt Program · SEC and Risk Disclosure | 0.580 |
| `product-manager` | 2/7 | ★ Defensive Security Handbook · Risk Management Framework | 0.589 |
| `prompt-engineer` | 1/10 | ★ Privacy and Security for LLMs · Standardized Attack Success Metrics | 0.754 |

`prompt-engineer` verdient trotz nur eines Treffers Beachtung: **„Standardized Attack Success
Metrics"** liefert der Rolle eine **Messgröße** für Prompt-Robustheit — messbare
Angriffs-Erfolgsraten statt qualitativer Einschätzung.

## 4. Kandidat: neue Rolle `security-engineer`

**7 von 12 Treffern aus dem neuen Korpus** — der klarste Einzelbefund der Analyse:

| Beleg (alle ★) | Abschnitt | Score |
|---|---|---|
| Web Application Security | Threat Modeling Applications | 0.693 |
| Kubernetes Security and Observability | Use a Managed Kubernetes Service | 0.647 |
| Learning Cloud Security | Encryption algorithms | 0.642 |
| Security Architecture for Hybrid Cloud | Threat Modeling | 0.635 |
| The Cybersecurity Manager's Guide | Defense-in-depth model | 0.633 |

**Begründung:** Das Framework hat Rollen für *Prüfung* (`dependency-auditor`),
*Reaktion* (`incident-responder`), *Verifikation* (`se-verifier`) und *Analyse*
(`log-analyzer`), aber **keine Rolle für Bedrohungsmodellierung und Verteidigungsdesign** —
also für die *vorausschauende* Arbeit. Threat Modeling erscheint in der Analyse als
eigenständiger Beleg zweimal, defense-in-depth und encryption algorithms kommen hinzu.

**Zu beachten:** Eine neue Rolle berührt `config/role-defaults.yaml`, Routing-Patterns und die
Template-Freeze-Mechanik — d. h. den in PR #840 beschriebenen Golden-Pfad. Der Kandidat ist
daher als **eigener Folge-PR** zu behandeln, nicht im selben Änderungssatz wie die Beleg-Ergänzungen.

## 5. Korrekturen gegenüber dem Keyword-Mapping

**Wichtige Korrektur, weil sie die Auswahl steuert:** Ein vorgelagertes **Keyword-Mapping** hatte
`incident-responder` als stärkstes Ziel ausgewiesen. Das ist **falsch**. Die semantische
Auswertung findet für diese Rolle nur **einen** Beleg aus dem neuen Korpus (Blue Team Handbook ·
„When NIST", 0.735) — hinter **fünf** Bänden, die bereits im Index liegen:

| Bestandsband | Abschnitt | Score |
|---|---|---|
| CompTIA Security+ Certification Guide | Incident response exercises | 0.772 |
| Cybersecurity Attack and Defense Strategies | On-call process | 0.758 |
| Foundations of Modern Information Security | National Institute of Standards and Technology | 0.736 |
| Blue Team Handbook · Incident Response (neu) | When NIST | 0.735 |
| Digital Forensics and Incident Response | Post-Incident Activity | 0.724 |
| Practical Cyber Intelligence | Detection and analysis | 0.700 |

**Fazit:** Incident Response ist im Framework **bereits gut abgedeckt**. Der Blue Team Handbook
ist der dichteste Band des Korpus (477 Chunks), aber **nicht die Lücke**. Die Lücken liegen in
Cloud, Kubernetes, Supply Chain und Architektur.

**Weitere Rollen ohne Nutzen aus diesem Korpus:** `product-manager`, `validator` und
`app-lifecycle-governor` erhalten ausschließlich schwache Treffer (0.580–0.655) und teils
unspezifische Abschnitts-Titel. Sie sind als „nice to have" geführt, nicht als Empfehlung.

**Bände mit geringem Erwartungswert für Engineering-Rollen:** Inside Cyber Warfare (Geopolitik),
The Cybersecurity Manager's Guide (Management-Sicht), Learning Cloud Security und
Learning Serverless Security (Einstiegsniveau). Sie bleiben als Referenz im Index, sind aber
keine Belegquelle für Rollen-Regeln.

## 6. Vorgeschlagenes Vorgehen

**Phase 1 — Beleg-Ergänzungen (Primär, 4 Rollen)**
`log-analyzer`, `dependency-auditor`, `devops-engineer`, `concept-architect`.
Je Rolle 1–2 Regeln im Rollenkörper, Beleg inline nach etabliertem Muster. Zielpfad:
`agents/1-generic/<rolle>.md`, optional `reference_standards` im Frontmatter.

**Phase 2 — Beleg-Ergänzungen (Sekundär, 6 Rollen)**
`code-reviewer` (via `config/review-rules/security.yaml`), `api-specialist`,
`app-lifecycle-governor`, `sre-engineer`, `validator`, `prompt-engineer`.

**Phase 3 — Rollen-Kandidat (separat)**
`security-engineer` als eigener PR inkl. `config/role-defaults.yaml`, Routing-Patterns und
Golden-Pfad.

**Verifikation je Phase:** `python3 scripts/sync.py --validate` → exit 0;
`python3 scripts/consistency-check.py` → keine neuen Findings;
volle pytest-Suite → keine neuen Fehlschläge. Vor dem Edit ist der **Volltext** der genannten
Abschnitte zu lesen — die Scores sind Hinweise, kein Nachweis.

## 7. Nicht-Ziele

- **Keine** Änderung an Rollen-Templates, Configs oder Skripten in diesem PR.
- **Keine** Berührung der Golden-Fixtures oder der Template-Slimming-Mechanik.
- **Kein** Eingriff in PR #840 oder dessen Branch.
- **Keine** Behauptung, die zitierten Abschnitte seien bereits inhaltlich geprüft.
