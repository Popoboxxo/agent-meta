# Branch-Guard

Verwende Feature-Branches (`feat/`, `fix/`, `chore/`). Keine Code-Änderungen direkt auf `main` oder `master`.

## Guard-Terminologie: Convention Boundary vs. Security Boundary

- **Convention boundary**: fail-closed gegen AKZIDENTIELLEN Missbrauch (Tippfehler, vergessene Bestätigungen, naive Automatisierung); kein Schutz gegen gezielten Bypass.
- **Security boundary**: fail-closed gegen einen DELIBERATEN Umgehungsversuch.

## Submodule-Pushes (`--recurse-submodules=on-demand|only`)

Bei `=on-demand`/`=only` prüft der DoD-Push-Check jedes Submodul gegen sein
eigenes Push-Ziel (#1051). Ein geschütztes **oder** unbestimmbares Ziel
blockiert (fail closed); die Meldung nennt Submodul, Ziel und Ausweg (ohne
`--recurse-submodules` pushen, dann auf einen Feature-Branch). Ohne
`.gitmodules` unverändert.

## Bekannte Grenzen

Erkennung per Tokenizer, kein Shell-Parser — Indirektion (`eval`, `$(...)`, `xargs`) bleibt unerkannt.
Lücken-Liste (#551/#592/#809), Guard-Einstufung: `docs/concepts/branch-guard-known-limits.md`.
