# Branch-Guard

Verwende Feature-Branches (`feat/`, `fix/`, `chore/`). Keine Code-Änderungen direkt auf `main` oder `master`.

## Guard-Terminologie: Convention Boundary vs. Security Boundary

Guards im System (Orchestrator-Guard, DoD-Push-Check, etc.) werden inkonsistent als
"Konventions-Tool" und als "security boundary" bezeichnet — beide Aussagen sind korrekt,
aber gegen unterschiedliche Bedrohungsmodelle:

- **Convention boundary**: fail-closed gegen AKZIDENTIELLEN Missbrauch (Tippfehler,
  vergessene Bestätigungen, naive Automatisierung). Nicht darauf ausgelegt, einen
  gezielten Bypass-Versuch zu widerstehen (siehe Lücken unten, z.B. #592).
- **Security boundary**: fail-closed gegen einen DELIBERATEN Umgehungsversuch.

Diese Definition ist die zentrale Referenz — Hook-Header und andere Doku sollen sie
verlinken (`.claude/rules/branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`)
statt sie ad hoc zu wiederholen.

`orchestrator-guard.sh` ist primär eine **convention boundary** (siehe Lücken unten),
mit einzelnen **security-boundary**-Eigenschaften für spezifische Fälle (z.B. das
Destructive-Gate aus #516/#809, das auch bei gültigem `git`-Sentinel blockt). `dod-push-check.sh`
ist als **security boundary** gegen fehlendes/kaputtes `python3` fail-closed (#595).

## Submodule-Pushes (`--recurse-submodules=on-demand|only`)

Der DoD-Push-Check prüft bei `--recurse-submodules=on-demand` und `=only` jedes
Submodul einzeln statt pauschal das Vorhandensein einer `.gitmodules` zu blocken
(Issue #1051, ersetzt die Fail-closed-Pauschale aus #953):

- Die Submodul-Pfade werden einmal aus `.gitmodules` gelesen; jedes Submodul wird
  aus seiner eigenen Push-Konfiguration aufgelöst (`remote.<name>.push`, sonst
  `push.default` / `branch.<n>.merge`). Git gibt beim Rekursiv-Push nur den
  Remote-Namen weiter, nicht das Refspec des Superprojekts.
- Blockiert wird, sobald ein Ziel ein geschützter Branch (`main`/`master` oder der
  konfigurierte Main-Branch) ist **oder** nicht bestimmt werden kann (unlesbare
  oder unvollständige Konfiguration, abgekoppelter Submodul-HEAD,
  `push.default=nothing|matching`, Wildcard-Refspec). Die Meldung nennt
  Submodul-Pfad und Ziel.
- Ist ein Ziel nicht bestimmbar, nennt die Meldung den Ausweg: das Superprojekt
  ohne `--recurse-submodules` pushen und die Submodule anschließend explizit auf
  einen Feature-Branch pushen.
- Repositories ohne `.gitmodules` sowie die Werte `check` und `no` bleiben
  unverändert.

## Bekannte Grenzen

Die technische Durchsetzung (`orchestrator-guard.sh`) erkennt Git-Mutationen über eine tokenisierte Analyse des Bash-Befehls (gemeinsamer Tokenizer für Destructive- und Mutation-Gate, Issue #551), kein vollständiger Shell-Parser. Das Destructive-Gate deckt zusätzlich die kanonischen Shell-Katastrophen ab (Issue #809): rekursives `rm` auf einem gefährlichen Root (`/`, `~`/`$HOME`, Top-Level-Systemverzeichnisse wie `/etc`) sowie eine rekursive Fork-Bomb (`` :(){ :|:& };: ``). Benigne In-Repo-Löschungen (`rm -rf .tmp/...`) bleiben erlaubt. Bekannte Lücken:

1. `eval "git commit ..."` wird nicht erkannt.
2. Direkte Schreibzugriffe auf `.git/` werden nicht geprüft.
3. Andere Git-Tools (`hub`, `gh repo ...`) sind nicht erfasst.
4. Command-Substitution und Indirektion (`$(...)`, Backticks, `xargs`, `eval`) können eine Git-Mutation am Tokenizer vorbeischleusen, weil der Hook den Befehl weder ausführt noch die Shell vollständig parst (Issue #592). Ein echter Shell-Interpreter wäre unverhältnismäßig für ein Konventions-Tool. Für das FS-Destructive-Gate (#809) gilt dasselbe: nur direkte `rm`-Aufrufe (ggf. hinter `sudo`/`env`/KEY=VALUE) werden erkannt; indirekte Löschungen (`find ... -delete`, `xargs rm`, Variablen-/`$(...)`-Expansion eines Pfads, gequoteter ANSI-C-Pfad, `rm` über einen Wrapper-Alias), Pfad-Traversal (`rm -rf /var/tmp/../etc`) sowie eine als String-Literal gequotete `:(){ :|:& };:`-Definition bzw. indirekte Fork-Bombs (`eval`, base64) bleiben möglich — ein Tippfehler-/Akzident-Netz, kein Ersatz für Backups.

Bewusster Trade-off, kein Bug (siehe Kommentar-Header in `.claude/hooks/orchestrator-guard.sh`) — nur relevant für Nutzer, die sich vollständig auf den Schutz statt auf die Konvention verlassen.
