# admin-server.py Split — Backlog

## STATUS: open

`scripts/admin-server.py` is ~5330 lines, a clear outlier (the `scripts/lib/*.py`
600-line convention doesn't formally apply to it — it's a CLI/HTTP entrypoint, not
a `lib/` module — but the size is a maintainability smell).

Future split candidate, analogous to the `scripts/lib` decomposition pattern from
the August-2026 refactoring roadmap (route/service extraction). No acute handling
need — flagged here so it stays visible on the next `docs/plans/` cleanup pass.
