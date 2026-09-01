---
name: admin-server-test-run-gotcha
description: admin-server tests need -p no:homeassistant (OpenSSL `lib` collides with scripts/lib on sys.path); full suite ~6.5min, admin-only ~0.4s
metadata:
  type: reference
---

Running `scripts/admin-server.py` tests:

- `tests/test_admin_server.py` inserts `<repo>/scripts` onto `sys.path` (so `lib.*` framework imports resolve). An auto-loaded pytest plugin (homeassistant/acme chain) does `from OpenSSL import ...` whose internal `lib` then resolves to THIS repo's `scripts/lib`, crashing with `module 'lib' has no attribute 'GEN_EMAIL'`.
- Fix / required flag: `-p no:homeassistant` (and `--ignore=tests/test_homeassistant` for the full suite). Command: `python3 -m pytest tests/ -q -p no:homeassistant --ignore=tests/test_homeassistant`.
- `coverage`/`ruff` are only runnable as `python3 -m coverage` / `python3 -m ruff` (no bare `coverage` on PATH). No ruff config file in repo → ruff defaults flag pre-existing EXE001/I001/BLE001/LOG014/S110; not enforced in CI.
- Timings: full suite ~6:30 (801 passed, 2 skipped baseline); `tests/test_admin_server.py` alone ~0.4s (91 tests) — use the admin-only run for fast iteration, full suite only at milestones.

Related: [[admin-server-god-object-split]].
