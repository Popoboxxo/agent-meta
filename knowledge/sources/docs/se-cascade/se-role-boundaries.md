# SE Role Boundaries — Trennung Requirements vs. Architect

> Quelle: `docs/concepts/se-pipeline-extension.md` — Lösung B
> Relevante REQs: REQ-SE-10, REQ-SE-11, REQ-SE-12, REQ-SE-13

---

## Prinzip

Per ISO/IEC 15288 sind Stakeholder Requirements (L1-SH) strikt von System Architecture zu trennen:

- **`se-requirements`** formuliert WAS das System leisten soll (Black-Box, messbar)
- **`se-architect`** entscheidet WIE es das leistet (White-Box, Topologie, Technologie)

Der `arch_impact`-Flag ist die Brücke: Requirements signalisiert Architekturbedarf, ohne die Entscheidung selbst zu treffen.

---

## `se-requirements` — Was ist ERLAUBT?

| Aktivitaet | Beispiel |
|------------|----------|
| Stakeholder-Bedarfe in messbare Black-Box-REQs ueberfuehren | "System soll 500ml Wasser in 120s auf 90C erhitzen" |
| REQ-IDs vergeben | REQ-L1-001 |
| Domaenen zuweisen | `system` / `software` / `hardware` / `mechanics` |
| Externe Schnittstellen am Systemrand erfassen | "230V AC Eingang", "Heisswasser-Auslauf" |
| Akzeptanzkriterien definieren | "RPO=0, RTO<30s" |
| Priorisieren | mandatory / desired / optional |
| **Arch-Impact flaggen** (NEU) | `arch_impact: true, arch_trigger: "decoupled async processing"` |
| Konflikte erkennen und eskalieren | "REQ-L1-003 widerspricht REQ-L1-007" |

## `se-requirements` — Was ist VERBOTEN?

| Verbotene Aktivitaet | Gegenbeispiel |
|-----------------------|---------------|
| Architektur-Pattern waehlen | "Microservice-Architektur mit Event-Bus" |
| Technologien festlegen | "PostgreSQL als primaerer Datenspeicher" |
| Systemgrenzen verschieben / neue Subsysteme erfinden | "Wir brauchen einen Auth-Service" |
| Deployment-Topologien festlegen | "Kubernetes mit 3 Replikas" |
| Interne Schnittstellen designen | "REST-API zwischen UI und Backend" |
| Trade-offs zwischen Alternativen entscheiden | "REST statt gRPC, weil einfacher" |
| Protokolle waehlen | "MQTT fuer IoT-Sensoren" |
| Datenmodelle entwerfen | "Users-Tabelle mit FK auf Sessions" |

---

## `se-critic` — Role Boundary Check

Der Critic fuehrt bei `review_target: "requirements"` einen zusaetzlichen Pruefschritt durch:

### Verbotsbegriffe-Liste

Architektur-Pattern: `microservice`, `event-bus`, `event-sourcing`, `monolith`, `CQRS`, `hexagonal`, `layered`
Technologien: `PostgreSQL`, `MySQL`, `MongoDB`, `DynamoDB`, `RabbitMQ`, `Kafka`, `Redis`, `S3`, `Docker`, `Kubernetes`, `nginx`
Protokolle: `REST`, `gRPC`, `GraphQL`, `MQTT`, `AMQP`, `WebSocket`, `SOAP`, `JWT`, `OAuth2`, `mTLS`
Deployment: `replicas`, `load-balancer`, `auto-scaling`, `helm chart`, `terraform`, `pod`, `container`
Datenmodelle: `users table`, `foreign key`, `normalized`, `denormalized`, `index on`, `primary key`

### Bei Verstoss

```
status: "rejected"
correction_hint: "REQ-L1-XXX verletzt Rollentrennung. Reformuliere als
  Verhaltensanforderung und setze arch_impact: true mit arch_trigger."
role_boundary.violations[]: { req_id, violation_type, forbidden_term, description }
```

---

## Beispiele

### Falsch (Rollenverletzung)

```json
{
  "req_id": "REQ-L1-005",
  "statement": "Das System soll RabbitMQ als Message-Broker verwenden um Auftraege zu queueen.",
  "domain": "software"
}
```

### Korrekt

```json
{
  "req_id": "REQ-L1-005",
  "statement": "Das System soll Auftragsannahme und Auftragsverarbeitung zeitlich entkoppeln, sodass Annahme-Latenz unabhaengig von Verarbeitungsdauer ist.",
  "domain": "system",
  "arch_impact": true,
  "arch_trigger": "decoupled async processing required (annahme/verarbeitung)",
  "acceptance_criteria": [
    "Annahme < 100ms p95",
    "Keine Auftragsverluste bei Verarbeitungs-Crash",
    "Verarbeitung skalierbar unabhaengig von Annahme"
  ]
}
```

### Kein Arch-Impact noetig (atomare REQ)

```json
{
  "req_id": "REQ-L1-020",
  "statement": "Das System soll Passwoerter mit mindestens 12 Zeichen verlangen.",
  "domain": "software",
  "arch_impact": false
}
```

---

## Workflow-Konsequenz

```
se-requirements → se-critic (mit Role Boundary Check)
                           ↓
                    approved → se-architect (erhaelt arch_trigger-Liste)
                    rejected → se-requirements (korrigieren)
                    blocked  → se-orchestrator (fundamentales Problem)
```

Der `se-architect` muss in seinem `architectural_rationale` explizit auf jeden `arch_trigger` eingehen und dokumentieren: gewaehlte Loesung, verworfene Alternative, warum.
