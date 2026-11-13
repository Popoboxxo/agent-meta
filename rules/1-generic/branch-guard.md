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
Nicht erkannt (#551/#592/#809): `eval "git commit ..."`, direkte Schreibzugriffe auf `.git/`, andere Git-Tools (`hub`, `gh repo ...`), `$(...)`/Backticks als Indirektion.
Das Destructive-Gate (#809) sieht nur direkte `rm`-Aufrufe (kein `find -delete`, `xargs rm`, Variablen-Pfade, Pfad-Traversal).
Der DoD-Push-Check (#1210) nimmt den Branch aus dem effektiven Verzeichnis des Pushs (`-C`-Kette bzw. führendes `cd`, sonst Hook-cwd; Worktrees zählen). Nur ein FÜHRENDES `cd` wird aufgelöst; nicht auflösbare Ziele, `pushd`/`popd`, `--git-dir`/`--work-tree` und `GIT_DIR` bleiben fail-closed.
Einstufung: Convention boundary (Akzident-Netz, kein Ersatz für Backups); Security-Eigenschaften nur für das Destructive-Gate und den DoD-Push-Check (fail-closed ohne `python3`, #595).
