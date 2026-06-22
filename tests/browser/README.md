# Browser tests (Playwright)

Browser tests for the agent-meta admin UI. They boot a local `admin-server.py`
on port `7421` and drive it with a headless Chromium instance.

## Prerequisites

```bash
pip install playwright pytest
playwright install chromium
```

Python `>= 3.8` is required (same as the rest of the repo).

## Running

From the repo root:

```bash
pytest tests/browser/ -v
```

To see the browser while debugging, change `headless=True` to `headless=False`
in `conftest.py::browser_ctx`.

## Layout

| File | What it covers |
|------|----------------|
| `conftest.py` | Starts the admin server on :7421 and opens a shared Chromium context. |
| `test_routing.py` | Dashboard loads, `/#/config-audit` renders (Bug 2), Tier Presets edit tab opens. |
| `test_tier_presets_save.py` | Save in Edit Mappings does not fail with the legacy `mapping` validation error (Bug 3A) and per-provider override rows render (Bug 3B). |

## Notes

- The fixtures terminate the admin server when the session ends. If a previous
  run crashed, kill any stray process on port 7421 manually.
- Tests are read-only with respect to repo configs: clicking *Save Configs* on
  an unmodified Edit Mappings view writes the current YAML back unchanged.
