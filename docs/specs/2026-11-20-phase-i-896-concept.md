---
spec-id: CONCEPT-PHASE-I-896-2026-11-20
title: "Phase-I-Konzept #896 — Admin-UI Startmodus local/network"
issue: 896
roadmap-pr: "0.7"
package: P33
rank: 1
status: APPROVED
approved-by: "Nutzergo 2026-11-20 (E-31)"
date: 2026-11-20
kind: concept
implementation: "später — Welle 7 (Roadmap §3.9)"
---

# Phase-I-Konzept #896 — Admin-UI Startmodus `local`/`network`

> Status: APPROVED (Nutzergo 2026-11-20, E-31)
> Freigabe: Nutzer-go 2026-11-20 für E-31-Einzel-Specs („Specs schreiben/Status APPROVED setzen mit Verweis auf Nutzergo 20.11., keine neuen Entscheidungen erfinden“). Der Approval-Marker wird vom Nutzer gesetzt, nicht vom Autor.
> Herkunft: ausschließlich Issue #896 und die freigegebene Master-Roadmap (PR 0.7, P33, E-31, §3.7/§3.9, §6) sowie die daraus abgeleitete, dokumentierte Roadmap-Entscheidung 31 (N12). **Keine neuen Entscheidungen.**
> Dieses Dokument ist ein **Konzept**, kein Implementierungsplan und keine Spec mit Code.

## 1. Problemstellung (aus Issue #896)

`/admin-ui start` startet aktuell nur mit Defaults (Loopback `127.0.0.1`). Für Netzwerkzugriff
müssen `--host 0.0.0.0 --admin-token ... --allowed-hosts ...` manuell kombiniert werden; ohne
diese Kombination sehen Nutzer `ERR_CONNECTION_REFUSED`. Der Skill bietet damit keinen
expliziten, geführten Einstieg für den Netzwerkbetrieb.

Das Issue ist ein Follow-up zu #456. Es wird **nur referenziert**, nicht geschlossen — keine
Closing-Keywords (`Closes`/`Fixes`/`Resolves`) in Commit- oder PR-Texten.

## 2. Ziel / Soll-Zustand (aus Issue #896)

Der Admin-UI-Start-Skill bietet zwei explizite Modi:

- **local** (Default): `127.0.0.1`, kein Token.
- **network**: `0.0.0.0`, Token wird erzwungen — der Skill generiert ein Zufalls-Token,
  persistiert es nicht und gibt es nur aus; optional `--allowed-hosts`; der Skill gibt die
  erreichbaren URL(s) aus (`http://<ip>:7420/?token=<T>`).

Die Skill-Dokumentation enthält eine Port-Matrix (7420 / 8765 / 9090), Firewall-Hinweise und
eine Sicherheitswarnung für den network-Modus.

Offene Beobachtung aus dem Issue: Das Viz-Dashboard (8765) bindet bei `--host 0.0.0.0`
ebenfalls netzweit, während MCP (9090) auf Loopback bleibt — „ist das gewollt?“.
Die Roadmap-Entscheidung 31 (N12, dokumentiert in der Phase-I-Planung) beantwortet dies
bereits: **beide Dienste netzweit konfigurierbar** (Viz-Dashboard 8765 und MCP 9090), je
eigene Option mit sicherem Default. Das Konzept übernimmt diese vorhandene Entscheidung
und erfindet keine neue.

## 3. Scope

### In Scope (Konzept-Ebene)

- Explicit `local`/`network`-Modus-Wahl für `/admin-ui start` (local = Default).
- Erzwungenes Admin-Token im network-Modus (Zufalls-Token, nicht persistiert, nur ausgegeben).
- Ausgabe der erreichbaren URL(s) inklusive Token im network-Modus.
- Optionale `--allowed-hosts`-Unterstützung im network-Modus.
- Skill-Doku: Port-Matrix 7420/8765/9090, Firewall-Hinweise, Sicherheitswarnung network.
- Klärung/Dokumentation des Bindeverhaltens Viz-Dashboard (8765) vs. MCP (9090) gemäß
  Roadmap-Entscheidung 31.

### Out of Scope (explizit)

- **Implementierung / Code-Änderungen** — erfolgt später in Welle 7 (§3.9), eigener Plan + PR.
- **Keine Golden-Rebaseline** — PR 0.7 ist laut Roadmap §3.1 RB-frei; dieses Dokument ist
  reine Doku und rendert keine Agenten-/Rule-Templates.
- **Keine TDD-Code-Arbeit, keine Tests** — docs-only.
- Kein Schließen/Kommentieren von #896 oder #456; keine Änderung an Issue/PR-Status.
- Keine Änderung an Master-Roadmap, Worker-Control-Dateien, Batch0-Dateien, archivierten
  Plänen oder anderen Roadmap-Paketen.
- Keine neuen Entscheidungen über Issue #896 + Roadmap hinaus.

## 4. Vorgeschlagener Ansatz mit Alternativen

### Ansatz A — Zwei-Modi-Design (issue-konform, empfohlen)

`/admin-ui start` erhält einen expliziten Modus-Parameter. `local` ist Default und verhält
sich wie heute (Loopback, kein Token). `network` setzt `0.0.0.0`, erzwingt ein generiertes,
nicht persistiertes Zufalls-Token, akzeptiert optional `--allowed-hosts` und gibt die
erreichbare URL samt Token aus. Die Doku ergänzt Port-Matrix, Firewall-Hinweise und
Sicherheitswarnung. Das Bindeverhalten von 8765/9090 wird gemäß Entscheidung 31 dokumentiert.

- **Vorteile:** direkte UX-Abhilfe gegen `ERR_CONNECTION_REFUSED`; sicherer Default (local);
  kein Token-Handling durch den Nutzer im network-Modus.
- **Nachteile:** neues Interface am Skill; Token nur in der Ausgabe → bei Prozess-Neustart
  neuer Token.

### Ansatz B — Status quo (manuelle Flag-Kombination)

Keine Änderung; Nutzer kombinieren `--host`/`--admin-token`/`--allowed-hosts` selbst.

- **Vorteile:** kein Implementierungsaufwand.
- **Nachteile:** identifiziertes Problem (`ERR_CONNECTION_REFUSED`, Tokenerzeugung manuell)
  bleibt bestehen; erfüllt die Akzeptanzkriterien des Issues nicht. → verworfen.

### Ansatz C — Nur Doku ohne Modus-Parameter

Nur README/Skill-Hinweise ergänzen, kein expliziter Modus.

- **Vorteile:** minimaler Aufwand.
- **Nachteile:** Akzeptanzkriterium „explizite local/network Modus-Wahl“ nicht erfüllt.
  → verworfen.

### Bindeverhalten 8765/9090 — Alternativen

- **Variante 1 (issue-Beobachtung dokumentieren, nichts ändern):** war „dokumentieren statt
  ändern“ als Empfehlung; durch Roadmap-Entscheidung 31 **entschieden abgelehnt**.
- **Variante 2 (Entscheidung 31, gültig):** beide Dienste netzweit konfigurierbar, je eigene
  Option mit sicherem Default; eigene Spec; DRAFT-Plan danach in die User-Freigabe. →
  **vom Konzept übernommen**, keine neue Entscheidung.

## 5. Akzeptanzkriterien (aus Issue #896, Konzept-Ebene)

- [ ] `/admin-ui start` unterstützt explizite `local`/`network`-Modus-Wahl (`local` = Default).
- [ ] network-Modus erzwingt Admin-Token und gibt die erreichbare URL inkl. Token aus.
- [ ] Skill-Doku enthält Port-Matrix (7420/8765/9090), Firewall-Hinweis und Sicherheitswarnung
      für den network-Modus.
- [ ] Bindeverhalten von Viz-Dashboard (8765) vs. MCP (9090) bei `--host 0.0.0.0` ist gemäß
      Roadmap-Entscheidung 31 geklärt und dokumentiert.

Diese AKs beschreiben den **Soll-Zustand der späteren Umsetzung**; ihre code-seitige Erfüllung
wird in Welle 7 (§3.9) geprüft und ist nicht Gegenstand dieses Doku-PRs.

## 6. Risiken / Annahmen

- **Annahme:** Die Roadmap-Entscheidung 31 (N12) ist als dokumentierte Roadmap-Entscheidung
  bindend; das Konzept führt keine darüber hinausgehende Entscheidung ein.
- **Annahme:** Der vorhandene DRAFT-Plan `docs/plans/2026-10-07-admin-ui-network-and-manager-plan.md`
  (`SPEC-897-896-ADMIN-UI-NETWORK-2026-10-07`) ist die spätere Umsetzungsgrundlage; er wird in
  diesem PR **nicht** verändert oder freigegeben. Vor W7 ist er gegen den dann aktuellen Code
  (`scripts/admin-server.py`, `docs/ui/admin-ui.html`) neu zu prüfen (Phase-B-Änderungen #1173,
  #898, #317 können ihn berühren).
- **Risiko:** Token nur in der Start-Ausgabe → kein Persistenz-/Wiederherstellungsweg. Bewusst
  so gewollt (Issue: „nicht persistiert, nur ausgegeben“); kein neues Verhalten erfinden.
- **Risiko:** Port-Matrix und Firewall-Hinweise können mit der Zeit veralten → in der
  W7-Umsetzungsdoku gegen den Code verifizieren.
- **Keine Rebaseline / kein Render-Diff:** reine Markdown-Änderung ohne Template-/Rule-Änderung.
- **Abhängigkeit:** #456 nur referenzieren; keine Closing-Keywords verwenden (Issue-Vorgabe).

## 7. Traceability

| Artefakt | Bezug |
|---|---|
| Issue #896 | Quelle für Problemstellung, Modi, Port-Matrix, Firewall/Sicherheit, AKs, #456-Follow-up |
| Master-Roadmap §3.1, PR 0.7 | `docs/phase-i-<issue>`, P33, Rang 1–3 zuerst (#896, #339, #681), RB-frei |
| Master-Roadmap §1, P33 | Phase-I-Konzept-PRs; Reihenfolge P33; je S–M |
| Master-Roadmap §4, E-31 | Specs/Konzepte einzeln nach Review, Reihenfolge P33; Freigabe hiermit erteilt (Nutzergo 20.11.) |
| Master-Roadmap §3.7 / §3.9 | Welle 7: Phase-I-Umsetzungen, je Issue eigener Plan + PR **nach** APPROVED-Concept aus 0.7 |
| Master-Roadmap §6 | Issue-Hygiene: #896 nicht in Close-/Park-Listen → hier keine Statusänderung |
| Roadmap-Entscheidung 31 (N12) | Dokumentierte Antwort auf die offene 8765/9090-Frage (beide netzweit konfigurierbar, je eigene Option, sicherer Default) |
| Nutzer-go 2026-11-20 (E-31) | Approval für dieses Konzept; keine neuen Entscheidungen |

## 8. Umsetzung — späterer PR (Welle 7)

Dieser PR liefert **nur** das Konzept (`docs/specs/2026-11-20-phase-i-896-concept.md`).
Die Implementierung folgt in einem eigenen PR in **Welle 7 (Roadmap §3.9)**: je Issue eigener
Plan + PR nach diesem APPROVED-Concept. Dort werden die AKs code-seitig umgesetzt und geprüft.

**Docs-only:** kein TDD-Code, keine Tests, keine Rebaseline. Bewusst kein Self-Approve — der
StatusMarker `APPROVED` stützt sich auf den Nutzergo 20.11. (E-31).

## 9. Bestätigung — keine neuen Entscheidungen

Alle Aussagen dieses Konzepts stammen aus Issue #896 und der freigegebenen Roadmap
(PR 0.7 / P33 / E-31, §3.7, §3.9, §6) sowie der bereits dokumentierten Roadmap-Entscheidung 31.
Es wurden **keine neuen Entscheidungen erfunden**, keine Issue-/PR-Status geändert und keine
weiteren Roadmap-Pakete berührt.
