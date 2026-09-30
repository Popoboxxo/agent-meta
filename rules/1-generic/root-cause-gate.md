# Root-Cause-Gate

Verbindliches Gate vor jedem Fix. Normativ, sobald das aktive DoD-Preset Ursachen-Belege
verlangt (`dod.root-cause-required`); die Rule wird nur dann ausgeliefert (Rule-Gate
`root-cause-gate`, `requires: dod.root-cause-required`).

## Ursache vor Symptom

- Vor jedem Fix werden **Ursache und Vorversuche belegt**, nicht nur das beobachtete
  Symptom.
- Der Beleg enthält mindestens:
  1. die identifizierte Ursache — den Mechanismus, nicht das Symptom;
  2. die bereits unternommenen Vorversuche und warum sie nicht gegriffen haben;
  3. wie der geplante Fix genau diese Ursache adressiert.
- Ein Fix, der nur das Symptom ändert (Guard, Suppression, Retry, Timeout-Verschiebung
  ohne Ursachen-Beleg), erfüllt das Gate **nicht**.

## Wo das Gate greift

- Pipeline `bugfix`: Stage `root-cause` liegt zwischen `triage` und `fix`
  (`mode: sequential`).
- Pipeline `quick-fix`: Stage `root-cause` ist konditional über
  `condition: {dod_flag: root-cause-required}` verdrahtet.
- Die Aktivierung ist rein deklarativ über `config/role-defaults.yaml`, das DoD-Preset
  und `config/rules-presets.yaml` gesteuert; dieses Gate ist keine Rollen-Route.

## Fail-closed

- Liegt der Ursachen-Beleg nicht vor, startet der Fix nicht.
- Ist die Ursache nicht abschließend bestimmbar, wird der Versuch als Vorversuch
  dokumentiert und der Fix bleibt offen — es wird nicht geraten.
- Das Gate ist eine **Convention boundary**, keine Security boundary (Terminologie:
  `branch-guard.md#guard-terminologie-convention-boundary-vs-security-boundary`).
