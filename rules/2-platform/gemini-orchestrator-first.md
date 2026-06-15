---
name: gemini-orchestrator-first
platform: gemini
version: 1.0.0
---
# Orchestrator-First — Gemini Platform

ALLE Entwicklungsaufgaben MÜSSEN über den orchestrator-Agenten gestartet werden.
Kein direkter Dispatch an developer, feature, se-* oder andere Worker-Agenten.

Ausnahmen: Nur lesende Diagnose-Operationen (read, grep, glob).
