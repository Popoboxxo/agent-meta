# Conclusions: Admin-UI Model-Loading-Fix (fix/admin-ui-model-loading)
Datum: 2026-08-29

## Zusammenfassung
Die Bugfix-Pipeline für den Admin-UI Model-Loading-Fix (Commit 05423292, Branch `fix/admin-ui-model-loading`) wurde abgeschlossen: Audit → Fix → Tests → Review (PASS_WITH_NITS, Iteration 2) → Dokumentation. Drei Symptome (OpenCode-Modelle laden nicht, Preise laden unsauber, Datalists liefern falsche/fehlende Modelle) wurden auf drei Root-Causes zurückgeführt und behoben. `CODEBASE_OVERVIEW.md` Sektion 9 umfasst nun die Model-Loading-Chain mit allen Kernfunktionen und Endpunkten.

## Erkenntnisse & Aktualisierungen

1. **Root-Causes (Audit: `docs/plans/audit-admin-ui-model-loading.md`)**
   - **RC1:** Stiller models.dev-Fetch-Fehler ohne Registry-Fallback und ohne Negative-Cache — jede Anfrage versuchte erneut einen 30-s-Blocking-Fetch, Datalists blieben leer; die UI löschte zusätzlich Registry-Zeilen von modelsdev-überschriebenen Providern (RC1c).
   - **RC2:** Overlay-Import persistierte Bare-IDs unter dem Provider-Key, aber `_collect_models()` sucht Preise nach Registry-ID — importierte Preise für opencode-go waren eine stille No-Op; fehlende Preisfelder/Crash beim First-Import (FileNotFoundError im Backup-Schritt).
   - **RC3:** Suggestions lieferten Bare-IDs wo die lauffähige ID namespaced ist (`opencode-go/<raw>` — `roles.py::_resolve_tier_to_model` persistiert verbatim), und `_suggestions_from_registry()` degrade auf ALL-Provider-"Soup" (51 Cross-Provider-Modelle) bei nicht zuordenbaren Providern.

2. **Fixes Server (`scripts/admin-server.py`)**
   - Per-Modell-Registry-ID-Resolver `_resolve_registry_model_id()` (bare → namespaced → Unanimity-Fallback; **keine** hartcodierten Providernamen). Wichtig: Registry-ID-Konventionen sind **per Modell**, nicht per Provider — ein Provider-weiter Blanket-Präfix (Review-Iteration 1) hatte kanonische Claude-Suggestions in nicht lauffähige `anthropic/…`-IDs verwandelt; Iteration 2 ist per Modell.
   - `_load_models_dev_data(force_refresh=…)`: Negative-Cache 60 s (`_MODELS_DEV_ERROR_TTL_SECONDS`), Stale-Cache-Auslieferung stampft den Negative-Cache ebenfalls (Review-Iteration 2 / M1), Fetch-Failure-Reason im Error-Payload, `force_refresh` (↻-Button) API-First statt SDK-Snapshot.
   - Degrade `modelsdev` → Registry in `_handle_get_model_suggestions()` mit ehrlicher Source-Angabe; Registry-Suggestions ohne zuordenbaren Slug → `[]` statt Soup; Import schreibt registry-konforme Overlay-Keys via denselben Resolver.

3. **Fixes UI (`docs/ui/admin-ui.html`)**
   - Registry-Fallback-Zeilen mit `_registryFallback`-Flag/Badge statt Tabellen-Wipe; models.dev-Tabelle substituiert Registry-Zeilen ("registry (models.dev offline)") bei fehlendem Katalog-Node; ehrliche Empty-States mit Server-Reason bei `source === "error"`; Provider-Tier-Overrides-Datalist enthält die persistierten Werte.

4. **Testlage**
   - 602 Unit-Tests (`tests/test_admin_server.py` +19 Regression-Tests) und 32 Browser-Tests (`tests/browser/test_models_page.py` +2) grün.
   - Hinweis (pre-existing): pytest benötigt in dieser Umgebung `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1`.

5. **Dokumentation aktualisiert**
   - `docs/CODEBASE_OVERVIEW.md`: Header-Datum, Pfadkorrektur `docs/admin-ui.html` → `docs/ui/admin-ui.html`, neuer Sub-Abschnitt "Admin-UI Model-Loading-Chain" (Data-Flow, Kernfunktionen mit Signaturen, Endpunkte, UI-Fallbacks, Tests).

## Nächste Schritte
- Residual Observations aus dem Audit (bewusst out of scope): Initial-Load bevorzugt weiterhin den SDK-Snapshot ("SDK primary"), legacy Curation-Einträge ohne Match bleiben inert, Gemini benötigt `model-source-preference: {Gemini: modelsdev}` für nützliche Suggestions (Registry enthält keine google-Modelle in diesem Projekt).
- Git-Agent folgt: Commit des Fixes inkl. Doku auf `fix/admin-ui-model-loading` (kein Push in diesem Task).
