# Stakeholder Needs — Smart-Light IoT Controller

## SH-01: Hausbesitzer

- Need: Licht soll automatisch bei Bewegung im Raum eingeschaltet werden
- Need: Helligkeit der Beleuchtung soll sich dem vorhandenen Tageslicht anpassen (dunkler Raum = heller, heller Raum = gedimmt)
- Constraint: Maximale Reaktionszeit von Bewegungserkennung bis Licht-Einschaltung < 200ms

## SH-02: Elektriker

- Need: System muss mit bestehenden 230V-Installationsleitungen kompatibel sein (keine额外的 Verdrahtung erforderlich)
- Need: Klare Fehlerdiagnose-Schnittstelle mit standardisierten Fehlercodes fur schnelle Fehlersuche
- Constraint: Installation muss nach VDE 0100 und EN 60669 erfolgen

## SH-03: Cloud-Provider

- Need: Stabile und wiederherstellbare MQTT-Verbindung mit automatischem Reconnect bei Netzausfall
- Need: Bandbreiten-Effizienz — Sensor-Daten sollen komprimiert und nur bei Zustandsanderung gesendet werden
- Need: OTA-Update-Fahigkeit fur Firmware-Updates ohne physischen Zugang zum Gerat

## SH-04: Datenschutzbeauftragter

- Need: Bewegungsdaten durfen nicht persistent gespeichert werden — nur Echtzeitverarbeitung
- Need: Alle personenbezogenen Daten mussen DSGVO-konform verarbeitet werden (kein Cloud-Storage von Anwesenheitsdaten)
- Constraint: Bei Cloud-Ausfall muss die lokale Steuerung vollstandig weiter funktionieren (Privacy-by-Design)

## SH-05: Wartungstechniker

- Need: Remote-Diagnose-Funktion — Systemstatus, Sensorwerte und Fehlerhistorie mussen aus der Ferne abrufbar sein
- Need: Modulares Design — defekte Komponenten (Sensor, Aktor) mussen einzeln austauschbar sein ohne Gesamtsystem-Ausfall
- Need: Integrierte Selbsttest-Funktion die beim Systemstart alle Komponenten auf Funktionsfahigkeit pruft
