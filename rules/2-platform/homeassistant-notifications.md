# Notifications & Debug-Modus

## Notification-Gruppen

| Gruppe | Entity | Verwendung |
|--------|--------|------------|
| **Standard** | `notify.{{platform.homeassistant.notify_group}}` | Normale Benachrichtigungen an alle Bewohner |
| **Admin/Debug** | `notify.{{platform.homeassistant.notify_admin_group}}` | Administrative und Debug-Meldungen |

## Debug-Modus

- **Sensor**: `{{platform.homeassistant.debug_sensor}}`
- Im eingeschalteten Zustand: Sende Zwischenschritt-Benachrichtigungen an die Admin-Gruppe

### Pattern: Debug-Check in Automations

```yaml
- condition: state
  entity_id: {{platform.homeassistant.debug_sensor}}
  state: 'on'
- action: notify.{{platform.homeassistant.notify_admin_group}}
  data:
    message: "DEBUG: [Automatisierungsname] — Zwischenschritt [N] erreicht"
```

### Best Practice
- Debug-Conditions immer **vor** dem eigentlichen Action-Block einfügen
- Message-Text: `"DEBUG: [Automation-Alias] — [was gerade passiert ist]"`
- Nach Debugging: `{{platform.homeassistant.debug_sensor}}` wieder auf `off` setzen — nie im Code lassen

## Actionable Notifications (iOS/Android)

- Actionable Notifications ermöglichen Schaltflächen direkt in der Push-Benachrichtigung
- Events werden als `mobile_app_notification_action` gefeuert
- Kamera-Snapshots: Via `camera.snapshot` vor dem Notify-Call erstellen, dann als `image:` anhängen

### Reload vs. Restart

| Änderung | Erforderlich |
|----------|-------------|
| YAML-Änderungen (Automations, Templates) | **Quick Reload** (Developer Tools → YAML) |
| Neue Domain hinzugefügt (z.B. neues `input_boolean`) | **Full Restart** |
| Package-Struktur geändert | **Full Restart** |
