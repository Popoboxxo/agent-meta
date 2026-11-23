# ADR 0003: `entry_prefix` — Ausnahme von IC-4 (byte-identische Migrations-Invariante)

- Status: Accepted
- Datum: 2026-11-23
- Bezug: #1167, #1339, `docs/specs/2026-11-11-req-id-format-1167-spec.md` (IC-4), `docs/concepts/2026-08-18-convention-profiles.md` (Abschnitt 8)

## Kontext

Issue #1167 hat mit der Spec `docs/specs/2026-11-11-req-id-format-1167-spec.md` das kanonische REQ-ID-Format `REQ-<AREA>-<NN>` festgelegt (D-H4, Ziffernzahl `\d{2,3}` durch User-Entscheidung 22.11.). Deren Interface Contract IC-4 listet unter „Zu ändernde Stellen" auch `config/conventions-presets.yaml:34` (`entry_prefix: "REQ-xxx: "`) auf (`docs/specs/2026-11-11-req-id-format-1167-spec.md:120-121`).

Gleichzeitig pinnt `tests/test_conventions_migration_invariant.py` genau diesen String als byte-identische Migrations-Invariante: `EXPECTED_CHANGELOG_BLOCK` enthält `REQ-xxx:` an drei Stellen (`:37`, `:40`, `:43`, Block `:32-48`), und `test_default_changelog_block_is_byte_identical` (`:74-78`) vergleicht den gerenderten `RELEASE_CHANGELOG_BLOCK` exakt damit. Eine Änderung des Präfixes bricht diese Invariante. Das Konzept `docs/concepts/2026-08-18-convention-profiles.md:216,228` hält dieselbe Invariante fest (Migrationspfad Abschnitt 7, offene Risiken Abschnitt 8).

Die Spec selbst trifft keine neue Produktentscheidung („diese Spec trifft keine neue Produktentscheidung", `docs/specs/2026-11-11-req-id-format-1167-spec.md:28`; „keine neue Entscheidung", `:182`); der #1339-Abschlussbericht verlangte für genau diese Abweichung einen dauerhaften ADR-/Issue-Vermerk. Die Abweichung ist damit zu dokumentieren, nicht neu zu entscheiden.

## Entscheidung

- `entry_prefix: "REQ-xxx: "` im `default`-Preset bleibt unverändert (`config/conventions-presets.yaml:34`, inkl. des dortigen Hinweises `:35-37`).
- Die byte-identische Migrations-Invariante (`tests/test_conventions_migration_invariant.py:32-48,74-78`) rangiert vor dem Format-Inventarpunkt IC-4 der #1167-Spec. IC-4 bleibt gelistet, wird an dieser Stelle aber bewusst nicht angewendet.
- Reine Festschreibung der bereits getroffenen Entscheidung: keine neue Produktentscheidung, kein Code-, Config- oder Test-Change, kein Breaking Change.

## Konsequenzen

- `config/conventions-presets.yaml:34` ist die dokumentierte Ausnahme in IC-4; die übrigen IC-4-Stellen sind von dieser Ausnahme nicht betroffen.
- Jede künftige Änderung an `entry_prefix` verlangt zuerst eine Aktualisierung des Invarianz-Tests (`tests/test_conventions_migration_invariant.py:32-48,74-78`) und einen eigenen ADR — analog zu ADR 0001 („Jede weitere Runtime-Dependency erfordert einen eigenen ADR").
- #1167 und #1339 werden als reine Verweise zitiert; keine Closing-Keywords (Entscheidung 38e der #1167-Spec), #1167 bleibt in Phase H nicht geschlossen.
- Pointer auf diesen ADR stehen in `docs/specs/2026-11-11-req-id-format-1167-spec.md:121` (IC-4) und `docs/concepts/2026-08-18-convention-profiles.md:229` (Abschnitt 8).
